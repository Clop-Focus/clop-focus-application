#!/usr/bin/env python3
"""
Versão tolerante do gaze detection com thresholds ajustados para uso prático.
Menos exigente, mais realista para trabalho diário.
"""

import cv2
import mediapipe as mp
import numpy as np
from typing import Dict, Union, Optional, Tuple
import time
import threading
from concurrent.futures import ThreadPoolExecutor
import base64

# Configurar MediaPipe
mp_face_mesh = mp.solutions.face_mesh

# Pontos importantes para gaze detection
LEFT_IRIS = [468, 469, 470, 471]
RIGHT_IRIS = [473, 474, 475, 476]
LEFT_EYE = [33, 133, 159, 145]
RIGHT_EYE = [362, 263, 386, 374]

# Singleton para FaceMesh
_face_mesh = None
_face_mesh_lock = threading.Lock()

def get_face_mesh():
    """Singleton para FaceMesh para evitar re-inicialização."""
    global _face_mesh
    if _face_mesh is None:
        with _face_mesh_lock:
            if _face_mesh is None:
                _face_mesh = mp_face_mesh.FaceMesh(
                    static_image_mode=False,
                    max_num_faces=1,
                    refine_landmarks=True,  # Importante para íris
                    min_detection_confidence=0.5,
                    min_tracking_confidence=0.5
                )
    return _face_mesh

def _to_ndarray(image_bytes: bytes) -> np.ndarray:
    """Converte bytes para numpy array."""
    try:
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        return cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    except Exception as e:
        print(f"❌ Erro na conversão de imagem: {e}")
        raise

def _landmarks_to_xy(landmarks, w: int, h: int, idxs: list) -> np.ndarray:
    """Extrai coordenadas dos landmarks."""
    coords = np.zeros((len(idxs), 2), dtype=np.float32)
    
    for i, idx in enumerate(idxs):
        landmark = landmarks.landmark[idx]
        coords[i, 0] = landmark.x * w
        coords[i, 1] = landmark.y * h
    
    return coords

def _eye_metrics_tolerant(iris_coords: np.ndarray, eye_coords: np.ndarray) -> Tuple[float, float, float]:
    """
    Cálculo tolerante de métricas do olho.
    Usa thresholds mais realistas para trabalho diário.
    """
    # Calcular centros
    iris_center = np.mean(iris_coords, axis=0)
    eye_center = np.mean(eye_coords, axis=0)
    
    # Calcular dimensões do olho
    eye_width = np.max(eye_coords[:, 0]) - np.min(eye_coords[:, 0])
    eye_height = np.max(eye_coords[:, 1]) - np.min(eye_coords[:, 1])
    
    # Evitar divisão por zero
    if eye_width == 0 or eye_height == 0:
        return 0.0, 0.0, 0.0
    
    # Calcular deslocamento normalizado
    dx = (iris_center[0] - eye_center[0]) / (eye_width / 2)
    dy = (iris_center[1] - eye_center[1]) / (eye_height / 2)
    
    # THRESHOLDS MAIS TOLERANTES:
    # - Antes: attention = 1.0 - min(1.0, (abs(dx) + abs(dy)) / 2)
    # - Agora: attention = 1.0 - min(1.0, (abs(dx) + abs(dy)) / 4)
    # Isso dobra a tolerância para movimentos dos olhos
    
    # Calcular nível de atenção com tolerância aumentada
    attention = 1.0 - min(1.0, (abs(dx) + abs(dy)) / 4)
    
    return float(dx), float(dy), float(attention)

