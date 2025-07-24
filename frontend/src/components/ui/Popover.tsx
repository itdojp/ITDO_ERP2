import React, { useState, useRef, useEffect } from 'react';

interface PopoverProps {
  content: React.ReactNode;
  children: React.ReactNode;
  placement?: 'top' | 'bottom' | 'left' | 'right';
  trigger?: 'hover' | 'click' | 'focus';
  title?: string;
  showArrow?: boolean;
  showCloseButton?: boolean;
  width?: number | string;
  onVisibilityChange?: (visible: boolean) => void;
  disabled?: boolean;
  offset?: number;
  className?: string;
}

export const Popover: React.FC<PopoverProps> = ({
  content,
  children,
  placement = 'bottom',
  trigger = 'click',
  title,
  showArrow = true,
  showCloseButton = true,
  width = 'auto',
  onVisibilityChange,
  disabled = false,
  offset = 10,
  className = ''
}) => {
  const [isVisible, setIsVisible] = useState(false);
  const [position, setPosition] = useState({ x: 0, y: 0 });
  const triggerRef = useRef<HTMLDivElement>(null);
  const popoverRef = useRef<HTMLDivElement>(null);

  const calculatePosition = () => {
    if (!triggerRef.current || !popoverRef.current) return;

    const triggerRect = triggerRef.current.getBoundingClientRect();
    const popoverRect = popoverRef.current.getBoundingClientRect();
    const scrollX = window.pageXOffset || document.documentElement.scrollLeft;
    const scrollY = window.pageYOffset || document.documentElement.scrollTop;

    let x = 0;
    let y = 0;

    switch (placement) {
      case 'top':
        x = triggerRect.left + scrollX + (triggerRect.width / 2) - (popoverRect.width / 2);
        y = triggerRect.top + scrollY - popoverRect.height - offset;
        break;
      case 'bottom':
        x = triggerRect.left + scrollX + (triggerRect.width / 2) - (popoverRect.width / 2);
        y = triggerRect.bottom + scrollY + offset;
        break;
      case 'left':
        x = triggerRect.left + scrollX - popoverRect.width - offset;
        y = triggerRect.top + scrollY + (triggerRect.height / 2) - (popoverRect.height / 2);
        break;
      case 'right':
        x = triggerRect.right + scrollX + offset;
        y = triggerRect.top + scrollY + (triggerRect.height / 2) - (popoverRect.height / 2);
        break;
    }

    // Keep popover within viewport
    const viewportWidth = window.innerWidth;
    const viewportHeight = window.innerHeight;

    if (x < 0) x = 8;
    if (x + popoverRect.width > viewportWidth) {
      x = viewportWidth - popoverRect.width - 8;
    }
    if (y < 0) y = 8;
    if (y + popoverRect.height > viewportHeight + scrollY) {
      y = viewportHeight + scrollY - popoverRect.height - 8;
    }

    setPosition({ x, y });
  };

  const showPopover = () => {
    if (disabled) return;
    setIsVisible(true);
    onVisibilityChange?.(true);
  };

  const hidePopover = () => {
    setIsVisible(false);
    onVisibilityChange?.(false);
  };

  const handleTriggerInteraction = (event: React.MouseEvent | React.FocusEvent) => {
    event.stopPropagation();
    
    if (trigger === 'click') {
      if (isVisible) {
        hidePopover();
      } else {
        showPopover();
      }
    }
  };

  const handleMouseEnter = () => {
    if (trigger === 'hover') showPopover();
  };

  const handleMouseLeave = () => {
    if (trigger === 'hover') hidePopover();
  };

  const handleFocus = () => {
    if (trigger === 'focus') showPopover();
  };

  const handleBlur = () => {
    if (trigger === 'focus') hidePopover();
  };

  const handleCloseClick = () => {
    hidePopover();
  };

  useEffect(() => {
    if (isVisible) {
      calculatePosition();
    }
  }, [isVisible, content, placement]);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        isVisible &&
        popoverRef.current &&
        triggerRef.current &&
        !popoverRef.current.contains(event.target as Node) &&
        !triggerRef.current.contains(event.target as Node)
      ) {
        hidePopover();
      }
    };

    const handleResize = () => {
      if (isVisible) calculatePosition();
    };

    const handleScroll = () => {
      if (isVisible) calculatePosition();
    };

    if (trigger === 'click') {
      document.addEventListener('mousedown', handleClickOutside);
    }

    window.addEventListener('resize', handleResize);
    window.addEventListener('scroll', handleScroll);

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
      window.removeEventListener('resize', handleResize);
      window.removeEventListener('scroll', handleScroll);
    };
  }, [isVisible, trigger]);

  const getArrowStyles = (): React.CSSProperties => {
    const arrowSize = 8;
    const arrowStyles: React.CSSProperties = {
      position: 'absolute',
      width: 0,
      height: 0,
    };

    switch (placement) {
      case 'top':
        arrowStyles.top = '100%';
        arrowStyles.left = '50%';
        arrowStyles.marginLeft = -arrowSize;
        arrowStyles.borderLeft = `${arrowSize}px solid transparent`;
        arrowStyles.borderRight = `${arrowSize}px solid transparent`;
        arrowStyles.borderTop = `${arrowSize}px solid white`;
        arrowStyles.filter = 'drop-shadow(0 2px 4px rgba(0, 0, 0, 0.1))';
        break;
      case 'bottom':
        arrowStyles.bottom = '100%';
        arrowStyles.left = '50%';
        arrowStyles.marginLeft = -arrowSize;
        arrowStyles.borderLeft = `${arrowSize}px solid transparent`;
        arrowStyles.borderRight = `${arrowSize}px solid transparent`;
        arrowStyles.borderBottom = `${arrowSize}px solid white`;
        arrowStyles.filter = 'drop-shadow(0 -2px 4px rgba(0, 0, 0, 0.1))';
        break;
      case 'left':
        arrowStyles.left = '100%';
        arrowStyles.top = '50%';
        arrowStyles.marginTop = -arrowSize;
        arrowStyles.borderTop = `${arrowSize}px solid transparent`;
        arrowStyles.borderBottom = `${arrowSize}px solid transparent`;
        arrowStyles.borderLeft = `${arrowSize}px solid white`;
        arrowStyles.filter = 'drop-shadow(2px 0 4px rgba(0, 0, 0, 0.1))';
        break;
      case 'right':
        arrowStyles.right = '100%';
        arrowStyles.top = '50%';
        arrowStyles.marginTop = -arrowSize;
        arrowStyles.borderTop = `${arrowSize}px solid transparent`;
        arrowStyles.borderBottom = `${arrowSize}px solid transparent`;
        arrowStyles.borderRight = `${arrowSize}px solid white`;
        arrowStyles.filter = 'drop-shadow(-2px 0 4px rgba(0, 0, 0, 0.1))';
        break;
    }

    return arrowStyles;
  };

  const popoverStyles: React.CSSProperties = {
    width: typeof width === 'number' ? `${width}px` : width,
    left: position.x,
    top: position.y,
  };

  return (
    <>
      <div
        ref={triggerRef}
        onMouseEnter={handleMouseEnter}
        onMouseLeave={handleMouseLeave}
        onClick={handleTriggerInteraction}
        onFocus={handleFocus}
        onBlur={handleBlur}
        className="inline-block cursor-pointer"
      >
        {children}
      </div>

      {isVisible && (
        <div
          ref={popoverRef}
          className={`
            fixed z-50 bg-white border border-gray-200 rounded-lg shadow-lg
            transition-opacity duration-200
            ${className}
          `}
          style={popoverStyles}
        >
          {showArrow && <div style={getArrowStyles()} />}
          
          {title && (
            <div className="px-4 py-3 border-b border-gray-100">
              <div className="flex items-center justify-between">
                <h3 className="text-sm font-semibold text-gray-900">{title}</h3>
                {showCloseButton && (
                  <button
                    onClick={handleCloseClick}
                    className="text-gray-400 hover:text-gray-600 transition-colors"
                    type="button"
                  >
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                )}
              </div>
            </div>
          )}
          
          <div className="p-4">
            {content}
          </div>

          {!title && showCloseButton && (
            <button
              onClick={handleCloseClick}
              className="absolute top-2 right-2 text-gray-400 hover:text-gray-600 transition-colors"
              type="button"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          )}
        </div>
      )}
    </>
  );
};

export default Popover;