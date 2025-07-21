import React from 'react'
import { 
  Play, 
  Pause, 
  RotateCcw, 
  Download,
  Wifi,
  WifiOff,
  Activity,
  TrendingUp,
  AlertCircle,
  Check
} from 'lucide-react'
import { cn } from '../../lib/utils'
import { useExperimentalFeature, useFeatureAnalytics } from './FeatureFlags'
import { useVirtualization } from '../../hooks/useVirtualization'
import { useMemoryOptimizedState } from '../../hooks/useMemoryOptimization'

export interface StreamingDataPoint {
  id: string
  timestamp: number
  data: Record<string, any>
  metadata?: {
    source?: string
    type?: string
    priority?: 'low' | 'medium' | 'high'
    status?: 'success' | 'warning' | 'error'
  }
}

export interface ColumnDefinition {
  key: string
  title: string
  width?: number
  type?: 'text' | 'number' | 'date' | 'status' | 'progress'
  format?: (value: any) => string | React.ReactNode
  sortable?: boolean
  filterable?: boolean
}

export interface StreamingDataGridProps {
  className?: string
  columns: ColumnDefinition[]
  dataSource: string | (() => Promise<StreamingDataPoint[]>)
  maxRows?: number
  refreshInterval?: number
  height?: number
  onRowClick?: (row: StreamingDataPoint) => void
  onDataUpdate?: (data: StreamingDataPoint[]) => void
  showControls?: boolean
  showStats?: boolean
  autoStart?: boolean
}

