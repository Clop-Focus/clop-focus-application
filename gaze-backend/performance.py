"""
Módulo de performance e profiling para diagnóstico de gargalos.
Inclui timers, métricas e middleware para monitoramento.
"""

import time
import functools
import threading
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, field
from collections import defaultdict, deque
import statistics
import os
from contextlib import contextmanager

@dataclass
class PerformanceMetrics:
    """Métricas de performance para uma operação."""
    operation: str
    total_calls: int = 0
    total_time: float = 0.0
    min_time: float = float('inf')
    max_time: float = 0.0
    times: deque = field(default_factory=lambda: deque(maxlen=1000))  # Últimos 1000 tempos
    
    @property
    def avg_time(self) -> float:
        """Tempo médio da operação."""
        return self.total_time / self.total_calls if self.total_calls > 0 else 0.0
    
    @property
    def median_time(self) -> float:
        """Tempo mediano da operação."""
        return statistics.median(self.times) if self.times else 0.0
    
    @property
    def p95_time(self) -> float:
        """Percentil 95 do tempo."""
        if not self.times:
            return 0.0
        sorted_times = sorted(self.times)
        index = int(0.95 * len(sorted_times))
        return sorted_times[index]
    
    def add_time(self, execution_time: float):
        """Adiciona um tempo de execução."""
        self.total_calls += 1
        self.total_time += execution_time
        self.min_time = min(self.min_time, execution_time)
        self.max_time = max(self.max_time, execution_time)
        self.times.append(execution_time)
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário para serialização."""
        return {
            "operation": self.operation,
            "total_calls": self.total_calls,
            "total_time": self.total_time,
            "avg_time": self.avg_time,
            "min_time": self.min_time,
            "max_time": self.max_time,
            "median_time": self.median_time,
            "p95_time": self.p95_time,
            "recent_samples": len(self.times)
        }


class PerformanceMonitor:
    """Monitor de performance global da aplicação."""
    
    def __init__(self):
        self.metrics: Dict[str, PerformanceMetrics] = defaultdict(PerformanceMetrics)
        self.lock = threading.Lock()
        self.start_time = time.time()
    
    def get_metrics(self, operation: str) -> PerformanceMetrics:
        """Obtém ou cria métricas para uma operação."""
        with self.lock:
            if operation not in self.metrics:
                self.metrics[operation] = PerformanceMetrics(operation)
            return self.metrics[operation]
    
    def record_time(self, operation: str, execution_time: float):
        """Registra tempo de execução de uma operação."""
        metrics = self.get_metrics(operation)
        metrics.add_time(execution_time)
    
    @contextmanager
    def timer(self, operation: str):
        """Context manager para medir tempo de execução."""
        start_time = time.time()
        try:
            yield
        finally:
            execution_time = time.time() - start_time
            self.record_time(operation, execution_time)
    
    def time_function(self, operation: str):
        """Decorator para medir tempo de função."""
        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                with self.timer(operation):
                    return func(*args, **kwargs)
            return wrapper
        return decorator
    
    def get_all_metrics(self) -> Dict[str, Dict[str, Any]]:
        """Obtém todas as métricas em formato serializável."""
        with self.lock:
            return {
                operation: metrics.to_dict() 
                for operation, metrics in self.metrics.items()
            }
    
    def get_summary(self) -> Dict[str, Any]:
        """Obtém resumo das métricas."""
        all_metrics = self.get_all_metrics()
        total_operations = sum(m["total_calls"] for m in all_metrics.values())
        total_time = sum(m["total_time"] for m in all_metrics.values())
        
        return {
            "uptime_seconds": time.time() - self.start_time,
            "total_operations": total_operations,
            "total_time": total_time,
            "operations": all_metrics
        }
    
    def reset_metrics(self):
        """Reseta todas as métricas."""
        with self.lock:
            self.metrics.clear()
            self.start_time = time.time()


# Instância global do monitor
performance_monitor = PerformanceMonitor()


def timer(operation: str):
    """Decorator global para medir performance de funções."""
    return performance_monitor.time_function(operation)


@contextmanager
def performance_timer(operation: str):
    """Context manager global para medir performance."""
    with performance_monitor.timer(operation):
        yield


class PerformanceMiddleware:
    """Middleware FastAPI para medir latência de requests."""
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            start_time = time.time()
            
            # Wrapper para capturar tempo de resposta
            async def send_wrapper(message):
                if message["type"] == "http.response.body":
                    execution_time = time.time() - start_time
                    path = scope.get("path", "unknown")
                    method = scope.get("method", "unknown")
                    operation = f"{method}_{path}"
                    performance_monitor.record_time(operation, execution_time)
                
                await send(message)
            
            await self.app(scope, receive, send_wrapper)
        else:
            await self.app(scope, receive, send)


def get_performance_metrics() -> Dict[str, Any]:
    """Endpoint helper para obter métricas de performance."""
    return performance_monitor.get_summary()


def reset_performance_metrics():
    """Reseta métricas de performance."""
    performance_monitor.reset_metrics()
