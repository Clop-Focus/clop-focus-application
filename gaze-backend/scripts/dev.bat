@echo off
REM Script de desenvolvimento para Gaze Backend (Windows)
REM Facilita a execução local com ambiente virtual

echo 🚀 Gaze Backend - Script de Desenvolvimento
echo ==============================================

REM Verificar se Python 3.11+ está instalado
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Erro: Python não está instalado ou não está no PATH
    pause
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version 2^>^&1') do set python_version=%%i
for /f "tokens=1,2 delims=." %%a in ("%python_version%") do set major_minor=%%a.%%b

echo ✅ Python %python_version% detectado

REM Verificar se ambiente virtual existe
if not exist ".venv" (
    echo 📦 Criando ambiente virtual...
    python -m venv .venv
)

REM Ativar ambiente virtual
echo 🔧 Ativando ambiente virtual...
call .venv\Scripts\activate.bat

REM Verificar se dependências estão instaladas
if not exist ".venv\Lib\site-packages" (
    echo 📥 Instalando dependências...
    python -m pip install --upgrade pip
    pip install -r requirements.txt
) else (
    echo ✅ Dependências já instaladas
)

echo.
echo 🎯 Iniciando servidor de desenvolvimento...
echo 📍 URL: http://localhost:8000
echo 📚 Docs: http://localhost:8000/docs
echo 🔍 Health: http://localhost:8000/health
echo.
echo 💡 Dicas:
echo    - Pressione Ctrl+C para parar
echo    - Use --reload para desenvolvimento
echo    - Verifique logs para debug
echo.

REM Executar aplicação
uvicorn app:app --reload --host 0.0.0.0 --port 8000 --log-level info

pause
