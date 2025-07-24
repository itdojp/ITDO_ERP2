import React, { useState, useRef, useCallback, useEffect, useMemo } from 'react';
import { cn } from '@/lib/utils';

export interface Widget {
  id: string;
  type: 'chart' | 'metric' | 'table' | 'text' | 'custom';
  title: string;
  data?: any;
  config?: any;
  loading?: boolean;
  error?: string;
  render?: () => React.ReactNode;
  group?: string;
}

export interface DashboardLayout {
  id: string;
  name: string;
  layout: 'grid' | 'masonry' | 'fixed';
  widgets: Widget[];
}

export interface DashboardTemplate {
  id: string;
  name: string;
  layout: 'grid' | 'masonry' | 'fixed';
  widgets: Widget[];
}

export interface DashboardNotification {
  id: string;
  type: 'info' | 'warning' | 'error' | 'success';
  message: string;
  timestamp: Date;
}

export interface DashboardAction {
  id: string;
  label: string;
  onClick: () => void;
}

export interface DashboardBreadcrumb {
  label: string;
  href: string;
}

export interface DashboardCollaborator {
  id: string;
  name: string;
  avatar: string;
  active: boolean;
}

export interface ContextMenuItem {
  label: string;
  icon?: React.ReactNode;
  onClick: (widgetId: string) => void;
  disabled?: boolean;
}

export interface DashboardProps {
  widgets?: Widget[];
  template?: DashboardTemplate;
  layout?: 'grid' | 'masonry' | 'fixed';
  columns?: { xs: number; sm: number; md: number; lg: number; xl: number };
  theme?: 'light' | 'dark' | 'auto';
  draggable?: boolean;
  resizable?: boolean;
  filterable?: boolean;
  searchable?: boolean;
  grouped?: boolean;
  configurable?: boolean;
  exportable?: boolean;
  shareable?: boolean;
  printable?: boolean;
  undoable?: boolean;
  responsive?: boolean;
  drillDownEnabled?: boolean;
  enablePerformanceMonitoring?: boolean;
  autoRefresh?: boolean;
  refreshInterval?: number;
  favorites?: string[];
  notifications?: DashboardNotification[];
  customActions?: DashboardAction[];
  breadcrumbs?: DashboardBreadcrumb[];
  collaborators?: DashboardCollaborator[];
  contextMenu?: ContextMenuItem[];
  gridSnap?: number;
  versionControlEnabled?: boolean;
  helpEnabled?: boolean;
  showTooltips?: boolean;
  ariaLabel?: string;
  ariaDescribedBy?: string;
  onWidgetReorder?: (fromIndex: number, toIndex: number) => void;
  onWidgetResize?: (widgetId: string, size: { width: number; height: number }) => void;
  onWidgetRefresh?: (widgetId: string) => void;
  onWidgetConfig?: (widgetId: string, config: any) => void;
  onFilterChange?: (filter: string) => void;
  onSearch?: (query: string) => void;
  onExport?: (format: string) => void;
  onShare?: () => void;
  onPrint?: () => void;
  onUndo?: () => void;
  onRedo?: () => void;
  onDrillDown?: (widgetId: string) => void;
  onPerformanceReport?: (metrics: any) => void;
  onAutoRefresh?: () => void;
  onFavoriteToggle?: (widgetId: string, isFavorite: boolean) => void;
  onVersionSave?: (version: any) => void;
  className?: string;
  'data-testid'?: string;
  'data-category'?: string;
  'data-id'?: string;
}

