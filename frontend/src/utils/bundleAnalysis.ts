/**
 * Bundle Analysis and Optimization Utilities
 */

export interface BundleStats {
  totalSize: number
  gzipSize: number
  chunks: ChunkInfo[]
  assets: AssetInfo[]
  modules: ModuleInfo[]
  warnings: string[]
  recommendations: string[]
}

export interface ChunkInfo {
  name: string
  size: number
  gzipSize: number
  modules: string[]
  isEntry: boolean
  isVendor: boolean
}

export interface AssetInfo {
  name: string
  size: number
  type: 'js' | 'css' | 'image' | 'font' | 'other'
  compressed?: number
}

export interface ModuleInfo {
  name: string
  size: number
  chunks: string[]
  isExternal: boolean
  reasons: string[]
}

export interface BundleAnalysisReport {
  summary: BundleSummary
  largestChunks: ChunkInfo[]
  duplicateModules: ModuleInfo[]
  unusedExports: string[]
  heaviestModules: ModuleInfo[]
  optimizationOpportunities: OptimizationOpportunity[]
}

export interface BundleSummary {
  totalBundleSize: number
  totalGzipSize: number
  chunkCount: number
  largestChunk: string
  vendorChunkSize: number
  appChunkSize: number
  compressionRatio: number
}

export interface OptimizationOpportunity {
  type: 'chunk-splitting' | 'tree-shaking' | 'compression' | 'lazy-loading' | 'vendor-optimization'
  description: string
  impact: 'high' | 'medium' | 'low'
  sizeSaving: number
  implementation: string
}

// Bundle size thresholds (in KB)
export const BUNDLE_THRESHOLDS = {
  CHUNK_WARNING: 500, // 500KB
  CHUNK_ERROR: 1000, // 1MB
  TOTAL_WARNING: 2000, // 2MB
  TOTAL_ERROR: 5000, // 5MB
  VENDOR_WARNING: 1000, // 1MB
  VENDOR_ERROR: 2000, // 2MB
} as const

// Analyze bundle statistics
export const analyzeBundleStats = async (statsPath?: string): Promise<BundleAnalysisReport> => {
  try {
    let stats: any = null
    
    if (statsPath) {
      const response = await fetch(statsPath)
      stats = await response.json()
    } else if (typeof window !== 'undefined') {
      // Try to get stats from build artifacts
      try {
        const response = await fetch('/dist/bundle-stats.json')
        stats = await response.json()
      } catch {
        console.warn('Bundle stats not found, generating mock analysis')
        return generateMockAnalysis()
      }
    }

    if (!stats) {
      return generateMockAnalysis()
    }

    const chunks = extractChunkInfo(stats)
    const modules = extractModuleInfo(stats)
    const assets = extractAssetInfo(stats)

    const summary = generateSummary(chunks, assets)
    const largestChunks = chunks
      .sort((a, b) => b.size - a.size)
      .slice(0, 10)

    const duplicateModules = findDuplicateModules(modules)
    const heaviestModules = modules
      .sort((a, b) => b.size - a.size)
      .slice(0, 20)

    const optimizationOpportunities = identifyOptimizationOpportunities(
      chunks,
      modules,
      assets,
      summary
    )

    return {
      summary,
      largestChunks,
      duplicateModules,
      unusedExports: [], // Would need static analysis
      heaviestModules,
      optimizationOpportunities
    }
  } catch (error) {
    console.error('Bundle analysis failed:', error)
    return generateMockAnalysis()
  }
}

// Extract chunk information from webpack stats
const extractChunkInfo = (stats: any): ChunkInfo[] => {
  if (!stats.chunks) return []

  return stats.chunks.map((chunk: any) => ({
    name: chunk.names?.[0] || chunk.id,
    size: chunk.size || 0,
    gzipSize: Math.round((chunk.size || 0) * 0.3), // Estimate
    modules: chunk.modules?.map((m: any) => m.name || m.identifier) || [],
    isEntry: chunk.entry || false,
    isVendor: chunk.names?.some((name: string) => 
      name.includes('vendor') || name.includes('node_modules')
    ) || false
  }))
}

