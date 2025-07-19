import { apiClient } from './api'
import {
  DashboardDataResponse,
  DashboardMetrics,
  SystemHealth,
  UserActivity,
  TaskAnalytics,
  OrganizationAnalytics,
  AnalyticsApiResponse,
  ReportRequest,
  ReportResponse,
  DashboardFilters,
  TimeSeriesData,
  PerformanceMetrics
} from '../types/dashboard'

class DashboardApiService {
  private baseUrl = '/api/v1/dashboard'

  async getDashboardData(_filters?: DashboardFilters): Promise<DashboardDataResponse> {
    // Use mock data for now while backend is being stabilized
    return this.generateMockDashboardData()
  }

  async getDashboardDataReal(filters?: DashboardFilters): Promise<DashboardDataResponse> {
    const params = new URLSearchParams()
    
    if (filters?.dateRange) {
      params.append('start_date', filters.dateRange.start)
      params.append('end_date', filters.dateRange.end)
    }
    
    if (filters?.organizations?.length) {
      params.append('organizations', filters.organizations.join(','))
    }
    
    if (filters?.departments?.length) {
      params.append('departments', filters.departments.join(','))
    }
    
    if (filters?.users?.length) {
      params.append('users', filters.users.join(','))
    }
    
    if (filters?.projects?.length) {
      params.append('projects', filters.projects.join(','))
    }

    const queryString = params.toString()
    const url = queryString ? `${this.baseUrl}?${queryString}` : this.baseUrl
    
    const response = await apiClient.get<AnalyticsApiResponse<DashboardDataResponse>>(url)
    return response.data.data
  }

  async getMetrics(filters?: DashboardFilters): Promise<DashboardMetrics> {
    const params = new URLSearchParams()
    
    if (filters?.dateRange) {
      params.append('start_date', filters.dateRange.start)
      params.append('end_date', filters.dateRange.end)
    }

    const queryString = params.toString()
    const url = queryString ? `${this.baseUrl}/metrics?${queryString}` : `${this.baseUrl}/metrics`
    
    const response = await apiClient.get<AnalyticsApiResponse<DashboardMetrics>>(url)
    return response.data.data
  }

  async getSystemHealth(): Promise<SystemHealth> {
    const response = await apiClient.get<AnalyticsApiResponse<SystemHealth>>(`${this.baseUrl}/system-health`)
    return response.data.data
  }

  async getUserActivity(filters?: DashboardFilters): Promise<UserActivity> {
    const params = new URLSearchParams()
    
    if (filters?.dateRange) {
      params.append('start_date', filters.dateRange.start)
      params.append('end_date', filters.dateRange.end)
    }

    const queryString = params.toString()
    const url = queryString ? `${this.baseUrl}/user-activity?${queryString}` : `${this.baseUrl}/user-activity`
    
    const response = await apiClient.get<AnalyticsApiResponse<UserActivity>>(url)
    return response.data.data
  }

  async getTaskAnalytics(filters?: DashboardFilters): Promise<TaskAnalytics> {
    const params = new URLSearchParams()
    
    if (filters?.dateRange) {
      params.append('start_date', filters.dateRange.start)
      params.append('end_date', filters.dateRange.end)
    }
    
    if (filters?.projects?.length) {
      params.append('projects', filters.projects.join(','))
    }

    const queryString = params.toString()
    const url = queryString ? `${this.baseUrl}/task-analytics?${queryString}` : `${this.baseUrl}/task-analytics`
    
    const response = await apiClient.get<AnalyticsApiResponse<TaskAnalytics>>(url)
    return response.data.data
  }

  async getOrganizationAnalytics(filters?: DashboardFilters): Promise<OrganizationAnalytics> {
    const params = new URLSearchParams()
    
    if (filters?.organizations?.length) {
      params.append('organizations', filters.organizations.join(','))
    }
    
    if (filters?.departments?.length) {
      params.append('departments', filters.departments.join(','))
    }

    const queryString = params.toString()
    const url = queryString ? `${this.baseUrl}/organization-analytics?${queryString}` : `${this.baseUrl}/organization-analytics`
    
    const response = await apiClient.get<AnalyticsApiResponse<OrganizationAnalytics>>(url)
    return response.data.data
  }

  async getTimeSeriesData(
    metric: string, 
    period: '1h' | '24h' | '7d' | '30d' | '90d' = '24h',
    filters?: DashboardFilters
  ): Promise<TimeSeriesData[]> {
    const params = new URLSearchParams({
      metric,
      period
    })
    
    if (filters?.dateRange) {
      params.append('start_date', filters.dateRange.start)
      params.append('end_date', filters.dateRange.end)
    }

    const response = await apiClient.get<AnalyticsApiResponse<TimeSeriesData[]>>(
      `${this.baseUrl}/timeseries?${params.toString()}`
    )
    return response.data.data
  }

