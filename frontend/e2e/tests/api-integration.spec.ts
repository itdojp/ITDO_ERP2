import { test, expect } from '@playwright/test';

test.describe('API Integration Testing', () => {
  let apiContext: any;

  test.beforeAll(async ({ playwright }) => {
    // Create API request context
    apiContext = await playwright.request.newContext({
      baseURL: 'http://localhost:8000/api/v1',
      extraHTTPHeaders: {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
      },
    });
  });

  test.afterAll(async () => {
    await apiContext.dispose();
  });

  test('API健全性チェック - ヘルスエンドポイント', async () => {
    const response = await apiContext.get('/health');
    
    expect(response.ok()).toBeTruthy();
    expect(response.status()).toBe(200);
    
    const data = await response.json();
    expect(data).toHaveProperty('status');
    expect(data.status).toBe('healthy');
  });

  test('認証API - ログインエンドポイント', async () => {
    const loginData = {
      email: 'admin@e2e.test',
      password: 'AdminPass123!'
    };

    const response = await apiContext.post('/auth/login', {
      data: loginData
    });

    expect(response.ok()).toBeTruthy();
    expect(response.status()).toBe(200);

    const data = await response.json();
    expect(data).toHaveProperty('access_token');
    expect(data).toHaveProperty('token_type', 'bearer');
    expect(data).toHaveProperty('user');
  });

  test('認証API - 無効な認証情報でのログイン失敗', async () => {
    const invalidLoginData = {
      email: 'invalid@example.com',
      password: 'wrongpassword'
    };

    const response = await apiContext.post('/auth/login', {
      data: invalidLoginData
    });

    expect(response.status()).toBe(401);
    
    const data = await response.json();
    expect(data).toHaveProperty('detail');
  });

  test('ユーザーAPI - ユーザー一覧取得', async () => {
    // First login to get token
    const loginResponse = await apiContext.post('/auth/login', {
      data: {
        email: 'admin@e2e.test',
        password: 'AdminPass123!'
      }
    });

    const { access_token } = await loginResponse.json();

    // Get users with authentication
    const response = await apiContext.get('/admin/users', {
      headers: {
        'Authorization': `Bearer ${access_token}`
      }
    });

    expect(response.ok()).toBeTruthy();
    expect(response.status()).toBe(200);

    const data = await response.json();
    expect(data).toHaveProperty('items');
    expect(Array.isArray(data.items)).toBeTruthy();
    expect(data).toHaveProperty('total');
    expect(data).toHaveProperty('page');
    expect(data).toHaveProperty('size');
  });

  test('ユーザーAPI - ユーザー作成', async () => {
    // Login first
    const loginResponse = await apiContext.post('/auth/login', {
      data: {
        email: 'admin@e2e.test',
        password: 'AdminPass123!'
      }
    });

    const { access_token } = await loginResponse.json();

    // Create new user
    const timestamp = Date.now();
    const userData = {
      email: `apitest${timestamp}@e2e.test`,
      full_name: `API Test User ${timestamp}`,
      phone: '+81-90-1111-2222',
      organization_id: 1,
      is_active: true
    };

    const response = await apiContext.post('/admin/users', {
      data: userData,
      headers: {
        'Authorization': `Bearer ${access_token}`
      }
    });

    expect(response.ok()).toBeTruthy();
    expect(response.status()).toBe(201);

    const data = await response.json();
    expect(data).toHaveProperty('id');
    expect(data).toHaveProperty('email', userData.email);
    expect(data).toHaveProperty('full_name', userData.full_name);
  });

  test('組織API - 組織一覧取得', async () => {
    // Login first
    const loginResponse = await apiContext.post('/auth/login', {
      data: {
        email: 'admin@e2e.test',
        password: 'AdminPass123!'
      }
    });

    const { access_token } = await loginResponse.json();

    // Get organizations
    const response = await apiContext.get('/admin/organizations', {
      headers: {
        'Authorization': `Bearer ${access_token}`
      }
    });

    expect(response.ok()).toBeTruthy();
    expect(response.status()).toBe(200);

    const data = await response.json();
    expect(data).toHaveProperty('items');
    expect(Array.isArray(data.items)).toBeTruthy();
  });

  test('タスクAPI - タスク一覧取得', async () => {
    // Login first
    const loginResponse = await apiContext.post('/auth/login', {
      data: {
        email: 'user@e2e.test',
        password: 'UserPass123!'
      }
    });

    const { access_token } = await loginResponse.json();

    // Get tasks
    const response = await apiContext.get('/tasks', {
      headers: {
        'Authorization': `Bearer ${access_token}`
      }
    });

    expect(response.ok()).toBeTruthy();
    expect(response.status()).toBe(200);

    const data = await response.json();
    expect(data).toHaveProperty('items');
    expect(Array.isArray(data.items)).toBeTruthy();
  });

  test('認証なしでの保護されたエンドポイントアクセス失敗', async () => {
    const response = await apiContext.get('/admin/users');
    
    expect(response.status()).toBe(401);
  });

  test('無効なトークンでのAPIアクセス失敗', async () => {
    const response = await apiContext.get('/admin/users', {
      headers: {
        'Authorization': 'Bearer invalid-token'
      }
    });
    
    expect(response.status()).toBe(401);
  });

  test('APIレスポンス時間が適切である', async () => {
    const startTime = Date.now();
    
    const response = await apiContext.get('/health');
    
    const responseTime = Date.now() - startTime;
    
    expect(response.ok()).toBeTruthy();
    expect(responseTime).toBeLessThan(1000); // Should respond within 1 second
  });

  test('APIエラーハンドリング - 存在しないリソース', async () => {
    // Login first
    const loginResponse = await apiContext.post('/auth/login', {
      data: {
        email: 'admin@e2e.test',
        password: 'AdminPass123!'
      }
    });

    const { access_token } = await loginResponse.json();

    // Try to get non-existent user
    const response = await apiContext.get('/admin/users/99999', {
      headers: {
        'Authorization': `Bearer ${access_token}`
      }
    });

    expect(response.status()).toBe(404);
    
    const data = await response.json();
    expect(data).toHaveProperty('detail');
  });

  test('APIページネーション機能', async () => {
    // Login first
    const loginResponse = await apiContext.post('/auth/login', {
      data: {
        email: 'admin@e2e.test',
        password: 'AdminPass123!'
      }
    });

    const { access_token } = await loginResponse.json();

    // Test pagination
    const response = await apiContext.get('/admin/users?page=1&size=5', {
      headers: {
        'Authorization': `Bearer ${access_token}`
      }
    });

    expect(response.ok()).toBeTruthy();
    
    const data = await response.json();
    expect(data).toHaveProperty('items');
    expect(data).toHaveProperty('page', 1);
    expect(data).toHaveProperty('size', 5);
    expect(data.items.length).toBeLessThanOrEqual(5);
  });

  test('APIフィルタリング機能', async () => {
    // Login first
    const loginResponse = await apiContext.post('/auth/login', {
      data: {
        email: 'admin@e2e.test',
        password: 'AdminPass123!'
      }
    });

    const { access_token } = await loginResponse.json();

    // Test filtering
    const response = await apiContext.get('/admin/users?search=admin', {
      headers: {
        'Authorization': `Bearer ${access_token}`
      }
    });

    expect(response.ok()).toBeTruthy();
    
    const data = await response.json();
    expect(data).toHaveProperty('items');
    
    // All returned items should match the search criteria
    data.items.forEach((user: any) => {
      const userText = (user.email + ' ' + user.full_name).toLowerCase();
      expect(userText).toContain('admin');
    });
  });

  test('同時リクエスト処理能力', async () => {
    // Create multiple concurrent requests
    const requests = Array.from({ length: 10 }, () => 
      apiContext.get('/health')
    );

    const responses = await Promise.all(requests);

    // All requests should succeed
    responses.forEach(response => {
      expect(response.ok()).toBeTruthy();
      expect(response.status()).toBe(200);
    });
  });
});