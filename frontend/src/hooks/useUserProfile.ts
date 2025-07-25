/**
 * React Query hooks for user profile management
 */

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { userProfileApi } from '../services/userProfileApi'
import type {
  User,
  UserProfileUpdate,
  UserPreferencesUpdate,
  UserPrivacyUpdate,
  UserSearchParams,
} from '../types/user'

// Query Keys
const USER_PROFILE_KEYS = {
  all: ['userProfile'] as const,
  profile: (userId: number) => [...USER_PROFILE_KEYS.all, 'profile', userId] as const,
  preferences: () => [...USER_PROFILE_KEYS.all, 'preferences'] as const,
  privacy: () => [...USER_PROFILE_KEYS.all, 'privacy'] as const,
  locale: () => [...USER_PROFILE_KEYS.all, 'locale'] as const,
  currentUser: () => [...USER_PROFILE_KEYS.all, 'currentUser'] as const,
  users: (params: UserSearchParams) => [...USER_PROFILE_KEYS.all, 'users', params] as const,
  privacyCheck: (type: string, userId: number) => 
    [...USER_PROFILE_KEYS.all, 'privacyCheck', type, userId] as const,
}

// Profile Hooks
export const useUserProfile = (userId: number) => {
  return useQuery({
    queryKey: USER_PROFILE_KEYS.profile(userId),
    queryFn: () => userProfileApi.getProfile(userId),
    enabled: !!userId,
  })
}

export const useCurrentUser = () => {
  return useQuery({
    queryKey: USER_PROFILE_KEYS.currentUser(),
    queryFn: () => userProfileApi.getCurrentUser(),
  })
}

export const useUpdateProfile = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ userId, data }: { userId: number; data: UserProfileUpdate }) =>
      userProfileApi.updateProfile(userId, data),
    onSuccess: (updatedUser, { userId }) => {
      // Update the user profile cache
      queryClient.setQueryData(USER_PROFILE_KEYS.profile(userId), updatedUser)
      
      // Update current user cache if it's the same user
      queryClient.setQueryData(USER_PROFILE_KEYS.currentUser(), (oldData: User | undefined) => {
        return oldData?.id === userId ? updatedUser : oldData
      })
      
      // Invalidate related queries
      queryClient.invalidateQueries({ queryKey: USER_PROFILE_KEYS.all })
    },
  })
}

export const useUploadProfileImage = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ userId, file }: { userId: number; file: File }) =>
      userProfileApi.uploadProfileImage(userId, file),
    onSuccess: (response, { userId }) => {
      // Update the user profile with new image URL
      queryClient.setQueryData(USER_PROFILE_KEYS.profile(userId), (oldData: User | undefined) => {
        return oldData ? { ...oldData, profile_image_url: response.image_url } : oldData
      })
      
      // Update current user cache if it's the same user
      queryClient.setQueryData(USER_PROFILE_KEYS.currentUser(), (oldData: User | undefined) => {
        return oldData?.id === userId 
          ? { ...oldData, profile_image_url: response.image_url } 
          : oldData
      })
    },
  })
}

export const useDeleteProfileImage = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (userId: number) => userProfileApi.deleteProfileImage(userId),
    onSuccess: (_, userId) => {
      // Remove image URL from cache
      queryClient.setQueryData(USER_PROFILE_KEYS.profile(userId), (oldData: User | undefined) => {
        return oldData ? { ...oldData, profile_image_url: undefined } : oldData
      })
      
      // Update current user cache
      queryClient.setQueryData(USER_PROFILE_KEYS.currentUser(), (oldData: User | undefined) => {
        return oldData?.id === userId 
          ? { ...oldData, profile_image_url: undefined } 
          : oldData
      })
    },
  })
}

// Preferences Hooks
export const useUserPreferences = () => {
  return useQuery({
    queryKey: USER_PROFILE_KEYS.preferences(),
    queryFn: () => userProfileApi.getPreferences(),
  })
}

export const useUpdatePreferences = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: UserPreferencesUpdate) => userProfileApi.updatePreferences(data),
    onSuccess: (updatedPreferences) => {
      queryClient.setQueryData(USER_PROFILE_KEYS.preferences(), updatedPreferences)
    },
  })
}

