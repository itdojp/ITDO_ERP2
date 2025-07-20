import { apiClient } from './api'
import { 
  Organization, 
  Department,
  OrganizationListResponse,
  DepartmentListResponse,
  CreateOrganizationRequest,
  UpdateOrganizationRequest,
  CreateDepartmentRequest,
  UpdateDepartmentRequest,
  OrganizationFilters,
  DepartmentFilters,
  OrganizationTreeNode,
  OrganizationPermission,
  CreateOrganizationPermissionRequest,
  UpdateOrganizationPermissionRequest,
  MoveDepartmentRequest,
  ManagerSearchResult,
  OrganizationSearchResult
} from '../types/organization'

class OrganizationApiService {
  private static instance: OrganizationApiService

  static getInstance(): OrganizationApiService {
    if (!OrganizationApiService.instance) {
      OrganizationApiService.instance = new OrganizationApiService()
    }
    return OrganizationApiService.instance
  }

  // Organization CRUD operations
  async getOrganizations(filters: OrganizationFilters = {}): Promise<OrganizationListResponse> {
    try {
      const params = new URLSearchParams()
      
      if (filters.search) params.append('search', filters.search)
      if (filters.industry) params.append('industry', filters.industry)
      if (filters.is_active !== undefined) params.append('is_active', filters.is_active.toString())
      if (filters.parent_id) params.append('parent_id', filters.parent_id.toString())

      const response = await apiClient.get<OrganizationListResponse>(`/organizations?${params.toString()}`)
      return response.data
    } catch (error) {
      console.error('Failed to fetch organizations:', error)
      throw error
    }
  }

  async getOrganizationById(id: number): Promise<Organization> {
    try {
      const response = await apiClient.get<Organization>(`/organizations/${id}`)
      return response.data
    } catch (error) {
      console.error(`Failed to fetch organization ${id}:`, error)
      throw error
    }
  }

  async createOrganization(data: CreateOrganizationRequest): Promise<Organization> {
    try {
      const response = await apiClient.post<Organization>('/organizations', data)
      return response.data
    } catch (error) {
      console.error('Failed to create organization:', error)
      throw error
    }
  }

  async updateOrganization(id: number, data: UpdateOrganizationRequest): Promise<Organization> {
    try {
      const response = await apiClient.put<Organization>(`/organizations/${id}`, data)
      return response.data
    } catch (error) {
      console.error(`Failed to update organization ${id}:`, error)
      throw error
    }
  }

  async deleteOrganization(id: number): Promise<void> {
    try {
      await apiClient.delete(`/organizations/${id}`)
    } catch (error) {
      console.error(`Failed to delete organization ${id}:`, error)
      throw error
    }
  }

  // Department CRUD operations
  async getDepartments(filters: DepartmentFilters = {}): Promise<DepartmentListResponse> {
    try {
      const params = new URLSearchParams()
      
      if (filters.search) params.append('search', filters.search)
      if (filters.type) params.append('type', filters.type)
      if (filters.organization_id) params.append('organization_id', filters.organization_id.toString())
      if (filters.is_active !== undefined) params.append('is_active', filters.is_active.toString())
      if (filters.has_manager !== undefined) params.append('has_manager', filters.has_manager.toString())

      const response = await apiClient.get<DepartmentListResponse>(`/departments?${params.toString()}`)
      return response.data
    } catch (error) {
      console.error('Failed to fetch departments:', error)
      throw error
    }
  }

  async getDepartmentById(id: number): Promise<Department> {
    try {
      const response = await apiClient.get<Department>(`/departments/${id}`)
      return response.data
    } catch (error) {
      console.error(`Failed to fetch department ${id}:`, error)
      throw error
    }
  }

  async createDepartment(data: CreateDepartmentRequest): Promise<Department> {
    try {
      const response = await apiClient.post<Department>('/departments', data)
      return response.data
    } catch (error) {
      console.error('Failed to create department:', error)
      throw error
    }
  }

