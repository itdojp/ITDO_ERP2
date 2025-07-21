import React from 'react'
import { Activity, Zap, Clock, TrendingUp, AlertTriangle, BarChart3 } from 'lucide-react'
import { cn } from '../../../lib/utils'
import { usePerformanceMonitor, PerformanceMetric, ComponentPerformanceData } from '../../../hooks/usePerformanceMonitor'

export interface PerformanceMonitorProps {
  className?: string
  showRealTime?: boolean
  showComponents?: boolean
  showWebVitals?: boolean
  refreshInterval?: number
  maxDisplayMetrics?: number
}

const formatValue = (value: number, unit: string): string => {
  if (unit === 'ms') {
    return value < 1000 ? `${Math.round(value)}ms` : `${(value / 1000).toFixed(2)}s`
  }
  if (unit === 'score') {
    return value.toFixed(3)
  }
  return `${Math.round(value)}${unit}`
}

const getPerformanceColor = (value: number, metric: PerformanceMetric): string => {
  const { name, unit } = metric
  
  if (name === 'LCP') {
    return value <= 2500 ? 'text-green-600' : value <= 4000 ? 'text-yellow-600' : 'text-red-600'
  }
  
  if (name === 'FID') {
    return value <= 100 ? 'text-green-600' : value <= 300 ? 'text-yellow-600' : 'text-red-600'
  }
  
  if (name === 'CLS') {
    return value <= 0.1 ? 'text-green-600' : value <= 0.25 ? 'text-yellow-600' : 'text-red-600'
  }
  
  if (unit === 'ms') {
    return value <= 100 ? 'text-green-600' : value <= 500 ? 'text-yellow-600' : 'text-red-600'
  }
  
  return 'text-gray-600'
}

const getMetricIcon = (category: PerformanceMetric['category']) => {
  switch (category) {
    case 'loading':
      return <Clock className="h-4 w-4" />
    case 'rendering':
      return <Activity className="h-4 w-4" />
    case 'interaction':
      return <Zap className="h-4 w-4" />
    case 'navigation':
      return <TrendingUp className="h-4 w-4" />
    case 'resource':
      return <BarChart3 className="h-4 w-4" />
    default:
      return <Activity className="h-4 w-4" />
  }
}

const MetricCard: React.FC<{
  metric: PerformanceMetric
  showTimestamp?: boolean
}> = ({ metric, showTimestamp = false }) => {
  const color = getPerformanceColor(metric.value, metric)
  const icon = getMetricIcon(metric.category)
  
  return (
    <div className="bg-white border border-gray-200 rounded-lg p-3 shadow-sm">
      <div className="flex items-start justify-between">
        <div className="flex items-center space-x-2">
          <div className={cn('flex-shrink-0', color)}>{icon}</div>
          <div className="min-w-0">
            <p className="text-sm font-medium text-gray-900 truncate">
              {metric.name}
            </p>
            <p className="text-xs text-gray-500 capitalize">
              {metric.category}
            </p>
          </div>
        </div>
        <div className="text-right">
          <p className={cn('text-lg font-semibold', color)}>
            {formatValue(metric.value, metric.unit)}
          </p>
          {showTimestamp && (
            <p className="text-xs text-gray-400">
              {new Date(metric.timestamp).toLocaleTimeString()}
            </p>
          )}
        </div>
      </div>
    </div>
  )
}

const ComponentCard: React.FC<{
  component: ComponentPerformanceData
}> = ({ component }) => {
  const isSlowComponent = component.averageRenderTime > 16
  
  return (
    <div className="bg-white border border-gray-200 rounded-lg p-3 shadow-sm">
      <div className="flex items-start justify-between">
        <div className="min-w-0 flex-1">
          <div className="flex items-center space-x-2">
            <h3 className="text-sm font-medium text-gray-900 truncate">
              {component.componentName}
            </h3>
            {isSlowComponent && (
              <AlertTriangle className="h-4 w-4 text-yellow-500 flex-shrink-0" />
            )}
          </div>
          <div className="mt-1 text-xs text-gray-500 space-y-1">
            <div className="flex justify-between">
              <span>Renders:</span>
              <span className="font-mono">{component.renderCount}</span>
            </div>
            <div className="flex justify-between">
              <span>Avg Time:</span>
              <span className={cn(
                'font-mono',
                isSlowComponent ? 'text-yellow-600' : 'text-green-600'
              )}>
                {formatValue(component.averageRenderTime, 'ms')}
              </span>
            </div>
            <div className="flex justify-between">
              <span>Slow Renders:</span>
              <span className={cn(
                'font-mono',
                component.slowRenders > 0 ? 'text-red-600' : 'text-green-600'
              )}>
                {component.slowRenders}
              </span>
            </div>
          </div>
        </div>
        <div className="text-right">
          <p className={cn(
            'text-sm font-semibold',
            isSlowComponent ? 'text-yellow-600' : 'text-green-600'
          )}>
            {formatValue(component.renderTime, 'ms')}
          </p>
          <p className="text-xs text-gray-400">
            Last render
          </p>
        </div>
      </div>
    </div>
  )
}

