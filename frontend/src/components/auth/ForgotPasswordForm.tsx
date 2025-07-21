import React from 'react'
import { Mail, ArrowLeft, CheckCircle } from 'lucide-react'
import { cn } from '../../lib/utils'

export interface ForgotPasswordFormProps {
  onSubmit: (email: string) => Promise<void> | void
  onBackToLogin?: () => void
  loading?: boolean
  success?: boolean
  error?: string | null
  className?: string
}

const ForgotPasswordForm = React.memo<ForgotPasswordFormProps>(({
  onSubmit,
  onBackToLogin,
  loading = false,
  success = false,
  error = null,
  className,
}) => {
  const [email, setEmail] = React.useState('')
  const [validationError, setValidationError] = React.useState<string>('')

  const validateEmail = React.useCallback((emailValue: string): string | null => {
    if (!emailValue) return 'Email is required'
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(emailValue)) {
      return 'Please enter a valid email address'
    }
    return null
  }, [])

  const handleInputChange = React.useCallback((value: string) => {
    setEmail(value)
    
    // Clear validation error when user starts typing
    if (validationError) {
      setValidationError('')
    }
  }, [validationError])

  const handleBlur = React.useCallback(() => {
    const error = validateEmail(email)
    if (error) {
      setValidationError(error)
    }
  }, [email, validateEmail])

  const handleSubmit = React.useCallback(async (e: React.FormEvent) => {
    e.preventDefault()
    
    const error = validateEmail(email)
    if (error) {
      setValidationError(error)
      return
    }
    
    try {
      await onSubmit(email)
    } catch (err) {
      console.error('Forgot password error:', err)
    }
  }, [email, validateEmail, onSubmit])

  const handleKeyPress = React.useCallback((e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleSubmit(e as any)
    }
  }, [handleSubmit])

  // Success state
  if (success) {
    return (
      <div className={cn('text-center space-y-6', className)}>
        <div className="flex justify-center">
          <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center">
            <CheckCircle className="w-8 h-8 text-green-600" />
          </div>
        </div>
        
        <div className="space-y-2">
          <h3 className="text-lg font-medium text-gray-900">
            Check your email
          </h3>
          <p className="text-sm text-gray-600">
            We've sent password reset instructions to {email}
          </p>
        </div>
        
        <div className="text-sm text-gray-500">
          <p>Didn't receive the email? Check your spam folder or try again in a few minutes.</p>
        </div>
        
        {onBackToLogin && (
          <button
            type="button"
            onClick={onBackToLogin}
            className="inline-flex items-center text-sm text-blue-600 hover:text-blue-500 focus:outline-none focus:underline"
          >
            <ArrowLeft className="w-4 h-4 mr-1" />
            Back to login
          </button>
        )}
      </div>
    )
  }

  // Form state
  return (
    <div className={cn('space-y-6', className)}>
      <div className="text-center space-y-2">
        <h3 className="text-lg font-medium text-gray-900">
          Forgot your password?
        </h3>
        <p className="text-sm text-gray-600">
          Enter your email address and we'll send you instructions to reset your password.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4" noValidate>
        {/* Error Display */}
        {error && (
          <div className="p-3 bg-red-50 border border-red-200 rounded-md">
            <p className="text-red-700 text-sm">{error}</p>
          </div>
        )}

        {/* Email Field */}
        <div className="space-y-1">
          <label
            htmlFor="forgot-email"
            className="block text-sm font-medium text-gray-700"
          >
            Email Address
          </label>
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <Mail className="h-5 w-5 text-gray-400" />
            </div>
            <input
              id="forgot-email"
              name="email"
              type="email"
              autoComplete="email"
              required
              value={email}
              onChange={(e) => handleInputChange(e.target.value)}
              onBlur={handleBlur}
              onKeyPress={handleKeyPress}
              className={cn(
                'block w-full pl-10 pr-3 py-2 border rounded-md',
                'focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'placeholder-gray-400 text-gray-900',
                validationError || error
                  ? 'border-red-300 bg-red-50'
                  : 'border-gray-300'
              )}
              placeholder="Enter your email address"
              disabled={loading}
            />
          </div>
          {validationError && (
            <p className="text-red-600 text-xs mt-1">{validationError}</p>
          )}
        </div>

        {/* Submit Button */}
        <button
          type="submit"
          disabled={loading || !!validationError || !email}
          className={cn(
            'w-full flex justify-center items-center py-2 px-4 border border-transparent',
            'text-sm font-medium rounded-md text-white',
            'focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500',
            loading || !!validationError || !email
              ? 'bg-gray-400 cursor-not-allowed'
              : 'bg-blue-600 hover:bg-blue-700'
          )}
        >
          {loading ? (
            <>
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2" />
              Sending instructions...
            </>
          ) : (
            'Send reset instructions'
          )}
        </button>
      </form>

      {/* Back to Login */}
      {onBackToLogin && (
        <div className="text-center">
          <button
            type="button"
            onClick={onBackToLogin}
            className="inline-flex items-center text-sm text-blue-600 hover:text-blue-500 focus:outline-none focus:underline"
            disabled={loading}
          >
            <ArrowLeft className="w-4 h-4 mr-1" />
            Back to login
          </button>
        </div>
      )}
    </div>
  )
})

ForgotPasswordForm.displayName = 'ForgotPasswordForm'

export default ForgotPasswordForm