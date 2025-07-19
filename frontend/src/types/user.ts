/**
 * User profile and management type definitions
 */

export interface User {
  id: number                    // Unique user identifier
  email: string                 // User email address (login credential)
  full_name: string            // User's display name
  phone?: string               // Optional phone number
  profile_image_url?: string   // Optional profile picture URL
  bio?: string                 // Optional user bio/description
  location?: string            // Optional location information
  website?: string             // Optional personal website
  is_active: boolean           // Whether user account is active
  created_at: string           // Account creation timestamp
  updated_at: string           // Last update timestamp
  last_login_at?: string       // Last login timestamp (optional)
  organizations: Organization[] // Organizations user belongs to
  departments: Department[]     // Departments user is assigned to
  roles: UserRole[]            // Roles assigned to the user
}

export interface Organization {
  id: number
  code: string
  name: string
}

export interface Department {
  id: number
  code: string
  name: string
}

export interface UserRole {
  role: Role
  organization: Organization
  department?: Department
  assigned_at: string
  expires_at?: string
}

export interface Role {
  id: number
  code: string
  name: string
}

export interface UserPreferences {
  id: number
  user_id: number
  language: 'en' | 'ja' | 'zh' | 'ko' | 'es' | 'fr' | 'de'
  timezone: string
  date_format: string
  time_format: string
  theme: 'light' | 'dark' | 'auto'
  notifications_email: boolean
  notifications_push: boolean
  created_at: string
  updated_at: string
}

export interface UserPrivacySettings {
  id: number
  user_id: number
  profile_visibility: VisibilityLevel
  email_visibility: VisibilityLevel
  phone_visibility: VisibilityLevel
  activity_visibility: VisibilityLevel
  show_online_status: boolean
  allow_direct_messages: boolean
  searchable_by_email: boolean
  searchable_by_name: boolean
  created_at: string
  updated_at: string
}

export type VisibilityLevel = 'PUBLIC' | 'ORGANIZATION' | 'DEPARTMENT' | 'PRIVATE'

export interface UserProfileUpdate {
  full_name?: string
  phone?: string
  bio?: string
  location?: string
  website?: string
}

export interface UserPreferencesUpdate {
  language?: UserPreferences['language']
  timezone?: string
  date_format?: string
  time_format?: string
  theme?: UserPreferences['theme']
  notifications_email?: boolean
  notifications_push?: boolean
}

export interface UserPrivacyUpdate {
  profile_visibility?: VisibilityLevel
  email_visibility?: VisibilityLevel
  phone_visibility?: VisibilityLevel
  activity_visibility?: VisibilityLevel
  show_online_status?: boolean
  allow_direct_messages?: boolean
  searchable_by_email?: boolean
  searchable_by_name?: boolean
}

export interface ProfileImageUpload {
  file: File
}

export interface ProfileImageResponse {
  message: string
  image_url: string
}

export interface UserSearchParams {
  search?: string
  organization_id?: number
  department_id?: number
  role_id?: number
  is_active?: boolean
}

export interface UserListResponse {
  items: User[]
  total: number
  page: number
  limit: number
}

// Additional types for user management CRUD operations
export interface CreateUserRequest {
  full_name: string
  email: string
  phone?: string
  password: string
  confirm_password: string
  role?: string
  organization_ids?: number[]
  department_ids?: number[]
}

export interface UpdateUserRequest {
  full_name?: string
  email?: string
  phone?: string
  role?: string
  is_active?: boolean
  organization_ids?: number[]
  department_ids?: number[]
}

export interface UserTableRow {
  id: number
  full_name: string
  email: string
  role: string
  status: 'Active' | 'Inactive'
  last_login_at?: string
  actions: boolean
}

export interface UserFilters {
  search?: string
  role?: string
  status?: 'active' | 'inactive'
  organization_id?: number
  department_id?: number
}

export interface PaginationParams {
  page: number
  limit: number
}

export interface BulkActionRequest {
  user_ids: number[]
  action: 'activate' | 'deactivate' | 'delete'
}

export interface UserFormData extends CreateUserRequest {
  id?: number
}

export interface UserFormErrors {
  full_name?: string
  email?: string
  phone?: string
  password?: string
  confirm_password?: string
  role?: string
}