import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import Dialog from './ui/Dialog'
import { userApiService, userQueryKeys } from '../services/userApi'
import { User } from '../types/user'

interface UserDeleteDialogProps {
  isOpen: boolean
  user: User | null
  onClose: () => void
  onSuccess?: (message: string) => void
  onError?: (message: string) => void
}

export function UserDeleteDialog({ isOpen, user, onClose, onSuccess, onError }: UserDeleteDialogProps) {
  const queryClient = useQueryClient()
  const [isDeleting, setIsDeleting] = useState(false)

  // Delete user mutation
  const deleteUserMutation = useMutation({
    mutationFn: (userId: number) => userApiService.deleteUser(userId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: userQueryKeys.lists() })
      onSuccess?.('User deleted successfully')
      onClose()
    },
    onError: (error: any) => {
      const errorMessage = error?.response?.data?.message || error?.message || 'Failed to delete user'
      onError?.(errorMessage)
    },
    onSettled: () => {
      setIsDeleting(false)
    }
  })

  const handleConfirmDelete = async () => {
    if (!user) return

    setIsDeleting(true)
    try {
      await deleteUserMutation.mutateAsync(user.id)
    } catch (error) {
      // Error handling is done in mutation onError
    }
  }

  if (!user) return null

  return (
    <Dialog
      isOpen={isOpen}
      onClose={onClose}
      title="Delete User"
      type="danger"
      confirmText={isDeleting ? 'Deleting...' : 'Delete'}
      cancelText="Cancel"
      onConfirm={handleConfirmDelete}
      onCancel={onClose}
      loading={isDeleting}
      closeOnOverlayClick={false}
      closeOnEscape={!isDeleting}
      description={`Are you sure you want to delete user "${user.full_name}"? This action cannot be undone.`}
    />
  )
}

export default UserDeleteDialog