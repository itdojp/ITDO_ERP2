import React, { useState, useCallback, useMemo, useRef } from 'react';
import { cn } from '@/lib/utils';
import { EnhancedDataTable } from '@/components/ui/EnhancedDataTable';
import { FormBuilder } from '@/components/ui/FormBuilder';
import { Tree } from '@/components/ui/Tree';
import { ChartSystem } from '@/components/ui/ChartSystem';
import { AnalyticsDashboard } from '@/components/ui/AnalyticsDashboard';
import { WorkflowEditor } from '@/components/ui/WorkflowEditor';

export interface Organization {
  id: string;
  name: string;
  type: 'company' | 'division' | 'department' | 'team' | 'unit';
  code: string;
  description?: string;
  parentId?: string;
  managerId?: string;
  address?: {
    street: string;
    city: string;
    state: string;
    zipCode: string;
    country: string;
  };
  contact?: {
    phone: string;
    email: string;
    website?: string;
  };
  budget?: number;
  employeeCount: number;
  status: 'active' | 'inactive' | 'restructuring' | 'dissolved';
  establishedDate: Date;
  tags?: string[];
  metadata?: Record<string, any>;
  createdAt: Date;
  updatedAt: Date;
}

export interface OrganizationFormData extends Omit<Organization, 'id' | 'createdAt' | 'updatedAt' | 'employeeCount'> {}

export interface OrganizationHierarchy extends Organization {
  children: OrganizationHierarchy[];
  level: number;
  path: string[];
}

export interface OrganizationManagementProps {
  organizations?: Organization[];
  managers?: Array<{ value: string; label: string }>;
  orgTypes?: Array<{ value: string; label: string }>;
  enableHierarchy?: boolean;
  enableWorkflow?: boolean;
  enableAnalytics?: boolean;
  enableBulkActions?: boolean;
  enableImportExport?: boolean;
  maxDepth?: number;
  pageSize?: number;
  readOnly?: boolean;
  className?: string;
  onOrganizationCreate?: (org: OrganizationFormData) => Promise<Organization>;
  onOrganizationUpdate?: (id: string, updates: Partial<OrganizationFormData>) => Promise<Organization>;
  onOrganizationDelete?: (id: string | string[]) => Promise<void>;
  onOrganizationMove?: (id: string, newParentId?: string) => Promise<void>;
  onManagerAssign?: (orgId: string, managerId: string) => Promise<void>;
  onBudgetUpdate?: (orgId: string, budget: number) => Promise<void>;
  onStatusChange?: (orgId: string, status: Organization['status']) => Promise<void>;
  onRestructure?: (changes: Array<{ id: string; parentId?: string; managerId?: string }>) => Promise<void>;
  onExport?: (format: 'csv' | 'xlsx' | 'json') => Promise<void>;
  onImport?: (file: File) => Promise<{ success: number; errors: string[] }>;
  onError?: (error: Error) => void;
  'data-testid'?: string;
}

