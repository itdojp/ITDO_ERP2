import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { useAuth } from '../useAuth';

// Mock the API client
vi.mock('../../services/api/client', () => ({
  apiClient: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
  },
}));

// Mock useNavigate
const mockNavigate = vi.fn();
vi.mock('react-router-dom', () => ({
  useNavigate: () => mockNavigate,
}));

describe('useAuth', () => {
  beforeEach(() => {
    localStorage.clear();
    vi.clearAllMocks();
  });

  it('initializes with unauthenticated state', () => {
    const { result } = renderHook(() => useAuth());

    expect(result.current.user).toBeNull();
    expect(result.current.isAuthenticated).toBe(false);
    expect(result.current.isLoading).toBe(true);
  });

  it('checks authentication status on mount', async () => {
    const mockUser = {
      id: 1,
      email: 'test@example.com',
      full_name: 'Test User',
      is_active: true,
      mfa_required: false,
      has_google_account: false,
      created_at: '2024-01-01T00:00:00Z',
    };

    localStorage.setItem('access_token', 'test-token');
    
    const { apiClient } = await import('../../services/api/client');
    (apiClient.get as any).mockResolvedValueOnce({ data: mockUser });

    const { result } = renderHook(() => useAuth());

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.user).toEqual(mockUser);
    expect(result.current.isAuthenticated).toBe(true);
  });

  it('handles login successfully', async () => {
    const mockLoginResponse = {
      access_token: 'test-token',
      token_type: 'bearer',
    };

    const mockUser = {
      id: 1,
      email: 'test@example.com',
      full_name: 'Test User',
      is_active: true,
      mfa_required: false,
      has_google_account: false,
      created_at: '2024-01-01T00:00:00Z',
    };

    const { apiClient } = await import('../../services/api/client');
    (apiClient.post as any).mockResolvedValueOnce({ data: mockLoginResponse });
    (apiClient.get as any).mockResolvedValueOnce({ data: mockUser });

    const { result } = renderHook(() => useAuth());

    await result.current.login('test@example.com', 'password123', false);

    expect(localStorage.getItem('access_token')).toBe('test-token');
    expect(result.current.user).toEqual(mockUser);
    expect(result.current.isAuthenticated).toBe(true);
  });

  it('handles login with MFA requirement', async () => {
    const mockLoginResponse = {
      requires_mfa: true,
      mfa_token: 'test-mfa-token',
    };

    const { apiClient } = await import('../../services/api/client');
    (apiClient.post as any).mockResolvedValueOnce({ data: mockLoginResponse });

    const { result } = renderHook(() => useAuth());

    const response = await result.current.login('test@example.com', 'password123', false);

    expect(response).toEqual(mockLoginResponse);
    expect(localStorage.getItem('access_token')).toBeNull();
  });

  it('handles logout', async () => {
    localStorage.setItem('access_token', 'test-token');

    const { apiClient } = await import('../../services/api/client');
    (apiClient.post as any).mockResolvedValueOnce({});

    const { result } = renderHook(() => useAuth());

    await result.current.logout();

    expect(localStorage.getItem('access_token')).toBeNull();
    expect(result.current.user).toBeNull();
    expect(result.current.isAuthenticated).toBe(false);
    expect(mockNavigate).toHaveBeenCalledWith('/auth/login');
  });

  it('handles registration', async () => {
    const userData = {
      email: 'new@example.com',
      password: 'password123',
      full_name: 'New User',
    };

    const { apiClient } = await import('../../services/api/client');
    (apiClient.post as any).mockResolvedValueOnce({ data: { success: true } });

    const { result } = renderHook(() => useAuth());

    await result.current.register(userData);

    expect(apiClient.post).toHaveBeenCalledWith('/api/v1/users/register', userData);
  });

  it('handles password reset request', async () => {
    const { apiClient } = await import('../../services/api/client');
    (apiClient.post as any).mockResolvedValueOnce({ data: { success: true } });

    const { result } = renderHook(() => useAuth());

    await result.current.requestPasswordReset('test@example.com');

    expect(apiClient.post).toHaveBeenCalledWith('/api/v1/password-reset/request', {
      email: 'test@example.com',
    });
  });

  it('handles MFA setup', async () => {
    const mockSetupData = {
      qr_code: 'data:image/png;base64,...',
      secret: 'ABCDEFGHIJKLMNOP',
      backup_codes: ['12345678', '87654321'],
    };

    const { apiClient } = await import('../../services/api/client');
    (apiClient.post as any).mockResolvedValueOnce({ data: mockSetupData });

    const { result } = renderHook(() => useAuth());

    const data = await result.current.setupMFA('totp');

    expect(data).toEqual(mockSetupData);
    expect(apiClient.post).toHaveBeenCalledWith('/api/v1/mfa/setup', { method: 'totp' });
  });
});