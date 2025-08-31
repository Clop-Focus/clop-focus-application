import { useState, useEffect, useCallback, useRef } from 'react';

interface DetectionResult {
  timestamp: string;
  has_face: boolean;
  has_pose: boolean;
  face_count: number;
  pose_count: number;
  confidence: number;
  error?: string;
}

interface FocusStatus {
  focus_lost: boolean;
  time_since_detection: number;
  focus_loss_count: number;
  total_focus_loss_time: number;
}

interface SessionStatistics {
  session_duration: number;
  total_frames_processed: number;
  frames_with_detection: number;
  detection_rate: number;
  focus_loss_count: number;
  total_focus_loss_time: number;
  average_focus_loss_duration: number;
}

interface FocusMonitorMessage {
  type: 'detection_result' | 'focus_loss_notification' | 'session_started' | 'session_stopped' | 'status' | 'error';
  timestamp: string;
  detection?: DetectionResult;
  focus_status?: FocusStatus;
  session_stats?: SessionStatistics;
  message?: string;
  config?: any;
  settings?: any;
}

interface FocusMonitorConfig {
  confidence_threshold: number;
  focus_loss_threshold: number;
}

interface FocusMonitorSettings {
  confidence_threshold?: number;
  focus_loss_threshold?: number;
}

export interface UseFocusMonitorReturn {
  // Estado da conexão
  isConnected: boolean;
  isMonitoring: boolean;
  connectionError: string | null;
  
  // Dados de detecção
  lastDetection: DetectionResult | null;
  focusStatus: FocusStatus | null;
  sessionStats: SessionStatistics | null;
  
  // Contadores
  focusLossCount: number;
  totalFocusLossTime: number;
  
  // Funções
  connect: () => Promise<void>;
  disconnect: () => void;
  startSession: (config?: FocusMonitorConfig) => Promise<void>;
  stopSession: () => Promise<void>;
  updateSettings: (settings: FocusMonitorSettings) => Promise<void>;
  getStatus: () => Promise<void>;
  
  // Eventos
  onFocusLoss: (callback: (focusStatus: FocusStatus) => void) => void;
  onDetectionUpdate: (callback: (detection: DetectionResult) => void) => void;
  onSessionUpdate: (callback: (stats: SessionStatistics) => void) => void;
}

