import React, { useState, useEffect, useRef, forwardRef } from 'react';

interface CheckboxProps {
  label?: string;
  checked?: boolean;
  defaultChecked?: boolean;
  onChange?: (checked: boolean) => void;
  onFocus?: (event: React.FocusEvent<HTMLInputElement>) => void;
  onBlur?: (event: React.FocusEvent<HTMLInputElement>) => void;
  disabled?: boolean;
  readonly?: boolean;
  required?: boolean;
  indeterminate?: boolean;
  size?: 'sm' | 'md' | 'lg';
  variant?: 'primary' | 'secondary' | 'success' | 'warning' | 'danger';
  color?: string;
  background?: string;
  rounded?: boolean;
  loading?: boolean;
  animate?: boolean;
  icon?: React.ReactNode;
  checkIcon?: React.ReactNode;
  description?: string;
  error?: string;
  success?: string;
  warning?: string;
  tooltip?: string;
  labelPosition?: 'left' | 'right';
  value?: string;
  className?: string;
  style?: React.CSSProperties;
  'aria-describedby'?: string;
  'aria-required'?: string;
  role?: string;
}

interface CheckboxGroupProps {
  children: React.ReactNode;
  label?: string;
  value?: string[];
  defaultValue?: string[];
  onChange?: (value: string[]) => void;
  disabled?: boolean;
  error?: string;
  success?: string;
  warning?: string;
  description?: string;
  selectAll?: boolean;
  selectAllLabel?: string;
  orientation?: 'horizontal' | 'vertical';
  spacing?: string;
  className?: string;
}

const CheckboxComponent = forwardRef<HTMLInputElement, CheckboxProps>(({
  label,
  checked,
  defaultChecked,
  onChange,
  onFocus,
  onBlur,
  disabled = false,
  readonly = false,
  required = false,
  indeterminate = false,
  size = 'md',
  variant = 'primary',
  color,
  background,
  rounded = false,
  loading = false,
  animate = false,
  icon,
  checkIcon,
  description,
  error,
  success,
  warning,
  tooltip,
  labelPosition = 'right',
  value,
  className = '',
  style,
  'aria-describedby': ariaDescribedBy,
  'aria-required': ariaRequired,
  role,
  ...props
}, ref) => {
  const [isChecked, setIsChecked] = useState(defaultChecked || false);
  const checkboxRef = useRef<HTMLInputElement>(null);
  
  const isControlled = checked !== undefined;
  const checkedState = isControlled ? checked : isChecked;

  useEffect(() => {
    if (checkboxRef.current) {
      checkboxRef.current.indeterminate = indeterminate;
    }
  }, [indeterminate]);

  const getSizeClasses = () => {
    const sizeMap = {
      sm: 'w-4 h-4',
      md: 'w-5 h-5',
      lg: 'w-6 h-6'
    };
    return sizeMap[size];
  };

  const getVariantClasses = () => {
    if (error) return 'border-red-500 text-red-600 focus:ring-red-500';
    if (success) return 'border-green-500 text-green-600 focus:ring-green-500';
    if (warning) return 'border-yellow-500 text-yellow-600 focus:ring-yellow-500';
    
    if (color) return `text-${color}-600 focus:ring-${color}-500`;
    
    const variantMap = {
      primary: 'text-blue-600 focus:ring-blue-500',
      secondary: 'text-gray-600 focus:ring-gray-500',
      success: 'text-green-600 focus:ring-green-500',
      warning: 'text-yellow-600 focus:ring-yellow-500',
      danger: 'text-red-600 focus:ring-red-500'
    };
    
    return variantMap[variant];
  };

  const getStateClasses = () => {
    let classes = '';
    
    if (disabled) {
      classes += ' opacity-50 cursor-not-allowed';
    } else {
      classes += ' cursor-pointer hover:bg-gray-50';
    }
    
    if (animate) {
      classes += ' transition-all duration-200';
    }
    
    if (rounded) {
      classes += ' rounded-lg';
    } else {
      classes += ' rounded';
    }
    
    return classes;
  };

  const getFlexDirection = () => {
    return labelPosition === 'left' ? 'flex-row-reverse' : 'flex-row';
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (disabled || readonly) return;
    
    const newChecked = e.target.checked;
    
    if (!isControlled) {
      setIsChecked(newChecked);
    }
    
    onChange?.(newChecked);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === ' ') {
      e.preventDefault();
      handleChange({ target: { checked: !checkedState } } as React.ChangeEvent<HTMLInputElement>);
    }
  };

  const checkboxId = `checkbox-${value || Math.random()}`;
  
  const checkboxElement = (
    <div className="relative">
      <input
        ref={(node) => {
          checkboxRef.current = node;
          if (typeof ref === 'function') {
            ref(node);
          } else if (ref) {
            ref.current = node;
          }
        }}
        id={checkboxId}
        type="checkbox"
        checked={checkedState}
        onChange={handleChange}
        onFocus={onFocus}
        onBlur={onBlur}
        onKeyDown={handleKeyDown}
        disabled={disabled}
        readOnly={readonly}
        required={required}
        value={value}
        title={tooltip}
        aria-describedby={ariaDescribedBy}
        aria-required={ariaRequired}
        role={role}
        className={[
          getSizeClasses(),
          getVariantClasses(),
          getStateClasses(),
          'border-gray-300 bg-white focus:ring-2 focus:ring-offset-2'
        ].join(' ')}
        {...props}
      />
      
      {loading && (
        <div className="absolute inset-0 flex items-center justify-center">
          <svg
            className="w-3 h-3 animate-spin text-current"
            fill="none"
            viewBox="0 0 24 24"
            role="img"
            aria-hidden="true"
          >
            <circle
              className="opacity-25"
              cx="12"
              cy="12"
              r="10"
              stroke="currentColor"
              strokeWidth="4"
            />
            <path
              className="opacity-75"
              fill="currentColor"
              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
            />
          </svg>
        </div>
      )}
      
      {checkedState && checkIcon && !loading && (
        <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
          {checkIcon}
        </div>
      )}
    </div>
  );

  const labelElement = label && (
    <label 
      htmlFor={checkboxId}
      className={`select-none ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'} ${labelPosition === 'left' ? 'mr-3' : 'ml-3'}`}
    >
      <div className="flex items-center">
        {icon && <span className="mr-2">{icon}</span>}
        <span className="text-sm font-medium text-gray-900">{label}</span>
      </div>
      {description && (
        <p className="text-sm text-gray-500 mt-1">{description}</p>
      )}
    </label>
  );

  const messageElement = (error || success || warning) && (
    <div className="mt-2">
      {error && <p className="text-sm text-red-600">{error}</p>}
      {success && <p className="text-sm text-green-600">{success}</p>}
      {warning && <p className="text-sm text-yellow-600">{warning}</p>}
    </div>
  );

  return (
    <div className={className} style={style}>
      <div 
        className={[
          'flex items-start',
          getFlexDirection(),
          background || ''
        ].filter(Boolean).join(' ')}
      >
        {checkboxElement}
        {labelElement}
      </div>
      {messageElement}
    </div>
  );
});

