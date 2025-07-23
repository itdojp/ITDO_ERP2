import React, { useState, useCallback, forwardRef } from 'react';

interface SwitchProps {
  checked?: boolean;
  defaultChecked?: boolean;
  disabled?: boolean;
  loading?: boolean;
  size?: 'sm' | 'md' | 'lg';
  color?: 'primary' | 'success' | 'warning' | 'danger';
  checkedLabel?: string;
  uncheckedLabel?: string;
  checkedIcon?: React.ReactNode;
  uncheckedIcon?: React.ReactNode;
  description?: string;
  className?: string;
  before?: React.ReactNode;
  after?: React.ReactNode;
  onChange?: (checked: boolean, event: React.ChangeEvent<HTMLInputElement>) => void | Promise<void>;
  onFocus?: (event: React.FocusEvent<HTMLInputElement>) => void;
  onBlur?: (event: React.FocusEvent<HTMLInputElement>) => void;
  onClick?: (event: React.MouseEvent<HTMLInputElement>) => void;
  'aria-label'?: string;
  'aria-labelledby'?: string;
  'aria-describedby'?: string;
  id?: string;
  name?: string;
  value?: string;
  tabIndex?: number;
}

export const Switch = forwardRef<HTMLInputElement, SwitchProps>(({
  checked,
  defaultChecked,
  disabled = false,
  loading = false,
  size = 'md',
  color = 'primary',
  checkedLabel,
  uncheckedLabel,
  checkedIcon,
  uncheckedIcon,
  description,
  className = '',
  before,
  after,
  onChange,
  onFocus,
  onBlur,
  onClick,
  'aria-label': ariaLabel,
  'aria-labelledby': ariaLabelledBy,
  'aria-describedby': ariaDescribedBy,
  id,
  name,
  value,
  tabIndex
}, ref) => {
  const [internalChecked, setInternalChecked] = useState(() => {
    if (defaultChecked !== undefined) return defaultChecked;
    return false;
  });

  const isControlled = checked !== undefined;
  const currentChecked = isControlled ? checked : internalChecked;
  const isDisabled = disabled || loading;

  const getSizeClasses = () => {
    const sizeMap = {
      sm: {
        container: 'w-8 h-4',
        thumb: 'w-3 h-3',
        thumbPosition: currentChecked ? 'translate-x-4' : 'translate-x-0.5',
        label: 'text-xs'
      },
      md: {
        container: 'w-12 h-6',
        thumb: 'w-5 h-5',
        thumbPosition: currentChecked ? 'translate-x-6' : 'translate-x-0.5',
        label: 'text-sm'
      },
      lg: {
        container: 'w-16 h-8',
        thumb: 'w-7 h-7',
        thumbPosition: currentChecked ? 'translate-x-8' : 'translate-x-0.5',
        label: 'text-base'
      }
    };
    return sizeMap[size];
  };

  const getColorClasses = () => {
    if (isDisabled) return 'bg-gray-300';
    if (!currentChecked) return 'bg-gray-200';
    
    const colorMap = {
      primary: 'bg-blue-600',
      success: 'bg-green-600',
      warning: 'bg-yellow-600',
      danger: 'bg-red-600'
    };
    return colorMap[color];
  };

  const sizeClasses = getSizeClasses();
  const colorClasses = getColorClasses();

  const handleChange = useCallback(async (event: React.ChangeEvent<HTMLInputElement>) => {
    if (isDisabled) return;

    const newChecked = event.target.checked;
    
    if (!isControlled) {
      setInternalChecked(newChecked);
    }

    if (onChange) {
      await onChange(newChecked, event);
    }
  }, [isDisabled, isControlled, onChange]);

  const handleKeyDown = useCallback((event: React.KeyboardEvent<HTMLInputElement>) => {
    if (isDisabled) return;
    
    if (event.key === ' ' || event.key === 'Enter') {
      event.preventDefault();
      const syntheticEvent = {
        ...event,
        target: { ...event.target, checked: !currentChecked },
        currentTarget: event.currentTarget
      } as React.ChangeEvent<HTMLInputElement>;
      
      handleChange(syntheticEvent);
    }
  }, [isDisabled, currentChecked, handleChange]);

  const handleClick = useCallback((event: React.MouseEvent<HTMLInputElement>) => {
    if (isDisabled) return;
    onClick?.(event);
  }, [isDisabled, onClick]);

  const renderThumbContent = () => {
    if (loading) {
      return (
        <div className="w-3 h-3 border border-white border-t-transparent rounded-full animate-spin" 
             role="img" 
             aria-hidden="true" />
      );
    }

    if (checkedIcon && currentChecked) {
      return <span className="text-white">{checkedIcon}</span>;
    }

    if (uncheckedIcon && !currentChecked) {
      return <span className="text-gray-500">{uncheckedIcon}</span>;
    }

    return null;
  };

  const renderLabel = () => {
    const label = currentChecked ? checkedLabel : uncheckedLabel;
    if (!label) return null;

    return (
      <span className={`font-medium text-gray-700 ${sizeClasses.label}`}>
        {label}
      </span>
    );
  };

  return (
    <div className={`flex items-center gap-3 ${className}`}>
      {before && <div className="flex-shrink-0">{before}</div>}
      
      <div className="flex flex-col gap-1">
        <div className="flex items-center gap-2">
          <div className="relative">
            <input
              ref={ref}
              id={id}
              name={name}
              value={value}
              type="checkbox"
              role="switch"
              checked={currentChecked}
              disabled={isDisabled}
              tabIndex={tabIndex}
              onChange={handleChange}
              onFocus={onFocus}
              onBlur={onBlur}
              onClick={handleClick}
              onKeyDown={handleKeyDown}
              aria-checked={currentChecked}
              aria-label={ariaLabel}
              aria-labelledby={ariaLabelledBy}
              aria-describedby={ariaDescribedBy}
              className="sr-only"
            />
            
            <div
              className={`
                relative inline-flex items-center rounded-full transition-colors duration-200 ease-in-out
                ${sizeClasses.container}
                ${colorClasses}
                ${isDisabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
                focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2
              `}
              onClick={() => !isDisabled && ref?.current?.click()}
            >
              <span
                className={`
                  inline-block bg-white rounded-full shadow transform transition-transform duration-200 ease-in-out
                  flex items-center justify-center
                  ${sizeClasses.thumb}
                  ${sizeClasses.thumbPosition}
                `}
              >
                {renderThumbContent()}
              </span>
            </div>
          </div>
          
          {renderLabel()}
        </div>
        
        {description && (
          <p className={`text-gray-500 ${sizeClasses.label}`}>
            {description}
          </p>
        )}
      </div>
      
      {after && <div className="flex-shrink-0">{after}</div>}
    </div>
  );
});

Switch.displayName = 'Switch';

export default Switch;