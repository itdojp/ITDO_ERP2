import { useState, useCallback } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { 
  Search, 
  Filter, 
  Plus, 
  CheckSquare, 
  Clock, 
  AlertCircle,
  User,
  Calendar,
  BarChart3,
  Edit,
  Trash2
} from 'lucide-react'
import Button from '../components/ui/Button'
import Input from '../components/ui/Input'
import Select from '../components/ui/Select'
import Loading from '../components/ui/Loading'
import Alert from '../components/ui/Alert'
import Toast from '../components/ui/Toast'
import { TaskCreateModal } from '../components/TaskCreateModal'
import { TaskEditModal } from '../components/TaskEditModal'
import { TaskDeleteDialog } from '../components/TaskDeleteDialog'
import { 
  taskApiService, 
  taskQueryKeys,
  projectQueryKeys
} from '../services/taskApi'
import { 
  Task,
  TaskFilters,
  TaskStatus,
  TaskPriority,
  TASK_STATUSES,
  TASK_PRIORITIES,
  TaskBoardColumn,
  TaskDragData
} from '../types/task'

interface TaskItemProps {
  task: Task
  onEdit: (task: Task) => void
  onDelete: (task: Task) => void
  onStatusChange: (task: Task, newStatus: TaskStatus) => void
  onProgressChange: (task: Task, progress: number) => void
}

function TaskItem({ task, onEdit, onDelete, onStatusChange, onProgressChange }: TaskItemProps) {
  const [isEditing, setIsEditing] = useState(false)
  const [progress, setProgress] = useState(task.progress)

  const handleProgressSave = () => {
    onProgressChange(task, progress)
    setIsEditing(false)
  }

  const getPriorityColor = (priority: TaskPriority) => {
    switch (priority) {
      case 'HIGH': return 'text-red-600 bg-red-100'
      case 'MEDIUM': return 'text-yellow-600 bg-yellow-100'
      case 'LOW': return 'text-gray-600 bg-gray-100'
      default: return 'text-gray-600 bg-gray-100'
    }
  }


  return (
    <div className="bg-white rounded-lg border p-4 hover:shadow-md transition-shadow" data-testid="task-item">
      {/* Header */}
      <div className="flex items-start justify-between mb-3">
        <div className="flex-1">
          <h3 className="text-lg font-semibold text-gray-900 mb-1">{task.title}</h3>
          {task.description && (
            <p className="text-sm text-gray-600 mb-2">{task.description}</p>
          )}
        </div>
        <div className="flex items-center gap-2 ml-4">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => onEdit(task)}
            data-testid="edit-task"
          >
            <Edit className="h-4 w-4" />
          </Button>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => onDelete(task)}
            data-testid="delete-task"
          >
            <Trash2 className="h-4 w-4 text-red-600" />
          </Button>
        </div>
      </div>

      {/* Status and Priority */}
      <div className="flex items-center gap-2 mb-3">
        <Select
          value={task.status}
          onChange={(value) => {
            const newStatus = Array.isArray(value) ? value[0] as TaskStatus : value as TaskStatus
            onStatusChange(task, newStatus)
          }}
          options={TASK_STATUSES.map(status => ({
            value: status.value,
            label: status.label
          }))}
          size="sm"
        />
        <span className={`px-2 py-1 rounded-full text-xs font-medium ${getPriorityColor(task.priority)}`}>
          {task.priority}
        </span>
      </div>

      {/* Progress */}
      <div className="mb-3">
        <div className="flex items-center justify-between mb-1">
          <span className="text-sm font-medium text-gray-700">Progress</span>
          <span className="text-sm text-gray-500" data-testid="progress-display">{task.progress}%</span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div 
            className="bg-blue-600 h-2 rounded-full transition-all duration-300" 
            style={{ width: `${task.progress}%` }}
          />
        </div>
        {isEditing ? (
          <div className="flex items-center gap-2 mt-2">
            <input
              type="range"
              min="0"
              max="100"
              value={progress}
              onChange={(e) => setProgress(parseInt(e.target.value))}
              className="flex-1"
              data-testid="progress-slider"
            />
            <Button size="sm" onClick={handleProgressSave} data-testid="save-progress">
              Save
            </Button>
            <Button size="sm" variant="outline" onClick={() => setIsEditing(false)}>
              Cancel
            </Button>
          </div>
        ) : (
          <Button
            size="sm"
            variant="ghost"
            onClick={() => setIsEditing(true)}
            className="mt-1 text-xs"
          >
            Update Progress
          </Button>
        )}
      </div>

      {/* Meta Information */}
      <div className="flex items-center justify-between text-sm text-gray-500">
        <div className="flex items-center gap-4">
          {task.assignee && (
            <div className="flex items-center gap-1">
              <User className="h-3 w-3" />
              <span>{task.assignee.full_name}</span>
            </div>
          )}
          {task.project && (
            <div className="flex items-center gap-1">
              <CheckSquare className="h-3 w-3" />
              <span>{task.project.name}</span>
            </div>
          )}
          {task.due_date && (
            <div className="flex items-center gap-1">
              <Calendar className="h-3 w-3" />
              <span>{new Date(task.due_date).toLocaleDateString()}</span>
            </div>
          )}
        </div>
        <div className="text-xs">
          Created {new Date(task.created_at).toLocaleDateString()}
        </div>
      </div>
    </div>
  )
}

