import React, { useState, useEffect, useCallback, useRef } from 'react';
import { cn } from '@/lib/utils';

export interface AnchorItem {
  href: string;
  title: string;
  disabled?: boolean;
  children?: AnchorItem[];
}

export interface AnchorProps {
  items?: AnchorItem[];
  children?: React.ReactNode;
  className?: string;
  style?: React.CSSProperties;
  direction?: 'vertical' | 'horizontal';
  size?: 'small' | 'medium' | 'large';
  offsetTop?: number;
  smooth?: boolean;
  fixed?: boolean;
  sticky?: boolean;
  bounds?: number;
  title?: string;
  collapsible?: boolean;
  targetContainer?: () => HTMLElement;
  animated?: boolean;
  showIndicator?: boolean;
  scrollSpy?: boolean;
  scrollContainer?: () => HTMLElement;
  hoverEffect?: boolean;
  preventDefault?: boolean;
  autoScroll?: boolean;
  renderLink?: (item: AnchorItem) => React.ReactNode;
  onChange?: (href: string) => void;
  onClick?: (e: React.MouseEvent, href: string) => void;
  'data-testid'?: string;
  'data-role'?: string;
}

interface AnchorLinkProps {
  href: string;
  title: string;
  disabled?: boolean;
  children?: AnchorItem[];
}

const AnchorLink: React.FC<AnchorLinkProps> = ({ href, title, disabled, children }) => {
  return (
    <div>
      <a
        href={href}
        className={cn(
          'block py-1 px-2 text-sm transition-colors hover:text-blue-600',
          disabled && 'opacity-50 cursor-not-allowed pointer-events-none'
        )}
      >
        {title}
      </a>
      {children && children.length > 0 && (
        <div className="ml-4">
          {children.map((child, index) => (
            <AnchorLink
              key={index}
              href={child.href}
              title={child.title}
              disabled={child.disabled}
              children={child.children}
            />
          ))}
        </div>
      )}
    </div>
  );
};

