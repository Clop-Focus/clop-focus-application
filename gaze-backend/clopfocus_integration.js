/**
 * Cliente JavaScript para integração com ClopFocus
 * Monitora gaze em tempo real e detecta perda de foco
 */

class ClopFocusGazeClient {
    constructor(options = {}) {
        this.options = {
            backendUrl: options.backendUrl || 'ws://localhost:8000',
            sessionId: options.sessionId || this.generateSessionId(),
            cameraIndex: options.cameraIndex || 1, // Usar câmera 1 que funciona
            frameRate: options.frameRate || 15, // FPS para processamento
            focusThresholds: {
                attentionMin: 0.4,
                gazeCenterThreshold: 0.6,
                focusLossTimeout: 3000, // 3 segundos
                notificationCooldown: 10000 // 10 segundos
            },
            ...options
        };

        this.websocket = null;
        this.camera = null;
        this.isConnected = false;
        this.isMonitoring = false;
        this.lastNotificationTime = 0;
        this.focusLossCount = 0;
        this.attentionHistory = [];
        
        // Callbacks para eventos
        this.onFocusLoss = options.onFocusLoss || this.defaultFocusLossHandler;
        this.onGazeUpdate = options.onGazeUpdate || this.defaultGazeUpdateHandler;
        this.onConnectionChange = options.onConnectionChange || this.defaultConnectionHandler;
        
        // Estado da sessão
        this.sessionState = {
            isActive: false,
            startTime: null,
            totalFocusTime: 0,
            totalDistractedTime: 0,
            currentFocusScore: 100
        };
    }

