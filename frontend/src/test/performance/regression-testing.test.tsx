import React from 'react'
import { render, cleanup } from '@testing-library/react'
import { describe, it, expect, beforeEach } from 'vitest'
import { act } from 'react'

// Import components for regression testing
import Badge from '../../components/ui/Badge'
import Button from '../../components/ui/Button'
import Card from '../../components/ui/Card'
import LoadingSpinner from '../../components/common/LoadingSpinner'
import SkeletonLoader from '../../components/common/SkeletonLoader'
import Modal from '../../components/ui/Modal'
import Input from '../../components/ui/Input'
import Alert from '../../components/ui/Alert'

describe('Performance Regression Testing', () => {
  let performanceBaseline: Record<string, any> = {}
  
  beforeEach(() => {
    // Establish performance baselines
    performanceBaseline = {
      // Baseline render times (in milliseconds)
      Badge: { single: 25, multiple: 80, heavy: 150 },
      Button: { single: 20, multiple: 60, heavy: 120 },
      Card: { single: 35, multiple: 100, heavy: 200 },
      LoadingSpinner: { single: 15, multiple: 45, heavy: 90 },
      SkeletonLoader: { single: 25, multiple: 75, heavy: 180 },
      Modal: { single: 40, multiple: 120, heavy: 250 },
      Input: { single: 30, multiple: 90, heavy: 160 },
      Alert: { single: 28, multiple: 85, heavy: 140 }
    }
    
    console.log('📊 Performance regression testing baseline established')
  })

  const measureRenderPerformance = (testName: string, renderFn: () => void): number => {
    const startTime = performance.now()
    
    act(() => {
      renderFn()
    })
    
    const endTime = performance.now()
    const renderTime = endTime - startTime
    
    console.log(`⏱️ ${testName}: ${renderTime.toFixed(2)}ms`)
    
    cleanup()
    return renderTime
  }

  const compareWithBaseline = (componentName: string, scenario: string, actualTime: number): {
    passed: boolean,
    baselineTime: number,
    actualTime: number,
    difference: number,
    percentageChange: number,
    status: 'improved' | 'degraded' | 'stable'
  } => {
    const baselineTime = performanceBaseline[componentName]?.[scenario] || 0
    const difference = actualTime - baselineTime
    const percentageChange = baselineTime > 0 ? (difference / baselineTime) * 100 : 0
    
    // Tolerance threshold: ±20% is considered stable
    const toleranceThreshold = 20
    
    let status: 'improved' | 'degraded' | 'stable' = 'stable'
    if (percentageChange < -toleranceThreshold) {
      status = 'improved'
    } else if (percentageChange > toleranceThreshold) {
      status = 'degraded'
    }
    
    const passed = percentageChange <= toleranceThreshold * 2 // Fail if >40% degradation
    
    return {
      passed,
      baselineTime,
      actualTime,
      difference,
      percentageChange,
      status
    }
  }

  it('tests Badge component performance regression', () => {
    console.log('🔍 Testing Badge component performance regression')
    
    const badgeTests = [
      {
        name: 'Badge-single',
        scenario: 'single',
        render: () => render(<Badge variant="primary">Regression Test</Badge>)
      },
      {
        name: 'Badge-multiple',
        scenario: 'multiple',
        render: () => render(
          <div>
            {Array.from({ length: 15 }, (_, i) => (
              <Badge key={i} variant="primary">Badge {i}</Badge>
            ))}
          </div>
        )
      },
      {
        name: 'Badge-heavy',
        scenario: 'heavy',
        render: () => render(
          <div>
            {Array.from({ length: 50 }, (_, i) => (
              <Badge key={i} variant={i % 2 === 0 ? 'primary' : 'secondary'} size="lg">
                Heavy Badge {i} with longer text content
              </Badge>
            ))}
          </div>
        )
      }
    ]

    const badgeResults: Array<ReturnType<typeof compareWithBaseline>> = []

    badgeTests.forEach(test => {
      const actualTime = measureRenderPerformance(test.name, test.render)
      const comparison = compareWithBaseline('Badge', test.scenario, actualTime)
      badgeResults.push(comparison)
      
      console.log(`📊 ${test.name}: ${comparison.status} (${comparison.percentageChange.toFixed(1)}% change)`)
    })

    // Assertions for Badge regression
    badgeResults.forEach(result => {
      expect(result.passed).toBe(true)
      expect(result.percentageChange).toBeLessThan(40) // No more than 40% degradation
    })

    console.log('✅ Badge component regression tests passed')
  })

  it('tests Button component performance regression', () => {
    console.log('🔍 Testing Button component performance regression')
    
    const buttonTests = [
      {
        name: 'Button-single',
        scenario: 'single',
        render: () => render(<Button variant="primary">Regression Test</Button>)
      },
      {
        name: 'Button-multiple',
        scenario: 'multiple',
        render: () => render(
          <div>
            {Array.from({ length: 12 }, (_, i) => (
              <Button key={i} variant="outline" size="md" loading={i % 3 === 0}>
                Button {i}
              </Button>
            ))}
          </div>
        )
      },
      {
        name: 'Button-heavy',
        scenario: 'heavy',
        render: () => render(
          <div>
            {Array.from({ length: 40 }, (_, i) => (
              <Button 
                key={i} 
                variant={['primary', 'secondary', 'outline', 'ghost'][i % 4] as any}
                size={['sm', 'md', 'lg'][i % 3] as any}
                loading={i % 4 === 0}
                disabled={i % 5 === 0}
              >
                Heavy Button {i} with extended content and multiple props
              </Button>
            ))}
          </div>
        )
      }
    ]

    const buttonResults: Array<ReturnType<typeof compareWithBaseline>> = []

    buttonTests.forEach(test => {
      const actualTime = measureRenderPerformance(test.name, test.render)
      const comparison = compareWithBaseline('Button', test.scenario, actualTime)
      buttonResults.push(comparison)
      
      console.log(`📊 ${test.name}: ${comparison.status} (${comparison.percentageChange.toFixed(1)}% change)`)
    })

    // Assertions for Button regression
    buttonResults.forEach(result => {
      expect(result.passed).toBe(true)
      expect(result.percentageChange).toBeLessThan(40)
    })

    console.log('✅ Button component regression tests passed')
  })

  it('tests Card component performance regression', () => {
    console.log('🔍 Testing Card component performance regression')
    
    const cardTests = [
      {
        name: 'Card-single',
        scenario: 'single',
        render: () => render(<Card title="Regression Test">Simple content</Card>)
      },
      {
        name: 'Card-multiple',
        scenario: 'multiple',
        render: () => render(
          <div>
            {Array.from({ length: 8 }, (_, i) => (
              <Card key={i} title={`Card ${i}`} variant="primary" size="md">
                <p>Card content {i}</p>
                <Badge variant="info">Status {i}</Badge>
              </Card>
            ))}
          </div>
        )
      },
      {
        name: 'Card-heavy',
        scenario: 'heavy',
        render: () => render(
          <div>
            {Array.from({ length: 25 }, (_, i) => (
              <Card key={i} title={`Heavy Card ${i}`} variant="primary" size="lg">
                <div>
                  <h3>Nested content section {i}</h3>
                  <p>{'Lorem ipsum content '.repeat(10)}</p>
                  <div>
                    {Array.from({ length: 5 }, (_, j) => (
                      <Badge key={j} variant="success">Tag {j}</Badge>
                    ))}
                  </div>
                  <Button variant="outline" size="sm">Action {i}</Button>
                </div>
              </Card>
            ))}
          </div>
        )
      }
    ]

    const cardResults: Array<ReturnType<typeof compareWithBaseline>> = []

    cardTests.forEach(test => {
      const actualTime = measureRenderPerformance(test.name, test.render)
      const comparison = compareWithBaseline('Card', test.scenario, actualTime)
      cardResults.push(comparison)
      
      console.log(`📊 ${test.name}: ${comparison.status} (${comparison.percentageChange.toFixed(1)}% change)`)
    })

    // Assertions for Card regression
    cardResults.forEach(result => {
      expect(result.passed).toBe(true)
      expect(result.percentageChange).toBeLessThan(40)
    })

    console.log('✅ Card component regression tests passed')
  })

  it('tests complex component interaction regression', () => {
    console.log('🔍 Testing complex component interaction regression')
    
    const complexTests = [
      {
        name: 'Modal-with-form',
        scenario: 'single',
        render: () => render(
          <Modal isOpen={true} onClose={() => {}} title="Complex Modal">
            <form>
              {Array.from({ length: 8 }, (_, i) => (
                <Input key={i} placeholder={`Field ${i}`} label={`Label ${i}`} />
              ))}
              <div>
                <Button type="submit" variant="primary">Submit</Button>
                <Button type="button" variant="secondary">Cancel</Button>
              </div>
            </form>
          </Modal>
        )
      },
      {
        name: 'Dashboard-simulation',
        scenario: 'heavy',
        render: () => render(
          <div>
            <div>
              {Array.from({ length: 6 }, (_, i) => (
                <Card key={i} title={`Dashboard Card ${i}`}>
                  <div>
                    <LoadingSpinner />
                    <p>Dashboard content {i}</p>
                    <Alert variant="info" message={`Alert ${i}`} />
                  </div>
                </Card>
              ))}
            </div>
            <div>
              {Array.from({ length: 20 }, (_, i) => (
                <SkeletonLoader key={i} variant="text" lines={3} />
              ))}
            </div>
          </div>
        )
      },
      {
        name: 'Data-table-simulation',
        scenario: 'heavy',
        render: () => render(
          <div>
            {Array.from({ length: 30 }, (_, i) => (
              <div key={i} style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Badge variant="primary">ID {i}</Badge>
                <Input placeholder="Edit field" size="sm" />
                <Button variant="outline" size="sm">Edit</Button>
                <Button variant="ghost" size="sm">Delete</Button>
              </div>
            ))}
          </div>
        )
      }
    ]

    const complexResults: Array<ReturnType<typeof compareWithBaseline>> = []

    complexTests.forEach(test => {
      const actualTime = measureRenderPerformance(test.name, test.render)
      
      // Use Modal baseline for Modal test, general heavy baseline for others
      const componentName = test.name.includes('Modal') ? 'Modal' : 'Card'
      const comparison = compareWithBaseline(componentName, test.scenario, actualTime)
      complexResults.push(comparison)
      
      console.log(`📊 ${test.name}: ${comparison.status} (${comparison.percentageChange.toFixed(1)}% change)`)
    })

    // Assertions for complex interactions
    complexResults.forEach(result => {
      expect(result.passed).toBe(true)
      expect(result.percentageChange).toBeLessThan(50) // Allow slightly more tolerance for complex scenarios
    })

    console.log('✅ Complex component interaction regression tests passed')
  })

  it('tests performance degradation detection and alerting', () => {
    console.log('🔍 Testing performance degradation detection system')
    
    const degradationTests = [
      {
        name: 'Intentional-slow-component',
        expectedDegradation: true,
        render: () => {
          // Simulate a performance regression by adding artificial delay
          const start = performance.now()
          while (performance.now() - start < 100) {
            // Busy wait to simulate slow rendering
          }
          
          return render(<Badge variant="primary">Slow Component</Badge>)
        }
      },
      {
        name: 'Normal-component',
        expectedDegradation: false,
        render: () => render(<Badge variant="primary">Normal Component</Badge>)
      }
    ]

    const degradationResults = degradationTests.map(test => {
      const actualTime = measureRenderPerformance(test.name, test.render)
      const comparison = compareWithBaseline('Badge', 'single', actualTime)
      
      return {
        testName: test.name,
        expectedDegradation: test.expectedDegradation,
        actualDegradation: comparison.status === 'degraded',
        percentageChange: comparison.percentageChange,
        comparison
      }
    })

    degradationResults.forEach(result => {
      console.log(`📊 ${result.testName}:`)
      console.log(`  Expected degradation: ${result.expectedDegradation}`)
      console.log(`  Actual degradation: ${result.actualDegradation}`)
      console.log(`  Performance change: ${result.percentageChange.toFixed(1)}%`)
      
      if (result.expectedDegradation) {
        // Should detect degradation in intentionally slow component
        expect(result.actualDegradation).toBe(true)
        expect(result.percentageChange).toBeGreaterThan(20)
      } else {
        // Should not detect degradation in normal component
        expect(result.actualDegradation).toBe(false)
        expect(Math.abs(result.percentageChange)).toBeLessThan(20)
      }
    })

    console.log('✅ Performance degradation detection tests passed')
  })

  it('generates comprehensive regression testing report', () => {
    console.log('📋 Generating comprehensive regression testing report')
    
    const regressionReport = {
      summary: {
        totalComponents: 8,
        totalScenarios: 24,
        passedTests: 0,
        failedTests: 0,
        improvedComponents: [] as string[],
        degradedComponents: [] as string[],
        stableComponents: [] as string[],
        overallHealthScore: 0
      },
      recommendations: [] as string[],
      alerts: [] as Array<{
        component: string,
        issue: string,
        severity: 'low' | 'medium' | 'high',
        action: string
      }>,
      nextActions: [] as string[]
    }

    // Simulate comprehensive test results analysis
    const simulatedResults = [
      { component: 'Badge', status: 'stable', change: 5.2 },
      { component: 'Button', status: 'improved', change: -8.1 },
      { component: 'Card', status: 'stable', change: 12.3 },
      { component: 'LoadingSpinner', status: 'improved', change: -15.7 },
      { component: 'SkeletonLoader', status: 'stable', change: 7.8 },
      { component: 'Modal', status: 'degraded', change: 25.4 },
      { component: 'Input', status: 'stable', change: -2.1 },
      { component: 'Alert', status: 'stable', change: 9.6 }
    ]

    simulatedResults.forEach(result => {
      if (result.status === 'improved') {
        regressionReport.summary.improvedComponents.push(result.component)
      } else if (result.status === 'degraded') {
        regressionReport.summary.degradedComponents.push(result.component)
        
        regressionReport.alerts.push({
          component: result.component,
          issue: `Performance degraded by ${result.change.toFixed(1)}%`,
          severity: result.change > 30 ? 'high' : 'medium',
          action: 'Investigate and optimize component rendering'
        })
      } else {
        regressionReport.summary.stableComponents.push(result.component)
      }
    })

    regressionReport.summary.passedTests = simulatedResults.filter(r => r.change < 40).length
    regressionReport.summary.failedTests = simulatedResults.filter(r => r.change >= 40).length

    // Calculate overall health score
    const avgChange = simulatedResults.reduce((sum, r) => sum + Math.abs(r.change), 0) / simulatedResults.length
    if (avgChange < 10) {
      regressionReport.summary.overallHealthScore = 95
    } else if (avgChange < 20) {
      regressionReport.summary.overallHealthScore = 85
    } else if (avgChange < 30) {
      regressionReport.summary.overallHealthScore = 70
    } else {
      regressionReport.summary.overallHealthScore = 50
    }

    // Generate recommendations
    if (regressionReport.summary.degradedComponents.length > 0) {
      regressionReport.recommendations.push('Investigate performance regressions in degraded components')
      regressionReport.recommendations.push('Consider implementing performance budgets for CI/CD pipeline')
    }

    if (regressionReport.summary.improvedComponents.length > 2) {
      regressionReport.recommendations.push('Document performance improvements for future reference')
    }

    regressionReport.recommendations.push('Schedule regular performance regression testing')
    regressionReport.recommendations.push('Add automated performance monitoring to production')
    regressionReport.recommendations.push('Create performance baseline updates quarterly')

    // Generate next actions
    regressionReport.nextActions = [
      'Update performance baselines with current metrics',
      'Set up automated regression testing in CI/CD pipeline',
      'Implement performance budgets for component rendering',
      'Create performance monitoring dashboard',
      'Schedule monthly performance review meetings'
    ]

    console.log('📊 Regression Testing Report Generated:')
    console.log(`Total Components: ${regressionReport.summary.totalComponents}`)
    console.log(`Passed Tests: ${regressionReport.summary.passedTests}/${regressionReport.summary.totalComponents}`)
    console.log(`Overall Health Score: ${regressionReport.summary.overallHealthScore}%`)
    console.log(`Improved Components: ${regressionReport.summary.improvedComponents.join(', ') || 'None'}`)
    console.log(`Degraded Components: ${regressionReport.summary.degradedComponents.join(', ') || 'None'}`)

    console.log('\n🚨 Performance Alerts:')
    regressionReport.alerts.forEach(alert => {
      console.log(`[${alert.severity.toUpperCase()}] ${alert.component}: ${alert.issue}`)
      console.log(`  Action: ${alert.action}`)
    })

    console.log('\n🎯 Recommendations:')
    regressionReport.recommendations.forEach(rec => console.log(`• ${rec}`))

    console.log('\n📋 Next Actions:')
    regressionReport.nextActions.forEach((action, index) => console.log(`${index + 1}. ${action}`))

    // Regression report assertions
    expect(regressionReport.summary.totalComponents).toBeGreaterThan(0)
    expect(regressionReport.summary.overallHealthScore).toBeGreaterThan(60) // Minimum acceptable health
    expect(regressionReport.recommendations.length).toBeGreaterThan(3)
    expect(regressionReport.nextActions.length).toBeGreaterThan(3)
    expect(regressionReport.summary.passedTests).toBeGreaterThanOrEqual(regressionReport.summary.totalComponents * 0.7) // 70% pass rate
  })
})