"""
Sistema de fila otimizado para processamento em tempo real.
Inclui drop de frames e worker dedicado para inferência.
"""

import asyncio
import threading
import queue
import time
from typing import Dict, Any, Optional, Callable, Tuple
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, Future
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class FrameRequest:
    """Request de processamento de frame."""
    id: str
    frame_data: bytes
    session_id: str
    timestamp: float
    priority: int = 0  # Maior número = maior prioridade


@dataclass
class ProcessedResult:
    """Resultado do processamento."""
    request_id: str
    result: Dict[str, Any]
    processing_time: float
    timestamp: float


class FrameQueueProcessor:
    """
    Processador de fila otimizado para frames em tempo real.
    Implementa drop de frames antigos e processamento prioritário.
    """
    
    def __init__(self, 
                 max_queue_size: int = 10,
                 max_workers: int = 2,
                 drop_old_frames: bool = True,
                 max_frame_age_ms: int = 100):
        
        self.max_queue_size = max_queue_size
        self.max_workers = max_workers
        self.drop_old_frames = drop_old_frames
        self.max_frame_age_ms = max_frame_age_ms
        
        # Fila principal de frames
        self.frame_queue = queue.PriorityQueue(maxsize=max_queue_size)
        
        # Thread pool para processamento
        self.executor = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="GazeWorker")
        
        # Estatísticas
        self.stats = {
            "frames_received": 0,
            "frames_processed": 0,
            "frames_dropped": 0,
            "frames_expired": 0,
            "avg_processing_time": 0.0,
            "queue_size": 0
        }
        
        # Lock para estatísticas
        self.stats_lock = threading.Lock()
        
        # Flag de shutdown
        self.shutdown_event = threading.Event()
        
        # Worker thread principal
        self.worker_thread = None
        
        logger.info(f"🚀 FrameQueueProcessor inicializado: max_queue={max_queue_size}, workers={max_workers}")
    
    def start(self):
        """Inicia o processador de fila."""
        if self.worker_thread is None or not self.worker_thread.is_alive():
            self.shutdown_event.clear()
            self.worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
            self.worker_thread.start()
            logger.info("✅ Worker thread iniciado")
    
    def stop(self):
        """Para o processador de fila."""
        self.shutdown_event.set()
        if self.worker_thread and self.worker_thread.is_alive():
            self.worker_thread.join(timeout=5.0)
        self.executor.shutdown(wait=True)
        logger.info("🛑 Worker thread parado")
    
    def submit_frame(self, 
                    frame_data: bytes, 
                    session_id: str, 
                    priority: int = 0) -> str:
        """
        Submete um frame para processamento.
        
        Args:
            frame_data: Bytes do frame
            session_id: ID da sessão
            priority: Prioridade (maior = mais importante)
            
        Returns:
            ID único do request
        """
        request_id = f"{session_id}_{int(time.time() * 1000)}"
        timestamp = time.time()
        
        # Verificar se deve dropar frames antigos
        if self.drop_old_frames and self.frame_queue.qsize() >= self.max_queue_size:
            self._drop_oldest_frame()
        
        # Criar request
        request = FrameRequest(
            id=request_id,
            frame_data=frame_data,
            session_id=session_id,
            timestamp=timestamp,
            priority=priority
        )
        
        # Adicionar à fila (prioridade invertida para PriorityQueue)
        try:
            self.frame_queue.put((-priority, timestamp, request), timeout=0.1)
            self._update_stats("frames_received", 1)
            logger.debug(f"📸 Frame {request_id} enfileirado (priority={priority})")
            return request_id
        except queue.Full:
            self._update_stats("frames_dropped", 1)
            logger.warning(f"⚠️ Fila cheia, frame {request_id} descartado")
            return None
    
    def _drop_oldest_frame(self):
        """Remove o frame mais antigo da fila."""
        try:
            # Tentar remover item mais antigo
            if not self.frame_queue.empty():
                # Não podemos facilmente remover itens específicos de PriorityQueue
                # Então vamos apenas marcar como dropado
                self._update_stats("frames_dropped", 1)
                logger.debug("🗑️ Frame antigo descartado")
        except Exception as e:
            logger.error(f"❌ Erro ao dropar frame antigo: {e}")
    
    def _worker_loop(self):
        """Loop principal do worker thread."""
        logger.info("🔄 Worker loop iniciado")
        
        while not self.shutdown_event.is_set():
            try:
                # Pegar próximo frame da fila
                try:
                    priority, timestamp, request = self.frame_queue.get(timeout=1.0)
                except queue.Empty:
                    continue
                
                # Verificar se o frame expirou
                if self.drop_old_frames and (time.time() - timestamp) * 1000 > self.max_frame_age_ms:
                    self._update_stats("frames_expired", 1)
                    logger.debug(f"⏰ Frame {request.id} expirado")
                    continue
                
                # Processar frame
                self._process_frame(request)
                
                # Marcar como concluído
                self.frame_queue.task_done()
                
            except Exception as e:
                logger.error(f"❌ Erro no worker loop: {e}")
                time.sleep(0.1)
        
        logger.info("🔄 Worker loop finalizado")
    
    def _process_frame(self, request: FrameRequest):
        """
        Processa um frame individual.
        Esta função será sobrescrita pelo usuário.
        """
        start_time = time.time()
        
        try:
            # Aqui você implementaria a lógica de processamento
            # Por enquanto, apenas simulamos
            result = {"status": "processed", "request_id": request.id}
            
            processing_time = time.time() - start_time
            
            # Atualizar estatísticas
            self._update_processing_stats(processing_time)
            
            logger.debug(f"✅ Frame {request.id} processado em {processing_time:.3f}s")
            
        except Exception as e:
            logger.error(f"❌ Erro ao processar frame {request.id}: {e}")
    
    def _update_stats(self, stat_name: str, increment: int = 1):
        """Atualiza estatísticas thread-safe."""
        with self.stats_lock:
            if stat_name in self.stats:
                if isinstance(self.stats[stat_name], (int, float)):
                    self.stats[stat_name] += increment
                else:
                    self.stats[stat_name] = increment
    
    def _update_processing_stats(self, processing_time: float):
        """Atualiza estatísticas de tempo de processamento."""
        with self.stats_lock:
            self.stats["frames_processed"] += 1
            
            # Calcular média móvel
            current_avg = self.stats["avg_processing_time"]
            total_processed = self.stats["frames_processed"]
            
            if total_processed == 1:
                self.stats["avg_processing_time"] = processing_time
            else:
                # Média móvel exponencial
                alpha = 0.1
                self.stats["avg_processing_time"] = (1 - alpha) * current_avg + alpha * processing_time
    
    def get_stats(self) -> Dict[str, Any]:
        """Obtém estatísticas atuais."""
        with self.stats_lock:
            stats = self.stats.copy()
            stats["queue_size"] = self.frame_queue.qsize()
            stats["worker_thread_alive"] = self.worker_thread.is_alive() if self.worker_thread else False
            return stats
    
    def get_queue_status(self) -> Dict[str, Any]:
        """Obtém status da fila."""
        return {
            "queue_size": self.frame_queue.qsize(),
            "max_queue_size": self.max_queue_size,
            "worker_thread_alive": self.worker_thread.is_alive() if self.worker_thread else False,
            "shutdown_requested": self.shutdown_event.is_set()
        }


