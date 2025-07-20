import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  Project,
  CreateProjectRequest,
  UpdateProjectRequest,
  ProjectFilters,
  ProjectListResponse,
  ProjectStatistics,
  ProjectMember
} from '../types/task'

class ProjectApiService {
  private baseUrl = '/api/v1'

  // Project Management
  async getProjects(filters: ProjectFilters = {}): Promise<ProjectListResponse> {
    try {
      const queryParams = new URLSearchParams()
      
      if (filters.search) queryParams.set('search', filters.search)
      if (filters.status) queryParams.set('status', filters.status)
      if (filters.owner_id) queryParams.set('owner_id', filters.owner_id.toString())

      const response = await fetch(`${this.baseUrl}/projects?${queryParams}`)
      if (!response.ok) throw new Error('Failed to fetch projects')
      
      return await response.json()
    } catch {
      // Mock data for development
      return this.getMockProjects(filters)
    }
  }

  async getProject(id: number): Promise<Project> {
    try {
      const response = await fetch(`${this.baseUrl}/projects/${id}`)
      if (!response.ok) throw new Error('Failed to fetch project')
      
      return await response.json()
    } catch {
      const mockProjects = this.generateMockProjects()
      const project = mockProjects.find(p => p.id === id)
      if (!project) throw new Error('Project not found')
      return project
    }
  }

