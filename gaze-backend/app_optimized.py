"""
Aplicação FastAPI otimizada para melhor performance no Mac M1.
Inclui middleware de performance, múltiplos workers e métricas.
"""

from fastapi import FastAPI, File, Form, HTTPException, UploadFile, BackgroundTasks, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import os
import multiprocessing
from typing import Optional, Dict, Any

# Importar módulos otimizados
from gaze_optimized import infer_gaze_optimized, process_base64_frame_optimized
from calibration import set_calibration, get_offsets, apply_offsets
from ws import stream_ws, get_connection_count, get_fps_info
from performance import PerformanceMiddleware, get_performance_metrics, reset_performance_metrics
from queue_processor import async_frame_processor
from gaze_websocket_server import gaze_websocket_endpoint, get_gaze_manager, get_active_sessions_count

# Configurações de performance
CPU_COUNT = os.cpu_count()
RECOMMENDED_WORKERS = min(4, CPU_COUNT) if CPU_COUNT else 1

# Criar aplicação FastAPI otimizada
app = FastAPI(
    title="Gaze Backend - Otimizado",
    description="Backend otimizado para estimação de gaze usando MediaPipe FaceMesh no Mac M1",
    version="2.0.0"
)

# Adicionar middleware de performance
app.add_middleware(PerformanceMiddleware)

# Configurar CORS para desenvolvimento
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Event handlers para startup/shutdown
@app.on_event("startup")
async def startup_event():
    """Evento de inicialização da aplicação."""
    print("🚀 Gaze Backend Otimizado iniciando...")
    print(f"🔧 CPU Count: {CPU_COUNT}")
    print(f"👥 Workers recomendados: {RECOMMENDED_WORKERS}")
    print(f"📊 Performance monitoring ativado")
    print(f"🔄 Frame queue processor ativado")
    print(f"👁️ Gaze WebSocket endpoints ativados")


@app.on_event("shutdown")
async def shutdown_event():
    """Evento de shutdown da aplicação."""
    print("🛑 Gaze Backend Otimizado finalizando...")


@app.get("/health")
async def health_check():
    """
    Endpoint de saúde da aplicação com informações de performance.
    
    Returns:
        Status da aplicação e métricas básicas
    """
    return {
        "status": "ok",
        "version": "2.0.0",
        "optimizations": {
            "performance_monitoring": True,
            "frame_queue_processor": True,
            "mediapipe_singleton": True,
            "recommended_workers": RECOMMENDED_WORKERS,
            "gaze_websocket": True
        }
    }


@app.post("/gaze")
async def process_gaze_optimized(
    frame: UploadFile = File(..., description="Frame da webcam"),
    session_id: str = Form(..., description="ID único da sessão"),
    background_tasks: BackgroundTasks = None
):
    """
    Processa frame da webcam para estimar gaze com otimizações de performance.
    
    Args:
        frame: Arquivo de imagem da webcam
        session_id: ID único da sessão para calibração
        background_tasks: Tarefas em background do FastAPI
        
    Returns:
        Resultado da inferência de gaze com calibração aplicada
    """
    try:
        # Validar tipo de arquivo
        if not frame.content_type or not frame.content_type.startswith("image/"):
            raise HTTPException(
                status_code=400, 
                detail="Arquivo deve ser uma imagem válida"
            )
        
        # Ler bytes da imagem
        image_bytes = await frame.read()
        
        if not image_bytes:
            raise HTTPException(
                status_code=400, 
                detail="Arquivo de imagem vazio"
            )
        
        # Processar imagem com versão otimizada
        result = infer_gaze_optimized(image_bytes)
        
        # Verificar se houve erro na inferência
        if "error" in result:
            return JSONResponse(
                status_code=400,
                content=result
            )
        
        # Aplicar calibração da sessão
        result = apply_offsets(result, session_id)
        
        # Adicionar métricas de performance ao resultado
        result["performance"] = {
            "optimized": True,
            "version": "2.0.0"
        }
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro interno ao processar imagem: {str(e)}"
        )


