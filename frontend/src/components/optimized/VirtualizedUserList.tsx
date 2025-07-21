import React from 'react'
import { User, Search, Filter, MoreHorizontal, Mail, Calendar, CheckCircle, XCircle, Clock, Shield } from 'lucide-react'
import { cn } from '../../lib/utils'
import { User as UserType, UserRole, UserStatus } from '../../services/api/types'
import { useVirtualization } from '../../hooks/useVirtualization'
import { usePerformanceMonitor } from '../../hooks/usePerformanceMonitor'
import { useMemoizedCallback, useThrottledCallback } from '../../hooks/useMemoizedCallback'

export interface VirtualizedUserListProps {
  users: UserType[]
  height: number
  loading?: boolean
  onUserSelect?: (user: UserType) => void
  onUserEdit?: (user: UserType) => void
  onUserDelete?: (user: UserType) => void
  onSearch?: (query: string) => void
  onFilter?: (filters: Record<string, any>) => void
  searchQuery?: string
  selectedUsers?: string[]
  onSelectionChange?: (userIds: string[]) => void
  className?: string
}

const USER_ROW_HEIGHT = 72 // Height of each user row in pixels

// Optimized status badge component with memoization
const UserStatusBadge = React.memo<{ status: UserStatus }>(({ status }) => {
  const statusConfig = React.useMemo(() => ({
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
  }), [])

  const config = statusConfig[status]

  return (
    <span className={cn('inline-flex items-center px-2 py-1 rounded-full text-xs font-medium', config.color)}>
      {config.icon}
      <span className="ml-1 capitalize">{status}</span>
    </span>
  )
})

UserStatusBadge.displayName = 'UserStatusBadge'

// Optimized role badge component with memoization
const UserRoleBadge = React.memo<{ role: UserRole }>(({ role }) => {
  const roleConfig = React.useMemo(() => ({
    [UserRole.ADMIN]: { color: 'bg-purple-100 text-purple-800', icon: <Shield className="h-3 w-3" /> },
    [UserRole.MANAGER]: { color: 'bg-blue-100 text-blue-800', icon: <User className="h-3 w-3" /> },
    [UserRole.MEMBER]: { color: 'bg-green-100 text-green-800', icon: <User className="h-3 w-3" /> },
    [UserRole.VIEWER]: { color: 'bg-gray-100 text-gray-800', icon: <User className="h-3 w-3" /> },
    [UserRole.GUEST]: { color: 'bg-orange-100 text-orange-800', icon: <User className="h-3 w-3" /> },
  }), [])

  const config = roleConfig[role]

  return (
    <span className={cn('inline-flex items-center px-2 py-1 rounded-full text-xs font-medium', config.color)}>
      {config.icon}
      <span className="ml-1 capitalize">{role}</span>
    </span>
  )
})

UserRoleBadge.displayName = 'UserRoleBadge'

