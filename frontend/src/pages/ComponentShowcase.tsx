import React, { useState, useCallback, useMemo } from 'react';
import { cn } from '@/lib/utils';

// Import showcase components
import { ComponentCatalog } from './ComponentCatalog';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Select } from '@/components/ui/Select';
import { AnalyticsDashboard } from '@/components/ui/AnalyticsDashboard';
import { ChartSystem } from '@/components/ui/ChartSystem';
import { FormBuilder } from '@/components/ui/FormBuilder';
import { EnhancedDataTable } from '@/components/ui/EnhancedDataTable';
import { WorkflowEditor } from '@/components/ui/WorkflowEditor';
import { NotificationCenter } from '@/components/ui/NotificationCenter';
import { ThemeSystem } from '@/components/ui/ThemeSystem';
import { PermissionUI } from '@/components/ui/PermissionUI';

export interface ShowcaseSection {
  id: string;
  title: string;
  description: string;
  component: React.ComponentType<any>;
  props: Record<string, any>;
  category: 'basic' | 'advanced' | 'business' | 'layout';
  featured?: boolean;
}

export interface ComponentShowcaseProps {
  sections?: ShowcaseSection[];
  defaultSection?: string;
  showNavigation?: boolean;
  showSearch?: boolean;
  theme?: 'light' | 'dark' | 'auto';
  fullscreen?: boolean;
  className?: string;
  'data-testid'?: string;
}