@app.post("/gaze/queue")
async def submit_frame_to_queue(
    frame: UploadFile = File(..., description="Frame da webcam"),
    session_id: str = Form(..., description="ID único da sessão"),
    priority: int = Form(0, description="Prioridade do frame (0-10)")
):
    """
    Submete frame para processamento em fila otimizada.
    
    Args:
        frame: Arquivo de imagem da webcam
        session_id: ID único da sessão
        priority: Prioridade do frame (0-10)
        
    Returns:
        ID do request enfileirado
    """
    try:
        # Validar tipo de arquivo
        if not frame.content_type or not frame.content_type.startswith("image/"):
            raise HTTPException(
                status_code=400, 
                detail="Arquivo deve ser uma imagem válida"
            )
        
        # Ler bytes da imagem
        image_bytes = await frame.read()
        
        if not image_bytes:
            raise HTTPException(
                status_code=400, 
                detail="Arquivo de imagem vazio"
            )
        
        # Submeter para fila de processamento
        request_id = await async_frame_processor.submit_frame_async(
            frame_data=image_bytes,
            session_id=session_id,
            priority=priority
        )
        
        if request_id is None:
            raise HTTPException(
                status_code=503,
                detail="Fila de processamento cheia, tente novamente"
            )
        
        return {
            "ok": True,
            "request_id": request_id,
            "message": "Frame enfileirado para processamento",
            "queue_status": await async_frame_processor.get_queue_status_async()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro interno ao enfileirar frame: {str(e)}"
        )


@app.post("/calibrate")
async def calibrate_gaze_optimized(
    frame: UploadFile = File(..., description="Frame de referência para calibração"),
    label: str = Form(..., description="Tipo de calibração (center)"),
    session_id: str = Form(..., description="ID único da sessão")
):
    """
    Calibra o sistema de gaze para uma sessão específica (otimizado).
    
    Args:
        frame: Frame de referência para calibração
        label: Tipo de calibração (para V1, apenas "center")
        session_id: ID único da sessão
        
    Returns:
        Offsets de calibração aplicados
    """
    try:
        # Validar tipo de arquivo
        if not frame.content_type or not frame.content_type.startswith("image/"):
            raise HTTPException(
                status_code=400, 
                detail="Arquivo deve ser uma imagem válida"
            )
        
        # Validar label de calibração
        if label != "center":
            raise HTTPException(
                status_code=400,
                detail="Para V1, apenas calibração 'center' é suportada"
            )
        
        # Ler bytes da imagem
        image_bytes = await frame.read()
        
        if not image_bytes:
            raise HTTPException(
                status_code=400, 
                detail="Arquivo de imagem vazio"
            )
        
        # Processar imagem com versão otimizada
        sample_gaze = infer_gaze_optimized(image_bytes)
        
        # Verificar se houve erro na inferência
        if "error" in sample_gaze:
            return JSONResponse(
                status_code=400,
                content=sample_gaze
            )
        
        # Definir calibração para a sessão
        offsets = set_calibration(session_id, sample_gaze, label)
        
        return {
            "ok": True,
            "message": f"Calibração '{label}' aplicada para sessão {session_id}",
            "offsets": offsets,
            "session_id": session_id,
            "optimized": True
        }
        
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro interno na calibração: {str(e)}"
        )


