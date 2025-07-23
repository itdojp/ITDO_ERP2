import React, { useState, useEffect, useRef, useMemo, useCallback } from 'react';
import { cn } from '@/lib/utils';

export interface SidebarItem {
  id: string;
  label?: string;
  type?: 'item' | 'header' | 'divider';
  icon?: React.ReactNode;
  href?: string;
  badge?: string | number;
  current?: boolean;
  disabled?: boolean;
  sticky?: boolean;
  children?: SidebarItem[];
  onClick?: (e: React.MouseEvent) => void;
}

export interface SidebarProps {
  items: SidebarItem[];
  position?: 'left' | 'right';
  size?: 'sm' | 'md' | 'lg';
  variant?: 'default' | 'minimal' | 'elevated';
  theme?: 'light' | 'dark';
  collapsible?: boolean;
  collapsed?: boolean;
  overlay?: boolean;
  showBackdrop?: boolean;
  resizable?: boolean;
  searchable?: boolean;
  searchPlaceholder?: string;
  keyboardNavigation?: boolean;
  showTooltips?: boolean;
  scrollable?: boolean;
  responsive?: boolean;
  autoClose?: boolean;
  loading?: boolean;
  loadingComponent?: React.ReactNode;
  width?: number;
  minWidth?: number;
  maxWidth?: number;
  header?: React.ReactNode;
  footer?: React.ReactNode;
  renderItem?: (item: SidebarItem, level?: number) => React.ReactNode;
  onToggle?: (collapsed: boolean) => void;
  onItemClick?: (item: SidebarItem) => void;
  onClose?: () => void;
  onResize?: (width: number) => void;
  className?: string;
  'data-testid'?: string;
  'data-category'?: string;
  'data-id'?: string;
}

