import React from 'react'
import { cn } from '../../../lib/utils'

export interface RadioOption {
  value: string
  label: string
  description?: string
  disabled?: boolean
}

export interface RadioProps {
  options: RadioOption[]
  value?: string
  onChange?: (value: string) => void
  name: string
  label?: string
  description?: string
  error?: boolean
  errorMessage?: string
  size?: 'sm' | 'md' | 'lg'
  variant?: 'default' | 'card'
  orientation?: 'horizontal' | 'vertical'
  disabled?: boolean
  className?: string
}

const Radio = React.memo(React.forwardRef<HTMLFieldSetElement, RadioProps>(
  ({
    options = [],
    value,
    onChange,
    name,
    label,
    description,
    error = false,
    errorMessage,
    size = 'md',
    variant = 'default',
    orientation = 'vertical',
    disabled = false,
    className,
  }, ref) => {
    const sizes = {
      sm: {
        radio: 'h-4 w-4',
        text: 'text-sm',
        dot: 'h-2 w-2',
        gap: 'gap-2'
      },
      md: {
        radio: 'h-5 w-5',
        text: 'text-base',
        dot: 'h-2.5 w-2.5',
        gap: 'gap-3'
      },
      lg: {
        radio: 'h-6 w-6',
        text: 'text-lg',
        dot: 'h-3 w-3',
        gap: 'gap-4'
      }
    }

    const radioClasses = cn(
      'relative border-2 rounded-full transition-all duration-200 cursor-pointer',
      'focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500',
      'disabled:cursor-not-allowed disabled:opacity-50',
      sizes[size].radio,
      error ? 'border-red-500' : 'border-gray-300',
      'hover:border-blue-500 disabled:hover:border-gray-300'
    )

    const containerClasses = cn(
      'flex flex-col gap-3',
      className
    )

    const optionsContainerClasses = cn(
      'flex',
      orientation === 'horizontal' ? 'flex-row flex-wrap gap-6' : 'flex-col gap-3'
    )

    const optionClasses = cn(
      'flex items-start',
      sizes[size].gap,
      variant === 'card' && 'p-4 border border-gray-200 rounded-lg hover:border-blue-200 transition-colors cursor-pointer',
      variant === 'card' && error && 'border-red-500 bg-red-50'
    )

    const handleOptionChange = (optionValue: string) => {
      if (!disabled && onChange) {
        onChange(optionValue)
      }
    }

    const handleCardClick = (optionValue: string, optionDisabled?: boolean) => {
      if (variant === 'card' && !disabled && !optionDisabled) {
        handleOptionChange(optionValue)
      }
    }

    return (
      <fieldset ref={ref} className={containerClasses} disabled={disabled}>
        {label && (
          <legend className={cn(
            'font-medium',
            sizes[size].text,
            error ? 'text-red-700' : 'text-gray-900'
          )}>
            {label}
          </legend>
        )}
        
        {description && (
          <p className={cn(
            'text-gray-600 -mt-2',
            size === 'sm' ? 'text-xs' : size === 'lg' ? 'text-base' : 'text-sm'
          )}>
            {description}
          </p>
        )}

        <div 
          className={optionsContainerClasses}
          role="radiogroup"
          aria-invalid={error}
          aria-describedby={error && errorMessage ? `${name}-error` : undefined}
        >
          {options.map((option) => {
            const isSelected = value === option.value
            const isDisabled = disabled || option.disabled

            return (
              <div
                key={option.value}
                className={cn(
                  optionClasses,
                  variant === 'card' && isSelected && 'border-blue-500 bg-blue-50',
                  variant === 'card' && isDisabled && 'opacity-50 cursor-not-allowed'
                )}
                onClick={() => handleCardClick(option.value, option.disabled)}
              >
                <div className="relative flex-shrink-0">
                  <input
                    type="radio"
                    id={`${name}-${option.value}`}
                    name={name}
                    value={option.value}
                    checked={isSelected}
                    disabled={isDisabled}
                    onChange={() => handleOptionChange(option.value)}
                    className="sr-only"
                  />
                  <label 
                    htmlFor={`${name}-${option.value}`}
                    className={cn(
                      radioClasses,
                      isSelected && (error ? 'bg-red-500 border-red-500' : 'bg-blue-600 border-blue-600'),
                      !isSelected && 'bg-white'
                    )}
                    onClick={(e) => {
                      if (variant === 'card') {
                        e.stopPropagation()
                      }
                    }}
                  >
                    {isSelected && (
                      <div className={cn(
                        'absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 rounded-full bg-white',
                        sizes[size].dot
                      )} />
                    )}
                  </label>
                </div>

                <div className="flex-1 min-w-0">
                  <label
                    htmlFor={`${name}-${option.value}`}
                    className={cn(
                      'font-medium cursor-pointer block',
                      sizes[size].text,
                      error ? 'text-red-700' : 'text-gray-900',
                      isDisabled && 'cursor-not-allowed opacity-50'
                    )}
                    onClick={(e) => {
                      if (variant === 'card') {
                        e.stopPropagation()
                      }
                    }}
                  >
                    {option.label}
                  </label>
                  
                  {option.description && (
                    <p className={cn(
                      'text-gray-600 mt-1',
                      size === 'sm' ? 'text-xs' : size === 'lg' ? 'text-base' : 'text-sm',
                      isDisabled && 'opacity-50'
                    )}>
                      {option.description}
                    </p>
                  )}
                </div>
              </div>
            )
          })}
        </div>

        {error && errorMessage && (
          <div id={`${name}-error`} className="flex items-center gap-1">
            <span className="text-sm text-red-600">{errorMessage}</span>
          </div>
        )}
      </fieldset>
    )
  }
))

Radio.displayName = 'Radio'

export default Radio