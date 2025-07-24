import React, { useState, useRef, useEffect, forwardRef } from 'react';

interface InputProps extends Omit<React.InputHTMLAttributes<HTMLInputElement>, 'size' | 'prefix'> {
  size?: 'sm' | 'md' | 'lg';
  variant?: 'default' | 'filled' | 'outlined' | 'borderless';
  status?: 'default' | 'error' | 'warning' | 'success';
  prefix?: React.ReactNode;
  suffix?: React.ReactNode;
  addonBefore?: React.ReactNode;
  addonAfter?: React.ReactNode;
  allowClear?: boolean;
  showCount?: boolean;
  maxLength?: number;
  loading?: boolean;
  bordered?: boolean;
  debounce?: number;
  onDebounceChange?: (value: string) => void;
  className?: string;
  wrapperClassName?: string;
  inputClassName?: string;
  onPressEnter?: (e: React.KeyboardEvent<HTMLInputElement>) => void;
  visibilityToggle?: boolean; // For password inputs
}

export const Input = forwardRef<HTMLInputElement, InputProps>(({
  size = 'md',
  variant = 'default',
  status = 'default',
  prefix,
  suffix,
  addonBefore,
  addonAfter,
  allowClear = false,
  showCount = false,
  maxLength,
  loading = false,
  bordered = true,
  debounce,
  onDebounceChange,
  className = '',
  wrapperClassName = '',
  inputClassName = '',
  onChange,
  onPressEnter,
  visibilityToggle = false,
  type = 'text',
  value,
  defaultValue,
  disabled,
  ...props
}, ref) => {
  const [internalValue, setInternalValue] = useState(defaultValue || '');
  const [showPassword, setShowPassword] = useState(false);
  const [isFocused, setIsFocused] = useState(false);
  const internalRef = useRef<HTMLInputElement>(null);
  const debounceTimer = useRef<NodeJS.Timeout>();

  const inputRef = (ref as React.RefObject<HTMLInputElement>) || internalRef;
  const currentValue = value !== undefined ? value : internalValue;
  const isPasswordType = type === 'password';
  const actualType = isPasswordType && showPassword ? 'text' : type;

  const getSizeClasses = () => {
    const sizeMap = {
      sm: 'px-2 py-1 text-sm',
      md: 'px-3 py-2 text-sm',
      lg: 'px-4 py-3 text-base'
    };
    return sizeMap[size];
  };

  const getVariantClasses = () => {
    const variantMap = {
      default: 'bg-white border border-gray-300',
      filled: 'bg-gray-50 border-0',
      outlined: 'bg-transparent border-2 border-gray-300',
      borderless: 'bg-transparent border-0'
    };
    return variantMap[variant];
  };

  const getStatusClasses = () => {
    if (disabled) return 'border-gray-200 text-gray-400 bg-gray-50';
    
    const statusMap = {
      default: '',
      error: 'border-red-500 focus:border-red-500 focus:ring-red-500',
      warning: 'border-yellow-500 focus:border-yellow-500 focus:ring-yellow-500',
      success: 'border-green-500 focus:border-green-500 focus:ring-green-500'
    };
    return statusMap[status];
  };

  const getWrapperClasses = () => {
    const baseClasses = `
      relative inline-flex items-center w-full transition-colors duration-200
      ${getVariantClasses()}
      ${getStatusClasses()}
      ${isFocused && status === 'default' ? 'border-blue-500 ring-1 ring-blue-500' : ''}
      ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-text'}
      ${bordered ? '' : 'border-0'}
      rounded-md
    `;
    return `${baseClasses} ${wrapperClassName}`.trim();
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newValue = e.target.value;
    
    if (value === undefined) {
      setInternalValue(newValue);
    }
    
    onChange?.(e);
    
    if (debounce && onDebounceChange) {
      if (debounceTimer.current) {
        clearTimeout(debounceTimer.current);
      }
      debounceTimer.current = setTimeout(() => {
        onDebounceChange(newValue);
      }, debounce);
    }
  };

  const handleClear = () => {
    const syntheticEvent = {
      target: { value: '' },
      currentTarget: { value: '' }
    } as React.ChangeEvent<HTMLInputElement>;
    
    if (value === undefined) {
      setInternalValue('');
    }
    
    onChange?.(syntheticEvent);
    inputRef.current?.focus();
  };

  const handleFocus = (e: React.FocusEvent<HTMLInputElement>) => {
    setIsFocused(true);
    props.onFocus?.(e);
  };

  const handleBlur = (e: React.FocusEvent<HTMLInputElement>) => {
    setIsFocused(false);
    props.onBlur?.(e);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      onPressEnter?.(e);
    }
    props.onKeyDown?.(e);
  };

  const togglePasswordVisibility = () => {
    setShowPassword(!showPassword);
  };

  const shouldShowClear = allowClear && currentValue && !disabled;
  const shouldShowCount = showCount && maxLength;
  const characterCount = String(currentValue).length;

  useEffect(() => {
    return () => {
      if (debounceTimer.current) {
        clearTimeout(debounceTimer.current);
      }
    };
  }, []);

  const renderPrefix = () => {
    if (!prefix) return null;
    return (
      <span className="flex-shrink-0 text-gray-500 mr-2">
        {prefix}
      </span>
    );
  };

  const renderSuffix = () => {
    const suffixElements = [];
    
    if (loading) {
      suffixElements.push(
        <div key="loading" className="flex-shrink-0 ml-2">
          <div className="w-4 h-4 border-2 border-gray-300 border-t-blue-500 rounded-full animate-spin" />
        </div>
      );
    }
    
    if (shouldShowCount) {
      suffixElements.push(
        <span key="count" className={`flex-shrink-0 ml-2 text-xs ${characterCount > maxLength! ? 'text-red-500' : 'text-gray-400'}`}>
          {characterCount}/{maxLength}
        </span>
      );
    }
    
    if (shouldShowClear) {
      suffixElements.push(
        <button
          key="clear"
          type="button"
          onClick={handleClear}
          className="flex-shrink-0 ml-2 p-1 text-gray-400 hover:text-gray-600 transition-colors rounded"
          tabIndex={-1}
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      );
    }
    
    if (isPasswordType && visibilityToggle) {
      suffixElements.push(
        <button
          key="visibility"
          type="button"
          onClick={togglePasswordVisibility}
          className="flex-shrink-0 ml-2 p-1 text-gray-400 hover:text-gray-600 transition-colors rounded"
          tabIndex={-1}
        >
          {showPassword ? (
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.878 9.878L3 3m6.878 6.878L21 21" />
            </svg>
          ) : (
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
            </svg>
          )}
        </button>
      );
    }
    
    if (suffix) {
      suffixElements.push(
        <span key="suffix" className="flex-shrink-0 ml-2 text-gray-500">
          {suffix}
        </span>
      );
    }
    
    return suffixElements.length > 0 ? (
      <div className="flex items-center">
        {suffixElements}
      </div>
    ) : null;
  };

  const inputElement = (
    <div className={getWrapperClasses()}>
      {renderPrefix()}
      <input
        {...props}
        ref={inputRef}
        type={actualType}
        value={currentValue}
        onChange={handleChange}
        onFocus={handleFocus}
        onBlur={handleBlur}
        onKeyDown={handleKeyDown}
        maxLength={maxLength}
        disabled={disabled}
        className={`
          flex-1 bg-transparent outline-none placeholder-gray-400 min-w-0
          ${disabled ? 'cursor-not-allowed' : ''}
          ${inputClassName}
        `}
      />
      {renderSuffix()}
    </div>
  );

  if (addonBefore || addonAfter) {
    return (
      <div className={`inline-flex w-full ${className}`}>
        {addonBefore && (
          <span className={`
            inline-flex items-center px-3 border border-r-0 border-gray-300 
            bg-gray-50 text-gray-500 text-sm rounded-l-md
            ${getSizeClasses()}
          `}>
            {addonBefore}
          </span>
        )}
        <div className="flex-1">
          {React.cloneElement(inputElement, {
            className: `
              ${getWrapperClasses()} 
              ${addonBefore ? 'rounded-l-none border-l-0' : ''}
              ${addonAfter ? 'rounded-r-none border-r-0' : ''}
            `
          })}
        </div>
        {addonAfter && (
          <span className={`
            inline-flex items-center px-3 border border-l-0 border-gray-300 
            bg-gray-50 text-gray-500 text-sm rounded-r-md
            ${getSizeClasses()}
          `}>
            {addonAfter}
          </span>
        )}
      </div>
    );
  }

  return (
    <div className={className}>
      {inputElement}
    </div>
  );
});

