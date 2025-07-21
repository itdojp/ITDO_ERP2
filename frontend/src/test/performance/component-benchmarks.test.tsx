import React from 'react'
import { render } from '@testing-library/react'
import { describe, it, expect, beforeEach } from 'vitest'
import { act } from 'react'

// Import components for benchmarking
import Badge from '../../components/ui/Badge'
import Button from '../../components/ui/Button'
import Card from '../../components/ui/Card'
import Alert from '../../components/ui/Alert'
import LoadingSpinner from '../../components/common/LoadingSpinner'
import SkeletonLoader from '../../components/common/SkeletonLoader'
import Modal from '../../components/ui/Modal'
import Input from '../../components/ui/Input'

describe('Component Render Performance Benchmarks', () => {
  let performanceMetrics: Record<string, any> = {}

  beforeEach(() => {
    performanceMetrics = {}
    // Clear performance entries
    if (typeof performance !== 'undefined' && performance.clearMarks) {
      performance.clearMarks()
      performance.clearMeasures()
    }
  })

  const measureRenderTime = (componentName: string, renderFn: () => void) => {
    const startTime = performance.now()
    
    act(() => {
      renderFn()
    })
    
    const endTime = performance.now()
    const renderTime = endTime - startTime
    
    performanceMetrics[componentName] = {
      renderTime,
      timestamp: new Date().toISOString()
    }
    
    return renderTime
  }

  it('benchmarks Badge component render performance', () => {
    console.log('🔍 Benchmarking Badge component performance')
    
    const badgeVariants = ['primary', 'secondary', 'success', 'warning', 'error', 'info'] as const
    const badgeSizes = ['sm', 'md', 'lg'] as const
    
    const badgeMetrics: Record<string, number> = {}
    
    // Test single badge render
    const singleBadgeTime = measureRenderTime('Badge-single', () => {
      render(<Badge variant="primary">Single Badge</Badge>)
    })
    badgeMetrics['single'] = singleBadgeTime
    
    // Test multiple badge variants
    const multiVariantTime = measureRenderTime('Badge-multiVariant', () => {
      render(
        <div>
          {badgeVariants.map(variant => (
            <Badge key={variant} variant={variant}>{variant}</Badge>
          ))}
        </div>
      )
    })
    badgeMetrics['multiVariant'] = multiVariantTime
    
    // Test large quantity render
    const largeQuantityTime = measureRenderTime('Badge-largeQuantity', () => {
      render(
        <div>
          {Array.from({ length: 100 }, (_, i) => (
            <Badge key={i} variant="primary">Badge {i}</Badge>
          ))}
        </div>
      )
    })
    badgeMetrics['largeQuantity'] = largeQuantityTime
    
    console.log('Badge Performance Metrics:', badgeMetrics)
    
    // Performance assertions
    expect(singleBadgeTime).toBeLessThan(50) // Single badge should render in <50ms
    expect(multiVariantTime).toBeLessThan(100) // 6 variants should render in <100ms
    expect(largeQuantityTime).toBeLessThan(500) // 100 badges should render in <500ms
    
    performanceMetrics.Badge = badgeMetrics
  })

  it('benchmarks Button component render performance', () => {
    console.log('🔍 Benchmarking Button component performance')
    
    const buttonVariants = ['primary', 'secondary', 'outline', 'ghost', 'link'] as const
    const buttonSizes = ['sm', 'md', 'lg'] as const
    
    const buttonMetrics: Record<string, number> = {}
    
    // Test single button render
    const singleButtonTime = measureRenderTime('Button-single', () => {
      render(<Button variant="primary">Single Button</Button>)
    })
    buttonMetrics['single'] = singleButtonTime
    
    // Test button with loading state
    const loadingButtonTime = measureRenderTime('Button-loading', () => {
      render(<Button loading={true}>Loading Button</Button>)
    })
    buttonMetrics['loading'] = loadingButtonTime
    
    // Test multiple button configurations
    const multiConfigTime = measureRenderTime('Button-multiConfig', () => {
      render(
        <div>
          {buttonVariants.map(variant => 
            buttonSizes.map(size => (
              <Button key={`${variant}-${size}`} variant={variant} size={size}>
                {variant} {size}
              </Button>
            ))
          )}
        </div>
      )
    })
    buttonMetrics['multiConfig'] = multiConfigTime
    
    console.log('Button Performance Metrics:', buttonMetrics)
    
    // Performance assertions
    expect(singleButtonTime).toBeLessThan(30) // Single button should render in <30ms
    expect(loadingButtonTime).toBeLessThan(50) // Loading button should render in <50ms
    expect(multiConfigTime).toBeLessThan(200) // 15 buttons should render in <200ms
    
    performanceMetrics.Button = buttonMetrics
  })

  it('benchmarks Card component render performance', () => {
    console.log('🔍 Benchmarking Card component performance')
    
    const cardMetrics: Record<string, number> = {}
    
    // Test simple card render
    const simpleCardTime = measureRenderTime('Card-simple', () => {
      render(<Card title="Simple Card">Simple content</Card>)
    })
    cardMetrics['simple'] = simpleCardTime
    
    // Test complex card with nested content
    const complexCardTime = measureRenderTime('Card-complex', () => {
      render(
        <Card title="Complex Card" variant="primary" size="lg">
          <div>
            <h3>Nested Title</h3>
            <p>Multiple paragraphs with various content types.</p>
            <Badge variant="success">Status Badge</Badge>
            <Button variant="outline" size="sm">Action Button</Button>
          </div>
        </Card>
      )
    })
    cardMetrics['complex'] = complexCardTime
    
    // Test multiple cards
    const multipleCardsTime = measureRenderTime('Card-multiple', () => {
      render(
        <div>
          {Array.from({ length: 20 }, (_, i) => (
            <Card key={i} title={`Card ${i}`} variant={i % 2 === 0 ? 'primary' : 'secondary'}>
              <p>Card content {i}</p>
              <Badge variant="info">Card {i}</Badge>
            </Card>
          ))}
        </div>
      )
    })
    cardMetrics['multiple'] = multipleCardsTime
    
    console.log('Card Performance Metrics:', cardMetrics)
    
    // Performance assertions
    expect(simpleCardTime).toBeLessThan(40) // Simple card should render in <40ms
    expect(complexCardTime).toBeLessThan(80) // Complex card should render in <80ms
    expect(multipleCardsTime).toBeLessThan(400) // 20 cards should render in <400ms
    
    performanceMetrics.Card = cardMetrics
  })

  it('benchmarks LoadingSpinner component render performance', () => {
    console.log('🔍 Benchmarking LoadingSpinner component performance')
    
    const spinnerMetrics: Record<string, number> = {}
    
    // Test single spinner render
    const singleSpinnerTime = measureRenderTime('LoadingSpinner-single', () => {
      render(<LoadingSpinner />)
    })
    spinnerMetrics['single'] = singleSpinnerTime
    
    // Test multiple spinners with different configurations
    const multipleSpinnersTime = measureRenderTime('LoadingSpinner-multiple', () => {
      render(
        <div>
          <LoadingSpinner size="small" color="primary" />
          <LoadingSpinner size="medium" color="secondary" />
          <LoadingSpinner size="large" color="white" />
        </div>
      )
    })
    spinnerMetrics['multiple'] = multipleSpinnersTime
    
    // Test rapid spinner state changes simulation
    const stateChangesTime = measureRenderTime('LoadingSpinner-stateChanges', () => {
      const SpinnerWithChanges = () => {
        const [visible, setVisible] = React.useState(true)
        
        React.useEffect(() => {
          const interval = setInterval(() => {
            setVisible(prev => !prev)
          }, 10)
          
          setTimeout(() => clearInterval(interval), 100)
          
          return () => clearInterval(interval)
        }, [])
        
        return visible ? <LoadingSpinner /> : <div>Hidden</div>
      }
      
      render(<SpinnerWithChanges />)
    })
    spinnerMetrics['stateChanges'] = stateChangesTime
    
    console.log('LoadingSpinner Performance Metrics:', spinnerMetrics)
    
    // Performance assertions
    expect(singleSpinnerTime).toBeLessThan(20) // Single spinner should render in <20ms
    expect(multipleSpinnersTime).toBeLessThan(60) // 3 spinners should render in <60ms
    expect(stateChangesTime).toBeLessThan(100) // State changes should handle in <100ms
    
    performanceMetrics.LoadingSpinner = spinnerMetrics
  })

  it('benchmarks SkeletonLoader component render performance', () => {
    console.log('🔍 Benchmarking SkeletonLoader component performance')
    
    const skeletonMetrics: Record<string, number> = {}
    
    // Test single skeleton render
    const singleSkeletonTime = measureRenderTime('SkeletonLoader-single', () => {
      render(<SkeletonLoader variant="text" />)
    })
    skeletonMetrics['single'] = singleSkeletonTime
    
    // Test complex skeleton variants
    const complexSkeletonTime = measureRenderTime('SkeletonLoader-complex', () => {
      render(
        <div>
          <SkeletonLoader variant="text" lines={5} />
          <SkeletonLoader variant="card" />
          <SkeletonLoader variant="avatar" />
          <SkeletonLoader variant="table" lines={3} />
        </div>
      )
    })
    skeletonMetrics['complex'] = complexSkeletonTime
    
    // Test large skeleton grid
    const largeGridTime = measureRenderTime('SkeletonLoader-largeGrid', () => {
      render(
        <div>
          {Array.from({ length: 50 }, (_, i) => (
            <SkeletonLoader key={i} variant={i % 2 === 0 ? 'text' : 'card'} />
          ))}
        </div>
      )
    })
    skeletonMetrics['largeGrid'] = largeGridTime
    
    console.log('SkeletonLoader Performance Metrics:', skeletonMetrics)
    
    // Performance assertions
    expect(singleSkeletonTime).toBeLessThan(30) // Single skeleton should render in <30ms
    expect(complexSkeletonTime).toBeLessThan(100) // Complex skeletons should render in <100ms
    expect(largeGridTime).toBeLessThan(600) // 50 skeletons should render in <600ms
    
    performanceMetrics.SkeletonLoader = skeletonMetrics
  })

  it('benchmarks Modal component render performance', () => {
    console.log('🔍 Benchmarking Modal component performance')
    
    const modalMetrics: Record<string, number> = {}
    
    // Test closed modal render (minimal)
    const closedModalTime = measureRenderTime('Modal-closed', () => {
      render(
        <Modal isOpen={false} onClose={() => {}} title="Closed Modal">
          <p>Modal content</p>
        </Modal>
      )
    })
    modalMetrics['closed'] = closedModalTime
    
    // Test open modal render
    const openModalTime = measureRenderTime('Modal-open', () => {
      render(
        <Modal isOpen={true} onClose={() => {}} title="Open Modal">
          <div>
            <p>Modal with complex content</p>
            <Input placeholder="Input in modal" />
            <Button variant="primary">Modal Button</Button>
          </div>
        </Modal>
      )
    })
    modalMetrics['open'] = openModalTime
    
    // Test modal with large content
    const largeContentModalTime = measureRenderTime('Modal-largeContent', () => {
      render(
        <Modal isOpen={true} onClose={() => {}} title="Large Content Modal">
          <div>
            {Array.from({ length: 100 }, (_, i) => (
              <p key={i}>Large content paragraph {i}</p>
            ))}
          </div>
        </Modal>
      )
    })
    modalMetrics['largeContent'] = largeContentModalTime
    
    console.log('Modal Performance Metrics:', modalMetrics)
    
    // Performance assertions
    expect(closedModalTime).toBeLessThan(15) // Closed modal should render in <15ms
    expect(openModalTime).toBeLessThan(80) // Open modal should render in <80ms
    expect(largeContentModalTime).toBeLessThan(300) // Large content modal should render in <300ms
    
    performanceMetrics.Modal = modalMetrics
  })

  it('benchmarks Input component render performance', () => {
    console.log('🔍 Benchmarking Input component performance')
    
    const inputMetrics: Record<string, number> = {}
    
    // Test simple input render
    const simpleInputTime = measureRenderTime('Input-simple', () => {
      render(<Input placeholder="Simple input" />)
    })
    inputMetrics['simple'] = simpleInputTime
    
    // Test complex input with all features
    const complexInputTime = measureRenderTime('Input-complex', () => {
      render(
        <Input
          variant="outline"
          size="lg"
          label="Complex Input"
          placeholder="Enter value"
          error={true}
          errorMessage="Validation error"
          leftIcon={<span>📧</span>}
          rightIcon={<span>🔍</span>}
          loading={true}
        />
      )
    })
    inputMetrics['complex'] = complexInputTime
    
    // Test multiple input forms
    const multipleInputsTime = measureRenderTime('Input-multiple', () => {
      render(
        <form>
          {Array.from({ length: 20 }, (_, i) => (
            <Input
              key={i}
              placeholder={`Input ${i}`}
              variant={i % 2 === 0 ? 'default' : 'outline'}
              size={i % 3 === 0 ? 'sm' : i % 3 === 1 ? 'md' : 'lg'}
            />
          ))}
        </form>
      )
    })
    inputMetrics['multiple'] = multipleInputsTime
    
    console.log('Input Performance Metrics:', inputMetrics)
    
    // Performance assertions
    expect(simpleInputTime).toBeLessThan(25) // Simple input should render in <25ms
    expect(complexInputTime).toBeLessThan(60) // Complex input should render in <60ms
    expect(multipleInputsTime).toBeLessThan(300) // 20 inputs should render in <300ms
    
    performanceMetrics.Input = inputMetrics
  })

  it('generates comprehensive performance report', () => {
    console.log('📊 Generating comprehensive performance report')
    
    const allComponents = Object.keys(performanceMetrics)
    const totalTests = allComponents.length
    
    let totalRenderTime = 0
    let slowestComponent = ''
    let fastestComponent = ''
    let slowestTime = 0
    let fastestTime = Infinity
    
    const performanceReport = {
      summary: {
        totalComponents: totalTests,
        totalRenderTime: 0,
        averageRenderTime: 0,
        slowestComponent: '',
        fastestComponent: '',
        performanceGrade: 'A'
      },
      componentDetails: performanceMetrics,
      recommendations: [] as string[]
    }
    
    // Calculate statistics
    allComponents.forEach(component => {
      const componentMetrics = performanceMetrics[component]
      if (componentMetrics && typeof componentMetrics === 'object') {
        const componentTimes = Object.values(componentMetrics).filter(v => typeof v === 'number')
        const avgComponentTime = componentTimes.reduce((a, b) => a + b, 0) / componentTimes.length
        
        totalRenderTime += avgComponentTime
        
        if (avgComponentTime > slowestTime) {
          slowestTime = avgComponentTime
          slowestComponent = component
        }
        
        if (avgComponentTime < fastestTime) {
          fastestTime = avgComponentTime
          fastestComponent = component
        }
      }
    })
    
    performanceReport.summary.totalRenderTime = totalRenderTime
    performanceReport.summary.averageRenderTime = totalRenderTime / totalTests
    performanceReport.summary.slowestComponent = `${slowestComponent} (${slowestTime.toFixed(2)}ms)`
    performanceReport.summary.fastestComponent = `${fastestComponent} (${fastestTime.toFixed(2)}ms)`
    
    // Determine performance grade
    const avgTime = performanceReport.summary.averageRenderTime
    if (avgTime < 30) {
      performanceReport.summary.performanceGrade = 'A+'
    } else if (avgTime < 50) {
      performanceReport.summary.performanceGrade = 'A'
    } else if (avgTime < 80) {
      performanceReport.summary.performanceGrade = 'B'
    } else if (avgTime < 120) {
      performanceReport.summary.performanceGrade = 'C'
    } else {
      performanceReport.summary.performanceGrade = 'D'
    }
    
    // Generate recommendations
    if (slowestTime > 100) {
      performanceReport.recommendations.push(`Optimize ${slowestComponent} component rendering (${slowestTime.toFixed(2)}ms)`)
    }
    
    if (avgTime > 60) {
      performanceReport.recommendations.push('Consider implementing React.memo for expensive components')
    }
    
    if (totalRenderTime > 500) {
      performanceReport.recommendations.push('Implement component lazy loading for better initial page performance')
    }
    
    performanceReport.recommendations.push('Implement performance monitoring in production environment')
    performanceReport.recommendations.push('Add performance budget to CI/CD pipeline')
    
    console.log('🎯 Performance Report Generated:', performanceReport)
    
    // Performance assertions
    expect(performanceReport.summary.averageRenderTime).toBeLessThan(100) // Average should be <100ms
    expect(performanceReport.summary.performanceGrade).toMatch(/^[A-C]/) // Should be A, B, or C grade
    expect(totalTests).toBeGreaterThanOrEqual(6) // Should test at least 6 components
    
    // Log final performance summary
    console.log(`
    📊 PERFORMANCE BENCHMARK SUMMARY:
    ===================================
    Total Components Tested: ${totalTests}
    Average Render Time: ${avgTime.toFixed(2)}ms
    Performance Grade: ${performanceReport.summary.performanceGrade}
    Slowest Component: ${performanceReport.summary.slowestComponent}
    Fastest Component: ${performanceReport.summary.fastestComponent}
    
    🎯 Recommendations:
    ${performanceReport.recommendations.map(rec => `• ${rec}`).join('\n    ')}
    `)
  })
})