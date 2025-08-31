import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { ClopAvatar } from '@/components/ClopAvatar';
import { LevelCard } from '@/components/LevelCard';
import { useClopFocusStore, SessionLevel } from '@/store/clopfocus-store';

// Mapeamento de níveis para durações em segundos
const levelDurations: Record<SessionLevel, number> = {
  leve: 25 * 60,      // 25 minutos
  medio: 45 * 60,     // 45 minutos
  intenso: 90 * 60,   // 90 minutos
};

export default function SetupScreen() {
  const navigate = useNavigate();
  const { startSession, preferences, updatePreferences } = useClopFocusStore();

  const [selectedLevel, setSelectedLevel] = useState<SessionLevel>(preferences.defaultLevel);

  const handleStartSession = async () => {
    const selectedDuration = levelDurations[selectedLevel];
    
    updatePreferences({
      defaultLevel: selectedLevel,
      defaultDurationSec: selectedDuration,
      cameraOn: true, // <- chave para a /session abrir câmera
    });

    startSession(selectedLevel, selectedDuration);
    navigate('/session');
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-background via-background to-primary/5">
      {/* Header */}
      <div className="p-3 bg-card/50 backdrop-blur-sm border-b">
        <div className="max-w-4xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <ClopAvatar size="sm" />
            <div>
              <h1 className="text-xl font-bold text-foreground">ClopFocus</h1>
              <p className="text-xs text-muted-foreground">Configure sua sessão de foco</p>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-2xl mx-auto p-5 space-y-6">
        {/* Main Content */}
        <div className="text-center pt-8 pb-4">
          <div className="mt-6">
            <h2 className="text-3xl font-bold text-foreground mb-2">Escolha seu nível</h2>
            <p className="text-muted-foreground">Configure sua sessão de foco em segundos</p>
          </div>
        </div>

        {/* Level Selection */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">Escolha seu nível</CardTitle>
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

        {/* Start Button */}
        <div className="pb-8 space-y-4">
          <Button
            size="lg"
            onClick={handleStartSession}
            className="w-full min-h-[56px] text-lg font-semibold"
            data-testid="start-button"
          >
            Iniciar Sessão de Foco
          </Button>
          
          <Button
            variant="outline"
            size="lg"
            onClick={() => navigate('/bothmods')}
            className="w-full min-h-[56px] text-lg font-semibold"
          >
            BothMods Integration (MediaPipe Face + Pose)
          </Button>
        </div>
      </div>
    </div>
  );
}
