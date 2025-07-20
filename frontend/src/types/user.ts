/**
 * User profile and management type definitions
 * NOTE: Some types are prepared but commented out to avoid unused export warnings
 */

// Core interfaces that are currently used
// export interface Organization { // Commented out to avoid unused export warning
interface Organization {
  id: number
  code: string
  name: string
}

// export interface Department { // Commented out to avoid unused export warning
interface Department {
  id: number
  code: string
  name: string
}

// export interface UserRole { // Commented out to avoid unused export warning
interface UserRole {
  role: Role
  organization: Organization
  department?: Department
  assigned_at: string
  expires_at?: string
}

// export interface Role { // Commented out to avoid unused export warning
interface Role {
  id: number
  code: string
  name: string
}

// Main exported interfaces
export interface User {
  id: number
  email: string
  full_name: string
  phone?: string
  profile_image_url?: string
  bio?: string
  location?: string
  website?: string
  is_active: boolean
  created_at: string
  updated_at: string
  last_login_at?: string
  organizations: Organization[]
  departments: Department[]
  roles: UserRole[]
}

export interface UserProfileUpdate {
  full_name?: string
  phone?: string
  bio?: string
  location?: string
  website?: string
}

export interface ProfileImageResponse {
  message: string
  image_url: string
}

// FUTURE TYPES - Ready for integration but currently commented out
/*
// export type VisibilityLevel = 'PUBLIC' | 'ORGANIZATION' | 'DEPARTMENT' | 'PRIVATE'

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

// export interface ProfileImageUpload { // Commented out to avoid unused export warning
interface ProfileImageUpload {
  file: File
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
*/