/**
 * Hook React para integração com sistema de gaze detection
 * Monitora atenção do usuário e detecta perda de foco
 */

import { useState, useEffect, useRef, useCallback } from 'react';

interface GazeData {
  gaze: {
    h: number; // -1 (esquerda) a +1 (direita)
    v: number; // -1 (baixo) a +1 (cima)
  };
  attention: number; // 0 (distraído) a 1 (focado)
  on_screen: boolean;
  focus_analysis: {
    status: 'focused' | 'wavering' | 'distracted' | 'focus_lost';
    focus_score: number; // 0-100
    attention_trend: number;
    focus_loss_detected: boolean;
    focus_loss_count: number;
  };
}

interface GazeSessionState {
  isActive: boolean;
  startTime: number | null;
  totalFocusTime: number;
  totalDistractedTime: number;
  currentFocusScore: number;
}

interface UseGazeDetectionOptions {
  backendUrl?: string;
  sessionId?: string;
  cameraIndex?: number;
  frameRate?: number;
  autoStart?: boolean;
  onFocusLoss?: (data: any) => void;
  onGazeUpdate?: (data: GazeData) => void;
  onConnectionChange?: (status: string, error?: any) => void;
}

interface UseGazeDetectionReturn {
  // Estado
  isConnected: boolean;
  isMonitoring: boolean;
  gazeData: GazeData | null;
  sessionState: GazeSessionState;
  connectionStatus: 'disconnected' | 'connecting' | 'connected' | 'error';
  
  // Métodos
  connect: () => Promise<void>;
  disconnect: () => void;
  startMonitoring: () => Promise<void>;
  stopMonitoring: () => void;
  getSessionStats: () => any;
  
  // Estatísticas
  focusLossCount: number;
  attentionHistory: number[];
  currentFocusScore: number;
  focusPercentage: number;
}

