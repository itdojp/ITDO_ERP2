import { apiClient } from './api'
import { 
  User, 
  UserListResponse, 
  CreateUserRequest, 
  UpdateUserRequest, 
  UserFilters, 
  PaginationParams,
  BulkActionRequest 
} from '../types/user'

class UserApiService {
  private static instance: UserApiService

  static getInstance(): UserApiService {
    if (!UserApiService.instance) {
      UserApiService.instance = new UserApiService()
    }
    return UserApiService.instance
  }

  async getUsers(
    filters: UserFilters = {}, 
    pagination: PaginationParams = { page: 1, limit: 10 }
  ): Promise<UserListResponse> {
    try {
      const params = new URLSearchParams()
      
      // Add pagination
      params.append('page', pagination.page.toString())
      params.append('limit', pagination.limit.toString())
      
      // Add filters
      if (filters.search) params.append('search', filters.search)
      if (filters.role) params.append('role', filters.role)
      if (filters.status) params.append('status', filters.status)
      if (filters.organization_id) params.append('organization_id', filters.organization_id.toString())
      if (filters.department_id) params.append('department_id', filters.department_id.toString())

      const response = await apiClient.get<UserListResponse>(`/users?${params.toString()}`)
      return response.data
    } catch (error) {
      console.error('Failed to fetch users:', error)
      throw error
    }
  }

  async getUserById(id: number): Promise<User> {
    try {
      const response = await apiClient.get<User>(`/users/${id}`)
      return response.data
    } catch (error) {
      console.error(`Failed to fetch user ${id}:`, error)
      throw error
    }
  }

  async createUser(userData: CreateUserRequest): Promise<User> {
    try {
      // Validate password confirmation
      if (userData.password !== userData.confirm_password) {
        throw new Error('Passwords do not match')
      }

      // Remove confirm_password before sending to API
      const { confirm_password, ...apiData } = userData

      const response = await apiClient.post<User>('/users', apiData)
      return response.data
    } catch (error) {
      console.error('Failed to create user:', error)
      throw error
    }
  }

  async updateUser(id: number, userData: UpdateUserRequest): Promise<User> {
    try {
      const response = await apiClient.put<User>(`/users/${id}`, userData)
      return response.data
    } catch (error) {
      console.error(`Failed to update user ${id}:`, error)
      throw error
    }
  }

  async deleteUser(id: number): Promise<void> {
    try {
      await apiClient.delete(`/users/${id}`)
    } catch (error) {
      console.error(`Failed to delete user ${id}:`, error)
      throw error
    }
  }

  async bulkAction(request: BulkActionRequest): Promise<{ success: number; failed: number; message: string }> {
    try {
      const response = await apiClient.post<{ success: number; failed: number; message: string }>(
        '/users/bulk-action', 
        request
      )
      return response.data
    } catch (error) {
      console.error('Failed to perform bulk action:', error)
      throw error
    }
  }

  async activateUser(id: number): Promise<User> {
    try {
      const response = await apiClient.patch<User>(`/users/${id}/activate`)
      return response.data
    } catch (error) {
      console.error(`Failed to activate user ${id}:`, error)
      throw error
    }
  }

  async deactivateUser(id: number): Promise<User> {
    try {
      const response = await apiClient.patch<User>(`/users/${id}/deactivate`)
      return response.data
    } catch (error) {
      console.error(`Failed to deactivate user ${id}:`, error)
      throw error
    }
  }

  async getUserRoles(): Promise<{ id: string; name: string }[]> {
    try {
      const response = await apiClient.get<{ id: string; name: string }[]>('/users/roles')
      return response.data
    } catch (error) {
      console.error('Failed to fetch user roles:', error)
      // Return mock data for development
      return [
        { id: 'admin', name: 'Administrator' },
        { id: 'user', name: 'User' },
        { id: 'manager', name: 'Manager' },
        { id: 'viewer', name: 'Viewer' }
      ]
    }
  }

  // Mock data generator for development/testing
  generateMockUsers(count: number = 50): User[] {
    const mockUsers: User[] = []
    const roles = ['admin', 'user', 'manager', 'viewer']
    
    for (let i = 1; i <= count; i++) {
      mockUsers.push({
        id: i,
        email: `user${i}@example.com`,
        full_name: `User ${i}`,
        phone: `+1234567${i.toString().padStart(3, '0')}`,
        profile_image_url: undefined,
        bio: `Bio for user ${i}`,
        location: `Location ${i}`,
        website: `https://user${i}.example.com`,
        is_active: Math.random() > 0.2, // 80% active
        created_at: new Date(Date.now() - Math.random() * 365 * 24 * 60 * 60 * 1000).toISOString(),
        updated_at: new Date().toISOString(),
        last_login_at: Math.random() > 0.3 ? new Date(Date.now() - Math.random() * 30 * 24 * 60 * 60 * 1000).toISOString() : undefined,
        organizations: [],
        departments: [],
        roles: [{
          role: {
            id: i % roles.length + 1,
            code: roles[i % roles.length],
            name: roles[i % roles.length].charAt(0).toUpperCase() + roles[i % roles.length].slice(1)
          },
          organization: {
            id: 1,
            code: 'MAIN',
            name: 'Main Organization'
          },
          assigned_at: new Date().toISOString()
        }]
      })
    }
    
    return mockUsers
  }

  // Development mode: return mock data when API is not available
  async getUsersMock(
    filters: UserFilters = {}, 
    pagination: PaginationParams = { page: 1, limit: 10 }
  ): Promise<UserListResponse> {
    console.warn('Using mock user data - API not available')
    
    let users = this.generateMockUsers()
    
    // Apply filters
    if (filters.search) {
      const search = filters.search.toLowerCase()
      users = users.filter(user => 
        user.full_name.toLowerCase().includes(search) ||
        user.email.toLowerCase().includes(search)
      )
    }
    
    if (filters.role) {
      users = users.filter(user => 
        user.roles.some(role => role.role.code === filters.role)
      )
    }
    
    if (filters.status) {
      users = users.filter(user => 
        filters.status === 'active' ? user.is_active : !user.is_active
      )
    }
    
    // Apply pagination
    const total = users.length
    const startIndex = (pagination.page - 1) * pagination.limit
    const endIndex = startIndex + pagination.limit
    const paginatedUsers = users.slice(startIndex, endIndex)
    
    return {
      items: paginatedUsers,
      total,
      page: pagination.page,
      limit: pagination.limit
    }
  }
}

// Export singleton instance
export const userApiService = UserApiService.getInstance()

// Export React Query keys for cache management
export const userQueryKeys = {
  all: ['users'] as const,
  lists: () => [...userQueryKeys.all, 'list'] as const,
  list: (filters: UserFilters, pagination: PaginationParams) => 
    [...userQueryKeys.lists(), filters, pagination] as const,
  details: () => [...userQueryKeys.all, 'detail'] as const,
  detail: (id: number) => [...userQueryKeys.details(), id] as const,
  roles: () => [...userQueryKeys.all, 'roles'] as const,
}