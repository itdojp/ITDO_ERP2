import React from 'react'
import { Eye, EyeOff, Lock, CheckCircle, AlertTriangle } from 'lucide-react'
import { cn } from '../../lib/utils'

export interface ResetPasswordData {
  password: string
  confirmPassword: string
}

export interface ResetPasswordFormProps {
  onSubmit: (data: ResetPasswordData) => Promise<void> | void
  loading?: boolean
  success?: boolean
  error?: string | null
  token?: string
  className?: string
}

interface PasswordStrength {
  score: number
  feedback: string[]
  color: string
}

const ResetPasswordForm = React.memo<ResetPasswordFormProps>(({
  onSubmit,
  loading = false,
  success = false,
  error = null,
  token,
  className,
}) => {
  const [formData, setFormData] = React.useState<ResetPasswordData>({
    password: '',
    confirmPassword: '',
  })
  
  const [showPassword, setShowPassword] = React.useState(false)
  const [showConfirmPassword, setShowConfirmPassword] = React.useState(false)
  const [validationErrors, setValidationErrors] = React.useState<Record<string, string>>({})
  const [passwordStrength, setPasswordStrength] = React.useState<PasswordStrength>({
    score: 0,
    feedback: [],
    color: 'bg-gray-200',
  })

  const calculatePasswordStrength = React.useCallback((password: string): PasswordStrength => {
    let score = 0
    const feedback: string[] = []
    
    if (password.length >= 8) {
      score += 1
    } else {
      feedback.push('At least 8 characters')
    }
    
    if (/[a-z]/.test(password)) {
      score += 1
    } else {
      feedback.push('Include lowercase letter')
    }
    
    if (/[A-Z]/.test(password)) {
      score += 1
    } else {
      feedback.push('Include uppercase letter')
    }
    
    if (/[0-9]/.test(password)) {
      score += 1
    } else {
      feedback.push('Include number')
    }
    
    if (/[^A-Za-z0-9]/.test(password)) {
      score += 1
    } else {
      feedback.push('Include special character')
    }
    
    const colors = ['bg-red-400', 'bg-orange-400', 'bg-yellow-400', 'bg-blue-400', 'bg-green-400']
    
    return {
      score,
      feedback,
      color: colors[Math.max(0, score - 1)] || 'bg-gray-200',
    }
  }, [])

  const validateField = React.useCallback((field: string, value: string): string | null => {
    switch (field) {
      case 'password':
        if (!value) return 'Password is required'
        if (value.length < 8) return 'Password must be at least 8 characters'
        return null
      case 'confirmPassword':
        if (!value) return 'Please confirm your password'
        if (value !== formData.password) return 'Passwords do not match'
        return null
      default:
        return null
    }
  }, [formData.password])

  const handleInputChange = React.useCallback((field: keyof ResetPasswordData, value: string) => {
    const newFormData = { ...formData, [field]: value }
    setFormData(newFormData)
    
    // Update password strength for password field
    if (field === 'password') {
      setPasswordStrength(calculatePasswordStrength(value))
    }
    
    // Clear validation error for this field
    if (validationErrors[field]) {
      setValidationErrors(prev => {
        const newErrors = { ...prev }
        delete newErrors[field]
        return newErrors
      })
    }
    
    // Revalidate confirmPassword if password changes
    if (field === 'password' && formData.confirmPassword) {
      const confirmError = validateField('confirmPassword', formData.confirmPassword)
      if (confirmError) {
        setValidationErrors(prev => ({ ...prev, confirmPassword: confirmError }))
      }
    }
  }, [formData, validationErrors, calculatePasswordStrength, validateField])

  const handleBlur = React.useCallback((field: string, value: string) => {
    const error = validateField(field, value)
    if (error) {
      setValidationErrors(prev => ({ ...prev, [field]: error }))
    }
  }, [validateField])

  const handleSubmit = React.useCallback(async (e: React.FormEvent) => {
    e.preventDefault()
    
    // Validate all fields
    const errors: Record<string, string> = {}
    Object.entries(formData).forEach(([field, value]) => {
      const error = validateField(field, value)
      if (error) errors[field] = error
    })
    
    setValidationErrors(errors)
    
    if (Object.keys(errors).length === 0) {
      try {
        await onSubmit(formData)
      } catch (err) {
        console.error('Reset password error:', err)
      }
    }
  }, [formData, validateField, onSubmit])

  // Invalid or missing token
  if (!token) {
    return (
      <div className={cn('text-center space-y-6', className)}>
        <div className="flex justify-center">
          <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center">
            <AlertTriangle className="w-8 h-8 text-red-600" />
          </div>
        </div>
        
        <div className="space-y-2">
          <h3 className="text-lg font-medium text-gray-900">
            Invalid Reset Link
          </h3>
          <p className="text-sm text-gray-600">
            This password reset link is invalid or has expired. Please request a new one.
          </p>
        </div>
        
        <a
          href="/forgot-password"
          className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
        >
          Request New Reset Link
        </a>
      </div>
    )
  }

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
            Password Reset Successful
          </h3>
          <p className="text-sm text-gray-600">
            Your password has been successfully updated. You can now log in with your new password.
          </p>
        </div>
        
        <a
          href="/login"
          className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
        >
          Go to Login
        </a>
      </div>
    )
  }

  // Form state
  return (
    <div className={cn('space-y-6', className)}>
      <div className="text-center space-y-2">
        <h3 className="text-lg font-medium text-gray-900">
          Reset Your Password
        </h3>
        <p className="text-sm text-gray-600">
          Enter your new password below.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6" noValidate>
        {/* Error Display */}
        {error && (
          <div className="p-4 bg-red-50 border border-red-200 rounded-md">
            <div className="flex items-center">
              <AlertTriangle className="h-5 w-5 text-red-500 mr-2" />
              <p className="text-red-700 text-sm">{error}</p>
            </div>
          </div>
        )}

        {/* New Password Field */}
        <div className="space-y-1">
          <label
            htmlFor="password"
            className="block text-sm font-medium text-gray-700"
          >
            New Password
          </label>
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <Lock className="h-5 w-5 text-gray-400" />
            </div>
            <input
              id="password"
              name="password"
              type={showPassword ? 'text' : 'password'}
              autoComplete="new-password"
              required
              value={formData.password}
              onChange={(e) => handleInputChange('password', e.target.value)}
              onBlur={(e) => handleBlur('password', e.target.value)}
              className={cn(
                'block w-full pl-10 pr-10 py-2 border rounded-md',
                'focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'placeholder-gray-400 text-gray-900',
                validationErrors.password
                  ? 'border-red-300 bg-red-50'
                  : 'border-gray-300'
              )}
              placeholder="Enter your new password"
              disabled={loading}
            />
            <div className="absolute inset-y-0 right-0 pr-3 flex items-center">
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="text-gray-400 hover:text-gray-500 focus:outline-none focus:text-gray-500"
                disabled={loading}
              >
                {showPassword ? (
                  <EyeOff className="h-5 w-5" />
                ) : (
                  <Eye className="h-5 w-5" />
                )}
              </button>
            </div>
          </div>
          
          {/* Password Strength Indicator */}
          {formData.password && (
            <div className="mt-2">
              <div className="flex items-center space-x-2">
                <div className="flex-1 bg-gray-200 rounded-full h-2">
                  <div
                    className={cn('h-2 rounded-full transition-all duration-300', passwordStrength.color)}
                    style={{ width: `${(passwordStrength.score / 5) * 100}%` }}
                  />
                </div>
                <span className="text-xs text-gray-500">
                  {passwordStrength.score < 3 ? 'Weak' : passwordStrength.score < 5 ? 'Good' : 'Strong'}
                </span>
              </div>
              {passwordStrength.feedback.length > 0 && (
                <div className="mt-1">
                  <p className="text-xs text-gray-600">Suggestions:</p>
                  <ul className="text-xs text-gray-500 list-disc list-inside">
                    {passwordStrength.feedback.slice(0, 3).map((suggestion, index) => (
                      <li key={index}>{suggestion}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}
          
          {validationErrors.password && (
            <p className="text-red-600 text-xs mt-1">{validationErrors.password}</p>
          )}
        </div>

        {/* Confirm Password Field */}
        <div className="space-y-1">
          <label
            htmlFor="confirmPassword"
            className="block text-sm font-medium text-gray-700"
          >
            Confirm New Password
          </label>
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <Lock className="h-5 w-5 text-gray-400" />
            </div>
            <input
              id="confirmPassword"
              name="confirmPassword"
              type={showConfirmPassword ? 'text' : 'password'}
              autoComplete="new-password"
              required
              value={formData.confirmPassword}
              onChange={(e) => handleInputChange('confirmPassword', e.target.value)}
              onBlur={(e) => handleBlur('confirmPassword', e.target.value)}
              className={cn(
                'block w-full pl-10 pr-10 py-2 border rounded-md',
                'focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'placeholder-gray-400 text-gray-900',
                validationErrors.confirmPassword
                  ? 'border-red-300 bg-red-50'
                  : 'border-gray-300'
              )}
              placeholder="Confirm your new password"
              disabled={loading}
            />
            <div className="absolute inset-y-0 right-0 pr-3 flex items-center">
              <button
                type="button"
                onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                className="text-gray-400 hover:text-gray-500 focus:outline-none focus:text-gray-500"
                disabled={loading}
              >
                {showConfirmPassword ? (
                  <EyeOff className="h-5 w-5" />
                ) : (
                  <Eye className="h-5 w-5" />
                )}
              </button>
            </div>
          </div>
          
          {/* Password Match Indicator */}
          {formData.confirmPassword && (
            <div className="flex items-center mt-1">
              {formData.password === formData.confirmPassword ? (
                <div className="flex items-center text-green-600 text-xs">
                  <CheckCircle className="h-3 w-3 mr-1" />
                  Passwords match
                </div>
              ) : (
                <div className="flex items-center text-red-600 text-xs">
                  <AlertTriangle className="h-3 w-3 mr-1" />
                  Passwords do not match
                </div>
              )}
            </div>
          )}
          
          {validationErrors.confirmPassword && (
            <p className="text-red-600 text-xs mt-1">{validationErrors.confirmPassword}</p>
          )}
        </div>

        {/* Submit Button */}
        <button
          type="submit"
          disabled={loading}
          className={cn(
            'w-full flex justify-center items-center py-2 px-4 border border-transparent',
            'text-sm font-medium rounded-md text-white',
            'focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500',
            loading
              ? 'bg-gray-400 cursor-not-allowed'
              : 'bg-blue-600 hover:bg-blue-700'
          )}
        >
          {loading ? (
            <>
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2" />
              Updating password...
            </>
          ) : (
            'Update password'
          )}
        </button>
      </form>
    </div>
  )
})

ResetPasswordForm.displayName = 'ResetPasswordForm'

export default ResetPasswordForm