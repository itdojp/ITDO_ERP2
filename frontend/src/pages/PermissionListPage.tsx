import { useState, useCallback } from 'react'
import { 
  Shield, 
  Search, 
  Filter, 
  Plus, 
  Edit, 
  Trash2,
  Users,
  Settings,
  BarChart3,
  Check
} from 'lucide-react'
import Button from '../components/ui/Button'
import Input from '../components/ui/Input'
import Select from '../components/ui/Select'
import Loading from '../components/ui/Loading'
import Alert from '../components/ui/Alert'
import Toast from '../components/ui/Toast'
import { RoleCreateModal } from '../components/RoleCreateModal'
import { RoleEditModal } from '../components/RoleEditModal'
import {
  useRoles,
  usePermissions,
  useRoleStatistics,
  useDeleteRole
} from '../services/permissionApi'
import {
  Role,
  Permission,
  RoleFilters,
  PermissionFilters,
  PERMISSION_RESOURCES,
  PERMISSION_ACTIONS,
  getPermissionDisplayName,
  groupPermissionsByResource
} from '../types/permission'

interface RoleItemProps {
  role: Role
  onEdit: (role: Role) => void
  onDelete: (role: Role) => void
  onViewPermissions: (role: Role) => void
}

function RoleItem({ role, onEdit, onDelete, onViewPermissions }: RoleItemProps) {
  return (
    <div className="bg-white rounded-lg border p-4 hover:shadow-md transition-shadow" data-testid="role-item">
      <div className="flex items-start justify-between mb-3">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-1">
            <h3 className="text-lg font-semibold text-gray-900">{role.name}</h3>
            {role.is_system && (
              <span className="px-2 py-1 bg-blue-100 text-blue-800 text-xs font-medium rounded">
                System
              </span>
            )}
          </div>
          {role.description && (
            <p className="text-sm text-gray-600 mb-2">{role.description}</p>
          )}
          <div className="flex items-center gap-4 text-sm text-gray-500">
            <span>Code: {role.code}</span>
            <span>{role.permissions.length} permissions</span>
            {role.organization_id && (
              <span>Org: {role.organization_id}</span>
            )}
          </div>
        </div>
        <div className="flex items-center gap-2 ml-4">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => onViewPermissions(role)}
            data-testid="view-permissions"
          >
            <Shield className="h-4 w-4" />
          </Button>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => onEdit(role)}
            data-testid="edit-role"
          >
            <Edit className="h-4 w-4" />
          </Button>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => onDelete(role)}
            data-testid="delete-role"
            disabled={role.is_system}
          >
            <Trash2 className="h-4 w-4 text-red-600" />
          </Button>
        </div>
      </div>
      
      <div className="flex flex-wrap gap-1">
        {role.permissions.slice(0, 5).map(permission => (
          <span
            key={permission.id}
            className="px-2 py-1 bg-gray-100 text-gray-700 text-xs rounded"
          >
            {permission.code}
          </span>
        ))}
        {role.permissions.length > 5 && (
          <span className="px-2 py-1 bg-gray-100 text-gray-500 text-xs rounded">
            +{role.permissions.length - 5} more
          </span>
        )}
      </div>
    </div>
  )
}

interface PermissionGroupProps {
  resource: string
  permissions: Permission[]
}

