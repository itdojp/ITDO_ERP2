// API Types and Interfaces

export interface BaseEntity {
  id: string
  createdAt: string
  updatedAt: string
  deletedAt?: string
}

export interface User extends BaseEntity {
  email: string
  firstName: string
  lastName: string
  fullName: string
  avatar?: string
  role: UserRole
  status: UserStatus
  lastLoginAt?: string
  emailVerifiedAt?: string
  preferences: UserPreferences
  permissions: Permission[]
  organizationId?: string
}

export interface UserPreferences {
  theme: 'light' | 'dark' | 'system'
  language: string
  timezone: string
  notifications: NotificationPreferences
  accessibility: AccessibilityPreferences
}

export interface NotificationPreferences {
  email: boolean
  push: boolean
  desktop: boolean
  types: {
    taskAssigned: boolean
    taskCompleted: boolean
    projectUpdates: boolean
    mentions: boolean
    deadlines: boolean
  }
}

export interface AccessibilityPreferences {
  reducedMotion: boolean
  highContrast: boolean
  fontSize: 'small' | 'medium' | 'large' | 'x-large'
  screenReaderOptimized: boolean
}

export enum UserRole {
  ADMIN = 'admin',
  MANAGER = 'manager',
  MEMBER = 'member',
  VIEWER = 'viewer',
  GUEST = 'guest'
}

export enum UserStatus {
  ACTIVE = 'active',
  INACTIVE = 'inactive',
  PENDING = 'pending',
  SUSPENDED = 'suspended'
}

export interface Permission {
  id: string
  name: string
  resource: string
  action: string
  conditions?: Record<string, any>
}

export interface Organization extends BaseEntity {
  name: string
  slug: string
  description?: string
  logo?: string
  website?: string
  industry?: string
  size: OrganizationSize
  plan: SubscriptionPlan
  settings: OrganizationSettings
  memberCount: number
  projectCount: number
}

export enum OrganizationSize {
  STARTUP = 'startup',
  SMALL = 'small',
  MEDIUM = 'medium',
  LARGE = 'large',
  ENTERPRISE = 'enterprise'
}

export interface SubscriptionPlan {
  id: string
  name: string
  features: string[]
  limits: PlanLimits
  price: number
  currency: string
  interval: 'monthly' | 'yearly'
}

export interface PlanLimits {
  users: number
  projects: number
  storage: number // in GB
  apiCalls: number
}

export interface OrganizationSettings {
  allowGuestAccess: boolean
  requireEmailVerification: boolean
  passwordPolicy: PasswordPolicy
  sessionTimeout: number
  twoFactorRequired: boolean
}

export interface PasswordPolicy {
  minLength: number
  requireUppercase: boolean
  requireLowercase: boolean
  requireNumbers: boolean
  requireSymbols: boolean
  maxAge: number // days
}

export interface Project extends BaseEntity {
  name: string
  description?: string
  status: ProjectStatus
  priority: Priority
  startDate?: string
  endDate?: string
  budget?: number
  currency?: string
  progress: number
  organizationId: string
  managerId: string
  members: ProjectMember[]
  tags: string[]
  settings: ProjectSettings
  statistics: ProjectStatistics
}

export enum ProjectStatus {
  PLANNING = 'planning',
  ACTIVE = 'active',
  ON_HOLD = 'on_hold',
  COMPLETED = 'completed',
  CANCELLED = 'cancelled',
  ARCHIVED = 'archived'
}

export enum Priority {
  LOW = 'low',
  MEDIUM = 'medium',
  HIGH = 'high',
  CRITICAL = 'critical'
}

export interface ProjectMember {
  userId: string
  user: User
  role: ProjectRole
  joinedAt: string
  permissions: string[]
}

export enum ProjectRole {
  OWNER = 'owner',
  MANAGER = 'manager',
  DEVELOPER = 'developer',
  DESIGNER = 'designer',
  TESTER = 'tester',
  VIEWER = 'viewer'
}

export interface ProjectSettings {
  isPublic: boolean
  allowGuestAccess: boolean
  requireTaskApproval: boolean
  autoAssignTasks: boolean
  notifyOnUpdates: boolean
}

export interface ProjectStatistics {
  totalTasks: number
  completedTasks: number
  overdueTasks: number
  totalTimeLogged: number
  averageCompletionTime: number
  memberActivity: Record<string, number>
}

