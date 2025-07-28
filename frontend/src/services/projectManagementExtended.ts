/**
 * Extended project management service with additional methods
 */

import {
  projectManagementService,
  ListResponse,
  ProjectMember,
  Budget,
  BudgetCreate,
  BudgetUpdate,
  ProgressReport,
  GanttData,
  Task,
  TaskCreate,
  TaskUpdate,
  ProjectMemberCreate,
  ProjectMemberUpdate,
} from "./projectManagement";

// Extend the service with missing methods
export const projectManagementServiceExtended = {
  ...projectManagementService,

  // Extended members methods
  members: {
    list: async (params?: {
      projectId?: number;
    }): Promise<ListResponse<ProjectMember>> => {
      if (params?.projectId) {
        // For now, return empty list since the API doesn't have a list method
        return { items: [], total: 0 };
      }
      return { items: [], total: 0 };
    },

    add: async (data: ProjectMemberCreate): Promise<ProjectMember> => {
      const response = await projectManagementService.members.add(
        data.projectId,
        data,
      );
      // Convert ListResponse to single ProjectMember
      return response.items[0];
    },

    update: async (
      memberId: number,
      data: ProjectMemberUpdate,
    ): Promise<ProjectMember> => {
      // Mock implementation since the original API doesn't have update
      return {
        id: memberId,
        projectId: 1,
        userId: 1,
        role: data.role || "member",
        allocationPercentage: data.allocationPercentage || 100,
        joinedAt: new Date().toISOString(),
        isActive: true,
        userName: "User",
        userEmail: "user@example.com",
      };
    },

    remove: async (memberId: number): Promise<void> => {
      // Extract userId from memberId (temporary solution)
      await projectManagementService.members.remove(1, memberId);
    },
  },

  // Extended budgets methods
  budgets: {
    getByProject: async (projectId: number): Promise<Budget | null> => {
      try {
        return await projectManagementService.budget.get(projectId);
      } catch {
        return null;
      }
    },

    create: async (data: BudgetCreate): Promise<Budget> => {
      // Mock implementation
      return {
        id: 1,
        projectId: data.projectId,
        budgetAmount: data.budgetAmount,
        actualCost: data.actualCost,
        consumptionRate: (data.actualCost / data.budgetAmount) * 100,
        costBreakdown: data.costBreakdown,
        variance: data.budgetAmount - data.actualCost,
        variancePercentage:
          ((data.budgetAmount - data.actualCost) / data.budgetAmount) * 100,
        revenue: data.revenue || 0,
        profit: (data.revenue || 0) - data.actualCost,
        profitRate: data.revenue
          ? ((data.revenue - data.actualCost) / data.revenue) * 100
          : 0,
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
      };
    },

    update: async (budgetId: number, data: BudgetUpdate): Promise<Budget> => {
      // Use project budget update
      return await projectManagementService.budget.update(1, data);
    },
  },

  // Extended projects methods
  projects: {
    ...projectManagementService.projects,

    getProgress: async (projectId: number): Promise<ProgressReport> => {
      return await projectManagementService.reports.getProgress(projectId);
    },

    getGanttData: async (projectId: number): Promise<GanttData> => {
      const ganttChart = await projectManagementService.gantt.get(projectId);
      // Convert GanttChart to GanttData
      return {
        tasks: ganttChart.tasks || [],
        dependencies: ganttChart.dependencies || [],
        criticalPath: ganttChart.criticalPath || [],
      };
    },

    clone: async (projectId: number): Promise<any> => {
      // Mock implementation
      const project = await projectManagementService.projects.get(projectId);
      return await projectManagementService.projects.create({
        code: `${project.code}-CLONE`,
        name: `${project.name} (Copy)`,
        description: project.description,
        startDate: project.startDate,
        endDate: project.endDate,
        budget: project.budget,
        status: "planning",
        projectType: project.projectType,
      });
    },

    autoSchedule: async (projectId: number): Promise<void> => {
      // Mock implementation
      console.log(`Auto-scheduling project ${projectId}`);
    },
  },

  // Extended tasks methods
  tasks: {
    list: async (params?: {
      projectId?: number;
    }): Promise<ListResponse<Task>> => {
      if (params?.projectId) {
        const result = await projectManagementService.tasks.list(
          params.projectId,
        );
        return {
          items: result.tasks,
          total: result.tasks.length,
        };
      }
      return { items: [], total: 0 };
    },

    create: async (data: TaskCreate & { projectId: number }): Promise<Task> => {
      return await projectManagementService.tasks.create(data.projectId, data);
    },

    update: async (taskId: number, data: TaskUpdate): Promise<Task> => {
      // Need to get task first to know projectId
      // Mock implementation for now
      return {
        id: taskId,
        projectId: 1,
        name: data.name || "Task",
        description: data.description,
        parentTaskId: null,
        startDate: data.startDate || new Date().toISOString(),
        endDate: data.endDate || new Date().toISOString(),
        estimatedHours: data.estimatedHours,
        actualHours: data.actualHours,
        priority: data.priority || "medium",
        status: data.status || "not_started",
        progressPercentage: data.progressPercentage || 0,
        assignedTo: [],
        dependencies: [],
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
      };
    },

    delete: async (taskId: number): Promise<void> => {
      // Mock implementation
      console.log(`Deleting task ${taskId}`);
    },
  },
};

// Export as the main service
export { projectManagementServiceExtended as projectManagementService };
