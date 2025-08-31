#!/bin/bash

# Script de desenvolvimento para Gaze Backend
# Facilita a execução local com ambiente virtual

set -e

echo "🚀 Gaze Backend - Script de Desenvolvimento"
echo "=============================================="

# Verificar se Python 3.11+ está instalado
python_version=$(python3 --version 2>/dev/null | cut -d' ' -f2 | cut -d'.' -f1,2)
if [[ "$python_version" < "3.11" ]]; then
    echo "❌ Erro: Python 3.11+ é necessário. Versão atual: $python_version"
    exit 1
fi

echo "✅ Python $python_version detectado"

# Verificar se ambiente virtual existe
if [ ! -d ".venv" ]; then
    echo "📦 Criando ambiente virtual..."
    python3 -m venv .venv
fi

# Ativar ambiente virtual
echo "🔧 Ativando ambiente virtual..."
source .venv/bin/activate

# Verificar se dependências estão instaladas
if [ ! -f ".venv/pyvenv.cfg" ] || [ ! -d ".venv/lib/python3.11/site-packages" ]; then
    echo "📥 Instalando dependências..."
    pip install --upgrade pip
    pip install -r requirements.txt
else
    echo "✅ Dependências já instaladas"
fi

# Verificar se webcam está disponível (Linux)
if command -v v4l2-ctl &> /dev/null; then
    echo "📹 Verificando webcam..."
    if v4l2-ctl --list-devices | grep -q "video"; then
        echo "✅ Webcam detectada"
    else
        echo "⚠️  Webcam não detectada"
    fi
fi

echo ""
echo "🎯 Iniciando servidor de desenvolvimento..."
echo "📍 URL: http://localhost:8000"
echo "📚 Docs: http://localhost:8000/docs"
echo "🔍 Health: http://localhost:8000/health"
echo ""
echo "💡 Dicas:"
echo "   - Pressione Ctrl+C para parar"
echo "   - Use --reload para desenvolvimento"
echo "   - Verifique logs para debug"
echo ""

# Executar aplicação
exec uvicorn app:app --reload --host 0.0.0.0 --port 8000 --log-level info