  async createProject(data: CreateProjectRequest): Promise<Project> {
    try {
      const response = await fetch(`${this.baseUrl}/projects`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
      })
      if (!response.ok) throw new Error('Failed to create project')
      
      return await response.json()
    } catch {
      // Mock creation for development
      const newProject: Project = {
        id: Date.now(),
        name: data.name,
        code: data.code,
        description: data.description,
        owner_id: 1, // Mock current user
        status: 'ACTIVE',
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        owner: {
          id: 1,
          full_name: 'Current User',
          email: 'current@example.com',
          is_active: true,
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
          organizations: [],
          departments: [],
          roles: []
        },
        task_count: 0
      }
      
      return newProject
    }
  }

  async updateProject(id: number, data: UpdateProjectRequest): Promise<Project> {
    try {
      const response = await fetch(`${this.baseUrl}/projects/${id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
      })
      if (!response.ok) throw new Error('Failed to update project')
      
      return await response.json()
    } catch {
      // Mock update for development
      const project = await this.getProject(id)
      
      return {
        ...project,
        name: data.name || project.name,
        code: data.code || project.code,
        description: data.description !== undefined ? data.description : project.description,
        status: data.status || project.status,
        updated_at: new Date().toISOString()
      }
    }
  }

  async deleteProject(id: number): Promise<void> {
    try {
      const response = await fetch(`${this.baseUrl}/projects/${id}`, {
        method: 'DELETE'
      })
      if (!response.ok) throw new Error('Failed to delete project')
    } catch {
      // Mock deletion for development - just return success
      return Promise.resolve()
    }
  }

  // Project Members
  async getProjectMembers(projectId: number): Promise<ProjectMember[]> {
    try {
      const response = await fetch(`${this.baseUrl}/projects/${projectId}/members`)
      if (!response.ok) throw new Error('Failed to fetch project members')
      
      return await response.json()
    } catch {
      // Mock project members for development
      return this.getMockProjectMembers(projectId)
    }
  }

  async addProjectMember(projectId: number, userId: number, role: ProjectMember['role']): Promise<ProjectMember> {
    try {
      const response = await fetch(`${this.baseUrl}/projects/${projectId}/members`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: userId, role })
      })
      if (!response.ok) throw new Error('Failed to add project member')
      
      return await response.json()
    } catch {
      // Mock member addition for development
      const mockMember: ProjectMember = {
        project_id: projectId,
        user_id: userId,
        role,
        added_by: 1,
        added_at: new Date().toISOString(),
        user: {
          id: userId,
          full_name: 'Test User',
          email: 'test@example.com',
          is_active: true,
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
          organizations: [],
          departments: [],
          roles: []
        }
      }
      
      return mockMember
    }
  }

  async removeProjectMember(projectId: number, userId: number): Promise<void> {
    try {
      const response = await fetch(`${this.baseUrl}/projects/${projectId}/members/${userId}`, {
        method: 'DELETE'
      })
      if (!response.ok) throw new Error('Failed to remove project member')
    } catch {
      // Mock removal for development - just return success
      return Promise.resolve()
    }
  }

  // Project Statistics
  async getProjectStatistics(): Promise<ProjectStatistics> {
    try {
      const response = await fetch(`${this.baseUrl}/projects/statistics`)
      if (!response.ok) throw new Error('Failed to fetch project statistics')
      
      return await response.json()
    } catch {
      // Mock statistics for development
      return this.getMockProjectStatistics()
    }
  }

  async getProjectStatisticsById(projectId: number): Promise<ProjectStatistics> {
    try {
      const response = await fetch(`${this.baseUrl}/projects/${projectId}/statistics`)
      if (!response.ok) throw new Error('Failed to fetch project statistics')
      
      return await response.json()
    } catch {
      // Mock project-specific statistics for development
      return {
        total_projects: 1,
        active_projects: 1,
        completed_projects: 0,
        total_tasks: 5,
        completion_rate: 60,
        my_projects: 1
      }
    }
  }

  // Mock Data Generators
  private generateMockProjects(): Project[] {
    return [
      {
        id: 1,
        name: 'ERP System Development',
        code: 'ERP_DEV',
        description: 'Complete ERP system with user management, tasks, and permissions',
        owner_id: 1,
        status: 'ACTIVE',
        created_at: '2024-01-15T09:00:00Z',
        updated_at: '2024-01-20T14:30:00Z',
        owner: {
          id: 1,
          full_name: 'Admin User',
          email: 'admin@example.com',
          is_active: true,
          created_at: '2024-01-01T00:00:00Z',
          updated_at: '2024-01-01T00:00:00Z',
          organizations: [],
          departments: [],
          roles: []
        },
        task_count: 12
      },
      {
        id: 2,
        name: 'Security Audit',
        code: 'SEC_AUDIT',
        description: 'Security assessment and vulnerability testing',
        owner_id: 2,
        status: 'ACTIVE',
        created_at: '2024-02-01T10:00:00Z',
        updated_at: '2024-02-05T16:45:00Z',
        owner: {
          id: 2,
          full_name: 'Security Manager',
          email: 'security@example.com',
          is_active: true,
          created_at: '2024-01-01T00:00:00Z',
          updated_at: '2024-01-01T00:00:00Z',
          organizations: [],
          departments: [],
          roles: []
        },
        task_count: 8
      },
      {
        id: 3,
        name: 'Database Migration',
        code: 'DB_MIGRATE',
        description: 'Migration from legacy database to new system',
        owner_id: 1,
        status: 'COMPLETED',
        created_at: '2023-12-01T08:00:00Z',
        updated_at: '2024-01-15T12:00:00Z',
        owner: {
          id: 1,
          full_name: 'Admin User',
          email: 'admin@example.com',
          is_active: true,
          created_at: '2024-01-01T00:00:00Z',
          updated_at: '2024-01-01T00:00:00Z',
          organizations: [],
          departments: [],
          roles: []
        },
        task_count: 25
      },
      {
        id: 4,
        name: 'User Training Program',
        code: 'USER_TRAINING',
        description: 'Training program for new system rollout',
        owner_id: 3,
        status: 'ACTIVE',
        created_at: '2024-02-10T09:30:00Z',
        updated_at: '2024-02-15T11:20:00Z',
        owner: {
          id: 3,
          full_name: 'Training Coordinator',
          email: 'training@example.com',
          is_active: true,
          created_at: '2024-01-01T00:00:00Z',
          updated_at: '2024-01-01T00:00:00Z',
          organizations: [],
          departments: [],
          roles: []
        },
        task_count: 6
      }
    ]
  }

  private getMockProjects(filters: ProjectFilters): ProjectListResponse {
    let projects = this.generateMockProjects()

    if (filters.search) {
      const search = filters.search.toLowerCase()
      projects = projects.filter(p => 
        p.name.toLowerCase().includes(search) ||
        p.code.toLowerCase().includes(search) ||
        p.description?.toLowerCase().includes(search)
      )
    }

    if (filters.status) {
      projects = projects.filter(p => p.status === filters.status)
    }

    if (filters.owner_id) {
      projects = projects.filter(p => p.owner_id === filters.owner_id)
    }

    return {
      items: projects,
      total: projects.length,
      page: 1,
      limit: 50
    }
  }

  private getMockProjectMembers(projectId: number): ProjectMember[] {
    return [
      {
        project_id: projectId,
        user_id: 1,
        role: 'OWNER',
        added_by: 1,
        added_at: '2024-01-01T00:00:00Z',
        user: {
          id: 1,
          full_name: 'Admin User',
          email: 'admin@example.com',
          is_active: true,
          created_at: '2024-01-01T00:00:00Z',
          updated_at: '2024-01-01T00:00:00Z',
          organizations: [],
          departments: [],
          roles: []
        }
      },
      {
        project_id: projectId,
        user_id: 2,
        role: 'MEMBER',
        added_by: 1,
        added_at: '2024-01-02T00:00:00Z',
        user: {
          id: 2,
          full_name: 'Team Member',
          email: 'member@example.com',
          is_active: true,
          created_at: '2024-01-01T00:00:00Z',
          updated_at: '2024-01-01T00:00:00Z',
          organizations: [],
          departments: [],
          roles: []
        }
      }
    ]
  }

  private getMockProjectStatistics(): ProjectStatistics {
    return {
      total_projects: 4,
      active_projects: 3,
      completed_projects: 1,
      total_tasks: 51,
      completion_rate: 68,
      my_projects: 2
    }
  }
}

export const projectApiService = new ProjectApiService()

// Query Keys
export const projectQueryKeys = {
  all: ['projects'] as const,
  lists: () => [...projectQueryKeys.all, 'list'] as const,
  list: (filters: ProjectFilters) => [...projectQueryKeys.lists(), { filters }] as const,
  details: () => [...projectQueryKeys.all, 'detail'] as const,
  detail: (id: number) => [...projectQueryKeys.details(), id] as const,
  statistics: () => [...projectQueryKeys.all, 'statistics'] as const,
  projectStatistics: (id: number) => [...projectQueryKeys.all, 'project-statistics', id] as const,
  members: (projectId: number) => [...projectQueryKeys.all, 'members', projectId] as const
}

// React Query Hooks
export function useProjects(filters: ProjectFilters = {}) {
  return useQuery({
    queryKey: projectQueryKeys.list(filters),
    queryFn: () => projectApiService.getProjects(filters)
  })
}

export function useProject(id: number) {
  return useQuery({
    queryKey: projectQueryKeys.detail(id),
    queryFn: () => projectApiService.getProject(id),
    enabled: !!id
  })
}

export function useProjectMembers(projectId: number) {
  return useQuery({
    queryKey: projectQueryKeys.members(projectId),
    queryFn: () => projectApiService.getProjectMembers(projectId),
    enabled: !!projectId
  })
}

export function useProjectStatistics() {
  return useQuery({
    queryKey: projectQueryKeys.statistics(),
    queryFn: () => projectApiService.getProjectStatistics()
  })
}

export function useProjectStatisticsById(projectId: number) {
  return useQuery({
    queryKey: projectQueryKeys.projectStatistics(projectId),
    queryFn: () => projectApiService.getProjectStatisticsById(projectId),
    enabled: !!projectId
  })
}

// Mutation Hooks
export function useCreateProject() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: (data: CreateProjectRequest) => projectApiService.createProject(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: projectQueryKeys.lists() })
      queryClient.invalidateQueries({ queryKey: projectQueryKeys.statistics() })
    }
  })
}

export function useUpdateProject() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: UpdateProjectRequest }) => 
      projectApiService.updateProject(id, data),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: projectQueryKeys.lists() })
      queryClient.invalidateQueries({ queryKey: projectQueryKeys.detail(id) })
      queryClient.invalidateQueries({ queryKey: projectQueryKeys.statistics() })
    }
  })
}

export function useDeleteProject() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: (id: number) => projectApiService.deleteProject(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: projectQueryKeys.lists() })
      queryClient.invalidateQueries({ queryKey: projectQueryKeys.statistics() })
    }
  })
}

export function useAddProjectMember() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: ({ projectId, userId, role }: { projectId: number; userId: number; role: ProjectMember['role'] }) => 
      projectApiService.addProjectMember(projectId, userId, role),
    onSuccess: (_, { projectId }) => {
      queryClient.invalidateQueries({ queryKey: projectQueryKeys.members(projectId) })
    }
  })
}

export function useRemoveProjectMember() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: ({ projectId, userId }: { projectId: number; userId: number }) => 
      projectApiService.removeProjectMember(projectId, userId),
    onSuccess: (_, { projectId }) => {
      queryClient.invalidateQueries({ queryKey: projectQueryKeys.members(projectId) })
    }
  })
}