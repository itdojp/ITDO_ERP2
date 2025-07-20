import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { AlertTriangle, Trash2 } from 'lucide-react'
import Button from './ui/Button'
import Modal from './ui/Modal'
import Loading from './ui/Loading'
import { organizationApiService, organizationQueryKeys } from '../services/organizationApi'
import { Department } from '../types/organization'

interface DepartmentDeleteDialogProps {
  isOpen: boolean
  onClose: () => void
  onSuccess?: () => void
  department: Department | null
}

export function DepartmentDeleteDialog({
  isOpen,
  onClose,
  onSuccess,
  department
}: DepartmentDeleteDialogProps) {
  const queryClient = useQueryClient()
  const [isDeleting, setIsDeleting] = useState(false)

  // Delete department mutation
  const deleteMutation = useMutation({
    mutationFn: (id: number) => organizationApiService.deleteDepartment(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: organizationQueryKeys.tree() })
      queryClient.invalidateQueries({ queryKey: organizationQueryKeys.departments() })
      onSuccess?.()
      onClose()
    },
    onError: () => {
      // Failed to delete department - error is handled by mutation
    }
  })

  const handleDelete = async () => {
    if (!department) return

    setIsDeleting(true)
    try {
      await deleteMutation.mutateAsync(department.id)
    } finally {
      setIsDeleting(false)
    }
  }

  const handleClose = () => {
    if (!isDeleting) {
      onClose()
    }
  }

  if (!department) return null

  const hasChildren = department.children && department.children.length > 0
  const hasUsers = (department.user_count || 0) > 0

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

          {/* Department Info */}
          <div className="text-center space-y-2">
            <h3 className="text-lg font-medium text-gray-900">
              Delete &quot;{department.name}&quot;?
            </h3>
            <p className="text-sm text-gray-500">
              Department Code: {department.code}
            </p>
            <p className="text-sm text-gray-500">
              This action cannot be undone. Please confirm you want to delete this department.
            </p>
          </div>

          {/* Warnings */}
          <div className="space-y-3">
            {hasChildren && (
              <div className="p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
                <div className="flex items-start gap-2">
                  <AlertTriangle className="h-5 w-5 text-yellow-600 mt-0.5" />
                  <div>
                    <p className="text-sm font-medium text-yellow-800">
                      Department has sub-departments
                    </p>
                    <p className="text-sm text-yellow-700">
                      This department has {department.children?.length} sub-department(s). 
                      Deleting this department will also affect its sub-departments.
                    </p>
                  </div>
                </div>
              </div>
            )}

            {hasUsers && (
              <div className="p-3 bg-orange-50 border border-orange-200 rounded-lg">
                <div className="flex items-start gap-2">
                  <AlertTriangle className="h-5 w-5 text-orange-600 mt-0.5" />
                  <div>
                    <p className="text-sm font-medium text-orange-800">
                      Department has active members
                    </p>
                    <p className="text-sm text-orange-700">
                      This department has {department.user_count} member(s). 
                      You may want to reassign them before deletion.
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
                    All department data, including historical records and associations, 
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
                  Delete Department
                </>
              )}
            </Button>
          </div>
        </div>
      </div>
    </Modal>
  )
}