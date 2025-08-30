import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { AlertCircle, Camera, Shield, Smartphone } from 'lucide-react';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { ClopAvatar } from '@/components/ClopAvatar';
import { LevelCard } from '@/components/LevelCard';
import { useClopFocusStore, SessionLevel } from '@/store/clopfocus-store';
import { cn } from '@/lib/utils';

const DURATION_PRESETS = [
  { label: '15min', value: 900, testId: 'duration-15' },
  { label: '25min', value: 1500, testId: 'duration-25' },
  { label: '45min', value: 2700, testId: 'duration-45' },
  { label: '60min', value: 3600, testId: 'duration-60' },
  { label: '90min', value: 5400, testId: 'duration-90' },
];

export default function SetupScreen() {
  const navigate = useNavigate();
  const { startSession, preferences, updatePreferences } = useClopFocusStore();
  
  const [selectedLevel, setSelectedLevel] = useState<SessionLevel>(preferences.defaultLevel);
  const [duration, setDuration] = useState(preferences.defaultDurationSec);
  const [customTime, setCustomTime] = useState('');
  const [showCamera, setShowCamera] = useState(preferences.cameraOn);
  const [enableFilters, setEnableFilters] = useState(preferences.notifFilter);
  const [cameraPermissionDenied, setCameraPermissionDenied] = useState(false);

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  const parseCustomTime = (timeStr: string) => {
    const match = timeStr.match(/^(\d{1,2}):(\d{2})$/);
    if (!match) return null;
    
    const mins = parseInt(match[1]);
    const secs = parseInt(match[2]);
    
    if (mins > 180 || secs > 59) return null;
    return mins * 60 + secs;
  };

  const handleStartSession = async () => {
    if (duration === 0) return;

    // Handle camera permission if needed
    if (showCamera) {
      try {
        await navigator.mediaDevices.getUserMedia({ video: true });
        setCameraPermissionDenied(false);
      } catch (error) {
        setCameraPermissionDenied(true);
        setShowCamera(false);
      }
    }

    // Update preferences
    updatePreferences({
      defaultLevel: selectedLevel,
      defaultDurationSec: duration,
      cameraOn: showCamera,
      notifFilter: enableFilters,
    });

    // Start session
    startSession(selectedLevel, duration);
    navigate('/session');
  };

  const customDuration = customTime ? parseCustomTime(customTime) : null;
  const isStartDisabled = duration === 0;

  return (
    <div className="min-h-screen bg-gradient-to-br from-background via-background to-primary/5 p-4">
      <div className="max-w-2xl mx-auto space-y-6">
        {/* Header */}
        <div className="text-center pt-8 pb-4">
          <ClopAvatar size="lg" showMessage />
          <div className="mt-6">
            <h1 className="text-3xl font-bold text-foreground mb-2">
              ClopFocus
            </h1>
            <p className="text-muted-foreground">
              Configure sua sessão de foco em segundos
            </p>
          </div>
        </div>

        {/* Level Selection */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <span>Escolha seu nível</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {(['leve', 'medio', 'intenso'] as SessionLevel[]).map((level) => (
                <LevelCard
                  key={level}
                  level={level}
                  isSelected={selectedLevel === level}
                  onClick={() => setSelectedLevel(level)}
                />
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Duration Selection */}
        <Card>
          <CardHeader>
            <CardTitle>Duração da sessão</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex flex-wrap gap-2">
              {DURATION_PRESETS.map((preset) => (
                <Badge
                  key={preset.value}
                  variant={duration === preset.value ? 'default' : 'outline'}
                  className={cn(
                    'cursor-pointer transition-all min-h-[44px] px-4 py-2',
                    'hover:scale-105 hover:shadow-sm',
                    duration === preset.value && 'bg-primary text-primary-foreground'
                  )}
                  onClick={() => {
                    setDuration(preset.value);
                    setCustomTime('');
                  }}
                  data-testid={preset.testId}
                  role="button"
                  tabIndex={0}
                >
                  {preset.label}
                </Badge>
              ))}
            </div>

            <Separator />

            <div className="space-y-2">
              <Label htmlFor="custom-time">Tempo personalizado (mm:ss)</Label>
              <Input
                id="custom-time"
                placeholder="Ex: 30:00"
                value={customTime}
                onChange={(e) => {
                  setCustomTime(e.target.value);
                  const parsed = parseCustomTime(e.target.value);
                  if (parsed !== null) {
                    setDuration(parsed);
                  }
                }}
                className="w-32"
              />
              {customDuration && (
                <p className="text-sm text-muted-foreground">
                  Duração: {Math.floor(customDuration / 60)} minutos
                </p>
              )}
            </div>

            {duration > 0 && (
              <div className="p-3 bg-muted/50 rounded-lg">
                <p className="text-sm font-medium">
                  Sessão configurada: <span className="text-primary">{formatTime(duration)}</span>
                </p>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Options */}
        <Card>
          <CardHeader>
            <CardTitle>Opções avançadas</CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <Camera className="w-5 h-5 text-muted-foreground" />
                <div>
                  <Label htmlFor="camera-toggle" className="font-medium">
                    Mostrar câmera
                  </Label>
                  <p className="text-sm text-muted-foreground">
                    Exibe preview da câmera durante a sessão
                  </p>
                </div>
              </div>
              <Switch
                id="camera-toggle"
                checked={showCamera}
                onCheckedChange={setShowCamera}
              />
            </div>

            <Separator />

            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <Shield className="w-5 h-5 text-muted-foreground" />
                <div>
                  <Label htmlFor="filter-toggle" className="font-medium">
                    Filtrar notificações
                  </Label>
                  <p className="text-sm text-muted-foreground">
                    Recursos avançados (indisponível nesta versão)
                  </p>
                </div>
              </div>
              <Switch
                id="filter-toggle"
                checked={enableFilters}
                onCheckedChange={setEnableFilters}
                disabled
              />
            </div>

            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <Smartphone className="w-5 h-5 text-muted-foreground" />
                <div>
                  <Label className="font-medium">Bloquear apps</Label>
                  <p className="text-sm text-muted-foreground">
                    Recursos avançados (indisponível nesta versão)
                  </p>
                </div>
              </div>
              <Switch disabled />
            </div>
          </CardContent>
        </Card>

        {/* Alerts */}
        {cameraPermissionDenied && (
          <Alert>
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>
              Permissão de câmera negada. A sessão continuará sem vídeo.
            </AlertDescription>
          </Alert>
        )}

        {isStartDisabled && (
          <Alert>
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>
              Selecione uma duração para começar sua sessão de foco.
            </AlertDescription>
          </Alert>
        )}

        {/* Start Button */}
        <div className="pb-8">
          <Button
            size="lg"
            onClick={handleStartSession}
            disabled={isStartDisabled}
            className="w-full min-h-[56px] text-lg font-semibold"
            data-testid="start-button"
          >
            {isStartDisabled ? 'Configure a duração' : 'Iniciar Sessão de Foco'}
          </Button>
        </div>
      </div>
    </div>
  );
}