import React from 'react'

/**
 * Feature Flags System for Experimental Features
 */

export interface FeatureConfig {
  enabled: boolean
  rolloutPercentage?: number
  userGroups?: string[]
  environment?: ('development' | 'staging' | 'production')[]
  startDate?: string
  endDate?: string
  dependencies?: string[]
  metadata?: Record<string, any>
}

export interface FeatureFlagContextValue {
  features: Record<string, FeatureConfig>
  isFeatureEnabled: (featureName: string, userId?: string, userGroup?: string) => boolean
  enableFeature: (featureName: string) => void
  disableFeature: (featureName: string) => void
  setFeatureConfig: (featureName: string, config: FeatureConfig) => void
  getFeatureConfig: (featureName: string) => FeatureConfig | undefined
}

// Default feature configurations
const DEFAULT_FEATURES: Record<string, FeatureConfig> = {
  'ai-assistant': {
    enabled: process.env.NODE_ENV === 'development',
    rolloutPercentage: 10,
    userGroups: ['beta-testers', 'developers'],
    environment: ['development', 'staging'],
    metadata: {
      description: 'AI-powered assistant for user guidance',
      owner: 'AI Team',
      status: 'alpha'
    }
  },
  'smart-search': {
    enabled: true,
    rolloutPercentage: 50,
    userGroups: ['premium-users', 'beta-testers'],
    environment: ['development', 'staging', 'production'],
    metadata: {
      description: 'Enhanced search with ML-powered suggestions',
      owner: 'Search Team',
      status: 'beta'
    }
  },
  'wasm-features': {
    enabled: false,
    rolloutPercentage: 5,
    userGroups: ['developers'],
    environment: ['development'],
    metadata: {
      description: 'WebAssembly-powered performance features',
      owner: 'Performance Team',
      status: 'experimental'
    }
  },
  'streaming-data': {
    enabled: process.env.NODE_ENV === 'development',
    rolloutPercentage: 25,
    userGroups: ['beta-testers', 'power-users'],
    environment: ['development', 'staging'],
    metadata: {
      description: 'Real-time streaming data components',
      owner: 'Data Team',
      status: 'beta'
    }
  },
  'advanced-ui': {
    enabled: false,
    rolloutPercentage: 1,
    userGroups: ['developers'],
    environment: ['development'],
    metadata: {
      description: 'Experimental UI patterns (VR, AR, Gesture)',
      owner: 'UI Innovation Team',
      status: 'experimental'
    }
  }
}

// Feature Flag Context
const FeatureFlagContext = React.createContext<FeatureFlagContextValue | null>(null)

// Feature Flag Provider
export const FeatureFlagProvider: React.FC<{
  children: React.ReactNode
  initialFeatures?: Record<string, FeatureConfig>
  userId?: string
  userGroup?: string
}> = ({ children, initialFeatures = {}, userId, userGroup }) => {
  const [features, setFeatures] = React.useState<Record<string, FeatureConfig>>(() => ({
    ...DEFAULT_FEATURES,
    ...initialFeatures
  }))

  // Hash function for consistent user-based rollouts
  const hashUserId = React.useCallback((userId: string, featureName: string): number => {
    let hash = 0
    const str = `${userId}-${featureName}`
    for (let i = 0; i < str.length; i++) {
      const char = str.charCodeAt(i)
      hash = ((hash << 5) - hash) + char
      hash = hash & hash // Convert to 32bit integer
    }
    return Math.abs(hash) % 100
  }, [])

  // Check if feature is enabled for current user
  const isFeatureEnabled = React.useCallback((
    featureName: string, 
    currentUserId?: string, 
    currentUserGroup?: string
  ): boolean => {
    const feature = features[featureName]
    if (!feature) return false

    // Basic enabled check
    if (!feature.enabled) return false

    // Environment check
    const currentEnv = process.env.NODE_ENV as 'development' | 'staging' | 'production'
    if (feature.environment && !feature.environment.includes(currentEnv)) {
      return false
    }

    // Date range check
    const now = new Date()
    if (feature.startDate && new Date(feature.startDate) > now) return false
    if (feature.endDate && new Date(feature.endDate) < now) return false

    // Dependency check
    if (feature.dependencies) {
      const allDependenciesMet = feature.dependencies.every(dep => 
        isFeatureEnabled(dep, currentUserId, currentUserGroup)
      )
      if (!allDependenciesMet) return false
    }

    // User group check
    const targetUserGroup = currentUserGroup || userGroup
    if (feature.userGroups && targetUserGroup) {
      if (feature.userGroups.includes(targetUserGroup)) return true
    }

    // Rollout percentage check (user-based for consistency)
    if (feature.rolloutPercentage !== undefined) {
      const targetUserId = currentUserId || userId
      if (targetUserId) {
        const userHash = hashUserId(targetUserId, featureName)
        return userHash < feature.rolloutPercentage
      } else {
        // Random rollout if no user ID
        return Math.random() * 100 < feature.rolloutPercentage
      }
    }

    return true
  }, [features, userId, userGroup, hashUserId])

  const enableFeature = React.useCallback((featureName: string) => {
    setFeatures(prev => ({
      ...prev,
      [featureName]: {
        ...prev[featureName],
        enabled: true
      }
    }))
  }, [])

  const disableFeature = React.useCallback((featureName: string) => {
    setFeatures(prev => ({
      ...prev,
      [featureName]: {
        ...prev[featureName],
        enabled: false
      }
    }))
  }, [])

  const setFeatureConfig = React.useCallback((featureName: string, config: FeatureConfig) => {
    setFeatures(prev => ({
      ...prev,
      [featureName]: config
    }))
  }, [])

  const getFeatureConfig = React.useCallback((featureName: string) => {
    return features[featureName]
  }, [features])

  const value: FeatureFlagContextValue = {
    features,
    isFeatureEnabled,
    enableFeature,
    disableFeature,
    setFeatureConfig,
    getFeatureConfig
  }

  return (
    <FeatureFlagContext.Provider value={value}>
      {children}
    </FeatureFlagContext.Provider>
  )
}

