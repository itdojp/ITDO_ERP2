import React, { useState, useEffect, useRef, useMemo, useCallback } from 'react';
import { cn } from '@/lib/utils';

export interface ListAction<T = any> {
  label: string;
  onClick: (item: T) => void;
  variant?: 'default' | 'primary' | 'danger';
  icon?: React.ReactNode;
}

export interface ListProps<T = any> {
  items: T[];
  renderItem: (item: T, index: number) => React.ReactNode;
  className?: string;
  variant?: 'default' | 'bordered' | 'divided' | 'flush';
  size?: 'sm' | 'md' | 'lg';
  hoverable?: boolean;
  selectable?: boolean;
  multiple?: boolean;
  selectedItems?: T[];
  onSelect?: (items: T[]) => void;
  loading?: boolean;
  loadingComponent?: React.ReactNode;
  emptyText?: string;
  emptyComponent?: React.ReactNode;
  virtual?: boolean;
  itemHeight?: number;
  containerHeight?: number;
  infiniteScroll?: boolean;
  onLoadMore?: () => void;
  hasMore?: boolean;
  loadingMore?: boolean;
  draggable?: boolean;
  onReorder?: (items: T[]) => void;
  searchable?: boolean;
  searchPlaceholder?: string;
  searchFunction?: (item: T, query: string) => boolean;
  sortable?: boolean;
  sortBy?: string;
  sortOrder?: 'asc' | 'desc';
  sortFunction?: (a: T, b: T) => number;
  paginated?: boolean;
  pageSize?: number;
  currentPage?: number;
  onPageChange?: (page: number) => void;
  groupBy?: string;
  renderGroup?: (group: string) => React.ReactNode;
  actions?: ListAction<T>[];
  keyboardNavigation?: boolean;
  header?: React.ReactNode;
  footer?: React.ReactNode;
  onItemClick?: (item: T, index: number) => void;
  getItemKey?: (item: T) => string | number;
  getItemDisabled?: (item: T) => boolean;
  'data-testid'?: string;
  'data-category'?: string;
  'data-id'?: string;
}

