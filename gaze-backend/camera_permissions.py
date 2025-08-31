"""
Script para verificar e solicitar permissões de câmera no macOS.
"""

import cv2
import subprocess
import sys
import os

def check_camera_permissions():
    """Verifica permissões de câmera no macOS."""
    print("🔐 Verificando permissões de câmera...")
    
    # Verificar se estamos no macOS
    if sys.platform != "darwin":
        print("⚠️ Este script é específico para macOS")
        return False
    
    # Verificar permissões usando tccutil
    try:
        result = subprocess.run(
            ["tccutil", "reset", "Camera"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            print("✅ Permissões de câmera resetadas")
            print("💡 Agora abra as Preferências do Sistema > Segurança e Privacidade > Câmera")
            print("💡 Adicione o Terminal ou Python à lista de apps permitidos")
            return True
        else:
            print(f"⚠️ Erro ao resetar permissões: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("⏰ Timeout ao verificar permissões")
        return False
    except FileNotFoundError:
        print("⚠️ tccutil não encontrado (pode precisar de sudo)")
        return False
    except Exception as e:
        print(f"❌ Erro ao verificar permissões: {e}")
        return False

def list_camera_devices():
    """Lista dispositivos de câmera disponíveis."""
    print("📷 Dispositivos de câmera disponíveis:")
    
    # Tentar diferentes índices de câmera
    for i in range(5):
        cap = cv2.VideoCapture(i)
        
        if cap.isOpened():
            # Obter informações da câmera
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = int(cap.get(cv2.CAP_PROP_FPS))
            
            print(f"   📹 Câmera {i}: {width}x{height} @ {fps}fps")
            
            # Tentar capturar um frame
            ret, frame = cap.read()
            if ret:
                print(f"      ✅ Funcionando - Frame: {frame.shape}")
            else:
                print(f"      ❌ Erro ao capturar frame")
            
            cap.release()
        else:
            print(f"   📹 Câmera {i}: Não disponível")
    
    print()

def test_camera_with_permission():
    """Testa câmera após verificar permissões."""
    print("🎯 Testando câmera com permissões...")
    
    # Tentar câmera padrão
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("❌ Câmera 0 não está disponível")
        
        # Tentar câmera 1 (às vezes é a câmera principal no Mac)
        cap = cv2.VideoCapture(1)
        
        if not cap.isOpened():
            print("❌ Câmera 1 também não está disponível")
            return False
    
    print("✅ Câmera aberta com sucesso!")
    
    # Configurar resolução
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    
    # Aguardar estabilização
    print("⏳ Aguardando estabilização...")
    for i in range(30):  # 3 segundos
        ret, frame = cap.read()
        if ret:
            print(f"\r⏳ Aguardando... {i+1}/30", end="", flush=True)
        time.sleep(0.1)
    
    print("\n📸 Capturando frame de teste...")
    
    # Capturar frame
    ret, frame = cap.read()
    
    if ret:
        print(f"✅ Frame capturado: {frame.shape}")
        
        # Salvar frame
        filename = "camera_test.jpg"
        cv2.imwrite(filename, frame)
        print(f"💾 Frame salvo como '{filename}'")
        
        # Verificar se arquivo foi criado
        if os.path.exists(filename):
            file_size = os.path.getsize(filename)
            print(f"📁 Arquivo criado: {file_size} bytes")
        else:
            print("❌ Erro: Arquivo não foi criado")
        
        cap.release()
        return True
    else:
        print("❌ Erro ao capturar frame")
        cap.release()
        return False

def main():
    """Função principal."""
    print("🚀 Verificador de Permissões de Câmera - macOS")
    print("=" * 60)
    
    # Listar dispositivos disponíveis
    list_camera_devices()
    
    # Verificar permissões
    if check_camera_permissions():
        print("\n💡 Após configurar as permissões, execute novamente este script")
        print("💡 Ou tente executar o script principal de teste")
    else:
        print("\n❌ Não foi possível verificar permissões")
    
    print("\n" + "=" * 60)
    print("📋 INSTRUÇÕES PARA PERMISSÕES DE CÂMERA:")
    print("1. Abra 'Preferências do Sistema'")
    print("2. Vá para 'Segurança e Privacidade'")
    print("3. Clique na aba 'Câmera'")
    print("4. Adicione 'Terminal' ou 'Python' à lista")
    print("5. Reinicie o Terminal")
    print("6. Execute novamente o script de teste")
    
    print("\n🔍 ALTERNATIVAS:")
    print("- Tente executar o script com sudo")
    print("- Verifique se a câmera está sendo usada por outro app")
    print("- Reinicie o Mac se necessário")

if __name__ == "__main__":
    import time
    main()