// Hook to use feature flags
export const useFeatureFlags = (): FeatureFlagContextValue => {
  const context = React.useContext(FeatureFlagContext)
  if (!context) {
    throw new Error('useFeatureFlags must be used within a FeatureFlagProvider')
  }
  return context
}

// Hook to check if a specific feature is enabled
export const useExperimentalFeature = (
  featureName: string, 
  userId?: string, 
  userGroup?: string
): boolean => {
  const { isFeatureEnabled } = useFeatureFlags()
  return isFeatureEnabled(featureName, userId, userGroup)
}

// Component to conditionally render based on feature flags
export const FeatureFlag: React.FC<{
  feature: string
  children: React.ReactNode
  fallback?: React.ReactNode
  userId?: string
  userGroup?: string
}> = ({ feature, children, fallback = null, userId, userGroup }) => {
  const isEnabled = useExperimentalFeature(feature, userId, userGroup)
  
  return isEnabled ? <>{children}</> : <>{fallback}</>
}

// HOC for feature-gated components
export const withFeatureFlag = <P extends object>(
  Component: React.ComponentType<P>,
  featureName: string,
  fallback?: React.ComponentType<P>
) => {
  const WrappedComponent = React.forwardRef<any, P>((props, ref) => {
    const isEnabled = useExperimentalFeature(featureName)
    
    if (isEnabled) {
      return <Component {...props} ref={ref} />
    }
    
    if (fallback) {
      return <fallback {...props} ref={ref} />
    }
    
    return null
  })

  WrappedComponent.displayName = `withFeatureFlag(${Component.displayName || Component.name})`
  
  return WrappedComponent
}

// Development tools for feature flags
export const FeatureFlagDevTools: React.FC = () => {
  const { features, enableFeature, disableFeature, isFeatureEnabled } = useFeatureFlags()

  if (process.env.NODE_ENV !== 'development') return null

  return (
    <div className="fixed bottom-4 right-4 bg-white border rounded-lg shadow-lg p-4 max-w-sm">
      <h3 className="text-sm font-semibold mb-2">Feature Flags</h3>
      <div className="space-y-2 max-h-64 overflow-y-auto">
        {Object.entries(features).map(([name, config]) => {
          const enabled = isFeatureEnabled(name)
          return (
            <div key={name} className="flex items-center justify-between text-xs">
              <span className="flex-1 truncate" title={config.metadata?.description}>
                {name}
              </span>
              <button
                onClick={() => enabled ? disableFeature(name) : enableFeature(name)}
                className={`px-2 py-1 rounded text-xs ${
                  enabled 
                    ? 'bg-green-100 text-green-800' 
                    : 'bg-gray-100 text-gray-600'
                }`}
              >
                {enabled ? 'ON' : 'OFF'}
              </button>
            </div>
          )
        })}
      </div>
    </div>
  )
}

// Feature analytics tracking
export const useFeatureAnalytics = () => {
  const { features } = useFeatureFlags()
  
  const trackFeatureUsage = React.useCallback((featureName: string, action: string, metadata?: any) => {
    if (process.env.NODE_ENV === 'development') {
      console.log('Feature analytics:', { featureName, action, metadata })
    }
    
    // In production, send to analytics service
    // analytics.track('feature_usage', { feature: featureName, action, metadata })
  }, [])

  const trackFeatureError = React.useCallback((featureName: string, error: Error) => {
    console.error(`Feature ${featureName} error:`, error)
    
    // Track feature-specific errors
    // analytics.track('feature_error', { feature: featureName, error: error.message })
  }, [])

  return {
    trackFeatureUsage,
    trackFeatureError,
    availableFeatures: Object.keys(features)
  }
}

// A/B testing utilities
export const useABTest = (testName: string, variants: string[], userId?: string) => {
  const hashUser = React.useCallback((userId: string, testName: string): number => {
    let hash = 0
    const str = `${userId}-${testName}`
    for (let i = 0; i < str.length; i++) {
      const char = str.charCodeAt(i)
      hash = ((hash << 5) - hash) + char
      hash = hash & hash
    }
    return Math.abs(hash) % variants.length
  }, [variants.length])

  const variant = React.useMemo(() => {
    if (!userId) {
      return variants[Math.floor(Math.random() * variants.length)]
    }
    
    const index = hashUser(userId, testName)
    return variants[index]
  }, [userId, testName, variants, hashUser])

  return variant
}