#!/usr/bin/env python3
"""
Exemplo de cliente Python para testar a API Gaze Backend.
Demonstra como usar os endpoints /gaze e /calibrate.
"""

import requests
import json
import base64
import cv2
import time
from typing import Dict, Any

class GazeClient:
    """Cliente para API Gaze Backend."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session_id = f"test_session_{int(time.time())}"
        
    def health_check(self) -> Dict[str, Any]:
        """Verifica saúde da API."""
        try:
            response = requests.get(f"{self.base_url}/health")
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"❌ Erro no health check: {e}")
            return {}
    
    def capture_frame(self) -> bytes:
        """Captura frame da webcam."""
        try:
            cap = cv2.VideoCapture(0)
            if not cap.isOpened():
                raise Exception("Não foi possível abrir a webcam")
            
            ret, frame = cap.read()
            cap.release()
            
            if not ret:
                raise Exception("Não foi possível capturar frame")
            
            # Converter para JPEG
            _, buffer = cv2.imencode('.jpg', frame)
            return buffer.tobytes()
            
        except Exception as e:
            print(f"❌ Erro ao capturar frame: {e}")
            return b""
    
    def calibrate(self, frame_bytes: bytes) -> Dict[str, Any]:
        """Calibra o sistema de gaze."""
        try:
            files = {"frame": ("frame.jpg", frame_bytes, "image/jpeg")}
            data = {"label": "center", "session_id": self.session_id}
            
            response = requests.post(
                f"{self.base_url}/calibrate",
                files=files,
                data=data
            )
            response.raise_for_status()
            
            result = response.json()
            print(f"✅ Calibração realizada: {result}")
            return result
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Erro na calibração: {e}")
            return {}
    
    def process_gaze(self, frame_bytes: bytes) -> Dict[str, Any]:
        """Processa frame para estimar gaze."""
        try:
            files = {"frame": ("frame.jpg", frame_bytes, "image/jpeg")}
            data = {"session_id": self.session_id}
            
            response = requests.post(
                f"{self.base_url}/gaze",
                files=files,
                data=data
            )
            response.raise_for_status()
            
            result = response.json()
            return result
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Erro no processamento de gaze: {e}")
            return {}
    
    def run_demo(self, duration_seconds: int = 30):
        """Executa demonstração da API."""
        print(f"🚀 Iniciando demonstração da API Gaze Backend")
        print(f"📍 URL: {self.base_url}")
        print(f"🆔 Session ID: {self.session_id}")
        print(f"⏱️  Duração: {duration_seconds} segundos")
        print("-" * 50)
        
        # Health check
        health = self.health_check()
        if not health:
            print("❌ API não está respondendo. Verifique se o servidor está rodando.")
            return
        
        print(f"✅ API está funcionando: {health}")
        
        # Calibração inicial
        print("\n🎯 Realizando calibração inicial...")
        frame = self.capture_frame()
        if not frame:
            print("❌ Falha ao capturar frame para calibração")
            return
        
        calibration = self.calibrate(frame)
        if not calibration.get("ok"):
            print("❌ Falha na calibração")
            return
        
        print("✅ Calibração concluída!")
        
        # Loop de processamento
        print(f"\n📹 Processando frames por {duration_seconds} segundos...")
        print("💡 Olhe para diferentes direções da tela")
        print("⏹️  Pressione Ctrl+C para parar")
        
        start_time = time.time()
        frame_count = 0
        
        try:
            while time.time() - start_time < duration_seconds:
                frame = self.capture_frame()
                if not frame:
                    continue
                
                result = self.process_gaze(frame)
                frame_count += 1
                
                if "error" in result:
                    print(f"❌ Frame {frame_count}: {result['message']}")
                else:
                    gaze = result["gaze"]
                    attention = result["attention"]
                    on_screen = result["on_screen"]
                    
                    # Emojis para direção
                    h_emoji = "⬅️" if gaze["h"] < -0.3 else "➡️" if gaze["h"] > 0.3 else "⬆️"
                    v_emoji = "⬇️" if gaze["v"] < -0.3 else "⬆️" if gaze["v"] > 0.3 else "⬆️"
                    screen_emoji = "👀" if on_screen else "😴"
                    
                    print(f"📊 Frame {frame_count:3d} | "
                          f"H: {gaze['h']:6.2f} {h_emoji} | "
                          f"V: {gaze['v']:6.2f} {v_emoji} | "
                          f"At: {attention:4.2f} | "
                          f"Screen: {screen_emoji}")
                
                time.sleep(0.5)  # 2 FPS para demonstração
                
        except KeyboardInterrupt:
            print("\n⏹️  Demonstração interrompida pelo usuário")
        
        elapsed = time.time() - start_time
        fps = frame_count / elapsed if elapsed > 0 else 0
        
        print(f"\n📈 Estatísticas da demonstração:")
        print(f"   Frames processados: {frame_count}")
        print(f"   Tempo total: {elapsed:.1f}s")
        print(f"   FPS médio: {fps:.1f}")
        print(f"   Session ID: {self.session_id}")
        print("✅ Demonstração concluída!")


def main():
    """Função principal."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Cliente de exemplo para Gaze Backend")
    parser.add_argument(
        "--url",
        default="http://localhost:8000",
        help="URL base da API (default: http://localhost:8000)"
    )
    parser.add_argument(
        "--duration",
        type=int,
        default=30,
        help="Duração da demonstração em segundos (default: 30)"
    )
    
    args = parser.parse_args()
    
    client = GazeClient(args.url)
    client.run_demo(args.duration)


if __name__ == "__main__":
    main()