function PermissionGroup({ resource, permissions }: PermissionGroupProps) {
  const resourceLabel = PERMISSION_RESOURCES.find(r => r.value === resource)?.label || resource

  return (
    <div className="bg-white rounded-lg border p-4">
      <h4 className="font-medium text-gray-900 mb-3">{resourceLabel}</h4>
      <div className="space-y-2">
        {permissions.map(permission => (
          <div 
            key={permission.id} 
            className="flex items-center justify-between py-2 px-3 bg-gray-50 rounded"
            data-testid="permission-item"
          >
            <div>
              <span className="font-medium text-sm">{getPermissionDisplayName(permission)}</span>
              <span className="text-xs text-gray-500 ml-2">({permission.code})</span>
            </div>
            <div className="flex items-center gap-2">
              <span className={`px-2 py-1 rounded text-xs font-medium ${
                permission.action === 'read' ? 'bg-green-100 text-green-800' :
                permission.action === 'create' ? 'bg-blue-100 text-blue-800' :
                permission.action === 'update' ? 'bg-yellow-100 text-yellow-800' :
                'bg-red-100 text-red-800'
              }`}>
                {permission.action}
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

interface StatisticsCardProps {
  title: string
  value: string | number
  icon: React.ReactNode
  color: string
}

function StatisticsCard({ title, value, icon, color }: StatisticsCardProps) {
  return (
    <div className="bg-white p-4 rounded-lg border">
      <div className="flex items-center">
        <div className={`p-2 rounded-lg ${color}`}>
          {icon}
        </div>
        <div className="ml-3">
          <p className="text-sm font-medium text-gray-500">{title}</p>
          <p className="text-2xl font-bold text-gray-900">{value}</p>
        </div>
      </div>
    </div>
  )
}

export function PermissionListPage() {
  
  // State management
  const [viewMode, setViewMode] = useState<'roles' | 'permissions'>('roles')
  const [roleFilters, setRoleFilters] = useState<RoleFilters>({})
  const [permissionFilters, setPermissionFilters] = useState<PermissionFilters>({})
  const [showFilters, setShowFilters] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedRole, setSelectedRole] = useState<Role | null>(null)
  const [toastMessage, setToastMessage] = useState<{ type: 'success' | 'error'; message: string } | null>(null)
  
  // Modal states
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [showEditModal, setShowEditModal] = useState(false)
  const [showDeleteDialog, setShowDeleteDialog] = useState(false)
  const [editingRole, setEditingRole] = useState<Role | null>(null)
  const [deletingRole, setDeletingRole] = useState<Role | null>(null)

  // Queries
  const { 
    data: rolesResponse, 
    isLoading: rolesLoading, 
    error: rolesError 
  } = useRoles(roleFilters)

  const { 
    data: permissionsResponse, 
    isLoading: permissionsLoading, 
    error: permissionsError 
  } = usePermissions(permissionFilters)

  const { data: statistics } = useRoleStatistics()

  const roles = rolesResponse?.items || []
  const permissions = permissionsResponse?.items || []
  const groupedPermissions = groupPermissionsByResource(permissions)

  // Mutations
  const deleteRoleMutation = useDeleteRole()

  // Event handlers
  const handleSearch = useCallback((value: string) => {
    setSearchQuery(value)
    if (viewMode === 'roles') {
      setRoleFilters(prev => ({ ...prev, search: value || undefined }))
    } else {
      setPermissionFilters(prev => ({ ...prev, search: value || undefined }))
    }
  }, [viewMode])

  const handleRoleFilterChange = useCallback((key: keyof RoleFilters, value: string | boolean | number | undefined) => {
    setRoleFilters(prev => ({ ...prev, [key]: value }))
  }, [])

  const handlePermissionFilterChange = useCallback((key: keyof PermissionFilters, value: string) => {
    setPermissionFilters(prev => ({ ...prev, [key]: value || undefined }))
  }, [])

  const handleCreateRole = () => {
    setShowCreateModal(true)
  }

  const handleEditRole = useCallback((role: Role) => {
    setEditingRole(role)
    setShowEditModal(true)
  }, [])

  const handleDeleteRole = useCallback((role: Role) => {
    setDeletingRole(role)
    setShowDeleteDialog(true)
  }, [])

  const handleViewPermissions = useCallback((role: Role) => {
    setSelectedRole(role)
  }, [])

  const handleConfirmDelete = async () => {
    if (!deletingRole) return

    try {
      await deleteRoleMutation.mutateAsync(deletingRole.id)
      setToastMessage({ type: 'success', message: 'Role deleted successfully' })
      setShowDeleteDialog(false)
      setDeletingRole(null)
    } catch {
      setToastMessage({ type: 'error', message: 'Failed to delete role' })
    }
  }

  const clearFilters = () => {
    if (viewMode === 'roles') {
      setRoleFilters({})
    } else {
      setPermissionFilters({})
    }
    setSearchQuery('')
  }

  // Loading state
  if (rolesLoading && viewMode === 'roles') {
    return <Loading message="Loading roles..." />
  }

  if (permissionsLoading && viewMode === 'permissions') {
    return <Loading message="Loading permissions..." />
  }

  // Error state
  if (rolesError && viewMode === 'roles' && !rolesResponse) {
    return (
      <Alert 
        variant="error" 
        title="Failed to load roles" 
        message="Please try again later." 
      />
    )
  }

  if (permissionsError && viewMode === 'permissions' && !permissionsResponse) {
    return (
      <Alert 
        variant="error" 
        title="Failed to load permissions" 
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
            <Shield className="h-8 w-8" />
            Permissions & Roles
          </h1>
          <p className="text-gray-600 mt-1">
            Manage system roles and permissions
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Select
            value={viewMode}
            onChange={(value) => setViewMode(Array.isArray(value) ? value[0] as 'roles' | 'permissions' : value as 'roles' | 'permissions')}
            options={[
              { value: 'roles', label: 'Roles' },
              { value: 'permissions', label: 'Permissions' }
            ]}
            size="sm"
          />
          {viewMode === 'roles' && (
            <Button onClick={handleCreateRole} data-testid="create-role-btn">
              <Plus className="h-4 w-4 mr-2" />
              Create Role
            </Button>
          )}
        </div>
      </div>

      {/* Statistics */}
      {statistics && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <StatisticsCard
            title="Total Roles"
            value={statistics.total_roles}
            icon={<Shield className="h-6 w-6 text-white" />}
            color="bg-blue-500"
          />
          <StatisticsCard
            title="System Roles"
            value={statistics.system_roles}
            icon={<Settings className="h-6 w-6 text-white" />}
            color="bg-green-500"
          />
          <StatisticsCard
            title="Custom Roles"
            value={statistics.custom_roles}
            icon={<Users className="h-6 w-6 text-white" />}
            color="bg-purple-500"
          />
          <StatisticsCard
            title="Total Permissions"
            value={statistics.total_permissions}
            icon={<BarChart3 className="h-6 w-6 text-white" />}
            color="bg-orange-500"
          />
        </div>
      )}

      {/* Controls */}
      <div className="flex flex-col sm:flex-row gap-4">
        <div className="flex-1">
          <Input
            placeholder={`Search ${viewMode}...`}
            value={searchQuery}
            onChange={(e) => handleSearch(e.target.value)}
            leftIcon={<Search className="h-4 w-4" />}
            data-testid="search-input"
          />
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            onClick={() => setShowFilters(!showFilters)}
          >
            <Filter className="h-4 w-4 mr-2" />
            Filters
          </Button>
          <Button
            variant="outline"
            onClick={clearFilters}
          >
            Clear
          </Button>
        </div>
      </div>

      {/* Advanced Filters */}
      {showFilters && (
        <div className="bg-gray-50 p-4 rounded-lg space-y-4">
          {viewMode === 'roles' ? (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <Select
                label="Organization"
                value={roleFilters.organization_id?.toString() || ''}
                onChange={(value) => {
                  const orgId = Array.isArray(value) ? parseInt(value[0]) : parseInt(value)
                  handleRoleFilterChange('organization_id', isNaN(orgId) ? undefined : orgId)
                }}
                options={[
                  { value: '', label: 'All Organizations' },
                  { value: '1', label: 'Test Organization' }
                ]}
              />
              <Select
                label="Type"
                value={roleFilters.is_system?.toString() || ''}
                onChange={(value) => {
                  const boolValue = Array.isArray(value) ? value[0] : value
                  handleRoleFilterChange('is_system', boolValue === 'true' ? true : boolValue === 'false' ? false : undefined)
                }}
                options={[
                  { value: '', label: 'All Types' },
                  { value: 'true', label: 'System Roles' },
                  { value: 'false', label: 'Custom Roles' }
                ]}
              />
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Select
                label="Resource"
                value={permissionFilters.resource || ''}
                onChange={(value) => handlePermissionFilterChange('resource', Array.isArray(value) ? value[0] : value)}
                options={[
                  { value: '', label: 'All Resources' },
                  ...PERMISSION_RESOURCES.map(resource => ({ value: resource.value, label: resource.label }))
                ]}
              />
              <Select
                label="Action"
                value={permissionFilters.action || ''}
                onChange={(value) => handlePermissionFilterChange('action', Array.isArray(value) ? value[0] : value)}
                options={[
                  { value: '', label: 'All Actions' },
                  ...PERMISSION_ACTIONS.map(action => ({ value: action.value, label: action.label }))
                ]}
              />
            </div>
          )}
        </div>
      )}

      {/* Content */}
      {viewMode === 'roles' ? (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Role List */}
          <div className="lg:col-span-2">
            <div className="bg-white rounded-lg border">
              <div className="p-4 border-b border-gray-200">
                <h3 className="text-lg font-medium text-gray-900">Roles</h3>
                <p className="text-sm text-gray-500">
                  {roles.length} role{roles.length !== 1 ? 's' : ''} found
                </p>
              </div>
              <div className="p-4" data-testid="role-list">
                {roles.length > 0 ? (
                  <div className="space-y-4">
                    {roles.map((role) => (
                      <RoleItem
                        key={role.id}
                        role={role}
                        onEdit={handleEditRole}
                        onDelete={handleDeleteRole}
                        onViewPermissions={handleViewPermissions}
                      />
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-8">
                    <Shield className="mx-auto h-12 w-12 text-gray-400" />
                    <h3 className="mt-2 text-sm font-medium text-gray-900">No roles found</h3>
                    <p className="mt-1 text-sm text-gray-500">
                      Get started by creating your first role.
                    </p>
                    <Button onClick={handleCreateRole} className="mt-4">
                      <Plus className="h-4 w-4 mr-2" />
                      Create Role
                    </Button>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Permission List for Selected Role */}
          <div>
            <div className="bg-white rounded-lg border">
              <div className="p-4 border-b border-gray-200">
                <h3 className="text-lg font-medium text-gray-900">
                  {selectedRole ? `${selectedRole.name} Permissions` : 'Role Permissions'}
                </h3>
                <p className="text-sm text-gray-500">
                  {selectedRole ? `${selectedRole.permissions.length} permissions` : 'Select a role to view permissions'}
                </p>
              </div>
              <div className="p-4" data-testid="permission-list">
                {selectedRole ? (
                  <div className="space-y-2">
                    {selectedRole.permissions.map((permission) => (
                      <div 
                        key={permission.id}
                        className="flex items-center justify-between py-2 px-3 bg-gray-50 rounded"
                        data-testid="permission-item"
                      >
                        <span className="text-sm font-medium">{permission.code}</span>
                        <Check className="h-4 w-4 text-green-600" />
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-8 text-gray-500">
                    <Shield className="mx-auto h-8 w-8 mb-2" />
                    <p className="text-sm">Select a role to view its permissions</p>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      ) : (
        <div className="space-y-6">
          {Object.entries(groupedPermissions).map(([resource, resourcePermissions]) => (
            <PermissionGroup
              key={resource}
              resource={resource}
              permissions={resourcePermissions}
            />
          ))}
        </div>
      )}

      {/* Toast Notifications */}
      {toastMessage && (
        <Toast
          variant={toastMessage.type === 'success' ? 'success' : 'error'}
          title={toastMessage.type === 'success' ? 'Success' : 'Error'}
          message={toastMessage.message}
          onClose={() => setToastMessage(null)}
          data-testid="success-message"
        />
      )}

      {/* Delete Confirmation Dialog */}
      {showDeleteDialog && deletingRole && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-96">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Delete Role</h3>
            <p className="text-sm text-gray-600 mb-6">
              Are you sure you want to delete the role "{deletingRole.name}"? This action cannot be undone.
            </p>
            <div className="flex justify-end gap-2">
              <Button
                variant="outline"
                onClick={() => {
                  setShowDeleteDialog(false)
                  setDeletingRole(null)
                }}
              >
                Cancel
              </Button>
              <Button
                variant="default"
                onClick={handleConfirmDelete}
                data-testid="confirm-delete"
                disabled={deleteRoleMutation.isPending}
              >
                {deleteRoleMutation.isPending ? 'Deleting...' : 'Delete'}
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Modals */}
      <RoleCreateModal
        isOpen={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        onSuccess={() => setToastMessage({ type: 'success', message: 'Role created successfully' })}
      />

      <RoleEditModal
        isOpen={showEditModal}
        onClose={() => {
          setShowEditModal(false)
          setEditingRole(null)
        }}
        onSuccess={() => setToastMessage({ type: 'success', message: 'Role updated successfully' })}
        role={editingRole}
      />
    </div>
  )
}