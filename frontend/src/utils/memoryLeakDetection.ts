/**
 * Memory Leak Detection and Prevention Utilities for React Applications
 */

export interface MemoryStats {
  usedJSHeapSize: number
  totalJSHeapSize: number
  jsHeapSizeLimit: number
  timestamp: number
  url: string
  userAgent: string
}

export interface ComponentMemoryProfile {
  componentName: string
  mountTime: number
  unmountTime?: number
  initialMemory: number
  finalMemory?: number
  memoryDelta?: number
  isLeak: boolean
  leakSeverity?: 'low' | 'medium' | 'high'
}

export interface MemoryLeakDetectionOptions {
  enabled?: boolean
  sampleInterval?: number
  leakThreshold?: number
  maxSamples?: number
  autoCleanup?: boolean
  reportCallback?: (leak: MemoryLeak) => void
}

export interface MemoryLeak {
  componentName: string
  leakSize: number
  severity: 'low' | 'medium' | 'high'
  timestamp: number
  stackTrace?: string
  recommendations: string[]
}

// Global memory monitoring state
class MemoryLeakDetector {
  private samples: MemoryStats[] = []
  private componentProfiles = new Map<string, ComponentMemoryProfile>()
  private intervalId: number | null = null
  private options: Required<MemoryLeakDetectionOptions>
  private isSupported: boolean

  constructor(options: MemoryLeakDetectionOptions = {}) {
    this.options = {
      enabled: options.enabled ?? process.env.NODE_ENV === 'development',
      sampleInterval: options.sampleInterval ?? 5000,
      leakThreshold: options.leakThreshold ?? 5 * 1024 * 1024, // 5MB
      maxSamples: options.maxSamples ?? 100,
      autoCleanup: options.autoCleanup ?? true,
      reportCallback: options.reportCallback ?? this.defaultReportCallback
    }

    this.isSupported = this.checkSupport()
    
    if (this.options.enabled && this.isSupported) {
      this.startMonitoring()
    }
  }

  private checkSupport(): boolean {
    return typeof window !== 'undefined' && 
           'performance' in window && 
           'memory' in (window.performance as any)
  }

  private defaultReportCallback = (leak: MemoryLeak) => {
    console.warn('Memory leak detected:', leak)
    
    if (leak.severity === 'high') {
      console.error('=¨ HIGH SEVERITY memory leak detected:', {
        component: leak.componentName,
        size: this.formatBytes(leak.leakSize),
        recommendations: leak.recommendations
      })
    }
  }

  private getCurrentMemoryStats(): MemoryStats | null {
    if (!this.isSupported) return null

    const memory = (performance as any).memory
    return {
      usedJSHeapSize: memory.usedJSHeapSize,
      totalJSHeapSize: memory.totalJSHeapSize,
      jsHeapSizeLimit: memory.jsHeapSizeLimit,
      timestamp: Date.now(),
      url: window.location.href,
      userAgent: navigator.userAgent
    }
  }

  private startMonitoring() {
    this.intervalId = window.setInterval(() => {
      const stats = this.getCurrentMemoryStats()
      if (stats) {
        this.addSample(stats)
        this.analyzeMemoryTrends()
      }
    }, this.options.sampleInterval)
  }

  private addSample(stats: MemoryStats) {
    this.samples.push(stats)
    
    if (this.samples.length > this.options.maxSamples) {
      this.samples.shift()
    }
  }

  private analyzeMemoryTrends() {
    if (this.samples.length < 10) return

    const recentSamples = this.samples.slice(-10)
    const growthTrend = this.calculateGrowthTrend(recentSamples)
    
    if (growthTrend > this.options.leakThreshold / 10) { // 10% of threshold
      this.detectPotentialLeaks()
    }
  }

  private calculateGrowthTrend(samples: MemoryStats[]): number {
    if (samples.length < 2) return 0
    
    const first = samples[0]
    const last = samples[samples.length - 1]
    
    return last.usedJSHeapSize - first.usedJSHeapSize
  }

  private detectPotentialLeaks() {
    for (const [componentName, profile] of this.componentProfiles) {
      if (profile.memoryDelta && profile.memoryDelta > this.options.leakThreshold) {
        const leak: MemoryLeak = {
          componentName,
          leakSize: profile.memoryDelta,
          severity: this.calculateSeverity(profile.memoryDelta),
          timestamp: Date.now(),
          stackTrace: this.getCurrentStackTrace(),
          recommendations: this.generateRecommendations(componentName, profile)
        }
        
        this.options.reportCallback(leak)
        profile.isLeak = true
        profile.leakSeverity = leak.severity
      }
    }
  }

