import React from 'react'
import { cn } from '../../lib/utils'
import { usePerformanceMonitor } from '../../hooks/usePerformanceMonitor'

export interface LoadingSpinnerProps extends React.HTMLAttributes<HTMLDivElement> {
  size?: 'small' | 'medium' | 'large'
  color?: 'primary' | 'secondary' | 'white'
}

const LoadingSpinner = React.memo(React.forwardRef<HTMLDivElement, LoadingSpinnerProps>(
  ({ className, size = 'medium', color = 'primary', ...props }, ref) => {
    // Performance monitoring for animations
    const { metrics } = usePerformanceMonitor({
      componentName: 'LoadingSpinner',
      threshold: 8 // Animation components should be very fast
    })
    const sizeClasses = React.useMemo(() => ({
      small: 'h-4 w-4',
      medium: 'h-6 w-6', 
      large: 'h-8 w-8'
    }), [])

    const colorClasses = React.useMemo(() => ({
      primary: 'border-blue-600 border-t-transparent',
      secondary: 'border-gray-500 border-t-transparent',
      white: 'border-white border-t-transparent'
    }), [])

    const spinnerClasses = React.useMemo(() => cn(
      'animate-spin rounded-full border-2',
      sizeClasses[size],
      colorClasses[color],
      className
    ), [sizeClasses, colorClasses, size, color, className])

    return (
      <div
        ref={ref}
        className={spinnerClasses}
        role="status"
        aria-label="Loading..."
        {...props}
      >
        <span className="sr-only">Loading...</span>
      </div>
    )
  }
))

LoadingSpinner.displayName = 'LoadingSpinner'

export default LoadingSpinner