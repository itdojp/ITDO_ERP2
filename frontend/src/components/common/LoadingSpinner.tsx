import React from 'react'
import { cn } from '../../lib/utils'

export interface LoadingSpinnerProps extends React.HTMLAttributes<HTMLDivElement> {
  size?: 'small' | 'medium' | 'large'
  color?: 'primary' | 'secondary' | 'white'
}

const LoadingSpinner = React.forwardRef<HTMLDivElement, LoadingSpinnerProps>(
  ({ className, size = 'medium', color = 'primary', ...props }, ref) => {
    const sizeClasses = {
      small: 'h-4 w-4',
      medium: 'h-6 w-6', 
      large: 'h-8 w-8'
    }

    const colorClasses = {
      primary: 'border-blue-600 border-t-transparent',
      secondary: 'border-gray-500 border-t-transparent',
      white: 'border-white border-t-transparent'
    }

    const spinnerClasses = cn(
      'animate-spin rounded-full border-2',
      sizeClasses[size],
      colorClasses[color],
      className
    )

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
)

LoadingSpinner.displayName = 'LoadingSpinner'

export default LoadingSpinner