import React, { useState, useRef, useCallback, useEffect, useMemo } from 'react';
import { cn } from '@/lib/utils';

export interface Metric {
  id: string;
  name: string;
  value: number | string;
  previousValue?: number | string;
  unit?: string;
  format?: 'number' | 'percentage' | 'currency' | 'duration' | 'bytes';
  trend?: 'up' | 'down' | 'neutral';
  change?: number;
  changeType?: 'absolute' | 'percentage';
  target?: number;
  category?: string;
  description?: string;
  icon?: React.ReactNode;
  color?: string;
  precision?: number;
  threshold?: {
    good: number;
    warning: number;
    critical: number;
  };
}

export interface ChartData {
  id: string;
  title: string;
  type: 'line' | 'bar' | 'area' | 'pie' | 'doughnut' | 'scatter' | 'heatmap' | 'gauge';
  data: Array<{
    x: string | number | Date;
    y: number;
    category?: string;
    label?: string;
  }>;
  series?: Array<{
    name: string;
    data: number[];
    color?: string;
  }>;
  config?: {
    xAxis?: string;
    yAxis?: string;
    showLegend?: boolean;
    showGrid?: boolean;
    stacked?: boolean;
    smooth?: boolean;
    colors?: string[];
    height?: number;
  };
}

export interface Widget {
  id: string;
  type: 'metric' | 'chart' | 'table' | 'text' | 'iframe' | 'custom';
  title: string;
  description?: string;
  position: { row: number; col: number; width: number; height: number };
  data?: Metric[] | ChartData | any[];
  config?: Record<string, any>;
  refreshInterval?: number;
  loading?: boolean;
  error?: string;
  visible?: boolean;
  minimized?: boolean;
}

export interface Dashboard {
  id: string;
  name: string;
  description?: string;
  widgets: Widget[];
  layout: 'grid' | 'flex' | 'masonry';
  theme?: 'light' | 'dark' | 'auto';
  refreshInterval?: number;
  filters?: Record<string, any>;
  dateRange?: {
    start: Date;
    end: Date;
    preset?: 'today' | 'yesterday' | 'week' | 'month' | 'quarter' | 'year' | 'custom';
  };
  tags?: string[];
  isPublic?: boolean;
  owner?: string;
  lastUpdated?: Date;
}

export interface Filter {
  id: string;
  name: string;
  type: 'select' | 'multiselect' | 'date' | 'daterange' | 'number' | 'text' | 'boolean';
  options?: Array<{ value: any; label: string }>;
  value?: any;
  defaultValue?: any;
  required?: boolean;
  visible?: boolean;
}

export interface TimeRange {
  start: Date;
  end: Date;
  preset?: string;
  label?: string;
}

export interface AnalyticsDashboardProps {
  dashboard?: Dashboard;
  widgets?: Widget[];
  metrics?: Metric[];
  charts?: ChartData[];
  filters?: Filter[];
  timeRange?: TimeRange;
  realTime?: boolean;
  refreshInterval?: number;
  enableEdit?: boolean;
  enableFilters?: boolean;
  enableExport?: boolean;
  enableFullscreen?: boolean;
  enableSharing?: boolean;
  gridColumns?: number;
  gridRowHeight?: number;
  compactMode?: boolean;
  showHeader?: boolean;
  showFooter?: boolean;
  autoRefresh?: boolean;
  width?: number | string;
  height?: number | string;
  className?: string;
  style?: React.CSSProperties;
  onWidgetUpdate?: (widgetId: string, updates: Partial<Widget>) => void;
  onWidgetAdd?: (widget: Widget) => void;
  onWidgetRemove?: (widgetId: string) => void;
  onDashboardUpdate?: (dashboard: Dashboard) => void;
  onFilterChange?: (filterId: string, value: any) => void;
  onTimeRangeChange?: (timeRange: TimeRange) => void;
  onRefresh?: () => void;
  onExport?: (format: 'pdf' | 'png' | 'csv' | 'json') => void;
  onError?: (error: Error) => void;
  'data-testid'?: string;
}

