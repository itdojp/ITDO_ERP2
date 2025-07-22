import React, { useState, useRef, useEffect } from 'react';

type TooltipPlacement = 'top' | 'bottom' | 'left' | 'right';

interface TooltipProps {
  title: string;
  children: React.ReactNode;
  placement?: TooltipPlacement;
  delay?: number;
  className?: string;
  disabled?: boolean;
}

export const Tooltip: React.FC<TooltipProps> = ({
  title,
  children,
  placement = 'top',
  delay = 500,
  className = '',
  disabled = false,
}) => {
  const [visible, setVisible] = useState(false);
  const [position, setPosition] = useState({ x: 0, y: 0 });
  const timeoutRef = useRef<NodeJS.Timeout>();
  const containerRef = useRef<HTMLDivElement>(null);

  const showTooltip = () => {
    if (disabled || !title) return;
    
    timeoutRef.current = setTimeout(() => {
      if (containerRef.current) {
        const rect = containerRef.current.getBoundingClientRect();
        const tooltipX = rect.left + rect.width / 2;
        const tooltipY = rect.top;
        
        setPosition({ x: tooltipX, y: tooltipY });
        setVisible(true);
      }
    }, delay);
  };

  const hideTooltip = () => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }
    setVisible(false);
  };

  useEffect(() => {
    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, []);

  // プレースメントごとのスタイル
  const getTooltipStyles = () => {
    const baseStyles = {
      position: 'fixed' as const,
      zIndex: 1000,
      background: '#374151',
      color: 'white',
      padding: '6px 8px',
      borderRadius: '4px',
      fontSize: '12px',
      whiteSpace: 'nowrap' as const,
      pointerEvents: 'none' as const,
      transform: 'translateX(-50%)',
      opacity: visible ? 1 : 0,
      transition: 'opacity 0.15s ease-in-out',
    };

    const placements = {
      top: {
        ...baseStyles,
        left: position.x,
        top: position.y - 35,
        transform: 'translateX(-50%)',
      },
      bottom: {
        ...baseStyles,
        left: position.x,
        top: position.y + 35,
        transform: 'translateX(-50%)',
      },
      left: {
        ...baseStyles,
        left: position.x - 10,
        top: position.y,
        transform: 'translateX(-100%) translateY(-50%)',
      },
      right: {
        ...baseStyles,
        left: position.x + 10,
        top: position.y,
        transform: 'translateY(-50%)',
      },
    };

    return placements[placement];
  };

  // 矢印のスタイル
  const getArrowStyles = () => {
    const baseArrow = {
      position: 'absolute' as const,
      width: 0,
      height: 0,
      borderStyle: 'solid',
    };

    const arrows = {
      top: {
        ...baseArrow,
        borderLeft: '5px solid transparent',
        borderRight: '5px solid transparent',
        borderTop: '5px solid #374151',
        left: '50%',
        top: '100%',
        transform: 'translateX(-50%)',
      },
      bottom: {
        ...baseArrow,
        borderLeft: '5px solid transparent',
        borderRight: '5px solid transparent',
        borderBottom: '5px solid #374151',
        left: '50%',
        bottom: '100%',
        transform: 'translateX(-50%)',
      },
      left: {
        ...baseArrow,
        borderTop: '5px solid transparent',
        borderBottom: '5px solid transparent',
        borderLeft: '5px solid #374151',
        right: '-5px',
        top: '50%',
        transform: 'translateY(-50%)',
      },
      right: {
        ...baseArrow,
        borderTop: '5px solid transparent',
        borderBottom: '5px solid transparent',
        borderRight: '5px solid #374151',
        left: '-5px',
        top: '50%',
        transform: 'translateY(-50%)',
      },
    };

    return arrows[placement];
  };

  return (
    <>
      <div
        ref={containerRef}
        className={`inline-block ${className}`}
        onMouseEnter={showTooltip}
        onMouseLeave={hideTooltip}
        onFocus={showTooltip}
        onBlur={hideTooltip}
      >
        {children}
      </div>
      
      {visible && title && !disabled && (
        <div style={getTooltipStyles()}>
          {title}
          <div style={getArrowStyles()} />
        </div>
      )}
    </>
  );
};