"""
Módulo WebSocket para processamento de frames em tempo real.
Recebe frames base64 e retorna resultados de gaze com debounce para ~15 FPS.
"""

import json
import base64
import asyncio
import time
from typing import Dict, Any
from fastapi import WebSocket, WebSocketDisconnect
from gaze import process_base64_frame
from calibration import apply_offsets


class WebSocketManager:
    """Gerencia conexões WebSocket e aplica debounce para controle de FPS."""
    
    def __init__(self, max_fps: int = 15):
        self.max_fps = max_fps
        self.min_interval = 1.0 / max_fps  # Tempo mínimo entre frames
        self.last_frame_time = 0.0
        self.active_connections: list[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        """Aceita nova conexão WebSocket."""
        await websocket.accept()
        self.active_connections.append(websocket)
        print(f"WebSocket conectado. Total de conexões: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        """Remove conexão WebSocket."""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            print(f"WebSocket desconectado. Total de conexões: {len(self.active_connections)}")
    
    def should_process_frame(self) -> bool:
        """
        Verifica se deve processar o frame atual baseado no FPS máximo.
        
        Returns:
            True se deve processar, False se deve pular
        """
        current_time = time.time()
        if current_time - self.last_frame_time >= self.min_interval:
            self.last_frame_time = current_time
            return True
        return False
    
    async def send_gaze_result(self, websocket: WebSocket, result: Dict[str, Any]):
        """
        Envia resultado de gaze para o cliente WebSocket.
        
        Args:
            websocket: Conexão WebSocket
            result: Resultado da inferência de gaze
        """
        try:
            message = {
                "type": "gaze",
                "data": result
            }
            await websocket.send_text(json.dumps(message))
        except Exception as e:
            print(f"Erro ao enviar resultado: {e}")
            # Marcar conexão para desconexão
            self.disconnect(websocket)
    
    async def send_error(self, websocket: WebSocket, error_message: str):
        """
        Envia mensagem de erro para o cliente WebSocket.
        
        Args:
            websocket: Conexão WebSocket
            error_message: Mensagem de erro
        """
        try:
            message = {
                "type": "error",
                "data": {"message": error_message}
            }
            await websocket.send_text(json.dumps(message))
        except Exception as e:
            print(f"Erro ao enviar erro: {e}")
            self.disconnect(websocket)


# Instância global do gerenciador WebSocket
ws_manager = WebSocketManager(max_fps=15)


async def stream_ws(websocket: WebSocket):
    """
    Handler principal para WebSocket de streaming.
    
    Args:
        websocket: Conexão WebSocket aceita
    """
    await ws_manager.connect(websocket)
    
    try:
        while True:
            # Receber mensagem do cliente
            message = await websocket.receive_text()
            
            try:
                data = json.loads(message)
                message_type = data.get("type")
                
                if message_type == "frame":
                    await _handle_frame_message(websocket, data)
                elif message_type == "ping":
                    # Responder pong para manter conexão ativa
                    await websocket.send_text(json.dumps({"type": "pong"}))
                else:
                    await ws_manager.send_error(websocket, f"Tipo de mensagem desconhecido: {message_type}")
                    
            except json.JSONDecodeError:
                await ws_manager.send_error(websocket, "Mensagem JSON inválida")
            except Exception as e:
                await ws_manager.send_error(websocket, f"Erro interno: {str(e)}")
                
    except WebSocketDisconnect:
        print("WebSocket desconectado pelo cliente")
    except Exception as e:
        print(f"Erro no WebSocket: {e}")
    finally:
        ws_manager.disconnect(websocket)


async def _handle_frame_message(websocket: WebSocket, data: Dict[str, Any]):
    """
    Processa mensagem de frame do WebSocket.
    
    Args:
        websocket: Conexão WebSocket
        data: Dados da mensagem
    """
    # Verificar se deve processar o frame (debounce)
    if not ws_manager.should_process_frame():
        return
    
    # Extrair dados do frame
    frame_data = data.get("data")
    session_id = data.get("session_id", "default")
    
    if not frame_data:
        await ws_manager.send_error(websocket, "Dados do frame não fornecidos")
        return
    
    try:
        # Processar frame base64
        result = process_base64_frame(frame_data)
        
        # Aplicar calibração se disponível
        if "error" not in result:
            result = apply_offsets(result, session_id)
        
        # Enviar resultado para o cliente
        await ws_manager.send_gaze_result(websocket, result)
        
    except Exception as e:
        await ws_manager.send_error(websocket, f"Erro ao processar frame: {str(e)}")


async def broadcast_gaze_result(result: Dict[str, Any]):
    """
    Envia resultado de gaze para todas as conexões WebSocket ativas.
    Útil para testes ou integração externa.
    
    Args:
        result: Resultado da inferência de gaze
    """
    if not ws_manager.active_connections:
        return
    
    # Criar cópias da lista para evitar problemas durante iteração
    connections = ws_manager.active_connections.copy()
    
    for websocket in connections:
        try:
            await ws_manager.send_gaze_result(websocket, result)
        except Exception as e:
            print(f"Erro ao enviar broadcast: {e}")
            ws_manager.disconnect(websocket)


def get_connection_count() -> int:
    """
    Retorna o número de conexões WebSocket ativas.
    
    Returns:
        Número de conexões ativas
    """
    return len(ws_manager.active_connections)


def get_fps_info() -> Dict[str, Any]:
    """
    Retorna informações sobre o controle de FPS.
    
    Returns:
        Dicionário com informações de FPS
    """
    return {
        "max_fps": ws_manager.max_fps,
        "min_interval": ws_manager.min_interval,
        "last_frame_time": ws_manager.last_frame_time,
        "time_since_last_frame": time.time() - ws_manager.last_frame_time
    }