export const List = <T extends any>({
  items,
  renderItem,
  className,
  variant = 'default',
  size = 'md',
  hoverable = false,
  selectable = false,
  multiple = false,
  selectedItems = [],
  onSelect,
  loading = false,
  loadingComponent,
  emptyText = 'No items to display',
  emptyComponent,
  virtual = false,
  itemHeight = 50,
  containerHeight = 300,
  infiniteScroll = false,
  onLoadMore,
  hasMore = false,
  loadingMore = false,
  draggable = false,
  onReorder,
  searchable = false,
  searchPlaceholder = 'Search...',
  searchFunction,
  sortable = false,
  sortBy,
  sortOrder = 'asc',
  sortFunction,
  paginated = false,
  pageSize = 10,
  currentPage = 1,
  onPageChange,
  groupBy,
  renderGroup,
  actions,
  keyboardNavigation = false,
  header,
  footer,
  onItemClick,
  getItemKey,
  getItemDisabled,
  'data-testid': dataTestId = 'list-container',
  'data-category': dataCategory,
  'data-id': dataId,
  ...props
}: ListProps<T>) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [internalSelectedItems, setInternalSelectedItems] = useState<T[]>(selectedItems);
  const [focusedIndex, setFocusedIndex] = useState(-1);
  const [draggedItem, setDraggedItem] = useState<T | null>(null);
  const [currentPageInternal, setCurrentPageInternal] = useState(currentPage);
  const listRef = useRef<HTMLUListElement>(null);
  const loadMoreRef = useRef<HTMLDivElement>(null);

  const sizeClasses = {
    sm: 'py-1 px-2 text-sm',
    md: 'py-2 px-3',
    lg: 'py-3 px-4 text-lg'
  };

  const variantClasses = {
    default: '',
    bordered: 'border border-gray-200 rounded-md',
    divided: 'divide-y divide-gray-200',
    flush: ''
  };

  // Filter items based on search
  const filteredItems = useMemo(() => {
    if (!searchable || !searchQuery) return items;
    
    return items.filter(item => {
      if (searchFunction) {
        return searchFunction(item, searchQuery);
      }
      
      const searchableText = typeof item === 'object' && item !== null 
        ? Object.values(item).join(' ').toLowerCase()
        : String(item).toLowerCase();
      
      return searchableText.includes(searchQuery.toLowerCase());
    });
  }, [items, searchQuery, searchable, searchFunction]);

  // Sort items
  const sortedItems = useMemo(() => {
    if (!sortable) return filteredItems;
    
    return [...filteredItems].sort((a, b) => {
      if (sortFunction) {
        return sortFunction(a, b);
      }
      
      if (sortBy && typeof a === 'object' && typeof b === 'object') {
        const aValue = (a as any)[sortBy];
        const bValue = (b as any)[sortBy];
        
        if (sortOrder === 'desc') {
          return aValue < bValue ? 1 : aValue > bValue ? -1 : 0;
        }
        return aValue > bValue ? 1 : aValue < bValue ? -1 : 0;
      }
      
      return 0;
    });
  }, [filteredItems, sortable, sortFunction, sortBy, sortOrder]);

  // Group items
  const groupedItems = useMemo(() => {
    if (!groupBy) return [{ group: null, items: sortedItems }];
    
    const groups = sortedItems.reduce((acc, item) => {
      const groupValue = typeof item === 'object' && item !== null 
        ? (item as any)[groupBy] 
        : 'default';
      
      if (!acc[groupValue]) {
        acc[groupValue] = [];
      }
      acc[groupValue].push(item);
      return acc;
    }, {} as Record<string, T[]>);
    
    return Object.entries(groups).map(([group, items]) => ({ group, items }));
  }, [sortedItems, groupBy]);

  // Paginate items
  const paginatedItems = useMemo(() => {
    if (!paginated) return groupedItems;
    
    const startIndex = (currentPageInternal - 1) * pageSize;
    const endIndex = startIndex + pageSize;
    
    return groupedItems.map(group => ({
      ...group,
      items: group.items.slice(startIndex, endIndex)
    }));
  }, [groupedItems, paginated, currentPageInternal, pageSize]);

  // Virtual scrolling
  const [virtualStart, setVirtualStart] = useState(0);
  const [virtualEnd, setVirtualEnd] = useState(Math.ceil(containerHeight / itemHeight));

  const virtualItems = useMemo(() => {
    if (!virtual) return paginatedItems;
    
    return paginatedItems.map(group => ({
      ...group,
      items: group.items.slice(virtualStart, virtualEnd)
    }));
  }, [paginatedItems, virtual, virtualStart, virtualEnd]);

  // Infinite scroll
  useEffect(() => {
    if (!infiniteScroll || !loadMoreRef.current) return;

    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting && hasMore && !loadingMore && onLoadMore) {
          onLoadMore();
        }
      },
      { threshold: 0.1 }
    );

    observer.observe(loadMoreRef.current);
    return () => observer.disconnect();
  }, [infiniteScroll, hasMore, loadingMore, onLoadMore]);

  // Keyboard navigation
  useEffect(() => {
    if (!keyboardNavigation) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      const totalItems = sortedItems.length;
      
      switch (e.key) {
        case 'ArrowDown':
          e.preventDefault();
          setFocusedIndex(prev => Math.min(prev + 1, totalItems - 1));
          break;
        case 'ArrowUp':
          e.preventDefault();
          setFocusedIndex(prev => Math.max(prev - 1, 0));
          break;
        case 'Enter':
          if (focusedIndex >= 0 && onItemClick) {
            onItemClick(sortedItems[focusedIndex], focusedIndex);
          }
          break;
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [keyboardNavigation, sortedItems, focusedIndex, onItemClick]);

  const handleItemClick = useCallback((item: T, index: number) => {
    if (getItemDisabled?.(item)) return;
    
    if (selectable) {
      const isSelected = internalSelectedItems.some(selected => 
        getItemKey ? getItemKey(selected) === getItemKey(item) : selected === item
      );
      
      let newSelection: T[];
      if (multiple) {
        newSelection = isSelected
          ? internalSelectedItems.filter(selected => 
              getItemKey ? getItemKey(selected) !== getItemKey(item) : selected !== item
            )
          : [...internalSelectedItems, item];
      } else {
        newSelection = isSelected ? [] : [item];
      }
      
      setInternalSelectedItems(newSelection);
      onSelect?.(newSelection);
    }
    
    onItemClick?.(item, index);
  }, [selectable, multiple, internalSelectedItems, getItemKey, getItemDisabled, onSelect, onItemClick]);

  const handleDragStart = (e: React.DragEvent, item: T) => {
    setDraggedItem(item);
    e.dataTransfer.effectAllowed = 'move';
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
  };

  const handleDrop = (e: React.DragEvent, targetItem: T) => {
    e.preventDefault();
    
    if (!draggedItem || !onReorder) return;
    
    const draggedIndex = items.indexOf(draggedItem);
    const targetIndex = items.indexOf(targetItem);
    
    if (draggedIndex === targetIndex) return;
    
    const newItems = [...items];
    newItems.splice(draggedIndex, 1);
    newItems.splice(targetIndex, 0, draggedItem);
    
    onReorder(newItems);
    setDraggedItem(null);
  };

  const isItemSelected = (item: T) => {
    return internalSelectedItems.some(selected => 
      getItemKey ? getItemKey(selected) === getItemKey(item) : selected === item
    );
  };

  const renderListItem = (item: T, index: number, globalIndex: number) => {
    const isSelected = isItemSelected(item);
    const isDisabled = getItemDisabled?.(item) || false;
    const isFocused = keyboardNavigation && focusedIndex === globalIndex;
    
    return (
      <li
        key={getItemKey ? getItemKey(item) : index}
        className={cn(
          'relative flex items-center justify-between',
          sizeClasses[size],
          hoverable && !isDisabled && 'hover:bg-gray-50 cursor-pointer',
          selectable && !isDisabled && 'cursor-pointer',
          isSelected && 'bg-blue-50 border-l-4 border-blue-500',
          isDisabled && 'opacity-50 cursor-not-allowed',
          isFocused && 'ring-2 ring-blue-500',
          variant === 'flush' && 'border-0'
        )}
        onClick={() => handleItemClick(item, globalIndex)}
        draggable={draggable && !isDisabled}
        onDragStart={(e) => handleDragStart(e, item)}
        onDragOver={handleDragOver}
        onDrop={(e) => handleDrop(e, item)}
      >
        <div className="flex-1">
          {renderItem(item, globalIndex)}
        </div>
        
        {actions && actions.length > 0 && (
          <div className="flex gap-2 ml-4">
            {actions.map((action, actionIndex) => (
              <button
                key={actionIndex}
                onClick={(e) => {
                  e.stopPropagation();
                  action.onClick(item);
                }}
                className={cn(
                  'px-2 py-1 text-xs rounded transition-colors',
                  action.variant === 'danger' 
                    ? 'text-red-600 hover:bg-red-50'
                    : action.variant === 'primary'
                    ? 'text-blue-600 hover:bg-blue-50'
                    : 'text-gray-600 hover:bg-gray-50'
                )}
              >
                {action.icon && <span className="mr-1">{action.icon}</span>}
                {action.label}
              </button>
            ))}
          </div>
        )}
      </li>
    );
  };

  if (loading) {
    return (
      <div data-testid="list-loading" className="flex items-center justify-center py-8">
        {loadingComponent || (
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 border-2 border-gray-300 border-t-blue-500 rounded-full animate-spin"></div>
            <span className="text-gray-500">Loading...</span>
          </div>
        )}
      </div>
    );
  }

  if (items.length === 0) {
    return (
      <div className="flex items-center justify-center py-8 text-gray-500">
        {emptyComponent || <div>{emptyText}</div>}
      </div>
    );
  }

  return (
    <div 
      className={cn('w-full', className)}
      data-testid={dataTestId}
      data-category={dataCategory}
      data-id={dataId}
      {...props}
    >
      {header && (
        <div className="mb-4">
          {header}
        </div>
      )}
      
      {searchable && (
        <div className="mb-4">
          <input
            type="text"
            placeholder={searchPlaceholder}
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
      )}
      
      <div
        className={cn(virtual && 'overflow-auto')}
        style={virtual ? { height: containerHeight } : undefined}
        data-testid={virtual ? 'virtual-list' : undefined}
      >
        <ul
          ref={listRef}
          className={cn(
            'list-none',
            variantClasses[variant]
          )}
        >
          {virtualItems.map((group, groupIndex) => (
            <React.Fragment key={groupIndex}>
              {group.group && renderGroup && (
                <li className="sticky top-0 bg-gray-100 px-4 py-2 font-medium text-gray-700 border-b">
                  {renderGroup(group.group)}
                </li>
              )}
              {group.items.map((item, itemIndex) => {
                const globalIndex = groupIndex * pageSize + itemIndex;
                return renderListItem(item, itemIndex, globalIndex);
              })}
            </React.Fragment>
          ))}
        </ul>
      </div>
      
      {infiniteScroll && hasMore && (
        <div
          ref={loadMoreRef}
          data-testid="loading-more"
          className="flex items-center justify-center py-4"
        >
          {loadingMore ? (
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 border-2 border-gray-300 border-t-blue-500 rounded-full animate-spin"></div>
              <span className="text-gray-500">Loading more...</span>
            </div>
          ) : (
            <span className="text-gray-400">Scroll for more</span>
          )}
        </div>
      )}
      
      {paginated && (
        <div className="flex items-center justify-between mt-4">
          <button
            onClick={() => {
              const newPage = Math.max(1, currentPageInternal - 1);
              setCurrentPageInternal(newPage);
              onPageChange?.(newPage);
            }}
            disabled={currentPageInternal === 1}
            className="px-3 py-1 bg-gray-100 rounded disabled:opacity-50"
          >
            Previous
          </button>
          
          <span className="text-sm text-gray-500">
            Page {currentPageInternal} of {Math.ceil(sortedItems.length / pageSize)}
          </span>
          
          <button
            onClick={() => {
              const newPage = Math.min(Math.ceil(sortedItems.length / pageSize), currentPageInternal + 1);
              setCurrentPageInternal(newPage);
              onPageChange?.(newPage);
            }}
            disabled={currentPageInternal >= Math.ceil(sortedItems.length / pageSize)}
            className="px-3 py-1 bg-gray-100 rounded disabled:opacity-50"
          >
            Next
          </button>
        </div>
      )}
      
      {footer && (
        <div className="mt-4">
          {footer}
        </div>
      )}
    </div>
  );
};

export default List;