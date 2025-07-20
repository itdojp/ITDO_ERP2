import { useState } from 'react'
import { ChevronDown, ChevronRight, Building2, Users, Plus, Edit, Move, Trash2 } from 'lucide-react'
import Button from './ui/Button'
import { OrganizationTreeNode } from '../types/organization'
import { cn } from '../lib/utils'

interface OrganizationTreeViewProps {
  treeData: OrganizationTreeNode[]
  selectedNode?: OrganizationTreeNode | null
  onNodeSelect?: (node: OrganizationTreeNode) => void
  onNodeExpand?: (node: OrganizationTreeNode) => void
  onCreateOrganization?: () => void
  onCreateDepartment?: (parentNode: OrganizationTreeNode) => void
  onEditNode?: (node: OrganizationTreeNode) => void
  onMoveNode?: (node: OrganizationTreeNode) => void
  onDeleteNode?: (node: OrganizationTreeNode) => void
  className?: string
}

interface TreeNodeProps {
  node: OrganizationTreeNode
  level: number
  selectedNode?: OrganizationTreeNode | null
  onNodeSelect?: (node: OrganizationTreeNode) => void
  onNodeExpand?: (node: OrganizationTreeNode) => void
  onCreateDepartment?: (parentNode: OrganizationTreeNode) => void
  onEditNode?: (node: OrganizationTreeNode) => void
  onMoveNode?: (node: OrganizationTreeNode) => void
  onDeleteNode?: (node: OrganizationTreeNode) => void
}

