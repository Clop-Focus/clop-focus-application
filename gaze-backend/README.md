# 🎯 Gaze Backend

Sistema de gaze detection robusto usando MediaPipe FaceMesh com integração frontend completa.

## 🚀 Quick Start

```bash
# Iniciar rapidamente
./quick_start.sh

# Ou manualmente
source .venv/bin/activate
make run
```

## 📊 Funcionalidades

- ✅ **Gaze Detection** com MediaPipe FaceMesh
- ✅ **Sistema de Alertas** em tempo real
- ✅ **WebSocket** para streaming
- ✅ **Interface de Teste** completa
- ✅ **Calibração** por sessão
- ✅ **Métricas** detalhadas (Yaw, Pitch, Foco)

## 🔗 Endpoints

- `GET /health` - Status do sistema
- `POST /gaze` - Inferência de gaze
- `POST /calibrate` - Calibração
- `WS /gaze/ws/{session_id}` - Streaming WebSocket

## 📱 Frontend

Interface de teste completa em `test_integration.html` com:
- Métricas em tempo real
- Visualização de landmarks
- Sistema de alertas
- BBox da face

## 🛠️ Comandos

```bash
make run      # Iniciar backend
make stop     # Parar backend
make health   # Verificar saúde
make logs     # Ver logs
```

## 📁 Arquivos Principais

- `gaze_roboflow.py` - Modelo de gaze detection
- `app_lazy.py` - FastAPI app
- `calibration.py` - Sistema de calibração
- `test_integration.html` - Interface de teste

## 📋 Status

**PROJETO COMPLETO E FUNCIONAL** ✅

Ver `PROJECT_STATUS.md` para detalhes completos.

---
**Pronto para integração futura** 🚀
