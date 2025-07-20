/**
 * Organization and Department management type definitions
 */

export interface Organization {
  id: number
  name: string
  code: string
  description?: string
  industry?: string
  website?: string
  phone?: string
  email?: string
  logo_url?: string
  is_active: boolean
  parent_id?: number
  address?: Address
  created_at: string
  updated_at: string
  children?: Organization[]
  departments?: Department[]
  user_count?: number
  department_count?: number
}

export interface Department {
  id: number
  name: string
  code: string
  description?: string
  type?: string
  organization_id: number
  parent_department_id?: number
  manager_id?: number
  is_active: boolean
  created_at: string
  updated_at: string
  organization: Organization
  parent_department?: Department
  manager?: DepartmentManager
  children?: Department[]
  user_count?: number
}

export interface Address {
  street: string
  city: string
  state: string
  postal_code: string
  country: string
}

export interface DepartmentManager {
  id: number
  full_name: string
  email: string
  avatar_url?: string
}

// CRUD operation types
export interface CreateOrganizationRequest {
  name: string
  code: string
  description?: string
  industry?: string
  website?: string
  phone?: string
  email?: string
  parent_id?: number
  address?: Address
}

export interface UpdateOrganizationRequest {
  name?: string
  code?: string
  description?: string
  industry?: string
  website?: string
  phone?: string
  email?: string
  is_active?: boolean
  address?: Address
}

export interface CreateDepartmentRequest {
  name: string
  code: string
  description?: string
  type?: string
  organization_id: number
  parent_department_id?: number
  manager_id?: number
}

export interface UpdateDepartmentRequest {
  name?: string
  code?: string
  description?: string
  type?: string
  parent_department_id?: number
  manager_id?: number
  is_active?: boolean
}

// Tree view and display types
export interface OrganizationTreeNode {
  id: number
  name: string
  code: string
  type: 'organization' | 'department'
  is_active: boolean
  parent_id?: number
  children: OrganizationTreeNode[]
  expanded: boolean
  user_count: number
  level: number
}

export interface OrganizationFilters {
  search?: string
  industry?: string
  is_active?: boolean
  parent_id?: number
}

export interface DepartmentFilters {
  search?: string
  type?: string
  organization_id?: number
  is_active?: boolean
  has_manager?: boolean
}

// Pagination and list responses
export interface OrganizationListResponse {
  items: Organization[]
  total: number
  page: number
  limit: number
}

export interface DepartmentListResponse {
  items: Department[]
  total: number
  page: number
  limit: number
}

// Permission management types
export interface OrganizationPermission {
  id: number
  organization_id: number
  user_id: number
  role: string
  permissions: string[]
  granted_at: string
  granted_by: number
  expires_at?: string
  user: {
    id: number
    full_name: string
    email: string
    avatar_url?: string
  }
}

export interface CreateOrganizationPermissionRequest {
  user_id: number
  role: string
  permissions: string[]
  expires_at?: string
}

export interface UpdateOrganizationPermissionRequest {
  role?: string
  permissions?: string[]
  expires_at?: string
}

// Move operations
export interface MoveDepartmentRequest {
  new_organization_id?: number
  new_parent_department_id?: number
}

// Search and autocomplete types
export interface ManagerSearchResult {
  id: number
  full_name: string
  email: string
  avatar_url?: string
  current_role?: string
}

export interface OrganizationSearchResult {
  id: number
  name: string
  code: string
  path: string
}

// Form validation types
export interface OrganizationFormData extends CreateOrganizationRequest {
  id?: number
}

export interface DepartmentFormData extends CreateDepartmentRequest {
  id?: number
}

export interface OrganizationFormErrors {
  name?: string
  code?: string
  description?: string
  industry?: string
  website?: string
  phone?: string
  email?: string
  'address.street'?: string
  'address.city'?: string
  'address.state'?: string
  'address.postal_code'?: string
  'address.country'?: string
}

export interface DepartmentFormErrors {
  name?: string
  code?: string
  description?: string
  type?: string
  organization_id?: string
  parent_department_id?: string
  manager_id?: string
}

// Constants and enums
export const INDUSTRY_OPTIONS = [
  { value: 'technology', label: 'Technology' },
  { value: 'finance', label: 'Finance' },
  { value: 'healthcare', label: 'Healthcare' },
  { value: 'education', label: 'Education' },
  { value: 'manufacturing', label: 'Manufacturing' },
  { value: 'retail', label: 'Retail' },
  { value: 'consulting', label: 'Consulting' },
  { value: 'other', label: 'Other' }
] as const

export const DEPARTMENT_TYPES = [
  { value: 'engineering', label: 'Engineering' },
  { value: 'sales', label: 'Sales' },
  { value: 'marketing', label: 'Marketing' },
  { value: 'hr', label: 'Human Resources' },
  { value: 'finance', label: 'Finance' },
  { value: 'operations', label: 'Operations' },
  { value: 'support', label: 'Customer Support' },
  { value: 'legal', label: 'Legal' },
  { value: 'admin', label: 'Administration' },
  { value: 'other', label: 'Other' }
] as const

export const ORGANIZATION_ROLES = [
  { value: 'org_owner', label: 'Organization Owner' },
  { value: 'org_admin', label: 'Organization Administrator' },
  { value: 'org_manager', label: 'Organization Manager' },
  { value: 'dept_manager', label: 'Department Manager' },
  { value: 'team_lead', label: 'Team Lead' },
  { value: 'member', label: 'Member' },
  { value: 'viewer', label: 'Viewer' }
] as const

export const ORGANIZATION_PERMISSIONS = [
  { value: 'view_reports', label: 'View Reports' },
  { value: 'manage_users', label: 'Manage Users' },
  { value: 'manage_departments', label: 'Manage Departments' },
  { value: 'manage_permissions', label: 'Manage Permissions' },
  { value: 'manage_settings', label: 'Manage Settings' },
  { value: 'view_audit_logs', label: 'View Audit Logs' },
  { value: 'export_data', label: 'Export Data' },
  { value: 'import_data', label: 'Import Data' }
] as const