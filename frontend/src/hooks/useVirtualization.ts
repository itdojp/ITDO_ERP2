import React from 'react'

export interface VirtualizationOptions {
  itemHeight: number
  containerHeight: number
  overscan?: number
  estimateItemHeight?: (index: number) => number
}

export interface VirtualizationResult {
  virtualItems: VirtualItem[]
  totalHeight: number
  startIndex: number
  endIndex: number
  scrollElementProps: {
    ref: React.RefObject<HTMLElement>
    onScroll: (event: React.UIEvent<HTMLElement>) => void
    style: React.CSSProperties
  }
  getItemProps: (index: number) => {
    key: string
    style: React.CSSProperties
    'data-index': number
  }
}

export interface VirtualItem {
  index: number
  start: number
  end: number
  size: number
}

export const useVirtualization = <T = any>(
  items: T[],
  options: VirtualizationOptions
): VirtualizationResult => {
  const {
    itemHeight,
    containerHeight,
    overscan = 5,
    estimateItemHeight
  } = options

  const scrollElementRef = React.useRef<HTMLElement>(null)
  const [scrollTop, setScrollTop] = React.useState(0)

  const getItemHeight = React.useCallback(
    (index: number): number => {
      return estimateItemHeight ? estimateItemHeight(index) : itemHeight
    },
    [itemHeight, estimateItemHeight]
  )

  const itemOffsets = React.useMemo(() => {
    const offsets = [0]
    for (let i = 0; i < items.length; i++) {
      offsets[i + 1] = offsets[i] + getItemHeight(i)
    }
    return offsets
  }, [items.length, getItemHeight])

  const totalHeight = itemOffsets[items.length] || 0

  const findNearestItem = React.useCallback(
    (scrollTop: number): number => {
      let low = 0
      let high = items.length - 1

      while (low <= high) {
        const mid = Math.floor((low + high) / 2)
        const offset = itemOffsets[mid]

        if (offset === scrollTop) {
          return mid
        } else if (offset < scrollTop) {
          low = mid + 1
        } else {
          high = mid - 1
        }
      }

      return Math.max(0, high)
    },
    [itemOffsets, items.length]
  )

  const { startIndex, endIndex } = React.useMemo(() => {
    if (items.length === 0) {
      return { startIndex: 0, endIndex: 0 }
    }

    const start = findNearestItem(scrollTop)
    const end = findNearestItem(scrollTop + containerHeight)

    return {
      startIndex: Math.max(0, start - overscan),
      endIndex: Math.min(items.length - 1, end + overscan)
    }
  }, [scrollTop, containerHeight, items.length, overscan, findNearestItem])

  const virtualItems = React.useMemo((): VirtualItem[] => {
    const items: VirtualItem[] = []

    for (let i = startIndex; i <= endIndex; i++) {
      const start = itemOffsets[i]
      const size = getItemHeight(i)
      items.push({
        index: i,
        start,
        end: start + size,
        size
      })
    }

    return items
  }, [startIndex, endIndex, itemOffsets, getItemHeight])

  const handleScroll = React.useCallback((event: React.UIEvent<HTMLElement>) => {
    const scrollTop = event.currentTarget.scrollTop
    setScrollTop(scrollTop)
  }, [])

  const scrollElementProps = React.useMemo(
    () => ({
      ref: scrollElementRef,
      onScroll: handleScroll,
      style: {
        height: containerHeight,
        overflow: 'auto' as const,
        position: 'relative' as const
      }
    }),
    [containerHeight, handleScroll]
  )

  const getItemProps = React.useCallback(
    (index: number) => {
      const offset = itemOffsets[index]
      const size = getItemHeight(index)

      return {
        key: `virtual-item-${index}`,
        style: {
          position: 'absolute' as const,
          top: offset,
          left: 0,
          right: 0,
          height: size
        },
        'data-index': index
      }
    },
    [itemOffsets, getItemHeight]
  )

  // Scroll to item functionality
  const scrollToItem = React.useCallback(
    (index: number, align: 'start' | 'center' | 'end' = 'start') => {
      const element = scrollElementRef.current
      if (!element) return

      const offset = itemOffsets[index]
      const size = getItemHeight(index)

      let scrollTop: number

      switch (align) {
        case 'start':
          scrollTop = offset
          break
        case 'center':
          scrollTop = offset - (containerHeight - size) / 2
          break
        case 'end':
          scrollTop = offset - containerHeight + size
          break
        default:
          scrollTop = offset
      }

      element.scrollTop = Math.max(0, Math.min(scrollTop, totalHeight - containerHeight))
    },
    [itemOffsets, getItemHeight, containerHeight, totalHeight]
  )

  return {
    virtualItems,
    totalHeight,
    startIndex,
    endIndex,
    scrollElementProps,
    getItemProps
  }
}

// Hook for dynamic item heights
export const useDynamicVirtualization = <T = any>(
  items: T[],
  options: Omit<VirtualizationOptions, 'estimateItemHeight'> & {
    estimateItemHeight: (index: number, item: T) => number
  }
): VirtualizationResult => {
  const { estimateItemHeight, ...restOptions } = options

  const estimateHeight = React.useCallback(
    (index: number) => estimateItemHeight(index, items[index]),
    [estimateItemHeight, items]
  )

  return useVirtualization(items, {
    ...restOptions,
    estimateItemHeight: estimateHeight
  })
}

// Virtual table row component
export interface VirtualTableRowProps {
  index: number
  style: React.CSSProperties
  children: React.ReactNode
}

export const VirtualTableRow: React.FC<VirtualTableRowProps> = ({
  index,
  style,
  children
}) => (
  <div
    style={style}
    className="virtual-table-row"
    data-index={index}
  >
    {children}
  </div>
)

// Virtual list component
export interface VirtualListProps<T> {
  items: T[]
  height: number
  itemHeight: number
  renderItem: (item: T, index: number) => React.ReactNode
  overscan?: number
  className?: string
  onScroll?: (scrollTop: number) => void
}

export const VirtualList = <T extends any>({
  items,
  height,
  itemHeight,
  renderItem,
  overscan = 5,
  className,
  onScroll
}: VirtualListProps<T>) => {
  const virtualization = useVirtualization(items, {
    itemHeight,
    containerHeight: height,
    overscan
  })

  const { virtualItems, totalHeight, scrollElementProps, getItemProps } = virtualization

  const handleScroll = React.useCallback(
    (event: React.UIEvent<HTMLElement>) => {
      scrollElementProps.onScroll(event)
      onScroll?.(event.currentTarget.scrollTop)
    },
    [scrollElementProps.onScroll, onScroll]
  )

  return (
    <div
      {...scrollElementProps}
      onScroll={handleScroll}
      className={className}
    >
      <div style={{ height: totalHeight, position: 'relative' }}>
        {virtualItems.map((virtualItem) => {
          const item = items[virtualItem.index]
          const itemProps = getItemProps(virtualItem.index)

          return (
            <div
              key={itemProps.key}
              style={itemProps.style}
              data-index={itemProps['data-index']}
            >
              {renderItem(item, virtualItem.index)}
            </div>
          )
        })}
      </div>
    </div>
  )
}