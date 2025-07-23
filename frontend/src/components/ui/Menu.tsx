import React, { useState, useEffect, useRef, useCallback, useMemo } from 'react';
import { cn } from '@/lib/utils';

export interface MenuItem {
  id: string;
  label?: string;
  type?: 'item' | 'header' | 'divider';
  icon?: React.ReactNode;
  badge?: string | number;
  shortcut?: string;
  description?: string;
  disabled?: boolean;
  children?: MenuItem[];
  onClick?: () => void;
}

export interface MenuProps {
  items: MenuItem[];
  className?: string;
  orientation?: 'horizontal' | 'vertical';
  size?: 'sm' | 'md' | 'lg';
  variant?: 'default' | 'pills' | 'tabs' | 'minimal';
  selectable?: boolean;
  multiple?: boolean;
  selectedItems?: string[];
  onSelect?: (selected: string | string[]) => void;
  keyboardNavigation?: boolean;
  disabled?: boolean;
  loading?: boolean;
  loadingComponent?: React.ReactNode;
  searchable?: boolean;
  searchPlaceholder?: string;
  collapsible?: boolean;
  autoClose?: boolean;
  onClose?: () => void;
  trigger?: React.ReactNode;
  position?: 'top' | 'bottom' | 'left' | 'right';
  contextMenu?: boolean;
  width?: number;
  maxHeight?: number;
  renderItem?: (item: MenuItem, level?: number) => React.ReactNode;
  'data-testid'?: string;
  'data-category'?: string;
  'data-id'?: string;
}

