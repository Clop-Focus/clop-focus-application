"""
Versão corrigida da aplicação que não conflita com loops de eventos existentes.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Criar aplicação FastAPI
app = FastAPI(
    title="Gaze Backend - Corrigido",
    description="Backend corrigido para estimação de gaze",
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

@app.get("/health")
async def health_check():
    """Endpoint de saúde."""
    return {"status": "ok", "version": "1.0.0"}

@app.get("/")
async def root():
    """Endpoint raiz."""
    return {"message": "Gaze Backend funcionando!"}

@app.get("/test")
async def test():
    """Endpoint de teste."""
    return {"message": "Teste OK", "timestamp": "2024-08-30"}

# Não usar if __name__ == "__main__" para evitar conflitos
