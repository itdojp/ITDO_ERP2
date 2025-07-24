import React, { useState, useRef, useCallback, useEffect, useMemo } from 'react';
import { cn } from '@/lib/utils';

export interface DataPoint {
  x: number | string | Date;
  y: number;
  label?: string;
  color?: string;
}

export interface ChartDataset {
  id: string;
  label: string;
  data: DataPoint[];
  type?: 'line' | 'bar' | 'area' | 'scatter' | 'pie' | 'doughnut' | 'radar' | 'bubble';
  color?: string;
  backgroundColor?: string;
  borderColor?: string;
  borderWidth?: number;
  fill?: boolean;
  tension?: number;
  pointRadius?: number;
  visible?: boolean;
}

export interface ChartAxis {
  id: string;
  type: 'linear' | 'logarithmic' | 'category' | 'time';
  position: 'left' | 'right' | 'top' | 'bottom';
  title?: string;
  min?: number;
  max?: number;
  step?: number;
  format?: string;
  gridLines?: boolean;
}

export interface ChartAnnotation {
  id: string;
  type: 'line' | 'box' | 'point' | 'text';
  x?: number | string;
  y?: number | string;
  x2?: number | string;
  y2?: number | string;
  label?: string;
  color?: string;
  borderColor?: string;
  backgroundColor?: string;
}

export interface ChartLegend {
  display: boolean;
  position: 'top' | 'bottom' | 'left' | 'right';
  align: 'start' | 'center' | 'end';
  labels?: {
    usePointStyle?: boolean;
    padding?: number;
    fontSize?: number;
  };
}

export interface ChartTooltip {
  enabled: boolean;
  mode: 'point' | 'nearest' | 'index' | 'dataset';
  intersect: boolean;
  backgroundColor?: string;
  titleColor?: string;
  bodyColor?: string;
  borderColor?: string;
  borderWidth?: number;
  cornerRadius?: number;
  displayColors?: boolean;
  callbacks?: {
    title?: (context: any) => string;
    label?: (context: any) => string;
    afterLabel?: (context: any) => string;
  };
}

export interface ChartAnimation {
  duration: number;
  easing: 'linear' | 'easeInQuad' | 'easeOutQuad' | 'easeInOutQuad' | 'easeInCubic' | 'easeOutCubic' | 'easeInOutCubic';
  delay?: number;
  loop?: boolean;
  animateRotate?: boolean;
  animateScale?: boolean;
}

export interface ChartInteraction {
  hover?: {
    mode: 'point' | 'nearest' | 'index' | 'dataset';
    intersect: boolean;
    animationDuration: number;
  };
  onClick?: (event: any, elements: any[]) => void;
  onHover?: (event: any, elements: any[]) => void;
  onLeave?: (event: any) => void;
}

export interface ChartExport {
  formats: Array<'png' | 'jpg' | 'pdf' | 'svg' | 'csv' | 'json'>;
  filename?: string;
  quality?: number;
  width?: number;
  height?: number;
}

export interface ChartRealTimeConfig {
  enabled: boolean;
  interval: number;
  maxDataPoints?: number;
  updateMode: 'append' | 'replace' | 'shift';
  pauseOnHover?: boolean;
  dataSource?: () => Promise<DataPoint[]>;
}

