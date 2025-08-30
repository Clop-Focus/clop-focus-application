import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { SessionLevel } from '@/store/clopfocus-store';
import { cn } from '@/lib/utils';
import { Clock, Zap, Flame } from 'lucide-react';

interface LevelCardProps {
  level: SessionLevel;
  isSelected: boolean;
  onClick: () => void;
  className?: string;
}

const levelConfig = {
  leve: {
    title: 'Leve',
    description: 'Ideal para começar, sessões mais curtas',
    duration: '25min',
    icon: Clock,
    color: 'bg-gradient-to-br from-level-leve to-level-leve/80',
    borderColor: 'border-level-leve/30',
    testId: 'level-leve',
  },
  medio: {
    title: 'Médio',
    description: 'Equilibrio entre foco e descanso',
    duration: '45min', 
    icon: Zap,
    color: 'bg-gradient-to-br from-level-medio to-level-medio/80',
    borderColor: 'border-level-medio/30',
    testId: 'level-medio',
  },
  intenso: {
    title: 'Intenso',
    description: 'Para quem quer foco máximo',
    duration: '90min',
    icon: Flame,
    color: 'bg-gradient-to-br from-level-intenso to-level-intenso/80',
    borderColor: 'border-level-intenso/30',
    testId: 'level-intenso',
  },
};

export const LevelCard = ({ level, isSelected, onClick, className }: LevelCardProps) => {
  const config = levelConfig[level];
  const Icon = config.icon;

  return (
    <Card 
      className={cn(
        'cursor-pointer transition-all duration-200 hover:scale-105',
        'border-2 hover:shadow-lg',
        isSelected 
          ? `${config.borderColor} shadow-lg scale-105 ${config.color} text-white` 
          : 'border-border hover:border-primary/30 bg-card',
        className
      )}
      onClick={onClick}
      data-testid={config.testId}
      role="button"
      tabIndex={0}
      aria-pressed={isSelected}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          onClick();
        }
      }}
    >
      <CardContent className="p-6 text-center">
        <div className="flex flex-col items-center gap-3">
          <div className={cn(
            'p-3 rounded-full',
            isSelected ? 'bg-white/20' : 'bg-primary/10'
          )}>
            <Icon className={cn(
              'w-6 h-6',
              isSelected ? 'text-white' : 'text-primary'
            )} />
          </div>
          
          <div className="space-y-2">
            <div className="flex items-center justify-center gap-2">
              <h3 className={cn(
                'font-bold text-lg',
                isSelected ? 'text-white' : 'text-foreground'
              )}>
                {config.title}
              </h3>
              <Badge variant={isSelected ? 'secondary' : 'outline'} className="text-xs">
                {config.duration}
              </Badge>
            </div>
            
            <p className={cn(
              'text-sm leading-relaxed',
              isSelected ? 'text-white/90' : 'text-muted-foreground'
            )}>
              {config.description}
            </p>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};