export function useGazeDetection(options: UseGazeDetectionOptions = {}): UseGazeDetectionReturn {
  // Estado interno
  const [isConnected, setIsConnected] = useState(false);
  const [isMonitoring, setIsMonitoring] = useState(false);
  const [gazeData, setGazeData] = useState<GazeData | null>(null);
  const [connectionStatus, setConnectionStatus] = useState<'disconnected' | 'connecting' | 'connected' | 'error'>('disconnected');
  const [focusLossCount, setFocusLossCount] = useState(0);
  const [attentionHistory, setAttentionHistory] = useState<number[]>([]);
  const [currentFocusScore, setCurrentFocusScore] = useState(100);
  const [focusPercentage, setFocusPercentage] = useState(100);

  // Estado da sessão
  const [sessionState, setSessionState] = useState<GazeSessionState>({
    isActive: false,
    startTime: null,
    totalFocusTime: 0,
    totalDistractedTime: 0,
    currentFocusScore: 100
  });

  // Refs
  const clientRef = useRef<any>(null);
  const websocketRef = useRef<WebSocket | null>(null);

  // Configurações padrão
  const config = {
    backendUrl: options.backendUrl || 'ws://localhost:8000',
    sessionId: options.sessionId || `clopfocus_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
    cameraIndex: options.cameraIndex || 1,
    frameRate: options.frameRate || 15,
    autoStart: options.autoStart || false,
    ...options
  };

  // Callbacks
  const handleFocusLoss = useCallback((data: any) => {
    setFocusLossCount(prev => prev + 1);
    options.onFocusLoss?.(data);
  }, [options.onFocusLoss]);

  const handleGazeUpdate = useCallback((data: GazeData) => {
    setGazeData(data);
    
    // Atualizar score de foco
    const focusScore = data.focus_analysis.focus_score;
    setCurrentFocusScore(focusScore);
    
    // Atualizar história de atenção
    setAttentionHistory(prev => {
      const newHistory = [...prev, data.attention];
      return newHistory.slice(-30); // Manter últimos 30 valores
    });
    
    // Atualizar estado da sessão
    setSessionState(prev => {
      const now = Date.now();
      const timeDiff = now - (prev.lastUpdate || now);
      
      let newTotalFocusTime = prev.totalFocusTime;
      let newTotalDistractedTime = prev.totalDistractedTime;
      
      if (data.focus_analysis.status === 'focused' || data.focus_analysis.status === 'wavering') {
        newTotalFocusTime += timeDiff;
      } else {
        newTotalDistractedTime += timeDiff;
      }
      
      const totalTime = newTotalFocusTime + newTotalDistractedTime;
      const newFocusPercentage = totalTime > 0 ? (newTotalFocusTime / totalTime) * 100 : 100;
      
      setFocusPercentage(newFocusPercentage);
      
      return {
        ...prev,
        totalFocusTime: newTotalFocusTime,
        totalDistractedTime: newTotalDistractedTime,
        currentFocusScore: focusScore,
        lastUpdate: now
      };
    });
    
    options.onGazeUpdate?.(data);
  }, [options.onGazeUpdate]);

  const handleConnectionChange = useCallback((status: string, error?: any) => {
    switch (status) {
      case 'connected':
        setIsConnected(true);
        setConnectionStatus('connected');
        break;
      case 'disconnected':
        setIsConnected(false);
        setIsMonitoring(false);
        setConnectionStatus('disconnected');
        break;
      case 'error':
        setConnectionStatus('error');
        break;
    }
    
    options.onConnectionChange?.(status, error);
  }, [options.onConnectionChange]);

  // Conectar ao backend
  const connect = useCallback(async () => {
    try {
      setConnectionStatus('connecting');
      
      const wsUrl = `${config.backendUrl.replace('http', 'ws')}/gaze/ws/${config.sessionId}`;
      const websocket = new WebSocket(wsUrl);
      
      websocket.onopen = () => {
        console.log('🔗 Conectado ao backend de gaze');
        handleConnectionChange('connected');
      };

      websocket.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          handleWebSocketMessage(data);
        } catch (error) {
          console.error('❌ Erro ao processar mensagem:', error);
        }
      };

      websocket.onclose = () => {
        console.log('🔌 Desconectado do backend de gaze');
        handleConnectionChange('disconnected');
      };

      websocket.onerror = (error) => {
        console.error('❌ Erro na conexão WebSocket:', error);
        handleConnectionChange('error', error);
      };

      websocketRef.current = websocket;
      
    } catch (error) {
      console.error('❌ Erro ao conectar:', error);
      setConnectionStatus('error');
      throw error;
    }
  }, [config.backendUrl, config.sessionId, handleConnectionChange]);

  // Desconectar
  const disconnect = useCallback(() => {
    if (websocketRef.current) {
      websocketRef.current.close();
      websocketRef.current = null;
    }
    
    setIsConnected(false);
    setIsMonitoring(false);
    setConnectionStatus('disconnected');
  }, []);

  // Iniciar monitoramento
  const startMonitoring = useCallback(async () => {
    if (!isConnected) {
      throw new Error('WebSocket não está conectado');
    }

    try {
      // Inicializar câmera
      await initializeCamera();
      
      setIsMonitoring(true);
      setSessionState(prev => ({
        ...prev,
        isActive: true,
        startTime: Date.now()
      }));
      
      console.log('🎯 Monitoramento de gaze iniciado');
      
      // Iniciar loop de captura
      startCaptureLoop();
      
    } catch (error) {
      console.error('❌ Erro ao iniciar monitoramento:', error);
      throw error;
    }
  }, [isConnected]);

  // Parar monitoramento
  const stopMonitoring = useCallback(() => {
    setIsMonitoring(false);
    setSessionState(prev => ({
      ...prev,
      isActive: false
    }));
    
    if (clientRef.current?.camera) {
      clientRef.current.camera.stop();
      clientRef.current.camera = null;
    }
    
    console.log('🛑 Monitoramento de gaze parado');
  }, []);

  // Inicializar câmera
  const initializeCamera = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: {
          deviceId: config.cameraIndex ? { exact: config.cameraIndex } : undefined,
          width: { ideal: 1280 },
          height: { ideal: 720 },
          frameRate: { ideal: config.frameRate }
        }
      });

      clientRef.current = { camera: stream };
      console.log('📷 Câmera inicializada com sucesso');
      
    } catch (error) {
      console.error('❌ Erro ao inicializar câmera:', error);
      throw error;
    }
  }, [config.cameraIndex, config.frameRate]);

  // Loop de captura
  const startCaptureLoop = useCallback(() => {
    if (!isMonitoring || !clientRef.current?.camera) return;

    const captureFrame = async () => {
      try {
        const frame = await captureFrameFromCamera();
        
        if (frame && websocketRef.current) {
          // Enviar frame para o backend
          const message = {
            type: 'frame',
            data: frame,
            timestamp: Date.now()
          };

          websocketRef.current.send(JSON.stringify(message));
        }

        // Agendar próximo frame
        if (isMonitoring) {
          setTimeout(captureFrame, 1000 / config.frameRate);
        }
        
      } catch (error) {
        console.error('❌ Erro no loop de captura:', error);
        // Tentar continuar mesmo com erro
        if (isMonitoring) {
          setTimeout(captureFrame, 1000 / config.frameRate);
        }
      }
    };

    captureFrame();
  }, [isMonitoring, config.frameRate]);

  // Capturar frame da câmera
  const captureFrameFromCamera = useCallback(async () => {
    try {
      if (!clientRef.current?.camera) return null;

      // Criar canvas para capturar frame
      const canvas = document.createElement('canvas');
      const context = canvas.getContext('2d');
      
      // Obter track de vídeo
      const videoTrack = clientRef.current.camera.getVideoTracks()[0];
      const imageCapture = new ImageCapture(videoTrack);
      
      // Capturar frame
      const bitmap = await imageCapture.grabFrame();
      
      // Desenhar no canvas
      canvas.width = bitmap.width;
      canvas.height = bitmap.height;
      context?.drawImage(bitmap, 0, 0);
      
      // Converter para base64
      const frameData = canvas.toDataURL('image/jpeg', 0.9);
      const base64Data = frameData.split(',')[1];
      
      return base64Data;
      
    } catch (error) {
      console.error('❌ Erro ao capturar frame:', error);
      return null;
    }
  }, []);

  // Processar mensagens do WebSocket
  const handleWebSocketMessage = useCallback((data: any) => {
    switch (data.type) {
      case 'connection':
        console.log('✅ Conexão estabelecida:', data.status);
        break;
        
      case 'gaze':
        handleGazeUpdate(data);
        break;
        
      case 'focus_alert':
        if (data.alert_type === 'focus_loss') {
          handleFocusLoss(data.data);
        }
        break;
        
      case 'stats':
        console.log('📊 Estatísticas da sessão:', data.data);
        break;
        
      default:
        console.log('📨 Mensagem recebida:', data);
    }
  }, [handleGazeUpdate, handleFocusLoss]);

  // Obter estatísticas da sessão
  const getSessionStats = useCallback(() => {
    const totalTime = sessionState.startTime ? Date.now() - sessionState.startTime : 0;
    
    return {
      sessionId: config.sessionId,
      isActive: sessionState.isActive,
      uptime: totalTime,
      focusPercentage: focusPercentage.toFixed(1),
      currentFocusScore: currentFocusScore,
      focusLossCount: focusLossCount,
      attentionHistory: attentionHistory.slice(-10),
      connectionStatus: connectionStatus
    };
  }, [config.sessionId, sessionState, focusPercentage, currentFocusScore, focusLossCount, attentionHistory, connectionStatus]);

  // Efeitos
  useEffect(() => {
    if (config.autoStart) {
      connect();
    }

    return () => {
      disconnect();
    };
  }, [config.autoStart, connect, disconnect]);

  // Retornar interface
  return {
    // Estado
    isConnected,
    isMonitoring,
    gazeData,
    sessionState,
    connectionStatus,
    
    // Métodos
    connect,
    disconnect,
    startMonitoring,
    stopMonitoring,
    getSessionStats,
    
    // Estatísticas
    focusLossCount,
    attentionHistory,
    currentFocusScore,
    focusPercentage
  };
}
