import React from 'react'
import { useClopFocusStore } from '@/store/clopfocus-store'
import { cn } from '@/lib/utils'

type ClopAvatarProps = {
  size?: 'sm' | 'md' | 'lg'
  showMessage?: boolean
  moodOverride?: 'focus' | 'calm' | 'alert'
}

const sizeMap = { sm: 32, md: 48, lg: 72 }

export const ClopAvatar: React.FC<ClopAvatarProps> = ({
  size = 'md',
  showMessage = false,
  moodOverride,
}) => {
  const { sessionState, isDistracted } = useClopFocusStore()

  const mood: 'focus' | 'calm' | 'alert' =
    moodOverride ??
    (isDistracted ? 'alert' : sessionState === 'paused' ? 'calm' : 'focus')

  const px = sizeMap[size]

  const ring =
    mood === 'alert'
      ? 'ring-rose-400/60'
      : mood === 'calm'
      ? 'ring-blue-400/60'
      : 'ring-violet-400/60'

  const msg =
    mood === 'alert' ? 'Ei, foco!' : mood === 'calm' ? 'Pausa controlada' : 'Bora!'

  return (
    <div className="flex items-center gap-2">
      <div
        className={cn(
          'rounded-full ring-4 bg-gradient-to-br from-primary/20 to-primary/10 shadow',
          ring
        )}
        style={{ width: px, height: px }}
      >
        <div className="w-full h-full grid place-items-center text-xl">🧠</div>
      </div>
      {showMessage && <span className="text-sm text-muted-foreground">{msg}</span>}
    </div>
  )
}