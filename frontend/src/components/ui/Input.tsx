import React from 'react'
import { cn } from '../../lib/utils'
import { Eye, EyeOff, Search, AlertCircle } from 'lucide-react'

export interface InputProps extends Omit<React.InputHTMLAttributes<HTMLInputElement>, 'size'> {
  variant?: 'default' | 'filled' | 'outline'
  size?: 'sm' | 'md' | 'lg'
  error?: boolean
  errorMessage?: string
  label?: string
  helperText?: string
  leftIcon?: React.ReactNode
  rightIcon?: React.ReactNode
  loading?: boolean
}

const Input = React.memo(React.forwardRef<HTMLInputElement, InputProps>(
  ({
    className,
    variant = 'default',
    size = 'md',
    type = 'text',
    error = false,
    errorMessage,
    label,
    helperText,
    leftIcon,
    rightIcon,
    loading = false,
    disabled,
    id,
    ...props
  }, ref) => {
    const [showPassword, setShowPassword] = React.useState(false)
    const generatedId = React.useId()
    const inputId = id || generatedId

    const isPassword = type === 'password'
    const isSearch = type === 'search'
    const actualType = isPassword && showPassword ? 'text' : type

    const baseStyles = [
      'flex w-full rounded-md border transition-colors duration-200',
      'focus-within:outline-none focus-within:ring-2 focus-within:ring-offset-2',
      'disabled:cursor-not-allowed disabled:opacity-50'
    ]

    const variants = {
      default: [
        'border-gray-300 bg-white',
        'focus-within:border-blue-500 focus-within:ring-blue-500/20',
        error && 'border-red-500 focus-within:border-red-500 focus-within:ring-red-500/20'
      ],
      filled: [
        'border-transparent bg-gray-100',
        'focus-within:bg-white focus-within:border-blue-500 focus-within:ring-blue-500/20',
        error && 'bg-red-50 border-red-200 focus-within:border-red-500 focus-within:ring-red-500/20'
      ],
      outline: [
        'border-gray-200 bg-transparent',
        'focus-within:border-blue-500 focus-within:ring-blue-500/20',
        error && 'border-red-500 focus-within:border-red-500 focus-within:ring-red-500/20'
      ]
    }

    const sizes = {
      sm: {
        container: 'h-8',
        input: 'px-3 py-1 text-sm',
        icon: 'h-4 w-4',
        padding: 'pl-8'
      },
      md: {
        container: 'h-10',
        input: 'px-3 py-2 text-base',
        icon: 'h-5 w-5',
        padding: 'pl-10'
      },
      lg: {
        container: 'h-12',
        input: 'px-4 py-3 text-lg',
        icon: 'h-6 w-6',
        padding: 'pl-12'
      }
    }

    const inputClasses = cn(
      'flex-1 border-none bg-transparent outline-none placeholder:text-gray-500',
      sizes[size].input,
      (leftIcon || isSearch) && sizes[size].padding,
      rightIcon && 'pr-10',
      isPassword && 'pr-10'
    )

    const containerClasses = cn(
      baseStyles,
      variants[variant],
      sizes[size].container,
      className
    )

    const renderIcon = (icon: React.ReactNode, position: 'left' | 'right') => {
      const iconClasses = cn(
        'absolute top-1/2 transform -translate-y-1/2 text-gray-500',
        sizes[size].icon,
        position === 'left' ? 'left-3' : 'right-3'
      )

      if (React.isValidElement(icon)) {
        return React.cloneElement(icon, { className: iconClasses } as React.HTMLAttributes<HTMLElement>)
      }

      return <div className={iconClasses}>{icon}</div>
    }

    const renderPasswordToggle = () => {
      if (!isPassword) return null

      return (
        <button
          type="button"
          className={cn(
            'absolute right-3 top-1/2 transform -translate-y-1/2',
            'text-gray-500 hover:text-gray-700 focus:outline-none',
            sizes[size].icon
          )}
          onClick={() => setShowPassword(!showPassword)}
          tabIndex={-1}
        >
          {showPassword ? (
            <EyeOff className={sizes[size].icon} />
          ) : (
            <Eye className={sizes[size].icon} />
          )}
        </button>
      )
    }

    const renderSearchIcon = () => {
      if (!isSearch || leftIcon) return null

      return renderIcon(<Search />, 'left')
    }

    return (
      <div className="space-y-1">
        {label && (
          <label
            htmlFor={inputId}
            className={cn(
              'block text-sm font-medium',
              error ? 'text-red-700' : 'text-gray-700'
            )}
          >
            {label}
          </label>
        )}
        
        <div className="relative">
          <div className={containerClasses}>
            {renderSearchIcon()}
            {leftIcon && renderIcon(leftIcon, 'left')}
            
            <input
              ref={ref}
              id={inputId}
              type={actualType}
              className={inputClasses}
              disabled={disabled || loading}
              {...props}
            />
            
            {loading && (
              <div className="absolute right-3 top-1/2 transform -translate-y-1/2">
                <div className={cn(
                  'animate-spin rounded-full border-2 border-gray-300 border-t-blue-600',
                  sizes[size].icon
                )} />
              </div>
            )}
            
            {!loading && rightIcon && renderIcon(rightIcon, 'right')}
            {!loading && renderPasswordToggle()}
          </div>
          
          {error && errorMessage && (
            <div className="flex items-center gap-1 mt-1">
              <AlertCircle className="h-4 w-4 text-red-500" />
              <span className="text-sm text-red-600">{errorMessage}</span>
            </div>
          )}
        </div>
        
        {helperText && !error && (
          <p className="text-sm text-gray-600">{helperText}</p>
        )}
      </div>
    )
  }
))

Input.displayName = 'Input'

export default Input