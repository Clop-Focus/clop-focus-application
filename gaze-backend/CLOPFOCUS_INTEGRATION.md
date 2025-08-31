# 🎯 **Integração ClopFocus + Gaze Detection**

Este documento explica como integrar o sistema de gaze detection com o frontend ClopFocus para monitoramento de atenção em tempo real.

## 🚀 **Visão Geral da Integração**

### **O que foi implementado:**

1. ✅ **Backend otimizado** com MediaPipe FaceMesh
2. ✅ **WebSocket em tempo real** para streaming de gaze
3. ✅ **Detecção automática de perda de foco**
4. ✅ **Cliente JavaScript** para integração
5. ✅ **Hook React** personalizado
6. ✅ **Sistema de notificações** integrado

### **Fluxo de funcionamento:**

```
📷 Câmera → 🧠 Backend (MediaPipe) → 📡 WebSocket → 🎯 ClopFocus → 🔔 Notificação
```

## 🔧 **1. Configuração do Backend**

### **Verificar se está rodando:**

```bash
# No diretório gaze-backend
source .venv/bin/activate
uvicorn app_optimized:app --host 0.0.0.0 --port 8000 --log-level info
```

### **Testar endpoints:**

```bash
# Health check
curl http://localhost:8000/health

# Ver sessões ativas
curl http://localhost:8000/gaze/sessions
```

## 📱 **2. Integração no ClopFocus**

### **Passo 1: Incluir o cliente JavaScript**

Adicione o arquivo `clopfocus_integration.js` ao seu projeto:

```html
<!-- No index.html ou onde for apropriado -->
<script src="/path/to/clopfocus_integration.js"></script>
```

### **Passo 2: Inicializar o cliente**

```javascript
// No seu componente principal ou onde quiser monitorar gaze
const gazeClient = window.initializeClopFocusGaze({
    backendUrl: 'ws://localhost:8000',
    cameraIndex: 1, // Câmera que funciona no Mac
    frameRate: 15,  // FPS para processamento
    
    // Callback para perda de foco
    onFocusLoss: (data) => {
        console.log('🚨 Perda de foco detectada!', data);
        
        // Aqui você pode integrar com o sistema de notificações do ClopFocus
        // Por exemplo, chamar a função de notificação existente
        if (window.electronAPI?.notifyFocusLoss) {
            window.electronAPI.notifyFocusLoss('Foco Perdido');
        }
    },
    
    // Callback para atualizações de gaze
    onGazeUpdate: (data) => {
        // Atualizar UI com dados de gaze
        console.log('👁️ Gaze atualizado:', data.focus_analysis.status);
    }
});

// Conectar e iniciar monitoramento
gazeClient.connect().then(() => {
    return gazeClient.startMonitoring();
}).catch(error => {
    console.error('❌ Erro ao iniciar gaze detection:', error);
});
```

## ⚛️ **3. Usando o Hook React**

### **Instalar o hook:**

```bash
# Copie o arquivo useGazeDetection.ts para seu projeto
cp gaze-backend/useGazeDetection.ts src/hooks/
```

### **Usar no componente:**

```tsx
import { useGazeDetection } from '../hooks/useGazeDetection';

function SessionScreen() {
    const {
        isConnected,
        isMonitoring,
        gazeData,
        currentFocusScore,
        focusLossCount,
        connect,
        startMonitoring,
        stopMonitoring
    } = useGazeDetection({
        backendUrl: 'ws://localhost:8000',
        cameraIndex: 1,
        frameRate: 15,
        
        onFocusLoss: (data) => {
            // Integrar com notificações do ClopFocus
            if (window.electronAPI?.notifyFocusLoss) {
                window.electronAPI.notifyFocusLoss('Foco Perdido');
            }
        }
    });

    // Iniciar monitoramento quando componente montar
    useEffect(() => {
        if (isConnected && !isMonitoring) {
            startMonitoring();
        }
    }, [isConnected, isMonitoring, startMonitoring]);

    return (
        <div>
            <h2>Sessão de Foco</h2>
            
            {/* Status da conexão */}
            <div className="connection-status">
                Status: {isConnected ? '🟢 Conectado' : '🔴 Desconectado'}
            </div>
            
            {/* Score de foco em tempo real */}
            {gazeData && (
                <div className="focus-metrics">
                    <div className="focus-score">
                        Score de Foco: {currentFocusScore.toFixed(1)}%
                    </div>
                    <div className="attention-level">
                        Atenção: {(gazeData.attention * 100).toFixed(1)}%
                    </div>
                    <div className="gaze-direction">
                        Olhando: {gazeData.on_screen ? '📺 Na tela' : '👀 Fora da tela'}
                    </div>
                </div>
            )}
            
            {/* Contadores */}
            <div className="counters">
                <div>Perdas de foco: {focusLossCount}</div>
            </div>
            
            {/* Controles */}
            <div className="controls">
                {!isConnected ? (
                    <button onClick={connect}>🔗 Conectar</button>
                ) : !isMonitoring ? (
                    <button onClick={startMonitoring}>🎯 Iniciar Monitoramento</button>
                ) : (
                    <button onClick={stopMonitoring}>🛑 Parar Monitoramento</button>
                )}
            </div>
        </div>
    );
}
```

## 🔔 **4. Integração com Sistema de Notificações**

### **Usar notificações existentes do ClopFocus:**

