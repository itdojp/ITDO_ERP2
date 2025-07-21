import React from 'react'
import { TrendingUp, TrendingDown, Minus, ArrowUp, ArrowDown } from 'lucide-react'
import { cn } from '../../../lib/utils'

export interface StatItem {
  id: string
  label: string
  value: string | number
  previousValue?: string | number
  change?: {
    value: number
    type: 'increase' | 'decrease' | 'neutral'
    percentage?: boolean
    period?: string
  }
  icon?: React.ReactNode
  color?: 'default' | 'success' | 'warning' | 'error' | 'info'
  format?: 'number' | 'currency' | 'percentage' | 'decimal'
  precision?: number
  href?: string
  onClick?: () => void
  loading?: boolean
  error?: string | null
}

export interface StatsProps {
  items: StatItem[]
  layout?: 'grid' | 'horizontal' | 'vertical'
  columns?: 1 | 2 | 3 | 4 | 5 | 6
  size?: 'sm' | 'md' | 'lg'
  variant?: 'default' | 'card' | 'minimal'
  showTrend?: boolean
  showComparison?: boolean
  className?: string
  itemClassName?: string
}

const Stats = React.memo<StatsProps>(({
  items,
  layout = 'grid',
  columns = 4,
  size = 'md',
  variant = 'card',
  showTrend = true,
  showComparison = true,
  className,
  itemClassName,
}) => {
  const formatValue = React.useCallback((
    value: string | number, 
    format?: StatItem['format'], 
    precision = 0
  ) => {
    if (typeof value === 'string') return value

    switch (format) {
      case 'currency':
        return new Intl.NumberFormat('en-US', {
          style: 'currency',
          currency: 'USD',
          minimumFractionDigits: precision,
          maximumFractionDigits: precision,
        }).format(value)
      
      case 'percentage':
        return `${value.toFixed(precision)}%`
      
      case 'decimal':
        return value.toFixed(precision)
      
      case 'number':
      default:
        return new Intl.NumberFormat('en-US', {
          minimumFractionDigits: precision,
          maximumFractionDigits: precision,
        }).format(value)
    }
  }, [])

  const calculateChange = React.useCallback((
    current: string | number,
    previous?: string | number
  ) => {
    if (previous === undefined || typeof current === 'string' || typeof previous === 'string') {
      return null
    }

    const diff = current - previous
    const percentage = previous !== 0 ? (diff / Math.abs(previous)) * 100 : 0

    return {
      absolute: diff,
      percentage,
      type: diff > 0 ? 'increase' : diff < 0 ? 'decrease' : 'neutral' as const,
    }
  }, [])

  const getTrendIcon = React.useCallback((type: 'increase' | 'decrease' | 'neutral') => {
    switch (type) {
      case 'increase':
        return <TrendingUp className="h-4 w-4" />
      case 'decrease':
        return <TrendingDown className="h-4 w-4" />
      case 'neutral':
      default:
        return <Minus className="h-4 w-4" />
    }
  }, [])

  const getChangeIcon = React.useCallback((type: 'increase' | 'decrease' | 'neutral') => {
    switch (type) {
      case 'increase':
        return <ArrowUp className="h-3 w-3" />
      case 'decrease':
        return <ArrowDown className="h-3 w-3" />
      case 'neutral':
      default:
        return <Minus className="h-3 w-3" />
    }
  }, [])

  const getColorClasses = React.useCallback((color: StatItem['color'] = 'default', type?: 'text' | 'bg' | 'border') => {
    const colors = {
      default: {
        text: 'text-gray-900',
        bg: 'bg-gray-50',
        border: 'border-gray-200',
      },
      success: {
        text: 'text-green-700',
        bg: 'bg-green-50',
        border: 'border-green-200',
      },
      warning: {
        text: 'text-yellow-700',
        bg: 'bg-yellow-50',
        border: 'border-yellow-200',
      },
      error: {
        text: 'text-red-700',
        bg: 'bg-red-50',
        border: 'border-red-200',
      },
      info: {
        text: 'text-blue-700',
        bg: 'bg-blue-50',
        border: 'border-blue-200',
      },
    }

    return type ? colors[color][type] : colors[color]
  }, [])

  const getChangeColorClasses = React.useCallback((type: 'increase' | 'decrease' | 'neutral') => {
    switch (type) {
      case 'increase':
        return 'text-green-600 bg-green-100'
      case 'decrease':
        return 'text-red-600 bg-red-100'
      case 'neutral':
      default:
        return 'text-gray-600 bg-gray-100'
    }
  }, [])

  const sizes = {
    sm: {
      container: 'p-4',
      value: 'text-xl font-semibold',
      label: 'text-xs',
      change: 'text-xs',
      icon: 'h-4 w-4',
    },
    md: {
      container: 'p-6',
      value: 'text-2xl font-semibold',
      label: 'text-sm',
      change: 'text-sm',
      icon: 'h-5 w-5',
    },
    lg: {
      container: 'p-8',
      value: 'text-3xl font-bold',
      label: 'text-base',
      change: 'text-base',
      icon: 'h-6 w-6',
    },
  }

  const sizeClasses = sizes[size]

  const layouts = {
    grid: `grid gap-4 grid-cols-1 md:grid-cols-${Math.min(columns, 3)} lg:grid-cols-${columns}`,
    horizontal: 'flex flex-wrap gap-4',
    vertical: 'space-y-4',
  }

  const variants = {
    default: 'bg-white border border-gray-200 rounded-lg shadow-sm',
    card: 'bg-white border border-gray-200 rounded-lg shadow-md',
    minimal: 'bg-transparent',
  }

  const containerClasses = cn(
    layouts[layout],
    className
  )

  const renderStatItem = (item: StatItem) => {
    const change = item.change || (showComparison && item.previousValue 
      ? { 
          ...calculateChange(item.value, item.previousValue)!, 
          percentage: true 
        } 
      : null
    )

    const itemClasses = cn(
      variants[variant],
      sizeClasses.container,
      'transition-all duration-200',
      (item.href || item.onClick) && 'cursor-pointer hover:shadow-md',
      item.error && 'border-red-200 bg-red-50',
      itemClassName
    )

    const ItemContent = (
      <>
        {/* Header with icon and label */}
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-2">
            {item.icon && (
              <div className={cn(
                'flex items-center justify-center',
                sizeClasses.icon,
                getColorClasses(item.color, 'text')
              )}>
                {item.icon}
              </div>
            )}
            <h3 className={cn(
              'font-medium text-gray-700 truncate',
              sizeClasses.label
            )}>
              {item.label}
            </h3>
          </div>
          
          {showTrend && change && (
            <div className={cn(
              'flex items-center justify-center p-1 rounded-full',
              getChangeColorClasses(change.type)
            )}>
              {getTrendIcon(change.type)}
            </div>
          )}
        </div>

        {/* Value */}
        <div className="mb-2">
          {item.loading ? (
            <div className="animate-pulse">
              <div className="h-8 bg-gray-200 rounded w-24"></div>
            </div>
          ) : item.error ? (
            <div className="text-red-600 text-sm">Error loading data</div>
          ) : (
            <div className={cn(
              'text-gray-900',
              sizeClasses.value
            )}>
              {formatValue(item.value, item.format, item.precision)}
            </div>
          )}
        </div>

        {/* Change indicator */}
        {showComparison && change && !item.loading && !item.error && (
          <div className="flex items-center gap-1">
            <div className={cn(
              'flex items-center gap-1 px-2 py-1 rounded-full',
              getChangeColorClasses(change.type),
              sizeClasses.change
            )}>
              {getChangeIcon(change.type)}
              <span className="font-medium">
                {change.percentage 
                  ? `${Math.abs(change.percentage).toFixed(1)}%`
                  : Math.abs(change.absolute || change.value)
                }
              </span>
            </div>
            {change.period && (
              <span className={cn('text-gray-500', sizeClasses.change)}>
                vs {change.period}
              </span>
            )}
          </div>
        )}
      </>
    )

    if (item.href) {
      return (
        <a
          key={item.id}
          href={item.href}
          className={itemClasses}
        >
          {ItemContent}
        </a>
      )
    }

    if (item.onClick) {
      return (
        <button
          key={item.id}
          type="button"
          className={itemClasses}
          onClick={item.onClick}
        >
          {ItemContent}
        </button>
      )
    }

    return (
      <div key={item.id} className={itemClasses}>
        {ItemContent}
      </div>
    )
  }

  return (
    <div className={containerClasses}>
      {items.map(renderStatItem)}
    </div>
  )
})

Stats.displayName = 'Stats'

export default Stats