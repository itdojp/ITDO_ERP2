import React from 'react'
import { cn } from '../../../lib/utils'
import { Check, Minus } from 'lucide-react'

export interface CheckboxProps extends Omit<React.InputHTMLAttributes<HTMLInputElement>, 'size'> {
  label?: string
  description?: string
  error?: boolean
  errorMessage?: string
  size?: 'sm' | 'md' | 'lg'
  variant?: 'default' | 'card'
  indeterminate?: boolean
  labelPosition?: 'right' | 'left'
}

const Checkbox = React.memo(React.forwardRef<HTMLInputElement, CheckboxProps>(
  ({
    className,
    label,
    description,
    error = false,
    errorMessage,
    size = 'md',
    variant = 'default',
    indeterminate = false,
    labelPosition = 'right',
    disabled,
    checked,
    id,
    ...props
  }, ref) => {
    const generatedId = React.useId()
    const checkboxId = id || generatedId
    
    const inputRef = React.useRef<HTMLInputElement>(null)
    
    React.useImperativeHandle(ref, () => inputRef.current!)

    React.useEffect(() => {
      if (inputRef.current) {
        inputRef.current.indeterminate = indeterminate
      }
    }, [indeterminate])

    const sizes = {
      sm: {
        checkbox: 'h-4 w-4',
        text: 'text-sm',
        icon: 'h-3 w-3',
        gap: 'gap-2'
      },
      md: {
        checkbox: 'h-5 w-5',
        text: 'text-base',
        icon: 'h-4 w-4',
        gap: 'gap-3'
      },
      lg: {
        checkbox: 'h-6 w-6',
        text: 'text-lg',
        icon: 'h-5 w-5',
        gap: 'gap-4'
      }
    }

    const checkboxClasses = cn(
      'relative border-2 rounded transition-all duration-200 cursor-pointer',
      'focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500',
      'disabled:cursor-not-allowed disabled:opacity-50',
      sizes[size].checkbox,
      error ? 'border-red-500' : 'border-gray-300',
      checked || indeterminate ? (error ? 'bg-red-500 border-red-500' : 'bg-blue-600 border-blue-600') : 'bg-white',
      'hover:border-blue-500 disabled:hover:border-gray-300'
    )

    const containerClasses = cn(
      'flex items-start',
      sizes[size].gap,
      variant === 'card' && 'p-4 border border-gray-200 rounded-lg hover:border-blue-200 transition-colors',
      variant === 'card' && checked && 'border-blue-500 bg-blue-50',
      variant === 'card' && error && 'border-red-500 bg-red-50',
      labelPosition === 'left' && 'flex-row-reverse',
      className
    )

    const renderCheckIcon = () => {
      if (indeterminate) {
        return <Minus className={cn('text-white', sizes[size].icon)} />
      }
      if (checked) {
        return <Check className={cn('text-white', sizes[size].icon)} />
      }
      return null
    }

    const handleContainerClick = () => {
      if (!disabled && inputRef.current) {
        inputRef.current.click()
      }
    }

    return (
      <div className="w-full">
        <div 
          className={containerClasses}
          onClick={variant === 'card' ? handleContainerClick : undefined}
        >
          <div className="relative flex-shrink-0">
            <input
              ref={inputRef}
              type="checkbox"
              id={checkboxId}
              className="sr-only"
              disabled={disabled}
              checked={checked}
              aria-invalid={error}
              aria-describedby={error && errorMessage ? `${checkboxId}-error` : undefined}
              {...props}
            />
            <label 
              htmlFor={checkboxId}
              className={checkboxClasses}
              onClick={(e) => {
                if (variant === 'card') {
                  e.stopPropagation()
                }
              }}
            >
              <div className="absolute inset-0 flex items-center justify-center">
                {renderCheckIcon()}
              </div>
            </label>
          </div>

          {(label || description) && (
            <div 
              className={cn(
                'flex-1',
                labelPosition === 'left' && 'text-right'
              )}
              onClick={variant !== 'card' ? handleContainerClick : undefined}
            >
              {label && (
                <label
                  htmlFor={checkboxId}
                  className={cn(
                    'font-medium cursor-pointer',
                    sizes[size].text,
                    error ? 'text-red-700' : 'text-gray-900',
                    disabled && 'cursor-not-allowed opacity-50'
                  )}
                  onClick={(e) => {
                    if (variant === 'card') {
                      e.stopPropagation()
                    }
                  }}
                >
                  {label}
                </label>
              )}
              
              {description && (
                <p className={cn(
                  'text-gray-600 mt-1',
                  size === 'sm' ? 'text-xs' : size === 'lg' ? 'text-base' : 'text-sm',
                  disabled && 'opacity-50'
                )}>
                  {description}
                </p>
              )}
            </div>
          )}
        </div>

        {error && errorMessage && (
          <div id={`${checkboxId}-error`} className="flex items-center gap-1 mt-1">
            <span className="text-sm text-red-600">{errorMessage}</span>
          </div>
        )}
      </div>
    )
  }
))

Checkbox.displayName = 'Checkbox'

export default Checkbox