@app.get("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    Endpoint WebSocket para streaming de gaze em tempo real.
    
    Args:
        websocket: Conexão WebSocket
    """
    await stream_ws(websocket)


@app.websocket("/gaze/ws/{session_id}")
async def gaze_websocket_endpoint_route(websocket: WebSocket, session_id: str):
    """
    Endpoint WebSocket específico para gaze detection com análise de foco.
    
    Args:
        websocket: Conexão WebSocket
        session_id: ID único da sessão
    """
    await gaze_websocket_endpoint(websocket, session_id)


@app.get("/gaze/sessions")
async def get_gaze_sessions():
    """
    Obtém informações sobre todas as sessões de gaze ativas.
    
    Returns:
        Lista de sessões ativas com estatísticas
    """
    gaze_manager = get_gaze_manager()
    return gaze_manager.get_all_stats()


@app.get("/gaze/session/{session_id}")
async def get_gaze_session_stats(session_id: str):
    """
    Obtém estatísticas de uma sessão específica de gaze.
    
    Args:
        session_id: ID da sessão
        
    Returns:
        Estatísticas da sessão
    """
    gaze_manager = get_gaze_manager()
    stats = gaze_manager.get_session_stats(session_id)
    
    if stats:
        return stats
    else:
        raise HTTPException(
            status_code=404,
            detail=f"Sessão {session_id} não encontrada"
        )


@app.get("/metrics")
async def get_metrics():
    """
    Endpoint para métricas de performance (estilo Prometheus).
    
    Returns:
        Métricas detalhadas de performance
    """
    return {
        "performance": get_performance_metrics(),
        "queue": await async_frame_processor.get_stats_async(),
        "gaze_sessions": get_gaze_manager().get_all_stats(),
        "system": {
            "cpu_count": CPU_COUNT,
            "recommended_workers": RECOMMENDED_WORKERS,
            "optimizations_enabled": True
        }
    }


@app.post("/metrics/reset")
async def reset_metrics():
    """
    Reseta métricas de performance.
    
    Returns:
        Confirmação de reset
    """
    reset_performance_metrics()
    return {"message": "Métricas de performance resetadas"}


@app.get("/queue/status")
async def get_queue_status():
    """
    Obtém status da fila de processamento.
    
    Returns:
        Status detalhado da fila
    """
    return await async_frame_processor.get_queue_status_async()


@app.get("/status")
async def get_status():
    """
    Endpoint para obter status da aplicação e estatísticas.
    
    Returns:
        Status da aplicação e estatísticas
    """
    return {
        "status": "ok",
        "version": "2.0.0",
        "optimizations": {
            "performance_monitoring": True,
            "frame_queue_processor": True,
            "mediapipe_singleton": True,
            "gaze_websocket": True
        },
        "websocket_connections": get_connection_count(),
        "fps_info": get_fps_info(),
        "queue_status": await async_frame_processor.get_queue_status_async(),
        "gaze_sessions": get_gaze_manager().get_all_stats(),
        "endpoints": {
            "health": "/health",
            "gaze": "/gaze",
            "gaze_queue": "/gaze/queue",
            "calibrate": "/calibrate",
            "websocket": "/ws",
            "gaze_websocket": "/gaze/ws/{session_id}",
            "gaze_sessions": "/gaze/sessions",
            "gaze_session_stats": "/gaze/session/{session_id}",
            "metrics": "/metrics",
            "queue_status": "/queue/status",
            "status": "/status"
        }
    }


@app.get("/")
async def root():
    """
    Endpoint raiz com informações da API otimizada.
    
    Returns:
        Informações básicas da API
    """
    return {
        "name": "Gaze Backend - Otimizado",
        "version": "2.0.0",
        "description": "Backend otimizado para estimação de gaze usando MediaPipe FaceMesh no Mac M1",
        "optimizations": [
            "Performance monitoring com timers",
            "Frame queue processor com drop de frames",
            "MediaPipe singleton para evitar reinicialização",
            "Múltiplos workers recomendados",
            "Core ML support via ONNX (quando disponível)",
            "Gaze WebSocket em tempo real",
            "Detecção automática de perda de foco"
        ],
        "docs": "/docs",
        "metrics": "/metrics",
        "endpoints": [
            "GET /health",
            "POST /gaze",
            "POST /gaze/queue",
            "POST /calibrate", 
            "GET /ws",
            "GET /gaze/ws/{session_id}",
            "GET /gaze/sessions",
            "GET /gaze/session/{session_id}",
            "GET /metrics",
            "GET /queue/status",
            "GET /status"
        ]
    }


if __name__ == "__main__":
    # Executar aplicação otimizada
    print(f"🚀 Iniciando Gaze Backend Otimizado...")
    print(f"🔧 CPU Count: {CPU_COUNT}")
    print(f"👥 Workers recomendados: {RECOMMENDED_WORKERS}")
    print(f"💡 Para produção, use: uvicorn app_optimized:app --workers {RECOMMENDED_WORKERS}")
    
    uvicorn.run(
        "app_optimized:app",
        host="0.0.0.0",
        port=8000,
        reload=False,  # Desabilitar reload para produção
        log_level="info"
    )
