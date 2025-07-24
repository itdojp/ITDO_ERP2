// k6 Load Testing Script for ITDO ERP System
// This script provides comprehensive performance testing scenarios

import http from 'k6/http';
import { check, group, sleep } from 'k6';
import { Rate, Trend, Counter } from 'k6/metrics';

// Custom metrics
const errorRate = new Rate('error_rate');
const responseTime = new Trend('response_time');
const requestCount = new Counter('request_count');

// Test configuration
export const options = {
  stages: [
    { duration: '2m', target: 10 },   // Ramp up to 10 users
    { duration: '5m', target: 10 },   // Stay at 10 users
    { duration: '2m', target: 20 },   // Ramp up to 20 users
    { duration: '5m', target: 20 },   // Stay at 20 users
    { duration: '2m', target: 0 },    // Ramp down
  ],
  thresholds: {
    http_req_duration: ['p(95)<2000'],      // 95% of requests under 2s
    http_req_failed: ['rate<0.05'],         // Error rate under 5%
    response_time: ['p(95)<1500'],          // Custom metric threshold
    error_rate: ['rate<0.1'],              // Custom error rate threshold
  },
};

// Environment configuration
const BASE_URL = __ENV.BASE_URL || 'http://localhost:8000';
const API_BASE = `${BASE_URL}/api/v1`;

// Test data
const testUsers = [
  { email: 'test1@example.com', password: 'testpass123' },
  { email: 'test2@example.com', password: 'testpass123' },
  { email: 'test3@example.com', password: 'testpass123' },
];

const testOrganizations = [
  { name: 'Test Org 1', description: 'Performance test organization 1' },
  { name: 'Test Org 2', description: 'Performance test organization 2' },
];

// Authentication helper
function authenticate(userIndex = 0) {
  const user = testUsers[userIndex % testUsers.length];
  
  const loginResponse = http.post(`${API_BASE}/auth/login`, {
    email: user.email,
    password: user.password,
  }, {
    headers: { 'Content-Type': 'application/json' },
  });
  
  if (loginResponse.status === 200) {
    const token = loginResponse.json('access_token');
    return {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    };
  }
  
  return null;
}

// Main test scenario
export default function () {
  const userIndex = Math.floor(Math.random() * testUsers.length);
  
  group('Authentication Flow', () => {
    // Health check
    group('Health Check', () => {
      const healthResponse = http.get(`${BASE_URL}/health`);
      
      check(healthResponse, {
        'health check status is 200': (r) => r.status === 200,
        'health check response time < 500ms': (r) => r.timings.duration < 500,
      });
      
      errorRate.add(healthResponse.status !== 200);
      responseTime.add(healthResponse.timings.duration);
      requestCount.add(1);
    });
    
    // User authentication
    const headers = authenticate(userIndex);
    if (!headers) {
      console.error('Authentication failed');
      return;
    }
    
    sleep(1);
    
    // API endpoints testing
    group('User Management', () => {
      // Get user profile
      const profileResponse = http.get(`${API_BASE}/users/me`, { headers });
      
      check(profileResponse, {
        'get profile status is 200': (r) => r.status === 200,
        'profile has user data': (r) => r.json('email') !== undefined,
      });
      
      errorRate.add(profileResponse.status !== 200);
      responseTime.add(profileResponse.timings.duration);
      requestCount.add(1);
    });
    
    sleep(1);
    
    group('Organization Management', () => {
      // List organizations
      const orgsResponse = http.get(`${API_BASE}/organizations`, { headers });
      
      check(orgsResponse, {
        'list organizations status is 200': (r) => r.status === 200,
        'organizations list is array': (r) => Array.isArray(r.json()),
      });
      
      errorRate.add(orgsResponse.status !== 200);
      responseTime.add(orgsResponse.timings.duration);
      requestCount.add(1);
      
      // Create organization (if needed)
      if (Math.random() < 0.3) { // 30% chance to create org
        const orgData = testOrganizations[Math.floor(Math.random() * testOrganizations.length)];
        orgData.name = `${orgData.name} ${Date.now()}`;
        
        const createOrgResponse = http.post(
          `${API_BASE}/organizations`,
          JSON.stringify(orgData),
          { headers }
        );
        
        check(createOrgResponse, {
          'create organization status is 201': (r) => r.status === 201,
          'created org has id': (r) => r.json('id') !== undefined,
        });
        
        errorRate.add(createOrgResponse.status !== 201);
        responseTime.add(createOrgResponse.timings.duration);
        requestCount.add(1);
      }
    });
    
    sleep(1);
    
    group('Department Management', () => {
      // List departments
      const deptResponse = http.get(`${API_BASE}/departments`, { headers });
      
      check(deptResponse, {
        'list departments status is 200': (r) => r.status === 200,
        'departments response is valid': (r) => r.json() !== undefined,
      });
      
      errorRate.add(deptResponse.status !== 200);
      responseTime.add(deptResponse.timings.duration);
      requestCount.add(1);
    });
    
    sleep(1);
    
    group('Task Management', () => {
      // List tasks
      const tasksResponse = http.get(`${API_BASE}/tasks`, { headers });
      
      check(tasksResponse, {
        'list tasks status is 200': (r) => r.status === 200,
        'tasks response time < 2s': (r) => r.timings.duration < 2000,
      });
      
      errorRate.add(tasksResponse.status !== 200);
      responseTime.add(tasksResponse.timings.duration);
      requestCount.add(1);
      
      // Create task (occasionally)
      if (Math.random() < 0.2) { // 20% chance to create task
        const taskData = {
          title: `Performance Test Task ${Date.now()}`,
          description: 'Task created during performance testing',
          status: 'pending',
          priority: 'medium',
        };
        
        const createTaskResponse = http.post(
          `${API_BASE}/tasks`,
          JSON.stringify(taskData),
          { headers }
        );
        
        check(createTaskResponse, {
          'create task status is 201': (r) => r.status === 201,
          'created task has id': (r) => r.json('id') !== undefined,
        });
        
        errorRate.add(createTaskResponse.status !== 201);
        responseTime.add(createTaskResponse.timings.duration);
        requestCount.add(1);
      }
    });
    
    sleep(2);
  });
}

// Setup function (runs once before test)
export function setup() {
  console.log('Starting performance test setup...');
  
  // Verify base URL is accessible
  const healthCheck = http.get(`${BASE_URL}/health`);
  if (healthCheck.status !== 200) {
    throw new Error(`Base URL ${BASE_URL} is not accessible`);
  }
  
  console.log(`Performance test targeting: ${BASE_URL}`);
  console.log('Test configuration:', JSON.stringify(options, null, 2));
  
  return { baseUrl: BASE_URL };
}

// Teardown function (runs once after test)
export function teardown(data) {
  console.log('Performance test completed');
  console.log('Test summary:');
  console.log(`- Target URL: ${data.baseUrl}`);
  console.log('- Test duration: ~16 minutes');
  console.log('- Max concurrent users: 20');
}