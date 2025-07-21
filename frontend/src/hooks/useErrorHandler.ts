import React from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { QueryError } from '../lib/queryClient'

// Error types
export type ErrorType = 'network' | 'validation' | 'authentication' | 'authorization' | 'server' | 'client' | 'unknown'

export interface ErrorDetails {
  id: string
  type: ErrorType
  message: string
  status?: number
  code?: string
  details?: any
  timestamp: Date
  context?: string
  userId?: string
  url?: string
  userAgent?: string
}

export interface ErrorHandlerOptions {
  enableAutoRetry?: boolean
  maxRetries?: number
  retryDelay?: number
  showNotification?: boolean
  logError?: boolean
  context?: string
}

// Error classification
export const classifyError = (error: any): ErrorType => {
  if (!error) return 'unknown'

  // Network errors
  if (error.message?.includes('Network') || error.name === 'NetworkError') {
    return 'network'
  }

  // Status code based classification
  if (error.status || error.response?.status) {
    const status = error.status || error.response?.status

    if (status === 401) return 'authentication'
    if (status === 403) return 'authorization'
    if (status >= 400 && status < 500) return 'validation'
    if (status >= 500) return 'server'
  }

  // Error code based classification
  if (error.code) {
    const code = error.code.toLowerCase()
    
    if (code.includes('network') || code.includes('timeout')) return 'network'
    if (code.includes('auth') || code.includes('token')) return 'authentication'
    if (code.includes('permission') || code.includes('forbidden')) return 'authorization'
    if (code.includes('validation') || code.includes('invalid')) return 'validation'
  }

  return 'client'
}

