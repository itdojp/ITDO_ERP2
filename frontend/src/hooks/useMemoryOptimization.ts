import React from 'react'
import { 
  memoryLeakDetector, 
  useMemoryLeakDetection, 
  useMemoryMonitor,
  WeakCache,
  TimerManager
} from '../utils/memoryLeakDetection'

/**
 * Memory optimization hooks for React components
 */

// Enhanced useCallback that automatically cleans up on unmount
export const useMemoryOptimizedCallback = <T extends (...args: any[]) => any>(
  callback: T,
  deps: React.DependencyList
): T => {
  const callbackRef = React.useRef(callback)
  const cleanupRef = React.useRef<(() => void) | null>(null)

  React.useEffect(() => {
    callbackRef.current = callback
  }, [callback])

  const memoizedCallback = React.useCallback((...args: Parameters<T>) => {
    return callbackRef.current(...args)
  }, deps) as T

  React.useEffect(() => {
    return () => {
      // Clear the callback reference to help GC
      callbackRef.current = null as any
      if (cleanupRef.current) {
        cleanupRef.current()
        cleanupRef.current = null
      }
    }
  }, [])

  return memoizedCallback
}

// Memory-optimized state that automatically cleans up large objects
export const useMemoryOptimizedState = <T>(
  initialState: T,
  options: {
    maxItems?: number
    maxSize?: number
    autoCleanup?: boolean
    cleanupDelay?: number
  } = {}
): [T, React.Dispatch<React.SetStateAction<T>>, () => void] => {
  const {
    maxItems = 1000,
    maxSize = 10 * 1024 * 1024, // 10MB
    autoCleanup = true,
    cleanupDelay = 30000 // 30 seconds
  } = options

  const [state, setState] = React.useState(initialState)
  const cleanupTimeoutRef = React.useRef<number>()
  const stateHistoryRef = React.useRef<T[]>([])

  const cleanup = React.useCallback(() => {
    // Clear state history
    stateHistoryRef.current = []
    
    // Force garbage collection if available
    if ('gc' in window && typeof (window as any).gc === 'function') {
      (window as any).gc()
    }
  }, [])

  const optimizedSetState = React.useCallback((newState: React.SetStateAction<T>) => {
    setState(prevState => {
      const nextState = typeof newState === 'function' 
        ? (newState as (prev: T) => T)(prevState)
        : newState

      // Track state changes for cleanup
      stateHistoryRef.current.push(prevState)
      
      // Cleanup old history
      if (stateHistoryRef.current.length > maxItems) {
        stateHistoryRef.current = stateHistoryRef.current.slice(-maxItems / 2)
      }

      // Check size if it's an object/array
      if (typeof nextState === 'object' && nextState !== null) {
        try {
          const size = JSON.stringify(nextState).length
          if (size > maxSize) {
            console.warn(`State size (${size} bytes) exceeds maxSize (${maxSize} bytes)`)
          }
        } catch (e) {
          // Ignore circular reference errors
        }
      }

      // Schedule cleanup
      if (autoCleanup) {
        if (cleanupTimeoutRef.current) {
          clearTimeout(cleanupTimeoutRef.current)
        }
        cleanupTimeoutRef.current = window.setTimeout(cleanup, cleanupDelay)
      }

      return nextState
    })
  }, [maxItems, maxSize, autoCleanup, cleanupDelay, cleanup])

  React.useEffect(() => {
    return () => {
      if (cleanupTimeoutRef.current) {
        clearTimeout(cleanupTimeoutRef.current)
      }
      cleanup()
    }
  }, [cleanup])

  return [state, optimizedSetState, cleanup]
}

// Optimized effect hook that properly cleans up
export const useMemoryOptimizedEffect = (
  effect: React.EffectCallback,
  deps?: React.DependencyList,
  componentName?: string
) => {
  const cleanupFnsRef = React.useRef<(() => void)[]>([])
  
  React.useEffect(() => {
    if (componentName) {
      useMemoryLeakDetection(componentName)
    }

    const cleanup = effect()
    
    if (cleanup) {
      cleanupFnsRef.current.push(cleanup)
    }

    return () => {
      // Run all cleanup functions
      cleanupFnsRef.current.forEach(fn => {
        try {
          fn()
        } catch (error) {
          console.error('Error during effect cleanup:', error)
        }
      })
      cleanupFnsRef.current = []
    }
  }, deps)

  React.useEffect(() => {
    return () => {
      // Final cleanup on unmount
      cleanupFnsRef.current.forEach(fn => {
        try {
          fn()
        } catch (error) {
          console.error('Error during final cleanup:', error)
        }
      })
    }
  }, [])
}

