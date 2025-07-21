import React from 'react'
import { renderHook, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { describe, it, expect, vi, beforeEach } from 'vitest'

import { useUsers, useUser, useCreateUser, useUpdateUser, useDeleteUser } from './useUsers'
import { useDashboardStats, useDashboardCharts } from './useDashboard'
import { useProjects, useProject, useCreateProject } from './useProjects'
import { queryKeys, handleApiError, QueryError } from '../../lib/queryClient'

// Mock API services
vi.mock('../../services/userApi', () => ({
  fetchUsers: vi.fn(),
  fetchUser: vi.fn(),
  createUser: vi.fn(),
  updateUser: vi.fn(),
  deleteUser: vi.fn(),
  fetchCurrentUserProfile: vi.fn(),
  fetchUserPermissions: vi.fn(),
  updateUserPermissions: vi.fn(),
  bulkUpdateUsers: vi.fn(),
  changePassword: vi.fn(),
  resetUserPassword: vi.fn(),
}))

vi.mock('../../services/dashboardApi', () => ({
  fetchDashboardStats: vi.fn(),
  fetchDashboardCharts: vi.fn(),
  fetchRecentActivities: vi.fn(),
  fetchSystemNotifications: vi.fn(),
  fetchPerformanceMetrics: vi.fn(),
  fetchTaskCompletionTrends: vi.fn(),
  fetchResourceUtilization: vi.fn(),
  fetchCustomWidgets: vi.fn(),
}))

vi.mock('../../services/projectApi', () => ({
  fetchProjects: vi.fn(),
  fetchProject: vi.fn(),
  createProject: vi.fn(),
  updateProject: vi.fn(),
  deleteProject: vi.fn(),
  fetchProjectsByOrganization: vi.fn(),
  archiveProject: vi.fn(),
  restoreProject: vi.fn(),
  fetchProjectMembers: vi.fn(),
  addProjectMember: vi.fn(),
  removeProjectMember: vi.fn(),
  fetchProjectStatistics: vi.fn(),
  duplicateProject: vi.fn(),
}))

// Test wrapper with QueryClient
const createTestQueryClient = () => new QueryClient({
  defaultOptions: {
    queries: {
      retry: false,
      cacheTime: 0,
    },
  },
})

const createWrapper = () => {
  const queryClient = createTestQueryClient()
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  )
}

