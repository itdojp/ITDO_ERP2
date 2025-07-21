import React from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import { ErrorBoundary } from 'react-error-boundary'

// Import lazy page components
import {
  LazyDashboard,
  LazyUserManagement,
  LazyUserProfile,
  LazyAnalytics,
  LazyReports,
  LazyOrganization,
  LazyDepartments,
  LazyProjects,
  LazyProjectDetail,
  LazyTasks,
  LazySettings,
  LazyProfile,
  LazyPreferences,
  LazyAdminUsers,
  LazyAdminRoles,
  LazyAdminPermissions,
  LazyAdminSystem,
  LazyNotFound,
  LazyUnauthorized,
  LazyServerError,
  LazyHelp,
  LazyDocumentation,
  LazyLogin,
  LazyRegister,
  LazyForgotPassword,
  LazyResetPassword,
  preloadCriticalRoutes
} from '../pages/lazy'

// Import layout components (these should remain eager for better UX)
import Layout from '../components/Layout'
import AdminLayout from '../components/AdminLayout'
import PrivateRoute from '../components/PrivateRoute'

// Error fallback component for route errors
const RouteErrorFallback: React.FC<{
  error: Error
  resetErrorBoundary: () => void
}> = ({ error, resetErrorBoundary }) => (
  <div className="min-h-screen flex items-center justify-center bg-gray-50">
    <div className="max-w-md w-full text-center">
      <div className="bg-red-50 border border-red-200 rounded-lg p-6">
        <h2 className="text-lg font-semibold text-red-900 mb-2">
          Route Loading Error
        </h2>
        <p className="text-red-700 mb-4">
          Failed to load the requested page.
        </p>
        <p className="text-sm text-red-600 mb-4">
          {error.message}
        </p>
        <div className="space-x-4">
          <button
            onClick={resetErrorBoundary}
            className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-red-600 hover:bg-red-700"
          >
            Try Again
          </button>
          <button
            onClick={() => window.location.href = '/'}
            className="inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
          >
            Go Home
          </button>
        </div>
      </div>
    </div>
  </div>
)

// Route preloading component
const RoutePreloader: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  React.useEffect(() => {
    // Preload critical routes after initial render
    const preloadTimer = setTimeout(() => {
      preloadCriticalRoutes().catch(console.error)
    }, 1000)

    return () => clearTimeout(preloadTimer)
  }, [])

  return <>{children}</>
}

