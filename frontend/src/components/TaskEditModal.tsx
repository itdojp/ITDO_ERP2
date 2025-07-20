import { useState, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { X, CheckSquare, Save } from 'lucide-react'
import Button from './ui/Button'
import Input from './ui/Input'
import Select from './ui/Select'
import Textarea from './ui/Textarea'
import Modal from './ui/Modal'
import Loading from './ui/Loading'
import { 
  taskApiService, 
  taskQueryKeys,
  projectQueryKeys
} from '../services/taskApi'
import { userApiService } from '../services/userApi'
import { 
  Task,
  UpdateTaskRequest, 
  TaskFormData, 
  TaskFormErrors,
  TASK_STATUSES,
  TASK_PRIORITIES 
} from '../types/task'

interface TaskEditModalProps {
  isOpen: boolean
  onClose: () => void
  onSuccess?: () => void
  task: Task | null
}

export function TaskEditModal({
  isOpen,
  onClose,
  onSuccess,
  task
}: TaskEditModalProps) {
  const queryClient = useQueryClient()
  
  // Form state
  const [formData, setFormData] = useState<TaskFormData>({
    title: '',
    description: '',
    priority: 'MEDIUM',
    status: 'TODO',
    project_id: undefined,
    assignee_id: undefined,
    due_date: undefined
  })
  
  const [errors, setErrors] = useState<TaskFormErrors>({})
  const [isSubmitting, setIsSubmitting] = useState(false)

  // Populate form when task changes
  useEffect(() => {
    if (isOpen && task) {
      setFormData({
        id: task.id,
        title: task.title,
        description: task.description || '',
        priority: task.priority,
        status: task.status,
        project_id: task.project_id,
        assignee_id: task.assignee_id,
        due_date: task.due_date
      })
      setErrors({})
    }
  }, [isOpen, task])

  // Query for projects list
  const { data: projectsResponse } = useQuery({
    queryKey: projectQueryKeys.list(),
    queryFn: () => taskApiService.getProjects(),
    enabled: isOpen
  })

  // Query for users list (for assignment)
  const { data: usersResponse } = useQuery({
    queryKey: ['users'],
    queryFn: () => userApiService.getUsers(),
    enabled: isOpen
  })

  const projects = projectsResponse?.items || []
  const users = usersResponse?.items || []

  // Update task mutation
  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: UpdateTaskRequest }) => 
      taskApiService.updateTask(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: taskQueryKeys.lists() })
      queryClient.invalidateQueries({ queryKey: taskQueryKeys.statistics() })
      onSuccess?.()
      onClose()
    },
    onError: () => {
      // Failed to update task - error is handled by mutation
    }
  })

  // Validation
  const validateForm = (): boolean => {
    const newErrors: TaskFormErrors = {}

    if (!formData.title.trim()) {
      newErrors.title = 'Task title is required'
    }

    if (!formData.priority) {
      newErrors.priority = 'Priority is required'
    }

    if (!formData.status) {
      newErrors.status = 'Status is required'
    }

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  // Handlers
  const handleInputChange = (field: keyof TaskFormData, value: string | number | undefined) => {
    setFormData(prev => ({ ...prev, [field]: value }))
    if (errors[field as keyof TaskFormErrors]) {
      setErrors(prev => ({ ...prev, [field]: undefined }))
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!validateForm() || !task) {
      return
    }

    setIsSubmitting(true)
    try {
      const updateData: UpdateTaskRequest = {
        title: formData.title !== task.title ? formData.title : undefined,
        description: formData.description !== task.description ? formData.description : undefined,
        priority: formData.priority !== task.priority ? formData.priority : undefined,
        status: formData.status !== task.status ? formData.status : undefined,
        project_id: formData.project_id !== task.project_id ? formData.project_id : undefined,
        assignee_id: formData.assignee_id !== task.assignee_id ? formData.assignee_id : undefined,
        due_date: formData.due_date !== task.due_date ? formData.due_date : undefined
      }

      // Only send fields that have changed
      const hasChanges = Object.values(updateData).some(value => value !== undefined)
      if (hasChanges) {
        await updateMutation.mutateAsync({ id: task.id, data: updateData })
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

  if (!task) return null

  return (
    <Modal isOpen={isOpen} onClose={handleClose} size="lg">
      <div className="p-6">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-blue-100 rounded-lg">
              <CheckSquare className="h-6 w-6 text-blue-600" />
            </div>
            <div>
              <h2 className="text-xl font-semibold text-gray-900">Edit Task</h2>
              <p className="text-sm text-gray-500">Update task information and settings</p>
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
            <h3 className="text-lg font-medium text-gray-900">Task Details</h3>
            
            <div>
              <Input
                label="Task Title"
                value={formData.title}
                onChange={(e) => handleInputChange('title', e.target.value)}
                error={!!errors.title}
                errorMessage={errors.title}
                placeholder="e.g., Implement user authentication"
                required
                data-testid="task-title"
              />
            </div>

            <div>
              <Textarea
                label="Description"
                value={formData.description || ''}
                onChange={(e) => handleInputChange('description', e.target.value)}
                placeholder="Describe the task requirements and acceptance criteria"
                rows={4}
                data-testid="task-description"
              />
            </div>
          </div>

          {/* Task Configuration */}
          <div className="space-y-4">
            <h3 className="text-lg font-medium text-gray-900">Configuration</h3>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <Select
                  label="Priority"
                  value={formData.priority}
                  onChange={(value) => {
                    const priority = Array.isArray(value) ? value[0] : value
                    handleInputChange('priority', priority)
                  }}
                  options={TASK_PRIORITIES.map(priority => ({
                    value: priority.value,
                    label: priority.label
                  }))}
                  error={!!errors.priority}
                  errorMessage={errors.priority}
                  required
                  data-testid="task-priority"
                />
              </div>
              
              <div>
                <Select
                  label="Status"
                  value={formData.status || 'TODO'}
                  onChange={(value) => {
                    const status = Array.isArray(value) ? value[0] : value
                    handleInputChange('status', status)
                  }}
                  options={TASK_STATUSES.map(status => ({
                    value: status.value,
                    label: status.label
                  }))}
                  error={!!errors.status}
                  errorMessage={errors.status}
                  required
                  data-testid="task-status"
                />
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <Select
                  label="Project"
                  value={formData.project_id?.toString() || ''}
                  onChange={(value) => {
                    const projectId = Array.isArray(value) ? parseInt(value[0]) : parseInt(value)
                    handleInputChange('project_id', isNaN(projectId) ? undefined : projectId)
                  }}
                  options={[
                    { value: '', label: 'No Project' },
                    ...projects.map(project => ({
                      value: project.id.toString(),
                      label: `${project.name} (${project.code})`
                    }))
                  ]}
                  data-testid="task-project"
                />
              </div>

              <div>
                <Select
                  label="Assignee"
                  value={formData.assignee_id?.toString() || ''}
                  onChange={(value) => {
                    const assigneeId = Array.isArray(value) ? parseInt(value[0]) : parseInt(value)
                    handleInputChange('assignee_id', isNaN(assigneeId) ? undefined : assigneeId)
                  }}
                  options={[
                    { value: '', label: 'Unassigned' },
                    ...users.map(user => ({
                      value: user.id.toString(),
                      label: `${user.full_name} (${user.email})`
                    }))
                  ]}
                />
              </div>
            </div>

            <div>
              <Input
                label="Due Date"
                type="date"
                value={formData.due_date || ''}
                onChange={(e) => handleInputChange('due_date', e.target.value || undefined)}
                error={!!errors.due_date}
                errorMessage={errors.due_date}
              />
            </div>
          </div>

          {/* Progress Information */}
          <div className="space-y-4">
            <h3 className="text-lg font-medium text-gray-900">Progress</h3>
            
            <div className="bg-gray-50 p-4 rounded-lg">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-gray-700">Current Progress</span>
                <span className="text-sm text-gray-500">{task.progress}%</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div 
                  className="bg-blue-600 h-2 rounded-full transition-all duration-300" 
                  style={{ width: `${task.progress}%` }}
                />
              </div>
              <p className="text-xs text-gray-500 mt-2">
                Progress can be updated from the task list view
              </p>
            </div>
          </div>

          {/* Status Information */}
          <div className="space-y-4">
            <h3 className="text-lg font-medium text-gray-900">Information</h3>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
              <div>
                <span className="font-medium text-gray-700">Created:</span>
                <p className="text-gray-600">{new Date(task.created_at).toLocaleString()}</p>
              </div>
              <div>
                <span className="font-medium text-gray-700">Last Updated:</span>
                <p className="text-gray-600">{new Date(task.updated_at).toLocaleString()}</p>
              </div>
              {task.completed_at && (
                <div>
                  <span className="font-medium text-gray-700">Completed:</span>
                  <p className="text-gray-600">{new Date(task.completed_at).toLocaleString()}</p>
                </div>
              )}
              <div>
                <span className="font-medium text-gray-700">Created by:</span>
                <p className="text-gray-600">{task.creator.full_name}</p>
              </div>
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
              data-testid="save-task"
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