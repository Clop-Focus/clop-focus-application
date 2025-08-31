#!/usr/bin/env python3
"""
Visualização dos pontos do rosto mapeados pelo MediaPipe FaceMesh.
Mostra exatamente quais pontos são usados para calcular o gaze.
"""

import cv2
import mediapipe as mp
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Circle
import matplotlib.patches as patches

# Configurar MediaPipe
mp_face_mesh = mp.solutions.face_mesh
mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles

def visualize_face_landmarks():
    """Visualiza todos os pontos do rosto mapeados pelo MediaPipe."""
    
    # Pontos específicos para gaze detection
    LEFT_EYE = [33, 133, 159, 145]  # Cantos do olho esquerdo
    RIGHT_EYE = [362, 263, 386, 374]  # Cantos do olho direito
    LEFT_IRIS = [468, 469, 470, 471]  # Pontos da íris esquerda
    RIGHT_IRIS = [473, 474, 475, 476]  # Pontos da íris direita
    
    # Pontos adicionais importantes
    NOSE_TIP = 4
    LEFT_EAR = 234
    RIGHT_EAR = 454
    FOREHEAD_CENTER = 10
    
    # Criar figura
    fig, ax = plt.subplots(1, 1, figsize=(12, 10))
    ax.set_xlim(0, 100)
    ax.set_ylim(100, 0)  # Inverter Y para corresponder às coordenadas de imagem
    
    # Título
    ax.set_title('🎭 Pontos do Rosto - MediaPipe FaceMesh\nGaze Detection Mapping', 
                 fontsize=16, fontweight='bold', pad=20)
    
    # Desenhar contorno do rosto (aproximado)
    face_outline = [
        (10, 10), (90, 10), (95, 20), (95, 80), (90, 90), (10, 90), (5, 80), (5, 20)
    ]
    face_polygon = patches.Polygon(face_outline, facecolor='lightgray', edgecolor='black', alpha=0.3)
    ax.add_patch(face_polygon)
    
    # Desenhar olhos
    # Olho esquerdo
    left_eye_center = (30, 40)
    ax.add_patch(patches.Ellipse(left_eye_center, 8, 4, facecolor='white', edgecolor='black'))
    ax.add_patch(patches.Ellipse((30, 40), 3, 3, facecolor='black'))  # Íris
    
    # Olho direito
    right_eye_center = (70, 40)
    ax.add_patch(patches.Ellipse(right_eye_center, 8, 4, facecolor='white', edgecolor='black'))
    ax.add_patch(patches.Ellipse((70, 40), 3, 3, facecolor='black'))  # Íris
    
    # Desenhar nariz
    ax.add_patch(patches.Polygon([(45, 50), (50, 60), (55, 50)], facecolor='pink', edgecolor='black'))
    
    # Desenhar boca
    ax.add_patch(patches.Ellipse((50, 75), 15, 8, facecolor='pink', edgecolor='black'))
    
    # Adicionar pontos específicos com legendas
    points_info = [
        # Olho Esquerdo
        (30, 40, "👁️ Olho Esquerdo", "blue", LEFT_EYE),
        (30, 40, "🎯 Íris Esquerda", "red", LEFT_IRIS),
        
        # Olho Direito  
        (70, 40, "👁️ Olho Direito", "blue", RIGHT_EYE),
        (70, 40, "🎯 Íris Direita", "red", RIGHT_IRIS),
        
        # Pontos de referência
        (50, 60, "👃 Ponta do Nariz", "green", [NOSE_TIP]),
        (20, 30, "👂 Orelha Esquerda", "orange", [LEFT_EAR]),
        (80, 30, "👂 Orelha Direita", "orange", [RIGHT_EAR]),
        (50, 15, "🧠 Centro da Testa", "purple", [FOREHEAD_CENTER])
    ]
    
    # Adicionar pontos e legendas
    for x, y, label, color, indices in points_info:
        ax.scatter(x, y, c=color, s=100, zorder=5)
        ax.annotate(label, (x, y), xytext=(5, 5), textcoords='offset points', 
                    fontsize=10, fontweight='bold', color=color)
        
        # Mostrar índices dos pontos
        indices_text = f"Índices: {indices}"
        ax.annotate(indices_text, (x, y), xytext=(5, -15), textcoords='offset points',
                    fontsize=8, color='gray')
    
    # Adicionar explicação do cálculo
    explanation = """
    📊 CÁLCULO DO GAZE:
    
    Para cada olho:
    1. Centro do olho = média dos cantos (pontos azuis)
    2. Centro da íris = média dos pontos da íris (pontos vermelhos)
    3. dx = (iris_x - eye_center_x) / (eye_width/2)
    4. dy = (iris_y - eye_center_y) / (eye_height/2)
    
    Gaze final = média dos dois olhos
    Atenção = 1.0 - min(1, (|dx| + |dy|) / 2)
    """
    
    ax.text(0.02, 0.98, explanation, transform=ax.transAxes, fontsize=10,
            verticalalignment='top', bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.8))
    
    # Configurações do gráfico
    ax.set_aspect('equal')
    ax.grid(True, alpha=0.3)
    ax.set_xlabel('Posição X (normalizada)')
    ax.set_ylabel('Posição Y (normalizada)')
    
    plt.tight_layout()
    plt.show()

