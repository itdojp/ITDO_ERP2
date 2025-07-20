import React from 'react'
import { cn } from '../../lib/utils'
import { AlertCircle } from 'lucide-react'

export interface TextareaProps extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
  variant?: 'default' | 'filled' | 'outline'
  size?: 'sm' | 'md' | 'lg'
  error?: boolean
  errorMessage?: string
  label?: string
  helperText?: string
  resize?: 'none' | 'vertical' | 'horizontal' | 'both'
  loading?: boolean
}

const Textarea = React.forwardRef<HTMLTextAreaElement, TextareaProps>(
  ({
    className,
    variant = 'default',
    size = 'md',
    error = false,
    errorMessage,
    label,
    helperText,
    resize = 'vertical',
    loading = false,
    disabled,
    id,
    rows = 3,
    ...props
  }, ref) => {
    const textareaId = id || React.useId()

    const baseStyles = [
      'w-full rounded-md border transition-colors duration-200',
      'focus:outline-none focus:ring-2 focus:ring-offset-2',
      'disabled:cursor-not-allowed disabled:opacity-50'
    ]

    const variants = {
      default: [
        'border-gray-300 bg-white',
        'focus:border-blue-500 focus:ring-blue-500/20',
        error && 'border-red-500 focus:border-red-500 focus:ring-red-500/20'
      ],
      filled: [
        'border-transparent bg-gray-100',
        'focus:bg-white focus:border-blue-500 focus:ring-blue-500/20',
        error && 'bg-red-50 border-red-200 focus:border-red-500 focus:ring-red-500/20'
      ],
      outline: [
        'border-gray-200 bg-transparent',
        'focus:border-blue-500 focus:ring-blue-500/20',
        error && 'border-red-500 focus:border-red-500 focus:ring-red-500/20'
      ]
    }

    const sizes = {
      sm: 'px-3 py-2 text-sm',
      md: 'px-3 py-2 text-base',
      lg: 'px-4 py-3 text-lg'
    }

    const resizeClasses = {
      none: 'resize-none',
      vertical: 'resize-y',
      horizontal: 'resize-x',
      both: 'resize'
    }

    const textareaClasses = cn(
      baseStyles,
      variants[variant],
      sizes[size],
      resizeClasses[resize],
      'placeholder:text-gray-500',
      className
    )

    return (
      <div className="space-y-1">
        {label && (
          <label
            htmlFor={textareaId}
            className={cn(
              'block text-sm font-medium',
              error ? 'text-red-700' : 'text-gray-700'
            )}
          >
            {label}
          </label>
        )}
        
        <div className="relative">
          <textarea
            ref={ref}
            id={textareaId}
            rows={rows}
            className={textareaClasses}
            disabled={disabled || loading}
            {...props}
          />
          
          {loading && (
            <div className="absolute right-3 top-3">
              <div className="h-5 w-5 animate-spin rounded-full border-2 border-gray-300 border-t-blue-600" />
            </div>
          )}
          
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
)

Textarea.displayName = 'Textarea'

export default Textarea