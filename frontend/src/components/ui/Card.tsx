import React from 'react'
import { cn } from '../../lib/utils'

export interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  title?: string
  variant?: 'default' | 'primary' | 'secondary' | 'success' | 'warning' | 'error'
  size?: 'sm' | 'md' | 'lg'
  children: React.ReactNode
}

const Card = React.forwardRef<HTMLDivElement, CardProps>(
  ({ className, title, variant = 'default', size = 'md', children, ...props }, ref) => {
    const baseClasses = [
      'border rounded-lg shadow-sm transition-colors duration-150'
    ]

    const variants = {
      default: 'bg-white border-gray-200',
      primary: 'bg-blue-50 border-blue-200',
      secondary: 'bg-gray-50 border-gray-200',
      success: 'bg-green-50 border-green-200',
      warning: 'bg-yellow-50 border-yellow-200',
      error: 'bg-red-50 border-red-200'
    }

    const sizes = {
      sm: 'p-3',
      md: 'p-4',
      lg: 'p-6'
    }

    const titleVariants = {
      default: 'text-gray-900',
      primary: 'text-blue-900',
      secondary: 'text-gray-700',
      success: 'text-green-900',
      warning: 'text-yellow-900',
      error: 'text-red-900'
    }

    const cardClasses = cn(
      baseClasses,
      variants[variant],
      sizes[size],
      className
    )

    const titleClasses = cn(
      'text-lg font-semibold mb-3',
      titleVariants[variant]
    )

    return (
      <div
        ref={ref}
        className={cardClasses}
        {...props}
      >
        {title && (
          <h3 className={titleClasses}>
            {title}
          </h3>
        )}
        <div className="text-gray-700">
          {children}
        </div>
      </div>
    )
  }
)

Card.displayName = 'Card'

export default Card