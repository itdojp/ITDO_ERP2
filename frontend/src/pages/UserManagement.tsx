import React, { useState, useCallback, useMemo, useRef } from 'react';
import { cn } from '@/lib/utils';
import { EnhancedDataTable } from '@/components/ui/EnhancedDataTable';
import { FormBuilder } from '@/components/ui/FormBuilder';
import { PermissionUI } from '@/components/ui/PermissionUI';
import { AnalyticsDashboard } from '@/components/ui/AnalyticsDashboard';

export interface User {
  id: string;
  firstName: string;
  lastName: string;
  email: string;
  phone?: string;
  avatar?: string;
  department: string;
  position: string;
  employeeId: string;
  startDate: Date;
  status: 'active' | 'inactive' | 'pending' | 'suspended';
  roles: string[];
  permissions: string[];
  manager?: string;
  salary?: number;
  lastLogin?: Date;
  createdAt: Date;
  updatedAt: Date;
  metadata?: Record<string, any>;
}

export interface UserFormData extends Omit<User, 'id' | 'createdAt' | 'updatedAt'> {
  password?: string;
  confirmPassword?: string;
}

export interface UserManagementProps {
  users?: User[];
  departments?: Array<{ value: string; label: string }>;
  positions?: Array<{ value: string; label: string }>;
  roles?: Array<{ value: string; label: string }>;
  permissions?: Array<{ value: string; label: string }>;
  managers?: Array<{ value: string; label: string }>;
  enableBulkActions?: boolean;
  enableExport?: boolean;
  enableImport?: boolean;
  enableAudit?: boolean;
  enableAnalytics?: boolean;
  pageSize?: number;
  maxUsers?: number;
  readOnly?: boolean;
  className?: string;
  onUserCreate?: (user: UserFormData) => Promise<User>;
  onUserUpdate?: (id: string, updates: Partial<UserFormData>) => Promise<User>;
  onUserDelete?: (id: string | string[]) => Promise<void>;
  onUserStatusChange?: (id: string, status: User['status']) => Promise<void>;
  onRoleAssign?: (userId: string, roleId: string) => Promise<void>;
  onRoleRemove?: (userId: string, roleId: string) => Promise<void>;
  onPermissionGrant?: (userId: string, permissionId: string) => Promise<void>;
  onPermissionRevoke?: (userId: string, permissionId: string) => Promise<void>;
  onExport?: (format: 'csv' | 'xlsx' | 'pdf') => Promise<void>;
  onImport?: (file: File) => Promise<{ success: number; errors: string[] }>;
  onError?: (error: Error) => void;
  'data-testid'?: string;
}

