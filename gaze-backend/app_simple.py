"""
Versão simplificada da aplicação para teste de inicialização.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Criar aplicação básica
app = FastAPI(
    title="Gaze Backend - Teste",
    description="Versão simplificada para teste",
    version="1.0.0"
)

# Configurar CORS básico
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check():
    """Endpoint básico de saúde."""
    return {"status": "ok", "version": "1.0.0"}

@app.get("/")
async def root():
    """Endpoint raiz."""
    return {"message": "Gaze Backend funcionando!"}

if __name__ == "__main__":
    print("🚀 Iniciando servidor de teste...")
    uvicorn.run(
        "app_simple:app",
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
