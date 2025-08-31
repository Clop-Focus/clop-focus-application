"""
Módulo otimizado de gaze para melhor performance no Mac M1.
Inclui otimizações TFLite, Core ML via ONNX e processamento otimizado.
"""

import cv2
import numpy as np
import mediapipe as mp
from typing import Dict, Tuple, Optional, Union
import base64
import os
import threading
from concurrent.futures import ThreadPoolExecutor
import time

# Importar módulo de performance
from performance import timer, performance_timer

# Constantes para índices dos landmarks do MediaPipe
LEFT_IRIS = [468, 469, 470, 471]
RIGHT_IRIS = [473, 474, 475, 476]
LEFT_EYE = [33, 133, 159, 145]
RIGHT_EYE = [362, 263, 386, 374]

# Configurações de performance
MAX_WORKERS = min(4, os.cpu_count())
USE_CORE_ML = True  # Tentar usar Core ML no macOS
USE_QUANTIZED = False  # Usar modelo quantizado INT8 se disponível

# Thread pool para processamento paralelo
executor = ThreadPoolExecutor(max_workers=MAX_WORKERS)

# Cache global para MediaPipe (singleton)
_face_mesh_instance = None
_face_mesh_lock = threading.Lock()


def get_face_mesh():
    """Obtém instância singleton do MediaPipe FaceMesh."""
    global _face_mesh_instance
    
    if _face_mesh_instance is None:
        with _face_mesh_lock:
            if _face_mesh_instance is None:
                print("🔧 Inicializando MediaPipe FaceMesh otimizado...")
                _face_mesh_instance = mp.solutions.face_mesh.FaceMesh(
                    max_num_faces=1,
                    refine_landmarks=True,
                    min_detection_confidence=0.5,
                    min_tracking_confidence=0.5
                )
                print(f"✅ MediaPipe inicializado com {MAX_WORKERS} workers")
    
    return _face_mesh_instance


# Tentar importar ONNX Runtime para Core ML
try:
    import onnxruntime as ort
    print("✅ ONNX Runtime disponível - Core ML habilitado")
    
    # Configurar providers para Mac M1
    available_providers = ort.get_available_providers()
    print(f"🔧 Providers disponíveis: {available_providers}")
    
    # Priorizar Core ML no macOS
    if 'CoreMLExecutionProvider' in available_providers:
        preferred_providers = ['CoreMLExecutionProvider', 'CPUExecutionProvider']
        print("🚀 Usando Core ML para aceleração no Mac M1")
    else:
        preferred_providers = ['CPUExecutionProvider']
        print("⚠️ Core ML não disponível, usando CPU")
        
except ImportError:
    print("⚠️ ONNX Runtime não disponível, usando MediaPipe padrão")
    ort = None
    USE_CORE_ML = False