def infer_gaze_tolerant(image_bytes: bytes) -> Dict[str, Union[bool, Dict, float]]:
    """
    Versão tolerante de inferência de gaze.
    Menos exigente, mais realista para uso diário.
    """
    try:
        # Pré-processamento
        img = _to_ndarray(image_bytes)
        h, w = img.shape[:2]
        
        # Inferência MediaPipe
        face_mesh = get_face_mesh()
        results = face_mesh.process(img)
        
        if not results.multi_face_landmarks:
            return {"error": "no_face", "message": "Nenhum rosto detectado na imagem"}
        
        # Extração de landmarks
        face_landmarks = results.multi_face_landmarks[0]
        
        left_iris_coords = _landmarks_to_xy(face_landmarks, w, h, LEFT_IRIS)
        right_iris_coords = _landmarks_to_xy(face_landmarks, w, h, RIGHT_IRIS)
        left_eye_coords = _landmarks_to_xy(face_landmarks, w, h, LEFT_EYE)
        right_eye_coords = _landmarks_to_xy(face_landmarks, w, h, RIGHT_EYE)
        
        # Cálculo de métricas tolerante
        left_dx, left_dy, left_attention = _eye_metrics_tolerant(left_iris_coords, left_eye_coords)
        right_dx, right_dy, right_attention = _eye_metrics_tolerant(right_iris_coords, right_eye_coords)
        
        # Média dos dois olhos
        dx = (left_dx + right_dx) / 2
        dy = (left_dy + right_dy) / 2
        attention = (left_attention + right_attention) / 2
        
        # THRESHOLDS MAIS TOLERANTES:
        # - Clamp mais amplo: de [-1.5, 1.5] para [-2.0, 2.0]
        # - on_screen mais tolerante: de 0.6 para 1.0
        # - attention mínima: de 0.4 para 0.2
        
        # Clamp dos valores (mais amplo)
        dx = np.clip(dx, -2.0, 2.0)
        dy = np.clip(dy, -2.0, 2.0)
        
        # Determinar on_screen (MUITO mais tolerante)
        on_screen = abs(dx) <= 1.0 and abs(dy) <= 1.0 and attention >= 0.2
        
        # Classificação de foco mais detalhada
        focus_level = "excelente"
        if attention >= 0.8:
            focus_level = "excelente"
        elif attention >= 0.6:
            focus_level = "bom"
        elif attention >= 0.4:
            focus_level = "moderado"
        elif attention >= 0.2:
            focus_level = "baixo"
        else:
            focus_level = "crítico"
        
        return {
            "ok": True,
            "gaze": {
                "h": float(dx),
                "v": float(dy)
            },
            "attention": float(attention),
            "on_screen": on_screen,
            "focus_level": focus_level,
            "calibration": {
                "h": 0.0,
                "v": 0.0
            },
            "thresholds": {
                "gaze_limit": 1.0,      # Antes era 0.6
                "attention_min": 0.2,   # Antes era 0.4
                "clamp_range": 2.0      # Antes era 1.5
            }
        }
        
    except Exception as e:
        return {
            "error": "processing_error",
            "message": f"Erro ao processar imagem: {str(e)}"
        }

def process_base64_frame_tolerant(base64_data: str) -> Dict[str, Union[bool, Dict, float]]:
    """Processamento tolerante de frame base64."""
    try:
        image_bytes = base64.b64decode(base64_data)
        return infer_gaze_tolerant(image_bytes)
    except Exception as e:
        return {
            "error": "base64_error",
            "message": f"Erro ao decodificar base64: {str(e)}"
        }

# Função para limpeza de recursos
def cleanup_resources():
    """Limpa recursos e fecha FaceMesh."""
    global _face_mesh
    if _face_mesh:
        _face_mesh.close()
        _face_mesh = None
        print("🧹 FaceMesh fechado")

# Registrar função de limpeza para ser chamada no shutdown
import atexit
atexit.register(cleanup_resources)

if __name__ == "__main__":
    print("🎯 Gaze Detection Tolerante carregado!")
    print("📊 Thresholds ajustados:")
    print("   - Gaze limit: 1.0 (era 0.6)")
    print("   - Attention min: 0.2 (era 0.4)")
    print("   - Clamp range: 2.0 (era 1.5)")
    print("   - Attention calc: /4 (era /2)")
