import React, { useState, useEffect, useRef, useCallback } from 'react';
import { createPortal } from 'react-dom';
import { cn } from '@/lib/utils';
import { Calendar } from './Calendar';

export interface DateRange {
  start: Date;
  end: Date;
}

export interface DatePickerProps {
  value?: Date | Date[] | DateRange | null;
  defaultValue?: Date | Date[] | DateRange | null;
  mode?: 'single' | 'multiple' | 'range';
  format?: string;
  placeholder?: string;
  size?: 'sm' | 'md' | 'lg';
  theme?: 'light' | 'dark';
  disabled?: boolean;
  readonly?: boolean;
  required?: boolean;
  clearable?: boolean;
  showIcon?: boolean;
  showTime?: boolean;
  inline?: boolean;
  portal?: boolean;
  animated?: boolean;
  closeOnSelect?: boolean;
  autoAdjustPosition?: boolean;
  loading?: boolean;
  error?: string | boolean;
  success?: boolean;
  warning?: boolean;
  label?: string;
  helperText?: string;
  position?: 'bottom' | 'top' | 'left' | 'right';
  zIndex?: number;
  minDate?: Date;
  maxDate?: Date;
  disabledDates?: Date[];
  isDateValid?: (date: Date) => boolean;
  loadingComponent?: React.ReactNode;
  customInput?: React.ReactElement;
  customCalendar?: React.ReactElement;
  inputProps?: React.InputHTMLAttributes<HTMLInputElement>;
  calendarProps?: any;
  onChange?: (date: Date | null) => void;
  onRangeChange?: (range: DateRange | null) => void;
  onMultipleChange?: (dates: Date[]) => void;
  onFocus?: (e: React.FocusEvent<HTMLInputElement>) => void;
  onBlur?: (e: React.FocusEvent<HTMLInputElement>) => void;
  onError?: (error: string) => void;
  className?: string;
  'data-testid'?: string;
  'data-category'?: string;
  'data-id'?: string;
}

