import React, { useState, useRef, useCallback, useEffect, useMemo } from 'react';
import { cn } from '@/lib/utils';

export interface Permission {
  id: string;
  name: string;
  description?: string;
  resource: string;
  action: string;
  level: 'read' | 'write' | 'delete' | 'admin' | 'owner';
  scope?: 'global' | 'organization' | 'project' | 'team' | 'personal';
  conditions?: Array<{
    field: string;
    operator: 'equals' | 'not_equals' | 'in' | 'not_in' | 'greater' | 'less' | 'contains';
    value: any;
  }>;
  metadata?: Record<string, any>;
  createdAt?: Date;
  updatedAt?: Date;
}

export interface Role {
  id: string;
  name: string;
  description?: string;
  type: 'system' | 'custom' | 'inherited';
  permissions: string[];
  parent?: string;
  level: number;
  color?: string;
  icon?: React.ReactNode;
  isDefault?: boolean;
  isActive?: boolean;
  userCount?: number;
  metadata?: Record<string, any>;
  createdAt?: Date;
  updatedAt?: Date;
}

export interface User {
  id: string;
  name: string;
  email: string;
  avatar?: string;
  roles: string[];
  directPermissions?: string[];
  status: 'active' | 'inactive' | 'pending' | 'suspended';
  lastLogin?: Date;
  metadata?: Record<string, any>;
  createdAt?: Date;
  updatedAt?: Date;
}

export interface Resource {
  id: string;
  name: string;
  type: string;
  path?: string;
  parent?: string;
  children?: string[];
  actions: string[];
  metadata?: Record<string, any>;
}

export interface PermissionMatrix {
  resources: Resource[];
  roles: Role[];
  permissions: Record<string, Record<string, boolean>>;
}

export interface AuditLog {
  id: string;
  userId: string;
  userName: string;
  action: 'grant' | 'revoke' | 'create_role' | 'update_role' | 'delete_role' | 'assign_role' | 'remove_role';
  target: string;
  targetType: 'permission' | 'role' | 'user';
  details: Record<string, any>;
  timestamp: Date;
  ipAddress?: string;
  userAgent?: string;
}

export interface PermissionUIProps {
  permissions?: Permission[];
  roles?: Role[];
  users?: User[];
  resources?: Resource[];
  auditLogs?: AuditLog[];
  currentUserId?: string;
  mode?: 'matrix' | 'tree' | 'list' | 'roles' | 'users' | 'audit';
  viewOnly?: boolean;
  enableBulkActions?: boolean;
  enableSearch?: boolean;
  enableFilters?: boolean;
  enableExport?: boolean;
  enableAudit?: boolean;
  showInherited?: boolean;
  showEffective?: boolean;
  groupByResource?: boolean;
  groupByRole?: boolean;
  maxDepth?: number;
  width?: number | string;
  height?: number | string;
  className?: string;
  style?: React.CSSProperties;
  onPermissionGrant?: (userId: string, permissionId: string) => void;
  onPermissionRevoke?: (userId: string, permissionId: string) => void;
  onRoleAssign?: (userId: string, roleId: string) => void;
  onRoleRemove?: (userId: string, roleId: string) => void;
  onRoleCreate?: (role: Omit<Role, 'id' | 'createdAt' | 'updatedAt'>) => void;
  onRoleUpdate?: (roleId: string, updates: Partial<Role>) => void;
  onRoleDelete?: (roleId: string) => void;
  onPermissionCreate?: (permission: Omit<Permission, 'id' | 'createdAt' | 'updatedAt'>) => void;
  onPermissionUpdate?: (permissionId: string, updates: Partial<Permission>) => void;
  onPermissionDelete?: (permissionId: string) => void;
  onUserStatusChange?: (userId: string, status: User['status']) => void;
  onBulkAction?: (action: string, targets: string[]) => void;
  onExport?: (format: 'csv' | 'json' | 'pdf') => void;
  onError?: (error: Error) => void;
  'data-testid'?: string;
}

