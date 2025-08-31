"""
Aplicação FastAPI principal para backend de estimação de gaze.
Expõe endpoints para inferência de gaze, calibração e streaming WebSocket.
"""

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.websockets import WebSocket
import uvicorn
from typing import Optional

# Importar módulos locais
from gaze import infer_gaze
from calibration import set_calibration, get_offsets, apply_offsets
from ws import stream_ws, get_connection_count, get_fps_info

# Criar aplicação FastAPI
app = FastAPI(
    title="Gaze Backend",
    description="Backend para estimação de gaze e atenção usando MediaPipe FaceMesh",
    version="1.0.0"
)

# Configurar CORS para desenvolvimento
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    """
    Endpoint de saúde da aplicação.
    
    Returns:
        Status da aplicação
    """
    return {"status": "ok"}


@app.post("/gaze")
async def process_gaze(
    frame: UploadFile = File(..., description="Frame da webcam"),
    session_id: str = Form(..., description="ID único da sessão")
):
    """
    Processa frame da webcam para estimar gaze e atenção.
    
    Args:
        frame: Arquivo de imagem da webcam
        session_id: ID único da sessão para calibração
        
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
        
        # Processar imagem para inferir gaze
        result = infer_gaze(image_bytes)
        
        # Verificar se houve erro na inferência
        if "error" in result:
            return JSONResponse(
                status_code=400,
                content=result
            )
        
        # Aplicar calibração da sessão
        result = apply_offsets(result, session_id)
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro interno ao processar imagem: {str(e)}"
        )


@app.post("/calibrate")
async def calibrate_gaze(
    frame: UploadFile = File(..., description="Frame de referência para calibração"),
    label: str = Form(..., description="Tipo de calibração (center)"),
    session_id: str = Form(..., description="ID único da sessão")
):
    """
    Calibra o sistema de gaze para uma sessão específica.
    
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
        
        # Processar imagem para obter gaze de referência
        sample_gaze = infer_gaze(image_bytes)
        
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
            "session_id": session_id
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


@app.get("/status")
async def get_status():
    """
    Endpoint para obter status da aplicação e estatísticas.
    
    Returns:
        Status da aplicação e estatísticas
    """
    return {
        "status": "ok",
        "websocket_connections": get_connection_count(),
        "fps_info": get_fps_info(),
        "endpoints": {
            "health": "/health",
            "gaze": "/gaze",
            "calibrate": "/calibrate",
            "websocket": "/ws",
            "status": "/status"
        }
    }


@app.get("/")
async def root():
    """
    Endpoint raiz com informações da API.
    
    Returns:
        Informações básicas da API
    """
    return {
        "name": "Gaze Backend",
        "version": "1.0.0",
        "description": "Backend para estimação de gaze e atenção usando MediaPipe FaceMesh",
        "docs": "/docs",
        "endpoints": [
            "GET /health",
            "POST /gaze",
            "POST /calibrate", 
            "GET /ws",
            "GET /status"
        ]
    }


if __name__ == "__main__":
    # Executar aplicação localmente
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
