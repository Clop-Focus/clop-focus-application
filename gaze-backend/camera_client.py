"""
Cliente de câmera para detecção de gaze em tempo real.
Abre a webcam e envia frames para o backend otimizado.
"""

import cv2
import numpy as np
import requests
import time
import json
from typing import Dict, Any, Optional
import threading
import queue
from dataclasses import dataclass

@dataclass
class GazeResult:
    """Resultado da análise de gaze."""
    horizontal: float  # -1.0 (esquerda) a 1.0 (direita)
    vertical: float    # -1.0 (baixo) a 1.0 (cima)
    attention: float   # 0.0 (distraído) a 1.0 (focado)
    on_screen: bool    # Se está olhando para a tela
    confidence: float  # Confiança da detecção

class GazeCameraClient:
    """
    Cliente que abre a câmera e detecta gaze em tempo real.
    """
    
    def __init__(self, 
                 backend_url: str = "http://localhost:8000",
                 camera_index: int = 0,
                 frame_width: int = 640,
                 frame_height: int = 480,
                 fps: int = 30):
        
        self.backend_url = backend_url
        self.camera_index = camera_index
        self.frame_width = frame_width
        self.frame_height = frame_height
        self.fps = fps
        
        # Controle de execução
        self.running = False
        self.camera = None
        
        # Fila para resultados
        self.result_queue = queue.Queue(maxsize=100)
        
        # Estatísticas
        self.stats = {
            "frames_captured": 0,
            "frames_processed": 0,
            "frames_failed": 0,
            "avg_processing_time": 0.0,
            "last_gaze_result": None
        }
        
        # Thread para processamento
        self.processing_thread = None
        
        print(f"📷 GazeCameraClient inicializado")
        print(f"🔗 Backend: {backend_url}")
        print(f"📐 Resolução: {frame_width}x{frame_height}")
        print(f"🎬 FPS: {fps}")
    
    def start_camera(self) -> bool:
        """Inicia a câmera."""
        try:
            self.camera = cv2.VideoCapture(self.camera_index)
            
            if not self.camera.isOpened():
                print(f"❌ Erro: Não foi possível abrir a câmera {self.camera_index}")
                return False
            
            # Configurar resolução e FPS
            self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, self.frame_width)
            self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, self.frame_height)
            self.camera.set(cv2.CAP_PROP_FPS, self.fps)
            
            # Verificar configurações aplicadas
            actual_width = int(self.camera.get(cv2.CAP_PROP_FRAME_WIDTH))
            actual_height = int(self.camera.get(cv2.CAP_PROP_FRAME_HEIGHT))
            actual_fps = int(self.camera.get(cv2.CAP_PROP_FPS))
            
            print(f"✅ Câmera iniciada com sucesso!")
            print(f"📐 Resolução real: {actual_width}x{actual_height}")
            print(f"🎬 FPS real: {actual_fps}")
            
            return True
            
        except Exception as e:
            print(f"❌ Erro ao iniciar câmera: {e}")
            return False
    
    def stop_camera(self):
        """Para a câmera."""
        self.running = False
        
        if self.processing_thread and self.processing_thread.is_alive():
            self.processing_thread.join(timeout=2.0)
        
        if self.camera:
            self.camera.release()
            self.camera = None
        
        print("🛑 Câmera parada")
    
    def process_frame(self, frame: np.ndarray) -> Optional[GazeResult]:
        """
        Processa um frame enviando para o backend.
        
        Args:
            frame: Frame da câmera em formato numpy array
            
        Returns:
            Resultado da análise de gaze ou None se falhar
        """
        try:
            start_time = time.time()
            
            # Converter frame para JPEG
            _, jpeg_data = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 90])
            
            # Preparar dados para envio
            files = {'frame': ('frame.jpg', jpeg_data.tobytes(), 'image/jpeg')}
            data = {'session_id': 'realtime_session'}
            
            # Enviar para backend
            response = requests.post(
                f"{self.backend_url}/gaze",
                files=files,
                data=data,
                timeout=5.0
            )
            
            if response.status_code == 200:
                result = response.json()
                
                if result.get("ok"):
                    gaze_data = result.get("gaze", {})
                    
                    gaze_result = GazeResult(
                        horizontal=gaze_data.get("h", 0.0),
                        vertical=gaze_data.get("v", 0.0),
                        attention=result.get("attention", 0.0),
                        on_screen=result.get("on_screen", False),
                        confidence=1.0  # MediaPipe não retorna confiança
                    )
                    
                    # Atualizar estatísticas
                    processing_time = time.time() - start_time
                    self._update_stats(processing_time, True)
                    
                    return gaze_result
                else:
                    print(f"⚠️ Backend retornou erro: {result}")
                    self._update_stats(0, False)
                    return None
            else:
                print(f"❌ Erro HTTP {response.status_code}: {response.text}")
                self._update_stats(0, False)
                return None
                
        except requests.exceptions.Timeout:
            print("⏰ Timeout ao processar frame")
            self._update_stats(0, False)
            return None
        except Exception as e:
            print(f"❌ Erro ao processar frame: {e}")
            self._update_stats(0, False)
            return None
    
    def _update_stats(self, processing_time: float, success: bool):
        """Atualiza estatísticas de processamento."""
        self.stats["frames_captured"] += 1
        
        if success:
            self.stats["frames_processed"] += 1
            
            # Calcular média móvel do tempo de processamento
            if self.stats["avg_processing_time"] == 0:
                self.stats["avg_processing_time"] = processing_time
            else:
                alpha = 0.1
                self.stats["avg_processing_time"] = (
                    (1 - alpha) * self.stats["avg_processing_time"] + 
                    alpha * processing_time
                )
        else:
            self.stats["frames_failed"] += 1
    
    def _processing_loop(self):
        """Loop principal de processamento de frames."""
        print("🔄 Loop de processamento iniciado")
        
        while self.running:
            if self.camera and self.camera.isOpened():
                ret, frame = self.camera.read()
                
                if ret:
                    # Processar frame
                    gaze_result = self.process_frame(frame)
                    
                    if gaze_result:
                        # Armazenar resultado na fila
                        try:
                            self.result_queue.put_nowait(gaze_result)
                            self.stats["last_gaze_result"] = gaze_result
                        except queue.Full:
                            # Remover item mais antigo se fila cheia
                            try:
                                self.result_queue.get_nowait()
                                self.result_queue.put_nowait(gaze_result)
                            except queue.Empty:
                                pass
                    
                    # Controlar FPS
                    time.sleep(1.0 / self.fps)
                else:
                    print("⚠️ Erro ao ler frame da câmera")
                    time.sleep(0.1)
            else:
                print("⚠️ Câmera não está disponível")
                time.sleep(0.1)
        
        print("🔄 Loop de processamento finalizado")
    
    def start_processing(self):
        """Inicia o processamento de frames."""
        if not self.camera or not self.camera.isOpened():
            print("❌ Câmera não está disponível")
            return False
        
        self.running = True
        self.processing_thread = threading.Thread(target=self._processing_loop, daemon=True)
        self.processing_thread.start()
        
        print("✅ Processamento de frames iniciado")
        return True
    
    def get_latest_gaze(self) -> Optional[GazeResult]:
        """Obtém o resultado mais recente de gaze."""
        try:
            return self.result_queue.get_nowait()
        except queue.Empty:
            return None
    
    def get_stats(self) -> Dict[str, Any]:
        """Obtém estatísticas atuais."""
        stats = self.stats.copy()
        stats["queue_size"] = self.result_queue.qsize()
        stats["processing_active"] = self.running
        return stats
    
    def run_interactive(self):
        """
        Executa o cliente de forma interativa com visualização.
        """
        if not self.start_camera():
            return
        
        if not self.start_processing():
            return
        
        print("\n🎯 Cliente de Gaze em execução!")
        print("📱 Olhe para a tela para ver a detecção")
        print("⏹️  Pressione 'q' para sair")
        print("📊 Pressione 's' para ver estatísticas")
        print("=" * 50)
        
        try:
            while True:
                # Obter resultado mais recente
                gaze_result = self.get_latest_gaze()
                
                if gaze_result:
                    # Exibir resultado
                    direction = self._get_direction_description(gaze_result)
                    attention_level = self._get_attention_description(gaze_result.attention)
                    
                    print(f"\r👁️  {direction} | 🧠 {attention_level} | 📺 {'Na tela' if gaze_result.on_screen else 'Fora da tela'} | ⏱️  {self.stats['avg_processing_time']:.3f}s", end="", flush=True)
                
                # Verificar teclas
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    break
                elif key == ord('s'):
                    self._print_stats()
                
                time.sleep(0.1)
                
        except KeyboardInterrupt:
            print("\n\n⏹️  Interrompido pelo usuário")
        
        finally:
            self.stop_camera()
            print("✅ Cliente finalizado")
    
    def _get_direction_description(self, gaze_result: GazeResult) -> str:
        """Converte coordenadas de gaze em descrição legível."""
        h, v = gaze_result.horizontal, gaze_result.vertical
        
        # Direção horizontal
        if abs(h) < 0.2:
            h_dir = "Centro"
        elif h < 0:
            h_dir = f"Esquerda ({abs(h):.2f})"
        else:
            h_dir = f"Direita ({h:.2f})"
        
        # Direção vertical
        if abs(v) < 0.2:
            v_dir = "Centro"
        elif v < 0:
            v_dir = f"Baixo ({abs(v):.2f})"
        else:
            v_dir = f"Cima ({v:.2f})"
        
        return f"{h_dir} | {v_dir}"
    
    def _get_attention_description(self, attention: float) -> str:
        """Converte nível de atenção em descrição."""
        if attention >= 0.8:
            return f"Focado ({attention:.2f})"
        elif attention >= 0.6:
            return f"Atento ({attention:.2f})"
        elif attention >= 0.4:
            return f"Distraído ({attention:.2f})"
        else:
            return f"Muito distraído ({attention:.2f})"
    
    def _print_stats(self):
        """Imprime estatísticas atuais."""
        stats = self.get_stats()
        print(f"\n\n📊 ESTATÍSTICAS:")
        print(f"   Frames capturados: {stats['frames_captured']}")
        print(f"   Frames processados: {stats['frames_processed']}")
        print(f"   Frames falharam: {stats['frames_failed']}")
        print(f"   Taxa de sucesso: {stats['frames_processed']/max(stats['frames_captured'], 1)*100:.1f}%")
        print(f"   Tempo médio: {stats['avg_processing_time']:.3f}s")
        print(f"   Tamanho da fila: {stats['queue_size']}")
        print(f"   Processamento ativo: {'Sim' if stats['processing_active'] else 'Não'}")


def main():
    """Função principal para execução do cliente."""
    print("🚀 Iniciando Cliente de Câmera para Gaze Detection")
    print("=" * 60)
    
    # Verificar se backend está rodando
    try:
        response = requests.get("http://localhost:8000/health", timeout=2)
        if response.status_code == 200:
            print("✅ Backend detectado e funcionando")
        else:
            print("⚠️ Backend respondeu mas com erro")
            return
    except requests.exceptions.RequestException:
        print("❌ Erro: Backend não está rodando em http://localhost:8000")
        print("💡 Execute primeiro: uvicorn app_optimized:app --host 0.0.0.0 --port 8000")
        return
    
    # Criar e executar cliente
    client = GazeCameraClient(
        backend_url="http://localhost:8000",
        camera_index=0,
        frame_width=640,
        frame_height=480,
        fps=15  # Reduzir FPS para melhor performance
    )
    
    try:
        client.run_interactive()
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
    finally:
        client.stop_camera()


if __name__ == "__main__":
    main()
