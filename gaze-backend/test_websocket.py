#!/usr/bin/env python3
"""
Cliente de teste para o WebSocket de gaze detection.
Testa a conexão e envia frames para o backend.
"""

import asyncio
import websockets
import base64
import json
import cv2
import time
from PIL import Image
import io

async def test_gaze_websocket():
    """Testa o WebSocket de gaze detection."""
    
    # URL do WebSocket
    uri = "ws://localhost:8000/gaze/ws/test_session_123"
    
    print(f"🔌 Conectando ao WebSocket: {uri}")
    
    try:
        async with websockets.connect(uri) as websocket:
            print("✅ Conectado ao WebSocket!")
            
            # Simular alguns frames de teste
            for i in range(5):
                print(f"\n📸 Enviando frame {i+1}/5...")
                
                # Criar um frame de teste simples (640x480, cor cinza)
                frame = Image.new('RGB', (640, 480), color='gray')
                
                # Converter para base64
                buffer = io.BytesIO()
                frame.save(buffer, format='JPEG', quality=85)
                frame_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
                
                # Enviar frame
                message = {
                    "type": "frame",
                    "data": frame_base64,
                    "timestamp": time.time()
                }
                
                await websocket.send(json.dumps(message))
                print(f"📤 Frame enviado ({len(frame_base64)} bytes)")
                
                # Aguardar resposta
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    data = json.loads(response)
                    print(f"📥 Resposta recebida: {data}")
                    
                    # Verificar se é um alerta de perda de foco
                    if data.get("type") == "focus_alert":
                        print(f"🚨 ALERTA DE PERDA DE FOCO: {data}")
                    
                except asyncio.TimeoutError:
                    print("⏰ Timeout aguardando resposta")
                
                # Aguardar um pouco antes do próximo frame
                await asyncio.sleep(1)
            
            print("\n✅ Teste concluído!")
            
    except Exception as e:
        print(f"❌ Erro na conexão WebSocket: {e}")

if __name__ == "__main__":
    print("🧪 Iniciando teste do WebSocket de gaze...")
    asyncio.run(test_gaze_websocket())
