import { test, expect } from '@playwright/test';

test.describe('API Integration Tests', () => {
  test('API health endpoint responds', async ({ request }) => {
    const response = await request.get('/api/v1/health');
    expect(response.status()).toBe(200);
    
    const data = await response.json();
    expect(data).toHaveProperty('status', 'healthy');
  });

  test('API authentication works', async ({ request }) => {
    // Login request
    const loginResponse = await request.post('/api/v1/auth/login', {
      data: {
        username: 'test@example.com',
        password: 'password123'
      }
    });
    
    expect(loginResponse.status()).toBe(200);
    
    const loginData = await loginResponse.json();
    expect(loginData).toHaveProperty('access_token');
    
    // Authenticated request
    const token = loginData.access_token;
    const userResponse = await request.get('/api/v1/users/me', {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });
    
    expect(userResponse.status()).toBe(200);
    
    const userData = await userResponse.json();
    expect(userData).toHaveProperty('email');
  });

  test('API rate limiting works', async ({ request }) => {
    const requests = [];
    
    // Make 150 rapid requests (above limit of 100)
    for (let i = 0; i < 150; i++) {
      requests.push(request.get('/api/v1/health'));
    }
    
    const responses = await Promise.all(requests);
    
    // Some requests should be rate limited (429)
    const rateLimited = responses.filter(r => r.status() === 429);
    expect(rateLimited.length).toBeGreaterThan(0);
  });

  test('API error handling', async ({ request }) => {
    // Invalid endpoint
    const response = await request.get('/api/v1/nonexistent');
    expect(response.status()).toBe(404);
    
    const data = await response.json();
    expect(data).toHaveProperty('detail');
  });

  test('API CORS headers', async ({ request }) => {
    const response = await request.options('/api/v1/health');
    
    const headers = response.headers();
    expect(headers['access-control-allow-origin']).toBeDefined();
    expect(headers['access-control-allow-methods']).toBeDefined();
  });
});