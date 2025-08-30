import { Heart } from 'lucide-react';
import { cn } from '@/lib/utils';

interface LifeBarProps {
  lives: number;
  maxLives?: number;
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

export const LifeBar = ({ lives, maxLives = 3, size = 'md', className }: LifeBarProps) => {
  const sizeClasses = {
    sm: 'w-4 h-4',
    md: 'w-6 h-6', 
    lg: 'w-8 h-8',
  };

  return (
    <div className={cn('flex items-center gap-1', className)} role="status" aria-label={`${lives} vidas restantes de ${maxLives}`}>
      {Array.from({ length: maxLives }, (_, index) => (
        <Heart
          key={index}
          className={cn(
            sizeClasses[size],
            'transition-all duration-300',
            index < lives
              ? 'text-destructive fill-destructive drop-shadow-sm'
              : 'text-muted-foreground/30 fill-transparent'
          )}
        />
      ))}
      
      {size !== 'sm' && (
        <span className="ml-2 text-sm font-medium text-foreground/70">
          {lives}/{maxLives}
        </span>
      )}
    </div>
  );
};