#!/usr/bin/env python3
"""
Versão do gaze detection que considera um ponto fixo na tela como referência.
Mais preciso para determinar se o usuário está olhando para a tela.
"""

import cv2
import mediapipe as mp
import numpy as np
from typing import Dict, Union, Optional, Tuple
import time
import threading
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
                    refine_landmarks=True,
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

def _calculate_screen_gaze(iris_coords: np.ndarray, eye_coords: np.ndarray, 
                          screen_center: Tuple[float, float], 
                          screen_size: Tuple[float, float]) -> Tuple[float, float, float]:
    """
    Calcula gaze em relação a um ponto fixo na tela.
    
    Args:
        iris_coords: Coordenadas da íris
        eye_coords: Coordenadas do olho
        screen_center: Centro da tela (0.5, 0.5)
        screen_size: Tamanho da tela (1.0, 1.0)
    
    Returns:
        (dx, dy, attention) onde dx/dy são relativos ao centro da tela
    """
    # Calcular centro da íris
    iris_center = np.mean(iris_coords, axis=0)
    
    # Normalizar coordenadas da íris para 0-1
    iris_normalized = (iris_center[0] / screen_size[0], iris_center[1] / screen_size[1])
    
    # Calcular deslocamento em relação ao centro da tela
    dx = (iris_normalized[0] - screen_center[0]) * 2  # Multiplicar por 2 para range -1 a +1
    dy = (iris_normalized[1] - screen_center[1]) * 2
    
    # Clamp para range -1 a +1
    dx = np.clip(dx, -1.0, 1.0)
    dy = np.clip(dy, -1.0, 1.0)
    
    # Calcular atenção baseada na distância do centro da tela
    # Quanto mais próximo do centro, maior a atenção
    distance_from_center = np.sqrt(dx**2 + dy**2)
    attention = max(0.0, 1.0 - distance_from_center)
    
    return float(dx), float(dy), float(attention)

def infer_gaze_screen_fixed(image_bytes: bytes) -> Dict[str, Union[bool, Dict, float]]:
    """
    Inferência de gaze considerando ponto fixo na tela.
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
        
        # Definir centro da tela como referência fixa
        screen_center = (0.5, 0.5)  # Centro da tela (50%, 50%)
        screen_size = (1.0, 1.0)    # Tamanho normalizado da tela
        
        # Calcular gaze para cada olho em relação à tela
        left_dx, left_dy, left_attention = _calculate_screen_gaze(
            left_iris_coords, left_eye_coords, screen_center, screen_size
        )
        
        right_dx, right_dy, right_attention = _calculate_screen_gaze(
            right_iris_coords, right_eye_coords, screen_center, screen_size
        )
        
        # Média dos dois olhos
        dx = (left_dx + right_dx) / 2
        dy = (left_dy + right_dy) / 2
        attention = (left_attention + right_attention) / 2
        
        # Determinar se está olhando para a tela
        # Usar thresholds mais tolerantes
        on_screen = abs(dx) <= 0.8 and abs(dy) <= 0.8 and attention >= 0.3
        
        # Classificação de foco baseada na distância do centro da tela
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
        
        # Calcular direção do olhar em linguagem natural
        gaze_direction = "centro"
        if abs(dx) > 0.3 or abs(dy) > 0.3:
            if dx > 0.3:
                gaze_direction = "direita"
            elif dx < -0.3:
                gaze_direction = "esquerda"
            
            if dy > 0.3:
                gaze_direction += " e cima"
            elif dy < -0.3:
                gaze_direction += " e baixo"
        
        return {
            "ok": True,
            "gaze": {
                "h": float(dx),
                "v": float(dy)
            },
            "attention": float(attention),
            "on_screen": on_screen,
            "focus_level": focus_level,
            "gaze_direction": gaze_direction,
            "screen_reference": {
                "center": screen_center,
                "gaze_distance": np.sqrt(dx**2 + dy**2)
            },
            "calibration": {
                "h": 0.0,
                "v": 0.0
            },
            "thresholds": {
                "gaze_limit": 0.8,      # Mais tolerante
                "attention_min": 0.3,   # Mais tolerante
                "screen_center": (0.5, 0.5)  # Ponto fixo na tela
            }
        }
        
    except Exception as e:
        return {
            "error": "processing_error",
            "message": f"Erro ao processar imagem: {str(e)}"
        }

def process_base64_frame_screen_fixed(base64_data: str) -> Dict[str, Union[bool, Dict, float]]:
    """Processamento de frame base64 com referência fixa na tela."""
    try:
        image_bytes = base64.b64decode(base64_data)
        return infer_gaze_screen_fixed(image_bytes)
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
    print("🎯 Gaze Detection com Ponto Fixo na Tela carregado!")
    print("📊 Características:")
    print("   - Ponto de referência: CENTRO DA TELA (0.5, 0.5)")
    print("   - Gaze calculado em relação à tela, não ao rosto")
    print("   - Thresholds tolerantes: 0.8 para gaze, 0.3 para atenção")
    print("   - Direção do olhar em linguagem natural")
    print("   - Distância do centro da tela calculada")
