import { renderHook, act, waitFor } from '@testing-library/react';
import { describe, it, expect, beforeEach, beforeAll, afterAll, vi } from 'vitest';
import { useProjects } from '../useProjects';
import { ProjectCreateData } from '../useProjects';

// Mock console methods to avoid noise in test output
const originalConsoleLog = console.log;
const originalConsoleError = console.error;

beforeAll(() => {
  console.log = vi.fn();
  console.error = vi.fn();
});

afterAll(() => {
  console.log = originalConsoleLog;
  console.error = originalConsoleError;
});

describe('useProjects', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should initialize with default state', () => {
    const { result } = renderHook(() => useProjects());

    expect(result.current.projects).toEqual([]);
    expect(result.current.loading).toBe(true); // Should be loading initially
    expect(result.current.error).toBe(null);
    expect(result.current.filters).toEqual({});
    expect(result.current.pagination).toEqual({
      currentPage: 1,
      totalPages: 1,
      totalItems: 0,
      itemsPerPage: 10
    });
  });

  it('should fetch projects on mount', async () => {
    const { result } = renderHook(() => useProjects());

    expect(result.current.loading).toBe(true);
    expect(result.current.projects).toEqual([]);

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.projects.length).toBeGreaterThan(0);
    expect(result.current.error).toBe(null);
    expect(result.current.pagination.totalItems).toBe(result.current.projects.length);
  });

  it('should create a new project successfully', async () => {
    const { result } = renderHook(() => useProjects());

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    const newProjectData: ProjectCreateData = {
      name: 'テストプロジェクト',
      project_code: 'TEST-001',
      description: 'テスト用プロジェクト',
      project_type: 'internal',
      priority: 'medium',
      organization_id: '1',
      budget_currency: 'JPY',
      total_budget: 1000000
    };

    await act(async () => {
      await result.current.createProject(newProjectData);
    });

    expect(result.current.loading).toBe(false);
    expect(result.current.error).toBe(null);
  });

  it('should handle loading states correctly during operations', async () => {
    const { result } = renderHook(() => useProjects());

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    await act(async () => {
      await result.current.createProject({
        name: 'Loading Test Project',
        project_type: 'internal',
        priority: 'low',
        organization_id: '1',
        budget_currency: 'JPY'
      });
    });

    expect(result.current.loading).toBe(false);
  });
});