export const Sidebar: React.FC<SidebarProps> = ({
  items,
  position = 'left',
  size = 'md',
  variant = 'default',
  theme = 'light',
  collapsible = false,
  collapsed: controlledCollapsed,
  overlay = false,
  showBackdrop = false,
  resizable = false,
  searchable = false,
  searchPlaceholder = 'Search...',
  keyboardNavigation = false,
  showTooltips = false,
  scrollable = true,
  responsive = false,
  autoClose = false,
  loading = false,
  loadingComponent,
  width = 250,
  minWidth = 200,
  maxWidth = 400,
  header,
  footer,
  renderItem,
  onToggle,
  onItemClick,
  onClose,
  onResize,
  className,
  'data-testid': dataTestId = 'sidebar-container',
  'data-category': dataCategory,
  'data-id': dataId,
  ...props
}) => {
  const [internalCollapsed, setInternalCollapsed] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [openItems, setOpenItems] = useState<Set<string>>(new Set());
  const [focusedIndex, setFocusedIndex] = useState(-1);
  const [currentWidth, setCurrentWidth] = useState(width);
  const [isResizing, setIsResizing] = useState(false);
  const sidebarRef = useRef<HTMLDivElement>(null);
  const resizeStartX = useRef<number>(0);
  const resizeStartWidth = useRef<number>(width);

  const isCollapsed = controlledCollapsed !== undefined ? controlledCollapsed : internalCollapsed;

  const sizeClasses = {
    sm: 'text-sm py-1 px-2',
    md: 'text-base py-2 px-3',
    lg: 'text-lg py-3 px-4'
  };

  const variantClasses = {
    default: 'bg-white border-r border-gray-200',
    minimal: 'bg-transparent',
    elevated: 'bg-white shadow-lg'
  };

  const themeClasses = {
    light: 'bg-white text-gray-900 border-gray-200',
    dark: 'bg-gray-900 text-white border-gray-700'
  };

  // Filter items based on search query
  const filteredItems = useMemo(() => {
    if (!searchable || !searchQuery) return items;
    
    const filterItems = (items: SidebarItem[]): SidebarItem[] => {
      return items.filter(item => {
        if (item.type !== 'item' && item.type !== undefined) return true;
        
        const matchesSearch = item.label?.toLowerCase().includes(searchQuery.toLowerCase());
        if (matchesSearch) return true;
        
        if (item.children) {
          const filteredChildren = filterItems(item.children);
          return filteredChildren.length > 0;
        }
        
        return false;
      }).map(item => ({
        ...item,
        children: item.children ? filterItems(item.children) : undefined
      }));
    };
    
    return filterItems(items);
  }, [items, searchQuery, searchable]);

  // Handle toggle
  const handleToggle = useCallback(() => {
    const newCollapsed = !isCollapsed;
    setInternalCollapsed(newCollapsed);
    onToggle?.(newCollapsed);
  }, [isCollapsed, onToggle]);

  // Handle item click
  const handleItemClick = useCallback((item: SidebarItem, e?: React.MouseEvent) => {
    if (item.disabled) return;
    
    if (item.children && item.children.length > 0) {
      setOpenItems(prev => {
        const newSet = new Set(prev);
        if (newSet.has(item.id)) {
          newSet.delete(item.id);
        } else {
          newSet.add(item.id);
        }
        return newSet;
      });
    }
    
    item.onClick?.(e!);
    onItemClick?.(item);
    
    if (overlay && autoClose && onToggle) {
      onToggle(false);
    }
  }, [overlay, autoClose, onToggle, onItemClick]);

  // Handle resize
  const handleMouseDown = useCallback((e: React.MouseEvent) => {
    if (!resizable) return;
    
    setIsResizing(true);
    resizeStartX.current = e.clientX;
    resizeStartWidth.current = currentWidth;
    
    const handleMouseMove = (e: MouseEvent) => {
      const delta = position === 'left' ? e.clientX - resizeStartX.current : resizeStartX.current - e.clientX;
      const newWidth = Math.min(maxWidth, Math.max(minWidth, resizeStartWidth.current + delta));
      setCurrentWidth(newWidth);
      onResize?.(newWidth);
    };
    
    const handleMouseUp = () => {
      setIsResizing(false);
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
    };
    
    document.addEventListener('mousemove', handleMouseMove);
    document.addEventListener('mouseup', handleMouseUp);
  }, [resizable, position, currentWidth, minWidth, maxWidth, onResize]);

  // Keyboard navigation
  useEffect(() => {
    if (!keyboardNavigation || !sidebarRef.current) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      const focusableItems = filteredItems.filter(item => 
        item.type === 'item' && !item.disabled
      );
      const totalItems = focusableItems.length;
      
      switch (e.key) {
        case 'ArrowDown':
          e.preventDefault();
          setFocusedIndex(prev => (prev + 1) % totalItems);
          break;
        case 'ArrowUp':
          e.preventDefault();
          setFocusedIndex(prev => (prev - 1 + totalItems) % totalItems);
          break;
        case 'Enter':
        case ' ':
          e.preventDefault();
          if (focusedIndex >= 0) {
            const currentItem = focusableItems[focusedIndex];
            handleItemClick(currentItem);
          }
          break;
      }
    };

    const sidebarElement = sidebarRef.current;
    sidebarElement.addEventListener('keydown', handleKeyDown);
    return () => sidebarElement.removeEventListener('keydown', handleKeyDown);
  }, [keyboardNavigation, filteredItems, focusedIndex, handleItemClick]);

  const renderSidebarItem = (item: SidebarItem, level: number = 0): React.ReactNode => {
    if (renderItem) {
      return (
        <div key={item.id}>
          {renderItem(item, level)}
        </div>
      );
    }

    if (item.type === 'divider') {
      return (
        <div
          key={item.id}
          data-testid="sidebar-divider"
          className="my-2 h-px bg-gray-200"
        />
      );
    }

    if (item.type === 'header') {
      return (
        <div
          key={item.id}
          className={cn(
            'px-3 py-2 text-xs font-semibold text-gray-500 uppercase tracking-wider',
            isCollapsed && 'text-center'
          )}
        >
          {!isCollapsed && item.label}
        </div>
      );
    }

    const isCurrent = item.current;
    const hasChildren = item.children && item.children.length > 0;
    const isOpen = openItems.has(item.id);

    return (
      <div key={item.id} className={cn(level > 0 && !isCollapsed && 'ml-4')}>
        <div className={cn(item.sticky && 'sticky bottom-0 bg-inherit')}>
          <a
            href={item.href}
            className={cn(
              'relative flex items-center transition-colors',
              sizeClasses[size],
              item.disabled && 'opacity-50 pointer-events-none cursor-not-allowed',
              !item.disabled && 'hover:bg-gray-100 cursor-pointer',
              isCurrent && 'bg-blue-100 text-blue-700 border-r-2 border-blue-500',
              isCollapsed && 'justify-center',
              'group'
            )}
            onClick={(e) => {
              e.preventDefault();
              handleItemClick(item, e);
            }}
            aria-disabled={item.disabled}
            title={isCollapsed && showTooltips ? item.label : undefined}
          >
            {item.icon && (
              <span className={cn('flex-shrink-0', !isCollapsed && 'mr-3')}>
                {item.icon}
              </span>
            )}
            
            {!isCollapsed && (
              <>
                <span className="flex-1 truncate">{item.label}</span>
                
                {item.badge && (
                  <span className="ml-2 px-1.5 py-0.5 text-xs bg-red-100 text-red-800 rounded-full">
                    {item.badge}
                  </span>
                )}
                
                {hasChildren && (
                  <span className={cn(
                    'ml-2 transition-transform',
                    isOpen && 'rotate-90'
                  )}>
                    ▶
                  </span>
                )}
              </>
            )}
            
            {/* Tooltip for collapsed mode */}
            {isCollapsed && showTooltips && (
              <div className="absolute left-full ml-2 px-2 py-1 bg-gray-900 text-white text-sm rounded opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none whitespace-nowrap z-50">
                {item.label}
              </div>
            )}
          </a>
        </div>
        
        {hasChildren && isOpen && !isCollapsed && (
          <div className="mt-1">
            {item.children!.map(child => renderSidebarItem(child, level + 1))}
          </div>
        )}
      </div>
    );
  };

  const renderSidebarContent = () => (
    <>
      {/* Header */}
      {header && (
        <div className={cn('flex-shrink-0 p-4', isCollapsed && 'px-2')}>
          {header}
        </div>
      )}
      
      {/* Collapse Button */}
      {collapsible && (
        <button
          data-testid="sidebar-collapse-btn"
          onClick={handleToggle}
          className={cn(
            'flex items-center justify-center p-2 m-2 rounded hover:bg-gray-100 transition-colors',
            isCollapsed && 'mx-auto'
          )}
        >
          <span className={cn('transform transition-transform', isCollapsed && 'rotate-180')}>
            {position === 'left' ? '◀' : '▶'}
          </span>
        </button>
      )}
      
      {/* Search */}
      {searchable && !isCollapsed && (
        <div className="flex-shrink-0 p-4">
          <input
            type="text"
            placeholder={searchPlaceholder}
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-1 focus:ring-blue-500"
          />
        </div>
      )}
      
      {/* Loading State */}
      {loading ? (
        <div data-testid="sidebar-loading" className="flex-1 flex items-center justify-center">
          {loadingComponent || (
            <div className="flex flex-col items-center gap-2">
              <div className="w-6 h-6 border-2 border-gray-300 border-t-blue-500 rounded-full animate-spin"></div>
              {!isCollapsed && <span className="text-sm text-gray-500">Loading...</span>}
            </div>
          )}
        </div>
      ) : (
        /* Sidebar Items */
        <nav className="flex-1 py-2">
          {filteredItems.map(item => renderSidebarItem(item))}
        </nav>
      )}
      
      {/* Footer */}
      {footer && (
        <div className={cn('flex-shrink-0 p-4', isCollapsed && 'px-2')}>
          {footer}
        </div>
      )}
      
      {/* Resize Handle */}
      {resizable && (
        <div
          data-testid="sidebar-resize-handle"
          className={cn(
            'absolute top-0 w-1 h-full cursor-col-resize hover:bg-blue-500 transition-colors',
            position === 'left' ? '-right-0.5' : '-left-0.5'
          )}
          onMouseDown={handleMouseDown}
        />
      )}
    </>
  );

  if (overlay) {
    return (
      <>
        {/* Backdrop */}
        {showBackdrop && (
          <div
            data-testid="sidebar-backdrop"
            className="fixed inset-0 bg-black bg-opacity-50 z-40"
            onClick={onClose}
          />
        )}
        
        {/* Overlay Sidebar */}
        <div
          ref={sidebarRef}
          className={cn(
            'fixed top-0 h-full z-50 sidebar flex flex-col',
            position === 'left' ? 'left-0' : 'right-0',
            variantClasses[variant],
            themeClasses[theme],
            `theme-${theme}`,
            scrollable && 'overflow-auto',
            responsive && 'responsive-sidebar',
            keyboardNavigation && 'focus:outline-none',
            className
          )}
          data-testid={dataTestId}
          data-category={dataCategory}
          data-id={dataId}
          style={{
            width: isCollapsed ? '4rem' : `${currentWidth}px`,
            transition: isResizing ? 'none' : 'width 0.3s ease'
          }}
          tabIndex={keyboardNavigation ? 0 : -1}
          {...props}
        >
          {renderSidebarContent()}
        </div>
      </>
    );
  }

  return (
    <div
      ref={sidebarRef}
      className={cn(
        'relative h-full sidebar flex flex-col',
        position === 'left' ? 'left-0' : 'right-0',
        variantClasses[variant],
        themeClasses[theme],
        `theme-${theme}`,
        scrollable && 'overflow-auto',
        responsive && 'responsive-sidebar',
        keyboardNavigation && 'focus:outline-none',
        className
      )}
      data-testid={dataTestId}
      data-category={dataCategory}
      data-id={dataId}
      style={{
        width: isCollapsed ? '4rem' : `${currentWidth}px`,
        transition: isResizing ? 'none' : 'width 0.3s ease'
      }}
      tabIndex={keyboardNavigation ? 0 : -1}
      {...props}
    >
      {renderSidebarContent()}
    </div>
  );
};

export default Sidebar;