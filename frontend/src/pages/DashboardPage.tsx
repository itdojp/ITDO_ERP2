import { useAuthState } from '../services/authApi'
import Button from '../components/ui/Button'
import DashboardAnalytics from '../components/dashboard/DashboardAnalytics'
import { User, Settings, Users, Building, FileText, LogOut } from 'lucide-react'

export function DashboardPage() {
  const { user } = useAuthState()

  const handleLogout = () => {
    // This will be handled by the logout functionality
    localStorage.removeItem('token')
    localStorage.removeItem('user')
    window.location.href = '/login'
  }

  const modules = [
    {
      title: 'User Management',
      description: 'Manage users, roles, and permissions',
      icon: Users,
      href: '/users',
      color: 'bg-blue-500'
    },
    {
      title: 'Organization Management',
      description: 'Manage organizations and departments',
      icon: Building,
      href: '/organizations',
      color: 'bg-green-500'
    },
    {
      title: 'Task Management',
      description: 'Create and track tasks and projects',
      icon: FileText,
      href: '/tasks',
      color: 'bg-purple-500'
    },
    {
      title: 'Settings',
      description: 'System configuration and preferences',
      icon: Settings,
      href: '/settings',
      color: 'bg-gray-500'
    }
  ]

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
              <p className="mt-1 text-sm text-gray-600">
                Welcome back, {user?.name || 'User'}
              </p>
            </div>
            
            <div className="flex items-center space-x-4">
              <Button
                variant="outline"
                aria-label="User menu"
                onClick={handleLogout}
                className="flex items-center space-x-2"
              >
                <User className="h-4 w-4" />
                <span>{user?.email}</span>
              </Button>
              
              <Button
                variant="ghost"
                onClick={handleLogout}
                className="flex items-center space-x-2"
              >
                <LogOut className="h-4 w-4" />
                <span>Logout</span>
              </Button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0">
          {/* Welcome Section */}
          <div className="bg-white overflow-hidden shadow rounded-lg mb-8">
            <div className="px-4 py-5 sm:p-6">
              <h2 className="text-lg font-medium text-gray-900 mb-2">
                Welcome to ITDO ERP System
              </h2>
              <p className="text-gray-600">
                Your comprehensive enterprise resource planning solution. 
                Select a module below to get started.
              </p>
            </div>
          </div>

          {/* Modules Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {modules.map((module) => {
              const IconComponent = module.icon
              return (
                <div
                  key={module.title}
                  className="bg-white overflow-hidden shadow rounded-lg hover:shadow-md transition-shadow cursor-pointer"
                  onClick={() => window.location.href = module.href}
                >
                  <div className="p-6">
                    <div className="flex items-center mb-4">
                      <div className={`${module.color} p-3 rounded-lg`}>
                        <IconComponent className="h-6 w-6 text-white" />
                      </div>
                    </div>
                    <h3 className="text-lg font-medium text-gray-900 mb-2">
                      {module.title}
                    </h3>
                    <p className="text-sm text-gray-600">
                      {module.description}
                    </p>
                  </div>
                </div>
              )
            })}
          </div>

          {/* Analytics Dashboard */}
          <DashboardAnalytics className="mt-8" />
        </div>
      </main>
    </div>
  )
}