import React from 'react'
import { 
  Zap, 
  Clock, 
  BarChart3, 
  AlertTriangle, 
  TrendingUp, 
  RefreshCw,
  Activity,
  Target,
  Layers,
  CheckCircle,
  XCircle
} from 'lucide-react'
import { cn } from '../../lib/utils'
import { 
  usePerformanceReport, 
  useComponentProfiler,
  reactDevToolsProfiler,
  ComponentProfile,
  PerformanceRecommendation,
  PERFORMANCE_THRESHOLDS
} from '../../utils/reactDevToolsProfiler'

export interface PerformanceProfilerPanelProps {
  className?: string
  showRecommendations?: boolean
  autoRefresh?: boolean
  refreshInterval?: number
}

const PerformanceProfilerPanel: React.FC<PerformanceProfilerPanelProps> = ({
  className,
  showRecommendations = true,
  autoRefresh = true,
  refreshInterval = 3000
}) => {
  const { report, isGenerating, generateReport, clear } = usePerformanceReport()
  const [selectedComponent, setSelectedComponent] = React.useState<string | null>(null)

  React.useEffect(() => {
    generateReport()
  }, [generateReport])

  React.useEffect(() => {
    if (!autoRefresh) return

    const interval = setInterval(generateReport, refreshInterval)
    return () => clearInterval(interval)
  }, [autoRefresh, refreshInterval, generateReport])

  if (process.env.NODE_ENV !== 'development') {
    return null
  }

  if (!reactDevToolsProfiler.isProfilerEnabled()) {
    return (
      <div className={cn('p-4 bg-yellow-50 rounded-lg border border-yellow-200', className)}>
        <div className="flex items-center space-x-2">
          <AlertTriangle className="h-4 w-4 text-yellow-600" />
          <span className="text-sm text-yellow-800">React DevTools Profiler not available</span>
        </div>
      </div>
    )
  }

  return (
    <div className={cn('bg-white rounded-lg border shadow-sm', className)}>
      {/* Header */}
      <div className="px-4 py-3 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Zap className="h-5 w-5 text-gray-600" />
            <h3 className="text-sm font-medium text-gray-900">Performance Profiler</h3>
            {report && (
              <span className="text-xs text-gray-500">
                ({report.totalComponents} components)
              </span>
            )}
          </div>
          <div className="flex items-center space-x-2">
            <button
              onClick={generateReport}
              disabled={isGenerating}
              className="text-xs text-gray-500 hover:text-gray-700 p-1"
              title="Refresh Report"
            >
              <RefreshCw className={cn('h-3 w-3', isGenerating && 'animate-spin')} />
            </button>
            <button
              onClick={clear}
              className="text-xs text-gray-500 hover:text-gray-700 p-1"
              title="Clear Data"
            >
              <XCircle className="h-3 w-3" />
            </button>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="p-4">
        {!report ? (
          <div className="text-center py-8">
            <Activity className="h-8 w-8 text-gray-400 mx-auto mb-2" />
            <p className="text-sm text-gray-600">No profiling data available</p>
            <p className="text-xs text-gray-500 mt-1">
              Interact with components to start collecting data
            </p>
          </div>
        ) : (
          <>
            {/* Summary Stats */}
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-4">
              <PerformanceStat
                icon={<BarChart3 className="h-4 w-4" />}
                label="Avg Render"
                value={`${report.averageRenderTime.toFixed(2)}ms`}
                status={report.averageRenderTime > PERFORMANCE_THRESHOLDS.SLOW_RENDER ? 'warning' : 'good'}
              />
              <PerformanceStat
                icon={<Clock className="h-4 w-4" />}
                label="Total Time"
                value={`${report.totalRenderTime.toFixed(2)}ms`}
                status="neutral"
              />
              <PerformanceStat
                icon={<Layers className="h-4 w-4" />}
                label="Components"
                value={report.totalComponents.toString()}
                status="neutral"
              />
              <PerformanceStat
                icon={<AlertTriangle className="h-4 w-4" />}
                label="Slow Components"
                value={report.slowComponents.length.toString()}
                status={report.slowComponents.length > 0 ? 'warning' : 'good'}
              />
            </div>

            {/* Slow Components */}
            {report.slowComponents.length > 0 && (
              <div className="mb-4">
                <h4 className="text-sm font-medium text-gray-900 mb-2 flex items-center">
                  <TrendingUp className="h-4 w-4 mr-1 text-red-500" />
                  Slow Components ({report.slowComponents.length})
                </h4>
                <div className="space-y-2 max-h-48 overflow-y-auto">
                  {report.slowComponents.slice(0, 10).map((component, index) => (
                    <ComponentCard
                      key={component.componentId}
                      component={component}
                      rank={index + 1}
                      isSelected={selectedComponent === component.componentId}
                      onClick={() => setSelectedComponent(
                        selectedComponent === component.componentId ? null : component.componentId
                      )}
                    />
                  ))}
                </div>
              </div>
            )}

            {/* Component Details */}
            {selectedComponent && (
              <ComponentDetails componentId={selectedComponent} />
            )}

            {/* Recommendations */}
            {showRecommendations && report.recommendations.length > 0 && (
              <div className="mb-4">
                <h4 className="text-sm font-medium text-gray-900 mb-2 flex items-center">
                  <Target className="h-4 w-4 mr-1" />
                  Performance Recommendations ({report.recommendations.length})
                </h4>
                <div className="space-y-2 max-h-48 overflow-y-auto">
                  {report.recommendations.slice(0, 5).map((recommendation, index) => (
                    <RecommendationCard key={index} recommendation={recommendation} />
                  ))}
                </div>
              </div>
            )}

            {/* Interactions */}
            {report.interactionsSummary.length > 0 && (
              <div>
                <h4 className="text-sm font-medium text-gray-900 mb-2">
                  User Interactions ({report.interactionsSummary.length})
                </h4>
                <div className="space-y-1 max-h-32 overflow-y-auto">
                  {report.interactionsSummary.slice(0, 5).map((interaction, index) => (
                    <div key={index} className="flex items-center justify-between text-xs p-2 bg-gray-50 rounded">
                      <span className="font-medium text-gray-900">{interaction.name}</span>
                      <div className="text-gray-600">
                        <span>{interaction.duration.toFixed(2)}ms</span>
                        <span className="ml-2">({interaction.componentsAffected.length} components)</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  )
}

interface PerformanceStatProps {
  icon: React.ReactNode
  label: string
  value: string
  status: 'good' | 'warning' | 'error' | 'neutral'
}

const PerformanceStat: React.FC<PerformanceStatProps> = ({
  icon,
  label,
  value,
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
    </div>
  )
}

interface ComponentCardProps {
  component: ComponentProfile
  rank: number
  isSelected: boolean
  onClick: () => void
}

const ComponentCard: React.FC<ComponentCardProps> = ({
  component,
  rank,
  isSelected,
  onClick
}) => {
  const getSeverityColor = (duration: number) => {
    if (duration > PERFORMANCE_THRESHOLDS.CRITICAL_RENDER) return 'text-red-600 bg-red-50 border-red-200'
    if (duration > PERFORMANCE_THRESHOLDS.VERY_SLOW_RENDER) return 'text-orange-600 bg-orange-50 border-orange-200'
    if (duration > PERFORMANCE_THRESHOLDS.SLOW_RENDER) return 'text-yellow-600 bg-yellow-50 border-yellow-200'
    return 'text-gray-600 bg-gray-50 border-gray-200'
  }

  return (
    <div
      className={cn(
        'p-3 rounded border cursor-pointer transition-all',
        getSeverityColor(component.averageDuration),
        isSelected && 'ring-2 ring-blue-500'
      )}
      onClick={onClick}
    >
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <span className="text-xs font-medium w-6">#{rank}</span>
          <span className="text-sm font-medium truncate">{component.componentId}</span>
        </div>
        <div className="text-xs text-right">
          <div>{component.averageDuration.toFixed(2)}ms avg</div>
          <div className="text-gray-500">{component.totalRenders} renders</div>
        </div>
      </div>
      
      {isSelected && (
        <div className="mt-2 pt-2 border-t border-current border-opacity-20">
          <div className="grid grid-cols-2 gap-2 text-xs">
            <div>
              <span className="text-gray-600">Fastest:</span> {component.fastestRender.toFixed(2)}ms
            </div>
            <div>
              <span className="text-gray-600">Slowest:</span> {component.slowestRender.toFixed(2)}ms
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

interface ComponentDetailsProps {
  componentId: string
}

const ComponentDetails: React.FC<ComponentDetailsProps> = ({ componentId }) => {
  const { profile } = useComponentProfiler(componentId)

  if (!profile) return null

  return (
    <div className="mb-4 p-3 bg-blue-50 border border-blue-200 rounded">
      <h5 className="text-sm font-medium text-blue-900 mb-2">{componentId} Details</h5>
      <div className="grid grid-cols-2 gap-4 text-xs">
        <div>
          <div className="text-blue-700 font-medium">Render Statistics</div>
          <div className="mt-1 space-y-1">
            <div>Total Renders: {profile.totalRenders}</div>
            <div>Average: {profile.averageDuration.toFixed(2)}ms</div>
            <div>Range: {profile.fastestRender.toFixed(2)}ms - {profile.slowestRender.toFixed(2)}ms</div>
            <div>Total Time: {profile.totalDuration.toFixed(2)}ms</div>
          </div>
        </div>
        <div>
          <div className="text-blue-700 font-medium">Recent Activity</div>
          <div className="mt-1 space-y-1">
            {profile.renderPhases.slice(-3).map((phase, index) => (
              <div key={index} className="flex justify-between">
                <span className="capitalize">{phase.phase}</span>
                <span>{phase.duration.toFixed(2)}ms</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}

interface RecommendationCardProps {
  recommendation: PerformanceRecommendation
}

const RecommendationCard: React.FC<RecommendationCardProps> = ({ recommendation }) => {
  const impactColors = {
    high: 'border-red-200 bg-red-50',
    medium: 'border-yellow-200 bg-yellow-50',
    low: 'border-blue-200 bg-blue-50'
  }

  const impactIcons = {
    high: <AlertTriangle className="h-4 w-4 text-red-600" />,
    medium: <TrendingUp className="h-4 w-4 text-yellow-600" />,
    low: <CheckCircle className="h-4 w-4 text-blue-600" />
  }

  return (
    <div className={cn('p-3 rounded border', impactColors[recommendation.impact])}>
      <div className="flex items-start space-x-2">
        {impactIcons[recommendation.impact]}
        <div className="flex-1 min-w-0">
          <div className="flex items-center justify-between mb-1">
            <span className="text-sm font-medium text-gray-900">
              {recommendation.componentId}
            </span>
            <span className="text-xs uppercase font-medium">
              {recommendation.impact} impact
            </span>
          </div>
          <p className="text-xs text-gray-700 mb-1">{recommendation.issue}</p>
          <p className="text-xs text-gray-600 italic">{recommendation.recommendation}</p>
          <p className="text-xs text-green-600 mt-1">{recommendation.estimatedImprovement}</p>
        </div>
      </div>
    </div>
  )
}

export default PerformanceProfilerPanel