/**
 * React DevTools Profiler Integration and Performance Analysis
 */

import React from 'react'

export interface ProfilerData {
  id: string
  phase: 'mount' | 'update'
  actualDuration: number
  baseDuration: number
  startTime: number
  commitTime: number
  interactions: Set<any>
}

export interface ComponentProfile {
  componentId: string
  totalRenders: number
  totalDuration: number
  averageDuration: number
  slowestRender: number
  fastestRender: number
  lastRenderTime: number
  mountTime?: number
  isSlowComponent: boolean
  renderPhases: Array<{
    phase: 'mount' | 'update'
    duration: number
    timestamp: number
  }>
}

export interface PerformanceReport {
  reportId: string
  timestamp: number
  totalComponents: number
  slowComponents: ComponentProfile[]
  averageRenderTime: number
  totalRenderTime: number
  interactionsSummary: InteractionSummary[]
  recommendations: PerformanceRecommendation[]
}

export interface InteractionSummary {
  name: string
  timestamp: number
  duration: number
  componentsAffected: string[]
}

export interface PerformanceRecommendation {
  type: 'optimization' | 'warning' | 'info'
  componentId: string
  issue: string
  recommendation: string
  impact: 'high' | 'medium' | 'low'
  estimatedImprovement: string
}

// Performance thresholds (in milliseconds)
export const PERFORMANCE_THRESHOLDS = {
  SLOW_RENDER: 16, // 60fps threshold
  VERY_SLOW_RENDER: 33, // 30fps threshold
  CRITICAL_RENDER: 100, // Noticeable lag
  MOUNT_THRESHOLD: 50, // Slow mount
  UPDATE_THRESHOLD: 16 // Slow update
} as const

// Global profiler state
class ReactDevToolsProfiler {
  private profiles = new Map<string, ComponentProfile>()
  private isEnabled: boolean
  private reportCallbacks = new Set<(report: PerformanceReport) => void>()
  private interactions = new Map<string, InteractionSummary>()

  constructor() {
    this.isEnabled = process.env.NODE_ENV === 'development'
    this.setupDevToolsIntegration()
  }

  private setupDevToolsIntegration() {
    if (!this.isEnabled || typeof window === 'undefined') return

    // Integration with React DevTools Performance tab
    if ('__REACT_DEVTOOLS_GLOBAL_HOOK__' in window) {
      const devTools = (window as any).__REACT_DEVTOOLS_GLOBAL_HOOK__
      
      // Listen for profiler events
      if (devTools.onCommitFiberRoot) {
        const originalOnCommit = devTools.onCommitFiberRoot
        devTools.onCommitFiberRoot = (...args: any[]) => {
          this.handleCommit(...args)
          return originalOnCommit.call(devTools, ...args)
        }
      }
    }
  }

  private handleCommit(id: string, root: any, priorityLevel: any) {
    // This would be called on each React commit
    // In a real implementation, we'd extract performance data from the fiber tree
    console.log('React commit detected:', { id, priorityLevel })
  }

  public onRender = (
    id: string,
    phase: 'mount' | 'update',
    actualDuration: number,
    baseDuration: number,
    startTime: number,
    commitTime: number,
    interactions: Set<any>
  ) => {
    if (!this.isEnabled) return

    const data: ProfilerData = {
      id,
      phase,
      actualDuration,
      baseDuration,
      startTime,
      commitTime,
      interactions
    }

    this.recordProfile(data)
    this.analyzeInteractions(interactions, id, actualDuration)
  }

  private recordProfile(data: ProfilerData) {
    const existing = this.profiles.get(data.id)
    
    if (existing) {
      // Update existing profile
      existing.totalRenders++
      existing.totalDuration += data.actualDuration
      existing.averageDuration = existing.totalDuration / existing.totalRenders
      existing.slowestRender = Math.max(existing.slowestRender, data.actualDuration)
      existing.fastestRender = Math.min(existing.fastestRender, data.actualDuration)
      existing.lastRenderTime = data.commitTime
      existing.isSlowComponent = data.actualDuration > PERFORMANCE_THRESHOLDS.SLOW_RENDER
      
      existing.renderPhases.push({
        phase: data.phase,
        duration: data.actualDuration,
        timestamp: data.commitTime
      })

      // Keep only last 100 render phases
      if (existing.renderPhases.length > 100) {
        existing.renderPhases = existing.renderPhases.slice(-100)
      }
    } else {
      // Create new profile
      const profile: ComponentProfile = {
        componentId: data.id,
        totalRenders: 1,
        totalDuration: data.actualDuration,
        averageDuration: data.actualDuration,
        slowestRender: data.actualDuration,
        fastestRender: data.actualDuration,
        lastRenderTime: data.commitTime,
        mountTime: data.phase === 'mount' ? data.commitTime : undefined,
        isSlowComponent: data.actualDuration > PERFORMANCE_THRESHOLDS.SLOW_RENDER,
        renderPhases: [{
          phase: data.phase,
          duration: data.actualDuration,
          timestamp: data.commitTime
        }]
      }

      this.profiles.set(data.id, profile)
    }

    // Generate recommendations for slow renders
    if (data.actualDuration > PERFORMANCE_THRESHOLDS.VERY_SLOW_RENDER) {
      this.generateWarning(data)
    }
  }

