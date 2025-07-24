import React, { useState, useCallback, useMemo, useRef } from 'react';
import { cn } from '@/lib/utils';
import { AnalyticsDashboard } from '@/components/ui/AnalyticsDashboard';
import { ChartSystem } from '@/components/ui/ChartSystem';
import { ReportBuilder } from '@/components/ui/ReportBuilder';
import { FormBuilder } from '@/components/ui/FormBuilder';
import { EnhancedDataTable } from '@/components/ui/EnhancedDataTable';

export interface ReportConfig {
  id: string;
  name: string;
  description?: string;
  type: 'dashboard' | 'table' | 'chart' | 'summary' | 'custom';
  category: string;
  dataSource: string;
  filters?: Record<string, any>;
  columns?: string[];
  chartConfig?: {
    type: 'line' | 'bar' | 'pie' | 'area' | 'scatter';
    xAxis: string;
    yAxis: string;
    groupBy?: string;
  };
  schedule?: {
    frequency: 'daily' | 'weekly' | 'monthly' | 'quarterly' | 'custom';
    time?: string;
    recipients?: string[];
    enabled: boolean;
  };
  permissions?: string[];
  createdBy: string;
  createdAt: Date;
  updatedAt: Date;
  lastRun?: Date;
  isFavorite?: boolean;
  isPublic?: boolean;
}

export interface ReportData {
  id: string;
  reportId: string;
  data: any[];
  metadata: {
    totalRecords: number;
    generatedAt: Date;
    parameters?: Record<string, any>;
    executionTime?: number;
  };
  status: 'generating' | 'completed' | 'failed' | 'cancelled';
  error?: string;
}

export interface DashboardWidget {
  id: string;
  title: string;
  type: 'metric' | 'chart' | 'table' | 'text';
  reportId?: string;
  position: {
    row: number;
    col: number;
    width: number;
    height: number;
  };
  config?: Record<string, any>;
  data?: any;
}

export interface ReportsProps {
  reports?: ReportConfig[];
  reportData?: ReportData[];
  dashboards?: {
    id: string;
    name: string;
    description?: string;
    widgets: DashboardWidget[];
    isDefault?: boolean;
  }[];
  categories?: Array<{ value: string; label: string }>;
  dataSources?: Array<{ value: string; label: string }>;
  users?: Array<{ value: string; label: string }>;
  enableReportBuilder?: boolean;
  enableScheduling?: boolean;
  enableSharing?: boolean;
  enableExport?: boolean;
  enableDashboards?: boolean;
  maxReports?: number;
  readOnly?: boolean;
  className?: string;
  onReportCreate?: (report: Omit<ReportConfig, 'id' | 'createdAt' | 'updatedAt'>) => Promise<ReportConfig>;
  onReportUpdate?: (id: string, updates: Partial<ReportConfig>) => Promise<ReportConfig>;
  onReportDelete?: (id: string | string[]) => Promise<void>;
  onReportRun?: (id: string, parameters?: Record<string, any>) => Promise<ReportData>;
  onReportSchedule?: (id: string, schedule: ReportConfig['schedule']) => Promise<void>;
  onReportShare?: (id: string, userIds: string[], permissions: string[]) => Promise<void>;
  onDashboardCreate?: (dashboard: { name: string; description?: string; widgets: DashboardWidget[] }) => Promise<void>;
  onDashboardUpdate?: (id: string, updates: { name?: string; description?: string; widgets?: DashboardWidget[] }) => Promise<void>;
  onExport?: (reportId: string, format: 'csv' | 'xlsx' | 'pdf') => Promise<void>;
  onError?: (error: Error) => void;
  'data-testid'?: string;
}

