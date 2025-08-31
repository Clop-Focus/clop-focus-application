"""
Servidor WebSocket otimizado para streaming de gaze em tempo real.
Integra com o frontend ClopFocus para monitoramento de atenção.
"""

import asyncio
import json
import base64
import cv2
import numpy as np
from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, List, Optional
import time
import logging
from dataclasses import dataclass

# Importar módulos otimizados
from gaze_optimized import infer_gaze_optimized
from performance import timer, performance_timer

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class GazeSession:
    """Sessão de monitoramento de gaze."""
    session_id: str
    websocket: WebSocket
    start_time: float
    last_gaze_time: float
    attention_history: List[float]
    focus_loss_count: int
    is_active: bool

class GazeWebSocketManager:
    """Gerenciador de conexões WebSocket para gaze."""
    
    def __init__(self):
        self.active_connections: Dict[str, GazeSession] = {}
        self.gaze_cache: Dict[str, Dict] = {}
        self.focus_thresholds = {
            "attention_min": 0.4,      # Atenção mínima para considerar focado
            "gaze_center_threshold": 0.6,  # Threshold para considerar olhando para tela
            "focus_loss_timeout": 3.0,     # Tempo em segundos para considerar perda de foco
            "notification_cooldown": 10.0  # Cooldown entre notificações (segundos)
        }
    
    async def connect(self, websocket: WebSocket, session_id: str):
        """Conecta um novo cliente WebSocket."""
        await websocket.accept()
        
        session = GazeSession(
            session_id=session_id,
            websocket=websocket,
            start_time=time.time(),
            last_gaze_time=time.time(),
            attention_history=[],
            focus_loss_count=0,
            is_active=True
        )
        
        self.active_connections[session_id] = session
        logger.info(f"🔗 Cliente conectado: {session_id}")
        
        # Enviar confirmação de conexão
        await websocket.send_json({
            "type": "connection",
            "status": "connected",
            "session_id": session_id,
            "focus_thresholds": self.focus_thresholds
        })
    
    def disconnect(self, session_id: str):
        """Desconecta um cliente."""
        if session_id in self.active_connections:
            session = self.active_connections[session_id]
            session.is_active = False
            del self.active_connections[session_id]
            logger.info(f"🔌 Cliente desconectado: {session_id}")
    
    async def process_gaze_frame(self, session_id: str, frame_data: str) -> Optional[Dict]:
        """
        Processa frame de gaze e retorna resultado com análise de foco.
        
        Args:
            session_id: ID da sessão
            frame_data: Frame em base64
            
        Returns:
            Resultado do gaze com análise de foco
        """
        try:
            # Decodificar frame base64
            with performance_timer("base64_decode"):
                image_bytes = base64.b64decode(frame_data)
            
            # Processar gaze
            with performance_timer("gaze_inference"):
                gaze_result = infer_gaze_optimized(image_bytes)
            
            if not gaze_result.get("ok"):
                return None
            
            # Analisar foco e atenção
            focus_analysis = self._analyze_focus(session_id, gaze_result)
            
            # Combinar resultado com análise de foco
            result = {
                "type": "gaze",
                "timestamp": time.time(),
                "session_id": session_id,
                "gaze": gaze_result.get("gaze", {}),
                "attention": gaze_result.get("attention", 0),
                "on_screen": gaze_result.get("on_screen", False),
                "focus_analysis": focus_analysis,
                "performance": {
                    "optimized": True,
                    "version": "2.0.0"
                }
            }
            
            # Cache do resultado
            self.gaze_cache[session_id] = result
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Erro ao processar frame: {e}")
            return None
    
    def _analyze_focus(self, session_id: str, gaze_result: Dict) -> Dict:
        """
        Analisa o nível de foco baseado no gaze e atenção.
        
        Args:
            session_id: ID da sessão
            gaze_result: Resultado da inferência de gaze
            
        Returns:
            Análise de foco com métricas
        """
        if session_id not in self.active_connections:
            return {"status": "unknown", "focus_score": 0.0}
        
        session = self.active_connections[session_id]
        current_time = time.time()
        
        # Extrair métricas
        attention = gaze_result.get("attention", 0)
        on_screen = gaze_result.get("on_screen", False)
        gaze = gaze_result.get("gaze", {})
        
        # Calcular score de foco (0-100)
        focus_score = 0.0
        
        if on_screen:
            focus_score += 40  # Base por estar olhando para tela
        
        focus_score += attention * 40  # Atenção contribui para o score
        
        # Bônus por estar no centro da tela
        h, v = abs(gaze.get("h", 0)), abs(gaze.get("v", 0))
        if h < 0.3 and v < 0.3:
            focus_score += 20  # Bônus por estar no centro
        
        focus_score = min(100.0, focus_score)
        
        # Atualizar histórico de atenção
        session.attention_history.append(attention)
        if len(session.attention_history) > 30:  # Manter últimos 30 valores
            session.attention_history.pop(0)
        
        # Calcular tendência de atenção
        attention_trend = 0.0
        if len(session.attention_history) >= 5:
            recent_avg = sum(session.attention_history[-5:]) / 5
            older_avg = sum(session.attention_history[:-5]) / (len(session.attention_history) - 5)
            attention_trend = recent_avg - older_avg
        
        # Determinar status do foco
        focus_status = "focused"
        focus_loss_detected = False
        
        if focus_score < 30:
            focus_status = "distracted"
        elif focus_score < 60:
            focus_status = "wavering"
        
        # Detectar perda de foco
        if focus_score < 20 and on_screen:
            time_since_last_gaze = current_time - session.last_gaze_time
            
            if time_since_last_gaze > self.focus_thresholds["focus_loss_timeout"]:
                focus_loss_detected = True
                session.focus_loss_count += 1
                
                # Verificar cooldown para notificação
                time_since_last_notification = current_time - getattr(session, 'last_notification_time', 0)
                if time_since_last_notification > self.focus_thresholds["notification_cooldown"]:
                    session.last_notification_time = current_time
                    focus_status = "focus_lost"
        
        # Atualizar tempo do último gaze
        if on_screen:
            session.last_gaze_time = current_time
        
        return {
            "status": focus_status,
            "focus_score": focus_score,
            "attention_trend": attention_trend,
            "focus_loss_detected": focus_loss_detected,
            "focus_loss_count": session.focus_loss_count,
            "attention_history_length": len(session.attention_history),
            "time_since_last_gaze": current_time - session.last_gaze_time
        }
    
    async def broadcast_gaze_update(self, session_id: str, gaze_data: Dict):
        """Envia atualização de gaze para o cliente específico."""
        if session_id in self.active_connections:
            session = self.active_connections[session_id]
            if session.is_active:
                try:
                    await session.websocket.send_json(gaze_data)
                except Exception as e:
                    logger.error(f"❌ Erro ao enviar para {session_id}: {e}")
                    self.disconnect(session_id)
    
    async def send_focus_alert(self, session_id: str, alert_type: str, data: Dict):
        """Envia alerta de foco para o cliente."""
        alert_message = {
            "type": "focus_alert",
            "alert_type": alert_type,
            "timestamp": time.time(),
            "session_id": session_id,
            "data": data
        }
        
        await self.broadcast_gaze_update(session_id, alert_message)
    
    def get_session_stats(self, session_id: str) -> Optional[Dict]:
        """Obtém estatísticas de uma sessão."""
        if session_id in self.active_connections:
            session = self.active_connections[session_id]
            return {
                "session_id": session_id,
                "uptime": time.time() - session.start_time,
                "focus_loss_count": session.focus_loss_count,
                "attention_history_length": len(session.attention_history),
                "is_active": session.is_active
            }
        return None
    
    def get_all_stats(self) -> Dict:
        """Obtém estatísticas de todas as sessões."""
        return {
            "total_connections": len(self.active_connections),
            "active_connections": len([s for s in self.active_connections.values() if s.is_active]),
            "sessions": {
                session_id: self.get_session_stats(session_id)
                for session_id in self.active_connections.keys()
            }
        }