export const Menu: React.FC<MenuProps> = ({
  items,
  className,
  orientation = 'vertical',
  size = 'md',
  variant = 'default',
  selectable = false,
  multiple = false,
  selectedItems = [],
  onSelect,
  keyboardNavigation = false,
  disabled = false,
  loading = false,
  loadingComponent,
  searchable = false,
  searchPlaceholder = 'Search...',
  collapsible = false,
  autoClose = false,
  onClose,
  trigger,
  position = 'bottom',
  contextMenu = false,
  width,
  maxHeight,
  renderItem,
  'data-testid': dataTestId = 'menu-container',
  'data-category': dataCategory,
  'data-id': dataId,
  ...props
}) => {
  const [focusedIndex, setFocusedIndex] = useState(-1);
  const [openSubmenus, setOpenSubmenus] = useState<Set<string>>(new Set());
  const [internalSelectedItems, setInternalSelectedItems] = useState<string[]>(selectedItems);
  const [searchQuery, setSearchQuery] = useState('');
  const menuRef = useRef<HTMLDivElement>(null);
  const itemRefs = useRef<{ [key: string]: HTMLElement | null }>({});

  const sizeClasses = {
    sm: 'text-sm py-1 px-2',
    md: 'text-base py-2 px-3',
    lg: 'text-lg py-3 px-4'
  };

  const variantClasses = {
    default: 'bg-white border border-gray-200 rounded-md shadow-md',
    pills: 'bg-transparent',
    tabs: 'border-b border-gray-200',
    minimal: 'bg-transparent'
  };

  // Filter items based on search query
  const filteredItems = useMemo(() => {
    if (!searchable || !searchQuery) return items;
    
    const filterItems = (items: MenuItem[]): MenuItem[] => {
      return items.filter(item => {
        if (item.type === 'divider') return false;
        if (item.type === 'header') return true;
        
        const matchesSearch = item.label?.toLowerCase().includes(searchQuery.toLowerCase()) ||
                            item.description?.toLowerCase().includes(searchQuery.toLowerCase());
        
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

  // Get all focusable items (flatten nested structure)
  const focusableItems = useMemo(() => {
    const flatten = (items: MenuItem[], level = 0): Array<{item: MenuItem, level: number}> => {
      return items.reduce((acc, item) => {
        if (item.type === 'item' && !item.disabled) {
          acc.push({ item, level });
        }
        if (item.children && openSubmenus.has(item.id)) {
          acc.push(...flatten(item.children, level + 1));
        }
        return acc;
      }, [] as Array<{item: MenuItem, level: number}>);
    };
    
    return flatten(filteredItems);
  }, [filteredItems, openSubmenus]);

  const handleItemClick = useCallback((item: MenuItem) => {
    if (!item || item.disabled) return;
    
    if (item.children) {
      if (collapsible) {
        setOpenSubmenus(prev => {
          const newSet = new Set(prev);
          if (newSet.has(item.id)) {
            newSet.delete(item.id);
          } else {
            newSet.add(item.id);
          }
          return newSet;
        });
      }
      return;
    }
    
    if (selectable) {
      let newSelection: string[];
      
      if (multiple) {
        const isSelected = internalSelectedItems.includes(item.id);
        newSelection = isSelected
          ? internalSelectedItems.filter(id => id !== item.id)
          : [...internalSelectedItems, item.id];
      } else {
        newSelection = internalSelectedItems.includes(item.id) ? [] : [item.id];
      }
      
      setInternalSelectedItems(newSelection);
      onSelect?.(multiple ? newSelection : newSelection[0] || '');
    }
    
    item.onClick?.();
    
    if (autoClose && onClose) {
      onClose();
    }
  }, [selectable, multiple, internalSelectedItems, onSelect, collapsible, autoClose, onClose]);

  // Keyboard navigation
  useEffect(() => {
    if (!keyboardNavigation || !menuRef.current) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      const totalItems = focusableItems.length;
      
      switch (e.key) {
        case 'ArrowDown':
          e.preventDefault();
          setFocusedIndex(prev => {
            const newIndex = prev < 0 ? 0 : (prev + 1) % totalItems;
            return newIndex;
          });
          break;
        case 'ArrowUp':
          e.preventDefault();
          setFocusedIndex(prev => {
            const newIndex = prev <= 0 ? totalItems - 1 : prev - 1;
            return newIndex;
          });
          break;
        case 'ArrowRight':
          e.preventDefault();
          if (focusedIndex >= 0) {
            const currentItem = focusableItems[focusedIndex]?.item;
            if (currentItem?.children) {
              setOpenSubmenus(prev => new Set([...prev, currentItem.id]));
            }
          }
          break;
        case 'ArrowLeft':
          e.preventDefault();
          if (focusedIndex >= 0) {
            const currentItem = focusableItems[focusedIndex]?.item;
            if (currentItem?.children) {
              setOpenSubmenus(prev => {
                const newSet = new Set(prev);
                newSet.delete(currentItem.id);
                return newSet;
              });
            }
          }
          break;
        case 'Enter':
        case ' ':
          e.preventDefault();
          if (focusedIndex >= 0 && focusedIndex < focusableItems.length) {
            const currentItem = focusableItems[focusedIndex]?.item;
            if (currentItem) {
              handleItemClick(currentItem);
            }
          }
          break;
        case 'Escape':
          if (onClose) onClose();
          break;
      }
    };

    const menuElement = menuRef.current;
    menuElement.addEventListener('keydown', handleKeyDown);
    return () => menuElement.removeEventListener('keydown', handleKeyDown);
  }, [keyboardNavigation, focusableItems, focusedIndex, onClose, handleItemClick]);

  const handleMouseEnter = useCallback((item: MenuItem) => {
    if (item.children && !collapsible) {
      setOpenSubmenus(prev => new Set([...prev, item.id]));
    }
  }, [collapsible]);

  const handleMouseLeave = useCallback((item: MenuItem) => {
    if (item.children && !collapsible) {
      setTimeout(() => {
        setOpenSubmenus(prev => {
          const newSet = new Set(prev);
          newSet.delete(item.id);
          return newSet;
        });
      }, 100);
    }
  }, [collapsible]);

  const renderMenuItem = (item: MenuItem, level: number = 0): React.ReactNode => {
    if (renderItem) {
      return (
        <div key={item.id}>
          {renderItem(item, level)}
        </div>
      );
    }

    const isSelected = internalSelectedItems.includes(item.id);
    const isFocused = keyboardNavigation && 
      focusableItems.findIndex(f => f.item.id === item.id) === focusedIndex;
    const hasSubmenu = item.children && item.children.length > 0;
    const isSubmenuOpen = openSubmenus.has(item.id);

    if (item.type === 'divider') {
      return (
        <div
          key={item.id}
          data-testid="menu-divider"
          className="my-1 h-px bg-gray-200"
        />
      );
    }

    if (item.type === 'header') {
      return (
        <div
          key={item.id}
          data-testid="menu-header"
          className="px-3 py-2 text-xs font-semibold text-gray-500 uppercase tracking-wider"
        >
          {item.label}
        </div>
      );
    }

    return (
      <div key={item.id} className={cn(level > 0 && `ml-${level * 4}`)}>
        <button
          ref={el => { itemRefs.current[item.id] = el; }}
          disabled={disabled || item.disabled}
          className={cn(
            'w-full flex items-center justify-between text-left transition-colors',
            sizeClasses[size],
            variant === 'pills' && 'rounded-full',
            variant === 'tabs' && 'border-b-2 border-transparent',
            item.disabled && 'opacity-50 cursor-not-allowed',
            !item.disabled && 'hover:bg-gray-50',
            isSelected && variant === 'default' && 'bg-blue-100 text-blue-700',
            isSelected && variant === 'pills' && 'bg-blue-500 text-white',
            isSelected && variant === 'tabs' && 'border-blue-500 text-blue-600',
            isFocused && 'ring-2 ring-blue-500 ring-inset'
          )}
          onClick={() => handleItemClick(item)}
          onMouseEnter={() => handleMouseEnter(item)}
          onMouseLeave={() => handleMouseLeave(item)}
        >
          <div className="flex items-center gap-2 flex-1">
            {item.icon && <span className="flex-shrink-0">{item.icon}</span>}
            
            <div className="flex-1 min-w-0">
              <div className="truncate">{item.label}</div>
              {item.description && (
                <div className="text-xs text-gray-500 truncate">
                  {item.description}
                </div>
              )}
            </div>
          </div>
          
          <div className="flex items-center gap-2">
            {item.badge && (
              <span className="px-1.5 py-0.5 text-xs bg-red-100 text-red-800 rounded-full">
                {item.badge}
              </span>
            )}
            
            {item.shortcut && (
              <span className="text-xs text-gray-400">
                {item.shortcut}
              </span>
            )}
            
            {hasSubmenu && (
              <span className={cn(
                'text-gray-400 transition-transform',
                isSubmenuOpen && 'rotate-90'
              )}>
                ▶
              </span>
            )}
          </div>
        </button>
        
        {hasSubmenu && isSubmenuOpen && (
          <div className="ml-4 mt-1 border-l border-gray-200 pl-2">
            {item.children!.map(child => renderMenuItem(child, level + 1))}
          </div>
        )}
      </div>
    );
  };

  if (loading) {
    return (
      <div data-testid="menu-loading" className="flex items-center justify-center py-4">
        {loadingComponent || (
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 border-2 border-gray-300 border-t-blue-500 rounded-full animate-spin"></div>
            <span className="text-gray-500">Loading...</span>
          </div>
        )}
      </div>
    );
  }

  return (
    <div
      ref={menuRef}
      tabIndex={keyboardNavigation ? 0 : -1}
      className={cn(
        'menu',
        orientation === 'horizontal' ? 'flex flex-row' : 'flex flex-col',
        variantClasses[variant],
        contextMenu && 'absolute z-50',
        maxHeight && 'overflow-auto',
        keyboardNavigation && 'focus:outline-none',
        className
      )}
      style={{
        width: width ? `${width}px` : undefined,
        maxHeight: maxHeight ? `${maxHeight}px` : undefined,
      }}
      data-testid={dataTestId}
      data-category={dataCategory}
      data-id={dataId}
      {...props}
    >
      {trigger && (
        <div className="menu-trigger">
          {trigger}
        </div>
      )}
      
      {searchable && (
        <div className="p-2 border-b border-gray-200">
          <input
            type="text"
            placeholder={searchPlaceholder}
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full px-2 py-1 text-sm border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500"
          />
        </div>
      )}
      
      <div className="menu-items">
        {filteredItems.map(item => renderMenuItem(item))}
      </div>
    </div>
  );
};

export default Menu;