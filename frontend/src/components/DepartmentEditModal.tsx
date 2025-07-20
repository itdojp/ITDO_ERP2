import { useState, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { X, Building, Save } from 'lucide-react'
import Button from './ui/Button'
import Input from './ui/Input'
import Select from './ui/Select'
import Textarea from './ui/Textarea'
import Modal from './ui/Modal'
import Loading from './ui/Loading'
import { 
  organizationApiService, 
  organizationQueryKeys 
} from '../services/organizationApi'
import { 
  Department,
  UpdateDepartmentRequest, 
  DepartmentFormData, 
  DepartmentFormErrors,
  DEPARTMENT_TYPES 
} from '../types/organization'

interface DepartmentEditModalProps {
  isOpen: boolean
  onClose: () => void
  onSuccess?: () => void
  department: Department | null
}

export function DepartmentEditModal({
  isOpen,
  onClose,
  onSuccess,
  department
}: DepartmentEditModalProps) {
  const queryClient = useQueryClient()
  
  // Form state
  const [formData, setFormData] = useState<DepartmentFormData>({
    name: '',
    code: '',
    description: '',
    type: '',
    organization_id: 0,
    parent_department_id: undefined,
    manager_id: undefined
  })
  
  const [errors, setErrors] = useState<DepartmentFormErrors>({})
  const [isSubmitting, setIsSubmitting] = useState(false)

  // Populate form when department changes
  useEffect(() => {
    if (isOpen && department) {
      setFormData({
        id: department.id,
        name: department.name,
        code: department.code,
        description: department.description || '',
        type: department.type || '',
        organization_id: department.organization_id,
        parent_department_id: department.parent_department_id,
        manager_id: department.manager_id
      })
      setErrors({})
    }
  }, [isOpen, department])

  // Query for organizations list
  const { data: organizationsResponse } = useQuery({
    queryKey: organizationQueryKeys.list(),
    queryFn: () => organizationApiService.getOrganizations(),
    enabled: isOpen
  })
  const organizations = organizationsResponse?.items || []

  // Query for departments list (for parent selection)
  const { data: departmentsResponse } = useQuery({
    queryKey: organizationQueryKeys.departments(),
    queryFn: () => organizationApiService.getDepartments(),
    enabled: isOpen
  })
  const departments = departmentsResponse?.items || []

  // Query for managers list
  const { data: managers = [] } = useQuery({
    queryKey: ['managers'],
    queryFn: () => organizationApiService.getManagers(),
    enabled: isOpen
  })

  // Update department mutation
  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: UpdateDepartmentRequest }) => 
      organizationApiService.updateDepartment(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: organizationQueryKeys.tree() })
      queryClient.invalidateQueries({ queryKey: organizationQueryKeys.departments() })
      onSuccess?.()
      onClose()
    },
    onError: () => {
      // Failed to update department - error is handled by mutation
    }
  })

  // Validation
  const validateForm = (): boolean => {
    const newErrors: DepartmentFormErrors = {}

    if (!formData.name.trim()) {
      newErrors.name = 'Department name is required'
    }

    if (!formData.code.trim()) {
      newErrors.code = 'Department code is required'
    } else if (!/^[A-Z0-9_]+$/.test(formData.code)) {
      newErrors.code = 'Code must contain only uppercase letters, numbers, and underscores'
    }

    if (!formData.organization_id) {
      newErrors.organization_id = 'Organization is required'
    }

    // Prevent setting self as parent
    if (formData.parent_department_id === formData.id) {
      newErrors.parent_department_id = 'Department cannot be its own parent'
    }

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  // Handlers
  const handleInputChange = (field: keyof DepartmentFormData, value: string | number | undefined) => {
    setFormData(prev => ({ ...prev, [field]: value }))
    if (errors[field as keyof DepartmentFormErrors]) {
      setErrors(prev => ({ ...prev, [field]: undefined }))
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!validateForm() || !department) {
      return
    }

    setIsSubmitting(true)
    try {
      const updateData: UpdateDepartmentRequest = {
        name: formData.name !== department.name ? formData.name : undefined,
        code: formData.code !== department.code ? formData.code : undefined,
        description: formData.description !== department.description ? formData.description : undefined,
        type: formData.type !== department.type ? formData.type : undefined,
        parent_department_id: formData.parent_department_id !== department.parent_department_id 
          ? formData.parent_department_id : undefined,
        manager_id: formData.manager_id !== department.manager_id ? formData.manager_id : undefined
      }

      // Only send fields that have changed
      const hasChanges = Object.values(updateData).some(value => value !== undefined)
      if (hasChanges) {
        await updateMutation.mutateAsync({ id: department.id, data: updateData })
      } else {
        onClose() // No changes to save
      }
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleClose = () => {
    if (!isSubmitting) {
      onClose()
    }
  }

  if (!department) return null

  return (
    <Modal isOpen={isOpen} onClose={handleClose} size="lg">
      <div className="p-6">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-blue-100 rounded-lg">
              <Building className="h-6 w-6 text-blue-600" />
            </div>
            <div>
              <h2 className="text-xl font-semibold text-gray-900">Edit Department</h2>
              <p className="text-sm text-gray-500">Update department information and structure</p>
            </div>
          </div>
          <Button
            variant="ghost"
            size="sm"
            onClick={handleClose}
            disabled={isSubmitting}
          >
            <X className="h-5 w-5" />
          </Button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Basic Information */}
          <div className="space-y-4">
            <h3 className="text-lg font-medium text-gray-900">Basic Information</h3>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <Input
                  label="Department Name"
                  value={formData.name}
                  onChange={(e) => handleInputChange('name', e.target.value)}
                  error={!!errors.name}
                  errorMessage={errors.name}
                  placeholder="e.g., Engineering"
                  required
                  data-testid="dept-name"
                />
              </div>
              
              <div>
                <Input
                  label="Department Code"
                  value={formData.code}
                  onChange={(e) => handleInputChange('code', e.target.value.toUpperCase())}
                  error={!!errors.code}
                  errorMessage={errors.code}
                  placeholder="e.g., ENG_DEPT"
                  required
                  data-testid="dept-code"
                />
              </div>
            </div>

            <div>
              <Textarea
                label="Description"
                value={formData.description || ''}
                onChange={(e) => handleInputChange('description', e.target.value)}
                placeholder="Brief description of the department's role and responsibilities"
                rows={3}
                data-testid="dept-description"
              />
            </div>
          </div>

          {/* Organization & Structure */}
          <div className="space-y-4">
            <h3 className="text-lg font-medium text-gray-900">Organization & Structure</h3>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <Select
                  label="Organization"
                  value={formData.organization_id?.toString() || ''}
                  onChange={(value) => {
                    const orgId = Array.isArray(value) ? parseInt(value[0]) : parseInt(value)
                    handleInputChange('organization_id', isNaN(orgId) ? undefined : orgId)
                  }}
                  options={[
                    { value: '', label: 'Select Organization' },
                    ...organizations.map(org => ({
                      value: org.id.toString(),
                      label: `${org.name} (${org.code})`
                    }))
                  ]}
                  error={!!errors.organization_id}
                  errorMessage={errors.organization_id}
                  required
                />
              </div>

              <div>
                <Select
                  label="Department Type"
                  value={formData.type || ''}
                  onChange={(value) => {
                    const typeValue = Array.isArray(value) ? value[0] : value
                    handleInputChange('type', typeValue || undefined)
                  }}
                  options={[
                    { value: '', label: 'Select Type' },
                    ...DEPARTMENT_TYPES.map(type => ({
                      value: type.value,
                      label: type.label
                    }))
                  ]}
                />
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <Select
                  label="Parent Department"
                  value={formData.parent_department_id?.toString() || ''}
                  onChange={(value) => {
                    const deptId = Array.isArray(value) ? parseInt(value[0]) : parseInt(value)
                    handleInputChange('parent_department_id', isNaN(deptId) ? undefined : deptId)
                  }}
                  options={[
                    { value: '', label: 'No Parent (Root Department)' },
                    ...departments
                      .filter(dept => 
                        dept.organization_id === formData.organization_id &&
                        dept.id !== formData.id // Prevent self-selection
                      )
                      .map(dept => ({
                        value: dept.id.toString(),
                        label: `${dept.name} (${dept.code})`
                      }))
                  ]}
                  error={!!errors.parent_department_id}
                  errorMessage={errors.parent_department_id}
                />
              </div>

              <div>
                <Select
                  label="Department Manager"
                  value={formData.manager_id?.toString() || ''}
                  onChange={(value) => {
                    const managerId = Array.isArray(value) ? parseInt(value[0]) : parseInt(value)
                    handleInputChange('manager_id', isNaN(managerId) ? undefined : managerId)
                  }}
                  options={[
                    { value: '', label: 'No Manager Assigned' },
                    ...managers.map(manager => ({
                      value: manager.id.toString(),
                      label: `${manager.full_name} (${manager.email})`
                    }))
                  ]}
                />
              </div>
            </div>
          </div>

          {/* Status */}
          <div className="space-y-4">
            <h3 className="text-lg font-medium text-gray-900">Status</h3>
            
            <div className="flex items-center gap-2">
              <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                department.is_active 
                  ? 'bg-green-100 text-green-800' 
                  : 'bg-red-100 text-red-800'
              }`}>
                {department.is_active ? 'Active' : 'Inactive'}
              </span>
              <span className="text-sm text-gray-500">
                Created: {new Date(department.created_at).toLocaleDateString()}
              </span>
            </div>
          </div>

          {/* Actions */}
          <div className="flex justify-end gap-3 pt-4 border-t border-gray-200">
            <Button
              type="button"
              variant="outline"
              onClick={handleClose}
              disabled={isSubmitting}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              disabled={isSubmitting}
              data-testid="save-department"
            >
              {isSubmitting ? (
                <>
                  <Loading size="sm" className="mr-2" />
                  Saving...
                </>
              ) : (
                <>
                  <Save className="h-4 w-4 mr-2" />
                  Save Changes
                </>
              )}
            </Button>
          </div>
        </form>
      </div>
    </Modal>
  )
}