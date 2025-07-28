import { apiClient } from './api-client';

export interface TestUser {
  email: string;
  password: string;
  fullName: string;
  mfaEnabled?: boolean;
  mfaSecret?: string;
  isLocked?: boolean;
}

const testUsers: TestUser[] = [
  {
    email: 'user@example.com',
    password: 'TestPassword123!',
    fullName: 'Test User',
    mfaEnabled: false,
  },
  {
    email: 'mfa-user@example.com',
    password: 'TestPassword123!',
    fullName: 'MFA Test User',
    mfaEnabled: true,
    mfaSecret: 'JBSWY3DPEHPK3PXP', // Test secret
  },
  {
    email: 'locked@example.com',
    password: 'TestPassword123!',
    fullName: 'Locked User',
    isLocked: true,
  },
  {
    email: 'existing@example.com',
    password: 'TestPassword123!',
    fullName: 'Existing User',
  },
];

export async function setupMockData() {
  // In a real E2E test, this would:
  // 1. Connect to test database
  // 2. Clear existing test data
  // 3. Create test users
  // 4. Set up test organization/roles
  
  try {
    // Clear test data
    await apiClient.post('/api/v1/test/reset');
    
    // Create test users
    for (const user of testUsers) {
      await apiClient.post('/api/v1/test/users', user);
    }
    
    // Set up test organization
    await apiClient.post('/api/v1/test/organization', {
      name: 'Test Organization',
      code: 'TEST001',
    });
  } catch (error) {
    console.warn('Mock data setup failed, using existing data:', error);
  }
}

export async function cleanupMockData() {
  try {
    await apiClient.post('/api/v1/test/cleanup');
  } catch (error) {
    console.warn('Mock data cleanup failed:', error);
  }
}

export async function generateTOTPCode(email: string): Promise<string> {
  // In real tests, this would generate actual TOTP code
  const user = testUsers.find(u => u.email === email);
  if (!user?.mfaSecret) {
    throw new Error(`No MFA secret for user ${email}`);
  }
  
  // Mock TOTP generation
  // In real implementation, use speakeasy or similar library
  return '123456';
}

export async function getPasswordResetToken(
  email: string,
  options?: { expired?: boolean }
): Promise<string> {
  try {
    const response = await apiClient.post('/api/v1/test/password-reset-token', {
      email,
      expired: options?.expired || false,
    });
    return response.data.token;
  } catch (error) {
    // Fallback for local testing
    return options?.expired ? 'expired-token-12345' : 'valid-token-12345';
  }
}

export async function createTestSession(email: string, deviceInfo?: any) {
  try {
    const response = await apiClient.post('/api/v1/test/session', {
      email,
      deviceInfo: deviceInfo || {
        browser: 'Chrome',
        os: 'Windows',
        isMobile: false,
      },
    });
    return response.data;
  } catch (error) {
    console.warn('Failed to create test session:', error);
  }
}

export async function getBackupCodes(email: string): Promise<string[]> {
  const user = testUsers.find(u => u.email === email);
  if (!user?.mfaEnabled) {
    throw new Error(`User ${email} does not have MFA enabled`);
  }
  
  // Mock backup codes
  return [
    'ABCD1234',
    'EFGH5678',
    'IJKL9012',
    'MNOP3456',
    'QRST7890',
    'UVWX1234',
    'YZAB5678',
    'CDEF9012',
  ];
}

// Utility to wait for API response
export async function waitForApi(path: string, timeout = 5000): Promise<void> {
  const startTime = Date.now();
  
  while (Date.now() - startTime < timeout) {
    try {
      await apiClient.get(path);
      return;
    } catch (error) {
      await new Promise(resolve => setTimeout(resolve, 100));
    }
  }
  
  throw new Error(`API ${path} did not respond within ${timeout}ms`);
}