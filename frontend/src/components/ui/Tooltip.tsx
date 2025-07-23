import React, { useState, useRef, useEffect, cloneElement } from 'react';
import { createPortal } from 'react-dom';

interface TooltipProps {
  children: React.ReactElement;
  content: React.ReactNode;
  position?: 'top' | 'bottom' | 'left' | 'right';
  variant?: 'dark' | 'light' | 'primary' | 'success' | 'warning' | 'danger';
  size?: 'sm' | 'md' | 'lg';
  trigger?: 'hover' | 'click' | 'focus' | 'manual';
  visible?: boolean;
  delay?: number;
  arrow?: boolean;
  disabled?: boolean;
  interactive?: boolean;
  animation?: 'fade' | 'scale' | 'slide';
  offset?: number;
  zIndex?: number;
  portal?: boolean;
  className?: string;
  onVisibleChange?: (visible: boolean) => void;
}

const Tooltip: React.FC<TooltipProps> = ({
  children,
  content,
  position = 'top',
  variant = 'dark',
  size = 'md',
  trigger = 'hover',
  visible: controlledVisible,
  delay = 0,
  arrow = true,
  disabled = false,
  interactive = false,
  animation = 'fade',
  offset = 8,
  zIndex = 1000,
  portal = true,
  className = '',
  onVisibleChange
}) => {
  const [internalVisible, setInternalVisible] = useState(false);
  const [tooltipPosition, setTooltipPosition] = useState(position);
  const triggerRef = useRef<HTMLElement>(null);
  const tooltipRef = useRef<HTMLDivElement>(null);
  const timeoutRef = useRef<NodeJS.Timeout>();
  
  const isVisible = controlledVisible !== undefined ? controlledVisible : internalVisible;
  const isManual = trigger === 'manual';

  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isVisible) {
        handleHide();
      }
    };
    
    if (isVisible) {
      document.addEventListener('keydown', handleEscape);
      return () => document.removeEventListener('keydown', handleEscape);
    }
  }, [isVisible]);

  useEffect(() => {
    if (isVisible && triggerRef.current && tooltipRef.current) {
      positionTooltip();
    }
  }, [isVisible, content]);

  const handleShow = () => {
    if (disabled || isManual) return;
    
    if (delay > 0) {
      timeoutRef.current = setTimeout(() => {
        setInternalVisible(true);
        onVisibleChange?.(true);
      }, delay);
    } else {
      setInternalVisible(true);
      onVisibleChange?.(true);
    }
  };

  const handleHide = () => {
    if (disabled || isManual) return;
    
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }
    
    if (!interactive || !isHoveredTooltip()) {
      setInternalVisible(false);
      onVisibleChange?.(false);
    }
  };

  const isHoveredTooltip = () => {
    if (!tooltipRef.current) return false;
    return tooltipRef.current.matches(':hover');
  };

  const positionTooltip = () => {
    if (!triggerRef.current || !tooltipRef.current) return;

    const triggerRect = triggerRef.current.getBoundingClientRect();
    const tooltipRect = tooltipRef.current.getBoundingClientRect();
    const viewportWidth = window.innerWidth;
    const viewportHeight = window.innerHeight;

    let newPosition = position;

    // Check if tooltip would overflow and adjust position
    switch (position) {
      case 'top':
        if (triggerRect.top - tooltipRect.height - offset < 0) {
          newPosition = 'bottom';
        }
        break;
      case 'bottom':
        if (triggerRect.bottom + tooltipRect.height + offset > viewportHeight) {
          newPosition = 'top';
        }
        break;
      case 'left':
        if (triggerRect.left - tooltipRect.width - offset < 0) {
          newPosition = 'right';
        }
        break;
      case 'right':
        if (triggerRect.right + tooltipRect.width + offset > viewportWidth) {
          newPosition = 'left';
        }
        break;
    }

    setTooltipPosition(newPosition);
  };

  const getTooltipStyle = () => {
    if (!triggerRef.current) return {};

    const triggerRect = triggerRef.current.getBoundingClientRect();
    let top = 0;
    let left = 0;

    switch (tooltipPosition) {
      case 'top':
        top = triggerRect.top - offset;
        left = triggerRect.left + triggerRect.width / 2;
        break;
      case 'bottom':
        top = triggerRect.bottom + offset;
        left = triggerRect.left + triggerRect.width / 2;
        break;
      case 'left':
        top = triggerRect.top + triggerRect.height / 2;
        left = triggerRect.left - offset;
        break;
      case 'right':
        top = triggerRect.top + triggerRect.height / 2;
        left = triggerRect.right + offset;
        break;
    }

    return {
      position: 'fixed' as const,
      top,
      left,
      zIndex,
      transform: getTransform(),
    };
  };

  const getTransform = () => {
    switch (tooltipPosition) {
      case 'top':
        return 'translate(-50%, -100%)';
      case 'bottom':
        return 'translate(-50%, 0)';
      case 'left':
        return 'translate(-100%, -50%)';
      case 'right':
        return 'translate(0, -50%)';
      default:
        return 'translate(-50%, -100%)';
    }
  };

  const getVariantClasses = () => {
    const variantMap = {
      dark: 'bg-gray-900 text-white',
      light: 'bg-white text-gray-900 border border-gray-200 shadow-lg',
      primary: 'bg-blue-500 text-white',
      success: 'bg-green-500 text-white',
      warning: 'bg-yellow-500 text-black',
      danger: 'bg-red-500 text-white'
    };
    return variantMap[variant];
  };

  const getSizeClasses = () => {
    const sizeMap = {
      sm: 'px-2 py-1 text-xs',
      md: 'px-3 py-2 text-sm',
      lg: 'px-4 py-3 text-base'
    };
    return sizeMap[size];
  };

  const getAnimationClasses = () => {
    if (!isVisible) return 'opacity-0 scale-95 pointer-events-none';
    
    const animationMap = {
      fade: 'opacity-100 scale-100',
      scale: 'opacity-100 scale-100',
      slide: 'opacity-100 translate-y-0'
    };
    return animationMap[animation];
  };

  const getArrowStyle = () => {
    const arrowSize = 6;
    let arrowStyle: React.CSSProperties = {
      position: 'absolute',
      width: 0,
      height: 0,
    };

    switch (tooltipPosition) {
      case 'top':
        arrowStyle = {
          ...arrowStyle,
          top: '100%',
          left: '50%',
          transform: 'translateX(-50%)',
          borderLeft: `${arrowSize}px solid transparent`,
          borderRight: `${arrowSize}px solid transparent`,
          borderTop: `${arrowSize}px solid`,
          borderTopColor: variant === 'light' ? '#f3f4f6' : 'currentColor'
        };
        break;
      case 'bottom':
        arrowStyle = {
          ...arrowStyle,
          bottom: '100%',
          left: '50%',
          transform: 'translateX(-50%)',
          borderLeft: `${arrowSize}px solid transparent`,
          borderRight: `${arrowSize}px solid transparent`,
          borderBottom: `${arrowSize}px solid`,
          borderBottomColor: variant === 'light' ? '#f3f4f6' : 'currentColor'
        };
        break;
      case 'left':
        arrowStyle = {
          ...arrowStyle,
          left: '100%',
          top: '50%',
          transform: 'translateY(-50%)',
          borderTop: `${arrowSize}px solid transparent`,
          borderBottom: `${arrowSize}px solid transparent`,
          borderLeft: `${arrowSize}px solid`,
          borderLeftColor: variant === 'light' ? '#f3f4f6' : 'currentColor'
        };
        break;
      case 'right':
        arrowStyle = {
          ...arrowStyle,
          right: '100%',
          top: '50%',
          transform: 'translateY(-50%)',
          borderTop: `${arrowSize}px solid transparent`,
          borderBottom: `${arrowSize}px solid transparent`,
          borderRight: `${arrowSize}px solid`,
          borderRightColor: variant === 'light' ? '#f3f4f6' : 'currentColor'
        };
        break;
    }

    return arrowStyle;
  };

  const handleTriggerEvents = () => {
    const events: Record<string, any> = {};

    if (trigger === 'hover') {
      events.onMouseEnter = handleShow;
      events.onMouseLeave = handleHide;
    }

    if (trigger === 'click') {
      events.onClick = () => {
        if (isVisible) {
          handleHide();
        } else {
          handleShow();
        }
      };
    }

    if (trigger === 'focus' || trigger === 'hover') {
      events.onFocus = handleShow;
      events.onBlur = handleHide;
    }

    // Add keyboard support
    if (trigger !== 'manual') {
      events.onKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          handleShow();
        }
      };
    }

    return events;
  };

  const tooltipContent = isVisible && (
    <div
      ref={tooltipRef}
      data-testid="tooltip"
      data-position={tooltipPosition}
      data-variant={variant}
      data-size={size}
      data-animation={animation}
      data-offset={offset}
      style={getTooltipStyle()}
      className={[
        'rounded-md transition-all duration-200 pointer-events-auto',
        getVariantClasses(),
        getSizeClasses(),
        getAnimationClasses(),
        className
      ].join(' ')}
      onMouseEnter={interactive ? () => {} : undefined}
      onMouseLeave={interactive ? handleHide : undefined}
    >
      {content}
      {arrow && (
        <div
          data-testid="tooltip-arrow"
          style={getArrowStyle()}
          className={variant === 'light' ? 'text-gray-200' : 'text-current'}
        />
      )}
    </div>
  );

  const triggerElement = cloneElement(children, {
    ref: triggerRef,
    ...handleTriggerEvents(),
    ...children.props
  });

  return (
    <>
      {triggerElement}
      {portal && typeof window !== 'undefined' 
        ? createPortal(tooltipContent, document.body)
        : tooltipContent
      }
    </>
  );
};

export { Tooltip };
export default Tooltip;