import React, { useState, useRef, useCallback, forwardRef, useEffect } from 'react';

interface SliderProps {
  value?: number | [number, number];
  defaultValue?: number | [number, number];
  min?: number;
  max?: number;
  step?: number;
  marks?: Record<number, React.ReactNode>;
  dots?: boolean;
  included?: boolean;
  disabled?: boolean;
  loading?: boolean;
  vertical?: boolean;
  reverse?: boolean;
  range?: boolean;
  tooltip?: boolean;
  tooltipFormatter?: (value: number) => string;
  size?: 'sm' | 'md' | 'lg';
  color?: 'primary' | 'success' | 'warning' | 'danger';
  className?: string;
  trackStyle?: React.CSSProperties;
  handleStyle?: React.CSSProperties;
  onChange?: (value: number | [number, number], event: React.ChangeEvent<HTMLInputElement>) => void;
  onAfterChange?: (value: number | [number, number]) => void;
  onBeforeChange?: (value: number | [number, number]) => void;
  onFocus?: (event: React.FocusEvent<HTMLInputElement>) => void;
  onBlur?: (event: React.FocusEvent<HTMLInputElement>) => void;
  'aria-label'?: string;
  'aria-labelledby'?: string;
  'aria-describedby'?: string;
  id?: string;
  name?: string;
  tabIndex?: number;
}

