import React, { useState, useRef, useEffect, forwardRef } from 'react';

interface TextareaProps {
  label?: string;
  value?: string;
  defaultValue?: string;
  placeholder?: string;
  onChange?: (value: string) => void;
  onFocus?: (event: React.FocusEvent<HTMLTextAreaElement>) => void;
  onBlur?: (event: React.FocusEvent<HTMLTextAreaElement>) => void;
  onKeyDown?: (event: React.KeyboardEvent<HTMLTextAreaElement>) => void;
  onKeyUp?: (event: React.KeyboardEvent<HTMLTextAreaElement>) => void;
  onPaste?: (event: React.ClipboardEvent<HTMLTextAreaElement>) => void;
  disabled?: boolean;
  readonly?: boolean;
  required?: boolean;
  rows?: number;
  cols?: number;
  minLength?: number;
  maxLength?: number;
  size?: 'sm' | 'md' | 'lg';
  variant?: 'primary' | 'secondary' | 'success' | 'warning' | 'danger';
  resize?: 'none' | 'vertical' | 'horizontal' | 'both';
  rounded?: 'none' | 'sm' | 'md' | 'lg' | 'xl';
  autoResize?: boolean;
  showCount?: boolean;
  loading?: boolean;
  spellCheck?: boolean;
  autoComplete?: string;
  wrap?: 'soft' | 'hard' | 'off';
  icon?: React.ReactNode;
  description?: string;
  error?: string;
  success?: string;
  warning?: string;
  tooltip?: string;
  background?: string;
  className?: string;
  style?: React.CSSProperties;
  'aria-describedby'?: string;
  'aria-label'?: string;
  role?: string;
}

