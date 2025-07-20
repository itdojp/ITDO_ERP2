import React from 'react'
import { cn } from '../../lib/utils'

export interface LoadingProps extends React.HTMLAttributes<HTMLDivElement> {
  size?: 'sm' | 'md' | 'lg' | 'xl'
  variant?: 'primary' | 'secondary' | 'light' | 'dark'
  message?: string
  fullScreen?: boolean
  overlay?: boolean
}

const Loading = React.forwardRef<HTMLDivElement, LoadingProps>(
  ({
    className,
    size = 'md',
    variant = 'primary',
    message,
    fullScreen = false,
    overlay = false,
    ...props
  }, ref) => {
    const baseStyles = [
      'flex items-center justify-center',
      fullScreen && 'fixed inset-0 z-50',
      overlay && 'bg-black/20'
    ]

    const spinnerSizes = {
      sm: 'h-4 w-4',
      md: 'h-6 w-6',
      lg: 'h-8 w-8',
      xl: 'h-12 w-12'
    }

    const spinnerVariants = {
      primary: 'border-blue-600 border-t-transparent',
      secondary: 'border-gray-600 border-t-transparent',
      light: 'border-white border-t-transparent',
      dark: 'border-gray-900 border-t-transparent'
    }

    const textSizes = {
      sm: 'text-sm',
      md: 'text-base',
      lg: 'text-lg',
      xl: 'text-xl'
    }

    const textVariants = {
      primary: 'text-blue-600',
      secondary: 'text-gray-600',
      light: 'text-white',
      dark: 'text-gray-900'
    }

    const containerClasses = cn(
      baseStyles,
      fullScreen && !overlay ? 'bg-white' : '',
      className
    )

    const spinnerClasses = cn(
      'animate-spin rounded-full border-2',
      spinnerSizes[size],
      spinnerVariants[variant]
    )

    const textClasses = cn(
      textSizes[size],
      textVariants[variant],
      message && 'ml-3'
    )

    return (
      <div
        ref={ref}
        className={containerClasses}
        role="status"
        aria-label={message || 'Loading'}
        {...props}
      >
        <div className="flex items-center">
          <div className={spinnerClasses} />
          {message && (
            <span className={textClasses}>
              {message}
            </span>
          )}
        </div>
      </div>
    )
  }
)

Loading.displayName = 'Loading'

export default Loading