export const DatePicker: React.FC<DatePickerProps> = ({
  value,
  defaultValue,
  mode = 'single',
  format = 'MM/dd/yyyy',
  placeholder = 'Select date',
  size = 'md',
  theme = 'light',
  disabled = false,
  readonly = false,
  required = false,
  clearable = false,
  showIcon = true,
  showTime = false,
  inline = false,
  portal = false,
  animated = false,
  closeOnSelect = true,
  autoAdjustPosition = true,
  loading = false,
  error,
  success = false,
  warning = false,
  label,
  helperText,
  position = 'bottom',
  zIndex = 1000,
  minDate,
  maxDate,
  disabledDates,
  isDateValid,
  loadingComponent,
  customInput,
  customCalendar,
  inputProps,
  calendarProps,
  onChange,
  onRangeChange,
  onMultipleChange,
  onFocus,
  onBlur,
  onError,
  className,
  'data-testid': dataTestId = 'datepicker-container',
  'data-category': dataCategory,
  'data-id': dataId,
  ...props
}) => {
  const [isOpen, setIsOpen] = useState(inline);
  const [internalValue, setInternalValue] = useState(value || defaultValue);
  const [inputValue, setInputValue] = useState('');
  const [calendarPosition, setCalendarPosition] = useState(position);

  const containerRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const calendarRef = useRef<HTMLDivElement>(null);

  const sizeClasses = {
    sm: 'size-sm text-sm px-3 py-1.5',
    md: 'size-md text-base px-4 py-2',
    lg: 'size-lg text-lg px-5 py-3'
  };

  const themeClasses = {
    light: 'theme-light bg-white border-gray-300 text-gray-900',
    dark: 'theme-dark bg-gray-800 border-gray-600 text-white'
  };

  // Format date for display
  const formatDate = useCallback((date: Date | null) => {
    if (!date) return '';
    
    if (showTime) {
      const timeStr = date.toLocaleTimeString('en-US', { 
        hour12: false, 
        hour: '2-digit', 
        minute: '2-digit' 
      });
      return `${formatDateOnly(date)} ${timeStr}`;
    }
    
    return formatDateOnly(date);
  }, [showTime, format]);

  const formatDateOnly = (date: Date) => {
    const day = date.getDate().toString().padStart(2, '0');
    const month = (date.getMonth() + 1).toString().padStart(2, '0');
    const year = date.getFullYear().toString();
    
    switch (format) {
      case 'MM-dd-yyyy':
        return `${month}-${day}-${year}`;
      case 'dd/MM/yyyy':
        return `${day}/${month}/${year}`;
      case 'yyyy-MM-dd':
        return `${year}-${month}-${day}`;
      default:
        return `${month}/${day}/${year}`;
    }
  };

  // Parse date from string
  const parseDate = (dateStr: string): Date | null => {
    if (!dateStr) return null;
    
    const parts = dateStr.split(/[-/]/);
    if (parts.length !== 3) return null;
    
    let day: number, month: number, year: number;
    
    switch (format) {
      case 'MM-dd-yyyy':
      case 'MM/dd/yyyy':
        [month, day, year] = parts.map(Number);
        break;
      case 'dd/MM/yyyy':
        [day, month, year] = parts.map(Number);
        break;
      case 'yyyy-MM-dd':
        [year, month, day] = parts.map(Number);
        break;
      default:
        [month, day, year] = parts.map(Number);
    }
    
    const date = new Date(year, month - 1, day);
    return isNaN(date.getTime()) ? null : date;
  };

  // Update input value when internal value changes
  useEffect(() => {
    if (mode === 'single') {
      const singleValue = internalValue as Date | null;
      setInputValue(singleValue ? formatDate(singleValue) : '');
    } else if (mode === 'range') {
      const rangeValue = internalValue as DateRange | null;
      if (rangeValue?.start && rangeValue?.end) {
        setInputValue(`${formatDate(rangeValue.start)} - ${formatDate(rangeValue.end)}`);
      } else {
        setInputValue('');
      }
    } else if (mode === 'multiple') {
      const multipleValue = internalValue as Date[] | null;
      if (multipleValue && multipleValue.length > 0) {
        setInputValue(multipleValue.map(date => formatDate(date)).join(', '));
      } else {
        setInputValue('');
      }
    }
  }, [internalValue, formatDate, mode]);

  // Close calendar on outside click
  useEffect(() => {
    if (inline) return;

    const handleClickOutside = (event: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
      return () => document.removeEventListener('mousedown', handleClickOutside);
    }
  }, [isOpen, inline]);

  // Auto-adjust position
  useEffect(() => {
    if (!autoAdjustPosition || !isOpen || inline) return;

    const updatePosition = () => {
      if (!inputRef.current || !calendarRef.current) return;

      const inputRect = inputRef.current.getBoundingClientRect();
      const calendarRect = calendarRef.current.getBoundingClientRect();
      const viewportHeight = window.innerHeight;
      const viewportWidth = window.innerWidth;

      let newPosition = position;

      // Check if calendar fits below input
      if (position === 'bottom' && inputRect.bottom + calendarRect.height > viewportHeight) {
        newPosition = 'top';
      }
      // Check if calendar fits above input
      else if (position === 'top' && inputRect.top - calendarRect.height < 0) {
        newPosition = 'bottom';
      }

      setCalendarPosition(newPosition);
    };

    updatePosition();
    window.addEventListener('scroll', updatePosition);
    window.addEventListener('resize', updatePosition);

    return () => {
      window.removeEventListener('scroll', updatePosition);
      window.removeEventListener('resize', updatePosition);
    };
  }, [isOpen, position, autoAdjustPosition, inline]);

  const handleInputClick = () => {
    if (disabled || readonly) return;
    setIsOpen(true);
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (readonly) return;
    setInputValue(e.target.value);
  };

  const handleInputBlur = (e: React.FocusEvent<HTMLInputElement>) => {
    if (readonly) return;
    
    const dateValue = parseDate(e.target.value);
    if (dateValue) {
      setInternalValue(dateValue);
      onChange?.(dateValue);
    } else if (e.target.value && e.target.value.trim() !== '') {
      onError?.('Invalid date format');
    }
    
    onBlur?.(e);
  };

  const handleInputKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'ArrowDown' && !isOpen) {
      setIsOpen(true);
    } else if (e.key === 'Escape' && isOpen) {
      setIsOpen(false);
    }
  };

  const handleDateSelect = (date: Date) => {
    if (mode === 'single') {
      setInternalValue(date);
      onChange?.(date);
      if (closeOnSelect) {
        setIsOpen(false);
      }
    }
  };

  const handleRangeSelect = (range: DateRange) => {
    setInternalValue(range);
    onRangeChange?.(range);
    if (closeOnSelect) {
      setIsOpen(false);
    }
  };

  const handleMultipleSelect = (dates: Date[]) => {
    setInternalValue(dates);
    onMultipleChange?.(dates);
  };

  const handleClear = () => {
    setInternalValue(null);
    setInputValue('');
    if (mode === 'single') {
      onChange?.(null);
    } else if (mode === 'range') {
      onRangeSelect?.(null);
    } else if (mode === 'multiple') {
      onMultipleChange?.([]);
    }
  };

  const renderInput = () => {
    if (customInput) {
      return React.cloneElement(customInput, {
        ref: inputRef,
        value: inputValue,
        placeholder,
        disabled,
        readOnly: readonly,
        onClick: handleInputClick,
        onChange: handleInputChange,
        onBlur: handleInputBlur,
        onKeyDown: handleInputKeyDown,
        onFocus,
        'data-testid': 'datepicker-input',
        ...inputProps
      });
    }

    return (
      <div className="relative">
        <input
          ref={inputRef}
          type="text"
          value={inputValue}
          placeholder={placeholder}
          disabled={disabled}
          readOnly={readonly}
          className={cn(
            'border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 transition-colors',
            sizeClasses[size],
            themeClasses[theme],
            error && 'error border-red-500',
            success && 'success border-green-500',
            warning && 'warning border-yellow-500',
            disabled && 'opacity-50 cursor-not-allowed',
            readonly && 'bg-gray-50'
          )}
          onClick={handleInputClick}
          onChange={handleInputChange}
          onBlur={handleInputBlur}
          onKeyDown={handleInputKeyDown}
          onFocus={onFocus}
          data-testid="datepicker-input"
          {...inputProps}
        />
        
        {showIcon && (
          <button
            type="button"
            onClick={handleInputClick}
            disabled={disabled}
            className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
            data-testid="datepicker-icon"
          >
            📅
          </button>
        )}
        
        {clearable && internalValue && (
          <button
            type="button"
            onClick={handleClear}
            className="absolute right-8 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
            data-testid="datepicker-clear"
          >
            ✕
          </button>
        )}
      </div>
    );
  };

  const renderCalendar = () => {
    if (customCalendar) {
      return customCalendar;
    }

    const calendarElement = (
      <div
        ref={calendarRef}
        className={cn(
          'absolute bg-white border rounded-lg shadow-lg z-50',
          `position-${calendarPosition}`,
          animated && 'animated',
          calendarPosition === 'bottom' && 'top-full mt-2',
          calendarPosition === 'top' && 'bottom-full mb-2',
          calendarPosition === 'left' && 'right-full mr-2',
          calendarPosition === 'right' && 'left-full ml-2'
        )}
        style={{ zIndex }}
        data-testid="datepicker-calendar"
        {...calendarProps}
      >
        <Calendar
          selectedDate={mode === 'single' ? (internalValue as Date) : undefined}
          selectedRange={mode === 'range' ? (internalValue as DateRange) : undefined}
          selectedDates={mode === 'multiple' ? (internalValue as Date[]) : undefined}
          mode={mode}
          theme={theme}
          minDate={minDate}
          maxDate={maxDate}
          disabledDates={disabledDates}
          isDateValid={isDateValid}
          showTime={showTime}
          onDateSelect={handleDateSelect}
          onRangeSelect={handleRangeSelect}
          onMultipleSelect={handleMultipleSelect}
          onTimeChange={(time) => {
            // Handle time change
            if (mode === 'single' && internalValue) {
              const newDate = new Date(internalValue as Date);
              newDate.setHours(time.hours, time.minutes);
              setInternalValue(newDate);
              onChange?.(newDate);
            }
          }}
        />
        {showTime && (
          <div data-testid="datepicker-time-picker" className="p-4 border-t">
            {/* Time picker would be rendered here */}
            <div className="text-sm text-gray-600">Time: 00:00</div>
          </div>
        )}
      </div>
    );

    if (portal && typeof window !== 'undefined') {
      return createPortal(calendarElement, document.body);
    }

    return calendarElement;
  };

  if (loading) {
    return (
      <div
        className={cn('flex items-center', className)}
        data-testid="datepicker-loading"
      >
        {loadingComponent || (
          <div className="flex items-center space-x-2">
            <div className="w-5 h-5 border-2 border-gray-300 border-t-blue-500 rounded-full animate-spin"></div>
            <span className="text-gray-500">Loading...</span>
          </div>
        )}
      </div>
    );
  }

  if (inline) {
    return (
      <div
        className={cn('inline-datepicker', className)}
        data-testid={dataTestId}
        data-category={dataCategory}
        data-id={dataId}
        {...props}
      >
        {label && (
          <label className="block text-sm font-medium text-gray-700 mb-2">
            {label}
            {required && <span className="text-red-500 ml-1">*</span>}
          </label>
        )}
        
        <div data-testid="datepicker-calendar">
          <Calendar
            selectedDate={mode === 'single' ? (internalValue as Date) : undefined}
            selectedRange={mode === 'range' ? (internalValue as DateRange) : undefined}
            selectedDates={mode === 'multiple' ? (internalValue as Date[]) : undefined}
            mode={mode}
            theme={theme}
            minDate={minDate}
            maxDate={maxDate}
            disabledDates={disabledDates}
            isDateValid={isDateValid}
            showTime={showTime}
            onDateSelect={handleDateSelect}
            onRangeSelect={handleRangeSelect}
            onMultipleSelect={handleMultipleSelect}
            {...calendarProps}
          />
        </div>
        
        {helperText && (
          <p className="mt-2 text-sm text-gray-600">{helperText}</p>
        )}
      </div>
    );
  }

  return (
    <div
      ref={containerRef}
      className={cn(
        'relative',
        `size-${size}`,
        `theme-${theme}`,
        className
      )}
      data-testid={dataTestId}
      data-category={dataCategory}
      data-id={dataId}
      {...props}
    >
      {label && (
        <label className="block text-sm font-medium text-gray-700 mb-2">
          {label}
          {required && <span className="text-red-500 ml-1">*</span>}
        </label>
      )}
      
      {renderInput()}
      
      {error && typeof error === 'string' && (
        <p className="mt-1 text-sm text-red-600">{error}</p>
      )}
      
      {helperText && !error && (
        <p className="mt-1 text-sm text-gray-600">{helperText}</p>
      )}
      
      {isOpen && renderCalendar()}
    </div>
  );
};

export default DatePicker;