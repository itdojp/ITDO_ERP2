import React, { useEffect, useState } from 'react'
import { Navigate, useLocation } from 'react-router-dom'
import { useAuthState } from '../services/authApi'
import Loading from './ui/Loading'

interface PrivateRouteProps {
  children: React.ReactNode
}

export function PrivateRoute({ children }: PrivateRouteProps) {
  const { isAuthenticated } = useAuthState()
  const location = useLocation()
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    // Add a small delay to allow auth state to initialize
    const timer = setTimeout(() => {
      setIsLoading(false)
    }, 100)

    return () => clearTimeout(timer)
  }, [])

  // Show loading while determining auth status
  if (isLoading) {
    return <Loading message="Checking authentication..." />
  }

  // If not authenticated, redirect to login with return URL
  if (!isAuthenticated) {
    const redirectTo = location.pathname + location.search
    return <Navigate to={`/login?redirect=${encodeURIComponent(redirectTo)}`} replace />
  }

  // If authenticated, render the protected component
  return <>{children}</>
}

export default PrivateRoute