// Extract module information
const extractModuleInfo = (stats: any): ModuleInfo[] => {
  if (!stats.modules) return []

  return stats.modules.map((module: any) => ({
    name: module.name || module.identifier || 'unknown',
    size: module.size || 0,
    chunks: module.chunks || [],
    isExternal: module.name?.includes('node_modules') || false,
    reasons: module.reasons?.map((r: any) => r.moduleName) || []
  }))
}

// Extract asset information
const extractAssetInfo = (stats: any): AssetInfo[] => {
  if (!stats.assets) return []

  return stats.assets.map((asset: any) => {
    const name = asset.name
    let type: AssetInfo['type'] = 'other'

    if (name.endsWith('.js')) type = 'js'
    else if (name.endsWith('.css')) type = 'css'
    else if (/\.(png|jpg|jpeg|gif|svg|webp)$/i.test(name)) type = 'image'
    else if (/\.(woff|woff2|ttf|eot)$/i.test(name)) type = 'font'

    return {
      name,
      size: asset.size || 0,
      type,
      compressed: asset.compressed
    }
  })
}

// Generate bundle summary
const generateSummary = (chunks: ChunkInfo[], assets: AssetInfo[]): BundleSummary => {
  const totalBundleSize = assets.reduce((acc, asset) => acc + asset.size, 0)
  const totalGzipSize = Math.round(totalBundleSize * 0.3) // Estimate

  const vendorChunks = chunks.filter(c => c.isVendor)
  const appChunks = chunks.filter(c => !c.isVendor)

  const vendorChunkSize = vendorChunks.reduce((acc, chunk) => acc + chunk.size, 0)
  const appChunkSize = appChunks.reduce((acc, chunk) => acc + chunk.size, 0)

  const largestChunk = chunks.reduce((largest, chunk) => 
    chunk.size > largest.size ? chunk : largest, chunks[0] || { name: 'none', size: 0 }
  )

  return {
    totalBundleSize,
    totalGzipSize,
    chunkCount: chunks.length,
    largestChunk: largestChunk.name,
    vendorChunkSize,
    appChunkSize,
    compressionRatio: totalBundleSize > 0 ? totalGzipSize / totalBundleSize : 0
  }
}

// Find duplicate modules across chunks
const findDuplicateModules = (modules: ModuleInfo[]): ModuleInfo[] => {
  const moduleChunkMap = new Map<string, string[]>()
  
  modules.forEach(module => {
    if (!moduleChunkMap.has(module.name)) {
      moduleChunkMap.set(module.name, [])
    }
    moduleChunkMap.get(module.name)!.push(...module.chunks)
  })

  return modules.filter(module => {
    const chunks = moduleChunkMap.get(module.name) || []
    return new Set(chunks).size > 1 // Module appears in multiple chunks
  })
}

// Identify optimization opportunities
const identifyOptimizationOpportunities = (
  chunks: ChunkInfo[],
  modules: ModuleInfo[],
  assets: AssetInfo[],
  summary: BundleSummary
): OptimizationOpportunity[] => {
  const opportunities: OptimizationOpportunity[] = []

  // Large chunk splitting
  const largeChunks = chunks.filter(c => c.size > BUNDLE_THRESHOLDS.CHUNK_WARNING * 1024)
  if (largeChunks.length > 0) {
    opportunities.push({
      type: 'chunk-splitting',
      description: `${largeChunks.length} chunks are larger than ${BUNDLE_THRESHOLDS.CHUNK_WARNING}KB`,
      impact: 'high',
      sizeSaving: largeChunks.reduce((acc, c) => acc + Math.max(0, c.size - BUNDLE_THRESHOLDS.CHUNK_WARNING * 1024), 0),
      implementation: 'Split large chunks using dynamic imports and code splitting'
    })
  }

  // Vendor chunk optimization
  if (summary.vendorChunkSize > BUNDLE_THRESHOLDS.VENDOR_WARNING * 1024) {
    opportunities.push({
      type: 'vendor-optimization',
      description: `Vendor chunk is ${Math.round(summary.vendorChunkSize / 1024)}KB`,
      impact: 'medium',
      sizeSaving: Math.max(0, summary.vendorChunkSize - BUNDLE_THRESHOLDS.VENDOR_WARNING * 1024),
      implementation: 'Split vendor libraries into separate chunks based on usage patterns'
    })
  }

  // Compression opportunities
  if (summary.compressionRatio > 0.5) {
    opportunities.push({
      type: 'compression',
      description: 'Bundle has poor compression ratio',
      impact: 'medium',
      sizeSaving: Math.round(summary.totalBundleSize * 0.2),
      implementation: 'Enable brotli compression and optimize asset delivery'
    })
  }

  // Tree shaking opportunities
  const heavyModules = modules.filter(m => m.size > 50 * 1024 && m.isExternal)
  if (heavyModules.length > 0) {
    opportunities.push({
      type: 'tree-shaking',
      description: `${heavyModules.length} large external modules may not be tree-shaken`,
      impact: 'high',
      sizeSaving: heavyModules.reduce((acc, m) => acc + Math.round(m.size * 0.3), 0),
      implementation: 'Review imports and ensure tree-shaking compatible imports'
    })
  }

  // Lazy loading opportunities
  const nonCriticalChunks = chunks.filter(c => !c.isEntry && c.size > 100 * 1024)
  if (nonCriticalChunks.length > 0) {
    opportunities.push({
      type: 'lazy-loading',
      description: `${nonCriticalChunks.length} non-critical chunks can be lazy loaded`,
      impact: 'medium',
      sizeSaving: nonCriticalChunks.reduce((acc, c) => acc + c.size, 0),
      implementation: 'Implement route-based code splitting and lazy component loading'
    })
  }

  return opportunities.sort((a, b) => {
    const impactWeight = { high: 3, medium: 2, low: 1 }
    return impactWeight[b.impact] - impactWeight[a.impact]
  })
}

