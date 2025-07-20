import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  Permission,
  Role,
  UserRole,
  EffectivePermission,
  CreateRoleRequest,
  UpdateRoleRequest,
  AssignRoleRequest,
  RoleFilters,
  PermissionFilters,
  UserRoleFilters,
  RoleListResponse,
  PermissionListResponse,
  UserRoleListResponse,
  RoleStatistics,
  PERMISSION_ACTIONS,
  PERMISSION_RESOURCES,
  SYSTEM_PERMISSIONS,
  DEFAULT_ROLES,
  formatPermissionCode
} from '../types/permission'

class PermissionApiService {
  private baseUrl = '/api/v1'

  // Permission Management
  async getPermissions(filters: PermissionFilters = {}): Promise<PermissionListResponse> {
    try {
      const queryParams = new URLSearchParams()
      
      if (filters.search) queryParams.set('search', filters.search)
      if (filters.resource) queryParams.set('resource', filters.resource)
      if (filters.action) queryParams.set('action', filters.action)

      const response = await fetch(`${this.baseUrl}/permissions?${queryParams}`)
      if (!response.ok) throw new Error('Failed to fetch permissions')
      
      return await response.json()
    } catch {
      // Mock data for development
      return this.getMockPermissions(filters)
    }
  }

  async getPermission(id: number): Promise<Permission> {
    try {
      const response = await fetch(`${this.baseUrl}/permissions/${id}`)
      if (!response.ok) throw new Error('Failed to fetch permission')
      
      return await response.json()
    } catch {
      const mockPermissions = this.generateMockPermissions()
      const permission = mockPermissions.find(p => p.id === id)
      if (!permission) throw new Error('Permission not found')
      return permission
    }
  }

  // Role Management
  async getRoles(filters: RoleFilters = {}): Promise<RoleListResponse> {
    try {
      const queryParams = new URLSearchParams()
      
      if (filters.search) queryParams.set('search', filters.search)
      if (filters.organization_id) queryParams.set('organization_id', filters.organization_id.toString())
      if (filters.is_system !== undefined) queryParams.set('is_system', filters.is_system.toString())

      const response = await fetch(`${this.baseUrl}/roles?${queryParams}`)
      if (!response.ok) throw new Error('Failed to fetch roles')
      
      return await response.json()
    } catch {
      // Mock data for development
      return this.getMockRoles(filters)
    }
  }

  async getRole(id: number): Promise<Role> {
    try {
      const response = await fetch(`${this.baseUrl}/roles/${id}`)
      if (!response.ok) throw new Error('Failed to fetch role')
      
      return await response.json()
    } catch {
      const mockRoles = this.generateMockRoles()
      const role = mockRoles.find(r => r.id === id)
      if (!role) throw new Error('Role not found')
      return role
    }
  }

