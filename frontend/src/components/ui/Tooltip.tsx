import React, { useState, useRef, useEffect } from 'react';

interface TooltipProps {
  content: React.ReactNode;
  children: React.ReactNode;
  placement?: 'top' | 'bottom' | 'left' | 'right';
  trigger?: 'hover' | 'click' | 'focus';
  delay?: number;
  hideDelay?: number;
  disabled?: boolean;
  arrow?: boolean;
  offset?: number;
  className?: string;
}

export const Tooltip: React.FC<TooltipProps> = ({
  content,
  children,
  placement = 'top',
  trigger = 'hover',
  delay = 0,
  hideDelay = 0,
  disabled = false,
  arrow = true,
  offset = 8,
  className = ''
}) => {
  const [isVisible, setIsVisible] = useState(false);
  const [position, setPosition] = useState({ x: 0, y: 0 });
  const triggerRef = useRef<HTMLDivElement>(null);
  const tooltipRef = useRef<HTMLDivElement>(null);
  const timeoutRef = useRef<NodeJS.Timeout>();
  const hideTimeoutRef = useRef<NodeJS.Timeout>();

  const calculatePosition = () => {
    if (!triggerRef.current || !tooltipRef.current) return;

    const triggerRect = triggerRef.current.getBoundingClientRect();
    const tooltipRect = tooltipRef.current.getBoundingClientRect();
    const scrollX = window.pageXOffset || document.documentElement.scrollLeft;
    const scrollY = window.pageYOffset || document.documentElement.scrollTop;

    let x = 0;
    let y = 0;

    switch (placement) {
      case 'top':
        x = triggerRect.left + scrollX + (triggerRect.width / 2) - (tooltipRect.width / 2);
        y = triggerRect.top + scrollY - tooltipRect.height - offset;
        break;
      case 'bottom':
        x = triggerRect.left + scrollX + (triggerRect.width / 2) - (tooltipRect.width / 2);
        y = triggerRect.bottom + scrollY + offset;
        break;
      case 'left':
        x = triggerRect.left + scrollX - tooltipRect.width - offset;
        y = triggerRect.top + scrollY + (triggerRect.height / 2) - (tooltipRect.height / 2);
        break;
      case 'right':
        x = triggerRect.right + scrollX + offset;
        y = triggerRect.top + scrollY + (triggerRect.height / 2) - (tooltipRect.height / 2);
        break;
    }

    // Keep tooltip within viewport
    const viewportWidth = window.innerWidth;
    const viewportHeight = window.innerHeight;

    if (x < 0) x = 8;
    if (x + tooltipRect.width > viewportWidth) {
      x = viewportWidth - tooltipRect.width - 8;
    }
    if (y < 0) y = 8;
    if (y + tooltipRect.height > viewportHeight + scrollY) {
      y = viewportHeight + scrollY - tooltipRect.height - 8;
    }

    setPosition({ x, y });
  };

  const showTooltip = () => {
    if (disabled) return;
    
    if (hideTimeoutRef.current) {
      clearTimeout(hideTimeoutRef.current);
    }

    if (delay > 0) {
      timeoutRef.current = setTimeout(() => {
        setIsVisible(true);
      }, delay);
    } else {
      setIsVisible(true);
    }
  };

  const hideTooltip = () => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }

    if (hideDelay > 0) {
      hideTimeoutRef.current = setTimeout(() => {
        setIsVisible(false);
      }, hideDelay);
    } else {
      setIsVisible(false);
    }
  };

  const handleMouseEnter = () => {
    if (trigger === 'hover') showTooltip();
  };

  const handleMouseLeave = () => {
    if (trigger === 'hover') hideTooltip();
  };

  const handleClick = () => {
    if (trigger === 'click') {
      if (isVisible) {
        hideTooltip();
      } else {
        showTooltip();
      }
    }
  };

  const handleFocus = () => {
    if (trigger === 'focus') showTooltip();
  };

  const handleBlur = () => {
    if (trigger === 'focus') hideTooltip();
  };

  useEffect(() => {
    if (isVisible) {
      calculatePosition();
    }
  }, [isVisible, content, placement]);

  useEffect(() => {
    const handleResize = () => {
      if (isVisible) calculatePosition();
    };

    const handleScroll = () => {
      if (isVisible) calculatePosition();
    };

    window.addEventListener('resize', handleResize);
    window.addEventListener('scroll', handleScroll);

    return () => {
      window.removeEventListener('resize', handleResize);
      window.removeEventListener('scroll', handleScroll);
      if (timeoutRef.current) clearTimeout(timeoutRef.current);
      if (hideTimeoutRef.current) clearTimeout(hideTimeoutRef.current);
    };
  }, [isVisible]);

  const getArrowStyles = () => {
    const arrowSize = 6;
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
        arrowStyles.borderTop = `${arrowSize}px solid #374151`;
        break;
      case 'bottom':
        arrowStyles.bottom = '100%';
        arrowStyles.left = '50%';
        arrowStyles.marginLeft = -arrowSize;
        arrowStyles.borderLeft = `${arrowSize}px solid transparent`;
        arrowStyles.borderRight = `${arrowSize}px solid transparent`;
        arrowStyles.borderBottom = `${arrowSize}px solid #374151`;
        break;
      case 'left':
        arrowStyles.left = '100%';
        arrowStyles.top = '50%';
        arrowStyles.marginTop = -arrowSize;
        arrowStyles.borderTop = `${arrowSize}px solid transparent`;
        arrowStyles.borderBottom = `${arrowSize}px solid transparent`;
        arrowStyles.borderLeft = `${arrowSize}px solid #374151`;
        break;
      case 'right':
        arrowStyles.right = '100%';
        arrowStyles.top = '50%';
        arrowStyles.marginTop = -arrowSize;
        arrowStyles.borderTop = `${arrowSize}px solid transparent`;
        arrowStyles.borderBottom = `${arrowSize}px solid transparent`;
        arrowStyles.borderRight = `${arrowSize}px solid #374151`;
        break;
    }

    return arrowStyles;
  };

  return (
    <>
      <div
        ref={triggerRef}
        onMouseEnter={handleMouseEnter}
        onMouseLeave={handleMouseLeave}
        onClick={handleClick}
        onFocus={handleFocus}
        onBlur={handleBlur}
        className="inline-block"
      >
        {children}
      </div>

      {isVisible && (
        <div
          ref={tooltipRef}
          className={`
            fixed z-50 px-2 py-1 text-sm text-white bg-gray-700 rounded shadow-lg
            transition-opacity duration-200 pointer-events-none
            ${className}
          `}
          style={{
            left: position.x,
            top: position.y,
          }}
        >
          {content}
          {arrow && <div style={getArrowStyles()} />}
        </div>
      )}
    </>
  );
};

export default Tooltip;