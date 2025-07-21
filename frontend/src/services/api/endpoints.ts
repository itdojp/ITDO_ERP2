// API Endpoints Configuration
export const API_ENDPOINTS = {
  // Authentication
  AUTH: {
    LOGIN: '/auth/login',
    LOGOUT: '/auth/logout',
    REFRESH: '/auth/refresh',
    REGISTER: '/auth/register',
    FORGOT_PASSWORD: '/auth/forgot-password',
    RESET_PASSWORD: '/auth/reset-password',
    VERIFY_EMAIL: '/auth/verify-email',
    PROFILE: '/auth/profile',
  },

  // Users
  USERS: {
    LIST: '/users',
    GET: (id: string) => `/users/${id}`,
    CREATE: '/users',
    UPDATE: (id: string) => `/users/${id}`,
    DELETE: (id: string) => `/users/${id}`,
    SEARCH: '/users/search',
    BULK_UPDATE: '/users/bulk',
    PERMISSIONS: (id: string) => `/users/${id}/permissions`,
    AVATAR: (id: string) => `/users/${id}/avatar`,
    PASSWORD: (id: string) => `/users/${id}/password`,
  },

  // Organizations
  ORGANIZATIONS: {
    LIST: '/organizations',
    GET: (id: string) => `/organizations/${id}`,
    CREATE: '/organizations',
    UPDATE: (id: string) => `/organizations/${id}`,
    DELETE: (id: string) => `/organizations/${id}`,
    MEMBERS: (id: string) => `/organizations/${id}/members`,
    INVITE: (id: string) => `/organizations/${id}/invite`,
    SETTINGS: (id: string) => `/organizations/${id}/settings`,
  },

  // Projects
  PROJECTS: {
    LIST: '/projects',
    GET: (id: string) => `/projects/${id}`,
    CREATE: '/projects',
    UPDATE: (id: string) => `/projects/${id}`,
    DELETE: (id: string) => `/projects/${id}`,
    ARCHIVE: (id: string) => `/projects/${id}/archive`,
    RESTORE: (id: string) => `/projects/${id}/restore`,
    DUPLICATE: (id: string) => `/projects/${id}/duplicate`,
    MEMBERS: (id: string) => `/projects/${id}/members`,
    TASKS: (id: string) => `/projects/${id}/tasks`,
    STATISTICS: (id: string) => `/projects/${id}/statistics`,
    BY_ORGANIZATION: (orgId: string) => `/organizations/${orgId}/projects`,
  },

  // Tasks
  TASKS: {
    LIST: '/tasks',
    GET: (id: string) => `/tasks/${id}`,
    CREATE: '/tasks',
    UPDATE: (id: string) => `/tasks/${id}`,
    DELETE: (id: string) => `/tasks/${id}`,
    COMPLETE: (id: string) => `/tasks/${id}/complete`,
    ASSIGN: (id: string) => `/tasks/${id}/assign`,
    COMMENTS: (id: string) => `/tasks/${id}/comments`,
    ATTACHMENTS: (id: string) => `/tasks/${id}/attachments`,
    TIME_LOGS: (id: string) => `/tasks/${id}/time-logs`,
    BY_PROJECT: (projectId: string) => `/projects/${projectId}/tasks`,
    BY_USER: (userId: string) => `/users/${userId}/tasks`,
  },

  // Files & Uploads
  FILES: {
    UPLOAD: '/files/upload',
    UPLOAD_MULTIPLE: '/files/upload/multiple',
    GET: (id: string) => `/files/${id}`,
    DELETE: (id: string) => `/files/${id}`,
    DOWNLOAD: (id: string) => `/files/${id}/download`,
    THUMBNAIL: (id: string) => `/files/${id}/thumbnail`,
    SEARCH: '/files/search',
  },

  // Dashboard & Analytics
  DASHBOARD: {
    STATS: '/dashboard/stats',
    CHARTS: '/dashboard/charts',
    ACTIVITIES: '/dashboard/activities',
    NOTIFICATIONS: '/dashboard/notifications',
    WIDGETS: '/dashboard/widgets',
    PERFORMANCE: '/dashboard/performance',
    REPORTS: '/dashboard/reports',
  },

  // Settings
  SETTINGS: {
    GENERAL: '/settings/general',
    NOTIFICATIONS: '/settings/notifications',
    SECURITY: '/settings/security',
    INTEGRATIONS: '/settings/integrations',
    BILLING: '/settings/billing',
    TEAM: '/settings/team',
  },

  // Search
  SEARCH: {
    GLOBAL: '/search',
    USERS: '/search/users',
    PROJECTS: '/search/projects',
    TASKS: '/search/tasks',
    FILES: '/search/files',
    SUGGESTIONS: '/search/suggestions',
  },

  // Notifications
  NOTIFICATIONS: {
    LIST: '/notifications',
    GET: (id: string) => `/notifications/${id}`,
    MARK_READ: (id: string) => `/notifications/${id}/read`,
    MARK_ALL_READ: '/notifications/read-all',
    DELETE: (id: string) => `/notifications/${id}`,
    SETTINGS: '/notifications/settings',
    PREFERENCES: '/notifications/preferences',
  },

  // Reports
  REPORTS: {
    GENERATE: '/reports/generate',
    LIST: '/reports',
    GET: (id: string) => `/reports/${id}`,
    DELETE: (id: string) => `/reports/${id}`,
    DOWNLOAD: (id: string) => `/reports/${id}/download`,
    TEMPLATES: '/reports/templates',
  },

  // Integrations
  INTEGRATIONS: {
    LIST: '/integrations',
    GET: (id: string) => `/integrations/${id}`,
    CONFIGURE: (id: string) => `/integrations/${id}/configure`,
    TEST: (id: string) => `/integrations/${id}/test`,
    LOGS: (id: string) => `/integrations/${id}/logs`,
    WEBHOOKS: '/integrations/webhooks',
  },

  // Admin
  ADMIN: {
    SYSTEM_INFO: '/admin/system',
    AUDIT_LOGS: '/admin/audit-logs',
    SYSTEM_SETTINGS: '/admin/settings',
    BACKUPS: '/admin/backups',
    MAINTENANCE: '/admin/maintenance',
    HEALTH: '/admin/health',
  },

  // Health & Monitoring
  HEALTH: '/health',
  STATUS: '/status',
  METRICS: '/metrics',
} as const

// Helper function to build URLs with query parameters
export const buildUrl = (
  endpoint: string,
  params?: Record<string, any>
): string => {
  if (!params) return endpoint

  const url = new URL(endpoint, 'http://dummy-base.com')
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null) {
      url.searchParams.append(key, String(value))
    }
  })

  return url.pathname + url.search
}

// Helper function to validate endpoint parameters
export const validateEndpoint = (endpoint: string): boolean => {
  try {
    new URL(endpoint, 'http://dummy-base.com')
    return true
  } catch {
    return false
  }
}

// API versioning support
export const API_VERSIONS = {
  V1: '/api/v1',
  V2: '/api/v2',
} as const

// Build versioned endpoint
export const buildVersionedEndpoint = (
  endpoint: string,
  version: string = API_VERSIONS.V1
): string => {
  return `${version}${endpoint}`
}

export default API_ENDPOINTS