// Main lazy router component
export const LazyRouter: React.FC = () => {
  return (
    <RoutePreloader>
      <ErrorBoundary FallbackComponent={RouteErrorFallback}>
        <Routes>
          {/* Public routes */}
          <Route path="/login" element={<LazyLogin.Component />} />
          <Route path="/register" element={<LazyRegister.Component />} />
          <Route path="/forgot-password" element={<LazyForgotPassword.Component />} />
          <Route path="/reset-password" element={<LazyResetPassword.Component />} />

          {/* Error pages */}
          <Route path="/unauthorized" element={<LazyUnauthorized.Component />} />
          <Route path="/server-error" element={<LazyServerError.Component />} />

          {/* Protected routes with layout */}
          <Route element={<PrivateRoute><Layout /></PrivateRoute>}>
            {/* Dashboard */}
            <Route path="/" element={<Navigate to="/dashboard" replace />} />
            <Route path="/dashboard" element={
              <ErrorBoundary FallbackComponent={RouteErrorFallback}>
                <LazyDashboard.Component />
              </ErrorBoundary>
            } />

            {/* User Management */}
            <Route path="/users" element={
              <ErrorBoundary FallbackComponent={RouteErrorFallback}>
                <LazyUserManagement.Component />
              </ErrorBoundary>
            } />
            <Route path="/users/:id" element={
              <ErrorBoundary FallbackComponent={RouteErrorFallback}>
                <LazyUserProfile.Component />
              </ErrorBoundary>
            } />

            {/* Analytics & Reports */}
            <Route path="/analytics" element={
              <ErrorBoundary FallbackComponent={RouteErrorFallback}>
                <LazyAnalytics.Component />
              </ErrorBoundary>
            } />
            <Route path="/reports" element={
              <ErrorBoundary FallbackComponent={RouteErrorFallback}>
                <LazyReports.Component />
              </ErrorBoundary>
            } />

            {/* Organization */}
            <Route path="/organization" element={
              <ErrorBoundary FallbackComponent={RouteErrorFallback}>
                <LazyOrganization.Component />
              </ErrorBoundary>
            } />
            <Route path="/departments" element={
              <ErrorBoundary FallbackComponent={RouteErrorFallback}>
                <LazyDepartments.Component />
              </ErrorBoundary>
            } />

            {/* Projects & Tasks */}
            <Route path="/projects" element={
              <ErrorBoundary FallbackComponent={RouteErrorFallback}>
                <LazyProjects.Component />
              </ErrorBoundary>
            } />
            <Route path="/projects/:id" element={
              <ErrorBoundary FallbackComponent={RouteErrorFallback}>
                <LazyProjectDetail.Component />
              </ErrorBoundary>
            } />
            <Route path="/tasks" element={
              <ErrorBoundary FallbackComponent={RouteErrorFallback}>
                <LazyTasks.Component />
              </ErrorBoundary>
            } />

            {/* User Settings */}
            <Route path="/settings" element={
              <ErrorBoundary FallbackComponent={RouteErrorFallback}>
                <LazySettings.Component />
              </ErrorBoundary>
            } />
            <Route path="/profile" element={
              <ErrorBoundary FallbackComponent={RouteErrorFallback}>
                <LazyProfile.Component />
              </ErrorBoundary>
            } />
            <Route path="/preferences" element={
              <ErrorBoundary FallbackComponent={RouteErrorFallback}>
                <LazyPreferences.Component />
              </ErrorBoundary>
            } />

            {/* Help & Documentation */}
            <Route path="/help" element={
              <ErrorBoundary FallbackComponent={RouteErrorFallback}>
                <LazyHelp.Component />
              </ErrorBoundary>
            } />
            <Route path="/docs" element={
              <ErrorBoundary FallbackComponent={RouteErrorFallback}>
                <LazyDocumentation.Component />
              </ErrorBoundary>
            } />
          </Route>

          {/* Admin routes with separate layout */}
          <Route path="/admin" element={
            <PrivateRoute requiredRole="admin">
              <AdminLayout />
            </PrivateRoute>
          }>
            <Route index element={<Navigate to="/admin/users" replace />} />
            <Route path="users" element={
              <ErrorBoundary FallbackComponent={RouteErrorFallback}>
                <LazyAdminUsers.Component />
              </ErrorBoundary>
            } />
            <Route path="roles" element={
              <ErrorBoundary FallbackComponent={RouteErrorFallback}>
                <LazyAdminRoles.Component />
              </ErrorBoundary>
            } />
            <Route path="permissions" element={
              <ErrorBoundary FallbackComponent={RouteErrorFallback}>
                <LazyAdminPermissions.Component />
              </ErrorBoundary>
            } />
            <Route path="system" element={
              <ErrorBoundary FallbackComponent={RouteErrorFallback}>
                <LazyAdminSystem.Component />
              </ErrorBoundary>
            } />
          </Route>

          {/* Catch all route */}
          <Route path="*" element={<LazyNotFound.Component />} />
        </Routes>
      </ErrorBoundary>
    </RoutePreloader>
  )
}

// Route preloading utilities
export const useRoutePreloading = () => {
  const [isPreloading, setIsPreloading] = React.useState(false)
  const [preloadedRoutes, setPreloadedRoutes] = React.useState<string[]>([])

  const preloadRoute = React.useCallback(async (routeName: string) => {
    if (preloadedRoutes.includes(routeName)) return

    setIsPreloading(true)
    try {
      // This would need to be implemented based on the specific route structure
      console.log(`Preloading route: ${routeName}`)
      setPreloadedRoutes(prev => [...prev, routeName])
    } catch (error) {
      console.error(`Failed to preload route ${routeName}:`, error)
    } finally {
      setIsPreloading(false)
    }
  }, [preloadedRoutes])

  const preloadRouteOnHover = React.useCallback((routeName: string) => {
    return {
      onMouseEnter: () => preloadRoute(routeName),
      onFocus: () => preloadRoute(routeName)
    }
  }, [preloadRoute])

  return {
    isPreloading,
    preloadedRoutes,
    preloadRoute,
    preloadRouteOnHover
  }
}

// Navigation component with smart preloading
export const SmartNavLink: React.FC<{
  to: string
  routeName?: string
  children: React.ReactNode
  className?: string
  onClick?: () => void
}> = ({ to, routeName, children, className, onClick }) => {
  const { preloadRouteOnHover } = useRoutePreloading()
  
  return (
    <a
      href={to}
      className={className}
      onClick={onClick}
      {...(routeName ? preloadRouteOnHover(routeName) : {})}
    >
      {children}
    </a>
  )
}

export default LazyRouter