Input.displayName = 'Input';

// Input.Password component
const Password = forwardRef<HTMLInputElement, Omit<InputProps, 'type' | 'visibilityToggle'>>(
  (props, ref) => {
    return <Input {...props} ref={ref} type="password" visibilityToggle={true} />;
  }
);

Password.displayName = 'Input.Password';

// Input.TextArea component
interface TextAreaProps extends Omit<React.TextareaHTMLAttributes<HTMLTextAreaElement>, 'size'> {
  size?: 'sm' | 'md' | 'lg';
  variant?: 'default' | 'filled' | 'outlined' | 'borderless';
  status?: 'default' | 'error' | 'warning' | 'success';
  showCount?: boolean;
  maxLength?: number;
  allowClear?: boolean;
  autoSize?: boolean | { minRows?: number; maxRows?: number };
  bordered?: boolean;
  className?: string;
}

const TextArea = forwardRef<HTMLTextAreaElement, TextAreaProps>(({
  size = 'md',
  variant = 'default',
  status = 'default',
  showCount = false,
  maxLength,
  allowClear = false,
  autoSize = false,
  bordered = true,
  className = '',
  onChange,
  value,
  defaultValue,
  disabled,
  ...props
}, ref) => {
  const [internalValue, setInternalValue] = useState(defaultValue || '');
  const [isFocused, setIsFocused] = useState(false);
  const internalRef = useRef<HTMLTextAreaElement>(null);
  const textareaRef = (ref as React.RefObject<HTMLTextAreaElement>) || internalRef;

  const currentValue = value !== undefined ? value : internalValue;
  const characterCount = String(currentValue).length;

  const getSizeClasses = () => {
    const sizeMap = {
      sm: 'px-2 py-1 text-sm',
      md: 'px-3 py-2 text-sm',
      lg: 'px-4 py-3 text-base'
    };
    return sizeMap[size];
  };

  const getVariantClasses = () => {
    const variantMap = {
      default: 'bg-white border border-gray-300',
      filled: 'bg-gray-50 border-0',
      outlined: 'bg-transparent border-2 border-gray-300',
      borderless: 'bg-transparent border-0'
    };
    return variantMap[variant];
  };

  const getStatusClasses = () => {
    if (disabled) return 'border-gray-200 text-gray-400 bg-gray-50';
    
    const statusMap = {
      default: 'focus:border-blue-500 focus:ring-1 focus:ring-blue-500',
      error: 'border-red-500 focus:border-red-500 focus:ring-red-500',
      warning: 'border-yellow-500 focus:border-yellow-500 focus:ring-yellow-500',
      success: 'border-green-500 focus:border-green-500 focus:ring-green-500'
    };
    return statusMap[status];
  };

  const adjustHeight = () => {
    if (autoSize && textareaRef.current) {
      const textarea = textareaRef.current;
      textarea.style.height = 'auto';
      
      const minRows = typeof autoSize === 'object' ? autoSize.minRows : undefined;
      const maxRows = typeof autoSize === 'object' ? autoSize.maxRows : undefined;
      
      let newHeight = textarea.scrollHeight;
      
      if (minRows) {
        const lineHeight = parseInt(getComputedStyle(textarea).lineHeight);
        newHeight = Math.max(newHeight, lineHeight * minRows);
      }
      
      if (maxRows) {
        const lineHeight = parseInt(getComputedStyle(textarea).lineHeight);
        newHeight = Math.min(newHeight, lineHeight * maxRows);
      }
      
      textarea.style.height = `${newHeight}px`;
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const newValue = e.target.value;
    
    if (value === undefined) {
      setInternalValue(newValue);
    }
    
    onChange?.(e);
    adjustHeight();
  };

  const handleClear = () => {
    const syntheticEvent = {
      target: { value: '' },
      currentTarget: { value: '' }
    } as React.ChangeEvent<HTMLTextAreaElement>;
    
    if (value === undefined) {
      setInternalValue('');
    }
    
    onChange?.(syntheticEvent);
    textareaRef.current?.focus();
    adjustHeight();
  };

  useEffect(() => {
    adjustHeight();
  }, [currentValue, autoSize]);

  return (
    <div className={`relative ${className}`}>
      <textarea
        {...props}
        ref={textareaRef}
        value={currentValue}
        onChange={handleChange}
        onFocus={(e) => {
          setIsFocused(true);
          props.onFocus?.(e);
        }}
        onBlur={(e) => {
          setIsFocused(false);
          props.onBlur?.(e);
        }}
        maxLength={maxLength}
        disabled={disabled}
        className={`
          w-full resize-none outline-none placeholder-gray-400 transition-colors duration-200
          ${getSizeClasses()}
          ${getVariantClasses()}
          ${getStatusClasses()}
          ${bordered ? '' : 'border-0'}
          ${disabled ? 'opacity-50 cursor-not-allowed' : ''}
          rounded-md
        `}
      />
      
      {allowClear && currentValue && !disabled && (
        <button
          type="button"
          onClick={handleClear}
          className="absolute top-2 right-2 p-1 text-gray-400 hover:text-gray-600 transition-colors rounded"
          tabIndex={-1}
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      )}
      
      {showCount && maxLength && (
        <div className={`absolute bottom-2 right-2 text-xs ${characterCount > maxLength ? 'text-red-500' : 'text-gray-400'}`}>
          {characterCount}/{maxLength}
        </div>
      )}
    </div>
  );
});

TextArea.displayName = 'Input.TextArea';

// Attach sub-components
(Input as any).Password = Password;
(Input as any).TextArea = TextArea;

export default Input;