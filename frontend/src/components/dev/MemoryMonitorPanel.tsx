import React from 'react'
import { 
  Activity, 
  AlertTriangle, 
  CheckCircle, 
  TrendingUp, 
  TrendingDown, 
  Trash2,
  RefreshCw,
  BarChart3,
  Clock,
  Zap
} from 'lucide-react'
import { cn } from '../../lib/utils'
import { useMemoryUsage } from '../../hooks/useMemoryOptimization'
import { memoryLeakDetector, MemoryStats, ComponentMemoryProfile } from '../../utils/memoryLeakDetection'

export interface MemoryMonitorPanelProps {
  className?: string
  showDetailedStats?: boolean
  autoRefresh?: boolean
  refreshInterval?: number
}

const MemoryMonitorPanel: React.FC<MemoryMonitorPanelProps> = ({
  className,
  showDetailedStats = false,
  autoRefresh = true,
  refreshInterval = 2000
}) => {
  const { memoryStats, trend, formatBytes, forceGC, getReport } = useMemoryUsage('MemoryMonitorPanel')
  const [detailedReport, setDetailedReport] = React.useState<ReturnType<typeof getReport> | null>(null)
  const [isRefreshing, setIsRefreshing] = React.useState(false)

  const refreshReport = React.useCallback(async () => {
    setIsRefreshing(true)
    try {
      // Small delay to show loading state
      await new Promise(resolve => setTimeout(resolve, 100))
      const report = getReport()
      setDetailedReport(report)
    } finally {
      setIsRefreshing(false)
    }
  }, [getReport])

  React.useEffect(() => {
    refreshReport()
  }, [refreshReport])

  React.useEffect(() => {
    if (!autoRefresh) return

    const interval = setInterval(refreshReport, refreshInterval)
    return () => clearInterval(interval)
  }, [autoRefresh, refreshInterval, refreshReport])

  if (process.env.NODE_ENV !== 'development') {
    return null
  }

  if (!memoryStats) {
    return (
      <div className={cn('p-4 bg-yellow-50 rounded-lg border border-yellow-200', className)}>
        <div className="flex items-center space-x-2">
          <AlertTriangle className="h-4 w-4 text-yellow-600" />
          <span className="text-sm text-yellow-800">Memory monitoring not supported</span>
        </div>
      </div>
    )
  }

  const memoryUsagePercentage = (memoryStats.usedJSHeapSize / memoryStats.totalJSHeapSize) * 100
  const isHighUsage = memoryUsagePercentage > 80
  const isMediumUsage = memoryUsagePercentage > 60

  return (
    <div className={cn('bg-white rounded-lg border shadow-sm', className)}>
      {/* Header */}
      <div className="px-4 py-3 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Activity className="h-5 w-5 text-gray-600" />
            <h3 className="text-sm font-medium text-gray-900">Memory Monitor</h3>
            <div className="flex items-center space-x-1">
              {trend === 'increasing' && <TrendingUp className="h-4 w-4 text-red-500" />}
              {trend === 'decreasing' && <TrendingDown className="h-4 w-4 text-green-500" />}
              {trend === 'stable' && <CheckCircle className="h-4 w-4 text-gray-500" />}
            </div>
          </div>
          <div className="flex items-center space-x-2">
            <button
              onClick={refreshReport}
              disabled={isRefreshing}
              className="text-xs text-gray-500 hover:text-gray-700 p-1"
              title="Refresh"
            >
              <RefreshCw className={cn('h-3 w-3', isRefreshing && 'animate-spin')} />
            </button>
            <button
              onClick={forceGC}
              className="text-xs text-gray-500 hover:text-gray-700 p-1"
              title="Force Garbage Collection"
            >
              <Trash2 className="h-3 w-3" />
            </button>
          </div>
        </div>
      </div>

      {/* Memory Stats */}
      <div className="p-4">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
          <MemoryStatCard
            icon={<BarChart3 className="h-4 w-4" />}
            label="Used Memory"
            value={formatBytes(memoryStats.usedJSHeapSize)}
            subvalue={`${memoryUsagePercentage.toFixed(1)}% of heap`}
            status={isHighUsage ? 'error' : isMediumUsage ? 'warning' : 'good'}
          />
          <MemoryStatCard
            icon={<Zap className="h-4 w-4" />}
            label="Total Heap"
            value={formatBytes(memoryStats.totalJSHeapSize)}
            subvalue={`Limit: ${formatBytes(memoryStats.jsHeapSizeLimit)}`}
            status="neutral"
          />
          <MemoryStatCard
            icon={<TrendingUp className="h-4 w-4" />}
            label="Trend"
            value={trend.charAt(0).toUpperCase() + trend.slice(1)}
            subvalue={`Last updated: ${new Date(memoryStats.timestamp).toLocaleTimeString()}`}
            status={trend === 'increasing' ? 'warning' : 'good'}
          />
        </div>

        {/* Memory Usage Bar */}
        <div className="mb-4">
          <div className="flex items-center justify-between text-sm mb-1">
            <span className="text-gray-600">Memory Usage</span>
            <span className="text-gray-900 font-medium">
              {formatBytes(memoryStats.usedJSHeapSize)} / {formatBytes(memoryStats.totalJSHeapSize)}
            </span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-3">
            <div
              className={cn(
                'h-3 rounded-full transition-all duration-300',
                isHighUsage ? 'bg-red-500' : isMediumUsage ? 'bg-yellow-500' : 'bg-green-500'
              )}
              style={{ width: `${Math.min(memoryUsagePercentage, 100)}%` }}
            />
          </div>
          {memoryUsagePercentage > 90 && (
            <div className="flex items-center space-x-1 mt-2 text-sm text-red-600">
              <AlertTriangle className="h-4 w-4" />
              <span>High memory usage detected</span>
            </div>
          )}
        </div>

        {/* Component Profiles */}
        {detailedReport && detailedReport.componentProfiles.length > 0 && (
          <div className="mb-4">
            <h4 className="text-sm font-medium text-gray-900 mb-2 flex items-center">
              <Clock className="h-4 w-4 mr-1" />
              Component Memory Profiles
            </h4>
            <div className="space-y-2 max-h-40 overflow-y-auto">
              {detailedReport.componentProfiles.slice(0, 10).map((profile, index) => (
                <ComponentProfileCard key={index} profile={profile} />
              ))}
            </div>
          </div>
        )}

        {/* Memory Leaks */}
        {detailedReport && detailedReport.leaks.length > 0 && (
          <div className="mb-4">
            <h4 className="text-sm font-medium text-red-900 mb-2 flex items-center">
              <AlertTriangle className="h-4 w-4 mr-1 text-red-500" />
              Detected Memory Leaks ({detailedReport.leaks.length})
            </h4>
            <div className="space-y-2">
              {detailedReport.leaks.map((leak, index) => (
                <MemoryLeakCard key={index} leak={leak} />
              ))}
            </div>
          </div>
        )}

        {/* Memory Samples Chart (Simple visualization) */}
        {showDetailedStats && detailedReport && detailedReport.samples.length > 0 && (
          <div>
            <h4 className="text-sm font-medium text-gray-900 mb-2">Memory History</h4>
            <MemoryChart samples={detailedReport.samples.slice(-20)} />
          </div>
        )}
      </div>
    </div>
  )
}

