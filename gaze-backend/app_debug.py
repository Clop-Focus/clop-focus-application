"""
Versão de debug para identificar onde a aplicação está travando.
"""

import time
import sys

print("🔍 Iniciando debug da aplicação...")

try:
    print("1️⃣ Importando FastAPI...")
    from fastapi import FastAPI
    print("✅ FastAPI importado")
except Exception as e:
    print(f"❌ Erro ao importar FastAPI: {e}")
    sys.exit(1)

try:
    print("2️⃣ Importando middleware...")
    from fastapi.middleware.cors import CORSMiddleware
    print("✅ CORS middleware importado")
except Exception as e:
    print(f"❌ Erro ao importar CORS: {e}")
    sys.exit(1)

try:
    print("3️⃣ Importando uvicorn...")
    import uvicorn
    print("✅ Uvicorn importado")
except Exception as e:
    print(f"❌ Erro ao importar uvicorn: {e}")
    sys.exit(1)

try:
    print("4️⃣ Criando aplicação FastAPI...")
    app = FastAPI(
        title="Gaze Backend - Debug",
        description="Versão de debug",
        version="1.0.0"
    )
    print("✅ Aplicação FastAPI criada")
except Exception as e:
    print(f"❌ Erro ao criar aplicação: {e}")
    sys.exit(1)

try:
    print("5️⃣ Configurando CORS...")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    print("✅ CORS configurado")
except Exception as e:
    print(f"❌ Erro ao configurar CORS: {e}")
    sys.exit(1)

try:
    print("6️⃣ Adicionando endpoints...")
    
    @app.get("/health")
    async def health_check():
        return {"status": "ok", "debug": True}
    
    @app.get("/")
    async def root():
        return {"message": "Debug funcionando!"}
    
    print("✅ Endpoints adicionados")
except Exception as e:
    print(f"❌ Erro ao adicionar endpoints: {e}")
    sys.exit(1)

try:
    print("7️⃣ Iniciando servidor...")
    print("🚀 Uvicorn iniciando em http://0.0.0.0:8000")
    
    uvicorn.run(
        "app_debug:app",
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
except Exception as e:
    print(f"❌ Erro ao iniciar servidor: {e}")
    sys.exit(1)