export const Anchor: React.FC<AnchorProps> & {
  Link: React.FC<AnchorLinkProps>;
} = ({
  items = [],
  children,
  className,
  style,
  direction = 'vertical',
  size = 'medium',
  offsetTop = 0,
  smooth = false,
  fixed = false,
  sticky = false,
  bounds = 5,
  title,
  collapsible = false,
  targetContainer,
  animated = false,
  showIndicator = false,
  scrollSpy = true,
  scrollContainer,
  hoverEffect = false,
  preventDefault = false,
  autoScroll = false,
  renderLink,
  onChange,
  onClick,
  'data-testid': dataTestId = 'anchor-container',
  'data-role': dataRole,
  ...props
}) => {
  const [activeHref, setActiveHref] = useState<string>('');
  const [collapsed, setCollapsed] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  const sizeClasses = {
    small: 'text-xs',
    medium: 'text-sm',
    large: 'text-base'
  };

  const scrollToElement = useCallback((href: string) => {
    const target = document.querySelector(href.replace('#', '#'));
    if (target) {
      const container = targetContainer ? targetContainer() : window;
      const rect = target.getBoundingClientRect();
      const scrollTop = container === window 
        ? window.pageYOffset 
        : (container as HTMLElement).scrollTop;
      
      const targetPosition = rect.top + scrollTop - offsetTop;

      if (container === window) {
        window.scrollTo({
          top: targetPosition,
          behavior: smooth ? 'smooth' : 'auto'
        });
      } else {
        (container as HTMLElement).scrollTo({
          top: targetPosition,
          behavior: smooth ? 'smooth' : 'auto'
        });
      }
    }
  }, [offsetTop, smooth, targetContainer]);

  const handleLinkClick = useCallback((e: React.MouseEvent, href: string) => {
    if (preventDefault) {
      e.preventDefault();
    }
    
    if (onClick) {
      onClick(e, href);
    }
    
    if (!preventDefault) {
      scrollToElement(href);
    }
    
    if (onChange) {
      onChange(href);
    }
    
    setActiveHref(href);
  }, [preventDefault, onClick, scrollToElement, onChange]);

  const updateActiveLink = useCallback(() => {
    if (!scrollSpy) return;

    const container = scrollContainer ? scrollContainer() : window;
    const scrollTop = container === window 
      ? window.pageYOffset 
      : (container as HTMLElement).scrollTop;

    const allItems = items.length > 0 ? items : [];
    let foundActive = false;
    
    for (const item of allItems) {
      const target = document.querySelector(item.href);
      if (target) {
        const rect = target.getBoundingClientRect();
        const elementTop = rect.top + scrollTop;
        
        // Check if the element is in the viewport with the scroll position
        if (scrollTop >= elementTop - offsetTop - bounds) {
          setActiveHref(item.href);
          if (onChange) {
            onChange(item.href);
          }
          foundActive = true;
        }
      }
    }
    
    // If no active found and we have items, set the first one as active
    if (!foundActive && allItems.length > 0) {
      setActiveHref(allItems[0].href);
      if (onChange) {
        onChange(allItems[0].href);
      }
    }
  }, [scrollSpy, scrollContainer, items, bounds, offsetTop, onChange]);

  useEffect(() => {
    if (scrollSpy) {
      const container = scrollContainer ? scrollContainer() : window;
      container.addEventListener('scroll', updateActiveLink);
      
      // Trigger initial update
      setTimeout(updateActiveLink, 0);
      
      return () => {
        container.removeEventListener('scroll', updateActiveLink);
      };
    }
  }, [scrollSpy, scrollContainer, updateActiveLink]);

  useEffect(() => {
    if (autoScroll && window.location.hash) {
      const href = window.location.hash;
      scrollToElement(href);
      setActiveHref(href);
    }
  }, [autoScroll, scrollToElement]);

  const renderAnchorItem = (item: AnchorItem, isActive: boolean) => {
    if (renderLink) {
      return renderLink(item);
    }

    return (
      <a
        key={item.href}
        href={item.href}
        className={cn(
          'block py-1 px-2 transition-colors',
          isActive && 'text-blue-600 font-medium',
          !isActive && 'text-gray-600 hover:text-blue-600',
          item.disabled && 'opacity-50 cursor-not-allowed pointer-events-none',
          hoverEffect && 'hover:bg-gray-100',
          sizeClasses[size]
        )}
        onClick={(e) => !item.disabled && handleLinkClick(e, item.href)}
      >
        {showIndicator && isActive && (
          <span className="inline-block w-1 h-4 bg-blue-600 mr-2"></span>
        )}
        {item.title}
      </a>
    );
  };

  const renderItems = () => {
    if (children) {
      return React.Children.map(children, (child) => {
        if (React.isValidElement(child) && child.type === AnchorLink) {
          const isActive = activeHref === child.props.href;
          return React.cloneElement(child, {
            ...child.props,
            className: cn(
              child.props.className,
              isActive && 'text-blue-600 font-medium'
            )
          });
        }
        return child;
      });
    }

    return items.map((item) => {
      const isActive = activeHref === item.href;
      return (
        <div key={item.href}>
          {renderAnchorItem(item, isActive)}
          {item.children && item.children.length > 0 && (
            <div className="ml-4">
              {item.children.map((child) => {
                const childIsActive = activeHref === child.href;
                return renderAnchorItem(child, childIsActive);
              })}
            </div>
          )}
        </div>
      );
    });
  };

  return (
    <div
      ref={containerRef}
      className={cn(
        'anchor-navigation',
        direction === 'horizontal' && 'flex flex-row space-x-4',
        direction === 'vertical' && 'flex flex-col space-y-1',
        fixed && 'fixed',
        sticky && 'sticky top-0',
        animated && 'transition-all duration-200',
        className
      )}
      style={style}
      data-testid={dataTestId}
      data-role={dataRole}
      {...props}
    >
      {title && (
        <div className="font-medium text-gray-900 mb-2 px-2">
          {title}
        </div>
      )}
      
      {collapsible && (
        <button
          className="flex items-center justify-between w-full p-2 text-left"
          onClick={() => setCollapsed(!collapsed)}
        >
          <span>Navigation</span>
          <span className={cn('transform transition-transform', collapsed && 'rotate-180')}>
            ▼
          </span>
        </button>
      )}
      
      <div className={cn(collapsible && collapsed && 'hidden')}>
        {renderItems()}
      </div>
    </div>
  );
};

Anchor.Link = AnchorLink;

export default Anchor;