const Textarea = forwardRef<HTMLTextAreaElement, TextareaProps>(({
  label,
  value,
  defaultValue,
  placeholder,
  onChange,
  onFocus,
  onBlur,
  onKeyDown,
  onKeyUp,
  onPaste,
  disabled = false,
  readonly = false,
  required = false,
  rows = 3,
  cols,
  minLength,
  maxLength,
  size = 'md',
  variant = 'primary',
  resize = 'vertical',
  rounded = 'md',
  autoResize = false,
  showCount = false,
  loading = false,
  spellCheck,
  autoComplete,
  wrap = 'soft',
  icon,
  description,
  error,
  success,
  warning,
  tooltip,
  background,
  className = '',
  style,
  'aria-describedby': ariaDescribedBy,
  'aria-label': ariaLabel,
  role,
  ...props
}, ref) => {
  const [internalValue, setInternalValue] = useState(defaultValue || '');
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  
  const isControlled = value !== undefined;
  const currentValue = isControlled ? value : internalValue;

  useEffect(() => {
    if (autoResize && textareaRef.current) {
      const textarea = textareaRef.current;
      textarea.style.height = 'auto';
      textarea.style.height = `${textarea.scrollHeight}px`;
    }
  }, [currentValue, autoResize]);

  const getSizeClasses = () => {
    const sizeMap = {
      sm: 'text-sm px-3 py-2',
      md: 'text-base px-4 py-3',
      lg: 'text-lg px-5 py-4'
    };
    return sizeMap[size];
  };

  const getVariantClasses = () => {
    if (error) return 'border-red-500 focus:border-red-500 focus:ring-red-500';
    if (success) return 'border-green-500 focus:border-green-500 focus:ring-green-500';
    if (warning) return 'border-yellow-500 focus:border-yellow-500 focus:ring-yellow-500';
    
    const variantMap = {
      primary: 'border-gray-300 focus:border-blue-500 focus:ring-blue-500',
      secondary: 'border-gray-300 focus:border-gray-500 focus:ring-gray-500',
      success: 'border-green-300 focus:border-green-500 focus:ring-green-500',
      warning: 'border-yellow-300 focus:border-yellow-500 focus:ring-yellow-500',
      danger: 'border-red-300 focus:border-red-500 focus:ring-red-500'
    };
    
    return variantMap[variant];
  };

  const getStateClasses = () => {
    let classes = '';
    
    if (disabled) {
      classes += ' opacity-50 cursor-not-allowed bg-gray-50';
    } else if (readonly) {
      classes += ' bg-gray-50 cursor-default';
    } else {
      classes += ' bg-white hover:border-gray-400';
    }
    
    return classes;
  };

  const getResizeClasses = () => {
    const resizeMap = {
      none: 'resize-none',
      vertical: 'resize-y',
      horizontal: 'resize-x',
      both: 'resize'
    };
    return resizeMap[resize];
  };

  const getRoundedClasses = () => {
    const roundedMap = {
      none: 'rounded-none',
      sm: 'rounded-sm',
      md: 'rounded-md',
      lg: 'rounded-lg',
      xl: 'rounded-xl'
    };
    return roundedMap[rounded];
  };

  const handleChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const newValue = e.target.value;
    
    if (!isControlled) {
      setInternalValue(newValue);
    }
    
    onChange?.(newValue);
  };

  const textareaId = `textarea-${Math.random().toString(36).substr(2, 9)}`;
  const characterCount = currentValue.length;
  const isOverLimit = maxLength && characterCount > maxLength;

  const labelElement = label && (
    <label 
      htmlFor={textareaId}
      className="block text-sm font-medium text-gray-700 mb-2"
    >
      {label}
      {required && <span className="text-red-500 ml-1">*</span>}
    </label>
  );

  const descriptionElement = description && (
    <p className="text-sm text-gray-500 mb-2">{description}</p>
  );

  const textareaElement = (
    <div className="relative">
      <textarea
        ref={(node) => {
          textareaRef.current = node;
          if (typeof ref === 'function') {
            ref(node);
          } else if (ref) {
            ref.current = node;
          }
        }}
        id={textareaId}
        value={currentValue}
        placeholder={placeholder}
        onChange={handleChange}
        onFocus={onFocus}
        onBlur={onBlur}
        onKeyDown={onKeyDown}
        onKeyUp={onKeyUp}
        onPaste={onPaste}
        disabled={disabled}
        readOnly={readonly}
        required={required}
        rows={autoResize ? 1 : rows}
        cols={cols}
        minLength={minLength}
        maxLength={maxLength}
        spellCheck={spellCheck}
        autoComplete={autoComplete}
        wrap={wrap}
        title={tooltip}
        aria-describedby={ariaDescribedBy}
        aria-label={ariaLabel}
        role={role}
        style={autoResize ? { minHeight: `${rows * 1.5}rem`, ...style } : style}
        className={[
          'w-full border shadow-sm focus:outline-none focus:ring-2 focus:ring-offset-2',
          getSizeClasses(),
          getVariantClasses(),
          getStateClasses(),
          getResizeClasses(),
          getRoundedClasses()
        ].join(' ')}
        {...props}
      />
      
      {loading && (
        <div className="absolute top-3 right-3">
          <svg
            className="w-4 h-4 animate-spin text-gray-400"
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
      
      {icon && (
        <div className="absolute top-3 right-3 text-gray-400">
          {icon}
        </div>
      )}
    </div>
  );

  const countElement = showCount && maxLength && (
    <div className={`text-sm text-right mt-2 ${isOverLimit ? 'text-red-500' : 'text-gray-500'}`}>
      {characterCount}/{maxLength}
    </div>
  );

  const messageElement = (error || success || warning) && (
    <div className="mt-2">
      {error && <p className="text-sm text-red-600">{error}</p>}
      {success && <p className="text-sm text-green-600">{success}</p>}
      {warning && <p className="text-sm text-yellow-600">{warning}</p>}
    </div>
  );

  return (
    <div className={className}>
      <div className={background || ''}>
        {labelElement}
        {descriptionElement}
        {textareaElement}
        {countElement}
        {messageElement}
      </div>
    </div>
  );
});

Textarea.displayName = 'Textarea';

export { Textarea };
export default Textarea;