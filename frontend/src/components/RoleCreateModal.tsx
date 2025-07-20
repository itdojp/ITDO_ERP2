import { useState, useEffect } from 'react'
import { useForm } from 'react-hook-form'
import { X, Shield, Check } from 'lucide-react'
import Button from './ui/Button'
import Input from './ui/Input'
import Select from './ui/Select'
import Loading from './ui/Loading'
import { 
  useCreateRole, 
  usePermissions
} from '../services/permissionApi'
import {
  CreateRoleRequest,
  PermissionResource,
  PERMISSION_RESOURCES,
  groupPermissionsByResource,
  getPermissionDisplayName
} from '../types/permission'

interface RoleCreateModalProps {
  isOpen: boolean
  onClose: () => void
  onSuccess: () => void
}

interface FormData {
  name: string
  code: string
  description: string
  organization_id: string
  permission_ids: number[]
}

export function RoleCreateModal({ isOpen, onClose, onSuccess }: RoleCreateModalProps) {
  const [selectedPermissions, setSelectedPermissions] = useState<Set<number>>(new Set())
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedResource, setSelectedResource] = useState<string>('')

  const {
    register,
    handleSubmit,
    reset,
    setValue,
    watch,
    formState: { errors, isSubmitting }
  } = useForm<FormData>({
    defaultValues: {
      name: '',
      code: '',
      description: '',
      organization_id: '',
      permission_ids: []
    }
  })

  const { data: permissionsResponse, isLoading: permissionsLoading } = usePermissions({
    search: searchQuery,
    resource: (selectedResource as PermissionResource) || undefined
  })

  const createRoleMutation = useCreateRole()

  const permissions = permissionsResponse?.items || []
  const groupedPermissions = groupPermissionsByResource(permissions)

  // Watch name field to auto-generate code
  const nameValue = watch('name')
  useEffect(() => {
    if (nameValue) {
      const generatedCode = nameValue
        .toLowerCase()
        .replace(/[^a-zA-Z0-9\s]/g, '')
        .replace(/\s+/g, '_')
      setValue('code', generatedCode)
    }
  }, [nameValue, setValue])

  // Update form when permissions change
  useEffect(() => {
    setValue('permission_ids', Array.from(selectedPermissions))
  }, [selectedPermissions, setValue])

  const handlePermissionToggle = (permissionId: number) => {
    setSelectedPermissions(prev => {
      const newSet = new Set(prev)
      if (newSet.has(permissionId)) {
        newSet.delete(permissionId)
      } else {
        newSet.add(permissionId)
      }
      return newSet
    })
  }

  const handleResourceToggle = (resource: string) => {
    const resourcePermissions = permissions.filter(p => p.resource === resource)
    const allSelected = resourcePermissions.every(p => selectedPermissions.has(p.id))
    
    setSelectedPermissions(prev => {
      const newSet = new Set(prev)
      if (allSelected) {
        // Deselect all permissions for this resource
        resourcePermissions.forEach(p => newSet.delete(p.id))
      } else {
        // Select all permissions for this resource
        resourcePermissions.forEach(p => newSet.add(p.id))
      }
      return newSet
    })
  }

  const onSubmit = async (data: FormData) => {
    try {
      const roleData: CreateRoleRequest = {
        name: data.name,
        code: data.code,
        description: data.description || undefined,
        permission_ids: Array.from(selectedPermissions),
        organization_id: data.organization_id ? parseInt(data.organization_id) : undefined
      }

      await createRoleMutation.mutateAsync(roleData)
      onSuccess()
      handleClose()
    } catch (error) {
      // Error handling - could be logged to monitoring service in production
    }
  }

  const handleClose = () => {
    reset()
    setSelectedPermissions(new Set())
    setSearchQuery('')
    setSelectedResource('')
    onClose()
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg w-full max-w-4xl max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <div className="flex items-center gap-2">
            <Shield className="h-6 w-6 text-blue-600" />
            <h2 className="text-xl font-semibold text-gray-900">Create New Role</h2>
          </div>
          <Button variant="ghost" onClick={handleClose}>
            <X className="h-5 w-5" />
          </Button>
        </div>

        <form onSubmit={handleSubmit(onSubmit)} className="flex flex-col h-full">
          <div className="flex-1 overflow-y-auto">
            <div className="p-6 space-y-6">
              {/* Basic Information */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <Input
                  label="Role Name"
                  {...register('name', { 
                    required: 'Role name is required',
                    minLength: { value: 2, message: 'Role name must be at least 2 characters' }
                  })}
                  error={!!errors.name}
                  errorMessage={errors.name?.message}
                  data-testid="role-name"
                />
                <Input
                  label="Role Code"
                  {...register('code', { 
                    required: 'Role code is required',
                    pattern: {
                      value: /^[a-z0-9_]+$/,
                      message: 'Role code must contain only lowercase letters, numbers, and underscores'
                    }
                  })}
                  error={!!errors.code}
                  errorMessage={errors.code?.message}
                  data-testid="role-code"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Description
                </label>
                <textarea
                  {...register('description')}
                  rows={3}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
                  data-testid="role-description"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Organization (Optional)
                </label>
                <select
                  {...register('organization_id')}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
                >
                  <option value="">System-wide Role</option>
                  <option value="1">Test Organization</option>
                </select>
              </div>

              {/* Permission Selection */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-4">
                  Permissions ({selectedPermissions.size} selected)
                </label>

                {/* Permission Search and Filter */}
                <div className="mb-4 flex gap-4">
                  <div className="flex-1">
                    <Input
                      placeholder="Search permissions..."
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                    />
                  </div>
                  <Select
                    placeholder="Filter by resource"
                    value={selectedResource}
                    onChange={(value) => setSelectedResource(Array.isArray(value) ? value[0] : value)}
                    options={[
                      { value: '', label: 'All Resources' },
                      ...PERMISSION_RESOURCES.map(resource => ({
                        value: resource.value,
                        label: resource.label
                      }))
                    ]}
                  />
                </div>

                {/* Permission List */}
                {permissionsLoading ? (
                  <Loading message="Loading permissions..." />
                ) : (
                  <div className="border border-gray-200 rounded-lg max-h-96 overflow-y-auto">
                    {Object.entries(groupedPermissions).map(([resource, resourcePermissions]) => {
                      const resourceLabel = PERMISSION_RESOURCES.find(r => r.value === resource)?.label || resource
                      const allSelected = resourcePermissions.every(p => selectedPermissions.has(p.id))
                      const someSelected = resourcePermissions.some(p => selectedPermissions.has(p.id))

                      return (
                        <div key={resource} className="border-b border-gray-100 last:border-b-0">
                          {/* Resource Header */}
                          <div 
                            className="p-3 bg-gray-50 cursor-pointer hover:bg-gray-100 transition-colors"
                            onClick={() => handleResourceToggle(resource)}
                          >
                            <div className="flex items-center justify-between">
                              <span className="font-medium text-gray-900">{resourceLabel}</span>
                              <div className="flex items-center gap-2">
                                <span className="text-sm text-gray-500">
                                  {resourcePermissions.filter(p => selectedPermissions.has(p.id)).length} / {resourcePermissions.length}
                                </span>
                                <div className={`w-4 h-4 border-2 rounded flex items-center justify-center ${
                                  allSelected ? 'bg-blue-600 border-blue-600' :
                                  someSelected ? 'bg-blue-100 border-blue-600' :
                                  'border-gray-300'
                                }`}>
                                  {allSelected && <Check className="h-3 w-3 text-white" />}
                                  {someSelected && !allSelected && <div className="w-2 h-2 bg-blue-600 rounded" />}
                                </div>
                              </div>
                            </div>
                          </div>

                          {/* Permission Items */}
                          <div className="divide-y divide-gray-100">
                            {resourcePermissions.map(permission => (
                              <div 
                                key={permission.id}
                                className="p-3 hover:bg-gray-50 cursor-pointer transition-colors"
                                onClick={() => handlePermissionToggle(permission.id)}
                              >
                                <div className="flex items-center justify-between">
                                  <div>
                                    <div className="font-medium text-sm text-gray-900">
                                      {getPermissionDisplayName(permission)}
                                    </div>
                                    <div className="text-xs text-gray-500">{permission.code}</div>
                                    {permission.description && (
                                      <div className="text-xs text-gray-500 mt-1">{permission.description}</div>
                                    )}
                                  </div>
                                  <input
                                    type="checkbox"
                                    checked={selectedPermissions.has(permission.id)}
                                    onChange={() => handlePermissionToggle(permission.id)}
                                    className="h-4 w-4 text-blue-600 rounded border-gray-300"
                                    data-testid={`permission-${permission.code}`}
                                  />
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>
                      )
                    })}
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Footer */}
          <div className="flex justify-end gap-2 p-6 border-t border-gray-200">
            <Button type="button" variant="outline" onClick={handleClose}>
              Cancel
            </Button>
            <Button 
              type="submit" 
              disabled={isSubmitting || createRoleMutation.isPending}
              data-testid="submit-role"
            >
              {isSubmitting || createRoleMutation.isPending ? 'Creating...' : 'Create Role'}
            </Button>
          </div>
        </form>
      </div>
    </div>
  )
}