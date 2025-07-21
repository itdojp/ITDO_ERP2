import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { queryKeys, handleApiError, invalidateQueries } from '../../lib/queryClient'
import * as projectApi from '../../services/projectApi'
import type { Project } from '../../types/project'

// Projects list query
export const useProjects = (params?: {
  page?: number
  limit?: number
  search?: string
  status?: string
  organizationId?: string
  userId?: string
  sortBy?: string
  sortOrder?: 'asc' | 'desc'
}) => {
  return useQuery({
    queryKey: [...queryKeys.projects(), 'list', params],
    queryFn: async () => {
      try {
        return await projectApi.fetchProjects(params)
      } catch (error) {
        throw handleApiError(error)
      }
    },
    staleTime: 2 * 60 * 1000, // 2 minutes
    keepPreviousData: true, // Keep previous data while fetching new data
  })
}

// Single project query
export const useProject = (id: string, enabled = true) => {
  return useQuery({
    queryKey: queryKeys.project(id),
    queryFn: async () => {
      try {
        return await projectApi.fetchProject(id)
      } catch (error) {
        throw handleApiError(error)
      }
    },
    enabled: enabled && !!id,
    staleTime: 5 * 60 * 1000, // 5 minutes
  })
}

// Projects by organization query
export const useProjectsByOrganization = (organizationId: string, enabled = true) => {
  return useQuery({
    queryKey: queryKeys.projectsByOrg(organizationId),
    queryFn: async () => {
      try {
        return await projectApi.fetchProjectsByOrganization(organizationId)
      } catch (error) {
        throw handleApiError(error)
      }
    },
    enabled: enabled && !!organizationId,
    staleTime: 3 * 60 * 1000, // 3 minutes
  })
}

// Create project mutation
export const useCreateProject = () => {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: async (projectData: Omit<Project, 'id' | 'createdAt' | 'updatedAt'>) => {
      try {
        return await projectApi.createProject(projectData)
      } catch (error) {
        throw handleApiError(error)
      }
    },
    onSuccess: (newProject) => {
      // Invalidate projects list
      invalidateQueries.projects()
      
      // Add new project to cache
      queryClient.setQueryData(queryKeys.project(newProject.id), newProject)
      
      // Invalidate organization-specific projects if applicable
      if (newProject.organizationId) {
        queryClient.invalidateQueries({ 
          queryKey: queryKeys.projectsByOrg(newProject.organizationId) 
        })
      }
    },
    onError: (error) => {
      console.error('Failed to create project:', error)
    },
  })
}

// Update project mutation
export const useUpdateProject = () => {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: async ({ id, ...projectData }: Partial<Project> & { id: string }) => {
      try {
        return await projectApi.updateProject(id, projectData)
      } catch (error) {
        throw handleApiError(error)
      }
    },
    onSuccess: (updatedProject, variables) => {
      // Update project in cache
      queryClient.setQueryData(queryKeys.project(variables.id), updatedProject)
      
      // Invalidate projects list
      invalidateQueries.projects()
      
      // Invalidate organization-specific projects if applicable
      if (updatedProject.organizationId) {
        queryClient.invalidateQueries({ 
          queryKey: queryKeys.projectsByOrg(updatedProject.organizationId) 
        })
      }
    },
    onError: (error) => {
      console.error('Failed to update project:', error)
    },
  })
}

// Delete project mutation
export const useDeleteProject = () => {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: async (id: string) => {
      try {
        const project = queryClient.getQueryData(queryKeys.project(id)) as Project
        await projectApi.deleteProject(id)
        return { id, project }
      } catch (error) {
        throw handleApiError(error)
      }
    },
    onSuccess: ({ id, project }) => {
      // Remove project from cache
      queryClient.removeQueries({ queryKey: queryKeys.project(id) })
      
      // Invalidate projects list
      invalidateQueries.projects()
      
      // Invalidate organization-specific projects if applicable
      if (project?.organizationId) {
        queryClient.invalidateQueries({ 
          queryKey: queryKeys.projectsByOrg(project.organizationId) 
        })
      }
      
      // Invalidate related tasks
      queryClient.invalidateQueries({ 
        queryKey: queryKeys.tasksByProject(id) 
      })
    },
    onError: (error) => {
      console.error('Failed to delete project:', error)
    },
  })
}