  private analyzeInteractions(interactions: Set<any>, componentId: string, duration: number) {
    interactions.forEach(interaction => {
      const name = interaction.name || 'unknown'
      const existing = this.interactions.get(name)
      
      if (existing) {
        existing.duration += duration
        if (!existing.componentsAffected.includes(componentId)) {
          existing.componentsAffected.push(componentId)
        }
      } else {
        this.interactions.set(name, {
          name,
          timestamp: Date.now(),
          duration,
          componentsAffected: [componentId]
        })
      }
    })
  }

  private generateWarning(data: ProfilerData) {
    if (process.env.NODE_ENV === 'development') {
      console.warn(`= Slow render detected in "${data.id}":`, {
        phase: data.phase,
        duration: `${data.actualDuration.toFixed(2)}ms`,
        threshold: `${PERFORMANCE_THRESHOLDS.SLOW_RENDER}ms`,
        suggestion: 'Consider using React.memo() or optimizing render logic'
      })
    }
  }

  public generateReport(): PerformanceReport {
    const profiles = Array.from(this.profiles.values())
    const slowComponents = profiles
      .filter(p => p.isSlowComponent)
      .sort((a, b) => b.averageDuration - a.averageDuration)

    const totalRenderTime = profiles.reduce((sum, p) => sum + p.totalDuration, 0)
    const totalRenders = profiles.reduce((sum, p) => sum + p.totalRenders, 0)
    const averageRenderTime = totalRenders > 0 ? totalRenderTime / totalRenders : 0

    const recommendations = this.generateRecommendations(profiles)

    return {
      reportId: `report-${Date.now()}`,
      timestamp: Date.now(),
      totalComponents: profiles.length,
      slowComponents,
      averageRenderTime,
      totalRenderTime,
      interactionsSummary: Array.from(this.interactions.values()),
      recommendations
    }
  }

  private generateRecommendations(profiles: ComponentProfile[]): PerformanceRecommendation[] {
    const recommendations: PerformanceRecommendation[] = []

    profiles.forEach(profile => {
      // Slow average render time
      if (profile.averageDuration > PERFORMANCE_THRESHOLDS.SLOW_RENDER) {
        recommendations.push({
          type: 'optimization',
          componentId: profile.componentId,
          issue: `Average render time is ${profile.averageDuration.toFixed(2)}ms`,
          recommendation: 'Consider using React.memo() to prevent unnecessary re-renders',
          impact: profile.averageDuration > PERFORMANCE_THRESHOLDS.VERY_SLOW_RENDER ? 'high' : 'medium',
          estimatedImprovement: `Could reduce render time by 30-70%`
        })
      }

      // Frequent re-renders
      if (profile.totalRenders > 50) {
        const recentRenders = profile.renderPhases.slice(-10)
        const recentUpdates = recentRenders.filter(r => r.phase === 'update').length
        
        if (recentUpdates > 7) {
          recommendations.push({
            type: 'warning',
            componentId: profile.componentId,
            issue: `Component re-renders very frequently (${recentUpdates}/10 recent renders were updates)`,
            recommendation: 'Check for unnecessary state updates or props changes. Consider useMemo/useCallback.',
            impact: 'medium',
            estimatedImprovement: 'Could reduce render frequency by 50-80%'
          })
        }
      }

      // Slow mount
      if (profile.mountTime && profile.renderPhases[0]?.duration > PERFORMANCE_THRESHOLDS.MOUNT_THRESHOLD) {
        recommendations.push({
          type: 'optimization',
          componentId: profile.componentId,
          issue: `Component mount time is slow (${profile.renderPhases[0].duration.toFixed(2)}ms)`,
          recommendation: 'Consider lazy loading or splitting this component',
          impact: 'medium',
          estimatedImprovement: 'Could improve initial load time'
        })
      }

      // Inconsistent render times
      const variance = profile.slowestRender - profile.fastestRender
      if (variance > PERFORMANCE_THRESHOLDS.SLOW_RENDER * 2) {
        recommendations.push({
          type: 'info',
          componentId: profile.componentId,
          issue: `Inconsistent render times (${profile.fastestRender.toFixed(2)}ms - ${profile.slowestRender.toFixed(2)}ms)`,
          recommendation: 'Profile render conditions to identify performance bottlenecks',
          impact: 'low',
          estimatedImprovement: 'Better understanding of performance characteristics'
        })
      }
    })

    return recommendations.sort((a, b) => {
      const impactWeight = { high: 3, medium: 2, low: 1 }
      return impactWeight[b.impact] - impactWeight[a.impact]
    })
  }

