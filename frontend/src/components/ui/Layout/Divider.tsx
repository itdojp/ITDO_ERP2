import React from 'react'
import { cn } from '../../../lib/utils'

export interface DividerProps extends React.HTMLAttributes<HTMLDivElement> {
  orientation?: 'horizontal' | 'vertical'
  variant?: 'solid' | 'dashed' | 'dotted'
  size?: 'sm' | 'md' | 'lg'
  color?: 'gray' | 'blue' | 'green' | 'red' | 'yellow'
  label?: string
  labelPosition?: 'left' | 'center' | 'right'
}

const Divider = React.memo(React.forwardRef<HTMLDivElement, DividerProps>(
  ({
    className,
    orientation = 'horizontal',
    variant = 'solid',
    size = 'md',
    color = 'gray',
    label,
    labelPosition = 'center',
    ...props
  }, ref) => {
    const sizeClasses = {
      sm: orientation === 'horizontal' ? 'h-px' : 'w-px',
      md: orientation === 'horizontal' ? 'h-0.5' : 'w-0.5',
      lg: orientation === 'horizontal' ? 'h-1' : 'w-1'
    }

    const colorClasses = {
      gray: 'border-gray-300',
      blue: 'border-blue-300',
      green: 'border-green-300',
      red: 'border-red-300',
      yellow: 'border-yellow-300'
    }

    const variantClasses = {
      solid: 'border-solid',
      dashed: 'border-dashed',
      dotted: 'border-dotted'
    }

    const dividerClasses = cn(
      'border-0',
      orientation === 'horizontal' ? 'w-full border-t' : 'h-full border-l',
      sizeClasses[size],
      colorClasses[color],
      variantClasses[variant],
      className
    )

    const labelPositionClasses = {
      left: 'justify-start',
      center: 'justify-center',
      right: 'justify-end'
    }

    if (label) {
      return (
        <div
          ref={ref}
          className={cn(
            'relative flex items-center',
            orientation === 'horizontal' ? 'w-full' : 'h-full flex-col',
            labelPositionClasses[labelPosition]
          )}
          {...props}
        >
          <div className={cn(
            'flex-1',
            orientation === 'horizontal' ? 'h-px' : 'w-px',
            colorClasses[color],
            variantClasses[variant],
            orientation === 'horizontal' ? 'border-t' : 'border-l'
          )} />
          
          <span className={cn(
            'bg-white px-3 py-1 text-sm text-gray-500 font-medium',
            orientation === 'vertical' && 'transform -rotate-90 whitespace-nowrap'
          )}>
            {label}
          </span>
          
          <div className={cn(
            'flex-1',
            orientation === 'horizontal' ? 'h-px' : 'w-px',
            colorClasses[color],
            variantClasses[variant],
            orientation === 'horizontal' ? 'border-t' : 'border-l'
          )} />
        </div>
      )
    }

    return (
      <div
        ref={ref}
        className={dividerClasses}
        role="separator"
        aria-orientation={orientation}
        {...props}
      />
    )
  }
))

Divider.displayName = 'Divider'

export default Divider