// Cache hook with automatic memory management
export const useMemoryOptimizedCache = <K extends object, V>(
  options: {
    maxSize?: number
    ttl?: number // Time to live in milliseconds
    onEvict?: (key: K, value: V) => void
  } = {}
) => {
  const { maxSize = 100, ttl = 5 * 60 * 1000, onEvict } = options // 5 minutes default TTL
  
  const cache = React.useRef(new WeakCache<K, V>())
  const lruKeys = React.useRef<K[]>([])
  const timeMap = React.useRef(new WeakMap<K, number>())
  const cleanupInterval = React.useRef<number>()

  const cleanup = React.useCallback(() => {
    const now = Date.now()
    const keysToRemove: K[] = []

    lruKeys.current.forEach(key => {
      const timestamp = timeMap.current.get(key)
      if (timestamp && (now - timestamp) > ttl) {
        keysToRemove.push(key)
      }
    })

    keysToRemove.forEach(key => {
      const value = cache.current.get(key)
      if (value && onEvict) {
        onEvict(key, value)
      }
      cache.current.delete(key)
      timeMap.current.delete(key)
    })

    lruKeys.current = lruKeys.current.filter(key => !keysToRemove.includes(key))
  }, [ttl, onEvict])

  React.useEffect(() => {
    cleanupInterval.current = window.setInterval(cleanup, ttl / 4) // Cleanup every quarter of TTL
    
    return () => {
      if (cleanupInterval.current) {
        clearInterval(cleanupInterval.current)
      }
      cleanup()
    }
  }, [cleanup, ttl])

  const get = React.useCallback((key: K): V | undefined => {
    const value = cache.current.get(key)
    if (value) {
      // Update access time
      timeMap.current.set(key, Date.now())
      
      // Move to end of LRU
      const index = lruKeys.current.indexOf(key)
      if (index > -1) {
        lruKeys.current.splice(index, 1)
      }
      lruKeys.current.push(key)
    }
    return value
  }, [])

  const set = React.useCallback((key: K, value: V): void => {
    // Remove oldest if at max size
    if (lruKeys.current.length >= maxSize) {
      const oldestKey = lruKeys.current.shift()
      if (oldestKey) {
        const oldValue = cache.current.get(oldestKey)
        if (oldValue && onEvict) {
          onEvict(oldestKey, oldValue)
        }
        cache.current.delete(oldestKey)
        timeMap.current.delete(oldestKey)
      }
    }

    cache.current.set(key, value)
    timeMap.current.set(key, Date.now())
    lruKeys.current.push(key)
  }, [maxSize, onEvict])

  const has = React.useCallback((key: K): boolean => {
    return cache.current.has(key)
  }, [])

  const remove = React.useCallback((key: K): void => {
    const value = cache.current.get(key)
    if (value && onEvict) {
      onEvict(key, value)
    }
    cache.current.delete(key)
    timeMap.current.delete(key)
    
    const index = lruKeys.current.indexOf(key)
    if (index > -1) {
      lruKeys.current.splice(index, 1)
    }
  }, [onEvict])

  const clear = React.useCallback(() => {
    lruKeys.current.forEach(key => {
      const value = cache.current.get(key)
      if (value && onEvict) {
        onEvict(key, value)
      }
    })
    
    // Note: WeakMap/WeakSet clear themselves when references are lost
    lruKeys.current = []
  }, [onEvict])

  return {
    get,
    set,
    has,
    remove,
    clear,
    size: lruKeys.current.length
  }
}

// Optimized ref hook that prevents memory leaks
export const useMemoryOptimizedRef = <T>(initialValue: T) => {
  const ref = React.useRef<T>(initialValue)
  
  React.useEffect(() => {
    return () => {
      // Clear ref on unmount to help GC
      ref.current = null as any
    }
  }, [])
  
  return ref
}

