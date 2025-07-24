import React, { useState, useRef, useEffect } from 'react';

export interface AccordionItem {
  id: string;
  title: string | React.ReactNode;
  content: React.ReactNode;
  disabled?: boolean;
  icon?: React.ReactNode;
  badge?: string | number;
}

interface AccordionProps {
  items: AccordionItem[];
  allowMultiple?: boolean;
  defaultExpandedItems?: string[];
  expandedItems?: string[];
  onItemToggle?: (itemId: string, isExpanded: boolean) => void;
  variant?: 'default' | 'bordered' | 'filled' | 'flush';
  size?: 'sm' | 'md' | 'lg';
  className?: string;
  itemClassName?: string;
  headerClassName?: string;
  contentClassName?: string;
  animated?: boolean;
  collapsible?: boolean;
  showIcon?: boolean;
  customIcon?: {
    expanded: React.ReactNode;
    collapsed: React.ReactNode;
  };
}

export const Accordion: React.FC<AccordionProps> = ({
  items,
  allowMultiple = false,
  defaultExpandedItems = [],
  expandedItems,
  onItemToggle,
  variant = 'default',
  size = 'md',
  className = '',
  itemClassName = '',
  headerClassName = '',
  contentClassName = '',
  animated = true,
  collapsible = true,
  showIcon = true,
  customIcon
}) => {
  const [internalExpandedItems, setInternalExpandedItems] = useState<Set<string>>(
    () => new Set(expandedItems || defaultExpandedItems)
  );

  const contentRefs = useRef<{ [key: string]: HTMLDivElement | null }>({});
  const currentExpandedItems = expandedItems ? new Set(expandedItems) : internalExpandedItems;

  const getSizeClasses = () => {
    const sizeMap = {
      sm: 'text-sm',
      md: 'text-base',
      lg: 'text-lg'
    };
    return sizeMap[size];
  };

  const getPaddingClasses = () => {
    const paddingMap = {
      sm: 'px-3 py-2',
      md: 'px-4 py-3',
      lg: 'px-6 py-4'
    };
    return paddingMap[size];
  };

  const getVariantClasses = () => {
    const variantMap = {
      default: 'border border-gray-200 rounded-lg',
      bordered: 'border border-gray-200',
      filled: 'bg-gray-50 border border-gray-200 rounded-lg',
      flush: 'border-0'
    };
    return variantMap[variant];
  };

  const getItemSpacing = () => {
    return variant === 'flush' ? '' : 'mb-2';
  };

  const handleItemToggle = (itemId: string, disabled?: boolean) => {
    if (disabled) return;

    const isCurrentlyExpanded = currentExpandedItems.has(itemId);
    
    if (!collapsible && currentExpandedItems.size === 1 && isCurrentlyExpanded) {
      return; // Prevent collapsing the last item if collapsible is false
    }

    let newExpandedItems: Set<string>;

    if (allowMultiple) {
      newExpandedItems = new Set(currentExpandedItems);
      if (isCurrentlyExpanded) {
        newExpandedItems.delete(itemId);
      } else {
        newExpandedItems.add(itemId);
      }
    } else {
      if (isCurrentlyExpanded && collapsible) {
        newExpandedItems = new Set();
      } else {
        newExpandedItems = new Set([itemId]);
      }
    }

    if (!expandedItems) {
      setInternalExpandedItems(newExpandedItems);
    }

    onItemToggle?.(itemId, newExpandedItems.has(itemId));
  };

  const handleKeyDown = (event: React.KeyboardEvent, itemId: string, disabled?: boolean) => {
    if (disabled) return;

    switch (event.key) {
      case 'Enter':
      case ' ':
        event.preventDefault();
        handleItemToggle(itemId, disabled);
        break;
      case 'ArrowDown':
        event.preventDefault();
        focusNextItem(itemId);
        break;
      case 'ArrowUp':
        event.preventDefault();
        focusPrevItem(itemId);
        break;
      case 'Home':
        event.preventDefault();
        focusFirstItem();
        break;
      case 'End':
        event.preventDefault();
        focusLastItem();
        break;
    }
  };

  const focusNextItem = (currentItemId: string) => {
    const currentIndex = items.findIndex(item => item.id === currentItemId);
    const enabledItems = items.filter(item => !item.disabled);
    const currentEnabledIndex = enabledItems.findIndex(item => item.id === currentItemId);
    const nextEnabledIndex = (currentEnabledIndex + 1) % enabledItems.length;
    const nextItem = enabledItems[nextEnabledIndex];
    
    const nextButton = document.getElementById(`accordion-header-${nextItem.id}`);
    nextButton?.focus();
  };

  const focusPrevItem = (currentItemId: string) => {
    const enabledItems = items.filter(item => !item.disabled);
    const currentEnabledIndex = enabledItems.findIndex(item => item.id === currentItemId);
    const prevEnabledIndex = currentEnabledIndex > 0 ? currentEnabledIndex - 1 : enabledItems.length - 1;
    const prevItem = enabledItems[prevEnabledIndex];
    
    const prevButton = document.getElementById(`accordion-header-${prevItem.id}`);
    prevButton?.focus();
  };

  const focusFirstItem = () => {
    const firstEnabledItem = items.find(item => !item.disabled);
    if (firstEnabledItem) {
      const firstButton = document.getElementById(`accordion-header-${firstEnabledItem.id}`);
      firstButton?.focus();
    }
  };

  const focusLastItem = () => {
    const enabledItems = items.filter(item => !item.disabled);
    const lastEnabledItem = enabledItems[enabledItems.length - 1];
    if (lastEnabledItem) {
      const lastButton = document.getElementById(`accordion-header-${lastEnabledItem.id}`);
      lastButton?.focus();
    }
  };

  const getContentHeight = (itemId: string, isExpanded: boolean) => {
    if (!animated) return isExpanded ? 'auto' : '0';
    
    const contentEl = contentRefs.current[itemId];
    if (!contentEl) return isExpanded ? 'auto' : '0';
    
    return isExpanded ? `${contentEl.scrollHeight}px` : '0';
  };

  const renderIcon = (isExpanded: boolean) => {
    if (!showIcon) return null;
    
    if (customIcon) {
      return isExpanded ? customIcon.expanded : customIcon.collapsed;
    }
    
    return (
      <svg
        className={`w-5 h-5 transition-transform duration-200 ${
          isExpanded ? 'rotate-180' : 'rotate-0'
        }`}
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
      >
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
      </svg>
    );
  };

  return (
    <div className={`${className}`} role="presentation">
      {items.map((item, index) => {
        const isExpanded = currentExpandedItems.has(item.id);
        const isLastItem = index === items.length - 1;

        return (
          <div
            key={item.id}
            className={`
              ${getVariantClasses()}
              ${!isLastItem ? getItemSpacing() : ''}
              ${itemClassName}
            `}
          >
            <button
              id={`accordion-header-${item.id}`}
              className={`
                w-full text-left flex items-center justify-between
                ${getPaddingClasses()}
                ${getSizeClasses()}
                ${item.disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer hover:bg-gray-50'}
                transition-colors duration-200
                ${variant === 'flush' && !isLastItem ? 'border-b border-gray-200' : ''}
                ${headerClassName}
              `}
              onClick={() => handleItemToggle(item.id, item.disabled)}
              onKeyDown={(e) => handleKeyDown(e, item.id, item.disabled)}
              disabled={item.disabled}
              aria-expanded={isExpanded}
              aria-controls={`accordion-content-${item.id}`}
              aria-disabled={item.disabled}
              role="button"
              tabIndex={0}
            >
              <div className="flex items-center gap-3 flex-1 min-w-0">
                {item.icon && (
                  <span className="flex-shrink-0" aria-hidden="true">
                    {item.icon}
                  </span>
                )}
                <span className="flex-1 truncate font-medium text-gray-900">
                  {item.title}
                </span>
                {item.badge && (
                  <span className="bg-blue-100 text-blue-800 text-xs font-medium px-2 py-1 rounded-full flex-shrink-0">
                    {item.badge}
                  </span>
                )}
              </div>
              
              {renderIcon(isExpanded)}
            </button>

            <div
              id={`accordion-content-${item.id}`}
              className={`
                overflow-hidden
                ${animated ? 'transition-all duration-300 ease-in-out' : ''}
              `}
              style={{
                height: getContentHeight(item.id, isExpanded),
              }}
              role="region"
              aria-labelledby={`accordion-header-${item.id}`}
              aria-hidden={!isExpanded}
            >
              <div
                ref={(el) => {
                  contentRefs.current[item.id] = el;
                }}
                className={`
                  ${getPaddingClasses()}
                  ${variant === 'flush' && !isLastItem ? 'border-b border-gray-200' : ''}
                  text-gray-700
                  ${contentClassName}
                `}
              >
                {item.content}
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
};

export default Accordion;