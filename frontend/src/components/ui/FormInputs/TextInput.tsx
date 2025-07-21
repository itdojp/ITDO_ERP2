import React from 'react'
import { cn } from '../../../lib/utils'
import { Eye, EyeOff, Search, AlertCircle, CheckCircle2, X } from 'lucide-react'

export interface TextInputProps extends Omit<React.InputHTMLAttributes<HTMLInputElement>, 'size'> {
  variant?: 'default' | 'filled' | 'outline' | 'underlined'
  size?: 'sm' | 'md' | 'lg'
  error?: boolean
  success?: boolean
  errorMessage?: string
  successMessage?: string
  label?: string
  helperText?: string
  leftIcon?: React.ReactNode
  rightIcon?: React.ReactNode
  loading?: boolean
  clearable?: boolean
  onClear?: () => void
  validation?: {
    required?: boolean
    minLength?: number
    maxLength?: number
    pattern?: RegExp
    customValidator?: (value: string) => string | null
  }
}

const TextInput = React.memo(React.forwardRef<HTMLInputElement, TextInputProps>(
  ({
    className,
    variant = 'default',
    size = 'md',
    type = 'text',
    error = false,
    success = false,
    errorMessage,
    successMessage,
    label,
    helperText,
    leftIcon,
    rightIcon,
    loading = false,
    clearable = false,
    onClear,
    validation,
    disabled,
    id,
    value,
    onChange,
    onBlur,
    ...props
  }, ref) => {
    const [showPassword, setShowPassword] = React.useState(false)
    const [validationError, setValidationError] = React.useState<string | null>(null)
    const [touched, setTouched] = React.useState(false)
    const generatedId = React.useId()
    const inputId = id || generatedId

    const isPassword = type === 'password'
    const isSearch = type === 'search'
    const actualType = isPassword && showPassword ? 'text' : type
    const hasError = error || (touched && !!validationError)
    const hasSuccess = success && !hasError

    const validateInput = React.useCallback((inputValue: string) => {
      if (!validation || !touched) return null

      if (validation.required && !inputValue.trim()) {
        return 'This field is required'
      }

      if (validation.minLength && inputValue.length < validation.minLength) {
        return `Minimum length is ${validation.minLength} characters`
      }

      if (validation.maxLength && inputValue.length > validation.maxLength) {
        return `Maximum length is ${validation.maxLength} characters`
      }

      if (validation.pattern && !validation.pattern.test(inputValue)) {
        return 'Invalid format'
      }

      if (validation.customValidator) {
        return validation.customValidator(inputValue)
      }

      return null
    }, [validation, touched])

    const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
      const newValue = e.target.value
      onChange?.(e)
      
      if (touched) {
        const error = validateInput(newValue)
        setValidationError(error)
      }
    }

    const handleBlur = (e: React.FocusEvent<HTMLInputElement>) => {
      if (!touched) setTouched(true)
      onBlur?.(e)
      
      const error = validateInput(e.target.value)
      setValidationError(error)
    }

    const handleClear = () => {
      if (onClear) {
        onClear()
      } else if (onChange) {
        const event = {
          target: { value: '' },
          currentTarget: { value: '' }
        } as React.ChangeEvent<HTMLInputElement>
        onChange(event)
      }
      setValidationError(null)
    }

    const baseStyles = [
      'flex w-full transition-all duration-200',
      'focus-within:outline-none focus-within:ring-2 focus-within:ring-offset-1',
      'disabled:cursor-not-allowed disabled:opacity-50'
    ]

    const variants = {
      default: [
        'border rounded-md bg-white',
        'focus-within:border-blue-500 focus-within:ring-blue-500/20',
        hasError && 'border-red-500 focus-within:border-red-500 focus-within:ring-red-500/20',
        hasSuccess && 'border-green-500 focus-within:border-green-500 focus-within:ring-green-500/20',
        !hasError && !hasSuccess && 'border-gray-300'
      ],
      filled: [
        'border border-transparent rounded-md bg-gray-100',
        'focus-within:bg-white focus-within:border-blue-500 focus-within:ring-blue-500/20',
        hasError && 'bg-red-50 border-red-200 focus-within:border-red-500 focus-within:ring-red-500/20',
        hasSuccess && 'bg-green-50 border-green-200 focus-within:border-green-500 focus-within:ring-green-500/20'
      ],
      outline: [
        'border-2 rounded-md bg-transparent',
        'focus-within:border-blue-500 focus-within:ring-blue-500/20',
        hasError && 'border-red-500 focus-within:border-red-500 focus-within:ring-red-500/20',
        hasSuccess && 'border-green-500 focus-within:border-green-500 focus-within:ring-green-500/20',
        !hasError && !hasSuccess && 'border-gray-200'
      ],
      underlined: [
        'border-b-2 border-t-0 border-l-0 border-r-0 rounded-none bg-transparent',
        'focus-within:border-blue-500',
        hasError && 'border-red-500 focus-within:border-red-500',
        hasSuccess && 'border-green-500 focus-within:border-green-500',
        !hasError && !hasSuccess && 'border-gray-300'
      ]
    }

    const sizes = {
      sm: {
        container: 'h-8',
        input: 'px-3 py-1 text-sm',
        icon: 'h-4 w-4',
        leftPadding: 'pl-8',
        rightPadding: 'pr-8'
      },
      md: {
        container: 'h-10',
        input: 'px-3 py-2 text-base',
        icon: 'h-5 w-5',
        leftPadding: 'pl-10',
        rightPadding: 'pr-10'
      },
      lg: {
        container: 'h-12',
        input: 'px-4 py-3 text-lg',
        icon: 'h-6 w-6',
        leftPadding: 'pl-12',
        rightPadding: 'pr-12'
      }
    }

    const inputClasses = cn(
      'flex-1 border-none bg-transparent outline-none placeholder:text-gray-500',
      sizes[size].input,
      (leftIcon || isSearch) && sizes[size].leftPadding,
      (rightIcon || isPassword || clearable || loading || hasError || hasSuccess) && sizes[size].rightPadding
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
        return React.cloneElement(icon, { className: iconClasses } as any)
      }

      return <div className={iconClasses}>{icon}</div>
    }

    const renderRightIcons = () => {
      const icons = []
      let rightOffset = 3

      // Status icons (leftmost)
      if (hasError) {
        icons.push(
          <AlertCircle 
            key="error" 
            className={cn(
              'absolute top-1/2 transform -translate-y-1/2 text-red-500',
              sizes[size].icon
            )}
            style={{ right: `${rightOffset * 0.75}rem` }}
          />
        )
        rightOffset += 6
      } else if (hasSuccess) {
        icons.push(
          <CheckCircle2 
            key="success" 
            className={cn(
              'absolute top-1/2 transform -translate-y-1/2 text-green-500',
              sizes[size].icon
            )}
            style={{ right: `${rightOffset * 0.75}rem` }}
          />
        )
        rightOffset += 6
      }

      // Loading spinner
      if (loading) {
        icons.push(
          <div 
            key="loading"
            className={cn(
              'absolute top-1/2 transform -translate-y-1/2 animate-spin rounded-full border-2 border-gray-300 border-t-blue-600',
              sizes[size].icon
            )}
            style={{ right: `${rightOffset * 0.75}rem` }}
          />
        )
        rightOffset += 6
      }

      // Clear button
      if (clearable && value && !loading) {
        icons.push(
          <button
            key="clear"
            type="button"
            onClick={handleClear}
            className={cn(
              'absolute top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600 focus:outline-none',
              sizes[size].icon
            )}
            style={{ right: `${rightOffset * 0.75}rem` }}
            tabIndex={-1}
          >
            <X className={sizes[size].icon} />
          </button>
        )
        rightOffset += 6
      }

      // Password toggle
      if (isPassword && !loading) {
        icons.push(
          <button
            key="password-toggle"
            type="button"
            onClick={() => setShowPassword(!showPassword)}
            className={cn(
              'absolute top-1/2 transform -translate-y-1/2 text-gray-500 hover:text-gray-700 focus:outline-none',
              sizes[size].icon
            )}
            style={{ right: `${rightOffset * 0.75}rem` }}
            tabIndex={-1}
          >
            {showPassword ? (
              <EyeOff className={sizes[size].icon} />
            ) : (
              <Eye className={sizes[size].icon} />
            )}
          </button>
        )
        rightOffset += 6
      }

      // Custom right icon (rightmost)
      if (rightIcon && !loading) {
        icons.push(
          <div 
            key="custom-right"
            className={cn(
              'absolute top-1/2 transform -translate-y-1/2',
              sizes[size].icon
            )}
            style={{ right: `${rightOffset * 0.75}rem` }}
          >
            {renderIcon(rightIcon, 'right')}
          </div>
        )
      }

      return icons
    }

    const renderSearchIcon = () => {
      if (!isSearch || leftIcon) return null
      return renderIcon(<Search />, 'left')
    }

    const finalErrorMessage = errorMessage || validationError
    const finalSuccessMessage = successMessage

    return (
      <div className="w-full">
        {label && (
          <label
            htmlFor={inputId}
            className={cn(
              'block text-sm font-medium mb-1',
              hasError ? 'text-red-700' : hasSuccess ? 'text-green-700' : 'text-gray-700'
            )}
          >
            {label}
            {validation?.required && <span className="text-red-500 ml-1">*</span>}
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
              value={value}
              onChange={handleChange}
              onBlur={handleBlur}
              aria-invalid={hasError}
              aria-describedby={cn(
                finalErrorMessage && `${inputId}-error`,
                finalSuccessMessage && `${inputId}-success`,
                helperText && `${inputId}-helper`
              )}
              {...props}
            />
            
            {renderRightIcons()}
          </div>
        </div>
        
        {finalErrorMessage && (
          <div id={`${inputId}-error`} className="flex items-center gap-1 mt-1">
            <AlertCircle className="h-4 w-4 text-red-500 flex-shrink-0" />
            <span className="text-sm text-red-600">{finalErrorMessage}</span>
          </div>
        )}
        
        {finalSuccessMessage && !hasError && (
          <div id={`${inputId}-success`} className="flex items-center gap-1 mt-1">
            <CheckCircle2 className="h-4 w-4 text-green-500 flex-shrink-0" />
            <span className="text-sm text-green-600">{finalSuccessMessage}</span>
          </div>
        )}
        
        {helperText && !hasError && !finalSuccessMessage && (
          <p id={`${inputId}-helper`} className="text-sm text-gray-600 mt-1">
            {helperText}
          </p>
        )}
      </div>
    )
  }
))

TextInput.displayName = 'TextInput'

export default TextInput