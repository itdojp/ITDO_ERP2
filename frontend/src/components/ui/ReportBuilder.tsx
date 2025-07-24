import React, { useState, useRef, useCallback, useEffect, useMemo } from 'react';
import { cn } from '@/lib/utils';

export interface ReportField {
  id: string;
  name: string;
  type: 'string' | 'number' | 'date' | 'boolean' | 'object' | 'array';
  label: string;
  description?: string;
  source: string;
  nullable?: boolean;
  format?: string;
  aggregation?: 'sum' | 'count' | 'avg' | 'min' | 'max' | 'distinct';
  groupBy?: boolean;
  sortable?: boolean;
  filterable?: boolean;
  visible?: boolean;
  width?: number;
  alignment?: 'left' | 'center' | 'right';
  conditional?: {
    field: string;
    operator: 'equals' | 'not_equals' | 'greater' | 'less' | 'contains' | 'starts_with' | 'ends_with';
    value: any;
    style?: React.CSSProperties;
  };
}

export interface ReportDataSource {
  id: string;
  name: string;
  type: 'database' | 'api' | 'file' | 'service' | 'custom';
  connection: {
    host?: string;
    port?: number;
    database?: string;
    username?: string;
    password?: string;
    url?: string;
    headers?: Record<string, string>;
    method?: 'GET' | 'POST' | 'PUT' | 'DELETE';
    body?: any;
    filePath?: string;
    format?: 'csv' | 'json' | 'xml' | 'excel';
  };
  query?: string;
  fields: ReportField[];
  refreshInterval?: number;
  cache?: boolean;
  timeout?: number;
}

export interface ReportFilter {
  id: string;
  field: string;
  operator: 'equals' | 'not_equals' | 'greater' | 'less' | 'between' | 'in' | 'not_in' | 'contains' | 'starts_with' | 'ends_with' | 'is_null' | 'is_not_null';
  value: any;
  values?: any[];
  label?: string;
  type: 'text' | 'number' | 'date' | 'select' | 'multiselect' | 'range' | 'boolean';
  options?: Array<{ value: any; label: string }>;
  required?: boolean;
  visible?: boolean;
  defaultValue?: any;
}

export interface ReportSorting {
  field: string;
  direction: 'asc' | 'desc';
  priority: number;
}

export interface ReportGrouping {
  field: string;
  label?: string;
  aggregations?: Array<{
    field: string;
    function: 'sum' | 'count' | 'avg' | 'min' | 'max' | 'distinct';
    label?: string;
  }>;
  collapsed?: boolean;
  showSubtotals?: boolean;
}

export interface ReportVisualization {
  id: string;
  type: 'table' | 'chart' | 'card' | 'kpi' | 'gauge' | 'map' | 'pivot' | 'crosstab';
  title?: string;
  subtitle?: string;
  config: {
    chartType?: 'line' | 'bar' | 'pie' | 'area' | 'scatter' | 'bubble';
    xAxis?: string;
    yAxis?: string | string[];
    series?: string[];
    colors?: string[];
    showLegend?: boolean;
    showGrid?: boolean;
    showTooltip?: boolean;
    stacked?: boolean;
    smooth?: boolean;
    fillArea?: boolean;
    showDataLabels?: boolean;
    responsive?: boolean;
    height?: number;
    width?: number;
  };
  position: { x: number; y: number; width: number; height: number };
  data?: any[];
}

export interface ReportTemplate {
  id: string;
  name: string;
  description?: string;
  category: string;
  dataSources: ReportDataSource[];
  fields: ReportField[];
  filters: ReportFilter[];
  sorting: ReportSorting[];
  grouping: ReportGrouping[];
  visualizations: ReportVisualization[];
  layout: 'grid' | 'free' | 'tabs' | 'sections';
  theme: 'default' | 'professional' | 'modern' | 'dark' | 'colorful';
  pageSize?: number;
  refreshInterval?: number;
  exportFormats: Array<'pdf' | 'excel' | 'csv' | 'word' | 'powerpoint' | 'json'>;
  permissions?: {
    view?: string[];
    edit?: string[];
    export?: string[];
  };
  tags?: string[];
  version?: string;
  author?: string;
  createdAt?: Date;
  updatedAt?: Date;
}