  private calculateSeverity(leakSize: number): 'low' | 'medium' | 'high' {
    const threshold = this.options.leakThreshold
    if (leakSize > threshold * 3) return 'high'
    if (leakSize > threshold * 1.5) return 'medium'
    return 'low'
  }

  private getCurrentStackTrace(): string {
    try {
      throw new Error()
    } catch (e) {
      return (e as Error).stack || 'Stack trace not available'
    }
  }

  private generateRecommendations(componentName: string, profile: ComponentMemoryProfile): string[] {
    const recommendations: string[] = []
    
    recommendations.push('Check for unremoved event listeners in useEffect cleanup')
    recommendations.push('Verify all subscriptions are properly unsubscribed')
    recommendations.push('Clear intervals and timeouts in component cleanup')
    recommendations.push('Remove DOM references that prevent garbage collection')
    
    if (profile.memoryDelta && profile.memoryDelta > 10 * 1024 * 1024) {
      recommendations.push('Consider implementing component virtualization')
      recommendations.push('Reduce component state size and complexity')
    }
    
    return recommendations
  }

  public startComponentProfile(componentName: string): void {
    if (!this.options.enabled || !this.isSupported) return

    const currentMemory = this.getCurrentMemoryStats()
    if (currentMemory) {
      this.componentProfiles.set(componentName, {
        componentName,
        mountTime: Date.now(),
        initialMemory: currentMemory.usedJSHeapSize,
        isLeak: false
      })
    }
  }

  public endComponentProfile(componentName: string): ComponentMemoryProfile | null {
    if (!this.options.enabled || !this.isSupported) return null

    const profile = this.componentProfiles.get(componentName)
    if (!profile) return null

    const currentMemory = this.getCurrentMemoryStats()
    if (currentMemory) {
      profile.unmountTime = Date.now()
      profile.finalMemory = currentMemory.usedJSHeapSize
      profile.memoryDelta = profile.finalMemory - profile.initialMemory
      
      // Auto cleanup old profiles
      if (this.options.autoCleanup) {
        setTimeout(() => {
          this.componentProfiles.delete(componentName)
        }, 60000) // Keep for 1 minute
      }
    }

    return profile
  }

  public getMemoryReport(): {
    currentStats: MemoryStats | null
    samples: MemoryStats[]
    componentProfiles: ComponentMemoryProfile[]
    leaks: ComponentMemoryProfile[]
  } {
    return {
      currentStats: this.getCurrentMemoryStats(),
      samples: [...this.samples],
      componentProfiles: Array.from(this.componentProfiles.values()),
      leaks: Array.from(this.componentProfiles.values()).filter(p => p.isLeak)
    }
  }

  public forceGarbageCollection(): void {
    if ('gc' in window && typeof (window as any).gc === 'function') {
      (window as any).gc()
    } else {
      console.warn('Garbage collection not available. Enable --expose-gc flag in development.')
    }
  }

  public stop(): void {
    if (this.intervalId) {
      clearInterval(this.intervalId)
      this.intervalId = null
    }
  }