export const AnalyticsDashboard: React.FC<AnalyticsDashboardProps> = ({
  dashboard,
  widgets = [],
  metrics = [],
  charts = [],
  filters = [],
  timeRange,
  realTime = false,
  refreshInterval = 30000,
  enableEdit = false,
  enableFilters = true,
  enableExport = true,
  enableFullscreen = true,
  enableSharing = true,
  gridColumns = 12,
  gridRowHeight = 80,
  compactMode = false,
  showHeader = true,
  showFooter = true,
  autoRefresh = true,
  width = '100%',
  height = '100vh',
  className,
  style,
  onWidgetUpdate,
  onWidgetAdd,
  onWidgetRemove,
  onDashboardUpdate,
  onFilterChange,
  onTimeRangeChange,
  onRefresh,
  onExport,
  onError,
  'data-testid': dataTestId = 'analytics-dashboard'
}) => {
  const [internalDashboard, setInternalDashboard] = useState<Dashboard>(
    dashboard || {
      id: 'default',
      name: 'Analytics Dashboard',
      widgets: [],
      layout: 'grid'
    }
  );
  
  const [selectedTimeRange, setSelectedTimeRange] = useState<TimeRange>(
    timeRange || {
      start: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000),
      end: new Date(),
      preset: 'week',
      label: 'Last 7 days'
    }
  );
  
  const [activeFilters, setActiveFilters] = useState<Record<string, any>>({});
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [editMode, setEditMode] = useState(false);
  const [selectedWidget, setSelectedWidget] = useState<string | null>(null);
  const [showFilters, setShowFilters] = useState(true);
  const [isLoading, setIsLoading] = useState(false);
  const [lastRefresh, setLastRefresh] = useState<Date>(new Date());
  const [draggedWidget, setDraggedWidget] = useState<string | null>(null);

  const dashboardRef = useRef<HTMLDivElement>(null);
  const refreshIntervalRef = useRef<NodeJS.Timeout | null>(null);

  // Time range presets
  const timePresets = [
    { id: 'today', label: 'Today', days: 0 },
    { id: 'yesterday', label: 'Yesterday', days: 1 },
    { id: 'week', label: 'Last 7 days', days: 7 },
    { id: 'month', label: 'Last 30 days', days: 30 },
    { id: 'quarter', label: 'Last 90 days', days: 90 },
    { id: 'year', label: 'Last 365 days', days: 365 }
  ];

  // Format metric value
  const formatMetricValue = useCallback((metric: Metric): string => {
    const value = typeof metric.value === 'number' ? metric.value : parseFloat(metric.value.toString());
    const precision = metric.precision || 0;

    switch (metric.format) {
      case 'percentage':
        return `${value.toFixed(precision)}%`;
      case 'currency':
        return new Intl.NumberFormat('en-US', {
          style: 'currency',
          currency: 'USD',
          minimumFractionDigits: precision,
          maximumFractionDigits: precision
        }).format(value);
      case 'bytes':
        const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
        const i = Math.floor(Math.log(value) / Math.log(1024));
        return `${(value / Math.pow(1024, i)).toFixed(precision)} ${sizes[i]}`;
      case 'duration':
        const hours = Math.floor(value / 3600);
        const minutes = Math.floor((value % 3600) / 60);
        const seconds = Math.floor(value % 60);
        return `${hours}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
      case 'number':
      default:
        return new Intl.NumberFormat('en-US', {
          minimumFractionDigits: precision,
          maximumFractionDigits: precision
        }).format(value);
    }
  }, []);

  // Get metric status based on thresholds
  const getMetricStatus = useCallback((metric: Metric): 'good' | 'warning' | 'critical' | 'neutral' => {
    if (!metric.threshold) return 'neutral';
    
    const value = typeof metric.value === 'number' ? metric.value : parseFloat(metric.value.toString());
    
    if (value >= metric.threshold.good) return 'good';
    if (value >= metric.threshold.warning) return 'warning';
    if (value >= metric.threshold.critical) return 'critical';
    
    return 'neutral';
  }, []);

  // Calculate metric change
  const calculateMetricChange = useCallback((metric: Metric): { change: number; changeType: string } => {
    if (!metric.previousValue) return { change: 0, changeType: 'neutral' };
    
    const current = typeof metric.value === 'number' ? metric.value : parseFloat(metric.value.toString());
    const previous = typeof metric.previousValue === 'number' ? metric.previousValue : parseFloat(metric.previousValue.toString());
    
    const change = metric.changeType === 'percentage' 
      ? ((current - previous) / previous) * 100
      : current - previous;
    
    const changeType = change > 0 ? 'positive' : change < 0 ? 'negative' : 'neutral';
    
    return { change: Math.abs(change), changeType };
  }, []);

  // Handle time range change
  const handleTimeRangeChange = useCallback((preset: string) => {
    const presetConfig = timePresets.find(p => p.id === preset);
    if (presetConfig) {
      const end = new Date();
      const start = new Date(end.getTime() - presetConfig.days * 24 * 60 * 60 * 1000);
      
      const newTimeRange: TimeRange = {
        start,
        end,
        preset,
        label: presetConfig.label
      };
      
      setSelectedTimeRange(newTimeRange);
      onTimeRangeChange?.(newTimeRange);
    }
  }, [onTimeRangeChange]);

  // Handle filter change
  const handleFilterChange = useCallback((filterId: string, value: any) => {
    setActiveFilters(prev => ({ ...prev, [filterId]: value }));
    onFilterChange?.(filterId, value);
  }, [onFilterChange]);

  // Handle refresh
  const handleRefresh = useCallback(async () => {
    setIsLoading(true);
    try {
      await onRefresh?.();
      setLastRefresh(new Date());
    } catch (error) {
      onError?.(error as Error);
    } finally {
      setIsLoading(false);
    }
  }, [onRefresh, onError]);

  // Auto refresh
  useEffect(() => {
    if (autoRefresh && !realTime) {
      refreshIntervalRef.current = setInterval(handleRefresh, refreshInterval);
      
      return () => {
        if (refreshIntervalRef.current) {
          clearInterval(refreshIntervalRef.current);
        }
      };
    }
  }, [autoRefresh, realTime, refreshInterval, handleRefresh]);

  // Handle fullscreen
  const handleFullscreen = useCallback(() => {
    if (!document.fullscreenElement) {
      dashboardRef.current?.requestFullscreen();
      setIsFullscreen(true);
    } else {
      document.exitFullscreen();
      setIsFullscreen(false);
    }
  }, []);

  // Handle widget drag
  const handleWidgetDrag = useCallback((widgetId: string, position: { row: number; col: number }) => {
    if (!enableEdit) return;
    
    const widget = widgets.find(w => w.id === widgetId);
    if (widget) {
      const updatedWidget = { ...widget, position: { ...widget.position, ...position } };
      onWidgetUpdate?.(widgetId, updatedWidget);
    }
  }, [enableEdit, widgets, onWidgetUpdate]);

  // Render metric widget
  const renderMetricWidget = useCallback((widget: Widget) => {
    const widgetMetrics = widget.data as Metric[] || [];
    
    return (
      <div className="h-full p-4">
        <div className="grid grid-cols-1 gap-4 h-full">
          {widgetMetrics.map(metric => {
            const status = getMetricStatus(metric);
            const { change, changeType } = calculateMetricChange(metric);
            
            return (
              <div
                key={metric.id}
                className={cn(
                  "p-4 rounded-lg border",
                  status === 'good' && "border-green-200 bg-green-50",
                  status === 'warning' && "border-yellow-200 bg-yellow-50",
                  status === 'critical' && "border-red-200 bg-red-50",
                  status === 'neutral' && "border-gray-200 bg-gray-50"
                )}
                data-testid={`metric-${metric.id}`}
              >
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center space-x-2">
                    {metric.icon && <span className="text-lg">{metric.icon}</span>}
                    <h3 className="text-sm font-medium text-gray-700">{metric.name}</h3>
                  </div>
                  {metric.trend && (
                    <div className={cn(
                      "text-xs px-2 py-1 rounded-full",
                      metric.trend === 'up' && "bg-green-100 text-green-800",
                      metric.trend === 'down' && "bg-red-100 text-red-800",
                      metric.trend === 'neutral' && "bg-gray-100 text-gray-800"
                    )}>
                      {metric.trend === 'up' ? '↗' : metric.trend === 'down' ? '↘' : '→'}
                    </div>
                  )}
                </div>
                
                <div className="flex items-end justify-between">
                  <div>
                    <div className="text-2xl font-bold" style={{ color: metric.color }}>
                      {formatMetricValue(metric)}
                    </div>
                    {metric.unit && (
                      <div className="text-xs text-gray-500">{metric.unit}</div>
                    )}
                  </div>
                  
                  {change > 0 && (
                    <div className={cn(
                      "text-sm",
                      changeType === 'positive' && "text-green-600",
                      changeType === 'negative' && "text-red-600",
                      changeType === 'neutral' && "text-gray-600"
                    )}>
                      {changeType === 'positive' ? '+' : changeType === 'negative' ? '-' : ''}
                      {formatMetricValue({ ...metric, value: change })}
                    </div>
                  )}
                </div>
                
                {metric.target && (
                  <div className="mt-2 w-full bg-gray-200 rounded-full h-2">
                    <div
                      className="bg-blue-500 h-2 rounded-full"
                      style={{
                        width: `${Math.min((parseFloat(metric.value.toString()) / metric.target) * 100, 100)}%`
                      }}
                    />
                  </div>
                )}
                
                {metric.description && (
                  <div className="mt-2 text-xs text-gray-600">{metric.description}</div>
                )}
              </div>
            );
          })}
        </div>
      </div>
    );
  }, [getMetricStatus, calculateMetricChange, formatMetricValue]);

  // Render chart widget
  const renderChartWidget = useCallback((widget: Widget) => {
    const chartData = widget.data as ChartData;
    
    return (
      <div className="h-full p-4">
        <div className="h-full flex flex-col">
          <div className="mb-4">
            <h3 className="text-lg font-semibold">{chartData?.title || widget.title}</h3>
          </div>
          
          <div className="flex-1 bg-gray-100 rounded-lg flex items-center justify-center">
            <div className="text-center text-gray-500">
              <div className="text-4xl mb-2">📊</div>
              <div className="text-sm">Chart: {chartData?.type || 'Unknown'}</div>
              <div className="text-xs mt-1">{chartData?.data?.length || 0} data points</div>
            </div>
          </div>
        </div>
      </div>
    );
  }, []);

  // Render widget
  const renderWidget = useCallback((widget: Widget) => {
    const isSelected = selectedWidget === widget.id;
    
    return (
      <div
        key={widget.id}
        className={cn(
          "bg-white border border-gray-200 rounded-lg shadow-sm transition-all duration-200",
          isSelected && "ring-2 ring-blue-500",
          widget.minimized && "opacity-50",
          enableEdit && "cursor-move hover:shadow-md"
        )}
        style={{
          gridColumn: `span ${widget.position.width}`,
          gridRow: `span ${widget.position.height}`,
          minHeight: widget.position.height * gridRowHeight
        }}
        onClick={() => enableEdit && setSelectedWidget(widget.id)}
        data-testid={`widget-${widget.id}`}
      >
        {/* Widget header */}
        <div className="flex items-center justify-between p-3 border-b border-gray-200">
          <h2 className="text-sm font-medium truncate">{widget.title}</h2>
          <div className="flex items-center space-x-1">
            {widget.loading && (
              <div className="animate-spin w-4 h-4 border-2 border-blue-500 border-t-transparent rounded-full" />
            )}
            {enableEdit && (
              <>
                <button
                  className="p-1 text-gray-400 hover:text-gray-600"
                  onClick={(e) => {
                    e.stopPropagation();
                    onWidgetUpdate?.(widget.id, { minimized: !widget.minimized });
                  }}
                  data-testid={`minimize-widget-${widget.id}`}
                >
                  {widget.minimized ? '📈' : '📉'}
                </button>
                <button
                  className="p-1 text-gray-400 hover:text-red-600"
                  onClick={(e) => {
                    e.stopPropagation();
                    onWidgetRemove?.(widget.id);
                  }}
                  data-testid={`remove-widget-${widget.id}`}
                >
                  ✕
                </button>
              </>
            )}
          </div>
        </div>
        
        {/* Widget content */}
        {!widget.minimized && (
          <div className="flex-1">
            {widget.error ? (
              <div className="p-4 text-center text-red-600">
                <div className="text-2xl mb-2">⚠️</div>
                <div className="text-sm">{widget.error}</div>
              </div>
            ) : widget.loading ? (
              <div className="p-4 text-center text-gray-500">
                <div className="animate-pulse">Loading...</div>
              </div>
            ) : (
              <>
                {widget.type === 'metric' && renderMetricWidget(widget)}
                {widget.type === 'chart' && renderChartWidget(widget)}
                {widget.type === 'text' && (
                  <div className="p-4">
                    <div className="text-gray-700">{widget.description}</div>
                  </div>
                )}
                {widget.type === 'custom' && (
                  <div className="p-4 text-center text-gray-500">
                    Custom widget: {widget.title}
                  </div>
                )}
              </>
            )}
          </div>
        )}
      </div>
    );
  }, [selectedWidget, enableEdit, gridRowHeight, onWidgetUpdate, onWidgetRemove, renderMetricWidget, renderChartWidget]);

  // Render header
  const renderHeader = () => {
    if (!showHeader) return null;
    
    return (
      <div className="flex items-center justify-between p-4 border-b border-gray-200 bg-white" data-testid="dashboard-header">
        <div className="flex items-center space-x-4">
          <div>
            <h1 className="text-xl font-semibold">{internalDashboard.name}</h1>
            {internalDashboard.description && (
              <p className="text-sm text-gray-600">{internalDashboard.description}</p>
            )}
          </div>
          
          {realTime && (
            <div className="flex items-center space-x-2 text-sm text-green-600">
              <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
              <span>Live</span>
            </div>
          )}
        </div>
        
        <div className="flex items-center space-x-2">
          {/* Time range selector */}
          <div className="flex items-center space-x-2">
            <select
              value={selectedTimeRange.preset || 'custom'}
              onChange={(e) => handleTimeRangeChange(e.target.value)}
              className="text-sm border border-gray-300 rounded px-2 py-1"
              data-testid="time-range-select"
            >
              {timePresets.map(preset => (
                <option key={preset.id} value={preset.id}>
                  {preset.label}
                </option>
              ))}
              <option value="custom">Custom</option>
            </select>
          </div>
          
          {/* Filter toggle */}
          {enableFilters && filters.length > 0 && (
            <button
              className={cn(
                "px-3 py-2 text-sm border rounded transition-colors",
                showFilters
                  ? "bg-blue-500 text-white border-blue-500"
                  : "bg-white text-gray-700 border-gray-300 hover:bg-gray-50"
              )}
              onClick={() => setShowFilters(!showFilters)}
              data-testid="toggle-filters"
            >
              Filters {showFilters ? '✓' : ''}
            </button>
          )}
          
          {/* Refresh button */}
          <button
            className="px-3 py-2 text-sm bg-gray-500 text-white rounded hover:bg-gray-600 disabled:opacity-50"
            onClick={handleRefresh}
            disabled={isLoading}
            data-testid="refresh-button"
          >
            {isLoading ? '⟳' : '🔄'} Refresh
          </button>
          
          {/* Edit mode toggle */}
          {enableEdit && (
            <button
              className={cn(
                "px-3 py-2 text-sm border rounded transition-colors",
                editMode
                  ? "bg-orange-500 text-white border-orange-500"
                  : "bg-white text-gray-700 border-gray-300 hover:bg-gray-50"
              )}
              onClick={() => setEditMode(!editMode)}
              data-testid="edit-mode-toggle"
            >
              {editMode ? 'Exit Edit' : 'Edit'}
            </button>
          )}
          
          {/* Export button */}
          {enableExport && (
            <button
              className="px-3 py-2 text-sm bg-green-500 text-white rounded hover:bg-green-600"
              onClick={() => onExport?.('pdf')}
              data-testid="export-button"
            >
              Export
            </button>
          )}
          
          {/* Fullscreen button */}
          {enableFullscreen && (
            <button
              className="px-3 py-2 text-sm bg-purple-500 text-white rounded hover:bg-purple-600"
              onClick={handleFullscreen}
              data-testid="fullscreen-button"
            >
              {isFullscreen ? '⤓' : '⤢'}
            </button>
          )}
        </div>
      </div>
    );
  };

  // Render filters
  const renderFilters = () => {
    if (!enableFilters || !showFilters || filters.length === 0) return null;
    
    return (
      <div className="p-4 border-b border-gray-200 bg-gray-50" data-testid="dashboard-filters">
        <div className="flex flex-wrap gap-4">
          {filters.map(filter => (
            <div key={filter.id} className="flex items-center space-x-2">
              <label className="text-sm font-medium text-gray-700">
                {filter.name}:
              </label>
              {filter.type === 'select' && (
                <select
                  value={activeFilters[filter.id] || filter.defaultValue || ''}
                  onChange={(e) => handleFilterChange(filter.id, e.target.value)}
                  className="text-sm border border-gray-300 rounded px-2 py-1"
                  data-testid={`filter-${filter.id}`}
                >
                  <option value="">All</option>
                  {filter.options?.map(option => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              )}
              {filter.type === 'text' && (
                <input
                  type="text"
                  value={activeFilters[filter.id] || filter.defaultValue || ''}
                  onChange={(e) => handleFilterChange(filter.id, e.target.value)}
                  className="text-sm border border-gray-300 rounded px-2 py-1"
                  placeholder={`Enter ${filter.name.toLowerCase()}`}
                  data-testid={`filter-${filter.id}`}
                />
              )}
              {filter.type === 'date' && (
                <input
                  type="date"
                  value={activeFilters[filter.id] || filter.defaultValue || ''}
                  onChange={(e) => handleFilterChange(filter.id, e.target.value)}
                  className="text-sm border border-gray-300 rounded px-2 py-1"
                  data-testid={`filter-${filter.id}`}
                />
              )}
            </div>
          ))}
        </div>
      </div>
    );
  };

  // Render footer
  const renderFooter = () => {
    if (!showFooter) return null;
    
    return (
      <div className="p-3 border-t border-gray-200 bg-gray-50 text-sm text-gray-600" data-testid="dashboard-footer">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <span>{widgets.length} widgets</span>
            <span>Last updated: {lastRefresh.toLocaleTimeString()}</span>
            {internalDashboard.owner && (
              <span>Owner: {internalDashboard.owner}</span>
            )}
          </div>
          
          {realTime && (
            <div className="text-green-600">
              Real-time updates enabled
            </div>
          )}
        </div>
      </div>
    );
  };

  return (
    <div
      ref={dashboardRef}
      className={cn(
        "flex flex-col bg-gray-100 min-h-screen",
        isFullscreen && "fixed inset-0 z-50",
        className
      )}
      style={{ width, height, ...style }}
      data-testid={dataTestId}
    >
      {renderHeader()}
      {renderFilters()}
      
      {/* Main dashboard content */}
      <div className="flex-1 overflow-auto p-4">
        {widgets.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-64 text-gray-500" data-testid="empty-dashboard">
            <div className="text-6xl mb-4">📊</div>
            <div className="text-xl mb-2">No widgets configured</div>
            <div className="text-sm">Add widgets to get started with your analytics dashboard</div>
            {enableEdit && (
              <button
                className="mt-4 px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
                onClick={() => {
                  const newWidget: Widget = {
                    id: `widget-${Date.now()}`,
                    type: 'metric',
                    title: 'Sample Metric',
                    position: { row: 1, col: 1, width: 3, height: 2 },
                    data: []
                  };
                  onWidgetAdd?.(newWidget);
                }}
                data-testid="add-sample-widget"
              >
                Add Sample Widget
              </button>
            )}
          </div>
        ) : (
          <div
            className={cn(
              "grid gap-4",
              compactMode ? "gap-2" : "gap-4"
            )}
            style={{
              gridTemplateColumns: `repeat(${gridColumns}, 1fr)`,
              gridAutoRows: `${gridRowHeight}px`
            }}
            data-testid="widgets-grid"
          >
            {widgets.filter(w => w.visible !== false).map(renderWidget)}
          </div>
        )}
      </div>
      
      {renderFooter()}
    </div>
  );
};

export default AnalyticsDashboard;