  async updateDepartment(id: number, data: UpdateDepartmentRequest): Promise<Department> {
    try {
      const response = await apiClient.put<Department>(`/departments/${id}`, data)
      return response.data
    } catch (error) {
      console.error(`Failed to update department ${id}:`, error)
      throw error
    }
  }

  async deleteDepartment(id: number): Promise<void> {
    try {
      await apiClient.delete(`/departments/${id}`)
    } catch (error) {
      console.error(`Failed to delete department ${id}:`, error)
      throw error
    }
  }

  async moveDepartment(id: number, data: MoveDepartmentRequest): Promise<Department> {
    try {
      const response = await apiClient.patch<Department>(`/departments/${id}/move`, data)
      return response.data
    } catch (error) {
      console.error(`Failed to move department ${id}:`, error)
      throw error
    }
  }

  // Tree view operations
  async getOrganizationTree(): Promise<OrganizationTreeNode[]> {
    try {
      const response = await apiClient.get<OrganizationTreeNode[]>('/organizations/tree')
      return response.data
    } catch (error) {
      console.error('Failed to fetch organization tree:', error)
      // Return mock data for development
      return this.generateMockOrganizationTree()
    }
  }

  // Permission management
  async getOrganizationPermissions(organizationId: number): Promise<OrganizationPermission[]> {
    try {
      const response = await apiClient.get<OrganizationPermission[]>(`/organizations/${organizationId}/permissions`)
      return response.data
    } catch (error) {
      console.error(`Failed to fetch permissions for organization ${organizationId}:`, error)
      throw error
    }
  }

  async createOrganizationPermission(
    organizationId: number, 
    data: CreateOrganizationPermissionRequest
  ): Promise<OrganizationPermission> {
    try {
      const response = await apiClient.post<OrganizationPermission>(
        `/organizations/${organizationId}/permissions`, 
        data
      )
      return response.data
    } catch (error) {
      console.error(`Failed to create permission for organization ${organizationId}:`, error)
      throw error
    }
  }

  async updateOrganizationPermission(
    organizationId: number, 
    permissionId: number, 
    data: UpdateOrganizationPermissionRequest
  ): Promise<OrganizationPermission> {
    try {
      const response = await apiClient.put<OrganizationPermission>(
        `/organizations/${organizationId}/permissions/${permissionId}`, 
        data
      )
      return response.data
    } catch (error) {
      console.error(`Failed to update permission ${permissionId} for organization ${organizationId}:`, error)
      throw error
    }
  }

  async deleteOrganizationPermission(organizationId: number, permissionId: number): Promise<void> {
    try {
      await apiClient.delete(`/organizations/${organizationId}/permissions/${permissionId}`)
    } catch (error) {
      console.error(`Failed to delete permission ${permissionId} for organization ${organizationId}:`, error)
      throw error
    }
  }

  // Search operations
  async searchManagers(query: string): Promise<ManagerSearchResult[]> {
    try {
      const response = await apiClient.get<ManagerSearchResult[]>(`/users/search/managers?q=${encodeURIComponent(query)}`)
      return response.data
    } catch (error) {
      console.error('Failed to search managers:', error)
      // Return mock data for development
      return [
        { id: 1, full_name: 'John Doe', email: 'john.doe@example.com', current_role: 'Engineering Manager' },
        { id: 2, full_name: 'Jane Smith', email: 'jane.smith@example.com', current_role: 'Product Manager' }
      ]
    }
  }

  async searchOrganizations(query: string): Promise<OrganizationSearchResult[]> {
    try {
      const response = await apiClient.get<OrganizationSearchResult[]>(`/organizations/search?q=${encodeURIComponent(query)}`)
      return response.data
    } catch (error) {
      console.error('Failed to search organizations:', error)
      throw error
    }
  }

