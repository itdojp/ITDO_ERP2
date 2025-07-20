import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Search, Filter, Users, Plus, Building2 } from 'lucide-react'
import Button from '../components/ui/Button'
import Input from '../components/ui/Input'
import Select from '../components/ui/Select'
import Loading from '../components/ui/Loading'
import Alert from '../components/ui/Alert'
import Toast from '../components/ui/Toast'
import { DepartmentCreateModal } from '../components/DepartmentCreateModal'
import { DepartmentEditModal } from '../components/DepartmentEditModal'
import { DepartmentDeleteDialog } from '../components/DepartmentDeleteDialog'
import { organizationApiService, organizationQueryKeys } from '../services/organizationApi'
import { OrganizationTreeNode, DepartmentFilters, DEPARTMENT_TYPES, Department } from '../types/organization'

interface DepartmentTreeNodeProps {
  node: OrganizationTreeNode
  level: number
  selectedNode?: OrganizationTreeNode | null
  onNodeSelect?: (node: OrganizationTreeNode) => void
  onNodeExpand?: (node: OrganizationTreeNode) => void
  onCreateDepartment?: () => void
  onEditDepartment?: (node: OrganizationTreeNode) => void
  onDeleteDepartment?: (node: OrganizationTreeNode) => void
}

function DepartmentTreeNode({ 
  node, 
  level, 
  selectedNode, 
  onNodeSelect, 
  onNodeExpand,
  onCreateDepartment,
  onEditDepartment,
  onDeleteDepartment
}: DepartmentTreeNodeProps) {
  const hasChildren = node.children && node.children.length > 0
  const isSelected = selectedNode?.id === node.id
  const isDepartment = node.type === 'department'

  const handleNodeClick = () => {
    if (onNodeSelect) {
      onNodeSelect(node)
    }
  }

  const handleExpand = (e: React.MouseEvent) => {
    e.stopPropagation()
    if (hasChildren && onNodeExpand) {
      onNodeExpand(node)
    }
  }

  // Only show departments in this view
  if (!isDepartment && level === 0) {
    return (
      <div>
        {node.children?.map((child) => (
          <DepartmentTreeNode
            key={child.id}
            node={child}
            level={0}
            selectedNode={selectedNode}
            onNodeSelect={onNodeSelect}
            onNodeExpand={onNodeExpand}
            onCreateDepartment={onCreateDepartment}
            onEditDepartment={onEditDepartment}
            onDeleteDepartment={onDeleteDepartment}
          />
        ))}
      </div>
    )
  }

  if (!isDepartment) return null

  return (
    <div data-testid="department-node" data-expandable={hasChildren}>
      <div
        className={`flex items-center p-3 rounded-lg cursor-pointer transition-colors hover:bg-gray-100 ${
          isSelected ? 'bg-blue-50 border border-blue-200' : ''
        }`}
        style={{ marginLeft: `${level * 20}px` }}
        onClick={handleNodeClick}
      >
        {/* Expand/Collapse Button */}
        {hasChildren && (
          <button
            onClick={handleExpand}
            className="p-1 rounded hover:bg-gray-200 transition-colors mr-2"
          >
            <span className="text-xs">{node.expanded ? '▼' : '▶'}</span>
          </button>
        )}

        {/* Department Icon */}
        <Users className="h-4 w-4 mr-3 text-blue-600" />

        {/* Department Info */}
        <div className="flex-1">
          <div className="font-medium text-gray-900">{node.name}</div>
          <div className="text-sm text-gray-500">
            {node.code} • {node.user_count} members
          </div>
        </div>

        {/* Actions */}
        {isSelected && (
          <div className="flex items-center gap-2">
            <Button
              variant="ghost"
              size="sm"
              onClick={(e) => {
                e.stopPropagation()
                onEditDepartment?.(node)
              }}
            >
              Edit
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={(e) => {
                e.stopPropagation()
                onDeleteDepartment?.(node)
              }}
              className="text-red-600 hover:text-red-700"
            >
              Delete
            </Button>
          </div>
        )}
      </div>

      {/* Children */}
      {hasChildren && node.expanded && (
        <div data-testid="department-children" className="ml-6">
          {node.children.map((child) => (
            <DepartmentTreeNode
              key={child.id}
              node={child}
              level={level + 1}
              selectedNode={selectedNode}
              onNodeSelect={onNodeSelect}
              onNodeExpand={onNodeExpand}
              onCreateDepartment={onCreateDepartment}
              onEditDepartment={onEditDepartment}
              onDeleteDepartment={onDeleteDepartment}
            />
          ))}
        </div>
      )}
    </div>
  )
}

