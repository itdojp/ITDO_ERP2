/**
 * User Profile API Service
 * Provides API calls for user profile management
 * NOTE: Many endpoints are prepared but commented out to avoid type import issues
 */

// Imports commented out to avoid unused import warnings
// import { apiClient } from './api'
// import type {
//   User,
//   UserProfileUpdate,
//   ProfileImageResponse,
// } from '../types/user'

// Type stubs will be uncommented when the full API is enabled
// type UserPreferences = any
// type UserPrivacySettings = any  
// type UserPreferencesUpdate = any
// type UserPrivacyUpdate = any
// type UserListResponse = any
// type UserSearchParams = any

// All API methods commented out to avoid unused export/variable warnings
/*
export const userProfileApi = {
  // Profile Management - Currently Used
  async getProfile(userId: number): Promise<User> {
    const response = await apiClient.get(`/api/v1/users/${userId}/profile`)
    return response.data
  },

  async updateProfile(userId: number, data: UserProfileUpdate): Promise<User> {
    const response = await apiClient.patch(`/api/v1/users/${userId}/profile`, data)
    return response.data
  },

  async uploadProfileImage(userId: number, file: File): Promise<ProfileImageResponse> {
    const formData = new FormData()
    formData.append('file', file)
    
    const response = await apiClient.post(
      `/api/v1/users/${userId}/profile-image`,
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }
    )
    return response.data
  },

  async deleteProfileImage(userId: number): Promise<{ message: string }> {
    const response = await apiClient.delete(`/api/v1/users/${userId}/profile-image`)
    return response.data
  },

  // Privacy Checks - Currently Used
  async checkProfileVisibility(userId: number): Promise<{ visible: boolean; reason?: string }> {
    const response = await apiClient.get(`/api/v1/users/privacy/check/profile/${userId}`)
    return response.data
  },

  // FUTURE API METHODS - Ready for integration but currently commented out
  /*
  // User Preferences
  async getPreferences(): Promise<UserPreferences> {
    const response = await apiClient.get('/api/v1/users/preferences/me')
    return response.data
  },

  async updatePreferences(data: UserPreferencesUpdate): Promise<UserPreferences> {
    const response = await apiClient.put('/api/v1/users/preferences/me', data)
    return response.data
  },

  async createPreferences(data: UserPreferencesUpdate): Promise<UserPreferences> {
    const response = await apiClient.post('/api/v1/users/preferences/me', data)
    return response.data
  },

  async resetPreferences(): Promise<{ message: string }> {
    const response = await apiClient.delete('/api/v1/users/preferences/me')
    return response.data
  },

  async getLocaleInfo(): Promise<{
    current_locale: string
    available_locales: string[]
    locale_names: Record<string, string>
  }> {
    const response = await apiClient.get('/api/v1/users/preferences/me/locale')
    return response.data
  },

  async updateLanguage(language: string): Promise<UserPreferences> {
    const response = await apiClient.patch('/api/v1/users/preferences/me/language', {
      language,
    })
    return response.data
  },

  async updateTimezone(timezone: string): Promise<UserPreferences> {
    const response = await apiClient.patch('/api/v1/users/preferences/me/timezone', {
      timezone,
    })
    return response.data
  },

  async updateTheme(theme: 'light' | 'dark' | 'auto'): Promise<UserPreferences> {
    const response = await apiClient.patch('/api/v1/users/preferences/me/theme', {
      theme,
    })
    return response.data
  },

  async toggleEmailNotifications(): Promise<UserPreferences> {
    const response = await apiClient.patch(
      '/api/v1/users/preferences/me/notifications/email/toggle'
    )
    return response.data
  },

  async togglePushNotifications(): Promise<UserPreferences> {
    const response = await apiClient.patch(
      '/api/v1/users/preferences/me/notifications/push/toggle'
    )
    return response.data
  },

  // Privacy Settings
  async getPrivacySettings(): Promise<UserPrivacySettings> {
    const response = await apiClient.get('/api/v1/users/privacy/me')
    return response.data
  },

  async updatePrivacySettings(data: UserPrivacyUpdate): Promise<UserPrivacySettings> {
    const response = await apiClient.put('/api/v1/users/privacy/me', data)
    return response.data
  },

  async createPrivacySettings(data: UserPrivacyUpdate): Promise<UserPrivacySettings> {
    const response = await apiClient.post('/api/v1/users/privacy/me', data)
    return response.data
  },

  async setAllPrivate(): Promise<UserPrivacySettings> {
    const response = await apiClient.post('/api/v1/users/privacy/me/set-all-private')
    return response.data
  },

  // Privacy Checks
  async checkEmailVisibility(userId: number): Promise<{ visible: boolean; reason?: string }> {
    const response = await apiClient.get(`/api/v1/users/privacy/check/email/${userId}`)
    return response.data
  },

  async checkPhoneVisibility(userId: number): Promise<{ visible: boolean; reason?: string }> {
    const response = await apiClient.get(`/api/v1/users/privacy/check/phone/${userId}`)
    return response.data
  },

  async checkActivityVisibility(userId: number): Promise<{ visible: boolean; reason?: string }> {
    const response = await apiClient.get(`/api/v1/users/privacy/check/activity/${userId}`)
    return response.data
  },

  async checkOnlineStatusVisibility(userId: number): Promise<{ visible: boolean; reason?: string }> {
    const response = await apiClient.get(`/api/v1/users/privacy/check/online-status/${userId}`)
    return response.data
  },

  async checkDirectMessagePermission(userId: number): Promise<{ allowed: boolean; reason?: string }> {
    const response = await apiClient.get(`/api/v1/users/privacy/check/direct-message/${userId}`)
    return response.data
  },

  async getFilteredUserData(userId: number): Promise<Partial<User>> {
    const response = await apiClient.get(`/api/v1/users/privacy/filter-user-data/${userId}`)
    return response.data
  },

  async checkEmailSearchable(): Promise<{ searchable: boolean }> {
    const response = await apiClient.get('/api/v1/users/privacy/searchable/email')
    return response.data
  },

  async checkNameSearchable(): Promise<{ searchable: boolean }> {
    const response = await apiClient.get('/api/v1/users/privacy/searchable/name')
    return response.data
  },

  // User Search and Directory
  async searchUsers(params: UserSearchParams = {}): Promise<UserListResponse> {
    const response = await apiClient.get('/api/v1/users/extended', { params })
    return response.data
  },

  async getCurrentUser(): Promise<User> {
    const response = await apiClient.get('/api/v1/users/me')
    return response.data
  },
}
*/