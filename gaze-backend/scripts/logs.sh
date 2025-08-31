#!/usr/bin/env bash
set -euo pipefail

# Se não estiver no diretório gaze-backend, navegar para ele
if [[ ! -f "app_fixed.py" ]]; then
    cd gaze-backend
fi

tail -f server.log
