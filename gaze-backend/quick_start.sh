#!/bin/bash

# 🚀 QUICK START - Gaze Backend
# Script para retomar o projeto rapidamente

echo "🎯 Iniciando Gaze Backend..."

# Verificar se estamos no diretório correto
if [ ! -f "gaze_roboflow.py" ]; then
    echo "❌ Execute este script de dentro do diretório gaze-backend"
    exit 1
fi

# Ativar ambiente virtual
echo "🔧 Ativando ambiente virtual..."
source .venv/bin/activate

# Verificar dependências
echo "📦 Verificando dependências..."
pip list | grep -E "(fastapi|mediapipe|opencv)" || {
    echo "⚠️ Dependências não encontradas. Instalando..."
    pip install -r requirements.txt
}

# Parar processos existentes
echo "🛑 Parando processos existentes..."
make stop 2>/dev/null || true

# Iniciar backend
echo "🚀 Iniciando backend..."
make run

# Aguardar inicialização
echo "⏳ Aguardando inicialização..."
sleep 3

# Verificar saúde
echo "🏥 Verificando saúde do sistema..."
curl -s http://localhost:8000/health | jq '.' || {
    echo "❌ Backend não está respondendo"
    exit 1
}

echo ""
echo "✅ GAZE BACKEND INICIADO COM SUCESSO!"
echo "🌐 URL: http://localhost:8000"
echo "📊 Health: http://localhost:8000/health"
echo "🔌 WebSocket: ws://localhost:8000/gaze/ws/{session_id}"
echo ""
echo "📱 Para testar o frontend:"
echo "   - Abra test_integration.html no navegador"
echo "   - Inicie a câmera e conecte ao gaze"
echo ""
echo "🛑 Para parar: make stop"
echo "📋 Para logs: make logs"
