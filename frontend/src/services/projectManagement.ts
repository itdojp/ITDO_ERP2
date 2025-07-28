/**
 * プロジェクト管理システムのAPIクライアントサービス
 */

import { apiClient } from './api';

// Types
export interface Project {
  id: number;
  code: string;
  name: string;
  description?: string;
  parentId?: number;
  startDate: string;
  endDate: string;
  budget: number;
  status: 'planning' | 'active' | 'completed' | 'suspended';
  projectType: 'standard' | 'recurring';
  organizationId: number;
  createdBy: number;
  createdAt: string;
  updatedAt: string;
  parentProject?: ProjectSummary;
  subProjects?: ProjectSummary[];
  progressPercentage?: number;
}

export interface ProjectSummary {
  id: number;
  code: string;
  name: string;
  status: string;
}

export interface ProjectCreate {
  code: string;
  name: string;
  description?: string;
  parentId?: number;
  startDate: string;
  endDate: string;
  budget: number;
  status?: 'planning' | 'active' | 'completed' | 'suspended';
  projectType?: 'standard' | 'recurring';
}

export interface ProjectUpdate {
  name?: string;
  description?: string;
  startDate?: string;
  endDate?: string;
  budget?: number;
  status?: 'planning' | 'active' | 'completed' | 'suspended';
}

export interface ProjectMember {
  id: number;
  projectId: number;
  userId: number;
  role: 'project_leader' | 'architect' | 'dev_leader' | 'developer' | 'tester' | 'other';
  allocationPercentage: number;
  startDate: string;
  endDate?: string;
  isActive: boolean;
  user?: UserSummary;
}

export interface ProjectMemberCreate {
  userId: number;
  role: string;
  allocationPercentage: number;
  startDate: string;
  endDate?: string;
}

export interface Task {
  id: number;
  projectId: number;
  parentTaskId?: number;
  name: string;
  description?: string;
  startDate: string;
  endDate: string;
  estimatedHours?: number;
  actualHours?: number;
  progressPercentage: number;
  status: 'not_started' | 'in_progress' | 'completed' | 'on_hold';
  priority: 'high' | 'medium' | 'low';
  createdBy: number;
  createdAt: string;
  updatedAt: string;
  subTasks?: Task[];
  dependencies?: TaskDependency[];
  resources?: ResourceAssignment[];
}

export interface TaskCreate {
  name: string;
  description?: string;
  parentTaskId?: number;
  startDate: string;
  endDate: string;
  estimatedHours?: number;
  priority?: 'high' | 'medium' | 'low';
}

export interface TaskUpdate {
  name?: string;
  description?: string;
  startDate?: string;
  endDate?: string;
  estimatedHours?: number;
  actualHours?: number;
  priority?: 'high' | 'medium' | 'low';
  status?: 'not_started' | 'in_progress' | 'completed' | 'on_hold';
  progressPercentage?: number;
}

export interface TaskDependency {
  id: number;
  predecessorId: number;
  successorId: number;
  dependencyType: 'finish_to_start' | 'start_to_start' | 'finish_to_finish' | 'start_to_finish';
  lagDays: number;
}

export interface ResourceAssignment {
  id: number;
  taskId: number;
  userId: number;
  allocationPercentage: number;
  startDate?: string;
  endDate?: string;
  plannedHours?: number;
  actualHours?: number;
  user?: UserSummary;
}

export interface Milestone {
  id: number;
  projectId: number;
  name: string;
  description?: string;
  targetDate: string;
  achievedDate?: string;
  status: 'pending' | 'achieved' | 'delayed' | 'cancelled';
  deliverable?: string;
  approverId?: number;
  approver?: UserSummary;
}

export interface MilestoneCreate {
  name: string;
  description?: string;
  targetDate: string;
  deliverable?: string;
  approverId?: number;
}

