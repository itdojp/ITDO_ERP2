import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { vi } from 'vitest';
import { Dashboard } from './Dashboard';

interface MockWidget {
  id: string;
  type: 'chart' | 'metric' | 'table' | 'text' | 'custom';
  title: string;
  data?: any;
  config?: any;
}

describe('Dashboard', () => {
  const mockWidgets: MockWidget[] = [
    {
      id: 'widget-1',
      type: 'metric',
      title: 'Total Sales',
      data: { value: 125000, change: 12.5, period: 'vs last month' }
    },
    {
      id: 'widget-2', 
      type: 'chart',
      title: 'Sales Chart',
      data: { values: [100, 120, 150, 180, 200], labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May'] }
    },
    {
      id: 'widget-3',
      type: 'table',
      title: 'Recent Orders',
      data: [
        { id: 1, customer: 'John Doe', amount: 1200 },
        { id: 2, customer: 'Jane Smith', amount: 800 }
      ]
    }
  ];

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders dashboard with widgets', () => {
    render(<Dashboard widgets={mockWidgets} />);
    
    expect(screen.getByTestId('dashboard-container')).toBeInTheDocument();
    expect(screen.getByText('Total Sales')).toBeInTheDocument();
    expect(screen.getByText('Sales Chart')).toBeInTheDocument();
    expect(screen.getByText('Recent Orders')).toBeInTheDocument();
  });

  it('supports different layouts', () => {
    const layouts = ['grid', 'masonry', 'fixed'] as const;
    
    layouts.forEach(layout => {
      const { unmount } = render(<Dashboard widgets={mockWidgets} layout={layout} />);
      const container = screen.getByTestId('dashboard-container');
      expect(container).toHaveClass(`layout-${layout}`);
      unmount();
    });
  });

  it('supports responsive breakpoints', () => {
    const breakpoints = { xs: 1, sm: 2, md: 3, lg: 4, xl: 6 };
    
    render(<Dashboard widgets={mockWidgets} columns={breakpoints} />);
    
    const container = screen.getByTestId('dashboard-container');
    expect(container).toHaveAttribute('data-breakpoints');
  });

  it('supports widget drag and drop', () => {
    const onWidgetReorder = vi.fn();
    
    render(
      <Dashboard 
        widgets={mockWidgets} 
        draggable 
        onWidgetReorder={onWidgetReorder}
      />
    );
    
    const firstWidget = screen.getByTestId('widget-widget-1');
    expect(firstWidget).toHaveAttribute('draggable', 'true');
  });

  it('handles widget resize', () => {
    const onWidgetResize = vi.fn();
    
    render(
      <Dashboard 
        widgets={mockWidgets} 
        resizable 
        onWidgetResize={onWidgetResize}
      />
    );
    
    const resizeHandle = screen.getByTestId('resize-handle-widget-1');
    expect(resizeHandle).toBeInTheDocument();
  });

  it('supports widget filtering', () => {
    const onFilterChange = vi.fn();
    
    render(
      <Dashboard 
        widgets={mockWidgets} 
        filterable
        onFilterChange={onFilterChange}
      />
    );
    
    const filterInput = screen.getByTestId('dashboard-filter');
    fireEvent.change(filterInput, { target: { value: 'sales' } });
    
    expect(onFilterChange).toHaveBeenCalledWith('sales');
  });

  it('supports full screen widget mode', () => {
    render(<Dashboard widgets={mockWidgets} />);
    
    const fullscreenButton = screen.getByTestId('fullscreen-widget-1');
    fireEvent.click(fullscreenButton);
    
    expect(screen.getByTestId('fullscreen-overlay')).toBeInTheDocument();
  });

  it('supports widget refresh', async () => {
    const onWidgetRefresh = vi.fn();
    
    render(
      <Dashboard 
        widgets={mockWidgets} 
        onWidgetRefresh={onWidgetRefresh}
      />
    );
    
    const refreshButton = screen.getByTestId('refresh-widget-1');
    fireEvent.click(refreshButton);
    
    expect(onWidgetRefresh).toHaveBeenCalledWith('widget-1');
  });

  it('displays loading state for widgets', () => {
    const loadingWidgets = mockWidgets.map(w => ({ ...w, loading: true }));
    
    render(<Dashboard widgets={loadingWidgets} />);
    
    expect(screen.getByTestId('widget-loading-widget-1')).toBeInTheDocument();
  });

  it('displays error state for widgets', () => {
    const errorWidgets = mockWidgets.map(w => ({ ...w, error: 'Failed to load data' }));
    
    render(<Dashboard widgets={errorWidgets} />);
    
    expect(screen.getByTestId('widget-error-widget-1')).toBeInTheDocument();
    expect(screen.getAllByText('Failed to load data')).toHaveLength(3);
  });

  it('supports custom widget rendering', () => {
    const customWidget = {
      id: 'custom-widget',
      type: 'custom' as const,
      title: 'Custom Widget',
      render: () => <div data-testid="custom-content">Custom Content</div>
    };
    
    render(<Dashboard widgets={[customWidget]} />);
    
    expect(screen.getByTestId('custom-content')).toBeInTheDocument();
  });

  it('supports dashboard themes', () => {
    const themes = ['light', 'dark', 'auto'] as const;
    
    themes.forEach(theme => {
      const { unmount } = render(<Dashboard widgets={mockWidgets} theme={theme} />);
      const container = screen.getByTestId('dashboard-container');
      expect(container).toHaveClass(`theme-${theme}`);
      unmount();
    });
  });

  it('supports dashboard export', () => {
    const onExport = vi.fn();
    
    render(
      <Dashboard 
        widgets={mockWidgets} 
        exportable
        onExport={onExport}
      />
    );
    
    const exportButton = screen.getByTestId('dashboard-export');
    fireEvent.click(exportButton);
    
    expect(onExport).toHaveBeenCalledWith('pdf');
  });

  it('supports real-time data updates', async () => {
    const { rerender } = render(<Dashboard widgets={mockWidgets} />);
    
    expect(screen.getByText('125000')).toBeInTheDocument();
    
    const updatedWidgets = [
      { ...mockWidgets[0], data: { value: 130000, change: 15.2, period: 'vs last month' } },
      ...mockWidgets.slice(1)
    ];
    
    rerender(<Dashboard widgets={updatedWidgets} />);
    
    expect(screen.getByText('130000')).toBeInTheDocument();
  });

  it('supports widget configuration panel', () => {
    render(<Dashboard widgets={mockWidgets} configurable />);
    
    const configButton = screen.getByTestId('config-widget-1');
    fireEvent.click(configButton);
    
    expect(screen.getByTestId('widget-config-panel')).toBeInTheDocument();
  });

  it('supports auto-refresh intervals', () => {
    const onAutoRefresh = vi.fn();
    
    render(
      <Dashboard 
        widgets={mockWidgets} 
        autoRefresh
        refreshInterval={30000}
        onAutoRefresh={onAutoRefresh}
      />
    );
    
    expect(screen.getByTestId('auto-refresh-indicator')).toBeInTheDocument();
  });

  it('supports dashboard templates', () => {
    const template = {
      id: 'sales-template',
      name: 'Sales Dashboard',
      layout: 'grid' as const,
      widgets: mockWidgets
    };
    
    render(<Dashboard template={template} />);
    
    expect(screen.getByTestId('dashboard-container')).toBeInTheDocument();
    expect(screen.getByText('Total Sales')).toBeInTheDocument();
  });

  it('supports widget groups', () => {
    const groupedWidgets = mockWidgets.map(w => ({ ...w, group: w.type }));
    
    render(<Dashboard widgets={groupedWidgets} grouped />);
    
    expect(screen.getByTestId('widget-group-metric')).toBeInTheDocument();
    expect(screen.getByTestId('widget-group-chart')).toBeInTheDocument();
    expect(screen.getByTestId('widget-group-table')).toBeInTheDocument();
  });

  it('supports dashboard search', () => {
    render(<Dashboard widgets={mockWidgets} searchable />);
    
    const searchInput = screen.getByTestId('dashboard-search');
    fireEvent.change(searchInput, { target: { value: 'sales' } });
    
    expect(screen.getByText('Total Sales')).toBeInTheDocument();
    expect(screen.getByText('Sales Chart')).toBeInTheDocument();
    expect(screen.queryByText('Recent Orders')).not.toBeInTheDocument();
  });

  it('supports widget favorites', () => {
    const onFavoriteToggle = vi.fn();
    
    render(
      <Dashboard 
        widgets={mockWidgets} 
        favorites={['widget-1']}
        onFavoriteToggle={onFavoriteToggle}
      />
    );
    
    const favoriteButton = screen.getByTestId('favorite-widget-1');
    fireEvent.click(favoriteButton);
    
    expect(onFavoriteToggle).toHaveBeenCalledWith('widget-1', false);
  });

  it('supports dashboard sharing', () => {
    const onShare = vi.fn();
    
    render(
      <Dashboard 
        widgets={mockWidgets} 
        shareable
        onShare={onShare}
      />
    );
    
    const shareButton = screen.getByTestId('dashboard-share');
    fireEvent.click(shareButton);
    
    expect(onShare).toHaveBeenCalled();
  });

  it('supports dashboard performance monitoring', () => {
    const onPerformanceReport = vi.fn();
    
    render(
      <Dashboard 
        widgets={mockWidgets} 
        enablePerformanceMonitoring
        onPerformanceReport={onPerformanceReport}
      />
    );
    
    expect(screen.getByTestId('dashboard-container')).toBeInTheDocument();
  });

  it('supports responsive widget sizing', () => {
    render(<Dashboard widgets={mockWidgets} responsive />);
    
    const container = screen.getByTestId('dashboard-container');
    expect(container).toHaveClass('responsive');
  });

  it('supports dashboard notifications', () => {
    const notifications = [
      { id: '1', type: 'info', message: 'Dashboard updated', timestamp: new Date() }
    ];
    
    render(<Dashboard widgets={mockWidgets} notifications={notifications} />);
    
    expect(screen.getByTestId('dashboard-notifications')).toBeInTheDocument();
    expect(screen.getByText('Dashboard updated')).toBeInTheDocument();
  });

  it('supports widget context menu', () => {
    const contextMenuItems = [
      { label: 'Edit', onClick: vi.fn() },
      { label: 'Delete', onClick: vi.fn() }
    ];
    
    render(
      <Dashboard 
        widgets={mockWidgets} 
        contextMenu={contextMenuItems}
      />
    );
    
    const widget = screen.getByTestId('widget-widget-1');
    fireEvent.contextMenu(widget);
    
    expect(screen.getByTestId('widget-context-menu')).toBeInTheDocument();
  });

  it('supports keyboard navigation', () => {
    render(<Dashboard widgets={mockWidgets} />);
    
    const container = screen.getByTestId('dashboard-container');
    container.focus();
    
    fireEvent.keyDown(container, { key: 'Tab' });
    
    const firstWidget = screen.getByTestId('widget-widget-1');
    expect(firstWidget).toHaveClass('focused');
  });

  it('supports dashboard undo/redo', () => {
    const onUndo = vi.fn();
    const onRedo = vi.fn();
    
    render(
      <Dashboard 
        widgets={mockWidgets} 
        undoable
        onUndo={onUndo}
        onRedo={onRedo}
      />
    );
    
    const undoButton = screen.getByTestId('dashboard-undo');
    const redoButton = screen.getByTestId('dashboard-redo');
    
    fireEvent.click(undoButton);
    expect(onUndo).toHaveBeenCalled();
    
    fireEvent.click(redoButton);
    expect(onRedo).toHaveBeenCalled();
  });

  it('supports dashboard printing', () => {
    const onPrint = vi.fn();
    
    render(
      <Dashboard 
        widgets={mockWidgets} 
        printable
        onPrint={onPrint}
      />
    );
    
    const printButton = screen.getByTestId('dashboard-print');
    fireEvent.click(printButton);
    
    expect(onPrint).toHaveBeenCalled();
  });

  it('supports widget data drilling', () => {
    const onDrillDown = vi.fn();
    
    render(
      <Dashboard 
        widgets={mockWidgets} 
        drillDownEnabled
        onDrillDown={onDrillDown}
      />
    );
    
    const metricWidget = screen.getByTestId('widget-widget-1');
    fireEvent.doubleClick(metricWidget);
    
    expect(onDrillDown).toHaveBeenCalledWith('widget-1');
  });

  it('supports custom dashboard actions', () => {
    const customActions = [
      { id: 'action-1', label: 'Custom Action', onClick: vi.fn() }
    ];
    
    render(
      <Dashboard 
        widgets={mockWidgets} 
        customActions={customActions}
      />
    );
    
    const actionButton = screen.getByTestId('custom-action-action-1');
    fireEvent.click(actionButton);
    
    expect(customActions[0].onClick).toHaveBeenCalled();
  });

  it('supports dashboard breadcrumbs', () => {
    const breadcrumbs = [
      { label: 'Home', href: '/' },
      { label: 'Analytics', href: '/analytics' },
      { label: 'Sales Dashboard', href: '/analytics/sales' }
    ];
    
    render(<Dashboard widgets={mockWidgets} breadcrumbs={breadcrumbs} />);
    
    expect(screen.getByTestId('dashboard-breadcrumbs')).toBeInTheDocument();
    expect(screen.getByText('Sales Dashboard')).toBeInTheDocument();
  });

  it('supports dashboard help system', () => {
    render(<Dashboard widgets={mockWidgets} helpEnabled />);
    
    const helpButton = screen.getByTestId('dashboard-help');
    fireEvent.click(helpButton);
    
    expect(screen.getByTestId('dashboard-help-panel')).toBeInTheDocument();
  });

  it('supports accessibility features', () => {
    render(
      <Dashboard 
        widgets={mockWidgets} 
        ariaLabel="Main dashboard"
        ariaDescribedBy="dashboard-description"
      />
    );
    
    const container = screen.getByTestId('dashboard-container');
    expect(container).toHaveAttribute('aria-label', 'Main dashboard');
    expect(container).toHaveAttribute('aria-describedby', 'dashboard-description');
  });

  it('supports custom styling', () => {
    render(<Dashboard widgets={mockWidgets} className="custom-dashboard" />);
    
    const container = screen.getByTestId('dashboard-container');
    expect(container).toHaveClass('custom-dashboard');
  });

  it('supports custom data attributes', () => {
    render(
      <Dashboard 
        widgets={mockWidgets} 
        data-category="analytics"
        data-id="main-dashboard"
      />
    );
    
    const container = screen.getByTestId('dashboard-container');
    expect(container).toHaveAttribute('data-category', 'analytics');
    expect(container).toHaveAttribute('data-id', 'main-dashboard');
  });

  it('handles empty widget state', () => {
    render(<Dashboard widgets={[]} />);
    
    expect(screen.getByTestId('dashboard-empty')).toBeInTheDocument();
  });

  it('supports dashboard tooltips', () => {
    render(<Dashboard widgets={mockWidgets} showTooltips />);
    
    const widget = screen.getByTestId('widget-widget-1');
    fireEvent.mouseEnter(widget);
    
    expect(screen.getByTestId('widget-tooltip-widget-1')).toBeInTheDocument();
  });

  it('supports dashboard grid snap', () => {
    render(<Dashboard widgets={mockWidgets} gridSnap={20} />);
    
    const container = screen.getByTestId('dashboard-container');
    expect(container).toHaveAttribute('data-grid-snap', '20');
  });

  it('supports dashboard version control', () => {
    const onVersionSave = vi.fn();
    
    render(
      <Dashboard 
        widgets={mockWidgets} 
        versionControlEnabled
        onVersionSave={onVersionSave}
      />
    );
    
    const saveVersionButton = screen.getByTestId('save-version');
    fireEvent.click(saveVersionButton);
    
    expect(onVersionSave).toHaveBeenCalled();
  });

  it('supports dashboard collaboration', () => {
    const collaborators = [
      { id: '1', name: 'John Doe', avatar: '/avatar1.jpg', active: true }
    ];
    
    render(<Dashboard widgets={mockWidgets} collaborators={collaborators} />);
    
    expect(screen.getByTestId('dashboard-collaborators')).toBeInTheDocument();
    expect(screen.getAllByText('John Doe')).toHaveLength(2); // One from collaborator, one from table widget
  });
});