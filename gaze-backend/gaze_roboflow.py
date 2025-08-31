#!/usr/bin/env python3
"""
Gaze Detection Robusto usando MediaPipe FaceMesh.
Detecta corretamente a posição dos olhos e aplica alta tolerância.
"""

import cv2
import numpy as np
import mediapipe as mp
from typing import Dict, Any, Tuple, Optional
import math
import time

# Configurações do MediaPipe
mp_face_mesh = mp.solutions.face_mesh
mp_drawing = mp.solutions.drawing_utils

# Pontos importantes para face detection (MediaPipe FaceMesh)
LEFT_IRIS = [468, 469, 470, 471]      # Íris esquerda
RIGHT_IRIS = [473, 474, 475, 476]     # Íris direita
LEFT_EYE = [33, 133, 159, 145]       # Olho esquerdo (cantos)
RIGHT_EYE = [362, 263, 386, 374]     # Olho direito (cantos)
LEFT_PUPIL = [468]                    # Pupila esquerda (centro da íris)
RIGHT_PUPIL = [473]                   # Pupila direita (centro da íris)
NOSE_TIP = [4]                        # Ponta do nariz
LEFT_EAR = [234]                      # Orelha esquerda
RIGHT_EAR = [454]                     # Orelha direita

class RobustGazeDetector:
    """
    Detector de gaze robusto com alta tolerância.
    Detecta corretamente a posição dos olhos e aplica configurações flexíveis.
    """
    
    def __init__(self):
        # CONFIGURAÇÃO MAIS REALISTA (não extremamente tolerante)
        self.gaze_threshold = 0.8      # Era 2.0, agora 0.8 (mais realista)
        self.attention_min = 0.3       # Era 0.05, agora 0.3 (mais realista)
        self.focus_thresholds = {
            'excellent': 0.8,    # Era 0.6, agora 0.8 (mais realista)
            'good': 0.6,         # Era 0.4, agora 0.6
            'moderate': 0.4,     # Era 0.2, agora 0.4
            'low': 0.2           # Era 0.05, agora 0.2
        }
        
        # Estado interno
        self.attention_history = []
        self.max_history = 15
        self.last_gaze = None
        self.face_mesh = None
        
        # Inicializar MediaPipe
        self._init_mediapipe()
    
    def _init_mediapipe(self):
        """Inicializa MediaPipe FaceMesh."""
        try:
            self.face_mesh = mp_face_mesh.FaceMesh(
                static_image_mode=False,
                max_num_faces=1,
                refine_landmarks=True,
                min_detection_confidence=0.5,
                min_tracking_confidence=0.5
            )
            print("✅ MediaPipe FaceMesh inicializado com sucesso!")
        except Exception as e:
            print(f"❌ Erro ao inicializar MediaPipe: {e}")
            self.face_mesh = None
    
    def detect_gaze_from_image(self, image_bytes: bytes) -> Dict[str, Any]:
        """
        Detecta gaze a partir de uma imagem.
        Método principal e mais robusto.
        """
        try:
            # Converter bytes para imagem
            nparr = np.frombuffer(image_bytes, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if img is None:
                return {"error": "invalid_image", "message": "Imagem inválida"}
            
            h, w = img.shape[:2]
            
            # Processar com MediaPipe
            img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            results = self.face_mesh.process(img_rgb)
            
            if not results.multi_face_landmarks:
                return {"error": "no_face", "message": "Nenhum rosto detectado na imagem"}
            
            # Obter landmarks
            landmarks = results.multi_face_landmarks[0]
            
            # Converter para coordenadas de pixel
            landmarks_px = []
            for landmark in landmarks.landmark:
                x = int(landmark.x * w)
                y = int(landmark.y * h)
                landmarks_px.append((x, y))
            
            # Calcular gaze robusto
            gaze_result = self._calculate_robust_gaze(landmarks_px, w, h)
            
            # Atualizar histórico
            self.update_attention_history(gaze_result["attention"])
            smoothed_attention = self.get_smoothed_attention()
            
            # Adicionar informações extras
            gaze_result["smoothed_attention"] = float(smoothed_attention)
            gaze_result["ok"] = True
            gaze_result["model"] = "Gaze Detection Robusto (Alta Tolerância)"
            gaze_result["image_size"] = {"width": w, "height": h}
            gaze_result["landmarks_count"] = len(landmarks_px)
            
            return gaze_result
            
        except Exception as e:
            return {
                "error": "processing_error",
                "message": f"Erro ao processar imagem: {str(e)}"
            }
    
    def _calculate_robust_gaze(self, landmarks: list, w: int, h: int) -> Dict[str, Any]:
        """
        Calcula gaze de forma robusta usando landmarks específicos.
        """
        # Calcular centro da íris (pupila) - mais preciso
        left_iris = np.mean([landmarks[idx] for idx in LEFT_IRIS], axis=0)
        right_iris = np.mean([landmarks[idx] for idx in RIGHT_IRIS], axis=0)
        iris_center = (left_iris + right_iris) / 2
        
        # Calcular centro do rosto (usando olhos como referência)
        left_eye = np.mean([landmarks[idx] for idx in LEFT_EYE], axis=0)
        right_eye = np.mean([landmarks[idx] for idx in RIGHT_EYE], axis=0)
        face_center = (left_eye + right_eye) / 2
        
        # Calcular deslocamento da íris em relação ao centro do rosto
        # Usar normalização mais tolerante
        iris_offset_x = (iris_center[0] - face_center[0]) / (w * 0.2)  # Mais tolerante
        iris_offset_y = (iris_center[1] - face_center[1]) / (h * 0.2)
        
        # Clamp para range válido (muito mais amplo)
        dx = np.clip(iris_offset_x, -3.0, 3.0)  # Range muito amplo
        dy = np.clip(iris_offset_y, -3.0, 3.0)
        
        # Calcular atenção baseada na distância do centro (LÓGICA CORRIGIDA)
        distance_from_center = math.sqrt(dx**2 + dy**2)
        
        # Fórmula mais realista: atenção diminui exponencialmente com a distância
        if distance_from_center <= 0.3:
            attention = 1.0  # Máxima atenção quando muito próximo do centro
        elif distance_from_center <= 0.8:
            attention = 1.0 - (distance_from_center - 0.3) * 0.7  # Decaimento linear
        else:
            attention = max(0.0, 0.65 - (distance_from_center - 0.8) * 0.5)  # Decaimento mais rápido
        
        # DETERMINAR SE ESTÁ NA TELA (MAIS REALISTA)
        on_screen = distance_from_center <= self.gaze_threshold and attention >= self.attention_min
        
        # Classificar nível de foco
        focus_level = self._classify_focus_level(attention)
        
        # Calcular direção do olhar
        gaze_direction = self._calculate_gaze_direction(dx, dy)
        
        # Calcular ângulos simulados (para compatibilidade)
        pitch_deg = math.degrees(math.atan(dy * 0.3))  # Reduzir amplitude
        yaw_deg = math.degrees(math.atan(dx * 0.3))
        
        # Mapear para coordenadas da tela (0-1)
        gaze_x = 0.5 + (dx / 6.0)  # Dividir por 6 para reduzir amplitude
        gaze_y = 0.5 + (dy / 6.0)
        
        # Clamp para range válido
        gaze_x = np.clip(gaze_x, 0.0, 1.0)
        gaze_y = np.clip(gaze_y, 0.0, 1.0)
        
        # Calcular bbox da face (aproximado)
        face_bbox = self._calculate_face_bbox(landmarks, w, h)
        
        return {
            "gaze": {
                "h": float(dx),
                "v": float(dy),
                "x": float(gaze_x),
                "y": float(gaze_y)
            },
            "angles": {
                "pitch_deg": float(pitch_deg),
                "yaw_deg": float(yaw_deg),
                "pitch_rad": float(pitch_deg * math.pi / 180),
                "yaw_rad": float(yaw_deg * math.pi / 180)
            },
            "screen_point": {
                "x": int(gaze_x * w),
                "y": int(gaze_y * h),
                "normalized": (gaze_x, gaze_y)
            },
            "attention": float(attention),
            "on_screen": on_screen,
            "focus_level": focus_level,
            "gaze_direction": gaze_direction,
            "distance_from_center": float(distance_from_center),
            "face_bbox": face_bbox,
            "thresholds": {
                "gaze_limit": self.gaze_threshold,
                "attention_min": self.attention_min,
                "focus_levels": self.focus_thresholds
            },
            "landmarks": {
                "left_iris": left_iris.tolist(),
                "right_iris": right_iris.tolist(),
                "left_eye": left_eye.tolist(),
                "right_eye": right_eye.tolist(),
                "face_center": face_center.tolist()
            }
        }
    
    def _calculate_face_bbox(self, landmarks: list, w: int, h: int) -> Dict[str, float]:
        """Calcula bbox da face normalizado (0-1)."""
        try:
            # Usar pontos extremos da face
            x_coords = [landmarks[i][0] for i in range(len(landmarks)) if i < 468]  # Pontos faciais
            y_coords = [landmarks[i][1] for i in range(len(landmarks)) if i < 468]
            
            if x_coords and y_coords:
                x_min, x_max = min(x_coords), max(x_coords)
                y_min, y_max = min(y_coords), max(y_coords)
                
                return {
                    "x": x_min / w,
                    "y": y_min / h,
                    "w": (x_max - x_min) / w,
                    "h": (y_max - y_min) / h
                }
        except:
            pass
        
        return {"x": 0.0, "y": 0.0, "w": 0.0, "h": 0.0}
    
    def _classify_focus_level(self, attention: float) -> str:
        """Classifica o nível de foco com thresholds muito tolerantes."""
        if attention >= self.focus_thresholds['excellent']:
            return "excelente"
        elif attention >= self.focus_thresholds['good']:
            return "bom"
        elif attention >= self.focus_thresholds['moderate']:
            return "moderado"
        elif attention >= self.focus_thresholds['low']:
            return "baixo"
        else:
            return "crítico"
    
    def _calculate_gaze_direction(self, dx: float, dy: float) -> str:
        """Calcula direção do olhar com alta tolerância."""
        direction = "centro"
        
        # Determinar direção horizontal (muito tolerante)
        if abs(dx) > 0.8:  # Era 0.5, agora 0.8
            if dx > 0:
                direction = "direita"
            else:
                direction = "esquerda"
        
        # Determinar direção vertical (muito tolerante)
        if abs(dy) > 0.8:  # Era 0.5, agora 0.8
            if dy > 0:
                direction += " e cima"
            else:
                direction += " e baixo"
        
        return direction
    
    def update_attention_history(self, attention: float):
        """Atualiza histórico de atenção para suavização."""
        self.attention_history.append(attention)
        
        if len(self.attention_history) > self.max_history:
            self.attention_history.pop(0)
    
    def get_smoothed_attention(self) -> float:
        """Retorna atenção suavizada."""
        if not self.attention_history:
            return 0.0
        
        # Média ponderada (frames mais recentes têm mais peso)
        weights = np.linspace(0.5, 1.0, len(self.attention_history))
        weighted_sum = np.sum(np.array(self.attention_history) * weights)
        total_weight = np.sum(weights)
        
        return weighted_sum / total_weight
    
    def cleanup(self):
        """Limpa recursos do MediaPipe."""
        if self.face_mesh:
            self.face_mesh.close()

def infer_gaze_roboflow(image_bytes: bytes) -> Dict[str, Any]:
    """
    Função principal para inferência de gaze.
    """
    try:
        detector = RobustGazeDetector()
        result = detector.detect_gaze_from_image(image_bytes)
        detector.cleanup()
        return result
    except Exception as e:
        return {
            "error": "detector_error",
            "message": f"Erro no detector: {str(e)}"
        }

def process_base64_frame_roboflow(base64_data: str) -> Dict[str, Any]:
    """Processamento de frame base64."""
    try:
        import base64 as b64
        image_bytes = b64.b64decode(base64_data)
        return infer_gaze_roboflow(image_bytes)
    except Exception as e:
        return {
            "error": "base64_error",
            "message": f"Erro ao decodificar base64: {str(e)}"
        }

if __name__ == "__main__":
        print("🎯 Gaze Detection Robusto carregado!")
    print("📊 Configurações REALISTAS:")
    print(f"   - Gaze threshold: {0.8} (mais realista)")
    print(f"   - Attention min: {0.3} (mais realista)")
    print(f"   - Focus thresholds: {0.8}, {0.6}, {0.4}, {0.2}")
    print("   - Considera 'Na Tela' com thresholds realistas")
    print("   - Detecção robusta da posição dos olhos")
    print("   - BBox da face incluído")