// Archive project mutation
export const useArchiveProject = () => {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: async (id: string) => {
      try {
        return await projectApi.archiveProject(id)
      } catch (error) {
        throw handleApiError(error)
      }
    },
    onSuccess: (archivedProject, id) => {
      // Update project in cache
      queryClient.setQueryData(queryKeys.project(id), archivedProject)
      
      // Invalidate projects list
      invalidateQueries.projects()
    },
    onError: (error) => {
      console.error('Failed to archive project:', error)
    },
  })
}

// Restore project mutation
export const useRestoreProject = () => {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: async (id: string) => {
      try {
        return await projectApi.restoreProject(id)
      } catch (error) {
        throw handleApiError(error)
      }
    },
    onSuccess: (restoredProject, id) => {
      // Update project in cache
      queryClient.setQueryData(queryKeys.project(id), restoredProject)
      
      // Invalidate projects list
      invalidateQueries.projects()
    },
    onError: (error) => {
      console.error('Failed to restore project:', error)
    },
  })
}

// Project members query
export const useProjectMembers = (projectId: string, enabled = true) => {
  return useQuery({
    queryKey: [...queryKeys.project(projectId), 'members'],
    queryFn: async () => {
      try {
        return await projectApi.fetchProjectMembers(projectId)
      } catch (error) {
        throw handleApiError(error)
      }
    },
    enabled: enabled && !!projectId,
    staleTime: 3 * 60 * 1000, // 3 minutes
  })
}

// Add project member mutation
export const useAddProjectMember = () => {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: async ({ 
      projectId, 
      userId, 
      role 
    }: { 
      projectId: string
      userId: string
      role?: string 
    }) => {
      try {
        return await projectApi.addProjectMember(projectId, userId, role)
      } catch (error) {
        throw handleApiError(error)
      }
    },
    onSuccess: (_, variables) => {
      // Invalidate project members
      queryClient.invalidateQueries({ 
        queryKey: [...queryKeys.project(variables.projectId), 'members'] 
      })
      
      // Invalidate projects list to update member counts
      invalidateQueries.projects()
    },
    onError: (error) => {
      console.error('Failed to add project member:', error)
    },
  })
}

// Remove project member mutation
export const useRemoveProjectMember = () => {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: async ({ 
      projectId, 
      userId 
    }: { 
      projectId: string
      userId: string 
    }) => {
      try {
        await projectApi.removeProjectMember(projectId, userId)
        return { projectId, userId }
      } catch (error) {
        throw handleApiError(error)
      }
    },
    onSuccess: ({ projectId }) => {
      // Invalidate project members
      queryClient.invalidateQueries({ 
        queryKey: [...queryKeys.project(projectId), 'members'] 
      })
      
      // Invalidate projects list to update member counts
      invalidateQueries.projects()
    },
    onError: (error) => {
      console.error('Failed to remove project member:', error)
    },
  })
}

// Project statistics query
export const useProjectStatistics = (projectId: string, enabled = true) => {
  return useQuery({
    queryKey: [...queryKeys.project(projectId), 'statistics'],
    queryFn: async () => {
      try {
        return await projectApi.fetchProjectStatistics(projectId)
      } catch (error) {
        throw handleApiError(error)
      }
    },
    enabled: enabled && !!projectId,
    staleTime: 5 * 60 * 1000, // 5 minutes
    select: (data) => {
      // Calculate additional statistics
      const totalTasks = data.taskCounts?.total || 0
      const completedTasks = data.taskCounts?.completed || 0
      const progress = totalTasks > 0 ? (completedTasks / totalTasks) * 100 : 0
      
      return {
        ...data,
        calculated: {
          progress: Math.round(progress),
          remainingTasks: totalTasks - completedTasks,
          completionRate: progress,
        },
      }
    },
  })
}

// Duplicate project mutation
export const useDuplicateProject = () => {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: async ({ 
      id, 
      name, 
      includeMembers = false,
      includeTasks = false 
    }: { 
      id: string
      name: string
      includeMembers?: boolean
      includeTasks?: boolean
    }) => {
      try {
        return await projectApi.duplicateProject(id, name, { includeMembers, includeTasks })
      } catch (error) {
        throw handleApiError(error)
      }
    },
    onSuccess: (duplicatedProject) => {
      // Add duplicated project to cache
      queryClient.setQueryData(queryKeys.project(duplicatedProject.id), duplicatedProject)
      
      // Invalidate projects list
      invalidateQueries.projects()
      
      // Invalidate organization-specific projects if applicable
      if (duplicatedProject.organizationId) {
        queryClient.invalidateQueries({ 
          queryKey: queryKeys.projectsByOrg(duplicatedProject.organizationId) 
        })
      }
    },
    onError: (error) => {
      console.error('Failed to duplicate project:', error)
    },
  })
}