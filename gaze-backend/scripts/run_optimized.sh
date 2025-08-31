#!/bin/bash

# Script de execução otimizada para Gaze Backend
# Configurado para máxima performance no Mac M1

set -e

echo "🚀 Gaze Backend - Execução Otimizada"
echo "====================================="

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
    echo "📥 Instalando dependências otimizadas..."
    pip install --upgrade pip
    pip install -r requirements_optimized.txt
else
    echo "✅ Dependências já instaladas"
fi

# Obter informações do sistema
CPU_COUNT=$(python3 -c "import os; print(os.cpu_count())")
RECOMMENDED_WORKERS=$(python3 -c "import os; print(min(4, os.cpu_count()))")

echo ""
echo "🔧 Configurações do Sistema:"
echo "   CPU Count: $CPU_COUNT"
echo "   Workers recomendados: $RECOMMENDED_WORKERS"
echo ""

echo "🎯 Iniciando servidor otimizado..."
echo "📍 URL: http://localhost:8000"
echo "📚 Docs: http://localhost:8000/docs"
echo "📊 Metrics: http://localhost:8000/metrics"
echo "🔍 Health: http://localhost:8000/health"
echo ""
echo "💡 Otimizações ativas:"
echo "   - Performance monitoring com timers"
echo "   - Frame queue processor com drop de frames"
echo "   - MediaPipe singleton"
echo "   - Múltiplos workers ($RECOMMENDED_WORKERS)"
echo "   - Core ML support (quando disponível)"
echo ""

# Executar aplicação otimizada com múltiplos workers
exec uvicorn app_optimized:app \
    --host 0.0.0.0 \
    --port 8000 \
    --workers $RECOMMENDED_WORKERS \
    --log-level info \
    --access-log
