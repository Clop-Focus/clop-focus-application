import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Button } from './ui/button';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { Progress } from './ui/progress';
import { Alert, AlertDescription } from './ui/alert';
import { Separator } from './ui/separator';
import { Camera, Play, Pause, Square, Settings, Wifi, WifiOff, Eye, Target } from 'lucide-react';

interface BothModsData {
  status: string;
  face_away?: boolean;
  debug_log?: string[];
  timestamp?: string;
  message?: string;
  processed_image?: string;
  face_detections?: number;
  pose_detections?: number;
}

interface ServerStatus {
  models_loaded: boolean;
  is_processing: boolean;
  clients_connected: number;
  timestamp: string;
}

interface BothModsIntegrationProps {
  onFaceAwayChange?: (faceAway: boolean | null) => void;
  onDebugLog?: (log: string[]) => void;
  cameraStream?: MediaStream | null;
  videoRef?: React.RefObject<HTMLVideoElement>;
  isActive?: boolean;
}

const BothModsIntegration: React.FC<BothModsIntegrationProps> = ({ 
  onFaceAwayChange, 
  onDebugLog, 
  cameraStream, 
  videoRef,
  isActive = true 
}) => {
  const [isConnected, setIsConnected] = useState(false);
  const [faceAway, setFaceAway] = useState<boolean | null>(null);
  const [debugLog, setDebugLog] = useState<string[]>([]);
  const [serverStatus, setServerStatus] = useState<ServerStatus | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [processedImage, setProcessedImage] = useState<string | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const processingIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const WS_URL = 'ws://localhost:8767';

  // WebSocket connection management
  const connectWebSocket = useCallback(() => {
    try {
      wsRef.current = new WebSocket(WS_URL);
      wsRef.current.onopen = () => {
        console.log('🔗 Conectado ao servidor BothMods');
        setIsConnected(true);
        setError(null);
        // Request status
        if (wsRef.current?.readyState === WebSocket.OPEN) {
          wsRef.current.send(JSON.stringify({ type: 'status' }));
        }
      };
      wsRef.current.onmessage = (event) => {
        try {
          const data: BothModsData | ServerStatus = JSON.parse(event.data);
          if ('models_loaded' in data) {
            setServerStatus(data as ServerStatus);
          } else {
            const bothModsData = data as BothModsData;
            if (bothModsData.status === 'success') {
              setFaceAway(bothModsData.face_away ?? null);
              setDebugLog(bothModsData.debug_log ?? []);
              if (bothModsData.processed_image) {
                setProcessedImage(bothModsData.processed_image);
              }
              if (onFaceAwayChange) onFaceAwayChange(bothModsData.face_away ?? null);
              if (onDebugLog) onDebugLog(bothModsData.debug_log ?? []);
            } else if (bothModsData.status === 'error') {
              setError(bothModsData.message || 'Erro desconhecido');
            }
          }
        } catch (e) {
          console.error('Erro ao processar mensagem:', e);
          setError('Erro ao processar resposta do servidor');
        }
      };
      wsRef.current.onerror = (error) => {
        console.error('Erro WebSocket:', error);
        setError('Erro de conexão com o servidor');
        setIsConnected(false);
      };
      wsRef.current.onclose = () => {
        console.log('🔌 Desconectado do servidor');
        setIsConnected(false);
      };
    } catch (e) {
      console.error('Erro ao conectar:', e);
      setError('Erro ao conectar com o servidor');
    }
  }, [onFaceAwayChange, onDebugLog]);

  const disconnectWebSocket = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
  }, []);

  // Capture frame from video and send to server
  const captureAndProcessFrame = useCallback(() => {
    if (!videoRef?.current || !canvasRef.current || !wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
      return;
    }

    try {
      const video = videoRef.current;
      const canvas = canvasRef.current;
      const ctx = canvas.getContext('2d');
      
      if (!ctx) return;

      // Set canvas size to match video
      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;
      
      // Draw video frame to canvas
      ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
      
      // Convert to base64
      const imageData = canvas.toDataURL('image/jpeg', 0.8);
      const base64Data = imageData.split(',')[1]; // Remove data:image/jpeg;base64, prefix
      
      // Send to server
      wsRef.current.send(JSON.stringify({
        type: 'process_frame',
        frame_data: base64Data
      }));
      
      setIsProcessing(true);
    } catch (e) {
      console.error('Erro ao capturar frame:', e);
    }
  }, [videoRef]);

  // Start/stop frame processing
  const startFrameProcessing = useCallback(() => {
    if (isConnected && cameraStream && isActive) {
      // Process frame every 500ms
      processingIntervalRef.current = setInterval(captureAndProcessFrame, 500);
    }
  }, [isConnected, cameraStream, isActive, captureAndProcessFrame]);

  const stopFrameProcessing = useCallback(() => {
    if (processingIntervalRef.current) {
      clearInterval(processingIntervalRef.current);
      processingIntervalRef.current = null;
    }
    setIsProcessing(false);
  }, []);

  // Connect on mount
  useEffect(() => {
    connectWebSocket();
    return () => {
      disconnectWebSocket();
    };
  }, [connectWebSocket, disconnectWebSocket]);

  // Start/stop processing based on connection and camera state
  useEffect(() => {
    if (isConnected && cameraStream && isActive) {
      startFrameProcessing();
    } else {
      stopFrameProcessing();
    }

    return () => {
      stopFrameProcessing();
    };
  }, [isConnected, cameraStream, isActive, startFrameProcessing, stopFrameProcessing]);

  return (
    <div className="space-y-4">
      {/* Status Cards */}
      <div className="grid grid-cols-2 gap-3">
        <Card className="border-primary/20 bg-primary/5">
          <CardContent className="p-3 text-center">
            <div className="flex items-center justify-center gap-2 mb-1">
              <Badge variant={isConnected ? "default" : "destructive"} className="text-xs">
                {isConnected ? <Wifi className="h-3 w-3" /> : <WifiOff className="h-3 w-3" />}
                {isConnected ? "Conectado" : "Desconectado"}
              </Badge>
            </div>
            <p className="text-xs text-muted-foreground">BothMods Server</p>
          </CardContent>
        </Card>
        
        <Card className="border-blue-500/20 bg-blue-500/5">
          <CardContent className="p-3 text-center">
            <div className="flex items-center justify-center gap-2 mb-1">
              <Badge variant={isProcessing ? "secondary" : "outline"} className="text-xs">
                <Eye className="h-3 w-3" />
                {isProcessing ? "Processando" : "Aguardando"}
              </Badge>
            </div>
            <p className="text-xs text-muted-foreground">Face Tracking</p>
          </CardContent>
        </Card>
      </div>

      {/* Face Away Status */}
      {faceAway !== null && (
        <Card className={faceAway ? "border-red-500/20 bg-red-500/5" : "border-green-500/20 bg-green-500/5"}>
          <CardContent className="p-4 text-center">
            <div className="flex items-center justify-center gap-2 mb-2">
              <Target className={`h-5 w-5 ${faceAway ? "text-red-500" : "text-green-500"}`} />
              <span className={`font-bold text-lg ${faceAway ? "text-red-600" : "text-green-600"}`}>
                {faceAway ? 'Rosto Virado' : 'Rosto Visível'}
              </span>
            </div>
            {faceAway && (
              <p className="text-sm text-red-600 font-medium">⚠️ Atenção: O rosto está virado para longe da câmera!</p>
            )}
          </CardContent>
        </Card>
      )}

      {/* Processed Image Display */}
      {processedImage && (
        <Card>
          <CardContent className="p-4">
            <h4 className="text-sm font-medium text-muted-foreground mb-3">Tracking do Rosto</h4>
            <div className="relative">
              <img 
                src={`data:image/jpeg;base64,${processedImage}`}
                alt="Processed frame with face tracking"
                className="w-full h-48 object-cover rounded-lg border-2 border-primary/20"
              />
              {faceAway && (
                <div className="absolute top-2 left-2">
                  <Badge variant="destructive" className="text-xs">
                    FACE AWAY
                  </Badge>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Error Display */}
      {error && (
        <Alert variant="destructive">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {/* Debug Log */}
      {debugLog.length > 0 && (
        <Card>
          <CardContent className="p-4">
            <h4 className="text-sm font-medium text-muted-foreground mb-2">Debug Log</h4>
            <div className="bg-gray-100 rounded p-2 text-xs overflow-auto max-h-24">
              <pre className="whitespace-pre-wrap">{debugLog.slice(-5).join('\n')}</pre>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Hidden canvas for frame capture */}
      <canvas ref={canvasRef} style={{ display: 'none' }} />
    </div>
  );
};

export default BothModsIntegration;