// Optimized user row component
const UserRow = React.memo<{
  user: UserType
  index: number
  isSelected: boolean
  onSelect: (user: UserType) => void
  onToggleSelection: (userId: string, checked: boolean) => void
  onAction: (user: UserType, action: string) => void
}>(({ user, index, isSelected, onSelect, onToggleSelection, onAction }) => {
  const handleRowClick = useMemoizedCallback(() => {
    onSelect(user)
  }, [user, onSelect])

  const handleCheckboxChange = useMemoizedCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    e.stopPropagation()
    onToggleSelection(user.id, e.target.checked)
  }, [user.id, onToggleSelection])

  const handleActionClick = useMemoizedCallback((e: React.MouseEvent, action: string) => {
    e.stopPropagation()
    onAction(user, action)
  }, [user, onAction])

  const avatarElement = React.useMemo(() => {
    if (user.avatar) {
      return (
        <img 
          className="h-10 w-10 rounded-full object-cover" 
          src={user.avatar} 
          alt={user.fullName}
          loading="lazy"
        />
      )
    }
    return (
      <div className="h-10 w-10 rounded-full bg-gray-300 flex items-center justify-center">
        <User className="h-6 w-6 text-gray-600" />
      </div>
    )
  }, [user.avatar, user.fullName])

  const lastLoginDisplay = React.useMemo(() => {
    if (user.lastLoginAt) {
      return (
        <div className="flex items-center text-sm text-gray-500">
          <Calendar className="h-3 w-3 mr-1" />
          {new Date(user.lastLoginAt).toLocaleDateString()}
        </div>
      )
    }
    return <span className="text-sm text-gray-500">Never</span>
  }, [user.lastLoginAt])

  const joinedDisplay = React.useMemo(() => (
    <div className="flex items-center text-sm text-gray-500">
      <Calendar className="h-3 w-3 mr-1" />
      {new Date(user.createdAt).toLocaleDateString()}
    </div>
  ), [user.createdAt])

  return (
    <div
      className={cn(
        'flex items-center px-6 py-4 hover:bg-gray-50 cursor-pointer border-b border-gray-100',
        isSelected && 'bg-blue-50'
      )}
      onClick={handleRowClick}
      role="row"
      tabIndex={0}
      data-index={index}
    >
      {/* Checkbox */}
      <div className="flex items-center mr-4">
        <input
          type="checkbox"
          checked={isSelected}
          onChange={handleCheckboxChange}
          className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
          aria-label={`Select ${user.fullName}`}
        />
      </div>

      {/* User Info */}
      <div className="flex items-center flex-1 min-w-0">
        <div className="flex-shrink-0 mr-4">
          {avatarElement}
        </div>
        <div className="min-w-0 flex-1">
          <div className="text-sm font-medium text-gray-900 truncate">{user.fullName}</div>
          <div className="text-sm text-gray-500 flex items-center truncate">
            <Mail className="h-3 w-3 mr-1 flex-shrink-0" />
            {user.email}
          </div>
        </div>
      </div>

      {/* Role */}
      <div className="flex-shrink-0 mr-4">
        <UserRoleBadge role={user.role} />
      </div>

      {/* Status */}
      <div className="flex-shrink-0 mr-4">
        <UserStatusBadge status={user.status} />
      </div>

      {/* Last Login */}
      <div className="flex-shrink-0 mr-4 min-w-0 w-24">
        {lastLoginDisplay}
      </div>

      {/* Joined */}
      <div className="flex-shrink-0 mr-4 min-w-0 w-24">
        {joinedDisplay}
      </div>

      {/* Actions */}
      <div className="flex-shrink-0">
        <button
          className="text-gray-400 hover:text-gray-600 p-1"
          onClick={(e) => handleActionClick(e, 'menu')}
          aria-label={`Actions for ${user.fullName}`}
        >
          <MoreHorizontal className="h-5 w-5" />
        </button>
      </div>
    </div>
  )
})

UserRow.displayName = 'UserRow'

