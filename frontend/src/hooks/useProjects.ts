import { useState, useEffect, useCallback } from 'react';

export interface Project {
  id: string;
  name: string;
  project_code: string;
  description?: string;
  status: 'planning' | 'active' | 'on_hold' | 'completed' | 'cancelled';
  priority: 'low' | 'medium' | 'high' | 'critical';
  project_type: 'internal' | 'client' | 'product' | 'research';
  project_manager_id?: string;
  project_manager_name?: string;
  organization_id: string;
  planned_start_date?: string;
  planned_end_date?: string;
  actual_start_date?: string;
  actual_end_date?: string;
  total_budget?: number;
  spent_budget?: number;
  budget_currency: string;
  completion_percentage: number;
  team_size?: number;
  created_at: string;
  updated_at: string;
}

export interface ProjectCreateData {
  name: string;
  project_code?: string;
  description?: string;
  project_type: 'internal' | 'client' | 'product' | 'research';
  priority: 'low' | 'medium' | 'high' | 'critical';
  project_manager_id?: string;
  organization_id: string;
  planned_start_date?: string;
  planned_end_date?: string;
  total_budget?: number;
  budget_currency: string;
  methodology?: 'waterfall' | 'agile' | 'hybrid' | 'lean';
  is_billable?: boolean;
  client_id?: string;
  tags?: string[];
}

interface UseProjectsFilters {
  organization_id?: string;
  status?: string;
  project_manager_id?: string;
  priority?: string;
  project_type?: string;
  search?: string;
}

interface UseProjectsPagination {
  currentPage: number;
  totalPages: number;
  totalItems: number;
  itemsPerPage: number;
}

interface UseProjectsReturn {
  projects: Project[];
  loading: boolean;
  error: string | null;
  filters: UseProjectsFilters;
  pagination: UseProjectsPagination;
  fetchProjects: () => Promise<void>;
  updateFilters: (newFilters: Partial<UseProjectsFilters>) => void;
  updatePagination: (newPagination: Partial<UseProjectsPagination>) => void;
  createProject: (projectData: ProjectCreateData) => Promise<void>;
  updateProject: (id: string, projectData: Partial<ProjectCreateData>) => Promise<void>;
  deleteProject: (id: string) => Promise<void>;
}

// Mock data for development - will be replaced with actual API calls
const mockProjects: Project[] = [
  {
    id: '1',
    name: 'ERPシステム刷新プロジェクト',
    project_code: 'ERP-2024-001',
    description: '既存ERPシステムの全面刷新とクラウド移行を行うプロジェクト',
    status: 'active',
    priority: 'high',
    project_type: 'internal',
    project_manager_id: 'user-001',
    project_manager_name: '田中 太郎',
    organization_id: '1',
    planned_start_date: '2024-01-15',
    planned_end_date: '2024-12-31',
    actual_start_date: '2024-01-15',
    total_budget: 50000000,
    spent_budget: 15000000,
    budget_currency: 'JPY',
    completion_percentage: 35,
    team_size: 12,
    created_at: '2024-01-10T09:00:00Z',
    updated_at: '2024-01-26T14:30:00Z'
  },
  {
    id: '2',
    name: '新製品開発プロジェクト',
    project_code: 'PROD-2024-002',
    description: 'AI技術を活用した新製品の開発プロジェクト',
    status: 'planning',
    priority: 'medium',
    project_type: 'product',
    project_manager_id: 'user-002',
    project_manager_name: '佐藤 花子',
    organization_id: '1',
    planned_start_date: '2024-03-01',
    planned_end_date: '2024-11-30',
    total_budget: 30000000,
    spent_budget: 2000000,
    budget_currency: 'JPY',
    completion_percentage: 10,
    team_size: 8,
    created_at: '2024-01-20T10:00:00Z',
    updated_at: '2024-01-25T16:45:00Z'
  }
];