export const UserManagement: React.FC<UserManagementProps> = ({
  users = [],
  departments = [],
  positions = [],
  roles = [],
  permissions = [],
  managers = [],
  enableBulkActions = true,
  enableExport = true,
  enableImport = true,
  enableAudit = true,
  enableAnalytics = true,
  pageSize = 25,
  maxUsers = 10000,
  readOnly = false,
  className,
  onUserCreate,
  onUserUpdate,
  onUserDelete,
  onUserStatusChange,
  onRoleAssign,
  onRoleRemove,
  onPermissionGrant,
  onPermissionRevoke,
  onExport,
  onImport,
  onError,
  'data-testid': dataTestId = 'user-management'
}) => {
  const [activeTab, setActiveTab] = useState<'users' | 'permissions' | 'analytics'>('users');
  const [selectedUsers, setSelectedUsers] = useState<string[]>([]);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [showEditForm, setShowEditForm] = useState(false);
  const [editingUser, setEditingUser] = useState<User | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [filters, setFilters] = useState<{
    department?: string;
    position?: string;
    status?: string;
    role?: string;
  }>({});
  const [isLoading, setIsLoading] = useState(false);
  const [showImportDialog, setShowImportDialog] = useState(false);

  const fileInputRef = useRef<HTMLInputElement>(null);

  // Filter users based on search and filters
  const filteredUsers = useMemo(() => {
    let filtered = [...users];

    // Apply search
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(user =>
        user.firstName.toLowerCase().includes(query) ||
        user.lastName.toLowerCase().includes(query) ||
        user.email.toLowerCase().includes(query) ||
        user.employeeId.toLowerCase().includes(query) ||
        user.department.toLowerCase().includes(query) ||
        user.position.toLowerCase().includes(query)
      );
    }

    // Apply filters
    if (filters.department) {
      filtered = filtered.filter(user => user.department === filters.department);
    }

    if (filters.position) {
      filtered = filtered.filter(user => user.position === filters.position);
    }

    if (filters.status) {
      filtered = filtered.filter(user => user.status === filters.status);
    }

    if (filters.role) {
      filtered = filtered.filter(user => user.roles.includes(filters.role));
    }

    return filtered;
  }, [users, searchQuery, filters]);

  // User form fields configuration
  const userFormFields = useMemo(() => [
    {
      id: 'personal-section',
      type: 'section' as const,
      label: 'Personal Information',
      description: 'Basic personal details'
    },
    {
      id: 'firstName',
      type: 'text' as const,
      label: 'First Name',
      placeholder: 'Enter first name',
      required: true,
      validation: { minLength: 2, maxLength: 50 }
    },
    {
      id: 'lastName',
      type: 'text' as const,
      label: 'Last Name',
      placeholder: 'Enter last name',
      required: true,
      validation: { minLength: 2, maxLength: 50 }
    },
    {
      id: 'email',
      type: 'email' as const,
      label: 'Email Address',
      placeholder: 'user@company.com',
      required: true,
      validation: { email: true }
    },
    {
      id: 'phone',
      type: 'tel' as const,
      label: 'Phone Number',
      placeholder: '+1 (555) 123-4567'
    },
    {
      id: 'employment-section',
      type: 'section' as const,
      label: 'Employment Information',
      description: 'Job-related details'
    },
    {
      id: 'employeeId',
      type: 'text' as const,
      label: 'Employee ID',
      placeholder: 'EMP001',
      required: true,
      validation: { pattern: '^[A-Z0-9]+$' }
    },
    {
      id: 'department',
      type: 'select' as const,
      label: 'Department',
      options: departments,
      required: true
    },
    {
      id: 'position',
      type: 'select' as const,
      label: 'Position',
      options: positions,
      required: true
    },
    {
      id: 'manager',
      type: 'select' as const,
      label: 'Manager',
      options: managers
    },
    {
      id: 'startDate',
      type: 'date' as const,
      label: 'Start Date',
      required: true
    },
    {
      id: 'salary',
      type: 'number' as const,
      label: 'Salary',
      min: 0,
      step: 1000
    },
    {
      id: 'access-section',
      type: 'section' as const,
      label: 'Access & Security',
      description: 'Roles and permissions'
    },
    {
      id: 'roles',
      type: 'multiselect' as const,
      label: 'Roles',
      options: roles
    },
    {
      id: 'status',
      type: 'select' as const,
      label: 'Status',
      options: [
        { value: 'active', label: 'Active' },
        { value: 'inactive', label: 'Inactive' },
        { value: 'pending', label: 'Pending' },
        { value: 'suspended', label: 'Suspended' }
      ],
      defaultValue: 'pending'
    },
    ...(editingUser ? [] : [
      {
        id: 'password',
        type: 'password' as const,
        label: 'Password',
        placeholder: 'Enter secure password',
        required: true,
        validation: { minLength: 8 }
      },
      {
        id: 'confirmPassword',
        type: 'password' as const,
        label: 'Confirm Password',
        placeholder: 'Confirm password',
        required: true,
        validation: { minLength: 8 }
      }
    ])
  ], [departments, positions, managers, roles, editingUser]);

  // Data table columns configuration
  const tableColumns = useMemo(() => [
    {
      key: 'avatar',
      title: '',
      width: 60,
      render: (value: string, user: User) => (
        <div className="flex items-center justify-center">
          {value ? (
            <img src={value} alt="" className="w-8 h-8 rounded-full" />
          ) : (
            <div className="w-8 h-8 bg-gray-300 rounded-full flex items-center justify-center text-sm font-medium">
              {user.firstName.charAt(0)}{user.lastName.charAt(0)}
            </div>
          )}
        </div>
      )
    },
    {
      key: 'name',
      title: 'Name',
      sortable: true,
      searchable: true,
      render: (_: any, user: User) => (
        <div>
          <div className="font-medium">{user.firstName} {user.lastName}</div>
          <div className="text-sm text-gray-500">{user.email}</div>
        </div>
      )
    },
    {
      key: 'employeeId',
      title: 'Employee ID',
      sortable: true,
      searchable: true,
      width: 120
    },
    {
      key: 'department',
      title: 'Department',
      sortable: true,
      filterable: true,
      width: 140
    },
    {
      key: 'position',
      title: 'Position',
      sortable: true,
      filterable: true,
      width: 140
    },
    {
      key: 'roles',
      title: 'Roles',
      width: 160,
      render: (roles: string[]) => (
        <div className="flex flex-wrap gap-1">
          {roles.slice(0, 2).map(roleId => {
            const role = roles.find(r => r.value === roleId);
            return (
              <span
                key={roleId}
                className="px-2 py-1 text-xs bg-blue-100 text-blue-800 rounded"
              >
                {role?.label || roleId}
              </span>
            );
          })}
          {roles.length > 2 && (
            <span className="px-2 py-1 text-xs bg-gray-100 text-gray-600 rounded">
              +{roles.length - 2}
            </span>
          )}
        </div>
      )
    },
    {
      key: 'status',
      title: 'Status',
      sortable: true,
      filterable: true,
      width: 100,
      render: (status: User['status']) => (
        <span className={cn(
          "px-2 py-1 text-xs rounded-full font-medium",
          status === 'active' && "bg-green-100 text-green-800",
          status === 'inactive' && "bg-gray-100 text-gray-800",
          status === 'pending' && "bg-yellow-100 text-yellow-800",
          status === 'suspended' && "bg-red-100 text-red-800"
        )}>
          {status.charAt(0).toUpperCase() + status.slice(1)}
        </span>
      )
    },
    {
      key: 'lastLogin',
      title: 'Last Login',
      sortable: true,
      width: 140,
      render: (date: Date) => date ? date.toLocaleDateString() : 'Never'
    },
    {
      key: 'actions',
      title: 'Actions',
      width: 120,
      render: (_: any, user: User) => (
        <div className="flex space-x-2">
          <button
            className="text-blue-600 hover:text-blue-800 text-sm"
            onClick={() => handleEditUser(user)}
            disabled={readOnly}
            data-testid={`edit-user-${user.id}`}
          >
            Edit
          </button>
          <button
            className="text-red-600 hover:text-red-800 text-sm"
            onClick={() => handleDeleteUsers([user.id])}
            disabled={readOnly}
            data-testid={`delete-user-${user.id}`}
          >
            Delete
          </button>
        </div>
      )
    }
  ], [readOnly, roles]);

  // User analytics data
  const analyticsData = useMemo(() => {
    const totalUsers = users.length;
    const activeUsers = users.filter(u => u.status === 'active').length;
    const departmentCounts = users.reduce((acc, user) => {
      acc[user.department] = (acc[user.department] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);

    return {
      widgets: [
        {
          id: 'user-metrics',
          type: 'metric',
          title: 'User Metrics',
          position: { row: 1, col: 1, width: 4, height: 2 },
          data: [
            {
              id: 'total-users',
              name: 'Total Users',
              value: totalUsers,
              format: 'number',
              icon: '👥',
              color: '#3b82f6'
            },
            {
              id: 'active-users',
              name: 'Active Users',
              value: activeUsers,
              format: 'number',
              trend: activeUsers > totalUsers * 0.8 ? 'up' : 'down',
              icon: '✅',
              color: '#10b981'
            }
          ]
        },
        {
          id: 'department-chart',
          type: 'chart',
          title: 'Users by Department',
          position: { row: 1, col: 5, width: 8, height: 4 },
          data: {
            id: 'department-distribution',
            title: 'Department Distribution',
            type: 'pie',
            data: Object.entries(departmentCounts).map(([dept, count]) => ({
              x: dept,
              y: count,
              label: dept
            }))
          }
        }
      ]
    };
  }, [users]);

  // Handle user creation
  const handleCreateUser = useCallback(async (formData: Record<string, any>) => {
    if (!onUserCreate) return;

    setIsLoading(true);
    try {
      const userData: UserFormData = {
        firstName: formData.firstName,
        lastName: formData.lastName,
        email: formData.email,
        phone: formData.phone,
        department: formData.department,
        position: formData.position,
        employeeId: formData.employeeId,
        startDate: new Date(formData.startDate),
        status: formData.status || 'pending',
        roles: formData.roles || [],
        permissions: [],
        manager: formData.manager,
        salary: formData.salary ? Number(formData.salary) : undefined,
        password: formData.password
      };

      await onUserCreate(userData);
      setShowCreateForm(false);
    } catch (error) {
      onError?.(error as Error);
    } finally {
      setIsLoading(false);
    }
  }, [onUserCreate, onError]);

  // Handle user editing
  const handleEditUser = useCallback((user: User) => {
    setEditingUser(user);
    setShowEditForm(true);
  }, []);

  // Handle user update
  const handleUpdateUser = useCallback(async (formData: Record<string, any>) => {
    if (!onUserUpdate || !editingUser) return;

    setIsLoading(true);
    try {
      const updates: Partial<UserFormData> = {
        firstName: formData.firstName,
        lastName: formData.lastName,
        email: formData.email,
        phone: formData.phone,
        department: formData.department,
        position: formData.position,
        employeeId: formData.employeeId,
        startDate: new Date(formData.startDate),
        status: formData.status,
        roles: formData.roles || [],
        manager: formData.manager,
        salary: formData.salary ? Number(formData.salary) : undefined
      };

      await onUserUpdate(editingUser.id, updates);
      setShowEditForm(false);
      setEditingUser(null);
    } catch (error) {
      onError?.(error as Error);
    } finally {
      setIsLoading(false);
    }
  }, [onUserUpdate, editingUser, onError]);

  // Handle user deletion
  const handleDeleteUsers = useCallback(async (userIds: string[]) => {
    if (!onUserDelete) return;

    const confirmed = window.confirm(
      `Are you sure you want to delete ${userIds.length} user(s)? This action cannot be undone.`
    );

    if (!confirmed) return;

    setIsLoading(true);
    try {
      await onUserDelete(userIds.length === 1 ? userIds[0] : userIds);
      setSelectedUsers([]);
    } catch (error) {
      onError?.(error as Error);
    } finally {
      setIsLoading(false);
    }
  }, [onUserDelete, onError]);

  // Handle user status change
  const handleStatusChange = useCallback(async (userId: string, status: User['status']) => {
    if (!onUserStatusChange) return;

    setIsLoading(true);
    try {
      await onUserStatusChange(userId, status);
    } catch (error) {
      onError?.(error as Error);
    } finally {
      setIsLoading(false);
    }
  }, [onUserStatusChange, onError]);

  // Handle bulk actions
  const handleBulkAction = useCallback(async (action: string) => {
    if (selectedUsers.length === 0) return;

    switch (action) {
      case 'activate':
        for (const userId of selectedUsers) {
          await handleStatusChange(userId, 'active');
        }
        break;
      case 'deactivate':
        for (const userId of selectedUsers) {
          await handleStatusChange(userId, 'inactive');
        }
        break;
      case 'delete':
        await handleDeleteUsers(selectedUsers);
        break;
      default:
        break;
    }

    setSelectedUsers([]);
  }, [selectedUsers, handleStatusChange, handleDeleteUsers]);

  // Handle file import
  const handleImport = useCallback(async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file || !onImport) return;

    setIsLoading(true);
    try {
      const result = await onImport(file);
      alert(`Import completed: ${result.success} users imported successfully. ${result.errors.length} errors.`);
      if (result.errors.length > 0) {
        console.error('Import errors:', result.errors);
      }
    } catch (error) {
      onError?.(error as Error);
    } finally {
      setIsLoading(false);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  }, [onImport, onError]);

  // Render header
  const renderHeader = () => (
    <div className="flex items-center justify-between p-6 border-b border-gray-200">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">User Management</h1>
        <p className="text-gray-600 mt-1">Manage users, roles, and permissions</p>
      </div>
      <div className="flex items-center space-x-3">
        {enableImport && !readOnly && (
          <>
            <input
              ref={fileInputRef}
              type="file"
              accept=".csv,.xlsx"
              onChange={handleImport}
              className="hidden"
              data-testid="import-file-input"
            />
            <button
              className="px-4 py-2 text-sm border border-gray-300 rounded hover:bg-gray-50"
              onClick={() => fileInputRef.current?.click()}
              disabled={isLoading}
              data-testid="import-users-button"
            >
              Import Users
            </button>
          </>
        )}
        {enableExport && (
          <button
            className="px-4 py-2 text-sm bg-gray-500 text-white rounded hover:bg-gray-600"
            onClick={() => onExport?.('csv')}
            disabled={isLoading}
            data-testid="export-users-button"
          >
            Export Users
          </button>
        )}
        {!readOnly && (
          <button
            className="px-4 py-2 text-sm bg-blue-500 text-white rounded hover:bg-blue-600"
            onClick={() => setShowCreateForm(true)}
            disabled={isLoading || users.length >= maxUsers}
            data-testid="create-user-button"
          >
            Create User
          </button>
        )}
      </div>
    </div>
  );

  // Render tabs
  const renderTabs = () => (
    <div className="border-b border-gray-200">
      <nav className="flex space-x-8 px-6">
        {['users', 'permissions', 'analytics'].map(tab => (
          <button
            key={tab}
            className={cn(
              "py-4 px-1 border-b-2 font-medium text-sm transition-colors",
              activeTab === tab
                ? "border-blue-500 text-blue-600"
                : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
            )}
            onClick={() => setActiveTab(tab as any)}
            data-testid={`tab-${tab}`}
          >
            {tab.charAt(0).toUpperCase() + tab.slice(1)}
          </button>
        ))}
      </nav>
    </div>
  );

  // Render users tab
  const renderUsersTab = () => (
    <div className="p-6">
      <div className="mb-6 flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <input
            type="text"
            placeholder="Search users..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
            data-testid="search-users-input"
          />
          
          <select
            value={filters.department || ''}
            onChange={(e) => setFilters(prev => ({ ...prev, department: e.target.value || undefined }))}
            className="px-3 py-2 border border-gray-300 rounded"
            data-testid="filter-department"
          >
            <option value="">All Departments</option>
            {departments.map(dept => (
              <option key={dept.value} value={dept.value}>
                {dept.label}
              </option>
            ))}
          </select>

          <select
            value={filters.status || ''}
            onChange={(e) => setFilters(prev => ({ ...prev, status: e.target.value || undefined }))}
            className="px-3 py-2 border border-gray-300 rounded"
            data-testid="filter-status"
          >
            <option value="">All Statuses</option>
            <option value="active">Active</option>
            <option value="inactive">Inactive</option>
            <option value="pending">Pending</option>
            <option value="suspended">Suspended</option>
          </select>
        </div>

        {enableBulkActions && selectedUsers.length > 0 && (
          <div className="flex items-center space-x-2">
            <span className="text-sm text-gray-600">
              {selectedUsers.length} selected
            </span>
            <select
              onChange={(e) => e.target.value && handleBulkAction(e.target.value)}
              className="px-3 py-2 text-sm border border-gray-300 rounded"
              defaultValue=""
              data-testid="bulk-actions-select"
            >
              <option value="">Bulk Actions</option>
              <option value="activate">Activate</option>
              <option value="deactivate">Deactivate</option>
              <option value="delete">Delete</option>
            </select>
          </div>
        )}
      </div>

      <EnhancedDataTable
        columns={tableColumns}
        data={filteredUsers}
        enableSearch={false}
        enableFilters={false}
        enableSorting={true}
        enableBulkActions={enableBulkActions}
        selectable={enableBulkActions}
        pageSize={pageSize}
        selectedRows={selectedUsers}
        onRowSelect={(selected) => setSelectedUsers(selected)}
        loading={isLoading}
        data-testid="users-table"
      />
    </div>
  );

  // Render permissions tab
  const renderPermissionsTab = () => (
    <div className="p-6">
      <PermissionUI
        users={users.map(user => ({
          id: user.id,
          name: `${user.firstName} ${user.lastName}`,
          email: user.email,
          roles: user.roles,
          status: user.status,
          avatar: user.avatar
        }))}
        roles={roles.map(role => ({
          id: role.value,
          name: role.label,
          type: 'custom',
          permissions: [],
          level: 1,
          isActive: true,
          userCount: users.filter(u => u.roles.includes(role.value)).length
        }))}
        permissions={permissions.map(perm => ({
          id: perm.value,
          name: perm.label,
          resource: 'users',
          action: 'read',
          level: 'read'
        }))}
        resources={[
          { id: 'users', name: 'Users', type: 'resource', actions: ['read', 'write', 'delete'] },
          { id: 'roles', name: 'Roles', type: 'resource', actions: ['read', 'write'] },
          { id: 'permissions', name: 'Permissions', type: 'resource', actions: ['read', 'write'] }
        ]}
        mode="matrix"
        viewOnly={readOnly}
        enableBulkActions={true}
        enableSearch={true}
        enableFilters={true}
        onRoleAssign={onRoleAssign}
        onRoleRemove={onRoleRemove}
        onPermissionGrant={onPermissionGrant}
        onPermissionRevoke={onPermissionRevoke}
        height={600}
        data-testid="permissions-ui"
      />
    </div>
  );

  // Render analytics tab
  const renderAnalyticsTab = () => (
    <div className="p-6">
      <AnalyticsDashboard
        {...analyticsData}
        enableEdit={false}
        enableFilters={false}
        enableExport={enableExport}
        realTime={false}
        height="70vh"
        data-testid="user-analytics"
      />
    </div>
  );

  return (
    <div
      className={cn("bg-white min-h-screen", className)}
      data-testid={dataTestId}
    >
      {renderHeader()}
      {renderTabs()}

      {/* Tab Content */}
      {activeTab === 'users' && renderUsersTab()}
      {activeTab === 'permissions' && renderPermissionsTab()}
      {activeTab === 'analytics' && enableAnalytics && renderAnalyticsTab()}

      {/* Create User Modal */}
      {showCreateForm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl w-full max-w-2xl max-h-[90vh] overflow-y-auto">
            <div className="p-6 border-b border-gray-200">
              <h2 className="text-xl font-semibold">Create New User</h2>
            </div>
            <div className="p-6">
              <FormBuilder
                fields={userFormFields}
                onSubmit={handleCreateUser}
                submitLabel="Create User"
                showPreview={false}
                loading={isLoading}
                data-testid="create-user-form"
              />
            </div>
            <div className="p-6 border-t border-gray-200 flex justify-end space-x-3">
              <button
                className="px-4 py-2 text-sm border border-gray-300 rounded hover:bg-gray-50"
                onClick={() => setShowCreateForm(false)}
                disabled={isLoading}
                data-testid="cancel-create-user"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Edit User Modal */}
      {showEditForm && editingUser && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl w-full max-w-2xl max-h-[90vh] overflow-y-auto">
            <div className="p-6 border-b border-gray-200">
              <h2 className="text-xl font-semibold">
                Edit User: {editingUser.firstName} {editingUser.lastName}
              </h2>
            </div>
            <div className="p-6">
              <FormBuilder
                fields={userFormFields}
                initialData={editingUser}
                onSubmit={handleUpdateUser}
                submitLabel="Update User"
                showPreview={false}
                loading={isLoading}
                data-testid="edit-user-form"
              />
            </div>
            <div className="p-6 border-t border-gray-200 flex justify-end space-x-3">
              <button
                className="px-4 py-2 text-sm border border-gray-300 rounded hover:bg-gray-50"
                onClick={() => {
                  setShowEditForm(false);
                  setEditingUser(null);
                }}
                disabled={isLoading}
                data-testid="cancel-edit-user"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default UserManagement;