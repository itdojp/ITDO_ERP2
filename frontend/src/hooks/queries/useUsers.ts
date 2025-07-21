import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { queryKeys, handleApiError, invalidateQueries } from '../../lib/queryClient'
import * as userApi from '../../services/userApi'
import type { User } from '../../types/user'

// User list query
export const useUsers = (params?: {
  page?: number
  limit?: number
  search?: string
  role?: string
  department?: string
}) => {
  return useQuery({
    queryKey: [...queryKeys.users(), 'list', params],
    queryFn: async () => {
      try {
        return await userApi.fetchUsers(params)
      } catch (error) {
        throw handleApiError(error)
      }
    },
    staleTime: 2 * 60 * 1000, // 2 minutes
    enabled: true,
  })
}

// Single user query
export const useUser = (id: string, enabled = true) => {
  return useQuery({
    queryKey: queryKeys.user(id),
    queryFn: async () => {
      try {
        return await userApi.fetchUser(id)
      } catch (error) {
        throw handleApiError(error)
      }
    },
    enabled: enabled && !!id,
    staleTime: 5 * 60 * 1000, // 5 minutes
  })
}

// Current user profile query
export const useUserProfile = () => {
  return useQuery({
    queryKey: queryKeys.userProfile(),
    queryFn: async () => {
      try {
        return await userApi.fetchCurrentUserProfile()
      } catch (error) {
        throw handleApiError(error)
      }
    },
    staleTime: 10 * 60 * 1000, // 10 minutes
    cacheTime: 30 * 60 * 1000, // 30 minutes
  })
}

// Create user mutation
export const useCreateUser = () => {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: async (userData: Omit<User, 'id' | 'createdAt' | 'updatedAt'>) => {
      try {
        return await userApi.createUser(userData)
      } catch (error) {
        throw handleApiError(error)
      }
    },
    onSuccess: (newUser) => {
      // Invalidate users list
      invalidateQueries.users()
      
      // Optionally add the new user to the cache
      queryClient.setQueryData(queryKeys.user(newUser.id), newUser)
    },
    onError: (error) => {
      console.error('Failed to create user:', error)
    },
  })
}

// Update user mutation
export const useUpdateUser = () => {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: async ({ id, ...userData }: Partial<User> & { id: string }) => {
      try {
        return await userApi.updateUser(id, userData)
      } catch (error) {
        throw handleApiError(error)
      }
    },
    onSuccess: (updatedUser, variables) => {
      // Update user in cache
      queryClient.setQueryData(queryKeys.user(variables.id), updatedUser)
      
      // Invalidate users list to refresh
      invalidateQueries.users()
      
      // If updating current user profile, invalidate profile cache
      if (variables.id === queryClient.getQueryData(queryKeys.userProfile())?.id) {
        invalidateQueries.userProfile = () => 
          queryClient.invalidateQueries({ queryKey: queryKeys.userProfile() })
        invalidateQueries.userProfile()
      }
    },
    onError: (error) => {
      console.error('Failed to update user:', error)
    },
  })
}

// Delete user mutation
export const useDeleteUser = () => {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: async (id: string) => {
      try {
        await userApi.deleteUser(id)
        return id
      } catch (error) {
        throw handleApiError(error)
      }
    },
    onSuccess: (deletedId) => {
      // Remove user from cache
      queryClient.removeQueries({ queryKey: queryKeys.user(deletedId) })
      
      // Invalidate users list
      invalidateQueries.users()
    },
    onError: (error) => {
      console.error('Failed to delete user:', error)
    },
  })
}

// Bulk update users mutation
export const useBulkUpdateUsers = () => {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: async (updates: Array<{ id: string; data: Partial<User> }>) => {
      try {
        return await userApi.bulkUpdateUsers(updates)
      } catch (error) {
        throw handleApiError(error)
      }
    },
    onSuccess: (updatedUsers) => {
      // Update individual users in cache
      updatedUsers.forEach(user => {
        queryClient.setQueryData(queryKeys.user(user.id), user)
      })
      
      // Invalidate users list
      invalidateQueries.users()
    },
    onError: (error) => {
      console.error('Failed to bulk update users:', error)
    },
  })
}

// Change user password mutation
export const useChangeUserPassword = () => {
  return useMutation({
    mutationFn: async ({ 
      currentPassword, 
      newPassword 
    }: { 
      currentPassword: string
      newPassword: string 
    }) => {
      try {
        return await userApi.changePassword(currentPassword, newPassword)
      } catch (error) {
        throw handleApiError(error)
      }
    },
    onError: (error) => {
      console.error('Failed to change password:', error)
    },
  })
}

// Reset user password mutation (admin only)
export const useResetUserPassword = () => {
  return useMutation({
    mutationFn: async ({ userId, newPassword }: { userId: string; newPassword: string }) => {
      try {
        return await userApi.resetUserPassword(userId, newPassword)
      } catch (error) {
        throw handleApiError(error)
      }
    },
    onError: (error) => {
      console.error('Failed to reset user password:', error)
    },
  })
}

// User permissions query
export const useUserPermissions = (userId: string, enabled = true) => {
  return useQuery({
    queryKey: queryKeys.userPermissions(userId),
    queryFn: async () => {
      try {
        return await userApi.fetchUserPermissions(userId)
      } catch (error) {
        throw handleApiError(error)
      }
    },
    enabled: enabled && !!userId,
    staleTime: 5 * 60 * 1000, // 5 minutes
  })
}

// Update user permissions mutation
export const useUpdateUserPermissions = () => {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: async ({ 
      userId, 
      permissions 
    }: { 
      userId: string
      permissions: string[] 
    }) => {
      try {
        return await userApi.updateUserPermissions(userId, permissions)
      } catch (error) {
        throw handleApiError(error)
      }
    },
    onSuccess: (_, variables) => {
      // Invalidate user permissions cache
      queryClient.invalidateQueries({ 
        queryKey: queryKeys.userPermissions(variables.userId) 
      })
    },
    onError: (error) => {
      console.error('Failed to update user permissions:', error)
    },
  })
}