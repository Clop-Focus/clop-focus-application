import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { 
  Play, 
  Pause, 
  Square, 
  ChevronUp, 
  ChevronDown, 
  Minimize2,
  Camera,
  Volume2,
  VolumeX,
  AlertTriangle
} from 'lucide-react';
import { ClopAvatar } from '@/components/ClopAvatar';
import { LifeBar } from '@/components/LifeBar';
import { useClopFocusStore } from '@/store/clopfocus-store';
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

export default function SessionScreen() {
  const navigate = useNavigate();
  const {
    currentSession,
    sessionState,
    lives,
    isDistracted,
    elapsedTime,
    showWidget,
    showCamera,
    pauseSession,
    resumeSession,
    endSession,
    simulateDistraction,
    updateElapsedTime,
    toggleWidget,
    handleWindowBlur,
    handleWindowFocus,
  } = useClopFocusStore();

  const [showEndDialog, setShowEndDialog] = useState(false);
  const [isMuted, setIsMuted] = useState(false);
  const [showCameraFeed, setShowCameraFeed] = useState(showCamera);

  // Redirect if no session
  useEffect(() => {
    if (!currentSession) {
      navigate('/');
      return;
    }
  }, [currentSession, navigate]);

  // Timer update
  useEffect(() => {
    const interval = setInterval(() => {
      updateElapsedTime();
    }, 1000);

    return () => clearInterval(interval);
  }, [updateElapsedTime]);

  // Window focus/blur detection
  useEffect(() => {
    const handleFocus = () => handleWindowFocus();
    const handleBlur = () => handleWindowBlur();

    window.addEventListener('focus', handleFocus);
    window.addEventListener('blur', handleBlur);

    return () => {
      window.removeEventListener('focus', handleFocus);
      window.removeEventListener('blur', handleBlur);
    };
  }, [handleWindowFocus, handleWindowBlur]);

  // Auto-end session when time is up
  useEffect(() => {
    if (currentSession && elapsedTime >= currentSession.durationSec) {
      endSession();
      navigate('/results');
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
    if (sessionState === 'paused') {
      resumeSession();
    } else {
      pauseSession();
    }
  };

  const handleEndSession = () => {
    endSession();
    navigate('/results');
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

  return (
    <div className={cn(
      'min-h-screen bg-gradient-to-br from-background via-background to-primary/5',
      'border-t-4 transition-all duration-300',
      getBorderColor()
    )}>
      {/* Header */}
      <div className="p-4 bg-card/50 backdrop-blur-sm border-b">
        <div className="max-w-4xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-4">
            <ClopAvatar size="sm" />
            <div>
              <Badge className={levelColors[currentSession.level]} variant="secondary">
                {currentSession.level.toUpperCase()}
              </Badge>
              <p className="text-sm text-muted-foreground mt-1">
                Sessão em andamento
              </p>
            </div>
          </div>

          <div className="flex items-center gap-4">
            <LifeBar lives={lives} size="sm" />
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setIsMuted(!isMuted)}
              aria-label={isMuted ? 'Ativar som' : 'Silenciar'}
            >
              {isMuted ? <VolumeX className="w-4 h-4" /> : <Volume2 className="w-4 h-4" />}
            </Button>
          </div>
        </div>
      </div>

      <div className="max-w-4xl mx-auto p-6 space-y-6">
        {/* Main Timer */}
        <Card className="text-center">
          <CardContent className="p-8">
            <div className="space-y-6">
              {/* Timer Display */}
              <div className="space-y-4">
                <div className="text-6xl font-mono font-bold text-foreground">
                  {formatTime(timeRemaining)}
                </div>
                <div className="text-lg text-muted-foreground">
                  Decorrido: {formatTime(elapsedTime)}
                </div>
              </div>

              {/* Progress Bar */}
              <div className="space-y-2">
                <Progress 
                  value={progressPercentage} 
                  className="h-3"
                />
                <p className="text-sm text-muted-foreground">
                  {Math.round(progressPercentage)}% concluído
                </p>
              </div>

              {/* Clop Status */}
              <div className="py-4">
                <ClopAvatar size="md" showMessage />
              </div>

              {/* Controls */}
              <div className="flex items-center justify-center gap-4">
                <Button
                  size="lg"
                  variant={sessionState === 'paused' ? 'default' : 'outline'}
                  onClick={handlePauseResume}
                  data-testid="session-pause"
                  className="min-w-[120px]"
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

                <Button
                  size="lg"
                  variant="destructive"
                  onClick={() => setShowEndDialog(true)}
                  data-testid="session-end"
                >
                  <Square className="w-4 h-4 mr-2" />
                  Encerrar
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Widget Toggle */}
        <div className="flex justify-center">
          <Button
            variant="outline"
            size="sm"
            onClick={toggleWidget}
            className="gap-2"
          >
            {showWidget ? (
              <>
                <ChevronDown className="w-4 h-4" />
                Minimizar detalhes
              </>
            ) : (
              <>
                <ChevronUp className="w-4 h-4" />
                Ver detalhes
              </>
            )}
          </Button>
        </div>

        {/* Expandable Widget */}
        {showWidget && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 animate-fade-in">
            <Card>
              <CardContent className="p-4 text-center">
                <div className="text-2xl font-bold text-primary">
                  {Math.floor(currentSession.focusSec / 60000)}min
                </div>
                <p className="text-sm text-muted-foreground">Tempo focado</p>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-4 text-center">
                <div className="text-2xl font-bold text-game-coin">
                  {currentSession.coins}
                </div>
                <p className="text-sm text-muted-foreground">Moedas</p>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-4 text-center">
                <div className="text-2xl font-bold text-muted-foreground">
                  {currentSession.pauses}
                </div>
                <p className="text-sm text-muted-foreground">Pausas</p>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-4 text-center">
                <div className="text-2xl font-bold text-game-distraction">
                  {currentSession.distractions}
                </div>
                <p className="text-sm text-muted-foreground">Distrações</p>
              </CardContent>
            </Card>
          </div>
        )}

        {/* Camera Feed */}
        {showCameraFeed && (
          <Card className="fixed bottom-4 right-4 w-48">
            <CardContent className="p-2">
              <div className="aspect-video bg-muted rounded flex items-center justify-center">
                <Camera className="w-8 h-8 text-muted-foreground" />
              </div>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setShowCameraFeed(false)}
                className="w-full mt-2"
              >
                <Minimize2 className="w-3 h-3 mr-1" />
                Minimizar
              </Button>
            </CardContent>
          </Card>
        )}

        {/* Simulation Button (for testing) */}
        <div className="flex justify-center">
          <Button
            variant="outline"
            size="sm"
            onClick={simulateDistraction}
            data-testid="simulate-distraction"
            className="gap-2 text-game-distraction border-game-distraction/30"
          >
            <AlertTriangle className="w-4 h-4" />
            Simular distração
          </Button>
        </div>
      </div>

      {/* End Session Dialog */}
      <AlertDialog open={showEndDialog} onOpenChange={setShowEndDialog}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Encerrar sessão?</AlertDialogTitle>
            <AlertDialogDescription>
              Tem certeza que deseja encerrar sua sessão de foco? 
              Seu progresso será salvo.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancelar</AlertDialogCancel>
            <AlertDialogAction onClick={handleEndSession}>
              Encerrar sessão
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}