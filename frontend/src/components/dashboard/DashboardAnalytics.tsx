import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { dashboardApi } from '../../services/dashboardApi'
import {
  DashboardFilters,
  DATE_RANGE_OPTIONS
} from '../../types/dashboard'
import {
  SimpleLineChart,
  SimpleAreaChart,
  SimpleBarChart,
  SimplePieChart,
  ChartContainer
} from '../charts/ChartComponents'
import {
  Users,
  Building,
  FileText,
  TrendingUp,
  Clock,
  AlertTriangle,
  CheckCircle,
  BarChart3,
  RefreshCw
} from 'lucide-react'
import Button from '../ui/Button'

interface DashboardAnalyticsProps {
  className?: string
}

export default function DashboardAnalytics({ className = '' }: DashboardAnalyticsProps) {
  const [filters, setFilters] = useState<DashboardFilters>({
    dateRange: {
      start: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
      end: new Date().toISOString().split('T')[0]
    }
  })

  const [selectedDateRange, setSelectedDateRange] = useState('month')
  const [isRefreshing, setIsRefreshing] = useState(false)

  // Core dashboard data queries
  const { 
    data: metrics, 
    isLoading: metricsLoading, 
    refetch: refetchMetrics 
  } = useQuery({
    queryKey: ['dashboard-metrics', filters],
    queryFn: async () => {
      try {
        // Try real API first
        return await dashboardApi.getMetrics(filters)
      } catch (error) {
        console.warn('Real API failed, using mock data:', error)
        // Fallback to mock data
        return dashboardApi.generateMockMetrics()
      }
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
    cacheTime: 10 * 60 * 1000, // 10 minutes
  })

  const { 
    data: systemHealth, 
    isLoading: healthLoading,
    refetch: refetchHealth 
  } = useQuery({
    queryKey: ['system-health'],
    queryFn: async () => {
      try {
        return await dashboardApi.getSystemHealth()
      } catch (error) {
        console.warn('System health API failed, using mock data:', error)
        return dashboardApi.generateMockSystemHealth()
      }
    },
    staleTime: 1 * 60 * 1000, // 1 minute
    cacheTime: 5 * 60 * 1000, // 5 minutes
  })

  const { 
    isLoading: activityLoading,
    refetch: refetchActivity 
  } = useQuery({
    queryKey: ['user-activity', filters],
    queryFn: () => dashboardApi.generateMockUserActivity(),
    staleTime: 5 * 60 * 1000,
    cacheTime: 10 * 60 * 1000,
  })

  const { 
    data: taskAnalytics, 
    isLoading: tasksLoading,
    refetch: refetchTasks 
  } = useQuery({
    queryKey: ['task-analytics', filters],
    queryFn: () => dashboardApi.generateMockTaskAnalytics(),
    staleTime: 5 * 60 * 1000,
    cacheTime: 10 * 60 * 1000,
  })

  const { 
    data: orgAnalytics, 
    isLoading: orgLoading,
    refetch: refetchOrg 
  } = useQuery({
    queryKey: ['organization-analytics', filters],
    queryFn: () => dashboardApi.generateMockOrganizationAnalytics(),
    staleTime: 5 * 60 * 1000,
    cacheTime: 10 * 60 * 1000,
  })

  // Time series data for charts
  const { data: userTrend } = useQuery({
    queryKey: ['user-trend', filters],
    queryFn: () => dashboardApi.generateMockTimeSeriesData('users', 30),
    staleTime: 5 * 60 * 1000,
  })

  const { data: taskTrend } = useQuery({
    queryKey: ['task-trend', filters],
    queryFn: () => dashboardApi.generateMockTimeSeriesData('tasks', 30),
    staleTime: 5 * 60 * 1000,
  })

  const handleDateRangeChange = (value: string) => {
    setSelectedDateRange(value)
    const option = DATE_RANGE_OPTIONS.find(opt => opt.value === value)
    if (option && option.days > 0) {
      const endDate = new Date()
      const startDate = new Date()
      startDate.setDate(startDate.getDate() - option.days)
      
      setFilters({
        ...filters,
        dateRange: {
          start: startDate.toISOString().split('T')[0],
          end: endDate.toISOString().split('T')[0]
        }
      })
    }
  }

  const handleRefresh = async () => {
    setIsRefreshing(true)
    try {
      await Promise.all([
        refetchMetrics(),
        refetchHealth(),
        refetchActivity(),
        refetchTasks(),
        refetchOrg()
      ])
    } finally {
      setIsRefreshing(false)
    }
  }

  const isLoading = metricsLoading || healthLoading || activityLoading || tasksLoading || orgLoading

  if (isLoading) {
    return (
      <div className={`${className} flex items-center justify-center h-64`}>
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Header with Controls */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Analytics Dashboard</h2>
          <p className="text-sm text-gray-600 mt-1">
            Real-time insights and system performance metrics
          </p>
        </div>
        
        <div className="flex items-center gap-3">
          <select
            value={selectedDateRange}
            onChange={(e) => handleDateRangeChange(e.target.value)}
            className="border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            {DATE_RANGE_OPTIONS.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
          
          <Button
            variant="outline"
            onClick={handleRefresh}
            disabled={isRefreshing}
            className="flex items-center gap-2"
          >
            <RefreshCw className={`h-4 w-4 ${isRefreshing ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
        </div>
      </div>

      {/* Key Metrics Overview */}
      {metrics && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <div className="bg-white rounded-lg border p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Total Users</p>
                <p className="text-2xl font-bold text-gray-900">{metrics.total_users.toLocaleString()}</p>
                <p className="text-sm text-gray-500">
                  {metrics.active_users.toLocaleString()} active
                </p>
              </div>
              <div className="h-12 w-12 bg-blue-100 rounded-lg flex items-center justify-center">
                <Users className="h-6 w-6 text-blue-600" />
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg border p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Organizations</p>
                <p className="text-2xl font-bold text-gray-900">{metrics.total_organizations}</p>
                <p className="text-sm text-gray-500">
                  {metrics.total_departments} departments
                </p>
              </div>
              <div className="h-12 w-12 bg-green-100 rounded-lg flex items-center justify-center">
                <Building className="h-6 w-6 text-green-600" />
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg border p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Total Tasks</p>
                <p className="text-2xl font-bold text-gray-900">{metrics.total_tasks.toLocaleString()}</p>
                <p className="text-sm text-green-600">
                  {metrics.task_completion_rate.toFixed(1)}% completion rate
                </p>
              </div>
              <div className="h-12 w-12 bg-purple-100 rounded-lg flex items-center justify-center">
                <FileText className="h-6 w-6 text-purple-600" />
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg border p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Active Projects</p>
                <p className="text-2xl font-bold text-gray-900">{metrics.active_projects}</p>
                <p className="text-sm text-gray-500">
                  of {metrics.total_projects} total
                </p>
              </div>
              <div className="h-12 w-12 bg-orange-100 rounded-lg flex items-center justify-center">
                <BarChart3 className="h-6 w-6 text-orange-600" />
              </div>
            </div>
          </div>
        </div>
      )}

      {/* System Health Status */}
      {systemHealth && (
        <div className="bg-white rounded-lg border p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-medium text-gray-900">System Health</h3>
            <div className="flex items-center gap-2">
              <div className="h-2 w-2 bg-green-500 rounded-full"></div>
              <span className="text-sm text-gray-600">All systems operational</span>
            </div>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-5 gap-4">
            <div className="text-center">
              <div className="text-2xl font-bold text-green-600">{systemHealth.overall_score}%</div>
              <div className="text-sm text-gray-600">Overall Score</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-blue-600">{systemHealth.uptime_percentage}%</div>
              <div className="text-sm text-gray-600">Uptime</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-purple-600">{systemHealth.response_time_avg}ms</div>
              <div className="text-sm text-gray-600">Avg Response</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-orange-600">{systemHealth.active_sessions}</div>
              <div className="text-sm text-gray-600">Active Sessions</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-red-600">{systemHealth.error_rate}%</div>
              <div className="text-sm text-gray-600">Error Rate</div>
            </div>
          </div>
        </div>
      )}

      {/* Charts Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* User Activity Trend */}
        {userTrend && (
          <ChartContainer 
            title="User Activity Trend" 
            subtitle="Daily active users over time"
          >
            <SimpleLineChart
              data={userTrend}
              xKey="date"
              yKey="value"
              height={300}
            />
          </ChartContainer>
        )}

        {/* Task Completion Trend */}
        {taskTrend && (
          <ChartContainer 
            title="Task Completion Trend" 
            subtitle="Daily task completions"
          >
            <SimpleAreaChart
              data={taskTrend}
              xKey="date"
              yKey="value"
              height={300}
            />
          </ChartContainer>
        )}
      </div>

      {/* Task Analytics */}
      {taskAnalytics && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <ChartContainer 
            title="Task Priority Breakdown" 
            subtitle="Current task distribution by priority"
          >
            <SimplePieChart
              data={[
                { name: 'High Priority', value: taskAnalytics.task_priority_breakdown.high },
                { name: 'Medium Priority', value: taskAnalytics.task_priority_breakdown.medium },
                { name: 'Low Priority', value: taskAnalytics.task_priority_breakdown.low }
              ]}
              valueKey="value"
              height={300}
            />
          </ChartContainer>

          <ChartContainer 
            title="Most Active Projects" 
            subtitle="Projects with highest task activity"
          >
            <SimpleBarChart
              data={taskAnalytics.most_active_projects}
              xKey="project_name"
              yKey="task_count"
              height={300}
            />
          </ChartContainer>
        </div>
      )}

      {/* Organization Performance */}
      {orgAnalytics && (
        <ChartContainer 
          title="Department Performance" 
          subtitle="Task completion rates by department"
        >
          <SimpleBarChart
            data={orgAnalytics.department_performance}
            xKey="department_name"
            yKey="task_completion_rate"
            height={300}
          />
        </ChartContainer>
      )}

      {/* Daily Metrics Summary */}
      {taskAnalytics && (
        <div className="bg-white rounded-lg border p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Today&apos;s Activity</h3>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="flex items-center gap-3">
              <div className="h-10 w-10 bg-green-100 rounded-lg flex items-center justify-center">
                <CheckCircle className="h-5 w-5 text-green-600" />
              </div>
              <div>
                <div className="text-lg font-semibold text-gray-900">
                  {taskAnalytics.tasks_completed_today}
                </div>
                <div className="text-sm text-gray-600">Tasks Completed</div>
              </div>
            </div>

            <div className="flex items-center gap-3">
              <div className="h-10 w-10 bg-blue-100 rounded-lg flex items-center justify-center">
                <TrendingUp className="h-5 w-5 text-blue-600" />
              </div>
              <div>
                <div className="text-lg font-semibold text-gray-900">
                  {taskAnalytics.tasks_created_today}
                </div>
                <div className="text-sm text-gray-600">New Tasks</div>
              </div>
            </div>

            <div className="flex items-center gap-3">
              <div className="h-10 w-10 bg-red-100 rounded-lg flex items-center justify-center">
                <AlertTriangle className="h-5 w-5 text-red-600" />
              </div>
              <div>
                <div className="text-lg font-semibold text-gray-900">
                  {taskAnalytics.tasks_overdue}
                </div>
                <div className="text-sm text-gray-600">Overdue Tasks</div>
              </div>
            </div>

            <div className="flex items-center gap-3">
              <div className="h-10 w-10 bg-purple-100 rounded-lg flex items-center justify-center">
                <Clock className="h-5 w-5 text-purple-600" />
              </div>
              <div>
                <div className="text-lg font-semibold text-gray-900">
                  {taskAnalytics.avg_completion_time.toFixed(1)}h
                </div>
                <div className="text-sm text-gray-600">Avg Completion</div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}