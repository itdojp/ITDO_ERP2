import { renderHook, act } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import useLoading from './useLoading'

describe('useLoading', () => {
  it('should initialize with default loading state false', () => {
    const { result } = renderHook(() => useLoading())
    
    expect(result.current.isLoading()).toBe(false)
    expect(result.current.anyLoading).toBe(false)
    expect(result.current.loadingStates).toEqual({ default: false })
  })

  it('should initialize with custom boolean state', () => {
    const { result } = renderHook(() => useLoading(true))
    
    expect(result.current.isLoading()).toBe(true)
    expect(result.current.anyLoading).toBe(true)
    expect(result.current.loadingStates).toEqual({ default: true })
  })

  it('should initialize with custom object state', () => {
    const initialState = { api: true, form: false }
    const { result } = renderHook(() => useLoading(initialState))
    
    expect(result.current.isLoading('api')).toBe(true)
    expect(result.current.isLoading('form')).toBe(false)
    expect(result.current.isLoading()).toBe(false) // default key
    expect(result.current.anyLoading).toBe(true)
    expect(result.current.loadingStates).toEqual({ default: false, api: true, form: false })
  })

  it('should set loading state for default key', () => {
    const { result } = renderHook(() => useLoading())
    
    act(() => {
      result.current.setLoading(true)
    })
    
    expect(result.current.isLoading()).toBe(true)
    expect(result.current.anyLoading).toBe(true)
  })

  it('should set loading state for custom key', () => {
    const { result } = renderHook(() => useLoading())
    
    act(() => {
      result.current.setLoading(true, 'api')
    })
    
    expect(result.current.isLoading('api')).toBe(true)
    expect(result.current.isLoading()).toBe(false) // default key
    expect(result.current.anyLoading).toBe(true)
  })

  it('should start loading for default key', () => {
    const { result } = renderHook(() => useLoading())
    
    act(() => {
      result.current.startLoading()
    })
    
    expect(result.current.isLoading()).toBe(true)
    expect(result.current.anyLoading).toBe(true)
  })

  it('should start loading for custom key', () => {
    const { result } = renderHook(() => useLoading())
    
    act(() => {
      result.current.startLoading('form')
    })
    
    expect(result.current.isLoading('form')).toBe(true)
    expect(result.current.isLoading()).toBe(false)
    expect(result.current.anyLoading).toBe(true)
  })

  it('should stop loading for default key', () => {
    const { result } = renderHook(() => useLoading(true))
    
    act(() => {
      result.current.stopLoading()
    })
    
    expect(result.current.isLoading()).toBe(false)
    expect(result.current.anyLoading).toBe(false)
  })

  it('should stop loading for custom key', () => {
    const { result } = renderHook(() => useLoading({ api: true, form: true }))
    
    act(() => {
      result.current.stopLoading('api')
    })
    
    expect(result.current.isLoading('api')).toBe(false)
    expect(result.current.isLoading('form')).toBe(true)
    expect(result.current.anyLoading).toBe(true)
  })

  it('should handle multiple loading states', () => {
    const { result } = renderHook(() => useLoading())
    
    act(() => {
      result.current.startLoading('api')
      result.current.startLoading('form')
      result.current.startLoading('upload')
    })
    
    expect(result.current.isLoading('api')).toBe(true)
    expect(result.current.isLoading('form')).toBe(true)
    expect(result.current.isLoading('upload')).toBe(true)
    expect(result.current.anyLoading).toBe(true)
    
    act(() => {
      result.current.stopLoading('api')
    })
    
    expect(result.current.isLoading('api')).toBe(false)
    expect(result.current.isLoading('form')).toBe(true)
    expect(result.current.isLoading('upload')).toBe(true)
    expect(result.current.anyLoading).toBe(true)
    
    act(() => {
      result.current.stopLoading('form')
      result.current.stopLoading('upload')
    })
    
    expect(result.current.anyLoading).toBe(false)
  })

  it('should return false for non-existent keys', () => {
    const { result } = renderHook(() => useLoading())
    
    expect(result.current.isLoading('nonexistent')).toBe(false)
  })

  it('should preserve existing states when setting new ones', () => {
    const { result } = renderHook(() => useLoading({ existing: true }))
    
    act(() => {
      result.current.setLoading(true, 'new')
    })
    
    expect(result.current.isLoading('existing')).toBe(true)
    expect(result.current.isLoading('new')).toBe(true)
    expect(result.current.loadingStates).toEqual({
      default: false,
      existing: true,
      new: true
    })
  })

  it('should update anyLoading correctly when all states are false', () => {
    const { result } = renderHook(() => useLoading({ a: true, b: true }))
    
    expect(result.current.anyLoading).toBe(true)
    
    act(() => {
      result.current.stopLoading('a')
      result.current.stopLoading('b')
    })
    
    expect(result.current.anyLoading).toBe(false)
  })
})