export interface Task extends BaseEntity {
  title: string
  description?: string
  status: TaskStatus
  priority: Priority
  type: TaskType
  assigneeId?: string
  assignee?: User
  reporterId: string
  reporter: User
  projectId: string
  project?: Project
  parentTaskId?: string
  subtasks?: Task[]
  dueDate?: string
  estimatedHours?: number
  actualHours?: number
  startDate?: string
  completedAt?: string
  tags: string[]
  labels: Label[]
  attachments: FileAttachment[]
  comments: Comment[]
  timeLogs: TimeLog[]
  dependencies: TaskDependency[]
  customFields: Record<string, any>
}

export enum TaskStatus {
  TODO = 'todo',
  IN_PROGRESS = 'in_progress',
  IN_REVIEW = 'in_review',
  BLOCKED = 'blocked',
  DONE = 'done',
  CANCELLED = 'cancelled'
}

export enum TaskType {
  FEATURE = 'feature',
  BUG = 'bug',
  IMPROVEMENT = 'improvement',
  TASK = 'task',
  EPIC = 'epic',
  STORY = 'story',
  SUBTASK = 'subtask'
}

export interface Label {
  id: string
  name: string
  color: string
  description?: string
}

export interface FileAttachment extends BaseEntity {
  filename: string
  originalName: string
  mimeType: string
  size: number
  url: string
  thumbnailUrl?: string
  uploadedById: string
  uploadedBy?: User
}

export interface Comment extends BaseEntity {
  content: string
  authorId: string
  author: User
  parentCommentId?: string
  replies?: Comment[]
  mentions: string[]
  attachments: FileAttachment[]
  reactions: Reaction[]
}

export interface Reaction {
  id: string
  type: string
  emoji: string
  userId: string
  user?: User
  createdAt: string
}

export interface TimeLog extends BaseEntity {
  description?: string
  duration: number // minutes
  startTime: string
  endTime?: string
  userId: string
  user?: User
  taskId: string
  task?: Task
  billable: boolean
  approved: boolean
}

export interface TaskDependency {
  id: string
  taskId: string
  dependsOnTaskId: string
  type: DependencyType
  createdAt: string
}

export enum DependencyType {
  BLOCKS = 'blocks',
  BLOCKED_BY = 'blocked_by',
  RELATES_TO = 'relates_to',
  DUPLICATES = 'duplicates'
}

export interface Notification extends BaseEntity {
  title: string
  message: string
  type: NotificationType
  category: NotificationCategory
  read: boolean
  readAt?: string
  actionUrl?: string
  actionText?: string
  userId: string
  relatedEntityType?: string
  relatedEntityId?: string
  metadata?: Record<string, any>
}

export enum NotificationType {
  INFO = 'info',
  SUCCESS = 'success',
  WARNING = 'warning',
  ERROR = 'error'
}

export enum NotificationCategory {
  TASK = 'task',
  PROJECT = 'project',
  SYSTEM = 'system',
  MENTION = 'mention',
  DEADLINE = 'deadline',
  APPROVAL = 'approval'
}

export interface SearchResult<T = any> {
  item: T
  score: number
  highlights: Record<string, string[]>
  type: string
}

export interface SearchResponse<T = any> {
  results: SearchResult<T>[]
  total: number
  query: string
  filters: Record<string, any>
  facets: Record<string, SearchFacet[]>
  suggestions: string[]
  executionTime: number
}

export interface SearchFacet {
  value: string
  count: number
  selected: boolean
}

export interface DashboardStats {
  totalProjects: number
  activeProjects: number
  totalTasks: number
  completedTasks: number
  overdueTasks: number
  totalUsers: number
  activeUsers: number
  recentActivity: ActivityItem[]
  upcomingDeadlines: Task[]
  projectProgress: ProjectProgress[]
  timeSpent: TimeSpentData
}

export interface ActivityItem {
  id: string
  type: string
  message: string
  userId: string
  user?: User
  entityType?: string
  entityId?: string
  timestamp: string
  metadata?: Record<string, any>
}

export interface ProjectProgress {
  projectId: string
  projectName: string
  progress: number
  status: ProjectStatus
  dueDate?: string
  tasksCompleted: number
  totalTasks: number
}