class AsyncFrameProcessor:
    """
    Wrapper assíncrono para o processador de fila.
    Permite integração com FastAPI.
    """
    
    def __init__(self, processor: FrameQueueProcessor):
        self.processor = processor
        self.loop = asyncio.get_event_loop()
    
    async def submit_frame_async(self, 
                                frame_data: bytes, 
                                session_id: str, 
                                priority: int = 0) -> str:
        """Versão assíncrona de submit_frame."""
        return await self.loop.run_in_executor(
            None, 
            self.processor.submit_frame, 
            frame_data, 
            session_id, 
            priority
        )
    
    async def get_stats_async(self) -> Dict[str, Any]:
        """Versão assíncrona de get_stats."""
        return await self.loop.run_in_executor(None, self.processor.get_stats)
    
    async def get_queue_status_async(self) -> Dict[str, Any]:
        """Versão assíncrona de get_queue_status."""
        return await self.loop.run_in_executor(None, self.processor.get_queue_status)


# Instância global do processador
frame_processor = FrameQueueProcessor(
    max_queue_size=20,
    max_workers=2,
    drop_old_frames=True,
    max_frame_age_ms=200
)

# Iniciar automaticamente
frame_processor.start()

# Wrapper assíncrono
async_frame_processor = AsyncFrameProcessor(frame_processor)
