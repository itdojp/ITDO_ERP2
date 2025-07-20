import React, { useEffect, useState } from 'react'
import { cn } from '../../lib/utils'
import { AlertCircle, CheckCircle, Info, X, AlertTriangle } from 'lucide-react'

export interface ToastProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: 'success' | 'error' | 'warning' | 'info'
  position?: 'top-right' | 'top-left' | 'bottom-right' | 'bottom-left' | 'top-center' | 'bottom-center'
  title?: string
  message: string
  duration?: number
  onClose?: () => void
  showIcon?: boolean
  closable?: boolean
}

const Toast = React.forwardRef<HTMLDivElement, ToastProps>(
  ({
    className,
    variant = 'info',
    position = 'top-right',
    title,
    message,
    duration = 5000,
    onClose,
    showIcon = true,
    closable = true,
    ...props
  }, ref) => {
    const [isVisible, setIsVisible] = useState(true)
    const [isExiting, setIsExiting] = useState(false)

    useEffect(() => {
      if (duration > 0) {
        const timer = setTimeout(() => {
          handleClose()
        }, duration)

        return () => clearTimeout(timer)
      }
    }, [duration])

    const handleClose = () => {
      setIsExiting(true)
      setTimeout(() => {
        setIsVisible(false)
        onClose?.()
      }, 200)
    }

    if (!isVisible) return null

    const baseStyles = [
      'fixed z-50 max-w-sm w-full rounded-lg border shadow-lg p-4',
      'flex items-start gap-3 transition-all duration-200',
      'bg-white border-gray-200'
    ]

    const positions = {
      'top-right': 'top-4 right-4',
      'top-left': 'top-4 left-4',
      'bottom-right': 'bottom-4 right-4',
      'bottom-left': 'bottom-4 left-4',
      'top-center': 'top-4 left-1/2 transform -translate-x-1/2',
      'bottom-center': 'bottom-4 left-1/2 transform -translate-x-1/2'
    }

    const variants = {
      success: 'border-green-200',
      error: 'border-red-200',
      warning: 'border-yellow-200',
      info: 'border-blue-200'
    }

    const iconVariants = {
      success: 'text-green-600',
      error: 'text-red-600',
      warning: 'text-yellow-600',
      info: 'text-blue-600'
    }

    const textVariants = {
      success: 'text-green-800',
      error: 'text-red-800',
      warning: 'text-yellow-800',
      info: 'text-blue-800'
    }

    const getIcon = () => {
      const iconClass = cn('h-5 w-5', iconVariants[variant])
      
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

    const toastClasses = cn(
      baseStyles,
      positions[position],
      variants[variant],
      isExiting ? 'opacity-0 scale-95' : 'opacity-100 scale-100',
      className
    )

    return (
      <div
        ref={ref}
        className={toastClasses}
        role="alert"
        aria-live="polite"
        {...props}
      >
        {showIcon && (
          <div className="flex-shrink-0 mt-0.5">
            {getIcon()}
          </div>
        )}
        
        <div className="flex-1 min-w-0">
          {title && (
            <h4 className={cn('font-medium mb-1', textVariants[variant])}>
              {title}
            </h4>
          )}
          <div className={cn('text-sm', textVariants[variant])}>
            {message}
          </div>
        </div>

        {closable && (
          <button
            type="button"
            className={cn(
              'flex-shrink-0 p-1 rounded-md transition-colors text-gray-500',
              'hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-500'
            )}
            onClick={handleClose}
            aria-label="Close toast"
          >
            <X className="h-4 w-4" />
          </button>
        )}
      </div>
    )
  }
)

Toast.displayName = 'Toast'

export default Toast