export function DepartmentListPage() {
  // State management
  const [filters, setFilters] = useState<DepartmentFilters>({})
  const [selectedNode, setSelectedNode] = useState<OrganizationTreeNode | null>(null)
  const [showFilters, setShowFilters] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')
  const [toastMessage, setToastMessage] = useState<{ type: 'success' | 'error'; message: string } | null>(null)
  const [treeData, setTreeData] = useState<OrganizationTreeNode[]>([])
  
  // Modal states
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [showEditModal, setShowEditModal] = useState(false)
  const [showDeleteDialog, setShowDeleteDialog] = useState(false)
  const [editingDepartment, setEditingDepartment] = useState<Department | null>(null)
  const [deletingDepartment, setDeletingDepartment] = useState<Department | null>(null)

  // Query for organization tree (to get departments)
  const { 
    data: organizationTree, 
    isLoading, 
    error 
  } = useQuery({
    queryKey: organizationQueryKeys.tree(),
    queryFn: () => organizationApiService.getOrganizationTree(),
    onSuccess: (data) => {
      setTreeData(data)
    }
  })

  // Event handlers
  const handleSearch = (value: string) => {
    setSearchQuery(value)
    setFilters(prev => ({ ...prev, search: value || undefined }))
  }

  const handleFilterChange = (key: keyof DepartmentFilters, value: string) => {
    setFilters(prev => ({ ...prev, [key]: value || undefined }))
  }

  const handleNodeSelect = (node: OrganizationTreeNode) => {
    setSelectedNode(node)
  }

  const handleNodeExpand = (node: OrganizationTreeNode) => {
    const updateNodeExpansion = (nodes: OrganizationTreeNode[]): OrganizationTreeNode[] => {
      return nodes.map(n => {
        if (n.id === node.id) {
          return { ...n, expanded: !n.expanded }
        }
        if (n.children) {
          return { ...n, children: updateNodeExpansion(n.children) }
        }
        return n
      })
    }
    
    setTreeData(updateNodeExpansion(treeData))
  }

  const handleCreateDepartment = () => {
    setShowCreateModal(true)
  }

  const handleEditDepartment = async (node: OrganizationTreeNode) => {
    try {
      // Convert OrganizationTreeNode to Department for editing
      const department = await organizationApiService.getDepartmentById(node.id)
      setEditingDepartment(department)
      setShowEditModal(true)
    } catch (error) {
      setToastMessage({ type: 'error', message: 'Failed to load department details' })
    }
  }

  const handleDeleteDepartment = async (node: OrganizationTreeNode) => {
    try {
      // Convert OrganizationTreeNode to Department for deletion
      const department = await organizationApiService.getDepartmentById(node.id)
      setDeletingDepartment(department)
      setShowDeleteDialog(true)
    } catch (error) {
      setToastMessage({ type: 'error', message: 'Failed to load department details' })
    }
  }

  const handleModalSuccess = () => {
    setToastMessage({ type: 'success', message: 'Department operation completed successfully' })
  }

  // Get all departments from tree for counting
  const getAllDepartments = (nodes: OrganizationTreeNode[]): OrganizationTreeNode[] => {
    const departments: OrganizationTreeNode[] = []
    const traverse = (nodeList: OrganizationTreeNode[]) => {
      nodeList.forEach(node => {
        if (node.type === 'department') {
          departments.push(node)
        }
        if (node.children) {
          traverse(node.children)
        }
      })
    }
    traverse(nodes)
    return departments
  }

  const allDepartments = getAllDepartments(treeData)

  // Loading state
  if (isLoading) {
    return <Loading message="Loading departments..." />
  }

  // Error state
  if (error && !organizationTree) {
    return (
      <Alert 
        variant="error" 
        title="Failed to load departments" 
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
            <Users className="h-8 w-8" />
            Departments
          </h1>
          <p className="text-gray-600 mt-1">
            Manage department structure and organization
          </p>
        </div>
        <Button onClick={handleCreateDepartment} data-testid="create-department-btn">
          <Plus className="h-4 w-4 mr-2" />
          Create Department
        </Button>
      </div>

      {/* Statistics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white p-4 rounded-lg border">
          <div className="flex items-center">
            <Users className="h-8 w-8 text-blue-500" />
            <div className="ml-3">
              <p className="text-sm font-medium text-gray-500">Total Departments</p>
              <p className="text-2xl font-bold text-gray-900">{allDepartments.length}</p>
            </div>
          </div>
        </div>
        <div className="bg-white p-4 rounded-lg border">
          <div className="flex items-center">
            <Building2 className="h-8 w-8 text-green-500" />
            <div className="ml-3">
              <p className="text-sm font-medium text-gray-500">Active</p>
              <p className="text-2xl font-bold text-gray-900">
                {allDepartments.filter(d => d.is_active).length}
              </p>
            </div>
          </div>
        </div>
        <div className="bg-white p-4 rounded-lg border">
          <div className="flex items-center">
            <Users className="h-8 w-8 text-purple-500" />
            <div className="ml-3">
              <p className="text-sm font-medium text-gray-500">Total Members</p>
              <p className="text-2xl font-bold text-gray-900">
                {allDepartments.reduce((sum, d) => sum + d.user_count, 0)}
              </p>
            </div>
          </div>
        </div>
        <div className="bg-white p-4 rounded-lg border">
          <div className="flex items-center">
            <Building2 className="h-8 w-8 text-orange-500" />
            <div className="ml-3">
              <p className="text-sm font-medium text-gray-500">Organizations</p>
              <p className="text-2xl font-bold text-gray-900">{treeData.length}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Search and Filters */}
      <div className="flex flex-col sm:flex-row gap-4">
        <div className="flex-1">
          <Input
            placeholder="Search departments..."
            value={searchQuery}
            onChange={(e) => handleSearch(e.target.value)}
            leftIcon={<Search className="h-4 w-4" />}
          />
        </div>
        <Button
          variant="outline"
          onClick={() => setShowFilters(!showFilters)}
        >
          <Filter className="h-4 w-4 mr-2" />
          Filters
        </Button>
      </div>

      {/* Filter Panel */}
      {showFilters && (
        <div className="bg-gray-50 p-4 rounded-lg space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Select
              label="Department Type"
              value={filters.type || ''}
              onChange={(value) => handleFilterChange('type', Array.isArray(value) ? value[0] : value)}
              options={[
                { value: '', label: 'All Types' },
                ...DEPARTMENT_TYPES.map(type => ({ value: type.value, label: type.label }))
              ]}
            />
            <Select
              label="Status"
              value={filters.is_active !== undefined ? filters.is_active.toString() : ''}
              onChange={(value) => {
                const val = Array.isArray(value) ? value[0] : value
                const boolVal = val === '' ? undefined : val === 'true'
                setFilters(prev => ({ ...prev, is_active: boolVal }))
              }}
              options={[
                { value: '', label: 'All Status' },
                { value: 'true', label: 'Active' },
                { value: 'false', label: 'Inactive' }
              ]}
            />
            <div className="flex items-end">
              <Button
                variant="outline"
                onClick={() => {
                  setFilters({})
                  setSearchQuery('')
                }}
              >
                Clear Filters
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Department Tree */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <div className="bg-white rounded-lg border">
            <div className="p-4 border-b border-gray-200">
              <h3 className="text-lg font-medium text-gray-900">Department Hierarchy</h3>
              <p className="text-sm text-gray-500">
                Browse and manage your department structure
              </p>
            </div>
            <div className="p-4" data-testid="department-tree">
              {treeData.length > 0 ? (
                <div className="space-y-2">
                  {treeData.map((node) => (
                    <DepartmentTreeNode
                      key={node.id}
                      node={node}
                      level={0}
                      selectedNode={selectedNode}
                      onNodeSelect={handleNodeSelect}
                      onNodeExpand={handleNodeExpand}
                      onCreateDepartment={handleCreateDepartment}
                      onEditDepartment={handleEditDepartment}
                      onDeleteDepartment={handleDeleteDepartment}
                    />
                  ))}
                </div>
              ) : (
                <div className="text-center py-8">
                  <Users className="mx-auto h-12 w-12 text-gray-400" />
                  <h3 className="mt-2 text-sm font-medium text-gray-900">No departments found</h3>
                  <p className="mt-1 text-sm text-gray-500">
                    Get started by creating your first department.
                  </p>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Details Panel */}
        <div className="lg:col-span-1">
          {selectedNode ? (
            <div className="bg-white rounded-lg border p-6">
              <h3 className="text-lg font-medium text-gray-900 mb-4">
                Department Details
              </h3>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700">Name</label>
                  <p className="mt-1 text-sm text-gray-900">{selectedNode.name}</p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Code</label>
                  <p className="mt-1 text-sm text-gray-900">{selectedNode.code}</p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Members</label>
                  <p className="mt-1 text-sm text-gray-900">{selectedNode.user_count}</p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Status</label>
                  <p className={`mt-1 text-sm ${selectedNode.is_active ? 'text-green-600' : 'text-red-600'}`}>
                    {selectedNode.is_active ? 'Active' : 'Inactive'}
                  </p>
                </div>
              </div>

              <div className="mt-6 space-y-2">
                <Button 
                  className="w-full"
                  onClick={() => handleEditDepartment(selectedNode)}
                >
                  Edit Department
                </Button>
                <Button 
                  variant="destructive"
                  className="w-full"
                  onClick={() => handleDeleteDepartment(selectedNode)}
                >
                  Delete Department
                </Button>
              </div>
            </div>
          ) : (
            <div className="bg-white rounded-lg border p-6">
              <div className="text-center text-gray-500">
                <Users className="mx-auto h-12 w-12 text-gray-400" />
                <h3 className="mt-2 text-sm font-medium text-gray-900">No selection</h3>
                <p className="mt-1 text-sm text-gray-500">
                  Select a department to view details
                </p>
              </div>
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
          className={`toast-${toastMessage.type}`}
        />
      )}

      {/* Modals */}
      <DepartmentCreateModal
        isOpen={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        onSuccess={handleModalSuccess}
      />

      <DepartmentEditModal
        isOpen={showEditModal}
        onClose={() => {
          setShowEditModal(false)
          setEditingDepartment(null)
        }}
        onSuccess={handleModalSuccess}
        department={editingDepartment}
      />

      <DepartmentDeleteDialog
        isOpen={showDeleteDialog}
        onClose={() => {
          setShowDeleteDialog(false)
          setDeletingDepartment(null)
        }}
        onSuccess={handleModalSuccess}
        department={deletingDepartment}
      />
    </div>
  )
}