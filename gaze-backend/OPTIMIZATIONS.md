# 🚀 **Otimizações de Performance - Gaze Backend**

Este documento detalha todas as otimizações implementadas para melhorar significativamente a performance do backend no **Mac M1**.

## 📊 **1. Diagnóstico de Gargalos - Timers de Performance**

### **Sistema de Profiling Completo**

- ✅ **Timers automáticos** para cada etapa do processamento
- ✅ **Métricas detalhadas** com percentis (P95, mediana, média)
- ✅ **Middleware FastAPI** para latência de requests
- ✅ **Endpoint `/metrics`** estilo Prometheus

### **Timers Implementados**

```python
# Decorator para funções
@timer("operation_name")
def my_function():
    pass

# Context manager para blocos de código
with performance_timer("operation_name"):
    # código aqui
    pass
```

### **Métricas Capturadas**

- **Pré-processamento**: Conversão de bytes para numpy array
- **Inferência MediaPipe**: Processamento do modelo
- **Extração de landmarks**: Coordenadas dos olhos e íris
- **Cálculo de métricas**: Deslocamento e atenção
- **Pós-processamento**: Clamp e determinação on_screen

## 🔧 **2. Melhorias Imediatas em TFLite/MediaPipe**

### **Singleton Pattern para MediaPipe**

```python
# Antes: Nova instância a cada request
face_mesh = mp.solutions.face_mesh.FaceMesh(...)

# Depois: Instância única global
_face_mesh_instance = None
_face_mesh_lock = threading.Lock()

def get_face_mesh():
    global _face_mesh_instance
    if _face_mesh_instance is None:
        with _face_mesh_lock:
            if _face_mesh_instance is None:
                _face_mesh_instance = mp.solutions.face_mesh.FaceMesh(...)
    return _face_mesh_instance
```

### **Configurações Otimizadas**

- ✅ **Thread pool dedicado** para processamento paralelo
- ✅ **Configuração automática** de workers baseada em CPU count
- ✅ **Uso de numpy vetorizado** para cálculos
- ✅ **Fallback inteligente** para diferentes métodos de processamento

### **Dependências Otimizadas**

```bash
# Processamento de imagem mais rápido
turbojpeg>=1.2.0          # Decodificação JPEG acelerada
Pillow-SIMD>=8.0.0        # Versão SIMD do Pillow
opencv-contrib-python      # Funcionalidades extras do OpenCV
```

## 🎯 **3. Quantização e Modelos Otimizados**

### **Suporte a Modelos Quantizados**

- ✅ **Detecção automática** de modelos INT8
- ✅ **Fallback para float32** se necessário
- ✅ **Configuração via variável de ambiente**

```python
USE_QUANTIZED = os.getenv("USE_QUANTIZED_MODEL", "false").lower() == "true"
```

### **Estrutura de Modelos**

```
models/
├── face_mesh_float32.tflite    # Modelo padrão
├── face_mesh_int8.tflite       # Modelo quantizado (quando disponível)
└── face_mesh.onnx              # Modelo ONNX para Core ML
```

## 🚀 **4. Integração Core ML / ONNX**

### **Suporte Automático ao Core ML**

```python
try:
    import onnxruntime as ort
    
    # Configurar providers para Mac M1
    if 'CoreMLExecutionProvider' in ort.get_available_providers():
        preferred_providers = ['CoreMLExecutionProvider', 'CPUExecutionProvider']
        print("🚀 Usando Core ML para aceleração no Mac M1")
    else:
        preferred_providers = ['CPUExecutionProvider']
        print("⚠️ Core ML não disponível, usando CPU")
        
except ImportError:
    print("⚠️ ONNX Runtime não disponível, usando MediaPipe padrão")
```

### **Conversão de Modelos**

```bash
# Converter MediaPipe para ONNX (quando possível)
python -m mediapipe.tools.convert_to_onnx \
    --model_path models/face_mesh.tflite \
    --output_path models/face_mesh.onnx
```

## ⚡ **5. Arquitetura para Tempo Real**

### **Sistema de Fila com Drop de Frames**

```python
class FrameQueueProcessor:
    def __init__(self, 
                 max_queue_size: int = 10,
                 max_workers: int = 2,
                 drop_old_frames: bool = True,
                 max_frame_age_ms: int = 100):
        # Configurações otimizadas para tempo real
```

### **Características da Fila**

- ✅ **Drop automático** de frames antigos (>200ms)
- ✅ **Processamento prioritário** (0-10)
- ✅ **Múltiplos workers** dedicados
- ✅ **Estatísticas em tempo real**

### **Worker Dedicado para Inferência**

```python
# Thread pool separado para inferência
executor = ThreadPoolExecutor(max_workers=MAX_WORKERS)

# Worker thread principal
self.worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
```

## 📈 **6. Métricas e Monitoramento**

### **Endpoint `/metrics`**