const SHOWCASE_SECTIONS: ShowcaseSection[] = [
  {
    id: 'catalog',
    title: 'Component Catalog',
    description: 'Interactive catalog of all available UI components',
    component: ComponentCatalog,
    props: {
      searchable: true,
      filterable: true,
      showCode: true,
      showProps: true,
      layout: 'grid'
    },
    category: 'basic',
    featured: true
  },
  {
    id: 'analytics-dashboard',
    title: 'Analytics Dashboard',
    description: 'Comprehensive analytics dashboard with customizable widgets',
    component: AnalyticsDashboard,
    props: {
      widgets: [
        {
          id: 'revenue-widget',
          type: 'metric',
          title: 'Revenue Metrics',
          position: { row: 1, col: 1, width: 4, height: 3 },
          data: [
            {
              id: 'total-revenue',
              name: 'Total Revenue',
              value: 2456780,
              format: 'currency',
              trend: 'up',
              change: 15.3,
              previousValue: 2134567,
              icon: '💰',
              color: '#10b981'
            },
            {
              id: 'monthly-growth',
              name: 'Monthly Growth',
              value: 18.7,
              format: 'percentage',
              trend: 'up',
              change: 2.4,
              previousValue: 16.3,
              icon: '📈',
              color: '#3b82f6'
            }
          ]
        },
        {
          id: 'chart-widget',
          type: 'chart',
          title: 'Sales Trend',
          position: { row: 1, col: 5, width: 8, height: 4 },
          data: {
            id: 'sales-chart',
            title: 'Monthly Sales',
            type: 'line',
            data: [
              { x: 'Jan', y: 65000 },
              { x: 'Feb', y: 78000 },
              { x: 'Mar', y: 92000 },
              { x: 'Apr', y: 87000 },
              { x: 'May', y: 95000 },
              { x: 'Jun', y: 112000 }
            ]
          }
        }
      ],
      enableEdit: true,
      enableFilters: true,
      enableExport: true,
      realTime: false
    },
    category: 'advanced',
    featured: true
  },
  {
    id: 'chart-system',
    title: 'Chart System',
    description: 'Integrated charting system with multiple chart types',
    component: ChartSystem,
    props: {
      datasets: [
        {
          id: 'sales-data',
          name: 'Sales Performance',
          data: [
            { x: 'Q1', y: 125000 },
            { x: 'Q2', y: 148000 },
            { x: 'Q3', y: 162000 },
            { x: 'Q4', y: 178000 }
          ],
          color: '#3b82f6'
        },
        {
          id: 'target-data',
          name: 'Target',
          data: [
            { x: 'Q1', y: 120000 },
            { x: 'Q2', y: 145000 },
            { x: 'Q3', y: 160000 },
            { x: 'Q4', y: 175000 }
          ],
          color: '#ef4444'
        }
      ],
      type: 'line',
      height: 400,
      interactive: true,
      showLegend: true,
      showGrid: true,
      zoom: { enabled: true, mode: 'x' }
    },
    category: 'advanced'
  },
  {
    id: 'form-builder',
    title: 'Form Builder',
    description: 'Dynamic form builder with drag-and-drop functionality',
    component: FormBuilder,
    props: {
      fields: [
        {
          id: 'personal-info',
          type: 'section',
          label: 'Personal Information',
          description: 'Basic personal details'
        },
        {
          id: 'full-name',
          type: 'text',
          label: 'Full Name',
          placeholder: 'Enter your full name',
          required: true,
          validation: { minLength: 2, maxLength: 100 }
        },
        {
          id: 'email',
          type: 'email',
          label: 'Email Address',
          placeholder: 'your.email@example.com',
          required: true,
          validation: { email: true }
        },
        {
          id: 'phone',
          type: 'tel',
          label: 'Phone Number',
          placeholder: '+1 (555) 123-4567',
          validation: { pattern: '^[+]?[0-9\\s\\-\\(\\)]+$' }
        },
        {
          id: 'department',
          type: 'select',
          label: 'Department',
          options: [
            { value: 'engineering', label: 'Engineering' },
            { value: 'marketing', label: 'Marketing' },
            { value: 'sales', label: 'Sales' },
            { value: 'hr', label: 'Human Resources' }
          ],
          required: true
        },
        {
          id: 'experience',
          type: 'number',
          label: 'Years of Experience',
          min: 0,
          max: 50,
          step: 1
        },
        {
          id: 'remote-work',
          type: 'boolean',
          label: 'Open to Remote Work',
          defaultValue: false
        },
        {
          id: 'bio',
          type: 'textarea',
          label: 'Bio',
          placeholder: 'Tell us about yourself...',
          rows: 4,
          validation: { maxLength: 500 }
        }
      ],
      enableDragDrop: true,
      enableValidation: true,
      showPreview: true,
      theme: 'modern'
    },
    category: 'advanced'
  },
  {
    id: 'data-table',
    title: 'Enhanced Data Table',
    description: 'Feature-rich data table with advanced operations',
    component: EnhancedDataTable,
    props: {
      columns: [
        { key: 'id', title: 'ID', sortable: true, width: 80 },
        { key: 'name', title: 'Employee Name', sortable: true, searchable: true },
        { key: 'department', title: 'Department', filterable: true, sortable: true },
        { key: 'position', title: 'Position', sortable: true },
        { key: 'salary', title: 'Salary', sortable: true, format: 'currency' },
        { key: 'startDate', title: 'Start Date', sortable: true, format: 'date' },
        { key: 'status', title: 'Status', filterable: true, 
          render: (value: string) => (
            <span className={cn(
              "px-2 py-1 text-xs rounded-full",
              value === 'active' && "bg-green-100 text-green-800",
              value === 'inactive' && "bg-red-100 text-red-800",
              value === 'pending' && "bg-yellow-100 text-yellow-800"
            )}>
              {value}
            </span>
          )
        }
      ],
      data: [
        { id: 1, name: 'John Doe', department: 'Engineering', position: 'Senior Developer', salary: 95000, startDate: '2022-01-15', status: 'active' },
        { id: 2, name: 'Jane Smith', department: 'Marketing', position: 'Marketing Manager', salary: 78000, startDate: '2021-11-20', status: 'active' },
        { id: 3, name: 'Mike Johnson', department: 'Sales', position: 'Sales Representative', salary: 55000, startDate: '2023-03-10', status: 'active' },
        { id: 4, name: 'Sarah Wilson', department: 'HR', position: 'HR Specialist', salary: 62000, startDate: '2022-08-05', status: 'inactive' },
        { id: 5, name: 'David Brown', department: 'Engineering', position: 'Junior Developer', salary: 65000, startDate: '2023-06-01', status: 'pending' },
        { id: 6, name: 'Lisa Davis', department: 'Marketing', position: 'Content Creator', salary: 52000, startDate: '2023-04-15', status: 'active' },
        { id: 7, name: 'Tom Anderson', department: 'Sales', position: 'Sales Manager', salary: 85000, startDate: '2021-09-12', status: 'active' },
        { id: 8, name: 'Amy White', department: 'Engineering', position: 'DevOps Engineer', salary: 88000, startDate: '2022-05-08', status: 'active' }
      ],
      enableSearch: true,
      enableFilters: true,
      enableSorting: true,
      enableBulkActions: true,
      enablePagination: true,
      pageSize: 5,
      selectable: true,
      height: 400
    },
    category: 'advanced'
  },
  {
    id: 'workflow-editor',
    title: 'Workflow Editor',
    description: 'Visual workflow editor with drag-and-drop nodes',
    component: WorkflowEditor,
    props: {
      nodes: [
        {
          id: 'start-1',
          type: 'start',
          position: { x: 100, y: 100 },
          data: { label: 'Start Process' }
        },
        {
          id: 'task-1',
          type: 'task',
          position: { x: 300, y: 100 },
          data: { 
            label: 'Review Application',
            assignee: 'HR Team',
            timeout: 3600
          }
        },
        {
          id: 'decision-1',
          type: 'decision',
          position: { x: 500, y: 100 },
          data: { 
            label: 'Approved?',
            conditions: [
              { field: 'score', operator: 'greater', value: 80 },
              { field: 'experience', operator: 'greater', value: 2 }
            ]
          }
        },
        {
          id: 'task-2',
          type: 'task',
          position: { x: 700, y: 50 },
          data: { 
            label: 'Send Approval',
            assignee: 'Manager'
          }
        },
        {
          id: 'task-3',
          type: 'task',
          position: { x: 700, y: 150 },
          data: { 
            label: 'Send Rejection',
            assignee: 'HR Team'
          }
        },
        {
          id: 'end-1',
          type: 'end',
          position: { x: 900, y: 100 },
          data: { label: 'End Process' }
        }
      ],
      connections: [
        { id: 'conn-1', source: 'start-1', target: 'task-1' },
        { id: 'conn-2', source: 'task-1', target: 'decision-1' },
        { id: 'conn-3', source: 'decision-1', target: 'task-2', label: 'Yes' },
        { id: 'conn-4', source: 'decision-1', target: 'task-3', label: 'No' },
        { id: 'conn-5', source: 'task-2', target: 'end-1' },
        { id: 'conn-6', source: 'task-3', target: 'end-1' }
      ],
      enableDragDrop: true,
      enableValidation: true,
      showMinimap: true,
      height: 500
    },
    category: 'advanced'
  },
  {
    id: 'notification-center',
    title: 'Notification Center',
    description: 'Comprehensive notification management system',
    component: NotificationCenter,
    props: {
      notifications: [
        {
          id: 'notif-1',
          type: 'success',
          title: 'Payment Processed',
          message: 'Your payment of $299.99 has been successfully processed.',
          timestamp: new Date(Date.now() - 5 * 60 * 1000), // 5 minutes ago
          read: false,
          priority: 'medium',
          category: 'billing',
          sender: {
            id: 'system',
            name: 'Payment System',
            role: 'System'
          }
        },
        {
          id: 'notif-2',
          type: 'warning',
          title: 'Password Expiring',
          message: 'Your password will expire in 3 days. Please update it to maintain account security.',
          timestamp: new Date(Date.now() - 2 * 60 * 60 * 1000), // 2 hours ago
          read: false,
          priority: 'high',
          category: 'security',
          actions: [
            { id: 'update-password', label: 'Update Password', type: 'primary', onClick: () => {} },
            { id: 'remind-later', label: 'Remind Later', type: 'secondary', onClick: () => {} }
          ]
        },
        {
          id: 'notif-3',
          type: 'info',
          title: 'New Feature Available',
          message: 'Check out the new analytics dashboard with enhanced reporting capabilities.',
          timestamp: new Date(Date.now() - 24 * 60 * 60 * 1000), // 1 day ago
          read: true,
          priority: 'low',
          category: 'product',
          sender: {
            id: 'product-team',
            name: 'Product Team',
            role: 'Team'
          }
        },
        {
          id: 'notif-4',
          type: 'error',
          title: 'Backup Failed',
          message: 'Automated backup process failed. Please check your backup configuration.',
          timestamp: new Date(Date.now() - 15 * 60 * 1000), // 15 minutes ago
          read: false,
          priority: 'urgent',
          category: 'system',
          actions: [
            { id: 'check-logs', label: 'Check Logs', type: 'primary', onClick: () => {} },
            { id: 'retry-backup', label: 'Retry Backup', type: 'secondary', onClick: () => {} }
          ]
        }
      ],
      enableSearch: true,
      enableFilters: true,
      enableBulkActions: true,
      groupByDate: true,
      maxItems: 50,
      height: 500
    },
    category: 'advanced'
  },
  {
    id: 'theme-system',
    title: 'Theme System',
    description: 'Comprehensive theme management and customization',
    component: ThemeSystem,
    props: {
      themes: [
        {
          id: 'light',
          name: 'Light Theme',
          type: 'light',
          colors: {
            primary: '#3b82f6',
            secondary: '#6b7280',
            success: '#10b981',
            warning: '#f59e0b',
            error: '#ef4444',
            background: '#ffffff',
            surface: '#f9fafb',
            text: '#111827'
          },
          isDefault: true,
          isActive: true
        },
        {
          id: 'dark',
          name: 'Dark Theme',
          type: 'dark',
          colors: {
            primary: '#60a5fa',
            secondary: '#9ca3af',
            success: '#34d399',
            warning: '#fbbf24',
            error: '#f87171',
            background: '#111827',
            surface: '#1f2937',
            text: '#f9fafb'
          },
          isDefault: false,
          isActive: false
        }
      ],
      enableCustomization: true,
      enablePreview: true,
      enableExport: true,
      showColorPicker: true
    },
    category: 'advanced'
  },
  {
    id: 'permission-ui',
    title: 'Permission Management',
    description: 'Role-based permission management interface',
    component: PermissionUI,
    props: {
      users: [
        { id: '1', name: 'John Doe', email: 'john@company.com', roles: ['admin', 'user'], status: 'active' },
        { id: '2', name: 'Jane Smith', email: 'jane@company.com', roles: ['user'], status: 'active' },
        { id: '3', name: 'Mike Johnson', email: 'mike@company.com', roles: ['manager', 'user'], status: 'inactive' }
      ],
      roles: [
        { id: 'admin', name: 'Administrator', type: 'system', permissions: ['read', 'write', 'delete'], level: 3, isActive: true, userCount: 1 },
        { id: 'manager', name: 'Manager', type: 'custom', permissions: ['read', 'write'], level: 2, isActive: true, userCount: 1 },
        { id: 'user', name: 'User', type: 'system', permissions: ['read'], level: 1, isActive: true, userCount: 3 }
      ],
      permissions: [
        { id: 'read', name: 'Read Access', resource: 'documents', action: 'read', level: 'read' },
        { id: 'write', name: 'Write Access', resource: 'documents', action: 'write', level: 'write' },
        { id: 'delete', name: 'Delete Access', resource: 'documents', action: 'delete', level: 'delete' }
      ],
      resources: [
        { id: 'documents', name: 'Documents', type: 'resource', actions: ['read', 'write', 'delete'] },
        { id: 'users', name: 'Users', type: 'resource', actions: ['read', 'write'] },
        { id: 'settings', name: 'Settings', type: 'resource', actions: ['read', 'write'] }
      ],
      mode: 'matrix',
      enableBulkActions: true,
      enableSearch: true,
      enableFilters: true,
      height: 500
    },
    category: 'business'
  }
];