interface MemoryStatCardProps {
  icon: React.ReactNode
  label: string
  value: string
  subvalue?: string
  status: 'good' | 'warning' | 'error' | 'neutral'
}

const MemoryStatCard: React.FC<MemoryStatCardProps> = ({
  icon,
  label,
  value,
  subvalue,
  status
}) => {
  const statusColors = {
    good: 'text-green-600 bg-green-50 border-green-200',
    warning: 'text-yellow-600 bg-yellow-50 border-yellow-200',
    error: 'text-red-600 bg-red-50 border-red-200',
    neutral: 'text-gray-600 bg-gray-50 border-gray-200'
  }

  return (
    <div className={cn('p-3 rounded-md border', statusColors[status])}>
      <div className="flex items-center space-x-2 mb-1">
        {icon}
        <span className="text-xs font-medium">{label}</span>
      </div>
      <div className="text-sm font-semibold">{value}</div>
      {subvalue && (
        <div className="text-xs opacity-75">{subvalue}</div>
      )}
    </div>
  )
}

interface ComponentProfileCardProps {
  profile: ComponentMemoryProfile
}

const ComponentProfileCard: React.FC<ComponentProfileCardProps> = ({ profile }) => {
  const isActive = !profile.unmountTime
  const memoryDelta = profile.memoryDelta || 0
  const isLeak = profile.isLeak

  return (
    <div className={cn(
      'p-2 rounded border text-xs',
      isLeak ? 'bg-red-50 border-red-200' : 'bg-gray-50 border-gray-200'
    )}>
      <div className="flex items-center justify-between">
        <span className={cn(
          'font-medium truncate flex-1',
          isLeak ? 'text-red-900' : 'text-gray-900'
        )}>
          {profile.componentName}
        </span>
        <div className="flex items-center space-x-2">
          {isActive && (
            <div className="h-2 w-2 bg-green-500 rounded-full" title="Active" />
          )}
          {isLeak && (
            <AlertTriangle className="h-3 w-3 text-red-500" title="Memory Leak" />
          )}
        </div>
      </div>
      <div className="flex items-center justify-between mt-1 text-gray-600">
        <span>
          {memoryDelta > 0 ? '+' : ''}{(memoryDelta / 1024 / 1024).toFixed(2)}MB
        </span>
        <span>
          {isActive ? 'Active' : `${((profile.unmountTime! - profile.mountTime) / 1000).toFixed(1)}s`}
        </span>
      </div>
    </div>
  )
}