function TreeNode({ 
  node, 
  level, 
  selectedNode, 
  onNodeSelect, 
  onNodeExpand, 
  onCreateDepartment,
  onEditNode,
  onMoveNode,
  onDeleteNode
}: TreeNodeProps) {
  const [showActions, setShowActions] = useState(false)
  const hasChildren = node.children && node.children.length > 0
  const isSelected = selectedNode?.id === node.id
  const isRoot = level === 0 && node.type === 'organization'

  const handleToggleExpand = (e: React.MouseEvent) => {
    e.stopPropagation()
    if (hasChildren && onNodeExpand) {
      onNodeExpand(node)
    }
  }

  const handleNodeClick = () => {
    if (onNodeSelect) {
      onNodeSelect(node)
    }
  }

  const getNodeIcon = () => {
    if (node.type === 'organization') {
      return <Building2 className="h-4 w-4" />
    }
    return <Users className="h-4 w-4" />
  }

  const getNodeClasses = () => {
    const baseClasses = cn(
      'org-node',
      'flex items-center p-2 rounded-lg cursor-pointer transition-colors hover:bg-gray-100',
      isSelected && 'bg-blue-50 border border-blue-200',
      isRoot && 'org-node-root',
      level > 0 && 'org-node-child',
      !node.is_active && 'opacity-50'
    )
    return baseClasses
  }

  return (
    <div>
      <div
        className={getNodeClasses()}
        style={{ marginLeft: `${level * 20}px` }}
        onClick={handleNodeClick}
        onMouseEnter={() => setShowActions(true)}
        onMouseLeave={() => setShowActions(false)}
      >
        {/* Expand/Collapse Button */}
        <div className="w-6 flex justify-center">
          {hasChildren ? (
            <button
              onClick={handleToggleExpand}
              aria-label={node.expanded ? 'Collapse' : 'Expand'}
              className="p-1 rounded hover:bg-gray-200 transition-colors"
            >
              {node.expanded ? (
                <ChevronDown className="h-3 w-3" />
              ) : (
                <ChevronRight className="h-3 w-3" />
              )}
            </button>
          ) : (
            <div className="w-5" />
          )}
        </div>

        {/* Node Icon */}
        <div className="mr-2 text-gray-600">
          {getNodeIcon()}
        </div>

        {/* Node Content */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center justify-between">
            <div className="flex-1 min-w-0">
              <div className="font-medium text-gray-900 truncate">
                {node.name}
              </div>
              <div className="text-xs text-gray-500 flex items-center gap-2">
                <span>{node.code}</span>
                <span>•</span>
                <span>{node.user_count} users</span>
                {!node.is_active && (
                  <>
                    <span>•</span>
                    <span className="text-red-600">Inactive</span>
                  </>
                )}
              </div>
            </div>

            {/* Action Buttons */}
            {showActions && isSelected && (
              <div className="flex items-center gap-1 ml-2">
                {node.type === 'organization' && onCreateDepartment && (
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={(e) => {
                      e.stopPropagation()
                      onCreateDepartment(node)
                    }}
                    aria-label="Add Department"
                    className="h-6 w-6 p-0"
                  >
                    <Plus className="h-3 w-3" />
                  </Button>
                )}
                
                {onEditNode && (
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={(e) => {
                      e.stopPropagation()
                      onEditNode(node)
                    }}
                    aria-label="Edit"
                    className="h-6 w-6 p-0"
                  >
                    <Edit className="h-3 w-3" />
                  </Button>
                )}

                {level > 0 && onMoveNode && (
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={(e) => {
                      e.stopPropagation()
                      onMoveNode(node)
                    }}
                    aria-label="Move"
                    className="h-6 w-6 p-0"
                  >
                    <Move className="h-3 w-3" />
                  </Button>
                )}

                {onDeleteNode && (
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={(e) => {
                      e.stopPropagation()
                      onDeleteNode(node)
                    }}
                    aria-label="Delete"
                    className="h-6 w-6 p-0 text-red-600 hover:text-red-700"
                  >
                    <Trash2 className="h-3 w-3" />
                  </Button>
                )}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Children */}
      {hasChildren && node.expanded && (
        <div className="ml-4">
          {node.children.map((child) => (
            <TreeNode
              key={child.id}
              node={child}
              level={level + 1}
              selectedNode={selectedNode}
              onNodeSelect={onNodeSelect}
              onNodeExpand={onNodeExpand}
              onCreateDepartment={onCreateDepartment}
              onEditNode={onEditNode}
              onMoveNode={onMoveNode}
              onDeleteNode={onDeleteNode}
            />
          ))}
        </div>
      )}
    </div>
  )
}

export function OrganizationTreeView({
  treeData,
  selectedNode,
  onNodeSelect,
  onNodeExpand,
  onCreateOrganization,
  onCreateDepartment,
  onEditNode,
  onMoveNode,
  onDeleteNode,
  className
}: OrganizationTreeViewProps) {
  if (!treeData || treeData.length === 0) {
    return (
      <div className={cn('org-tree-view bg-white rounded-lg border p-6', className)}>
        <div className="text-center">
          <Building2 className="mx-auto h-12 w-12 text-gray-400" />
          <h3 className="mt-2 text-sm font-medium text-gray-900">No organizations</h3>
          <p className="mt-1 text-sm text-gray-500">
            Get started by creating your first organization.
          </p>
          {onCreateOrganization && (
            <div className="mt-6">
              <Button onClick={onCreateOrganization}>
                <Plus className="h-4 w-4 mr-2" />
                Create Organization
              </Button>
            </div>
          )}
        </div>
      </div>
    )
  }

  return (
    <div className={cn('org-tree-view bg-white rounded-lg border', className)}>
      {/* Header */}
      <div className="p-4 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-medium text-gray-900">Organization Structure</h3>
            <p className="text-sm text-gray-500">
              Manage your organization hierarchy and departments
            </p>
          </div>
          {onCreateOrganization && (
            <Button onClick={onCreateOrganization}>
              <Plus className="h-4 w-4 mr-2" />
              Create Organization
            </Button>
          )}
        </div>
      </div>

      {/* Tree Content */}
      <div className="p-4">
        <div className="space-y-1">
          {treeData.map((node) => (
            <TreeNode
              key={node.id}
              node={node}
              level={0}
              selectedNode={selectedNode}
              onNodeSelect={onNodeSelect}
              onNodeExpand={onNodeExpand}
              onCreateDepartment={onCreateDepartment}
              onEditNode={onEditNode}
              onMoveNode={onMoveNode}
              onDeleteNode={onDeleteNode}
            />
          ))}
        </div>
      </div>

      {/* Selected Node Info */}
      {selectedNode && (
        <div className="border-t border-gray-200 p-4 bg-gray-50">
          <h4 className="text-sm font-medium text-gray-900 mb-2">Selected {selectedNode.type}</h4>
          <div className="text-sm text-gray-600 space-y-1">
            <div><span className="font-medium">Name:</span> {selectedNode.name}</div>
            <div><span className="font-medium">Code:</span> {selectedNode.code}</div>
            <div><span className="font-medium">Users:</span> {selectedNode.user_count}</div>
            <div><span className="font-medium">Status:</span> {selectedNode.is_active ? 'Active' : 'Inactive'}</div>
            {selectedNode.children && selectedNode.children.length > 0 && (
              <div><span className="font-medium">Children:</span> {selectedNode.children.length}</div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}

export default OrganizationTreeView