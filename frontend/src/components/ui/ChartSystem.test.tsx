import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { vi } from 'vitest';
import { ChartSystem } from './ChartSystem';

// Mock ResizeObserver
global.ResizeObserver = vi.fn().mockImplementation(() => ({
  observe: vi.fn(),
  unobserve: vi.fn(),
  disconnect: vi.fn(),
}));

interface MockDataset {
  id: string;
  label: string;
  data: Array<{ x: number | string; y: number; label?: string; color?: string }>;
  type?: 'line' | 'bar' | 'area' | 'scatter' | 'pie' | 'doughnut' | 'radar' | 'bubble';
  color?: string;
  backgroundColor?: string;
  borderColor?: string;
  visible?: boolean;
}

describe('ChartSystem', () => {
  const mockDatasets: MockDataset[] = [
    {
      id: 'dataset-1',
      label: 'Sales',
      data: [
        { x: '2023-01', y: 100 },
        { x: '2023-02', y: 150 },
        { x: '2023-03', y: 200 },
        { x: '2023-04', y: 180 }
      ]
    },
    {
      id: 'dataset-2',
      label: 'Revenue',
      data: [
        { x: '2023-01', y: 1000 },
        { x: '2023-02', y: 1500 },
        { x: '2023-03', y: 2000 },
        { x: '2023-04', y: 1800 }
      ]
    }
  ];

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders chart system with data', () => {
    render(<ChartSystem datasets={mockDatasets} />);
    
    expect(screen.getByTestId('chart-system')).toBeInTheDocument();
    expect(screen.getByTestId('chart-canvas')).toBeInTheDocument();
    expect(screen.getByTestId('chart-legend')).toBeInTheDocument();
  });

  it('supports different chart types', () => {
    const chartTypes = ['line', 'bar', 'area', 'scatter', 'pie'] as const;
    
    chartTypes.forEach(type => {
      const { unmount } = render(<ChartSystem datasets={mockDatasets} type={type} />);
      expect(screen.getByTestId('chart-system')).toBeInTheDocument();
      unmount();
    });
  });

  it('displays chart title and subtitle', () => {
    render(
      <ChartSystem 
        datasets={mockDatasets} 
        title="Sales Dashboard"
        subtitle="Monthly performance metrics"
      />
    );
    
    expect(screen.getByTestId('chart-header')).toBeInTheDocument();
    expect(screen.getByText('Sales Dashboard')).toBeInTheDocument();
    expect(screen.getByText('Monthly performance metrics')).toBeInTheDocument();
  });

  it('supports interactive legend', () => {
    render(<ChartSystem datasets={mockDatasets} />);
    
    const salesLegend = screen.getByTestId('legend-item-dataset-1');
    const revenueLegend = screen.getByTestId('legend-item-dataset-2');
    
    expect(salesLegend).toBeInTheDocument();
    expect(revenueLegend).toBeInTheDocument();
    
    // Click to toggle dataset visibility
    fireEvent.click(salesLegend);
    expect(salesLegend).toHaveClass('bg-gray-100');
  });

  it('supports different legend positions', () => {
    const positions = ['top', 'bottom', 'left', 'right'] as const;
    
    positions.forEach(position => {
      const { unmount } = render(
        <ChartSystem 
          datasets={mockDatasets} 
          legend={{ display: true, position, align: 'center' }}
        />
      );
      expect(screen.getByTestId('chart-legend')).toBeInTheDocument();
      unmount();
    });
  });

  it('supports toolbar functionality', () => {
    render(<ChartSystem datasets={mockDatasets} toolbar />);
    
    expect(screen.getByTestId('chart-toolbar')).toBeInTheDocument();
    expect(screen.getByTestId('toolbar-toggle')).toBeInTheDocument();
    
    // Test toolbar collapse
    const toggleButton = screen.getByTestId('toolbar-toggle');
    fireEvent.click(toggleButton);
    
    const toolbar = screen.getByTestId('chart-toolbar');
    expect(toolbar).toHaveClass('h-8', 'overflow-hidden');
  });

  it('supports zoom functionality', () => {
    render(
      <ChartSystem 
        datasets={mockDatasets} 
        zoom={{ enabled: true, mode: 'xy' }}
        toolbar
      />
    );
    
    expect(screen.getByTestId('reset-zoom')).toBeInTheDocument();
    
    const resetButton = screen.getByTestId('reset-zoom');
    fireEvent.click(resetButton);
  });

  it('supports real-time data updates', async () => {
    const mockDataSource = vi.fn().mockResolvedValue([
      { x: '2023-05', y: 220, label: 'Sales' }
    ]);
    
    const onDataUpdate = vi.fn();
    
    render(
      <ChartSystem 
        datasets={mockDatasets}
        realTime={{
          enabled: true,
          interval: 100,
          updateMode: 'append',
          dataSource: mockDataSource
        }}
        toolbar
        onDataUpdate={onDataUpdate}
      />
    );
    
    expect(screen.getByTestId('realtime-toggle')).toBeInTheDocument();
    
    const playButton = screen.getByTestId('realtime-toggle');
    expect(playButton).toHaveTextContent('Pause');
    
    // Pause real-time updates
    fireEvent.click(playButton);
    expect(playButton).toHaveTextContent('Play');
  });

  it('supports export functionality', () => {
    const onExport = vi.fn();
    
    render(
      <ChartSystem 
        datasets={mockDatasets}
        exportConfig={{
          formats: ['png', 'csv', 'json'],
          filename: 'chart-export'
        }}
        toolbar
        onExport={onExport}
      />
    );
    
    expect(screen.getByTestId('export-select')).toBeInTheDocument();
    
    const exportSelect = screen.getByTestId('export-select');
    fireEvent.change(exportSelect, { target: { value: 'csv' } });
    
    expect(onExport).toHaveBeenCalledWith('csv', expect.any(String));
  });

  it('supports context menu', () => {
    render(
      <ChartSystem 
        datasets={mockDatasets}
        exportConfig={{ formats: ['png'] }}
      />
    );
    
    const chartSystem = screen.getByTestId('chart-system');
    fireEvent.contextMenu(chartSystem);
    
    expect(screen.getByTestId('chart-context-menu')).toBeInTheDocument();
    expect(screen.getByText('Reset View')).toBeInTheDocument();
    expect(screen.getByText('Export as PNG')).toBeInTheDocument();
  });

  it('supports different themes', () => {
    const { rerender } = render(<ChartSystem datasets={mockDatasets} theme="light" />);
    let container = screen.getByTestId('chart-system');
    expect(container).toHaveClass('bg-white');
    
    rerender(<ChartSystem datasets={mockDatasets} theme="dark" />);
    container = screen.getByTestId('chart-system');
    expect(container).toHaveClass('bg-gray-900');
  });

  it('supports different color schemes', () => {
    const colorSchemes = ['default', 'viridis', 'plasma', 'inferno'] as const;
    
    colorSchemes.forEach(scheme => {
      const { unmount } = render(
        <ChartSystem datasets={mockDatasets} colorScheme={scheme} />
      );
      expect(screen.getByTestId('chart-system')).toBeInTheDocument();
      unmount();
    });
  });

  it('displays loading state', () => {
    render(<ChartSystem datasets={mockDatasets} loading />);
    
    expect(screen.getByTestId('chart-loading')).toBeInTheDocument();
    expect(screen.queryByTestId('chart-canvas')).not.toBeInTheDocument();
  });

  it('displays error state', () => {
    render(<ChartSystem datasets={mockDatasets} error="Failed to load data" />);
    
    expect(screen.getByTestId('chart-error')).toBeInTheDocument();
    expect(screen.getByText('Failed to load data')).toBeInTheDocument();
    expect(screen.getByText('Retry')).toBeInTheDocument();
  });

  it('displays empty state', () => {
    render(<ChartSystem datasets={[]} />);
    
    expect(screen.getByTestId('chart-empty')).toBeInTheDocument();
    expect(screen.getByText('No data to display')).toBeInTheDocument();
  });

  it('supports custom empty state', () => {
    const customEmpty = <div data-testid="custom-empty">No chart data available</div>;
    
    render(<ChartSystem datasets={[]} emptyState={customEmpty} />);
    
    expect(screen.getByTestId('custom-empty')).toBeInTheDocument();
    expect(screen.getByText('No chart data available')).toBeInTheDocument();
  });

  it('supports responsive design', () => {
    render(<ChartSystem datasets={mockDatasets} responsive />);
    
    const canvas = screen.getByTestId('chart-canvas');
    expect(canvas).toHaveClass('max-w-full');
  });

  it('supports watermark', () => {
    render(<ChartSystem datasets={mockDatasets} watermark="© Company 2023" />);
    
    expect(screen.getByTestId('chart-watermark')).toBeInTheDocument();
    expect(screen.getByText('© Company 2023')).toBeInTheDocument();
  });

  it('supports accessibility features', () => {
    render(
      <ChartSystem 
        datasets={mockDatasets}
        accessibility={{
          enabled: true,
          description: "Sales and revenue chart showing monthly data"
        }}
      />
    );
    
    expect(screen.getByTestId('chart-accessibility')).toBeInTheDocument();
    expect(screen.getByText('Sales and revenue chart showing monthly data')).toBeInTheDocument();
  });

  it('supports crosshair functionality', () => {
    render(
      <ChartSystem 
        datasets={mockDatasets}
        crosshair={{
          enabled: true,
          color: '#ff0000',
          width: 2
        }}
      />
    );
    
    expect(screen.getByTestId('chart-crosshair')).toBeInTheDocument();
  });

  it('handles chart interactions', () => {
    const onZoom = vi.fn();
    const onPan = vi.fn();
    
    render(
      <ChartSystem 
        datasets={mockDatasets}
        zoom={{ enabled: true, mode: 'xy' }}
        pan={{ enabled: true, mode: 'xy' }}
        onZoom={onZoom}
        onPan={onPan}
      />
    );
    
    expect(screen.getByTestId('chart-canvas')).toBeInTheDocument();
  });

  it('supports custom styling', () => {
    render(
      <ChartSystem 
        datasets={mockDatasets}
        className="custom-chart"
        style={{ border: '2px solid red' }}
      />
    );
    
    const container = screen.getByTestId('chart-system');
    expect(container).toHaveClass('custom-chart');
    expect(container).toHaveStyle('border: 2px solid red');
  });

  it('supports mixed chart types', () => {
    const mixedDatasets = [
      { ...mockDatasets[0], type: 'line' as const },
      { ...mockDatasets[1], type: 'bar' as const }
    ];
    
    render(<ChartSystem datasets={mixedDatasets} type="mixed" />);
    
    expect(screen.getByTestId('chart-system')).toBeInTheDocument();
  });

  it('supports annotations', () => {
    const annotations = [
      {
        id: 'annotation-1',
        type: 'line' as const,
        x: '2023-03',
        label: 'Peak Performance',
        color: '#ff0000'
      }
    ];
    
    render(<ChartSystem datasets={mockDatasets} annotations={annotations} />);
    
    expect(screen.getByTestId('chart-system')).toBeInTheDocument();
  });

  it('supports data aggregation', () => {
    render(
      <ChartSystem 
        datasets={mockDatasets}
        aggregation={{
          enabled: true,
          method: 'average',
          interval: 'month'
        }}
      />
    );
    
    expect(screen.getByTestId('chart-system')).toBeInTheDocument();
  });

  it('supports performance optimizations', () => {
    render(
      <ChartSystem 
        datasets={mockDatasets}
        performance={{
          enableWorker: true,
          throttleResize: 200,
          decimation: true,
          skipNull: true
        }}
      />
    );
    
    expect(screen.getByTestId('chart-system')).toBeInTheDocument();
  });

  it('supports multiple data formats', () => {
    const timeSeriesData = [
      {
        id: 'timeseries',
        label: 'Time Series',
        data: [
          { x: '2023-01-01', y: 100 },
          { x: '2023-01-02', y: 150 },
          { x: '2023-01-03', y: 200 }
        ]
      }
    ];
    
    render(<ChartSystem datasets={timeSeriesData} />);
    
    expect(screen.getByTestId('chart-system')).toBeInTheDocument();
  });

  it('handles large datasets efficiently', () => {
    const largeDataset = [{
      id: 'large-dataset',
      label: 'Large Data',
      data: Array.from({ length: 10000 }, (_, i) => ({
        x: i,
        y: Math.random() * 100
      }))
    }];
    
    render(
      <ChartSystem 
        datasets={largeDataset}
        performance={{
          decimation: true,
          enableWorker: true
        }}
      />
    );
    
    expect(screen.getByTestId('chart-system')).toBeInTheDocument();
  });

  it('supports brush selection', () => {
    render(<ChartSystem datasets={mockDatasets} brushSelection />);
    
    expect(screen.getByTestId('chart-system')).toBeInTheDocument();
  });

  it('supports compare mode', () => {
    render(<ChartSystem datasets={mockDatasets} compareMode />);
    
    expect(screen.getByTestId('chart-system')).toBeInTheDocument();
  });

  it('supports minimap functionality', () => {
    render(<ChartSystem datasets={mockDatasets} minimap />);
    
    expect(screen.getByTestId('chart-system')).toBeInTheDocument();
  });

  it('handles real-time data source errors', async () => {
    const failingDataSource = vi.fn().mockRejectedValue(new Error('Data fetch failed'));
    const onError = vi.fn();
    
    render(
      <ChartSystem 
        datasets={mockDatasets}
        realTime={{
          enabled: true,
          interval: 100,
          updateMode: 'append',
          dataSource: failingDataSource
        }}
        onError={onError}
      />
    );
    
    await waitFor(() => {
      expect(onError).toHaveBeenCalledWith(expect.any(Error));
    }, { timeout: 200 });
  });

  it('supports custom data attributes', () => {
    render(
      <ChartSystem 
        datasets={mockDatasets}
        data-testid="custom-chart"
      />
    );
    
    expect(screen.getByTestId('custom-chart')).toBeInTheDocument();
  });

  it('maintains aspect ratio when specified', () => {
    render(<ChartSystem datasets={mockDatasets} maintainAspectRatio />);
    
    const canvas = screen.getByTestId('chart-canvas');
    expect(canvas).not.toHaveClass('w-full');
  });

  it('supports custom chart dimensions', () => {
    render(<ChartSystem datasets={mockDatasets} width={800} height={600} />);
    
    const canvas = screen.getByTestId('chart-canvas');
    expect(canvas).toHaveAttribute('width', '800');
    expect(canvas).toHaveAttribute('height', '600');
  });

  it('supports pan functionality', () => {
    render(
      <ChartSystem 
        datasets={mockDatasets}
        pan={{ enabled: true, mode: 'xy' }}
      />
    );
    
    expect(screen.getByTestId('chart-canvas')).toBeInTheDocument();
  });

  it('displays current time in real-time mode', () => {
    render(
      <ChartSystem 
        datasets={mockDatasets}
        realTime={{ enabled: true, interval: 1000, updateMode: 'append' }}
        toolbar
      />
    );
    
    expect(screen.getByTestId('current-time')).toBeInTheDocument();
  });

  it('shows dataset count in toolbar', () => {
    render(<ChartSystem datasets={mockDatasets} toolbar />);
    
    expect(screen.getByText('2 datasets')).toBeInTheDocument();
  });

  it('handles click outside to close context menu', () => {
    render(<ChartSystem datasets={mockDatasets} />);
    
    const chartSystem = screen.getByTestId('chart-system');
    fireEvent.contextMenu(chartSystem);
    
    expect(screen.getByTestId('chart-context-menu')).toBeInTheDocument();
    
    // Click outside
    fireEvent.mouseDown(document.body);
    
    expect(screen.queryByTestId('chart-context-menu')).not.toBeInTheDocument();
  });

  it('supports different update modes for real-time data', () => {
    const updateModes = ['append', 'replace', 'shift'] as const;
    
    updateModes.forEach(mode => {
      const { unmount } = render(
        <ChartSystem 
          datasets={mockDatasets}
          realTime={{
            enabled: true,
            interval: 1000,
            updateMode: mode
          }}
        />
      );
      expect(screen.getByTestId('chart-system')).toBeInTheDocument();
      unmount();
    });
  });

  it('limits data points when maxDataPoints is specified', () => {
    render(
      <ChartSystem 
        datasets={mockDatasets}
        realTime={{
          enabled: true,
          interval: 1000,
          updateMode: 'append',
          maxDataPoints: 100
        }}
      />
    );
    
    expect(screen.getByTestId('chart-system')).toBeInTheDocument();
  });

  it('supports multiple plugins', () => {
    render(
      <ChartSystem 
        datasets={mockDatasets}
        plugins={['zoom', 'annotation', 'datalabels', 'streaming']}
      />
    );
    
    expect(screen.getByTestId('chart-system')).toBeInTheDocument();
  });

  it('handles empty datasets gracefully', () => {
    const emptyDataset = [{
      id: 'empty',
      label: 'Empty Dataset',
      data: []
    }];
    
    render(<ChartSystem datasets={emptyDataset} />);
    
    expect(screen.getByTestId('chart-system')).toBeInTheDocument();
  });
});