export interface ChartSystemProps {
  datasets: ChartDataset[];
  type?: 'line' | 'bar' | 'area' | 'scatter' | 'pie' | 'doughnut' | 'radar' | 'bubble' | 'mixed';
  width?: number;
  height?: number;
  responsive?: boolean;
  maintainAspectRatio?: boolean;
  title?: string;
  subtitle?: string;
  axes?: ChartAxis[];
  legend?: ChartLegend;
  tooltip?: ChartTooltip;
  animation?: ChartAnimation;
  interaction?: ChartInteraction;
  annotations?: ChartAnnotation[];
  theme?: 'light' | 'dark' | 'auto';
  colorScheme?: 'default' | 'viridis' | 'plasma' | 'inferno' | 'magma' | 'cividis';
  grid?: {
    display: boolean;
    color?: string;
    lineWidth?: number;
  };
  zoom?: {
    enabled: boolean;
    mode: 'x' | 'y' | 'xy';
    limits?: {
      x?: { min: number; max: number };
      y?: { min: number; max: number };
    };
  };
  pan?: {
    enabled: boolean;
    mode: 'x' | 'y' | 'xy';
    limits?: {
      x?: { min: number; max: number };
      y?: { min: number; max: number };
    };
  };
  crosshair?: {
    enabled: boolean;
    color?: string;
    width?: number;
    dash?: number[];
  };
  realTime?: ChartRealTimeConfig;
  exportConfig?: ChartExport;
  plugins?: Array<'zoom' | 'annotation' | 'datalabels' | 'streaming' | 'crosshair'>;
  loading?: boolean;
  error?: string | null;
  emptyState?: React.ReactNode;
  toolbar?: boolean;
  minimap?: boolean;
  brushSelection?: boolean;
  compareMode?: boolean;
  aggregation?: {
    enabled: boolean;
    method: 'sum' | 'average' | 'min' | 'max' | 'count';
    interval: 'second' | 'minute' | 'hour' | 'day' | 'week' | 'month';
  };
  performance?: {
    enableWorker?: boolean;
    throttleResize?: number;
    decimation?: boolean;
    skipNull?: boolean;
  };
  accessibility?: {
    enabled: boolean;
    description?: string;
    announceNewData?: boolean;
    keyboardNavigation?: boolean;
  };
  watermark?: string;
  className?: string;
  style?: React.CSSProperties;
  onDataUpdate?: (datasets: ChartDataset[]) => void;
  onZoom?: (zoomState: any) => void;
  onPan?: (panState: any) => void;
  onSelectionChange?: (selection: any) => void;
  onExport?: (format: string, data: any) => void;
  onError?: (error: Error) => void;
  onReady?: () => void;
  'data-testid'?: string;
}

