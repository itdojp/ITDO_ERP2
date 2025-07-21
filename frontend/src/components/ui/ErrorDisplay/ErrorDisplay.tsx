import React from 'react'
import { AlertTriangle, X, RefreshCw, ExternalLink, ChevronDown, ChevronRight } from 'lucide-react'
import { cn } from '../../../lib/utils'
import { ErrorDetails, ErrorType, getUserFriendlyMessage } from '../../../hooks/useErrorHandler'

export interface ErrorDisplayProps {
  error?: any
  errorDetails?: ErrorDetails
  title?: string
  description?: string
  variant?: 'inline' | 'banner' | 'modal' | 'toast'
  severity?: 'low' | 'medium' | 'high' | 'critical'
  showDetails?: boolean
  showRetry?: boolean
  showDismiss?: boolean
  onRetry?: () => void
  onDismiss?: () => void
  className?: string
  actions?: React.ReactNode
}

const ErrorDisplay: React.FC<ErrorDisplayProps> = ({
  error,
  errorDetails,
  title,
  description,
  variant = 'inline',
  severity = 'medium',
  showDetails = false,
  showRetry = false,
  showDismiss = true,
  onRetry,
  onDismiss,
  className,
  actions,
}) => {
  const [isDetailsExpanded, setIsDetailsExpanded] = React.useState(false)

  // Determine error type and message
  const errorType: ErrorType = errorDetails?.type || 'unknown'
  const errorMessage = description || 
    (errorDetails ? getUserFriendlyMessage(error || errorDetails, errorType) : 
     error?.message || 
     'An unexpected error occurred')

  // Get severity-based styles
  const severityStyles = {
    low: {
      bg: 'bg-blue-50',
      border: 'border-blue-200',
      text: 'text-blue-800',
      icon: 'text-blue-500',
    },
    medium: {
      bg: 'bg-yellow-50',
      border: 'border-yellow-200',
      text: 'text-yellow-800',
      icon: 'text-yellow-500',
    },
    high: {
      bg: 'bg-orange-50',
      border: 'border-orange-200',
      text: 'text-orange-800',
      icon: 'text-orange-500',
    },
    critical: {
      bg: 'bg-red-50',
      border: 'border-red-200',
      text: 'text-red-800',
      icon: 'text-red-500',
    },
  }

  const styles = severityStyles[severity]

  // Variant-specific classes
  const variantClasses = {
    inline: 'rounded-lg p-4',
    banner: 'rounded-none px-4 py-3 border-l-4 border-r-0 border-t-0 border-b-0',
    modal: 'rounded-lg p-6',
    toast: 'rounded-lg p-4 shadow-lg',
  }

  const baseClasses = cn(
    'border',
    styles.bg,
    styles.border,
    variantClasses[variant],
    className
  )

  const renderErrorDetails = () => {
    if (!showDetails || !errorDetails) return null

    return (
      <div className="mt-4">
        <button
          type="button"
          onClick={() => setIsDetailsExpanded(!isDetailsExpanded)}
          className={cn(
            'flex items-center text-sm font-medium',
            styles.text,
            'hover:opacity-80 focus:outline-none'
          )}
        >
          {isDetailsExpanded ? (
            <ChevronDown className="h-4 w-4 mr-1" />
          ) : (
            <ChevronRight className="h-4 w-4 mr-1" />
          )}
          Error Details
        </button>

        {isDetailsExpanded && (
          <div className="mt-3 p-3 bg-white bg-opacity-50 rounded-md text-xs space-y-2">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <span className="font-semibold">Error ID:</span>
                <div className="font-mono break-all">{errorDetails.id}</div>
              </div>
              <div>
                <span className="font-semibold">Type:</span>
                <div className="font-mono">{errorDetails.type}</div>
              </div>
              <div>
                <span className="font-semibold">Status:</span>
                <div className="font-mono">{errorDetails.status || 'N/A'}</div>
              </div>
              <div>
                <span className="font-semibold">Code:</span>
                <div className="font-mono">{errorDetails.code || 'N/A'}</div>
              </div>
              <div className="col-span-2">
                <span className="font-semibold">Timestamp:</span>
                <div className="font-mono">{errorDetails.timestamp.toLocaleString()}</div>
              </div>
              {errorDetails.context && (
                <div className="col-span-2">
                  <span className="font-semibold">Context:</span>
                  <div className="font-mono">{errorDetails.context}</div>
                </div>
              )}
            </div>

            {error?.stack && (
              <div>
                <span className="font-semibold">Stack Trace:</span>
                <pre className="mt-1 p-2 bg-gray-100 rounded text-xs overflow-auto max-h-32 font-mono text-gray-700">
                  {error.stack}
                </pre>
              </div>
            )}

            {errorDetails.details && (
              <div>
                <span className="font-semibold">Additional Details:</span>
                <pre className="mt-1 p-2 bg-gray-100 rounded text-xs overflow-auto max-h-32 font-mono text-gray-700">
                  {JSON.stringify(errorDetails.details, null, 2)}
                </pre>
              </div>
            )}
          </div>
        )}
      </div>
    )
  }

  return (
    <div className={baseClasses} role="alert">
      <div className="flex">
        <div className="flex-shrink-0">
          <AlertTriangle className={cn('h-5 w-5', styles.icon)} />
        </div>
        
        <div className="ml-3 flex-1">
          <div className="flex items-start justify-between">
            <div className="flex-1">
              {title && (
                <h3 className={cn('text-sm font-medium', styles.text)}>
                  {title}
                </h3>
              )}
              
              <div className={cn('text-sm', title ? 'mt-1' : '', styles.text)}>
                {errorMessage}
              </div>

              {renderErrorDetails()}
            </div>

            <div className="ml-4 flex items-center space-x-2">
              {actions}
              
              {showRetry && onRetry && (
                <button
                  type="button"
                  onClick={onRetry}
                  className={cn(
                    'inline-flex items-center px-2 py-1 text-xs font-medium rounded',
                    'bg-white bg-opacity-80 hover:bg-opacity-100',
                    'focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500',
                    styles.text
                  )}
                >
                  <RefreshCw className="h-3 w-3 mr-1" />
                  Retry
                </button>
              )}

              {showDismiss && onDismiss && (
                <button
                  type="button"
                  onClick={onDismiss}
                  className={cn(
                    'inline-flex rounded-md p-1.5',
                    'hover:bg-white hover:bg-opacity-50',
                    'focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500',
                    styles.text
                  )}
                >
                  <span className="sr-only">Dismiss</span>
                  <X className="h-4 w-4" />
                </button>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

// Specialized error display components
export const NetworkErrorDisplay: React.FC<Omit<ErrorDisplayProps, 'errorType'>> = (props) => (
  <ErrorDisplay
    {...props}
    title="Connection Problem"
    severity="high"
    showRetry={true}
  />
)

export const ValidationErrorDisplay: React.FC<Omit<ErrorDisplayProps, 'errorType'>> = (props) => (
  <ErrorDisplay
    {...props}
    title="Invalid Input"
    severity="medium"
    variant="inline"
  />
)

export const AuthErrorDisplay: React.FC<Omit<ErrorDisplayProps, 'errorType'>> = (props) => (
  <ErrorDisplay
    {...props}
    title="Authentication Required"
    severity="high"
    actions={
      <a
        href="/login"
        className="inline-flex items-center text-sm text-blue-600 hover:text-blue-800"
      >
        <ExternalLink className="h-3 w-3 mr-1" />
        Login
      </a>
    }
  />
)

export const ServerErrorDisplay: React.FC<Omit<ErrorDisplayProps, 'errorType'>> = (props) => (
  <ErrorDisplay
    {...props}
    title="Server Error"
    severity="critical"
    showRetry={true}
    showDetails={true}
  />
)

// Error list component for displaying multiple errors
export interface ErrorListProps {
  errors: ErrorDetails[]
  maxVisible?: number
  onClearError?: (errorId: string) => void
  onClearAll?: () => void
  className?: string
}

export const ErrorList: React.FC<ErrorListProps> = ({
  errors,
  maxVisible = 5,
  onClearError,
  onClearAll,
  className,
}) => {
  const [isExpanded, setIsExpanded] = React.useState(false)
  const visibleErrors = isExpanded ? errors : errors.slice(0, maxVisible)
  const hasMoreErrors = errors.length > maxVisible

  if (errors.length === 0) {
    return null
  }

  return (
    <div className={cn('space-y-3', className)}>
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-medium text-gray-900">
          Recent Errors ({errors.length})
        </h3>
        {errors.length > 1 && onClearAll && (
          <button
            type="button"
            onClick={onClearAll}
            className="text-xs text-gray-500 hover:text-gray-700"
          >
            Clear All
          </button>
        )}
      </div>

      <div className="space-y-2">
        {visibleErrors.map((errorDetails) => (
          <ErrorDisplay
            key={errorDetails.id}
            errorDetails={errorDetails}
            variant="inline"
            showDismiss={!!onClearError}
            onDismiss={onClearError ? () => onClearError(errorDetails.id) : undefined}
          />
        ))}
      </div>

      {hasMoreErrors && (
        <button
          type="button"
          onClick={() => setIsExpanded(!isExpanded)}
          className="w-full text-center text-xs text-gray-500 hover:text-gray-700 py-2"
        >
          {isExpanded ? 'Show Less' : `Show ${errors.length - maxVisible} More`}
        </button>
      )}
    </div>
  )
}

export default ErrorDisplay