import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Separator } from '@/components/ui/separator';
import { 
  RotateCcw, 
  History, 
  Trophy, 
  Clock, 
  Target, 
  Pause, 
  AlertTriangle,
  Coins
} from 'lucide-react';
import { ClopAvatar } from '@/components/ClopAvatar';
import { useClopFocusStore } from '@/store/clopfocus-store';

export default function ResultsScreen() {
  const navigate = useNavigate();
  const { currentSession, calculateScore } = useClopFocusStore();
  const [score, setScore] = useState(0);

  useEffect(() => {
    if (!currentSession) {
      navigate('/');
      return;
    }

    if (currentSession.isCompleted) {
      setScore(calculateScore(currentSession));
    }
  }, [currentSession, calculateScore, navigate]);

  if (!currentSession) return null;

  const focusEfficiency = Math.round((currentSession.focusSec / (currentSession.durationSec * 1000)) * 100);
  const focusMinutes = Math.floor(currentSession.focusSec / (1000 * 60));
  const totalMinutes = Math.floor(currentSession.durationSec / 60);

  const getScoreColor = (score: number) => {
    if (score >= 80) return 'text-game-focus';
    if (score >= 60) return 'text-game-warning';
    return 'text-game-distraction';
  };

  const getScoreMessage = (score: number) => {
    if (score >= 80) return "Excelente foco! Você mandou muito bem!";
    if (score >= 60) return "Bom trabalho! Continue assim!";
    if (score >= 40) return "Não foi mal. Da próxima vai ser melhor!";
    return "Tá tudo bem. Bora tentar de novo com mais calma!";
  };

  const getFeedback = (score: number, efficiency: number) => {
    if (score >= 80) {
      return "Sua concentração foi impressionante! Continue mantendo esse ritmo.";
    }
    if (efficiency < 50) {
      return "Tente minimizar as distrações na próxima sessão. Que tal começar com um tempo menor?";
    }
    if ((currentSession.livesLost || 0) > 1) {
      return "Muitas distrações podem prejudicar o foco. Tente encontrar um ambiente mais silencioso.";
    }
    return "Continue praticando! O foco é uma habilidade que se desenvolve com o tempo.";
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
              <p className="text-xs text-muted-foreground">Sessão concluída</p>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-4xl mx-auto p-5 space-y-6">
        {/* Main Content */}
        <div className="text-center space-y-4">
          <div>
            <h2 className="text-3xl font-bold">Sessão Concluída!</h2>
            <p className="text-muted-foreground">Parabéns por completar sua sessão de foco</p>
          </div>
        </div>

        {/* Score Card */}
        <Card className="text-center">
          <CardHeader>
            <CardTitle className="flex items-center justify-center gap-2">
              <Trophy className="w-6 h-6" />
              Pontuação Final
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className={`text-6xl font-bold ${getScoreColor(score)}`}>
              {score}
            </div>
            <p className="text-lg text-muted-foreground">{getScoreMessage(score)}</p>
            <p className="text-sm text-muted-foreground">{getFeedback(score, focusEfficiency)}</p>
          </CardContent>
        </Card>

        {/* Big Numbers Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <Card className="border-primary/20 bg-primary/5">
            <CardContent className="p-6 text-center">
              <Clock className="w-10 h-10 mx-auto mb-3 text-primary" />
              <div className="text-3xl font-bold text-primary mb-1">
                {focusMinutes}m
              </div>
              <p className="text-sm text-muted-foreground">Tempo Focado</p>
            </CardContent>
          </Card>

          <Card className="border-blue-500/20 bg-blue-500/5">
            <CardContent className="p-6 text-center">
              <Target className="w-10 h-10 mx-auto mb-3 text-blue-500" />
              <div className="text-3xl font-bold text-blue-500 mb-1">
                {focusEfficiency}%
              </div>
              <p className="text-sm text-muted-foreground">Eficiência</p>
            </CardContent>
          </Card>

          <Card className="border-green-500/20 bg-green-500/5">
            <CardContent className="p-6 text-center">
              <Pause className="w-10 h-10 mx-auto mb-3 text-green-500" />
              <div className="text-3xl font-bold text-green-500 mb-1">
                {currentSession.pauses}
              </div>
              <p className="text-sm text-muted-foreground">Pausas</p>
            </CardContent>
          </Card>

          <Card className="border-game-distraction/20 bg-game-distraction/5">
            <CardContent className="p-6 text-center">
              <AlertTriangle className="w-10 h-10 mx-auto mb-3 text-game-distraction" />
              <div className="text-3xl font-bold text-game-distraction mb-1">
                {currentSession.distractions}
              </div>
              <p className="text-sm text-muted-foreground">Distrações</p>
            </CardContent>
          </Card>
        </div>

        {/* Session Details */}
        <Card>
          <CardHeader>
            <CardTitle>Detalhes da Sessão</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
              <div>
                <p className="text-muted-foreground">Duração configurada</p>
                <p className="font-medium">{totalMinutes} minutos</p>
              </div>
              <div>
                <p className="text-muted-foreground">Vidas perdidas</p>
                <p className="font-medium text-game-distraction">{currentSession.livesLost || 0}</p>
              </div>
              <div>
                <p className="text-muted-foreground">Nível</p>
                <p className="font-medium capitalize">{currentSession.level}</p>
              </div>
              <div>
                <p className="text-muted-foreground">Moedas</p>
                <p className="font-medium text-game-coin">{currentSession.coins}</p>
              </div>
            </div>

            <Separator />

            <div className="space-y-2">
              <h4 className="font-medium">Recomendações para próximas sessões:</h4>
              <ul className="text-sm text-muted-foreground space-y-1 pl-4">
                {currentSession.distractions > 3 && (
                  <li>• Tente encontrar um ambiente mais silencioso</li>
                )}
                {focusEfficiency < 60 && (
                  <li>• Considere sessões mais curtas para começar</li>
                )}
                {(currentSession.livesLost || 0) === 0 && (
                  <li>• Excelente! Tente um nível mais desafiador</li>
                )}
                <li>• Mantenha-se hidratado e faça pausas regulares</li>
              </ul>
            </div>
          </CardContent>
        </Card>

        {/* Actions */}
        <div className="flex flex-col sm:flex-row gap-4 justify-center">
          <Button onClick={() => navigate('/')} className="gap-2">
            <RotateCcw className="w-4 h-4" />
            Nova Sessão
          </Button>
          <Button variant="outline" onClick={() => navigate('/')} className="gap-2">
            <History className="w-4 h-4" />
            Voltar ao Início
          </Button>
        </div>
      </div>
    </div>
  );
}