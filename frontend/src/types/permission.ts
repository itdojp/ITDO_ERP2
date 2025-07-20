export type PermissionAction = 'create' | 'read' | 'update' | 'delete'
export type PermissionResource = 'user' | 'organization' | 'department' | 'task' | 'project' | 'role' | 'permission'

export interface Permission {
  id: number
  code: string
  name: string
  description?: string
  resource: PermissionResource
  action: PermissionAction
  created_at: string
  updated_at: string
}

export interface Role {
  id: number
  name: string
  code: string
  description?: string
  permissions: Permission[]
  is_system?: boolean
  organization_id?: number
  created_at: string
  updated_at: string
}

export interface UserRole {
  id: number
  user_id: number
  role_id: number
  organization_id: number
  assigned_at: string
  assigned_by: number
  role: Role
  organization: {
    id: number
    name: string
  }
  user: {
    id: number
    full_name: string
    email: string
  }
}

export interface EffectivePermission {
  permission: Permission
  source_roles: Role[]
  organization_scope?: {
    id: number
    name: string
  }
}

export interface CreateRoleRequest {
  name: string
  code: string
  description?: string
  permission_ids: number[]
  organization_id?: number
}

export interface UpdateRoleRequest {
  name?: string
  code?: string
  description?: string
  permission_ids?: number[]
}

export interface AssignRoleRequest {
  user_id: number
  role_id: number
  organization_id: number
}

export interface RoleFilters {
  search?: string
  organization_id?: number
  is_system?: boolean
}

export interface PermissionFilters {
  search?: string
  resource?: PermissionResource
  action?: PermissionAction
}

export interface UserRoleFilters {
  user_id?: number
  role_id?: number
  organization_id?: number
}

export interface RoleListResponse {
  items: Role[]
  total: number
  page: number
  per_page: number
  total_pages: number
}

export interface PermissionListResponse {
  items: Permission[]
  total: number
  page: number
  per_page: number
  total_pages: number
}

export interface UserRoleListResponse {
  items: UserRole[]
  total: number
  page: number
  per_page: number
  total_pages: number
}

export interface RoleStatistics {
  total_roles: number
  system_roles: number
  custom_roles: number
  total_permissions: number
  most_assigned_role: {
    role: Role
    assignment_count: number
  }
  permissions_by_resource: Record<PermissionResource, number>
}

export const PERMISSION_ACTIONS: Array<{ value: PermissionAction; label: string }> = [
  { value: 'create', label: 'Create' },
  { value: 'read', label: 'Read' },
  { value: 'update', label: 'Update' },
  { value: 'delete', label: 'Delete' }
]

export const PERMISSION_RESOURCES: Array<{ value: PermissionResource; label: string }> = [
  { value: 'user', label: 'User Management' },
  { value: 'organization', label: 'Organization Management' },
  { value: 'department', label: 'Department Management' },
  { value: 'task', label: 'Task Management' },
  { value: 'project', label: 'Project Management' },
  { value: 'role', label: 'Role Management' },
  { value: 'permission', label: 'Permission Management' }
]

export const SYSTEM_PERMISSIONS = {
  USER_READ: 'user:read',
  USER_WRITE: 'user:write',
  USER_DELETE: 'user:delete',
  ORGANIZATION_READ: 'organization:read',
  ORGANIZATION_WRITE: 'organization:write',
  ORGANIZATION_DELETE: 'organization:delete',
  DEPARTMENT_READ: 'department:read',
  DEPARTMENT_WRITE: 'department:write',
  DEPARTMENT_DELETE: 'department:delete',
  TASK_READ: 'task:read',
  TASK_WRITE: 'task:write',
  TASK_DELETE: 'task:delete',
  PROJECT_READ: 'project:read',
  PROJECT_WRITE: 'project:write',
  PROJECT_DELETE: 'project:delete',
  ROLE_READ: 'role:read',
  ROLE_WRITE: 'role:write',
  ROLE_DELETE: 'role:delete',
  PERMISSION_READ: 'permission:read',
  PERMISSION_WRITE: 'permission:write',
  PERMISSION_DELETE: 'permission:delete'
} as const

export const DEFAULT_ROLES = {
  ADMINISTRATOR: 'administrator',
  USER: 'user',
  MANAGER: 'manager',
  VIEWER: 'viewer'
} as const

export function formatPermissionCode(resource: PermissionResource, action: PermissionAction): string {
  return `${resource}:${action}`
}

export function parsePermissionCode(code: string): { resource: PermissionResource; action: PermissionAction } | null {
  const parts = code.split(':')
  if (parts.length !== 2) return null
  
  const [resource, action] = parts
  if (!PERMISSION_RESOURCES.some(r => r.value === resource) || 
      !PERMISSION_ACTIONS.some(a => a.value === action)) {
    return null
  }
  
  return {
    resource: resource as PermissionResource,
    action: action as PermissionAction
  }
}

export function getPermissionDisplayName(permission: Permission): string {
  const resourceLabel = PERMISSION_RESOURCES.find(r => r.value === permission.resource)?.label || permission.resource
  const actionLabel = PERMISSION_ACTIONS.find(a => a.value === permission.action)?.label || permission.action
  return `${actionLabel} ${resourceLabel}`
}

export function hasPermission(userPermissions: Permission[], requiredPermission: string): boolean {
  return userPermissions.some(permission => 
    formatPermissionCode(permission.resource, permission.action) === requiredPermission
  )
}

export function filterPermissionsByResource(permissions: Permission[], resource: PermissionResource): Permission[] {
  return permissions.filter(permission => permission.resource === resource)
}

export function groupPermissionsByResource(permissions: Permission[]): Record<PermissionResource, Permission[]> {
  return permissions.reduce((groups, permission) => {
    if (!groups[permission.resource]) {
      groups[permission.resource] = []
    }
    groups[permission.resource].push(permission)
    return groups
  }, {} as Record<PermissionResource, Permission[]>)
}

export interface PermissionCheckContext {
  user_id: number
  organization_id?: number
  resource_id?: number
}

export interface PermissionCheck {
  context: PermissionCheckContext
  required_permission: string
  has_permission: boolean
  granted_by?: Role[]
}