  public addReportCallback(callback: (report: PerformanceReport) => void) {
    this.reportCallbacks.add(callback)
  }

  public removeReportCallback(callback: (report: PerformanceReport) => void) {
    this.reportCallbacks.delete(callback)
  }

  public clear() {
    this.profiles.clear()
    this.interactions.clear()
  }

  public getProfile(componentId: string): ComponentProfile | undefined {
    return this.profiles.get(componentId)
  }

  public getAllProfiles(): ComponentProfile[] {
    return Array.from(this.profiles.values())
  }

  public isProfilerEnabled(): boolean {
    return this.isEnabled
  }
}

// Global profiler instance
export const reactDevToolsProfiler = new ReactDevToolsProfiler()

// React Profiler wrapper component
export const PerformanceProfiler: React.FC<{
  id: string
  children: React.ReactNode
  onRender?: (data: ProfilerData) => void
}> = ({ id, children, onRender }) => {
  const handleRender = React.useCallback((
    id: string,
    phase: 'mount' | 'update',
    actualDuration: number,
    baseDuration: number,
    startTime: number,
    commitTime: number,
    interactions: Set<any>
  ) => {
    const data: ProfilerData = {
      id,
      phase,
      actualDuration,
      baseDuration,
      startTime,
      commitTime,
      interactions
    }

    reactDevToolsProfiler.onRender(
      id,
      phase,
      actualDuration,
      baseDuration,
      startTime,
      commitTime,
      interactions
    )

    onRender?.(data)
  }, [onRender])

  if (process.env.NODE_ENV !== 'development') {
    return <>{children}</>
  }

  return (
    <React.Profiler id={id} onRender={handleRender}>
      {children}
    </React.Profiler>
  )
}

// HOC for automatic profiling
export const withProfiler = <P extends object>(
  Component: React.ComponentType<P>,
  profileId?: string
) => {
  const WrappedComponent = React.forwardRef<any, P>((props, ref) => {
    const id = profileId || Component.displayName || Component.name || 'Unknown'
    
    return (
      <PerformanceProfiler id={id}>
        <Component {...props} ref={ref} />
      </PerformanceProfiler>
    )
  })

  WrappedComponent.displayName = `withProfiler(${Component.displayName || Component.name})`
  
  return WrappedComponent
}

// Hook for component performance monitoring
export const useComponentProfiler = (componentId: string) => {
  const [profile, setProfile] = React.useState<ComponentProfile | undefined>()

  React.useEffect(() => {
    const updateProfile = () => {
      const currentProfile = reactDevToolsProfiler.getProfile(componentId)
      setProfile(currentProfile)
    }

    updateProfile()
    
    const interval = setInterval(updateProfile, 1000)
    return () => clearInterval(interval)
  }, [componentId])

  return {
    profile,
    isSlowComponent: profile?.isSlowComponent || false,
    averageRenderTime: profile?.averageDuration || 0,
    totalRenders: profile?.totalRenders || 0
  }
}

// Hook for performance reporting
export const usePerformanceReport = () => {
  const [report, setReport] = React.useState<PerformanceReport | null>(null)
  const [isGenerating, setIsGenerating] = React.useState(false)

  const generateReport = React.useCallback(async () => {
    setIsGenerating(true)
    try {
      await new Promise(resolve => setTimeout(resolve, 100)) // Small delay for UX
      const newReport = reactDevToolsProfiler.generateReport()
      setReport(newReport)
    } finally {
      setIsGenerating(false)
    }
  }, [])

  React.useEffect(() => {
    const callback = (newReport: PerformanceReport) => {
      setReport(newReport)
    }

    reactDevToolsProfiler.addReportCallback(callback)
    return () => reactDevToolsProfiler.removeReportCallback(callback)
  }, [])

  return {
    report,
    isGenerating,
    generateReport,
    clear: () => {
      reactDevToolsProfiler.clear()
      setReport(null)
    }
  }
}

// Performance measurement utilities
export const measureRender = async <T>(
  renderFn: () => T,
  componentId: string
): Promise<{ result: T; duration: number }> => {
  const start = performance.now()
  const result = renderFn()
  const end = performance.now()
  const duration = end - start

  if (duration > PERFORMANCE_THRESHOLDS.SLOW_RENDER) {
    console.warn(`Slow render in ${componentId}: ${duration.toFixed(2)}ms`)
  }

  return { result, duration }
}

// DevTools profiler commands (for browser console)
if (typeof window !== 'undefined' && process.env.NODE_ENV === 'development') {
  (window as any).__REACT_PROFILER__ = {
    generateReport: () => reactDevToolsProfiler.generateReport(),
    getProfile: (id: string) => reactDevToolsProfiler.getProfile(id),
    getAllProfiles: () => reactDevToolsProfiler.getAllProfiles(),
    clear: () => reactDevToolsProfiler.clear(),
    isEnabled: () => reactDevToolsProfiler.isProfilerEnabled()
  }

  console.log('=€ React Profiler available at window.__REACT_PROFILER__')
}