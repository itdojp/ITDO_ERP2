/**
 * Lazy-loaded components for code splitting optimization
 */

import { createLazyComponent, createLazyRoute, globalPreloader } from '../../utils/lazyLoading'

// User Management Components (Heavy components that can be lazy loaded)
export const LazyUserList = createLazyComponent(
  () => import('../user-management/UserList'),
  {
    chunkName: 'user-management',
    fallback: () => (
      <div className="animate-pulse">
        <div className="h-8 bg-gray-200 rounded mb-4"></div>
        <div className="space-y-3">
          {Array.from({ length: 5 }).map((_, i) => (
            <div key={i} className="h-16 bg-gray-200 rounded"></div>
          ))}
        </div>
      </div>
    )
  }
)

export const LazyVirtualizedUserList = createLazyComponent(
  () => import('../optimized/VirtualizedUserList'),
  {
    chunkName: 'virtualized-components',
    preload: true // Preload this critical component
  }
)

// Chart Components (Heavy due to recharts dependency)
export const LazyChartComponents = createLazyComponent(
  () => import('../charts/ChartComponents'),
  {
    chunkName: 'charts',
    fallback: () => (
      <div className="flex items-center justify-center h-64 bg-gray-50 rounded-lg">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-2 border-blue-600 border-t-transparent mx-auto mb-2"></div>
          <div className="text-sm text-gray-600">Loading charts...</div>
        </div>
      </div>
    )
  }
)

export const LazyDashboardAnalytics = createLazyComponent(
  () => import('../dashboard/DashboardAnalytics'),
  {
    chunkName: 'dashboard-analytics',
    fallback: () => (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {Array.from({ length: 6 }).map((_, i) => (
          <div key={i} className="animate-pulse">
            <div className="h-32 bg-gray-200 rounded-lg"></div>
          </div>
        ))}
      </div>
    )
  }
)

// Profile Components
export const LazyUserProfileView = createLazyComponent(
  () => import('../UserProfile/UserProfileView'),
  {
    chunkName: 'user-profile',
    fallback: () => (
      <div className="animate-pulse">
        <div className="flex items-center space-x-4 mb-6">
          <div className="h-16 w-16 bg-gray-200 rounded-full"></div>
          <div className="space-y-2">
            <div className="h-4 bg-gray-200 rounded w-32"></div>
            <div className="h-3 bg-gray-200 rounded w-24"></div>
          </div>
        </div>
        <div className="space-y-4">
          <div className="h-32 bg-gray-200 rounded"></div>
          <div className="h-24 bg-gray-200 rounded"></div>
        </div>
      </div>
    )
  }
)

export const LazyUserProfileEdit = createLazyComponent(
  () => import('../UserProfile/UserProfileEdit'),
  {
    chunkName: 'user-profile-edit',
    fallback: () => (
      <div className="animate-pulse space-y-4">
        <div className="h-8 bg-gray-200 rounded w-48"></div>
        {Array.from({ length: 8 }).map((_, i) => (
          <div key={i} className="h-12 bg-gray-200 rounded"></div>
        ))}
        <div className="flex space-x-4">
          <div className="h-10 bg-gray-200 rounded w-24"></div>
          <div className="h-10 bg-gray-200 rounded w-24"></div>
        </div>
      </div>
    )
  }
)

// Modal Components (Can be lazy loaded as they're not immediately visible)
export const LazyUserCreateModal = createLazyComponent(
  () => import('../UserCreateModal'),
  {
    chunkName: 'user-modals',
    fallback: () => (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center">
        <div className="bg-white rounded-lg p-6 w-full max-w-md">
          <div className="animate-pulse space-y-4">
            <div className="h-6 bg-gray-200 rounded w-32"></div>
            {Array.from({ length: 4 }).map((_, i) => (
              <div key={i} className="h-12 bg-gray-200 rounded"></div>
            ))}
            <div className="flex space-x-4">
              <div className="h-10 bg-gray-200 rounded w-20"></div>
              <div className="h-10 bg-gray-200 rounded w-20"></div>
            </div>
          </div>
        </div>
      </div>
    )
  }
)

export const LazyUserEditModal = createLazyComponent(
  () => import('../UserEditModal'),
  { chunkName: 'user-modals' }
)

export const LazyUserDeleteDialog = createLazyComponent(
  () => import('../UserDeleteDialog'),
  { chunkName: 'user-modals' }
)

