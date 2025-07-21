import React from 'react'
import { Settings, Eye, Type, MousePointer, Volume2, Monitor, Palette } from 'lucide-react'
import { cn } from '../../../lib/utils'
import { useAccessibility, AccessibilityPreferences } from '../../../hooks/useAccessibility'

export interface AccessibilityPanelProps {
  className?: string
  isOpen?: boolean
  onClose?: () => void
}

const AccessibilityPanel = React.memo<AccessibilityPanelProps>(({
  className,
  isOpen = false,
  onClose,
}) => {
  const { preferences, updatePreferences, resetPreferences } = useAccessibility()

  const handlePreferenceChange = React.useCallback(
    <K extends keyof AccessibilityPreferences>(
      key: K,
      value: AccessibilityPreferences[K]
    ) => {
      updatePreferences({ [key]: value })
    },
    [updatePreferences]
  )

  if (!isOpen) return null

  return (
    <div className={cn('fixed inset-0 z-50 flex items-center justify-center', className)}>
      {/* Backdrop */}
      <div 
        className="absolute inset-0 bg-black bg-opacity-50"
        onClick={onClose}
        aria-hidden="true"
      />
      
      {/* Panel */}
      <div 
        className="relative bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-[90vh] overflow-hidden"
        role="dialog"
        aria-labelledby="accessibility-panel-title"
        aria-modal="true"
      >
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <div className="flex items-center space-x-3">
            <Settings className="h-6 w-6 text-blue-500" />
            <h2 id="accessibility-panel-title" className="text-xl font-semibold text-gray-900">
              Accessibility Settings
            </h2>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-100 rounded-full transition-colors"
            aria-label="Close accessibility panel"
          >
            ×
          </button>
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto max-h-[calc(90vh-140px)]">
          <div className="space-y-8">
            {/* Visual Preferences */}
            <section>
              <h3 className="text-lg font-medium text-gray-900 mb-4 flex items-center">
                <Eye className="h-5 w-5 mr-2 text-gray-600" />
                Visual Preferences
              </h3>
              
              <div className="space-y-4">
                {/* High Contrast */}
                <div className="flex items-center justify-between">
                  <div>
                    <label className="text-sm font-medium text-gray-700">
                      High Contrast Mode
                    </label>
                    <p className="text-xs text-gray-500">
                      Increase contrast for better visibility
                    </p>
                  </div>
                  <label className="relative inline-flex items-center cursor-pointer">
                    <input
                      type="checkbox"
                      checked={preferences.highContrast}
                      onChange={(e) => handlePreferenceChange('highContrast', e.target.checked)}
                      className="sr-only peer"
                    />
                    <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                  </label>
                </div>

                {/* Font Size */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Font Size
                  </label>
                  <div className="grid grid-cols-4 gap-2">
                    {(['small', 'medium', 'large', 'x-large'] as const).map((size) => (
                      <button
                        key={size}
                        onClick={() => handlePreferenceChange('fontSize', size)}
                        className={cn(
                          'px-3 py-2 text-sm rounded-md border transition-colors',
                          preferences.fontSize === size
                            ? 'bg-blue-100 border-blue-500 text-blue-700'
                            : 'bg-white border-gray-300 text-gray-700 hover:bg-gray-50'
                        )}
                      >
                        {size === 'x-large' ? 'XL' : size.charAt(0).toUpperCase() + size.slice(1)}
                      </button>
                    ))}
                  </div>
                </div>

                {/* Color Blindness Support */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Color Blindness Support
                  </label>
                  <select
                    value={preferences.colorBlindnessMode}
                    onChange={(e) => handlePreferenceChange('colorBlindnessMode', e.target.value as any)}
                    className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  >
                    <option value="none">None</option>
                    <option value="protanopia">Protanopia (Red-blind)</option>
                    <option value="deuteranopia">Deuteranopia (Green-blind)</option>
                    <option value="tritanopia">Tritanopia (Blue-blind)</option>
                  </select>
                </div>
              </div>
            </section>

            {/* Motion Preferences */}
            <section>
              <h3 className="text-lg font-medium text-gray-900 mb-4 flex items-center">
                <MousePointer className="h-5 w-5 mr-2 text-gray-600" />
                Motion & Animation
              </h3>
              
              <div className="space-y-4">
                {/* Reduced Motion */}
                <div className="flex items-center justify-between">
                  <div>
                    <label className="text-sm font-medium text-gray-700">
                      Reduce Motion
                    </label>
                    <p className="text-xs text-gray-500">
                      Minimize animations and transitions
                    </p>
                  </div>
                  <label className="relative inline-flex items-center cursor-pointer">
                    <input
                      type="checkbox"
                      checked={preferences.reducedMotion}
                      onChange={(e) => handlePreferenceChange('reducedMotion', e.target.checked)}
                      className="sr-only peer"
                    />
                    <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                  </label>
                </div>
              </div>
            </section>

            {/* Focus & Navigation */}
            <section>
              <h3 className="text-lg font-medium text-gray-900 mb-4 flex items-center">
                <Palette className="h-5 w-5 mr-2 text-gray-600" />
                Focus & Navigation
              </h3>
              
              <div className="space-y-4">
                {/* Focus Ring Style */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Focus Indicator Style
                  </label>
                  <div className="grid grid-cols-3 gap-2">
                    {(['default', 'high-contrast', 'custom'] as const).map((style) => (
                      <button
                        key={style}
                        onClick={() => handlePreferenceChange('focusRingStyle', style)}
                        className={cn(
                          'px-3 py-2 text-sm rounded-md border transition-colors capitalize',
                          preferences.focusRingStyle === style
                            ? 'bg-blue-100 border-blue-500 text-blue-700'
                            : 'bg-white border-gray-300 text-gray-700 hover:bg-gray-50'
                        )}
                      >
                        {style}
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            </section>

            {/* Screen Reader */}
            <section>
              <h3 className="text-lg font-medium text-gray-900 mb-4 flex items-center">
                <Volume2 className="h-5 w-5 mr-2 text-gray-600" />
                Screen Reader
              </h3>
              
              <div className="space-y-4">
                {/* Screen Reader Optimization */}
                <div className="flex items-center justify-between">
                  <div>
                    <label className="text-sm font-medium text-gray-700">
                      Screen Reader Optimized
                    </label>
                    <p className="text-xs text-gray-500">
                      Optimize interface for screen readers
                    </p>
                  </div>
                  <label className="relative inline-flex items-center cursor-pointer">
                    <input
                      type="checkbox"
                      checked={preferences.screenReaderOptimized}
                      onChange={(e) => handlePreferenceChange('screenReaderOptimized', e.target.checked)}
                      className="sr-only peer"
                    />
                    <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                  </label>
                </div>
              </div>
            </section>
          </div>
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between p-6 border-t border-gray-200 bg-gray-50">
          <button
            onClick={resetPreferences}
            className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
          >
            Reset to Default
          </button>
          
          <div className="flex space-x-3">
            <button
              onClick={onClose}
              className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
            >
              Cancel
            </button>
            <button
              onClick={onClose}
              className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
            >
              Apply Settings
            </button>
          </div>
        </div>
      </div>
    </div>
  )
})

AccessibilityPanel.displayName = 'AccessibilityPanel'

export default AccessibilityPanel