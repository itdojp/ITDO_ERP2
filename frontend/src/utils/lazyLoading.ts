import React from 'react'

/**
 * Advanced lazy loading utilities with error boundaries and fallbacks
 */

export interface LazyLoadOptions {
  fallback?: React.ComponentType
  errorFallback?: React.ComponentType<ErrorFallbackProps>
  retryAttempts?: number
  retryDelay?: number
  preload?: boolean
  chunkName?: string
}

export interface ErrorFallbackProps {
  error: Error
  retry: () => void
  attempts: number
}

export interface LazyComponentResult<T> {
  Component: React.ComponentType<T>
  preload: () => Promise<void>
  isLoaded: () => boolean
}

// Default loading fallback
const DefaultLoadingFallback: React.FC = () => (
  <div className="flex items-center justify-center p-8">
    <div className="animate-spin rounded-full h-6 w-6 border-2 border-blue-600 border-t-transparent" />
    <span className="ml-2 text-sm text-gray-600">Loading...</span>
  </div>
)

// Default error fallback
const DefaultErrorFallback: React.FC<ErrorFallbackProps> = ({ error, retry, attempts }) => (
  <div className="flex flex-col items-center justify-center p-8 bg-red-50 border border-red-200 rounded-lg">
    <div className="text-red-600 mb-2">Failed to load component</div>
    <div className="text-sm text-red-500 mb-4">{error.message}</div>
    <button
      onClick={retry}
      className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700 text-sm"
      disabled={attempts >= 3}
    >
      {attempts >= 3 ? 'Max retries reached' : `Retry (${attempts}/3)`}
    </button>
  </div>
)

// Enhanced lazy loading with retry logic
export const createLazyComponent = <T extends React.ComponentType<any>>(
  importFunction: () => Promise<{ default: T }>,
  options: LazyLoadOptions = {}
): LazyComponentResult<React.ComponentProps<T>> => {
  const {
    fallback = DefaultLoadingFallback,
    errorFallback = DefaultErrorFallback,
    retryAttempts = 3,
    retryDelay = 1000,
    preload = false,
    chunkName
  } = options

  let componentPromise: Promise<{ default: T }> | null = null
  let isComponentLoaded = false

  // Enhanced import function with retry logic
  const enhancedImport = async (attempt = 1): Promise<{ default: T }> => {
    try {
      const module = await importFunction()
      isComponentLoaded = true
      return module
    } catch (error) {
      console.error(`Failed to load component (attempt ${attempt}):`, error)
      
      if (attempt < retryAttempts) {
        await new Promise(resolve => setTimeout(resolve, retryDelay * attempt))
        return enhancedImport(attempt + 1)
      }
      
      throw error
    }
  }

  // Create lazy component with error boundary
  const LazyComponent = React.lazy(() => {
    if (!componentPromise) {
      componentPromise = enhancedImport()
    }
    return componentPromise
  })

  // Error boundary wrapper
  class LazyErrorBoundary extends React.Component<
    { children: React.ReactNode; ErrorFallback: React.ComponentType<ErrorFallbackProps> },
    { hasError: boolean; error: Error | null; attempts: number }
  > {
    constructor(props: any) {
      super(props)
      this.state = { hasError: false, error: null, attempts: 0 }
    }

    static getDerivedStateFromError(error: Error) {
      return { hasError: true, error }
    }

    componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
      console.error('Lazy component error:', error, errorInfo)
    }

    retry = () => {
      this.setState(prev => ({
        hasError: false,
        error: null,
        attempts: prev.attempts + 1
      }))
      
      // Reset component promise to force re-import
      componentPromise = null
      isComponentLoaded = false
    }

    render() {
      if (this.state.hasError && this.state.error) {
        const ErrorFallback = this.props.ErrorFallback
        return (
          <ErrorFallback
            error={this.state.error}
            retry={this.retry}
            attempts={this.state.attempts}
          />
        )
      }

      return this.props.children
    }
  }

  // Wrapped component with suspense and error boundary
  const WrappedComponent = React.forwardRef<any, React.ComponentProps<T>>((props, ref) => (
    <LazyErrorBoundary ErrorFallback={errorFallback}>
      <React.Suspense fallback={<fallback />}>
        <LazyComponent {...props} ref={ref} />
      </React.Suspense>
    </LazyErrorBoundary>
  ))

  WrappedComponent.displayName = `Lazy(${chunkName || 'Component'})`

  // Preload function
  const preloadComponent = async (): Promise<void> => {
    if (!componentPromise) {
      componentPromise = enhancedImport()
    }
    await componentPromise
  }

  // Auto-preload if specified
  if (preload) {
    preloadComponent().catch(console.error)
  }

  return {
    Component: WrappedComponent,
    preload: preloadComponent,
    isLoaded: () => isComponentLoaded
  }
}

// Route-based lazy loading
export const createLazyRoute = <T extends React.ComponentType<any>>(
  importFunction: () => Promise<{ default: T }>,
  options: LazyLoadOptions & { routeName?: string } = {}
) => {
  const { routeName, ...lazyOptions } = options
  
  return createLazyComponent(importFunction, {
    ...lazyOptions,
    chunkName: routeName,
    fallback: options.fallback || (() => (
      <div className="flex items-center justify-center min-h-[200px]">
        <div className="animate-spin rounded-full h-8 w-8 border-2 border-blue-600 border-t-transparent" />
        <span className="ml-3 text-gray-600">Loading {routeName || 'page'}...</span>
      </div>
    ))
  })
}

