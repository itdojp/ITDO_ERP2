import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Search, Filter, Building2, Plus } from 'lucide-react'
import Button from '../components/ui/Button'
import Input from '../components/ui/Input'
import Select from '../components/ui/Select'
import Loading from '../components/ui/Loading'
import Alert from '../components/ui/Alert'
import Toast from '../components/ui/Toast'
import OrganizationTreeView from '../components/OrganizationTreeView'
import { organizationApiService, organizationQueryKeys } from '../services/organizationApi'
import { OrganizationTreeNode, OrganizationFilters, INDUSTRY_OPTIONS } from '../types/organization'

export function OrganizationListPage() {
  // State management
  const [filters, setFilters] = useState<OrganizationFilters>({})
  const [selectedNode, setSelectedNode] = useState<OrganizationTreeNode | null>(null)
  const [showFilters, setShowFilters] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')
  const [toastMessage, setToastMessage] = useState<{ type: 'success' | 'error'; message: string } | null>(null)
  const [treeData, setTreeData] = useState<OrganizationTreeNode[]>([])

  // Query for organization tree
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

  const handleFilterChange = (key: keyof OrganizationFilters, value: string) => {
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

  const handleCreateOrganization = () => {
    setToastMessage({ type: 'success', message: 'Create Organization modal would open here' })
  }

  const handleCreateDepartment = (parentNode: OrganizationTreeNode) => {
    setToastMessage({ type: 'success', message: `Add Department modal would open for ${parentNode.name}` })
  }

  const handleEditNode = (node: OrganizationTreeNode) => {
    setToastMessage({ type: 'success', message: `Edit ${node.type} modal would open for ${node.name}` })
  }

  const handleMoveNode = (node: OrganizationTreeNode) => {
    setToastMessage({ type: 'success', message: `Move Department modal would open for ${node.name}` })
  }

  const handleDeleteNode = (node: OrganizationTreeNode) => {
    if (window.confirm(`Are you sure you want to delete ${node.name}?`)) {
      setToastMessage({ type: 'success', message: `${node.name} would be deleted` })
    }
  }

  // Loading state
  if (isLoading) {
    return <Loading message="Loading organization structure..." />
  }

  // Error state
  if (error && !organizationTree) {
    return (
      <Alert 
        variant="error" 
        title="Failed to load organizations" 
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
            <Building2 className="h-8 w-8" />
            Organization Management
          </h1>
          <p className="text-gray-600 mt-1">
            Manage your organization structure and departments
          </p>
        </div>
        <Button onClick={handleCreateOrganization}>
          <Plus className="h-4 w-4 mr-2" />
          Create Organization
        </Button>
      </div>

      {/* Search and Filters */}
      <div className="flex flex-col sm:flex-row gap-4">
        <div className="flex-1">
          <Input
            placeholder="Search organizations..."
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
              label="Industry"
              value={filters.industry || ''}
              onChange={(value) => handleFilterChange('industry', Array.isArray(value) ? value[0] : value)}
              options={[
                { value: '', label: 'All Industries' },
                ...INDUSTRY_OPTIONS.map(option => ({ value: option.value, label: option.label }))
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

      {/* Organization Tree */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <OrganizationTreeView
            treeData={treeData}
            selectedNode={selectedNode}
            onNodeSelect={handleNodeSelect}
            onNodeExpand={handleNodeExpand}
            onCreateOrganization={handleCreateOrganization}
            onCreateDepartment={handleCreateDepartment}
            onEditNode={handleEditNode}
            onMoveNode={handleMoveNode}
            onDeleteNode={handleDeleteNode}
          />
        </div>

        {/* Details Panel */}
        <div className="lg:col-span-1">
          {selectedNode ? (
            <div className="bg-white rounded-lg border p-6">
              <h3 className="text-lg font-medium text-gray-900 mb-4">
                {selectedNode.type === 'organization' ? 'Organization' : 'Department'} Details
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
                  <label className="block text-sm font-medium text-gray-700">User Count</label>
                  <p className="mt-1 text-sm text-gray-900">{selectedNode.user_count}</p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Status</label>
                  <p className={`mt-1 text-sm ${selectedNode.is_active ? 'text-green-600' : 'text-red-600'}`}>
                    {selectedNode.is_active ? 'Active' : 'Inactive'}
                  </p>
                </div>
                {selectedNode.children && selectedNode.children.length > 0 && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Children</label>
                    <p className="mt-1 text-sm text-gray-900">{selectedNode.children.length}</p>
                  </div>
                )}
              </div>

              <div className="mt-6 space-y-2">
                <Button 
                  className="w-full"
                  onClick={() => handleEditNode(selectedNode)}
                >
                  Edit {selectedNode.type === 'organization' ? 'Organization' : 'Department'}
                </Button>
                
                {selectedNode.type === 'organization' && (
                  <Button 
                    variant="outline"
                    className="w-full"
                    onClick={() => handleCreateDepartment(selectedNode)}
                  >
                    Add Department
                  </Button>
                )}

                {selectedNode.type === 'department' && (
                  <Button 
                    variant="outline"
                    className="w-full"
                    onClick={() => handleMoveNode(selectedNode)}
                  >
                    Move Department
                  </Button>
                )}

                <Button 
                  variant="destructive"
                  className="w-full"
                  onClick={() => handleDeleteNode(selectedNode)}
                >
                  Delete {selectedNode.type === 'organization' ? 'Organization' : 'Department'}
                </Button>
              </div>
            </div>
          ) : (
            <div className="bg-white rounded-lg border p-6">
              <div className="text-center text-gray-500">
                <Building2 className="mx-auto h-12 w-12 text-gray-400" />
                <h3 className="mt-2 text-sm font-medium text-gray-900">No selection</h3>
                <p className="mt-1 text-sm text-gray-500">
                  Select an organization or department to view details
                </p>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Search Results Count */}
      {searchQuery && (
        <div className="search-results-count text-sm text-gray-600">
          {treeData.length} result{treeData.length !== 1 ? 's' : ''} found
        </div>
      )}

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
    </div>
  )
}