interface TaskBoardProps {
  tasks: Task[]
  onTaskMove: (task: Task, newStatus: TaskStatus) => void
  onEdit: (task: Task) => void
  onDelete: (task: Task) => void
  onProgressChange: (task: Task, progress: number) => void
}

function TaskBoard({ tasks, onTaskMove, onEdit, onDelete, onProgressChange }: TaskBoardProps) {
  const columns: TaskBoardColumn[] = TASK_STATUSES.map(status => ({
    status: status.value,
    title: status.label,
    color: status.color,
    tasks: tasks.filter(task => task.status === status.value)
  }))

  const handleDragStart = (e: React.DragEvent, task: Task) => {
    const dragData: TaskDragData = {
      task,
      sourceColumn: task.status,
      sourceIndex: columns.find(col => col.status === task.status)?.tasks.indexOf(task) || 0
    }
    e.dataTransfer.setData('application/json', JSON.stringify(dragData))
  }

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault()
  }

  const handleDrop = (e: React.DragEvent, targetStatus: TaskStatus) => {
    e.preventDefault()
    try {
      const dragData: TaskDragData = JSON.parse(e.dataTransfer.getData('application/json'))
      if (dragData.task.status !== targetStatus) {
        onTaskMove(dragData.task, targetStatus)
      }
    } catch (error) {
      console.error('Error parsing drag data:', error)
    }
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
      {columns.map(column => (
        <div
          key={column.status}
          className="bg-gray-50 rounded-lg p-4"
          data-testid={`status-column-${column.status.toLowerCase().replace('_', '-')}`}
          onDragOver={handleDragOver}
          onDrop={(e) => handleDrop(e, column.status)}
        >
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-semibold text-gray-900">{column.title}</h3>
            <span className="bg-white px-2 py-1 rounded-full text-sm text-gray-600">
              {column.tasks.length}
            </span>
          </div>
          <div className="space-y-3">
            {column.tasks.map(task => (
              <div
                key={task.id}
                draggable
                onDragStart={(e) => handleDragStart(e, task)}
                className="cursor-move"
              >
                <TaskItem
                  task={task}
                  onEdit={onEdit}
                  onDelete={onDelete}
                  onStatusChange={onTaskMove}
                  onProgressChange={onProgressChange}
                />
              </div>
            ))}
            {column.tasks.length === 0 && (
              <div className="text-center py-8 text-gray-500">
                <Clock className="h-8 w-8 mx-auto mb-2" />
                <p className="text-sm">No {column.title.toLowerCase()} tasks</p>
              </div>
            )}
          </div>
        </div>
      ))}
    </div>
  )
}