CheckboxComponent.displayName = 'Checkbox';

const CheckboxGroup: React.FC<CheckboxGroupProps> = ({
  children,
  label,
  value = [],
  defaultValue = [],
  onChange,
  disabled = false,
  error,
  success,
  warning,
  description,
  selectAll = false,
  selectAllLabel = 'Select All',
  orientation = 'vertical',
  spacing = 'space-y-2',
  className = ''
}) => {
  const [selectedValues, setSelectedValues] = useState<string[]>(defaultValue);
  
  const isControlled = value !== undefined;
  const currentValues = isControlled ? value : selectedValues;

  const childrenArray = React.Children.toArray(children);
  const allValues = childrenArray
    .filter((child): child is React.ReactElement => React.isValidElement(child))
    .map(child => child.props.value)
    .filter(Boolean);

  const handleSelectAll = (checked: boolean) => {
    const newValues = checked ? allValues : [];
    
    if (!isControlled) {
      setSelectedValues(newValues);
    }
    
    onChange?.(newValues);
  };

  const handleChildChange = (childValue: string, checked: boolean) => {
    let newValues: string[];
    
    if (checked) {
      newValues = [...currentValues, childValue];
    } else {
      newValues = currentValues.filter(v => v !== childValue);
    }
    
    if (!isControlled) {
      setSelectedValues(newValues);
    }
    
    onChange?.(newValues);
  };

  const isAllSelected = allValues.length > 0 && allValues.every(val => currentValues.includes(val));
  const isIndeterminate = currentValues.length > 0 && currentValues.length < allValues.length;

  const getGroupSpacing = () => {
    if (orientation === 'horizontal') {
      return spacing.replace('space-y-', 'space-x-');
    }
    return spacing;
  };

  const getGroupDirection = () => {
    return orientation === 'horizontal' ? 'flex-row' : 'flex-col';
  };

  return (
    <div className={className}>
      {label && (
        <div className="mb-4">
          <h3 className="text-base font-medium text-gray-900">{label}</h3>
          {description && (
            <p className="text-sm text-gray-500 mt-1">{description}</p>
          )}
        </div>
      )}
      
      {selectAll && (
        <div className="mb-3">
          <CheckboxComponent
            label={selectAllLabel}
            checked={isAllSelected}
            indeterminate={isIndeterminate}
            onChange={handleSelectAll}
            disabled={disabled}
          />
        </div>
      )}
      
      <div className={`flex ${getGroupDirection()} ${getGroupSpacing()}`}>
        {React.Children.map(children, (child) => {
          if (!React.isValidElement(child)) return child;
          
          const childValue = child.props.value;
          const isChecked = currentValues.includes(childValue);
          
          return React.cloneElement(child as React.ReactElement<CheckboxProps>, {
            ...child.props,
            checked: isChecked,
            onChange: (checked: boolean) => handleChildChange(childValue, checked),
            disabled: disabled || child.props.disabled
          });
        })}
      </div>
      
      {(error || success || warning) && (
        <div className="mt-3">
          {error && <p className="text-sm text-red-600">{error}</p>}
          {success && <p className="text-sm text-green-600">{success}</p>}
          {warning && <p className="text-sm text-yellow-600">{warning}</p>}
        </div>
      )}
    </div>
  );
};

type CheckboxType = typeof CheckboxComponent & {
  Group: typeof CheckboxGroup;
};

const Checkbox = CheckboxComponent as CheckboxType;
Checkbox.Group = CheckboxGroup;

export { Checkbox };
export default Checkbox;