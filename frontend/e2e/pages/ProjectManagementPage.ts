/**
 * プロジェクト管理システムのPage Objectモデル
 */

import { Page, Locator } from '@playwright/test';

export class ProjectListPage {
  readonly page: Page;
  readonly newProjectButton: Locator;
  readonly searchInput: Locator;
  readonly statusFilter: Locator;
  readonly searchButton: Locator;
  readonly resetButton: Locator;

  constructor(page: Page) {
    this.page = page;
    this.newProjectButton = page.locator('button:has-text("新規プロジェクト")');
    this.searchInput = page.locator('input[placeholder="プロジェクト名で検索..."]');
    this.statusFilter = page.locator('select').first();
    this.searchButton = page.locator('button:has-text("検索")');
    this.resetButton = page.locator('button svg.h-5.w-5').last();
  }

  async goto() {
    await this.page.goto('/projects');
  }

  async searchProjects(searchTerm: string) {
    await this.searchInput.fill(searchTerm);
    await this.searchButton.click();
  }

  async filterByStatus(status: string) {
    await this.statusFilter.selectOption(status);
  }

  async clickNewProject() {
    await this.newProjectButton.click();
  }

  async clickProjectCard(index: number = 0) {
    await this.page.locator('.bg-white.shadow.rounded-lg').nth(index).click();
  }
}

export class ProjectFormPage {
  readonly page: Page;
  readonly codeInput: Locator;
  readonly nameInput: Locator;
  readonly descriptionTextarea: Locator;
  readonly parentSelect: Locator;
  readonly startDateInput: Locator;
  readonly endDateInput: Locator;
  readonly budgetInput: Locator;
  readonly statusSelect: Locator;
  readonly projectTypeSelect: Locator;
  readonly submitButton: Locator;
  readonly cancelButton: Locator;

  constructor(page: Page) {
    this.page = page;
    this.codeInput = page.locator('input[id="code"]');
    this.nameInput = page.locator('input[id="name"]');
    this.descriptionTextarea = page.locator('textarea[id="description"]');
    this.parentSelect = page.locator('select[id="parentId"]');
    this.startDateInput = page.locator('input[id="startDate"]');
    this.endDateInput = page.locator('input[id="endDate"]');
    this.budgetInput = page.locator('input[id="budget"]');
    this.statusSelect = page.locator('select[id="status"]');
    this.projectTypeSelect = page.locator('select[id="projectType"]');
    this.submitButton = page.locator('button[type="submit"]');
    this.cancelButton = page.locator('button:has-text("キャンセル")');
  }

  async fillForm(data: {
    code?: string;
    name?: string;
    description?: string;
    parentId?: string;
    startDate?: string;
    endDate?: string;
    budget?: string;
    status?: string;
    projectType?: string;
  }) {
    if (data.code) await this.codeInput.fill(data.code);
    if (data.name) await this.nameInput.fill(data.name);
    if (data.description) await this.descriptionTextarea.fill(data.description);
    if (data.parentId) await this.parentSelect.selectOption(data.parentId);
    if (data.startDate) await this.startDateInput.fill(data.startDate);
    if (data.endDate) await this.endDateInput.fill(data.endDate);
    if (data.budget) await this.budgetInput.fill(data.budget);
    if (data.status) await this.statusSelect.selectOption(data.status);
    if (data.projectType) await this.projectTypeSelect.selectOption(data.projectType);
  }

  async submit() {
    await this.submitButton.click();
  }

  async cancel() {
    await this.cancelButton.click();
  }
}

export class ProjectDetailPage {
  readonly page: Page;
  readonly tabs: {
    dashboard: Locator;
    tasks: Locator;
    gantt: Locator;
    members: Locator;
    budget: Locator;
  };
  readonly backButton: Locator;
  readonly editButton: Locator;
  readonly cloneButton: Locator;
  readonly autoScheduleButton: Locator;

  constructor(page: Page) {
    this.page = page;
    this.tabs = {
      dashboard: page.locator('button:has-text("ダッシュボード")'),
      tasks: page.locator('button:has-text("タスク")'),
      gantt: page.locator('button:has-text("ガントチャート")'),
      members: page.locator('button:has-text("メンバー")'),
      budget: page.locator('button:has-text("予算管理")'),
    };
    this.backButton = page.locator('button svg.h-5.w-5').first();
    this.editButton = page.locator('button[title="編集"]');
    this.cloneButton = page.locator('button[title="複製"]');
    this.autoScheduleButton = page.locator('button[title="自動スケジューリング"]');
  }

  async goto(projectId: number) {
    await this.page.goto(`/projects/${projectId}`);
  }

  async switchTab(tabName: keyof typeof this.tabs) {
    await this.tabs[tabName].click();
  }

  async goBack() {
    await this.backButton.click();
  }
}

export class TaskPage {
  readonly page: Page;
  readonly addTaskButton: Locator;
  readonly taskTree: Locator;

  constructor(page: Page) {
    this.page = page;
    this.addTaskButton = page.locator('button:has-text("タスクを追加")');
    this.taskTree = page.locator('div:has(h3:has-text("タスク一覧（WBS）"))');
  }

  async addTask() {
    await this.addTaskButton.click();
  }

  async editTask(taskName: string) {
    const taskRow = this.page.locator(`div:has(h4:has-text("${taskName}"))`);
    await taskRow.locator('button[title="編集"]').click();
  }

