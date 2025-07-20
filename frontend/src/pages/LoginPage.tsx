import { useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import Button from '../components/ui/Button'
import Input from '../components/ui/Input'
import Alert from '../components/ui/Alert'
import Loading from '../components/ui/Loading'

interface LoginFormData {
  email: string
  password: string
  rememberMe?: boolean
}

export function LoginPage() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const {
    register,
    handleSubmit,
    formState: { errors }
  } = useForm<LoginFormData>()

  const onSubmit = async (data: LoginFormData) => {
    setIsLoading(true)
    setError(null)

    try {
      // TODO: Replace with actual API call
      await new Promise(resolve => setTimeout(resolve, 1000))
      
      // Mock authentication
      if (data.email === 'test@example.com' && data.password === 'password123') {
        // Set session cookies
        // Set session duration based on remember me option
        // sessionExpiry would be used for actual cookie setting

        // Store token in localStorage for now
        localStorage.setItem('token', 'mock-jwt-token')
        localStorage.setItem('user', JSON.stringify({
          id: '1',
          email: data.email,
          name: 'Test User'
        }))

        // Redirect to requested page or dashboard
        const redirectTo = searchParams.get('redirect') || '/dashboard'
        navigate(redirectTo)
      } else {
        throw new Error('Invalid credentials')
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Login failed')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <div>
          <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
            Sign in to ITDO ERP
          </h2>
          <p className="mt-2 text-center text-sm text-gray-600">
            Enter your credentials to access the system
          </p>
        </div>

        <form className="mt-8 space-y-6" onSubmit={handleSubmit(onSubmit)}>
          <div className="space-y-4">
            <div>
              <Input
                label="Email address"
                type="email"
                required
                {...register('email', {
                  required: 'Email is required',
                  pattern: {
                    value: /^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$/i,
                    message: 'Invalid email address'
                  }
                })}
                error={!!errors.email}
                errorMessage={errors.email?.message}
              />
              {errors.email && <div id="email-error" className="sr-only">{errors.email.message}</div>}
            </div>

            <div>
              <Input
                label="Password"
                type="password"
                required
                {...register('password', {
                  required: 'Password is required',
                  minLength: {
                    value: 6,
                    message: 'Password must be at least 6 characters'
                  }
                })}
                error={!!errors.password}
                errorMessage={errors.password?.message}
              />
              {errors.password && <div id="password-error" className="sr-only">{errors.password.message}</div>}
            </div>

            <div className="flex items-center">
              <input
                {...register('rememberMe')}
                id="rememberMe"
                name="rememberMe"
                type="checkbox"
                className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
              />
              <label htmlFor="rememberMe" className="ml-2 block text-sm text-gray-900">
                Remember me
              </label>
            </div>
          </div>

          {error && (
            <Alert 
              variant="error" 
              title="Login Failed" 
              message={error}
              className="error-message"
            />
          )}

          <div>
            <Button
              type="submit"
              className="w-full"
              loading={isLoading}
              disabled={isLoading}
            >
              {isLoading ? (
                <div className="loading-spinner">
                  <Loading message="Signing in..." />
                </div>
              ) : (
                'Sign in'
              )}
            </Button>
          </div>
        </form>

        <div className="text-center">
          <p className="text-sm text-gray-600">
            Test credentials: test@example.com / password123
          </p>
        </div>
      </div>
    </div>
  )
}