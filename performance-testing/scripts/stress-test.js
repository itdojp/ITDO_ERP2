// k6 Stress Testing Script for ITDO ERP System
// This script tests system behavior under extreme load conditions

import http from 'k6/http';
import { check, group, sleep } from 'k6';
import { Rate, Trend, Counter } from 'k6/metrics';

// Custom metrics for stress testing
const errorRate = new Rate('stress_error_rate');
const responseTime = new Trend('stress_response_time');
const requestCount = new Counter('stress_request_count');
const timeouts = new Counter('timeout_count');

// Stress test configuration
export const options = {
  stages: [
    { duration: '1m', target: 10 },    // Normal load
    { duration: '2m', target: 50 },    // Increase load
    { duration: '3m', target: 100 },   // High load
    { duration: '2m', target: 200 },   // Stress load
    { duration: '1m', target: 300 },   // Peak stress
    { duration: '2m', target: 200 },   // Scale back
    { duration: '3m', target: 100 },   // Cool down
    { duration: '2m', target: 0 },     // Ramp down
  ],
  thresholds: {
    http_req_duration: ['p(99)<5000'],     // 99% of requests under 5s
    http_req_failed: ['rate<0.20'],        // Error rate under 20% (higher for stress)
    stress_response_time: ['p(90)<3000'],  // 90% under 3s
    timeout_count: ['count<100'],          // Max 100 timeouts
  },
  // Increase timeout for stress testing
  timeout: '60s',
};

// Environment configuration
const BASE_URL = __ENV.BASE_URL || 'http://localhost:8000';
const API_BASE = `${BASE_URL}/api/v1`;

// Stress test scenarios
const stressScenarios = {
  // Heavy read operations
  heavyRead: () => {
    const headers = { 'Content-Type': 'application/json' };
    
    // Multiple concurrent reads
    const promises = [
      http.asyncRequest('GET', `${BASE_URL}/health`, null, { headers }),
      http.asyncRequest('GET', `${API_BASE}/users`, null, { headers }),
      http.asyncRequest('GET', `${API_BASE}/organizations`, null, { headers }),
      http.asyncRequest('GET', `${API_BASE}/departments`, null, { headers }),
      http.asyncRequest('GET', `${API_BASE}/tasks`, null, { headers }),
    ];
    
    const responses = promises.map(p => p.wait());
    
    responses.forEach((response, index) => {
      const endpoint = ['health', 'users', 'organizations', 'departments', 'tasks'][index];
      
      check(response, {
        [`${endpoint} stress test success`]: (r) => r.status < 400,
        [`${endpoint} response time acceptable`]: (r) => r.timings.duration < 10000,
      });
      
      errorRate.add(response.status >= 400);
      responseTime.add(response.timings.duration);
      requestCount.add(1);
      
      if (response.timings.duration > 30000) {
        timeouts.add(1);
      }
    });
  },
  
  // Write-heavy operations
  heavyWrite: () => {
    const headers = { 'Content-Type': 'application/json' };
    
    // Create multiple resources rapidly
    const timestamp = Date.now();
    const orgData = {
      name: `Stress Org ${timestamp}`,
      description: `Created during stress test at ${new Date().toISOString()}`,
    };
    
    const createResponse = http.post(
      `${API_BASE}/organizations`,
      JSON.stringify(orgData),
      { headers }
    );
    
    check(createResponse, {
      'stress create organization success': (r) => r.status === 201 || r.status === 429, // Allow rate limiting
      'stress create response time': (r) => r.timings.duration < 15000,
    });
    
    errorRate.add(createResponse.status >= 400 && createResponse.status !== 429);
    responseTime.add(createResponse.timings.duration);
    requestCount.add(1);
    
    if (createResponse.timings.duration > 30000) {
      timeouts.add(1);
    }
  },
  
  // Database stress
  databaseStress: () => {
    const headers = { 'Content-Type': 'application/json' };
    
    // Complex queries and operations
    const queries = [
      `${API_BASE}/tasks?limit=100&sort=created_at`,
      `${API_BASE}/users?include_inactive=true`,
      `${API_BASE}/organizations?search=test`,
      `${API_BASE}/departments?hierarchy=true`,
    ];
    
    const randomQuery = queries[Math.floor(Math.random() * queries.length)];
    const response = http.get(randomQuery, { headers });
    
    check(response, {
      'database stress query success': (r) => r.status < 500,
      'database query response time': (r) => r.timings.duration < 20000,
    });
    
    errorRate.add(response.status >= 500);
    responseTime.add(response.timings.duration);
    requestCount.add(1);
    
    if (response.timings.duration > 30000) {
      timeouts.add(1);
    }
  },
};

// Main stress test function
export default function () {
  const currentVu = __VU;
  const currentIter = __ITER;
  
  group('Stress Test Scenarios', () => {
    // Distribute load across different scenarios
    const scenario = currentVu % 3;
    
    switch (scenario) {
      case 0:
        group('Heavy Read Stress', () => {
          stressScenarios.heavyRead();
        });
        break;
      case 1:
        group('Heavy Write Stress', () => {
          stressScenarios.heavyWrite();
        });
        break;
      case 2:
        group('Database Stress', () => {
          stressScenarios.databaseStress();
        });
        break;
    }
    
    // Random sleep to simulate realistic user behavior
    const sleepTime = Math.random() * 3; // 0-3 seconds
    sleep(sleepTime);
    
    // Occasionally perform burst requests
    if (currentIter % 10 === 0) {
      group('Burst Requests', () => {
        for (let i = 0; i < 5; i++) {
          const burstResponse = http.get(`${BASE_URL}/health`);
          check(burstResponse, {
            'burst request success': (r) => r.status === 200,
          });
          
          errorRate.add(burstResponse.status !== 200);
          responseTime.add(burstResponse.timings.duration);
          requestCount.add(1);
        }
      });
    }
  });
}

// Setup for stress test
export function setup() {
  console.log('Starting stress test setup...');
  
  // Pre-flight checks
  const healthCheck = http.get(`${BASE_URL}/health`);
  if (healthCheck.status !== 200) {
    throw new Error(`System is not healthy before stress test: ${healthCheck.status}`);
  }
  
  console.log('🚨 STRESS TEST WARNING 🚨');
  console.log('This test will apply extreme load to the system');
  console.log(`Target: ${BASE_URL}`);
  console.log('Expected: High error rates and response times');
  console.log('Duration: ~16 minutes with up to 300 concurrent users');
  
  return {
    baseUrl: BASE_URL,
    startTime: Date.now(),
  };
}

// Teardown for stress test
export function teardown(data) {
  const duration = Math.round((Date.now() - data.startTime) / 1000);
  
  console.log('🏁 Stress test completed');
  console.log(`Duration: ${duration} seconds`);
  console.log(`Target: ${data.baseUrl}`);
  console.log('');
  console.log('📊 Expected Results Analysis:');
  console.log('- Response times should increase under load');
  console.log('- Error rates may spike during peak stress (300 users)');
  console.log('- System should recover during cool-down period');
  console.log('- No complete system failures should occur');
  console.log('');
  console.log('Next steps: Analyze results for bottlenecks and scaling needs');
}