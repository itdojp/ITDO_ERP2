import React from 'react'
import { cn } from '../../../lib/utils'

export interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: 'default' | 'primary' | 'secondary' | 'success' | 'warning' | 'error' | 'outlined' | 'elevated'
  size?: 'sm' | 'md' | 'lg'
  shadow?: 'none' | 'sm' | 'md' | 'lg' | 'xl'
  hover?: boolean
  interactive?: boolean
  children: React.ReactNode
}

export interface CardHeaderProps extends React.HTMLAttributes<HTMLDivElement> {
  title?: string
  subtitle?: string
  actions?: React.ReactNode
  children?: React.ReactNode
}

export interface CardBodyProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode
}

export interface CardFooterProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode
}

const Card = React.memo(React.forwardRef<HTMLDivElement, CardProps>(
  ({
    className,
    variant = 'default',
    size = 'md',
    shadow = 'sm',
    hover = false,
    interactive = false,
    children,
    ...props
  }, ref) => {
    const baseClasses = [
      'border rounded-lg transition-all duration-200 overflow-hidden'
    ]

    const variants = {
      default: 'bg-white border-gray-200',
      primary: 'bg-blue-50 border-blue-200',
      secondary: 'bg-gray-50 border-gray-200',
      success: 'bg-green-50 border-green-200',
      warning: 'bg-yellow-50 border-yellow-200',
      error: 'bg-red-50 border-red-200',
      outlined: 'bg-white border-gray-300 border-2',
      elevated: 'bg-white border-gray-100'
    }

    const sizes = {
      sm: 'p-3',
      md: 'p-4',
      lg: 'p-6'
    }

    const shadows = {
      none: '',
      sm: 'shadow-sm',
      md: 'shadow-md',
      lg: 'shadow-lg',
      xl: 'shadow-xl'
    }

    const cardClasses = cn(
      baseClasses,
      variants[variant],
      sizes[size],
      shadows[shadow],
      hover && 'hover:shadow-lg hover:-translate-y-0.5',
      interactive && 'cursor-pointer focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2',
      className
    )

    const cardProps = {
      ...props,
      ...(interactive && {
        tabIndex: 0,
        role: 'button'
      })
    }

    return (
      <div
        ref={ref}
        className={cardClasses}
        {...cardProps}
      >
        {children}
      </div>
    )
  }
))

Card.displayName = 'Card'

const CardHeader = React.memo(React.forwardRef<HTMLDivElement, CardHeaderProps>(
  ({
    className,
    title,
    subtitle,
    actions,
    children,
    ...props
  }, ref) => {
    const headerClasses = cn(
      'flex items-start justify-between gap-4 -m-4 mb-4 p-4 border-b border-gray-100',
      className
    )

    if (children) {
      return (
        <div
          ref={ref}
          className={headerClasses}
          {...props}
        >
          {children}
        </div>
      )
    }

    return (
      <div
        ref={ref}
        className={headerClasses}
        {...props}
      >
        <div className="flex-1 min-w-0">
          {title && (
            <h3 className="text-lg font-semibold text-gray-900 truncate">
              {title}
            </h3>
          )}
          {subtitle && (
            <p className="mt-1 text-sm text-gray-600 truncate">
              {subtitle}
            </p>
          )}
        </div>
        {actions && (
          <div className="flex-shrink-0">
            {actions}
          </div>
        )}
      </div>
    )
  }
))

CardHeader.displayName = 'CardHeader'

const CardBody = React.memo(React.forwardRef<HTMLDivElement, CardBodyProps>(
  ({
    className,
    children,
    ...props
  }, ref) => {
    const bodyClasses = cn(
      'text-gray-700',
      className
    )

    return (
      <div
        ref={ref}
        className={bodyClasses}
        {...props}
      >
        {children}
      </div>
    )
  }
))

CardBody.displayName = 'CardBody'

const CardFooter = React.memo(React.forwardRef<HTMLDivElement, CardFooterProps>(
  ({
    className,
    children,
    ...props
  }, ref) => {
    const footerClasses = cn(
      'flex items-center justify-between gap-4 -m-4 mt-4 p-4 border-t border-gray-100 bg-gray-50',
      className
    )

    return (
      <div
        ref={ref}
        className={footerClasses}
        {...props}
      >
        {children}
      </div>
    )
  }
))

CardFooter.displayName = 'CardFooter'

// Compound component pattern
const CardCompound = Object.assign(Card, {
  Header: CardHeader,
  Body: CardBody,
  Footer: CardFooter
})

export default CardCompound
export { CardHeader, CardBody, CardFooter }