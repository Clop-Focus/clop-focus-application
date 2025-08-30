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
import { 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  Legend
} from 'recharts';

export default function ResultsScreen() {
  const navigate = useNavigate();
  const { currentSession, calculateScore, sessions } = useClopFocusStore();
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

  // Chart data
  const chartData = [
    {
      name: 'Foco',
      minutes: focusMinutes,
      fill: 'hsl(var(--game-focus))',
    },
    {
      name: 'Pausas', 
      minutes: Math.max(0, totalMinutes - focusMinutes - currentSession.distractions),
      fill: 'hsl(var(--muted))',
    },
    {
      name: 'Distrações',
      minutes: currentSession.distractions,
      fill: 'hsl(var(--game-distraction))',
    },
  ];

  const pieData = [
    { name: 'Tempo Focado', value: focusMinutes, fill: 'hsl(var(--game-focus))' },
    { name: 'Pausas/Outras', value: totalMinutes - focusMinutes, fill: 'hsl(var(--muted))' },
  ];

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
    if (currentSession.livesLost > 1) {
      return "Muitas distrações podem prejudicar o foco. Tente encontrar um ambiente mais silencioso.";
    }
    return "Você está no caminho certo! A prática leva à perfeição.";
  };

  const levelColors = {
    leve: 'bg-level-leve text-white',
    medio: 'bg-level-medio text-white',
    intenso: 'bg-level-intenso text-white',
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-background via-background to-primary/5 p-4">
      <div className="max-w-4xl mx-auto space-y-6">
        {/* Header */}
        <div className="text-center pt-8 pb-4">
          <ClopAvatar size="lg" showMessage />
          <div className="mt-6">
            <h1 className="text-3xl font-bold text-foreground mb-2">
              Sessão Concluída!
            </h1>
            <Badge className={levelColors[currentSession.level]} variant="secondary">
              Nível {currentSession.level.toUpperCase()}
            </Badge>
          </div>
        </div>

        {/* Score Card */}
        <Card className="text-center">
          <CardContent className="p-8">
            <div className="space-y-4">
              <div className="flex items-center justify-center gap-4">
                <Trophy className={`w-12 h-12 ${getScoreColor(score)}`} />
                <div>
                  <div className={`text-6xl font-bold ${getScoreColor(score)}`} data-testid="score">
                    {score}
                  </div>
                  <p className="text-lg text-muted-foreground">Pontuação</p>
                </div>
              </div>
              
              <Progress value={score} className="h-3" />
              
              <div className="space-y-2">
                <p className="text-lg font-medium text-foreground">
                  {getScoreMessage(score)}
                </p>
                <p className="text-sm text-muted-foreground max-w-md mx-auto">
                  {getFeedback(score, focusEfficiency)}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Big Numbers */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <Card>
            <CardContent className="p-6 text-center">
              <div className="flex flex-col items-center gap-2">
                <Clock className="w-8 h-8 text-game-focus" />
                <div className="text-3xl font-bold text-game-focus" data-testid="big-number-focus">
                  {focusMinutes}min
                </div>
                <p className="text-sm text-muted-foreground">Tempo focado</p>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-6 text-center">
              <div className="flex flex-col items-center gap-2">
                <Target className="w-8 h-8 text-primary" />
                <div className="text-3xl font-bold text-primary">
                  {focusEfficiency}%
                </div>
                <p className="text-sm text-muted-foreground">Foco efetivo</p>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-6 text-center">
              <div className="flex flex-col items-center gap-2">
                <Pause className="w-8 h-8 text-muted-foreground" />
                <div className="text-3xl font-bold text-muted-foreground">
                  {currentSession.pauses}
                </div>
                <p className="text-sm text-muted-foreground">Pausas</p>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-6 text-center">
              <div className="flex flex-col items-center gap-2">
                <Coins className="w-8 h-8 text-game-coin" />
                <div className="text-3xl font-bold text-game-coin">
                  {currentSession.coins}
                </div>
                <p className="text-sm text-muted-foreground">Moedas</p>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Charts */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <Card>
            <CardHeader>
              <CardTitle>Distribuição do Tempo</CardTitle>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={200}>
                <BarChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" />
                  <YAxis />
                  <Bar dataKey="minutes" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Eficiência da Sessão</CardTitle>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={200}>
                <PieChart>
                  <Pie
                    data={pieData}
                    cx="50%"
                    cy="50%"
                    innerRadius={40}
                    outerRadius={80}
                    paddingAngle={5}
                    dataKey="value"
                  >
                    {pieData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.fill} />
                    ))}
                  </Pie>
                  <Legend />
                </PieChart>
              </ResponsiveContainer>
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
                <p className="font-medium">{Math.floor(currentSession.durationSec / 60)} minutos</p>
              </div>
              <div>
                <p className="text-muted-foreground">Vidas perdidas</p>
                <p className="font-medium text-game-distraction">{currentSession.livesLost}</p>
              </div>
              <div>
                <p className="text-muted-foreground">Distrações</p>
                <p className="font-medium text-game-distraction">{currentSession.distractions}</p>
              </div>
              <div>
                <p className="text-muted-foreground">Nível</p>
                <p className="font-medium capitalize">{currentSession.level}</p>
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
                {currentSession.livesLost === 0 && (
                  <li>• Excelente! Tente um nível mais desafiador</li>
                )}
                <li>• Mantenha-se hidratado e faça pausas regulares</li>
              </ul>
            </div>
          </CardContent>
        </Card>

        {/* Action Buttons */}
        <div className="flex flex-col sm:flex-row gap-4 pb-8">
          <Button
            size="lg"
            onClick={() => navigate('/')}
            className="flex-1"
            data-testid="cta-new-session"
          >
            <RotateCcw className="w-4 h-4 mr-2" />
            Iniciar Nova Sessão
          </Button>
          
          <Button
            size="lg"
            variant="outline"
            onClick={() => {
              // Navigate to history (placeholder for now)
              console.log('Ver histórico de', sessions.length, 'sessões');
            }}
            className="flex-1"
          >
            <History className="w-4 h-4 mr-2" />
            Ver Histórico
          </Button>
        </div>
      </div>
    </div>
  );
}