export const PermissionUI: React.FC<PermissionUIProps> = ({
  permissions = [],
  roles = [],
  users = [],
  resources = [],
  auditLogs = [],
  currentUserId,
  mode = 'matrix',
  viewOnly = false,
  enableBulkActions = true,
  enableSearch = true,
  enableFilters = true,
  enableExport = true,
  enableAudit = true,
  showInherited = true,
  showEffective = true,
  groupByResource = false,
  groupByRole = false,
  maxDepth = 5,
  width = '100%',
  height = 600,
  className,
  style,
  onPermissionGrant,
  onPermissionRevoke,
  onRoleAssign,
  onRoleRemove,
  onRoleCreate,
  onRoleUpdate,
  onRoleDelete,
  onPermissionCreate,
  onPermissionUpdate,
  onPermissionDelete,
  onUserStatusChange,
  onBulkAction,
  onExport,
  onError,
  'data-testid': dataTestId = 'permission-ui'
}) => {
  const [selectedMode, setSelectedMode] = useState(mode);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedFilters, setSelectedFilters] = useState<{
    roles?: string[];
    permissions?: string[];
    resources?: string[];
    users?: string[];
    levels?: string[];
    scopes?: string[];
    status?: string[];
  }>({});
  const [selectedItems, setSelectedItems] = useState<string[]>([]);
  const [expandedNodes, setExpandedNodes] = useState<Set<string>>(new Set());
  const [showCreateRole, setShowCreateRole] = useState(false);
  const [showCreatePermission, setShowCreatePermission] = useState(false);
  const [editingRole, setEditingRole] = useState<Role | null>(null);
  const [editingPermission, setEditingPermission] = useState<Permission | null>(null);
  const [sortBy, setSortBy] = useState<'name' | 'type' | 'level' | 'created'>('name');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('asc');

  const containerRef = useRef<HTMLDivElement>(null);

  // Permission levels hierarchy
  const permissionLevels = {
    read: { order: 1, color: 'green', icon: '👁️' },
    write: { order: 2, color: 'blue', icon: '✏️' },
    delete: { order: 3, color: 'orange', icon: '🗑️' },
    admin: { order: 4, color: 'purple', icon: '⚙️' },
    owner: { order: 5, color: 'red', icon: '👑' }
  };

  // Get effective permissions for a user
  const getUserEffectivePermissions = useCallback((userId: string): Permission[] => {
    const user = users.find(u => u.id === userId);
    if (!user) return [];

    const effectivePermissions = new Set<string>();
    
    // Add direct permissions
    if (user.directPermissions) {
      user.directPermissions.forEach(permId => effectivePermissions.add(permId));
    }

    // Add role-based permissions
    user.roles.forEach(roleId => {
      const role = roles.find(r => r.id === roleId);
      if (role && role.isActive) {
        role.permissions.forEach(permId => effectivePermissions.add(permId));
        
        // Add inherited permissions from parent roles
        if (showInherited && role.parent) {
          const getParentPermissions = (parentRoleId: string, depth = 0) => {
            if (depth > maxDepth) return;
            const parentRole = roles.find(r => r.id === parentRoleId);
            if (parentRole && parentRole.isActive) {
              parentRole.permissions.forEach(permId => effectivePermissions.add(permId));
              if (parentRole.parent) {
                getParentPermissions(parentRole.parent, depth + 1);
              }
            }
          };
          getParentPermissions(role.parent);
        }
      }
    });

    return permissions.filter(p => effectivePermissions.has(p.id));
  }, [users, roles, permissions, showInherited, maxDepth]);

  // Check if user has specific permission
  const hasPermission = useCallback((userId: string, resource: string, action: string, level?: string): boolean => {
    const userPermissions = getUserEffectivePermissions(userId);
    
    return userPermissions.some(perm => {
      const matchesResource = perm.resource === resource || perm.resource === '*';
      const matchesAction = perm.action === action || perm.action === '*';
      const matchesLevel = !level || perm.level === level || 
        permissionLevels[perm.level]?.order >= (permissionLevels[level as keyof typeof permissionLevels]?.order || 0);
      
      return matchesResource && matchesAction && matchesLevel;
    });
  }, [getUserEffectivePermissions]);

  // Filter and sort data
  const filteredData = useMemo(() => {
    let filteredUsers = [...users];
    let filteredRoles = [...roles];
    let filteredPermissions = [...permissions];

    // Apply search
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      filteredUsers = filteredUsers.filter(user =>
        user.name.toLowerCase().includes(query) ||
        user.email.toLowerCase().includes(query)
      );
      filteredRoles = filteredRoles.filter(role =>
        role.name.toLowerCase().includes(query) ||
        role.description?.toLowerCase().includes(query)
      );
      filteredPermissions = filteredPermissions.filter(perm =>
        perm.name.toLowerCase().includes(query) ||
        perm.description?.toLowerCase().includes(query) ||
        perm.resource.toLowerCase().includes(query)
      );
    }

    // Apply filters
    if (selectedFilters.status?.length) {
      filteredUsers = filteredUsers.filter(user => selectedFilters.status!.includes(user.status));
    }

    if (selectedFilters.levels?.length) {
      filteredPermissions = filteredPermissions.filter(perm =>
        selectedFilters.levels!.includes(perm.level)
      );
    }

    if (selectedFilters.scopes?.length) {
      filteredPermissions = filteredPermissions.filter(perm =>
        perm.scope && selectedFilters.scopes!.includes(perm.scope)
      );
    }

    // Sort data
    const sortFn = (a: any, b: any) => {
      let comparison = 0;
      switch (sortBy) {
        case 'name':
          comparison = a.name.localeCompare(b.name);
          break;
        case 'type':
          comparison = (a.type || '').localeCompare(b.type || '');
          break;
        case 'level':
          comparison = (permissionLevels[a.level]?.order || 0) - (permissionLevels[b.level]?.order || 0);
          break;
        case 'created':
          comparison = (a.createdAt?.getTime() || 0) - (b.createdAt?.getTime() || 0);
          break;
      }
      return sortOrder === 'desc' ? -comparison : comparison;
    };

    filteredUsers.sort(sortFn);
    filteredRoles.sort(sortFn);
    filteredPermissions.sort(sortFn);

    return { users: filteredUsers, roles: filteredRoles, permissions: filteredPermissions };
  }, [users, roles, permissions, searchQuery, selectedFilters, sortBy, sortOrder]);

  // Handle item selection
  const handleItemSelect = useCallback((itemId: string, selected: boolean) => {
    setSelectedItems(prev =>
      selected ? [...prev, itemId] : prev.filter(id => id !== itemId)
    );
  }, []);

  // Handle bulk actions
  const handleBulkAction = useCallback((action: string) => {
    if (selectedItems.length === 0) return;
    
    try {
      onBulkAction?.(action, selectedItems);
      setSelectedItems([]);
    } catch (error) {
      onError?.(error as Error);
    }
  }, [selectedItems, onBulkAction, onError]);

  // Toggle node expansion
  const toggleNodeExpansion = useCallback((nodeId: string) => {
    setExpandedNodes(prev => {
      const newSet = new Set(prev);
      if (newSet.has(nodeId)) {
        newSet.delete(nodeId);
      } else {
        newSet.add(nodeId);
      }
      return newSet;
    });
  }, []);

  // Render toolbar
  const renderToolbar = () => (
    <div className="flex items-center justify-between p-4 border-b border-gray-200 bg-gray-50" data-testid="permission-toolbar">
      <div className="flex items-center space-x-4">
        {/* Mode selector */}
        <div className="flex space-x-1">
          {['matrix', 'tree', 'list', 'roles', 'users', 'audit'].map(modeOption => (
            <button
              key={modeOption}
              className={cn(
                "px-3 py-1 text-sm rounded border transition-colors",
                selectedMode === modeOption
                  ? "bg-blue-500 text-white border-blue-500"
                  : "bg-white text-gray-700 border-gray-300 hover:bg-gray-50"
              )}
              onClick={() => setSelectedMode(modeOption as any)}
              data-testid={`mode-${modeOption}`}
            >
              {modeOption.charAt(0).toUpperCase() + modeOption.slice(1)}
            </button>
          ))}
        </div>

        {/* Search */}
        {enableSearch && (
          <div className="relative">
            <input
              type="text"
              placeholder="Search..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-8 pr-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
              data-testid="search-input"
            />
            <div className="absolute left-2 top-2.5 text-gray-400">🔍</div>
          </div>
        )}
      </div>

      <div className="flex items-center space-x-2">
        {/* Action buttons */}
        {!viewOnly && (
          <>
            <button
              className="px-3 py-2 text-sm bg-green-500 text-white rounded hover:bg-green-600"
              onClick={() => setShowCreateRole(true)}
              data-testid="create-role-button"
            >
              + Role
            </button>
            <button
              className="px-3 py-2 text-sm bg-blue-500 text-white rounded hover:bg-blue-600"
              onClick={() => setShowCreatePermission(true)}
              data-testid="create-permission-button"
            >
              + Permission
            </button>
          </>
        )}

        {/* Export */}
        {enableExport && (
          <button
            className="px-3 py-2 text-sm bg-purple-500 text-white rounded hover:bg-purple-600"
            onClick={() => onExport?.('json')}
            data-testid="export-button"
          >
            Export
          </button>
        )}

        {/* Bulk actions */}
        {enableBulkActions && selectedItems.length > 0 && (
          <div className="relative">
            <select
              onChange={(e) => e.target.value && handleBulkAction(e.target.value)}
              className="px-3 py-2 text-sm border border-gray-300 rounded"
              defaultValue=""
              data-testid="bulk-actions-select"
            >
              <option value="">Bulk Actions ({selectedItems.length})</option>
              <option value="activate">Activate</option>
              <option value="deactivate">Deactivate</option>
              <option value="delete">Delete</option>
            </select>
          </div>
        )}
      </div>
    </div>
  );

  // Render permission matrix
  const renderMatrix = () => (
    <div className="p-4" data-testid="permission-matrix">
      <div className="overflow-auto max-h-96">
        <table className="w-full border border-gray-200 rounded">
          <thead className="bg-gray-50 sticky top-0">
            <tr>
              <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase border-b">
                User / Role
              </th>
              {resources.map(resource => (
                <th
                  key={resource.id}
                  className="px-3 py-2 text-center text-xs font-medium text-gray-500 uppercase border-b border-l"
                >
                  {resource.name}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {filteredData.users.map(user => (
              <tr key={user.id} className="hover:bg-gray-50">
                <td className="px-3 py-2 text-sm font-medium text-gray-900 border-r">
                  <div className="flex items-center space-x-2">
                    {user.avatar ? (
                      <img src={user.avatar} alt="" className="w-6 h-6 rounded-full" />
                    ) : (
                      <div className="w-6 h-6 bg-gray-300 rounded-full flex items-center justify-center text-xs">
                        {user.name.charAt(0)}
                      </div>
                    )}
                    <span>{user.name}</span>
                    <span className={cn(
                      "px-1.5 py-0.5 text-xs rounded-full",
                      user.status === 'active' && "bg-green-100 text-green-800",
                      user.status === 'inactive' && "bg-gray-100 text-gray-800",
                      user.status === 'suspended' && "bg-red-100 text-red-800"
                    )}>
                      {user.status}
                    </span>
                  </div>
                </td>
                {resources.map(resource => (
                  <td key={resource.id} className="px-3 py-2 text-center border-l">
                    <div className="flex justify-center space-x-1">
                      {resource.actions.map(action => {
                        const hasAccess = hasPermission(user.id, resource.id, action);
                        return (
                          <button
                            key={action}
                            className={cn(
                              "w-6 h-6 rounded text-xs font-medium transition-colors",
                              hasAccess
                                ? "bg-green-500 text-white"
                                : "bg-gray-200 text-gray-500 hover:bg-gray-300"
                            )}
                            onClick={() => {
                              if (!viewOnly) {
                                // Toggle permission
                                const permissionId = `${resource.id}-${action}`;
                                if (hasAccess) {
                                  onPermissionRevoke?.(user.id, permissionId);
                                } else {
                                  onPermissionGrant?.(user.id, permissionId);
                                }
                              }
                            }}
                            title={`${action} on ${resource.name}`}
                            disabled={viewOnly}
                            data-testid={`permission-${user.id}-${resource.id}-${action}`}
                          >
                            {action.charAt(0).toUpperCase()}
                          </button>
                        );
                      })}
                    </div>
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );

  // Render roles list
  const renderRolesList = () => (
    <div className="p-4" data-testid="roles-list">
      {enableBulkActions && (
        <div className="mb-4">
          <label className="flex items-center text-sm">
            <input
              type="checkbox"
              checked={selectedItems.length === filteredData.roles.length}
              onChange={(e) => {
                if (e.target.checked) {
                  setSelectedItems(filteredData.roles.map(r => r.id));
                } else {
                  setSelectedItems([]);
                }
              }}
              className="mr-2"
              data-testid="select-all-roles"
            />
            Select all roles
          </label>
        </div>
      )}
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {filteredData.roles.map(role => (
          <div
            key={role.id}
            className={cn(
              "p-4 border border-gray-200 rounded-lg hover:shadow-md transition-shadow",
              selectedItems.includes(role.id) && "ring-2 ring-blue-500"
            )}
            data-testid={`role-card-${role.id}`}
          >
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center space-x-2">
                {enableBulkActions && (
                  <input
                    type="checkbox"
                    checked={selectedItems.includes(role.id)}
                    onChange={(e) => handleItemSelect(role.id, e.target.checked)}
                    data-testid={`role-checkbox-${role.id}`}
                  />
                )}
                <div
                  className="w-3 h-3 rounded-full"
                  style={{ backgroundColor: role.color || '#6B7280' }}
                />
                <h3 className="font-medium">{role.name}</h3>
              </div>
              <div className="flex items-center space-x-1">
                <span className={cn(
                  "px-2 py-1 text-xs rounded",
                  role.type === 'system' && "bg-blue-100 text-blue-800",
                  role.type === 'custom' && "bg-green-100 text-green-800",
                  role.type === 'inherited' && "bg-gray-100 text-gray-800"
                )}>
                  {role.type}
                </span>
                {!viewOnly && (
                  <button
                    className="p-1 text-gray-400 hover:text-gray-600"
                    onClick={() => setEditingRole(role)}
                    data-testid={`edit-role-${role.id}`}
                  >
                    ✏️
                  </button>
                )}
              </div>
            </div>
            
            {role.description && (
              <p className="text-sm text-gray-600 mb-3">{role.description}</p>
            )}
            
            <div className="flex items-center justify-between text-xs text-gray-500">
              <span>{role.permissions.length} permissions</span>
              <span>{role.userCount || 0} users</span>
              <span className={cn(
                "px-1.5 py-0.5 rounded-full",
                role.isActive ? "bg-green-100 text-green-800" : "bg-red-100 text-red-800"
              )}>
                {role.isActive ? 'Active' : 'Inactive'}
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );

  // Render users list
  const renderUsersList = () => (
    <div className="p-4" data-testid="users-list">
      <div className="overflow-x-auto">
        <table className="w-full border border-gray-200 rounded">
          <thead className="bg-gray-50">
            <tr>
              {enableBulkActions && (
                <th className="px-3 py-2 text-left">
                  <input
                    type="checkbox"
                    checked={selectedItems.length === filteredData.users.length}
                    onChange={(e) => {
                      if (e.target.checked) {
                        setSelectedItems(filteredData.users.map(u => u.id));
                      } else {
                        setSelectedItems([]);
                      }
                    }}
                    data-testid="select-all-users"
                  />
                </th>
              )}
              <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">User</th>
              <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">Roles</th>
              <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">Permissions</th>
              <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
              <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">Last Login</th>
              {!viewOnly && (
                <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">Actions</th>
              )}
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {filteredData.users.map(user => {
              const userRoles = roles.filter(r => user.roles.includes(r.id));
              const effectivePermissions = getUserEffectivePermissions(user.id);
              
              return (
                <tr key={user.id} className="hover:bg-gray-50" data-testid={`user-row-${user.id}`}>
                  {enableBulkActions && (
                    <td className="px-3 py-2">
                      <input
                        type="checkbox"
                        checked={selectedItems.includes(user.id)}
                        onChange={(e) => handleItemSelect(user.id, e.target.checked)}
                        data-testid={`user-checkbox-${user.id}`}
                      />
                    </td>
                  )}
                  <td className="px-3 py-2">
                    <div className="flex items-center space-x-3">
                      {user.avatar ? (
                        <img src={user.avatar} alt="" className="w-8 h-8 rounded-full" />
                      ) : (
                        <div className="w-8 h-8 bg-gray-300 rounded-full flex items-center justify-center text-sm">
                          {user.name.charAt(0)}
                        </div>
                      )}
                      <div>
                        <div className="font-medium">{user.name}</div>
                        <div className="text-sm text-gray-500">{user.email}</div>
                      </div>
                    </div>
                  </td>
                  <td className="px-3 py-2">
                    <div className="flex flex-wrap gap-1">
                      {userRoles.map(role => (
                        <span
                          key={role.id}
                          className="px-2 py-1 text-xs bg-blue-100 text-blue-800 rounded"
                        >
                          {role.name}
                        </span>
                      ))}
                    </div>
                  </td>
                  <td className="px-3 py-2">
                    <span className="text-sm text-gray-600">
                      {effectivePermissions.length} permission{effectivePermissions.length !== 1 ? 's' : ''}
                    </span>
                  </td>
                  <td className="px-3 py-2">
                    <span className={cn(
                      "px-2 py-1 text-xs rounded-full",
                      user.status === 'active' && "bg-green-100 text-green-800",
                      user.status === 'inactive' && "bg-gray-100 text-gray-800",
                      user.status === 'pending' && "bg-yellow-100 text-yellow-800",
                      user.status === 'suspended' && "bg-red-100 text-red-800"
                    )}>
                      {user.status}
                    </span>
                  </td>
                  <td className="px-3 py-2 text-sm text-gray-600">
                    {user.lastLogin ? user.lastLogin.toLocaleDateString() : 'Never'}
                  </td>
                  {!viewOnly && (
                    <td className="px-3 py-2">
                      <div className="flex space-x-2">
                        <button
                          className="text-blue-600 hover:text-blue-800 text-sm"
                          data-testid={`edit-user-${user.id}`}
                        >
                          Edit
                        </button>
                        <select
                          value={user.status}
                          onChange={(e) => onUserStatusChange?.(user.id, e.target.value as User['status'])}
                          className="text-xs border border-gray-300 rounded px-1 py-0.5"
                          data-testid={`status-select-${user.id}`}
                        >
                          <option value="active">Active</option>
                          <option value="inactive">Inactive</option>
                          <option value="pending">Pending</option>
                          <option value="suspended">Suspended</option>
                        </select>
                      </div>
                    </td>
                  )}
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );

  // Render audit logs
  const renderAuditLogs = () => (
    <div className="p-4" data-testid="audit-logs">
      <div className="overflow-x-auto">
        <table className="w-full border border-gray-200 rounded">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">Timestamp</th>
              <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">User</th>
              <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">Action</th>
              <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">Target</th>
              <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">Details</th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {auditLogs.map(log => (
              <tr key={log.id} className="hover:bg-gray-50" data-testid={`audit-log-${log.id}`}>
                <td className="px-3 py-2 text-sm text-gray-600">
                  {log.timestamp.toLocaleString()}
                </td>
                <td className="px-3 py-2 text-sm">
                  {log.userName}
                </td>
                <td className="px-3 py-2">
                  <span className={cn(
                    "px-2 py-1 text-xs rounded",
                    log.action.includes('grant') && "bg-green-100 text-green-800",
                    log.action.includes('revoke') && "bg-red-100 text-red-800",
                    log.action.includes('create') && "bg-blue-100 text-blue-800",
                    log.action.includes('update') && "bg-yellow-100 text-yellow-800",
                    log.action.includes('delete') && "bg-red-100 text-red-800"
                  )}>
                    {log.action.replace('_', ' ')}
                  </span>
                </td>
                <td className="px-3 py-2 text-sm">
                  <span className="font-medium">{log.target}</span>
                  <span className="text-gray-500 ml-1">({log.targetType})</span>
                </td>
                <td className="px-3 py-2 text-sm text-gray-600">
                  {JSON.stringify(log.details)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );

  // Render main content based on selected mode
  const renderContent = () => {
    switch (selectedMode) {
      case 'matrix':
        return renderMatrix();
      case 'roles':
        return renderRolesList();
      case 'users':
        return renderUsersList();
      case 'audit':
        return enableAudit ? renderAuditLogs() : <div>Audit logs not enabled</div>;
      default:
        return renderMatrix();
    }
  };

  return (
    <div
      ref={containerRef}
      className={cn(
        "bg-white border border-gray-200 rounded-lg shadow-lg overflow-hidden",
        className
      )}
      style={{ width, height, ...style }}
      data-testid={dataTestId}
    >
      {renderToolbar()}
      
      <div className="flex-1 overflow-auto">
        {renderContent()}
      </div>

      {/* Summary footer */}
      <div className="p-3 border-t border-gray-200 bg-gray-50 text-sm text-gray-600" data-testid="permission-summary">
        <div className="flex items-center justify-between">
          <div className="flex space-x-4">
            <span>{filteredData.users.length} users</span>
            <span>{filteredData.roles.length} roles</span>
            <span>{filteredData.permissions.length} permissions</span>
          </div>
          {selectedItems.length > 0 && (
            <span>{selectedItems.length} selected</span>
          )}
        </div>
      </div>
    </div>
  );
};

export default PermissionUI;