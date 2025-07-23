import React, { useState, useEffect, useRef, useCallback } from 'react';

interface BackTopProps {
  children?: React.ReactNode;
  text?: string;
  icon?: React.ReactNode;
  size?: 'small' | 'medium' | 'large';
  shape?: 'circle' | 'square';
  position?: 'bottom-right' | 'bottom-left' | 'top-right' | 'top-left';
  visibilityHeight?: number;
  scrollOffset?: number;
  duration?: number;
  smooth?: boolean;
  animationType?: 'fade' | 'slide' | 'scale';
  animated?: boolean;
  hoverEffect?: boolean;
  pulse?: boolean;
  disabled?: boolean;
  right?: number;
  bottom?: number;
  left?: number;
  top?: number;
  zIndex?: number;
  tooltip?: string;
  ariaLabel?: string;
  target?: () => HTMLElement | Window | null;
  scrollContainer?: () => HTMLElement | null;
  onClick?: () => void;
  onShow?: () => void;
  onHide?: () => void;
  className?: string;
  style?: React.CSSProperties;
  [key: string]: any;
}

const BackTop: React.FC<BackTopProps> = ({
  children,
  text,
  icon,
  size = 'medium',
  shape = 'circle',
  position = 'bottom-right',
  visibilityHeight = 400,
  scrollOffset = 0,
  duration = 450,
  smooth = true,
  animationType = 'fade',
  animated = true,
  hoverEffect = true,
  pulse = false,
  disabled = false,
  right = 24,
  bottom = 24,
  left,
  top,
  zIndex = 1000,
  tooltip,
  ariaLabel = 'Back to top',
  target,
  scrollContainer,
  onClick,
  onShow,
  onHide,
  className = '',
  style,
  ...props
}) => {
  const [visible, setVisible] = useState(false);
  const [isScrolling, setIsScrolling] = useState(false);
  const [showTooltip, setShowTooltip] = useState(false);
  const buttonRef = useRef<HTMLButtonElement>(null);
  const scrollTimeoutRef = useRef<NodeJS.Timeout>();

  const getScrollTarget = useCallback(() => {
    if (target) {
      return target();
    }
    if (scrollContainer) {
      return scrollContainer();
    }
    return window;
  }, [target, scrollContainer]);

  const getScrollTop = useCallback(() => {
    const scrollTarget = getScrollTarget();
    if (scrollTarget === window) {
      return window.pageYOffset || document.documentElement.scrollTop || document.body.scrollTop || 0;
    }
    return (scrollTarget as HTMLElement)?.scrollTop || 0;
  }, [getScrollTarget]);

  const handleScroll = useCallback(() => {
    const scrollTop = getScrollTop();
    const shouldShow = scrollTop >= visibilityHeight;
    
    if (shouldShow !== visible) {
      setVisible(shouldShow);
      if (shouldShow) {
        onShow?.();
      } else {
        onHide?.();
      }
    }
  }, [getScrollTop, visibilityHeight, visible, onShow, onHide]);

  useEffect(() => {
    const scrollTarget = getScrollTarget();
    if (!scrollTarget) return;

    handleScroll(); // Initial check
    
    scrollTarget.addEventListener('scroll', handleScroll, { passive: true });
    return () => {
      scrollTarget.removeEventListener('scroll', handleScroll);
    };
  }, [handleScroll, getScrollTarget]);

  const scrollToTop = useCallback(() => {
    if (isScrolling || disabled) return;
    
    setIsScrolling(true);
    
    const scrollTarget = getScrollTarget();
    if (!scrollTarget) return;

    const scrollOptions: ScrollToOptions = {
      top: scrollOffset,
      behavior: smooth ? 'smooth' : 'auto'
    };

    if (scrollTarget === window) {
      window.scrollTo(scrollOptions);
    } else {
      (scrollTarget as HTMLElement).scrollTo(scrollOptions);
    }

    // Reset scrolling state after animation
    scrollTimeoutRef.current = setTimeout(() => {
      setIsScrolling(false);
    }, duration);
  }, [isScrolling, disabled, getScrollTarget, scrollOffset, smooth, duration]);

  useEffect(() => {
    return () => {
      if (scrollTimeoutRef.current) {
        clearTimeout(scrollTimeoutRef.current);
      }
    };
  }, []);

  const handleClick = () => {
    if (onClick) {
      onClick();
    } else {
      scrollToTop();
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      handleClick();
    }
  };

  const getSizeClasses = () => {
    const sizeMap = {
      small: 'w-8 h-8 text-sm',
      medium: 'w-10 h-10 text-base',
      large: 'w-12 h-12 text-lg'
    };
    return sizeMap[size];
  };

  const getShapeClasses = () => {
    const shapeMap = {
      circle: 'rounded-full',
      square: 'rounded-lg'
    };
    return shapeMap[shape];
  };

  const getPositionClasses = () => {
    const positions = {
      'bottom-right': 'bottom-0 right-0',
      'bottom-left': 'bottom-0 left-0',
      'top-right': 'top-0 right-0',
      'top-left': 'top-0 left-0'
    };
    return positions[position];
  };

  const getAnimationClasses = () => {
    if (!animated) return '';
    
    const animationMap = {
      fade: `transition-opacity duration-300 ${visible ? 'opacity-100' : 'opacity-0'}`,
      slide: `transition-transform duration-300 ${visible ? 'translate-y-0' : 'translate-y-full'}`,
      scale: `transition-transform duration-300 ${visible ? 'scale-100' : 'scale-0'}`
    };
    return animationMap[animationType];
  };

  const getPositionStyles = (): React.CSSProperties => {
    const styles: React.CSSProperties = { zIndex };
    
    if (position.includes('right') && right !== undefined) styles.right = `${right}px`;
    if (position.includes('left') && left !== undefined) styles.left = `${left}px`;
    if (position.includes('bottom') && bottom !== undefined) styles.bottom = `${bottom}px`;
    if (position.includes('top') && top !== undefined) styles.top = `${top}px`;
    
    return styles;
  };

  const renderIcon = () => {
    if (children) return children;
    if (text) return text;
    if (icon) return icon;
    
    return (
      <svg
        className="w-4 h-4"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
        role="img"
        aria-hidden="true"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M5 10l7-7m0 0l7 7m-7-7v18"
        />
      </svg>
    );
  };

  const buttonClasses = [
    'fixed flex items-center justify-center',
    'bg-blue-600 text-white shadow-lg',
    'hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2',
    'transition-all duration-200',
    getSizeClasses(),
    getShapeClasses(),
    getPositionClasses(),
    getAnimationClasses(),
    hoverEffect ? 'hover:scale-110' : '',
    pulse ? 'animate-pulse' : '',
    disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer',
    isScrolling ? 'pointer-events-none' : '',
    className
  ].filter(Boolean).join(' ');

  const combinedStyles: React.CSSProperties = {
    ...getPositionStyles(),
    ...style
  };

  return (
    <>
      <button
        ref={buttonRef}
        className={buttonClasses}
        style={combinedStyles}
        onClick={handleClick}
        onKeyDown={handleKeyDown}
        onMouseEnter={() => tooltip && setShowTooltip(true)}
        onMouseLeave={() => tooltip && setShowTooltip(false)}
        disabled={disabled}
        aria-label={ariaLabel}
        {...props}
      >
        {renderIcon()}
      </button>
      
      {tooltip && showTooltip && (
        <div
          className="fixed bg-black text-white text-xs px-2 py-1 rounded shadow-lg pointer-events-none z-50"
          style={{
            bottom: bottom + 50,
            right: position.includes('right') ? right : undefined,
            left: position.includes('left') ? left : undefined,
          }}
        >
          {tooltip}
          <div className="absolute top-full left-1/2 transform -translate-x-1/2 border-4 border-transparent border-t-black" />
        </div>
      )}
    </>
  );
};

export { BackTop };
export default BackTop;