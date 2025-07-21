import React from 'react'
import { 
  Package, 
  BarChart3, 
  AlertTriangle, 
  CheckCircle, 
  TrendingUp, 
  TrendingDown,
  FileText,
  Zap,
  Layers,
  HardDrive,
  RefreshCw
} from 'lucide-react'
import { cn } from '../../lib/utils'
import { 
  useBundleMonitoring, 
  formatSize, 
  calculateSizeDiff, 
  isBundleSizeAcceptable,
  BundleAnalysisReport,
  OptimizationOpportunity,
  BUNDLE_THRESHOLDS
} from '../../utils/bundleAnalysis'

export interface BundleAnalysisPanelProps {
  className?: string
  onOptimizationClick?: (opportunity: OptimizationOpportunity) => void
}

const BundleAnalysisPanel: React.FC<BundleAnalysisPanelProps> = ({
  className,
  onOptimizationClick
}) => {
  const { analysis, loading, analyzeBundle } = useBundleMonitoring()

  if (process.env.NODE_ENV !== 'development') {
    return null
  }

  if (loading) {
    return (
      <div className={cn('p-4 bg-gray-50 rounded-lg border', className)}>
        <div className="flex items-center space-x-2">
          <RefreshCw className="h-4 w-4 animate-spin" />
          <span className="text-sm text-gray-600">Analyzing bundle...</span>
        </div>
      </div>
    )
  }

  if (!analysis) {
    return (
      <div className={cn('p-4 bg-yellow-50 rounded-lg border border-yellow-200', className)}>
        <div className="flex items-center space-x-2">
          <AlertTriangle className="h-4 w-4 text-yellow-600" />
          <span className="text-sm text-yellow-800">Bundle analysis not available</span>
          <button
            onClick={analyzeBundle}
            className="text-xs text-yellow-600 hover:text-yellow-800 underline"
          >
            Retry
          </button>
        </div>
      </div>
    )
  }

  const isAcceptable = isBundleSizeAcceptable(analysis.summary)

  return (
    <div className={cn('bg-white rounded-lg border shadow-sm', className)}>
      {/* Header */}
      <div className="px-4 py-3 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Package className="h-5 w-5 text-gray-600" />
            <h3 className="text-sm font-medium text-gray-900">Bundle Analysis</h3>
            {isAcceptable ? (
              <CheckCircle className="h-4 w-4 text-green-500" />
            ) : (
              <AlertTriangle className="h-4 w-4 text-yellow-500" />
            )}
          </div>
          <button
            onClick={analyzeBundle}
            className="text-xs text-gray-500 hover:text-gray-700"
          >
            <RefreshCw className="h-3 w-3" />
          </button>
        </div>
      </div>

      {/* Summary Stats */}
      <div className="p-4">
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-4">
          <SummaryCard
            icon={<HardDrive className="h-4 w-4" />}
            label="Total Size"
            value={formatSize(analysis.summary.totalBundleSize)}
            subvalue={`${formatSize(analysis.summary.totalGzipSize)} gzipped`}
            status={analysis.summary.totalBundleSize > BUNDLE_THRESHOLDS.TOTAL_WARNING * 1024 ? 'warning' : 'good'}
          />
          <SummaryCard
            icon={<Layers className="h-4 w-4" />}
            label="Chunks"
            value={analysis.summary.chunkCount.toString()}
            subvalue={`Largest: ${analysis.summary.largestChunk}`}
            status="neutral"
          />
          <SummaryCard
            icon={<Package className="h-4 w-4" />}
            label="Vendor Size"
            value={formatSize(analysis.summary.vendorChunkSize)}
            subvalue={`${Math.round((analysis.summary.vendorChunkSize / analysis.summary.totalBundleSize) * 100)}% of total`}
            status={analysis.summary.vendorChunkSize > BUNDLE_THRESHOLDS.VENDOR_WARNING * 1024 ? 'warning' : 'good'}
          />
          <SummaryCard
            icon={<Zap className="h-4 w-4" />}
            label="Compression"
            value={`${Math.round((1 - analysis.summary.compressionRatio) * 100)}%`}
            subvalue="Gzip ratio"
            status={analysis.summary.compressionRatio > 0.5 ? 'warning' : 'good'}
          />
        </div>

        {/* Largest Chunks */}
        {analysis.largestChunks.length > 0 && (
          <div className="mb-4">
            <h4 className="text-sm font-medium text-gray-900 mb-2 flex items-center">
              <BarChart3 className="h-4 w-4 mr-1" />
              Largest Chunks
            </h4>
            <div className="space-y-2">
              {analysis.largestChunks.slice(0, 5).map((chunk, index) => (
                <ChunkBar
                  key={chunk.name}
                  chunk={chunk}
                  maxSize={analysis.largestChunks[0].size}
                  rank={index + 1}
                />
              ))}
            </div>
          </div>
        )}

        {/* Optimization Opportunities */}
        {analysis.optimizationOpportunities.length > 0 && (
          <div className="mb-4">
            <h4 className="text-sm font-medium text-gray-900 mb-2 flex items-center">
              <TrendingUp className="h-4 w-4 mr-1" />
              Optimization Opportunities
            </h4>
            <div className="space-y-2">
              {analysis.optimizationOpportunities.slice(0, 3).map((opportunity, index) => (
                <OptimizationCard
                  key={index}
                  opportunity={opportunity}
                  onClick={() => onOptimizationClick?.(opportunity)}
                />
              ))}
            </div>
          </div>
        )}

        {/* Heavy Modules */}
        {analysis.heaviestModules.length > 0 && (
          <div>
            <h4 className="text-sm font-medium text-gray-900 mb-2 flex items-center">
              <FileText className="h-4 w-4 mr-1" />
              Heaviest Modules
            </h4>
            <div className="space-y-1 max-h-32 overflow-y-auto">
              {analysis.heaviestModules.slice(0, 10).map((module, index) => (
                <div key={index} className="flex items-center justify-between text-xs">
                  <span className="text-gray-600 truncate flex-1 mr-2" title={module.name}>
                    {module.name.length > 30 ? `...${module.name.slice(-30)}` : module.name}
                  </span>
                  <span className="text-gray-900 font-medium">
                    {formatSize(module.size)}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

interface SummaryCardProps {
  icon: React.ReactNode
  label: string
  value: string
  subvalue?: string
  status: 'good' | 'warning' | 'error' | 'neutral'
}

const SummaryCard: React.FC<SummaryCardProps> = ({
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
      <div className="text-lg font-semibold">{value}</div>
      {subvalue && (
        <div className="text-xs opacity-75">{subvalue}</div>
      )}
    </div>
  )
}

interface ChunkBarProps {
  chunk: any
  maxSize: number
  rank: number
}

const ChunkBar: React.FC<ChunkBarProps> = ({ chunk, maxSize, rank }) => {
  const percentage = (chunk.size / maxSize) * 100

  return (
    <div className="flex items-center space-x-2">
      <span className="text-xs text-gray-500 w-4">{rank}</span>
      <div className="flex-1">
        <div className="flex items-center justify-between mb-1">
          <span className="text-xs font-medium text-gray-900">{chunk.name}</span>
          <span className="text-xs text-gray-600">{formatSize(chunk.size)}</span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div
            className={cn(
              'h-2 rounded-full',
              chunk.isVendor ? 'bg-blue-500' : 'bg-green-500'
            )}
            style={{ width: `${percentage}%` }}
          />
        </div>
      </div>
    </div>
  )
}

interface OptimizationCardProps {
  opportunity: OptimizationOpportunity
  onClick?: () => void
}

const OptimizationCard: React.FC<OptimizationCardProps> = ({
  opportunity,
  onClick
}) => {
  const impactColors = {
    high: 'border-red-200 bg-red-50',
    medium: 'border-yellow-200 bg-yellow-50',
    low: 'border-blue-200 bg-blue-50'
  }

  const impactIcons = {
    high: <TrendingUp className="h-4 w-4 text-red-600" />,
    medium: <TrendingUp className="h-4 w-4 text-yellow-600" />,
    low: <TrendingUp className="h-4 w-4 text-blue-600" />
  }

  return (
    <div
      className={cn(
        'p-3 rounded-md border cursor-pointer hover:shadow-sm transition-shadow',
        impactColors[opportunity.impact]
      )}
      onClick={onClick}
    >
      <div className="flex items-start space-x-2">
        {impactIcons[opportunity.impact]}
        <div className="flex-1 min-w-0">
          <div className="flex items-center justify-between mb-1">
            <span className="text-sm font-medium text-gray-900 capitalize">
              {opportunity.type.replace('-', ' ')}
            </span>
            <span className="text-xs text-gray-600">
              -{formatSize(opportunity.sizeSaving)}
            </span>
          </div>
          <p className="text-xs text-gray-700 mb-2">{opportunity.description}</p>
          <p className="text-xs text-gray-600 italic">{opportunity.implementation}</p>
        </div>
      </div>
    </div>
  )
}

export default BundleAnalysisPanel