import { useEffect, useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import {
  Play,
  Pause,
  Square,
  Camera,
  Volume2,
  VolumeX,
  AlertTriangle,
  Video,
  VideoOff,
  Eye,
  Target,
} from 'lucide-react';
import { ClopAvatar } from '@/components/ClopAvatar';
import { LifeBar } from '@/components/LifeBar';
import { ClopIcon } from '@/components/ClopIcon';
import { useClopFocusStore } from '@/store/clopfocus-store';
import { useNotifications } from '@/hooks/use-notifications';
import { cn } from '@/lib/utils';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog';
import { useGazeDetection } from '@/hooks/useGazeDetection';

export default function SessionScreen() {
  const navigate = useNavigate();
  const {
    currentSession,
    sessionState,
    lives,
    isDistracted,
    elapsedTime,
    preferences,
    pauseSession,
    resumeSession,
    endSession,
    updateElapsedTime,
    handleWindowBlur,
    handleWindowFocus,
  } = useClopFocusStore();

  const [showEndDialog, setShowEndDialog] = useState(false);
  const [isMuted, setIsMuted] = useState(false);
  const [cameraStream, setCameraStream] = useState<MediaStream | null>(null);
  const [cameraError, setCameraError] = useState<string | null>(null);
  const videoRef = useRef<HTMLVideoElement>(null);

  // Hook para notificações do sistema
  const { permission, requestPermission, notifyFocusLoss } = useNotifications();

  // Hook para detecção de gaze
  const {
    isConnected,
    isMonitoring,
    gazeData,
    sessionState: gazeSessionState,
    connect,
    startMonitoring,
    stopMonitoring,
    getSessionStats,
    focusLossCount,
    currentFocusScore,
    focusPercentage,
  } = useGazeDetection({
    backendUrl: 'ws://localhost:8000',
    onFocusLoss: (data) => {
      console.log('🚨 Perda de foco detectada pelo gaze:', data);
      // Aqui você pode integrar com o sistema de notificações
      if (permission === 'granted') {
        notifyFocusLoss(currentSession?.level || 'medio');
      }
    },
    onGazeUpdate: (data) => {
      console.log('👁️ Gaze atualizado:', data.focus_analysis.status);
    }
  });

  const justEndedRef = useRef(false);

  useEffect(() => {
    if (!currentSession) {
      if (justEndedRef.current) return;
      navigate('/');
    }
  }, [currentSession, navigate]);

  useEffect(() => {
    if (currentSession && preferences.cameraOn && !cameraStream) {
      initializeCamera();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [currentSession, preferences.cameraOn]);

  // Conectar e iniciar monitoramento de gaze quando a câmera estiver ativa
  useEffect(() => {
    if (cameraStream && !isConnected) {
      connect().then(() => {
        console.log('✅ Conectado ao backend de gaze');
        startMonitoring();
      }).catch((error) => {
        console.error('❌ Erro ao conectar ao backend de gaze:', error);
      });
    }
  }, [cameraStream, isConnected, connect, startMonitoring]);

  // Solicitar permissão de notificação quando a sessão iniciar
  useEffect(() => {
    if (currentSession && permission === 'default') {
      requestPermission();
    }
  }, [currentSession, permission, requestPermission]);

  useEffect(() => {
    return () => {
      if (cameraStream) cameraStream.getTracks().forEach((track) => track.stop());
      if (isMonitoring) stopMonitoring();
    };
  }, [cameraStream, isMonitoring, stopMonitoring]);

  const initializeCamera = async () => {
    try {
      setCameraError(null);
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { width: { ideal: 640 }, height: { ideal: 480 } },
      });
      setCameraStream(stream);
      if (videoRef.current) videoRef.current.srcObject = stream;
    } catch (error) {
      if (error instanceof Error) {
        if (error.name === 'NotAllowedError') setCameraError('Permissão de câmera negada');
        else if (error.name === 'NotFoundError') setCameraError('Câmera não encontrada');
        else setCameraError('Não foi possível acessar a câmera');
      } else setCameraError('Erro desconhecido ao acessar câmera');
    }
  };

  const stopCamera = () => {
    if (cameraStream) {
      cameraStream.getTracks().forEach((track) => track.stop());
      setCameraStream(null);
      setCameraError(null);
    }
  };

  useEffect(() => {
    const interval = setInterval(() => updateElapsedTime(), 1000);
    return () => clearInterval(interval);
  }, [updateElapsedTime]);

  useEffect(() => {
    const onFocus = () => handleWindowFocus();
    const onBlur = () => {
      handleWindowBlur();
      // Enviar notificação do sistema quando perder foco
      if (currentSession && sessionState === 'running' && permission === 'granted') {
        notifyFocusLoss(currentSession.level);
      }
    };
    window.addEventListener('focus', onFocus);
    window.addEventListener('blur', onBlur);
    return () => {
      window.removeEventListener('focus', onFocus);
      window.removeEventListener('blur', onBlur);
    };
  }, [handleWindowFocus, handleWindowBlur, currentSession, sessionState, permission, notifyFocusLoss]);

  useEffect(() => {
    if (currentSession && elapsedTime >= currentSession.durationSec) {
      stopCamera();
      justEndedRef.current = true;
      navigate('/results', { replace: true });
      setTimeout(() => {
        endSession();
        justEndedRef.current = false;
      }, 0);
    }
  }, [currentSession, elapsedTime, endSession, navigate]);

  if (!currentSession) return null;

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  const timeRemaining = Math.max(0, currentSession.durationSec - elapsedTime);
  const progressPercentage = (elapsedTime / currentSession.durationSec) * 100;

  const handlePauseResume = () => {
    if (sessionState === 'paused') resumeSession();
    else pauseSession();
  };

  const handleEndSession = () => {
    stopCamera();
    justEndedRef.current = true;
    navigate('/results', { replace: true });
    setTimeout(() => {
      endSession();
      justEndedRef.current = false;
    }, 0);
  };

  const getBorderColor = () => {
    if (isDistracted) return 'border-game-distraction shadow-game-distraction/50';
    if (sessionState === 'running') return 'border-game-focus shadow-game-focus/50';
    return 'border-border';
  };

  const levelColors = {
    leve: 'bg-level-leve text-white',
    medio: 'bg-level-medio text-white',
    intenso: 'bg-level-intenso text-white',
  };

  const getFocusLevelColor = (score: number) => {
    if (score >= 80) return 'text-green-600';
    if (score >= 60) return 'text-yellow-600';
    if (score >= 40) return 'text-orange-600';
    return 'text-red-600';
  };

  const getFocusLevelText = (score: number) => {
    if (score >= 80) return 'Excelente';
    if (score >= 60) return 'Bom';
    if (score >= 40) return 'Moderado';
    return 'Baixo';
  };

  const MetricsGrid = () => (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 items-start">
      <Card>
        <CardContent className="p-3 text-center">
          <div className="text-xl font-bold text-primary">
            {Math.floor(currentSession.focusSec / 60000)}min
          </div>
          <p className="text-xs text-muted-foreground">Tempo focado</p>
        </CardContent>
      </Card>
      <Card>
        <CardContent className="p-3 text-center">
          <div className="text-xl font-bold text-game-coin">{currentSession.coins}</div>
          <p className="text-xs text-muted-foreground">Moedas</p>
        </CardContent>
      </Card>
      <Card>
        <CardContent className="p-3 text-center">
          <div className="text-xl font-bold text-muted-foreground">{currentSession.pauses}</div>
          <p className="text-xs text-muted-foreground">Pausas</p>
        </CardContent>
      </Card>
      <Card>
        <CardContent className="p-3 text-center">
          <div className="text-xl font-bold text-game-distraction">{currentSession.distractions}</div>
          <p className="text-xs text-muted-foreground">Distrações</p>
        </CardContent>
      </Card>
    </div>
  );

  return (
    <div
      className={cn(
        'min-h-screen bg-gradient-to-br from-background via-background to-primary/5',
        'border-t-4 transition-all duration-300',
        getBorderColor()
      )}
    >
      {/* Header */}
      <div className="p-3 bg-card/50 backdrop-blur-sm border-b">
        <div className="max-w-4xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <ClopAvatar size="sm" />
            <div>
              <Badge className={levelColors[currentSession.level]} variant="secondary">
                {currentSession.level.toUpperCase()}
              </Badge>
              <p className="text-xs text-muted-foreground mt-0.5">Sessão em andamento</p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <LifeBar lives={lives} size="sm" />
            
            {/* Status do Gaze Detection */}
            {preferences.cameraOn && (
              <div className="flex items-center gap-2">
                <div className={cn(
                  "w-2 h-2 rounded-full",
                  isConnected ? "bg-green-500" : "bg-gray-400",
                  isMonitoring ? "animate-pulse" : ""
                )}></div>
                <Badge variant="secondary" className={cn(
                  isConnected ? "bg-green-500/20 text-green-600 border-green-500/30" : "bg-gray-500/20 text-gray-600 border-gray-500/30"
                )}>
                  {isConnected ? "👁️ Gaze Ativo" : "👁️ Gaze Inativo"}
                </Badge>
              </div>
            )}
            
            <Button
              variant="ghost"
              size="icon"
              onClick={() => setIsMuted(!isMuted)}
              aria-label={isMuted ? 'Ativar som' : 'Silenciar'}
              className="h-8 w-8"
            >
              {isMuted ? <VolumeX className="w-4 h-4" /> : <Volume2 className="w-4 h-4" />}
            </Button>
          </div>
        </div>
      </div>

      <div className="max-w-4xl mx-auto p-5 space-y-5">
        {/* Timer */}
        <Card className="text-center">
          <CardContent className="p-6">
            <div className="space-y-4">
              <div className="space-y-2">
                <div className="text-5xl font-mono font-bold text-foreground">
                  {formatTime(timeRemaining)}
                </div>
                <div className="text-sm text-muted-foreground">
                  Decorrido: {formatTime(elapsedTime)}
                </div>
              </div>
              <div className="space-y-1">
                <Progress value={progressPercentage} className="h-2" />
                <p className="text-xs text-muted-foreground">
                  {Math.round(progressPercentage)}% concluído
                </p>
              </div>
              <div className="flex items-center justify-center gap-3 pt-2">
                <Button
                  size="sm"
                  variant={sessionState === 'paused' ? 'default' : 'outline'}
                  onClick={handlePauseResume}
                  className="min-w-[110px]"
                >
                  {sessionState === 'paused' ? (
                    <>
                      <Play className="w-4 h-4 mr-2" />
                      Retomar
                    </>
                  ) : (
                    <>
                      <Pause className="w-4 h-4 mr-2" />
                      Pausar
                    </>
                  )}
                </Button>
                <Button size="sm" variant="destructive" onClick={() => setShowEndDialog(true)}>
                  <Square className="w-4 h-4 mr-2" />
                  Encerrar
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Camera ligada */}
        {preferences.cameraOn && (
          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between mb-6">
                <h3 className="text-lg font-semibold flex items-center gap-3">
                  <Camera className="w-6 h-6 text-primary" />
                  Monitoramento de Foco com IA
                </h3>
                <div className="flex items-center gap-2">
                  {!cameraStream && !cameraError && (
                    <Button variant="outline" size="sm" onClick={initializeCamera} className="gap-2">
                      <Video className="w-4 h-4" />
                      Ativar Câmera
                    </Button>
                  )}
                  {cameraStream && (
                    <Button variant="outline" size="sm" onClick={stopCamera} className="gap-2">
                      <VideoOff className="w-4 h-4" />
                      Desativar
                    </Button>
                  )}
                </div>
              </div>
              
              <div className="grid grid-cols-1 xl:grid-cols-[1fr_auto] gap-8 items-start">
                {/* Métricas - Lado esquerdo */}
                <div className="space-y-4">
                  <h4 className="text-sm font-medium text-muted-foreground mb-3">Métricas em Tempo Real</h4>
                  
                  {/* Métricas de Gaze */}
                  {gazeData && (
                    <div className="grid grid-cols-2 gap-4 mb-4">
                      <Card className="border-blue-500/20 bg-blue-500/5">
                        <CardContent className="p-4 text-center">
                          <div className="flex items-center justify-center gap-2 mb-2">
                            <Eye className="w-4 h-4 text-blue-500" />
                            <span className="text-xs text-muted-foreground">Score de Foco</span>
                          </div>
                          <div className={cn("text-2xl font-bold mb-1", getFocusLevelColor(currentFocusScore))}>
                            {currentFocusScore}%
                          </div>
                          <p className="text-xs text-muted-foreground">{getFocusLevelText(currentFocusScore)}</p>
                        </CardContent>
                      </Card>
                      
                      <Card className="border-green-500/20 bg-green-500/5">
                        <CardContent className="p-4 text-center">
                          <div className="flex items-center justify-center gap-2 mb-2">
                            <Target className="w-4 h-4 text-green-500" />
                            <span className="text-xs text-muted-foreground">Atenção</span>
                          </div>
                          <div className="text-2xl font-bold text-green-500 mb-1">
                            {Math.round(gazeData.attention * 100)}%
                          </div>
                          <p className="text-xs text-muted-foreground">
                            {gazeData.focus_analysis.status === 'focused' ? 'Focado' : 'Distraído'}
                          </p>
                        </CardContent>
                      </Card>
                    </div>
                  )}
                  
                  <div className="grid grid-cols-2 gap-4">
                    <Card className="border-primary/20 bg-primary/5">
                      <CardContent className="p-4 text-center">
                        <div className="text-2xl font-bold text-primary mb-1">
                          {Math.floor(currentSession.focusSec / 60000)}min
                        </div>
                        <p className="text-sm text-muted-foreground">Tempo focado</p>
                      </CardContent>
                    </Card>
                    <Card className="border-game-coin/20 bg-game-coin/5">
                      <CardContent className="p-4 text-center">
                        <div className="text-2xl font-bold text-game-coin mb-1">
                          {currentSession.coins}
                        </div>
                        <p className="text-sm text-muted-foreground">Moedas</p>
                      </CardContent>
                    </Card>
                    <Card className="border-blue-500/20 bg-blue-500/5">
                      <CardContent className="p-4 text-center">
                        <div className="text-2xl font-bold text-blue-500 mb-1">
                          {currentSession.pauses}
                        </div>
                        <p className="text-sm text-muted-foreground">Pausas</p>
                      </CardContent>
                    </Card>
                    <Card className="border-game-distraction/20 bg-game-distraction/5">
                      <CardContent className="p-4 text-center">
                        <div className="text-2xl font-bold text-game-distraction mb-1">
                          {focusLossCount}
                        </div>
                        <p className="text-sm text-muted-foreground">Perdas de foco</p>
                      </CardContent>
                    </Card>
                  </div>
                </div>

                {/* Vídeo - Lado direito */}
                <div className="space-y-4 min-w-[400px]">
                  <h4 className="text-sm font-medium text-muted-foreground mb-3">Preview da Câmera</h4>
                  
                  {cameraStream ? (
                    <div className="relative">
                      <video
                        ref={videoRef}
                        autoPlay
                        playsInline
                        muted
                        className="w-full h-64 object-cover rounded-xl shadow-lg border-2 border-primary/20 bg-black"
                      />
                      <div className="absolute top-2 right-2">
                        <div className="w-3 h-3 bg-green-500 rounded-full animate-pulse"></div>
                      </div>
                      
                      {/* Status do Gaze Detection */}
                      <div className="absolute top-2 left-2">
                        <div className={cn(
                          "w-3 h-3 rounded-full",
                          isConnected ? "bg-blue-500" : "bg-gray-400",
                          isMonitoring ? "animate-pulse" : ""
                        )}></div>
                      </div>
                      
                      {/* Indicador de foco */}
                      {gazeData && (
                        <div className="absolute bottom-2 left-2">
                          <Badge variant="secondary" className={cn(
                            "text-xs",
                            gazeData.focus_analysis.status === 'focused' 
                              ? "bg-green-500/20 text-green-600 border-green-500/30" 
                              : "bg-red-500/20 text-red-600 border-red-500/30"
                          )}>
                            <ClopIcon size="md" className="mr-1" />
                            {gazeData.focus_analysis.status === 'focused' ? 'Focado' : 'Distraído'}
                          </Badge>
                        </div>
                      )}
                    </div>
                  ) : cameraError ? (
                    <div className="w-full h-64 border-2 border-dashed border-red-300 rounded-xl flex items-center justify-center bg-red-50">
                      <div className="text-center text-red-600">
                        <AlertTriangle className="w-8 h-8 mx-auto mb-2" />
                        <p className="text-sm font-medium">{cameraError}</p>
                      </div>
                    </div>
                  ) : (
                    <div className="w-full h-64 border-2 border-dashed border-muted-foreground/30 rounded-xl flex items-center justify-center bg-muted/20">
                      <div className="text-center text-muted-foreground">
                        <Video className="w-8 h-8 mx-auto mb-2" />
                        <p className="text-sm font-medium">Câmera não ativada</p>
                        <p className="text-xs">Clique em "Ativar Câmera" para começar</p>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Camera desligada */}
        {!preferences.cameraOn && <MetricsGrid />}
      </div>

      <AlertDialog open={showEndDialog} onOpenChange={setShowEndDialog}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Encerrar sessão?</AlertDialogTitle>
            <AlertDialogDescription>
              Tem certeza que deseja encerrar sua sessão de foco? Seu progresso será salvo.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancelar</AlertDialogCancel>
            <AlertDialogAction onClick={handleEndSession}>Encerrar sessão</AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
