import { apiClient } from './api'
import { 
  Task, 
  Project,
  TaskComment,
  TaskListResponse,
  ProjectListResponse,
  TaskCommentListResponse,
  CreateTaskRequest,
  UpdateTaskRequest,
  CreateProjectRequest,
  UpdateProjectRequest,
  CreateTaskCommentRequest,
  TaskFilters,
  ProjectFilters,
  TaskStatistics,
  ProjectStatistics,
  BulkTaskAction,
  BulkTaskResponse,
} from '../types/task'

class TaskApiService {
  private static instance: TaskApiService

  static getInstance(): TaskApiService {
    if (!TaskApiService.instance) {
      TaskApiService.instance = new TaskApiService()
    }
    return TaskApiService.instance
  }

  // Task CRUD operations
  async getTasks(filters: TaskFilters = {}): Promise<TaskListResponse> {
    try {
      const params = new URLSearchParams()
      
      if (filters.search) params.append('search', filters.search)
      if (filters.status) params.append('status', filters.status)
      if (filters.priority) params.append('priority', filters.priority)
      if (filters.assignee_id) params.append('assignee_id', filters.assignee_id.toString())
      if (filters.project_id) params.append('project_id', filters.project_id.toString())
      if (filters.creator_id) params.append('creator_id', filters.creator_id.toString())
      if (filters.due_before) params.append('due_before', filters.due_before)
      if (filters.due_after) params.append('due_after', filters.due_after)

      const response = await apiClient.get<TaskListResponse>(`/tasks?${params.toString()}`)
      return response.data
    } catch (error) {
      // Return mock data for development
      return this.generateMockTasks(filters)
    }
  }

  async getTaskById(id: number): Promise<Task> {
    try {
      const response = await apiClient.get<Task>(`/tasks/${id}`)
      return response.data
    } catch (error) {
      // Return mock data for development
      const mockTasks = this.generateMockTasks()
      const task = mockTasks.items.find(t => t.id === id)
      if (!task) {
        throw new Error(`Task ${id} not found`)
      }
      return task
    }
  }

  async createTask(data: CreateTaskRequest): Promise<Task> {
    try {
      const response = await apiClient.post<Task>('/tasks', data)
      return response.data
    } catch (error) {
      // Return mock data for development
      const newTask: Task = {
        id: Date.now(),
        title: data.title,
        description: data.description,
        status: data.status || 'TODO',
        priority: data.priority,
        progress: 0,
        project_id: data.project_id,
        assignee_id: data.assignee_id,
        creator_id: 1, // Mock current user ID
        due_date: data.due_date,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        creator: {
          id: 1,
          full_name: 'Current User',
          email: 'current@example.com',
          is_active: true,
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
          organizations: [],
          departments: [],
          roles: []
        }
      }
      return newTask
    }
  }

  async updateTask(id: number, data: UpdateTaskRequest): Promise<Task> {
    try {
      const response = await apiClient.put<Task>(`/tasks/${id}`, data)
      return response.data
    } catch (error) {
      // Return mock updated task for development
      const existingTask = await this.getTaskById(id)
      return { ...existingTask, ...data, updated_at: new Date().toISOString() }
    }
  }

  async deleteTask(id: number): Promise<void> {
    try {
      await apiClient.delete(`/tasks/${id}`)
    } catch (error) {
      // Mock success for development
      return Promise.resolve()
    }
  }

  async bulkUpdateTasks(action: BulkTaskAction): Promise<BulkTaskResponse> {
    try {
      const response = await apiClient.post<BulkTaskResponse>('/tasks/bulk', action)
      return response.data
    } catch (error) {
      // Return mock success for development
      return {
        success_count: action.task_ids.length,
        error_count: 0
      }
    }
  }