const PerformanceMonitor = React.memo<PerformanceMonitorProps>(({
  className,
  showRealTime = true,
  showComponents = true,
  showWebVitals = true,
  refreshInterval = 5000,
  maxDisplayMetrics = 10,
}) => {
  const {
    metrics,
    componentData,
    getMetricsByCategory,
    getAverageMetric,
    clearMetrics,
    getSlowComponents,
  } = usePerformanceMonitor({ enabled: true })

  const [activeTab, setActiveTab] = React.useState<'overview' | 'components' | 'details'>('overview')

  // Get recent metrics for display
  const recentMetrics = React.useMemo(() => {
    return metrics
      .slice(-maxDisplayMetrics)
      .sort((a, b) => b.timestamp - a.timestamp)
  }, [metrics, maxDisplayMetrics])

  // Get Web Vitals
  const webVitals = React.useMemo(() => {
    const lcp = getAverageMetric('LCP')
    const fid = getAverageMetric('FID')
    const cls = getAverageMetric('CLS')
    
    return { lcp, fid, cls }
  }, [getAverageMetric])

  // Get performance summary
  const performanceSummary = React.useMemo(() => {
    const loadingMetrics = getMetricsByCategory('loading')
    const renderingMetrics = getMetricsByCategory('rendering')
    const interactionMetrics = getMetricsByCategory('interaction')
    const resourceMetrics = getMetricsByCategory('resource')
    
    const slowComponents = getSlowComponents()
    
    return {
      totalMetrics: metrics.length,
      loadingCount: loadingMetrics.length,
      renderingCount: renderingMetrics.length,
      interactionCount: interactionMetrics.length,
      resourceCount: resourceMetrics.length,
      slowComponentsCount: slowComponents.length,
      averageRenderTime: componentData.reduce((sum, comp) => sum + comp.averageRenderTime, 0) / componentData.length || 0,
    }
  }, [metrics, getMetricsByCategory, getSlowComponents, componentData])

  return (
    <div className={cn('bg-gray-50 rounded-lg border border-gray-200', className)}>
      {/* Header */}
      <div className="px-4 py-3 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold text-gray-900 flex items-center">
            <Activity className="h-5 w-5 mr-2 text-blue-500" />
            Performance Monitor
          </h2>
          <div className="flex items-center space-x-2">
            <button
              onClick={clearMetrics}
              className="text-sm text-gray-500 hover:text-gray-700 px-2 py-1 rounded"
            >
              Clear
            </button>
          </div>
        </div>
        
        {/* Tabs */}
        <div className="flex space-x-4 mt-3">
          {['overview', 'components', 'details'].map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab as any)}
              className={cn(
                'px-3 py-1 text-sm font-medium rounded-md capitalize',
                activeTab === tab
                  ? 'bg-blue-100 text-blue-700'
                  : 'text-gray-500 hover:text-gray-700'
              )}
            >
              {tab}
            </button>
          ))}
        </div>
      </div>

      <div className="p-4">
        {/* Overview Tab */}
        {activeTab === 'overview' && (
          <div className="space-y-6">
            {/* Summary Stats */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="bg-white rounded-lg border p-3 text-center">
                <p className="text-2xl font-bold text-blue-600">{performanceSummary.totalMetrics}</p>
                <p className="text-xs text-gray-500">Total Metrics</p>
              </div>
              <div className="bg-white rounded-lg border p-3 text-center">
                <p className="text-2xl font-bold text-green-600">{componentData.length}</p>
                <p className="text-xs text-gray-500">Components</p>
              </div>
              <div className="bg-white rounded-lg border p-3 text-center">
                <p className="text-2xl font-bold text-yellow-600">{performanceSummary.slowComponentsCount}</p>
                <p className="text-xs text-gray-500">Slow Components</p>
              </div>
              <div className="bg-white rounded-lg border p-3 text-center">
                <p className="text-2xl font-bold text-purple-600">
                  {formatValue(performanceSummary.averageRenderTime, 'ms')}
                </p>
                <p className="text-xs text-gray-500">Avg Render</p>
              </div>
            </div>

            {/* Web Vitals */}
            {showWebVitals && (
              <div>
                <h3 className="text-sm font-medium text-gray-900 mb-3">Web Vitals</h3>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  {webVitals.lcp && (
                    <div className="bg-white rounded-lg border p-3">
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="text-sm font-medium text-gray-900">LCP</p>
                          <p className="text-xs text-gray-500">Largest Contentful Paint</p>
                        </div>
                        <p className={cn(
                          'text-lg font-semibold',
                          webVitals.lcp.average <= 2500 ? 'text-green-600' :
                          webVitals.lcp.average <= 4000 ? 'text-yellow-600' : 'text-red-600'
                        )}>
                          {formatValue(webVitals.lcp.average, webVitals.lcp.unit)}
                        </p>
                      </div>
                    </div>
                  )}
                  
                  {webVitals.fid && (
                    <div className="bg-white rounded-lg border p-3">
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="text-sm font-medium text-gray-900">FID</p>
                          <p className="text-xs text-gray-500">First Input Delay</p>
                        </div>
                        <p className={cn(
                          'text-lg font-semibold',
                          webVitals.fid.average <= 100 ? 'text-green-600' :
                          webVitals.fid.average <= 300 ? 'text-yellow-600' : 'text-red-600'
                        )}>
                          {formatValue(webVitals.fid.average, webVitals.fid.unit)}
                        </p>
                      </div>
                    </div>
                  )}
                  
                  {webVitals.cls && (
                    <div className="bg-white rounded-lg border p-3">
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="text-sm font-medium text-gray-900">CLS</p>
                          <p className="text-xs text-gray-500">Cumulative Layout Shift</p>
                        </div>
                        <p className={cn(
                          'text-lg font-semibold',
                          webVitals.cls.average <= 0.1 ? 'text-green-600' :
                          webVitals.cls.average <= 0.25 ? 'text-yellow-600' : 'text-red-600'
                        )}>
                          {formatValue(webVitals.cls.average, webVitals.cls.unit)}
                        </p>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Recent Metrics */}
            {showRealTime && recentMetrics.length > 0 && (
              <div>
                <h3 className="text-sm font-medium text-gray-900 mb-3">Recent Metrics</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                  {recentMetrics.slice(0, 6).map((metric, index) => (
                    <MetricCard
                      key={`${metric.name}-${metric.timestamp}-${index}`}
                      metric={metric}
                      showTimestamp={true}
                    />
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Components Tab */}
        {activeTab === 'components' && (
          <div className="space-y-4">
            {componentData.length > 0 ? (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {componentData
                  .sort((a, b) => b.averageRenderTime - a.averageRenderTime)
                  .map((component) => (
                    <ComponentCard
                      key={component.componentName}
                      component={component}
                    />
                  ))}
              </div>
            ) : (
              <div className="text-center py-8 text-gray-500">
                <Activity className="h-12 w-12 mx-auto mb-4 text-gray-300" />
                <p>No component performance data available</p>
                <p className="text-sm">Components will appear here as they render</p>
              </div>
            )}
          </div>
        )}

        {/* Details Tab */}
        {activeTab === 'details' && (
          <div className="space-y-6">
            {/* Metrics by Category */}
            {['loading', 'rendering', 'interaction', 'resource'].map((category) => {
              const categoryMetrics = getMetricsByCategory(category as any)
              if (categoryMetrics.length === 0) return null

              return (
                <div key={category}>
                  <h3 className="text-sm font-medium text-gray-900 mb-3 capitalize flex items-center">
                    {getMetricIcon(category as any)}
                    <span className="ml-2">{category} Metrics ({categoryMetrics.length})</span>
                  </h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                    {categoryMetrics.slice(-6).map((metric, index) => (
                      <MetricCard
                        key={`${metric.name}-${metric.timestamp}-${index}`}
                        metric={metric}
                      />
                    ))}
                  </div>
                </div>
              )
            })}
          </div>
        )}
      </div>
    </div>
  )
})

PerformanceMonitor.displayName = 'PerformanceMonitor'

export default PerformanceMonitor