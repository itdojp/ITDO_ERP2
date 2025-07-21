import React from 'react'
import { Eye, EyeOff, Mail, Lock, User, AlertTriangle, CheckCircle } from 'lucide-react'
import { cn } from '../../lib/utils'

export interface SignUpData {
  firstName: string
  lastName: string
  email: string
  password: string
  confirmPassword: string
  agreeToTerms: boolean
  subscribesToNewsletter?: boolean
}

export interface SignUpFormProps {
  onSubmit: (data: SignUpData) => Promise<void> | void
  loading?: boolean
  error?: string | null
  showSocialSignUp?: boolean
  showNewsletterOption?: boolean
  onSocialSignUp?: (provider: string) => void
  className?: string
}

interface PasswordStrength {
  score: number
  feedback: string[]
  color: string
}

const SignUpForm = React.memo<SignUpFormProps>(({
  onSubmit,
  loading = false,
  error = null,
  showSocialSignUp = false,
  showNewsletterOption = true,
  onSocialSignUp,
  className,
}) => {
  const [formData, setFormData] = React.useState<SignUpData>({
    firstName: '',
    lastName: '',
    email: '',
    password: '',
    confirmPassword: '',
    agreeToTerms: false,
    subscribesToNewsletter: false,
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
      case 'firstName':
        if (!value.trim()) return 'First name is required'
        if (value.trim().length < 2) return 'First name must be at least 2 characters'
        return null
      case 'lastName':
        if (!value.trim()) return 'Last name is required'
        if (value.trim().length < 2) return 'Last name must be at least 2 characters'
        return null
      case 'email':
        if (!value) return 'Email is required'
        if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value)) return 'Please enter a valid email address'
        return null
      case 'password':
        if (!value) return 'Password is required'
        if (value.length < 8) return 'Password must be at least 8 characters'
        return null
      case 'confirmPassword':
        if (!value) return 'Please confirm your password'
        if (value !== formData.password) return 'Passwords do not match'
        return null
      case 'agreeToTerms':
        if (!formData.agreeToTerms) return 'You must agree to the terms and conditions'
        return null
      default:
        return null
    }
  }, [formData.password, formData.agreeToTerms])

  const handleInputChange = React.useCallback((field: keyof SignUpData, value: string | boolean) => {
    const newFormData = { ...formData, [field]: value }
    setFormData(newFormData)
    
    // Update password strength for password field
    if (field === 'password' && typeof value === 'string') {
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
      if (field !== 'subscribesToNewsletter') {
        const error = validateField(field, value as string)
        if (error) errors[field] = error
      }
    })
    
    setValidationErrors(errors)
    
    if (Object.keys(errors).length === 0) {
      try {
        await onSubmit(formData)
      } catch (err) {
        console.error('Sign up error:', err)
      }
    }
  }, [formData, validateField, onSubmit])

  const socialProviders = [
    { id: 'google', name: 'Google', icon: '🌐' },
    { id: 'github', name: 'GitHub', icon: '🐙' },
    { id: 'microsoft', name: 'Microsoft', icon: '🏢' },
  ]

  return (
    <form
      onSubmit={handleSubmit}
      className={cn('space-y-6', className)}
      noValidate
    >
      {/* Form Error Display */}
      {error && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-md">
          <div className="flex items-center">
            <AlertTriangle className="h-5 w-5 text-red-500 mr-2" />
            <p className="text-red-700 text-sm">{error}</p>
          </div>
        </div>
      )}

      {/* Name Fields */}
      <div className="grid grid-cols-2 gap-4">
        {/* First Name */}
        <div className="space-y-1">
          <label
            htmlFor="firstName"
            className="block text-sm font-medium text-gray-700"
          >
            First Name
          </label>
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <User className="h-5 w-5 text-gray-400" />
            </div>
            <input
              id="firstName"
              name="firstName"
              type="text"
              autoComplete="given-name"
              required
              value={formData.firstName}
              onChange={(e) => handleInputChange('firstName', e.target.value)}
              onBlur={(e) => handleBlur('firstName', e.target.value)}
              className={cn(
                'block w-full pl-10 pr-3 py-2 border rounded-md',
                'focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'placeholder-gray-400 text-gray-900',
                validationErrors.firstName
                  ? 'border-red-300 bg-red-50'
                  : 'border-gray-300'
              )}
              placeholder="John"
              disabled={loading}
            />
          </div>
          {validationErrors.firstName && (
            <p className="text-red-600 text-xs mt-1">{validationErrors.firstName}</p>
          )}
        </div>

        {/* Last Name */}
        <div className="space-y-1">
          <label
            htmlFor="lastName"
            className="block text-sm font-medium text-gray-700"
          >
            Last Name
          </label>
          <input
            id="lastName"
            name="lastName"
            type="text"
            autoComplete="family-name"
            required
            value={formData.lastName}
            onChange={(e) => handleInputChange('lastName', e.target.value)}
            onBlur={(e) => handleBlur('lastName', e.target.value)}
            className={cn(
              'block w-full px-3 py-2 border rounded-md',
              'focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent',
              'placeholder-gray-400 text-gray-900',
              validationErrors.lastName
                ? 'border-red-300 bg-red-50'
                : 'border-gray-300'
            )}
            placeholder="Doe"
            disabled={loading}
          />
          {validationErrors.lastName && (
            <p className="text-red-600 text-xs mt-1">{validationErrors.lastName}</p>
          )}
        </div>
      </div>

      {/* Email Field */}
      <div className="space-y-1">
        <label
          htmlFor="email"
          className="block text-sm font-medium text-gray-700"
        >
          Email Address
        </label>
        <div className="relative">
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
            <Mail className="h-5 w-5 text-gray-400" />
          </div>
          <input
            id="email"
            name="email"
            type="email"
            autoComplete="email"
            required
            value={formData.email}
            onChange={(e) => handleInputChange('email', e.target.value)}
            onBlur={(e) => handleBlur('email', e.target.value)}
            className={cn(
              'block w-full pl-10 pr-3 py-2 border rounded-md',
              'focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent',
              'placeholder-gray-400 text-gray-900',
              validationErrors.email
                ? 'border-red-300 bg-red-50'
                : 'border-gray-300'
            )}
            placeholder="john@example.com"
            disabled={loading}
          />
        </div>
        {validationErrors.email && (
          <p className="text-red-600 text-xs mt-1">{validationErrors.email}</p>
        )}
      </div>

      {/* Password Field */}
      <div className="space-y-1">
        <label
          htmlFor="password"
          className="block text-sm font-medium text-gray-700"
        >
          Password
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
            placeholder="Create a strong password"
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
          Confirm Password
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
            placeholder="Confirm your password"
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

      {/* Terms and Conditions */}
      <div className="space-y-4">
        <div className="flex items-start">
          <div className="flex items-center h-5">
            <input
              id="agreeToTerms"
              name="agreeToTerms"
              type="checkbox"
              checked={formData.agreeToTerms}
              onChange={(e) => handleInputChange('agreeToTerms', e.target.checked)}
              className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
              disabled={loading}
            />
          </div>
          <div className="ml-3 text-sm">
            <label
              htmlFor="agreeToTerms"
              className="font-medium text-gray-700"
            >
              I agree to the{' '}
              <a href="/terms" className="text-blue-600 hover:text-blue-500">
                Terms and Conditions
              </a>{' '}
              and{' '}
              <a href="/privacy" className="text-blue-600 hover:text-blue-500">
                Privacy Policy
              </a>
            </label>
          </div>
        </div>
        {validationErrors.agreeToTerms && (
          <p className="text-red-600 text-xs">{validationErrors.agreeToTerms}</p>
        )}

        {/* Newsletter Subscription */}
        {showNewsletterOption && (
          <div className="flex items-start">
            <div className="flex items-center h-5">
              <input
                id="subscribesToNewsletter"
                name="subscribesToNewsletter"
                type="checkbox"
                checked={formData.subscribesToNewsletter}
                onChange={(e) => handleInputChange('subscribesToNewsletter', e.target.checked)}
                className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                disabled={loading}
              />
            </div>
            <div className="ml-3 text-sm">
              <label
                htmlFor="subscribesToNewsletter"
                className="text-gray-700"
              >
                Subscribe to our newsletter for product updates and tips
              </label>
            </div>
          </div>
        )}
      </div>

      {/* Submit Button */}
      <div>
        <button
          type="submit"
          disabled={loading || !formData.agreeToTerms}
          className={cn(
            'w-full flex justify-center items-center py-2 px-4 border border-transparent',
            'text-sm font-medium rounded-md text-white',
            'focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500',
            loading || !formData.agreeToTerms
              ? 'bg-gray-400 cursor-not-allowed'
              : 'bg-blue-600 hover:bg-blue-700'
          )}
        >
          {loading ? (
            <>
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2" />
              Creating account...
            </>
          ) : (
            'Create account'
          )}
        </button>
      </div>

      {/* Social Sign Up */}
      {showSocialSignUp && onSocialSignUp && (
        <div className="mt-6">
          <div className="relative">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-gray-300" />
            </div>
            <div className="relative flex justify-center text-sm">
              <span className="px-2 bg-white text-gray-500">Or sign up with</span>
            </div>
          </div>

          <div className="mt-6 grid grid-cols-1 gap-3">
            {socialProviders.map((provider) => (
              <button
                key={provider.id}
                type="button"
                onClick={() => onSocialSignUp(provider.id)}
                disabled={loading}
                className={cn(
                  'w-full inline-flex justify-center items-center py-2 px-4',
                  'border border-gray-300 rounded-md shadow-sm bg-white',
                  'text-sm font-medium text-gray-500',
                  'hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500',
                  loading && 'cursor-not-allowed opacity-50'
                )}
              >
                <span className="mr-2 text-lg">{provider.icon}</span>
                {provider.name}
              </button>
            ))}
          </div>
        </div>
      )}
    </form>
  )
})

SignUpForm.displayName = 'SignUpForm'

export default SignUpForm