# Instância global do gerenciador
gaze_manager = GazeWebSocketManager()

async def gaze_websocket_endpoint(websocket: WebSocket, session_id: str):
    """
    Endpoint WebSocket para streaming de gaze em tempo real.
    
    Args:
        websocket: Conexão WebSocket
        session_id: ID único da sessão
    """
    await gaze_manager.connect(websocket, session_id)
    
    try:
        while True:
            # Receber mensagem do cliente
            message = await websocket.receive_text()
            data = json.loads(message)
            
            if data.get("type") == "frame":
                # Processar frame de gaze
                frame_data = data.get("data", "")
                
                if frame_data:
                    # Processar gaze
                    gaze_result = await gaze_manager.process_gaze_frame(session_id, frame_data)
                    
                    if gaze_result:
                        # Enviar resultado para o cliente
                        await gaze_manager.broadcast_gaze_update(session_id, gaze_result)
                        
                        # Verificar se precisa enviar alerta de foco
                        focus_analysis = gaze_result.get("focus_analysis", {})
                        
                        if focus_analysis.get("focus_loss_detected"):
                            await gaze_manager.send_focus_alert(
                                session_id,
                                "focus_loss",
                                {
                                    "focus_score": focus_analysis.get("focus_score", 0),
                                    "attention": gaze_result.get("attention", 0),
                                    "focus_loss_count": focus_analysis.get("focus_loss_count", 0)
                                }
                            )
                
            elif data.get("type") == "ping":
                # Responder ping
                await websocket.send_json({
                    "type": "pong",
                    "timestamp": time.time()
                })
                
            elif data.get("type") == "get_stats":
                # Enviar estatísticas da sessão
                stats = gaze_manager.get_session_stats(session_id)
                await websocket.send_json({
                    "type": "stats",
                    "data": stats
                })
    
    except WebSocketDisconnect:
        logger.info(f"🔌 WebSocket desconectado: {session_id}")
    except Exception as e:
        logger.error(f"❌ Erro no WebSocket {session_id}: {e}")
    finally:
        gaze_manager.disconnect(session_id)

# Funções auxiliares para integração
def get_gaze_manager():
    """Obtém a instância global do gerenciador de gaze."""
    return gaze_manager

def get_active_sessions_count():
    """Obtém o número de sessões ativas."""
    return len([s for s in gaze_manager.active_connections.values() if s.is_active])

def get_session_focus_stats(session_id: str):
    """Obtém estatísticas de foco de uma sessão específica."""
    return gaze_manager.get_session_stats(session_id)