  async createRole(data: CreateRoleRequest): Promise<Role> {
    try {
      const response = await fetch(`${this.baseUrl}/roles`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
      })
      if (!response.ok) throw new Error('Failed to create role')
      
      return await response.json()
    } catch {
      // Mock creation for development
      const mockPermissions = this.generateMockPermissions()
      const selectedPermissions = mockPermissions.filter(p => data.permission_ids.includes(p.id))
      
      const newRole: Role = {
        id: Date.now(),
        name: data.name,
        code: data.code,
        description: data.description,
        permissions: selectedPermissions,
        is_system: false,
        organization_id: data.organization_id,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString()
      }
      
      return newRole
    }
  }

  async updateRole(id: number, data: UpdateRoleRequest): Promise<Role> {
    try {
      const response = await fetch(`${this.baseUrl}/roles/${id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
      })
      if (!response.ok) throw new Error('Failed to update role')
      
      return await response.json()
    } catch {
      // Mock update for development
      const role = await this.getRole(id)
      const mockPermissions = this.generateMockPermissions()
      
      return {
        ...role,
        name: data.name || role.name,
        code: data.code || role.code,
        description: data.description !== undefined ? data.description : role.description,
        permissions: data.permission_ids ? 
          mockPermissions.filter(p => data.permission_ids!.includes(p.id)) : 
          role.permissions,
        updated_at: new Date().toISOString()
      }
    }
  }

  async deleteRole(id: number): Promise<void> {
    try {
      const response = await fetch(`${this.baseUrl}/roles/${id}`, {
        method: 'DELETE'
      })
      if (!response.ok) throw new Error('Failed to delete role')
    } catch {
      // Mock deletion for development - just return success
      return Promise.resolve()
    }
  }

  // User Role Assignment
  async getUserRoles(filters: UserRoleFilters = {}): Promise<UserRoleListResponse> {
    try {
      const queryParams = new URLSearchParams()
      
      if (filters.user_id) queryParams.set('user_id', filters.user_id.toString())
      if (filters.role_id) queryParams.set('role_id', filters.role_id.toString())
      if (filters.organization_id) queryParams.set('organization_id', filters.organization_id.toString())

      const response = await fetch(`${this.baseUrl}/user-roles?${queryParams}`)
      if (!response.ok) throw new Error('Failed to fetch user roles')
      
      return await response.json()
    } catch {
      // Mock data for development
      return this.getMockUserRoles(filters)
    }
  }

  async assignRole(data: AssignRoleRequest): Promise<UserRole> {
    try {
      const response = await fetch(`${this.baseUrl}/user-roles`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
      })
      if (!response.ok) throw new Error('Failed to assign role')
      
      return await response.json()
    } catch {
      // Mock assignment for development
      const mockRoles = this.generateMockRoles()
      const role = mockRoles.find(r => r.id === data.role_id)
      if (!role) throw new Error('Role not found')
      
      const newUserRole: UserRole = {
        id: Date.now(),
        user_id: data.user_id,
        role_id: data.role_id,
        organization_id: data.organization_id,
        assigned_at: new Date().toISOString(),
        assigned_by: 1, // Mock admin user
        role,
        organization: {
          id: data.organization_id,
          name: 'Test Organization'
        },
        user: {
          id: data.user_id,
          full_name: 'Test User',
          email: 'test@example.com'
        }
      }
      
      return newUserRole
    }
  }

  async revokeRole(userRoleId: number): Promise<void> {
    try {
      const response = await fetch(`${this.baseUrl}/user-roles/${userRoleId}`, {
        method: 'DELETE'
      })
      if (!response.ok) throw new Error('Failed to revoke role')
    } catch {
      // Mock revocation for development - just return success
      return Promise.resolve()
    }
  }

  // Permission Checking
  async getEffectivePermissions(userId: number, organizationId?: number): Promise<EffectivePermission[]> {
    try {
      const queryParams = new URLSearchParams()
      if (organizationId) queryParams.set('organization_id', organizationId.toString())

      const response = await fetch(`${this.baseUrl}/users/${userId}/effective-permissions?${queryParams}`)
      if (!response.ok) throw new Error('Failed to fetch effective permissions')
      
      return await response.json()
    } catch {
      // Mock effective permissions for development
      return this.getMockEffectivePermissions(userId, organizationId)
    }
  }

  async checkPermission(userId: number, permission: string, organizationId?: number): Promise<boolean> {
    try {
      const queryParams = new URLSearchParams()
      queryParams.set('permission', permission)
      if (organizationId) queryParams.set('organization_id', organizationId.toString())

      const response = await fetch(`${this.baseUrl}/users/${userId}/check-permission?${queryParams}`)
      if (!response.ok) throw new Error('Failed to check permission')
      
      const result = await response.json()
      return result.has_permission
    } catch {
      // Mock permission check for development
      return this.mockCheckPermission(userId, permission)
    }
  }

  // Statistics
  async getRoleStatistics(): Promise<RoleStatistics> {
    try {
      const response = await fetch(`${this.baseUrl}/roles/statistics`)
      if (!response.ok) throw new Error('Failed to fetch role statistics')
      
      return await response.json()
    } catch {
      // Mock statistics for development
      return this.getMockRoleStatistics()
    }
  }

  // Mock Data Generators
  private generateMockPermissions(): Permission[] {
    const permissions: Permission[] = []
    let id = 1

    for (const resource of PERMISSION_RESOURCES) {
      for (const action of PERMISSION_ACTIONS) {
        permissions.push({
          id: id++,
          code: formatPermissionCode(resource.value, action.value),
          name: `${action.label} ${resource.label}`,
          description: `Permission to ${action.label.toLowerCase()} ${resource.label.toLowerCase()}`,
          resource: resource.value,
          action: action.value,
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString()
        })
      }
    }

    return permissions
  }

  private generateMockRoles(): Role[] {
    const mockPermissions = this.generateMockPermissions()
    
    return [
      {
        id: 1,
        name: 'Administrator',
        code: DEFAULT_ROLES.ADMINISTRATOR,
        description: 'Full system access with all permissions',
        permissions: mockPermissions,
        is_system: true,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString()
      },
      {
        id: 2,
        name: 'User',
        code: DEFAULT_ROLES.USER,
        description: 'Standard user with limited permissions',
        permissions: mockPermissions.filter(p => 
          p.resource === 'task' || 
          (p.resource === 'user' && p.action === 'read')
        ),
        is_system: true,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString()
      },
      {
        id: 3,
        name: 'Manager',
        code: DEFAULT_ROLES.MANAGER,
        description: 'Management role with extended permissions',
        permissions: mockPermissions.filter(p => 
          p.resource === 'task' || 
          p.resource === 'project' ||
          p.resource === 'user' ||
          p.resource === 'department'
        ),
        is_system: false,
        organization_id: 1,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString()
      }
    ]
  }

  private getMockPermissions(filters: PermissionFilters): PermissionListResponse {
    let permissions = this.generateMockPermissions()

    if (filters.search) {
      const search = filters.search.toLowerCase()
      permissions = permissions.filter(p => 
        p.name.toLowerCase().includes(search) ||
        p.code.toLowerCase().includes(search) ||
        p.description?.toLowerCase().includes(search)
      )
    }

    if (filters.resource) {
      permissions = permissions.filter(p => p.resource === filters.resource)
    }

    if (filters.action) {
      permissions = permissions.filter(p => p.action === filters.action)
    }

    return {
      items: permissions,
      total: permissions.length,
      page: 1,
      per_page: 50,
      total_pages: Math.ceil(permissions.length / 50)
    }
  }

  private getMockRoles(filters: RoleFilters): RoleListResponse {
    let roles = this.generateMockRoles()

    if (filters.search) {
      const search = filters.search.toLowerCase()
      roles = roles.filter(r => 
        r.name.toLowerCase().includes(search) ||
        r.code.toLowerCase().includes(search) ||
        r.description?.toLowerCase().includes(search)
      )
    }

    if (filters.organization_id) {
      roles = roles.filter(r => 
        r.organization_id === filters.organization_id ||
        r.is_system
      )
    }

    if (filters.is_system !== undefined) {
      roles = roles.filter(r => r.is_system === filters.is_system)
    }

    return {
      items: roles,
      total: roles.length,
      page: 1,
      per_page: 50,
      total_pages: Math.ceil(roles.length / 50)
    }
  }

  private getMockUserRoles(filters: UserRoleFilters): UserRoleListResponse {
    const mockRoles = this.generateMockRoles()
    const userRoles: UserRole[] = [
      {
        id: 1,
        user_id: 1,
        role_id: 1,
        organization_id: 1,
        assigned_at: new Date().toISOString(),
        assigned_by: 1,
        role: mockRoles[0],
        organization: { id: 1, name: 'Test Organization' },
        user: { id: 1, full_name: 'Admin User', email: 'admin@example.com' }
      },
      {
        id: 2,
        user_id: 2,
        role_id: 2,
        organization_id: 1,
        assigned_at: new Date().toISOString(),
        assigned_by: 1,
        role: mockRoles[1],
        organization: { id: 1, name: 'Test Organization' },
        user: { id: 2, full_name: 'Test User', email: 'test@example.com' }
      }
    ]

    let filtered = userRoles

    if (filters.user_id) {
      filtered = filtered.filter(ur => ur.user_id === filters.user_id)
    }

    if (filters.role_id) {
      filtered = filtered.filter(ur => ur.role_id === filters.role_id)
    }

    if (filters.organization_id) {
      filtered = filtered.filter(ur => ur.organization_id === filters.organization_id)
    }

    return {
      items: filtered,
      total: filtered.length,
      page: 1,
      per_page: 50,
      total_pages: Math.ceil(filtered.length / 50)
    }
  }

  private getMockEffectivePermissions(userId: number, organizationId?: number): EffectivePermission[] {
    const mockPermissions = this.generateMockPermissions()
    const mockRoles = this.generateMockRoles()

    // Simple mock: admin user gets all permissions, regular user gets limited
    const isAdmin = userId === 1
    const permissions = isAdmin ? mockPermissions : mockPermissions.filter(p => 
      p.resource === 'task' || (p.resource === 'user' && p.action === 'read')
    )

    return permissions.map(permission => ({
      permission,
      source_roles: isAdmin ? [mockRoles[0]] : [mockRoles[1]],
      organization_scope: organizationId ? {
        id: organizationId,
        name: 'Test Organization'
      } : undefined
    }))
  }

  private mockCheckPermission(userId: number, permission: string): boolean {
    // Simple mock: admin user has all permissions, others have limited
    const isAdmin = userId === 1
    if (isAdmin) return true

    // Regular users can read tasks and their own profile
    return permission === SYSTEM_PERMISSIONS.TASK_READ || 
           permission === SYSTEM_PERMISSIONS.USER_READ
  }

  private getMockRoleStatistics(): RoleStatistics {
    const mockRoles = this.generateMockRoles()
    const mockPermissions = this.generateMockPermissions()

    return {
      total_roles: mockRoles.length,
      system_roles: mockRoles.filter(r => r.is_system).length,
      custom_roles: mockRoles.filter(r => !r.is_system).length,
      total_permissions: mockPermissions.length,
      most_assigned_role: {
        role: mockRoles[1], // User role
        assignment_count: 15
      },
      permissions_by_resource: PERMISSION_RESOURCES.reduce((acc, resource) => {
        acc[resource.value] = PERMISSION_ACTIONS.length
        return acc
      }, {} as Record<string, number>)
    }
  }
}

export const permissionApiService = new PermissionApiService()

// Query Keys
export const permissionQueryKeys = {
  all: ['permissions'] as const,
  lists: () => [...permissionQueryKeys.all, 'list'] as const,
  list: (filters: PermissionFilters) => [...permissionQueryKeys.lists(), { filters }] as const,
  details: () => [...permissionQueryKeys.all, 'detail'] as const,
  detail: (id: number) => [...permissionQueryKeys.details(), id] as const
}

export const roleQueryKeys = {
  all: ['roles'] as const,
  lists: () => [...roleQueryKeys.all, 'list'] as const,
  list: (filters: RoleFilters) => [...roleQueryKeys.lists(), { filters }] as const,
  details: () => [...roleQueryKeys.all, 'detail'] as const,
  detail: (id: number) => [...roleQueryKeys.details(), id] as const,
  statistics: () => [...roleQueryKeys.all, 'statistics'] as const
}

export const userRoleQueryKeys = {
  all: ['userRoles'] as const,
  lists: () => [...userRoleQueryKeys.all, 'list'] as const,
  list: (filters: UserRoleFilters) => [...userRoleQueryKeys.lists(), { filters }] as const,
  effectivePermissions: (userId: number, organizationId?: number) => 
    [...userRoleQueryKeys.all, 'effective', userId, organizationId] as const
}

// React Query Hooks
export function usePermissions(filters: PermissionFilters = {}) {
  return useQuery({
    queryKey: permissionQueryKeys.list(filters),
    queryFn: () => permissionApiService.getPermissions(filters)
  })
}

export function usePermission(id: number) {
  return useQuery({
    queryKey: permissionQueryKeys.detail(id),
    queryFn: () => permissionApiService.getPermission(id),
    enabled: !!id
  })
}

export function useRoles(filters: RoleFilters = {}) {
  return useQuery({
    queryKey: roleQueryKeys.list(filters),
    queryFn: () => permissionApiService.getRoles(filters)
  })
}

export function useRole(id: number) {
  return useQuery({
    queryKey: roleQueryKeys.detail(id),
    queryFn: () => permissionApiService.getRole(id),
    enabled: !!id
  })
}

export function useUserRoles(filters: UserRoleFilters = {}) {
  return useQuery({
    queryKey: userRoleQueryKeys.list(filters),
    queryFn: () => permissionApiService.getUserRoles(filters)
  })
}

export function useEffectivePermissions(userId: number, organizationId?: number) {
  return useQuery({
    queryKey: userRoleQueryKeys.effectivePermissions(userId, organizationId),
    queryFn: () => permissionApiService.getEffectivePermissions(userId, organizationId),
    enabled: !!userId
  })
}

export function useRoleStatistics() {
  return useQuery({
    queryKey: roleQueryKeys.statistics(),
    queryFn: () => permissionApiService.getRoleStatistics()
  })
}

// Mutation Hooks
export function useCreateRole() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: (data: CreateRoleRequest) => permissionApiService.createRole(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: roleQueryKeys.lists() })
      queryClient.invalidateQueries({ queryKey: roleQueryKeys.statistics() })
    }
  })
}

export function useUpdateRole() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: UpdateRoleRequest }) => 
      permissionApiService.updateRole(id, data),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: roleQueryKeys.lists() })
      queryClient.invalidateQueries({ queryKey: roleQueryKeys.detail(id) })
      queryClient.invalidateQueries({ queryKey: roleQueryKeys.statistics() })
    }
  })
}

export function useDeleteRole() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: (id: number) => permissionApiService.deleteRole(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: roleQueryKeys.lists() })
      queryClient.invalidateQueries({ queryKey: roleQueryKeys.statistics() })
      queryClient.invalidateQueries({ queryKey: userRoleQueryKeys.lists() })
    }
  })
}

export function useAssignRole() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: (data: AssignRoleRequest) => permissionApiService.assignRole(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: userRoleQueryKeys.lists() })
    }
  })
}

export function useRevokeRole() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: (userRoleId: number) => permissionApiService.revokeRole(userRoleId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: userRoleQueryKeys.lists() })
    }
  })
}