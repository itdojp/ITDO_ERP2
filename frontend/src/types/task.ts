/**
 * Task management type definitions
 */

import { User } from './user'

export type TaskStatus = 'TODO' | 'IN_PROGRESS' | 'COMPLETED'
export type TaskPriority = 'LOW' | 'MEDIUM' | 'HIGH'

export interface Task {
  id: number
  title: string
  description?: string
  status: TaskStatus
  priority: TaskPriority
  progress: number // 0-100
  project_id?: number
  assignee_id?: number
  creator_id: number
  due_date?: string
  created_at: string
  updated_at: string
  completed_at?: string
  assignee?: User
  creator: User
  project?: Project
  comments?: TaskComment[]
}

export interface Project {
  id: number
  name: string
  code: string
  description?: string
  owner_id: number
  status: 'ACTIVE' | 'COMPLETED' | 'ARCHIVED'
  created_at: string
  updated_at: string
  owner: User
  task_count?: number
}

export interface TaskComment {
  id: number
  task_id: number
  user_id: number
  content: string
  created_at: string
  updated_at: string
  user: User
}

// CRUD operation types
export interface CreateTaskRequest {
  title: string
  description?: string
  priority: TaskPriority
  status?: TaskStatus
  project_id?: number
  assignee_id?: number
  due_date?: string
}

export interface UpdateTaskRequest {
  title?: string
  description?: string
  priority?: TaskPriority
  status?: TaskStatus
  progress?: number
  project_id?: number
  assignee_id?: number
  due_date?: string
}

export interface CreateProjectRequest {
  name: string
  code: string
  description?: string
}

export interface UpdateProjectRequest {
  name?: string
  code?: string
  description?: string
  status?: Project['status']
}

export interface CreateTaskCommentRequest {
  content: string
}

// Filter and search types
export interface TaskFilters {
  status?: TaskStatus
  priority?: TaskPriority
  assignee_id?: number
  project_id?: number
  creator_id?: number
  search?: string
  due_before?: string
  due_after?: string
}

export interface ProjectFilters {
  status?: Project['status']
  owner_id?: number
  search?: string
}

// List response types
export interface TaskListResponse {
  items: Task[]
  total: number
  page: number
  limit: number
}

export interface ProjectListResponse {
  items: Project[]
  total: number
  page: number
  limit: number
}

export interface TaskCommentListResponse {
  items: TaskComment[]
  total: number
  page: number
  limit: number
}

// UI and display types
export interface TaskTableRow {
  id: number
  title: string
  status: TaskStatus
  priority: TaskPriority
  progress: number
  assignee?: string
  project?: string
  due_date?: string
  actions: boolean
}

export interface TaskBoardColumn {
  status: TaskStatus
  title: string
  tasks: Task[]
  color: string
}

export interface ProjectTableRow {
  id: number
  name: string
  code: string
  status: Project['status']
  owner: string
  task_count: number
  created_at: string
  actions: boolean
}

// Form data types
export interface TaskFormData extends CreateTaskRequest {
  id?: number
}

export interface ProjectFormData extends CreateProjectRequest {
  id?: number
}

export interface TaskFormErrors {
  title?: string
  description?: string
  priority?: string
  status?: string
  project_id?: string
  assignee_id?: string
  due_date?: string
}

export interface ProjectFormErrors {
  name?: string
  code?: string
  description?: string
}

// Assignment and relationship types
export interface TaskAssignment {
  task_id: number
  user_id: number
  assigned_by: number
  assigned_at: string
  notes?: string
}

export interface ProjectMember {
  project_id: number
  user_id: number
  role: 'OWNER' | 'MEMBER' | 'VIEWER'
  added_by: number
  added_at: string
  user: User
}

// Statistics and analytics types
export interface TaskStatistics {
  total_tasks: number
  by_status: {
    [K in TaskStatus]: number
  }
  by_priority: {
    [K in TaskPriority]: number
  }
  completion_rate: number
  overdue_tasks: number
  my_tasks: number
}

export interface ProjectStatistics {
  total_projects: number
  active_projects: number
  completed_projects: number
  total_tasks: number
  completion_rate: number
  my_projects: number
}

// Constants and enums
export const TASK_STATUSES = [
  { value: 'TODO', label: 'To Do', color: 'gray' },
  { value: 'IN_PROGRESS', label: 'In Progress', color: 'blue' },
  { value: 'COMPLETED', label: 'Completed', color: 'green' }
] as const

export const TASK_PRIORITIES = [
  { value: 'LOW', label: 'Low', color: 'gray' },
  { value: 'MEDIUM', label: 'Medium', color: 'yellow' },
  { value: 'HIGH', label: 'High', color: 'red' }
] as const

export const PROJECT_STATUSES = [
  { value: 'ACTIVE', label: 'Active', color: 'green' },
  { value: 'COMPLETED', label: 'Completed', color: 'blue' },
  { value: 'ARCHIVED', label: 'Archived', color: 'gray' }
] as const

// Drag and drop types
export interface TaskDragData {
  task: Task
  sourceColumn: TaskStatus
  sourceIndex: number
}

export interface TaskDropData {
  targetColumn: TaskStatus
  targetIndex: number
}

// Pagination types
export interface PaginationParams {
  page: number
  limit: number
}

// Bulk operation types
export interface BulkTaskAction {
  task_ids: number[]
  action: 'update_status' | 'assign' | 'delete' | 'move_project'
  data?: {
    status?: TaskStatus
    assignee_id?: number
    project_id?: number
  }
}

export interface BulkTaskResponse {
  success_count: number
  error_count: number
  errors?: Array<{
    task_id: number
    error: string
  }>
}