export function TaskListPage() {
  const queryClient = useQueryClient()
  
  // State management
  const [filters, setFilters] = useState<TaskFilters>({})
  const [showFilters, setShowFilters] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')
  const [viewMode, setViewMode] = useState<'list' | 'board'>('list')
  const [toastMessage, setToastMessage] = useState<{ type: 'success' | 'error'; message: string } | null>(null)
  
  // Modal states
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [showEditModal, setShowEditModal] = useState(false)
  const [showDeleteDialog, setShowDeleteDialog] = useState(false)
  const [editingTask, setEditingTask] = useState<Task | null>(null)
  const [deletingTask, setDeletingTask] = useState<Task | null>(null)

  // Queries
  const { 
    data: tasksResponse, 
    isLoading, 
    error 
  } = useQuery({
    queryKey: taskQueryKeys.list(filters),
    queryFn: () => taskApiService.getTasks(filters)
  })

  const { data: projectsResponse } = useQuery({
    queryKey: projectQueryKeys.list(),
    queryFn: () => taskApiService.getProjects()
  })

  const { data: statistics } = useQuery({
    queryKey: taskQueryKeys.statistics(),
    queryFn: () => taskApiService.getTaskStatistics()
  })

  const tasks = tasksResponse?.items || []
  const projects = projectsResponse?.items || []

  // Mutations
  const updateTaskMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: any }) => 
      taskApiService.updateTask(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: taskQueryKeys.lists() })
      queryClient.invalidateQueries({ queryKey: taskQueryKeys.statistics() })
      setToastMessage({ type: 'success', message: 'Task updated successfully' })
    },
    onError: () => {
      setToastMessage({ type: 'error', message: 'Failed to update task' })
    }
  })

  const deleteTaskMutation = useMutation({
    mutationFn: (id: number) => taskApiService.deleteTask(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: taskQueryKeys.lists() })
      queryClient.invalidateQueries({ queryKey: taskQueryKeys.statistics() })
      setToastMessage({ type: 'success', message: 'Task deleted successfully' })
    },
    onError: () => {
      setToastMessage({ type: 'error', message: 'Failed to delete task' })
    }
  })

  // Event handlers
  const handleSearch = useCallback((value: string) => {
    setSearchQuery(value)
    setFilters(prev => ({ ...prev, search: value || undefined }))
  }, [])

  const handleFilterChange = useCallback((key: keyof TaskFilters, value: string) => {
    setFilters(prev => ({ ...prev, [key]: value || undefined }))
  }, [])

  const handleStatusFilter = useCallback((status: TaskStatus) => {
    setFilters(prev => ({ ...prev, status: prev.status === status ? undefined : status }))
  }, [])

  const handlePriorityFilter = useCallback((priority: TaskPriority) => {
    setFilters(prev => ({ ...prev, priority: prev.priority === priority ? undefined : priority }))
  }, [])

  const handleTaskEdit = useCallback((task: Task) => {
    setEditingTask(task)
    setShowEditModal(true)
  }, [])

  const handleTaskDelete = useCallback((task: Task) => {
    setDeletingTask(task)
    setShowDeleteDialog(true)
  }, [deleteTaskMutation])

  const handleStatusChange = useCallback((task: Task, newStatus: TaskStatus) => {
    updateTaskMutation.mutate({
      id: task.id,
      data: { status: newStatus }
    })
  }, [updateTaskMutation])

  const handleProgressChange = useCallback((task: Task, progress: number) => {
    updateTaskMutation.mutate({
      id: task.id,
      data: { progress }
    })
  }, [updateTaskMutation])

  const handleCreateTask = () => {
    setShowCreateModal(true)
  }

  const handleModalSuccess = () => {
    setToastMessage({ type: 'success', message: 'Task operation completed successfully' })
  }

  // Loading state
  if (isLoading) {
    return <Loading message="Loading tasks..." />
  }

  // Error state
  if (error && !tasksResponse) {
    return (
      <Alert 
        variant="error" 
        title="Failed to load tasks" 
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
            <CheckSquare className="h-8 w-8" />
            Tasks
          </h1>
          <p className="text-gray-600 mt-1">
            Manage and track your tasks and projects
          </p>
        </div>
        <Button onClick={handleCreateTask} data-testid="create-task-btn">
          <Plus className="h-4 w-4 mr-2" />
          Create Task
        </Button>
      </div>

      {/* Statistics */}
      {statistics && (
        <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
          <div className="bg-white p-4 rounded-lg border">
            <div className="flex items-center">
              <CheckSquare className="h-8 w-8 text-blue-500" />
              <div className="ml-3">
                <p className="text-sm font-medium text-gray-500">Total Tasks</p>
                <p className="text-2xl font-bold text-gray-900">{statistics.total_tasks}</p>
              </div>
            </div>
          </div>
          <div className="bg-white p-4 rounded-lg border">
            <div className="flex items-center">
              <Clock className="h-8 w-8 text-yellow-500" />
              <div className="ml-3">
                <p className="text-sm font-medium text-gray-500">In Progress</p>
                <p className="text-2xl font-bold text-gray-900">{statistics.by_status.IN_PROGRESS}</p>
              </div>
            </div>
          </div>
          <div className="bg-white p-4 rounded-lg border">
            <div className="flex items-center">
              <CheckSquare className="h-8 w-8 text-green-500" />
              <div className="ml-3">
                <p className="text-sm font-medium text-gray-500">Completed</p>
                <p className="text-2xl font-bold text-gray-900">{statistics.by_status.COMPLETED}</p>
              </div>
            </div>
          </div>
          <div className="bg-white p-4 rounded-lg border">
            <div className="flex items-center">
              <AlertCircle className="h-8 w-8 text-red-500" />
              <div className="ml-3">
                <p className="text-sm font-medium text-gray-500">High Priority</p>
                <p className="text-2xl font-bold text-gray-900">{statistics.by_priority.HIGH}</p>
              </div>
            </div>
          </div>
          <div className="bg-white p-4 rounded-lg border">
            <div className="flex items-center">
              <BarChart3 className="h-8 w-8 text-purple-500" />
              <div className="ml-3">
                <p className="text-sm font-medium text-gray-500">Completion Rate</p>
                <p className="text-2xl font-bold text-gray-900">{statistics.completion_rate}%</p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Controls */}
      <div className="flex flex-col sm:flex-row gap-4">
        <div className="flex-1">
          <Input
            placeholder="Search tasks..."
            value={searchQuery}
            onChange={(e) => handleSearch(e.target.value)}
            leftIcon={<Search className="h-4 w-4" />}
            data-testid="task-search"
          />
        </div>
        <div className="flex items-center gap-2">
          {/* Status Filters */}
          <Button
            variant={filters.status === 'IN_PROGRESS' ? 'default' : 'outline'}
            size="sm"
            onClick={() => handleStatusFilter('IN_PROGRESS')}
            data-testid="filter-in-progress"
          >
            In Progress
          </Button>
          <Button
            variant={filters.priority === 'HIGH' ? 'default' : 'outline'}
            size="sm"
            onClick={() => handlePriorityFilter('HIGH')}
            data-testid="filter-high-priority"
          >
            High Priority
          </Button>
          <Button
            variant="outline"
            onClick={() => setShowFilters(!showFilters)}
          >
            <Filter className="h-4 w-4 mr-2" />
            Filters
          </Button>
          <Select
            value={viewMode}
            onChange={(value) => setViewMode(Array.isArray(value) ? value[0] as 'list' | 'board' : value as 'list' | 'board')}
            options={[
              { value: 'list', label: 'List View' },
              { value: 'board', label: 'Board View' }
            ]}
            size="sm"
          />
        </div>
      </div>

      {/* Advanced Filters */}
      {showFilters && (
        <div className="bg-gray-50 p-4 rounded-lg space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <Select
              label="Status"
              value={filters.status || ''}
              onChange={(value) => handleFilterChange('status', Array.isArray(value) ? value[0] : value)}
              options={[
                { value: '', label: 'All Statuses' },
                ...TASK_STATUSES.map(status => ({ value: status.value, label: status.label }))
              ]}
            />
            <Select
              label="Priority"
              value={filters.priority || ''}
              onChange={(value) => handleFilterChange('priority', Array.isArray(value) ? value[0] : value)}
              options={[
                { value: '', label: 'All Priorities' },
                ...TASK_PRIORITIES.map(priority => ({ value: priority.value, label: priority.label }))
              ]}
            />
            <Select
              label="Project"
              value={filters.project_id?.toString() || ''}
              onChange={(value) => {
                const projectId = Array.isArray(value) ? parseInt(value[0]) : parseInt(value)
                handleFilterChange('project_id', isNaN(projectId) ? '' : projectId.toString())
              }}
              options={[
                { value: '', label: 'All Projects' },
                ...projects.map(project => ({ value: project.id.toString(), label: project.name }))
              ]}
            />
            <div className="flex items-end">
              <Button
                variant="outline"
                onClick={() => {
                  setFilters({})
                  setSearchQuery('')
                }}
              >
                Clear Filters
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Task Display */}
      {viewMode === 'board' ? (
        <TaskBoard
          tasks={tasks}
          onTaskMove={handleStatusChange}
          onEdit={handleTaskEdit}
          onDelete={handleTaskDelete}
          onProgressChange={handleProgressChange}
        />
      ) : (
        <div className="bg-white rounded-lg border">
          <div className="p-4 border-b border-gray-200">
            <h3 className="text-lg font-medium text-gray-900">Task List</h3>
            <p className="text-sm text-gray-500">
              {tasks.length} task{tasks.length !== 1 ? 's' : ''} found
            </p>
          </div>
          <div className="p-4" data-testid="task-list">
            {tasks.length > 0 ? (
              <div className="space-y-4">
                {tasks.map((task) => (
                  <TaskItem
                    key={task.id}
                    task={task}
                    onEdit={handleTaskEdit}
                    onDelete={handleTaskDelete}
                    onStatusChange={handleStatusChange}
                    onProgressChange={handleProgressChange}
                  />
                ))}
              </div>
            ) : (
              <div className="text-center py-8">
                <CheckSquare className="mx-auto h-12 w-12 text-gray-400" />
                <h3 className="mt-2 text-sm font-medium text-gray-900">No tasks found</h3>
                <p className="mt-1 text-sm text-gray-500">
                  Get started by creating your first task.
                </p>
                <Button onClick={handleCreateTask} className="mt-4">
                  <Plus className="h-4 w-4 mr-2" />
                  Create Task
                </Button>
              </div>
            )}
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
          data-testid="success-message"
        />
      )}

      {/* Modals */}
      <TaskCreateModal
        isOpen={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        onSuccess={handleModalSuccess}
      />

      <TaskEditModal
        isOpen={showEditModal}
        onClose={() => {
          setShowEditModal(false)
          setEditingTask(null)
        }}
        onSuccess={handleModalSuccess}
        task={editingTask}
      />

      <TaskDeleteDialog
        isOpen={showDeleteDialog}
        onClose={() => {
          setShowDeleteDialog(false)
          setDeletingTask(null)
        }}
        onSuccess={handleModalSuccess}
        task={deletingTask}
      />
    </div>
  )
}