export const ComponentShowcase: React.FC<ComponentShowcaseProps> = ({
  sections = SHOWCASE_SECTIONS,
  defaultSection = 'catalog',
  showNavigation = true,
  showSearch = true,
  theme = 'light',
  fullscreen = false,
  className,
  'data-testid': dataTestId = 'component-showcase'
}) => {
  const [activeSection, setActiveSection] = useState(defaultSection);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string>('all');

  // Filter sections based on search and category
  const filteredSections = useMemo(() => {
    let filtered = sections;

    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(section =>
        section.title.toLowerCase().includes(query) ||
        section.description.toLowerCase().includes(query)
      );
    }

    if (selectedCategory !== 'all') {
      filtered = filtered.filter(section => section.category === selectedCategory);
    }

    return filtered;
  }, [sections, searchQuery, selectedCategory]);

  const categories = useMemo(() => {
    const cats = new Set(sections.map(s => s.category));
    return ['all', ...Array.from(cats)];
  }, [sections]);

  const activeShowcaseSection = sections.find(s => s.id === activeSection);

  const renderNavigation = () => {
    if (!showNavigation) return null;

    return (
      <div className="w-64 bg-white border-r border-gray-200 flex flex-col">
        {/* Search */}
        {showSearch && (
          <div className="p-4 border-b border-gray-200">
            <input
              type="text"
              placeholder="Search sections..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
              data-testid="section-search"
            />
          </div>
        )}

        {/* Category Filter */}
        <div className="p-4 border-b border-gray-200">
          <select
            value={selectedCategory}
            onChange={(e) => setSelectedCategory(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded text-sm"
            data-testid="category-filter"
          >
            {categories.map(cat => (
              <option key={cat} value={cat}>
                {cat === 'all' ? 'All Categories' : cat.charAt(0).toUpperCase() + cat.slice(1)}
              </option>
            ))}
          </select>
        </div>

        {/* Section List */}
        <div className="flex-1 overflow-y-auto">
          {filteredSections.map(section => (
            <button
              key={section.id}
              className={cn(
                "w-full p-4 text-left hover:bg-gray-50 border-b border-gray-100 transition-colors",
                activeSection === section.id && "bg-blue-50 border-r-2 border-r-blue-500"
              )}
              onClick={() => setActiveSection(section.id)}
              data-testid={`section-nav-${section.id}`}
            >
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="font-medium text-sm">{section.title}</h3>
                  <p className="text-xs text-gray-600 mt-1 line-clamp-2">
                    {section.description}
                  </p>
                </div>
                {section.featured && (
                  <div className="w-2 h-2 bg-blue-500 rounded-full" />
                )}
              </div>
              <div className="flex items-center mt-2">
                <span className={cn(
                  "px-2 py-1 text-xs rounded",
                  section.category === 'basic' && "bg-green-100 text-green-700",
                  section.category === 'advanced' && "bg-red-100 text-red-700",
                  section.category === 'business' && "bg-purple-100 text-purple-700",
                  section.category === 'layout' && "bg-blue-100 text-blue-700"
                )}>
                  {section.category}
                </span>
              </div>
            </button>
          ))}
        </div>
      </div>
    );
  };

  const renderContent = () => {
    if (!activeShowcaseSection) {
      return (
        <div className="flex-1 flex items-center justify-center">
          <div className="text-center">
            <div className="text-4xl mb-4">🔍</div>
            <h3 className="text-lg font-medium text-gray-900 mb-2">
              Section not found
            </h3>
            <p className="text-gray-600">
              The selected section could not be found.
            </p>
          </div>
        </div>
      );
    }

    const Component = activeShowcaseSection.component;

    return (
      <div className="flex-1 overflow-auto">
        {/* Section Header */}
        <div className="bg-white border-b border-gray-200 p-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">
                {activeShowcaseSection.title}
              </h1>
              <p className="text-gray-600 mt-1">
                {activeShowcaseSection.description}
              </p>
            </div>
            <div className="flex items-center space-x-2">
              <span className={cn(
                "px-3 py-1 text-sm rounded-full",
                activeShowcaseSection.category === 'basic' && "bg-green-100 text-green-700",
                activeShowcaseSection.category === 'advanced' && "bg-red-100 text-red-700",
                activeShowcaseSection.category === 'business' && "bg-purple-100 text-purple-700",
                activeShowcaseSection.category === 'layout' && "bg-blue-100 text-blue-700"
              )}>
                {activeShowcaseSection.category}
              </span>
              {activeShowcaseSection.featured && (
                <span className="px-3 py-1 text-sm bg-yellow-100 text-yellow-700 rounded-full">
                  Featured
                </span>
              )}
            </div>
          </div>
        </div>

        {/* Component Content */}
        <div className="p-6">
          <Component {...activeShowcaseSection.props} />
        </div>
      </div>
    );
  };

  return (
    <div
      className={cn(
        "flex h-screen bg-gray-100",
        theme === 'dark' && "bg-gray-900",
        fullscreen && "fixed inset-0 z-50",
        className
      )}
      data-testid={dataTestId}
    >
      {renderNavigation()}
      {renderContent()}
    </div>
  );
};

export default ComponentShowcase;