def show_landmark_indices():
    """Mostra os índices específicos dos pontos importantes."""
    
    print("🎭 PONTOS DO ROSTO - MEDIAPIPE FACEMESH")
    print("=" * 50)
    
    print("\n👁️ OLHO ESQUERDO:")
    print("   Cantos: [33, 133, 159, 145]")
    print("   Íris: [468, 469, 470, 471]")
    
    print("\n👁️ OLHO DIREITO:")
    print("   Cantos: [362, 263, 386, 374]")
    print("   Íris: [473, 474, 475, 476]")
    
    print("\n📏 PONTOS DE REFERÊNCIA:")
    print("   Nariz: 4")
    print("   Orelha Esquerda: 234")
    print("   Orelha Direita: 454")
    print("   Testa: 10")
    
    print("\n🔍 COMO FUNCIONA:")
    print("   1. MediaPipe detecta 468 pontos no rosto")
    print("   2. Selecionamos pontos específicos dos olhos")
    print("   3. Calculamos centro do olho vs centro da íris")
    print("   4. Diferença = direção do olhar")
    print("   5. Atenção = quão centralizado está o olhar")

def create_gaze_calculation_demo():
    """Demonstra o cálculo do gaze com exemplo visual."""
    
    print("\n🧮 DEMONSTRAÇÃO DO CÁLCULO:")
    print("=" * 40)
    
    # Exemplo de cálculo
    print("\n📐 EXEMPLO PRÁTICO:")
    print("   Olho esquerdo:")
    print("   - Centro: (100, 200)")
    print("   - Íris: (105, 195)")
    print("   - dx = (105-100)/25 = +0.2 (olhando para direita)")
    print("   - dy = (195-200)/15 = -0.33 (olhando para baixo)")
    
    print("\n   Olho direito:")
    print("   - Centro: (300, 200)")
    print("   - Íris: (295, 205)")
    print("   - dx = (295-300)/25 = -0.2 (olhando para esquerda)")
    print("   - dy = (205-200)/15 = +0.33 (olhando para cima)")
    
    print("\n   Gaze final:")
    print("   - H = (0.2 + -0.2) / 2 = 0.0 (centro)")
    print("   - V = (-0.33 + 0.33) / 2 = 0.0 (centro)")
    print("   - Atenção = 1.0 - (|0.0| + |0.0|) / 2 = 1.0 (100%)")

if __name__ == "__main__":
    print("🎯 VISUALIZAÇÃO DOS PONTOS DO ROSTO")
    print("=" * 50)
    
    # Mostrar informações dos índices
    show_landmark_indices()
    
    # Mostrar demonstração do cálculo
    create_gaze_calculation_demo()
    
    print("\n🖼️ Abrindo visualização gráfica...")
    
    # Criar visualização
    try:
        visualize_face_landmarks()
    except Exception as e:
        print(f"❌ Erro ao criar visualização: {e}")
        print("💡 Certifique-se de ter matplotlib instalado: pip install matplotlib")
