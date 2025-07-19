import React from 'react'
import { cn } from '../../lib/utils'
import { AlertCircle, CheckCircle, Info, X, AlertTriangle } from 'lucide-react'

export interface AlertProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: 'success' | 'error' | 'warning' | 'info'
  size?: 'sm' | 'md' | 'lg'
  title?: string
  message: string
  closable?: boolean
  onClose?: () => void
  showIcon?: boolean
}

const Alert = React.forwardRef<HTMLDivElement, AlertProps>(
  ({
    className,
    variant = 'info',
    size = 'md',
    title,
    message,
    closable = false,
    onClose,
    showIcon = true,
    ...props
  }, ref) => {
    const baseStyles = [
      'relative rounded-lg border p-4 flex items-start gap-3',
      'transition-all duration-200'
    ]

    const variants = {
      success: 'bg-green-50 border-green-200 text-green-800',
      error: 'bg-red-50 border-red-200 text-red-800',
      warning: 'bg-yellow-50 border-yellow-200 text-yellow-800',
      info: 'bg-blue-50 border-blue-200 text-blue-800'
    }

    const iconVariants = {
      success: 'text-green-600',
      error: 'text-red-600',
      warning: 'text-yellow-600',
      info: 'text-blue-600'
    }

    const sizes = {
      sm: 'text-sm',
      md: 'text-base',
      lg: 'text-lg'
    }

    const iconSizes = {
      sm: 'h-4 w-4',
      md: 'h-5 w-5',
      lg: 'h-6 w-6'
    }

    const getIcon = () => {
      const iconClass = cn(iconSizes[size], iconVariants[variant])
      
      switch (variant) {
        case 'success':
          return <CheckCircle className={iconClass} />
        case 'error':
          return <AlertCircle className={iconClass} />
        case 'warning':
          return <AlertTriangle className={iconClass} />
        case 'info':
          return <Info className={iconClass} />
        default:
          return <Info className={iconClass} />
      }
    }

    const alertClasses = cn(
      baseStyles,
      variants[variant],
      sizes[size],
      className
    )

    return (
      <div
        ref={ref}
        className={alertClasses}
        role="alert"
        {...props}
      >
        {showIcon && (
          <div className="flex-shrink-0 mt-0.5">
            {getIcon()}
          </div>
        )}
        
        <div className="flex-1 min-w-0">
          {title && (
            <h4 className="font-medium mb-1">
              {title}
            </h4>
          )}
          <div className="text-current">
            {message}
          </div>
        </div>

        {closable && onClose && (
          <button
            type="button"
            className={cn(
              'flex-shrink-0 p-1 rounded-md transition-colors',
              'hover:bg-black/10 focus:outline-none focus:ring-2 focus:ring-offset-2',
              variant === 'success' && 'focus:ring-green-500',
              variant === 'error' && 'focus:ring-red-500',
              variant === 'warning' && 'focus:ring-yellow-500',
              variant === 'info' && 'focus:ring-blue-500'
            )}
            onClick={onClose}
            aria-label="Close alert"
          >
            <X className={cn(iconSizes[size], 'text-current')} />
          </button>
        )}
      </div>
    )
  }
)

Alert.displayName = 'Alert'

export default Alert