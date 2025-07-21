import React from 'react'
import { User, Permission, UserRole } from '../services/api/types'

export interface PermissionContext {
  user: User | null
  permissions: Permission[]
  roles: UserRole[]
  hasPermission: (resource: string, action: string, context?: any) => boolean
  hasRole: (role: UserRole | UserRole[]) => boolean
  hasAnyPermission: (permissions: Array<{ resource: string; action: string }>) => boolean
  hasAllPermissions: (permissions: Array<{ resource: string; action: string }>) => boolean
  canAccess: (resource: string, action?: string) => boolean
  isAdmin: boolean
  isManager: boolean
  isMember: boolean
  isGuest: boolean
}

export interface UsePermissionsOptions {
  user?: User | null
  permissions?: Permission[]
  roles?: UserRole[]
}

// Default role hierarchy (higher number = more permissions)
const ROLE_HIERARCHY: Record<UserRole, number> = {
  [UserRole.GUEST]: 1,
  [UserRole.VIEWER]: 2,
  [UserRole.MEMBER]: 3,
  [UserRole.MANAGER]: 4,
  [UserRole.ADMIN]: 5,
}

// Permission evaluation engine
class PermissionEngine {
  private user: User | null
  private permissions: Permission[]
  private roleHierarchy: Record<UserRole, number>

  constructor(user: User | null, permissions: Permission[] = [], roleHierarchy = ROLE_HIERARCHY) {
    this.user = user
    this.permissions = permissions
    this.roleHierarchy = roleHierarchy
  }

  hasPermission(resource: string, action: string, context?: any): boolean {
    if (!this.user) return false

    // Admin has all permissions
    if (this.user.role === UserRole.ADMIN) return true

    // Check explicit permissions
    const hasExplicitPermission = this.permissions.some(permission => {
      if (permission.resource !== resource || permission.action !== action) {
        return false
      }

      // Check conditions if any
      if (permission.conditions && context) {
        return this.evaluateConditions(permission.conditions, context)
      }

      return true
    })

    if (hasExplicitPermission) return true

    // Check role-based permissions
    return this.checkRoleBasedPermission(resource, action, context)
  }

  hasRole(role: UserRole | UserRole[]): boolean {
    if (!this.user) return false

    const roles = Array.isArray(role) ? role : [role]
    return roles.includes(this.user.role)
  }

  hasAnyRole(roles: UserRole[]): boolean {
    if (!this.user) return false
    return roles.includes(this.user.role)
  }

  hasRoleLevel(minimumLevel: UserRole): boolean {
    if (!this.user) return false

    const userLevel = this.roleHierarchy[this.user.role] || 0
    const requiredLevel = this.roleHierarchy[minimumLevel] || 0

    return userLevel >= requiredLevel
  }

  private evaluateConditions(conditions: Record<string, any>, context: any): boolean {
    return Object.entries(conditions).every(([key, expectedValue]) => {
      const actualValue = this.getNestedValue(context, key)
      
      if (Array.isArray(expectedValue)) {
        return expectedValue.includes(actualValue)
      }
      
      if (typeof expectedValue === 'object' && expectedValue !== null) {
        if (expectedValue.operator === 'in') {
          return expectedValue.values.includes(actualValue)
        }
        if (expectedValue.operator === 'equals') {
          return actualValue === expectedValue.value
        }
        if (expectedValue.operator === 'not_equals') {
          return actualValue !== expectedValue.value
        }
        if (expectedValue.operator === 'contains') {
          return String(actualValue).includes(expectedValue.value)
        }
      }
      
      return actualValue === expectedValue
    })
  }

  private getNestedValue(obj: any, path: string): any {
    return path.split('.').reduce((current, key) => current?.[key], obj)
  }