```javascript
// No callback onFocusLoss
onFocusLoss: (data) => {
    // Usar o sistema de notificações existente
    if (window.electronAPI?.notifyFocusLoss) {
        window.electronAPI.notifyFocusLoss('Foco Perdido');
    }
    
    // Ou usar o sistema de toast existente
    if (window.toast) {
        window.toast({
            title: '🚨 Perda de Foco!',
            description: 'Você perdeu o foco na sessão. Volte para a tela!',
            duration: 5000
        });
    }
}
```

### **Personalizar notificações:**

```javascript
onFocusLoss: (data) => {
    const { focusScore, attention, focusLossCount } = data;
    
    // Notificação personalizada baseada no contexto
    const message = focusScore < 10 
        ? '🚨 Foco muito baixo! Concentre-se!'
        : '⚠️ Atenção caindo. Volte ao foco!';
    
    if (window.electronAPI?.notifyFocusLoss) {
        window.electronAPI.notifyFocusLoss(message);
    }
}
```

## 📊 **5. Métricas e Estatísticas**

### **Obter estatísticas da sessão:**

```javascript
// Usando o cliente JavaScript
const stats = gazeClient.getSessionStats();
console.log('📊 Estatísticas:', stats);

// Usando o hook React
const stats = getSessionStats();
console.log('📊 Estatísticas:', stats);
```

### **Exemplo de estatísticas retornadas:**

```json
{
  "sessionId": "clopfocus_1234567890_abc123",
  "isActive": true,
  "uptime": 300000, // 5 minutos em ms
  "focusPercentage": "85.2",
  "currentFocusScore": 78,
  "focusLossCount": 3,
  "attentionHistory": [0.8, 0.7, 0.9, 0.6, 0.8],
  "connectionStatus": "connected"
}
```

## 🎯 **6. Configurações Avançadas**

### **Ajustar thresholds de foco:**

```javascript
const gazeClient = window.initializeClopFocusGaze({
    focusThresholds: {
        attentionMin: 0.3,           // Atenção mínima (padrão: 0.4)
        gazeCenterThreshold: 0.5,    // Threshold para tela (padrão: 0.6)
        focusLossTimeout: 5000,      // Timeout perda foco (padrão: 3000ms)
        notificationCooldown: 15000  // Cooldown notificações (padrão: 10000ms)
    }
});
```

### **Configurar câmera específica:**

```javascript
// Para Mac M1, usar câmera 1
const gazeClient = window.initializeClopFocusGaze({
    cameraIndex: 1,
    frameRate: 15, // Reduzir FPS para melhor performance
    backendUrl: 'ws://localhost:8000'
});
```

## 🧪 **7. Testando a Integração**

### **Teste básico:**

```javascript
// No console do navegador
const client = window.initializeClopFocusGaze();

client.connect().then(() => {
    console.log('✅ Conectado!');
    return client.startMonitoring();
}).then(() => {
    console.log('🎯 Monitoramento iniciado!');
    
    // Ver estatísticas
    setInterval(() => {
        console.log('📊 Stats:', client.getSessionStats());
    }, 5000);
    
}).catch(console.error);
```

### **Verificar logs:**

```bash
# No terminal do backend
tail -f server.log

# Ver métricas em tempo real
curl http://localhost:8000/metrics | jq
```

## 🔧 **8. Troubleshooting**

### **Problemas comuns:**

1. **"Câmera não inicializa"**
   - Verificar permissões de câmera no macOS
   - Usar `cameraIndex: 1` no Mac M1
   - Verificar se outro app está usando a câmera

2. **"WebSocket não conecta"**
   - Verificar se backend está rodando em `localhost:8000`
   - Verificar logs do backend
   - Testar endpoint `/health`

3. **"Performance baixa"**
   - Reduzir `frameRate` para 10-15 FPS
   - Verificar se MediaPipe está usando Core ML
   - Monitorar métricas em `/metrics`

### **Logs úteis:**

```javascript
// Habilitar logs detalhados
const client = window.initializeClopFocusGaze({
    onConnectionChange: (status, error) => {
        console.log('🔗 Status:', status, error);
    },
    onGazeUpdate: (data) => {
        console.log('👁️ Gaze:', data);
    }
});
```

## 🚀 **9. Próximos Passos**

### **Melhorias futuras:**

- 📊 **Dashboard de métricas** em tempo real
- 🎯 **Calibração personalizada** por usuário
- 🔄 **Sincronização com estado** do ClopFocus
- 📱 **Notificações inteligentes** baseadas em padrões
- 🧠 **Machine Learning** para melhor detecção

### **Integração avançada:**

- **Store Zustand**: Integrar gaze data com estado global
- **Context API**: Compartilhar dados de gaze entre componentes
- **PWA**: Funcionar offline com cache de dados
- **Analytics**: Rastrear padrões de foco ao longo do tempo

---

## 🎉 **Resumo da Integração**

Agora você tem um sistema **completo e integrado** que:

1. ✅ **Monitora gaze em tempo real** via WebSocket
2. ✅ **Detecta automaticamente perda de foco**
3. ✅ **Integra com notificações** existentes do ClopFocus
4. ✅ **Fornece métricas detalhadas** de atenção
5. ✅ **Funciona perfeitamente no Mac M1** com otimizações

**Para começar:** Copie os arquivos de integração para seu projeto ClopFocus e siga os passos de configuração! 🚀✨
