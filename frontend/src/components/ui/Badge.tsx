import React from 'react'
import { cn } from '../../lib/utils'

export interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?: 'primary' | 'secondary' | 'success' | 'warning' | 'error' | 'info'
  size?: 'sm' | 'md' | 'lg'
  children: React.ReactNode
}

const Badge = React.forwardRef<HTMLSpanElement, BadgeProps>(
  ({ className, variant = 'primary', size = 'md', children, ...props }, ref) => {
    const baseClasses = [
      'inline-flex items-center font-medium rounded-full px-2 py-1',
      'transition-colors duration-150'
    ]

    const variants = {
      primary: 'bg-blue-100 text-blue-800 border border-blue-200',
      secondary: 'bg-gray-100 text-gray-800 border border-gray-200',
      success: 'bg-green-100 text-green-800 border border-green-200',
      warning: 'bg-yellow-100 text-yellow-800 border border-yellow-200',
      error: 'bg-red-100 text-red-800 border border-red-200',
      info: 'bg-cyan-100 text-cyan-800 border border-cyan-200'
    }

    const sizes = {
      sm: 'text-xs px-2 py-0.5',
      md: 'text-sm px-2.5 py-1',
      lg: 'text-base px-3 py-1.5'
    }

    const badgeClasses = cn(
      baseClasses,
      variants[variant],
      sizes[size],
      className
    )

    return (
      <span
        ref={ref}
        className={badgeClasses}
        {...props}
      >
        {children}
      </span>
    )
  }
)

Badge.displayName = 'Badge'

export default Badge