  async deleteTask(taskName: string) {
    const taskRow = this.page.locator(`div:has(h4:has-text("${taskName}"))`);
    await taskRow.locator('button[title="削除"]').click();
  }

  async addSubTask(parentTaskName: string) {
    const taskRow = this.page.locator(`div:has(h4:has-text("${parentTaskName}"))`);
    await taskRow.locator('button[title="サブタスクを追加"]').click();
  }

  async expandTask(taskName: string) {
    const taskRow = this.page.locator(`div:has(h4:has-text("${taskName}"))`);
    const expandButton = taskRow.locator('svg.h-4.w-4').first();
    await expandButton.click();
  }
}

export class TaskFormPage {
  readonly page: Page;
  readonly nameInput: Locator;
  readonly descriptionTextarea: Locator;
  readonly startDateInput: Locator;
  readonly endDateInput: Locator;
  readonly estimatedHoursInput: Locator;
  readonly actualHoursInput: Locator;
  readonly prioritySelect: Locator;
  readonly statusSelect: Locator;
  readonly progressInput: Locator;
  readonly submitButton: Locator;
  readonly cancelButton: Locator;

  constructor(page: Page) {
    this.page = page;
    this.nameInput = page.locator('input[id="name"]');
    this.descriptionTextarea = page.locator('textarea[id="description"]');
    this.startDateInput = page.locator('input[id="startDate"]');
    this.endDateInput = page.locator('input[id="endDate"]');
    this.estimatedHoursInput = page.locator('input[id="estimatedHours"]');
    this.actualHoursInput = page.locator('input[id="actualHours"]');
    this.prioritySelect = page.locator('select[id="priority"]');
    this.statusSelect = page.locator('select[id="status"]');
    this.progressInput = page.locator('input[id="progressPercentage"]');
    this.submitButton = page.locator('button[type="submit"]');
    this.cancelButton = page.locator('button:has-text("キャンセル")');
  }

  async fillForm(data: {
    name?: string;
    description?: string;
    startDate?: string;
    endDate?: string;
    estimatedHours?: string;
    actualHours?: string;
    priority?: string;
    status?: string;
    progressPercentage?: string;
  }) {
    if (data.name) await this.nameInput.fill(data.name);
    if (data.description) await this.descriptionTextarea.fill(data.description);
    if (data.startDate) await this.startDateInput.fill(data.startDate);
    if (data.endDate) await this.endDateInput.fill(data.endDate);
    if (data.estimatedHours) await this.estimatedHoursInput.fill(data.estimatedHours);
    if (data.actualHours) await this.actualHoursInput.fill(data.actualHours);
    if (data.priority) await this.prioritySelect.selectOption(data.priority);
    if (data.status) await this.statusSelect.selectOption(data.status);
    if (data.progressPercentage) await this.progressInput.fill(data.progressPercentage);
  }

  async submit() {
    await this.submitButton.click();
  }
}

export class MemberPage {
  readonly page: Page;
  readonly addMemberButton: Locator;
  readonly memberTable: Locator;

  constructor(page: Page) {
    this.page = page;
    this.addMemberButton = page.locator('button:has-text("メンバーを追加")');
    this.memberTable = page.locator('table');
  }

  async addMember(userId: string, role: string, allocation: string) {
    await this.addMemberButton.click();
    await this.page.fill('input[placeholder="ユーザーIDを入力"]', userId);
    await this.page.selectOption('select', role);
    await this.page.fill('input[type="number"][min="0"][max="100"]', allocation);
    await this.page.click('button:has-text("追加")');
  }

  async editMember(userName: string) {
    const memberRow = this.page.locator(`tr:has(td:has-text("${userName}"))`);
    await memberRow.locator('button svg.h-5.w-5').first().click();
  }

  async removeMember(userName: string) {
    const memberRow = this.page.locator(`tr:has(td:has-text("${userName}"))`);
    await memberRow.locator('button svg.h-5.w-5').last().click();
  }
}

export class BudgetPage {
  readonly page: Page;
  readonly editButton: Locator;
  readonly saveButton: Locator;
  readonly cancelButton: Locator;

  constructor(page: Page) {
    this.page = page;
    this.editButton = page.locator('button:has-text("編集")');
    this.saveButton = page.locator('button:has-text("保存")');
    this.cancelButton = page.locator('button:has-text("キャンセル")');
  }

  async editBudget() {
    await this.editButton.click();
  }

  async updateCost(category: 'labor' | 'outsourcing' | 'expense', type: 'planned' | 'actual', value: string) {
    // コスト入力フィールドを特定する（実装に応じて調整）
    const inputs = await this.page.locator('input[type="number"]').all();
    // カテゴリとタイプに基づいてインデックスを計算
    const categoryIndex = category === 'labor' ? 0 : category === 'outsourcing' ? 1 : 2;
    const typeOffset = type === 'planned' ? 0 : 1;
    const index = categoryIndex * 2 + typeOffset;
    
    if (inputs[index]) {
      await inputs[index].fill(value);
    }
  }

  async updateRevenue(value: string) {
    const revenueInput = this.page.locator('input[type="number"]').last();
    await revenueInput.fill(value);
  }

  async save() {
    await this.saveButton.click();
  }

  async cancel() {
    await this.cancelButton.click();
  }
}