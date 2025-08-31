"""
Script simples para testar a câmera e detecção de gaze.
"""

import cv2
import numpy as np
import requests
import time
import json

def test_camera():
    """Testa se a câmera está funcionando."""
    print("📷 Testando câmera...")
    
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("❌ Erro: Não foi possível abrir a câmera")
        return False
    
    # Capturar um frame
    ret, frame = cap.read()
    
    if ret:
        print(f"✅ Câmera funcionando! Frame capturado: {frame.shape}")
        cap.release()
        return True
    else:
        print("❌ Erro: Não foi possível capturar frame")
        cap.release()
        return False

def test_backend():
    """Testa se o backend está funcionando."""
    print("🔗 Testando backend...")
    
    try:
        response = requests.get("http://localhost:8000/health", timeout=2)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Backend funcionando! Versão: {result.get('version')}")
            return True
        else:
            print(f"❌ Backend respondeu com erro: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Erro ao conectar com backend: {e}")
        return False

def capture_and_detect():
    """Captura um frame e testa a detecção de gaze."""
    print("🎯 Capturando frame e testando detecção...")
    
    # Capturar frame
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    
    if not cap.isOpened():
        print("❌ Erro: Não foi possível abrir a câmera")
        return
    
    # Aguardar um pouco para a câmera estabilizar
    print("⏳ Aguardando estabilização da câmera...")
    time.sleep(2)
    
    # Capturar frame
    ret, frame = cap.read()
    cap.release()
    
    if not ret:
        print("❌ Erro: Não foi possível capturar frame")
        return
    
    print(f"✅ Frame capturado: {frame.shape}")
    
    # Salvar frame para debug
    cv2.imwrite("test_frame.jpg", frame)
    print("💾 Frame salvo como 'test_frame.jpg'")
    
    # Converter para JPEG
    _, jpeg_data = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 90])
    
    # Enviar para backend
    print("📤 Enviando frame para backend...")
    
    try:
        files = {'frame': ('frame.jpg', jpeg_data.tobytes(), 'image/jpeg')}
        data = {'session_id': 'test_session'}
        
        response = requests.post(
            "http://localhost:8000/gaze",
            files=files,
            data=data,
            timeout=10.0
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Resposta do backend:")
            print(json.dumps(result, indent=2, ensure_ascii=False))
            
            if result.get("ok"):
                gaze = result.get("gaze", {})
                attention = result.get("attention", 0)
                on_screen = result.get("on_screen", False)
                
                print(f"\n🎯 RESULTADO DA DETECÇÃO:")
                print(f"   Direção Horizontal: {gaze.get('h', 0):.3f} (-1=esquerda, +1=direita)")
                print(f"   Direção Vertical: {gaze.get('v', 0):.3f} (-1=baixo, +1=cima)")
                print(f"   Nível de Atenção: {attention:.3f} (0=distraído, 1=focado)")
                print(f"   Olhando para tela: {'Sim' if on_screen else 'Não'}")
                
                # Interpretar direção
                h, v = gaze.get('h', 0), gaze.get('v', 0)
                
                if abs(h) < 0.2 and abs(v) < 0.2:
                    print("   📍 Olhando para o CENTRO da tela")
                elif abs(h) < 0.2:
                    if v > 0.2:
                        print("   📍 Olhando para CIMA da tela")
                    else:
                        print("   📍 Olhando para BAIXO da tela")
                elif abs(v) < 0.2:
                    if h > 0.2:
                        print("   📍 Olhando para DIREITA da tela")
                    else:
                        print("   📍 Olhando para ESQUERDA da tela")
                else:
                    print("   📍 Olhando para uma posição específica da tela")
                
            else:
                print(f"❌ Backend retornou erro: {result}")
                
        else:
            print(f"❌ Erro HTTP {response.status_code}: {response.text}")
            
    except requests.exceptions.Timeout:
        print("⏰ Timeout ao processar frame")
    except Exception as e:
        print(f"❌ Erro ao processar frame: {e}")

def main():
    """Função principal."""
    print("🚀 Teste de Câmera e Detecção de Gaze")
    print("=" * 50)
    
    # Testar câmera
    if not test_camera():
        print("❌ Teste da câmera falhou. Verifique se a câmera está conectada.")
        return
    
    # Testar backend
    if not test_backend():
        print("❌ Teste do backend falhou. Verifique se está rodando.")
        return
    
    print("\n" + "=" * 50)
    
    # Capturar e detectar
    capture_and_detect()
    
    print("\n✅ Teste concluído!")

if __name__ == "__main__":
    main()
