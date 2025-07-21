import React from 'react'
import { AlertTriangle, RefreshCw, Home, Bug } from 'lucide-react'
import { cn } from '../lib/utils'

export interface ErrorInfo {
  componentStack: string
  errorBoundary?: string
  errorBoundaryStack?: string
}

export interface ErrorBoundaryState {
  hasError: boolean
  error: Error | null
  errorInfo: ErrorInfo | null
  errorId?: string
}

export interface ErrorBoundaryProps {
  children: React.ReactNode
  fallback?: React.ComponentType<ErrorFallbackProps>
  onError?: (error: Error, errorInfo: ErrorInfo) => void
  level?: 'page' | 'section' | 'component'
  resetKeys?: Array<string | number>
  resetOnPropsChange?: boolean
  showErrorDetails?: boolean
  className?: string
}

export interface ErrorFallbackProps {
  error: Error
  errorInfo: ErrorInfo | null
  resetError: () => void
  level: NonNullable<ErrorBoundaryProps['level']>
  showErrorDetails: boolean
}

// Error logging service
const logError = (error: Error, errorInfo: ErrorInfo, errorId: string) => {
  // In production, this would send to logging service (Sentry, LogRocket, etc.)
  if (process.env.NODE_ENV === 'development') {
    console.group(`🐛 Error Boundary: ${errorId}`)
    console.error('Error:', error)
    console.error('Error Info:', errorInfo)
    console.groupEnd()
  } else {
    // Production logging would go here
    // Example: Sentry.captureException(error, { extra: errorInfo, tags: { errorId } })
  }
}

