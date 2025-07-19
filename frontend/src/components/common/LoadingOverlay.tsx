import React from 'react'
import { cn } from '../../lib/utils'
import LoadingSpinner from './LoadingSpinner'

export interface LoadingOverlayProps extends React.HTMLAttributes<HTMLDivElement> {
  mode?: 'fullscreen' | 'container'
  message?: string
  backdrop?: boolean
  blur?: boolean
  size?: 'small' | 'medium' | 'large'
  color?: 'primary' | 'secondary' | 'white'
}

const LoadingOverlay = React.forwardRef<HTMLDivElement, LoadingOverlayProps>(
  ({ 
    className, 
    mode = 'container', 
    message, 
    backdrop = true,
    blur = true,
    size = 'medium',
    color = 'primary',
    children,
    ...props 
  }, ref) => {
    const baseClasses = [
      'flex flex-col items-center justify-center',
      'absolute inset-0 z-50',
      mode === 'fullscreen' ? 'fixed' : 'absolute'
    ]

    const backdropClasses = [
      backdrop && 'bg-black/50',
      blur && 'backdrop-blur-sm'
    ]

    const overlayClasses = cn(
      baseClasses,
      backdropClasses,
      className
    )

    const messageClasses = cn(
      'mt-3 text-sm font-medium',
      color === 'white' ? 'text-white' : 'text-gray-900'
    )

    return (
      <div
        ref={ref}
        className={overlayClasses}
        role="status"
        aria-label={message || 'Loading'}
        {...props}
      >
        <LoadingSpinner size={size} color={color} />
        {message && (
          <div className={messageClasses}>
            {message}
          </div>
        )}
        {children}
      </div>
    )
  }
)

LoadingOverlay.displayName = 'LoadingOverlay'

export default LoadingOverlay