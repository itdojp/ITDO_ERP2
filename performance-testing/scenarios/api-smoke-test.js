// API Smoke Test for ITDO ERP System
// Quick validation of critical API endpoints

import http from 'k6/http';
import { check, group } from 'k6';

// Minimal load for smoke testing
export const options = {
  vus: 1,
  duration: '2m',
  thresholds: {
    http_req_duration: ['p(95)<1000'],     // 95% under 1s
    http_req_failed: ['rate<0.01'],        // <1% error rate
  },
};

const BASE_URL = __ENV.BASE_URL || 'http://localhost:8000';
const API_BASE = `${BASE_URL}/api/v1`;

export default function () {
  group('API Smoke Test', () => {
    group('Health Endpoints', () => {
      // Main health check
      const health = http.get(`${BASE_URL}/health`);
      check(health, {
        'health endpoint accessible': (r) => r.status === 200,
        'health response has status': (r) => r.json('status') !== undefined,
      });
      
      // Ping endpoint
      const ping = http.get(`${BASE_URL}/ping`);
      check(ping, {
        'ping endpoint accessible': (r) => r.status === 200,
      });
      
      // OpenAPI docs
      const docs = http.get(`${BASE_URL}/docs`);
      check(docs, {
        'docs endpoint accessible': (r) => r.status === 200,
      });
    });
    
    group('Public API Endpoints', () => {
      // Test endpoints that don't require authentication
      const endpoints = [
        '/organizations',
        '/departments',
        '/users',
        '/tasks',
      ];
      
      endpoints.forEach(endpoint => {
        const response = http.get(`${API_BASE}${endpoint}`);
        check(response, {
          [`${endpoint} responds`]: (r) => r.status === 200 || r.status === 401, // 401 is acceptable for protected endpoints
          [`${endpoint} fast response`]: (r) => r.timings.duration < 2000,
        });
      });
    });
    
    group('API Metadata', () => {
      // Check API version and metadata
      const root = http.get(API_BASE);
      check(root, {
        'API root accessible': (r) => r.status === 200 || r.status === 404, // Some APIs don't have root endpoint
      });
    });
  });
}

export function setup() {
  console.log('🔍 Starting API Smoke Test');
  console.log(`Target: ${BASE_URL}`);
  return { baseUrl: BASE_URL };
}

export function teardown(data) {
  console.log('✅ API Smoke Test completed');
  console.log('This test validates basic API accessibility and response times');
}