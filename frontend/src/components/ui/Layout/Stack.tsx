import React from 'react'
import { cn } from '../../../lib/utils'

export interface StackProps extends React.HTMLAttributes<HTMLDivElement> {
  direction?: 'vertical' | 'horizontal'
  spacing?: 'none' | 'xs' | 'sm' | 'md' | 'lg' | 'xl' | '2xl'
  align?: 'start' | 'center' | 'end' | 'stretch'
  justify?: 'start' | 'center' | 'end' | 'between' | 'around' | 'evenly'
  wrap?: boolean
  divider?: React.ReactNode
  children: React.ReactNode
}

const Stack = React.memo(React.forwardRef<HTMLDivElement, StackProps>(
  ({
    className,
    direction = 'vertical',
    spacing = 'md',
    align = 'stretch',
    justify = 'start',
    wrap = false,
    divider,
    children,
    ...props
  }, ref) => {
    const spacingClasses = {
      none: 'gap-0',
      xs: 'gap-1',
      sm: 'gap-2',
      md: 'gap-4',
      lg: 'gap-6',
      xl: 'gap-8',
      '2xl': 'gap-12'
    }

    const alignClasses = {
      start: direction === 'vertical' ? 'items-start' : 'items-start',
      center: direction === 'vertical' ? 'items-center' : 'items-center',
      end: direction === 'vertical' ? 'items-end' : 'items-end',
      stretch: direction === 'vertical' ? 'items-stretch' : 'items-stretch'
    }

    const justifyClasses = {
      start: 'justify-start',
      center: 'justify-center',
      end: 'justify-end',
      between: 'justify-between',
      around: 'justify-around',
      evenly: 'justify-evenly'
    }

    const stackClasses = cn(
      'flex',
      direction === 'vertical' ? 'flex-col' : 'flex-row',
      !divider && spacingClasses[spacing],
      alignClasses[align],
      justifyClasses[justify],
      wrap && 'flex-wrap',
      className
    )

    // If divider is provided, we need to manually insert dividers between children
    const renderChildrenWithDividers = () => {
      if (!divider) return children

      const childArray = React.Children.toArray(children)
      return childArray.reduce((acc: React.ReactNode[], child, index) => {
        acc.push(child)
        if (index < childArray.length - 1) {
          acc.push(
            <div key={`divider-${index}`} className="flex-shrink-0">
              {divider}
            </div>
          )
        }
        return acc
      }, [])
    }

    return (
      <div
        ref={ref}
        className={stackClasses}
        {...props}
      >
        {renderChildrenWithDividers()}
      </div>
    )
  }
))

Stack.displayName = 'Stack'

export default Stack