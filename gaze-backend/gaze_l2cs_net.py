#!/usr/bin/env python3
"""
Implementação corrigida do gaze detection com alta tolerância.
Detecta corretamente a direção do olhar e considera "Na Tela" até foco baixo.
"""

import cv2
import numpy as np
from typing import Dict, Union, Optional, Tuple
import time
import threading
import base64
import math

# Pontos importantes para face detection
LEFT_IRIS = [468, 469, 470, 471]
RIGHT_IRIS = [473, 474, 475, 476]
LEFT_EYE = [33, 133, 159, 145]
RIGHT_EYE = [362, 263, 386, 374]

class ImprovedGazeDetector:
    """
    Detector de gaze melhorado com alta tolerância.
    """
    
    def __init__(self):
        # AUMENTAR TOLERÂNCIA SIGNIFICATIVAMENTE
        self.gaze_threshold = 1.5      # Era 0.8, agora 1.5 (muito mais tolerante)
        self.attention_min = 0.1       # Era 0.3, agora 0.1 (muito mais tolerante)
        
        # Thresholds para classificação de foco
        self.focus_thresholds = {
            'excellent': 0.7,    # Era 0.8, agora 0.7
            'good': 0.5,         # Era 0.6, agora 0.5
            'moderate': 0.3,     # Era 0.4, agora 0.3
            'low': 0.1           # Era 0.2, agora 0.1
        }
        
        # Estado interno
        self.attention_history = []
        self.max_history = 20
        
    def detect_gaze_from_landmarks(self, landmarks, image_width: int, image_height: int) -> Dict:
        """
        Detecta gaze a partir dos landmarks do MediaPipe.
        Método mais direto e preciso.
        """
        
        # Calcular centro da íris (pupila)
        left_iris = np.mean([landmarks[idx] for idx in LEFT_IRIS], axis=0)
        right_iris = np.mean([landmarks[idx] for idx in RIGHT_IRIS], axis=0)
        iris_center = (left_iris + right_iris) / 2
        
        # Calcular centro do rosto (aproximado)
        left_eye = np.mean([landmarks[idx] for idx in LEFT_EYE], axis=0)
        right_eye = np.mean([landmarks[idx] for idx in RIGHT_EYE], axis=0)
        face_center = (left_eye + right_eye) / 2
        
        # Calcular deslocamento da íris em relação ao centro do rosto
        # Normalizar para valores entre -1 e +1
        iris_offset_x = (iris_center[0] - face_center[0]) / (image_width * 0.15)  # Aumentar tolerância
        iris_offset_y = (iris_center[1] - face_center[1]) / (image_height * 0.15)
        
        # Clamp para range válido
        dx = np.clip(iris_offset_x, -2.0, 2.0)  # Range mais amplo
        dy = np.clip(iris_offset_y, -2.0, 2.0)
        
        # Calcular atenção baseada na distância do centro
        # Quanto mais próximo do centro, maior a atenção
        distance_from_center = math.sqrt(dx**2 + dy**2)
        attention = max(0.0, 1.0 - (distance_from_center / 3.0))  # Divisor maior = mais tolerante
        
        # DETERMINAR SE ESTÁ NA TELA (MUITO MAIS TOLERANTE)
        # Considerar "Na Tela" até foco baixo
        on_screen = distance_from_center <= self.gaze_threshold and attention >= self.attention_min
        
        # Classificar nível de foco
        focus_level = self._classify_focus_level(attention)
        
        # Calcular direção do olhar em linguagem natural
        gaze_direction = self._calculate_gaze_direction(dx, dy)
        
        # Calcular ângulos simulados para compatibilidade
        pitch_deg = math.degrees(math.atan(dy * 0.5))  # Reduzir amplitude
        yaw_deg = math.degrees(math.atan(dx * 0.5))
        
        # Mapear para coordenadas da tela (0-1)
        gaze_x = 0.5 + (dx / 4.0)  # Dividir por 4 para reduzir amplitude
        gaze_y = 0.5 + (dy / 4.0)
        
        # Clamp para range válido
        gaze_x = np.clip(gaze_x, 0.0, 1.0)
        gaze_y = np.clip(gaze_y, 0.0, 1.0)
        
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
                "x": int(gaze_x * image_width),
                "y": int(gaze_y * image_height),
                "normalized": (gaze_x, gaze_y)
            },
            "attention": float(attention),
            "on_screen": on_screen,
            "focus_level": focus_level,
            "gaze_direction": gaze_direction,
            "distance_from_center": float(distance_from_center),
            "thresholds": {
                "gaze_limit": self.gaze_threshold,
                "attention_min": self.attention_min,
                "focus_levels": self.focus_thresholds
            }
        }
    
    def _classify_focus_level(self, attention: float) -> str:
        """Classifica o nível de foco com thresholds mais tolerantes."""
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
        """Calcula direção do olhar em linguagem natural."""
        direction = "centro"
        
        # Determinar direção horizontal (mais tolerante)
        if abs(dx) > 0.5:  # Era 0.3, agora 0.5
            if dx > 0:
                direction = "direita"
            else:
                direction = "esquerda"
        
        # Determinar direção vertical (mais tolerante)
        if abs(dy) > 0.5:  # Era 0.3, agora 0.5
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
        
        # Média simples para estabilidade
        return np.mean(self.attention_history)

def infer_gaze_improved(image_bytes: bytes) -> Dict[str, Union[bool, Dict, float]]:
    """
    Inferência de gaze melhorada com alta tolerância.
    """
    try:
        # Converter bytes para imagem
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if img is None:
            return {"error": "invalid_image", "message": "Imagem inválida"}
        
        h, w = img.shape[:2]
        
        # Configurar MediaPipe para landmarks
        import mediapipe as mp
        mp_face_mesh = mp.solutions.face_mesh
        
        with mp_face_mesh.FaceMesh(
            static_image_mode=True,
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5
        ) as face_mesh:
            
            # Processar imagem
            img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            results = face_mesh.process(img_rgb)
            
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
            
            # Usar detector melhorado
            detector = ImprovedGazeDetector()
            gaze_result = detector.detect_gaze_from_landmarks(landmarks_px, w, h)
            
            # Atualizar histórico de atenção
            detector.update_attention_history(gaze_result["attention"])
            smoothed_attention = detector.get_smoothed_attention()
            
            # Adicionar informações adicionais
            gaze_result["smoothed_attention"] = float(smoothed_attention)
            gaze_result["ok"] = True
            gaze_result["model"] = "Gaze Detection Melhorado (Alta Tolerância)"
            
            return gaze_result
            
    except Exception as e:
        return {
            "error": "processing_error",
            "message": f"Erro ao processar imagem: {str(e)}"
        }

def process_base64_frame_improved(base64_data: str) -> Dict[str, Union[bool, Dict, float]]:
    """Processamento de frame base64 com detector melhorado."""
    try:
        image_bytes = base64.b64decode(base64_data)
        return infer_gaze_improved(image_bytes)
    except Exception as e:
        return {
            "error": "base64_error",
            "message": f"Erro ao decodificar base64: {str(e)}"
        }

if __name__ == "__main__":
    print("🎯 Gaze Detection Melhorado carregado!")
    print("📊 Configurações de alta tolerância:")
    print(f"   - Gaze threshold: {1.5} (era 0.8)")
    print(f"   - Attention min: {0.1} (era 0.3)")
    print(f"   - Focus thresholds: {0.7}, {0.5}, {0.3}, {0.1}")
    print("   - Considera 'Na Tela' até foco baixo")
    print("   - Detecção mais precisa da direção do olhar")
