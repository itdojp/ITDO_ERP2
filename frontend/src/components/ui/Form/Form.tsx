import React from 'react'
import { cn } from '../../../lib/utils'
import useFormValidation, { FormValidationConfig } from '../../../hooks/useFormValidation'

export interface FormProps {
  children: React.ReactNode | ((formProps: ReturnType<typeof useFormValidation>) => React.ReactNode)
  initialValues?: Record<string, any>
  validationConfig: FormValidationConfig
  onSubmit?: (values: Record<string, any>) => void | Promise<void>
  validateOnMount?: boolean
  className?: string
  noValidate?: boolean
}

export interface FormGroupProps {
  children: React.ReactNode
  className?: string
  error?: boolean
}

export interface FormErrorProps {
  message?: string | null
  className?: string
}

export interface FormFieldProps {
  name: string
  label?: string
  required?: boolean
  error?: string | null
  helpText?: string
  children: React.ReactNode
  className?: string
  labelClassName?: string
  errorClassName?: string
  helpClassName?: string
}

// Form Context
interface FormContextValue {
  formProps: ReturnType<typeof useFormValidation>
}

const FormContext = React.createContext<FormContextValue | null>(null)

export const useFormContext = () => {
  const context = React.useContext(FormContext)
  if (!context) {
    throw new Error('Form components must be used within a Form component')
  }
  return context
}

// Main Form Component
const Form = React.memo<FormProps>(({
  children,
  initialValues,
  validationConfig,
  onSubmit,
  validateOnMount = false,
  className,
  noValidate = true,
}) => {
  const formProps = useFormValidation({
    initialValues,
    validationConfig,
    onSubmit,
    validateOnMount,
  })

  const contextValue = React.useMemo((): FormContextValue => ({
    formProps,
  }), [formProps])

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    formProps.handleSubmit()
  }

  return (
    <FormContext.Provider value={contextValue}>
      <form
        onSubmit={handleSubmit}
        noValidate={noValidate}
        className={cn('space-y-6', className)}
      >
        {typeof children === 'function' ? children(formProps) : children}
      </form>
    </FormContext.Provider>
  )
})

Form.displayName = 'Form'

// Form Group Component
const FormGroup = React.memo<FormGroupProps>(({
  children,
  className,
  error = false,
}) => {
  return (
    <div
      className={cn(
        'space-y-2',
        error && 'space-y-1',
        className
      )}
    >
      {children}
    </div>
  )
})

FormGroup.displayName = 'FormGroup'

// Form Error Component
const FormError = React.memo<FormErrorProps>(({
  message,
  className,
}) => {
  if (!message) return null

  return (
    <div
      className={cn(
        'text-sm text-red-600 flex items-center gap-1',
        className
      )}
      role="alert"
      aria-live="polite"
    >
      <span className="inline-block w-1 h-1 bg-red-600 rounded-full flex-shrink-0 mt-2" />
      <span>{message}</span>
    </div>
  )
})

FormError.displayName = 'FormError'

// Form Field Component
const FormField = React.memo<FormFieldProps>(({
  name,
  label,
  required,
  error,
  helpText,
  children,
  className,
  labelClassName,
  errorClassName,
  helpClassName,
}) => {
  const fieldId = `field-${name}`
  const errorId = `${fieldId}-error`
  const helpId = `${fieldId}-help`

  return (
    <FormGroup className={className} error={!!error}>
      {label && (
        <label
          htmlFor={fieldId}
          className={cn(
            'block text-sm font-medium text-gray-700',
            labelClassName
          )}
        >
          {label}
          {required && <span className="text-red-500 ml-1">*</span>}
        </label>
      )}
      
      <div className="relative">
        {React.cloneElement(children as React.ReactElement, {
          id: fieldId,
          'aria-describedby': cn(
            error ? errorId : '',
            helpText ? helpId : ''
          ).trim() || undefined,
          'aria-invalid': !!error,
        })}
      </div>

      {error && (
        <FormError
          message={error}
          className={errorClassName}
        />
      )}

      {helpText && !error && (
        <div
          id={helpId}
          className={cn(
            'text-sm text-gray-500',
            helpClassName
          )}
        >
          {helpText}
        </div>
      )}
    </FormGroup>
  )
})

FormField.displayName = 'FormField'

// Form Submit Button Component
export interface FormSubmitProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  loading?: boolean
  loadingText?: string
  variant?: 'primary' | 'secondary' | 'outline'
  size?: 'sm' | 'md' | 'lg'
}

