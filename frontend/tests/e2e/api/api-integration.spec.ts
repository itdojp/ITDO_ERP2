import { test, expect } from '@playwright/test';

test.describe('API Integration', () => {
  const API_BASE_URL = process.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';
  
  test.beforeEach(async ({ request }) => {
    // Verify API is accessible
    const response = await request.get(`${API_BASE_URL.replace('/api/v1', '')}/health`);
    expect(response.ok()).toBeTruthy();
  });

  test('should authenticate via API', async ({ request }) => {
    // Test login endpoint
    const loginResponse = await request.post(`${API_BASE_URL}/auth/login`, {
      data: {
        email: 'test@example.com',
        password: 'password123'
      }
    });
    
    expect(loginResponse.ok()).toBeTruthy();
    const loginData = await loginResponse.json();
    expect(loginData).toHaveProperty('access_token');
    expect(loginData).toHaveProperty('token_type', 'bearer');
    
    // Use token for authenticated request
    const userResponse = await request.get(`${API_BASE_URL}/users/me`, {
      headers: {
        'Authorization': `Bearer ${loginData.access_token}`
      }
    });
    
    expect(userResponse.ok()).toBeTruthy();
    const userData = await userResponse.json();
    expect(userData.email).toBe('test@example.com');
  });

  test('should handle CORS properly', async ({ request }) => {
    // Test OPTIONS request for CORS preflight
    const optionsResponse = await request.fetch(`${API_BASE_URL}/users`, {
      method: 'OPTIONS',
      headers: {
        'Origin': 'http://localhost:3000',
        'Access-Control-Request-Method': 'GET',
        'Access-Control-Request-Headers': 'authorization,content-type'
      }
    });
    
    expect(optionsResponse.ok()).toBeTruthy();
    
    const corsHeaders = optionsResponse.headers();
    expect(corsHeaders['access-control-allow-origin']).toBeTruthy();
    expect(corsHeaders['access-control-allow-methods']).toContain('GET');
  });

  test('should fetch user data', async ({ request }) => {
    // Login first
    const loginResponse = await request.post(`${API_BASE_URL}/auth/login`, {
      data: {
        email: 'admin@example.com',
        password: 'admin123'
      }
    });
    
    const { access_token } = await loginResponse.json();
    
    // Fetch users list
    const usersResponse = await request.get(`${API_BASE_URL}/users`, {
      headers: {
        'Authorization': `Bearer ${access_token}`
      }
    });
    
    expect(usersResponse.ok()).toBeTruthy();
    const usersData = await usersResponse.json();
    expect(Array.isArray(usersData.items)).toBeTruthy();
    expect(usersData.items.length).toBeGreaterThan(0);
    
    // Verify user structure
    const firstUser = usersData.items[0];
    expect(firstUser).toHaveProperty('id');
    expect(firstUser).toHaveProperty('email');
    expect(firstUser).toHaveProperty('full_name');
    expect(firstUser).not.toHaveProperty('hashed_password'); // Should not expose password
  });

  test('should create and manage tasks via API', async ({ request }) => {
    // Login first
    const loginResponse = await request.post(`${API_BASE_URL}/auth/login`, {
      data: {
        email: 'admin@example.com',
        password: 'admin123'
      }
    });
    
    const { access_token } = await loginResponse.json();
    const authHeaders = { 'Authorization': `Bearer ${access_token}` };
    
    // Create a task
    const createResponse = await request.post(`${API_BASE_URL}/tasks`, {
      headers: authHeaders,
      data: {
        title: 'API Test Task',
        description: 'Task created via API test',
        project_id: 1, // Assuming test project exists
        priority: 'HIGH',
        status: 'TODO'
      }
    });
    
    expect(createResponse.ok()).toBeTruthy();
    const createdTask = await createResponse.json();
    expect(createdTask.title).toBe('API Test Task');
    expect(createdTask.priority).toBe('HIGH');
    
    const taskId = createdTask.id;
    
    // Update the task
    const updateResponse = await request.put(`${API_BASE_URL}/tasks/${taskId}`, {
      headers: authHeaders,
      data: {
        title: 'API Test Task - Updated',
        status: 'IN_PROGRESS'
      }
    });
    
    expect(updateResponse.ok()).toBeTruthy();
    const updatedTask = await updateResponse.json();
    expect(updatedTask.title).toBe('API Test Task - Updated');
    expect(updatedTask.status).toBe('IN_PROGRESS');
    
    // Fetch the task
    const fetchResponse = await request.get(`${API_BASE_URL}/tasks/${taskId}`, {
      headers: authHeaders
    });
    
    expect(fetchResponse.ok()).toBeTruthy();
    const fetchedTask = await fetchResponse.json();
    expect(fetchedTask.id).toBe(taskId);
    
    // Delete the task
    const deleteResponse = await request.delete(`${API_BASE_URL}/tasks/${taskId}`, {
      headers: authHeaders
    });
    
    expect(deleteResponse.ok()).toBeTruthy();
    
    // Verify task is deleted
    const verifyDeleteResponse = await request.get(`${API_BASE_URL}/tasks/${taskId}`, {
      headers: authHeaders
    });
    
    expect(verifyDeleteResponse.status()).toBe(404);
  });

  test('should handle API errors gracefully', async ({ request }) => {
    // Test unauthorized access
    const unauthorizedResponse = await request.get(`${API_BASE_URL}/users`);
    expect(unauthorizedResponse.status()).toBe(401);
    
    // Login for further tests
    const loginResponse = await request.post(`${API_BASE_URL}/auth/login`, {
      data: {
        email: 'admin@example.com',
        password: 'admin123'
      }
    });
    
    const { access_token } = await loginResponse.json();
    const authHeaders = { 'Authorization': `Bearer ${access_token}` };
    
    // Test invalid resource
    const notFoundResponse = await request.get(`${API_BASE_URL}/tasks/99999`, {
      headers: authHeaders
    });
    expect(notFoundResponse.status()).toBe(404);
    
    // Test validation errors
    const validationResponse = await request.post(`${API_BASE_URL}/tasks`, {
      headers: authHeaders,
      data: {
        // Missing required title field
        description: 'Task without title'
      }
    });
    expect(validationResponse.status()).toBe(422);
    
    const validationData = await validationResponse.json();
    expect(validationData).toHaveProperty('detail');
  });

  test('should handle pagination correctly', async ({ request }) => {
    // Login first
    const loginResponse = await request.post(`${API_BASE_URL}/auth/login`, {
      data: {
        email: 'admin@example.com',
        password: 'admin123'
      }
    });
    
    const { access_token } = await loginResponse.json();
    const authHeaders = { 'Authorization': `Bearer ${access_token}` };
    
    // Test pagination on tasks endpoint
    const page1Response = await request.get(`${API_BASE_URL}/tasks?page=1&limit=2`, {
      headers: authHeaders
    });
    
    expect(page1Response.ok()).toBeTruthy();
    const page1Data = await page1Response.json();
    
    expect(page1Data).toHaveProperty('items');
    expect(page1Data).toHaveProperty('total');
    expect(page1Data).toHaveProperty('page', 1);
    expect(page1Data).toHaveProperty('limit', 2);
    expect(page1Data).toHaveProperty('has_next');
    expect(page1Data).toHaveProperty('has_prev', false);
    
    if (page1Data.total > 2) {
      expect(page1Data.has_next).toBe(true);
      expect(page1Data.items.length).toBe(2);
      
      // Test second page
      const page2Response = await request.get(`${API_BASE_URL}/tasks?page=2&limit=2`, {
        headers: authHeaders
      });
      
      const page2Data = await page2Response.json();
      expect(page2Data.page).toBe(2);
      expect(page2Data.has_prev).toBe(true);
    }
  });

  test('should handle concurrent API requests', async ({ request }) => {
    // Login first
    const loginResponse = await request.post(`${API_BASE_URL}/auth/login`, {
      data: {
        email: 'admin@example.com',
        password: 'admin123'
      }
    });
    
    const { access_token } = await loginResponse.json();
    const authHeaders = { 'Authorization': `Bearer ${access_token}` };
    
    // Make multiple concurrent requests
    const promises = [
      request.get(`${API_BASE_URL}/users`, { headers: authHeaders }),
      request.get(`${API_BASE_URL}/tasks`, { headers: authHeaders }),
      request.get(`${API_BASE_URL}/organizations`, { headers: authHeaders }),
      request.get(`${API_BASE_URL}/departments`, { headers: authHeaders }),
    ];
    
    const responses = await Promise.all(promises);
    
    // All requests should succeed
    responses.forEach(response => {
      expect(response.ok()).toBeTruthy();
    });
    
    // Verify response times are reasonable
    const responseTimes = responses.map(r => {
      const timing = r.request().timing();
      return timing.responseEnd - timing.requestStart;
    });
    
    responseTimes.forEach(time => {
      expect(time).toBeLessThan(5000); // Less than 5 seconds
    });
  });

  test('should validate API schema compliance', async ({ request }) => {
    // Login first
    const loginResponse = await request.post(`${API_BASE_URL}/auth/login`, {
      data: {
        email: 'admin@example.com',
        password: 'admin123'
      }
    });
    
    const { access_token } = await loginResponse.json();
    const authHeaders = { 'Authorization': `Bearer ${access_token}` };
    
    // Test API schema for tasks endpoint
    const tasksResponse = await request.get(`${API_BASE_URL}/tasks`, {
      headers: authHeaders
    });
    
    const tasksData = await tasksResponse.json();
    
    // Validate response structure
    expect(tasksData).toHaveProperty('items');
    expect(Array.isArray(tasksData.items)).toBeTruthy();
    
    if (tasksData.items.length > 0) {
      const task = tasksData.items[0];
      
      // Validate task schema
      expect(task).toHaveProperty('id');
      expect(task).toHaveProperty('title');
      expect(task).toHaveProperty('status');
      expect(task).toHaveProperty('priority');
      expect(task).toHaveProperty('project_id');
      expect(task).toHaveProperty('created_at');
      expect(task).toHaveProperty('updated_at');
      
      // Validate data types
      expect(typeof task.id).toBe('number');
      expect(typeof task.title).toBe('string');
      expect(['TODO', 'IN_PROGRESS', 'IN_REVIEW', 'COMPLETED', 'CANCELLED', 'BLOCKED']).toContain(task.status);
      expect(['LOW', 'MEDIUM', 'HIGH', 'URGENT']).toContain(task.priority);
    }
  });
});