export const Reports: React.FC<ReportsProps> = ({
  reports = [],
  reportData = [],
  dashboards = [],
  categories = [],
  dataSources = [],
  users = [],
  enableReportBuilder = true,
  enableScheduling = true,
  enableSharing = true,
  enableExport = true,
  enableDashboards = true,
  maxReports = 1000,
  readOnly = false,
  className,
  onReportCreate,
  onReportUpdate,
  onReportDelete,
  onReportRun,
  onReportSchedule,
  onReportShare,
  onDashboardCreate,
  onDashboardUpdate,
  onExport,
  onError,
  'data-testid': dataTestId = 'reports'
}) => {
  const [activeTab, setActiveTab] = useState<'reports' | 'dashboards' | 'builder'>('reports');
  const [selectedReports, setSelectedReports] = useState<string[]>([]);
  const [selectedDashboard, setSelectedDashboard] = useState<string>('');
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [showEditForm, setShowEditForm] = useState(false);
  const [showScheduleForm, setShowScheduleForm] = useState(false);
  const [showShareForm, setShowShareForm] = useState(false);
  const [editingReport, setEditingReport] = useState<ReportConfig | null>(null);
  const [schedulingReport, setSchedulingReport] = useState<ReportConfig | null>(null);
  const [sharingReport, setSharingReport] = useState<ReportConfig | null>(null);
  const [runningReports, setRunningReports] = useState<Set<string>>(new Set());
  const [searchQuery, setSearchQuery] = useState('');
  const [filters, setFilters] = useState<{
    category?: string;
    type?: string;
    dataSource?: string;
    createdBy?: string;
    favorites?: boolean;
  }>({});
  const [isLoading, setIsLoading] = useState(false);

  // Filter reports based on search and filters
  const filteredReports = useMemo(() => {
    let filtered = [...reports];

    // Apply search
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(report =>
        report.name.toLowerCase().includes(query) ||
        report.description?.toLowerCase().includes(query) ||
        report.category.toLowerCase().includes(query) ||
        report.dataSource.toLowerCase().includes(query)
      );
    }

    // Apply filters
    if (filters.category) {
      filtered = filtered.filter(report => report.category === filters.category);
    }

    if (filters.type) {
      filtered = filtered.filter(report => report.type === filters.type);
    }

    if (filters.dataSource) {
      filtered = filtered.filter(report => report.dataSource === filters.dataSource);
    }

    if (filters.createdBy) {
      filtered = filtered.filter(report => report.createdBy === filters.createdBy);
    }

    if (filters.favorites) {
      filtered = filtered.filter(report => report.isFavorite);
    }

    return filtered;
  }, [reports, searchQuery, filters]);

  // Report form fields configuration
  const reportFormFields = useMemo(() => [
    {
      id: 'basic-section',
      type: 'section' as const,
      label: 'Basic Information',
      description: 'Report identification and description'
    },
    {
      id: 'name',
      type: 'text' as const,
      label: 'Report Name',
      placeholder: 'Enter report name',
      required: true,
      validation: { minLength: 2, maxLength: 100 }
    },
    {
      id: 'description',
      type: 'textarea' as const,
      label: 'Description',
      placeholder: 'Enter report description',
      rows: 3
    },
    {
      id: 'category',
      type: 'select' as const,
      label: 'Category',
      options: categories,
      required: true
    },
    {
      id: 'type',
      type: 'select' as const,
      label: 'Report Type',
      options: [
        { value: 'dashboard', label: 'Dashboard' },
        { value: 'table', label: 'Table' },
        { value: 'chart', label: 'Chart' },
        { value: 'summary', label: 'Summary' },
        { value: 'custom', label: 'Custom' }
      ],
      required: true
    },
    {
      id: 'data-section',
      type: 'section' as const,
      label: 'Data Configuration',
      description: 'Data source and filtering'
    },
    {
      id: 'dataSource',
      type: 'select' as const,
      label: 'Data Source',
      options: dataSources,
      required: true
    },
    {
      id: 'permissions-section',
      type: 'section' as const,
      label: 'Access Control',
      description: 'Permissions and sharing settings'
    },
    {
      id: 'isPublic',
      type: 'switch' as const,
      label: 'Public Report',
      description: 'Allow all users to view this report'
    },
    {
      id: 'permissions',
      type: 'multiselect' as const,
      label: 'Required Permissions',
      options: [
        { value: 'reports.view', label: 'View Reports' },
        { value: 'reports.edit', label: 'Edit Reports' },
        { value: 'reports.admin', label: 'Admin Reports' },
        { value: 'data.sensitive', label: 'Sensitive Data' }
      ]
    }
  ], [categories, dataSources]);

  // Schedule form fields
  const scheduleFormFields = useMemo(() => [
    {
      id: 'frequency',
      type: 'select' as const,
      label: 'Frequency',
      options: [
        { value: 'daily', label: 'Daily' },
        { value: 'weekly', label: 'Weekly' },
        { value: 'monthly', label: 'Monthly' },
        { value: 'quarterly', label: 'Quarterly' },
        { value: 'custom', label: 'Custom' }
      ],
      required: true
    },
    {
      id: 'time',
      type: 'time' as const,
      label: 'Execution Time',
      defaultValue: '09:00'
    },
    {
      id: 'recipients',
      type: 'multiselect' as const,
      label: 'Recipients',
      options: users
    },
    {
      id: 'enabled',
      type: 'switch' as const,
      label: 'Enable Schedule',
      defaultValue: true
    }
  ], [users]);

  // Share form fields
  const shareFormFields = useMemo(() => [
    {
      id: 'userIds',
      type: 'multiselect' as const,
      label: 'Share with Users',
      options: users,
      required: true
    },
    {
      id: 'permissions',
      type: 'multiselect' as const,
      label: 'Permissions',
      options: [
        { value: 'view', label: 'View' },
        { value: 'edit', label: 'Edit' },
        { value: 'schedule', label: 'Schedule' },
        { value: 'share', label: 'Share' }
      ],
      defaultValue: ['view']
    }
  ], [users]);

  // Reports table columns
  const reportsTableColumns = useMemo(() => [
    {
      key: 'name',
      title: 'Name',
      sortable: true,
      searchable: true,
      render: (name: string, report: ReportConfig) => (
        <div>
          <div className="flex items-center space-x-2">
            <span className="font-medium">{name}</span>
            {report.isFavorite && <span className="text-yellow-500">⭐</span>}
            {report.isPublic && <span className="text-blue-500">🌐</span>}
          </div>
          {report.description && (
            <div className="text-sm text-gray-500">{report.description}</div>
          )}
        </div>
      )
    },
    {
      key: 'type',
      title: 'Type',
      sortable: true,
      filterable: true,
      width: 100,
      render: (type: ReportConfig['type']) => (
        <span className={cn(
          "px-2 py-1 text-xs rounded font-medium",
          type === 'dashboard' && "bg-blue-100 text-blue-800",
          type === 'table' && "bg-green-100 text-green-800",
          type === 'chart' && "bg-purple-100 text-purple-800",
          type === 'summary' && "bg-orange-100 text-orange-800",
          type === 'custom' && "bg-gray-100 text-gray-800"
        )}>
          {type.charAt(0).toUpperCase() + type.slice(1)}
        </span>
      )
    },
    {
      key: 'category',
      title: 'Category',
      sortable: true,
      filterable: true,
      width: 120
    },
    {
      key: 'dataSource',
      title: 'Data Source',
      sortable: true,
      filterable: true,
      width: 140
    },
    {
      key: 'schedule',
      title: 'Schedule',
      width: 120,
      render: (schedule: ReportConfig['schedule']) => (
        <div>
          {schedule?.enabled ? (
            <div>
              <div className="text-sm font-medium text-green-600">
                {schedule.frequency}
              </div>
              {schedule.time && (
                <div className="text-xs text-gray-500">
                  at {schedule.time}
                </div>
              )}
            </div>
          ) : (
            <span className="text-gray-400">Not scheduled</span>
          )}
        </div>
      )
    },
    {
      key: 'lastRun',
      title: 'Last Run',
      sortable: true,
      width: 140,
      render: (lastRun: Date) => lastRun ? lastRun.toLocaleDateString() : 'Never'
    },
    {
      key: 'createdBy',
      title: 'Created By',
      sortable: true,
      width: 120
    },
    {
      key: 'actions',
      title: 'Actions',
      width: 240,
      render: (_: any, report: ReportConfig) => (
        <div className="flex space-x-2">
          <button
            className="text-blue-600 hover:text-blue-800 text-sm"
            onClick={() => handleRunReport(report.id)}
            disabled={runningReports.has(report.id)}
            data-testid={`run-report-${report.id}`}
          >
            {runningReports.has(report.id) ? 'Running...' : 'Run'}
          </button>
          <button
            className="text-green-600 hover:text-green-800 text-sm"
            onClick={() => handleEditReport(report)}
            disabled={readOnly}
            data-testid={`edit-report-${report.id}`}
          >
            Edit
          </button>
          {enableScheduling && (
            <button
              className="text-purple-600 hover:text-purple-800 text-sm"
              onClick={() => handleScheduleReport(report)}
              disabled={readOnly}
              data-testid={`schedule-report-${report.id}`}
            >
              Schedule
            </button>
          )}
          {enableSharing && (
            <button
              className="text-orange-600 hover:text-orange-800 text-sm"
              onClick={() => handleShareReport(report)}
              disabled={readOnly}
              data-testid={`share-report-${report.id}`}
            >
              Share
            </button>
          )}
          {enableExport && (
            <button
              className="text-gray-600 hover:text-gray-800 text-sm"
              onClick={() => onExport?.(report.id, 'xlsx')}
              data-testid={`export-report-${report.id}`}
            >
              Export
            </button>
          )}
          <button
            className="text-red-600 hover:text-red-800 text-sm"
            onClick={() => handleDeleteReports([report.id])}
            disabled={readOnly}
            data-testid={`delete-report-${report.id}`}
          >
            Delete
          </button>
        </div>
      )
    }
  ], [readOnly, runningReports, enableScheduling, enableSharing, enableExport, onExport]);

  // Handle report creation
  const handleCreateReport = useCallback(async (formData: Record<string, any>) => {
    if (!onReportCreate) return;

    setIsLoading(true);
    try {
      const reportData: Omit<ReportConfig, 'id' | 'createdAt' | 'updatedAt'> = {
        name: formData.name,
        description: formData.description,
        type: formData.type,
        category: formData.category,
        dataSource: formData.dataSource,
        permissions: formData.permissions || [],
        createdBy: 'current-user', // This would come from auth context
        isPublic: formData.isPublic || false
      };

      await onReportCreate(reportData);
      setShowCreateForm(false);
    } catch (error) {
      onError?.(error as Error);
    } finally {
      setIsLoading(false);
    }
  }, [onReportCreate, onError]);

  // Handle report editing
  const handleEditReport = useCallback((report: ReportConfig) => {
    setEditingReport(report);
    setShowEditForm(true);
  }, []);

  // Handle report update
  const handleUpdateReport = useCallback(async (formData: Record<string, any>) => {
    if (!onReportUpdate || !editingReport) return;

    setIsLoading(true);
    try {
      const updates: Partial<ReportConfig> = {
        name: formData.name,
        description: formData.description,
        type: formData.type,
        category: formData.category,
        dataSource: formData.dataSource,
        permissions: formData.permissions || [],
        isPublic: formData.isPublic || false
      };

      await onReportUpdate(editingReport.id, updates);
      setShowEditForm(false);
      setEditingReport(null);
    } catch (error) {
      onError?.(error as Error);
    } finally {
      setIsLoading(false);
    }
  }, [onReportUpdate, editingReport, onError]);

  // Handle report deletion
  const handleDeleteReports = useCallback(async (reportIds: string[]) => {
    if (!onReportDelete) return;

    const confirmed = window.confirm(
      `Are you sure you want to delete ${reportIds.length} report(s)? This action cannot be undone.`
    );

    if (!confirmed) return;

    setIsLoading(true);
    try {
      await onReportDelete(reportIds.length === 1 ? reportIds[0] : reportIds);
      setSelectedReports([]);
    } catch (error) {
      onError?.(error as Error);
    } finally {
      setIsLoading(false);
    }
  }, [onReportDelete, onError]);

  // Handle report execution
  const handleRunReport = useCallback(async (reportId: string) => {
    if (!onReportRun) return;

    setRunningReports(prev => new Set([...prev, reportId]));
    try {
      await onReportRun(reportId);
    } catch (error) {
      onError?.(error as Error);
    } finally {
      setRunningReports(prev => {
        const newSet = new Set(prev);
        newSet.delete(reportId);
        return newSet;
      });
    }
  }, [onReportRun, onError]);

  // Handle report scheduling
  const handleScheduleReport = useCallback((report: ReportConfig) => {
    setSchedulingReport(report);
    setShowScheduleForm(true);
  }, []);

  // Handle schedule submission
  const handleSubmitSchedule = useCallback(async (formData: Record<string, any>) => {
    if (!onReportSchedule || !schedulingReport) return;

    setIsLoading(true);
    try {
      const schedule: ReportConfig['schedule'] = {
        frequency: formData.frequency,
        time: formData.time,
        recipients: formData.recipients || [],
        enabled: formData.enabled !== false
      };

      await onReportSchedule(schedulingReport.id, schedule);
      setShowScheduleForm(false);
      setSchedulingReport(null);
    } catch (error) {
      onError?.(error as Error);
    } finally {
      setIsLoading(false);
    }
  }, [onReportSchedule, schedulingReport, onError]);

  // Handle report sharing
  const handleShareReport = useCallback((report: ReportConfig) => {
    setSharingReport(report);
    setShowShareForm(true);
  }, []);

  // Handle share submission
  const handleSubmitShare = useCallback(async (formData: Record<string, any>) => {
    if (!onReportShare || !sharingReport) return;

    setIsLoading(true);
    try {
      await onReportShare(
        sharingReport.id,
        formData.userIds || [],
        formData.permissions || ['view']
      );
      setShowShareForm(false);
      setSharingReport(null);
    } catch (error) {
      onError?.(error as Error);
    } finally {
      setIsLoading(false);
    }
  }, [onReportShare, sharingReport, onError]);

  // Handle bulk actions
  const handleBulkAction = useCallback(async (action: string) => {
    if (selectedReports.length === 0) return;

    switch (action) {
      case 'delete':
        await handleDeleteReports(selectedReports);
        break;
      case 'run':
        for (const reportId of selectedReports) {
          await handleRunReport(reportId);
        }
        break;
      default:
        break;
    }

    setSelectedReports([]);
  }, [selectedReports, handleDeleteReports, handleRunReport]);

  // Render header
  const renderHeader = () => (
    <div className="flex items-center justify-between p-6 border-b border-gray-200">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Reports & Dashboards</h1>
        <p className="text-gray-600 mt-1">Generate, schedule, and share business reports</p>
      </div>
      <div className="flex items-center space-x-3">
        {enableExport && (
          <button
            className="px-4 py-2 text-sm bg-gray-500 text-white rounded hover:bg-gray-600"
            onClick={() => onExport?.('', 'xlsx')}
            disabled={isLoading}
            data-testid="export-all-reports-button"
          >
            Export All
          </button>
        )}
        {!readOnly && (
          <button
            className="px-4 py-2 text-sm bg-blue-500 text-white rounded hover:bg-blue-600"
            onClick={() => setShowCreateForm(true)}
            disabled={isLoading || reports.length >= maxReports}
            data-testid="create-report-button"
          >
            Create Report
          </button>
        )}
      </div>
    </div>
  );

  // Render tabs
  const renderTabs = () => (
    <div className="border-b border-gray-200">
      <nav className="flex space-x-8 px-6">
        {['reports', 'dashboards', 'builder'].map(tab => {
          if (!enableDashboards && tab === 'dashboards') return null;
          if (!enableReportBuilder && tab === 'builder') return null;
          
          return (
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
          );
        })}
      </nav>
    </div>
  );

  // Render reports tab
  const renderReportsTab = () => (
    <div className="p-6">
      <div className="mb-6 flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <input
            type="text"
            placeholder="Search reports..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
            data-testid="search-reports-input"
          />
          
          <select
            value={filters.category || ''}
            onChange={(e) => setFilters(prev => ({ ...prev, category: e.target.value || undefined }))}
            className="px-3 py-2 border border-gray-300 rounded"
            data-testid="filter-category"
          >
            <option value="">All Categories</option>
            {categories.map(cat => (
              <option key={cat.value} value={cat.value}>
                {cat.label}
              </option>
            ))}
          </select>

          <select
            value={filters.type || ''}
            onChange={(e) => setFilters(prev => ({ ...prev, type: e.target.value || undefined }))}
            className="px-3 py-2 border border-gray-300 rounded"
            data-testid="filter-type"
          >
            <option value="">All Types</option>
            <option value="dashboard">Dashboard</option>
            <option value="table">Table</option>
            <option value="chart">Chart</option>
            <option value="summary">Summary</option>
            <option value="custom">Custom</option>
          </select>

          <label className="flex items-center space-x-2">
            <input
              type="checkbox"
              checked={filters.favorites || false}
              onChange={(e) => setFilters(prev => ({ ...prev, favorites: e.target.checked || undefined }))}
              data-testid="filter-favorites"
            />
            <span className="text-sm">Favorites Only</span>
          </label>
        </div>

        {selectedReports.length > 0 && (
          <div className="flex items-center space-x-2">
            <span className="text-sm text-gray-600">
              {selectedReports.length} selected
            </span>
            <select
              onChange={(e) => e.target.value && handleBulkAction(e.target.value)}
              className="px-3 py-2 text-sm border border-gray-300 rounded"
              defaultValue=""
              data-testid="bulk-actions-select"
            >
              <option value="">Bulk Actions</option>
              <option value="run">Run Selected</option>
              <option value="delete">Delete Selected</option>
            </select>
          </div>
        )}
      </div>

      <EnhancedDataTable
        columns={reportsTableColumns}
        data={filteredReports}
        enableSearch={false}
        enableFilters={false}
        enableSorting={true}
        enableBulkActions={true}
        selectable={true}
        pageSize={25}
        selectedRows={selectedReports}
        onRowSelect={(selected) => setSelectedReports(selected)}
        loading={isLoading}
        data-testid="reports-table"
      />
    </div>
  );

  // Render dashboards tab
  const renderDashboardsTab = () => {
    const selectedDash = dashboards.find(d => d.id === selectedDashboard) || dashboards[0];
    
    return (
      <div className="p-6">
        <div className="mb-6 flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <select
              value={selectedDashboard}
              onChange={(e) => setSelectedDashboard(e.target.value)}
              className="px-3 py-2 border border-gray-300 rounded"
              data-testid="dashboard-selector"
            >
              {dashboards.map(dashboard => (
                <option key={dashboard.id} value={dashboard.id}>
                  {dashboard.name}
                </option>
              ))}
            </select>
            {selectedDash?.description && (
              <span className="text-sm text-gray-600">{selectedDash.description}</span>
            )}
          </div>

          {!readOnly && (
            <button
              className="px-4 py-2 text-sm bg-green-500 text-white rounded hover:bg-green-600"
              onClick={() => {/* Handle dashboard creation */}}
              data-testid="create-dashboard-button"
            >
              Create Dashboard
            </button>
          )}
        </div>

        {selectedDash ? (
          <AnalyticsDashboard
            widgets={selectedDash.widgets}
            enableEdit={!readOnly}
            enableFilters={true}
            enableExport={enableExport}
            realTime={false}
            height="80vh"
            data-testid="dashboard-analytics"
          />
        ) : (
          <div className="text-center py-12">
            <h3 className="text-lg font-medium text-gray-900 mb-2">No Dashboards Available</h3>
            <p className="text-gray-600 mb-4">Create your first dashboard to get started</p>
            {!readOnly && (
              <button
                className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
                onClick={() => {/* Handle dashboard creation */}}
                data-testid="create-first-dashboard-button"
              >
                Create Dashboard
              </button>
            )}
          </div>
        )}
      </div>
    );
  };

  // Render builder tab
  const renderBuilderTab = () => (
    <div className="p-6">
      <div className="mb-6">
        <h3 className="text-lg font-medium text-gray-900 mb-2">Report Builder</h3>
        <p className="text-gray-600">Create custom reports with drag-and-drop interface</p>
      </div>

      <ReportBuilder
        dataSources={dataSources}
        onSave={(reportConfig) => {
          // Handle saving the built report
          console.log('Saving report:', reportConfig);
        }}
        height="70vh"
        data-testid="report-builder"
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
      {activeTab === 'reports' && renderReportsTab()}
      {activeTab === 'dashboards' && enableDashboards && renderDashboardsTab()}
      {activeTab === 'builder' && enableReportBuilder && renderBuilderTab()}

      {/* Create Report Modal */}
      {showCreateForm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl w-full max-w-2xl max-h-[90vh] overflow-y-auto">
            <div className="p-6 border-b border-gray-200">
              <h2 className="text-xl font-semibold">Create New Report</h2>
            </div>
            <div className="p-6">
              <FormBuilder
                fields={reportFormFields}
                onSubmit={handleCreateReport}
                submitLabel="Create Report"
                showPreview={false}
                loading={isLoading}
                data-testid="create-report-form"
              />
            </div>
            <div className="p-6 border-t border-gray-200 flex justify-end space-x-3">
              <button
                className="px-4 py-2 text-sm border border-gray-300 rounded hover:bg-gray-50"
                onClick={() => setShowCreateForm(false)}
                disabled={isLoading}
                data-testid="cancel-create-report"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Edit Report Modal */}
      {showEditForm && editingReport && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl w-full max-w-2xl max-h-[90vh] overflow-y-auto">
            <div className="p-6 border-b border-gray-200">
              <h2 className="text-xl font-semibold">
                Edit Report: {editingReport.name}
              </h2>
            </div>
            <div className="p-6">
              <FormBuilder
                fields={reportFormFields}
                initialData={editingReport}
                onSubmit={handleUpdateReport}
                submitLabel="Update Report"
                showPreview={false}
                loading={isLoading}
                data-testid="edit-report-form"
              />
            </div>
            <div className="p-6 border-t border-gray-200 flex justify-end space-x-3">
              <button
                className="px-4 py-2 text-sm border border-gray-300 rounded hover:bg-gray-50"
                onClick={() => {
                  setShowEditForm(false);
                  setEditingReport(null);
                }}
                disabled={isLoading}
                data-testid="cancel-edit-report"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Schedule Report Modal */}
      {showScheduleForm && schedulingReport && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl w-full max-w-lg">
            <div className="p-6 border-b border-gray-200">
              <h2 className="text-xl font-semibold">
                Schedule Report: {schedulingReport.name}
              </h2>
            </div>
            <div className="p-6">
              <FormBuilder
                fields={scheduleFormFields}
                initialData={schedulingReport.schedule}
                onSubmit={handleSubmitSchedule}
                submitLabel="Save Schedule"
                showPreview={false}
                loading={isLoading}
                data-testid="schedule-form"
              />
            </div>
            <div className="p-6 border-t border-gray-200 flex justify-end space-x-3">
              <button
                className="px-4 py-2 text-sm border border-gray-300 rounded hover:bg-gray-50"
                onClick={() => {
                  setShowScheduleForm(false);
                  setSchedulingReport(null);
                }}
                disabled={isLoading}
                data-testid="cancel-schedule"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Share Report Modal */}
      {showShareForm && sharingReport && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl w-full max-w-lg">
            <div className="p-6 border-b border-gray-200">
              <h2 className="text-xl font-semibold">
                Share Report: {sharingReport.name}
              </h2>
            </div>
            <div className="p-6">
              <FormBuilder
                fields={shareFormFields}
                onSubmit={handleSubmitShare}
                submitLabel="Share Report"
                showPreview={false}
                loading={isLoading}
                data-testid="share-form"
              />
            </div>
            <div className="p-6 border-t border-gray-200 flex justify-end space-x-3">
              <button
                className="px-4 py-2 text-sm border border-gray-300 rounded hover:bg-gray-50"
                onClick={() => {
                  setShowShareForm(false);
                  setSharingReport(null);
                }}
                disabled={isLoading}
                data-testid="cancel-share"
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

export default Reports;