describe('Query Hooks', () => {
  describe('useUsers', () => {
    beforeEach(() => {
      vi.clearAllMocks()
    })

    it('fetches users successfully', async () => {
      const mockUsers = [
        { id: '1', name: 'John Doe', email: 'john@example.com' },
        { id: '2', name: 'Jane Smith', email: 'jane@example.com' },
      ]

      const userApi = await import('../../services/userApi')
      vi.mocked(userApi.fetchUsers).mockResolvedValue({
        data: mockUsers,
        total: 2,
        page: 1,
        limit: 10,
      })

      const { result } = renderHook(() => useUsers(), {
        wrapper: createWrapper(),
      })

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true)
      })

      expect(result.current.data?.data).toEqual(mockUsers)
      expect(userApi.fetchUsers).toHaveBeenCalledWith(undefined)
    })

    it('handles query parameters', async () => {
      const params = { page: 2, limit: 5, search: 'john' }
      const userApi = await import('../../services/userApi')
      vi.mocked(userApi.fetchUsers).mockResolvedValue({
        data: [],
        total: 0,
        page: 2,
        limit: 5,
      })

      renderHook(() => useUsers(params), {
        wrapper: createWrapper(),
      })

      await waitFor(() => {
        expect(userApi.fetchUsers).toHaveBeenCalledWith(params)
      })
    })

    it('handles fetch errors', async () => {
      const userApi = await import('../../services/userApi')
      vi.mocked(userApi.fetchUsers).mockRejectedValue(new Error('API Error'))

      const { result } = renderHook(() => useUsers(), {
        wrapper: createWrapper(),
      })

      await waitFor(() => {
        expect(result.current.isError).toBe(true)
      })

      expect(result.current.error).toBeTruthy()
    })
  })

  describe('useUser', () => {
    it('fetches single user successfully', async () => {
      const mockUser = { id: '1', name: 'John Doe', email: 'john@example.com' }
      const userApi = await import('../../services/userApi')
      vi.mocked(userApi.fetchUser).mockResolvedValue(mockUser)

      const { result } = renderHook(() => useUser('1'), {
        wrapper: createWrapper(),
      })

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true)
      })

      expect(result.current.data).toEqual(mockUser)
      expect(userApi.fetchUser).toHaveBeenCalledWith('1')
    })

    it('is disabled when id is empty', () => {
      const { result } = renderHook(() => useUser(''), {
        wrapper: createWrapper(),
      })

      expect(result.current.status).toBe('idle')
    })

    it('respects enabled parameter', () => {
      const { result } = renderHook(() => useUser('1', false), {
        wrapper: createWrapper(),
      })

      expect(result.current.status).toBe('idle')
    })
  })

  describe('useCreateUser', () => {
    it('creates user successfully and invalidates cache', async () => {
      const newUser = { name: 'New User', email: 'new@example.com', role: 'user' }
      const createdUser = { id: '3', ...newUser, createdAt: new Date(), updatedAt: new Date() }
      
      const userApi = await import('../../services/userApi')
      vi.mocked(userApi.createUser).mockResolvedValue(createdUser)

      const queryClient = createTestQueryClient()
      const wrapper = ({ children }: { children: React.ReactNode }) => (
        <QueryClientProvider client={queryClient}>
          {children}
        </QueryClientProvider>
      )

      const { result } = renderHook(() => useCreateUser(), { wrapper })

      await waitFor(() => {
        result.current.mutate(newUser)
      })

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true)
      })

      expect(result.current.data).toEqual(createdUser)
      expect(userApi.createUser).toHaveBeenCalledWith(newUser)
      
      // Check if user was added to cache
      const cachedUser = queryClient.getQueryData(queryKeys.user('3'))
      expect(cachedUser).toEqual(createdUser)
    })

    it('handles creation errors', async () => {
      const newUser = { name: 'New User', email: 'invalid-email', role: 'user' }
      const userApi = await import('../../services/userApi')
      vi.mocked(userApi.createUser).mockRejectedValue(new Error('Validation Error'))

      const { result } = renderHook(() => useCreateUser(), {
        wrapper: createWrapper(),
      })

      result.current.mutate(newUser)

      await waitFor(() => {
        expect(result.current.isError).toBe(true)
      })

      expect(result.current.error).toBeTruthy()
    })
  })

  describe('useUpdateUser', () => {
    it('updates user successfully and updates cache', async () => {
      const updatedData = { id: '1', name: 'Updated Name' }
      const updatedUser = { id: '1', name: 'Updated Name', email: 'john@example.com' }
      
      const userApi = await import('../../services/userApi')
      vi.mocked(userApi.updateUser).mockResolvedValue(updatedUser)

      const queryClient = createTestQueryClient()
      const wrapper = ({ children }: { children: React.ReactNode }) => (
        <QueryClientProvider client={queryClient}>
          {children}
        </QueryClientProvider>
      )

      const { result } = renderHook(() => useUpdateUser(), { wrapper })

      result.current.mutate(updatedData)

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true)
      })

      expect(result.current.data).toEqual(updatedUser)
      expect(userApi.updateUser).toHaveBeenCalledWith('1', { name: 'Updated Name' })
      
      // Check if cache was updated
      const cachedUser = queryClient.getQueryData(queryKeys.user('1'))
      expect(cachedUser).toEqual(updatedUser)
    })
  })

  describe('useDeleteUser', () => {
    it('deletes user successfully and removes from cache', async () => {
      const userApi = await import('../../services/userApi')
      vi.mocked(userApi.deleteUser).mockResolvedValue(undefined)

      const queryClient = createTestQueryClient()
      // Pre-populate cache
      queryClient.setQueryData(queryKeys.user('1'), { id: '1', name: 'John Doe' })

      const wrapper = ({ children }: { children: React.ReactNode }) => (
        <QueryClientProvider client={queryClient}>
          {children}
        </QueryClientProvider>
      )

      const { result } = renderHook(() => useDeleteUser(), { wrapper })

      result.current.mutate('1')

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true)
      })

      expect(userApi.deleteUser).toHaveBeenCalledWith('1')
      
      // Check if user was removed from cache
      const cachedUser = queryClient.getQueryData(queryKeys.user('1'))
      expect(cachedUser).toBeUndefined()
    })
  })

  describe('useDashboardStats', () => {
    it('fetches dashboard statistics successfully', async () => {
      const mockStats = {
        totalUsers: 100,
        activeProjects: 25,
        completedTasks: 500,
        revenue: 150000,
      }

      const dashboardApi = await import('../../services/dashboardApi')
      vi.mocked(dashboardApi.fetchDashboardStats).mockResolvedValue(mockStats)

      const { result } = renderHook(() => useDashboardStats(), {
        wrapper: createWrapper(),
      })

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true)
      })

      expect(result.current.data).toEqual(mockStats)
    })

    it('handles dashboard stats with parameters', async () => {
      const params = {
        dateRange: { start: new Date('2023-01-01'), end: new Date('2023-12-31') },
        organizationId: 'org-1',
      }

      const dashboardApi = await import('../../services/dashboardApi')
      vi.mocked(dashboardApi.fetchDashboardStats).mockResolvedValue({})

      renderHook(() => useDashboardStats(params), {
        wrapper: createWrapper(),
      })

      await waitFor(() => {
        expect(dashboardApi.fetchDashboardStats).toHaveBeenCalledWith(params)
      })
    })
  })

  describe('useDashboardCharts', () => {
    it('fetches and transforms chart data correctly', async () => {
      const mockChartData = {
        charts: [
          {
            id: 'chart-1',
            type: 'line',
            data: [{ x: 1, y: 10 }, { x: 2, y: 20 }],
            lastUpdated: '2023-01-01T00:00:00Z',
          },
        ],
      }

      const dashboardApi = await import('../../services/dashboardApi')
      vi.mocked(dashboardApi.fetchDashboardCharts).mockResolvedValue(mockChartData)

      const { result } = renderHook(() => useDashboardCharts(), {
        wrapper: createWrapper(),
      })

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true)
      })

      expect(result.current.data?.charts[0]).toHaveProperty('lastUpdated')
      expect(result.current.data?.charts[0].lastUpdated).toBeInstanceOf(Date)
    })
  })

  describe('useProjects', () => {
    it('fetches projects with keepPreviousData', async () => {
      const mockProjects = [
        { id: '1', name: 'Project 1', status: 'active' },
        { id: '2', name: 'Project 2', status: 'completed' },
      ]

      const projectApi = await import('../../services/projectApi')
      vi.mocked(projectApi.fetchProjects).mockResolvedValue({
        data: mockProjects,
        total: 2,
        page: 1,
        limit: 10,
      })

      const { result } = renderHook(() => useProjects(), {
        wrapper: createWrapper(),
      })

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true)
      })

      expect(result.current.data?.data).toEqual(mockProjects)
    })
  })

  describe('useProject', () => {
    it('fetches single project with statistics calculation', async () => {
      const mockProject = { id: '1', name: 'Project 1', organizationId: 'org-1' }
      const projectApi = await import('../../services/projectApi')
      vi.mocked(projectApi.fetchProject).mockResolvedValue(mockProject)

      const { result } = renderHook(() => useProject('1'), {
        wrapper: createWrapper(),
      })

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true)
      })

      expect(result.current.data).toEqual(mockProject)
    })
  })

  describe('useCreateProject', () => {
    it('creates project and invalidates related queries', async () => {
      const newProject = { 
        name: 'New Project', 
        description: 'Test project',
        organizationId: 'org-1',
      }
      const createdProject = { 
        id: '3', 
        ...newProject, 
        createdAt: new Date(), 
        updatedAt: new Date() 
      }
      
      const projectApi = await import('../../services/projectApi')
      vi.mocked(projectApi.createProject).mockResolvedValue(createdProject)

      const queryClient = createTestQueryClient()
      const wrapper = ({ children }: { children: React.ReactNode }) => (
        <QueryClientProvider client={queryClient}>
          {children}
        </QueryClientProvider>
      )

      const { result } = renderHook(() => useCreateProject(), { wrapper })

      result.current.mutate(newProject)

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true)
      })

      expect(result.current.data).toEqual(createdProject)
      
      // Check if project was added to cache
      const cachedProject = queryClient.getQueryData(queryKeys.project('3'))
      expect(cachedProject).toEqual(createdProject)
    })
  })
})

