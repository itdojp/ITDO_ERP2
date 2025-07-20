import { useEffect } from 'react'
import { useForm } from 'react-hook-form'
import { X, Folder } from 'lucide-react'
import Button from './ui/Button'
import Input from './ui/Input'
import { 
  useCreateProject
} from '../services/projectApi'
import {
  CreateProjectRequest
} from '../types/task'

interface ProjectCreateModalProps {
  isOpen: boolean
  onClose: () => void
  onSuccess: () => void
}

interface FormData {
  name: string
  code: string
  description: string
}

export function ProjectCreateModal({ isOpen, onClose, onSuccess }: ProjectCreateModalProps) {
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
      description: ''
    }
  })

  const createProjectMutation = useCreateProject()

  // Watch name field to auto-generate code
  const nameValue = watch('name')
  useEffect(() => {
    if (nameValue) {
      const generatedCode = nameValue
        .toUpperCase()
        .replace(/[^A-Z0-9\s]/g, '')
        .replace(/\s+/g, '_')
        .substring(0, 20) // Limit length
      setValue('code', generatedCode)
    }
  }, [nameValue, setValue])

  const onSubmit = async (data: FormData) => {
    try {
      const projectData: CreateProjectRequest = {
        name: data.name,
        code: data.code,
        description: data.description || undefined
      }

      await createProjectMutation.mutateAsync(projectData)
      onSuccess()
      handleClose()
    } catch (error) {
      // Error handling - could be logged to monitoring service in production
    }
  }

  const handleClose = () => {
    reset()
    onClose()
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg w-full max-w-md max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <div className="flex items-center gap-2">
            <Folder className="h-6 w-6 text-blue-600" />
            <h2 className="text-xl font-semibold text-gray-900">Create New Project</h2>
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
                data-testid="project-name"
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
                data-testid="project-code"
                placeholder="PROJECT_CODE"
                helperText="Auto-generated from project name, but you can edit it"
              />

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
                  data-testid="project-description"
                  placeholder="Describe the project goals and objectives..."
                />
                {errors.description && (
                  <p className="mt-1 text-sm text-red-600">{errors.description.message}</p>
                )}
              </div>

              {/* Project Info */}
              <div className="bg-blue-50 p-4 rounded-lg">
                <h4 className="text-sm font-medium text-blue-900 mb-2">Project Information</h4>
                <ul className="text-sm text-blue-800 space-y-1">
                  <li>• You will be set as the project owner</li>
                  <li>• Project status will be set to &ldquo;Active&rdquo;</li>
                  <li>• You can add team members after creation</li>
                  <li>• Tasks can be created and assigned to this project</li>
                </ul>
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
              disabled={isSubmitting || createProjectMutation.isPending}
              data-testid="submit-project"
            >
              {isSubmitting || createProjectMutation.isPending ? 'Creating...' : 'Create Project'}
            </Button>
          </div>
        </form>
      </div>
    </div>
  )
}