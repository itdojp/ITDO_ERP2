import React from 'react'
import { 
  User, 
  Search, 
  Filter, 
  Plus, 
  MoreHorizontal, 
  Edit, 
  Trash2, 
  UserPlus, 
  UserX,
  Mail,
  Phone,
  Calendar,
  Shield,
  CheckCircle,
  XCircle,
  Clock
} from 'lucide-react'
import { cn } from '../../lib/utils'
import { User as UserType, UserRole, UserStatus } from '../../services/api/types'

export interface UserListProps {
  users: UserType[]
  loading?: boolean
  onUserSelect?: (user: UserType) => void
  onUserEdit?: (user: UserType) => void
  onUserDelete?: (user: UserType) => void
  onUserInvite?: () => void
  onUserBulkAction?: (action: string, userIds: string[]) => void
  onSearch?: (query: string) => void
  onFilter?: (filters: Record<string, any>) => void
  searchQuery?: string
  selectedUsers?: string[]
  onSelectionChange?: (userIds: string[]) => void
  className?: string
}

const UserStatusBadge: React.FC<{ status: UserStatus }> = ({ status }) => {
  const statusConfig = {
    [UserStatus.ACTIVE]: { 
      color: 'bg-green-100 text-green-800', 
      icon: <CheckCircle className="h-3 w-3" /> 
    },
    [UserStatus.INACTIVE]: { 
      color: 'bg-gray-100 text-gray-800', 
      icon: <XCircle className="h-3 w-3" /> 
    },
    [UserStatus.PENDING]: { 
      color: 'bg-yellow-100 text-yellow-800', 
      icon: <Clock className="h-3 w-3" /> 
    },
    [UserStatus.SUSPENDED]: { 
      color: 'bg-red-100 text-red-800', 
      icon: <XCircle className="h-3 w-3" /> 
    },
  }

  const config = statusConfig[status]

  return (
    <span className={cn('inline-flex items-center px-2 py-1 rounded-full text-xs font-medium', config.color)}>
      {config.icon}
      <span className="ml-1 capitalize">{status}</span>
    </span>
  )
}

const UserRoleBadge: React.FC<{ role: UserRole }> = ({ role }) => {
  const roleConfig = {
    [UserRole.ADMIN]: { color: 'bg-purple-100 text-purple-800', icon: <Shield className="h-3 w-3" /> },
    [UserRole.MANAGER]: { color: 'bg-blue-100 text-blue-800', icon: <User className="h-3 w-3" /> },
    [UserRole.MEMBER]: { color: 'bg-green-100 text-green-800', icon: <User className="h-3 w-3" /> },
    [UserRole.VIEWER]: { color: 'bg-gray-100 text-gray-800', icon: <User className="h-3 w-3" /> },
    [UserRole.GUEST]: { color: 'bg-orange-100 text-orange-800', icon: <User className="h-3 w-3" /> },
  }

  const config = roleConfig[role]

  return (
    <span className={cn('inline-flex items-center px-2 py-1 rounded-full text-xs font-medium', config.color)}>
      {config.icon}
      <span className="ml-1 capitalize">{role}</span>
    </span>
  )
}

