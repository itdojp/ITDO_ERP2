import React from 'react'

export type ValidationRule<T = any> = {
  validator: (value: T, formData?: Record<string, any>) => boolean | Promise<boolean>
  message: string
  when?: (formData: Record<string, any>) => boolean
}

export type FieldValidation<T = any> = {
  required?: boolean | string
  rules?: ValidationRule<T>[]
  debounceMs?: number
  validateOnChange?: boolean
  validateOnBlur?: boolean
}

export type FormValidationConfig = {
  [fieldName: string]: FieldValidation
}

export type ValidationError = {
  field: string
  message: string
  rule?: string
}

export type FormValidationState = {
  values: Record<string, any>
  errors: Record<string, string | null>
  touched: Record<string, boolean>
  isSubmitting: boolean
  isValid: boolean
  isDirty: boolean
}

export interface FormValidationOptions {
  initialValues?: Record<string, any>
  validationConfig: FormValidationConfig
  onSubmit?: (values: Record<string, any>) => void | Promise<void>
  validateOnMount?: boolean
}

const useFormValidation = (options: FormValidationOptions) => {
  const {
    initialValues = {},
    validationConfig,
    onSubmit,
    validateOnMount = false,
  } = options

  const [state, setState] = React.useState<FormValidationState>({
    values: initialValues,
    errors: {},
    touched: {},
    isSubmitting: false,
    isValid: false,
    isDirty: false,
  })

  const validationTimeouts = React.useRef<Record<string, NodeJS.Timeout>>({})

  const validateField = React.useCallback(
    async (fieldName: string, value: any, allValues?: Record<string, any>): Promise<string | null> => {
      const config = validationConfig[fieldName]
      if (!config) return null

      const currentValues = allValues || state.values

      // Check conditional validation
      if (config.rules) {
        for (const rule of config.rules) {
          if (rule.when && !rule.when(currentValues)) {
            continue
          }

          try {
            const isValid = await rule.validator(value, currentValues)
            if (!isValid) {
              return rule.message
            }
          } catch (error) {
            return rule.message
          }
        }
      }

      // Required validation
      if (config.required) {
        const isEmpty = value === null || 
                       value === undefined || 
                       value === '' || 
                       (Array.isArray(value) && value.length === 0)

        if (isEmpty) {
          return typeof config.required === 'string' 
            ? config.required 
            : `${fieldName} is required`
        }
      }

      return null
    },
    [validationConfig, state.values]
  )

  const validateForm = React.useCallback(async (): Promise<Record<string, string | null>> => {
    const errors: Record<string, string | null> = {}
    
    for (const fieldName of Object.keys(validationConfig)) {
      const value = state.values[fieldName]
      const error = await validateField(fieldName, value, state.values)
      errors[fieldName] = error
    }

    return errors
  }, [validationConfig, state.values, validateField])

  const validateFieldWithDebounce = React.useCallback(
    (fieldName: string, value: any) => {
      const config = validationConfig[fieldName]
      const debounceMs = config?.debounceMs || 300

      // Clear existing timeout
      if (validationTimeouts.current[fieldName]) {
        clearTimeout(validationTimeouts.current[fieldName])
      }

      // Set new timeout
      validationTimeouts.current[fieldName] = setTimeout(async () => {
        const error = await validateField(fieldName, value)
        setState(prev => ({
          ...prev,
          errors: {
            ...prev.errors,
            [fieldName]: error,
          },
        }))
      }, debounceMs)
    },
    [validationConfig, validateField]
  )

  const setValue = React.useCallback(
    (fieldName: string, value: any) => {
      setState(prev => {
        const newValues = { ...prev.values, [fieldName]: value }
        return {
          ...prev,
          values: newValues,
          isDirty: true,
        }
      })

      const config = validationConfig[fieldName]
      if (config?.validateOnChange) {
        validateFieldWithDebounce(fieldName, value)
      }
    },
    [validationConfig, validateFieldWithDebounce]
  )

  const setFieldTouched = React.useCallback(
    async (fieldName: string, touched = true) => {
      setState(prev => ({
        ...prev,
        touched: {
          ...prev.touched,
          [fieldName]: touched,
        },
      }))

      const config = validationConfig[fieldName]
      if (touched && config?.validateOnBlur) {
        const value = state.values[fieldName]
        const error = await validateField(fieldName, value)
        setState(prev => ({
          ...prev,
          errors: {
            ...prev.errors,
            [fieldName]: error,
          },
        }))
      }
    },
    [validationConfig, state.values, validateField]
  )

  const setValues = React.useCallback((values: Record<string, any>) => {
    setState(prev => ({
      ...prev,
      values: { ...prev.values, ...values },
      isDirty: true,
    }))
  }, [])

  const setErrors = React.useCallback((errors: Record<string, string | null>) => {
    setState(prev => ({
      ...prev,
      errors: { ...prev.errors, ...errors },
    }))
  }, [])

  const resetForm = React.useCallback(() => {
    setState({
      values: initialValues,
      errors: {},
      touched: {},
      isSubmitting: false,
      isValid: false,
      isDirty: false,
    })

    // Clear all validation timeouts
    Object.values(validationTimeouts.current).forEach(timeout => {
      clearTimeout(timeout)
    })
    validationTimeouts.current = {}
  }, [initialValues])

  const handleSubmit = React.useCallback(
    async (e?: React.FormEvent) => {
      if (e) {
        e.preventDefault()
      }

      setState(prev => ({ ...prev, isSubmitting: true }))

      try {
        const errors = await validateForm()
        const hasErrors = Object.values(errors).some(error => error !== null)

        setState(prev => ({
          ...prev,
          errors,
          isValid: !hasErrors,
          touched: Object.keys(validationConfig).reduce((acc, key) => {
            acc[key] = true
            return acc
          }, {} as Record<string, boolean>),
        }))

        if (!hasErrors && onSubmit) {
          await onSubmit(state.values)
        }

        return !hasErrors
      } catch (error) {
        console.error('Form submission error:', error)
        return false
      } finally {
        setState(prev => ({ ...prev, isSubmitting: false }))
      }
    },
    [validateForm, validationConfig, onSubmit, state.values]
  )

  const getFieldProps = React.useCallback(
    (fieldName: string) => ({
      value: state.values[fieldName] || '',
      error: state.touched[fieldName] ? state.errors[fieldName] : null,
      onChange: (value: any) => setValue(fieldName, value),
      onBlur: () => setFieldTouched(fieldName, true),
    }),
    [state.values, state.errors, state.touched, setValue, setFieldTouched]
  )

  // Calculate isValid based on current errors
  React.useEffect(() => {
    const hasErrors = Object.values(state.errors).some(error => error !== null)
    setState(prev => ({
      ...prev,
      isValid: !hasErrors && Object.keys(prev.values).length > 0,
    }))
  }, [state.errors])

  // Validate on mount if requested
  React.useEffect(() => {
    if (validateOnMount) {
      validateForm().then(errors => {
        setState(prev => ({
          ...prev,
          errors,
        }))
      })
    }
  }, [validateOnMount, validateForm])

  // Cleanup timeouts on unmount
  React.useEffect(() => {
    return () => {
      Object.values(validationTimeouts.current).forEach(timeout => {
        clearTimeout(timeout)
      })
    }
  }, [])

  return {
    values: state.values,
    errors: state.errors,
    touched: state.touched,
    isSubmitting: state.isSubmitting,
    isValid: state.isValid,
    isDirty: state.isDirty,
    setValue,
    setValues,
    setErrors,
    setFieldTouched,
    resetForm,
    handleSubmit,
    validateField,
    validateForm,
    getFieldProps,
  }
}

