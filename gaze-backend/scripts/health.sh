#!/usr/bin/env bash
set -euo pipefail
PORT="${PORT:-8000}"
curl -sS "http://localhost:${PORT}/health" || true
