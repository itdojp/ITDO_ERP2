import React from 'react'

/**
 * Enhanced useCallback with deep comparison and stable references
 * Useful for complex dependency arrays and objects
 */
export const useMemoizedCallback = <T extends (...args: any[]) => any>(
  callback: T,
  deps: React.DependencyList
): T => {
  const ref = React.useRef<T>()
  const depsRef = React.useRef<React.DependencyList>()

  // Deep comparison for dependencies
  const depsChanged = !depsRef.current || !shallowEqual(depsRef.current, deps)

  if (depsChanged) {
    ref.current = callback
    depsRef.current = deps
  }

  return React.useCallback((...args: Parameters<T>) => {
    return ref.current!(...args)
  }, [depsChanged]) as T
}

/**
 * Stable callback that doesn't change between renders
 * Useful for event handlers that don't need to capture fresh values
 */
export const useStableCallback = <T extends (...args: any[]) => any>(
  callback: T
): T => {
  const callbackRef = React.useRef(callback)

  React.useLayoutEffect(() => {
    callbackRef.current = callback
  })

  return React.useCallback((...args: Parameters<T>) => {
    return callbackRef.current(...args)
  }, []) as T
}

/**
 * Memoized callback with automatic cleanup
 * Cancels the callback if component unmounts or dependencies change
 */
export const useCancellableCallback = <T extends (...args: any[]) => any>(
  callback: T,
  deps: React.DependencyList
): [T, () => void] => {
  const cancelRef = React.useRef<boolean>(false)
  const timeoutRef = React.useRef<NodeJS.Timeout>()

  const cancel = React.useCallback(() => {
    cancelRef.current = true
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current)
    }
  }, [])

  const memoizedCallback = React.useCallback((...args: Parameters<T>) => {
    if (cancelRef.current) return

    const result = callback(...args)

    // Handle async functions
    if (result && typeof result.then === 'function') {
      return result.catch((error: Error) => {
        if (!cancelRef.current) {
          throw error
        }
      })
    }

    return result
  }, deps) as T

  React.useEffect(() => {
    cancelRef.current = false
    return cancel
  }, deps)

  React.useEffect(() => {
    return cancel
  }, [])

  return [memoizedCallback, cancel]
}

/**
 * Debounced callback with memoization
 */
export const useDebouncedCallback = <T extends (...args: any[]) => any>(
  callback: T,
  delay: number,
  deps: React.DependencyList = []
): T => {
  const timeoutRef = React.useRef<NodeJS.Timeout>()
  
  const debouncedCallback = React.useCallback((...args: Parameters<T>) => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current)
    }

    timeoutRef.current = setTimeout(() => {
      callback(...args)
    }, delay)
  }, [callback, delay, ...deps]) as T

  React.useEffect(() => {
    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current)
      }
    }
  }, [])

  return debouncedCallback
}

/**
 * Throttled callback with memoization
 */
export const useThrottledCallback = <T extends (...args: any[]) => any>(
  callback: T,
  delay: number,
  deps: React.DependencyList = []
): T => {
  const timeoutRef = React.useRef<NodeJS.Timeout>()
  const lastExecRef = React.useRef<number>(0)
  
  const throttledCallback = React.useCallback((...args: Parameters<T>) => {
    const now = Date.now()

    if (now - lastExecRef.current >= delay) {
      lastExecRef.current = now
      callback(...args)
    } else if (!timeoutRef.current) {
      timeoutRef.current = setTimeout(() => {
        lastExecRef.current = Date.now()
        callback(...args)
        timeoutRef.current = undefined
      }, delay - (now - lastExecRef.current))
    }
  }, [callback, delay, ...deps]) as T

  React.useEffect(() => {
    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current)
      }
    }
  }, [])

  return throttledCallback
}

/**
 * Callback with retry mechanism
 */
export const useRetryCallback = <T extends (...args: any[]) => any>(
  callback: T,
  maxRetries: number = 3,
  delay: number = 1000,
  deps: React.DependencyList = []
): T => {
  const retryCallback = React.useCallback(async (...args: Parameters<T>) => {
    let lastError: Error | null = null
    
    for (let attempt = 0; attempt <= maxRetries; attempt++) {
      try {
        return await callback(...args)
      } catch (error) {
        lastError = error as Error
        
        if (attempt < maxRetries) {
          await new Promise(resolve => setTimeout(resolve, delay * Math.pow(2, attempt)))
        }
      }
    }
    
    throw lastError
  }, [callback, maxRetries, delay, ...deps]) as T

  return retryCallback
}

/**
 * Callback that batches multiple calls
 */
export const useBatchedCallback = <T extends (...args: any[]) => any>(
  callback: (batchedArgs: Parameters<T>[]) => void,
  batchSize: number = 10,
  flushInterval: number = 100,
  deps: React.DependencyList = []
): T => {
  const batchRef = React.useRef<Parameters<T>[]>([])
  const timeoutRef = React.useRef<NodeJS.Timeout>()

  const flush = React.useCallback(() => {
    if (batchRef.current.length > 0) {
      callback([...batchRef.current])
      batchRef.current = []
    }
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current)
      timeoutRef.current = undefined
    }
  }, [callback])

  const batchedCallback = React.useCallback((...args: Parameters<T>) => {
    batchRef.current.push(args)

    if (batchRef.current.length >= batchSize) {
      flush()
    } else if (!timeoutRef.current) {
      timeoutRef.current = setTimeout(flush, flushInterval)
    }
  }, [flush, batchSize, flushInterval, ...deps]) as T

  React.useEffect(() => {
    return () => {
      flush()
    }
  }, [flush])

  return batchedCallback
}

// Utility function for shallow comparison
function shallowEqual(a: React.DependencyList, b: React.DependencyList): boolean {
  if (a.length !== b.length) return false
  
  for (let i = 0; i < a.length; i++) {
    if (Object.is(a[i], b[i]) === false) return false
  }
  
  return true
}

// Utility function for deep comparison (limited depth)
function deepEqual(a: any, b: any, depth: number = 5): boolean {
  if (depth <= 0) return Object.is(a, b)
  
  if (Object.is(a, b)) return true
  
  if (a === null || b === null) return false
  if (typeof a !== typeof b) return false
  
  if (typeof a === 'object') {
    const keysA = Object.keys(a)
    const keysB = Object.keys(b)
    
    if (keysA.length !== keysB.length) return false
    
    for (const key of keysA) {
      if (!keysB.includes(key)) return false
      if (!deepEqual(a[key], b[key], depth - 1)) return false
    }
    
    return true
  }
  
  return false
}

/**
 * Deep memoized callback with configurable comparison depth
 */
export const useDeepMemoizedCallback = <T extends (...args: any[]) => any>(
  callback: T,
  deps: React.DependencyList,
  depth: number = 5
): T => {
  const ref = React.useRef<T>()
  const depsRef = React.useRef<React.DependencyList>()

  const depsChanged = !depsRef.current || !deps.every((dep, index) => 
    deepEqual(dep, depsRef.current![index], depth)
  )

  if (depsChanged) {
    ref.current = callback
    depsRef.current = deps
  }

  return React.useCallback((...args: Parameters<T>) => {
    return ref.current!(...args)
  }, [depsChanged]) as T
}