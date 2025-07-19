/**
 * Dashboard and Analytics type definitions
 */

// Core Analytics Types
export interface DashboardMetrics {
  total_users: number
  active_users: number
  total_organizations: number
  total_departments: number
  total_projects: number
  active_projects: number
  total_tasks: number
  completed_tasks: number
  pending_tasks: number
  task_completion_rate: number
}

export interface SystemHealth {
  overall_score: number // 0-100
  uptime_percentage: number
  response_time_avg: number // in milliseconds
  active_sessions: number
  error_rate: number // percentage
  last_updated: string
}

export interface UserActivity {
  daily_active_users: number
  weekly_active_users: number
  monthly_active_users: number
  new_users_today: number
  new_users_this_week: number
  new_users_this_month: number
  user_growth_rate: number // percentage
}

export interface TaskAnalytics {
  tasks_created_today: number
  tasks_completed_today: number
  tasks_overdue: number
  avg_completion_time: number // in hours
  most_active_projects: Array<{
    project_id: number
    project_name: string
    task_count: number
    completion_rate: number
  }>
  task_priority_breakdown: {
    high: number
    medium: number
    low: number
  }
}

export interface OrganizationAnalytics {
  most_active_organizations: Array<{
    organization_id: number
    organization_name: string
    user_count: number
    project_count: number
    task_count: number
    activity_score: number
  }>
  department_performance: Array<{
    department_id: number
    department_name: string
    organization_name: string
    user_count: number
    task_completion_rate: number
    avg_response_time: number
  }>
}

// Chart Data Types
export interface ChartDataPoint {
  x: string | number
  y: number
  label?: string
}

export interface TimeSeriesData extends Record<string, unknown> {
  date: string
  value: number
  category?: string
}

export interface PieChartData {
  name: string
  value: number
  color?: string
}

export interface BarChartData {
  category: string
  value: number
  color?: string
}

// Dashboard Component Types
export interface DashboardWidget {
  id: string
  title: string
  type: 'metric' | 'chart' | 'list' | 'table'
  size: 'small' | 'medium' | 'large'
  data: Record<string, unknown>
  refreshInterval?: number // in seconds
  lastUpdated: string
}

export interface MetricWidget extends DashboardWidget {
  type: 'metric'
  data: {
    value: number | string
    change?: number // percentage change
    trend?: 'up' | 'down' | 'stable'
    icon?: string
    color?: string
  }
}

export interface ChartWidget extends DashboardWidget {
  type: 'chart'
  data: {
    chartType: 'line' | 'bar' | 'pie' | 'area' | 'donut'
    datasets: Array<{
      label: string
      data: ChartDataPoint[]
      color?: string
    }>
    options?: Record<string, unknown>
  }
}

// Filters and Options
export interface DashboardFilters {
  dateRange?: {
    start: string
    end: string
  }
  organizations?: number[]
  departments?: number[]
  users?: number[]
  projects?: number[]
}

export interface DateRangeOption {
  label: string
  value: string
  days: number
}

// API Response Types
export interface DashboardDataResponse {
  metrics: DashboardMetrics
  system_health: SystemHealth
  user_activity: UserActivity
  task_analytics: TaskAnalytics
  organization_analytics: OrganizationAnalytics
  timestamp: string
}

export interface AnalyticsApiResponse<T> {
  data: T
  success: boolean
  timestamp: string
  cache_duration?: number
}

// Report Types
export interface ReportRequest {
  type: 'users' | 'organizations' | 'tasks' | 'projects' | 'system_health'
  format: 'pdf' | 'csv' | 'excel'
  filters: DashboardFilters
  include_charts: boolean
}

export interface ReportResponse {
  report_id: string
  download_url: string
  expires_at: string
  file_size: number
  status: 'generating' | 'ready' | 'failed'
}

// Real-time Updates
export interface RealtimeUpdate {
  type: 'metric_update' | 'new_user' | 'task_completed' | 'system_alert'
  data: Record<string, unknown>
  timestamp: string
}

export interface SystemAlert {
  id: string
  type: 'info' | 'warning' | 'error' | 'success'
  title: string
  message: string
  timestamp: string
  dismissed: boolean
  actions?: Array<{
    label: string
    action: string
  }>
}

// Performance Monitoring
export interface PerformanceMetrics {
  page_load_time: number
  api_response_times: Record<string, number>
  error_rates: Record<string, number>
  user_interactions: Record<string, number>
  browser_stats: Record<string, number>
  device_stats: Record<string, number>
}

// Constants
export const DATE_RANGE_OPTIONS: DateRangeOption[] = [
  { label: 'Today', value: 'today', days: 1 },
  { label: 'Yesterday', value: 'yesterday', days: 1 },
  { label: 'Last 7 days', value: 'week', days: 7 },
  { label: 'Last 30 days', value: 'month', days: 30 },
  { label: 'Last 90 days', value: 'quarter', days: 90 },
  { label: 'Last 365 days', value: 'year', days: 365 },
  { label: 'Custom', value: 'custom', days: 0 }
]

export const CHART_COLORS = [
  '#3B82F6', // blue
  '#10B981', // green  
  '#F59E0B', // yellow
  '#EF4444', // red
  '#8B5CF6', // purple
  '#F97316', // orange
  '#06B6D4', // cyan
  '#84CC16', // lime
  '#EC4899', // pink
  '#6B7280'  // gray
]

export const WIDGET_SIZES = {
  small: 'col-span-1 row-span-1',
  medium: 'col-span-2 row-span-1', 
  large: 'col-span-2 row-span-2'
}

// Utility Types
export type DashboardTheme = 'light' | 'dark' | 'auto'
export type RefreshInterval = 30 | 60 | 300 | 600 | 1800 | 3600 // seconds
export type ChartType = 'line' | 'bar' | 'pie' | 'area' | 'donut' | 'scatter'
export type MetricTrend = 'up' | 'down' | 'stable'
export type AlertSeverity = 'low' | 'medium' | 'high' | 'critical'