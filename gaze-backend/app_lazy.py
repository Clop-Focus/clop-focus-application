"""
Versão com lazy-load para evitar travamentos no startup.
Carrega os módulos pesados apenas quando necessário.
"""

from fastapi import FastAPI, File, Form, HTTPException, UploadFile, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import threading
import time
import json
import base64
import asyncio

# Criar aplicação FastAPI
app = FastAPI(
    title="Gaze Backend - Lazy Load",
    description="Backend com carregamento sob demanda",
    version="1.0.0"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Estado global para lazy-load
gaze_module = None
calibration_module = None
ready = False
loading = False

# Gerenciador de sessões WebSocket
websocket_sessions = {}

def load_modules():
    """Carrega módulos pesados em background."""
    global gaze_module, calibration_module, ready, loading
    
    if loading:
        return
    
    loading = True
    try:
        print("🔄 Carregando módulos pesados...")

        # Importar módulos robustos de gaze detection
        from gaze_roboflow import infer_gaze_roboflow
        from calibration import set_calibration, get_offsets, apply_offsets

        gaze_module = {
            'infer_gaze': infer_gaze_roboflow
        }

        calibration_module = {
            'set_calibration': set_calibration,
            'get_offsets': get_offsets,
            'apply_offsets': apply_offsets
        }

        ready = True
        print("✅ Módulos robustos carregados com sucesso!")
        print("🎯 EXTREMA tolerância configurada!")
        print("📊 Considera 'Na Tela' até foco crítico!")
        print("👁️ Detecção robusta da posição dos olhos!")
        print("📦 BBox da face incluído!")

    except Exception as e:
        print(f"❌ Erro ao carregar módulos: {e}")
        ready = False
    finally:
        loading = False

@app.on_event("startup")
async def startup_event():
    """Evento de inicialização - carrega módulos em thread separada."""
    print("🚀 Gaze Backend Lazy iniciando...")
    
    # Carregar módulos em background
    thread = threading.Thread(target=load_modules, daemon=True)
    thread.start()

@app.get("/health")
async def health_check():
    """Endpoint de saúde com status de carregamento."""
    return {
        "status": "ready" if ready else "initializing",
        "loading": loading,
        "version": "1.0.0"
    }

@app.get("/")
async def root():
    """Endpoint raiz."""
    return {
        "message": "Gaze Backend Lazy funcionando!",
        "status": "ready" if ready else "initializing"
    }

@app.websocket("/gaze/ws/{session_id}")
async def gaze_websocket_endpoint(websocket: WebSocket, session_id: str):
    """Endpoint WebSocket para gaze detection em tempo real."""
    if not ready:
        await websocket.close(code=1008, reason="Sistema ainda inicializando")
        return
    
    await websocket.accept()
    print(f"🔌 WebSocket conectado para sessão: {session_id}")
    
    # Registrar sessão
    websocket_sessions[session_id] = websocket
    
    try:
        while True:
            # Receber mensagem do cliente
            message = await websocket.receive_text()
            data = json.loads(message)
            
            if data.get("type") == "frame":
                # Processar frame
                frame_data = data.get("data")
                if frame_data:
                    try:
                        # Decodificar base64
                        frame_bytes = base64.b64decode(frame_data)
                        
                        # Processar com MediaPipe
                        result = gaze_module['infer_gaze'](frame_bytes)
                        
                        if "error" not in result:
                            # Aplicar calibração
                            result = calibration_module['apply_offsets'](result, session_id)
                            
                            # Adicionar timestamp
                            result["timestamp"] = time.time()
                            result["session_id"] = session_id
                            
                            # Enviar resultado
                            await websocket.send_text(json.dumps(result))
                            
                            # Verificar se há perda de foco
                            if not result.get("on_screen", True):
                                focus_alert = {
                                    "type": "focus_alert",
                                    "message": "Perda de foco detectada!",
                                    "gaze": result["gaze"],
                                    "attention": result["attention"],
                                    "timestamp": time.time()
                                }
                                await websocket.send_text(json.dumps(focus_alert))
                            
                            # Verificar se há erro de detecção de rosto
                            elif "error" in result and result["error"] == "no_face":
                                no_face_alert = {
                                    "type": "no_face_alert",
                                    "message": "Rosto não detectado! Verifique a posição da câmera.",
                                    "error": "no_face",
                                    "timestamp": time.time(),
                                    "severity": "warning"
                                }
                                await websocket.send_text(json.dumps(no_face_alert))
                            
                            # Verificar outros erros de detecção
                            elif "error" in result:
                                detection_alert = {
                                    "type": "detection_alert",
                                    "message": f"Erro de detecção: {result.get('message', 'Erro desconhecido')}",
                                    "error": result["error"],
                                    "timestamp": time.time(),
                                    "severity": "error"
                                }
                                await websocket.send_text(json.dumps(detection_alert))
                            
                        else:
                            # Enviar erro
                            await websocket.send_text(json.dumps(result))
                            
                    except Exception as e:
                        error_msg = {
                            "error": "processing_error",
                            "message": f"Erro ao processar frame: {str(e)}"
                        }
                        await websocket.send_text(json.dumps(error_msg))
            
            elif data.get("type") == "ping":
                # Responder ping
                await websocket.send_text(json.dumps({"type": "pong", "timestamp": time.time()}))
                
    except Exception as e:
        print(f"❌ Erro no WebSocket: {e}")
    finally:
        # Remover sessão
        if session_id in websocket_sessions:
            del websocket_sessions[session_id]
        print(f"🔌 WebSocket desconectado para sessão: {session_id}")

@app.get("/websocket/sessions")
async def get_websocket_sessions():
    """Lista sessões WebSocket ativas."""
    return {
        "active_sessions": list(websocket_sessions.keys()),
        "count": len(websocket_sessions)
    }

@app.post("/gaze")
async def process_gaze(
    frame: UploadFile = File(..., description="Frame da webcam"),
    session_id: str = Form(..., description="ID único da sessão")
):
    """Processa frame da webcam (lazy-load)."""
    if not ready:
        raise HTTPException(
            status_code=503,
            detail="Sistema ainda inicializando. Tente novamente em alguns segundos."
        )
    
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
        
        # Processar imagem
        result = gaze_module['infer_gaze'](image_bytes)
        
        # Verificar se houve erro na inferência
        if "error" in result:
            return JSONResponse(
                status_code=400,
                content=result
            )
        
        # Aplicar calibração da sessão
        result = calibration_module['apply_offsets'](result, session_id)
        
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
    """Calibra o sistema de gaze (lazy-load)."""
    if not ready:
        raise HTTPException(
            status_code=503,
            detail="Sistema ainda inicializando. Tente novamente em alguns segundos."
        )
    
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
        
        # Processar imagem
        sample_gaze = gaze_module['infer_gaze'](image_bytes)
        
        # Verificar se houve erro na inferência
        if "error" in sample_gaze:
            return JSONResponse(
                status_code=400,
                content=sample_gaze
            )
        
        # Definir calibração para a sessão
        offsets = calibration_module['set_calibration'](session_id, sample_gaze, label)
        
        return {
            "ok": True,
            "message": f"Calibração '{label}' aplicada para sessão {session_id}",
            "offsets": offsets,
            "session_id": session_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro interno na calibração: {str(e)}"
        )

@app.get("/status")
async def get_status():
    """Status detalhado da aplicação."""
    return {
        "status": "ready" if ready else "initializing",
        "loading": loading,
        "version": "1.0.0",
        "modules": {
            "gaze": gaze_module is not None,
            "calibration": calibration_module is not None
        },
        "websocket_sessions": len(websocket_sessions)
    }