export const Dashboard = ({
  widgets = [],
  template,
  layout = 'grid',
  columns = { xs: 1, sm: 2, md: 3, lg: 4, xl: 6 },
  theme = 'light',
  draggable = false,
  resizable = false,
  filterable = false,
  searchable = false,
  grouped = false,
  configurable = false,
  exportable = false,
  shareable = false,
  printable = false,
  undoable = false,
  responsive = false,
  drillDownEnabled = false,
  enablePerformanceMonitoring = false,
  autoRefresh = false,
  refreshInterval = 30000,
  favorites = [],
  notifications = [],
  customActions = [],
  breadcrumbs = [],
  collaborators = [],
  contextMenu = [],
  gridSnap = 10,
  versionControlEnabled = false,
  helpEnabled = false,
  showTooltips = false,
  ariaLabel = 'Dashboard',
  ariaDescribedBy,
  onWidgetReorder,
  onWidgetResize,
  onWidgetRefresh,
  onWidgetConfig,
  onFilterChange,
  onSearch,
  onExport,
  onShare,
  onPrint,
  onUndo,
  onRedo,
  onDrillDown,
  onPerformanceReport,
  onAutoRefresh,
  onFavoriteToggle,
  onVersionSave,
  className,
  'data-testid': dataTestId = 'dashboard-container',
  'data-category': dataCategory,
  'data-id': dataId,
  ...props
}: DashboardProps) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [filterValue, setFilterValue] = useState('');
  const [fullscreenWidget, setFullscreenWidget] = useState<string | null>(null);
  const [showConfigPanel, setShowConfigPanel] = useState<string | null>(null);
  const [showHelp, setShowHelp] = useState(false);
  const [draggedWidget, setDraggedWidget] = useState<string | null>(null);
  const [focusedIndex, setFocusedIndex] = useState(-1);
  const [performanceMetrics, setPerformanceMetrics] = useState<any>(null);
  const [contextMenuPosition, setContextMenuPosition] = useState<{ x: number; y: number; widgetId: string } | null>(null);

  const dashboardRef = useRef<HTMLDivElement>(null);
  const autoRefreshRef = useRef<NodeJS.Timeout | null>(null);
  const performanceRef = useRef({
    renderStart: 0,
    renderEnd: 0,
    updateCount: 0
  });

  // Use template widgets if provided, otherwise use widgets prop
  const effectiveWidgets = template ? template.widgets : widgets;
  const effectiveLayout = template ? template.layout : layout;

  // Filter and search widgets
  const filteredWidgets = useMemo(() => {
    let filtered = [...effectiveWidgets];

    // Apply search
    if (searchQuery && searchable) {
      filtered = filtered.filter(widget =>
        widget.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
        JSON.stringify(widget.data || {}).toLowerCase().includes(searchQuery.toLowerCase())
      );
    }

    // Apply filter
    if (filterValue && filterable) {
      filtered = filtered.filter(widget =>
        widget.type.includes(filterValue) || widget.title.toLowerCase().includes(filterValue.toLowerCase())
      );
    }

    return filtered;
  }, [effectiveWidgets, searchQuery, filterValue, searchable, filterable]);

  // Group widgets if needed
  const groupedWidgets = useMemo(() => {
    if (!grouped) return { ungrouped: filteredWidgets };

    const groups: Record<string, Widget[]> = {};
    filteredWidgets.forEach(widget => {
      const group = widget.group || widget.type;
      if (!groups[group]) {
        groups[group] = [];
      }
      groups[group].push(widget);
    });

    return groups;
  }, [filteredWidgets, grouped]);

  // Handle search
  const handleSearch = useCallback((query: string) => {
    setSearchQuery(query);
    onSearch?.(query);
  }, [onSearch]);

  // Handle filter
  const handleFilter = useCallback((filter: string) => {
    setFilterValue(filter);
    onFilterChange?.(filter);
  }, [onFilterChange]);

  // Handle widget refresh
  const handleWidgetRefresh = useCallback((widgetId: string) => {
    onWidgetRefresh?.(widgetId);
  }, [onWidgetRefresh]);

  // Handle widget fullscreen
  const handleFullscreen = useCallback((widgetId: string) => {
    setFullscreenWidget(fullscreenWidget === widgetId ? null : widgetId);
  }, [fullscreenWidget]);

  // Handle widget config
  const handleWidgetConfig = useCallback((widgetId: string) => {
    setShowConfigPanel(showConfigPanel === widgetId ? null : widgetId);
  }, [showConfigPanel]);

  // Handle drag and drop
  const handleDragStart = useCallback((e: React.DragEvent, widgetId: string) => {
    if (!draggable) return;
    setDraggedWidget(widgetId);
    e.dataTransfer.effectAllowed = 'move';
  }, [draggable]);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    if (!draggable || !draggedWidget) return;
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
  }, [draggable, draggedWidget]);

  const handleDrop = useCallback((e: React.DragEvent, targetWidgetId: string) => {
    if (!draggable || !draggedWidget) return;
    e.preventDefault();
    
    const fromIndex = effectiveWidgets.findIndex(w => w.id === draggedWidget);
    const toIndex = effectiveWidgets.findIndex(w => w.id === targetWidgetId);
    
    if (fromIndex !== -1 && toIndex !== -1 && fromIndex !== toIndex) {
      onWidgetReorder?.(fromIndex, toIndex);
    }
    
    setDraggedWidget(null);
  }, [draggable, draggedWidget, effectiveWidgets, onWidgetReorder]);

  // Handle keyboard navigation
  const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
    switch (e.key) {
      case 'Tab':
        e.preventDefault();
        const nextIndex = (focusedIndex + 1) % filteredWidgets.length;
        setFocusedIndex(nextIndex);
        break;
      case 'Enter':
        if (focusedIndex >= 0 && drillDownEnabled) {
          const widget = filteredWidgets[focusedIndex];
          onDrillDown?.(widget.id);
        }
        break;
      case 'Escape':
        setFullscreenWidget(null);
        setShowConfigPanel(null);
        setShowHelp(false);
        break;
    }
  }, [focusedIndex, filteredWidgets, drillDownEnabled, onDrillDown]);

  // Handle favorite toggle
  const handleFavoriteToggle = useCallback((widgetId: string) => {
    const isFavorite = favorites.includes(widgetId);
    onFavoriteToggle?.(widgetId, !isFavorite);
  }, [favorites, onFavoriteToggle]);

  // Handle widget context menu
  const handleWidgetContextMenu = useCallback((e: React.MouseEvent, widgetId: string) => {
    if (contextMenu.length === 0) return;
    
    e.preventDefault();
    setContextMenuPosition({
      x: e.clientX,
      y: e.clientY,
      widgetId
    });
  }, [contextMenu]);

  // Auto refresh setup
  useEffect(() => {
    if (autoRefresh && refreshInterval > 0) {
      autoRefreshRef.current = setInterval(() => {
        onAutoRefresh?.();
      }, refreshInterval);

      return () => {
        if (autoRefreshRef.current) {
          clearInterval(autoRefreshRef.current);
        }
      };
    }
  }, [autoRefresh, refreshInterval, onAutoRefresh]);

  // Performance monitoring
  useEffect(() => {
    if (enablePerformanceMonitoring) {
      performanceRef.current.renderStart = performance.now();
      performanceRef.current.updateCount++;

      return () => {
        performanceRef.current.renderEnd = performance.now();
        const metrics = {
          renderTime: performanceRef.current.renderEnd - performanceRef.current.renderStart,
          updateCount: performanceRef.current.updateCount,
          widgetCount: filteredWidgets.length,
          timestamp: new Date()
        };
        setPerformanceMetrics(metrics);
        onPerformanceReport?.(metrics);
      };
    }
  }, [enablePerformanceMonitoring, filteredWidgets.length, onPerformanceReport]);

  // Render toolbar
  const renderToolbar = () => (
    <div className="flex items-center justify-between p-4 border-b bg-white">
      <div className="flex items-center space-x-4">
        {breadcrumbs.length > 0 && (
          <nav className="flex items-center space-x-2" data-testid="dashboard-breadcrumbs">
            {breadcrumbs.map((crumb, index) => (
              <React.Fragment key={index}>
                {index > 0 && <span className="text-gray-400">/</span>}
                <a href={crumb.href} className="text-blue-600 hover:text-blue-700">
                  {crumb.label}
                </a>
              </React.Fragment>
            ))}
          </nav>
        )}

        {searchable && (
          <div className="flex items-center">
            <input
              type="text"
              placeholder="Search widgets..."
              value={searchQuery}
              onChange={(e) => handleSearch(e.target.value)}
              className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              data-testid="dashboard-search"
            />
          </div>
        )}

        {filterable && (
          <div className="flex items-center">
            <input
              type="text"
              placeholder="Filter widgets..."
              value={filterValue}
              onChange={(e) => handleFilter(e.target.value)}
              className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              data-testid="dashboard-filter"
            />
          </div>
        )}
      </div>

      <div className="flex items-center space-x-2">
        {autoRefresh && (
          <div className="flex items-center text-sm text-gray-600" data-testid="auto-refresh-indicator">
            <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse mr-2"></div>
            Auto-refresh enabled
          </div>
        )}

        {collaborators.length > 0 && (
          <div className="flex items-center space-x-2" data-testid="dashboard-collaborators">
            {collaborators.map(collaborator => (
              <div key={collaborator.id} className="flex items-center">
                <img
                  src={collaborator.avatar}
                  alt={collaborator.name}
                  className="w-6 h-6 rounded-full"
                />
                <span className="ml-1 text-sm">{collaborator.name}</span>
                {collaborator.active && (
                  <div className="w-2 h-2 bg-green-500 rounded-full ml-1"></div>
                )}
              </div>
            ))}
          </div>
        )}

        {customActions.map(action => (
          <button
            key={action.id}
            onClick={action.onClick}
            className="px-3 py-2 bg-gray-100 text-gray-700 rounded hover:bg-gray-200"
            data-testid={`custom-action-${action.id}`}
          >
            {action.label}
          </button>
        ))}

        {undoable && (
          <>
            <button
              onClick={onUndo}
              className="px-3 py-2 bg-gray-100 text-gray-700 rounded hover:bg-gray-200"
              data-testid="dashboard-undo"
            >
              Undo
            </button>
            <button
              onClick={onRedo}
              className="px-3 py-2 bg-gray-100 text-gray-700 rounded hover:bg-gray-200"
              data-testid="dashboard-redo"
            >
              Redo
            </button>
          </>
        )}

        {versionControlEnabled && (
          <button
            onClick={() => onVersionSave?.({})}
            className="px-3 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
            data-testid="save-version"
          >
            Save Version
          </button>
        )}

        {exportable && (
          <button
            onClick={() => onExport?.('pdf')}
            className="px-3 py-2 bg-green-500 text-white rounded hover:bg-green-600"
            data-testid="dashboard-export"
          >
            Export
          </button>
        )}

        {shareable && (
          <button
            onClick={onShare}
            className="px-3 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
            data-testid="dashboard-share"
          >
            Share
          </button>
        )}

        {printable && (
          <button
            onClick={onPrint}
            className="px-3 py-2 bg-gray-500 text-white rounded hover:bg-gray-600"
            data-testid="dashboard-print"
          >
            Print
          </button>
        )}

        {helpEnabled && (
          <button
            onClick={() => setShowHelp(!showHelp)}
            className="px-3 py-2 bg-gray-100 text-gray-700 rounded hover:bg-gray-200"
            data-testid="dashboard-help"
          >
            Help
          </button>
        )}
      </div>
    </div>
  );

  // Render notifications
  const renderNotifications = () => {
    if (notifications.length === 0) return null;

    return (
      <div className="p-4 border-b bg-yellow-50" data-testid="dashboard-notifications">
        {notifications.map(notification => (
          <div key={notification.id} className="flex items-center text-sm">
            <span className={cn(
              'w-2 h-2 rounded-full mr-2',
              notification.type === 'info' && 'bg-blue-500',
              notification.type === 'warning' && 'bg-yellow-500',
              notification.type === 'error' && 'bg-red-500',
              notification.type === 'success' && 'bg-green-500'
            )}></span>
            <span>{notification.message}</span>
            <span className="ml-auto text-gray-500">
              {notification.timestamp.toLocaleTimeString()}
            </span>
          </div>
        ))}
      </div>
    );
  };

  // Render widget
  const renderWidget = (widget: Widget, index: number) => {
    const isFavorite = favorites.includes(widget.id);
    const isFocused = index === focusedIndex;
    const isDragged = draggedWidget === widget.id;

    return (
      <div
        key={widget.id}
        className={cn(
          'bg-white border border-gray-200 rounded-lg shadow-sm overflow-hidden',
          isFocused && 'focused ring-2 ring-blue-500',
          isDragged && 'opacity-50',
          showTooltips && 'cursor-help'
        )}
        draggable={draggable}
        onDragStart={(e) => handleDragStart(e, widget.id)}
        onDragOver={handleDragOver}
        onDrop={(e) => handleDrop(e, widget.id)}
        onDoubleClick={() => drillDownEnabled && onDrillDown?.(widget.id)}
        onContextMenu={(e) => handleWidgetContextMenu(e, widget.id)}
        data-testid={`widget-${widget.id}`}
        title={showTooltips ? widget.title : undefined}
      >
        <div className="flex items-center justify-between p-3 border-b bg-gray-50">
          <h3 className="font-medium text-gray-900">{widget.title}</h3>
          <div className="flex items-center space-x-1">
            <button
              onClick={() => handleFavoriteToggle(widget.id)}
              className={cn(
                'p-1 rounded hover:bg-gray-200',
                isFavorite ? 'text-yellow-500' : 'text-gray-400'
              )}
              data-testid={`favorite-${widget.id}`}
            >
              ★
            </button>
            <button
              onClick={() => handleWidgetRefresh(widget.id)}
              className="p-1 text-gray-400 rounded hover:bg-gray-200"
              data-testid={`refresh-${widget.id}`}
            >
              ↻
            </button>
            <button
              onClick={() => handleFullscreen(widget.id)}
              className="p-1 text-gray-400 rounded hover:bg-gray-200"
              data-testid={`fullscreen-${widget.id}`}
            >
              ⛶
            </button>
            {configurable && (
              <button
                onClick={() => handleWidgetConfig(widget.id)}
                className="p-1 text-gray-400 rounded hover:bg-gray-200"
                data-testid={`config-${widget.id}`}
              >
                ⚙
              </button>
            )}
            {resizable && (
              <div
                className="w-3 h-3 bg-gray-300 cursor-nw-resize"
                data-testid={`resize-handle-${widget.id}`}
              />
            )}
          </div>
        </div>

        <div className="p-4">
          {widget.loading && (
            <div className="flex items-center justify-center h-32" data-testid={`widget-loading-${widget.id}`}>
              <div className="w-6 h-6 border-2 border-gray-300 border-t-blue-500 rounded-full animate-spin"></div>
            </div>
          )}

          {widget.error && (
            <div className="flex items-center justify-center h-32 text-red-500" data-testid={`widget-error-${widget.id}`}>
              <div className="text-center">
                <div className="text-2xl mb-2">⚠</div>
                <div>{widget.error}</div>
              </div>
            </div>
          )}

          {!widget.loading && !widget.error && (
            <div className="widget-content">
              {widget.render ? (
                widget.render()
              ) : widget.type === 'metric' && widget.data ? (
                <div className="text-center">
                  <div className="text-3xl font-bold text-blue-600">{widget.data.value}</div>
                  {widget.data.change && (
                    <div className={cn(
                      'text-sm mt-1',
                      widget.data.change > 0 ? 'text-green-600' : 'text-red-600'
                    )}>
                      {widget.data.change > 0 ? '+' : ''}{widget.data.change}% {widget.data.period}
                    </div>
                  )}
                </div>
              ) : widget.type === 'chart' && widget.data ? (
                <div className="h-32 flex items-center justify-center bg-gray-100 rounded">
                  Chart: {JSON.stringify(widget.data.values)}
                </div>
              ) : widget.type === 'table' && widget.data ? (
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <tbody>
                      {widget.data.map((row: any, idx: number) => (
                        <tr key={idx} className="border-b border-gray-100">
                          <td className="py-1">{row.customer}</td>
                          <td className="py-1 text-right">${row.amount}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <div className="text-gray-500 text-center">No data available</div>
              )}
            </div>
          )}
        </div>

        {showTooltips && (
          <div
            className="absolute z-50 p-2 bg-black text-white text-sm rounded shadow-lg pointer-events-none"
            data-testid={`widget-tooltip-${widget.id}`}
            style={{ display: 'none' }}
          >
            {widget.title}
          </div>
        )}
      </div>
    );
  };

  // Render grouped widgets
  const renderGroupedWidgets = () => {
    return Object.entries(groupedWidgets).map(([groupName, groupWidgets]) => (
      <div key={groupName}>
        {grouped && groupName !== 'ungrouped' && (
          <h2 className="text-lg font-semibold mb-4 border-b pb-2" data-testid={`widget-group-${groupName}`}>
            {groupName.charAt(0).toUpperCase() + groupName.slice(1)}
          </h2>
        )}
        <div className={cn(
          'grid gap-4 mb-8',
          effectiveLayout === 'grid' && 'grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4',
          effectiveLayout === 'masonry' && 'masonry-grid',
          effectiveLayout === 'fixed' && 'fixed-grid'
        )}>
          {groupWidgets.map((widget, index) => renderWidget(widget, index))}
        </div>
      </div>
    ));
  };

  // Render fullscreen overlay
  const renderFullscreenOverlay = () => {
    if (!fullscreenWidget) return null;

    const widget = effectiveWidgets.find(w => w.id === fullscreenWidget);
    if (!widget) return null;

    return (
      <div
        className="fixed inset-0 z-50 bg-black bg-opacity-50 flex items-center justify-center"
        data-testid="fullscreen-overlay"
      >
        <div className="bg-white rounded-lg shadow-xl max-w-4xl max-h-4xl w-full h-full m-4 overflow-auto">
          <div className="flex items-center justify-between p-4 border-b">
            <h2 className="text-xl font-semibold">{widget.title}</h2>
            <button
              onClick={() => setFullscreenWidget(null)}
              className="p-2 text-gray-400 hover:text-gray-600"
            >
              ✕
            </button>
          </div>
          <div className="p-6">
            {renderWidget(widget, 0)}
          </div>
        </div>
      </div>
    );
  };

  // Render config panel
  const renderConfigPanel = () => {
    if (!showConfigPanel) return null;

    return (
      <div
        className="fixed right-0 top-0 bottom-0 w-80 bg-white shadow-xl border-l z-40"
        data-testid="widget-config-panel"
      >
        <div className="p-4 border-b">
          <h3 className="font-semibold">Widget Configuration</h3>
          <button
            onClick={() => setShowConfigPanel(null)}
            className="absolute top-4 right-4 text-gray-400 hover:text-gray-600"
          >
            ✕
          </button>
        </div>
        <div className="p-4">
          <p className="text-gray-600">Configuration options for widget: {showConfigPanel}</p>
        </div>
      </div>
    );
  };

  // Render help panel
  const renderHelpPanel = () => {
    if (!showHelp) return null;

    return (
      <div
        className="fixed inset-0 z-50 bg-black bg-opacity-50 flex items-center justify-center"
        data-testid="dashboard-help-panel"
      >
        <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full m-4">
          <div className="flex items-center justify-between p-4 border-b">
            <h2 className="text-xl font-semibold">Dashboard Help</h2>
            <button
              onClick={() => setShowHelp(false)}
              className="p-2 text-gray-400 hover:text-gray-600"
            >
              ✕
            </button>
          </div>
          <div className="p-6">
            <p className="text-gray-600">Help content for using the dashboard...</p>
          </div>
        </div>
      </div>
    );
  };

  // Render widget context menu
  const renderWidgetContextMenu = () => {
    if (!contextMenuPosition) return null;

    return (
      <div
        className="fixed z-50 bg-white border border-gray-200 rounded-md shadow-lg min-w-32"
        style={{ left: contextMenuPosition.x, top: contextMenuPosition.y }}
        data-testid="widget-context-menu"
      >
        {contextMenu.map((item, index) => (
          <button
            key={index}
            className="w-full px-3 py-2 text-left text-sm hover:bg-gray-100 first:rounded-t-md last:rounded-b-md disabled:opacity-50"
            disabled={item.disabled}
            onClick={() => {
              item.onClick(contextMenuPosition.widgetId);
              setContextMenuPosition(null);
            }}
          >
            {item.icon && <span className="mr-2">{item.icon}</span>}
            {item.label}
          </button>
        ))}
      </div>
    );
  };

  if (effectiveWidgets.length === 0) {
    return (
      <div
        className="flex items-center justify-center h-64 text-gray-500"
        data-testid="dashboard-empty"
      >
        No widgets to display
      </div>
    );
  }

  return (
    <div
      ref={dashboardRef}
      className={cn(
        'dashboard',
        `layout-${effectiveLayout}`,
        `theme-${theme}`,
        responsive && 'responsive',
        className
      )}
      style={{ gridSnap: gridSnap }}
      tabIndex={0}
      onKeyDown={handleKeyDown}
      role="main"
      aria-label={ariaLabel}
      aria-describedby={ariaDescribedBy}
      data-testid={dataTestId}
      data-category={dataCategory}
      data-id={dataId}
      data-breakpoints={JSON.stringify(columns)}
      data-grid-snap={gridSnap}
      {...props}
    >
      {renderToolbar()}
      {renderNotifications()}
      
      <div className="p-6">
        {renderGroupedWidgets()}
      </div>

      {renderFullscreenOverlay()}
      {renderConfigPanel()}
      {renderHelpPanel()}
      {renderWidgetContextMenu()}
    </div>
  );
};

export default Dashboard;