// Generate unique error ID
const generateErrorId = (): string => {
  return `err_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
}

// Default Error Fallback Component
const DefaultErrorFallback: React.FC<ErrorFallbackProps> = ({
  error,
  errorInfo,
  resetError,
  level,
  showErrorDetails,
}) => {
  const [showDetails, setShowDetails] = React.useState(false)

  const levelConfig = {
    page: {
      icon: <AlertTriangle className="h-16 w-16 text-red-500 mx-auto mb-4" />,
      title: 'Oops! Something went wrong',
      description: 'We encountered an unexpected error. Please try refreshing the page.',
      containerClass: 'min-h-screen flex items-center justify-center p-4',
      contentClass: 'max-w-md w-full text-center',
      showHomeButton: true,
    },
    section: {
      icon: <AlertTriangle className="h-12 w-12 text-red-500 mx-auto mb-3" />,
      title: 'Section Error',
      description: 'This section encountered an error. Please try again.',
      containerClass: 'p-8 flex items-center justify-center min-h-48',
      contentClass: 'max-w-sm w-full text-center',
      showHomeButton: false,
    },
    component: {
      icon: <AlertTriangle className="h-8 w-8 text-red-500 mx-auto mb-2" />,
      title: 'Component Error',
      description: 'This component failed to load.',
      containerClass: 'p-4 flex items-center justify-center min-h-24',
      contentClass: 'max-w-xs w-full text-center text-sm',
      showHomeButton: false,
    },
  }

  const config = levelConfig[level]

  const handleReload = () => {
    window.location.reload()
  }

  const handleGoHome = () => {
    window.location.href = '/'
  }

  return (
    <div className={cn(
      'bg-gray-50 border border-gray-200 rounded-lg',
      config.containerClass
    )}>
      <div className={config.contentClass}>
        {config.icon}
        
        <h2 className="text-lg font-semibold text-gray-900 mb-2">
          {config.title}
        </h2>
        
        <p className="text-gray-600 mb-6">
          {config.description}
        </p>

        <div className="space-y-3">
          <div className="flex gap-3 justify-center">
            <button
              onClick={resetError}
              className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 transition-colors"
            >
              <RefreshCw className="h-4 w-4 mr-2" />
              Try Again
            </button>
            
            {level === 'page' && (
              <button
                onClick={handleReload}
                className="inline-flex items-center px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2 transition-colors"
              >
                <RefreshCw className="h-4 w-4 mr-2" />
                Reload Page
              </button>
            )}
          </div>

          {config.showHomeButton && (
            <button
              onClick={handleGoHome}
              className="inline-flex items-center px-4 py-2 text-gray-600 hover:text-gray-800 transition-colors"
            >
              <Home className="h-4 w-4 mr-2" />
              Go to Home
            </button>
          )}
        </div>

        {showErrorDetails && (
          <div className="mt-6">
            <button
              onClick={() => setShowDetails(!showDetails)}
              className="inline-flex items-center text-sm text-gray-500 hover:text-gray-700 transition-colors"
            >
              <Bug className="h-4 w-4 mr-1" />
              {showDetails ? 'Hide' : 'Show'} Error Details
            </button>
            
            {showDetails && (
              <div className="mt-3 p-4 bg-gray-100 rounded-md text-left">
                <div className="text-xs text-gray-700 space-y-2">
                  <div>
                    <strong>Error:</strong>
                    <div className="font-mono text-red-600 break-all">
                      {error.message}
                    </div>
                  </div>
                  
                  {error.stack && (
                    <div>
                      <strong>Stack Trace:</strong>
                      <pre className="font-mono text-xs text-gray-600 overflow-auto max-h-32 whitespace-pre-wrap break-all">
                        {error.stack}
                      </pre>
                    </div>
                  )}

                  {errorInfo && (
                    <div>
                      <strong>Component Stack:</strong>
                      <pre className="font-mono text-xs text-gray-600 overflow-auto max-h-32 whitespace-pre-wrap">
                        {errorInfo.componentStack}
                      </pre>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

// Main Error Boundary Class Component
class ErrorBoundary extends React.Component<ErrorBoundaryProps, ErrorBoundaryState> {
  private resetTimeoutId: number | null = null

  constructor(props: ErrorBoundaryProps) {
    super(props)
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
    }
  }

  static getDerivedStateFromError(error: Error): Partial<ErrorBoundaryState> {
    return {
      hasError: true,
      error,
      errorId: generateErrorId(),
    }
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    const enhancedErrorInfo: ErrorInfo = {
      componentStack: errorInfo.componentStack,
      errorBoundary: this.constructor.name,
      errorBoundaryStack: errorInfo.errorBoundaryStack || '',
    }

    this.setState({
      errorInfo: enhancedErrorInfo,
    })

    const errorId = this.state.errorId || generateErrorId()
    
    // Log error
    logError(error, enhancedErrorInfo, errorId)
    
    // Call optional error handler
    if (this.props.onError) {
      try {
        this.props.onError(error, enhancedErrorInfo)
      } catch (handlerError) {
        console.error('Error in onError handler:', handlerError)
      }
    }
  }

  componentDidUpdate(prevProps: ErrorBoundaryProps) {
    const { resetKeys, resetOnPropsChange } = this.props
    const { hasError } = this.state

    // Reset error state if resetKeys have changed
    if (hasError && resetKeys && prevProps.resetKeys !== resetKeys) {
      const prevKeysString = prevProps.resetKeys?.join(',') || ''
      const currentKeysString = resetKeys.join(',')
      
      if (prevKeysString !== currentKeysString) {
        this.resetErrorBoundary()
      }
    }

    // Reset error state if any props have changed and resetOnPropsChange is true
    if (hasError && resetOnPropsChange && prevProps.children !== this.props.children) {
      this.resetErrorBoundary()
    }
  }

  componentWillUnmount() {
    if (this.resetTimeoutId) {
      clearTimeout(this.resetTimeoutId)
    }
  }

  resetErrorBoundary = () => {
    if (this.resetTimeoutId) {
      clearTimeout(this.resetTimeoutId)
    }

    this.resetTimeoutId = window.setTimeout(() => {
      this.setState({
        hasError: false,
        error: null,
        errorInfo: null,
        errorId: undefined,
      })
    }, 0)
  }

  render() {
    const { 
      children, 
      fallback: FallbackComponent, 
      level = 'component',
      showErrorDetails = process.env.NODE_ENV === 'development',
      className 
    } = this.props
    
    const { hasError, error, errorInfo } = this.state

    if (hasError && error) {
      const FallbackToRender = FallbackComponent || DefaultErrorFallback
      
      return (
        <div className={className}>
          <FallbackToRender
            error={error}
            errorInfo={errorInfo}
            resetError={this.resetErrorBoundary}
            level={level}
            showErrorDetails={showErrorDetails}
          />
        </div>
      )
    }

    return children
  }
}

// Hook for functional component error handling
export const useErrorHandler = () => {
  const [error, setError] = React.useState<Error | null>(null)

  const resetError = React.useCallback(() => {
    setError(null)
  }, [])

  const captureError = React.useCallback((error: Error | string, errorInfo?: any) => {
    const errorObj = typeof error === 'string' ? new Error(error) : error
    
    // Log error
    const errorId = generateErrorId()
    logError(errorObj, { componentStack: errorInfo || '' }, errorId)
    
    setError(errorObj)
  }, [])

  React.useEffect(() => {
    if (error) {
      throw error
    }
  }, [error])

  return {
    captureError,
    resetError,
    hasError: !!error,
    error,
  }
}

// HOC for adding error boundary to components
export const withErrorBoundary = <P extends object>(
  Component: React.ComponentType<P>,
  errorBoundaryConfig?: Omit<ErrorBoundaryProps, 'children'>
) => {
  const WrappedComponent = React.forwardRef<any, P>((props, ref) => (
    <ErrorBoundary {...errorBoundaryConfig}>
      <Component {...props} ref={ref} />
    </ErrorBoundary>
  ))

  WrappedComponent.displayName = `withErrorBoundary(${Component.displayName || Component.name})`
  
  return WrappedComponent
}

export default ErrorBoundary