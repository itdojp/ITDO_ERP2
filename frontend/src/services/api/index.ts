// API Integration Layer - Main Export File

export { apiClient, createApiClient } from './apiClient'
export type { 
  ApiResponse, 
  PaginatedResponse, 
  ApiError, 
  RequestOptions 
} from './apiClient'

export { default as API_ENDPOINTS, buildUrl, validateEndpoint, buildVersionedEndpoint } from './endpoints'

export * from './types'

// Re-export commonly used types for convenience
export type {
  User,
  Organization,
  Project,
  Task,
  UserRole,
  ProjectStatus,
  TaskStatus,
  Priority,
  LoginRequest,
  LoginResponse,
  CreateUserRequest,
  UpdateUserRequest,
  CreateProjectRequest,
  UpdateProjectRequest,
  CreateTaskRequest,
  UpdateTaskRequest,
  SearchRequest,
  SearchResponse,
  DashboardStats,
  Notification,
  Report
} from './types'