"""
Módulo principal para detecção de gaze usando MediaPipe FaceMesh.
Processa imagens para estimar direção do olhar e nível de atenção.
"""

import cv2
import numpy as np
import mediapipe as mp
from typing import Dict, Tuple, Optional, Union
import base64

# Constantes para índices dos landmarks do MediaPipe
LEFT_IRIS = [468, 469, 470, 471]
RIGHT_IRIS = [473, 474, 475, 476]
LEFT_EYE = [33, 133, 159, 145]  # cantos + pálpebras
RIGHT_EYE = [362, 263, 386, 374]

# Inicializar MediaPipe FaceMesh
mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(
    max_num_faces=1,
    refine_landmarks=True,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)


def _to_ndarray(image_bytes: bytes) -> np.ndarray:
    """
    Converte bytes de imagem para numpy array RGB.
    
    Args:
        image_bytes: Bytes da imagem
        
    Returns:
        numpy array RGB da imagem
    """
    # Decodificar bytes para numpy array
    nparr = np.frombuffer(image_bytes, np.uint8)
    # Decodificar como BGR (OpenCV default)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    # Converter BGR para RGB
    return cv2.cvtColor(img, cv2.COLOR_BGR2RGB)


def _landmarks_to_xy(landmarks, w: int, h: int, idxs: list) -> np.ndarray:
    """
    Extrai coordenadas x,y dos landmarks especificados.
    
    Args:
        landmarks: Objeto landmarks do MediaPipe
        w: Largura da imagem
        h: Altura da imagem
        idxs: Lista de índices dos landmarks
        
    Returns:
        Array numpy com coordenadas [x, y] para cada landmark
    """
    coords = []
    for idx in idxs:
        landmark = landmarks.landmark[idx]
        x = int(landmark.x * w)
        y = int(landmark.y * h)
        coords.append([x, y])
    return np.array(coords)


def _eye_metrics(iris_coords: np.ndarray, eye_coords: np.ndarray) -> Tuple[float, float, float]:
    """
    Calcula métricas do olho: deslocamento da íris e nível de atenção.
    
    Args:
        iris_coords: Coordenadas dos 4 pontos da íris
        eye_coords: Coordenadas dos 4 pontos do olho
        
    Returns:
        Tuple (dx, dy, attention) onde:
        - dx: deslocamento horizontal normalizado [-1, 1]
        - dy: deslocamento vertical normalizado [-1, 1]
        - attention: nível de atenção [0, 1]
    """
    # Calcular centro da íris
    iris_center = np.mean(iris_coords, axis=0)
    
    # Calcular centro do olho
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
    
    # Calcular nível de atenção baseado no movimento dos olhos
    # Quanto mais estável o olhar, maior a atenção
    attention = 1.0 - min(1.0, (abs(dx) + abs(dy)) / 2)
    
    return dx, dy, attention


def infer_gaze(image_bytes: bytes) -> Dict[str, Union[bool, Dict, float]]:
    """
    Infere direção do gaze e nível de atenção a partir de uma imagem.
    
    Args:
        image_bytes: Bytes da imagem
        
    Returns:
        Dicionário com resultados da inferência ou erro
    """
    try:
        # Converter bytes para numpy array
        img = _to_ndarray(image_bytes)
        h, w = img.shape[:2]
        
        # Processar imagem com MediaPipe
        results = face_mesh.process(img)
        
        if not results.multi_face_landmarks:
            return {"error": "no_face", "message": "Nenhum rosto detectado na imagem"}
        
        # Pegar o primeiro rosto detectado
        face_landmarks = results.multi_face_landmarks[0]
        
        # Extrair coordenadas dos olhos e íris
        left_iris_coords = _landmarks_to_xy(face_landmarks, w, h, LEFT_IRIS)
        right_iris_coords = _landmarks_to_xy(face_landmarks, w, h, RIGHT_IRIS)
        left_eye_coords = _landmarks_to_xy(face_landmarks, w, h, LEFT_EYE)
        right_eye_coords = _landmarks_to_xy(face_landmarks, w, h, RIGHT_EYE)
        
        # Calcular métricas para cada olho
        left_dx, left_dy, left_attention = _eye_metrics(left_iris_coords, left_eye_coords)
        right_dx, right_dy, right_attention = _eye_metrics(right_iris_coords, right_eye_coords)
        
        # Média dos dois olhos
        dx = (left_dx + right_dx) / 2
        dy = (left_dy + right_dy) / 2
        attention = (left_attention + right_attention) / 2
        
        # Clamp dos valores em [-1.5, 1.5]
        dx = np.clip(dx, -1.5, 1.5)
        dy = np.clip(dy, -1.5, 1.5)
        
        # Determinar se está olhando para a tela
        # on_screen = abs(h) <= 0.6 && abs(v) <= 0.6 && attention >= 0.4
        on_screen = abs(dx) <= 0.6 and abs(dy) <= 0.6 and attention >= 0.4
        
        return {
            "ok": True,
            "gaze": {
                "h": float(dx),
                "v": float(dy)
            },
            "attention": float(attention),
            "on_screen": on_screen,
            "calibration": {
                "h": 0.0,  # Será aplicado pelo módulo de calibração
                "v": 0.0
            }
        }
        
    except Exception as e:
        return {
            "error": "processing_error",
            "message": f"Erro ao processar imagem: {str(e)}"
        }


def process_base64_frame(base64_data: str) -> Dict[str, Union[bool, Dict, float]]:
    """
    Processa frame em base64 para inferência de gaze.
    
    Args:
        base64_data: String base64 da imagem
        
    Returns:
        Resultado da inferência de gaze
    """
    try:
        # Decodificar base64 para bytes
        image_bytes = base64.b64decode(base64_data)
        return infer_gaze(image_bytes)
    except Exception as e:
        return {
            "error": "base64_error",
            "message": f"Erro ao decodificar base64: {str(e)}"
        }