// Main virtualized user list component
export const VirtualizedUserList = React.memo<VirtualizedUserListProps>(({
  users,
  height,
  loading = false,
  onUserSelect,
  onUserEdit,
  onUserDelete,
  onSearch,
  onFilter,
  searchQuery = '',
  selectedUsers = [],
  onSelectionChange,
  className
}) => {
  // Performance monitoring
  const { metrics } = usePerformanceMonitor({
    componentName: 'VirtualizedUserList',
    threshold: 20 // List components can be slightly slower
  })

  const [localSearchQuery, setLocalSearchQuery] = React.useState(searchQuery)

  // Virtualization setup
  const virtualization = useVirtualization(users, {
    itemHeight: USER_ROW_HEIGHT,
    containerHeight: height - 120, // Account for header
    overscan: 5
  })

  const { virtualItems, totalHeight, scrollElementProps, getItemProps } = virtualization

  // Throttled search to avoid excessive API calls
  const throttledSearch = useThrottledCallback((query: string) => {
    onSearch?.(query)
  }, 300, [onSearch])

  // Handle search input changes
  React.useEffect(() => {
    throttledSearch(localSearchQuery)
  }, [localSearchQuery, throttledSearch])

  // Memoized callbacks for performance
  const handleUserSelect = useMemoizedCallback((user: UserType) => {
    onUserSelect?.(user)
  }, [onUserSelect])

  const handleSelectionChange = useMemoizedCallback((userIds: string[]) => {
    onSelectionChange?.(userIds)
  }, [onSelectionChange])

  const handleToggleSelection = useMemoizedCallback((userId: string, checked: boolean) => {
    if (checked) {
      handleSelectionChange([...selectedUsers, userId])
    } else {
      handleSelectionChange(selectedUsers.filter(id => id !== userId))
    }
  }, [selectedUsers, handleSelectionChange])

  const handleSelectAll = useMemoizedCallback((checked: boolean) => {
    if (checked) {
      handleSelectionChange(users.map(user => user.id))
    } else {
      handleSelectionChange([])
    }
  }, [users, handleSelectionChange])

  const handleUserAction = useMemoizedCallback((user: UserType, action: string) => {
    switch (action) {
      case 'edit':
        onUserEdit?.(user)
        break
      case 'delete':
        onUserDelete?.(user)
        break
      default:
        break
    }
  }, [onUserEdit, onUserDelete])

  // Selection state calculations
  const isAllSelected = users.length > 0 && selectedUsers.length === users.length
  const isPartiallySelected = selectedUsers.length > 0 && selectedUsers.length < users.length

  // Render loading skeleton
  const renderLoadingSkeleton = React.useMemo(() => (
    <div className="space-y-4 p-6">
      {Array.from({ length: 5 }).map((_, index) => (
        <div key={index} className="flex items-center space-x-4">
          <div className="h-4 w-4 bg-gray-200 rounded animate-pulse" />
          <div className="h-10 w-10 bg-gray-200 rounded-full animate-pulse" />
          <div className="flex-1 space-y-2">
            <div className="h-4 w-32 bg-gray-200 rounded animate-pulse" />
            <div className="h-3 w-48 bg-gray-200 rounded animate-pulse" />
          </div>
          <div className="h-6 w-16 bg-gray-200 rounded-full animate-pulse" />
          <div className="h-6 w-16 bg-gray-200 rounded-full animate-pulse" />
          <div className="h-4 w-20 bg-gray-200 rounded animate-pulse" />
          <div className="h-4 w-20 bg-gray-200 rounded animate-pulse" />
          <div className="h-8 w-8 bg-gray-200 rounded animate-pulse" />
        </div>
      ))}
    </div>
  ), [])

  if (loading) {
    return (
      <div className={cn('bg-white rounded-lg shadow', className)} style={{ height }}>
        {renderLoadingSkeleton}
      </div>
    )
  }

  return (
    <div className={cn('bg-white rounded-lg shadow flex flex-col', className)} style={{ height }}>
      {/* Header */}
      <div className="flex-shrink-0 px-6 py-4 border-b border-gray-200">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-gray-900 flex items-center">
            <User className="h-5 w-5 mr-2" />
            Users ({users.length})
            {process.env.NODE_ENV === 'development' && (
              <span className="ml-2 text-xs text-gray-500">
                ({metrics.lastRenderTime.toFixed(1)}ms)
              </span>
            )}
          </h2>
          
          {selectedUsers.length > 0 && (
            <div className="text-sm text-gray-600">
              {selectedUsers.length} selected
            </div>
          )}
        </div>

        {/* Search */}
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

      {/* Table Header */}
      <div className="flex-shrink-0 bg-gray-50 px-6 py-3 border-b border-gray-200">
        <div className="flex items-center">
          <div className="flex items-center mr-4">
            <input
              type="checkbox"
              checked={isAllSelected}
              ref={(input) => {
                if (input) input.indeterminate = isPartiallySelected
              }}
              onChange={(e) => handleSelectAll(e.target.checked)}
              className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
              aria-label="Select all users"
            />
          </div>
          <div className="flex-1 grid grid-cols-5 gap-4 text-xs font-medium text-gray-500 uppercase tracking-wider">
            <div>User</div>
            <div>Role</div>
            <div>Status</div>
            <div>Last Login</div>
            <div>Joined</div>
          </div>
          <div className="flex-shrink-0 w-12"></div>
        </div>
      </div>

      {/* Virtualized List */}
      <div className="flex-1 relative overflow-hidden">
        {users.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full">
            <User className="h-12 w-12 text-gray-300 mb-4" />
            <p className="text-gray-500">No users found</p>
            <p className="text-sm text-gray-400 mt-1">
              {searchQuery ? 'Try adjusting your search' : 'Add users to get started'}
            </p>
          </div>
        ) : (
          <div
            {...scrollElementProps}
            className="absolute inset-0 overflow-auto"
          >
            <div style={{ height: totalHeight, position: 'relative' }}>
              {virtualItems.map((virtualItem) => {
                const user = users[virtualItem.index]
                const itemProps = getItemProps(virtualItem.index)
                
                return (
                  <div
                    key={itemProps.key}
                    style={itemProps.style}
                    data-index={itemProps['data-index']}
                  >
                    <UserRow
                      user={user}
                      index={virtualItem.index}
                      isSelected={selectedUsers.includes(user.id)}
                      onSelect={handleUserSelect}
                      onToggleSelection={handleToggleSelection}
                      onAction={handleUserAction}
                    />
                  </div>
                )
              })}
            </div>
          </div>
        )}
      </div>
    </div>
  )
})

VirtualizedUserList.displayName = 'VirtualizedUserList'

export default VirtualizedUserList