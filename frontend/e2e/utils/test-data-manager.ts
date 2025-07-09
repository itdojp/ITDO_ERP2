import { APIRequestContext } from '@playwright/test';

/**
 * Test Data Manager
 * Sprint 3 Day 2 - Advanced E2E Testing
 * 
 * Utilities for managing test data lifecycle, cleanup, and isolation
 */

export interface TestDataConfig {
  autoCleanup: boolean;
  isolationLevel: 'test' | 'suite' | 'global';
  seedData: boolean;
}

export interface TestEntity {
  id: string;
  type: 'user' | 'organization' | 'department' | 'task' | 'project' | 'role';
  data: any;
  createdAt: Date;
  dependencies: string[];
}

export class TestDataManager {
  private entities: Map<string, TestEntity> = new Map();
  private apiContext: APIRequestContext;
  private config: TestDataConfig;
  private authToken: string | null = null;

  constructor(apiContext: APIRequestContext, config: TestDataConfig = {
    autoCleanup: true,
    isolationLevel: 'test',
    seedData: true
  }) {
    this.apiContext = apiContext;
    this.config = config;
  }

  /**
   * Authenticate with admin credentials
   */
  async authenticate(email: string = 'admin@e2e.test', password: string = 'AdminPass123!'): Promise<void> {
    const response = await this.apiContext.post('/auth/login', {
      data: { email, password }
    });

    if (response.ok()) {
      const data = await response.json();
      this.authToken = data.access_token;
    } else {
      throw new Error('Authentication failed');
    }
  }

  /**
   * Get authorization headers
   */
  private getAuthHeaders(): Record<string, string> {
    return this.authToken ? { Authorization: `Bearer ${this.authToken}` } : {};
  }

  /**
   * Create test organization
   */
  async createOrganization(data: Partial<any> = {}): Promise<TestEntity> {
    const timestamp = Date.now();
    const organizationData = {
      name: `Test Organization ${timestamp}`,
      code: `TEST-ORG-${timestamp}`,
      description: `E2E test organization ${timestamp}`,
      industry: 'Technology',
      website: `https://testorg${timestamp}.example.com`,
      ...data
    };

    const response = await this.apiContext.post('/admin/organizations', {
      data: organizationData,
      headers: this.getAuthHeaders()
    });

    if (!response.ok()) {
      throw new Error(`Failed to create organization: ${response.status()}`);
    }

    const createdOrg = await response.json();
    const entity: TestEntity = {
      id: `org-${createdOrg.id}`,
      type: 'organization',
      data: createdOrg,
      createdAt: new Date(),
      dependencies: []
    };

    this.entities.set(entity.id, entity);
    return entity;
  }

  /**
   * Create test department
   */
  async createDepartment(organizationId: number, data: Partial<any> = {}): Promise<TestEntity> {
    const timestamp = Date.now();
    const departmentData = {
      name: `Test Department ${timestamp}`,
      code: `TEST-DEPT-${timestamp}`,
      description: `E2E test department ${timestamp}`,
      organization_id: organizationId,
      ...data
    };

    const response = await this.apiContext.post('/admin/departments', {
      data: departmentData,
      headers: this.getAuthHeaders()
    });

    if (!response.ok()) {
      throw new Error(`Failed to create department: ${response.status()}`);
    }

    const createdDept = await response.json();
    const entity: TestEntity = {
      id: `dept-${createdDept.id}`,
      type: 'department',
      data: createdDept,
      createdAt: new Date(),
      dependencies: [`org-${organizationId}`]
    };

    this.entities.set(entity.id, entity);
    return entity;
  }

  /**
   * Create test user
   */
  async createUser(organizationId: number, data: Partial<any> = {}): Promise<TestEntity> {
    const timestamp = Date.now();
    const userData = {
      email: `testuser${timestamp}@e2e.test`,
      full_name: `Test User ${timestamp}`,
      phone: `+81-90-${String(Math.floor(Math.random() * 100000000)).padStart(8, '0')}`,
      organization_id: organizationId,
      is_active: true,
      role_ids: [],
      ...data
    };

    const response = await this.apiContext.post('/admin/users', {
      data: userData,
      headers: this.getAuthHeaders()
    });

    if (!response.ok()) {
      throw new Error(`Failed to create user: ${response.status()}`);
    }

    const createdUser = await response.json();
    const entity: TestEntity = {
      id: `user-${createdUser.id}`,
      type: 'user',
      data: createdUser,
      createdAt: new Date(),
      dependencies: [`org-${organizationId}`]
    };

    this.entities.set(entity.id, entity);
    return entity;
  }