// Timer management hook with automatic cleanup
export const useMemoryOptimizedTimer = () => {
  const timerManager = React.useRef(new TimerManager())
  
  React.useEffect(() => {
    return () => {
      timerManager.current.clearAll()
    }
  }, [])
  
  return {
    setTimeout: (callback: () => void, delay: number) => 
      timerManager.current.setTimeout(callback, delay),
    setInterval: (callback: () => void, delay: number) => 
      timerManager.current.setInterval(callback, delay),
    clearTimeout: (id: number) => 
      timerManager.current.clearTimeout(id),
    clearInterval: (id: number) => 
      timerManager.current.clearInterval(id),
    clearAll: () => 
      timerManager.current.clearAll()
  }
}

// Event listener hook with memory optimization
export const useMemoryOptimizedEventListener = <K extends keyof WindowEventMap>(
  eventName: K,
  handler: (event: WindowEventMap[K]) => void,
  options?: AddEventListenerOptions & { throttle?: number; debounce?: number }
) => {
  const { throttle, debounce, ...listenerOptions } = options || {}
  const handlerRef = React.useRef(handler)
  const lastCall = React.useRef<number>(0)
  const timeoutRef = React.useRef<number>()

  React.useEffect(() => {
    handlerRef.current = handler
  }, [handler])

  React.useEffect(() => {
    let eventHandler = (event: WindowEventMap[K]) => handlerRef.current(event)

    // Apply throttling
    if (throttle) {
      eventHandler = (event: WindowEventMap[K]) => {
        const now = Date.now()
        if (now - lastCall.current >= throttle) {
          lastCall.current = now
          handlerRef.current(event)
        }
      }
    }

    // Apply debouncing
    if (debounce) {
      eventHandler = (event: WindowEventMap[K]) => {
        if (timeoutRef.current) {
          clearTimeout(timeoutRef.current)
        }
        timeoutRef.current = window.setTimeout(() => {
          handlerRef.current(event)
        }, debounce)
      }
    }

    window.addEventListener(eventName, eventHandler, listenerOptions)

    return () => {
      window.removeEventListener(eventName, eventHandler, listenerOptions)
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current)
      }
    }
  }, [eventName, throttle, debounce, listenerOptions])
}

// Intersection observer hook with memory optimization
export const useMemoryOptimizedIntersectionObserver = (
  options?: IntersectionObserverInit
) => {
  const observer = React.useRef<IntersectionObserver>()
  const elementsMap = React.useRef(new WeakMap<Element, (entry: IntersectionObserverEntry) => void>())

  React.useEffect(() => {
    observer.current = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        const callback = elementsMap.current.get(entry.target)
        if (callback) {
          callback(entry)
        }
      })
    }, options)

    return () => {
      if (observer.current) {
        observer.current.disconnect()
      }
    }
  }, [options])

  const observe = React.useCallback((
    element: Element, 
    callback: (entry: IntersectionObserverEntry) => void
  ) => {
    if (observer.current) {
      elementsMap.current.set(element, callback)
      observer.current.observe(element)
    }
  }, [])

  const unobserve = React.useCallback((element: Element) => {
    if (observer.current) {
      observer.current.unobserve(element)
      elementsMap.current.delete(element)
    }
  }, [])

  return { observe, unobserve }
}

// Memory usage monitoring hook
export const useMemoryUsage = (componentName?: string) => {
  const { memoryStats, trend, formatBytes, forceGC } = useMemoryMonitor({
    enabled: process.env.NODE_ENV === 'development'
  })

  React.useEffect(() => {
    if (componentName) {
      memoryLeakDetector.startComponentProfile(componentName)
      
      return () => {
        memoryLeakDetector.endComponentProfile(componentName)
      }
    }
  }, [componentName])

  return {
    memoryStats,
    trend,
    formatBytes,
    forceGC,
    getReport: () => memoryLeakDetector.getMemoryReport()
  }
}

// Cleanup manager hook
export const useCleanupManager = () => {
  const cleanupFunctions = React.useRef<Array<() => void>>([])

  const addCleanup = React.useCallback((cleanup: () => void) => {
    cleanupFunctions.current.push(cleanup)
  }, [])

  const runCleanup = React.useCallback(() => {
    cleanupFunctions.current.forEach(fn => {
      try {
        fn()
      } catch (error) {
        console.error('Error during cleanup:', error)
      }
    })
    cleanupFunctions.current = []
  }, [])

  React.useEffect(() => {
    return runCleanup
  }, [runCleanup])

  return { addCleanup, runCleanup }
}