// Task Management Components
export const LazyTaskCreateModal = createLazyComponent(
  () => import('../TaskCreateModal'),
  { chunkName: 'task-modals' }
)

export const LazyTaskEditModal = createLazyComponent(
  () => import('../TaskEditModal'),
  { chunkName: 'task-modals' }
)

export const LazyTaskDeleteDialog = createLazyComponent(
  () => import('../TaskDeleteDialog'),
  { chunkName: 'task-modals' }
)

// Department Management Components
export const LazyDepartmentCreateModal = createLazyComponent(
  () => import('../DepartmentCreateModal'),
  { chunkName: 'department-modals' }
)

export const LazyDepartmentEditModal = createLazyComponent(
  () => import('../DepartmentEditModal'),
  { chunkName: 'department-modals' }
)

export const LazyDepartmentDeleteDialog = createLazyComponent(
  () => import('../DepartmentDeleteDialog'),
  { chunkName: 'department-modals' }
)

// Project Management Components
export const LazyProjectCreateModal = createLazyComponent(
  () => import('../ProjectCreateModal'),
  { chunkName: 'project-modals' }
)

export const LazyProjectEditModal = createLazyComponent(
  () => import('../ProjectEditModal'),
  { chunkName: 'project-modals' }
)

// Role Management Components
export const LazyRoleCreateModal = createLazyComponent(
  () => import('../RoleCreateModal'),
  { chunkName: 'role-modals' }
)

export const LazyRoleEditModal = createLazyComponent(
  () => import('../RoleEditModal'),
  { chunkName: 'role-modals' }
)

// Tree View Component (Can be heavy with large datasets)
export const LazyOrganizationTreeView = createLazyComponent(
  () => import('../OrganizationTreeView'),
  {
    chunkName: 'tree-components',
    fallback: () => (
      <div className="animate-pulse space-y-2">
        {Array.from({ length: 8 }).map((_, i) => (
          <div key={i} className="flex items-center space-x-2">
            <div className="h-4 w-4 bg-gray-200 rounded"></div>
            <div className="h-4 bg-gray-200 rounded flex-1"></div>
          </div>
        ))}
      </div>
    )
  }
)

// Development Tools (Only load in development)
export const LazyBundleAnalysisPanel = createLazyComponent(
  () => import('../dev/BundleAnalysisPanel'),
  {
    chunkName: 'dev-tools',
    preload: process.env.NODE_ENV === 'development'
  }
)

// Auth Components (Can be split as they're used in specific flows)
export const LazyLoginForm = createLazyComponent(
  () => import('../auth/LoginForm'),
  {
    chunkName: 'auth-forms',
    fallback: () => (
      <div className="animate-pulse space-y-4">
        <div className="h-12 bg-gray-200 rounded"></div>
        <div className="h-12 bg-gray-200 rounded"></div>
        <div className="h-10 bg-gray-200 rounded"></div>
      </div>
    )
  }
)

export const LazySignUpForm = createLazyComponent(
  () => import('../auth/SignUpForm'),
  { chunkName: 'auth-forms' }
)

export const LazyForgotPasswordForm = createLazyComponent(
  () => import('../auth/ForgotPasswordForm'),
  { chunkName: 'auth-forms' }
)

export const LazyResetPasswordForm = createLazyComponent(
  () => import('../auth/ResetPasswordForm'),
  { chunkName: 'auth-forms' }
)

// Register all components with the global preloader for intelligent preloading
if (typeof window !== 'undefined') {
  // Critical components that should be preloaded
  globalPreloader.register('user-management', () => import('../user-management/UserList'))
  globalPreloader.register('virtualized-components', () => import('../optimized/VirtualizedUserList'))
  
  // Secondary components for later preload
  globalPreloader.register('charts', () => import('../charts/ChartComponents'))
  globalPreloader.register('dashboard-analytics', () => import('../dashboard/DashboardAnalytics'))
  globalPreloader.register('user-profile', () => import('../UserProfile/UserProfileView'))
  
  // On idle, start preloading secondary components
  if ('requestIdleCallback' in window) {
    requestIdleCallback(() => {
      globalPreloader.preload([
        'charts',
        'dashboard-analytics',
        'user-profile'
      ]).catch(console.error)
    })
  }
}

// Export preloader for manual control
export { globalPreloader }