  async getPerformanceMetrics(): Promise<PerformanceMetrics> {
    const response = await apiClient.get<AnalyticsApiResponse<PerformanceMetrics>>(`${this.baseUrl}/performance`)
    return response.data.data
  }

  async generateReport(request: ReportRequest): Promise<ReportResponse> {
    const response = await apiClient.post<AnalyticsApiResponse<ReportResponse>>(`${this.baseUrl}/reports`, request)
    return response.data.data
  }

  async getReportStatus(reportId: string): Promise<ReportResponse> {
    const response = await apiClient.get<AnalyticsApiResponse<ReportResponse>>(`${this.baseUrl}/reports/${reportId}`)
    return response.data.data
  }

  async downloadReport(reportId: string): Promise<Blob> {
    const response = await apiClient.get<Blob>(`${this.baseUrl}/reports/${reportId}/download`, {
      responseType: 'blob'
    })
    return response.data
  }

  // Mock data generators for development
  generateMockMetrics(): DashboardMetrics {
    return {
      total_users: 1247,
      active_users: 892,
      total_organizations: 15,
      total_departments: 67,
      total_projects: 234,
      active_projects: 156,
      total_tasks: 2847,
      completed_tasks: 1923,
      pending_tasks: 924,
      task_completion_rate: 67.5
    }
  }

  generateMockSystemHealth(): SystemHealth {
    return {
      overall_score: 94,
      uptime_percentage: 99.8,
      response_time_avg: 145,
      active_sessions: 156,
      error_rate: 0.2,
      last_updated: new Date().toISOString()
    }
  }

  generateMockUserActivity(): UserActivity {
    return {
      daily_active_users: 312,
      weekly_active_users: 748,
      monthly_active_users: 1156,
      new_users_today: 12,
      new_users_this_week: 87,
      new_users_this_month: 234,
      user_growth_rate: 15.3
    }
  }

  generateMockTaskAnalytics(): TaskAnalytics {
    return {
      tasks_created_today: 45,
      tasks_completed_today: 38,
      tasks_overdue: 23,
      avg_completion_time: 4.2,
      most_active_projects: [
        { project_id: 1, project_name: 'ERP Migration', task_count: 156, completion_rate: 78.2 },
        { project_id: 2, project_name: 'Mobile App', task_count: 89, completion_rate: 65.4 },
        { project_id: 3, project_name: 'Data Analytics', task_count: 67, completion_rate: 82.1 }
      ],
      task_priority_breakdown: {
        high: 89,
        medium: 234,
        low: 156
      }
    }
  }

  generateMockOrganizationAnalytics(): OrganizationAnalytics {
    return {
      most_active_organizations: [
        { 
          organization_id: 1, 
          organization_name: 'Tech Solutions Inc.', 
          user_count: 234, 
          project_count: 12, 
          task_count: 456, 
          activity_score: 89 
        },
        { 
          organization_id: 2, 
          organization_name: 'Digital Innovations Ltd.', 
          user_count: 156, 
          project_count: 8, 
          task_count: 287, 
          activity_score: 76 
        }
      ],
      department_performance: [
        {
          department_id: 1,
          department_name: 'Engineering',
          organization_name: 'Tech Solutions Inc.',
          user_count: 45,
          task_completion_rate: 84.2,
          avg_response_time: 2.3
        },
        {
          department_id: 2,
          department_name: 'Marketing',
          organization_name: 'Tech Solutions Inc.',
          user_count: 23,
          task_completion_rate: 91.7,
          avg_response_time: 1.8
        }
      ]
    }
  }

  generateMockDashboardData(): DashboardDataResponse {
    return {
      metrics: this.generateMockMetrics(),
      system_health: this.generateMockSystemHealth(),
      user_activity: this.generateMockUserActivity(),
      task_analytics: this.generateMockTaskAnalytics(),
      organization_analytics: this.generateMockOrganizationAnalytics(),
      timestamp: new Date().toISOString()
    }
  }

  generateMockTimeSeriesData(metric: string, days: number = 30): TimeSeriesData[] {
    const data: TimeSeriesData[] = []
    const now = new Date()
    
    for (let i = days - 1; i >= 0; i--) {
      const date = new Date(now)
      date.setDate(date.getDate() - i)
      
      const baseValue = metric === 'users' ? 800 : metric === 'tasks' ? 200 : 50
      const variation = Math.random() * 0.3 - 0.15 // ±15% variation
      const value = Math.round(baseValue * (1 + variation))
      
      data.push({
        date: date.toISOString().split('T')[0],
        value,
        category: metric
      })
    }
    
    return data
  }
}

export const dashboardApi = new DashboardApiService()