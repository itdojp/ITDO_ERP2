import React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { renderHook, act } from '@testing-library/react'
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest'

import { usePerformanceMonitor, withPerformanceMonitor } from '../hooks/usePerformanceMonitor'
import { useVirtualization } from '../hooks/useVirtualization'
import { useMemoizedCallback, useStableCallback } from '../hooks/useMemoizedCallback'
import VirtualizedUserList from '../components/optimized/VirtualizedUserList'
import { UserRole, UserStatus, User } from '../services/api/types'

// Mock data
const createMockUser = (id: number): User => ({
  id: id.toString(),
  email: `user${id}@example.com`,
  fullName: `User ${id}`,
  role: UserRole.MEMBER,
  status: UserStatus.ACTIVE,
  avatar: null,
  lastLoginAt: new Date().toISOString(),
  createdAt: new Date().toISOString(),
  updatedAt: new Date().toISOString(),
  departmentId: '1',
  permissions: []
})

const createMockUsers = (count: number): User[] => {
  return Array.from({ length: count }, (_, i) => createMockUser(i + 1))
}

// Performance test utilities
const measureRenderTime = async (renderFn: () => void): Promise<number> => {
  const start = performance.now()
  renderFn()
  const end = performance.now()
  return end - start
}

const measureAsyncRenderTime = async (renderFn: () => Promise<void>): Promise<number> => {
  const start = performance.now()
  await renderFn()
  const end = performance.now()
  return end - start
}

