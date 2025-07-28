/**
 * プロジェクト管理システムE2Eテスト用のテストデータとユーティリティ
 */

export const testProjects = {
  parent: {
    code: 'E2E-PARENT-001',
    name: 'E2E親プロジェクト',
    description: 'E2Eテスト用の親プロジェクト',
    startDate: '2024-01-01',
    endDate: '2024-12-31',
    budget: '50000000',
    status: 'active',
    projectType: 'standard',
  },
  child: {
    code: 'E2E-CHILD-001',
    name: 'E2E子プロジェクト',
    description: 'E2Eテスト用の子プロジェクト',
    startDate: '2024-02-01',
    endDate: '2024-06-30',
    budget: '10000000',
    status: 'active',
    projectType: 'standard',
  },
  recurring: {
    code: 'E2E-RECURRING-001',
    name: 'E2E月次レポート',
    description: 'E2Eテスト用の繰り返しプロジェクト',
    startDate: '2024-01-01',
    endDate: '2024-01-31',
    budget: '1000000',
    status: 'planning',
    projectType: 'recurring',
  },
};

export const testTasks = {
  design: {
    name: 'E2E設計フェーズ',
    description: '設計作業のタスク',
    startDate: '2024-01-15',
    endDate: '2024-02-15',
    estimatedHours: '80',
    priority: 'high',
  },
  development: {
    name: 'E2E開発フェーズ',
    description: '開発作業のタスク',
    startDate: '2024-02-16',
    endDate: '2024-04-30',
    estimatedHours: '320',
    priority: 'high',
  },
  testing: {
    name: 'E2Eテストフェーズ',
    description: 'テスト作業のタスク',
    startDate: '2024-05-01',
    endDate: '2024-05-31',
    estimatedHours: '160',
    priority: 'medium',
  },
  subtask: {
    name: 'E2E単体テスト',
    description: 'サブタスクのテスト',
    startDate: '2024-05-01',
    endDate: '2024-05-15',
    estimatedHours: '80',
    priority: 'medium',
  },
};

export const testMembers = {
  manager: {
    userId: '1',
    role: 'manager',
    allocationPercentage: '50',
  },
  developer1: {
    userId: '2',
    role: 'member',
    allocationPercentage: '100',
  },
  developer2: {
    userId: '3',
    role: 'member',
    allocationPercentage: '80',
  },
  observer: {
    userId: '4',
    role: 'observer',
    allocationPercentage: '20',
  },
};

export const testBudget = {
  labor: {
    planned: '5000000',
    actual: '4500000',
  },
  outsourcing: {
    planned: '3000000',
    actual: '3200000',
  },
  expense: {
    planned: '2000000',
    actual: '1800000',
  },
  revenue: '15000000',
};

// ユーティリティ関数
export function generateProjectCode(prefix: string = 'E2E'): string {
  const timestamp = Date.now();
  return `${prefix}-${timestamp}`;
}

export function getFutureDate(daysFromNow: number): string {
  const date = new Date();
  date.setDate(date.getDate() + daysFromNow);
  return date.toISOString().split('T')[0];
}

export function getDateRange(startDaysFromNow: number, durationDays: number): { start: string; end: string } {
  return {
    start: getFutureDate(startDaysFromNow),
    end: getFutureDate(startDaysFromNow + durationDays),
  };
}

// テストデータのクリーンアップ用
export async function cleanupTestProjects(page: any, projectCodePrefix: string = 'E2E') {
  // APIを使用してテストプロジェクトを削除
  // 実装はAPIの仕様に応じて調整
  try {
    const response = await page.request.get('/api/v1/projects', {
      params: { search: projectCodePrefix },
    });
    
    if (response.ok()) {
      const data = await response.json();
      const testProjects = data.items.filter((p: any) => p.code.startsWith(projectCodePrefix));
      
      for (const project of testProjects) {
        await page.request.delete(`/api/v1/projects/${project.id}`);
      }
    }
  } catch (error) {
    console.error('Failed to cleanup test projects:', error);
  }
}

// ランダムなテストデータ生成
export function generateRandomProject(index: number = 0) {
  const dateRange = getDateRange(index * 30, 90);
  return {
    code: generateProjectCode(),
    name: `自動生成プロジェクト ${index + 1}`,
    description: `パフォーマンステスト用のプロジェクト ${index + 1}`,
    startDate: dateRange.start,
    endDate: dateRange.end,
    budget: String(Math.floor(Math.random() * 10000000) + 1000000),
    status: ['planning', 'active', 'completed'][Math.floor(Math.random() * 3)],
    projectType: 'standard',
  };
}

export function generateRandomTask(projectStartDate: string, index: number = 0) {
  const startOffset = index * 10;
  const duration = Math.floor(Math.random() * 20) + 5;
  const startDate = new Date(projectStartDate);
  startDate.setDate(startDate.getDate() + startOffset);
  
  const endDate = new Date(startDate);
  endDate.setDate(endDate.getDate() + duration);
  
  return {
    name: `タスク ${index + 1}`,
    description: `自動生成されたタスク ${index + 1}`,
    startDate: startDate.toISOString().split('T')[0],
    endDate: endDate.toISOString().split('T')[0],
    estimatedHours: String(duration * 8),
    priority: ['high', 'medium', 'low'][Math.floor(Math.random() * 3)],
    progressPercentage: String(Math.floor(Math.random() * 101)),
  };
}

// API モック用のレスポンス
export const mockApiResponses = {
  projectList: {
    items: [
      {
        id: 1,
        ...testProjects.parent,
        createdAt: '2024-01-01T00:00:00Z',
        updatedAt: '2024-01-01T00:00:00Z',
      },
    ],
    total: 1,
    page: 1,
    pageSize: 10,
  },
  projectDetail: {
    id: 1,
    ...testProjects.parent,
    progressPercentage: 45,
    subProjects: [],
    createdAt: '2024-01-01T00:00:00Z',
    updatedAt: '2024-01-01T00:00:00Z',
  },
  taskList: {
    items: [
      {
        id: 1,
        projectId: 1,
        ...testTasks.design,
        status: 'completed',
        progressPercentage: 100,
        createdAt: '2024-01-15T00:00:00Z',
        updatedAt: '2024-02-15T00:00:00Z',
      },
      {
        id: 2,
        projectId: 1,
        ...testTasks.development,
        status: 'in_progress',
        progressPercentage: 60,
        createdAt: '2024-02-16T00:00:00Z',
        updatedAt: '2024-03-30T00:00:00Z',
      },
    ],
    total: 2,
  },
};