  private formatBytes(bytes: number): string {
    if (bytes === 0) return '0 B'
    const k = 1024
    const sizes = ['B', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return `${parseFloat((bytes / Math.pow(k, i)).toFixed(2))} ${sizes[i]}`
  }
}

// Global detector instance
export const memoryLeakDetector = new MemoryLeakDetector()

// React hooks for memory leak detection
export const useMemoryLeakDetection = (componentName: string) => {
  React.useEffect(() => {
    memoryLeakDetector.startComponentProfile(componentName)
    
    return () => {
      memoryLeakDetector.endComponentProfile(componentName)
    }
  }, [componentName])
}

// HOC for automatic memory leak detection
export const withMemoryLeakDetection = <P extends object>(
  Component: React.ComponentType<P>,
  componentName?: string
) => {
  const WrappedComponent = React.forwardRef<any, P>((props, ref) => {
    const name = componentName || Component.displayName || Component.name || 'Unknown'
    useMemoryLeakDetection(name)
    
    return <Component {...props} ref={ref} />
  })
  
  WrappedComponent.displayName = `withMemoryLeakDetection(${Component.displayName || Component.name})`
  
  return WrappedComponent
}

// Hook for memory monitoring in development
export const useMemoryMonitor = (options: { interval?: number; enabled?: boolean } = {}) => {
  const { interval = 5000, enabled = process.env.NODE_ENV === 'development' } = options
  const [memoryStats, setMemoryStats] = React.useState<MemoryStats | null>(null)
  const [trend, setTrend] = React.useState<'increasing' | 'decreasing' | 'stable'>('stable')
  
  React.useEffect(() => {
    if (!enabled) return
    
    const updateStats = () => {
      const stats = memoryLeakDetector.getCurrentMemoryStats()
      if (stats) {
        setMemoryStats(prevStats => {
          if (prevStats) {
            const delta = stats.usedJSHeapSize - prevStats.usedJSHeapSize
            if (delta > 1024 * 1024) setTrend('increasing') // 1MB increase
            else if (delta < -1024 * 1024) setTrend('decreasing') // 1MB decrease
            else setTrend('stable')
          }
          return stats
        })
      }
    }
    
    updateStats()
    const intervalId = setInterval(updateStats, interval)
    
    return () => clearInterval(intervalId)
  }, [interval, enabled])
  
  return {
    memoryStats,
    trend,
    formatBytes: (bytes: number) => memoryLeakDetector['formatBytes'](bytes),
    forceGC: () => memoryLeakDetector.forceGarbageCollection()
  }
}

// Memory-aware state hook
export const useMemoryAwareState = <T>(
  initialState: T,
  maxSize?: number
): [T, React.Dispatch<React.SetStateAction<T>>] => {
  const [state, setState] = React.useState(initialState)
  const stateRef = React.useRef(state)
  
  React.useEffect(() => {
    stateRef.current = state
  }, [state])
  
  const memoryAwareSetState = React.useCallback((newState: React.SetStateAction<T>) => {
    if (maxSize && typeof newState === 'object') {
      const serialized = JSON.stringify(newState)
      if (serialized.length > maxSize) {
        console.warn(`State size (${serialized.length} chars) exceeds maxSize (${maxSize} chars)`)
      }
    }
    
    setState(newState)
  }, [maxSize])
  
  // Cleanup on unmount
  React.useEffect(() => {
    return () => {
      // Clear references to help GC
      stateRef.current = initialState
    }
  }, [initialState])
  
  return [state, memoryAwareSetState]
}

// WeakMap-based cache to prevent memory leaks
export class WeakCache<K extends object, V> {
  private cache = new WeakMap<K, V>()
  
  get(key: K): V | undefined {
    return this.cache.get(key)
  }
  
  set(key: K, value: V): void {
    this.cache.set(key, value)
  }
  
  has(key: K): boolean {
    return this.cache.has(key)
  }
  
  delete(key: K): boolean {
    return this.cache.delete(key)
  }
}

// Memory-safe event listener hook
export const useMemorySafeEventListener = <K extends keyof WindowEventMap>(
  eventName: K,
  handler: (event: WindowEventMap[K]) => void,
  options?: AddEventListenerOptions
) => {
  const handlerRef = React.useRef(handler)
  
  React.useEffect(() => {
    handlerRef.current = handler
  }, [handler])
  
  React.useEffect(() => {
    const eventHandler = (event: WindowEventMap[K]) => handlerRef.current(event)
    
    window.addEventListener(eventName, eventHandler, options)
    
    return () => {
      window.removeEventListener(eventName, eventHandler, options)
    }
  }, [eventName, options])
}

// Timer management to prevent leaks
export class TimerManager {
  private timers = new Set<number>()
  
  setTimeout(callback: () => void, delay: number): number {
    const id = window.setTimeout(() => {
      this.timers.delete(id)
      callback()
    }, delay)
    
    this.timers.add(id)
    return id
  }
  
  setInterval(callback: () => void, delay: number): number {
    const id = window.setInterval(callback, delay)
    this.timers.add(id)
    return id
  }
  
  clearTimeout(id: number): void {
    window.clearTimeout(id)
    this.timers.delete(id)
  }
  
  clearInterval(id: number): void {
    window.clearInterval(id)
    this.timers.delete(id)
  }
  
  clearAll(): void {
    this.timers.forEach(id => {
      window.clearTimeout(id)
      window.clearInterval(id)
    })
    this.timers.clear()
  }
}

// Hook for timer management
export const useTimerManager = () => {
  const timerManager = React.useRef(new TimerManager())
  
  React.useEffect(() => {
    return () => {
      timerManager.current.clearAll()
    }
  }, [])
  
  return timerManager.current
}