export const useProjects = (): UseProjectsReturn => {
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [filters, setFilters] = useState<UseProjectsFilters>({});
  const [pagination, setPagination] = useState<UseProjectsPagination>({
    currentPage: 1,
    totalPages: 1,
    totalItems: 0,
    itemsPerPage: 10
  });

  const fetchProjects = useCallback(async () => {
    setLoading(true);
    setError(null);
    
    try {
      // TODO: Replace with actual API call to /api/v1/projects
      await new Promise(resolve => setTimeout(resolve, 500));
      
      let filteredProjects = [...mockProjects];
      
      if (filters.status) {
        filteredProjects = filteredProjects.filter(p => p.status === filters.status);
      }
      
      if (filters.priority) {
        filteredProjects = filteredProjects.filter(p => p.priority === filters.priority);
      }
      
      if (filters.project_type) {
        filteredProjects = filteredProjects.filter(p => p.project_type === filters.project_type);
      }
      
      if (filters.search) {
        const searchLower = filters.search.toLowerCase();
        filteredProjects = filteredProjects.filter(p =>
          p.name.toLowerCase().includes(searchLower) ||
          p.project_code.toLowerCase().includes(searchLower) ||
          (p.description && p.description.toLowerCase().includes(searchLower))
        );
      }
      
      setProjects(filteredProjects);
      setPagination(prev => ({
        ...prev,
        totalItems: filteredProjects.length,
        totalPages: Math.ceil(filteredProjects.length / prev.itemsPerPage)
      }));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'プロジェクトの取得に失敗しました');
    } finally {
      setLoading(false);
    }
  }, [filters]);

  const updateFilters = useCallback((newFilters: Partial<UseProjectsFilters>) => {
    setFilters(prev => ({ ...prev, ...newFilters }));
    setPagination(prev => ({ ...prev, currentPage: 1 }));
  }, []);

  const updatePagination = useCallback((newPagination: Partial<UseProjectsPagination>) => {
    setPagination(prev => ({ ...prev, ...newPagination }));
  }, []);

  const createProject = useCallback(async (projectData: ProjectCreateData) => {
    setLoading(true);
    setError(null);
    
    try {
      // TODO: Replace with actual API call
      await new Promise(resolve => setTimeout(resolve, 800));
      
      const newProject: Project = {
        id: `proj-${Date.now()}`,
        name: projectData.name,
        project_code: projectData.project_code || `AUTO-${Date.now()}`,
        description: projectData.description,
        status: 'planning',
        priority: projectData.priority,
        project_type: projectData.project_type,
        project_manager_id: projectData.project_manager_id,
        organization_id: projectData.organization_id,
        planned_start_date: projectData.planned_start_date,
        planned_end_date: projectData.planned_end_date,
        total_budget: projectData.total_budget,
        budget_currency: projectData.budget_currency,
        completion_percentage: 0,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString()
      };
      
      mockProjects.unshift(newProject);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'プロジェクトの作成に失敗しました');
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const updateProject = useCallback(async (id: string, projectData: Partial<ProjectCreateData>) => {
    setLoading(true);
    setError(null);
    
    try {
      // TODO: Replace with actual API call
      await new Promise(resolve => setTimeout(resolve, 600));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'プロジェクトの更新に失敗しました');
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const deleteProject = useCallback(async (id: string) => {
    setLoading(true);
    setError(null);
    
    try {
      // TODO: Replace with actual API call
      await new Promise(resolve => setTimeout(resolve, 400));
      
      const projectIndex = mockProjects.findIndex(p => p.id === id);
      if (projectIndex > -1) {
        mockProjects.splice(projectIndex, 1);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'プロジェクトの削除に失敗しました');
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchProjects();
  }, [fetchProjects]);

  return {
    projects,
    loading,
    error,
    filters,
    pagination,
    fetchProjects,
    updateFilters,
    updatePagination,
    createProject,
    updateProject,
    deleteProject
  };
};