import { useQuery, useQueryClient } from '@tanstack/react-query'
import { queryKeys, handleApiError } from '../../lib/queryClient'
import * as dashboardApi from '../../services/dashboardApi'

// Dashboard statistics query
export const useDashboardStats = (params?: {
  dateRange?: {
    start: Date
    end: Date
  }
  organizationId?: string
  departmentId?: string
}) => {
  return useQuery({
    queryKey: [...queryKeys.dashboardStats(), params],
    queryFn: async () => {
      try {
        return await dashboardApi.fetchDashboardStats(params)
      } catch (error) {
        throw handleApiError(error)
      }
    },
    staleTime: 2 * 60 * 1000, // 2 minutes
    cacheTime: 5 * 60 * 1000, // 5 minutes
  })
}

// Dashboard charts data query
export const useDashboardCharts = (params?: {
  chartTypes?: string[]
  dateRange?: {
    start: Date
    end: Date
  }
  organizationId?: string
}) => {
  return useQuery({
    queryKey: [...queryKeys.dashboardCharts(), params],
    queryFn: async () => {
      try {
        return await dashboardApi.fetchDashboardCharts(params)
      } catch (error) {
        throw handleApiError(error)
      }
    },
    staleTime: 2 * 60 * 1000, // 2 minutes
    cacheTime: 5 * 60 * 1000, // 5 minutes
    select: (data) => {
      // Transform chart data for better consumption
      return {
        ...data,
        charts: data.charts.map((chart: any) => ({
          ...chart,
          data: chart.data || [],
          lastUpdated: new Date(chart.lastUpdated || Date.now()),
        })),
      }
    },
  })
}

// Recent activities query
export const useRecentActivities = (params?: {
  limit?: number
  userId?: string
  organizationId?: string
  activityTypes?: string[]
}) => {
  return useQuery({
    queryKey: [...queryKeys.dashboard(), 'activities', params],
    queryFn: async () => {
      try {
        return await dashboardApi.fetchRecentActivities(params)
      } catch (error) {
        throw handleApiError(error)
      }
    },
    staleTime: 1 * 60 * 1000, // 1 minute
    cacheTime: 3 * 60 * 1000, // 3 minutes
  })
}

// System notifications query
export const useSystemNotifications = (params?: {
  unreadOnly?: boolean
  limit?: number
  types?: string[]
}) => {
  return useQuery({
    queryKey: [...queryKeys.dashboard(), 'notifications', params],
    queryFn: async () => {
      try {
        return await dashboardApi.fetchSystemNotifications(params)
      } catch (error) {
        throw handleApiError(error)
      }
    },
    staleTime: 30 * 1000, // 30 seconds
    cacheTime: 2 * 60 * 1000, // 2 minutes
    refetchInterval: 5 * 60 * 1000, // Auto-refetch every 5 minutes
  })
}

// Performance metrics query
export const usePerformanceMetrics = (params?: {
  metrics?: string[]
  timeframe?: 'hour' | 'day' | 'week' | 'month'
  organizationId?: string
}) => {
  return useQuery({
    queryKey: [...queryKeys.dashboard(), 'performance', params],
    queryFn: async () => {
      try {
        return await dashboardApi.fetchPerformanceMetrics(params)
      } catch (error) {
        throw handleApiError(error)
      }
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
    cacheTime: 10 * 60 * 1000, // 10 minutes
    select: (data) => {
      // Calculate additional metrics
      return {
        ...data,
        calculated: {
          averageResponseTime: data.responseTime?.average || 0,
          totalRequests: data.requests?.reduce((sum: number, req: any) => sum + req.count, 0) || 0,
          errorRate: data.errors?.rate || 0,
        },
      }
    },
  })
}

// Task completion trends query
export const useTaskCompletionTrends = (params?: {
  dateRange?: {
    start: Date
    end: Date
  }
  projectId?: string
  userId?: string
  granularity?: 'day' | 'week' | 'month'
}) => {
  return useQuery({
    queryKey: [...queryKeys.dashboard(), 'task-trends', params],
    queryFn: async () => {
      try {
        return await dashboardApi.fetchTaskCompletionTrends(params)
      } catch (error) {
        throw handleApiError(error)
      }
    },
    staleTime: 10 * 60 * 1000, // 10 minutes
    cacheTime: 20 * 60 * 1000, // 20 minutes
  })
}

// Resource utilization query
export const useResourceUtilization = (params?: {
  resourceTypes?: string[]
  organizationId?: string
  timeframe?: 'current' | 'day' | 'week'
}) => {
  return useQuery({
    queryKey: [...queryKeys.dashboard(), 'resources', params],
    queryFn: async () => {
      try {
        return await dashboardApi.fetchResourceUtilization(params)
      } catch (error) {
        throw handleApiError(error)
      }
    },
    staleTime: 3 * 60 * 1000, // 3 minutes
    cacheTime: 10 * 60 * 1000, // 10 minutes
  })
}

// Custom dashboard widgets query
export const useCustomDashboardWidgets = (dashboardId?: string) => {
  return useQuery({
    queryKey: [...queryKeys.dashboard(), 'widgets', dashboardId],
    queryFn: async () => {
      try {
        return await dashboardApi.fetchCustomWidgets(dashboardId)
      } catch (error) {
        throw handleApiError(error)
      }
    },
    enabled: !!dashboardId,
    staleTime: 5 * 60 * 1000, // 5 minutes
    cacheTime: 15 * 60 * 1000, // 15 minutes
  })
}

// Dashboard refresh utility
export const useDashboardRefresh = () => {
  const queryClient = useQueryClient()

  const refreshDashboard = () => {
    // Invalidate all dashboard-related queries
    queryClient.invalidateQueries({ queryKey: queryKeys.dashboard() })
  }

  const refreshStats = () => {
    queryClient.invalidateQueries({ queryKey: queryKeys.dashboardStats() })
  }

  const refreshCharts = () => {
    queryClient.invalidateQueries({ queryKey: queryKeys.dashboardCharts() })
  }

  return {
    refreshDashboard,
    refreshStats,
    refreshCharts,
  }
}

// Real-time dashboard data hook with polling
export const useRealtimeDashboard = (params?: {
  pollingInterval?: number
  enableRealtime?: boolean
  organizationId?: string
}) => {
  const { pollingInterval = 30000, enableRealtime = false } = params || {}

  const statsQuery = useDashboardStats({
    organizationId: params?.organizationId,
  })

  const chartsQuery = useDashboardCharts({
    organizationId: params?.organizationId,
  })

  const notificationsQuery = useSystemNotifications({
    unreadOnly: true,
    limit: 10,
  })

  // Enable polling when real-time is requested
  React.useEffect(() => {
    if (!enableRealtime) return

    const intervals: NodeJS.Timeout[] = []

    // Poll stats
    intervals.push(
      setInterval(() => {
        statsQuery.refetch()
      }, pollingInterval)
    )

    // Poll charts less frequently
    intervals.push(
      setInterval(() => {
        chartsQuery.refetch()
      }, pollingInterval * 2)
    )

    // Poll notifications more frequently
    intervals.push(
      setInterval(() => {
        notificationsQuery.refetch()
      }, pollingInterval / 2)
    )

    return () => {
      intervals.forEach(clearInterval)
    }
  }, [enableRealtime, pollingInterval])

  return {
    stats: statsQuery,
    charts: chartsQuery,
    notifications: notificationsQuery,
    isLoading: statsQuery.isLoading || chartsQuery.isLoading,
    hasError: statsQuery.isError || chartsQuery.isError,
    errors: {
      stats: statsQuery.error,
      charts: chartsQuery.error,
    },
  }
}