interface MemoryLeakCardProps {
  leak: ComponentMemoryProfile
}

const MemoryLeakCard: React.FC<MemoryLeakCardProps> = ({ leak }) => {
  const severityColors = {
    low: 'bg-yellow-50 border-yellow-200 text-yellow-900',
    medium: 'bg-orange-50 border-orange-200 text-orange-900',
    high: 'bg-red-50 border-red-200 text-red-900'
  }

  return (
    <div className={cn(
      'p-3 rounded border',
      severityColors[leak.leakSeverity || 'low']
    )}>
      <div className="flex items-center justify-between mb-1">
        <span className="text-sm font-medium">{leak.componentName}</span>
        <span className="text-xs uppercase font-medium">
          {leak.leakSeverity} severity
        </span>
      </div>
      <div className="text-xs">
        Memory leaked: {((leak.memoryDelta || 0) / 1024 / 1024).toFixed(2)}MB
      </div>
    </div>
  )
}

interface MemoryChartProps {
  samples: MemoryStats[]
}

const MemoryChart: React.FC<MemoryChartProps> = ({ samples }) => {
  if (samples.length === 0) return null

  const maxMemory = Math.max(...samples.map(s => s.usedJSHeapSize))
  const minMemory = Math.min(...samples.map(s => s.usedJSHeapSize))
  const range = maxMemory - minMemory

  return (
    <div className="h-20 border border-gray-200 rounded p-2 bg-gray-50">
      <svg width="100%" height="100%" className="overflow-visible">
        <polyline
          fill="none"
          stroke="#3B82F6"
          strokeWidth="1"
          points={samples.map((sample, index) => {
            const x = (index / (samples.length - 1)) * 100
            const y = range > 0 ? (1 - (sample.usedJSHeapSize - minMemory) / range) * 80 : 50
            return `${x},${y}`
          }).join(' ')}
          vectorEffect="non-scaling-stroke"
        />
      </svg>
      <div className="flex justify-between text-xs text-gray-500 mt-1">
        <span>{((minMemory) / 1024 / 1024).toFixed(1)}MB</span>
        <span>{((maxMemory) / 1024 / 1024).toFixed(1)}MB</span>
      </div>
    </div>
  )
}

export default MemoryMonitorPanel