export const useFocusMonitor = (websocketUrl: string = 'ws://localhost:8765'): UseFocusMonitorReturn => {
  const [isConnected, setIsConnected] = useState(false);
  const [isMonitoring, setIsMonitoring] = useState(false);
  const [connectionError, setConnectionError] = useState<string | null>(null);
  
  const [lastDetection, setLastDetection] = useState<DetectionResult | null>(null);
  const [focusStatus, setFocusStatus] = useState<FocusStatus | null>(null);
  const [sessionStats, setSessionStats] = useState<SessionStatistics | null>(null);
  
  const [focusLossCount, setFocusLossCount] = useState(0);
  const [totalFocusLossTime, setTotalFocusLossTime] = useState(0);
  
  const websocketRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const reconnectAttemptsRef = useRef(0);
  const maxReconnectAttempts = 5;
  
  // Callbacks para eventos
  const focusLossCallbacksRef = useRef<((focusStatus: FocusStatus) => void)[]>([]);
  const detectionUpdateCallbacksRef = useRef<((detection: DetectionResult) => void)[]>([]);
  const sessionUpdateCallbacksRef = useRef<((stats: SessionStatistics) => void)[]>([]);
  
  // Função para enviar mensagens
  const sendMessage = useCallback((message: any) => {
    if (websocketRef.current && websocketRef.current.readyState === WebSocket.OPEN) {
      websocketRef.current.send(JSON.stringify(message));
    } else {
      console.warn('WebSocket não está conectado');
    }
  }, []);
  
  // Função para processar mensagens recebidas
  const handleMessage = useCallback((event: MessageEvent) => {
    try {
      const data: FocusMonitorMessage = JSON.parse(event.data);
      
      switch (data.type) {
        case 'detection_result':
          if (data.detection) {
            setLastDetection(data.detection);
            detectionUpdateCallbacksRef.current.forEach(callback => callback(data.detection!));
          }
          if (data.focus_status) {
            setFocusStatus(data.focus_status);
            setFocusLossCount(data.focus_status.focus_loss_count);
            setTotalFocusLossTime(data.focus_status.total_focus_loss_time);
          }
          if (data.session_stats) {
            setSessionStats(data.session_stats);
            sessionUpdateCallbacksRef.current.forEach(callback => callback(data.session_stats!));
          }
          break;
          
        case 'focus_loss_notification':
          if (data.focus_status) {
            setFocusStatus(data.focus_status);
            setFocusLossCount(data.focus_status.focus_loss_count);
            setTotalFocusLossTime(data.focus_status.total_focus_loss_time);
            
            // Executar callbacks de perda de foco
            focusLossCallbacksRef.current.forEach(callback => callback(data.focus_status!));
          }
          break;
          
        case 'session_started':
          setIsMonitoring(true);
          console.log('Sessão de monitoramento iniciada:', data.config);
          break;
          
        case 'session_stopped':
          setIsMonitoring(false);
          if (data.statistics) {
            setSessionStats(data.statistics);
          }
          console.log('Sessão de monitoramento parada');
          break;
          
        case 'status':
          setIsMonitoring(data.is_monitoring || false);
          if (data.session_stats) {
            setSessionStats(data.session_stats);
          }
          break;
          
        case 'error':
          console.error('Erro do servidor:', data.message);
          setConnectionError(data.message || 'Erro desconhecido');
          break;
          
        default:
          console.warn('Tipo de mensagem desconhecido:', data.type);
      }
    } catch (error) {
      console.error('Erro ao processar mensagem:', error);
    }
  }, []);
  
  // Função para conectar ao WebSocket
  const connect = useCallback(async () => {
    try {
      setConnectionError(null);
      
      if (websocketRef.current) {
        websocketRef.current.close();
      }
      
      const ws = new WebSocket(websocketUrl);
      websocketRef.current = ws;
      
      ws.onopen = () => {
        console.log('Conectado ao serviço de monitoramento de foco');
        setIsConnected(true);
        reconnectAttemptsRef.current = 0;
        
        // Solicitar status atual
        sendMessage({ type: 'get_status' });
      };
      
      ws.onmessage = handleMessage;
      
      ws.onclose = (event) => {
        console.log('Conexão fechada:', event.code, event.reason);
        setIsConnected(false);
        setIsMonitoring(false);
        
        // Tentar reconectar se não foi fechamento intencional
        if (event.code !== 1000 && reconnectAttemptsRef.current < maxReconnectAttempts) {
          reconnectAttemptsRef.current++;
          const delay = Math.min(1000 * Math.pow(2, reconnectAttemptsRef.current), 10000);
          
          reconnectTimeoutRef.current = setTimeout(() => {
            console.log(`Tentativa de reconexão ${reconnectAttemptsRef.current}/${maxReconnectAttempts}`);
            connect();
          }, delay);
        }
      };
      
      ws.onerror = (error) => {
        console.error('Erro na conexão WebSocket:', error);
        setConnectionError('Erro na conexão com o serviço de monitoramento');
      };
      
    } catch (error) {
      console.error('Erro ao conectar:', error);
      setConnectionError('Falha ao conectar com o serviço de monitoramento');
    }
  }, [websocketUrl, handleMessage, sendMessage]);
  
  // Função para desconectar
  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
    
    if (websocketRef.current) {
      websocketRef.current.close(1000, 'Desconexão solicitada pelo usuário');
      websocketRef.current = null;
    }
    
    setIsConnected(false);
    setIsMonitoring(false);
    setConnectionError(null);
  }, []);
  
  // Função para iniciar sessão
  const startSession = useCallback(async (config?: FocusMonitorConfig) => {
    const sessionConfig = config || {
      confidence_threshold: 0.75,
      focus_loss_threshold: 3.0
    };
    
    sendMessage({
      type: 'start_session',
      config: sessionConfig
    });
  }, [sendMessage]);
  
  // Função para parar sessão
  const stopSession = useCallback(async () => {
    sendMessage({ type: 'stop_session' });
  }, [sendMessage]);
  
  // Função para atualizar configurações
  const updateSettings = useCallback(async (settings: FocusMonitorSettings) => {
    sendMessage({
      type: 'update_settings',
      settings
    });
  }, [sendMessage]);
  
  // Função para obter status
  const getStatus = useCallback(async () => {
    sendMessage({ type: 'get_status' });
  }, [sendMessage]);
  
  // Função para registrar callback de perda de foco
  const onFocusLoss = useCallback((callback: (focusStatus: FocusStatus) => void) => {
    focusLossCallbacksRef.current.push(callback);
    
    // Retornar função para remover callback
    return () => {
      const index = focusLossCallbacksRef.current.indexOf(callback);
      if (index > -1) {
        focusLossCallbacksRef.current.splice(index, 1);
      }
    };
  }, []);
  
  // Função para registrar callback de atualização de detecção
  const onDetectionUpdate = useCallback((callback: (detection: DetectionResult) => void) => {
    detectionUpdateCallbacksRef.current.push(callback);
    
    // Retornar função para remover callback
    return () => {
      const index = detectionUpdateCallbacksRef.current.indexOf(callback);
      if (index > -1) {
        detectionUpdateCallbacksRef.current.splice(index, 1);
      }
    };
  }, []);
  
  // Função para registrar callback de atualização de sessão
  const onSessionUpdate = useCallback((callback: (stats: SessionStatistics) => void) => {
    sessionUpdateCallbacksRef.current.push(callback);
    
    // Retornar função para remover callback
    return () => {
      const index = sessionUpdateCallbacksRef.current.indexOf(callback);
      if (index > -1) {
        sessionUpdateCallbacksRef.current.splice(index, 1);
      }
    };
  }, []);
  
  // Conectar automaticamente quando o hook é montado
  useEffect(() => {
    connect();
    
    // Limpar na desmontagem
    return () => {
      disconnect();
    };
  }, [connect, disconnect]);
  
  return {
    // Estado da conexão
    isConnected,
    isMonitoring,
    connectionError,
    
    // Dados de detecção
    lastDetection,
    focusStatus,
    sessionStats,
    
    // Contadores
    focusLossCount,
    totalFocusLossTime,
    
    // Funções
    connect,
    disconnect,
    startSession,
    stopSession,
    updateSettings,
    getStatus,
    
    // Eventos
    onFocusLoss,
    onDetectionUpdate,
    onSessionUpdate
  };
};