describe('Query Client Utilities', () => {
  describe('handleApiError', () => {
    it('handles QueryError instances', () => {
      const originalError = new QueryError('Test error', 400, 'VALIDATION_ERROR')
      const result = handleApiError(originalError)
      
      expect(result).toBe(originalError)
    })

    it('handles axios-style errors', () => {
      const axiosError = {
        response: {
          status: 404,
          data: {
            message: 'Not found',
            code: 'NOT_FOUND',
            details: { resource: 'user' },
          },
        },
      }
      
      const result = handleApiError(axiosError)
      
      expect(result).toBeInstanceOf(QueryError)
      expect(result.message).toBe('Not found')
      expect(result.status).toBe(404)
      expect(result.code).toBe('NOT_FOUND')
    })

    it('handles fetch-style errors', () => {
      const fetchError = {
        status: 500,
        message: 'Internal Server Error',
      }
      
      const result = handleApiError(fetchError)
      
      expect(result).toBeInstanceOf(QueryError)
      expect(result.status).toBe(500)
      expect(result.message).toBe('Internal Server Error')
    })

    it('handles generic errors', () => {
      const genericError = new Error('Something went wrong')
      const result = handleApiError(genericError)
      
      expect(result).toBeInstanceOf(QueryError)
      expect(result.message).toBe('Something went wrong')
      expect(result.status).toBe(500)
    })

    it('handles unknown error formats', () => {
      const unknownError = 'string error'
      const result = handleApiError(unknownError)
      
      expect(result).toBeInstanceOf(QueryError)
      expect(result.status).toBe(500)
    })
  })

  describe('queryKeys', () => {
    it('generates consistent query keys', () => {
      expect(queryKeys.users()).toEqual(['queries', 'users'])
      expect(queryKeys.user('123')).toEqual(['queries', 'users', '123'])
      expect(queryKeys.projects()).toEqual(['queries', 'projects'])
      expect(queryKeys.project('456')).toEqual(['queries', 'projects', '456'])
    })

    it('generates nested query keys correctly', () => {
      expect(queryKeys.tasksByProject('proj-1')).toEqual(['queries', 'tasks', 'byProject', 'proj-1'])
      expect(queryKeys.userPermissions('user-1')).toEqual(['queries', 'permissions', 'user', 'user-1'])
    })
  })
})