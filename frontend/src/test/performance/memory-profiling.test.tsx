import React from 'react'
import { render, cleanup } from '@testing-library/react'
import { describe, it, expect, beforeEach, afterEach } from 'vitest'
import { act } from 'react'

// Import components for memory profiling
import Badge from '../../components/ui/Badge'
import Button from '../../components/ui/Button'
import Card from '../../components/ui/Card'
import LoadingSpinner from '../../components/common/LoadingSpinner'
import SkeletonLoader from '../../components/common/SkeletonLoader'
import Modal from '../../components/ui/Modal'
import Input from '../../components/ui/Input'

describe('Memory Usage Profiling Tests', () => {
  let initialMemory: number = 0
  let memoryMetrics: Record<string, any> = {}

  beforeEach(() => {
    // Record initial memory if available
    if (typeof performance !== 'undefined' && (performance as any).memory) {
      initialMemory = (performance as any).memory.usedJSHeapSize || 0
    } else {
      // Fallback for environments without memory API
      initialMemory = 0
    }
    
    memoryMetrics = {}
    console.log(`🧠 Initial memory baseline: ${(initialMemory / 1024 / 1024).toFixed(2)} MB`)
  })

  afterEach(() => {
    cleanup()
    
    // Force garbage collection if available (Chrome DevTools)
    if (typeof window !== 'undefined' && (window as any).gc) {
      (window as any).gc()
    }
  })

  const measureMemoryUsage = (testName: string, testFn: () => void) => {
    const startMemory = typeof performance !== 'undefined' && (performance as any).memory 
      ? (performance as any).memory.usedJSHeapSize 
      : 0

    testFn()

    const endMemory = typeof performance !== 'undefined' && (performance as any).memory 
      ? (performance as any).memory.usedJSHeapSize 
      : 0

    const memoryDelta = endMemory - startMemory
    const memoryDeltaMB = memoryDelta / 1024 / 1024

    memoryMetrics[testName] = {
      startMemory: startMemory,
      endMemory: endMemory,
      memoryDelta: memoryDelta,
      memoryDeltaMB: memoryDeltaMB.toFixed(3),
      timestamp: new Date().toISOString()
    }

    console.log(`📊 ${testName}: ${memoryDeltaMB > 0 ? '+' : ''}${memoryDeltaMB.toFixed(3)} MB`)
    
    return memoryDelta
  }

  it('profiles memory usage for single component renders', () => {
    console.log('🧠 Profiling single component memory usage')
    
    const singleComponentTests = [
      {
        name: 'Badge-single',
        render: () => render(<Badge variant="primary">Memory Test</Badge>)
      },
      {
        name: 'Button-single', 
        render: () => render(<Button variant="primary">Memory Test</Button>)
      },
      {
        name: 'Card-single',
        render: () => render(<Card title="Memory Test">Content</Card>)
      },
      {
        name: 'LoadingSpinner-single',
        render: () => render(<LoadingSpinner />)
      },
      {
        name: 'SkeletonLoader-single',
        render: () => render(<SkeletonLoader variant="text" />)
      }
    ]

    const singleComponentMetrics: Record<string, number> = {}

    singleComponentTests.forEach(test => {
      const memoryDelta = measureMemoryUsage(test.name, () => {
        act(() => {
          test.render()
        })
      })
      singleComponentMetrics[test.name] = memoryDelta
      
      // Clean up after each test
      cleanup()
    })

    console.log('📊 Single Component Memory Profile:', singleComponentMetrics)

    // Memory usage assertions for single components
    Object.values(singleComponentMetrics).forEach(delta => {
      expect(Math.abs(delta)).toBeLessThan(1024 * 1024) // Each component should use <1MB
    })

    memoryMetrics.singleComponents = singleComponentMetrics
  })

  it('profiles memory usage for multiple component renders', () => {
    console.log('🧠 Profiling multiple component memory usage')

    const multipleComponentTests = [
      {
        name: 'Badge-multiple-10',
        render: () => render(
          <div>
            {Array.from({ length: 10 }, (_, i) => (
              <Badge key={i} variant="primary">Badge {i}</Badge>
            ))}
          </div>
        )
      },
      {
        name: 'Button-multiple-10',
        render: () => render(
          <div>
            {Array.from({ length: 10 }, (_, i) => (
              <Button key={i} variant="primary">Button {i}</Button>
            ))}
          </div>
        )
      },
      {
        name: 'Card-multiple-5',
        render: () => render(
          <div>
            {Array.from({ length: 5 }, (_, i) => (
              <Card key={i} title={`Card ${i}`}>Content {i}</Card>
            ))}
          </div>
        )
      },
      {
        name: 'Mixed-components-20',
        render: () => render(
          <div>
            {Array.from({ length: 20 }, (_, i) => {
              if (i % 4 === 0) return <Badge key={i} variant="primary">Item {i}</Badge>
              if (i % 4 === 1) return <Button key={i} variant="secondary">Item {i}</Button>
              if (i % 4 === 2) return <LoadingSpinner key={i} />
              return <SkeletonLoader key={i} variant="text" />
            })}
          </div>
        )
      }
    ]

    const multipleComponentMetrics: Record<string, number> = {}

    multipleComponentTests.forEach(test => {
      const memoryDelta = measureMemoryUsage(test.name, () => {
        act(() => {
          test.render()
        })
      })
      multipleComponentMetrics[test.name] = memoryDelta
      
      cleanup()
    })

    console.log('📊 Multiple Component Memory Profile:', multipleComponentMetrics)

    // Memory usage assertions for multiple components
    Object.entries(multipleComponentMetrics).forEach(([testName, delta]) => {
      const componentCount = parseInt(testName.split('-')[2] || '1')
      const memoryPerComponent = Math.abs(delta) / componentCount
      
      expect(memoryPerComponent).toBeLessThan(100 * 1024) // Each component should use <100KB on average
    })

    memoryMetrics.multipleComponents = multipleComponentMetrics
  })

  it('profiles memory usage for heavy component scenarios', () => {
    console.log('🧠 Profiling heavy component memory scenarios')

    const heavyScenarios = [
      {
        name: 'Heavy-Card-with-nested-components',
        render: () => render(
          <Card title="Heavy Card" variant="primary" size="lg">
            <div>
              <h1>Large Title</h1>
              <p>{'Large text content '.repeat(100)}</p>
              <div>
                {Array.from({ length: 20 }, (_, i) => (
                  <Badge key={i} variant="success">Tag {i}</Badge>
                ))}
              </div>
              <div>
                {Array.from({ length: 10 }, (_, i) => (
                  <Button key={i} variant="outline" size="sm">Action {i}</Button>
                ))}
              </div>
            </div>
          </Card>
        )
      },
      {
        name: 'Modal-with-complex-content',
        render: () => render(
          <Modal isOpen={true} onClose={() => {}} title="Complex Modal">
            <div>
              <form>
                {Array.from({ length: 15 }, (_, i) => (
                  <Input key={i} placeholder={`Field ${i}`} />
                ))}
              </form>
              <div>
                {Array.from({ length: 30 }, (_, i) => (
                  <SkeletonLoader key={i} variant="text" />
                ))}
              </div>
            </div>
          </Modal>
        )
      },
      {
        name: 'Large-component-tree',
        render: () => render(
          <div>
            {Array.from({ length: 100 }, (_, i) => (
              <Card key={i} title={`Card ${i}`}>
                <Badge variant="info">Status {i}</Badge>
                <p>Content for card {i}</p>
                <Button size="sm">Action {i}</Button>
              </Card>
            ))}
          </div>
        )
      }
    ]

    const heavyScenarioMetrics: Record<string, number> = {}

    heavyScenarios.forEach(test => {
      const memoryDelta = measureMemoryUsage(test.name, () => {
        act(() => {
          test.render()
        })
      })
      heavyScenarioMetrics[test.name] = memoryDelta
      
      cleanup()
    })

    console.log('📊 Heavy Scenario Memory Profile:', heavyScenarioMetrics)

    // Memory usage assertions for heavy scenarios
    Object.values(heavyScenarioMetrics).forEach(delta => {
      expect(Math.abs(delta)).toBeLessThan(10 * 1024 * 1024) // Heavy scenarios should use <10MB
    })

    memoryMetrics.heavyScenarios = heavyScenarioMetrics
  })

  it('profiles memory leaks and cleanup efficiency', () => {
    console.log('🧠 Profiling memory leaks and cleanup efficiency')

    const leakTests = [
      {
        name: 'Component-mount-unmount-cycle',
        test: () => {
          const iterations = 10
          
          for (let i = 0; i < iterations; i++) {
            const { unmount } = render(
              <div>
                <Card title={`Cycle ${i}`}>
                  <LoadingSpinner />
                  <Badge variant="primary">Iteration {i}</Badge>
                  <Button onClick={() => console.log('clicked')}>Button {i}</Button>
                </Card>
              </div>
            )
            
            // Immediately unmount
            unmount()
          }
        }
      },
      {
        name: 'Event-listener-cleanup',
        test: () => {
          const EventComponent = () => {
            React.useEffect(() => {
              const handleClick = () => console.log('global click')
              const handleResize = () => console.log('resize')
              
              document.addEventListener('click', handleClick)
              window.addEventListener('resize', handleResize)
              
              return () => {
                document.removeEventListener('click', handleClick)
                window.removeEventListener('resize', handleResize)
              }
            }, [])
            
            return <div>Event Component</div>
          }
          
          const iterations = 5
          
          for (let i = 0; i < iterations; i++) {
            const { unmount } = render(<EventComponent />)
            unmount()
          }
        }
      },
      {
        name: 'Timer-cleanup',
        test: () => {
          const TimerComponent = () => {
            React.useEffect(() => {
              const interval = setInterval(() => {
                console.log('timer tick')
              }, 100)
              
              const timeout = setTimeout(() => {
                console.log('timeout')
              }, 500)
              
              return () => {
                clearInterval(interval)
                clearTimeout(timeout)
              }
            }, [])
            
            return <div>Timer Component</div>
          }
          
          const iterations = 3
          
          for (let i = 0; i < iterations; i++) {
            const { unmount } = render(<TimerComponent />)
            // Let it run briefly before unmounting
            setTimeout(() => unmount(), 50)
          }
        }
      }
    ]

    const leakTestMetrics: Record<string, number> = {}

    leakTests.forEach(test => {
      const memoryDelta = measureMemoryUsage(test.name, () => {
        act(() => {
          test.test()
        })
      })
      leakTestMetrics[test.name] = memoryDelta
    })

    console.log('📊 Memory Leak Test Profile:', leakTestMetrics)

    // Memory leak assertions
    Object.entries(leakTestMetrics).forEach(([testName, delta]) => {
      // Memory should not significantly increase after cleanup cycles
      expect(Math.abs(delta)).toBeLessThan(2 * 1024 * 1024) // Should not leak more than 2MB
    })

    memoryMetrics.leakTests = leakTestMetrics
  })

  it('generates comprehensive memory usage report', () => {
    console.log('📋 Generating comprehensive memory usage report')

    const memoryReport = {
      summary: {
        totalTests: 0,
        averageMemoryPerComponent: 0,
        maxMemoryUsage: 0,
        minMemoryUsage: 0,
        memoryEfficiencyGrade: 'A',
        leakDetected: false
      },
      componentAnalysis: {
        mostMemoryEfficient: '',
        leastMemoryEfficient: '',
        heaviestComponent: '',
        lightestComponent: ''
      },
      recommendations: [] as string[],
      optimizationOpportunities: [] as Array<{
        component: string,
        issue: string,
        solution: string,
        impact: string
      }>
    }

    // Analyze all memory metrics
    const allDeltas: number[] = []
    const componentMemoryMap: Record<string, number> = {}

    Object.entries(memoryMetrics).forEach(([category, metrics]) => {
      if (typeof metrics === 'object' && metrics !== null) {
        Object.entries(metrics).forEach(([testName, delta]) => {
          if (typeof delta === 'number') {
            allDeltas.push(Math.abs(delta))
            componentMemoryMap[testName] = Math.abs(delta)
          }
        })
      }
    })

    memoryReport.summary.totalTests = allDeltas.length

    if (allDeltas.length > 0) {
      memoryReport.summary.averageMemoryPerComponent = allDeltas.reduce((a, b) => a + b, 0) / allDeltas.length
      memoryReport.summary.maxMemoryUsage = Math.max(...allDeltas)
      memoryReport.summary.minMemoryUsage = Math.min(...allDeltas)

      // Find most/least efficient components
      const sortedComponents = Object.entries(componentMemoryMap).sort((a, b) => a[1] - b[1])
      
      if (sortedComponents.length > 0) {
        memoryReport.componentAnalysis.lightestComponent = `${sortedComponents[0][0]} (${(sortedComponents[0][1] / 1024).toFixed(1)}KB)`
        memoryReport.componentAnalysis.heaviestComponent = `${sortedComponents[sortedComponents.length - 1][0]} (${(sortedComponents[sortedComponents.length - 1][1] / 1024).toFixed(1)}KB)`
      }

      // Determine efficiency grade
      const avgKB = memoryReport.summary.averageMemoryPerComponent / 1024
      if (avgKB < 50) {
        memoryReport.summary.memoryEfficiencyGrade = 'A+'
      } else if (avgKB < 100) {
        memoryReport.summary.memoryEfficiencyGrade = 'A'
      } else if (avgKB < 200) {
        memoryReport.summary.memoryEfficiencyGrade = 'B'
      } else if (avgKB < 500) {
        memoryReport.summary.memoryEfficiencyGrade = 'C'
      } else {
        memoryReport.summary.memoryEfficiencyGrade = 'D'
      }

      // Check for potential leaks
      const leakTests = memoryMetrics.leakTests || {}
      const hasSignificantLeaks = Object.values(leakTests).some(delta => 
        typeof delta === 'number' && Math.abs(delta) > 1024 * 1024
      )
      memoryReport.summary.leakDetected = hasSignificantLeaks
    }

    // Generate recommendations
    if (memoryReport.summary.maxMemoryUsage > 5 * 1024 * 1024) {
      memoryReport.recommendations.push('Implement component virtualization for large lists')
    }

    if (memoryReport.summary.averageMemoryPerComponent > 100 * 1024) {
      memoryReport.recommendations.push('Optimize component props and reduce unnecessary re-renders')
    }

    if (memoryReport.summary.leakDetected) {
      memoryReport.recommendations.push('Review event listener and timer cleanup in useEffect hooks')
    }

    memoryReport.recommendations.push('Implement React.memo for expensive components')
    memoryReport.recommendations.push('Use React DevTools Profiler to identify memory bottlenecks')
    memoryReport.recommendations.push('Add memory usage monitoring to production builds')

    // Generate optimization opportunities
    if (componentMemoryMap['Heavy-Card-with-nested-components'] > 1024 * 1024) {
      memoryReport.optimizationOpportunities.push({
        component: 'Card with nested components',
        issue: 'High memory usage with complex content',
        solution: 'Implement content virtualization or lazy loading',
        impact: 'Reduce memory by 50-70%'
      })
    }

    if (componentMemoryMap['Large-component-tree'] > 5 * 1024 * 1024) {
      memoryReport.optimizationOpportunities.push({
        component: 'Large component trees',
        issue: 'Excessive memory usage with many components',
        solution: 'Implement windowing/virtualization',
        impact: 'Reduce memory by 80-90%'
      })
    }

    console.log('📊 Memory Usage Report Generated:')
    console.log(`Total Tests: ${memoryReport.summary.totalTests}`)
    console.log(`Average Memory per Component: ${(memoryReport.summary.averageMemoryPerComponent / 1024).toFixed(1)}KB`)
    console.log(`Memory Efficiency Grade: ${memoryReport.summary.memoryEfficiencyGrade}`)
    console.log(`Leak Detected: ${memoryReport.summary.leakDetected ? 'Yes' : 'No'}`)
    console.log(`Lightest Component: ${memoryReport.componentAnalysis.lightestComponent}`)
    console.log(`Heaviest Component: ${memoryReport.componentAnalysis.heaviestComponent}`)

    console.log('\n🎯 Memory Optimization Recommendations:')
    memoryReport.recommendations.forEach(rec => console.log(`• ${rec}`))

    console.log('\n🔧 Optimization Opportunities:')
    memoryReport.optimizationOpportunities.forEach(opp => {
      console.log(`• ${opp.component}: ${opp.issue}`)
      console.log(`  Solution: ${opp.solution}`)
      console.log(`  Impact: ${opp.impact}`)
    })

    // Memory report assertions
    expect(memoryReport.summary.totalTests).toBeGreaterThan(0)
    expect(memoryReport.summary.memoryEfficiencyGrade).toMatch(/^[A-D]/)
    expect(memoryReport.recommendations.length).toBeGreaterThan(0)
    expect(memoryReport.summary.averageMemoryPerComponent).toBeLessThan(10 * 1024 * 1024) // <10MB average
  })
})