export interface Budget {
  budgetAmount: number;
  estimatedCost: number;
  actualCost: number;
  costBreakdown: {
    labor: CostItem;
    outsourcing: CostItem;
    expense: CostItem;
  };
  consumptionRate: number;
  forecastAtCompletion: number;
  variance: number;
  revenue: number;
  profit: number;
  profitRate: number;
}

export interface CostItem {
  planned: number;
  actual: number;
  variance: number;
}

export interface BudgetUpdate {
  estimatedCost?: number;
  actualCost?: number;
  laborCost?: number;
  outsourcingCost?: number;
  expenseCost?: number;
}

export interface GanttTask {
  id: number;
  name: string;
  startDate: string;
  endDate: string;
  progress: number;
  level: number;
  isMilestone: boolean;
  resources: string[];
}

export interface GanttDependency {
  source: number;
  target: number;
  type: string;
}

export interface GanttChart {
  tasks: GanttTask[];
  dependencies: GanttDependency[];
  criticalPath: number[];
}

export interface ResourceInfo {
  id: number;
  name: string;
  email: string;
  skills: string[];
  maxAllocation: number;
  currentAllocation: number;
}

export interface UtilizationDetail {
  date: string;
  utilization: number;
}

export interface UtilizationReport {
  resourceId: number;
  period: {
    startDate: string;
    endDate: string;
  };
  dailyUtilization: UtilizationDetail[];
  averageUtilization: number;
  peakUtilization: number;
  overallocatedDays: number;
}

export interface ProgressReport {
  project: ProjectSummary;
  reportDate: string;
  overallProgress: number;
  milestoneStatus: Record<string, number>;
  taskStatus: Record<string, number>;
  budgetStatus: {
    budgetAmount: number;
    actualCost: number;
    consumptionRate: number;
  };
  risks: Array<{
    type: string;
    description: string;
    impact: string;
  }>;
}

export interface RecurringProjectCreate {
  template: ProjectCreate;
  recurrencePattern: 'daily' | 'weekly' | 'monthly' | 'yearly';
  recurrenceCount: number;
  startDate: string;
}

export interface UserSummary {
  id: number;
  name: string;
  email: string;
}

export interface ListResponse<T> {
  items: T[];
  total: number;
  page?: number;
  pageSize?: number;
}

