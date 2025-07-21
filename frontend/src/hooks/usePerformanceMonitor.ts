import React from 'react'

export interface PerformanceMetrics {
  renderTime: number
  renderCount: number
  lastRenderTime: number
  averageRenderTime: number
  isSlowRender: boolean
  memoryUsage?: number
  componentName?: string
}

export interface UsePerformanceMonitorOptions {
  threshold?: number
  trackMemory?: boolean
  componentName?: string
  onSlowRender?: (metrics: PerformanceMetrics) => void
  enabled?: boolean
}

export interface UsePerformanceMonitorReturn {
  metrics: PerformanceMetrics
  markRenderStart: () => void
  markRenderEnd: () => void
  reset: () => void
  getReport: () => string
}

const DEFAULT_THRESHOLD = 16 // 16ms for 60fps

export const usePerformanceMonitor = (
  options: UsePerformanceMonitorOptions = {}
): UsePerformanceMonitorReturn => {
  const {
    threshold = DEFAULT_THRESHOLD,
    trackMemory = false,
    componentName = 'Unknown',
    onSlowRender,
    enabled = process.env.NODE_ENV === 'development'
  } = options

  const renderStartTime = React.useRef<number>(0)
  const renderTimes = React.useRef<number[]>([])
  const renderCountRef = React.useRef<number>(0)

  const [metrics, setMetrics] = React.useState<PerformanceMetrics>({
    renderTime: 0,
    renderCount: 0,
    lastRenderTime: 0,
    averageRenderTime: 0,
    isSlowRender: false,
    componentName
  })

  const getMemoryUsage = React.useCallback((): number | undefined => {
    if (!trackMemory || !enabled) return undefined
    
    if ('memory' in performance) {
      const memory = (performance as any).memory
      return memory.usedJSHeapSize / 1024 / 1024 // Convert to MB
    }
    
    return undefined
  }, [trackMemory, enabled])

  const markRenderStart = React.useCallback(() => {
    if (!enabled) return
    renderStartTime.current = performance.now()
  }, [enabled])

  const markRenderEnd = React.useCallback(() => {
    if (!enabled || renderStartTime.current === 0) return

    const endTime = performance.now()
    const renderTime = endTime - renderStartTime.current
    
    renderTimes.current.push(renderTime)
    renderCountRef.current += 1

    // Keep only last 100 render times for average calculation
    if (renderTimes.current.length > 100) {
      renderTimes.current = renderTimes.current.slice(-100)
    }

    const averageRenderTime = renderTimes.current.reduce((a, b) => a + b, 0) / renderTimes.current.length
    const isSlowRender = renderTime > threshold
    const memoryUsage = getMemoryUsage()

    const newMetrics: PerformanceMetrics = {
      renderTime,
      renderCount: renderCountRef.current,
      lastRenderTime: renderTime,
      averageRenderTime,
      isSlowRender,
      memoryUsage,
      componentName
    }

    setMetrics(newMetrics)

    if (isSlowRender && onSlowRender) {
      onSlowRender(newMetrics)
    }

    renderStartTime.current = 0
  }, [enabled, threshold, componentName, onSlowRender, getMemoryUsage])

  const reset = React.useCallback(() => {
    renderTimes.current = []
    renderCountRef.current = 0
    setMetrics({
      renderTime: 0,
      renderCount: 0,
      lastRenderTime: 0,
      averageRenderTime: 0,
      isSlowRender: false,
      componentName
    })
  }, [componentName])

  const getReport = React.useCallback((): string => {
    const { renderCount, averageRenderTime, lastRenderTime, memoryUsage } = metrics
    
    let report = `Performance Report for ${componentName}:\n`
    report += `- Total Renders: ${renderCount}\n`
    report += `- Average Render Time: ${averageRenderTime.toFixed(2)}ms\n`
    report += `- Last Render Time: ${lastRenderTime.toFixed(2)}ms\n`
    report += `- Slow Renders: ${renderTimes.current.filter(time => time > threshold).length}\n`
    
    if (memoryUsage !== undefined) {
      report += `- Memory Usage: ${memoryUsage.toFixed(2)}MB\n`
    }
    
    return report
  }, [metrics, componentName, threshold])

  // Auto-mark render start on each render
  React.useEffect(() => {
    markRenderStart()
  })

  // Mark render end after DOM update
  React.useLayoutEffect(() => {
    markRenderEnd()
  })

  return {
    metrics,
    markRenderStart,
    markRenderEnd,
    reset,
    getReport
  }
}

export const withPerformanceMonitor = <P extends object>(
  Component: React.ComponentType<P>,
  options?: UsePerformanceMonitorOptions
) => {
  const WrappedComponent = React.memo((props: P) => {
    const { metrics } = usePerformanceMonitor({
      ...options,
      componentName: options?.componentName || Component.displayName || Component.name
    })

    if (process.env.NODE_ENV === 'development' && metrics.isSlowRender) {
      console.warn(`Slow render detected in ${Component.displayName || Component.name}: ${metrics.lastRenderTime.toFixed(2)}ms`)
    }

    return <Component {...props} />
  })

  WrappedComponent.displayName = `withPerformanceMonitor(${Component.displayName || Component.name})`
  
  return WrappedComponent
}