// Common validation rules
export const ValidationRules = {
  required: (message = 'This field is required'): ValidationRule => ({
    validator: (value) => {
      return value !== null && value !== undefined && value !== '' && 
             (!Array.isArray(value) || value.length > 0)
    },
    message,
  }),

  minLength: (min: number, message?: string): ValidationRule<string> => ({
    validator: (value) => !value || value.length >= min,
    message: message || `Must be at least ${min} characters`,
  }),

  maxLength: (max: number, message?: string): ValidationRule<string> => ({
    validator: (value) => !value || value.length <= max,
    message: message || `Must be no more than ${max} characters`,
  }),

  email: (message = 'Please enter a valid email address'): ValidationRule<string> => ({
    validator: (value) => {
      if (!value) return true
      const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
      return emailRegex.test(value)
    },
    message,
  }),

  pattern: (regex: RegExp, message = 'Invalid format'): ValidationRule<string> => ({
    validator: (value) => !value || regex.test(value),
    message,
  }),

  min: (min: number, message?: string): ValidationRule<number> => ({
    validator: (value) => typeof value !== 'number' || value >= min,
    message: message || `Must be at least ${min}`,
  }),

  max: (max: number, message?: string): ValidationRule<number> => ({
    validator: (value) => typeof value !== 'number' || value <= max,
    message: message || `Must be no more than ${max}`,
  }),

  matches: (fieldName: string, message = 'Fields must match'): ValidationRule => ({
    validator: (value, formData) => {
      return !formData || value === formData[fieldName]
    },
    message,
  }),

  custom: (validator: (value: any, formData?: Record<string, any>) => boolean | Promise<boolean>, message: string): ValidationRule => ({
    validator,
    message,
  }),

  async: (asyncValidator: (value: any, formData?: Record<string, any>) => Promise<boolean>, message: string): ValidationRule => ({
    validator: asyncValidator,
    message,
  }),
}

export default useFormValidation