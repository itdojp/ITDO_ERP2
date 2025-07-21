import React from 'react'
import { cn } from '../../lib/utils'
import { usePerformanceMonitor } from '../../hooks/usePerformanceMonitor'

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'default' | 'primary' | 'secondary' | 'outline' | 'ghost' | 'destructive'
  size?: 'sm' | 'md' | 'lg'
  fullWidth?: boolean
  loading?: boolean
  icon?: React.ReactNode
  iconPosition?: 'left' | 'right'
}

const Button = React.memo(React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({
    className,
    variant = 'default',
    size = 'md',
    fullWidth = false,
    loading = false,
    icon,
    iconPosition = 'left',
    disabled,
    children,
    ...props
  }, ref) => {
    // Performance monitoring
    const { metrics } = usePerformanceMonitor({
      componentName: 'Button',
      threshold: 5 // Buttons should render very quickly
    })
    const baseStyles = [
      'inline-flex items-center justify-center rounded-md font-medium transition-colors',
      'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2',
      'disabled:pointer-events-none disabled:opacity-50',
      'relative overflow-hidden'
    ]

    const variants = {
      default: 'bg-primary text-primary-foreground hover:bg-primary/90',
      primary: 'bg-blue-600 text-white hover:bg-blue-700 focus-visible:ring-blue-500',
      secondary: 'bg-gray-100 text-gray-900 hover:bg-gray-200 focus-visible:ring-gray-500',
      outline: 'border border-input bg-background hover:bg-accent hover:text-accent-foreground',
      ghost: 'hover:bg-accent hover:text-accent-foreground',
      destructive: 'bg-red-600 text-white hover:bg-red-700 focus-visible:ring-red-500'
    }

    const sizes = {
      sm: 'h-8 px-3 text-sm',
      md: 'h-10 px-4 py-2',
      lg: 'h-12 px-6 text-lg'
    }

    const buttonClasses = cn(
      baseStyles,
      variants[variant],
      sizes[size],
      fullWidth && 'w-full',
      className
    )

    const renderIcon = React.useCallback((position: 'left' | 'right') => {
      if (!icon || iconPosition !== position) return null
      return (
        <span className={cn(
          'flex items-center',
          position === 'left' ? 'mr-2' : 'ml-2',
          loading && 'opacity-0'
        )}>
          {icon}
        </span>
      )
    }, [icon, iconPosition, loading])

    const renderContent = React.useCallback(() => {
      if (loading) {
        return (
          <>
            <div className="absolute inset-0 flex items-center justify-center">
              <div className="animate-spin rounded-full h-4 w-4 border-2 border-current border-t-transparent" />
            </div>
            <span className="opacity-0 flex items-center">
              {renderIcon('left')}
              {children}
              {renderIcon('right')}
            </span>
          </>
        )
      }

      return (
        <>
          {renderIcon('left')}
          {children}
          {renderIcon('right')}
        </>
      )
    }, [loading, renderIcon, children])

    return (
      <button
        ref={ref}
        className={buttonClasses}
        disabled={disabled || loading}
        {...props}
      >
        {renderContent()}
      </button>
    )
  }
))

Button.displayName = 'Button'

export default Button