  /**
   * Create test task
   */
  async createTask(projectId: number, data: Partial<any> = {}): Promise<TestEntity> {
    const timestamp = Date.now();
    const taskData = {
      title: `Test Task ${timestamp}`,
      description: `E2E test task ${timestamp}`,
      project_id: projectId,
      priority: 'medium',
      status: 'todo',
      estimated_hours: Math.floor(Math.random() * 40) + 1,
      ...data
    };

    const response = await this.apiContext.post('/tasks', {
      data: taskData,
      headers: this.getAuthHeaders()
    });

    if (!response.ok()) {
      throw new Error(`Failed to create task: ${response.status()}`);
    }

    const createdTask = await response.json();
    const entity: TestEntity = {
      id: `task-${createdTask.id}`,
      type: 'task',
      data: createdTask,
      createdAt: new Date(),
      dependencies: [`project-${projectId}`]
    };

    this.entities.set(entity.id, entity);
    return entity;
  }

  /**
   * Create test project
   */
  async createProject(organizationId: number, data: Partial<any> = {}): Promise<TestEntity> {
    const timestamp = Date.now();
    const projectData = {
      name: `Test Project ${timestamp}`,
      code: `TEST-PROJ-${timestamp}`,
      description: `E2E test project ${timestamp}`,
      organization_id: organizationId,
      status: 'active',
      start_date: new Date().toISOString().split('T')[0],
      end_date: new Date(Date.now() + 90 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
      budget: Math.floor(Math.random() * 1000000) + 100000,
      ...data
    };

    const response = await this.apiContext.post('/projects', {
      data: projectData,
      headers: this.getAuthHeaders()
    });

    if (!response.ok()) {
      throw new Error(`Failed to create project: ${response.status()}`);
    }

    const createdProject = await response.json();
    const entity: TestEntity = {
      id: `project-${createdProject.id}`,
      type: 'project',
      data: createdProject,
      createdAt: new Date(),
      dependencies: [`org-${organizationId}`]
    };

    this.entities.set(entity.id, entity);
    return entity;
  }

  /**
   * Create complete test scenario
   */
  async createTestScenario(name: string = 'default'): Promise<{
    organization: TestEntity;
    department: TestEntity;
    users: TestEntity[];
    project: TestEntity;
    tasks: TestEntity[];
  }> {
    console.log(`Creating test scenario: ${name}`);

    // Create organization
    const organization = await this.createOrganization({
      name: `Test Org for ${name}`
    });

    // Create department
    const department = await this.createDepartment(organization.data.id, {
      name: `Test Dept for ${name}`
    });

    // Create users
    const users = await Promise.all([
      this.createUser(organization.data.id, {
        full_name: `Admin User for ${name}`,
        email: `admin-${name}@e2e.test`
      }),
      this.createUser(organization.data.id, {
        full_name: `Manager User for ${name}`,
        email: `manager-${name}@e2e.test`
      }),
      this.createUser(organization.data.id, {
        full_name: `Regular User for ${name}`,
        email: `user-${name}@e2e.test`
      })
    ]);

    // Create project
    const project = await this.createProject(organization.data.id, {
      name: `Test Project for ${name}`
    });

    // Create tasks
    const tasks = await Promise.all([
      this.createTask(project.data.id, {
        title: `High Priority Task for ${name}`,
        priority: 'high'
      }),
      this.createTask(project.data.id, {
        title: `Medium Priority Task for ${name}`,
        priority: 'medium'
      }),
      this.createTask(project.data.id, {
        title: `Low Priority Task for ${name}`,
        priority: 'low'
      })
    ]);

    return {
      organization,
      department,
      users,
      project,
      tasks
    };
  }

  /**
   * Get entity by ID
   */
  getEntity(id: string): TestEntity | undefined {
    return this.entities.get(id);
  }

  /**
   * Get entities by type
   */
  getEntitiesByType(type: TestEntity['type']): TestEntity[] {
    return Array.from(this.entities.values()).filter(entity => entity.type === type);
  }

  /**
   * Delete entity and its dependencies
   */
  async deleteEntity(id: string): Promise<void> {
    const entity = this.entities.get(id);
    if (!entity) return;

    // Delete dependent entities first
    const dependents = Array.from(this.entities.values())
      .filter(e => e.dependencies.includes(id))
      .sort((a, b) => b.createdAt.getTime() - a.createdAt.getTime());

    for (const dependent of dependents) {
      await this.deleteEntity(dependent.id);
    }

    // Delete the entity
    await this.deleteEntityFromAPI(entity);
    this.entities.delete(id);
  }

  /**
   * Delete entity from API
   */
  private async deleteEntityFromAPI(entity: TestEntity): Promise<void> {
    const endpoints = {
      user: `/admin/users/${entity.data.id}`,
      organization: `/admin/organizations/${entity.data.id}`,
      department: `/admin/departments/${entity.data.id}`,
      task: `/tasks/${entity.data.id}`,
      project: `/projects/${entity.data.id}`,
      role: `/admin/roles/${entity.data.id}`
    };

    const endpoint = endpoints[entity.type];
    if (!endpoint) return;

    try {
      await this.apiContext.delete(endpoint, {
        headers: this.getAuthHeaders()
      });
    } catch (error) {
      console.warn(`Failed to delete ${entity.type} ${entity.id}:`, error);
    }
  }

  /**
   * Clean up all test data
   */
  async cleanup(): Promise<void> {
    console.log(`Cleaning up ${this.entities.size} test entities`);

    // Sort by creation time (newest first) to handle dependencies
    const sortedEntities = Array.from(this.entities.values())
      .sort((a, b) => b.createdAt.getTime() - a.createdAt.getTime());

    for (const entity of sortedEntities) {
      await this.deleteEntityFromAPI(entity);
    }

    this.entities.clear();
  }

  /**
   * Get cleanup summary
   */
  getCleanupSummary(): Record<string, number> {
    const summary: Record<string, number> = {};
    
    for (const entity of this.entities.values()) {
      summary[entity.type] = (summary[entity.type] || 0) + 1;
    }

    return summary;
  }

  /**
   * Seed standard test data
   */
  async seedStandardData(): Promise<void> {
    if (!this.config.seedData) return;

    console.log('Seeding standard test data...');

    // Create standard organizations
    const orgs = await Promise.all([
      this.createOrganization({
        name: 'Standard Test Organization',
        code: 'STD-ORG-001'
      }),
      this.createOrganization({
        name: 'Secondary Test Organization',
        code: 'STD-ORG-002'
      })
    ]);

    // Create standard departments
    await Promise.all([
      this.createDepartment(orgs[0].data.id, {
        name: 'Engineering',
        code: 'ENG'
      }),
      this.createDepartment(orgs[0].data.id, {
        name: 'Sales',
        code: 'SALES'
      }),
      this.createDepartment(orgs[1].data.id, {
        name: 'Marketing',
        code: 'MKT'
      })
    ]);

    // Create standard users
    await Promise.all([
      this.createUser(orgs[0].data.id, {
        email: 'standard.admin@e2e.test',
        full_name: 'Standard Admin User'
      }),
      this.createUser(orgs[0].data.id, {
        email: 'standard.user@e2e.test',
        full_name: 'Standard Regular User'
      }),
      this.createUser(orgs[1].data.id, {
        email: 'secondary.user@e2e.test',
        full_name: 'Secondary Organization User'
      })
    ]);

    console.log('Standard test data seeded successfully');
  }

  /**
   * Wait for entity to be ready
   */
  async waitForEntity(id: string, timeout: number = 5000): Promise<TestEntity> {
    const startTime = Date.now();
    
    while (Date.now() - startTime < timeout) {
      const entity = this.entities.get(id);
      if (entity) return entity;
      
      await new Promise(resolve => setTimeout(resolve, 100));
    }
    
    throw new Error(`Entity ${id} not found within timeout`);
  }

  /**
   * Export test data for debugging
   */
  exportTestData(): string {
    const data = Array.from(this.entities.values()).map(entity => ({
      id: entity.id,
      type: entity.type,
      data: entity.data,
      createdAt: entity.createdAt.toISOString(),
      dependencies: entity.dependencies
    }));

    return JSON.stringify(data, null, 2);
  }
}