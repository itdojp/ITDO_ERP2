import React from 'react'
import { cn } from '../../../lib/utils'

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'default' | 'primary' | 'secondary' | 'outline' | 'ghost' | 'destructive' | 'danger'
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl'
  fullWidth?: boolean
  loading?: boolean
  icon?: React.ReactNode
  iconPosition?: 'left' | 'right'
  rounded?: 'none' | 'sm' | 'md' | 'lg' | 'full'
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
    rounded = 'md',
    disabled,
    children,
    ...props
  }, ref) => {
    const baseStyles = [
      'inline-flex items-center justify-center font-medium transition-all duration-200',
      'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2',
      'disabled:pointer-events-none disabled:opacity-50',
      'relative overflow-hidden',
      'active:scale-95'
    ]

    const variants = {
      default: 'bg-gray-900 text-white hover:bg-gray-800 focus-visible:ring-gray-900',
      primary: 'bg-blue-600 text-white hover:bg-blue-700 focus-visible:ring-blue-500 shadow-md hover:shadow-lg',
      secondary: 'bg-gray-100 text-gray-900 hover:bg-gray-200 focus-visible:ring-gray-500 border border-gray-200',
      outline: 'border border-gray-300 bg-transparent hover:bg-gray-50 focus-visible:ring-gray-500 text-gray-700',
      ghost: 'bg-transparent hover:bg-gray-100 focus-visible:ring-gray-500 text-gray-700',
      destructive: 'bg-red-600 text-white hover:bg-red-700 focus-visible:ring-red-500 shadow-md hover:shadow-lg',
      danger: 'bg-red-600 text-white hover:bg-red-700 focus-visible:ring-red-500 shadow-md hover:shadow-lg'
    }

    const sizes = {
      xs: 'h-6 px-2 text-xs',
      sm: 'h-8 px-3 text-sm',
      md: 'h-10 px-4 py-2 text-base',
      lg: 'h-12 px-6 text-lg',
      xl: 'h-14 px-8 text-xl'
    }

    const roundedOptions = {
      none: 'rounded-none',
      sm: 'rounded-sm',
      md: 'rounded-md',
      lg: 'rounded-lg',
      full: 'rounded-full'
    }

    const buttonClasses = cn(
      baseStyles,
      variants[variant],
      sizes[size],
      roundedOptions[rounded],
      fullWidth && 'w-full',
      className
    )

    const iconSizes = {
      xs: 'h-3 w-3',
      sm: 'h-4 w-4',
      md: 'h-5 w-5',
      lg: 'h-6 w-6',
      xl: 'h-7 w-7'
    }

    const renderIcon = (position: 'left' | 'right') => {
      if (!icon || iconPosition !== position) return null
      return (
        <span className={cn(
          'flex items-center',
          position === 'left' ? 'mr-2' : 'ml-2',
          iconSizes[size],
          loading && 'opacity-0'
        )}>
          {React.isValidElement(icon) 
            ? React.cloneElement(icon, { className: iconSizes[size] } as any)
            : icon
          }
        </span>
      )
    }

    const renderLoadingSpinner = () => (
      <div className="absolute inset-0 flex items-center justify-center">
        <div className={cn(
          'animate-spin rounded-full border-2 border-current border-t-transparent',
          iconSizes[size]
        )} />
      </div>
    )

    const renderContent = () => {
      if (loading) {
        return (
          <>
            {renderLoadingSpinner()}
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
    }

    return (
      <button
        ref={ref}
        type="button"
        className={buttonClasses}
        disabled={disabled || loading}
{...(loading && { 'aria-busy': true })}
        {...props}
      >
        {renderContent()}
      </button>
    )
  }
))

Button.displayName = 'Button'

export default Button