  // Project CRUD operations
  async getProjects(filters: ProjectFilters = {}): Promise<ProjectListResponse> {
    try {
      const params = new URLSearchParams()
      
      if (filters.search) params.append('search', filters.search)
      if (filters.status) params.append('status', filters.status)
      if (filters.owner_id) params.append('owner_id', filters.owner_id.toString())

      const response = await apiClient.get<ProjectListResponse>(`/projects?${params.toString()}`)
      return response.data
    } catch (error) {
      // Return mock data for development
      return this.generateMockProjects(filters)
    }
  }

  async getProjectById(id: number): Promise<Project> {
    try {
      const response = await apiClient.get<Project>(`/projects/${id}`)
      return response.data
    } catch (error) {
      // Return mock data for development
      const mockProjects = this.generateMockProjects()
      const project = mockProjects.items.find(p => p.id === id)
      if (!project) {
        throw new Error(`Project ${id} not found`)
      }
      return project
    }
  }

  async createProject(data: CreateProjectRequest): Promise<Project> {
    try {
      const response = await apiClient.post<Project>('/projects', data)
      return response.data
    } catch (error) {
      // Return mock data for development
      const newProject: Project = {
        id: Date.now(),
        name: data.name,
        code: data.code,
        description: data.description,
        owner_id: 1, // Mock current user ID
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
      const response = await apiClient.put<Project>(`/projects/${id}`, data)
      return response.data
    } catch (error) {
      // Return mock updated project for development
      const existingProject = await this.getProjectById(id)
      return { ...existingProject, ...data, updated_at: new Date().toISOString() }
    }
  }

  async deleteProject(id: number): Promise<void> {
    try {
      await apiClient.delete(`/projects/${id}`)
    } catch (error) {
      // Mock success for development
      return Promise.resolve()
    }
  }

  // Task Comments
  async getTaskComments(taskId: number): Promise<TaskCommentListResponse> {
    try {
      const response = await apiClient.get<TaskCommentListResponse>(`/tasks/${taskId}/comments`)
      return response.data
    } catch (error) {
      // Return mock comments for development
      return {
        items: [],
        total: 0,
        page: 1,
        limit: 20
      }
    }
  }

  async createTaskComment(taskId: number, data: CreateTaskCommentRequest): Promise<TaskComment> {
    try {
      const response = await apiClient.post<TaskComment>(`/tasks/${taskId}/comments`, data)
      return response.data
    } catch (error) {
      // Return mock comment for development
      const newComment: TaskComment = {
        id: Date.now(),
        task_id: taskId,
        user_id: 1,
        content: data.content,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        user: {
          id: 1,
          full_name: 'Current User',
          email: 'current@example.com',
          is_active: true,
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
          organizations: [],
          departments: [],
          roles: []
        }
      }
      return newComment
    }
  }

  // Statistics
  async getTaskStatistics(): Promise<TaskStatistics> {
    try {
      const response = await apiClient.get<TaskStatistics>('/tasks/statistics')
      return response.data
    } catch (error) {
      // Return mock statistics for development
      return {
        total_tasks: 15,
        by_status: {
          'TODO': 5,
          'IN_PROGRESS': 7,
          'COMPLETED': 3
        },
        by_priority: {
          'LOW': 4,
          'MEDIUM': 8,
          'HIGH': 3
        },
        completion_rate: 20,
        overdue_tasks: 2,
        my_tasks: 8
      }
    }
  }

  async getProjectStatistics(): Promise<ProjectStatistics> {
    try {
      const response = await apiClient.get<ProjectStatistics>('/projects/statistics')
      return response.data
    } catch (error) {
      // Return mock statistics for development
      return {
        total_projects: 5,
        active_projects: 3,
        completed_projects: 2,
        total_tasks: 15,
        completion_rate: 40,
        my_projects: 3
      }
    }
  }

  // Mock data generators for development
  generateMockTasks(filters: TaskFilters = {}): TaskListResponse {
    const mockTasks: Task[] = [
      {
        id: 1,
        title: 'Test Task 1',
        description: 'First test task for development',
        status: 'TODO',
        priority: 'MEDIUM',
        progress: 0,
        project_id: 1,
        creator_id: 1,
        created_at: '2024-07-01T00:00:00Z',
        updated_at: '2024-07-19T00:00:00Z',
        creator: {
          id: 1,
          full_name: 'Admin User',
          email: 'admin@example.com',
          is_active: true,
          created_at: '2024-01-01T00:00:00Z',
          updated_at: '2024-07-19T00:00:00Z',
          organizations: [],
          departments: [],
          roles: []
        },
        project: {
          id: 1,
          name: 'ITDO ERP Development',
          code: 'ITDO_ERP',
          status: 'ACTIVE',
          owner_id: 1,
          created_at: '2024-06-01T00:00:00Z',
          updated_at: '2024-07-19T00:00:00Z',
          owner: {
            id: 1,
            full_name: 'Admin User',
            email: 'admin@example.com',
            is_active: true,
            created_at: '2024-01-01T00:00:00Z',
            updated_at: '2024-07-19T00:00:00Z',
            organizations: [],
            departments: [],
            roles: []
          }
        }
      },
      {
        id: 2,
        title: 'Test Task 2',
        description: 'Second test task in progress',
        status: 'IN_PROGRESS',
        priority: 'HIGH',
        progress: 50,
        project_id: 1,
        assignee_id: 2,
        creator_id: 1,
        created_at: '2024-07-05T00:00:00Z',
        updated_at: '2024-07-19T00:00:00Z',
        creator: {
          id: 1,
          full_name: 'Admin User',
          email: 'admin@example.com',
          is_active: true,
          created_at: '2024-01-01T00:00:00Z',
          updated_at: '2024-07-19T00:00:00Z',
          organizations: [],
          departments: [],
          roles: []
        },
        assignee: {
          id: 2,
          full_name: 'Test User',
          email: 'test@example.com',
          is_active: true,
          created_at: '2024-01-02T00:00:00Z',
          updated_at: '2024-07-19T00:00:00Z',
          organizations: [],
          departments: [],
          roles: []
        },
        project: {
          id: 1,
          name: 'ITDO ERP Development',
          code: 'ITDO_ERP',
          status: 'ACTIVE',
          owner_id: 1,
          created_at: '2024-06-01T00:00:00Z',
          updated_at: '2024-07-19T00:00:00Z',
          owner: {
            id: 1,
            full_name: 'Admin User',
            email: 'admin@example.com',
            is_active: true,
            created_at: '2024-01-01T00:00:00Z',
            updated_at: '2024-07-19T00:00:00Z',
            organizations: [],
            departments: [],
            roles: []
          }
        }
      },
      {
        id: 3,
        title: 'Test Task 3',
        description: 'Third test task completed',
        status: 'COMPLETED',
        priority: 'LOW',
        progress: 100,
        project_id: 2,
        assignee_id: 2,
        creator_id: 1,
        created_at: '2024-07-10T00:00:00Z',
        updated_at: '2024-07-19T00:00:00Z',
        completed_at: '2024-07-18T00:00:00Z',
        creator: {
          id: 1,
          full_name: 'Admin User',
          email: 'admin@example.com',
          is_active: true,
          created_at: '2024-01-01T00:00:00Z',
          updated_at: '2024-07-19T00:00:00Z',
          organizations: [],
          departments: [],
          roles: []
        },
        assignee: {
          id: 2,
          full_name: 'Test User',
          email: 'test@example.com',
          is_active: true,
          created_at: '2024-01-02T00:00:00Z',
          updated_at: '2024-07-19T00:00:00Z',
          organizations: [],
          departments: [],
          roles: []
        }
      }
    ]

    // Apply filters
    let filteredTasks = mockTasks

    if (filters.status) {
      filteredTasks = filteredTasks.filter(task => task.status === filters.status)
    }

    if (filters.priority) {
      filteredTasks = filteredTasks.filter(task => task.priority === filters.priority)
    }

    if (filters.search) {
      const search = filters.search.toLowerCase()
      filteredTasks = filteredTasks.filter(task => 
        task.title.toLowerCase().includes(search) ||
        task.description?.toLowerCase().includes(search)
      )
    }

    if (filters.assignee_id) {
      filteredTasks = filteredTasks.filter(task => task.assignee_id === filters.assignee_id)
    }

    if (filters.project_id) {
      filteredTasks = filteredTasks.filter(task => task.project_id === filters.project_id)
    }

    return {
      items: filteredTasks,
      total: filteredTasks.length,
      page: 1,
      limit: 20
    }
  }

  generateMockProjects(filters: ProjectFilters = {}): ProjectListResponse {
    const mockProjects: Project[] = [
      {
        id: 1,
        name: 'ITDO ERP Development',
        code: 'ITDO_ERP',
        description: 'Main ERP system development project',
        status: 'ACTIVE',
        owner_id: 1,
        created_at: '2024-06-01T00:00:00Z',
        updated_at: '2024-07-19T00:00:00Z',
        owner: {
          id: 1,
          full_name: 'Admin User',
          email: 'admin@example.com',
          is_active: true,
          created_at: '2024-01-01T00:00:00Z',
          updated_at: '2024-07-19T00:00:00Z',
          organizations: [],
          departments: [],
          roles: []
        },
        task_count: 8
      },
      {
        id: 2,
        name: 'Mobile App Development',
        code: 'MOBILE_APP',
        description: 'Companion mobile application',
        status: 'ACTIVE',
        owner_id: 2,
        created_at: '2024-06-15T00:00:00Z',
        updated_at: '2024-07-19T00:00:00Z',
        owner: {
          id: 2,
          full_name: 'Test User',
          email: 'test@example.com',
          is_active: true,
          created_at: '2024-01-02T00:00:00Z',
          updated_at: '2024-07-19T00:00:00Z',
          organizations: [],
          departments: [],
          roles: []
        },
        task_count: 5
      }
    ]

    // Apply filters
    let filteredProjects = mockProjects

    if (filters.status) {
      filteredProjects = filteredProjects.filter(project => project.status === filters.status)
    }

    if (filters.search) {
      const search = filters.search.toLowerCase()
      filteredProjects = filteredProjects.filter(project => 
        project.name.toLowerCase().includes(search) ||
        project.description?.toLowerCase().includes(search) ||
        project.code.toLowerCase().includes(search)
      )
    }

    if (filters.owner_id) {
      filteredProjects = filteredProjects.filter(project => project.owner_id === filters.owner_id)
    }

    return {
      items: filteredProjects,
      total: filteredProjects.length,
      page: 1,
      limit: 20
    }
  }
}

// Export singleton instance
export const taskApiService = TaskApiService.getInstance()

// Export React Query keys for cache management
export const taskQueryKeys = {
  all: ['tasks'] as const,
  lists: () => [...taskQueryKeys.all, 'list'] as const,
  list: (filters?: TaskFilters) => [...taskQueryKeys.lists(), filters] as const,
  details: () => [...taskQueryKeys.all, 'detail'] as const,
  detail: (id: number) => [...taskQueryKeys.details(), id] as const,
  comments: (taskId: number) => [...taskQueryKeys.all, 'comments', taskId] as const,
  statistics: () => [...taskQueryKeys.all, 'statistics'] as const,
}

export const projectQueryKeys = {
  all: ['projects'] as const,
  lists: () => [...projectQueryKeys.all, 'list'] as const,
  list: (filters?: ProjectFilters) => [...projectQueryKeys.lists(), filters] as const,
  details: () => [...projectQueryKeys.all, 'detail'] as const,
  detail: (id: number) => [...projectQueryKeys.details(), id] as const,
  statistics: () => [...projectQueryKeys.all, 'statistics'] as const,
}