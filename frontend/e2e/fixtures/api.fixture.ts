import { APIRequestContext, request } from '@playwright/test';

/**
 * API Client Fixture for E2E Tests
 * Sprint 2 Day 1 - E2E Test Infrastructure
 * 
 * Provides API client wrapper with request/response logging,
 * error handling, and test data generators
 */

export interface ApiRequestOptions {
  headers?: Record<string, string>;
  timeout?: number;
  retries?: number;
}

export interface ApiResponse<T = any> {
  data: T;
  status: number;
  headers: Record<string, string>;
  duration: number;
}

export class ApiClient {
  private baseUrl: string;
  private context?: APIRequestContext;
  private defaultHeaders: Record<string, string>;
  private requestLog: Array<{
    method: string;
    url: string;
    status: number;
    duration: number;
    timestamp: Date;
  }> = [];

  constructor(baseUrl?: string) {
    this.baseUrl = baseUrl || process.env.API_BASE_URL || 'http://localhost:8000/api/v1';
    this.defaultHeaders = {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
    };
  }

  /**
   * Initialize API context
   */
  async init(): Promise<void> {
    this.context = await request.newContext({
      baseURL: this.baseUrl,
      extraHTTPHeaders: this.defaultHeaders,
    });
  }

  /**
   * Close API context
   */
  async close(): Promise<void> {
    if (this.context) {
      await this.context.dispose();
    }
  }

  /**
   * Generic request method with logging and error handling
   */
  private async makeRequest<T>(
    method: string,
    endpoint: string,
    data?: any,
    options?: ApiRequestOptions
  ): Promise<T> {
    if (!this.context) {
      await this.init();
    }

    const url = endpoint.startsWith('http') ? endpoint : `${this.baseUrl}${endpoint}`;
    const startTime = Date.now();
    
    console.log(`🔍 ${method} ${url}`);
    if (data) {
      console.log('📦 Request data:', JSON.stringify(data, null, 2));
    }

    try {
      const response = await this.context![method.toLowerCase()](endpoint, {
        data,
        headers: { ...this.defaultHeaders, ...options?.headers },
        timeout: options?.timeout || 30000,
      });

      const duration = Date.now() - startTime;
      const responseData = await response.json().catch(() => null);

      // Log request
      this.requestLog.push({
        method,
        url,
        status: response.status(),
        duration,
        timestamp: new Date(),
      });

      console.log(`✅ ${method} ${url} - ${response.status()} (${duration}ms)`);
      if (responseData) {
        console.log('📥 Response:', JSON.stringify(responseData, null, 2));
      }

      if (!response.ok()) {
        throw new Error(
          `API Error: ${response.status()} ${response.statusText()} - ${JSON.stringify(responseData)}`
        );
      }

      return responseData;
    } catch (error) {
      console.error(`❌ ${method} ${url} failed:`, error);
      throw error;
    }
  }

  /**
   * GET request
   */
  async get<T = any>(endpoint: string, options?: ApiRequestOptions): Promise<T> {
    return this.makeRequest<T>('GET', endpoint, undefined, options);
  }

  /**
   * POST request
   */
  async post<T = any>(endpoint: string, data?: any, options?: ApiRequestOptions): Promise<T> {
    return this.makeRequest<T>('POST', endpoint, data, options);
  }

  /**
   * PUT request
   */
  async put<T = any>(endpoint: string, data?: any, options?: ApiRequestOptions): Promise<T> {
    return this.makeRequest<T>('PUT', endpoint, data, options);
  }

  /**
   * PATCH request
   */
  async patch<T = any>(endpoint: string, data?: any, options?: ApiRequestOptions): Promise<T> {
    return this.makeRequest<T>('PATCH', endpoint, data, options);
  }

  /**
   * DELETE request
   */
  async delete<T = any>(endpoint: string, options?: ApiRequestOptions): Promise<T> {
    return this.makeRequest<T>('DELETE', endpoint, undefined, options);
  }

  /**
   * Set authorization header
   */
  setAuthToken(token: string): void {
    this.defaultHeaders['Authorization'] = `Bearer ${token}`;
  }

  /**
   * Clear authorization header
   */
  clearAuthToken(): void {
    delete this.defaultHeaders['Authorization'];
  }

  /**
   * Get request log
   */
  getRequestLog(): typeof this.requestLog {
    return this.requestLog;
  }

  /**
   * Clear request log
   */
  clearRequestLog(): void {
    this.requestLog = [];
  }

  /**
   * Health check
   */
  async healthCheck(): Promise<boolean> {
    try {
      await this.get('/health');
      return true;
    } catch {
      return false;
    }
  }

  /**
   * Wait for API to be ready
   */
  async waitForApi(timeout: number = 60000): Promise<void> {
    const startTime = Date.now();
    
    while (Date.now() - startTime < timeout) {
      if (await this.healthCheck()) {
        console.log('✅ API is ready');
        return;
      }
      await new Promise(resolve => setTimeout(resolve, 1000));
    }
    
    throw new Error(`API not ready within ${timeout}ms`);
  }
}

/**
 * Test Data Generators
 */
export class TestDataGenerator {
  private static counter = 0;

  /**
   * Generate unique email
   */
  static generateEmail(prefix: string = 'test'): string {
    this.counter++;
    return `${prefix}.${Date.now()}.${this.counter}@e2e.test`;
  }

  /**
   * Generate organization data
   */
  static generateOrganization(overrides?: Partial<any>): any {
    this.counter++;
    return {
      name: `Test Organization ${this.counter}`,
      code: `TEST-ORG-${this.counter}`,
      description: `E2E test organization ${this.counter}`,
      industry: 'Technology',
      website: `https://testorg${this.counter}.example.com`,
      ...overrides,
    };
  }

  /**
   * Generate department data
   */
  static generateDepartment(organizationId: number, overrides?: Partial<any>): any {
    this.counter++;
    return {
      name: `Test Department ${this.counter}`,
      code: `TEST-DEPT-${this.counter}`,
      description: `E2E test department ${this.counter}`,
      organization_id: organizationId,
      ...overrides,
    };
  }

  /**
   * Generate user data
   */
  static generateUser(organizationId: number, overrides?: Partial<any>): any {
    this.counter++;
    return {
      email: this.generateEmail('user'),
      password: 'E2ETest@User123!',
      full_name: `Test User ${this.counter}`,
      phone: `+81-90-${String(Math.floor(Math.random() * 100000000)).padStart(8, '0')}`,
      organization_id: organizationId,
      role_ids: [],
      is_active: true,
      ...overrides,
    };
  }

  /**
   * Generate task data
   */
  static generateTask(projectId: number, overrides?: Partial<any>): any {
    this.counter++;
    return {
      title: `Test Task ${this.counter}`,
      description: `E2E test task description ${this.counter}`,
      project_id: projectId,
      priority: 'medium',
      status: 'todo',
      estimated_hours: Math.floor(Math.random() * 40) + 1,
      ...overrides,
    };
  }

  /**
   * Generate project data
   */
  static generateProject(organizationId: number, overrides?: Partial<any>): any {
    this.counter++;
    return {
      name: `Test Project ${this.counter}`,
      code: `TEST-PROJ-${this.counter}`,
      description: `E2E test project ${this.counter}`,
      organization_id: organizationId,
      status: 'active',
      start_date: new Date().toISOString().split('T')[0],
      end_date: new Date(Date.now() + 90 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
      budget: Math.floor(Math.random() * 1000000) + 100000,
      ...overrides,
    };
  }

  /**
   * Reset counter
   */
  static reset(): void {
    this.counter = 0;
  }
}