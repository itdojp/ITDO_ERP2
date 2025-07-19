import React from 'react'
import { cn } from '../../lib/utils'

export interface SkeletonLoaderProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: 'text' | 'card' | 'avatar' | 'table'
  lines?: number
  width?: string
  height?: string
  rounded?: boolean
  animate?: boolean
}

const SkeletonLoader = React.forwardRef<HTMLDivElement, SkeletonLoaderProps>(
  ({ 
    className, 
    variant = 'text', 
    lines = 1,
    width,
    height,
    rounded = false,
    animate = true,
    ...props 
  }, ref) => {
    const baseClasses = [
      'bg-gray-200',
      animate && 'animate-pulse'
    ]

    const shimmerClasses = [
      animate && 'relative overflow-hidden',
      animate && 'before:absolute before:inset-0',
      animate && 'before:bg-gradient-to-r before:from-transparent before:via-white/20 before:to-transparent',
      animate && 'before:animate-shimmer before:duration-1000'
    ]

    const getVariantClasses = () => {
      const baseVariant = (() => {
        switch (variant) {
          case 'text':
            return 'h-4 rounded'
          case 'card':
            return 'h-32 rounded-lg'
          case 'avatar':
            return 'h-10 w-10 rounded-full'
          case 'table':
            return 'h-8 rounded'
          default:
            return 'h-4 rounded'
        }
      })()
      
      // Add additional rounded-md class if rounded prop is true
      return cn(baseVariant, rounded && 'rounded-md')
    }

    const skeletonClasses = cn(
      baseClasses,
      shimmerClasses,
      getVariantClasses(),
      className
    )

    const style = {
      width: width || (variant === 'avatar' ? undefined : '100%'),
      height: height || undefined
    }

    if (variant === 'text' && lines > 1) {
      return (
        <div ref={ref} className="space-y-2" data-testid="skeleton-container" {...props}>
          {Array.from({ length: lines }, (_, i) => (
            <div
              key={i}
              className={cn(
                skeletonClasses,
                i === lines - 1 && 'w-3/4' // Last line is shorter
              )}
              style={style}
            />
          ))}
        </div>
      )
    }

    if (variant === 'card') {
      return (
        <div ref={ref} className="space-y-3" data-testid="skeleton-container" {...props}>
          <div className={cn(skeletonClasses, 'h-32')} style={style} />
          <div className="space-y-2">
            <div className="h-4 bg-gray-200 rounded animate-pulse" />
            <div className="h-4 bg-gray-200 rounded animate-pulse w-3/4" />
          </div>
        </div>
      )
    }

    if (variant === 'table') {
      return (
        <div ref={ref} className="space-y-2" data-testid="skeleton-container" {...props}>
          {Array.from({ length: lines }, (_, i) => (
            <div key={i} className="flex space-x-4">
              <div className="h-8 bg-gray-200 rounded animate-pulse flex-1" />
              <div className="h-8 bg-gray-200 rounded animate-pulse w-24" />
              <div className="h-8 bg-gray-200 rounded animate-pulse w-16" />
            </div>
          ))}
        </div>
      )
    }

    return (
      <div
        ref={ref}
        className={skeletonClasses}
        style={style}
        role="status"
        aria-label="Loading content..."
        {...props}
      />
    )
  }
)

SkeletonLoader.displayName = 'SkeletonLoader'

export default SkeletonLoader