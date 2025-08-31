#!/usr/bin/env python3
"""
Script de inicialização alternativo para o Gaze Backend.
Permite configuração via variáveis de ambiente e argumentos de linha de comando.
"""

import os
import argparse
import uvicorn
from app import app

def main():
    """Função principal de inicialização."""
    parser = argparse.ArgumentParser(description="Gaze Backend - FastAPI Server")
    
    parser.add_argument(
        "--host",
        default=os.getenv("HOST", "0.0.0.0"),
        help="Host para bind do servidor (default: 0.0.0.0)"
    )
    
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.getenv("PORT", "8000")),
        help="Porta para bind do servidor (default: 8000)"
    )
    
    parser.add_argument(
        "--reload",
        action="store_true",
        default=os.getenv("RELOAD", "false").lower() == "true",
        help="Habilitar reload automático (default: false)"
    )
    
    parser.add_argument(
        "--workers",
        type=int,
        default=int(os.getenv("WORKERS", "1")),
        help="Número de workers (default: 1)"
    )
    
    parser.add_argument(
        "--log-level",
        default=os.getenv("LOG_LEVEL", "info"),
        choices=["debug", "info", "warning", "error", "critical"],
        help="Nível de log (default: info)"
    )
    
    args = parser.parse_args()
    
    print(f"🚀 Iniciando Gaze Backend...")
    print(f"📍 Host: {args.host}")
    print(f"🔌 Porta: {args.port}")
    print(f"🔄 Reload: {args.reload}")
    print(f"👥 Workers: {args.workers}")
    print(f"📝 Log Level: {args.log_level}")
    print(f"🌐 API Docs: http://{args.host}:{args.port}/docs")
    print(f"🔍 Health Check: http://{args.host}:{args.port}/health")
    print("-" * 50)
    
    # Configurar uvicorn
    uvicorn.run(
        "app:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        workers=args.workers if not args.reload else 1,
        log_level=args.log_level,
        access_log=True
    )

if __name__ == "__main__":
    main()