// Intersection Observer based lazy loading for components
export const useIntersectionLazyLoad = <T extends React.ComponentType<any>>(
  importFunction: () => Promise<{ default: T }>,
  options: LazyLoadOptions & { threshold?: number; rootMargin?: string } = {}
) => {
  const [shouldLoad, setShouldLoad] = React.useState(false)
  const [isIntersecting, setIsIntersecting] = React.useState(false)
  const ref = React.useRef<HTMLDivElement>(null)

  const { threshold = 0.1, rootMargin = '50px', ...lazyOptions } = options

  React.useEffect(() => {
    const element = ref.current
    if (!element) return

    const observer = new IntersectionObserver(
      ([entry]) => {
        setIsIntersecting(entry.isIntersecting)
        if (entry.isIntersecting && !shouldLoad) {
          setShouldLoad(true)
        }
      },
      { threshold, rootMargin }
    )

    observer.observe(element)

    return () => observer.disconnect()
  }, [threshold, rootMargin, shouldLoad])

  const lazyComponent = React.useMemo(() => {
    if (!shouldLoad) return null
    return createLazyComponent(importFunction, lazyOptions)
  }, [shouldLoad, importFunction, lazyOptions])

  return {
    ref,
    Component: lazyComponent?.Component || null,
    shouldLoad,
    isIntersecting,
    preload: lazyComponent?.preload || (() => Promise.resolve())
  }
}

// Preloader for multiple components
export class ComponentPreloader {
  private preloadPromises = new Map<string, Promise<void>>()
  private loadedComponents = new Set<string>()

  register<T extends React.ComponentType<any>>(
    name: string,
    importFunction: () => Promise<{ default: T }>
  ) {
    if (!this.preloadPromises.has(name)) {
      this.preloadPromises.set(name, 
        importFunction()
          .then(() => {
            this.loadedComponents.add(name)
          })
          .catch(error => {
            console.error(`Failed to preload component ${name}:`, error)
            this.preloadPromises.delete(name)
          })
      )
    }
    return this.preloadPromises.get(name)!
  }

  async preload(names: string[]): Promise<void> {
    const promises = names
      .map(name => this.preloadPromises.get(name))
      .filter(Boolean) as Promise<void>[]
    
    await Promise.allSettled(promises)
  }

  async preloadAll(): Promise<void> {
    await Promise.allSettled(Array.from(this.preloadPromises.values()))
  }

  isLoaded(name: string): boolean {
    return this.loadedComponents.has(name)
  }

  getLoadedCount(): number {
    return this.loadedComponents.size
  }

  getTotalCount(): number {
    return this.preloadPromises.size
  }
}

// Global preloader instance
export const globalPreloader = new ComponentPreloader()

// Hook for component preloading
export const useComponentPreloader = () => {
  const [loadedCount, setLoadedCount] = React.useState(globalPreloader.getLoadedCount())
  const [totalCount, setTotalCount] = React.useState(globalPreloader.getTotalCount())

  React.useEffect(() => {
    const interval = setInterval(() => {
      setLoadedCount(globalPreloader.getLoadedCount())
      setTotalCount(globalPreloader.getTotalCount())
    }, 1000)

    return () => clearInterval(interval)
  }, [])

  return {
    loadedCount,
    totalCount,
    progress: totalCount > 0 ? loadedCount / totalCount : 0,
    preload: globalPreloader.preload.bind(globalPreloader),
    preloadAll: globalPreloader.preloadAll.bind(globalPreloader),
    isLoaded: globalPreloader.isLoaded.bind(globalPreloader)
  }
}

// Image lazy loading with blur placeholder
export const useLazyImage = (
  src: string, 
  options: {
    placeholder?: string
    blurDataURL?: string
    threshold?: number
    rootMargin?: string
  } = {}
) => {
  const { placeholder, blurDataURL, threshold = 0.1, rootMargin = '50px' } = options
  const [imageSrc, setImageSrc] = React.useState(placeholder || blurDataURL || '')
  const [isLoaded, setIsLoaded] = React.useState(false)
  const [isInView, setIsInView] = React.useState(false)
  const imgRef = React.useRef<HTMLImageElement>(null)

  React.useEffect(() => {
    const img = imgRef.current
    if (!img) return

    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting && !isInView) {
          setIsInView(true)
        }
      },
      { threshold, rootMargin }
    )

    observer.observe(img)
    return () => observer.disconnect()
  }, [threshold, rootMargin, isInView])

  React.useEffect(() => {
    if (!isInView || isLoaded) return

    const img = new Image()
    img.onload = () => {
      setImageSrc(src)
      setIsLoaded(true)
    }
    img.onerror = () => {
      console.error('Failed to load image:', src)
    }
    img.src = src
  }, [isInView, src, isLoaded])

  return {
    ref: imgRef,
    src: imageSrc,
    isLoaded,
    isInView
  }
}

// Dynamic module loader
export const useDynamicModule = <T = any>(
  modulePath: string,
  options: { 
    dependencies?: string[]
    enabled?: boolean 
  } = {}
) => {
  const { dependencies = [], enabled = true } = options
  const [module, setModule] = React.useState<T | null>(null)
  const [loading, setLoading] = React.useState(false)
  const [error, setError] = React.useState<Error | null>(null)

  const loadModule = React.useCallback(async () => {
    if (!enabled || loading || module) return

    setLoading(true)
    setError(null)

    try {
      const loadedModule = await import(/* @vite-ignore */ modulePath)
      setModule(loadedModule.default || loadedModule)
    } catch (err) {
      setError(err as Error)
      console.error('Failed to load module:', modulePath, err)
    } finally {
      setLoading(false)
    }
  }, [modulePath, enabled, loading, module])

  React.useEffect(() => {
    loadModule()
  }, [loadModule, ...dependencies])

  return {
    module,
    loading,
    error,
    reload: loadModule
  }
}