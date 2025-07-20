import { useState, useCallback } from 'react'
import { 
  Folder, 
  Search, 
  Filter, 
  Plus, 
  Edit, 
  Trash2,
  Calendar,
  BarChart3,
  CheckSquare,
  Clock,
  User
} from 'lucide-react'
import Button from '../components/ui/Button'
import Input from '../components/ui/Input'
import Select from '../components/ui/Select'
import Loading from '../components/ui/Loading'
import Alert from '../components/ui/Alert'
import Toast from '../components/ui/Toast'
import { ProjectCreateModal } from '../components/ProjectCreateModal'
import { ProjectEditModal } from '../components/ProjectEditModal'
import {
  useProjects,
  useProjectStatistics,
  useDeleteProject
} from '../services/projectApi'
import {
  Project,
  ProjectFilters
} from '../types/task'

interface ProjectItemProps {
  project: Project
  onEdit: (project: Project) => void
  onDelete: (project: Project) => void
  onViewDetails: (project: Project) => void
}

function ProjectItem({ project, onEdit, onDelete, onViewDetails }: ProjectItemProps) {
  const getStatusColor = (status: Project['status']) => {
    switch (status) {
      case 'ACTIVE': return 'text-green-600 bg-green-100'
      case 'COMPLETED': return 'text-blue-600 bg-blue-100'
      case 'ARCHIVED': return 'text-gray-600 bg-gray-100'
      default: return 'text-gray-600 bg-gray-100'
    }
  }

  return (
    <div className="bg-white rounded-lg border p-4 hover:shadow-md transition-shadow" data-testid="project-item">
      {/* Header */}
      <div className="flex items-start justify-between mb-3">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-1">
            <h3 className="text-lg font-semibold text-gray-900">{project.name}</h3>
            <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(project.status)}`}>
              {project.status}
            </span>
          </div>
          <p className="text-sm text-gray-600 mb-2">Code: {project.code}</p>
          {project.description && (
            <p className="text-sm text-gray-600 mb-2">{project.description}</p>
          )}
        </div>
        <div className="flex items-center gap-2 ml-4">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => onViewDetails(project)}
            data-testid="view-project"
          >
            <Folder className="h-4 w-4" />
          </Button>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => onEdit(project)}
            data-testid="edit-project"
          >
            <Edit className="h-4 w-4" />
          </Button>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => onDelete(project)}
            data-testid="delete-project"
          >
            <Trash2 className="h-4 w-4 text-red-600" />
          </Button>
        </div>
      </div>
      
      {/* Project Info */}
      <div className="flex items-center justify-between text-sm text-gray-500">
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-1">
            <User className="h-3 w-3" />
            <span>{project.owner.full_name}</span>
          </div>
          <div className="flex items-center gap-1">
            <CheckSquare className="h-3 w-3" />
            <span>{project.task_count || 0} tasks</span>
          </div>
          <div className="flex items-center gap-1">
            <Calendar className="h-3 w-3" />
            <span>Created {new Date(project.created_at).toLocaleDateString()}</span>
          </div>
        </div>
        <div className="text-xs">
          Updated {new Date(project.updated_at).toLocaleDateString()}
        </div>
      </div>
    </div>
  )
}

interface StatisticsCardProps {
  title: string
  value: string | number
  icon: React.ReactNode
  color: string
}

function StatisticsCard({ title, value, icon, color }: StatisticsCardProps) {
  return (
    <div className="bg-white p-4 rounded-lg border">
      <div className="flex items-center">
        <div className={`p-2 rounded-lg ${color}`}>
          {icon}
        </div>
        <div className="ml-3">
          <p className="text-sm font-medium text-gray-500">{title}</p>
          <p className="text-2xl font-bold text-gray-900">{value}</p>
        </div>
      </div>
    </div>
  )
}

export function ProjectListPage() {
  // State management
  const [filters, setFilters] = useState<ProjectFilters>({})
  const [showFilters, setShowFilters] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')
  const [toastMessage, setToastMessage] = useState<{ type: 'success' | 'error'; message: string } | null>(null)
  
  // Modal states
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [showEditModal, setShowEditModal] = useState(false)
  const [showDeleteDialog, setShowDeleteDialog] = useState(false)
  const [showDetailsModal, setShowDetailsModal] = useState(false)
  const [editingProject, setEditingProject] = useState<Project | null>(null)
  const [deletingProject, setDeletingProject] = useState<Project | null>(null)
  const [viewingProject, setViewingProject] = useState<Project | null>(null)

  // Queries
  const { 
    data: projectsResponse, 
    isLoading, 
    error 
  } = useProjects(filters)

  const { data: statistics } = useProjectStatistics()

  const projects = projectsResponse?.items || []

  // Mutations
  const deleteProjectMutation = useDeleteProject()

  // Event handlers
  const handleSearch = useCallback((value: string) => {
    setSearchQuery(value)
    setFilters(prev => ({ ...prev, search: value || undefined }))
  }, [])

  const handleFilterChange = useCallback((key: keyof ProjectFilters, value: string | number | undefined) => {
    setFilters(prev => ({ ...prev, [key]: value }))
  }, [])

  const handleStatusFilter = useCallback((status: Project['status']) => {
    setFilters(prev => ({ ...prev, status: prev.status === status ? undefined : status }))
  }, [])

  const handleCreateProject = () => {
    setShowCreateModal(true)
  }

  const handleEditProject = useCallback((project: Project) => {
    setEditingProject(project)
    setShowEditModal(true)
  }, [])

  const handleDeleteProject = useCallback((project: Project) => {
    setDeletingProject(project)
    setShowDeleteDialog(true)
  }, [])

  const handleViewProjectDetails = useCallback((project: Project) => {
    setViewingProject(project)
    setShowDetailsModal(true)
  }, [])

  const handleConfirmDelete = async () => {
    if (!deletingProject) return

    try {
      await deleteProjectMutation.mutateAsync(deletingProject.id)
      setToastMessage({ type: 'success', message: 'Project deleted successfully' })
      setShowDeleteDialog(false)
      setDeletingProject(null)
    } catch {
      setToastMessage({ type: 'error', message: 'Failed to delete project' })
    }
  }

  const clearFilters = () => {
    setFilters({})
    setSearchQuery('')
  }

  // Loading state
  if (isLoading) {
    return <Loading message="Loading projects..." />
  }

  // Error state
  if (error && !projectsResponse) {
    return (
      <Alert 
        variant="error" 
        title="Failed to load projects" 
        message="Please try again later." 
      />
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
            <Folder className="h-8 w-8" />
            Projects
          </h1>
          <p className="text-gray-600 mt-1">
            Manage and track your projects
          </p>
        </div>
        <Button onClick={handleCreateProject} data-testid="create-project-btn">
          <Plus className="h-4 w-4 mr-2" />
          Create Project
        </Button>
      </div>

      {/* Statistics */}
      {statistics && (
        <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
          <StatisticsCard
            title="Total Projects"
            value={statistics.total_projects}
            icon={<Folder className="h-6 w-6 text-white" />}
            color="bg-blue-500"
          />
          <StatisticsCard
            title="Active Projects"
            value={statistics.active_projects}
            icon={<Clock className="h-6 w-6 text-white" />}
            color="bg-green-500"
          />
          <StatisticsCard
            title="Completed Projects"
            value={statistics.completed_projects}
            icon={<CheckSquare className="h-6 w-6 text-white" />}
            color="bg-purple-500"
          />
          <StatisticsCard
            title="Total Tasks"
            value={statistics.total_tasks}
            icon={<BarChart3 className="h-6 w-6 text-white" />}
            color="bg-orange-500"
          />
          <StatisticsCard
            title="Completion Rate"
            value={`${statistics.completion_rate}%`}
            icon={<BarChart3 className="h-6 w-6 text-white" />}
            color="bg-indigo-500"
          />
        </div>
      )}

      {/* Controls */}
      <div className="flex flex-col sm:flex-row gap-4">
        <div className="flex-1">
          <Input
            placeholder="Search projects..."
            value={searchQuery}
            onChange={(e) => handleSearch(e.target.value)}
            leftIcon={<Search className="h-4 w-4" />}
            data-testid="project-search"
          />
        </div>
        <div className="flex items-center gap-2">
          {/* Status Filters */}
          <Button
            variant={filters.status === 'ACTIVE' ? 'default' : 'outline'}
            size="sm"
            onClick={() => handleStatusFilter('ACTIVE')}
            data-testid="filter-active"
          >
            Active
          </Button>
          <Button
            variant={filters.status === 'COMPLETED' ? 'default' : 'outline'}
            size="sm"
            onClick={() => handleStatusFilter('COMPLETED')}
            data-testid="filter-completed"
          >
            Completed
          </Button>
          <Button
            variant="outline"
            onClick={() => setShowFilters(!showFilters)}
          >
            <Filter className="h-4 w-4 mr-2" />
            Filters
          </Button>
        </div>
      </div>

      {/* Advanced Filters */}
      {showFilters && (
        <div className="bg-gray-50 p-4 rounded-lg space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Select
              label="Status"
              value={filters.status || ''}
              onChange={(value) => handleFilterChange('status', Array.isArray(value) ? value[0] : value)}
              options={[
                { value: '', label: 'All Statuses' },
                { value: 'ACTIVE', label: 'Active' },
                { value: 'COMPLETED', label: 'Completed' },
                { value: 'ARCHIVED', label: 'Archived' }
              ]}
            />
            <Select
              label="Owner"
              value={filters.owner_id?.toString() || ''}
              onChange={(value) => {
                const ownerId = Array.isArray(value) ? parseInt(value[0]) : parseInt(value)
                handleFilterChange('owner_id', isNaN(ownerId) ? undefined : ownerId)
              }}
              options={[
                { value: '', label: 'All Owners' },
                { value: '1', label: 'Admin User' },
                { value: '2', label: 'Security Manager' },
                { value: '3', label: 'Training Coordinator' }
              ]}
            />
            <div className="flex items-end">
              <Button
                variant="outline"
                onClick={clearFilters}
              >
                Clear Filters
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Project List */}
      <div className="bg-white rounded-lg border">
        <div className="p-4 border-b border-gray-200">
          <h3 className="text-lg font-medium text-gray-900">Project List</h3>
          <p className="text-sm text-gray-500">
            {projects.length} project{projects.length !== 1 ? 's' : ''} found
          </p>
        </div>
        <div className="p-4" data-testid="project-list">
          {projects.length > 0 ? (
            <div className="space-y-4">
              {projects.map((project) => (
                <ProjectItem
                  key={project.id}
                  project={project}
                  onEdit={handleEditProject}
                  onDelete={handleDeleteProject}
                  onViewDetails={handleViewProjectDetails}
                />
              ))}
            </div>
          ) : (
            <div className="text-center py-8">
              <Folder className="mx-auto h-12 w-12 text-gray-400" />
              <h3 className="mt-2 text-sm font-medium text-gray-900">No projects found</h3>
              <p className="mt-1 text-sm text-gray-500">
                Get started by creating your first project.
              </p>
              <Button onClick={handleCreateProject} className="mt-4">
                <Plus className="h-4 w-4 mr-2" />
                Create Project
              </Button>
            </div>
          )}
        </div>
      </div>

      {/* Toast Notifications */}
      {toastMessage && (
        <Toast
          variant={toastMessage.type === 'success' ? 'success' : 'error'}
          title={toastMessage.type === 'success' ? 'Success' : 'Error'}
          message={toastMessage.message}
          onClose={() => setToastMessage(null)}
          data-testid="success-message"
        />
      )}

      {/* Delete Confirmation Dialog */}
      {showDeleteDialog && deletingProject && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-96">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Delete Project</h3>
            <p className="text-sm text-gray-600 mb-6">
              Are you sure you want to delete the project "{deletingProject.name}"? This action cannot be undone.
              {deletingProject.task_count && deletingProject.task_count > 0 && (
                <span className="block mt-2 text-amber-600 font-medium">
                  Warning: This project has {deletingProject.task_count} associated tasks.
                </span>
              )}
            </p>
            <div className="flex justify-end gap-2">
              <Button
                variant="outline"
                onClick={() => {
                  setShowDeleteDialog(false)
                  setDeletingProject(null)
                }}
              >
                Cancel
              </Button>
              <Button
                variant="default"
                onClick={handleConfirmDelete}
                data-testid="confirm-delete"
                disabled={deleteProjectMutation.isPending}
              >
                {deleteProjectMutation.isPending ? 'Deleting...' : 'Delete'}
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Project Details Modal Placeholder */}
      {showDetailsModal && viewingProject && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-96">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Project Details</h3>
            <div className="space-y-3">
              <div>
                <span className="font-medium">Name:</span> {viewingProject.name}
              </div>
              <div>
                <span className="font-medium">Code:</span> {viewingProject.code}
              </div>
              <div>
                <span className="font-medium">Status:</span> {viewingProject.status}
              </div>
              <div>
                <span className="font-medium">Owner:</span> {viewingProject.owner.full_name}
              </div>
              <div>
                <span className="font-medium">Tasks:</span> {viewingProject.task_count || 0}
              </div>
              {viewingProject.description && (
                <div>
                  <span className="font-medium">Description:</span> {viewingProject.description}
                </div>
              )}
            </div>
            <div className="flex justify-end mt-6">
              <Button
                variant="outline"
                onClick={() => {
                  setShowDetailsModal(false)
                  setViewingProject(null)
                }}
              >
                Close
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Modals */}
      <ProjectCreateModal
        isOpen={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        onSuccess={() => setToastMessage({ type: 'success', message: 'Project created successfully' })}
      />

      <ProjectEditModal
        isOpen={showEditModal}
        onClose={() => {
          setShowEditModal(false)
          setEditingProject(null)
        }}
        onSuccess={() => setToastMessage({ type: 'success', message: 'Project updated successfully' })}
        project={editingProject}
      />
    </div>
  )
}