export const useCreatePreferences = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: UserPreferencesUpdate) => userProfileApi.createPreferences(data),
    onSuccess: (newPreferences) => {
      queryClient.setQueryData(USER_PROFILE_KEYS.preferences(), newPreferences)
    },
  })
}

export const useResetPreferences = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: () => userProfileApi.resetPreferences(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: USER_PROFILE_KEYS.preferences() })
    },
  })
}

export const useLocaleInfo = () => {
  return useQuery({
    queryKey: USER_PROFILE_KEYS.locale(),
    queryFn: () => userProfileApi.getLocaleInfo(),
  })
}

export const useUpdateLanguage = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (language: string) => userProfileApi.updateLanguage(language),
    onSuccess: (updatedPreferences) => {
      queryClient.setQueryData(USER_PROFILE_KEYS.preferences(), updatedPreferences)
    },
  })
}

export const useUpdateTimezone = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (timezone: string) => userProfileApi.updateTimezone(timezone),
    onSuccess: (updatedPreferences) => {
      queryClient.setQueryData(USER_PROFILE_KEYS.preferences(), updatedPreferences)
    },
  })
}

export const useUpdateTheme = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (theme: 'light' | 'dark' | 'auto') => userProfileApi.updateTheme(theme),
    onSuccess: (updatedPreferences) => {
      queryClient.setQueryData(USER_PROFILE_KEYS.preferences(), updatedPreferences)
    },
  })
}

export const useToggleEmailNotifications = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: () => userProfileApi.toggleEmailNotifications(),
    onSuccess: (updatedPreferences) => {
      queryClient.setQueryData(USER_PROFILE_KEYS.preferences(), updatedPreferences)
    },
  })
}

export const useTogglePushNotifications = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: () => userProfileApi.togglePushNotifications(),
    onSuccess: (updatedPreferences) => {
      queryClient.setQueryData(USER_PROFILE_KEYS.preferences(), updatedPreferences)
    },
  })
}

// Privacy Hooks
export const useUserPrivacySettings = () => {
  return useQuery({
    queryKey: USER_PROFILE_KEYS.privacy(),
    queryFn: () => userProfileApi.getPrivacySettings(),
  })
}

export const useUpdatePrivacySettings = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: UserPrivacyUpdate) => userProfileApi.updatePrivacySettings(data),
    onSuccess: (updatedSettings) => {
      queryClient.setQueryData(USER_PROFILE_KEYS.privacy(), updatedSettings)
    },
  })
}

export const useCreatePrivacySettings = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: UserPrivacyUpdate) => userProfileApi.createPrivacySettings(data),
    onSuccess: (newSettings) => {
      queryClient.setQueryData(USER_PROFILE_KEYS.privacy(), newSettings)
    },
  })
}

export const useSetAllPrivate = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: () => userProfileApi.setAllPrivate(),
    onSuccess: (updatedSettings) => {
      queryClient.setQueryData(USER_PROFILE_KEYS.privacy(), updatedSettings)
    },
  })
}

// User Search Hooks
export const useSearchUsers = (params: UserSearchParams = {}) => {
  return useQuery({
    queryKey: USER_PROFILE_KEYS.users(params),
    queryFn: () => userProfileApi.searchUsers(params),
  })
}

// Privacy Check Hooks
export const useCheckProfileVisibility = (userId: number) => {
  return useQuery({
    queryKey: USER_PROFILE_KEYS.privacyCheck('profile', userId),
    queryFn: () => userProfileApi.checkProfileVisibility(userId),
    enabled: !!userId,
  })
}

export const useCheckEmailVisibility = (userId: number) => {
  return useQuery({
    queryKey: USER_PROFILE_KEYS.privacyCheck('email', userId),
    queryFn: () => userProfileApi.checkEmailVisibility(userId),
    enabled: !!userId,
  })
}

export const useCheckPhoneVisibility = (userId: number) => {
  return useQuery({
    queryKey: USER_PROFILE_KEYS.privacyCheck('phone', userId),
    queryFn: () => userProfileApi.checkPhoneVisibility(userId),
    enabled: !!userId,
  })
}

export const useGetFilteredUserData = (userId: number) => {
  return useQuery({
    queryKey: USER_PROFILE_KEYS.privacyCheck('filtered', userId),
    queryFn: () => userProfileApi.getFilteredUserData(userId),
    enabled: !!userId,
  })
}