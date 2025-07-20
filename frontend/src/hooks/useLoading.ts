import { useState, useCallback } from 'react'

export interface LoadingState {
  [key: string]: boolean
}

export interface UseLoadingReturn {
  isLoading: (key?: string) => boolean
  setLoading: (loading: boolean, key?: string) => void
  startLoading: (key?: string) => void
  stopLoading: (key?: string) => void
  loadingStates: LoadingState
  anyLoading: boolean
}

export const useLoading = (initialState: boolean | LoadingState = false): UseLoadingReturn => {
  const [loadingStates, setLoadingStates] = useState<LoadingState>(() => {
    if (typeof initialState === 'boolean') {
      return { default: initialState }
    }
    return { default: false, ...initialState }
  })

  const isLoading = useCallback((key: string = 'default'): boolean => {
    return loadingStates[key] || false
  }, [loadingStates])

  const setLoading = useCallback((loading: boolean, key: string = 'default') => {
    setLoadingStates(prev => ({
      ...prev,
      [key]: loading
    }))
  }, [])

  const startLoading = useCallback((key: string = 'default') => {
    setLoading(true, key)
  }, [setLoading])

  const stopLoading = useCallback((key: string = 'default') => {
    setLoading(false, key)
  }, [setLoading])

  const anyLoading = Object.values(loadingStates).some(Boolean)

  return {
    isLoading,
    setLoading,
    startLoading,
    stopLoading,
    loadingStates,
    anyLoading
  }
}

export default useLoading