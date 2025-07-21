import React from 'react'
import { cn } from '../../../lib/utils'

export interface GridProps extends React.HTMLAttributes<HTMLDivElement> {
  cols?: 1 | 2 | 3 | 4 | 5 | 6 | 8 | 12
  gap?: 'none' | 'xs' | 'sm' | 'md' | 'lg' | 'xl'
  responsive?: {
    sm?: 1 | 2 | 3 | 4 | 5 | 6 | 8 | 12
    md?: 1 | 2 | 3 | 4 | 5 | 6 | 8 | 12
    lg?: 1 | 2 | 3 | 4 | 5 | 6 | 8 | 12
    xl?: 1 | 2 | 3 | 4 | 5 | 6 | 8 | 12
  }
  autoFit?: boolean
  minColWidth?: string
  children: React.ReactNode
}

const Grid = React.memo(React.forwardRef<HTMLDivElement, GridProps>(
  ({
    className,
    cols = 1,
    gap = 'md',
    responsive,
    autoFit = false,
    minColWidth = '250px',
    children,
    ...props
  }, ref) => {
    const gapClasses = {
      none: 'gap-0',
      xs: 'gap-1',
      sm: 'gap-2',
      md: 'gap-4',
      lg: 'gap-6',
      xl: 'gap-8'
    }

    const colClasses = {
      1: 'grid-cols-1',
      2: 'grid-cols-2',
      3: 'grid-cols-3',
      4: 'grid-cols-4',
      5: 'grid-cols-5',
      6: 'grid-cols-6',
      8: 'grid-cols-8',
      12: 'grid-cols-12'
    }

    const responsiveClasses = responsive ? [
      responsive.sm && `sm:grid-cols-${responsive.sm}`,
      responsive.md && `md:grid-cols-${responsive.md}`,
      responsive.lg && `lg:grid-cols-${responsive.lg}`,
      responsive.xl && `xl:grid-cols-${responsive.xl}`
    ].filter(Boolean) : []

    const gridClasses = cn(
      'grid',
      !autoFit && colClasses[cols],
      gapClasses[gap],
      ...responsiveClasses,
      className
    )

    const gridStyle = autoFit ? {
      gridTemplateColumns: `repeat(auto-fit, minmax(${minColWidth}, 1fr))`
    } : undefined

    return (
      <div
        ref={ref}
        className={gridClasses}
        style={gridStyle}
        {...props}
      >
        {children}
      </div>
    )
  }
))

Grid.displayName = 'Grid'

export default Grid