const UserList = React.memo<UserListProps>(({
  users,
  loading = false,
  onUserSelect,
  onUserEdit,
  onUserDelete,
  onUserInvite,
  onUserBulkAction,
  onSearch,
  onFilter,
  searchQuery = '',
  selectedUsers = [],
  onSelectionChange,
  className,
}) => {
  const [localSearchQuery, setLocalSearchQuery] = React.useState(searchQuery)
  const [showFilters, setShowFilters] = React.useState(false)
  const [filters, setFilters] = React.useState({
    role: '',
    status: '',
    joinedAfter: '',
    joinedBefore: '',
  })

  // Handle search input with debouncing
  React.useEffect(() => {
    const timer = setTimeout(() => {
      onSearch?.(localSearchQuery)
    }, 300)

    return () => clearTimeout(timer)
  }, [localSearchQuery, onSearch])

  // Handle filter changes
  const handleFilterChange = (key: string, value: string) => {
    const newFilters = { ...filters, [key]: value }
    setFilters(newFilters)
    onFilter?.(newFilters)
  }

  // Handle select all
  const handleSelectAll = (checked: boolean) => {
    if (checked) {
      onSelectionChange?.(users.map(user => user.id))
    } else {
      onSelectionChange?.([])
    }
  }

  // Handle individual selection
  const handleUserSelection = (userId: string, checked: boolean) => {
    if (checked) {
      onSelectionChange?.([...selectedUsers, userId])
    } else {
      onSelectionChange?.(selectedUsers.filter(id => id !== userId))
    }
  }

  // Handle bulk actions
  const handleBulkAction = (action: string) => {
    if (selectedUsers.length > 0) {
      onUserBulkAction?.(action, selectedUsers)
    }
  }

  const isAllSelected = users.length > 0 && selectedUsers.length === users.length
  const isPartiallySelected = selectedUsers.length > 0 && selectedUsers.length < users.length

  return (
    <div className={cn('bg-white rounded-lg shadow', className)}>
      {/* Header */}
      <div className="px-6 py-4 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <h2 className="text-lg font-semibold text-gray-900 flex items-center">
              <User className="h-5 w-5 mr-2" />
              Users ({users.length})
            </h2>
            
            {selectedUsers.length > 0 && (
              <div className="flex items-center space-x-2">
                <span className="text-sm text-gray-600">{selectedUsers.length} selected</span>
                <select
                  onChange={(e) => e.target.value && handleBulkAction(e.target.value)}
                  className="text-sm border-gray-300 rounded-md"
                  defaultValue=""
                >
                  <option value="" disabled>Bulk Actions</option>
                  <option value="activate">Activate</option>
                  <option value="deactivate">Deactivate</option>
                  <option value="delete">Delete</option>
                  <option value="export">Export</option>
                </select>
              </div>
            )}
          </div>

          <div className="flex items-center space-x-3">
            <button
              onClick={() => setShowFilters(!showFilters)}
              className={cn(
                'p-2 text-gray-400 hover:text-gray-600 rounded-md',
                showFilters && 'text-blue-600 bg-blue-50'
              )}
            >
              <Filter className="h-4 w-4" />
            </button>

            <button
              onClick={onUserInvite}
              className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700"
            >
              <UserPlus className="h-4 w-4 mr-2" />
              Invite User
            </button>
          </div>
        </div>

        {/* Search Bar */}
        <div className="mt-4">
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <Search className="h-4 w-4 text-gray-400" />
            </div>
            <input
              type="text"
              value={localSearchQuery}
              onChange={(e) => setLocalSearchQuery(e.target.value)}
              className="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md leading-5 bg-white placeholder-gray-500 focus:outline-none focus:placeholder-gray-400 focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
              placeholder="Search users by name, email, or role..."
            />
          </div>
        </div>

        {/* Filters */}
        {showFilters && (
          <div className="mt-4 p-4 bg-gray-50 rounded-md">
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Role</label>
                <select
                  value={filters.role}
                  onChange={(e) => handleFilterChange('role', e.target.value)}
                  className="block w-full border-gray-300 rounded-md text-sm"
                >
                  <option value="">All Roles</option>
                  <option value={UserRole.ADMIN}>Admin</option>
                  <option value={UserRole.MANAGER}>Manager</option>
                  <option value={UserRole.MEMBER}>Member</option>
                  <option value={UserRole.VIEWER}>Viewer</option>
                  <option value={UserRole.GUEST}>Guest</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Status</label>
                <select
                  value={filters.status}
                  onChange={(e) => handleFilterChange('status', e.target.value)}
                  className="block w-full border-gray-300 rounded-md text-sm"
                >
                  <option value="">All Statuses</option>
                  <option value={UserStatus.ACTIVE}>Active</option>
                  <option value={UserStatus.INACTIVE}>Inactive</option>
                  <option value={UserStatus.PENDING}>Pending</option>
                  <option value={UserStatus.SUSPENDED}>Suspended</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Joined After</label>
                <input
                  type="date"
                  value={filters.joinedAfter}
                  onChange={(e) => handleFilterChange('joinedAfter', e.target.value)}
                  className="block w-full border-gray-300 rounded-md text-sm"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Joined Before</label>
                <input
                  type="date"
                  value={filters.joinedBefore}
                  onChange={(e) => handleFilterChange('joinedBefore', e.target.value)}
                  className="block w-full border-gray-300 rounded-md text-sm"
                />
              </div>
            </div>

            <div className="mt-4 flex justify-end">
              <button
                onClick={() => {
                  setFilters({ role: '', status: '', joinedAfter: '', joinedBefore: '' })
                  onFilter?.({})
                }}
                className="text-sm text-gray-600 hover:text-gray-800"
              >
                Clear Filters
              </button>
            </div>
          </div>
        )}
      </div>

      {/* User Table */}
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th scope="col" className="px-6 py-3 text-left">
                <input
                  type="checkbox"
                  checked={isAllSelected}
                  ref={(input) => {
                    if (input) input.indeterminate = isPartiallySelected
                  }}
                  onChange={(e) => handleSelectAll(e.target.checked)}
                  className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                />
              </th>
              <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                User
              </th>
              <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Role
              </th>
              <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Status
              </th>
              <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Last Login
              </th>
              <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Joined
              </th>
              <th scope="col" className="relative px-6 py-3">
                <span className="sr-only">Actions</span>
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {loading ? (
              // Loading skeleton
              Array.from({ length: 5 }).map((_, index) => (
                <tr key={index}>
                  <td className="px-6 py-4">
                    <div className="h-4 w-4 bg-gray-200 rounded animate-pulse" />
                  </td>
                  <td className="px-6 py-4">
                    <div className="flex items-center">
                      <div className="h-10 w-10 bg-gray-200 rounded-full animate-pulse" />
                      <div className="ml-4 space-y-2">
                        <div className="h-4 w-24 bg-gray-200 rounded animate-pulse" />
                        <div className="h-3 w-32 bg-gray-200 rounded animate-pulse" />
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <div className="h-6 w-16 bg-gray-200 rounded-full animate-pulse" />
                  </td>
                  <td className="px-6 py-4">
                    <div className="h-6 w-16 bg-gray-200 rounded-full animate-pulse" />
                  </td>
                  <td className="px-6 py-4">
                    <div className="h-4 w-20 bg-gray-200 rounded animate-pulse" />
                  </td>
                  <td className="px-6 py-4">
                    <div className="h-4 w-20 bg-gray-200 rounded animate-pulse" />
                  </td>
                  <td className="px-6 py-4">
                    <div className="h-8 w-8 bg-gray-200 rounded animate-pulse" />
                  </td>
                </tr>
              ))
            ) : users.length === 0 ? (
              <tr>
                <td colSpan={7} className="px-6 py-12 text-center">
                  <User className="h-12 w-12 text-gray-300 mx-auto mb-4" />
                  <p className="text-gray-500">No users found</p>
                  <p className="text-sm text-gray-400 mt-1">
                    {searchQuery || Object.values(filters).some(Boolean)
                      ? 'Try adjusting your search or filters'
                      : 'Invite users to get started'}
                  </p>
                </td>
              </tr>
            ) : (
              users.map((user) => (
                <tr
                  key={user.id}
                  className="hover:bg-gray-50 cursor-pointer"
                  onClick={() => onUserSelect?.(user)}
                >
                  <td className="px-6 py-4" onClick={(e) => e.stopPropagation()}>
                    <input
                      type="checkbox"
                      checked={selectedUsers.includes(user.id)}
                      onChange={(e) => handleUserSelection(user.id, e.target.checked)}
                      className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                    />
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center">
                      <div className="h-10 w-10 flex-shrink-0">
                        {user.avatar ? (
                          <img className="h-10 w-10 rounded-full" src={user.avatar} alt={user.fullName} />
                        ) : (
                          <div className="h-10 w-10 rounded-full bg-gray-300 flex items-center justify-center">
                            <User className="h-6 w-6 text-gray-600" />
                          </div>
                        )}
                      </div>
                      <div className="ml-4">
                        <div className="text-sm font-medium text-gray-900">{user.fullName}</div>
                        <div className="text-sm text-gray-500 flex items-center">
                          <Mail className="h-3 w-3 mr-1" />
                          {user.email}
                        </div>
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <UserRoleBadge role={user.role} />
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <UserStatusBadge status={user.status} />
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {user.lastLoginAt ? (
                      <div className="flex items-center">
                        <Calendar className="h-3 w-3 mr-1" />
                        {new Date(user.lastLoginAt).toLocaleDateString()}
                      </div>
                    ) : (
                      'Never'
                    )}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    <div className="flex items-center">
                      <Calendar className="h-3 w-3 mr-1" />
                      {new Date(user.createdAt).toLocaleDateString()}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium" onClick={(e) => e.stopPropagation()}>
                    <div className="relative">
                      <button
                        className="text-gray-400 hover:text-gray-600"
                        onClick={(e) => {
                          e.preventDefault()
                          // Show dropdown menu
                        }}
                      >
                        <MoreHorizontal className="h-5 w-5" />
                      </button>
                      {/* Dropdown menu would be implemented here */}
                    </div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
})

UserList.displayName = 'UserList'

export default UserList