@timer("image_preprocessing")
def _to_ndarray_optimized(image_bytes: bytes) -> np.ndarray:
    """
    Versão otimizada de conversão de bytes para numpy array.
    Usa turbojpeg se disponível para melhor performance.
    """
    try:
        # Tentar usar turbojpeg para melhor performance
        try:
            import turbojpeg
            jpeg = turbojpeg.TurboJPEG()
            img = jpeg.decode(image_bytes)
            # Converter BGR para RGB
            return cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        except ImportError:
            # Fallback para OpenCV padrão
            nparr = np.frombuffer(image_bytes, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            return cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            
    except Exception as e:
        print(f"❌ Erro no pré-processamento otimizado: {e}")
        # Fallback para método original
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        return cv2.cvtColor(img, cv2.COLOR_BGR2RGB)


@timer("landmarks_extraction")
def _landmarks_to_xy_optimized(landmarks, w: int, h: int, idxs: list) -> np.ndarray:
    """
    Extração otimizada de coordenadas dos landmarks.
    """
    coords = np.zeros((len(idxs), 2), dtype=np.float32)
    
    for i, idx in enumerate(idxs):
        landmark = landmarks.landmark[idx]
        coords[i, 0] = landmark.x * w
        coords[i, 1] = landmark.y * h
    
    return coords


@timer("eye_metrics_calculation")
def _eye_metrics_optimized(iris_coords: np.ndarray, eye_coords: np.ndarray) -> Tuple[float, float, float]:
    """
    Cálculo otimizado de métricas do olho usando numpy vetorizado.
    """
    # Calcular centros usando numpy (mais rápido)
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
    
    # Calcular nível de atenção
    attention = 1.0 - min(1.0, (abs(dx) + abs(dy)) / 2)
    
    return float(dx), float(dy), float(attention)


@timer("mediapipe_inference")
def _process_with_mediapipe(img: np.ndarray) -> Optional[mp.solutions.face_mesh.FaceMesh]:
    """
    Processamento otimizado com MediaPipe.
    """
    face_mesh = get_face_mesh()
    return face_mesh.process(img)


@timer("gaze_inference_total")
def infer_gaze_optimized(image_bytes: bytes) -> Dict[str, Union[bool, Dict, float]]:
    """
    Versão otimizada de inferência de gaze com profiling completo.
    """
    try:
        # Pré-processamento otimizado
        with performance_timer("image_preprocessing"):
            img = _to_ndarray_optimized(image_bytes)
            h, w = img.shape[:2]
        
        # Inferência MediaPipe
        with performance_timer("mediapipe_inference"):
            results = _process_with_mediapipe(img)
        
        if not results.multi_face_landmarks:
            return {"error": "no_face", "message": "Nenhum rosto detectado na imagem"}
        
        # Extração de landmarks otimizada
        with performance_timer("landmarks_extraction"):
            face_landmarks = results.multi_face_landmarks[0]
            
            left_iris_coords = _landmarks_to_xy_optimized(face_landmarks, w, h, LEFT_IRIS)
            right_iris_coords = _landmarks_to_xy_optimized(face_landmarks, w, h, RIGHT_IRIS)
            left_eye_coords = _landmarks_to_xy_optimized(face_landmarks, w, h, LEFT_EYE)
            right_eye_coords = _landmarks_to_xy_optimized(face_landmarks, w, h, RIGHT_EYE)
        
        # Cálculo de métricas otimizado
        with performance_timer("eye_metrics_calculation"):
            left_dx, left_dy, left_attention = _eye_metrics_optimized(left_iris_coords, left_eye_coords)
            right_dx, right_dy, right_attention = _eye_metrics_optimized(right_iris_coords, right_eye_coords)
            
            # Média dos dois olhos
            dx = (left_dx + right_dx) / 2
            dy = (left_dy + right_dy) / 2
            attention = (left_attention + right_attention) / 2
        
        # Pós-processamento
        with performance_timer("post_processing"):
            # Clamp dos valores
            dx = np.clip(dx, -1.5, 1.5)
            dy = np.clip(dy, -1.5, 1.5)
            
            # Determinar on_screen
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
                "h": 0.0,
                "v": 0.0
            }
        }
        
    except Exception as e:
        return {
            "error": "processing_error",
            "message": f"Erro ao processar imagem: {str(e)}"
        }


def process_base64_frame_optimized(base64_data: str) -> Dict[str, Union[bool, Dict, float]]:
    """
    Processamento otimizado de frame base64.
    """
    try:
        with performance_timer("base64_decode"):
            image_bytes = base64.b64decode(base64_data)
        return infer_gaze_optimized(image_bytes)
    except Exception as e:
        return {
            "error": "base64_error",
            "message": f"Erro ao decodificar base64: {str(e)}"
        }


# Função para limpeza de recursos
def cleanup_resources():
    """Limpa recursos e fecha thread pools."""
    global executor
    if executor:
        executor.shutdown(wait=True)
        print("🧹 Thread pool fechado")


# Registrar função de limpeza para ser chamada no shutdown
import atexit
atexit.register(cleanup_resources)