// Generate mock analysis for development
const generateMockAnalysis = (): BundleAnalysisReport => {
  const mockChunks: ChunkInfo[] = [
    {
      name: 'main',
      size: 250 * 1024,
      gzipSize: 80 * 1024,
      modules: ['src/main.tsx', 'src/App.tsx'],
      isEntry: true,
      isVendor: false
    },
    {
      name: 'vendor',
      size: 800 * 1024,
      gzipSize: 250 * 1024,
      modules: ['react', 'react-dom', '@tanstack/react-query'],
      isEntry: false,
      isVendor: true
    }
  ]

  const mockSummary: BundleSummary = {
    totalBundleSize: 1050 * 1024,
    totalGzipSize: 330 * 1024,
    chunkCount: 2,
    largestChunk: 'vendor',
    vendorChunkSize: 800 * 1024,
    appChunkSize: 250 * 1024,
    compressionRatio: 0.31
  }

  return {
    summary: mockSummary,
    largestChunks: mockChunks,
    duplicateModules: [],
    unusedExports: [],
    heaviestModules: [],
    optimizationOpportunities: []
  }
}

// Bundle size monitoring hook
export const useBundleMonitoring = () => {
  const [analysis, setAnalysis] = React.useState<BundleAnalysisReport | null>(null)
  const [loading, setLoading] = React.useState(false)

  const analyzeBundle = React.useCallback(async () => {
    setLoading(true)
    try {
      const result = await analyzeBundleStats()
      setAnalysis(result)
    } catch (error) {
      console.error('Bundle analysis failed:', error)
    } finally {
      setLoading(false)
    }
  }, [])

  React.useEffect(() => {
    if (process.env.NODE_ENV === 'development') {
      analyzeBundle()
    }
  }, [analyzeBundle])

  return {
    analysis,
    loading,
    analyzeBundle
  }
}

// Format size for display
export const formatSize = (bytes: number): string => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(1))} ${sizes[i]}`
}

// Calculate size difference
export const calculateSizeDiff = (before: number, after: number): string => {
  const diff = after - before
  const percentage = before > 0 ? ((diff / before) * 100).toFixed(1) : '0'
  const sign = diff > 0 ? '+' : ''
  return `${sign}${formatSize(Math.abs(diff))} (${sign}${percentage}%)`
}

// Check if bundle size is within acceptable limits
export const isBundleSizeAcceptable = (summary: BundleSummary): boolean => {
  return (
    summary.totalBundleSize < BUNDLE_THRESHOLDS.TOTAL_WARNING * 1024 &&
    summary.vendorChunkSize < BUNDLE_THRESHOLDS.VENDOR_WARNING * 1024 &&
    summary.largestChunk !== 'unknown'
  )
}