    /**
     * Gera ID único para a sessão
     */
    generateSessionId() {
        return `clopfocus_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    }

    /**
     * Inicia a conexão WebSocket com o backend
     */
    async connect() {
        try {
            const wsUrl = `${this.options.backendUrl.replace('http', 'ws')}/gaze/ws/${this.options.sessionId}`;
            
            this.websocket = new WebSocket(wsUrl);
            
            this.websocket.onopen = () => {
                console.log('🔗 Conectado ao backend de gaze');
                this.isConnected = true;
                this.onConnectionChange('connected');
            };

            this.websocket.onmessage = (event) => {
                this.handleWebSocketMessage(JSON.parse(event.data));
            };

            this.websocket.onclose = () => {
                console.log('🔌 Desconectado do backend de gaze');
                this.isConnected = false;
                this.isMonitoring = false;
                this.onConnectionChange('disconnected');
            };

            this.websocket.onerror = (error) => {
                console.error('❌ Erro na conexão WebSocket:', error);
                this.onConnectionChange('error', error);
            };

        } catch (error) {
            console.error('❌ Erro ao conectar:', error);
            throw error;
        }
    }

    /**
     * Inicia o monitoramento de gaze
     */
    async startMonitoring() {
        if (!this.isConnected) {
            throw new Error('WebSocket não está conectado');
        }

        try {
            // Inicializar câmera
            await this.initializeCamera();
            
            this.isMonitoring = true;
            this.sessionState.isActive = true;
            this.sessionState.startTime = Date.now();
            
            console.log('🎯 Monitoramento de gaze iniciado');
            
            // Iniciar loop de captura
            this.captureLoop();
            
        } catch (error) {
            console.error('❌ Erro ao iniciar monitoramento:', error);
            throw error;
        }
    }

    /**
     * Para o monitoramento de gaze
     */
    stopMonitoring() {
        this.isMonitoring = false;
        this.sessionState.isActive = false;
        
        if (this.camera) {
            this.camera.stop();
            this.camera = null;
        }
        
        console.log('🛑 Monitoramento de gaze parado');
    }

    /**
     * Inicializa a câmera
     */
    async initializeCamera() {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({
                video: {
                    deviceId: this.options.cameraIndex ? { exact: this.options.cameraIndex } : undefined,
                    width: { ideal: 1280 },
                    height: { ideal: 720 },
                    frameRate: { ideal: this.options.frameRate }
                }
            });

            this.camera = stream;
            console.log('📷 Câmera inicializada com sucesso');
            
        } catch (error) {
            console.error('❌ Erro ao inicializar câmera:', error);
            throw error;
        }
    }

    /**
     * Loop principal de captura de frames
     */
    async captureLoop() {
        if (!this.isMonitoring || !this.camera) return;

        try {
            // Capturar frame da câmera
            const frame = await this.captureFrame();
            
            if (frame) {
                // Enviar frame para o backend
                await this.sendFrame(frame);
            }

            // Agendar próximo frame
            setTimeout(() => this.captureLoop(), 1000 / this.options.frameRate);
            
        } catch (error) {
            console.error('❌ Erro no loop de captura:', error);
            // Tentar continuar mesmo com erro
            setTimeout(() => this.captureLoop(), 1000 / this.options.frameRate);
        }
    }

    /**
     * Captura um frame da câmera
     */
    async captureFrame() {
        try {
            // Criar canvas para capturar frame
            const canvas = document.createElement('canvas');
            const context = canvas.getContext('2d');
            
            // Obter track de vídeo
            const videoTrack = this.camera.getVideoTracks()[0];
            const imageCapture = new ImageCapture(videoTrack);
            
            // Capturar frame
            const bitmap = await imageCapture.grabFrame();
            
            // Desenhar no canvas
            canvas.width = bitmap.width;
            canvas.height = bitmap.height;
            context.drawImage(bitmap, 0, 0);
            
            // Converter para base64
            const frameData = canvas.toDataURL('image/jpeg', 0.9);
            const base64Data = frameData.split(',')[1];
            
            return base64Data;
            
        } catch (error) {
            console.error('❌ Erro ao capturar frame:', error);
            return null;
        }
    }

    /**
     * Envia frame para o backend via WebSocket
     */
    async sendFrame(frameData) {
        if (!this.isConnected || !this.websocket) return;

        try {
            const message = {
                type: 'frame',
                data: frameData,
                timestamp: Date.now()
            };

            this.websocket.send(JSON.stringify(message));
            
        } catch (error) {
            console.error('❌ Erro ao enviar frame:', error);
        }
    }

    /**
     * Processa mensagens recebidas do WebSocket
     */
    handleWebSocketMessage(data) {
        switch (data.type) {
            case 'connection':
                console.log('✅ Conexão estabelecida:', data.status);
                break;
                
            case 'gaze':
                this.handleGazeUpdate(data);
                break;
                
            case 'focus_alert':
                this.handleFocusAlert(data);
                break;
                
            case 'stats':
                console.log('📊 Estatísticas da sessão:', data.data);
                break;
                
            default:
                console.log('📨 Mensagem recebida:', data);
        }
    }

    /**
     * Processa atualização de gaze
     */
    handleGazeUpdate(data) {
        const { gaze, attention, on_screen, focus_analysis } = data;
        
        // Atualizar estado da sessão
        this.updateSessionState(focus_analysis);
        
        // Adicionar à história de atenção
        this.attentionHistory.push(attention);
        if (this.attentionHistory.length > 30) {
            this.attentionHistory.shift();
        }
        
        // Chamar callback de atualização
        this.onGazeUpdate({
            gaze,
            attention,
            on_screen,
            focus_analysis,
            sessionState: this.sessionState,
            timestamp: data.timestamp
        });
    }

    /**
     * Processa alerta de perda de foco
     */
    handleFocusAlert(data) {
        const { alert_type, data: alertData } = data;
        
        if (alert_type === 'focus_loss') {
            this.focusLossCount++;
            
            // Verificar cooldown para notificação
            const now = Date.now();
            if (now - this.lastNotificationTime > this.options.focusThresholds.notificationCooldown) {
                this.lastNotificationTime = now;
                
                // Chamar callback de perda de foco
                this.onFocusLoss({
                    focusScore: alertData.focus_score,
                    attention: alertData.attention,
                    focusLossCount: this.focusLossCount,
                    sessionState: this.sessionState
                });
            }
        }
    }

    /**
     * Atualiza estado da sessão
     */
    updateSessionState(focusAnalysis) {
        const { focus_score, status } = focusAnalysis;
        
        this.sessionState.currentFocusScore = focus_score;
        
        // Calcular tempo focado vs distraído
        const now = Date.now();
        const timeDiff = now - (this.sessionState.lastUpdate || now);
        
        if (status === 'focused' || status === 'wavering') {
            this.sessionState.totalFocusTime += timeDiff;
        } else {
            this.sessionState.totalDistractedTime += timeDiff;
        }
        
        this.sessionState.lastUpdate = now;
    }

    /**
     * Obtém estatísticas da sessão
     */
    getSessionStats() {
        const totalTime = Date.now() - this.sessionState.startTime;
        const focusPercentage = totalTime > 0 ? (this.sessionState.totalFocusTime / totalTime) * 100 : 0;
        
        return {
            sessionId: this.options.sessionId,
            isActive: this.sessionState.isActive,
            uptime: totalTime,
            focusPercentage: focusPercentage.toFixed(1),
            currentFocusScore: this.sessionState.currentFocusScore,
            focusLossCount: this.focusLossCount,
            attentionHistory: this.attentionHistory.slice(-10), // Últimos 10 valores
            connectionStatus: this.isConnected ? 'connected' : 'disconnected'
        };
    }

    /**
     * Desconecta do backend
     */
    disconnect() {
        this.stopMonitoring();
        
        if (this.websocket) {
            this.websocket.close();
            this.websocket = null;
        }
        
        this.isConnected = false;
        console.log('🔌 Desconectado do backend de gaze');
    }

    // Handlers padrão
    defaultFocusLossHandler(data) {
        console.log('🚨 PERDA DE FOCO DETECTADA:', data);
        
        // Aqui você pode integrar com o sistema de notificações do ClopFocus
        if (window.electronAPI && window.electronAPI.notifyFocusLoss) {
            window.electronAPI.notifyFocusLoss('Foco Perdido');
        }
    }

    defaultGazeUpdateHandler(data) {
        // Log silencioso para não poluir o console
        if (data.focus_analysis.status === 'focus_lost') {
            console.log('👁️ Gaze atualizado:', data.focus_analysis.status);
        }
    }

    defaultConnectionHandler(status, error) {
        console.log('🔗 Status da conexão:', status);
        if (error) {
            console.error('❌ Erro de conexão:', error);
        }
    }
}

// Exportar para uso global
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ClopFocusGazeClient;
} else if (typeof window !== 'undefined') {
    window.ClopFocusGazeClient = ClopFocusGazeClient;
}

// Exemplo de uso para ClopFocus
if (typeof window !== 'undefined') {
    // Função para inicializar o cliente de gaze no ClopFocus
    window.initializeClopFocusGaze = function(options = {}) {
        const client = new ClopFocusGazeClient({
            ...options,
            onFocusLoss: (data) => {
                // Integrar com o sistema de notificações do ClopFocus
                console.log('🚨 ClopFocus: Perda de foco detectada!', data);
                
                // Aqui você pode chamar as funções do ClopFocus
                if (window.clopFocusStore) {
                    window.clopFocusStore.getState().notifyFocusLoss(data);
                }
            },
            onGazeUpdate: (data) => {
                // Atualizar UI do ClopFocus com dados de gaze
                if (window.clopFocusStore) {
                    window.clopFocusStore.getState().updateGazeData(data);
                }
            }
        });

        return client;
    };
}
