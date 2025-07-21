import React from 'react'
import { usePermissionContext } from '../../hooks/usePermissions'
import { UserRole } from '../../services/api/types'

export interface PermissionGateProps {
  children: React.ReactNode
  requiredPermission?: {
    resource: string
    action: string
    context?: any
  }
  requiredRole?: UserRole | UserRole[]
  requiresAuth?: boolean
  fallback?: React.ReactNode
  renderWhenDenied?: boolean
  mode?: 'all' | 'any' // For multiple permissions
  permissions?: Array<{ resource: string; action: string; context?: any }>
}

/**
 * PermissionGate component conditionally renders children based on user permissions
 */
const PermissionGate = React.memo<PermissionGateProps>(({
  children,
  requiredPermission,
  requiredRole,
  requiresAuth = true,
  fallback = null,
  renderWhenDenied = false,
  mode = 'all',
  permissions = [],
}) => {
  const {
    user,
    hasPermission,
    hasRole,
    hasAllPermissions,
    hasAnyPermission,
  } = usePermissionContext()

  // Check authentication
  if (requiresAuth && !user) {
    return renderWhenDenied ? <>{fallback}</> : null
  }

  // Check role-based access
  if (requiredRole && !hasRole(requiredRole)) {
    return renderWhenDenied ? <>{fallback}</> : null
  }

  // Check single permission
  if (requiredPermission) {
    const { resource, action, context } = requiredPermission
    if (!hasPermission(resource, action, context)) {
      return renderWhenDenied ? <>{fallback}</> : null
    }
  }

  // Check multiple permissions
  if (permissions.length > 0) {
    const permissionChecks = permissions.map(({ resource, action }) => ({
      resource,
      action,
    }))

    const hasRequiredPermissions = mode === 'all' 
      ? hasAllPermissions(permissionChecks)
      : hasAnyPermission(permissionChecks)

    if (!hasRequiredPermissions) {
      return renderWhenDenied ? <>{fallback}</> : null
    }
  }

  return <>{children}</>
})

PermissionGate.displayName = 'PermissionGate'

export default PermissionGate