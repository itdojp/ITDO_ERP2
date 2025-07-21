import React from 'react'

/**
 * Performance optimization utilities for React components
 */

// Lazy loading with error boundaries
export const createLazyComponent = <T extends React.ComponentType<any>>(
  importFunction: () => Promise<{ default: T }>,
  fallback?: React.ComponentType
) => {
  const LazyComponent = React.lazy(importFunction)
  
  return React.forwardRef<any, React.ComponentProps<T>>((props, ref) => (
    <React.Suspense 
      fallback={fallback ? <fallback /> : <div>Loading...</div>}
    >
      <LazyComponent {...props} ref={ref} />
    </React.Suspense>
  ))
}

// Image lazy loading with intersection observer
export const useLazyImage = (src: string, placeholder?: string) => {
  const [imageSrc, setImageSrc] = React.useState(placeholder || '')
  const [isLoaded, setIsLoaded] = React.useState(false)
  const imgRef = React.useRef<HTMLImageElement>(null)

  React.useEffect(() => {
    const img = imgRef.current
    if (!img) return

    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setImageSrc(src)
          observer.disconnect()
        }
      },
      { threshold: 0.1 }
    )

    observer.observe(img)

    return () => observer.disconnect()
  }, [src])

  React.useEffect(() => {
    if (!imageSrc || imageSrc === placeholder) return

    const img = new Image()
    img.onload = () => setIsLoaded(true)
    img.src = imageSrc
  }, [imageSrc, placeholder])

  return {
    ref: imgRef,
    src: imageSrc,
    isLoaded
  }
}

// Debounced state hook
export const useDebouncedState = <T>(
  initialValue: T,
  delay: number = 300
): [T, T, (value: T) => void] => {
  const [value, setValue] = React.useState(initialValue)
  const [debouncedValue, setDebouncedValue] = React.useState(initialValue)

  React.useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedValue(value)
    }, delay)

    return () => clearTimeout(timer)
  }, [value, delay])

  return [value, debouncedValue, setValue]
}

// Throttled state hook
export const useThrottledState = <T>(
  initialValue: T,
  delay: number = 100
): [T, T, (value: T) => void] => {
  const [value, setValue] = React.useState(initialValue)
  const [throttledValue, setThrottledValue] = React.useState(initialValue)
  const lastExecuted = React.useRef<number>(Date.now())

  React.useEffect(() => {
    const now = Date.now()
    const timeSinceLastExecution = now - lastExecuted.current

    if (timeSinceLastExecution >= delay) {
      setThrottledValue(value)
      lastExecuted.current = now
    } else {
      const timer = setTimeout(() => {
        setThrottledValue(value)
        lastExecuted.current = Date.now()
      }, delay - timeSinceLastExecution)

      return () => clearTimeout(timer)
    }
  }, [value, delay])

  return [value, throttledValue, setValue]
}

// Batch state updates
export const useBatchedState = <T extends Record<string, any>>(
  initialState: T
): [T, (updates: Partial<T>) => void, () => void] => {
  const [state, setState] = React.useState(initialState)
  const pendingUpdates = React.useRef<Partial<T>>({})
  const timeoutRef = React.useRef<NodeJS.Timeout>()

  const batchUpdate = React.useCallback((updates: Partial<T>) => {
    Object.assign(pendingUpdates.current, updates)

    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current)
    }

    timeoutRef.current = setTimeout(() => {
      setState(prev => ({ ...prev, ...pendingUpdates.current }))
      pendingUpdates.current = {}
    }, 0)
  }, [])

  const flushUpdates = React.useCallback(() => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current)
    }
    setState(prev => ({ ...prev, ...pendingUpdates.current }))
    pendingUpdates.current = {}
  }, [])

  React.useEffect(() => {
    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current)
      }
    }
  }, [])

  return [state, batchUpdate, flushUpdates]
}

// Memoized computation with dependencies
export const useComputedValue = <T, D extends React.DependencyList>(
  compute: () => T,
  deps: D
): T => {
  return React.useMemo(compute, deps)
}

// Stable reference hook
export const useStableValue = <T>(value: T): T => {
  const ref = React.useRef(value)
  
  if (!Object.is(ref.current, value)) {
    ref.current = value
  }
  
  return ref.current
}

// Resource pooling for expensive objects
class ResourcePool<T> {
  private pool: T[] = []
  private createResource: () => T
  private resetResource?: (resource: T) => void

  constructor(
    createResource: () => T,
    resetResource?: (resource: T) => void,
    initialSize: number = 5
  ) {
    this.createResource = createResource
    this.resetResource = resetResource

    // Pre-populate pool
    for (let i = 0; i < initialSize; i++) {
      this.pool.push(createResource())
    }
  }

  acquire(): T {
    const resource = this.pool.pop()
    if (resource) {
      return resource
    }
    return this.createResource()
  }

  release(resource: T): void {
    if (this.resetResource) {
      this.resetResource(resource)
    }
    if (this.pool.length < 10) { // Max pool size
      this.pool.push(resource)
    }
  }
}

