import React from 'react'
import { cn } from '@/lib/utils'

type ClopIconProps = {
  size?: 'sm' | 'md' | 'lg'
  className?: string
}

const sizeMap = { sm: 24, md: 48, lg: 96 }

export const ClopIcon: React.FC<ClopIconProps> = ({
  size = 'md',
  className
}) => {
  const px = sizeMap[size]
  
  return (
    <div 
      className={cn(
        "flex items-center justify-center",
        className
      )}
      style={{ width: px, height: px }}
    >
      <img 
        src="/icon_def.jpeg" 
        alt="ClopFocus Icon"
        className="w-full h-full object-cover rounded-sm"
        style={{ 
          width: px, 
          height: px,
          minWidth: px,
          minHeight: px
        }}
      />
    </div>
  )
}