export const ChartSystem: React.FC<ChartSystemProps> = ({
  datasets,
  type = 'line',
  width,
  height = 400,
  responsive = true,
  maintainAspectRatio = true,
  title,
  subtitle,
  axes = [],
  legend = { display: true, position: 'top', align: 'center' },
  tooltip = { enabled: true, mode: 'nearest', intersect: false },
  animation = { duration: 750, easing: 'easeInOutQuad' },
  interaction,
  annotations = [],
  theme = 'light',
  colorScheme = 'default',
  grid = { display: true, color: '#e0e0e0', lineWidth: 1 },
  zoom,
  pan,
  crosshair,
  realTime,
  exportConfig,
  plugins = [],
  loading = false,
  error = null,
  emptyState,
  toolbar = true,
  minimap = false,
  brushSelection = false,
  compareMode = false,
  aggregation,
  performance,
  accessibility = { enabled: true },
  watermark,
  className,
  style,
  onDataUpdate,
  onZoom,
  onPan,
  onSelectionChange,
  onExport,
  onError,
  onReady,
  'data-testid': dataTestId = 'chart-system'
}) => {
  const [internalDatasets, setInternalDatasets] = useState<ChartDataset[]>(datasets);
  const [selectedDatasets, setSelectedDatasets] = useState<string[]>(datasets.map(d => d.id));
  const [zoomState, setZoomState] = useState<any>(null);
  const [panState, setPanState] = useState<any>(null);
  const [isPlaying, setIsPlaying] = useState(realTime?.enabled || false);
  const [currentTime, setCurrentTime] = useState<Date>(new Date());
  const [brushSelectionState, setBrushSelectionState] = useState<any>(null);
  const [contextMenu, setContextMenu] = useState<{ x: number; y: number; visible: boolean }>({ x: 0, y: 0, visible: false });
  const [toolbarCollapsed, setToolbarCollapsed] = useState(false);

  const chartRef = useRef<HTMLCanvasElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const realTimeRef = useRef<NodeJS.Timeout | null>(null);
  const resizeObserverRef = useRef<ResizeObserver | null>(null);

  // Color schemes
  const colorSchemes = {
    default: ['#3B82F6', '#EF4444', '#10B981', '#F59E0B', '#8B5CF6', '#F97316', '#06B6D4', '#84CC16'],
    viridis: ['#440154', '#414487', '#2A788E', '#22A884', '#7AD151', '#FDE725'],
    plasma: ['#0D0887', '#6A00A8', '#B12A90', '#E16462', '#FCA636', '#F0F921'],
    inferno: ['#000004', '#420A68', '#932667', '#DD513A', '#FCA50A', '#FCFFA4'],
    magma: ['#000004', '#3B0F70', '#8C2981', '#DE4968', '#FE9F6D', '#FCFDBF'],
    cividis: ['#00224E', '#123570', '#3B496C', '#575D6D', '#707173', '#8A8779']
  };

  // Get color for dataset
  const getDatasetColor = useCallback((index: number) => {
    const colors = colorSchemes[colorScheme] || colorSchemes.default;
    return colors[index % colors.length];
  }, [colorScheme]);

  // Prepare chart data
  const chartData = useMemo(() => {
    const visibleDatasets = internalDatasets.filter(dataset => 
      dataset.visible !== false && selectedDatasets.includes(dataset.id)
    );

    return {
      datasets: visibleDatasets.map((dataset, index) => ({
        ...dataset,
        borderColor: dataset.borderColor || getDatasetColor(index),
        backgroundColor: dataset.backgroundColor || (dataset.fill ? `${getDatasetColor(index)}33` : getDatasetColor(index)),
        data: dataset.data
      }))
    };
  }, [internalDatasets, selectedDatasets, getDatasetColor]);

  // Real-time data updates
  useEffect(() => {
    if (realTime?.enabled && isPlaying && realTime.dataSource) {
      const interval = setInterval(async () => {
        try {
          const newData = await realTime.dataSource!();
          
          setInternalDatasets(prevDatasets => {
            const updatedDatasets = prevDatasets.map(dataset => {
              const datasetNewData = newData.filter(point => point.label === dataset.label);
              
              if (datasetNewData.length > 0) {
                let updatedData = [...dataset.data];
                
                if (realTime.updateMode === 'append') {
                  updatedData = [...updatedData, ...datasetNewData];
                } else if (realTime.updateMode === 'replace') {
                  updatedData = datasetNewData;
                } else if (realTime.updateMode === 'shift') {
                  updatedData = [...updatedData.slice(datasetNewData.length), ...datasetNewData];
                }
                
                // Limit data points if specified
                if (realTime.maxDataPoints && updatedData.length > realTime.maxDataPoints) {
                  updatedData = updatedData.slice(-realTime.maxDataPoints);
                }
                
                return { ...dataset, data: updatedData };
              }
              
              return dataset;
            });
            
            onDataUpdate?.(updatedDatasets);
            return updatedDatasets;
          });
          
          setCurrentTime(new Date());
        } catch (error) {
          console.error('Real-time data update failed:', error);
          onError?.(error as Error);
        }
      }, realTime.interval);
      
      realTimeRef.current = interval;
      
      return () => {
        if (realTimeRef.current) {
          clearInterval(realTimeRef.current);
        }
      };
    }
  }, [realTime, isPlaying, onDataUpdate, onError]);

  // Handle resize
  useEffect(() => {
    if (responsive && containerRef.current) {
      const resizeObserver = new ResizeObserver(entries => {
        // Throttle resize updates for performance
        const throttleDelay = performance?.throttleResize || 100;
        setTimeout(() => {
          // Trigger chart resize
          setCurrentTime(new Date()); // Force re-render
        }, throttleDelay);
      });
      
      resizeObserver.observe(containerRef.current);
      resizeObserverRef.current = resizeObserver;
      
      return () => {
        resizeObserver.disconnect();
      };
    }
  }, [responsive, performance?.throttleResize]);

  // Dataset toggle
  const handleDatasetToggle = useCallback((datasetId: string) => {
    setSelectedDatasets(prev => 
      prev.includes(datasetId) 
        ? prev.filter(id => id !== datasetId)
        : [...prev, datasetId]
    );
  }, []);

  // Zoom handlers
  const handleZoom = useCallback((newZoomState: any) => {
    setZoomState(newZoomState);
    onZoom?.(newZoomState);
  }, [onZoom]);

  const handlePan = useCallback((newPanState: any) => {
    setPanState(newPanState);
    onPan?.(newPanState);
  }, [onPan]);

  // Reset zoom/pan
  const handleResetZoom = useCallback(() => {
    setZoomState(null);
    setPanState(null);
  }, []);

  // Export functionality
  const handleExport = useCallback(async (format: string) => {
    if (!chartRef.current) return;
    
    try {
      let exportData: any;
      
      if (format === 'png' || format === 'jpg') {
        const canvas = chartRef.current;
        const dataURL = canvas.toDataURL(`image/${format}`, exportConfig?.quality || 1.0);
        exportData = dataURL;
      } else if (format === 'csv') {
        // Convert chart data to CSV
        const headers = ['x', ...internalDatasets.map(d => d.label)];
        const rows: string[][] = [];
        
        // Get all unique x values
        const allXValues = Array.from(new Set(
          internalDatasets.flatMap(d => d.data.map(p => p.x))
        )).sort();
        
        allXValues.forEach(x => {
          const row = [String(x)];
          internalDatasets.forEach(dataset => {
            const point = dataset.data.find(p => p.x === x);
            row.push(point ? String(point.y) : '');
          });
          rows.push(row);
        });
        
        exportData = [headers, ...rows].map(row => row.join(',')).join('\n');
      } else if (format === 'json') {
        exportData = JSON.stringify({
          title,
          subtitle,
          datasets: internalDatasets,
          exportedAt: new Date().toISOString()
        }, null, 2);
      }
      
      onExport?.(format, exportData);
    } catch (error) {
      console.error('Export failed:', error);
      onError?.(error as Error);
    }
  }, [chartRef, internalDatasets, title, subtitle, exportConfig, onExport, onError]);

  // Context menu
  const handleContextMenu = useCallback((e: React.MouseEvent) => {
    e.preventDefault();
    setContextMenu({
      x: e.clientX,
      y: e.clientY,
      visible: true
    });
  }, []);

  // Real-time controls
  const handlePlayPause = useCallback(() => {
    setIsPlaying(prev => !prev);
  }, []);

  // Render toolbar
  const renderToolbar = () => {
    if (!toolbar) return null;
    
    return (
      <div className={cn(
        "flex items-center justify-between p-2 border-b bg-gray-50",
        toolbarCollapsed && "h-8 overflow-hidden"
      )} data-testid="chart-toolbar">
        <div className="flex items-center space-x-2">
          <button
            className="p-1 hover:bg-gray-200 rounded"
            onClick={() => setToolbarCollapsed(!toolbarCollapsed)}
            data-testid="toolbar-toggle"
          >
            {toolbarCollapsed ? '▼' : '▲'}
          </button>
          
          {!toolbarCollapsed && (
            <>
              {zoom?.enabled && (
                <button
                  className="px-2 py-1 text-sm bg-blue-500 text-white rounded hover:bg-blue-600"
                  onClick={handleResetZoom}
                  data-testid="reset-zoom"
                >
                  Reset Zoom
                </button>
              )}
              
              {realTime?.enabled && (
                <button
                  className={cn(
                    "px-2 py-1 text-sm rounded",
                    isPlaying 
                      ? "bg-red-500 text-white hover:bg-red-600" 
                      : "bg-green-500 text-white hover:bg-green-600"
                  )}
                  onClick={handlePlayPause}
                  data-testid="realtime-toggle"
                >
                  {isPlaying ? 'Pause' : 'Play'}
                </button>
              )}
              
              {exportConfig && (
                <div className="relative">
                  <select
                    className="px-2 py-1 text-sm border rounded"
                    onChange={(e) => e.target.value && handleExport(e.target.value)}
                    defaultValue=""
                    data-testid="export-select"
                  >
                    <option value="">Export...</option>
                    {exportConfig.formats.map(format => (
                      <option key={format} value={format}>
                        {format.toUpperCase()}
                      </option>
                    ))}
                  </select>
                </div>
              )}
            </>
          )}
        </div>
        
        {!toolbarCollapsed && (
          <div className="flex items-center space-x-2">
            {realTime?.enabled && (
              <span className="text-xs text-gray-500" data-testid="current-time">
                {currentTime.toLocaleTimeString()}
              </span>
            )}
            
            <div className="text-xs text-gray-500">
              {internalDatasets.length} dataset{internalDatasets.length !== 1 ? 's' : ''}
            </div>
          </div>
        )}
      </div>
    );
  };

  // Render legend
  const renderLegend = () => {
    if (!legend.display) return null;
    
    return (
      <div 
        className={cn(
          "flex flex-wrap gap-2 p-2",
          legend.position === 'top' && "order-first",
          legend.position === 'bottom' && "order-last",
          legend.position === 'left' && "flex-col w-32",
          legend.position === 'right' && "flex-col w-32",
          legend.align === 'start' && "justify-start",
          legend.align === 'center' && "justify-center",
          legend.align === 'end' && "justify-end"
        )}
        data-testid="chart-legend"
      >
        {internalDatasets.map((dataset, index) => (
          <button
            key={dataset.id}
            className={cn(
              "flex items-center space-x-1 px-2 py-1 rounded text-sm",
              selectedDatasets.includes(dataset.id) 
                ? "bg-blue-100 text-blue-800" 
                : "bg-gray-100 text-gray-500"
            )}
            onClick={() => handleDatasetToggle(dataset.id)}
            data-testid={`legend-item-${dataset.id}`}
          >
            <div 
              className="w-3 h-3 rounded-full"
              style={{ backgroundColor: dataset.color || getDatasetColor(index) }}
            />
            <span>{dataset.label}</span>
          </button>
        ))}
      </div>
    );
  };

  // Render context menu
  const renderContextMenu = () => {
    if (!contextMenu.visible) return null;
    
    return (
      <div
        className="fixed z-50 bg-white border border-gray-200 rounded-md shadow-lg min-w-32"
        style={{ left: contextMenu.x, top: contextMenu.y }}
        data-testid="chart-context-menu"
      >
        <button
          className="w-full px-3 py-2 text-left text-sm hover:bg-gray-100"
          onClick={() => {
            handleResetZoom();
            setContextMenu({ ...contextMenu, visible: false });
          }}
        >
          Reset View
        </button>
        {exportConfig && exportConfig.formats.map(format => (
          <button
            key={format}
            className="w-full px-3 py-2 text-left text-sm hover:bg-gray-100"
            onClick={() => {
              handleExport(format);
              setContextMenu({ ...contextMenu, visible: false });
            }}
          >
            Export as {format.toUpperCase()}
          </button>
        ))}
      </div>
    );
  };

  // Click outside handler
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setContextMenu({ ...contextMenu, visible: false });
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [contextMenu]);

  // Loading state
  if (loading) {
    return (
      <div 
        className="flex items-center justify-center border border-gray-200 rounded-lg"
        style={{ height }}
        data-testid="chart-loading"
      >
        <div className="w-8 h-8 border-2 border-gray-300 border-t-blue-500 rounded-full animate-spin"></div>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div 
        className="flex flex-col items-center justify-center border border-red-200 bg-red-50 rounded-lg"
        style={{ height }}
        data-testid="chart-error"
      >
        <div className="w-6 h-6 text-red-500 mb-2">⚠</div>
        <div className="text-sm text-red-600">{error}</div>
        <button 
          className="mt-2 px-3 py-1 text-xs bg-red-500 text-white rounded hover:bg-red-600"
          onClick={() => window.location.reload()}
        >
          Retry
        </button>
      </div>
    );
  }

  // Empty state
  if (internalDatasets.length === 0) {
    return (
      <div 
        className="flex flex-col items-center justify-center border border-gray-200 rounded-lg"
        style={{ height }}
        data-testid="chart-empty"
      >
        {emptyState || (
          <>
            <div className="w-12 h-12 text-gray-400 mb-2">📊</div>
            <div className="text-sm text-gray-500">No data to display</div>
          </>
        )}
      </div>
    );
  }

  return (
    <div
      ref={containerRef}
      className={cn(
        "relative border border-gray-200 rounded-lg bg-white",
        theme === 'dark' && "bg-gray-900 border-gray-700",
        className
      )}
      style={style}
      onContextMenu={handleContextMenu}
      data-testid={dataTestId}
    >
      {renderToolbar()}
      
      <div className="flex">
        {legend.position === 'left' && renderLegend()}
        
        <div className="flex-1">
          {(title || subtitle) && (
            <div className="p-4 text-center" data-testid="chart-header">
              {title && (
                <h2 className={cn(
                  "text-lg font-semibold",
                  theme === 'dark' && "text-white"
                )}>
                  {title}
                </h2>
              )}
              {subtitle && (
                <p className={cn(
                  "text-sm text-gray-600",
                  theme === 'dark' && "text-gray-400"
                )}>
                  {subtitle}
                </p>
              )}
            </div>
          )}
          
          {legend.position === 'top' && renderLegend()}
          
          <div className="relative">
            <canvas
              ref={chartRef}
              width={width}
              height={height}
              className={cn(
                "max-w-full",
                !maintainAspectRatio && "w-full"
              )}
              data-testid="chart-canvas"
            />
            
            {watermark && (
              <div 
                className="absolute bottom-2 right-2 text-xs text-gray-400 opacity-50 pointer-events-none"
                data-testid="chart-watermark"
              >
                {watermark}
              </div>
            )}
            
            {crosshair?.enabled && (
              <div 
                className="absolute inset-0 pointer-events-none"
                data-testid="chart-crosshair"
              />
            )}
          </div>
          
          {legend.position === 'bottom' && renderLegend()}
        </div>
        
        {legend.position === 'right' && renderLegend()}
      </div>
      
      {renderContextMenu()}
      
      {accessibility?.enabled && (
        <div className="sr-only" data-testid="chart-accessibility">
          <p>{accessibility.description || `Chart displaying ${internalDatasets.length} datasets`}</p>
          {internalDatasets.map(dataset => (
            <div key={dataset.id}>
              <h3>{dataset.label}</h3>
              <ul>
                {dataset.data.map((point, index) => (
                  <li key={index}>
                    X: {point.x}, Y: {point.y}
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default ChartSystem;