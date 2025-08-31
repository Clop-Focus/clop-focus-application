#!/usr/bin/env python3
"""
Mostra os pontos reais do MediaPipe FaceMesh em uma imagem.
Demonstra exatamente quais pontos são usados para gaze detection.
"""

import cv2
import mediapipe as mp
import numpy as np

# Configurar MediaPipe
mp_face_mesh = mp.solutions.face_mesh
mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles

def show_landmarks_on_image(image_path):
    """Mostra os pontos do MediaPipe em uma imagem real."""
    
    # Ler imagem
    image = cv2.imread(image_path)
    if image is None:
        print(f"❌ Não foi possível carregar a imagem: {image_path}")
        return
    
    # Converter BGR para RGB
    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    
    # Configurar FaceMesh
    with mp_face_mesh.FaceMesh(
        static_image_mode=True,
        max_num_faces=1,
        refine_landmarks=True,  # Importante para íris
        min_detection_confidence=0.5
    ) as face_mesh:
        
        # Processar imagem
        results = face_mesh.process(image_rgb)
        
        if not results.multi_face_landmarks:
            print("❌ Nenhum rosto detectado na imagem")
            return
        
        # Obter landmarks do primeiro rosto
        landmarks = results.multi_face_landmarks[0]
        
        # Converter para coordenadas de pixel
        h, w, _ = image.shape
        landmarks_px = []
        for landmark in landmarks.landmark:
            x = int(landmark.x * w)
            y = int(landmark.y * h)
            landmarks_px.append((x, y))
        
        # Definir pontos importantes para gaze
        LEFT_EYE = [33, 133, 159, 145]
        RIGHT_EYE = [362, 263, 386, 374]
        LEFT_IRIS = [468, 469, 470, 471]
        RIGHT_IRIS = [473, 474, 475, 476]
        
        # Pontos de referência adicionais
        NOSE_TIP = 4
        LEFT_EAR = 234
        RIGHT_EAR = 454
        FOREHEAD_CENTER = 10
        
        # Criar cópia da imagem para desenhar
        image_draw = image.copy()
        
        # Desenhar todos os pontos do rosto (pequenos)
        for i, (x, y) in enumerate(landmarks_px):
            cv2.circle(image_draw, (x, y), 1, (100, 100, 100), -1)
        
        # Desenhar pontos importantes com cores diferentes
        colors = {
            'left_eye': (255, 0, 0),      # Azul
            'right_eye': (0, 255, 0),     # Verde
            'left_iris': (0, 0, 255),     # Vermelho
            'right_iris': (255, 0, 255),  # Magenta
            'nose': (0, 255, 255),        # Ciano
            'ears': (255, 255, 0),        # Amarelo
            'forehead': (128, 0, 128)     # Roxo
        }
        
        # Desenhar olho esquerdo
        for idx in LEFT_EYE:
            x, y = landmarks_px[idx]
            cv2.circle(image_draw, (x, y), 3, colors['left_eye'], -1)
            cv2.putText(image_draw, str(idx), (x+5, y-5), cv2.FONT_HERSHEY_SIMPLEX, 0.3, colors['left_eye'], 1)
        
        # Desenhar olho direito
        for idx in RIGHT_EYE:
            x, y = landmarks_px[idx]
            cv2.circle(image_draw, (x, y), 3, colors['right_eye'], -1)
            cv2.putText(image_draw, str(idx), (x+5, y-5), cv2.FONT_HERSHEY_SIMPLEX, 0.3, colors['right_eye'], 1)
        
        # Desenhar íris esquerda
        for idx in LEFT_IRIS:
            x, y = landmarks_px[idx]
            cv2.circle(image_draw, (x, y), 4, colors['left_iris'], -1)
            cv2.putText(image_draw, str(idx), (x+5, y-5), cv2.FONT_HERSHEY_SIMPLEX, 0.3, colors['left_iris'], 1)
        
        # Desenhar íris direita
        for idx in RIGHT_IRIS:
            x, y = landmarks_px[idx]
            cv2.circle(image_draw, (x, y), 4, colors['right_iris'], -1)
            cv2.putText(image_draw, str(idx), (x+5, y-5), cv2.FONT_HERSHEY_SIMPLEX, 0.3, colors['right_iris'], 1)
        
        # Desenhar nariz
        x, y = landmarks_px[NOSE_TIP]
        cv2.circle(image_draw, (x, y), 5, colors['nose'], -1)
        cv2.putText(image_draw, str(NOSE_TIP), (x+5, y-5), cv2.FONT_HERSHEY_SIMPLEX, 0.4, colors['nose'], 1)
        
        # Desenhar orelhas
        for idx in [LEFT_EAR, RIGHT_EAR]:
            x, y = landmarks_px[idx]
            cv2.circle(image_draw, (x, y), 4, colors['ears'], -1)
            cv2.putText(image_draw, str(idx), (x+5, y-5), cv2.FONT_HERSHEY_SIMPLEX, 0.3, colors['ears'], 1)
        
        # Desenhar testa
        x, y = landmarks_px[FOREHEAD_CENTER]
        cv2.circle(image_draw, (x, y), 4, colors['forehead'], -1)
        cv2.putText(image_draw, str(FOREHEAD_CENTER), (x+5, y-5), cv2.FONT_HERSHEY_SIMPLEX, 0.3, colors['forehead'], 1)
        
        # Calcular e mostrar gaze
        print("\n🎯 CÁLCULO DO GAZE EM TEMPO REAL:")
        print("=" * 40)
        
        # Calcular centro dos olhos
        left_eye_center = np.mean([landmarks_px[idx] for idx in LEFT_EYE], axis=0)
        right_eye_center = np.mean([landmarks_px[idx] for idx in RIGHT_EYE], axis=0)
        
        # Calcular centro das íris
        left_iris_center = np.mean([landmarks_px[idx] for idx in LEFT_IRIS], axis=0)
        right_iris_center = np.mean([landmarks_px[idx] for idx in RIGHT_IRIS], axis=0)
        
        # Calcular gaze para cada olho
        left_dx = (left_iris_center[0] - left_eye_center[0]) / 50  # Normalizar
        left_dy = (left_iris_center[1] - left_eye_center[1]) / 30
        
        right_dx = (right_iris_center[0] - right_eye_center[0]) / 50
        right_dy = (right_iris_center[1] - right_eye_center[1]) / 30
        
        # Gaze final (média dos dois olhos)
        gaze_h = (left_dx + right_dx) / 2
        gaze_v = (left_dy + right_dy) / 2
        
        # Calcular atenção
        attention = 1.0 - min(1, (abs(gaze_h) + abs(gaze_v)) / 2)
        
        print(f"👁️ Olho Esquerdo:")
        print(f"   Centro: ({left_eye_center[0]:.1f}, {left_eye_center[1]:.1f})")
        print(f"   Íris: ({left_iris_center[0]:.1f}, {left_iris_center[1]:.1f})")
        print(f"   dx: {left_dx:.3f}, dy: {left_dy:.3f}")
        
        print(f"\n👁️ Olho Direito:")
        print(f"   Centro: ({right_eye_center[0]:.1f}, {right_eye_center[1]:.1f})")
        print(f"   Íris: ({right_iris_center[0]:.1f}, {right_iris_center[1]:.1f})")
        print(f"   dx: {right_dx:.3f}, dy: {right_dy:.3f}")
        
        print(f"\n🎯 GAZE FINAL:")
        print(f"   Horizontal: {gaze_h:.3f} ({'esquerda' if gaze_h < -0.1 else 'direita' if gaze_h > 0.1 else 'centro'})")
        print(f"   Vertical: {gaze_v:.3f} ({'baixo' if gaze_v < -0.1 else 'cima' if gaze_v > 0.1 else 'centro'})")
        print(f"   Atenção: {attention:.1%}")
        
        # Desenhar setas de gaze
        center_x, center_y = int(w/2), int(h/2)
        gaze_x = int(center_x + gaze_h * 100)
        gaze_y = int(center_y + gaze_v * 100)
        
        cv2.arrowedLine(image_draw, (center_x, center_y), (gaze_x, gaze_y), (0, 255, 255), 3)
        cv2.putText(image_draw, f"Gaze: H={gaze_h:.2f}, V={gaze_v:.2f}", (10, 30), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
        cv2.putText(image_draw, f"Attention: {attention:.1%}", (10, 60), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
        
        # Adicionar legenda
        legend_y = h - 150
        cv2.putText(image_draw, "LEGENDA:", (10, legend_y), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        cv2.circle(image_draw, (10, legend_y + 20), 3, colors['left_eye'], -1)
        cv2.putText(image_draw, "Olho Esquerdo (azul)", (20, legend_y + 25), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
        
        cv2.circle(image_draw, (10, legend_y + 40), 3, colors['right_eye'], -1)
        cv2.putText(image_draw, "Olho Direito (verde)", (20, legend_y + 45), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
        
        cv2.circle(image_draw, (10, legend_y + 60), 4, colors['left_iris'], -1)
        cv2.putText(image_draw, "Íris Esquerda (vermelho)", (20, legend_y + 65), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
        
        cv2.circle(image_draw, (10, legend_y + 80), 4, colors['right_iris'], -1)
        cv2.putText(image_draw, "Íris Direita (magenta)", (20, legend_y + 85), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
        
        cv2.circle(image_draw, (10, legend_y + 100), 5, colors['nose'], -1)
        cv2.putText(image_draw, "Nariz (ciano)", (20, legend_y + 105), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
        
        # Salvar imagem com landmarks
        output_path = "landmarks_visualization.jpg"
        cv2.imwrite(output_path, image_draw)
        print(f"\n💾 Imagem salva como: {output_path}")
        
        # Mostrar imagem
        cv2.imshow("MediaPipe FaceMesh - Landmarks", image_draw)
        cv2.waitKey(0)
        cv2.destroyAllWindows()

if __name__ == "__main__":
    print("🎯 VISUALIZAÇÃO DOS PONTOS REAIS DO ROSTO")
    print("=" * 50)
    
    # Tentar usar uma das imagens disponíveis
    image_paths = [
        "test_frame_camera1.jpg",  # Esta tem rosto
        "camera_0_test.jpg"
    ]
    
    for path in image_paths:
        if cv2.imread(path) is not None:
            print(f"📸 Usando imagem: {path}")
            show_landmarks_on_image(path)
            break
    else:
        print("❌ Nenhuma imagem encontrada para teste")
        print("💡 Coloque uma imagem com rosto no diretório para testar")
