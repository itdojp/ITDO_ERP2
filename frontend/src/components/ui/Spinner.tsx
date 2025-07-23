import React, { useState, useEffect } from 'react';

interface SpinnerProps {
  size?: 'sm' | 'md' | 'lg' | 'xl';
  color?: 'primary' | 'success' | 'warning' | 'danger' | 'white' | 'gray';
  type?: 'spin' | 'pulse' | 'bounce' | 'ring' | 'dots' | 'bars' | 'grid' | 'pulsing-dots';
  speed?: 'slow' | 'normal' | 'fast';
  theme?: 'light' | 'dark' | 'auto';
  text?: string;
  description?: string;
  showText?: boolean;
  centered?: boolean;
  inline?: boolean;
  overlay?: boolean;
  backdropBlur?: boolean;
  position?: 'top' | 'center' | 'bottom';
  strokeWidth?: number;
  borderColor?: string;
  borderTopColor?: string;
  dotCount?: number;
  progress?: number;
  delay?: number;
  minTime?: number;
  animationDuration?: string;
  indeterminate?: boolean;
  show?: boolean;
  icon?: React.ReactNode;
  className?: string;
  style?: React.CSSProperties;
  title?: string;
  'aria-label'?: string;
  'aria-describedby'?: string;
}

export const Spinner: React.FC<SpinnerProps> = ({
  size = 'md',
  color = 'primary',
  type = 'spin',
  speed = 'normal',
  theme = 'auto',
  text,
  description,
  showText = false,
  centered = false,
  inline = false,
  overlay = false,
  backdropBlur = false,
  position = 'center',
  strokeWidth = 2,
  borderColor,
  borderTopColor,
  dotCount = 3,
  progress,
  delay = 0,
  minTime,
  animationDuration,
  indeterminate = false,
  show = true,
  icon,
  className = '',
  style,
  title,
  'aria-label': ariaLabel,
  'aria-describedby': ariaDescribedBy
}) => {
  const [visible, setVisible] = useState(delay === 0);
  const [startTime] = useState(Date.now());

  useEffect(() => {
    let delayTimer: NodeJS.Timeout;
    let minTimer: NodeJS.Timeout;

    if (delay > 0) {
      delayTimer = setTimeout(() => {
        setVisible(true);
      }, delay);
    }

    if (minTime && show) {
      minTimer = setTimeout(() => {
        if (!show) {
          setVisible(false);
        }
      }, minTime);
    }

    return () => {
      if (delayTimer) clearTimeout(delayTimer);
      if (minTimer) clearTimeout(minTimer);
    };
  }, [delay, minTime, show]);

  useEffect(() => {
    if (!show && minTime) {
      const elapsed = Date.now() - startTime;
      if (elapsed >= minTime) {
        setVisible(false);
      }
    } else if (show) {
      setVisible(true);
    }
  }, [show, minTime, startTime]);

  const getSizeClasses = () => {
    const sizeMap = {
      sm: 'w-4 h-4',
      md: 'w-6 h-6',
      lg: 'w-8 h-8',
      xl: 'w-12 h-12'
    };
    return sizeMap[size];
  };

  const getColorClasses = () => {
    if (theme === 'dark') return 'text-white';
    if (theme === 'light') return 'text-gray-600';
    
    const colorMap = {
      primary: 'text-blue-500',
      success: 'text-green-500',
      warning: 'text-yellow-500',
      danger: 'text-red-500',
      white: 'text-white',
      gray: 'text-gray-500'
    };
    return colorMap[color];
  };

  const getSpeedClasses = () => {
    const speedMap = {
      slow: 'animate-slow-spin',
      normal: 'animate-spin',
      fast: 'animate-fast-spin'
    };
    return speedMap[speed] || 'animate-spin';
  };

  const getBorderClasses = () => {
    const borderMap = {
      2: 'border-2',
      3: 'border-3',
      4: 'border-4'
    };
    return borderMap[strokeWidth] || 'border-2';
  };

  const renderSpinIcon = () => {
    if (icon) {
      return <span className={`${getSizeClasses()} ${getSpeedClasses()}`}>{icon}</span>;
    }

    if (type === 'ring') {
      return (
        <div 
          className={`
            ${getSizeClasses()} ${getBorderClasses()} ${borderColor || getColorClasses()}
            ${borderTopColor || 'border-t-transparent'} rounded-full ${getSpeedClasses()}
          `}
          role="img"
          aria-hidden="true"
          aria-label={ariaLabel}
          aria-describedby={ariaDescribedBy}
          title={title}
          style={animationDuration ? { animationDuration } : style}
        />
      );
    }

    return (
      <svg 
        className={`${getSizeClasses()} ${getColorClasses()} ${getSpeedClasses()}`}
        fill="none" 
        viewBox="0 0 24 24"
        role="img"
        aria-hidden="true"
        aria-label={ariaLabel}
        aria-describedby={ariaDescribedBy}
        title={title}
        style={animationDuration ? { animationDuration } : style}
      >
        <circle 
          className="opacity-25" 
          cx="12" 
          cy="12" 
          r="10" 
          stroke="currentColor" 
          strokeWidth={strokeWidth}
        />
        <path 
          className="opacity-75" 
          fill="currentColor" 
          d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
        />
      </svg>
    );
  };

  const renderPulseIcon = () => (
    <div 
      className={`${getSizeClasses()} ${getColorClasses()} bg-current rounded-full animate-pulse`}
      role="img"
      aria-hidden="true"
      aria-label={ariaLabel}
      title={title}
      style={style}
    />
  );

  const renderBounceIcon = () => (
    <div 
      className={`${getSizeClasses()} ${getColorClasses()} bg-current rounded-full animate-bounce`}
      role="img"
      aria-hidden="true"
      aria-label={ariaLabel}
      title={title}
      style={style}
    />
  );

  const renderDots = () => {
    const dots = Array.from({ length: dotCount }, (_, index) => (
      <div
        key={index}
        data-testid="spinner-dot"
        className={`w-2 h-2 ${getColorClasses()} bg-current rounded-full animate-pulse`}
        style={{
          animationDelay: `${index * 0.1}s`,
          animationDuration: animationDuration || '1.4s'
        }}
      />
    ));

    return (
      <div 
        className="flex space-x-1"
        role="img"
        aria-hidden="true"
        aria-label={ariaLabel}
        title={title}
      >
        {dots}
      </div>
    );
  };

  const renderPulsingDots = () => {
    const dots = Array.from({ length: 3 }, (_, index) => (
      <div
        key={index}
        data-testid="spinner-dot"
        className={`w-3 h-3 ${getColorClasses()} bg-current rounded-full animate-pulse`}
        style={{
          animationDelay: `${index * 0.2}s`,
          animationDuration: animationDuration || '1s'
        }}
      />
    ));

    return (
      <div 
        className="flex space-x-2"
        role="img"
        aria-hidden="true"
        aria-label={ariaLabel}
        title={title}
      >
        {dots}
      </div>
    );
  };

  const renderBars = () => {
    const bars = Array.from({ length: 5 }, (_, index) => (
      <div
        key={index}
        data-testid="spinner-bar"
        className={`w-1 h-6 ${getColorClasses()} bg-current animate-pulse`}
        style={{
          animationDelay: `${index * 0.1}s`,
          animationDuration: animationDuration || '1.2s'
        }}
      />
    ));

    return (
      <div 
        className="flex space-x-1 items-end"
        role="img"
        aria-hidden="true"
        aria-label={ariaLabel}
        title={title}
      >
        {bars}
      </div>
    );
  };

  const renderGrid = () => {
    const gridItems = Array.from({ length: 9 }, (_, index) => (
      <div
        key={index}
        data-testid="spinner-grid-item"
        className={`w-2 h-2 ${getColorClasses()} bg-current animate-pulse`}
        style={{
          animationDelay: `${(index % 3) * 0.1}s`,
          animationDuration: animationDuration || '1.5s'
        }}
      />
    ));

    return (
      <div 
        className="grid grid-cols-3 gap-1"
        role="img"
        aria-hidden="true"
        aria-label={ariaLabel}
        title={title}
      >
        {gridItems}
      </div>
    );
  };

  const renderSpinner = () => {
    if (type === 'pulse') return renderPulseIcon();
    if (type === 'bounce') return renderBounceIcon();
    if (type === 'dots') return renderDots();
    if (type === 'pulsing-dots') return renderPulsingDots();
    if (type === 'bars') return renderBars();
    if (type === 'grid') return renderGrid();
    return renderSpinIcon();
  };

  const getPositionClasses = () => {
    const positionMap = {
      top: 'justify-start items-start pt-20',
      center: 'justify-center items-center',
      bottom: 'justify-end items-end pb-20'
    };
    return positionMap[position];
  };

  const renderContent = () => (
    <div className={`${centered ? 'flex items-center justify-center' : ''} ${inline ? 'inline-flex' : 'flex'} flex-col items-center space-y-2`}>
      {renderSpinner()}
      
      {(showText || (text && showText !== false)) && (
        <div className="text-center">
          <div className="text-sm font-medium text-gray-700">
            {text || 'Loading...'}
          </div>
          {description && (
            <div className="text-xs text-gray-500 mt-1">
              {description}
            </div>
          )}
        </div>
      )}
      
      {progress !== undefined && (
        <div className="text-xs font-medium text-gray-600">
          {progress}%
        </div>
      )}
    </div>
  );

  if (!show || !visible) {
    return null;
  }

  if (overlay) {
    return (
      <div 
        data-testid="spinner-overlay"
        className={`
          fixed inset-0 z-50 bg-black/50 
          ${backdropBlur ? 'backdrop-blur-sm' : ''}
          flex ${getPositionClasses()}
        `}
      >
        <div className={`flex flex-col items-center space-y-4 ${className}`} style={style}>
          {renderContent()}
        </div>
      </div>
    );
  }

  return (
    <div 
      className={`
        ${delay > 0 && !visible ? 'opacity-0' : 'opacity-100'}
        transition-opacity duration-200 ${className}
      `}
      style={style}
    >
      {renderContent()}
    </div>
  );
};

export default Spinner;