import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { useMutation, useQueryClient, useQuery } from '@tanstack/react-query'
import Modal from './ui/Modal'
import Button from './ui/Button'
import Input from './ui/Input'
import Select from './ui/Select'
import { userApiService, userQueryKeys } from '../services/userApi'
import { CreateUserRequest } from '../types/user'

interface UserCreateModalProps {
  isOpen: boolean
  onClose: () => void
  onSuccess?: (message: string) => void
  onError?: (message: string) => void
}

export function UserCreateModal({ isOpen, onClose, onSuccess, onError }: UserCreateModalProps) {
  const queryClient = useQueryClient()
  const [isSubmitting, setIsSubmitting] = useState(false)

  // Form management
  const {
    register,
    handleSubmit,
    formState: { errors },
    reset,
    watch,
    clearErrors,
    setValue
  } = useForm<CreateUserRequest>()

  const password = watch('password')

  // Query for user roles
  const { data: roles = [] } = useQuery({
    queryKey: userQueryKeys.roles(),
    queryFn: () => userApiService.getUserRoles()
  })

  // Create user mutation
  const createUserMutation = useMutation({
    mutationFn: (userData: CreateUserRequest) => userApiService.createUser(userData),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: userQueryKeys.lists() })
      onSuccess?.('User created successfully')
      reset()
      onClose()
    },
    onError: (error: any) => {
      const errorMessage = error?.response?.data?.message || error?.message || 'Failed to create user'
      onError?.(errorMessage)
    },
    onSettled: () => {
      setIsSubmitting(false)
    }
  })

  const onSubmit = async (data: CreateUserRequest) => {
    setIsSubmitting(true)
    clearErrors()

    // Client-side validation
    if (data.password !== data.confirm_password) {
      onError?.('Passwords do not match')
      setIsSubmitting(false)
      return
    }

    try {
      await createUserMutation.mutateAsync(data)
    } catch (error) {
      // Error handling is done in mutation onError
    }
  }

  const handleClose = () => {
    reset()
    clearErrors()
    onClose()
  }

  return (
    <Modal
      isOpen={isOpen}
      onClose={handleClose}
      title="Add User"
      size="md"
      closeOnOverlayClick={false}
    >
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
        <div className="space-y-4">
          {/* Full Name */}
          <div>
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
            {errors.full_name && (
              <div id="full_name-error" className="sr-only">
                {errors.full_name.message}
              </div>
            )}
          </div>

          {/* Email */}
          <div>
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
            {errors.email && (
              <div id="email-error" className="sr-only">
                {errors.email.message}
              </div>
            )}
          </div>

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
            helperText="Optional. Include country code (e.g., +1234567890)"
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

          {/* Password */}
          <div>
            <Input
              label="Password"
              type="password"
              required
              {...register('password', {
                required: 'Password is required',
                minLength: {
                  value: 8,
                  message: 'Password must be at least 8 characters'
                },
                pattern: {
                  value: /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]/,
                  message: 'Password must contain uppercase, lowercase, number, and special character'
                }
              })}
              error={!!errors.password}
              errorMessage={errors.password?.message}
              helperText="Must contain uppercase, lowercase, number, and special character"
            />
            {errors.password && (
              <div id="password-error" className="sr-only">
                {errors.password.message}
              </div>
            )}
          </div>

          {/* Confirm Password */}
          <div>
            <Input
              label="Confirm Password"
              type="password"
              required
              {...register('confirm_password', {
                required: 'Please confirm your password',
                validate: (value) => value === password || 'Passwords do not match'
              })}
              error={!!errors.confirm_password}
              errorMessage={errors.confirm_password?.message}
            />
            {errors.confirm_password && (
              <div id="confirm_password-error" className="sr-only">
                {errors.confirm_password.message}
              </div>
            )}
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
            {isSubmitting ? 'Creating...' : 'Create User'}
          </Button>
        </div>
      </form>
    </Modal>
  )
}

export default UserCreateModal