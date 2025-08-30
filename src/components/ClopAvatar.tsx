import { useClopFocusStore } from '@/store/clopfocus-store';
import { cn } from '@/lib/utils';

interface ClopAvatarProps {
  size?: 'sm' | 'md' | 'lg';
  showMessage?: boolean;
  className?: string;
}

export const ClopAvatar = ({ size = 'md', showMessage = false, className }: ClopAvatarProps) => {
  const { getClopMood, getMotivationalMessage, preferences } = useClopFocusStore();
  
  const mood = getClopMood();
  const message = getMotivationalMessage();
  
  const sizeClasses = {
    sm: 'w-12 h-12 text-2xl',
    md: 'w-16 h-16 text-4xl',
    lg: 'w-24 h-24 text-6xl',
  };

  const moodEmojis = {
    happy: '🎯',
    neutral: '😊',
    sad: '😔',
    focused: '🧠',
    distracted: '😵',
  };

  const moodColors = {
    happy: 'from-game-focus to-game-coin',
    neutral: 'from-primary to-secondary',
    sad: 'from-game-distraction to-destructive',
    focused: 'from-game-focus to-accent',
    distracted: 'from-game-distraction to-game-warning animate-pulse',
  };

  return (
    <div className={cn('flex flex-col items-center gap-3', className)}>
      <div 
        className={cn(
          'flex items-center justify-center rounded-full',
          'bg-gradient-to-br border-2 border-border/20',
          'shadow-lg transition-all duration-300',
          sizeClasses[size],
          moodColors[mood]
        )}
        role="img"
        aria-label={`Clop está ${mood === 'happy' ? 'feliz' : mood === 'focused' ? 'focado' : mood === 'distracted' ? 'distraído' : mood === 'sad' ? 'triste' : 'neutro'}`}
      >
        <span className="drop-shadow-sm">
          {moodEmojis[mood]}
        </span>
      </div>
      
      {showMessage && (
        <div className="text-center max-w-xs">
          <p className="text-sm font-medium text-foreground/80 animate-fade-in">
            {message}
          </p>
        </div>
      )}
    </div>
  );
};