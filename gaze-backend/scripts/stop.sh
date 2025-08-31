#!/usr/bin/env bash
set -euo pipefail

# Se não estiver no diretório gaze-backend, navegar para ele
if [[ ! -f "app_fixed.py" ]]; then
    cd gaze-backend
fi

if [[ -f uvicorn.pid ]]; then
  kill -TERM "$(cat uvicorn.pid)" 2>/dev/null || true
  rm -f uvicorn.pid
  echo "Parado."
else
  echo "Sem PID. Nada para parar."
fi
