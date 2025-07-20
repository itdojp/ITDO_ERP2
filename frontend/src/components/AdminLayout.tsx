import { ReactNode } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { 
  Shield, 
  Users, 
  Building, 
  Settings, 
  Home,
  ChevronRight,
  User
} from 'lucide-react'

interface AdminLayoutProps {
  children: ReactNode
}

const adminNavigation = [
  { name: 'Dashboard', href: '/admin', icon: Home, exact: true },
  { name: 'User Management', href: '/admin/users', icon: Users },
  { name: 'Permissions & Roles', href: '/admin/permissions', icon: Shield },
  { name: 'Organizations', href: '/admin/organizations', icon: Building },
  { name: 'System Settings', href: '/admin/settings', icon: Settings }
]

const breadcrumbMapping: Record<string, string> = {
  '/admin': 'Admin Dashboard',
  '/admin/users': 'User Management',
  '/admin/permissions': 'Permissions & Roles',
  '/admin/organizations': 'Organizations',
  '/admin/settings': 'System Settings'
}

function Breadcrumb() {
  const location = useLocation()
  const pathSegments = location.pathname.split('/').filter(Boolean)
  
  const breadcrumbs = pathSegments.reduce((acc, segment, index) => {
    const path = '/' + pathSegments.slice(0, index + 1).join('/')
    const label = breadcrumbMapping[path] || segment.charAt(0).toUpperCase() + segment.slice(1)
    acc.push({ path, label })
    return acc
  }, [] as Array<{ path: string; label: string }>)

  return (
    <nav className="flex items-center space-x-2 text-sm text-gray-500">
      <Link to="/" className="hover:text-gray-700">
        ITDO ERP
      </Link>
      {breadcrumbs.map((breadcrumb, index) => (
        <div key={breadcrumb.path} className="flex items-center space-x-2">
          <ChevronRight className="h-4 w-4" />
          {index === breadcrumbs.length - 1 ? (
            <span className="text-gray-900 font-medium">{breadcrumb.label}</span>
          ) : (
            <Link to={breadcrumb.path} className="hover:text-gray-700">
              {breadcrumb.label}
            </Link>
          )}
        </div>
      ))}
    </nav>
  )
}

export function AdminLayout({ children }: AdminLayoutProps) {
  const location = useLocation()

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Top Navigation */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center space-x-4">
              <Link to="/dashboard" className="text-xl font-semibold text-gray-900 hover:text-blue-600">
                ITDO ERP System
              </Link>
              <span className="px-2 py-1 bg-red-100 text-red-800 text-xs font-medium rounded">
                Admin Panel
              </span>
            </div>
            
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2 text-sm text-gray-700">
                <User className="h-4 w-4" />
                <span>Administrator</span>
              </div>
              <Link 
                to="/dashboard" 
                className="text-sm text-gray-600 hover:text-gray-900 px-3 py-2 rounded-md hover:bg-gray-100"
              >
                Back to Dashboard
              </Link>
            </div>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {/* Breadcrumb */}
        <div className="mb-6">
          <Breadcrumb />
        </div>

        <div className="flex gap-6">
          {/* Sidebar Navigation */}
          <aside className="w-64 flex-shrink-0">
            <div className="bg-white rounded-lg shadow-sm border border-gray-200">
              <div className="p-4 border-b border-gray-200">
                <h3 className="text-lg font-medium text-gray-900">Administration</h3>
                <p className="text-sm text-gray-500 mt-1">System management tools</p>
              </div>
              <nav className="p-2" data-testid="admin-menu">
                {adminNavigation.map((item) => {
                  const Icon = item.icon
                  const isActive = item.exact ? 
                    location.pathname === item.href : 
                    location.pathname.startsWith(item.href)
                  
                  return (
                    <Link
                      key={item.name}
                      to={item.href}
                      className={`flex items-center px-3 py-2 text-sm font-medium rounded-md transition-colors mb-1 ${
                        isActive 
                          ? 'bg-blue-50 text-blue-700 border-r-2 border-blue-600' 
                          : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
                      }`}
                      data-testid={item.name === 'User Management' ? 'user-management-link' : 
                                  item.name === 'Permissions & Roles' ? 'role-management-link' : 
                                  undefined}
                    >
                      <Icon className="h-5 w-5 mr-3" />
                      {item.name}
                    </Link>
                  )
                })}
              </nav>
            </div>

            {/* Quick Stats */}
            <div className="mt-6 bg-white rounded-lg shadow-sm border border-gray-200 p-4">
              <h4 className="text-sm font-medium text-gray-900 mb-3">Quick Stats</h4>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-600">Total Users</span>
                  <span className="font-medium">156</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Active Roles</span>
                  <span className="font-medium">8</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Organizations</span>
                  <span className="font-medium">12</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">System Health</span>
                  <span className="text-green-600 font-medium">Good</span>
                </div>
              </div>
            </div>
          </aside>

          {/* Main Content */}
          <main className="flex-1 min-w-0">
            <div className="bg-white rounded-lg shadow-sm border border-gray-200">
              {children}
            </div>
          </main>
        </div>
      </div>
    </div>
  )
}