const StreamingDataGrid: React.FC<StreamingDataGridProps> = ({
  className,
  columns,
  dataSource,
  maxRows = 1000,
  refreshInterval = 2000,
  height = 400,
  onRowClick,
  onDataUpdate,
  showControls = true,
  showStats = true,
  autoStart = true
}) => {
  const isEnabled = useExperimentalFeature('streaming-data')
  const { trackFeatureUsage } = useFeatureAnalytics()

  const [data, setData] = useMemoryOptimizedState<StreamingDataPoint[]>([], {
    maxItems: maxRows,
    autoCleanup: true
  })
  const [isStreaming, setIsStreaming] = React.useState(autoStart)
  const [isConnected, setIsConnected] = React.useState(false)
  const [stats, setStats] = React.useState({
    totalRows: 0,
    updateRate: 0,
    lastUpdate: 0,
    errors: 0
  })
  const [sortConfig, setSortConfig] = React.useState<{
    key: string
    direction: 'asc' | 'desc'
  } | null>(null)

  const intervalRef = React.useRef<number>()
  const wsRef = React.useRef<WebSocket>()
  const updateCountRef = React.useRef(0)
  const lastUpdateTimeRef = React.useRef(Date.now())

  // Virtualization for performance
  const virtualization = useVirtualization(data, {
    itemHeight: 40,
    containerHeight: height - 120, // Account for header and controls
    overscan: 5
  })

  // WebSocket connection for real-time data
  const connectWebSocket = React.useCallback(() => {
    if (typeof dataSource !== 'string') return

    try {
      wsRef.current = new WebSocket(dataSource)
      
      wsRef.current.onopen = () => {
        setIsConnected(true)
        trackFeatureUsage('streaming-data', 'websocket_connected')
      }

      wsRef.current.onmessage = (event) => {
        try {
          const newData: StreamingDataPoint | StreamingDataPoint[] = JSON.parse(event.data)
          const dataPoints = Array.isArray(newData) ? newData : [newData]
          
          setData(prev => {
            const updated = [...prev, ...dataPoints].slice(-maxRows)
            onDataUpdate?.(updated)
            return updated
          })

          updateCountRef.current++
          updateStats()
        } catch (error) {
          console.error('Failed to parse WebSocket data:', error)
          setStats(prev => ({ ...prev, errors: prev.errors + 1 }))
        }
      }

      wsRef.current.onclose = () => {
        setIsConnected(false)
      }

      wsRef.current.onerror = (error) => {
        console.error('WebSocket error:', error)
        setIsConnected(false)
        setStats(prev => ({ ...prev, errors: prev.errors + 1 }))
      }
    } catch (error) {
      console.error('Failed to connect WebSocket:', error)
    }
  }, [dataSource, maxRows, onDataUpdate, trackFeatureUsage])

  // Polling for data sources that aren't WebSocket
  const pollData = React.useCallback(async () => {
    if (typeof dataSource === 'string') return

    try {
      const newData = await dataSource()
      setData(prev => {
        const updated = [...prev, ...newData].slice(-maxRows)
        onDataUpdate?.(updated)
        return updated
      })

      updateCountRef.current += newData.length
      updateStats()
    } catch (error) {
      console.error('Failed to poll data:', error)
      setStats(prev => ({ ...prev, errors: prev.errors + 1 }))
    }
  }, [dataSource, maxRows, onDataUpdate])

  const updateStats = React.useCallback(() => {
    const now = Date.now()
    const timeDiff = now - lastUpdateTimeRef.current
    const rate = timeDiff > 0 ? (updateCountRef.current / timeDiff) * 1000 : 0

    setStats(prev => ({
      totalRows: data.length,
      updateRate: Math.round(rate * 100) / 100,
      lastUpdate: now,
      errors: prev.errors
    }))

    lastUpdateTimeRef.current = now
    updateCountRef.current = 0
  }, [data.length])

  // Start/stop streaming
  const toggleStreaming = () => {
    setIsStreaming(prev => {
      const newState = !prev
      
      if (newState) {
        if (typeof dataSource === 'string') {
          connectWebSocket()
        } else {
          intervalRef.current = window.setInterval(pollData, refreshInterval)
        }
        trackFeatureUsage('streaming-data', 'streaming_started')
      } else {
        if (wsRef.current) {
          wsRef.current.close()
        }
        if (intervalRef.current) {
          clearInterval(intervalRef.current)
        }
        trackFeatureUsage('streaming-data', 'streaming_stopped')
      }
      
      return newState
    })
  }

  // Clear data
  const clearData = () => {
    setData([])
    setStats(prev => ({ ...prev, totalRows: 0, errors: 0 }))
    trackFeatureUsage('streaming-data', 'data_cleared')
  }

  // Export data
  const exportData = () => {
    const csv = [
      columns.map(col => col.title).join(','),
      ...data.map(row => 
        columns.map(col => {
          const value = row.data[col.key]
          return typeof value === 'string' ? `"${value}"` : value
        }).join(',')
      )
    ].join('\n')

    const blob = new Blob([csv], { type: 'text/csv' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `streaming-data-${new Date().toISOString().split('T')[0]}.csv`
    a.click()
    URL.revokeObjectURL(url)

    trackFeatureUsage('streaming-data', 'data_exported', { rowCount: data.length })
  }

  // Sorting
  const handleSort = (columnKey: string) => {
    setSortConfig(prev => ({
      key: columnKey,
      direction: prev?.key === columnKey && prev.direction === 'asc' ? 'desc' : 'asc'
    }))
  }

  // Sort data
  const sortedData = React.useMemo(() => {
    if (!sortConfig) return data

    return [...data].sort((a, b) => {
      const aVal = a.data[sortConfig.key]
      const bVal = b.data[sortConfig.key]
      
      if (aVal === bVal) return 0
      
      const comparison = aVal < bVal ? -1 : 1
      return sortConfig.direction === 'asc' ? comparison : -comparison
    })
  }, [data, sortConfig])

  // Auto-start streaming
  React.useEffect(() => {
    if (autoStart && isEnabled) {
      toggleStreaming()
    }

    return () => {
      if (wsRef.current) {
        wsRef.current.close()
      }
      if (intervalRef.current) {
        clearInterval(intervalRef.current)
      }
    }
  }, [autoStart, isEnabled])

  if (!isEnabled) {
    return (
      <div className={cn('p-8 text-center border-2 border-dashed border-gray-300 rounded-lg', className)}>
        <WifiOff className="h-8 w-8 text-gray-400 mx-auto mb-2" />
        <p className="text-gray-600">Streaming data features are not available</p>
      </div>
    )
  }

  return (
    <div className={cn('bg-white rounded-lg border shadow-sm', className)}>
      {/* Header */}
      <div className="px-4 py-3 border-b">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Activity className="h-5 w-5 text-blue-600" />
            <h3 className="text-lg font-semibold">Streaming Data</h3>
            <div className="flex items-center space-x-1">
              {isConnected ? (
                <Wifi className="h-4 w-4 text-green-500" />
              ) : (
                <WifiOff className="h-4 w-4 text-red-500" />
              )}
              <span className={cn('w-2 h-2 rounded-full', isStreaming ? 'bg-green-500' : 'bg-gray-400')} />
            </div>
          </div>

          {showControls && (
            <div className="flex items-center space-x-2">
              <button
                onClick={toggleStreaming}
                className={cn(
                  'p-2 rounded-md transition-colors',
                  isStreaming
                    ? 'bg-red-100 text-red-600 hover:bg-red-200'
                    : 'bg-green-100 text-green-600 hover:bg-green-200'
                )}
                title={isStreaming ? 'Pause Streaming' : 'Start Streaming'}
              >
                {isStreaming ? <Pause className="h-4 w-4" /> : <Play className="h-4 w-4" />}
              </button>
              <button
                onClick={clearData}
                className="p-2 bg-gray-100 text-gray-600 rounded-md hover:bg-gray-200"
                title="Clear Data"
              >
                <RotateCcw className="h-4 w-4" />
              </button>
              <button
                onClick={exportData}
                className="p-2 bg-blue-100 text-blue-600 rounded-md hover:bg-blue-200"
                title="Export Data"
                disabled={data.length === 0}
              >
                <Download className="h-4 w-4" />
              </button>
            </div>
          )}
        </div>

        {/* Stats */}
        {showStats && (
          <div className="mt-3 grid grid-cols-4 gap-4 text-sm">
            <div className="flex items-center space-x-2">
              <span className="text-gray-600">Rows:</span>
              <span className="font-medium">{stats.totalRows}</span>
            </div>
            <div className="flex items-center space-x-2">
              <span className="text-gray-600">Rate:</span>
              <span className="font-medium">{stats.updateRate}/s</span>
            </div>
            <div className="flex items-center space-x-2">
              <span className="text-gray-600">Last Update:</span>
              <span className="font-medium">
                {stats.lastUpdate ? new Date(stats.lastUpdate).toLocaleTimeString() : 'Never'}
              </span>
            </div>
            <div className="flex items-center space-x-2">
              <span className="text-gray-600">Errors:</span>
              <span className={cn('font-medium', stats.errors > 0 ? 'text-red-600' : 'text-green-600')}>
                {stats.errors}
              </span>
            </div>
          </div>
        )}
      </div>

      {/* Table Header */}
      <div className="border-b bg-gray-50">
        <div className="flex">
          {columns.map((column) => (
            <div
              key={column.key}
              className={cn(
                'px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider',
                column.sortable && 'cursor-pointer hover:bg-gray-100'
              )}
              style={{ width: column.width || 'auto', flex: column.width ? undefined : 1 }}
              onClick={() => column.sortable && handleSort(column.key)}
            >
              <div className="flex items-center space-x-1">
                <span>{column.title}</span>
                {column.sortable && sortConfig?.key === column.key && (
                  <TrendingUp className={cn('h-3 w-3', sortConfig.direction === 'desc' && 'rotate-180')} />
                )}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Virtualized Table Body */}
      <div style={{ height: height - 120 }}>
        {sortedData.length === 0 ? (
          <div className="flex items-center justify-center h-full">
            <div className="text-center">
              <Activity className="h-8 w-8 text-gray-300 mx-auto mb-2" />
              <p className="text-gray-500">No data available</p>
              <p className="text-sm text-gray-400 mt-1">
                {isStreaming ? 'Waiting for data...' : 'Start streaming to see data'}
              </p>
            </div>
          </div>
        ) : (
          <div
            {...virtualization.scrollElementProps}
            style={{ ...virtualization.scrollElementProps.style, height: '100%' }}
          >
            <div style={{ height: virtualization.totalHeight, position: 'relative' }}>
              {virtualization.virtualItems.map((virtualItem) => {
                const row = sortedData[virtualItem.index]
                const itemProps = virtualization.getItemProps(virtualItem.index)

                return (
                  <div
                    key={itemProps.key}
                    style={itemProps.style}
                    data-index={itemProps['data-index']}
                    className="flex border-b border-gray-100 hover:bg-gray-50 cursor-pointer"
                    onClick={() => onRowClick?.(row)}
                  >
                    {columns.map((column) => (
                      <div
                        key={column.key}
                        className="px-4 py-2 text-sm"
                        style={{ width: column.width || 'auto', flex: column.width ? undefined : 1 }}
                      >
                        <CellContent
                          value={row.data[column.key]}
                          column={column}
                          metadata={row.metadata}
                        />
                      </div>
                    ))}
                  </div>
                )
              })}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

interface CellContentProps {
  value: any
  column: ColumnDefinition
  metadata?: StreamingDataPoint['metadata']
}

const CellContent: React.FC<CellContentProps> = ({ value, column, metadata }) => {
  if (column.format) {
    return <>{column.format(value)}</>
  }

  switch (column.type) {
    case 'date':
      return <span>{new Date(value).toLocaleString()}</span>
    
    case 'status':
      const statusIcon = {
        success: <Check className="h-4 w-4 text-green-500" />,
        warning: <AlertCircle className="h-4 w-4 text-yellow-500" />,
        error: <AlertCircle className="h-4 w-4 text-red-500" />
      }
      return (
        <div className="flex items-center space-x-1">
          {metadata?.status && statusIcon[metadata.status]}
          <span>{value}</span>
        </div>
      )
    
    case 'progress':
      const percentage = Math.min(100, Math.max(0, value))
      return (
        <div className="flex items-center space-x-2">
          <div className="flex-1 bg-gray-200 rounded-full h-2">
            <div
              className="bg-blue-600 h-2 rounded-full transition-all duration-300"
              style={{ width: `${percentage}%` }}
            />
          </div>
          <span className="text-xs">{percentage}%</span>
        </div>
      )
    
    case 'number':
      return <span className="font-mono">{typeof value === 'number' ? value.toFixed(2) : value}</span>
    
    default:
      return <span>{value}</span>
  }
}

export default StreamingDataGrid