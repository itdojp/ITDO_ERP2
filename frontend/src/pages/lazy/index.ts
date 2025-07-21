/**
 * Lazy-loaded pages for route-based code splitting
 */

import { createLazyRoute, globalPreloader } from '../../utils/lazyLoading'

// Dashboard Pages
export const LazyDashboard = createLazyRoute(
  () => import('../Dashboard'),
  {
    routeName: 'Dashboard',
    chunkName: 'dashboard-page',
    preload: true // Critical route, preload immediately
  }
)

// User Management Pages
export const LazyUserManagement = createLazyRoute(
  () => import('../UserManagement'),
  {
    routeName: 'User Management',
    chunkName: 'user-management-page',
    preload: true // High-priority route
  }
)

export const LazyUserProfile = createLazyRoute(
  () => import('../UserProfile'),
  {
    routeName: 'User Profile',
    chunkName: 'user-profile-page'
  }
)

// Analytics & Reports Pages
export const LazyAnalytics = createLazyRoute(
  () => import('../Analytics'),
  {
    routeName: 'Analytics',
    chunkName: 'analytics-page',
    fallback: () => (
      <div className="p-6">
        <div className="animate-pulse">
          <div className="h-8 bg-gray-200 rounded w-48 mb-6"></div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {Array.from({ length: 6 }).map((_, i) => (
              <div key={i} className="h-64 bg-gray-200 rounded-lg"></div>
            ))}
          </div>
        </div>
      </div>
    )
  }
)

export const LazyReports = createLazyRoute(
  () => import('../Reports'),
  {
    routeName: 'Reports',
    chunkName: 'reports-page'
  }
)

// Organization Management Pages
export const LazyOrganization = createLazyRoute(
  () => import('../Organization'),
  {
    routeName: 'Organization',
    chunkName: 'organization-page'
  }
)

export const LazyDepartments = createLazyRoute(
  () => import('../Departments'),
  {
    routeName: 'Departments',
    chunkName: 'departments-page'
  }
)

// Project Management Pages
export const LazyProjects = createLazyRoute(
  () => import('../Projects'),
  {
    routeName: 'Projects',
    chunkName: 'projects-page'
  }
)

export const LazyProjectDetail = createLazyRoute(
  () => import('../ProjectDetail'),
  {
    routeName: 'Project Details',
    chunkName: 'project-detail-page'
  }
)

export const LazyTasks = createLazyRoute(
  () => import('../Tasks'),
  {
    routeName: 'Tasks',
    chunkName: 'tasks-page'
  }
)

// Settings Pages
export const LazySettings = createLazyRoute(
  () => import('../Settings'),
  {
    routeName: 'Settings',
    chunkName: 'settings-page'
  }
)

export const LazyProfile = createLazyRoute(
  () => import('../Profile'),
  {
    routeName: 'Profile',
    chunkName: 'profile-page'
  }
)

export const LazyPreferences = createLazyRoute(
  () => import('../Preferences'),
  {
    routeName: 'Preferences',
    chunkName: 'preferences-page'
  }
)

// Administrative Pages
export const LazyAdminUsers = createLazyRoute(
  () => import('../admin/Users'),
  {
    routeName: 'Admin - Users',
    chunkName: 'admin-users-page'
  }
)

export const LazyAdminRoles = createLazyRoute(
  () => import('../admin/Roles'),
  {
    routeName: 'Admin - Roles',
    chunkName: 'admin-roles-page'
  }
)

export const LazyAdminPermissions = createLazyRoute(
  () => import('../admin/Permissions'),
  {
    routeName: 'Admin - Permissions',
    chunkName: 'admin-permissions-page'
  }
)

export const LazyAdminSystem = createLazyRoute(
  () => import('../admin/System'),
  {
    routeName: 'Admin - System',
    chunkName: 'admin-system-page'
  }
)

// Error Pages
export const LazyNotFound = createLazyRoute(
  () => import('../NotFound'),
  {
    routeName: '404 Not Found',
    chunkName: 'error-pages'
  }
)