  private checkRoleBasedPermission(resource: string, action: string, context?: any): boolean {
    if (!this.user) return false

    // Define default role-based permissions
    const rolePermissions: Record<UserRole, Array<{ resource: string; actions: string[] }>> = {
      [UserRole.ADMIN]: [
        { resource: '*', actions: ['*'] }
      ],
      [UserRole.MANAGER]: [
        { resource: 'user', actions: ['read', 'create', 'update'] },
        { resource: 'project', actions: ['read', 'create', 'update', 'delete'] },
        { resource: 'task', actions: ['read', 'create', 'update', 'delete'] },
        { resource: 'report', actions: ['read', 'create'] },
      ],
      [UserRole.MEMBER]: [
        { resource: 'user', actions: ['read'] },
        { resource: 'project', actions: ['read'] },
        { resource: 'task', actions: ['read', 'create', 'update'] },
        { resource: 'report', actions: ['read'] },
      ],
      [UserRole.VIEWER]: [
        { resource: 'user', actions: ['read'] },
        { resource: 'project', actions: ['read'] },
        { resource: 'task', actions: ['read'] },
        { resource: 'report', actions: ['read'] },
      ],
      [UserRole.GUEST]: [
        { resource: 'project', actions: ['read'] },
        { resource: 'task', actions: ['read'] },
      ],
    }

    const userRolePermissions = rolePermissions[this.user.role] || []

    return userRolePermissions.some(permission => {
      if (permission.resource === '*' || permission.resource === resource) {
        return permission.actions.includes('*') || permission.actions.includes(action)
      }
      return false
    })
  }
}

export const usePermissions = (options: UsePermissionsOptions = {}): PermissionContext => {
  const { user = null, permissions = [], roles = [] } = options

  const permissionEngine = React.useMemo(
    () => new PermissionEngine(user, permissions),
    [user, permissions]
  )

  const hasPermission = React.useCallback(
    (resource: string, action: string, context?: any) => 
      permissionEngine.hasPermission(resource, action, context),
    [permissionEngine]
  )

  const hasRole = React.useCallback(
    (role: UserRole | UserRole[]) => permissionEngine.hasRole(role),
    [permissionEngine]
  )

  const hasAnyPermission = React.useCallback(
    (permissionChecks: Array<{ resource: string; action: string }>) =>
      permissionChecks.some(({ resource, action }) => 
        permissionEngine.hasPermission(resource, action)
      ),
    [permissionEngine]
  )

  const hasAllPermissions = React.useCallback(
    (permissionChecks: Array<{ resource: string; action: string }>) =>
      permissionChecks.every(({ resource, action }) => 
        permissionEngine.hasPermission(resource, action)
      ),
    [permissionEngine]
  )

  const canAccess = React.useCallback(
    (resource: string, action: string = 'read') =>
      permissionEngine.hasPermission(resource, action),
    [permissionEngine]
  )

  // Role checks
  const isAdmin = user?.role === UserRole.ADMIN
  const isManager = user?.role === UserRole.MANAGER
  const isMember = user?.role === UserRole.MEMBER
  const isGuest = user?.role === UserRole.GUEST

  return {
    user,
    permissions,
    roles,
    hasPermission,
    hasRole,
    hasAnyPermission,
    hasAllPermissions,
    canAccess,
    isAdmin,
    isManager,
    isMember,
    isGuest,
  }
}

// React Context for permissions
export const PermissionContext = React.createContext<PermissionContext | null>(null)

export interface PermissionProviderProps {
  children: React.ReactNode
  user?: User | null
  permissions?: Permission[]
  roles?: UserRole[]
}

export const PermissionProvider: React.FC<PermissionProviderProps> = ({
  children,
  user,
  permissions,
  roles,
}) => {
  const permissionContext = usePermissions({ user, permissions, roles })

  return (
    <PermissionContext.Provider value={permissionContext}>
      {children}
    </PermissionContext.Provider>
  )
}

// Hook to use permission context
export const usePermissionContext = (): PermissionContext => {
  const context = React.useContext(PermissionContext)
  if (!context) {
    throw new Error('usePermissionContext must be used within a PermissionProvider')
  }
  return context
}

export default usePermissions