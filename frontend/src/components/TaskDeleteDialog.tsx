import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { AlertTriangle, Trash2 } from 'lucide-react'
import Button from './ui/Button'
import Modal from './ui/Modal'
import Loading from './ui/Loading'
import { taskApiService, taskQueryKeys } from '../services/taskApi'
import { Task } from '../types/task'

interface TaskDeleteDialogProps {
  isOpen: boolean
  onClose: () => void
  onSuccess?: () => void
  task: Task | null
}

export function TaskDeleteDialog({
  isOpen,
  onClose,
  onSuccess,
  task
}: TaskDeleteDialogProps) {
  const queryClient = useQueryClient()
  const [isDeleting, setIsDeleting] = useState(false)

  // Delete task mutation
  const deleteMutation = useMutation({
    mutationFn: (id: number) => taskApiService.deleteTask(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: taskQueryKeys.lists() })
      queryClient.invalidateQueries({ queryKey: taskQueryKeys.statistics() })
      onSuccess?.()
      onClose()
    },
    onError: () => {
      // Failed to delete task - error is handled by mutation
    }
  })

  const handleDelete = async () => {
    if (!task) return

    setIsDeleting(true)
    try {
      await deleteMutation.mutateAsync(task.id)
    } finally {
      setIsDeleting(false)
    }
  }

  const handleClose = () => {
    if (!isDeleting) {
      onClose()
    }
  }

  if (!task) return null

  const hasProgress = task.progress > 0
  const isInProgress = task.status === 'IN_PROGRESS'
  const hasComments = task.comments && task.comments.length > 0

  return (
    <Modal isOpen={isOpen} onClose={handleClose} size="md">
      <div className="p-6">
        <div className="space-y-4">
          {/* Warning Icon */}
          <div className="flex items-center justify-center">
            <div className="p-3 bg-red-100 rounded-full">
              <AlertTriangle className="h-8 w-8 text-red-600" />
            </div>
          </div>

          {/* Task Info */}
          <div className="text-center space-y-2">
            <h3 className="text-lg font-medium text-gray-900">
              Delete Task &quot;{task.title}&quot;?
            </h3>
            <p className="text-sm text-gray-500">
              This action cannot be undone. Please confirm you want to delete this task.
            </p>
          </div>

          {/* Task Details */}
          <div className="bg-gray-50 p-4 rounded-lg space-y-2">
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <span className="font-medium text-gray-700">Status:</span>
                <span className="ml-2 text-gray-600">{task.status}</span>
              </div>
              <div>
                <span className="font-medium text-gray-700">Priority:</span>
                <span className="ml-2 text-gray-600">{task.priority}</span>
              </div>
              <div>
                <span className="font-medium text-gray-700">Progress:</span>
                <span className="ml-2 text-gray-600">{task.progress}%</span>
              </div>
              {task.assignee && (
                <div>
                  <span className="font-medium text-gray-700">Assignee:</span>
                  <span className="ml-2 text-gray-600">{task.assignee.full_name}</span>
                </div>
              )}
              {task.project && (
                <div className="col-span-2">
                  <span className="font-medium text-gray-700">Project:</span>
                  <span className="ml-2 text-gray-600">{task.project.name}</span>
                </div>
              )}
            </div>
          </div>

          {/* Warnings */}
          <div className="space-y-3">
            {hasProgress && (
              <div className="p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
                <div className="flex items-start gap-2">
                  <AlertTriangle className="h-5 w-5 text-yellow-600 mt-0.5" />
                  <div>
                    <p className="text-sm font-medium text-yellow-800">
                      Task has progress
                    </p>
                    <p className="text-sm text-yellow-700">
                      This task is {task.progress}% complete. Deleting it will lose all progress tracking.
                    </p>
                  </div>
                </div>
              </div>
            )}

            {isInProgress && (
              <div className="p-3 bg-orange-50 border border-orange-200 rounded-lg">
                <div className="flex items-start gap-2">
                  <AlertTriangle className="h-5 w-5 text-orange-600 mt-0.5" />
                  <div>
                    <p className="text-sm font-medium text-orange-800">
                      Task is in progress
                    </p>
                    <p className="text-sm text-orange-700">
                      This task is currently being worked on. You may want to change its status before deletion.
                    </p>
                  </div>
                </div>
              </div>
            )}

            {hasComments && (
              <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg">
                <div className="flex items-start gap-2">
                  <AlertTriangle className="h-5 w-5 text-blue-600 mt-0.5" />
                  <div>
                    <p className="text-sm font-medium text-blue-800">
                      Task has comments
                    </p>
                    <p className="text-sm text-blue-700">
                      This task has {task.comments?.length} comment(s) that will also be deleted.
                    </p>
                  </div>
                </div>
              </div>
            )}

            <div className="p-3 bg-red-50 border border-red-200 rounded-lg">
              <div className="flex items-start gap-2">
                <AlertTriangle className="h-5 w-5 text-red-600 mt-0.5" />
                <div>
                  <p className="text-sm font-medium text-red-800">
                    This action cannot be undone
                  </p>
                  <p className="text-sm text-red-700">
                    All task data, including progress, comments, and historical records, 
                    will be permanently removed from the system.
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* Actions */}
          <div className="flex justify-end gap-3 pt-4">
            <Button
              variant="outline"
              onClick={handleClose}
              disabled={isDeleting}
            >
              Cancel
            </Button>
            <Button
              variant="destructive"
              onClick={handleDelete}
              disabled={isDeleting}
              data-testid="confirm-delete"
            >
              {isDeleting ? (
                <>
                  <Loading size="sm" className="mr-2" />
                  Deleting...
                </>
              ) : (
                <>
                  <Trash2 className="h-4 w-4 mr-2" />
                  Delete Task
                </>
              )}
            </Button>
          </div>
        </div>
      </div>
    </Modal>
  )
}