const FormSubmit = React.memo<FormSubmitProps>(({
  children,
  loading,
  loadingText = 'Submitting...',
  disabled,
  variant = 'primary',
  size = 'md',
  className,
  ...props
}) => {
  const { formProps } = useFormContext()
  const isDisabled = disabled || loading || formProps.isSubmitting || !formProps.isValid

  const variants = {
    primary: 'bg-blue-600 hover:bg-blue-700 text-white border-blue-600',
    secondary: 'bg-gray-600 hover:bg-gray-700 text-white border-gray-600',
    outline: 'bg-transparent hover:bg-blue-50 text-blue-600 border-blue-600',
  }

  const sizes = {
    sm: 'px-3 py-1.5 text-sm',
    md: 'px-4 py-2 text-sm',
    lg: 'px-6 py-3 text-base',
  }

  const buttonClasses = cn(
    'inline-flex items-center justify-center font-medium rounded-md border',
    'transition-colors duration-200',
    'focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2',
    'disabled:opacity-50 disabled:cursor-not-allowed',
    variants[variant],
    sizes[size],
    className
  )

  return (
    <button
      type="submit"
      disabled={isDisabled}
      className={buttonClasses}
      {...props}
    >
      {(loading || formProps.isSubmitting) ? (
        <>
          <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2" />
          {loadingText}
        </>
      ) : (
        children
      )}
    </button>
  )
})

FormSubmit.displayName = 'FormSubmit'

// Connected Form Input Component
export interface ConnectedFormInputProps {
  name: string
  label?: string
  type?: 'text' | 'email' | 'password' | 'number' | 'tel' | 'url'
  placeholder?: string
  helpText?: string
  required?: boolean
  disabled?: boolean
  autoComplete?: string
  className?: string
  inputClassName?: string
}

const ConnectedFormInput = React.memo<ConnectedFormInputProps>(({
  name,
  label,
  required,
  helpText,
  className,
  inputClassName,
  ...inputProps
}) => {
  const { formProps } = useFormContext()
  const fieldProps = formProps.getFieldProps(name)

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    fieldProps.onChange(e.target.value)
  }

  const handleBlur = () => {
    fieldProps.onBlur()
  }

  return (
    <FormField
      name={name}
      label={label}
      required={required}
      error={fieldProps.error}
      helpText={helpText}
      className={className}
    >
      <input
        {...inputProps}
        value={fieldProps.value}
        onChange={handleChange}
        onBlur={handleBlur}
        className={cn(
          'block w-full border border-gray-300 rounded-md px-3 py-2 text-sm',
          'placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent',
          'disabled:bg-gray-50 disabled:text-gray-500 disabled:cursor-not-allowed',
          'transition-colors duration-200',
          fieldProps.error && 'border-red-500 focus:ring-red-500',
          inputClassName
        )}
      />
    </FormField>
  )
})

ConnectedFormInput.displayName = 'ConnectedFormInput'

// Connected Form Textarea Component
export interface ConnectedFormTextareaProps {
  name: string
  label?: string
  placeholder?: string
  helpText?: string
  required?: boolean
  disabled?: boolean
  rows?: number
  className?: string
  textareaClassName?: string
}

const ConnectedFormTextarea = React.memo<ConnectedFormTextareaProps>(({
  name,
  label,
  required,
  helpText,
  rows = 3,
  className,
  textareaClassName,
  ...textareaProps
}) => {
  const { formProps } = useFormContext()
  const fieldProps = formProps.getFieldProps(name)

  const handleChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    fieldProps.onChange(e.target.value)
  }

  const handleBlur = () => {
    fieldProps.onBlur()
  }

  return (
    <FormField
      name={name}
      label={label}
      required={required}
      error={fieldProps.error}
      helpText={helpText}
      className={className}
    >
      <textarea
        {...textareaProps}
        rows={rows}
        value={fieldProps.value}
        onChange={handleChange}
        onBlur={handleBlur}
        className={cn(
          'block w-full border border-gray-300 rounded-md px-3 py-2 text-sm',
          'placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent',
          'disabled:bg-gray-50 disabled:text-gray-500 disabled:cursor-not-allowed',
          'transition-colors duration-200 resize-vertical',
          fieldProps.error && 'border-red-500 focus:ring-red-500',
          textareaClassName
        )}
      />
    </FormField>
  )
})

ConnectedFormTextarea.displayName = 'ConnectedFormTextarea'

// Compound component exports
const FormCompound = Object.assign(Form, {
  Group: FormGroup,
  Field: FormField,
  Error: FormError,
  Submit: FormSubmit,
  Input: ConnectedFormInput,
  Textarea: ConnectedFormTextarea,
})

export default FormCompound
export { FormGroup, FormField, FormError, FormSubmit, ConnectedFormInput, ConnectedFormTextarea }