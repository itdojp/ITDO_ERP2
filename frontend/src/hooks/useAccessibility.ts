import React from 'react'

export interface AccessibilityPreferences {
  reducedMotion: boolean
  highContrast: boolean
  fontSize: 'small' | 'medium' | 'large' | 'x-large'
  screenReaderOptimized: boolean
  colorBlindnessMode: 'none' | 'protanopia' | 'deuteranopia' | 'tritanopia'
  focusRingStyle: 'default' | 'high-contrast' | 'custom'
}

export interface UseAccessibilityOptions {
  autoDetectPreferences?: boolean
  persistPreferences?: boolean
  storageKey?: string
}

export interface FocusManagementOptions {
  restoreFocus?: boolean
  trapFocus?: boolean
  autoFocus?: boolean
}

const DEFAULT_PREFERENCES: AccessibilityPreferences = {
  reducedMotion: false,
  highContrast: false,
  fontSize: 'medium',
  screenReaderOptimized: false,
  colorBlindnessMode: 'none',
  focusRingStyle: 'default',
}

// Detect system accessibility preferences
const detectSystemPreferences = (): Partial<AccessibilityPreferences> => {
  const preferences: Partial<AccessibilityPreferences> = {}
  
  if (typeof window !== 'undefined') {
    // Check for reduced motion preference
    const reducedMotionQuery = window.matchMedia('(prefers-reduced-motion: reduce)')
    preferences.reducedMotion = reducedMotionQuery.matches
    
    // Check for high contrast preference
    const highContrastQuery = window.matchMedia('(prefers-contrast: high)')
    preferences.highContrast = highContrastQuery.matches
    
    // Check for screen reader usage (heuristic)
    preferences.screenReaderOptimized = window.navigator.userAgent.includes('JAWS') ||
      window.navigator.userAgent.includes('NVDA') ||
      window.speechSynthesis?.getVoices().length > 0
  }
  
  return preferences
}

// Apply accessibility preferences to DOM
const applyAccessibilityPreferences = (preferences: AccessibilityPreferences) => {
  if (typeof document === 'undefined') return
  
  const root = document.documentElement
  
  // Apply reduced motion
  if (preferences.reducedMotion) {
    root.style.setProperty('--animation-duration', '0ms')
    root.style.setProperty('--transition-duration', '0ms')
    root.classList.add('reduced-motion')
  } else {
    root.style.removeProperty('--animation-duration')
    root.style.removeProperty('--transition-duration')
    root.classList.remove('reduced-motion')
  }
  
  // Apply high contrast
  if (preferences.highContrast) {
    root.classList.add('high-contrast')
  } else {
    root.classList.remove('high-contrast')
  }
  
  // Apply font size
  const fontSizeMap = {
    small: '14px',
    medium: '16px',
    large: '18px',
    'x-large': '20px',
  }
  root.style.fontSize = fontSizeMap[preferences.fontSize]
  
  // Apply color blindness filters
  const filterMap = {
    none: 'none',
    protanopia: 'url(#protanopia-filter)',
    deuteranopia: 'url(#deuteranopia-filter)',
    tritanopia: 'url(#tritanopia-filter)',
  }
  
  if (preferences.colorBlindnessMode !== 'none') {
    root.style.filter = filterMap[preferences.colorBlindnessMode]
    root.classList.add('color-blind-mode')
  } else {
    root.style.removeProperty('filter')
    root.classList.remove('color-blind-mode')
  }
  
  // Apply focus ring style
  root.setAttribute('data-focus-style', preferences.focusRingStyle)
  
  // Apply screen reader optimizations
  if (preferences.screenReaderOptimized) {
    root.classList.add('screen-reader-optimized')
  } else {
    root.classList.remove('screen-reader-optimized')
  }
}

