#!/usr/bin/env python3
"""
Cliente de teste para o WebSocket de gaze detection usando imagem real.
"""

import asyncio
import websockets
import base64
import json
import time
import os

async def test_gaze_websocket_real():
    """Testa o WebSocket com imagem real."""
    
    # URL do WebSocket
    uri = "ws://localhost:8000/gaze/ws/test_session_real"
    
    print(f"🔌 Conectando ao WebSocket: {uri}")
    
    try:
        async with websockets.connect(uri) as websocket:
            print("✅ Conectado ao WebSocket!")
            
            # Carregar imagem real que tem rosto
            image_path = "test_frame_camera1.jpg"
            if not os.path.exists(image_path):
                print(f"❌ Imagem não encontrada: {image_path}")
                return
            
            print(f"📸 Carregando imagem: {image_path}")
            
            # Ler e converter para base64
            with open(image_path, "rb") as f:
                image_bytes = f.read()
                frame_base64 = base64.b64encode(image_bytes).decode('utf-8')
            
            print(f"📤 Enviando frame real ({len(frame_base64)} bytes)...")
            
            # Enviar frame
            message = {
                "type": "frame",
                "data": frame_base64,
                "timestamp": time.time()
            }
            
            await websocket.send(json.dumps(message))
            print("📤 Frame enviado!")
            
            # Aguardar resposta
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                data = json.loads(response)
                print(f"📥 Resposta recebida:")
                print(f"   - Tipo: {data.get('type', 'N/A')}")
                print(f"   - Gaze H: {data.get('gaze', {}).get('h', 'N/A')}")
                print(f"   - Gaze V: {data.get('gaze', {}).get('v', 'N/A')}")
                print(f"   - Attention: {data.get('attention', 'N/A')}")
                print(f"   - On Screen: {data.get('on_screen', 'N/A')}")
                
                # Verificar se é um alerta de perda de foco
                if data.get("type") == "focus_alert":
                    print(f"🚨 ALERTA DE PERDA DE FOCO: {data}")
                
            except asyncio.TimeoutError:
                print("⏰ Timeout aguardando resposta")
            
            print("\n✅ Teste concluído!")
            
    except Exception as e:
        print(f"❌ Erro na conexão WebSocket: {e}")

if __name__ == "__main__":
    print("🧪 Iniciando teste do WebSocket com imagem real...")
    asyncio.run(test_gaze_websocket_real())
