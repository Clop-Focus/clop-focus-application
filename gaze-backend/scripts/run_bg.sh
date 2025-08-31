#!/usr/bin/env bash
set -euo pipefail

APP_MODULE="${APP_MODULE:-app_fixed:app}"   # mude para app_optimized:app se quiser
PORT="${PORT:-8000}"

# Se não estiver no diretório gaze-backend, navegar para ele
if [[ ! -f "app_fixed.py" ]]; then
    cd gaze-backend
fi

source .venv/bin/activate

# mata algo preso na porta
lsof -ti :$PORT | xargs -r kill -9 || true

# sobe em background e guarda PID
nohup uvicorn "$APP_MODULE" --host 0.0.0.0 --port "$PORT" --log-level info \
  > server.log 2>&1 &

echo $! > uvicorn.pid
echo "UVICORN PID $(cat uvicorn.pid). Logs: server.log"