export const OrganizationManagement: React.FC<OrganizationManagementProps> = ({
  organizations = [],
  managers = [],
  orgTypes = [
    { value: 'company', label: 'Company' },
    { value: 'division', label: 'Division' },
    { value: 'department', label: 'Department' },
    { value: 'team', label: 'Team' },
    { value: 'unit', label: 'Unit' }
  ],
  enableHierarchy = true,
  enableWorkflow = true,
  enableAnalytics = true,
  enableBulkActions = true,
  enableImportExport = true,
  maxDepth = 10,
  pageSize = 25,
  readOnly = false,
  className,
  onOrganizationCreate,
  onOrganizationUpdate,
  onOrganizationDelete,
  onOrganizationMove,
  onManagerAssign,
  onBudgetUpdate,
  onStatusChange,
  onRestructure,
  onExport,
  onImport,
  onError,
  'data-testid': dataTestId = 'organization-management'
}) => {
  const [activeTab, setActiveTab] = useState<'list' | 'hierarchy' | 'workflow' | 'analytics'>('list');
  const [selectedOrganizations, setSelectedOrganizations] = useState<string[]>([]);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [showEditForm, setShowEditForm] = useState(false);
  const [editingOrg, setEditingOrg] = useState<Organization | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [filters, setFilters] = useState<{
    type?: string;
    status?: string;
    manager?: string;
    parentId?: string;
  }>({});
  const [isLoading, setIsLoading] = useState(false);
  const [expandedNodes, setExpandedNodes] = useState<Set<string>>(new Set());
  const [showRestructureMode, setShowRestructureMode] = useState(false);
  const [restructureChanges, setRestructureChanges] = useState<Array<{ id: string; parentId?: string; managerId?: string }>>([]);

  const fileInputRef = useRef<HTMLInputElement>(null);

  // Build organization hierarchy
  const organizationHierarchy = useMemo(() => {
    const orgMap = new Map<string, OrganizationHierarchy>();
    const rootOrgs: OrganizationHierarchy[] = [];

    // Initialize all organizations
    organizations.forEach(org => {
      orgMap.set(org.id, {
        ...org,
        children: [],
        level: 0,
        path: []
      });
    });

    // Build hierarchy
    organizations.forEach(org => {
      const orgNode = orgMap.get(org.id)!;
      
      if (org.parentId && orgMap.has(org.parentId)) {
        const parent = orgMap.get(org.parentId)!;
        parent.children.push(orgNode);
        orgNode.level = parent.level + 1;
        orgNode.path = [...parent.path, parent.id];
      } else {
        rootOrgs.push(orgNode);
      }
    });

    return rootOrgs;
  }, [organizations]);

  // Filter organizations
  const filteredOrganizations = useMemo(() => {
    let filtered = [...organizations];

    // Apply search
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(org =>
        org.name.toLowerCase().includes(query) ||
        org.code.toLowerCase().includes(query) ||
        org.description?.toLowerCase().includes(query)
      );
    }

    // Apply filters
    if (filters.type) {
      filtered = filtered.filter(org => org.type === filters.type);
    }

    if (filters.status) {
      filtered = filtered.filter(org => org.status === filters.status);
    }

    if (filters.manager) {
      filtered = filtered.filter(org => org.managerId === filters.manager);
    }

    if (filters.parentId) {
      filtered = filtered.filter(org => org.parentId === filters.parentId);
    }

    return filtered;
  }, [organizations, searchQuery, filters]);

  // Organization form fields
  const organizationFormFields = useMemo(() => [
    {
      id: 'basic-section',
      type: 'section' as const,
      label: 'Basic Information',
      description: 'Organization details'
    },
    {
      id: 'name',
      type: 'text' as const,
      label: 'Organization Name',
      placeholder: 'Enter organization name',
      required: true,
      validation: { minLength: 2, maxLength: 100 }
    },
    {
      id: 'code',
      type: 'text' as const,
      label: 'Organization Code',
      placeholder: 'ORG001',
      required: true,
      validation: { pattern: '^[A-Z0-9]+$' }
    },
    {
      id: 'type',
      type: 'select' as const,
      label: 'Organization Type',
      options: orgTypes,
      required: true
    },
    {
      id: 'parentId',
      type: 'select' as const,
      label: 'Parent Organization',
      options: [
        { value: '', label: 'None (Root Level)' },
        ...organizations
          .filter(org => editingOrg ? org.id !== editingOrg.id : true)
          .map(org => ({ value: org.id, label: `${org.name} (${org.code})` }))
      ]
    },
    {
      id: 'managerId',
      type: 'select' as const,
      label: 'Manager',
      options: [
        { value: '', label: 'No Manager Assigned' },
        ...managers
      ]
    },
    {
      id: 'description',
      type: 'textarea' as const,
      label: 'Description',
      placeholder: 'Organization description...',
      rows: 3,
      validation: { maxLength: 500 }
    },
    {
      id: 'contact-section',
      type: 'section' as const,
      label: 'Contact Information',
      description: 'Address and contact details'
    },
    {
      id: 'contact.phone',
      type: 'tel' as const,
      label: 'Phone Number',
      placeholder: '+1 (555) 123-4567'
    },
    {
      id: 'contact.email',
      type: 'email' as const,
      label: 'Email Address',
      placeholder: 'contact@organization.com'
    },
    {
      id: 'contact.website',
      type: 'url' as const,
      label: 'Website',
      placeholder: 'https://www.organization.com'
    },
    {
      id: 'address.street',
      type: 'text' as const,
      label: 'Street Address',
      placeholder: '123 Business St'
    },
    {
      id: 'address.city',
      type: 'text' as const,
      label: 'City',
      placeholder: 'Business City'
    },
    {
      id: 'address.state',
      type: 'text' as const,
      label: 'State/Province',
      placeholder: 'State'
    },
    {
      id: 'address.zipCode',
      type: 'text' as const,
      label: 'ZIP/Postal Code',
      placeholder: '12345'
    },
    {
      id: 'address.country',
      type: 'text' as const,
      label: 'Country',
      placeholder: 'Country'
    },
    {
      id: 'financial-section',
      type: 'section' as const,
      label: 'Financial Information',
      description: 'Budget and financial details'
    },
    {
      id: 'budget',
      type: 'number' as const,
      label: 'Budget',
      placeholder: '0',
      min: 0,
      step: 1000
    },
    {
      id: 'establishedDate',
      type: 'date' as const,
      label: 'Established Date',
      required: true
    },
    {
      id: 'status',
      type: 'select' as const,
      label: 'Status',
      options: [
        { value: 'active', label: 'Active' },
        { value: 'inactive', label: 'Inactive' },
        { value: 'restructuring', label: 'Restructuring' },
        { value: 'dissolved', label: 'Dissolved' }
      ],
      defaultValue: 'active'
    },
    {
      id: 'tags',
      type: 'multiselect' as const,
      label: 'Tags',
      options: [
        { value: 'headquarters', label: 'Headquarters' },
        { value: 'branch', label: 'Branch' },
        { value: 'remote', label: 'Remote' },
        { value: 'startup', label: 'Startup' },
        { value: 'enterprise', label: 'Enterprise' }
      ]
    }
  ], [orgTypes, organizations, managers, editingOrg]);

  // Data table columns
  const tableColumns = useMemo(() => [
    {
      key: 'name',
      title: 'Organization',
      sortable: true,
      searchable: true,
      render: (_: any, org: Organization) => (
        <div>
          <div className="font-medium">{org.name}</div>
          <div className="text-sm text-gray-500">
            {org.code} • {org.type.charAt(0).toUpperCase() + org.type.slice(1)}
          </div>
        </div>
      )
    },
    {
      key: 'hierarchy',
      title: 'Hierarchy',
      width: 200,
      render: (_: any, org: Organization) => {
        const parent = organizations.find(o => o.id === org.parentId);
        return (
          <div className="text-sm">
            {parent ? (
              <span className="text-gray-600">
                Under: <span className="font-medium">{parent.name}</span>
              </span>
            ) : (
              <span className="text-blue-600 font-medium">Root Level</span>
            )}
          </div>
        );
      }
    },
    {
      key: 'manager',
      title: 'Manager',
      width: 150,
      render: (_: any, org: Organization) => {
        const manager = managers.find(m => m.value === org.managerId);
        return manager ? manager.label : 'Unassigned';
      }
    },
    {
      key: 'employeeCount',
      title: 'Employees',
      sortable: true,
      width: 100,
      render: (count: number) => count.toLocaleString()
    },
    {
      key: 'budget',
      title: 'Budget',
      sortable: true,
      width: 120,
      render: (budget: number) => 
        budget ? `$${budget.toLocaleString()}` : 'Not set'
    },
    {
      key: 'status',
      title: 'Status',
      sortable: true,
      filterable: true,
      width: 120,
      render: (status: Organization['status']) => (
        <span className={cn(
          "px-2 py-1 text-xs rounded-full font-medium",
          status === 'active' && "bg-green-100 text-green-800",
          status === 'inactive' && "bg-gray-100 text-gray-800",
          status === 'restructuring' && "bg-yellow-100 text-yellow-800",
          status === 'dissolved' && "bg-red-100 text-red-800"
        )}>
          {status.charAt(0).toUpperCase() + status.slice(1)}
        </span>
      )
    },
    {
      key: 'establishedDate',
      title: 'Established',
      sortable: true,
      width: 120,
      render: (date: Date) => date.toLocaleDateString()
    },
    {
      key: 'actions',
      title: 'Actions',
      width: 150,
      render: (_: any, org: Organization) => (
        <div className="flex space-x-2">
          <button
            className="text-blue-600 hover:text-blue-800 text-sm"
            onClick={() => handleEditOrganization(org)}
            disabled={readOnly}
            data-testid={`edit-org-${org.id}`}
          >
            Edit
          </button>
          <button
            className="text-green-600 hover:text-green-800 text-sm"
            onClick={() => handleViewDetails(org)}
            data-testid={`view-org-${org.id}`}
          >
            View
          </button>
          <button
            className="text-red-600 hover:text-red-800 text-sm"
            onClick={() => handleDeleteOrganizations([org.id])}
            disabled={readOnly}
            data-testid={`delete-org-${org.id}`}
          >
            Delete
          </button>
        </div>
      )
    }
  ], [organizations, managers, readOnly]);

  // Analytics data
  const analyticsData = useMemo(() => {
    const totalOrgs = organizations.length;
    const activeOrgs = organizations.filter(o => o.status === 'active').length;
    const totalEmployees = organizations.reduce((sum, org) => sum + org.employeeCount, 0);
    const totalBudget = organizations.reduce((sum, org) => sum + (org.budget || 0), 0);

    const typeDistribution = organizations.reduce((acc, org) => {
      acc[org.type] = (acc[org.type] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);

    const statusDistribution = organizations.reduce((acc, org) => {
      acc[org.status] = (acc[org.status] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);

    return {
      widgets: [
        {
          id: 'org-metrics',
          type: 'metric',
          title: 'Organization Metrics',
          position: { row: 1, col: 1, width: 4, height: 3 },
          data: [
            {
              id: 'total-orgs',
              name: 'Total Organizations',
              value: totalOrgs,
              format: 'number',
              icon: '🏢',
              color: '#3b82f6'
            },
            {
              id: 'active-orgs',
              name: 'Active Organizations',
              value: activeOrgs,
              format: 'number',
              trend: activeOrgs > totalOrgs * 0.8 ? 'up' : 'down',
              icon: '✅',
              color: '#10b981'
            },
            {
              id: 'total-employees',
              name: 'Total Employees',
              value: totalEmployees,
              format: 'number',
              icon: '👥',
              color: '#8b5cf6'
            },
            {
              id: 'total-budget',
              name: 'Total Budget',
              value: totalBudget,
              format: 'currency',
              icon: '💰',
              color: '#f59e0b'
            }
          ]
        },
        {
          id: 'type-chart',
          type: 'chart',
          title: 'Organizations by Type',
          position: { row: 1, col: 5, width: 4, height: 4 },
          data: {
            id: 'type-distribution',
            title: 'Type Distribution',
            type: 'doughnut',
            data: Object.entries(typeDistribution).map(([type, count]) => ({
              x: type.charAt(0).toUpperCase() + type.slice(1),
              y: count,
              label: type
            }))
          }
        },
        {
          id: 'status-chart',
          type: 'chart',
          title: 'Organizations by Status',
          position: { row: 1, col: 9, width: 4, height: 4 },
          data: {
            id: 'status-distribution',
            title: 'Status Distribution',
            type: 'bar',
            data: Object.entries(statusDistribution).map(([status, count]) => ({
              x: status.charAt(0).toUpperCase() + status.slice(1),
              y: count,
              label: status
            }))
          }
        }
      ]
    };
  }, [organizations]);

  // Workflow data for organization approval process
  const workflowData = useMemo(() => ({
    nodes: [
      {
        id: 'start-1',
        type: 'start' as const,
        position: { x: 100, y: 100 },
        data: { label: 'Organization Request' }
      },
      {
        id: 'task-1',
        type: 'task' as const,
        position: { x: 300, y: 100 },
        data: { 
          label: 'HR Review',
          assignee: 'HR Team',
          timeout: 7200
        }
      },
      {
        id: 'decision-1',
        type: 'decision' as const,
        position: { x: 500, y: 100 },
        data: { 
          label: 'Budget Approved?',
          conditions: [
            { field: 'budget', operator: 'less', value: 1000000 }
          ]
        }
      },
      {
        id: 'task-2',
        type: 'task' as const,
        position: { x: 700, y: 50 },
        data: { 
          label: 'Create Organization',
          assignee: 'Admin'
        }
      },
      {
        id: 'task-3',
        type: 'task' as const,
        position: { x: 700, y: 150 },
        data: { 
          label: 'Request Additional Approval',
          assignee: 'Executive Team'
        }
      },
      {
        id: 'end-1',
        type: 'end' as const,
        position: { x: 900, y: 100 },
        data: { label: 'Process Complete' }
      }
    ],
    connections: [
      { id: 'conn-1', source: 'start-1', target: 'task-1' },
      { id: 'conn-2', source: 'task-1', target: 'decision-1' },
      { id: 'conn-3', source: 'decision-1', target: 'task-2', label: 'Approved' },
      { id: 'conn-4', source: 'decision-1', target: 'task-3', label: 'Needs Review' },
      { id: 'conn-5', source: 'task-2', target: 'end-1' },
      { id: 'conn-6', source: 'task-3', target: 'end-1' }
    ]
  }), []);

  // Handle organization creation
  const handleCreateOrganization = useCallback(async (formData: Record<string, any>) => {
    if (!onOrganizationCreate) return;

    setIsLoading(true);
    try {
      const orgData: OrganizationFormData = {
        name: formData.name,
        code: formData.code,
        type: formData.type,
        parentId: formData.parentId || undefined,
        managerId: formData.managerId || undefined,
        description: formData.description,
        address: {
          street: formData['address.street'] || '',
          city: formData['address.city'] || '',
          state: formData['address.state'] || '',
          zipCode: formData['address.zipCode'] || '',
          country: formData['address.country'] || ''
        },
        contact: {
          phone: formData['contact.phone'] || '',
          email: formData['contact.email'] || '',
          website: formData['contact.website']
        },
        budget: formData.budget ? Number(formData.budget) : undefined,
        status: formData.status || 'active',
        establishedDate: new Date(formData.establishedDate),
        tags: formData.tags || []
      };

      // Clean up empty objects
      if (!orgData.address?.street && !orgData.address?.city) {
        orgData.address = undefined;
      }
      if (!orgData.contact?.phone && !orgData.contact?.email) {
        orgData.contact = undefined;
      }

      await onOrganizationCreate(orgData);
      setShowCreateForm(false);
    } catch (error) {
      onError?.(error as Error);
    } finally {
      setIsLoading(false);
    }
  }, [onOrganizationCreate, onError]);

  // Handle organization editing
  const handleEditOrganization = useCallback((org: Organization) => {
    setEditingOrg(org);
    setShowEditForm(true);
  }, []);

  // Handle organization update
  const handleUpdateOrganization = useCallback(async (formData: Record<string, any>) => {
    if (!onOrganizationUpdate || !editingOrg) return;

    setIsLoading(true);
    try {
      const updates: Partial<OrganizationFormData> = {
        name: formData.name,
        code: formData.code,
        type: formData.type,
        parentId: formData.parentId || undefined,
        managerId: formData.managerId || undefined,
        description: formData.description,
        address: {
          street: formData['address.street'] || '',
          city: formData['address.city'] || '',
          state: formData['address.state'] || '',
          zipCode: formData['address.zipCode'] || '',
          country: formData['address.country'] || ''
        },
        contact: {
          phone: formData['contact.phone'] || '',
          email: formData['contact.email'] || '',
          website: formData['contact.website']
        },
        budget: formData.budget ? Number(formData.budget) : undefined,
        status: formData.status,
        establishedDate: new Date(formData.establishedDate),
        tags: formData.tags || []
      };

      await onOrganizationUpdate(editingOrg.id, updates);
      setShowEditForm(false);
      setEditingOrg(null);
    } catch (error) {
      onError?.(error as Error);
    } finally {
      setIsLoading(false);
    }
  }, [onOrganizationUpdate, editingOrg, onError]);

  // Handle organization deletion
  const handleDeleteOrganizations = useCallback(async (orgIds: string[]) => {
    if (!onOrganizationDelete) return;

    const hasChildren = orgIds.some(id => 
      organizations.some(org => org.parentId === id)
    );

    if (hasChildren) {
      alert('Cannot delete organizations that have child organizations. Please restructure first.');
      return;
    }

    const confirmed = window.confirm(
      `Are you sure you want to delete ${orgIds.length} organization(s)? This action cannot be undone.`
    );

    if (!confirmed) return;

    setIsLoading(true);
    try {
      await onOrganizationDelete(orgIds.length === 1 ? orgIds[0] : orgIds);
      setSelectedOrganizations([]);
    } catch (error) {
      onError?.(error as Error);
    } finally {
      setIsLoading(false);
    }
  }, [onOrganizationDelete, organizations, onError]);

  // Handle view details
  const handleViewDetails = useCallback((org: Organization) => {
    alert(`Organization Details:\n\nName: ${org.name}\nCode: ${org.code}\nType: ${org.type}\nEmployees: ${org.employeeCount}\nBudget: ${org.budget ? `$${org.budget.toLocaleString()}` : 'Not set'}\nStatus: ${org.status}`);
  }, []);

  // Handle bulk actions
  const handleBulkAction = useCallback(async (action: string) => {
    if (selectedOrganizations.length === 0) return;

    switch (action) {
      case 'activate':
        for (const orgId of selectedOrganizations) {
          await onStatusChange?.(orgId, 'active');
        }
        break;
      case 'deactivate':
        for (const orgId of selectedOrganizations) {
          await onStatusChange?.(orgId, 'inactive');
        }
        break;
      case 'delete':
        await handleDeleteOrganizations(selectedOrganizations);
        break;
      default:
        break;
    }

    setSelectedOrganizations([]);
  }, [selectedOrganizations, onStatusChange, handleDeleteOrganizations]);

  // Handle restructure
  const handleRestructure = useCallback(async () => {
    if (!onRestructure || restructureChanges.length === 0) return;

    setIsLoading(true);
    try {
      await onRestructure(restructureChanges);
      setShowRestructureMode(false);
      setRestructureChanges([]);
    } catch (error) {
      onError?.(error as Error);
    } finally {
      setIsLoading(false);
    }
  }, [onRestructure, restructureChanges, onError]);

  // Handle file import
  const handleImport = useCallback(async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file || !onImport) return;

    setIsLoading(true);
    try {
      const result = await onImport(file);
      alert(`Import completed: ${result.success} organizations imported. ${result.errors.length} errors.`);
    } catch (error) {
      onError?.(error as Error);
    } finally {
      setIsLoading(false);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  }, [onImport, onError]);

  // Convert organizations to tree nodes
  const convertToTreeNodes = useCallback((orgs: OrganizationHierarchy[]) => {
    return orgs.map(org => ({
      id: org.id,
      label: `${org.name} (${org.code})`,
      children: org.children.length > 0 ? convertToTreeNodes(org.children) : undefined,
      metadata: {
        type: org.type,
        status: org.status,
        employeeCount: org.employeeCount,
        manager: managers.find(m => m.value === org.managerId)?.label || 'Unassigned'
      }
    }));
  }, [managers]);

  // Render header
  const renderHeader = () => (
    <div className="flex items-center justify-between p-6 border-b border-gray-200">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Organization Management</h1>
        <p className="text-gray-600 mt-1">Manage organizational structure and hierarchy</p>
      </div>
      <div className="flex items-center space-x-3">
        {enableImportExport && !readOnly && (
          <>
            <input
              ref={fileInputRef}
              type="file"
              accept=".csv,.xlsx,.json"
              onChange={handleImport}
              className="hidden"
              data-testid="import-file-input"
            />
            <button
              className="px-4 py-2 text-sm border border-gray-300 rounded hover:bg-gray-50"
              onClick={() => fileInputRef.current?.click()}
              disabled={isLoading}
              data-testid="import-orgs-button"
            >
              Import
            </button>
          </>
        )}
        {enableImportExport && (
          <button
            className="px-4 py-2 text-sm bg-gray-500 text-white rounded hover:bg-gray-600"
            onClick={() => onExport?.('xlsx')}
            disabled={isLoading}
            data-testid="export-orgs-button"
          >
            Export
          </button>
        )}
        {showRestructureMode ? (
          <div className="flex space-x-2">
            <button
              className="px-4 py-2 text-sm bg-green-500 text-white rounded hover:bg-green-600"
              onClick={handleRestructure}
              disabled={isLoading || restructureChanges.length === 0}
              data-testid="save-restructure-button"
            >
              Save Changes ({restructureChanges.length})
            </button>
            <button
              className="px-4 py-2 text-sm border border-gray-300 rounded hover:bg-gray-50"
              onClick={() => {
                setShowRestructureMode(false);
                setRestructureChanges([]);
              }}
              data-testid="cancel-restructure-button"
            >
              Cancel
            </button>
          </div>
        ) : (
          <>
            {!readOnly && (
              <button
                className="px-4 py-2 text-sm bg-orange-500 text-white rounded hover:bg-orange-600"
                onClick={() => setShowRestructureMode(true)}
                disabled={isLoading}
                data-testid="restructure-mode-button"
              >
                Restructure
              </button>
            )}
            {!readOnly && (
              <button
                className="px-4 py-2 text-sm bg-blue-500 text-white rounded hover:bg-blue-600"
                onClick={() => setShowCreateForm(true)}
                disabled={isLoading}
                data-testid="create-org-button"
              >
                Create Organization
              </button>
            )}
          </>
        )}
      </div>
    </div>
  );

  // Render tabs
  const renderTabs = () => (
    <div className="border-b border-gray-200">
      <nav className="flex space-x-8 px-6">
        {[
          { id: 'list', label: 'List View' },
          ...(enableHierarchy ? [{ id: 'hierarchy', label: 'Hierarchy' }] : []),
          ...(enableWorkflow ? [{ id: 'workflow', label: 'Workflow' }] : []),
          ...(enableAnalytics ? [{ id: 'analytics', label: 'Analytics' }] : [])
        ].map(tab => (
          <button
            key={tab.id}
            className={cn(
              "py-4 px-1 border-b-2 font-medium text-sm transition-colors",
              activeTab === tab.id
                ? "border-blue-500 text-blue-600"
                : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
            )}
            onClick={() => setActiveTab(tab.id as any)}
            data-testid={`tab-${tab.id}`}
          >
            {tab.label}
          </button>
        ))}
      </nav>
    </div>
  );

  // Render list tab
  const renderListTab = () => (
    <div className="p-6">
      <div className="mb-6 flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <input
            type="text"
            placeholder="Search organizations..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
            data-testid="search-orgs-input"
          />
          
          <select
            value={filters.type || ''}
            onChange={(e) => setFilters(prev => ({ ...prev, type: e.target.value || undefined }))}
            className="px-3 py-2 border border-gray-300 rounded"
            data-testid="filter-type"
          >
            <option value="">All Types</option>
            {orgTypes.map(type => (
              <option key={type.value} value={type.value}>
                {type.label}
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
            <option value="restructuring">Restructuring</option>
            <option value="dissolved">Dissolved</option>
          </select>
        </div>

        {enableBulkActions && selectedOrganizations.length > 0 && (
          <div className="flex items-center space-x-2">
            <span className="text-sm text-gray-600">
              {selectedOrganizations.length} selected
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
        data={filteredOrganizations}
        enableSearch={false}
        enableFilters={false}
        enableSorting={true}
        enableBulkActions={enableBulkActions}
        selectable={enableBulkActions}
        pageSize={pageSize}
        selectedRows={selectedOrganizations}
        onRowSelect={(selected) => setSelectedOrganizations(selected)}
        loading={isLoading}
        data-testid="organizations-table"
      />
    </div>
  );

  // Render hierarchy tab
  const renderHierarchyTab = () => (
    <div className="p-6">
      <div className="mb-4">
        <h3 className="text-lg font-medium mb-2">Organization Hierarchy</h3>
        <p className="text-sm text-gray-600">
          Interactive view of organizational structure
        </p>
      </div>
      
      <Tree
        nodes={convertToTreeNodes(organizationHierarchy)}
        expandedNodes={expandedNodes}
        onNodeToggle={(nodeId) => {
          const newExpanded = new Set(expandedNodes);
          if (newExpanded.has(nodeId)) {
            newExpanded.delete(nodeId);
          } else {
            newExpanded.add(nodeId);
          }
          setExpandedNodes(newExpanded);
        }}
        showMetadata={true}
        enableDragDrop={showRestructureMode}
        onNodeMove={showRestructureMode ? (nodeId, newParentId) => {
          setRestructureChanges(prev => [
            ...prev.filter(c => c.id !== nodeId),
            { id: nodeId, parentId: newParentId }
          ]);
        } : undefined}
        height={600}
        data-testid="organization-tree"
      />
    </div>
  );

  // Render workflow tab
  const renderWorkflowTab = () => (
    <div className="p-6">
      <div className="mb-4">
        <h3 className="text-lg font-medium mb-2">Organization Approval Workflow</h3>
        <p className="text-sm text-gray-600">
          Process flow for creating and managing organizations
        </p>
      </div>
      
      <WorkflowEditor
        {...workflowData}
        enableEdit={!readOnly}
        enableValidation={true}
        showMinimap={true}
        height={500}
        data-testid="organization-workflow"
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
        enableExport={enableImportExport}
        realTime={false}
        height="70vh"
        data-testid="organization-analytics"
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
      {activeTab === 'list' && renderListTab()}
      {activeTab === 'hierarchy' && enableHierarchy && renderHierarchyTab()}
      {activeTab === 'workflow' && enableWorkflow && renderWorkflowTab()}
      {activeTab === 'analytics' && enableAnalytics && renderAnalyticsTab()}

      {/* Create Organization Modal */}
      {showCreateForm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl w-full max-w-4xl max-h-[90vh] overflow-y-auto">
            <div className="p-6 border-b border-gray-200">
              <h2 className="text-xl font-semibold">Create New Organization</h2>
            </div>
            <div className="p-6">
              <FormBuilder
                fields={organizationFormFields}
                onSubmit={handleCreateOrganization}
                submitLabel="Create Organization"
                showPreview={false}
                loading={isLoading}
                data-testid="create-org-form"
              />
            </div>
            <div className="p-6 border-t border-gray-200 flex justify-end space-x-3">
              <button
                className="px-4 py-2 text-sm border border-gray-300 rounded hover:bg-gray-50"
                onClick={() => setShowCreateForm(false)}
                disabled={isLoading}
                data-testid="cancel-create-org"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Edit Organization Modal */}
      {showEditForm && editingOrg && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl w-full max-w-4xl max-h-[90vh] overflow-y-auto">
            <div className="p-6 border-b border-gray-200">
              <h2 className="text-xl font-semibold">
                Edit Organization: {editingOrg.name}
              </h2>
            </div>
            <div className="p-6">
              <FormBuilder
                fields={organizationFormFields}
                initialData={{
                  ...editingOrg,
                  'address.street': editingOrg.address?.street,
                  'address.city': editingOrg.address?.city,
                  'address.state': editingOrg.address?.state,
                  'address.zipCode': editingOrg.address?.zipCode,
                  'address.country': editingOrg.address?.country,
                  'contact.phone': editingOrg.contact?.phone,
                  'contact.email': editingOrg.contact?.email,
                  'contact.website': editingOrg.contact?.website
                }}
                onSubmit={handleUpdateOrganization}
                submitLabel="Update Organization"
                showPreview={false}
                loading={isLoading}
                data-testid="edit-org-form"
              />
            </div>
            <div className="p-6 border-t border-gray-200 flex justify-end space-x-3">
              <button
                className="px-4 py-2 text-sm border border-gray-300 rounded hover:bg-gray-50"
                onClick={() => {
                  setShowEditForm(false);
                  setEditingOrg(null);
                }}
                disabled={isLoading}
                data-testid="cancel-edit-org"
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

export default OrganizationManagement;