```json
{
  "performance": {
    "uptime_seconds": 3600,
    "total_operations": 15000,
    "operations": {
      "image_preprocessing": {
        "avg_time": 0.002,
        "p95_time": 0.005,
        "total_calls": 5000
      },
      "mediapipe_inference": {
        "avg_time": 0.045,
        "p95_time": 0.080,
        "total_calls": 5000
      }
    }
  },
  "queue": {
    "frames_received": 5000,
    "frames_processed": 4800,
    "frames_dropped": 200,
    "avg_processing_time": 0.047
  }
}
```

### **Métricas do Sistema**

- **CPU Count** e workers recomendados
- **Status da fila** de processamento
- **Latência por operação** com percentis
- **Taxa de drop** de frames

## 🚀 **7. Como Executar Otimizado**

### **Execução Local Otimizada**

```bash
# Script otimizado
chmod +x scripts/run_optimized.sh
./scripts/run_optimized.sh

# Ou manualmente
uvicorn app_optimized:app --workers 4 --log-level info
```

### **Execução com Docker Otimizado**

```bash
# Construir imagem otimizada
docker build -f Dockerfile.optimized -t gaze-backend-optimized .

# Executar com múltiplos workers
docker run --rm -p 8000:8000 gaze-backend-optimized
```

### **Configurações de Produção**

```bash
# Variáveis de ambiente
export USE_QUANTIZED_MODEL=true
export MAX_WORKERS=4
export DROP_OLD_FRAMES=true
export MAX_FRAME_AGE_MS=200

# Executar com workers recomendados
uvicorn app_optimized:app --workers 4 --host 0.0.0.0 --port 8000
```

## 📊 **8. Comparação de Performance**

### **Antes das Otimizações**

- **MediaPipe**: Nova instância a cada request
- **Processamento**: Síncrono, bloqueante
- **Métricas**: Nenhuma
- **Workers**: Apenas 1
- **Fila**: Sem controle de frames antigos

### **Depois das Otimizações**

- **MediaPipe**: Singleton global
- **Processamento**: Assíncrono com fila
- **Métricas**: Profiling completo
- **Workers**: Múltiplos (baseado em CPU)
- **Fila**: Drop automático de frames antigos

### **Ganhos Esperados**

- 🚀 **2-4x mais rápido** no processamento
- 📉 **Redução de 60-80%** na latência
- 🔄 **Melhor throughput** para múltiplos requests
- 📊 **Visibilidade completa** de performance
- ⚡ **Suporte a Core ML** no Mac M1

## 🧪 **9. Testes de Performance**

### **Benchmark Automático**

```bash
# Executar testes de performance
python -m pytest tests/test_performance.py -v

# Teste de carga
python scripts/benchmark.py --requests 1000 --concurrent 10
```

### **Métricas de Teste**

- **Requests por segundo** (RPS)
- **Latência média** e percentis
- **Uso de CPU** e memória
- **Taxa de erro** e timeouts

## 🔧 **10. Troubleshooting**

### **Problemas Comuns**

1. **"Core ML não disponível"**
   - Verificar se `onnxruntime` está instalado
   - Confirmar versão do macOS (10.15+)

2. **"Fila cheia"**
   - Aumentar `max_queue_size`
   - Verificar se workers estão ativos

3. **"Performance baixa"**
   - Verificar métricas em `/metrics`
   - Confirmar número de workers
   - Verificar se MediaPipe singleton está funcionando

### **Logs de Debug**

```bash
# Executar com logs detalhados
uvicorn app_optimized:app --log-level debug

# Verificar métricas em tempo real
curl http://localhost:8000/metrics | jq
```

## 📚 **11. Próximos Passos**

### **Otimizações Futuras**

- 🔄 **Modelo customizado** treinado para gaze
- 🧠 **TensorRT** para aceleração GPU
- 📱 **Core ML customizado** para Mac M1
- 🌐 **Distributed processing** com múltiplas máquinas

### **Monitoramento Avançado**

- 📊 **Grafana dashboards** para métricas
- 🔔 **Alertas automáticos** para degradação
- 📈 **Trend analysis** de performance
- 🎯 **A/B testing** de otimizações

---

## 🎯 **Resumo das Otimizações**

| Categoria | Antes | Depois | Melhoria |
|-----------|-------|--------|----------|
| **MediaPipe** | Nova instância/request | Singleton global | 3-5x |
| **Workers** | 1 | 4 (baseado em CPU) | 4x |
| **Processamento** | Síncrono | Assíncrono + fila | 2-3x |
| **Métricas** | Nenhuma | Profiling completo | 100% |
| **Core ML** | Não | Suporte automático | 2-4x |
| **Drop de frames** | Não | Automático | 100% |

**Resultado esperado**: **2-4x mais rápido** no Mac M1 com **visibilidade completa** de performance! 🚀✨
