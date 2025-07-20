import { useState, useEffect } from 'react'
import { useForm } from 'react-hook-form'
import { useMutation, useQueryClient, useQuery } from '@tanstack/react-query'
import Modal from './ui/Modal'
import Button from './ui/Button'
import Input from './ui/Input'
import Select from './ui/Select'
import Loading from './ui/Loading'
import { userApiService, userQueryKeys } from '../services/userApi'
import { UpdateUserRequest } from '../types/user'

interface UserEditModalProps {
  isOpen: boolean
  userId: number | null
  onClose: () => void
  onSuccess?: (message: string) => void
  onError?: (message: string) => void
}

export function UserEditModal({ isOpen, userId, onClose, onSuccess, onError }: UserEditModalProps) {
  const queryClient = useQueryClient()
  const [isSubmitting, setIsSubmitting] = useState(false)

  // Form management
  const {
    register,
    handleSubmit,
    formState: { errors },
    reset,
    setValue,
    clearErrors,
    watch
  } = useForm<UpdateUserRequest>()

  // Query for user details
  const { 
    data: user, 
    isLoading: isLoadingUser 
  } = useQuery({
    queryKey: userQueryKeys.detail(userId!),
    queryFn: () => userApiService.getUserById(userId!),
    enabled: !!userId && isOpen,
  })

  // Query for user roles
  const { data: roles = [] } = useQuery({
    queryKey: userQueryKeys.roles(),
    queryFn: () => userApiService.getUserRoles()
  })

  // Update user mutation
  const updateUserMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: UpdateUserRequest }) => 
      userApiService.updateUser(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: userQueryKeys.lists() })
      queryClient.invalidateQueries({ queryKey: userQueryKeys.detail(userId!) })
      onSuccess?.('User updated successfully')
      onClose()
    },
    onError: (error: any) => {
      const errorMessage = error?.response?.data?.message || error?.message || 'Failed to update user'
      onError?.(errorMessage)
    },
    onSettled: () => {
      setIsSubmitting(false)
    }
  })

  // Populate form when user data loads
  useEffect(() => {
    if (user && isOpen) {
      setValue('full_name', user.full_name)
      setValue('email', user.email)
      setValue('phone', user.phone || '')
      setValue('is_active', user.is_active)
      setValue('role', user.roles[0]?.role.code || '')
    }
  }, [user, isOpen, setValue])

  const onSubmit = async (data: UpdateUserRequest) => {
    if (!userId) return
    
    setIsSubmitting(true)
    clearErrors()

    try {
      await updateUserMutation.mutateAsync({ id: userId, data })
    } catch (error) {
      // Error handling is done in mutation onError
    }
  }

  const handleClose = () => {
    reset()
    clearErrors()
    onClose()
  }

  if (!isOpen) return null

  if (isLoadingUser) {
    return (
      <Modal
        isOpen={isOpen}
        onClose={handleClose}
        title="Edit User"
        size="md"
      >
        <div className="py-8">
          <Loading message="Loading user details..." />
        </div>
      </Modal>
    )
  }

  if (!user) {
    return (
      <Modal
        isOpen={isOpen}
        onClose={handleClose}
        title="Edit User"
        size="md"
      >
        <div className="py-8 text-center">
          <p className="text-red-600">Failed to load user details.</p>
          <Button onClick={handleClose} className="mt-4">
            Close
          </Button>
        </div>
      </Modal>
    )
  }

  return (
    <Modal
      isOpen={isOpen}
      onClose={handleClose}
      title="Edit User"
      size="md"
      closeOnOverlayClick={false}
    >
      <div className="modal-header mb-6">
        <h2 className="text-lg font-semibold">Edit User</h2>
        <p className="text-sm text-gray-600">
          Update user information and settings
        </p>
      </div>

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
        <div className="space-y-4">
          {/* Full Name */}
          <Input
            label="Full Name"
            required
            {...register('full_name', {
              required: 'Name is required',
              minLength: {
                value: 2,
                message: 'Name must be at least 2 characters'
              }
            })}
            error={!!errors.full_name}
            errorMessage={errors.full_name?.message}
          />

          {/* Email */}
          <Input
            label="Email Address"
            type="email"
            required
            {...register('email', {
              required: 'Email is required',
              pattern: {
                value: /^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$/i,
                message: 'Invalid email format'
              }
            })}
            error={!!errors.email}
            errorMessage={errors.email?.message}
          />

          {/* Phone */}
          <Input
            label="Phone Number"
            type="tel"
            {...register('phone', {
              pattern: {
                value: /^[\+]?[1-9][\d]{0,15}$/,
                message: 'Invalid phone number format'
              }
            })}
            error={!!errors.phone}
            errorMessage={errors.phone?.message}
            helperText="Include country code (e.g., +1234567890)"
          />

          {/* Role */}
          <Select
            label="Role"
            value={watch('role') || ''}
            onChange={(value) => setValue('role', Array.isArray(value) ? value[0] : value)}
            options={[
              { value: '', label: 'Select a role' },
              ...roles.map(role => ({ value: role.id, label: role.name }))
            ]}
            error={!!errors.role}
            errorMessage={errors.role?.message}
          />

          {/* Status */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Account Status
            </label>
            <div className="flex items-center space-x-4">
              <label className="flex items-center">
                <input
                  type="radio"
                  {...register('is_active')}
                  value="true"
                  className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300"
                />
                <span className="ml-2 text-sm text-gray-700">Active</span>
              </label>
              <label className="flex items-center">
                <input
                  type="radio"
                  {...register('is_active')}
                  value="false"
                  className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300"
                />
                <span className="ml-2 text-sm text-gray-700">Inactive</span>
              </label>
            </div>
          </div>
        </div>

        {/* User Info Display */}
        <div className="bg-gray-50 p-4 rounded-lg">
          <h4 className="text-sm font-medium text-gray-700 mb-2">Additional Information</h4>
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <span className="text-gray-500">Created:</span>
              <span className="ml-2 text-gray-900">
                {new Date(user.created_at).toLocaleDateString()}
              </span>
            </div>
            <div>
              <span className="text-gray-500">Last Login:</span>
              <span className="ml-2 text-gray-900">
                {user.last_login_at 
                  ? new Date(user.last_login_at).toLocaleDateString()
                  : 'Never'
                }
              </span>
            </div>
          </div>
        </div>

        {/* Form Actions */}
        <div className="flex justify-end space-x-3 pt-6 border-t">
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
            loading={isSubmitting}
            disabled={isSubmitting}
          >
            Save Changes
          </Button>
        </div>
      </form>
    </Modal>
  )
}

export default UserEditModal