  async getManagers(): Promise<ManagerSearchResult[]> {
    try {
      const response = await apiClient.get<ManagerSearchResult[]>('/users/managers')
      return response.data
    } catch (error) {
      console.error('Failed to fetch managers:', error)
      // Return mock data for development
      return [
        { id: 1, full_name: 'John Doe', email: 'john.doe@example.com', current_role: 'Engineering Manager' },
        { id: 2, full_name: 'Jane Smith', email: 'jane.smith@example.com', current_role: 'Product Manager' },
        { id: 3, full_name: 'Mike Johnson', email: 'mike.johnson@example.com', current_role: 'Sales Director' },
        { id: 4, full_name: 'Sarah Wilson', email: 'sarah.wilson@example.com', current_role: 'Marketing Manager' }
      ]
    }
  }

  // Mock data generators for development
  generateMockOrganizationTree(): OrganizationTreeNode[] {
    return [
      {
        id: 1,
        name: 'ITDO Corporation',
        code: 'ITDO-CORP',
        type: 'organization',
        is_active: true,
        parent_id: undefined,
        expanded: false,
        user_count: 150,
        level: 0,
        children: [
          {
            id: 2,
            name: 'Engineering',
            code: 'ENG',
            type: 'department',
            is_active: true,
            parent_id: 1,
            expanded: false,
            user_count: 45,
            level: 1,
            children: [
              {
                id: 3,
                name: 'Frontend Team',
                code: 'FRONTEND',
                type: 'department',
                is_active: true,
                parent_id: 2,
                expanded: false,
                user_count: 12,
                level: 2,
                children: []
              },
              {
                id: 4,
                name: 'Backend Team',
                code: 'BACKEND',
                type: 'department',
                is_active: true,
                parent_id: 2,
                expanded: false,
                user_count: 15,
                level: 2,
                children: []
              }
            ]
          },
          {
            id: 5,
            name: 'Sales Division',
            code: 'SALES',
            type: 'department',
            is_active: true,
            parent_id: 1,
            expanded: false,
            user_count: 25,
            level: 1,
            children: []
          },
          {
            id: 6,
            name: 'Marketing',
            code: 'MKT',
            type: 'department',
            is_active: true,
            parent_id: 1,
            expanded: false,
            user_count: 18,
            level: 1,
            children: []
          }
        ]
      },
      {
        id: 7,
        name: 'Subsidiary Corp',
        code: 'SUB-CORP',
        type: 'organization',
        is_active: true,
        parent_id: undefined,
        expanded: false,
        user_count: 75,
        level: 0,
        children: [
          {
            id: 8,
            name: 'Operations',
            code: 'OPS',
            type: 'department',
            is_active: true,
            parent_id: 7,
            expanded: false,
            user_count: 30,
            level: 1,
            children: []
          }
        ]
      }
    ]
  }

  generateMockOrganizations(): Organization[] {
    return [
      {
        id: 1,
        name: 'ITDO Corporation',
        code: 'ITDO-CORP',
        description: 'Main technology corporation focused on innovative solutions',
        industry: 'technology',
        website: 'https://itdo.com',
        phone: '+1-555-0123',
        email: 'contact@itdo.com',
        is_active: true,
        address: {
          street: '123 Innovation Drive',
          city: 'Tech City',
          state: 'CA',
          postal_code: '94000',
          country: 'USA'
        },
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-07-19T00:00:00Z',
        user_count: 150,
        department_count: 8
      }
    ]
  }
}

// Export singleton instance
export const organizationApiService = OrganizationApiService.getInstance()

// Export React Query keys for cache management
export const organizationQueryKeys = {
  all: ['organizations'] as const,
  lists: () => [...organizationQueryKeys.all, 'list'] as const,
  list: (filters?: OrganizationFilters) => [...organizationQueryKeys.lists(), filters] as const,
  details: () => [...organizationQueryKeys.all, 'detail'] as const,
  detail: (id: number) => [...organizationQueryKeys.details(), id] as const,
  tree: () => [...organizationQueryKeys.all, 'tree'] as const,
  permissions: (id: number) => [...organizationQueryKeys.all, 'permissions', id] as const,
  departments: () => ['departments'] as const,
  departmentDetail: (id: number) => ['departments', id] as const,
}