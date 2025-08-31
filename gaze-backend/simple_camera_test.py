"""
Teste simples de câmera que solicita permissão de forma mais direta.
"""

import cv2
import time

def test_camera_simple():
    """Testa câmera de forma mais simples."""
    print("📷 Testando câmera de forma simples...")
    
    # Tentar diferentes índices
    for camera_index in [0, 1]:
        print(f"\n🔍 Tentando câmera {camera_index}...")
        
        try:
            # Abrir câmera
            cap = cv2.VideoCapture(camera_index)
            
            if not cap.isOpened():
                print(f"   ❌ Câmera {camera_index} não abriu")
                continue
            
            print(f"   ✅ Câmera {camera_index} aberta")
            
            # Configurar propriedades
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            
            # Aguardar um pouco
            print("   ⏳ Aguardando estabilização...")
            time.sleep(2)
            
            # Tentar capturar frame
            ret, frame = cap.read()
            
            if ret:
                print(f"   ✅ Frame capturado: {frame.shape}")
                
                # Salvar frame
                filename = f"camera_{camera_index}_test.jpg"
                cv2.imwrite(filename, frame)
                print(f"   💾 Frame salvo como '{filename}'")
                
                # Mostrar frame em janela
                print("   🖼️  Mostrando frame em janela...")
                print("   💡 Pressione qualquer tecla para fechar a janela")
                
                cv2.imshow(f'Camera {camera_index} Test', frame)
                cv2.waitKey(0)
                cv2.destroyAllWindows()
                
                cap.release()
                return True
                
            else:
                print(f"   ❌ Erro ao capturar frame da câmera {camera_index}")
                cap.release()
                
        except Exception as e:
            print(f"   ❌ Erro com câmera {camera_index}: {e}")
            if 'cap' in locals():
                cap.release()
    
    return False

def main():
    """Função principal."""
    print("🚀 Teste Simples de Câmera")
    print("=" * 40)
    
    print("💡 Este teste vai:")
    print("   1. Tentar abrir a câmera")
    print("   2. Solicitar permissão se necessário")
    print("   3. Capturar um frame")
    print("   4. Mostrar o frame em uma janela")
    print("   5. Salvar o frame como imagem")
    
    print("\n🔐 IMPORTANTE: Se aparecer um popup de permissão de câmera,")
    print("   CLIQUE EM 'PERMITIR' para o Terminal/Python")
    
    input("\n⏳ Pressione ENTER para continuar...")
    
    if test_camera_simple():
        print("\n✅ Teste da câmera bem-sucedido!")
        print("💡 Agora você pode executar o teste de detecção de gaze")
    else:
        print("\n❌ Teste da câmera falhou")
        print("💡 Verifique as permissões de câmera nas Preferências do Sistema")

if __name__ == "__main__":
    main()