// Hook for accessibility management
export const useAccessibility = (options: UseAccessibilityOptions = {}) => {
  const {
    autoDetectPreferences = true,
    persistPreferences = true,
    storageKey = 'accessibility-preferences',
  } = options
  
  const [preferences, setPreferences] = React.useState<AccessibilityPreferences>(() => {
    if (typeof window === 'undefined') return DEFAULT_PREFERENCES
    
    // Try to load from localStorage first
    if (persistPreferences) {
      try {
        const stored = localStorage.getItem(storageKey)
        if (stored) {
          const parsed = JSON.parse(stored)
          return { ...DEFAULT_PREFERENCES, ...parsed }
        }
      } catch (error) {
        console.warn('Failed to load accessibility preferences:', error)
      }
    }
    
    // Auto-detect preferences if enabled
    if (autoDetectPreferences) {
      const detected = detectSystemPreferences()
      return { ...DEFAULT_PREFERENCES, ...detected }
    }
    
    return DEFAULT_PREFERENCES
  })
  
  // Persist preferences to localStorage
  const persistPrefs = React.useCallback((prefs: AccessibilityPreferences) => {
    if (!persistPreferences || typeof window === 'undefined') return
    
    try {
      localStorage.setItem(storageKey, JSON.stringify(prefs))
    } catch (error) {
      console.warn('Failed to save accessibility preferences:', error)
    }
  }, [persistPreferences, storageKey])
  
  // Update preferences
  const updatePreferences = React.useCallback((updates: Partial<AccessibilityPreferences>) => {
    setPreferences(prev => {
      const newPrefs = { ...prev, ...updates }
      persistPrefs(newPrefs)
      return newPrefs
    })
  }, [persistPrefs])
  
  // Reset to defaults
  const resetPreferences = React.useCallback(() => {
    const defaultPrefs = autoDetectPreferences 
      ? { ...DEFAULT_PREFERENCES, ...detectSystemPreferences() }
      : DEFAULT_PREFERENCES
      
    setPreferences(defaultPrefs)
    persistPrefs(defaultPrefs)
  }, [autoDetectPreferences, persistPrefs])
  
  // Apply preferences to DOM when they change
  React.useEffect(() => {
    applyAccessibilityPreferences(preferences)
  }, [preferences])
  
  // Listen for system preference changes
  React.useEffect(() => {
    if (!autoDetectPreferences || typeof window === 'undefined') return
    
    const reducedMotionQuery = window.matchMedia('(prefers-reduced-motion: reduce)')
    const highContrastQuery = window.matchMedia('(prefers-contrast: high)')
    
    const handleReducedMotionChange = (e: MediaQueryListEvent) => {
      updatePreferences({ reducedMotion: e.matches })
    }
    
    const handleHighContrastChange = (e: MediaQueryListEvent) => {
      updatePreferences({ highContrast: e.matches })
    }
    
    reducedMotionQuery.addEventListener('change', handleReducedMotionChange)
    highContrastQuery.addEventListener('change', handleHighContrastChange)
    
    return () => {
      reducedMotionQuery.removeEventListener('change', handleReducedMotionChange)
      highContrastQuery.removeEventListener('change', handleHighContrastChange)
    }
  }, [autoDetectPreferences, updatePreferences])
  
  return {
    preferences,
    updatePreferences,
    resetPreferences,
  }
}

// Hook for managing focus
export const useFocusManagement = () => {
  const [focusStack, setFocusStack] = React.useState<HTMLElement[]>([])
  
  const pushFocus = React.useCallback((element: HTMLElement) => {
    const previouslyFocused = document.activeElement as HTMLElement
    if (previouslyFocused && previouslyFocused !== document.body) {
      setFocusStack(prev => [...prev, previouslyFocused])
    }
    element.focus()
  }, [])
  
  const popFocus = React.useCallback(() => {
    setFocusStack(prev => {
      const newStack = [...prev]
      const elementToFocus = newStack.pop()
      
      if (elementToFocus && elementToFocus.isConnected) {
        elementToFocus.focus()
      }
      
      return newStack
    })
  }, [])
  
  const clearFocusStack = React.useCallback(() => {
    setFocusStack([])
  }, [])
  
  return {
    pushFocus,
    popFocus,
    clearFocusStack,
    focusStackLength: focusStack.length,
  }
}

// Hook for focus trap
export const useFocusTrap = (
  containerRef: React.RefObject<HTMLElement>,
  options: FocusManagementOptions = {}
) => {
  const { restoreFocus = true, trapFocus = true, autoFocus = true } = options
  const { pushFocus, popFocus } = useFocusManagement()
  
  React.useEffect(() => {
    const container = containerRef.current
    if (!container || !trapFocus) return
    
    // Get all focusable elements
    const getFocusableElements = () => {
      const focusableSelectors = [
        'button:not([disabled])',
        'input:not([disabled])',
        'select:not([disabled])',
        'textarea:not([disabled])',
        'a[href]',
        '[tabindex]:not([tabindex="-1"])',
        '[contenteditable="true"]',
      ].join(', ')
      
      return Array.from(container.querySelectorAll(focusableSelectors)) as HTMLElement[]
    }
    
    const focusableElements = getFocusableElements()
    
    // Auto focus first element
    if (autoFocus && focusableElements.length > 0) {
      pushFocus(focusableElements[0])
    }
    
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key !== 'Tab') return
      
      const currentFocusableElements = getFocusableElements()
      const firstElement = currentFocusableElements[0]
      const lastElement = currentFocusableElements[currentFocusableElements.length - 1]
      
      if (e.shiftKey) {
        // Shift + Tab
        if (document.activeElement === firstElement) {
          e.preventDefault()
          lastElement?.focus()
        }
      } else {
        // Tab
        if (document.activeElement === lastElement) {
          e.preventDefault()
          firstElement?.focus()
        }
      }
    }
    
    container.addEventListener('keydown', handleKeyDown)
    
    return () => {
      container.removeEventListener('keydown', handleKeyDown)
      
      if (restoreFocus) {
        popFocus()
      }
    }
  }, [containerRef, trapFocus, autoFocus, restoreFocus, pushFocus, popFocus])
}