export interface ReportSchedule {
  id: string;
  reportId: string;
  name: string;
  enabled: boolean;
  frequency: 'once' | 'daily' | 'weekly' | 'monthly' | 'quarterly' | 'yearly' | 'custom';
  schedule: {
    startDate: Date;
    endDate?: Date;
    time: string;
    timezone: string;
    daysOfWeek?: number[];
    daysOfMonth?: number[];
    customCron?: string;
  };
  recipients: Array<{
    email: string;
    name?: string;
    type: 'to' | 'cc' | 'bcc';
  }>;
  format: 'pdf' | 'excel' | 'csv' | 'inline';
  subject?: string;
  message?: string;
  filters?: Record<string, any>;
}

export interface ReportBuilderProps {
  template?: ReportTemplate;
  dataSources?: ReportDataSource[];
  availableFields?: ReportField[];
  mode?: 'builder' | 'viewer' | 'preview';
  theme?: 'light' | 'dark';
  readonly?: boolean;
  collaborative?: boolean;
  autoSave?: boolean;
  realTimeData?: boolean;
  exportEnabled?: boolean;
  scheduleEnabled?: boolean;
  width?: number | string;
  height?: number | string;
  className?: string;
  style?: React.CSSProperties;
  onTemplateChange?: (template: ReportTemplate) => void;
  onDataSourceAdd?: (dataSource: ReportDataSource) => void;
  onDataSourceUpdate?: (id: string, updates: Partial<ReportDataSource>) => void;
  onDataSourceDelete?: (id: string) => void;
  onFieldAdd?: (field: ReportField) => void;
  onFieldUpdate?: (id: string, updates: Partial<ReportField>) => void;
  onFieldDelete?: (id: string) => void;
  onFilterAdd?: (filter: ReportFilter) => void;
  onFilterUpdate?: (id: string, updates: Partial<ReportFilter>) => void;
  onFilterDelete?: (id: string) => void;
  onVisualizationAdd?: (visualization: ReportVisualization) => void;
  onVisualizationUpdate?: (id: string, updates: Partial<ReportVisualization>) => void;
  onVisualizationDelete?: (id: string) => void;
  onReportSave?: (template: ReportTemplate) => void;
  onReportLoad?: (template: ReportTemplate) => void;
  onReportExport?: (format: string, data: any) => void;
  onReportSchedule?: (schedule: ReportSchedule) => void;
  onDataRefresh?: () => void;
  onError?: (error: Error) => void;
  'data-testid'?: string;
}

