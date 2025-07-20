import { useEffect } from 'react'
import { useForm } from 'react-hook-form'
import { X, Folder } from 'lucide-react'
import Button from './ui/Button'
import Input from './ui/Input'
import { 
  useUpdateProject
} from '../services/projectApi'
import {
  Project,
  UpdateProjectRequest
} from '../types/task'

interface ProjectEditModalProps {
  isOpen: boolean
  onClose: () => void
  onSuccess: () => void
  project: Project | null
}

interface FormData {
  name: string
  code: string
  description: string
  status: Project['status']
}

export function ProjectEditModal({ isOpen, onClose, onSuccess, project }: ProjectEditModalProps) {
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting }
  } = useForm<FormData>()

  const updateProjectMutation = useUpdateProject()

  // Initialize form when project changes
  useEffect(() => {
    if (project && isOpen) {
      reset({
        name: project.name,
        code: project.code,
        description: project.description || '',
        status: project.status
      })
    }
  }, [project, isOpen, reset])

  const onSubmit = async (data: FormData) => {
    if (!project) return

    try {
      const updateData: UpdateProjectRequest = {
        name: data.name !== project.name ? data.name : undefined,
        code: data.code !== project.code ? data.code : undefined,
        description: data.description !== (project.description || '') ? data.description : undefined,
        status: data.status !== project.status ? data.status : undefined
      }

      // Only include fields that have changed
      const hasChanges = updateData.name || updateData.code || 
        updateData.description !== undefined || updateData.status

      if (hasChanges) {
        await updateProjectMutation.mutateAsync({ id: project.id, data: updateData })
        onSuccess()
        handleClose()
      } else {
        handleClose()
      }
    } catch (error) {
      console.error('Failed to update project:', error)
    }
  }

  const handleClose = () => {
    reset()
    onClose()
  }

  if (!isOpen || !project) return null

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg w-full max-w-md max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <div className="flex items-center gap-2">
            <Folder className="h-6 w-6 text-blue-600" />
            <h2 className="text-xl font-semibold text-gray-900">Edit Project: {project.name}</h2>
          </div>
          <Button variant="ghost" onClick={handleClose}>
            <X className="h-5 w-5" />
          </Button>
        </div>

        <form onSubmit={handleSubmit(onSubmit)} className="flex flex-col h-full">
          <div className="flex-1 overflow-y-auto">
            <div className="p-6 space-y-4">
              {/* Project Name */}
              <Input
                label="Project Name"
                {...register('name', { 
                  required: 'Project name is required',
                  minLength: { value: 2, message: 'Project name must be at least 2 characters' },
                  maxLength: { value: 100, message: 'Project name must be less than 100 characters' }
                })}
                error={!!errors.name}
                errorMessage={errors.name?.message}
                placeholder="Enter project name"
              />

              {/* Project Code */}
              <Input
                label="Project Code"
                {...register('code', { 
                  required: 'Project code is required',
                  pattern: {
                    value: /^[A-Z0-9_]+$/,
                    message: 'Project code must contain only uppercase letters, numbers, and underscores'
                  },
                  maxLength: { value: 20, message: 'Project code must be less than 20 characters' }
                })}
                error={!!errors.code}
                errorMessage={errors.code?.message}
                placeholder="PROJECT_CODE"
              />

              {/* Project Status */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Project Status
                </label>
                <select
                  {...register('status', { required: 'Status is required' })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
                >
                  <option value="ACTIVE">Active</option>
                  <option value="COMPLETED">Completed</option>
                  <option value="ARCHIVED">Archived</option>
                </select>
                {errors.status && (
                  <p className="mt-1 text-sm text-red-600">{errors.status.message}</p>
                )}
              </div>

              {/* Description */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Description (Optional)
                </label>
                <textarea
                  {...register('description', {
                    maxLength: { value: 500, message: 'Description must be less than 500 characters' }
                  })}
                  rows={4}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500 resize-none"
                  placeholder="Describe the project goals and objectives..."
                />
                {errors.description && (
                  <p className="mt-1 text-sm text-red-600">{errors.description.message}</p>
                )}
              </div>

              {/* Project Metadata */}
              <div className="bg-gray-50 p-4 rounded-lg">
                <h4 className="text-sm font-medium text-gray-900 mb-2">Project Information</h4>
                <div className="text-sm text-gray-600 space-y-1">
                  <div>Owner: {project.owner.full_name}</div>
                  <div>Tasks: {project.task_count || 0}</div>
                  <div>Created: {new Date(project.created_at).toLocaleDateString()}</div>
                  <div>Last Updated: {new Date(project.updated_at).toLocaleDateString()}</div>
                </div>
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
              disabled={isSubmitting || updateProjectMutation.isPending}
              data-testid="save-project"
            >
              {isSubmitting || updateProjectMutation.isPending ? 'Saving...' : 'Save Changes'}
            </Button>
          </div>
        </form>
      </div>
    </div>
  )
}