export const LazyUnauthorized = createLazyRoute(
  () => import('../Unauthorized'),
  {
    routeName: '403 Unauthorized',
    chunkName: 'error-pages'
  }
)

export const LazyServerError = createLazyRoute(
  () => import('../ServerError'),
  {
    routeName: '500 Server Error',
    chunkName: 'error-pages'
  }
)

// Help & Documentation Pages
export const LazyHelp = createLazyRoute(
  () => import('../Help'),
  {
    routeName: 'Help',
    chunkName: 'help-page'
  }
)

export const LazyDocumentation = createLazyRoute(
  () => import('../Documentation'),
  {
    routeName: 'Documentation',
    chunkName: 'documentation-page'
  }
)

// Auth Pages (Separate chunk as they're used in different flow)
export const LazyLogin = createLazyRoute(
  () => import('../auth/Login'),
  {
    routeName: 'Login',
    chunkName: 'auth-pages',
    fallback: () => (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="max-w-md w-full space-y-8">
          <div className="animate-pulse">
            <div className="h-12 bg-gray-200 rounded w-32 mx-auto mb-8"></div>
            <div className="space-y-4">
              <div className="h-12 bg-gray-200 rounded"></div>
              <div className="h-12 bg-gray-200 rounded"></div>
              <div className="h-10 bg-gray-200 rounded"></div>
            </div>
          </div>
        </div>
      </div>
    )
  }
)

export const LazyRegister = createLazyRoute(
  () => import('../auth/Register'),
  {
    routeName: 'Register',
    chunkName: 'auth-pages'
  }
)

export const LazyForgotPassword = createLazyRoute(
  () => import('../auth/ForgotPassword'),
  {
    routeName: 'Forgot Password',
    chunkName: 'auth-pages'
  }
)

export const LazyResetPassword = createLazyRoute(
  () => import('../auth/ResetPassword'),
  {
    routeName: 'Reset Password',
    chunkName: 'auth-pages'
  }
)

// Register critical pages with global preloader
if (typeof window !== 'undefined') {
  // Core application pages
  globalPreloader.register('dashboard-page', () => import('../Dashboard'))
  globalPreloader.register('user-management-page', () => import('../UserManagement'))
  
  // Secondary pages for later preload
  globalPreloader.register('analytics-page', () => import('../Analytics'))
  globalPreloader.register('projects-page', () => import('../Projects'))
  globalPreloader.register('settings-page', () => import('../Settings'))
  
  // Start preloading critical pages after initial load
  if (document.readyState === 'complete') {
    setTimeout(() => {
      globalPreloader.preload(['dashboard-page', 'user-management-page']).catch(console.error)
    }, 2000) // Wait 2 seconds after page load
  } else {
    window.addEventListener('load', () => {
      setTimeout(() => {
        globalPreloader.preload(['dashboard-page', 'user-management-page']).catch(console.error)
      }, 2000)
    })
  }
  
  // Preload secondary pages on user interaction
  const preloadSecondaryPages = () => {
    globalPreloader.preload([
      'analytics-page',
      'projects-page',
      'settings-page'
    ]).catch(console.error)
    
    // Remove listeners after first interaction
    document.removeEventListener('mousemove', preloadSecondaryPages)
    document.removeEventListener('scroll', preloadSecondaryPages)
    document.removeEventListener('keydown', preloadSecondaryPages)
  }
  
  // Preload on first user interaction
  document.addEventListener('mousemove', preloadSecondaryPages, { once: true })
  document.addEventListener('scroll', preloadSecondaryPages, { once: true })
  document.addEventListener('keydown', preloadSecondaryPages, { once: true })
}

// Route preloading utilities
export const preloadRoute = (routeName: string) => {
  return globalPreloader.register(routeName, () => import(`../${routeName}`))
}

export const preloadCriticalRoutes = () => {
  return globalPreloader.preload([
    'dashboard-page',
    'user-management-page'
  ])
}

export const preloadAllRoutes = () => {
  return globalPreloader.preloadAll()
}