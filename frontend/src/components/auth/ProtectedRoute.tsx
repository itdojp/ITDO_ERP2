import React from 'react'
import { Navigate, useLocation } from 'react-router-dom'
import { usePermissionContext } from '../../hooks/usePermissions'
import { UserRole } from '../../services/api/types'
import { AlertTriangle, Lock } from 'lucide-react'

export interface ProtectedRouteProps {
  children: React.ReactNode
  requiredPermission?: {
    resource: string
    action: string
    context?: any
  }
  requiredRole?: UserRole | UserRole[]
  requiresAuth?: boolean
  fallback?: React.ReactNode
  redirectTo?: string
  showFallback?: boolean
}

const AccessDeniedFallback: React.FC<{
  message?: string
  canGoBack?: boolean
}> = ({ 
  message = "You don't have permission to access this page.",
  canGoBack = true 
}) => (
  <div className="min-h-screen flex items-center justify-center bg-gray-50">
    <div className="max-w-md w-full bg-white shadow-lg rounded-lg p-8 text-center">
      <div className="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-red-100 mb-4">
        <Lock className="h-6 w-6 text-red-600" />
      </div>
      <h1 className="text-lg font-semibold text-gray-900 mb-2">Access Denied</h1>
      <p className="text-gray-600 mb-6">{message}</p>
      {canGoBack && (
        <div className="space-y-3">
          <button
            onClick={() => window.history.back()}
            className="w-full bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700"
          >
            Go Back
          </button>
          <button
            onClick={() => window.location.href = '/'}
            className="w-full bg-gray-200 text-gray-700 px-4 py-2 rounded-md hover:bg-gray-300"
          >
            Go to Dashboard
          </button>
        </div>
      )}
    </div>
  </div>
)

const NotAuthenticatedFallback: React.FC = () => (
  <div className="min-h-screen flex items-center justify-center bg-gray-50">
    <div className="max-w-md w-full bg-white shadow-lg rounded-lg p-8 text-center">
      <div className="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-yellow-100 mb-4">
        <AlertTriangle className="h-6 w-6 text-yellow-600" />
      </div>
      <h1 className="text-lg font-semibold text-gray-900 mb-2">Authentication Required</h1>
      <p className="text-gray-600 mb-6">Please log in to access this page.</p>
      <button
        onClick={() => window.location.href = '/login'}
        className="w-full bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700"
      >
        Go to Login
      </button>
    </div>
  </div>
)

const ProtectedRoute = React.memo<ProtectedRouteProps>(({
  children,
  requiredPermission,
  requiredRole,
  requiresAuth = true,
  fallback,
  redirectTo,
  showFallback = true,
}) => {
  const location = useLocation()
  const {
    user,
    hasPermission,
    hasRole,
  } = usePermissionContext()

  // Check authentication
  if (requiresAuth && !user) {
    if (redirectTo) {
      return <Navigate to={redirectTo} state={{ from: location }} replace />
    }
    
    if (showFallback) {
      return fallback || <NotAuthenticatedFallback />
    }
    
    return <Navigate to="/login" state={{ from: location }} replace />
  }

  // Check role-based access
  if (requiredRole && !hasRole(requiredRole)) {
    if (redirectTo) {
      return <Navigate to={redirectTo} replace />
    }
    
    if (showFallback) {
      return fallback || (
        <AccessDeniedFallback 
          message="Your role doesn't have access to this page." 
        />
      )
    }
    
    return <Navigate to="/dashboard" replace />
  }

  // Check permission-based access
  if (requiredPermission) {
    const { resource, action, context } = requiredPermission
    if (!hasPermission(resource, action, context)) {
      if (redirectTo) {
        return <Navigate to={redirectTo} replace />
      }
      
      if (showFallback) {
        return fallback || (
          <AccessDeniedFallback 
            message="You don't have the required permissions to access this page." 
          />
        )
      }
      
      return <Navigate to="/dashboard" replace />
    }
  }

  return <>{children}</>
})

ProtectedRoute.displayName = 'ProtectedRoute'

export default ProtectedRoute