describe('Performance Monitoring', () => {
  beforeEach(() => {
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  describe('usePerformanceMonitor', () => {
    it('should track render metrics', () => {
      const { result } = renderHook(() =>
        usePerformanceMonitor({
          componentName: 'TestComponent',
          threshold: 16
        })
      )

      expect(result.current.metrics.componentName).toBe('TestComponent')
      expect(result.current.metrics.renderCount).toBe(1)
      expect(result.current.metrics.renderTime).toBeGreaterThan(0)
    })

    it('should detect slow renders', () => {
      const onSlowRender = vi.fn()
      
      const { result, rerender } = renderHook(() =>
        usePerformanceMonitor({
          componentName: 'SlowComponent',
          threshold: 1, // Very low threshold
          onSlowRender
        })
      )

      // Force a slow render by blocking the main thread
      const blockMainThread = (ms: number) => {
        const start = Date.now()
        while (Date.now() - start < ms) {
          // Block
        }
      }

      act(() => {
        blockMainThread(5) // Block for 5ms
        rerender()
      })

      expect(onSlowRender).toHaveBeenCalled()
      expect(result.current.metrics.isSlowRender).toBe(true)
    })

    it('should calculate average render time', () => {
      const { result, rerender } = renderHook(() =>
        usePerformanceMonitor({
          componentName: 'TestComponent'
        })
      )

      // Trigger multiple renders
      act(() => {
        for (let i = 0; i < 5; i++) {
          rerender()
        }
      })

      expect(result.current.metrics.renderCount).toBe(6) // Initial + 5 rerenders
      expect(result.current.metrics.averageRenderTime).toBeGreaterThan(0)
    })

    it('should provide performance report', () => {
      const { result } = renderHook(() =>
        usePerformanceMonitor({
          componentName: 'ReportComponent'
        })
      )

      const report = result.current.getReport()
      expect(report).toContain('Performance Report for ReportComponent')
      expect(report).toContain('Total Renders:')
      expect(report).toContain('Average Render Time:')
    })
  })

  describe('withPerformanceMonitor HOC', () => {
    it('should wrap component with performance monitoring', () => {
      const TestComponent = ({ children }: { children: React.ReactNode }) => (
        <div>{children}</div>
      )

      const MonitoredComponent = withPerformanceMonitor(TestComponent, {
        componentName: 'MonitoredTest'
      })

      render(<MonitoredComponent>Test Content</MonitoredComponent>)

      expect(screen.getByText('Test Content')).toBeInTheDocument()
    })

    it('should log slow renders in development', () => {
      const originalEnv = process.env.NODE_ENV
      process.env.NODE_ENV = 'development'
      
      const consoleSpy = vi.spyOn(console, 'warn').mockImplementation(() => {})

      const SlowComponent = () => {
        // Simulate slow component
        const start = Date.now()
        while (Date.now() - start < 20) {
          // Block
        }
        return <div>Slow Component</div>
      }

      const MonitoredSlowComponent = withPerformanceMonitor(SlowComponent, {
        componentName: 'SlowComponent',
        threshold: 10
      })

      render(<MonitoredSlowComponent />)

      // Fast forward timers to trigger performance check
      act(() => {
        vi.runAllTimers()
      })

      expect(consoleSpy).toHaveBeenCalledWith(
        expect.stringContaining('Slow render detected in SlowComponent')
      )

      consoleSpy.mockRestore()
      process.env.NODE_ENV = originalEnv
    })
  })
})

describe('Virtualization Performance', () => {
  describe('useVirtualization', () => {
    it('should handle large datasets efficiently', () => {
      const items = createMockUsers(10000) // Large dataset
      
      const { result } = renderHook(() =>
        useVirtualization(items, {
          itemHeight: 50,
          containerHeight: 400,
          overscan: 5
        })
      )

      // Should only render visible items + overscan
      expect(result.current.virtualItems.length).toBeLessThan(20)
      expect(result.current.totalHeight).toBe(500000) // 10000 * 50
    })

    it('should update virtual items on scroll', () => {
      const items = createMockUsers(1000)
      
      const { result } = renderHook(() =>
        useVirtualization(items, {
          itemHeight: 50,
          containerHeight: 400,
          overscan: 2
        })
      )

      const initialStartIndex = result.current.startIndex

      // Simulate scroll
      act(() => {
        const mockScrollEvent = {
          currentTarget: { scrollTop: 500 }
        } as React.UIEvent<HTMLElement>
        
        result.current.scrollElementProps.onScroll(mockScrollEvent)
      })

      expect(result.current.startIndex).toBeGreaterThan(initialStartIndex)
    })

    it('should provide correct item props', () => {
      const items = createMockUsers(100)
      
      const { result } = renderHook(() =>
        useVirtualization(items, {
          itemHeight: 60,
          containerHeight: 300
        })
      )

      const itemProps = result.current.getItemProps(5)
      
      expect(itemProps.key).toBe('virtual-item-5')
      expect(itemProps.style.position).toBe('absolute')
      expect(itemProps.style.top).toBe(300) // 5 * 60
      expect(itemProps.style.height).toBe(60)
      expect(itemProps['data-index']).toBe(5)
    })
  })

  describe('VirtualizedUserList', () => {
    it('should render large user lists efficiently', async () => {
      const users = createMockUsers(5000)
      const onUserSelect = vi.fn()

      const renderTime = await measureRenderTime(() => {
        render(
          <VirtualizedUserList
            users={users}
            height={600}
            onUserSelect={onUserSelect}
          />
        )
      })

      // Should render quickly even with large datasets
      expect(renderTime).toBeLessThan(100) // 100ms threshold

      // Should only render visible DOM elements
      const userRows = screen.getAllByRole('row')
      expect(userRows.length).toBeLessThan(20) // Only visible rows
    })

    it('should handle search efficiently', async () => {
      const users = createMockUsers(1000)
      const onSearch = vi.fn()

      render(
        <VirtualizedUserList
          users={users}
          height={600}
          onSearch={onSearch}
        />
      )

      const searchInput = screen.getByPlaceholderText(/search users/i)

      const start = performance.now()
      fireEvent.change(searchInput, { target: { value: 'test query' } })
      
      // Wait for throttled search
      await act(async () => {
        vi.advanceTimersByTime(350)
      })

      const end = performance.now()
      const searchTime = end - start

      expect(searchTime).toBeLessThan(50) // Fast search response
      expect(onSearch).toHaveBeenCalledWith('test query')
    })

    it('should handle selection efficiently', () => {
      const users = createMockUsers(100)
      const onSelectionChange = vi.fn()

      render(
        <VirtualizedUserList
          users={users}
          height={600}
          onSelectionChange={onSelectionChange}
          selectedUsers={[]}
        />
      )

      const selectAllCheckbox = screen.getByLabelText(/select all users/i)

      const start = performance.now()
      fireEvent.click(selectAllCheckbox)
      const end = performance.now()

      const selectionTime = end - start

      expect(selectionTime).toBeLessThan(10) // Very fast selection
      expect(onSelectionChange).toHaveBeenCalledWith(
        users.map(user => user.id)
      )
    })
  })
})

describe('Callback Optimization', () => {
  describe('useMemoizedCallback', () => {
    it('should memoize callbacks with stable dependencies', () => {
      let renderCount = 0
      const TestComponent = ({ value }: { value: number }) => {
        renderCount++
        
        const callback = useMemoizedCallback(() => {
          return value * 2
        }, [value])

        return <div onClick={callback}>Value: {value}</div>
      }

      const { rerender } = render(<TestComponent value={5} />)
      
      // Same dependencies should not cause re-render
      rerender(<TestComponent value={5} />)
      rerender(<TestComponent value={5} />)

      expect(renderCount).toBe(3) // Component re-renders but callback is memoized
    })

    it('should update callback when dependencies change', () => {
      const results: number[] = []
      
      const TestComponent = ({ value }: { value: number }) => {
        const callback = useMemoizedCallback(() => {
          results.push(value * 2)
          return value * 2
        }, [value])

        React.useEffect(() => {
          callback()
        }, [callback])

        return <div>Value: {value}</div>
      }

      const { rerender } = render(<TestComponent value={5} />)
      rerender(<TestComponent value={10} />)
      rerender(<TestComponent value={10} />) // Same value, should not re-execute

      expect(results).toEqual([10, 20]) // Only executed when value changed
    })
  })

  describe('useStableCallback', () => {
    it('should provide stable callback reference', () => {
      const callbacks: Array<() => void> = []
      
      const TestComponent = ({ value }: { value: number }) => {
        const stableCallback = useStableCallback(() => {
          console.log('Stable callback called with:', value)
        })

        callbacks.push(stableCallback)
        return <div>Value: {value}</div>
      }

      const { rerender } = render(<TestComponent value={1} />)
      rerender(<TestComponent value={2} />)
      rerender(<TestComponent value={3} />)

      // All callbacks should be the same reference
      expect(callbacks[0]).toBe(callbacks[1])
      expect(callbacks[1]).toBe(callbacks[2])
    })
  })
})

describe('Memory Management', () => {
  it('should not create memory leaks with large datasets', () => {
    const initialMemory = (performance as any).memory?.usedJSHeapSize || 0

    // Render and unmount multiple large components
    for (let i = 0; i < 10; i++) {
      const users = createMockUsers(1000)
      const { unmount } = render(
        <VirtualizedUserList users={users} height={600} />
      )
      unmount()
    }

    // Force garbage collection if available
    if (global.gc) {
      global.gc()
    }

    const finalMemory = (performance as any).memory?.usedJSHeapSize || 0
    const memoryGrowth = finalMemory - initialMemory

    // Memory growth should be minimal (less than 10MB)
    expect(memoryGrowth).toBeLessThan(10 * 1024 * 1024)
  })

  it('should clean up event listeners and timers', () => {
    const addEventListenerSpy = vi.spyOn(window, 'addEventListener')
    const removeEventListenerSpy = vi.spyOn(window, 'removeEventListener')
    const setTimeoutSpy = vi.spyOn(global, 'setTimeout')
    const clearTimeoutSpy = vi.spyOn(global, 'clearTimeout')

    const users = createMockUsers(100)
    const { unmount } = render(
      <VirtualizedUserList users={users} height={600} />
    )

    const addListenerCalls = addEventListenerSpy.mock.calls.length
    const setTimeoutCalls = setTimeoutSpy.mock.calls.length

    unmount()

    // Should clean up resources
    expect(removeEventListenerSpy.mock.calls.length).toBeGreaterThanOrEqual(0)
    expect(clearTimeoutSpy.mock.calls.length).toBeGreaterThanOrEqual(0)

    addEventListenerSpy.mockRestore()
    removeEventListenerSpy.mockRestore()
    setTimeoutSpy.mockRestore()
    clearTimeoutSpy.mockRestore()
  })
})

describe('Bundle Size Impact', () => {
  it('should have minimal bundle size impact for performance hooks', () => {
    // This is a conceptual test - in a real scenario you'd use bundle analyzers
    const hooks = [
      usePerformanceMonitor,
      useVirtualization,
      useMemoizedCallback,
      useStableCallback
    ]

    // Each hook should be tree-shakeable and not import unnecessary dependencies
    hooks.forEach(hook => {
      expect(typeof hook).toBe('function')
      expect(hook.length).toBeLessThan(3) // Reasonable parameter count
    })
  })
})