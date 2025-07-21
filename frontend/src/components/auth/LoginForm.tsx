import React from 'react'
import { Eye, EyeOff, Mail, Lock, AlertTriangle } from 'lucide-react'
import { cn } from '../../lib/utils'

export interface LoginCredentials {
  email: string
  password: string
  rememberMe?: boolean
}

export interface LoginFormProps {
  onSubmit: (credentials: LoginCredentials) => Promise<void> | void
  loading?: boolean
  error?: string | null
  showRememberMe?: boolean
  showForgotPassword?: boolean
  showSocialLogin?: boolean
  onForgotPassword?: () => void
  onSocialLogin?: (provider: string) => void
  className?: string
}

const LoginForm = React.memo<LoginFormProps>(({
  onSubmit,
  loading = false,
  error = null,
  showRememberMe = true,
  showForgotPassword = true,
  showSocialLogin = false,
  onForgotPassword,
  onSocialLogin,
  className,
}) => {
  const [formData, setFormData] = React.useState<LoginCredentials>({
    email: '',
    password: '',
    rememberMe: false,
  })
  
  const [showPassword, setShowPassword] = React.useState(false)
  const [validationErrors, setValidationErrors] = React.useState<Record<string, string>>({})

  const validateField = React.useCallback((field: string, value: string): string | null => {
    switch (field) {
      case 'email':
        if (!value) return 'Email is required'
        if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value)) return 'Please enter a valid email address'
        return null
      case 'password':
        if (!value) return 'Password is required'
        if (value.length < 8) return 'Password must be at least 8 characters'
        return null
      default:
        return null
    }
  }, [])

  const handleInputChange = React.useCallback((field: keyof LoginCredentials, value: string | boolean) => {
    setFormData(prev => ({ ...prev, [field]: value }))
    
    // Clear validation error for this field
    if (validationErrors[field]) {
      setValidationErrors(prev => {
        const newErrors = { ...prev }
        delete newErrors[field]
        return newErrors
      })
    }
  }, [validationErrors])

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
      if (field !== 'rememberMe') {
        const error = validateField(field, value as string)
        if (error) errors[field] = error
      }
    })
    
    setValidationErrors(errors)
    
    if (Object.keys(errors).length === 0) {
      try {
        await onSubmit(formData)
      } catch (err) {
        // Error handling is managed by parent component
        console.error('Login error:', err)
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
            placeholder="Enter your email"
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
            autoComplete="current-password"
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
            placeholder="Enter your password"
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
        {validationErrors.password && (
          <p className="text-red-600 text-xs mt-1">{validationErrors.password}</p>
        )}
      </div>

      {/* Remember Me & Forgot Password */}
      {(showRememberMe || showForgotPassword) && (
        <div className="flex items-center justify-between">
          {showRememberMe && (
            <div className="flex items-center">
              <input
                id="rememberMe"
                name="rememberMe"
                type="checkbox"
                checked={formData.rememberMe}
                onChange={(e) => handleInputChange('rememberMe', e.target.checked)}
                className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                disabled={loading}
              />
              <label
                htmlFor="rememberMe"
                className="ml-2 block text-sm text-gray-700"
              >
                Remember me
              </label>
            </div>
          )}

          {showForgotPassword && onForgotPassword && (
            <button
              type="button"
              onClick={onForgotPassword}
              className="text-sm text-blue-600 hover:text-blue-500 focus:outline-none focus:underline"
              disabled={loading}
            >
              Forgot password?
            </button>
          )}
        </div>
      )}

      {/* Submit Button */}
      <div>
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
              Signing in...
            </>
          ) : (
            'Sign in'
          )}
        </button>
      </div>

      {/* Social Login */}
      {showSocialLogin && onSocialLogin && (
        <div className="mt-6">
          <div className="relative">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-gray-300" />
            </div>
            <div className="relative flex justify-center text-sm">
              <span className="px-2 bg-white text-gray-500">Or continue with</span>
            </div>
          </div>

          <div className="mt-6 grid grid-cols-1 gap-3">
            {socialProviders.map((provider) => (
              <button
                key={provider.id}
                type="button"
                onClick={() => onSocialLogin(provider.id)}
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

LoginForm.displayName = 'LoginForm'

export default LoginForm