// Hook for keyboard navigation
export const useKeyboardNavigation = (
  items: HTMLElement[] | (() => HTMLElement[]),
  options: {
    orientation?: 'horizontal' | 'vertical' | 'both'
    wrap?: boolean
    activateOnFocus?: boolean
  } = {}
) => {
  const { orientation = 'vertical', wrap = true, activateOnFocus = false } = options
  const [currentIndex, setCurrentIndex] = React.useState(0)
  
  const getItems = React.useCallback(() => {
    return typeof items === 'function' ? items() : items
  }, [items])
  
  const handleKeyDown = React.useCallback((e: KeyboardEvent) => {
    const itemsList = getItems()
    if (itemsList.length === 0) return
    
    let newIndex = currentIndex
    
    switch (e.key) {
      case 'ArrowUp':
        if (orientation === 'vertical' || orientation === 'both') {
          e.preventDefault()
          newIndex = currentIndex > 0 ? currentIndex - 1 : (wrap ? itemsList.length - 1 : 0)
        }
        break
        
      case 'ArrowDown':
        if (orientation === 'vertical' || orientation === 'both') {
          e.preventDefault()
          newIndex = currentIndex < itemsList.length - 1 ? currentIndex + 1 : (wrap ? 0 : itemsList.length - 1)
        }
        break
        
      case 'ArrowLeft':
        if (orientation === 'horizontal' || orientation === 'both') {
          e.preventDefault()
          newIndex = currentIndex > 0 ? currentIndex - 1 : (wrap ? itemsList.length - 1 : 0)
        }
        break
        
      case 'ArrowRight':
        if (orientation === 'horizontal' || orientation === 'both') {
          e.preventDefault()
          newIndex = currentIndex < itemsList.length - 1 ? currentIndex + 1 : (wrap ? 0 : itemsList.length - 1)
        }
        break
        
      case 'Home':
        e.preventDefault()
        newIndex = 0
        break
        
      case 'End':
        e.preventDefault()
        newIndex = itemsList.length - 1
        break
        
      case 'Enter':
      case ' ':
        if (activateOnFocus) {
          e.preventDefault()
          itemsList[currentIndex]?.click()
        }
        break
        
      default:
        return
    }
    
    if (newIndex !== currentIndex) {
      setCurrentIndex(newIndex)
      itemsList[newIndex]?.focus()
    }
  }, [currentIndex, getItems, orientation, wrap, activateOnFocus])
  
  React.useEffect(() => {
    document.addEventListener('keydown', handleKeyDown)
    return () => document.removeEventListener('keydown', handleKeyDown)
  }, [handleKeyDown])
  
  return {
    currentIndex,
    setCurrentIndex,
  }
}

// Hook for screen reader announcements
export const useScreenReaderAnnouncements = () => {
  const [announcer, setAnnouncer] = React.useState<HTMLElement | null>(null)
  
  React.useEffect(() => {
    // Create live region for announcements
    const element = document.createElement('div')
    element.setAttribute('aria-live', 'polite')
    element.setAttribute('aria-atomic', 'true')
    element.className = 'sr-only'
    element.style.cssText = `
      position: absolute !important;
      width: 1px !important;
      height: 1px !important;
      padding: 0 !important;
      margin: -1px !important;
      overflow: hidden !important;
      clip: rect(0, 0, 0, 0) !important;
      white-space: nowrap !important;
      border: 0 !important;
    `
    
    document.body.appendChild(element)
    setAnnouncer(element)
    
    return () => {
      document.body.removeChild(element)
    }
  }, [])
  
  const announce = React.useCallback((message: string, priority: 'polite' | 'assertive' = 'polite') => {
    if (!announcer) return
    
    announcer.setAttribute('aria-live', priority)
    announcer.textContent = ''
    
    // Use setTimeout to ensure the message is announced
    setTimeout(() => {
      announcer.textContent = message
    }, 10)
  }, [announcer])
  
  return { announce }
}

export default useAccessibility