export const Slider = forwardRef<HTMLInputElement, SliderProps>(({
  value,
  defaultValue,
  min = 0,
  max = 100,
  step = 1,
  marks,
  dots = false,
  included = true,
  disabled = false,
  loading = false,
  vertical = false,
  reverse = false,
  range = false,
  tooltip = false,
  tooltipFormatter,
  size = 'md',
  color = 'primary',
  className = '',
  trackStyle,
  handleStyle,
  onChange,
  onAfterChange,
  onBeforeChange,
  onFocus,
  onBlur,
  'aria-label': ariaLabel,
  'aria-labelledby': ariaLabelledBy,
  'aria-describedby': ariaDescribedBy,
  id,
  name,
  tabIndex
}, ref) => {
  const [internalValue, setInternalValue] = useState<number | [number, number]>(() => {
    if (defaultValue !== undefined) return defaultValue;
    return range ? [min, max] : min;
  });
  const [showTooltip, setShowTooltip] = useState(false);
  const [isDragging, setIsDragging] = useState(false);
  
  const containerRef = useRef<HTMLDivElement>(null);
  const sliderRef = useRef<HTMLInputElement>(null);

  const isControlled = value !== undefined;
  const currentValue = isControlled ? value : internalValue;
  const isDisabled = disabled || loading;

  const getSizeClasses = () => {
    const sizeMap = {
      sm: {
        track: 'h-1',
        handle: 'w-4 h-4',
        vertical: 'w-1 h-32'
      },
      md: {
        track: 'h-2',
        handle: 'w-5 h-5',
        vertical: 'w-2 h-40'
      },
      lg: {
        track: 'h-3',
        handle: 'w-6 h-6',
        vertical: 'w-3 h-48'
      }
    };
    return sizeMap[size];
  };

  const getColorClasses = () => {
    if (isDisabled) return 'bg-gray-300';
    
    const colorMap = {
      primary: 'bg-blue-500',
      success: 'bg-green-500',
      warning: 'bg-yellow-500',
      danger: 'bg-red-500'
    };
    return colorMap[color];
  };

  const sizeClasses = getSizeClasses();
  const colorClasses = getColorClasses();

  const normalizeValue = useCallback((val: number) => {
    return Math.min(Math.max(val, min), max);
  }, [min, max]);

  const snapToMark = useCallback((val: number) => {
    if (!marks || !included) return val;
    
    const markValues = Object.keys(marks).map(Number).sort((a, b) => a - b);
    let closest = markValues[0];
    let minDistance = Math.abs(val - closest);
    
    for (const markValue of markValues) {
      const distance = Math.abs(val - markValue);
      if (distance < minDistance) {
        minDistance = distance;
        closest = markValue;
      }
    }
    
    return closest;
  }, [marks, included]);

  const calculatePercentage = useCallback((val: number) => {
    return ((val - min) / (max - min)) * 100;
  }, [min, max]);

  const handleChange = useCallback((event: React.ChangeEvent<HTMLInputElement>, index?: number) => {
    if (isDisabled) return;

    let newValue = parseFloat(event.target.value);
    newValue = normalizeValue(newValue);
    newValue = snapToMark(newValue);

    let finalValue: number | [number, number];

    if (range && Array.isArray(currentValue)) {
      const newRangeValue = [...currentValue] as [number, number];
      
      if (index === 0) {
        newRangeValue[0] = Math.min(newValue, newRangeValue[1]);
      } else if (index === 1) {
        newRangeValue[1] = Math.max(newValue, newRangeValue[0]);
      }
      
      finalValue = newRangeValue;
    } else {
      finalValue = newValue;
    }

    if (!isControlled) {
      setInternalValue(finalValue);
    }

    onChange?.(finalValue, event);
  }, [isDisabled, normalizeValue, snapToMark, range, currentValue, isControlled, onChange]);

  const handleKeyDown = useCallback((event: React.KeyboardEvent<HTMLInputElement>) => {
    if (isDisabled) return;

    const currentVal = range && Array.isArray(currentValue) ? currentValue[0] : (currentValue as number);
    let newValue = currentVal;

    switch (event.key) {
      case 'ArrowRight':
      case 'ArrowUp':
        event.preventDefault();
        newValue = Math.min(currentVal + step, max);
        break;
      case 'ArrowLeft':
      case 'ArrowDown':
        event.preventDefault();
        newValue = Math.max(currentVal - step, min);
        break;
      case 'PageUp':
        event.preventDefault();
        newValue = Math.min(currentVal + step * 10, max);
        break;
      case 'PageDown':
        event.preventDefault();
        newValue = Math.max(currentVal - step * 10, min);
        break;
      case 'Home':
        event.preventDefault();
        newValue = min;
        break;
      case 'End':
        event.preventDefault();
        newValue = max;
        break;
    }

    if (newValue !== currentVal) {
      const syntheticEvent = {
        ...event,
        target: { ...event.target, value: newValue.toString() },
        currentTarget: event.currentTarget
      } as React.ChangeEvent<HTMLInputElement>;
      
      handleChange(syntheticEvent);
    }
  }, [isDisabled, currentValue, range, step, min, max, handleChange]);

  const handleFocus = useCallback((event: React.FocusEvent<HTMLInputElement>) => {
    if (isDisabled) return;
    
    setIsDragging(true);
    onBeforeChange?.(currentValue);
    onFocus?.(event);
  }, [isDisabled, currentValue, onBeforeChange, onFocus]);

  const handleBlur = useCallback((event: React.FocusEvent<HTMLInputElement>) => {
    setIsDragging(false);
    onAfterChange?.(currentValue);
    onBlur?.(event);
  }, [currentValue, onAfterChange, onBlur]);

  const renderTrack = () => {
    const trackClasses = `
      relative bg-gray-200 rounded-full
      ${vertical ? sizeClasses.vertical : `w-full ${sizeClasses.track}`}
      ${isDisabled ? 'opacity-50' : ''}
    `;

    const getFilledStyle = () => {
      if (!included) return {};

      if (range && Array.isArray(currentValue)) {
        const [start, end] = currentValue;
        const startPercent = calculatePercentage(start);
        const endPercent = calculatePercentage(end);
        
        if (vertical) {
          return reverse 
            ? { top: `${100 - endPercent}%`, height: `${endPercent - startPercent}%` }
            : { bottom: `${startPercent}%`, height: `${endPercent - startPercent}%` };
        } else {
          return reverse
            ? { right: `${100 - endPercent}%`, width: `${endPercent - startPercent}%` }
            : { left: `${startPercent}%`, width: `${endPercent - startPercent}%` };
        }
      } else {
        const percent = calculatePercentage(currentValue as number);
        
        if (vertical) {
          return reverse 
            ? { top: `${100 - percent}%`, height: `${percent}%` }
            : { bottom: 0, height: `${percent}%` };
        } else {
          return reverse
            ? { right: 0, width: `${percent}%` }
            : { left: 0, width: `${percent}%` };
        }
      }
    };

    return (
      <div className={trackClasses} style={trackStyle}>
        {included && (
          <div 
            className={`absolute rounded-full ${colorClasses} ${vertical ? 'w-full' : 'h-full'}`}
            style={getFilledStyle()}
          />
        )}
      </div>
    );
  };

  const renderHandle = (val: number, index?: number) => {
    const percent = calculatePercentage(val);
    const handlePosition = vertical 
      ? (reverse ? { top: `${100 - percent}%` } : { bottom: `${percent}%` })
      : (reverse ? { right: `${percent}%` } : { left: `${percent}%` });

    return (
      <input
        key={index}
        ref={index === undefined ? (ref || sliderRef) : (index === 0 ? ref : undefined)}
        id={index === 0 ? id : undefined}
        name={index === 0 ? name : undefined}
        type="range"
        role="slider"
        min={min}
        max={max}
        step={step}
        value={val}
        disabled={isDisabled}
        tabIndex={tabIndex}
        onChange={(e) => handleChange(e, index)}
        onKeyDown={handleKeyDown}
        onFocus={handleFocus}
        onBlur={handleBlur}
        onMouseEnter={() => tooltip && setShowTooltip(true)}
        onMouseLeave={() => tooltip && setShowTooltip(false)}
        aria-valuenow={val}
        aria-valuemin={min}
        aria-valuemax={max}
        aria-label={ariaLabel}
        aria-labelledby={ariaLabelledBy}
        aria-describedby={ariaDescribedBy}
        className="absolute appearance-none bg-transparent cursor-pointer focus:outline-none"
        style={{
          ...handlePosition,
          transform: vertical ? 'translateY(50%)' : 'translateX(-50%)',
          ...handleStyle,
          width: vertical ? '100%' : sizeClasses.handle.split(' ')[0].replace('w-', ''),
          height: vertical ? sizeClasses.handle.split(' ')[1].replace('h-', '') : '100%'
        }}
      />
    );
  };

  const renderTooltip = (val: number, index?: number) => {
    if (!tooltip || (!showTooltip && !isDragging)) return null;

    const percent = calculatePercentage(val);
    const tooltipPosition = vertical 
      ? (reverse ? { top: `${100 - percent}%` } : { bottom: `${percent}%` })
      : (reverse ? { right: `${percent}%` } : { left: `${percent}%` });

    const displayValue = tooltipFormatter ? tooltipFormatter(val) : val.toString();

    return (
      <div
        key={`tooltip-${index}`}
        className="absolute bg-gray-900 text-white text-xs px-2 py-1 rounded pointer-events-none z-10"
        style={{
          ...tooltipPosition,
          transform: vertical 
            ? 'translateY(50%) translateX(20px)' 
            : 'translateX(-50%) translateY(-30px)'
        }}
      >
        {displayValue}
      </div>
    );
  };

  const renderMarks = () => {
    if (!marks) return null;

    return Object.entries(marks).map(([value, label]) => {
      const val = Number(value);
      const percent = calculatePercentage(val);
      const markPosition = vertical 
        ? (reverse ? { top: `${100 - percent}%` } : { bottom: `${percent}%` })
        : (reverse ? { right: `${percent}%` } : { left: `${percent}%` });

      return (
        <div key={value} className="absolute" style={markPosition}>
          <div className={`w-1 h-1 bg-gray-400 rounded-full ${vertical ? '' : 'transform -translate-x-1/2'}`} />
          <div className={`text-xs text-gray-500 mt-2 ${vertical ? 'ml-3' : 'transform -translate-x-1/2'}`}>
            {label}
          </div>
        </div>
      );
    });
  };

  const renderDots = () => {
    if (!dots) return null;

    const stepCount = Math.floor((max - min) / step) + 1;
    const dotElements = [];

    for (let i = 0; i < stepCount; i++) {
      const val = min + i * step;
      const percent = calculatePercentage(val);
      const dotPosition = vertical 
        ? (reverse ? { top: `${100 - percent}%` } : { bottom: `${percent}%` })
        : (reverse ? { right: `${percent}%` } : { left: `${percent}%` });

      dotElements.push(
        <div
          key={i}
          data-testid="slider-dot"
          className={`absolute w-2 h-2 bg-gray-400 rounded-full ${vertical ? '' : 'transform -translate-x-1/2'}`}
          style={{
            ...dotPosition,
            transform: vertical ? 'translateY(50%)' : 'translateX(-50%)'
          }}
        />
      );
    }

    return dotElements;
  };

  if (loading) {
    return (
      <div className={`relative ${vertical ? 'flex flex-col' : ''} ${className}`}>
        <div className="flex items-center justify-center">
          <div 
            className="w-4 h-4 border-2 border-gray-300 border-t-blue-500 rounded-full animate-spin mr-2"
            role="img" 
            aria-hidden="true" 
          />
          <span className="text-gray-500 text-sm">Loading...</span>
        </div>
      </div>
    );
  }

  return (
    <div 
      ref={containerRef}
      className={`relative ${vertical ? 'flex flex-col' : ''} ${isDisabled ? 'opacity-50 cursor-not-allowed' : ''} ${className}`}
    >
      {renderTrack()}
      
      {range && Array.isArray(currentValue) ? (
        <>
          {renderHandle(currentValue[0], 0)}
          {renderHandle(currentValue[1], 1)}
          {renderTooltip(currentValue[0], 0)}
          {renderTooltip(currentValue[1], 1)}
        </>
      ) : (
        <>
          {renderHandle(currentValue as number)}
          {renderTooltip(currentValue as number)}
        </>
      )}
      
      {renderMarks()}
      {renderDots()}
    </div>
  );
});

Slider.displayName = 'Slider';

export default Slider;