export interface TimeSpentData {
  today: number
  thisWeek: number
  thisMonth: number
  breakdown: {
    date: string
    hours: number
  }[]
}

export interface Report extends BaseEntity {
  name: string
  description?: string
  type: ReportType
  format: ReportFormat
  parameters: ReportParameters
  schedule?: ReportSchedule
  generatedAt?: string
  fileUrl?: string
  status: ReportStatus
  createdById: string
  createdBy?: User
}

export enum ReportType {
  PROJECT_SUMMARY = 'project_summary',
  TIME_TRACKING = 'time_tracking',
  USER_ACTIVITY = 'user_activity',
  TASK_COMPLETION = 'task_completion',
  CUSTOM = 'custom'
}

export enum ReportFormat {
  PDF = 'pdf',
  EXCEL = 'excel',
  CSV = 'csv',
  JSON = 'json'
}

export interface ReportParameters {
  dateRange: {
    start: string
    end: string
  }
  projects?: string[]
  users?: string[]
  filters?: Record<string, any>
  groupBy?: string[]
  metrics?: string[]
}

export interface ReportSchedule {
  frequency: 'daily' | 'weekly' | 'monthly' | 'quarterly'
  dayOfWeek?: number
  dayOfMonth?: number
  time?: string
  timezone?: string
  recipients: string[]
}

export enum ReportStatus {
  PENDING = 'pending',
  GENERATING = 'generating',
  COMPLETED = 'completed',
  FAILED = 'failed'
}

// API Request/Response types
export interface LoginRequest {
  email: string
  password: string
  rememberMe?: boolean
}

export interface LoginResponse {
  user: User
  tokens: {
    accessToken: string
    refreshToken: string
    expiresIn: number
  }
  permissions: Permission[]
}

export interface CreateUserRequest {
  email: string
  firstName: string
  lastName: string
  role: UserRole
  organizationId?: string
  sendInvite?: boolean
}

export interface UpdateUserRequest {
  firstName?: string
  lastName?: string
  role?: UserRole
  status?: UserStatus
  preferences?: Partial<UserPreferences>
}

export interface CreateProjectRequest {
  name: string
  description?: string
  organizationId: string
  managerId?: string
  startDate?: string
  endDate?: string
  budget?: number
  currency?: string
  settings?: Partial<ProjectSettings>
  memberIds?: string[]
}

export interface UpdateProjectRequest {
  name?: string
  description?: string
  status?: ProjectStatus
  priority?: Priority
  startDate?: string
  endDate?: string
  budget?: number
  currency?: string
  settings?: Partial<ProjectSettings>
}

export interface CreateTaskRequest {
  title: string
  description?: string
  projectId: string
  assigneeId?: string
  parentTaskId?: string
  priority?: Priority
  type?: TaskType
  dueDate?: string
  estimatedHours?: number
  tags?: string[]
  customFields?: Record<string, any>
}

export interface UpdateTaskRequest {
  title?: string
  description?: string
  status?: TaskStatus
  priority?: Priority
  assigneeId?: string
  dueDate?: string
  estimatedHours?: number
  tags?: string[]
  customFields?: Record<string, any>
}

export interface SearchRequest {
  query: string
  types?: string[]
  filters?: Record<string, any>
  sort?: string
  order?: 'asc' | 'desc'
  page?: number
  limit?: number
}

// Utility types
export type EntityType = 'user' | 'organization' | 'project' | 'task' | 'comment' | 'file'

export interface AuditLog extends BaseEntity {
  action: string
  entityType: EntityType
  entityId: string
  userId: string
  user?: User
  changes: Record<string, any>
  metadata: Record<string, any>
  ipAddress?: string
  userAgent?: string
}

export interface SystemHealth {
  status: 'healthy' | 'degraded' | 'down'
  version: string
  uptime: number
  services: ServiceHealth[]
  metrics: SystemMetrics
}

export interface ServiceHealth {
  name: string
  status: 'healthy' | 'degraded' | 'down'
  responseTime: number
  lastCheck: string
  message?: string
}

export interface SystemMetrics {
  cpu: number
  memory: number
  disk: number
  activeConnections: number
  requestsPerSecond: number
  errorRate: number
}

export default {}