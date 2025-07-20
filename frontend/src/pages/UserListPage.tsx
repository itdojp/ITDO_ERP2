import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Search, Filter, Plus, Edit, Trash2, Users } from 'lucide-react'
import Button from '../components/ui/Button'
import Input from '../components/ui/Input'
import Select from '../components/ui/Select'
import Loading from '../components/ui/Loading'
import Alert from '../components/ui/Alert'
import Toast from '../components/ui/Toast'
import { userApiService, userQueryKeys } from '../services/userApi'
import { UserFilters, PaginationParams } from '../types/user'

export function UserListPage() {
  const queryClient = useQueryClient()
  
  // State management
  const [filters, setFilters] = useState<UserFilters>({})
  const [pagination, setPagination] = useState<PaginationParams>({ page: 1, limit: 10 })
  const [selectedUsers, setSelectedUsers] = useState<number[]>([])
  const [showFilters, setShowFilters] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')
  const [toastMessage, setToastMessage] = useState<{ type: 'success' | 'error'; message: string } | null>(null)

  // Query for user list
  const { 
    data: userListResponse, 
    isLoading, 
    error, 
 
  } = useQuery({
    queryKey: userQueryKeys.list(filters, pagination),
    queryFn: () => userApiService.getUsersMock(filters, pagination), // Using mock for development
    keepPreviousData: true
  })

  // Query for user roles
  const { data: roles = [] } = useQuery({
    queryKey: userQueryKeys.roles(),
    queryFn: () => userApiService.getUserRoles()
  })

  // Delete user mutation
  const deleteUserMutation = useMutation({
    mutationFn: (userId: number) => userApiService.deleteUser(userId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: userQueryKeys.lists() })
      setToastMessage({ type: 'success', message: 'User deleted successfully' })
    },
    onError: () => {
      setToastMessage({ type: 'error', message: 'Failed to delete user' })
    }
  })

  // Bulk action mutation
  const bulkActionMutation = useMutation({
    mutationFn: userApiService.bulkAction,
    onSuccess: (result) => {
      queryClient.invalidateQueries({ queryKey: userQueryKeys.lists() })
      setSelectedUsers([])
      setToastMessage({ 
        type: 'success', 
        message: `${result.success} users ${selectedUsers.length > 1 ? 'processed' : 'processed'} successfully` 
      })
    },
    onError: () => {
      setToastMessage({ type: 'error', message: 'Bulk action failed' })
    }
  })

  // Computed values
  const users = userListResponse?.items || []
  const total = userListResponse?.total || 0
  const totalPages = Math.ceil(total / pagination.limit)
  const isAllSelected = selectedUsers.length === users.length && users.length > 0
  const isSomeSelected = selectedUsers.length > 0 && selectedUsers.length < users.length

  // Event handlers
  const handleSearch = (value: string) => {
    setSearchQuery(value)
    setFilters(prev => ({ ...prev, search: value || undefined }))
    setPagination(prev => ({ ...prev, page: 1 }))
  }

  const handleFilterChange = (key: keyof UserFilters, value: string) => {
    setFilters(prev => ({ ...prev, [key]: value || undefined }))
    setPagination(prev => ({ ...prev, page: 1 }))
  }

  const handlePageChange = (newPage: number) => {
    setPagination(prev => ({ ...prev, page: newPage }))
  }

  const handleSelectAll = () => {
    if (isAllSelected) {
      setSelectedUsers([])
    } else {
      setSelectedUsers(users.map(user => user.id))
    }
  }

  const handleSelectUser = (userId: number) => {
    setSelectedUsers(prev => 
      prev.includes(userId) 
        ? prev.filter(id => id !== userId)
        : [...prev, userId]
    )
  }

  const handleDeleteUser = (userId: number) => {
    if (window.confirm('Are you sure you want to delete this user?')) {
      deleteUserMutation.mutate(userId)
    }
  }

  const handleBulkAction = (action: 'activate' | 'deactivate' | 'delete') => {
    const actionText = action === 'activate' ? 'activate' : action === 'deactivate' ? 'deactivate' : 'delete'
    if (window.confirm(`Are you sure you want to ${actionText} ${selectedUsers.length} selected users?`)) {
      bulkActionMutation.mutate({
        user_ids: selectedUsers,
        action
      })
    }
  }

  // Loading state
  if (isLoading && !userListResponse) {
    return <Loading message="Loading users..." />
  }

  // Error state
  if (error && !userListResponse) {
    return (
      <Alert 
        variant="error" 
        title="Failed to load users" 
        message="Please try again later." 
      />
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
            <Users className="h-8 w-8" />
            User Management
          </h1>
          <p className="text-gray-600 mt-1">
            Manage users, roles, and permissions
          </p>
        </div>
        <Button onClick={() => setToastMessage({ type: 'success', message: 'Add User modal would open here' })}>
          <Plus className="h-4 w-4 mr-2" />
          Add User
        </Button>
      </div>

      {/* Search and Filters */}
      <div className="flex flex-col sm:flex-row gap-4">
        <div className="flex-1">
          <Input
            placeholder="Search users..."
            value={searchQuery}
            onChange={(e) => handleSearch(e.target.value)}
            leftIcon={<Search className="h-4 w-4" />}
          />
        </div>
        <Button
          variant="outline"
          onClick={() => setShowFilters(!showFilters)}
        >
          <Filter className="h-4 w-4 mr-2" />
          Filter
        </Button>
      </div>

      {/* Filter Panel */}
      {showFilters && (
        <div className="bg-gray-50 p-4 rounded-lg space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Select
              label="Role"
              value={filters.role || ''}
              onChange={(value) => handleFilterChange('role', Array.isArray(value) ? value[0] : value)}
              options={[
                { value: '', label: 'All Roles' },
                ...roles.map(role => ({ value: role.id, label: role.name }))
              ]}
            />
            <Select
              label="Status"
              value={filters.status || ''}
              onChange={(value) => handleFilterChange('status', Array.isArray(value) ? value[0] : value)}
              options={[
                { value: '', label: 'All Status' },
                { value: 'active', label: 'Active' },
                { value: 'inactive', label: 'Inactive' }
              ]}
            />
            <div className="flex items-end">
              <Button
                variant="outline"
                onClick={() => {
                  setFilters({})
                  setSearchQuery('')
                  setPagination({ page: 1, limit: 10 })
                }}
              >
                Clear Filters
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Bulk Actions */}
      {selectedUsers.length > 0 && (
        <div className="bg-blue-50 p-4 rounded-lg flex items-center justify-between bulk-actions">
          <span className="text-blue-700 font-medium">
            {selectedUsers.length} users selected
          </span>
          <div className="flex gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => handleBulkAction('activate')}
            >
              Activate Selected
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => handleBulkAction('deactivate')}
            >
              Deactivate Selected
            </Button>
            <Button
              variant="destructive"
              size="sm"
              onClick={() => handleBulkAction('delete')}
            >
              Delete Selected
            </Button>
          </div>
        </div>
      )}

      {/* User Table */}
      <div className="bg-white shadow rounded-lg overflow-hidden">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                <input
                  type="checkbox"
                  checked={isAllSelected}
                  ref={(input) => {
                    if (input) input.indeterminate = isSomeSelected && !isAllSelected
                  }}
                  onChange={handleSelectAll}
                  className="rounded border-gray-300"
                />
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Name
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Email
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Role
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Status
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Last Login
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {users.map((user) => (
              <tr key={user.id} className="hover:bg-gray-50">
                <td className="px-6 py-4 whitespace-nowrap">
                  <input
                    type="checkbox"
                    checked={selectedUsers.includes(user.id)}
                    onChange={() => handleSelectUser(user.id)}
                    className="rounded border-gray-300"
                  />
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="flex items-center">
                    <div className="flex-shrink-0 h-10 w-10">
                      <div className="h-10 w-10 rounded-full bg-gray-300 flex items-center justify-center">
                        <span className="text-sm font-medium text-gray-700">
                          {user.full_name.charAt(0).toUpperCase()}
                        </span>
                      </div>
                    </div>
                    <div className="ml-4">
                      <div className="text-sm font-medium text-gray-900">
                        {user.full_name}
                      </div>
                      {user.phone && (
                        <div className="text-sm text-gray-500">
                          {user.phone}
                        </div>
                      )}
                    </div>
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                  {user.email}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                  {user.roles[0]?.role.name || 'No Role'}
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                    user.is_active 
                      ? 'bg-green-100 text-green-800' 
                      : 'bg-red-100 text-red-800'
                  }`}>
                    {user.is_active ? 'Active' : 'Inactive'}
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {user.last_login_at 
                    ? new Date(user.last_login_at).toLocaleDateString()
                    : 'Never'
                  }
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                  <div className="flex space-x-2">
                    <Button
                      variant="ghost"
                      size="sm"
                      aria-label="Edit"
                      onClick={() => setToastMessage({ type: 'success', message: 'Edit modal would open here' })}
                    >
                      <Edit className="h-4 w-4" />
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      aria-label="Delete"
                      onClick={() => handleDeleteUser(user.id)}
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>

        {users.length === 0 && (
          <div className="text-center py-12">
            <Users className="mx-auto h-12 w-12 text-gray-400" />
            <h3 className="mt-2 text-sm font-medium text-gray-900">No users found</h3>
            <p className="mt-1 text-sm text-gray-500">
              {filters.search || filters.role || filters.status 
                ? 'Try adjusting your search or filter criteria.'
                : 'Get started by creating a new user.'
              }
            </p>
          </div>
        )}
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="pagination flex items-center justify-between">
          <div className="text-sm text-gray-700">
            Showing {((pagination.page - 1) * pagination.limit) + 1} to {Math.min(pagination.page * pagination.limit, total)} of {total} results
          </div>
          <div className="flex space-x-2">
            <Button
              variant="outline"
              disabled={pagination.page <= 1}
              onClick={() => handlePageChange(pagination.page - 1)}
            >
              Previous
            </Button>
            {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
              const pageNum = pagination.page - 2 + i
              if (pageNum < 1 || pageNum > totalPages) return null
              return (
                <Button
                  key={pageNum}
                  variant={pageNum === pagination.page ? "primary" : "outline"}
                  onClick={() => handlePageChange(pageNum)}
                >
                  {pageNum}
                </Button>
              )
            })}
            <Button
              variant="outline"
              disabled={pagination.page >= totalPages}
              onClick={() => handlePageChange(pagination.page + 1)}
            >
              Next
            </Button>
          </div>
        </div>
      )}

      {/* Toast Notifications */}
      {toastMessage && (
        <Toast
          variant={toastMessage.type === 'success' ? 'success' : 'error'}
          title={toastMessage.type === 'success' ? 'Success' : 'Error'}
          message={toastMessage.message}
          onClose={() => setToastMessage(null)}
          className={`toast-${toastMessage.type}`}
        />
      )}
    </div>
  )
}