export const useResourcePool = <T>(
  createResource: () => T,
  resetResource?: (resource: T) => void,
  initialSize?: number
) => {
  const pool = React.useMemo(
    () => new ResourcePool(createResource, resetResource, initialSize),
    [createResource, resetResource, initialSize]
  )

  return React.useMemo(
    () => ({
      acquire: () => pool.acquire(),
      release: (resource: T) => pool.release(resource)
    }),
    [pool]
  )
}

// Component update scheduler
export const useScheduledUpdate = () => {
  const [, forceUpdate] = React.useReducer(x => x + 1, 0)
  const rafRef = React.useRef<number>()

  const scheduleUpdate = React.useCallback(() => {
    if (rafRef.current) {
      cancelAnimationFrame(rafRef.current)
    }
    
    rafRef.current = requestAnimationFrame(() => {
      forceUpdate()
    })
  }, [forceUpdate])

  React.useEffect(() => {
    return () => {
      if (rafRef.current) {
        cancelAnimationFrame(rafRef.current)
      }
    }
  }, [])

  return scheduleUpdate
}

// Memory usage tracker
export const useMemoryTracker = (sampleInterval: number = 5000) => {
  const [memoryInfo, setMemoryInfo] = React.useState<{
    used: number
    total: number
    percentage: number
  } | null>(null)

  React.useEffect(() => {
    if (!('memory' in performance)) return

    const updateMemoryInfo = () => {
      const memory = (performance as any).memory
      const used = memory.usedJSHeapSize / 1024 / 1024 // MB
      const total = memory.totalJSHeapSize / 1024 / 1024 // MB
      const percentage = (used / total) * 100

      setMemoryInfo({ used, total, percentage })
    }

    updateMemoryInfo()
    const interval = setInterval(updateMemoryInfo, sampleInterval)

    return () => clearInterval(interval)
  }, [sampleInterval])

  return memoryInfo
}

// Bundle size analyzer (development only)
export const analyzeBundleSize = async (chunkName?: string) => {
  if (process.env.NODE_ENV !== 'development') return null

  try {
    const response = await fetch('/stats.json')
    const stats = await response.json()
    
    if (chunkName) {
      const chunk = stats.chunks?.find((c: any) => c.names.includes(chunkName))
      return {
        size: chunk?.size || 0,
        modules: chunk?.modules?.length || 0
      }
    }
    
    return {
      totalSize: stats.chunks?.reduce((acc: number, chunk: any) => acc + chunk.size, 0) || 0,
      chunkCount: stats.chunks?.length || 0
    }
  } catch (error) {
    console.warn('Could not analyze bundle size:', error)
    return null
  }
}

// Performance timing utilities
export const performanceTiming = {
  mark: (name: string) => {
    if ('mark' in performance) {
      performance.mark(name)
    }
  },
  
  measure: (name: string, startMark: string, endMark?: string) => {
    if ('measure' in performance) {
      performance.measure(name, startMark, endMark)
    }
  },
  
  getEntries: (name?: string) => {
    if ('getEntriesByName' in performance && name) {
      return performance.getEntriesByName(name)
    }
    if ('getEntries' in performance) {
      return performance.getEntries()
    }
    return []
  },
  
  clear: (name?: string) => {
    if ('clearMarks' in performance) {
      performance.clearMarks(name)
    }
    if ('clearMeasures' in performance) {
      performance.clearMeasures(name)
    }
  }
}

// React DevTools profiler helpers
export const withProfiler = <P extends object>(
  Component: React.ComponentType<P>,
  id: string,
  onRender?: (
    id: string,
    phase: 'mount' | 'update',
    actualDuration: number,
    baseDuration: number,
    startTime: number,
    commitTime: number
  ) => void
) => {
  return React.forwardRef<any, P>((props, ref) => (
    <React.Profiler id={id} onRender={onRender}>
      <Component {...props} ref={ref} />
    </React.Profiler>
  ))
}

// Error boundary for performance monitoring
export class PerformanceErrorBoundary extends React.Component<
  { children: React.ReactNode; onError?: (error: Error, errorInfo: React.ErrorInfo) => void },
  { hasError: boolean; error?: Error }
> {
  constructor(props: any) {
    super(props)
    this.state = { hasError: false }
  }

  static getDerivedStateFromError(error: Error) {
    return { hasError: true, error }
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('Performance Error Boundary caught an error:', error, errorInfo)
    this.props.onError?.(error, errorInfo)
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="p-4 bg-red-50 border border-red-200 rounded-md">
          <h3 className="text-red-800 font-medium">Performance Error</h3>
          <p className="text-red-600 text-sm mt-2">
            A performance-related error occurred. Please refresh the page.
          </p>
          {process.env.NODE_ENV === 'development' && this.state.error && (
            <pre className="text-xs text-red-500 mt-2 overflow-auto">
              {this.state.error.stack}
            </pre>
          )}
        </div>
      )
    }

    return this.props.children
  }
}