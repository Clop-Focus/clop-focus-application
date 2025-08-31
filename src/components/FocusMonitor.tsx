import React, { useEffect, useState } from 'react';
import { useFocusMonitor } from '../hooks/useFocusMonitor';
import { Button } from './ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { Progress } from './ui/progress';
import { Alert, AlertDescription } from './ui/alert';
import { Separator } from './ui/separator';
import { 
  Eye, 
  EyeOff, 
  Play, 
  Pause, 
  Settings, 
  Wifi, 
  WifiOff, 
  AlertTriangle,
  CheckCircle,
  Clock,
  Activity
} from 'lucide-react';
import { toast } from 'sonner';

interface FocusMonitorProps {
  onFocusLoss?: (focusLossCount: number) => void;
  onSessionUpdate?: (stats: any) => void;
  className?: string;
}

export const FocusMonitor: React.FC<FocusMonitorProps> = ({
  onFocusLoss,
  onSessionUpdate,
  className = ''
}) => {
  const {
    isConnected,
    isMonitoring,
    connectionError,
    lastDetection,
    focusStatus,
    sessionStats,
    focusLossCount,
    totalFocusLossTime,
    startSession,
    stopSession,
    updateSettings,
    onFocusLoss: onFocusLossEvent,
    onSessionUpdate: onSessionUpdateEvent
  } = useFocusMonitor();

  const [showSettings, setShowSettings] = useState(false);
  const [confidenceThreshold, setConfidenceThreshold] = useState(0.75);
  const [focusLossThreshold, setFocusLossThreshold] = useState(3.0);

  // Configurar callbacks de eventos
  useEffect(() => {
    const unsubscribeFocusLoss = onFocusLossEvent((focusStatus) => {
      // Notificar o componente pai
      if (onFocusLoss) {
        onFocusLoss(focusStatus.focus_loss_count);
      }
      
      // Mostrar toast de notificação
      toast.error('Perda de foco detectada!', {
        description: `Você perdeu o foco por ${focusStatus.time_since_detection.toFixed(1)} segundos`,
        duration: 3000,
      });
    });

    const unsubscribeSessionUpdate = onSessionUpdateEvent((stats) => {
      // Notificar o componente pai
      if (onSessionUpdate) {
        onSessionUpdate(stats);
      }
    });

    return () => {
      unsubscribeFocusLoss();
      unsubscribeSessionUpdate();
    };
  }, [onFocusLossEvent, onSessionUpdateEvent, onFocusLoss, onSessionUpdate]);

  // Função para iniciar monitoramento
  const handleStartMonitoring = async () => {
    try {
      await startSession({
        confidence_threshold: confidenceThreshold,
        focus_loss_threshold: focusLossThreshold
      });
      toast.success('Monitoramento de foco iniciado!');
    } catch (error) {
      toast.error('Erro ao iniciar monitoramento', {
        description: 'Verifique se o serviço está rodando'
      });
    }
  };

  // Função para parar monitoramento
  const handleStopMonitoring = async () => {
    try {
      await stopSession();
      toast.success('Monitoramento de foco parado!');
    } catch (error) {
      toast.error('Erro ao parar monitoramento');
    }
  };

  // Função para atualizar configurações
  const handleUpdateSettings = async () => {
    try {
      await updateSettings({
        confidence_threshold: confidenceThreshold,
        focus_loss_threshold: focusLossThreshold
      });
      setShowSettings(false);
      toast.success('Configurações atualizadas!');
    } catch (error) {
      toast.error('Erro ao atualizar configurações');
    }
  };

  // Calcular estatísticas
  const detectionRate = sessionStats?.detection_rate || 0;
  const sessionDuration = sessionStats?.session_duration || 0;
  const averageFocusLossDuration = sessionStats?.average_focus_loss_duration || 0;

  return (
    <div className={`space-y-4 ${className}`}>
      {/* Status da Conexão */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="flex items-center gap-2 text-lg">
            {isConnected ? (
              <>
                <Wifi className="h-5 w-5 text-green-500" />
                Conectado ao Monitor de Foco
              </>
            ) : (
              <>
                <WifiOff className="h-5 w-5 text-red-500" />
                Desconectado
              </>
            )}
          </CardTitle>
          <CardDescription>
            Status da conexão com o serviço de monitoramento de foco
          </CardDescription>
        </CardHeader>
        <CardContent>
          {connectionError && (
            <Alert className="mb-4">
              <AlertTriangle className="h-4 w-4" />
              <AlertDescription>{connectionError}</AlertDescription>
            </Alert>
          )}
          
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Badge variant={isConnected ? "default" : "destructive"}>
                {isConnected ? "Online" : "Offline"}
              </Badge>
              {isMonitoring && (
                <Badge variant="secondary">
                  <Activity className="h-3 w-3 mr-1 animate-pulse" />
                  Monitorando
                </Badge>
              )}
            </div>
            
            <Button
              variant="outline"
              size="sm"
              onClick={() => setShowSettings(!showSettings)}
            >
              <Settings className="h-4 w-4 mr-2" />
              Configurações
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Configurações */}
      {showSettings && (
        <Card>
          <CardHeader>
            <CardTitle>Configurações do Monitor</CardTitle>
            <CardDescription>
              Ajuste os parâmetros de detecção e monitoramento
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <label className="text-sm font-medium">Limiar de Confiança</label>
              <div className="flex items-center gap-2 mt-1">
                <input
                  type="range"
                  min="0.1"
                  max="1.0"
                  step="0.05"
                  value={confidenceThreshold}
                  onChange={(e) => setConfidenceThreshold(parseFloat(e.target.value))}
                  className="flex-1"
                />
                <span className="text-sm text-muted-foreground w-12">
                  {(confidenceThreshold * 100).toFixed(0)}%
                </span>
              </div>
            </div>
            
            <div>
              <label className="text-sm font-medium">Limiar de Perda de Foco (segundos)</label>
              <div className="flex items-center gap-2 mt-1">
                <input
                  type="range"
                  min="1"
                  max="10"
                  step="0.5"
                  value={focusLossThreshold}
                  onChange={(e) => setFocusLossThreshold(parseFloat(e.target.value))}
                  className="flex-1"
                />
                <span className="text-sm text-muted-foreground w-12">
                  {focusLossThreshold}s
                </span>
              </div>
            </div>
            
            <div className="flex gap-2">
              <Button onClick={handleUpdateSettings} size="sm">
                Salvar
              </Button>
              <Button 
                variant="outline" 
                size="sm" 
                onClick={() => setShowSettings(false)}
              >
                Cancelar
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Controles de Monitoramento */}
      <Card>
        <CardHeader>
          <CardTitle>Controles</CardTitle>
          <CardDescription>
            Inicie ou pare o monitoramento de foco
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex gap-2">
            <Button
              onClick={handleStartMonitoring}
              disabled={!isConnected || isMonitoring}
              className="flex-1"
            >
              <Play className="h-4 w-4 mr-2" />
              Iniciar Monitoramento
            </Button>
            
            <Button
              variant="outline"
              onClick={handleStopMonitoring}
              disabled={!isConnected || !isMonitoring}
              className="flex-1"
            >
              <Pause className="h-4 w-4 mr-2" />
              Parar Monitoramento
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Status da Detecção */}
      {lastDetection && (
        <Card>
          <CardHeader>
            <CardTitle>Status da Detecção</CardTitle>
            <CardDescription>
              Informações em tempo real sobre a detecção
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 gap-4">
              <div className="flex items-center gap-2">
                {lastDetection.has_face ? (
                  <Eye className="h-4 w-4 text-green-500" />
                ) : (
                  <EyeOff className="h-4 w-4 text-red-500" />
                )}
                <span className="text-sm">Face Detectada</span>
                <Badge variant={lastDetection.has_face ? "default" : "secondary"}>
                  {lastDetection.has_face ? "Sim" : "Não"}
                </Badge>
              </div>
              
              <div className="flex items-center gap-2">
                {lastDetection.has_pose ? (
                  <CheckCircle className="h-4 w-4 text-green-500" />
                ) : (
                  <AlertTriangle className="h-4 w-4 text-yellow-500" />
                )}
                <span className="text-sm">Postura Detectada</span>
                <Badge variant={lastDetection.has_pose ? "default" : "secondary"}>
                  {lastDetection.has_pose ? "Sim" : "Não"}
                </Badge>
              </div>
              
              <div className="flex items-center gap-2">
                <span className="text-sm">Confiança:</span>
                <Progress value={lastDetection.confidence * 100} className="flex-1" />
                <span className="text-sm text-muted-foreground">
                  {(lastDetection.confidence * 100).toFixed(1)}%
                </span>
              </div>
              
              <div className="flex items-center gap-2">
                <Clock className="h-4 w-4" />
                <span className="text-sm">Última Atualização:</span>
                <span className="text-sm text-muted-foreground">
                  {new Date(lastDetection.timestamp).toLocaleTimeString()}
                </span>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Estatísticas da Sessão */}
      {sessionStats && (
        <Card>
          <CardHeader>
            <CardTitle>Estatísticas da Sessão</CardTitle>
            <CardDescription>
              Métricas de performance do monitoramento
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <div className="text-2xl font-bold text-green-600">
                  {detectionRate.toFixed(1)}%
                </div>
                <div className="text-sm text-muted-foreground">Taxa de Detecção</div>
              </div>
              
              <div>
                <div className="text-2xl font-bold text-blue-600">
                  {focusLossCount}
                </div>
                <div className="text-sm text-muted-foreground">Perdas de Foco</div>
              </div>
              
              <div>
                <div className="text-2xl font-bold text-purple-600">
                  {Math.floor(sessionDuration / 60)}:{(sessionDuration % 60).toFixed(0).padStart(2, '0')}
                </div>
                <div className="text-sm text-muted-foreground">Duração da Sessão</div>
              </div>
              
              <div>
                <div className="text-2xl font-bold text-orange-600">
                  {averageFocusLossDuration.toFixed(1)}s
                </div>
                <div className="text-sm text-muted-foreground">Tempo Médio de Perda</div>
              </div>
            </div>
            
            <Separator className="my-4" />
            
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span>Frames Processados:</span>
                <span className="font-medium">{sessionStats.total_frames_processed}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span>Frames com Detecção:</span>
                <span className="font-medium">{sessionStats.frames_with_detection}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span>Tempo Total de Perda:</span>
                <span className="font-medium">{totalFocusLossTime.toFixed(1)}s</span>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Status do Foco */}
      {focusStatus && (
        <Card>
          <CardHeader>
            <CardTitle>Status do Foco</CardTitle>
            <CardDescription>
              Informações sobre o estado atual do foco
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-sm">Status Atual:</span>
                <Badge variant={focusStatus.focus_lost ? "destructive" : "default"}>
                  {focusStatus.focus_lost ? "Perda de Foco" : "Focado"}
                </Badge>
              </div>
              
              {focusStatus.focus_lost && (
                <Alert>
                  <AlertTriangle className="h-4 w-4" />
                  <AlertDescription>
                    Perda de foco detectada há {focusStatus.time_since_detection.toFixed(1)} segundos
                  </AlertDescription>
                </Alert>
              )}
              
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="text-muted-foreground">Tempo desde última detecção:</span>
                  <div className="font-medium">{focusStatus.time_since_detection.toFixed(1)}s</div>
                </div>
                <div>
                  <span className="text-muted-foreground">Total de perdas:</span>
                  <div className="font-medium">{focusStatus.focus_loss_count}</div>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};