// Generate error ID
const generateErrorId = (): string => {
  return `err_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
}

// Error reporter - in production, this would send to external service
const reportError = (errorDetails: ErrorDetails) => {
  if (process.env.NODE_ENV === 'development') {
    console.group(`🚨 Error Report: ${errorDetails.id}`)
    console.error('Type:', errorDetails.type)
    console.error('Message:', errorDetails.message)
    console.error('Status:', errorDetails.status)
    console.error('Code:', errorDetails.code)
    console.error('Details:', errorDetails.details)
    console.error('Context:', errorDetails.context)
    console.error('Timestamp:', errorDetails.timestamp)
    console.groupEnd()
  } else {
    // In production, send to logging service
    // Example: Sentry, LogRocket, etc.
    // sentryReportError(errorDetails)
  }
}

// Get user-friendly error message
export const getUserFriendlyMessage = (error: any, type: ErrorType): string => {
  // Custom error messages based on type
  const messages = {
    network: 'Network connection error. Please check your internet connection and try again.',
    authentication: 'Authentication required. Please log in and try again.',
    authorization: 'You do not have permission to perform this action.',
    validation: 'Invalid data provided. Please check your input and try again.',
    server: 'Server error occurred. Please try again later.',
    client: 'An error occurred. Please try again.',
    unknown: 'An unexpected error occurred. Please try again.',
  }

  // Use specific error message if available and user-friendly
  if (error?.message && error.message.length < 100 && !error.message.includes('stack')) {
    return error.message
  }

  return messages[type]
}

// Main error handler hook
export const useErrorHandler = (defaultOptions: ErrorHandlerOptions = {}) => {
  const queryClient = useQueryClient()
  const [errors, setErrors] = React.useState<ErrorDetails[]>([])

  const handleError = React.useCallback((
    error: any,
    options: ErrorHandlerOptions = {}
  ) => {
    const config = { ...defaultOptions, ...options }
    const {
      enableAutoRetry = false,
      maxRetries = 3,
      retryDelay = 1000,
      showNotification = true,
      logError = true,
      context = 'Unknown'
    } = config

    // Create error details
    const errorType = classifyError(error)
    const errorDetails: ErrorDetails = {
      id: generateErrorId(),
      type: errorType,
      message: error?.message || 'Unknown error',
      status: error?.status || error?.response?.status,
      code: error?.code || error?.response?.data?.code,
      details: error?.details || error?.response?.data?.details,
      timestamp: new Date(),
      context,
      url: window.location.href,
      userAgent: navigator.userAgent,
    }

    // Add to errors state
    setErrors(prev => [errorDetails, ...prev.slice(0, 9)]) // Keep last 10 errors

    // Log error if enabled
    if (logError) {
      reportError(errorDetails)
    }

    // Show notification if enabled
    if (showNotification) {
      // This would integrate with your notification system
      console.warn(`Error: ${getUserFriendlyMessage(error, errorType)}`)
    }

    // Auto retry logic
    if (enableAutoRetry && errorType === 'network') {
      const retryCount = error._retryCount || 0
      if (retryCount < maxRetries) {
        setTimeout(() => {
          const enhancedError = { ...error, _retryCount: retryCount + 1 }
          // Retry the failed operation (would need to be passed in)
          console.log(`Retrying operation... (${retryCount + 1}/${maxRetries})`)
        }, retryDelay * Math.pow(2, retryCount)) // Exponential backoff
      }
    }

    return errorDetails
  }, [defaultOptions])

  const clearErrors = React.useCallback(() => {
    setErrors([])
  }, [])

  const clearError = React.useCallback((errorId: string) => {
    setErrors(prev => prev.filter(error => error.id !== errorId))
  }, [])

  const retryLastError = React.useCallback(() => {
    // This would need to be implemented based on your specific use case
    console.log('Retry functionality would be implemented here')
  }, [])

  const hasErrors = errors.length > 0
  const latestError = errors[0] || null

  return {
    handleError,
    clearErrors,
    clearError,
    retryLastError,
    errors,
    hasErrors,
    latestError,
    errorCount: errors.length,
  }
}

// Specialized hooks for different error types

// Query error handler
export const useQueryErrorHandler = () => {
  const { handleError, ...rest } = useErrorHandler({
    context: 'Query',
    showNotification: true,
    logError: true,
  })

  const handleQueryError = React.useCallback((error: any, queryKey?: any[]) => {
    const context = queryKey ? `Query: ${queryKey.join('.')}` : 'Query'
    return handleError(error, { context })
  }, [handleError])

  return {
    handleQueryError,
    handleError,
    ...rest,
  }
}

// Mutation error handler
export const useMutationErrorHandler = () => {
  const { handleError, ...rest } = useErrorHandler({
    context: 'Mutation',
    showNotification: true,
    logError: true,
  })

  const handleMutationError = React.useCallback((error: any, mutationKey?: string) => {
    const context = mutationKey ? `Mutation: ${mutationKey}` : 'Mutation'
    return handleError(error, { context })
  }, [handleError])

  return {
    handleMutationError,
    handleError,
    ...rest,
  }
}

// Form error handler
export const useFormErrorHandler = () => {
  const { handleError, ...rest } = useErrorHandler({
    context: 'Form',
    showNotification: false, // Forms usually show errors inline
    logError: true,
  })

  const handleFormError = React.useCallback((error: any, formName?: string) => {
    const context = formName ? `Form: ${formName}` : 'Form'
    return handleError(error, { context, showNotification: false })
  }, [handleError])

  const parseFormErrors = React.useCallback((error: any): Record<string, string> => {
    const fieldErrors: Record<string, string> = {}

    if (error?.details?.fieldErrors) {
      return error.details.fieldErrors
    }

    if (error?.response?.data?.fieldErrors) {
      return error.response.data.fieldErrors
    }

    if (error?.response?.data?.errors && Array.isArray(error.response.data.errors)) {
      error.response.data.errors.forEach((err: any) => {
        if (err.field && err.message) {
          fieldErrors[err.field] = err.message
        }
      })
    }

    return fieldErrors
  }, [])

  return {
    handleFormError,
    parseFormErrors,
    handleError,
    ...rest,
  }
}

// Global error handler for uncaught errors
export const useGlobalErrorHandler = () => {
  const { handleError } = useErrorHandler({
    context: 'Global',
    showNotification: true,
    logError: true,
  })

  React.useEffect(() => {
    const handleUnhandledRejection = (event: PromiseRejectionEvent) => {
      handleError(event.reason, { context: 'Unhandled Promise Rejection' })
    }

    const handleError = (event: ErrorEvent) => {
      handleError(new Error(event.message), { 
        context: 'Global Error',
        details: {
          filename: event.filename,
          line: event.lineno,
          column: event.colno,
        }
      })
    }

    window.addEventListener('unhandledrejection', handleUnhandledRejection)
    window.addEventListener('error', handleError)

    return () => {
      window.removeEventListener('unhandledrejection', handleUnhandledRejection)
      window.removeEventListener('error', handleError)
    }
  }, [handleError])
}

export default useErrorHandler