export const ReportBuilder: React.FC<ReportBuilderProps> = ({
  template,
  dataSources = [],
  availableFields = [],
  mode = 'builder',
  theme = 'light',
  readonly = false,
  collaborative = false,
  autoSave = false,
  realTimeData = false,
  exportEnabled = true,
  scheduleEnabled = true,
  width = '100%',
  height = 600,
  className,
  style,
  onTemplateChange,
  onDataSourceAdd,
  onDataSourceUpdate,
  onDataSourceDelete,
  onFieldAdd,
  onFieldUpdate,
  onFieldDelete,
  onFilterAdd,
  onFilterUpdate,
  onFilterDelete,
  onVisualizationAdd,
  onVisualizationUpdate,
  onVisualizationDelete,
  onReportSave,
  onReportLoad,
  onReportExport,
  onReportSchedule,
  onDataRefresh,
  onError,
  'data-testid': dataTestId = 'report-builder'
}) => {
  const [internalTemplate, setInternalTemplate] = useState<ReportTemplate>(
    template || {
      id: `report-${Date.now()}`,
      name: 'New Report',
      category: 'General',
      dataSources: [],
      fields: [],
      filters: [],
      sorting: [],
      grouping: [],
      visualizations: [],
      layout: 'grid',
      theme: 'default',
      exportFormats: ['pdf', 'excel', 'csv']
    }
  );
  
  const [selectedPanel, setSelectedPanel] = useState<'data' | 'fields' | 'filters' | 'visualizations' | 'settings'>('data');
  const [selectedDataSource, setSelectedDataSource] = useState<string | null>(null);
  const [selectedField, setSelectedField] = useState<string | null>(null);
  const [selectedVisualization, setSelectedVisualization] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [previewData, setPreviewData] = useState<any[]>([]);
  const [isDragging, setIsDragging] = useState(false);
  const [draggedItem, setDraggedItem] = useState<{ type: string; data: any } | null>(null);
  const [showPreview, setShowPreview] = useState(false);
  const [validationErrors, setValidationErrors] = useState<string[]>([]);

  const builderRef = useRef<HTMLDivElement>(null);
  const previewRef = useRef<HTMLDivElement>(null);
  const autoSaveRef = useRef<NodeJS.Timeout | null>(null);

  // Available chart types for visualizations
  const chartTypes = [
    { id: 'table', name: 'Table', icon: '📊' },
    { id: 'line', name: 'Line Chart', icon: '📈' },
    { id: 'bar', name: 'Bar Chart', icon: '📊' },
    { id: 'pie', name: 'Pie Chart', icon: '🥧' },
    { id: 'area', name: 'Area Chart', icon: '📊' },
    { id: 'scatter', name: 'Scatter Plot', icon: '💎' },
    { id: 'kpi', name: 'KPI Card', icon: '🎯' },
    { id: 'gauge', name: 'Gauge', icon: '⏲️' }
  ];

  // Filter operators by field type
  const filterOperators = {
    string: ['equals', 'not_equals', 'contains', 'starts_with', 'ends_with', 'is_null', 'is_not_null'],
    number: ['equals', 'not_equals', 'greater', 'less', 'between', 'is_null', 'is_not_null'],
    date: ['equals', 'not_equals', 'greater', 'less', 'between', 'is_null', 'is_not_null'],
    boolean: ['equals', 'not_equals', 'is_null', 'is_not_null']
  };

  // Validate report template
  const validateTemplate = useCallback(() => {
    const errors: string[] = [];
    
    if (!internalTemplate.name.trim()) {
      errors.push('Report name is required');
    }
    
    if (internalTemplate.dataSources.length === 0) {
      errors.push('At least one data source is required');
    }
    
    if (internalTemplate.fields.length === 0) {
      errors.push('At least one field must be selected');
    }
    
    if (internalTemplate.visualizations.length === 0) {
      errors.push('At least one visualization is required');
    }
    
    // Validate data source connections
    internalTemplate.dataSources.forEach(ds => {
      if (!ds.name.trim()) {
        errors.push(`Data source name is required`);
      }
      
      if (ds.type === 'database' && (!ds.connection.host || !ds.connection.database)) {
        errors.push(`Database connection requires host and database name`);
      }
      
      if (ds.type === 'api' && !ds.connection.url) {
        errors.push(`API connection requires URL`);
      }
    });
    
    // Validate visualizations
    internalTemplate.visualizations.forEach(viz => {
      if (viz.type === 'chart' && !viz.config.chartType) {
        errors.push(`Chart visualization requires chart type`);
      }
      
      if (viz.type === 'chart' && (!viz.config.xAxis || !viz.config.yAxis)) {
        errors.push(`Chart visualization requires X and Y axis configuration`);
      }
    });
    
    setValidationErrors(errors);
    return errors.length === 0;
  }, [internalTemplate]);

  // Handle drag and drop
  const handleDragStart = useCallback((e: React.DragEvent, type: string, data: any) => {
    if (readonly) return;
    
    setIsDragging(true);
    setDraggedItem({ type, data });
    
    e.dataTransfer.effectAllowed = 'copy';
    e.dataTransfer.setData('text/plain', JSON.stringify({ type, data }));
  }, [readonly]);

  const handleDragEnd = useCallback(() => {
    setIsDragging(false);
    setDraggedItem(null);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent, target: string) => {
    if (readonly) return;
    
    e.preventDefault();
    const dragData = JSON.parse(e.dataTransfer.getData('text/plain'));
    
    if (target === 'fields' && dragData.type === 'availableField') {
      const field = dragData.data as ReportField;
      const newField = {
        ...field,
        id: `field-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
        visible: true
      };
      
      const updatedTemplate = {
        ...internalTemplate,
        fields: [...internalTemplate.fields, newField]
      };
      
      setInternalTemplate(updatedTemplate);
      onTemplateChange?.(updatedTemplate);
      onFieldAdd?.(newField);
    }
    
    if (target === 'visualizations' && dragData.type === 'chartType') {
      const chartType = dragData.data;
      const newVisualization: ReportVisualization = {
        id: `viz-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
        type: chartType.id === 'table' ? 'table' : 'chart',
        title: `New ${chartType.name}`,
        config: {
          chartType: chartType.id === 'table' ? undefined : chartType.id,
          height: 300,
          responsive: true,
          showLegend: true,
          showGrid: true,
          showTooltip: true
        },
        position: { x: 0, y: 0, width: 6, height: 4 }
      };
      
      const updatedTemplate = {
        ...internalTemplate,
        visualizations: [...internalTemplate.visualizations, newVisualization]
      };
      
      setInternalTemplate(updatedTemplate);
      onTemplateChange?.(updatedTemplate);
      onVisualizationAdd?.(newVisualization);
    }
    
    setIsDragging(false);
    setDraggedItem(null);
  }, [readonly, internalTemplate, onTemplateChange, onFieldAdd, onVisualizationAdd]);

  // Handle data source management
  const handleDataSourceAdd = useCallback(() => {
    if (readonly) return;
    
    const newDataSource: ReportDataSource = {
      id: `ds-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      name: 'New Data Source',
      type: 'database',
      connection: {},
      fields: []
    };
    
    const updatedTemplate = {
      ...internalTemplate,
      dataSources: [...internalTemplate.dataSources, newDataSource]
    };
    
    setInternalTemplate(updatedTemplate);
    onTemplateChange?.(updatedTemplate);
    onDataSourceAdd?.(newDataSource);
    setSelectedDataSource(newDataSource.id);
  }, [readonly, internalTemplate, onTemplateChange, onDataSourceAdd]);

  // Handle filter management
  const handleFilterAdd = useCallback((field: ReportField) => {
    if (readonly) return;
    
    const newFilter: ReportFilter = {
      id: `filter-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      field: field.id,
      operator: 'equals',
      value: '',
      label: field.label,
      type: field.type === 'number' ? 'number' : field.type === 'date' ? 'date' : 'text',
      visible: true
    };
    
    const updatedTemplate = {
      ...internalTemplate,
      filters: [...internalTemplate.filters, newFilter]
    };
    
    setInternalTemplate(updatedTemplate);
    onTemplateChange?.(updatedTemplate);
    onFilterAdd?.(newFilter);
  }, [readonly, internalTemplate, onTemplateChange, onFilterAdd]);

  // Generate preview data
  const generatePreviewData = useCallback(() => {
    if (internalTemplate.fields.length === 0) {
      setPreviewData([]);
      return;
    }
    
    // Generate mock data based on field types
    const mockData = Array.from({ length: 50 }, (_, index) => {
      const row: any = {};
      
      internalTemplate.fields.forEach(field => {
        switch (field.type) {
          case 'string':
            row[field.id] = `Sample ${field.name} ${index + 1}`;
            break;
          case 'number':
            row[field.id] = Math.floor(Math.random() * 1000) + 1;
            break;
          case 'date':
            row[field.id] = new Date(2023, Math.floor(Math.random() * 12), Math.floor(Math.random() * 28) + 1).toISOString().split('T')[0];
            break;
          case 'boolean':
            row[field.id] = Math.random() > 0.5;
            break;
          default:
            row[field.id] = `Value ${index + 1}`;
        }
      });
      
      return row;
    });
    
    setPreviewData(mockData);
  }, [internalTemplate.fields]);

  // Auto-save functionality
  useEffect(() => {
    if (autoSave && !readonly) {
      if (autoSaveRef.current) {
        clearTimeout(autoSaveRef.current);
      }
      
      autoSaveRef.current = setTimeout(() => {
        onReportSave?.(internalTemplate);
      }, 2000);
      
      return () => {
        if (autoSaveRef.current) {
          clearTimeout(autoSaveRef.current);
        }
      };
    }
  }, [internalTemplate, autoSave, readonly, onReportSave]);

  // Generate preview data when fields change
  useEffect(() => {
    generatePreviewData();
  }, [generatePreviewData]);

  // Validate template on changes
  useEffect(() => {
    validateTemplate();
  }, [validateTemplate]);

  // Render data sources panel
  const renderDataSourcesPanel = () => (
    <div className="p-4" data-testid="data-sources-panel">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-medium">Data Sources</h3>
        {!readonly && (
          <button
            className="px-2 py-1 text-xs bg-blue-500 text-white rounded hover:bg-blue-600"
            onClick={handleDataSourceAdd}
            data-testid="add-data-source"
          >
            + Add
          </button>
        )}
      </div>
      
      <div className="space-y-2">
        {internalTemplate.dataSources.map(ds => (
          <div
            key={ds.id}
            className={cn(
              "p-2 border border-gray-200 rounded cursor-pointer hover:bg-gray-50",
              selectedDataSource === ds.id && "border-blue-500 bg-blue-50"
            )}
            onClick={() => setSelectedDataSource(ds.id)}
            data-testid={`data-source-${ds.id}`}
          >
            <div className="font-medium text-sm">{ds.name}</div>
            <div className="text-xs text-gray-500">{ds.type}</div>
            <div className="text-xs text-gray-400">{ds.fields.length} fields</div>
          </div>
        ))}
      </div>
      
      {availableFields.length > 0 && (
        <div className="mt-6">
          <h4 className="text-sm font-medium mb-2">Available Fields</h4>
          <div className="space-y-1 max-h-48 overflow-y-auto">
            {availableFields.map(field => (
              <div
                key={field.id}
                className="p-2 border border-gray-200 rounded cursor-grab hover:bg-gray-50"
                draggable
                onDragStart={(e) => handleDragStart(e, 'availableField', field)}
                onDragEnd={handleDragEnd}
                data-testid={`available-field-${field.id}`}
              >
                <div className="text-xs font-medium">{field.label}</div>
                <div className="text-xs text-gray-500">{field.type}</div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );

  // Render fields panel
  const renderFieldsPanel = () => (
    <div 
      className="p-4"
      onDragOver={(e) => e.preventDefault()}
      onDrop={(e) => handleDrop(e, 'fields')}
      data-testid="fields-panel"
    >
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-medium">Report Fields</h3>
        <div className="text-xs text-gray-500">{internalTemplate.fields.length} fields</div>
      </div>
      
      {internalTemplate.fields.length === 0 ? (
        <div className="text-center py-8 text-gray-500 border-2 border-dashed border-gray-300 rounded">
          <div className="text-sm">Drop fields here</div>
          <div className="text-xs mt-1">Drag fields from available fields to add them</div>
        </div>
      ) : (
        <div className="space-y-2">
          {internalTemplate.fields.map(field => (
            <div
              key={field.id}
              className={cn(
                "p-2 border border-gray-200 rounded cursor-pointer hover:bg-gray-50",
                selectedField === field.id && "border-blue-500 bg-blue-50"
              )}
              onClick={() => setSelectedField(field.id)}
              data-testid={`report-field-${field.id}`}
            >
              <div className="flex items-center justify-between">
                <div>
                  <div className="text-sm font-medium">{field.label}</div>
                  <div className="text-xs text-gray-500">{field.type}</div>
                </div>
                <div className="flex space-x-1">
                  {!readonly && (
                    <>
                      <button
                        className="text-xs text-blue-600 hover:text-blue-800"
                        onClick={(e) => {
                          e.stopPropagation();
                          handleFilterAdd(field);
                        }}
                        data-testid={`add-filter-${field.id}`}
                      >
                        Filter
                      </button>
                      <button
                        className="text-xs text-red-600 hover:text-red-800"
                        onClick={(e) => {
                          e.stopPropagation();
                          const updatedTemplate = {
                            ...internalTemplate,
                            fields: internalTemplate.fields.filter(f => f.id !== field.id)
                          };
                          setInternalTemplate(updatedTemplate);
                          onTemplateChange?.(updatedTemplate);
                          onFieldDelete?.(field.id);
                        }}
                        data-testid={`delete-field-${field.id}`}
                      >
                        Remove
                      </button>
                    </>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );

  // Render filters panel
  const renderFiltersPanel = () => (
    <div className="p-4" data-testid="filters-panel">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-medium">Filters</h3>
        <div className="text-xs text-gray-500">{internalTemplate.filters.length} filters</div>
      </div>
      
      {internalTemplate.filters.length === 0 ? (
        <div className="text-center py-8 text-gray-500">
          <div className="text-sm">No filters configured</div>
          <div className="text-xs mt-1">Add filters from the fields panel</div>
        </div>
      ) : (
        <div className="space-y-2">
          {internalTemplate.filters.map(filter => (
            <div
              key={filter.id}
              className="p-2 border border-gray-200 rounded"
              data-testid={`report-filter-${filter.id}`}
            >
              <div className="flex items-center justify-between">
                <div>
                  <div className="text-sm font-medium">{filter.label}</div>
                  <div className="text-xs text-gray-500">
                    {filter.operator} {filter.value && `"${filter.value}"`}
                  </div>
                </div>
                {!readonly && (
                  <button
                    className="text-xs text-red-600 hover:text-red-800"
                    onClick={() => {
                      const updatedTemplate = {
                        ...internalTemplate,
                        filters: internalTemplate.filters.filter(f => f.id !== filter.id)
                      };
                      setInternalTemplate(updatedTemplate);
                      onTemplateChange?.(updatedTemplate);
                      onFilterDelete?.(filter.id);
                    }}
                    data-testid={`delete-filter-${filter.id}`}
                  >
                    Remove
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );

  // Render visualizations panel
  const renderVisualizationsPanel = () => (
    <div 
      className="p-4"
      onDragOver={(e) => e.preventDefault()}
      onDrop={(e) => handleDrop(e, 'visualizations')}
      data-testid="visualizations-panel"
    >
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-medium">Visualizations</h3>
        <div className="text-xs text-gray-500">{internalTemplate.visualizations.length} charts</div>
      </div>
      
      <div className="mb-4">
        <h4 className="text-xs font-medium mb-2 text-gray-600">Chart Types</h4>
        <div className="grid grid-cols-2 gap-2">
          {chartTypes.map(chartType => (
            <div
              key={chartType.id}
              className="p-2 border border-gray-200 rounded cursor-grab hover:bg-gray-50 text-center"
              draggable
              onDragStart={(e) => handleDragStart(e, 'chartType', chartType)}
              onDragEnd={handleDragEnd}
              data-testid={`chart-type-${chartType.id}`}
            >
              <div className="text-lg">{chartType.icon}</div>
              <div className="text-xs mt-1">{chartType.name}</div>
            </div>
          ))}
        </div>
      </div>
      
      {internalTemplate.visualizations.length === 0 ? (
        <div className="text-center py-8 text-gray-500 border-2 border-dashed border-gray-300 rounded">
          <div className="text-sm">Drop chart types here</div>
          <div className="text-xs mt-1">Drag chart types to create visualizations</div>
        </div>
      ) : (
        <div className="space-y-2">
          {internalTemplate.visualizations.map(viz => (
            <div
              key={viz.id}
              className={cn(
                "p-2 border border-gray-200 rounded cursor-pointer hover:bg-gray-50",
                selectedVisualization === viz.id && "border-blue-500 bg-blue-50"
              )}
              onClick={() => setSelectedVisualization(viz.id)}
              data-testid={`visualization-${viz.id}`}
            >
              <div className="flex items-center justify-between">
                <div>
                  <div className="text-sm font-medium">{viz.title}</div>
                  <div className="text-xs text-gray-500">{viz.type}</div>
                </div>
                {!readonly && (
                  <button
                    className="text-xs text-red-600 hover:text-red-800"
                    onClick={(e) => {
                      e.stopPropagation();
                      const updatedTemplate = {
                        ...internalTemplate,
                        visualizations: internalTemplate.visualizations.filter(v => v.id !== viz.id)
                      };
                      setInternalTemplate(updatedTemplate);
                      onTemplateChange?.(updatedTemplate);
                      onVisualizationDelete?.(viz.id);
                    }}
                    data-testid={`delete-visualization-${viz.id}`}
                  >
                    Remove
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );

  // Render settings panel
  const renderSettingsPanel = () => (
    <div className="p-4" data-testid="settings-panel">
      <h3 className="text-sm font-medium mb-4">Report Settings</h3>
      
      <div className="space-y-4">
        <div>
          <label className="block text-xs font-medium text-gray-700 mb-1">
            Report Name
          </label>
          <input
            type="text"
            value={internalTemplate.name}
            onChange={(e) => {
              const updatedTemplate = { ...internalTemplate, name: e.target.value };
              setInternalTemplate(updatedTemplate);
              onTemplateChange?.(updatedTemplate);
            }}
            className="w-full px-2 py-1 text-sm border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500"
            disabled={readonly}
            data-testid="report-name-input"
          />
        </div>
        
        <div>
          <label className="block text-xs font-medium text-gray-700 mb-1">
            Category
          </label>
          <select
            value={internalTemplate.category}
            onChange={(e) => {
              const updatedTemplate = { ...internalTemplate, category: e.target.value };
              setInternalTemplate(updatedTemplate);
              onTemplateChange?.(updatedTemplate);
            }}
            className="w-full px-2 py-1 text-sm border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500"
            disabled={readonly}
            data-testid="report-category-select"
          >
            <option value="General">General</option>
            <option value="Sales">Sales</option>
            <option value="Marketing">Marketing</option>
            <option value="Finance">Finance</option>
            <option value="Operations">Operations</option>
            <option value="HR">Human Resources</option>
          </select>
        </div>
        
        <div>
          <label className="block text-xs font-medium text-gray-700 mb-1">
            Theme
          </label>
          <select
            value={internalTemplate.theme}
            onChange={(e) => {
              const updatedTemplate = { ...internalTemplate, theme: e.target.value as any };
              setInternalTemplate(updatedTemplate);
              onTemplateChange?.(updatedTemplate);
            }}
            className="w-full px-2 py-1 text-sm border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500"
            disabled={readonly}
            data-testid="report-theme-select"
          >
            <option value="default">Default</option>
            <option value="professional">Professional</option>
            <option value="modern">Modern</option>
            <option value="dark">Dark</option>
            <option value="colorful">Colorful</option>
          </select>
        </div>
        
        <div>
          <label className="block text-xs font-medium text-gray-700 mb-1">
            Layout
          </label>
          <select
            value={internalTemplate.layout}
            onChange={(e) => {
              const updatedTemplate = { ...internalTemplate, layout: e.target.value as any };
              setInternalTemplate(updatedTemplate);
              onTemplateChange?.(updatedTemplate);
            }}
            className="w-full px-2 py-1 text-sm border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500"
            disabled={readonly}
            data-testid="report-layout-select"
          >
            <option value="grid">Grid</option>
            <option value="free">Free Form</option>
            <option value="tabs">Tabs</option>
            <option value="sections">Sections</option>
          </select>
        </div>
        
        <div>
          <label className="block text-xs font-medium text-gray-700 mb-1">
            Export Formats
          </label>
          <div className="space-y-1">
            {['pdf', 'excel', 'csv', 'word', 'powerpoint', 'json'].map(format => (
              <label key={format} className="flex items-center text-xs">
                <input
                  type="checkbox"
                  checked={internalTemplate.exportFormats.includes(format as any)}
                  onChange={(e) => {
                    const formats = e.target.checked
                      ? [...internalTemplate.exportFormats, format as any]
                      : internalTemplate.exportFormats.filter(f => f !== format);
                    const updatedTemplate = { ...internalTemplate, exportFormats: formats };
                    setInternalTemplate(updatedTemplate);
                    onTemplateChange?.(updatedTemplate);
                  }}
                  className="mr-2"
                  disabled={readonly}
                  data-testid={`export-format-${format}`}
                />
                {format.toUpperCase()}
              </label>
            ))}
          </div>
        </div>
      </div>
    </div>
  );

  // Render toolbar
  const renderToolbar = () => (
    <div className="flex items-center justify-between p-2 border-b bg-gray-50" data-testid="report-toolbar">
      <div className="flex items-center space-x-2">
        <button
          className="px-3 py-1 text-sm bg-blue-500 text-white rounded hover:bg-blue-600 disabled:opacity-50"
          onClick={() => setShowPreview(!showPreview)}
          data-testid="toggle-preview"
        >
          {showPreview ? 'Design' : 'Preview'}
        </button>
        
        {!readonly && (
          <>
            <button
              className="px-3 py-1 text-sm bg-green-500 text-white rounded hover:bg-green-600"
              onClick={() => onReportSave?.(internalTemplate)}
              data-testid="save-report"
            >
              Save
            </button>
            
            <button
              className="px-3 py-1 text-sm bg-purple-500 text-white rounded hover:bg-purple-600"
              onClick={() => validateTemplate()}
              data-testid="validate-report"
            >
              Validate
            </button>
          </>
        )}
        
        {exportEnabled && (
          <button
            className="px-3 py-1 text-sm bg-orange-500 text-white rounded hover:bg-orange-600"
            onClick={() => onReportExport?.('pdf', { template: internalTemplate, data: previewData })}
            disabled={validationErrors.length > 0}
            data-testid="export-report"
          >
            Export
          </button>
        )}
        
        <button
          className="px-3 py-1 text-sm bg-gray-500 text-white rounded hover:bg-gray-600"
          onClick={() => {
            onDataRefresh?.();
            generatePreviewData();
          }}
          data-testid="refresh-data"
        >
          Refresh
        </button>
      </div>
      
      <div className="flex items-center space-x-4 text-xs text-gray-500">
        {validationErrors.length > 0 && (
          <div className="text-red-500" data-testid="validation-status">
            {validationErrors.length} error{validationErrors.length !== 1 ? 's' : ''}
          </div>
        )}
        
        <div>
          {internalTemplate.dataSources.length} sources, {internalTemplate.fields.length} fields, {internalTemplate.visualizations.length} charts
        </div>
        
        {autoSave && !readonly && (
          <div className="text-green-600">Auto-save enabled</div>
        )}
      </div>
    </div>
  );

  // Render preview
  const renderPreview = () => (
    <div className="p-4" data-testid="report-preview">
      <div className="mb-4">
        <h2 className="text-lg font-bold">{internalTemplate.name}</h2>
        {internalTemplate.category && (
          <div className="text-sm text-gray-600">{internalTemplate.category}</div>
        )}
      </div>
      
      {previewData.length > 0 && internalTemplate.fields.length > 0 ? (
        <div className="overflow-x-auto">
          <table className="w-full border border-gray-200 rounded">
            <thead className="bg-gray-50">
              <tr>
                {internalTemplate.fields.filter(f => f.visible !== false).map(field => (
                  <th
                    key={field.id}
                    className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider border-b"
                  >
                    {field.label}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {previewData.slice(0, 10).map((row, index) => (
                <tr key={index} className="hover:bg-gray-50">
                  {internalTemplate.fields.filter(f => f.visible !== false).map(field => (
                    <td
                      key={field.id}
                      className="px-3 py-2 whitespace-nowrap text-sm text-gray-900 border-b"
                    >
                      {String(row[field.id] || '')}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
          
          {previewData.length > 10 && (
            <div className="text-center text-sm text-gray-500 mt-2">
              Showing 10 of {previewData.length} records
            </div>
          )}
        </div>
      ) : (
        <div className="text-center py-8 text-gray-500">
          <div className="text-sm">No preview data available</div>
          <div className="text-xs mt-1">Configure data sources and fields to see preview</div>
        </div>
      )}
    </div>
  );

  return (
    <div
      ref={builderRef}
      className={cn(
        "flex h-full border border-gray-200 rounded-lg bg-white",
        theme === 'dark' && "bg-gray-900 border-gray-700",
        className
      )}
      style={{ width, height, ...style }}
      data-testid={dataTestId}
    >
      {/* Sidebar */}
      {!showPreview && (
        <div className="w-80 border-r border-gray-200 flex flex-col">
          {/* Panel tabs */}
          <div className="flex border-b border-gray-200" data-testid="panel-tabs">
            {[
              { id: 'data', label: 'Data', icon: '🗄️' },
              { id: 'fields', label: 'Fields', icon: '📊' },
              { id: 'filters', label: 'Filters', icon: '🔍' },
              { id: 'visualizations', label: 'Charts', icon: '📈' },
              { id: 'settings', label: 'Settings', icon: '⚙️' }
            ].map(panel => (
              <button
                key={panel.id}
                className={cn(
                  "flex-1 px-2 py-2 text-xs font-medium border-b-2 transition-colors",
                  selectedPanel === panel.id
                    ? "border-blue-500 text-blue-600 bg-blue-50"
                    : "border-transparent text-gray-500 hover:text-gray-700"
                )}
                onClick={() => setSelectedPanel(panel.id as any)}
                data-testid={`panel-tab-${panel.id}`}
              >
                <div className="text-center">
                  <div>{panel.icon}</div>
                  <div className="mt-1">{panel.label}</div>
                </div>
              </button>
            ))}
          </div>
          
          {/* Panel content */}
          <div className="flex-1 overflow-y-auto">
            {selectedPanel === 'data' && renderDataSourcesPanel()}
            {selectedPanel === 'fields' && renderFieldsPanel()}
            {selectedPanel === 'filters' && renderFiltersPanel()}
            {selectedPanel === 'visualizations' && renderVisualizationsPanel()}
            {selectedPanel === 'settings' && renderSettingsPanel()}
          </div>
        </div>
      )}
      
      {/* Main content */}
      <div className="flex-1 flex flex-col">
        {renderToolbar()}
        
        <div className="flex-1 overflow-auto">
          {showPreview ? renderPreview() : (
            <div className="p-4 text-center text-gray-500">
              <div className="text-lg mb-2">📊</div>
              <div className="text-sm">Report Design Canvas</div>
              <div className="text-xs mt-1">Configure your report using the panels on the left</div>
            </div>
          )}
        </div>
        
        {/* Validation errors */}
        {validationErrors.length > 0 && (
          <div className="p-3 bg-red-50 border-t border-red-200" data-testid="validation-errors">
            <div className="text-sm font-medium text-red-800 mb-1">Validation Errors:</div>
            <ul className="text-xs text-red-600 space-y-1">
              {validationErrors.map((error, index) => (
                <li key={index}>• {error}</li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  );
};

export default ReportBuilder;