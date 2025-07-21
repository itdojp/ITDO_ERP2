import React from 'react'
import { ChevronRight, Home } from 'lucide-react'
import { cn } from '../../../lib/utils'

export interface BreadcrumbItem {
  label: string
  href?: string
  icon?: React.ReactNode
  current?: boolean
}

export interface BreadcrumbProps {
  items: BreadcrumbItem[]
  separator?: React.ReactNode
  showHomeIcon?: boolean
  maxItems?: number
  className?: string
  itemClassName?: string
  separatorClassName?: string
  onItemClick?: (item: BreadcrumbItem, index: number) => void
}

const Breadcrumb = React.memo<BreadcrumbProps>(({
  items,
  separator = <ChevronRight className="h-4 w-4" />,
  showHomeIcon = true,
  maxItems,
  className,
  itemClassName,
  separatorClassName,
  onItemClick,
}) => {
  const processedItems = React.useMemo(() => {
    if (!maxItems || items.length <= maxItems) {
      return items
    }

    // If we have too many items, show first item, ellipsis, and last few items
    const keepCount = maxItems - 2 // Account for ellipsis and first item
    const firstItem = items[0]
    const lastItems = items.slice(-keepCount)
    
    return [
      firstItem,
      { label: '...', href: undefined, current: false },
      ...lastItems
    ]
  }, [items, maxItems])

  const handleItemClick = (item: BreadcrumbItem, index: number, event: React.MouseEvent) => {
    if (onItemClick) {
      event.preventDefault()
      onItemClick(item, index)
    }
  }

  const renderItem = (item: BreadcrumbItem, index: number, isLast: boolean) => {
    const isCurrentPage = item.current || isLast
    const isEllipsis = item.label === '...'
    
    const baseClasses = cn(
      'inline-flex items-center gap-2 text-sm transition-colors',
      isCurrentPage
        ? 'text-gray-900 font-medium cursor-default'
        : 'text-gray-600 hover:text-gray-900',
      !item.href && !onItemClick && !isCurrentPage && 'cursor-default',
      itemClassName
    )

    const content = (
      <>
        {index === 0 && showHomeIcon && !item.icon && (
          <Home className="h-4 w-4" aria-hidden="true" />
        )}
        {item.icon && <span aria-hidden="true">{item.icon}</span>}
        <span>{item.label}</span>
      </>
    )

    if (isEllipsis) {
      return (
        <span
          key={index}
          className={cn(baseClasses, 'cursor-default')}
          aria-hidden="true"
        >
          {item.label}
        </span>
      )
    }

    if (item.href && !isCurrentPage) {
      return (
        <a
          key={index}
          href={item.href}
          className={baseClasses}
          onClick={(e) => handleItemClick(item, index, e)}
          aria-current={isCurrentPage ? 'page' : undefined}
        >
          {content}
        </a>
      )
    }

    if (onItemClick && !isCurrentPage) {
      return (
        <button
          key={index}
          type="button"
          className={baseClasses}
          onClick={(e) => handleItemClick(item, index, e)}
          aria-current={isCurrentPage ? 'page' : undefined}
        >
          {content}
        </button>
      )
    }

    return (
      <span
        key={index}
        className={baseClasses}
        aria-current={isCurrentPage ? 'page' : undefined}
      >
        {content}
      </span>
    )
  }

  const renderSeparator = (index: number) => (
    <span
      key={`separator-${index}`}
      className={cn(
        'flex items-center text-gray-400',
        separatorClassName
      )}
      aria-hidden="true"
    >
      {separator}
    </span>
  )

  return (
    <nav
      aria-label="Breadcrumb"
      className={cn('flex items-center space-x-2', className)}
    >
      <ol className="flex items-center space-x-2">
        {processedItems.map((item, index) => {
          const isLast = index === processedItems.length - 1
          
          return (
            <React.Fragment key={index}>
              <li className="flex items-center">
                {renderItem(item, index, isLast)}
              </li>
              {!isLast && (
                <li className="flex items-center">
                  {renderSeparator(index)}
                </li>
              )}
            </React.Fragment>
          )
        })}
      </ol>
    </nav>
  )
})

Breadcrumb.displayName = 'Breadcrumb'

export default Breadcrumb