// API Service
export const projectManagementService = {
  // Projects
  projects: {
    list: async (params?: {
      status?: string;
      parentId?: number;
      page?: number;
      pageSize?: number;
    }): Promise<ListResponse<Project>> => {
      const response = await apiClient.get('/api/v1/projects', { params });
      return response.data;
    },

    get: async (projectId: number): Promise<Project> => {
      const response = await apiClient.get(`/api/v1/projects/${projectId}`);
      return response.data;
    },

    create: async (data: ProjectCreate): Promise<Project> => {
      const response = await apiClient.post('/api/v1/projects', data);
      return response.data;
    },

    update: async (projectId: number, data: ProjectUpdate): Promise<Project> => {
      const response = await apiClient.put(`/api/v1/projects/${projectId}`, data);
      return response.data;
    },

    delete: async (projectId: number): Promise<void> => {
      await apiClient.delete(`/api/v1/projects/${projectId}`);
    },

    // Recurring projects
    createRecurring: async (data: RecurringProjectCreate): Promise<{
      masterProject: Project;
      generatedProjects: Project[];
      totalBudget: number;
    }> => {
      const response = await apiClient.post('/api/v1/projects/recurring', data);
      return response.data;
    },
  },

  // Project Members
  members: {
    add: async (projectId: number, data: ProjectMemberCreate): Promise<ListResponse<ProjectMember>> => {
      const response = await apiClient.post(`/api/v1/projects/${projectId}/members`, data);
      return response.data;
    },

    remove: async (projectId: number, userId: number): Promise<void> => {
      await apiClient.delete(`/api/v1/projects/${projectId}/members/${userId}`);
    },
  },

  // Tasks
  tasks: {
    list: async (projectId: number): Promise<{ tasks: Task[] }> => {
      const response = await apiClient.get(`/api/v1/projects/${projectId}/tasks`);
      return response.data;
    },

    get: async (projectId: number, taskId: number): Promise<Task> => {
      const response = await apiClient.get(`/api/v1/projects/${projectId}/tasks/${taskId}`);
      return response.data;
    },

    create: async (projectId: number, data: TaskCreate): Promise<Task> => {
      const response = await apiClient.post(`/api/v1/projects/${projectId}/tasks`, data);
      return response.data;
    },

    update: async (projectId: number, taskId: number, data: TaskUpdate): Promise<Task> => {
      const response = await apiClient.put(`/api/v1/projects/${projectId}/tasks/${taskId}`, data);
      return response.data;
    },

    delete: async (projectId: number, taskId: number): Promise<void> => {
      await apiClient.delete(`/api/v1/projects/${projectId}/tasks/${taskId}`);
    },

    updateProgress: async (projectId: number, taskId: number, data: {
      progressPercentage: number;
      actualHours: number;
      comment?: string;
    }): Promise<Task> => {
      const response = await apiClient.put(
        `/api/v1/projects/${projectId}/tasks/${taskId}/progress`,
        data
      );
      return response.data;
    },

    createDependency: async (projectId: number, taskId: number, data: {
      predecessorId: number;
      dependencyType?: string;
      lagDays?: number;
    }): Promise<void> => {
      await apiClient.post(
        `/api/v1/projects/${projectId}/tasks/${taskId}/dependencies`,
        data
      );
    },
  },

  // Resources
  resources: {
    listByProject: async (projectId: number): Promise<ListResponse<ResourceInfo>> => {
      const response = await apiClient.get(`/api/v1/projects/${projectId}/resources`);
      return response.data;
    },

    assignToTask: async (projectId: number, taskId: number, data: {
      resourceId: number;
      allocationPercentage: number;
      startDate?: string;
      endDate?: string;
      plannedHours?: number;
    }): Promise<void> => {
      await apiClient.post(
        `/api/v1/projects/${projectId}/tasks/${taskId}/resources`,
        data
      );
    },

    getUtilization: async (userId: number, startDate: string, endDate: string): Promise<UtilizationReport> => {
      const response = await apiClient.get(`/api/v1/projects/resources/${userId}/utilization`, {
        params: { startDate, endDate }
      });
      return response.data;
    },
  },

  // Milestones
  milestones: {
    list: async (projectId: number, status?: string): Promise<ListResponse<Milestone>> => {
      const response = await apiClient.get(`/api/v1/projects/${projectId}/milestones`, {
        params: { status }
      });
      return response.data;
    },

    create: async (projectId: number, data: MilestoneCreate): Promise<Milestone> => {
      const response = await apiClient.post(`/api/v1/projects/${projectId}/milestones`, data);
      return response.data;
    },
  },

  // Budget
  budget: {
    get: async (projectId: number): Promise<Budget> => {
      const response = await apiClient.get(`/api/v1/projects/${projectId}/budget`);
      return response.data;
    },

    update: async (projectId: number, data: BudgetUpdate): Promise<Budget> => {
      const response = await apiClient.put(`/api/v1/projects/${projectId}/budget`, data);
      return response.data;
    },
  },

  // Gantt Chart
  gantt: {
    get: async (projectId: number): Promise<GanttChart> => {
      const response = await apiClient.get(`/api/v1/projects/${projectId}/gantt`);
      return response.data;
    },
  },

  // Reports
  reports: {
    getProgress: async (projectId: number, reportDate?: string): Promise<ProgressReport> => {
      const response = await apiClient.get(`/api/v1/projects/${projectId}/reports/progress`, {
        params: { reportDate }
      });
      return response.data;
    },
  },
};

export default projectManagementService;