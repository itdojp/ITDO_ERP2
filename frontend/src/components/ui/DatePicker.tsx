<<<<<<< HEAD
import React, { useState, useRef, useEffect } from 'react';

interface DatePickerProps {
  value?: string;
  onChange?: (date: string) => void;
  placeholder?: string;
  disabled?: boolean;
  minDate?: string;
  maxDate?: string;
  format?: 'YYYY-MM-DD' | 'MM/DD/YYYY' | 'DD/MM/YYYY';
  showToday?: boolean;
  size?: 'sm' | 'md' | 'lg';
=======
import React, { useState, useEffect, useRef, useCallback } from "react";
import { createPortal } from "react-dom";
import { cn } from "@/lib/utils";
import { Calendar } from "./Calendar";

export interface DateRange {
  start: Date;
  end: Date;
}

export interface DatePickerProps {
  value?: Date | Date[] | DateRange | null;
  defaultValue?: Date | Date[] | DateRange | null;
  mode?: "single" | "multiple" | "range";
  format?: string;
  placeholder?: string;
  size?: "sm" | "md" | "lg";
  theme?: "light" | "dark";
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
  position?: "bottom" | "top" | "left" | "right";
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
  "data-testid"?: string;
  "data-category"?: string;
  "data-id"?: string;
>>>>>>> origin/main
}

export const DatePicker: React.FC<DatePickerProps> = ({
  value,
<<<<<<< HEAD
  onChange,
  placeholder = '日付を選択',
  disabled = false,
  minDate,
  maxDate,
  format = 'YYYY-MM-DD',
  showToday = true,
  size = 'md'
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [currentMonth, setCurrentMonth] = useState(new Date());
  const [selectedDate, setSelectedDate] = useState<string | null>(value || null);
  const containerRef = useRef<HTMLDivElement>(null);

  const sizeClasses = {
    sm: 'h-8 text-sm px-3',
    md: 'h-10 text-base px-4',
    lg: 'h-12 text-lg px-5'
  };

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
=======
  defaultValue,
  mode = "single",
  format = "MM/dd/yyyy",
  placeholder = "Select date",
  size = "md",
  theme = "light",
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
  position = "bottom",
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
  "data-testid": dataTestId = "datepicker-container",
  "data-category": dataCategory,
  "data-id": dataId,
  ...props
}) => {
  const [isOpen, setIsOpen] = useState(inline);
  const [internalValue, setInternalValue] = useState(value || defaultValue);
  const [inputValue, setInputValue] = useState("");
  const [calendarPosition, setCalendarPosition] = useState(position);

  const containerRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const calendarRef = useRef<HTMLDivElement>(null);

  const sizeClasses = {
    sm: "size-sm text-sm px-3 py-1.5",
    md: "size-md text-base px-4 py-2",
    lg: "size-lg text-lg px-5 py-3",
  };

  const themeClasses = {
    light: "theme-light bg-white border-gray-300 text-gray-900",
    dark: "theme-dark bg-gray-800 border-gray-600 text-white",
  };

  // Format date for display
  const formatDate = useCallback(
    (date: Date | null) => {
      if (!date) return "";

      if (showTime) {
        const timeStr = date.toLocaleTimeString("en-US", {
          hour12: false,
          hour: "2-digit",
          minute: "2-digit",
        });
        return `${formatDateOnly(date)} ${timeStr}`;
      }

      return formatDateOnly(date);
    },
    [showTime, format],
  );

  const formatDateOnly = (date: Date) => {
    const day = date.getDate().toString().padStart(2, "0");
    const month = (date.getMonth() + 1).toString().padStart(2, "0");
    const year = date.getFullYear().toString();

    switch (format) {
      case "MM-dd-yyyy":
        return `${month}-${day}-${year}`;
      case "dd/MM/yyyy":
        return `${day}/${month}/${year}`;
      case "yyyy-MM-dd":
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
      case "MM-dd-yyyy":
      case "MM/dd/yyyy":
        [month, day, year] = parts.map(Number);
        break;
      case "dd/MM/yyyy":
        [day, month, year] = parts.map(Number);
        break;
      case "yyyy-MM-dd":
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
    if (mode === "single") {
      const singleValue = internalValue as Date | null;
      setInputValue(singleValue ? formatDate(singleValue) : "");
    } else if (mode === "range") {
      const rangeValue = internalValue as DateRange | null;
      if (rangeValue?.start && rangeValue?.end) {
        setInputValue(
          `${formatDate(rangeValue.start)} - ${formatDate(rangeValue.end)}`,
        );
      } else {
        setInputValue("");
      }
    } else if (mode === "multiple") {
      const multipleValue = internalValue as Date[] | null;
      if (multipleValue && multipleValue.length > 0) {
        setInputValue(multipleValue.map((date) => formatDate(date)).join(", "));
      } else {
        setInputValue("");
      }
    }
  }, [internalValue, formatDate, mode]);

  // Close calendar on outside click
  useEffect(() => {
    if (inline) return;

    const handleClickOutside = (event: MouseEvent) => {
      if (
        containerRef.current &&
        !containerRef.current.contains(event.target as Node)
      ) {
>>>>>>> origin/main
        setIsOpen(false);
      }
    };

<<<<<<< HEAD
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const formatDate = (dateString: string, formatType: string): string => {
    const date = new Date(dateString);
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');

    switch (formatType) {
      case 'MM/DD/YYYY':
        return `${month}/${day}/${year}`;
      case 'DD/MM/YYYY':
        return `${day}/${month}/${year}`;
      default:
        return `${year}-${month}-${day}`;
    }
  };

  const parseDate = (dateString: string): string => {
    // Always return YYYY-MM-DD format for internal use
    if (!dateString) return '';
    
    const date = new Date(dateString);
    if (isNaN(date.getTime())) return '';
    
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    
    return `${year}-${month}-${day}`;
  };

  const getDaysInMonth = (date: Date): number => {
    return new Date(date.getFullYear(), date.getMonth() + 1, 0).getDate();
  };

  const getFirstDayOfMonth = (date: Date): number => {
    return new Date(date.getFullYear(), date.getMonth(), 1).getDay();
  };

  const isDateDisabled = (dateString: string): boolean => {
    if (!dateString) return false;
    
    const date = new Date(dateString);
    if (minDate && date < new Date(minDate)) return true;
    if (maxDate && date > new Date(maxDate)) return true;
    
    return false;
  };

  const handleDateSelect = (day: number) => {
    const year = currentMonth.getFullYear();
    const month = currentMonth.getMonth();
    const dateString = `${year}-${String(month + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
    
    if (isDateDisabled(dateString)) return;
    
    setSelectedDate(dateString);
    onChange?.(dateString);
    setIsOpen(false);
  };

  const handleTodaySelect = () => {
    const today = new Date().toISOString().split('T')[0];
    if (isDateDisabled(today)) return;
    
    setSelectedDate(today);
    onChange?.(today);
    setIsOpen(false);
  };

  const navigateMonth = (direction: 'prev' | 'next') => {
    setCurrentMonth(prev => {
      const newMonth = new Date(prev);
      if (direction === 'prev') {
        newMonth.setMonth(newMonth.getMonth() - 1);
      } else {
        newMonth.setMonth(newMonth.getMonth() + 1);
      }
      return newMonth;
    });
  };

  const renderCalendar = () => {
    const daysInMonth = getDaysInMonth(currentMonth);
    const firstDay = getFirstDayOfMonth(currentMonth);
    const days = [];
    const monthNames = [
      '1月', '2月', '3月', '4月', '5月', '6月',
      '7月', '8月', '9月', '10月', '11月', '12月'
    ];

    // Empty cells for days before the first day of the month
    for (let i = 0; i < firstDay; i++) {
      days.push(<div key={`empty-${i}`} className="w-8 h-8" />);
    }

    // Days of the month
    for (let day = 1; day <= daysInMonth; day++) {
      const dateString = `${currentMonth.getFullYear()}-${String(currentMonth.getMonth() + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
      const isSelected = selectedDate === dateString;
      const isToday = dateString === new Date().toISOString().split('T')[0];
      const isDisabled = isDateDisabled(dateString);

      days.push(
        <button
          key={day}
          onClick={() => handleDateSelect(day)}
          disabled={isDisabled}
          className={`
            w-8 h-8 text-sm rounded hover:bg-blue-50 transition-colors
            ${isSelected ? 'bg-blue-600 text-white hover:bg-blue-700' : ''}
            ${isToday && !isSelected ? 'bg-blue-100 text-blue-600' : ''}
            ${isDisabled ? 'text-gray-300 cursor-not-allowed hover:bg-transparent' : ''}
          `}
        >
          {day}
        </button>
      );
    }

    return (
      <div className="absolute top-full left-0 mt-1 bg-white border border-gray-200 rounded-lg shadow-lg z-10 p-4">
        <div className="flex items-center justify-between mb-4">
          <button
            onClick={() => navigateMonth('prev')}
            className="p-1 hover:bg-gray-100 rounded"
            type="button"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
          </button>
          <span className="font-medium">
            {currentMonth.getFullYear()}年 {monthNames[currentMonth.getMonth()]}
          </span>
          <button
            onClick={() => navigateMonth('next')}
            className="p-1 hover:bg-gray-100 rounded"
            type="button"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
            </svg>
          </button>
        </div>

        <div className="grid grid-cols-7 gap-1 mb-2">
          {['日', '月', '火', '水', '木', '金', '土'].map(day => (
            <div key={day} className="w-8 h-8 text-xs text-gray-500 flex items-center justify-center">
              {day}
            </div>
          ))}
        </div>

        <div className="grid grid-cols-7 gap-1 mb-4">
          {days}
        </div>

        {showToday && (
          <div className="border-t border-gray-100 pt-2">
            <button
              onClick={handleTodaySelect}
              disabled={isDateDisabled(new Date().toISOString().split('T')[0])}
              className="w-full text-sm text-blue-600 hover:text-blue-800 disabled:text-gray-400 disabled:cursor-not-allowed"
              type="button"
            >
              今日を選択
            </button>
          </div>
=======
    if (isOpen) {
      document.addEventListener("mousedown", handleClickOutside);
      return () =>
        document.removeEventListener("mousedown", handleClickOutside);
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
      if (
        position === "bottom" &&
        inputRect.bottom + calendarRect.height > viewportHeight
      ) {
        newPosition = "top";
      }
      // Check if calendar fits above input
      else if (position === "top" && inputRect.top - calendarRect.height < 0) {
        newPosition = "bottom";
      }

      setCalendarPosition(newPosition);
    };

    updatePosition();
    window.addEventListener("scroll", updatePosition);
    window.addEventListener("resize", updatePosition);

    return () => {
      window.removeEventListener("scroll", updatePosition);
      window.removeEventListener("resize", updatePosition);
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
    } else if (e.target.value && e.target.value.trim() !== "") {
      onError?.("Invalid date format");
    }

    onBlur?.(e);
  };

  const handleInputKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "ArrowDown" && !isOpen) {
      setIsOpen(true);
    } else if (e.key === "Escape" && isOpen) {
      setIsOpen(false);
    }
  };

  const handleDateSelect = (date: Date) => {
    if (mode === "single") {
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
    setInputValue("");
    if (mode === "single") {
      onChange?.(null);
    } else if (mode === "range") {
      onRangeSelect?.(null);
    } else if (mode === "multiple") {
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
        "data-testid": "datepicker-input",
        ...inputProps,
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
            "border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 transition-colors",
            sizeClasses[size],
            themeClasses[theme],
            error && "error border-red-500",
            success && "success border-green-500",
            warning && "warning border-yellow-500",
            disabled && "opacity-50 cursor-not-allowed",
            readonly && "bg-gray-50",
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
>>>>>>> origin/main
        )}
      </div>
    );
  };

<<<<<<< HEAD
  const displayValue = selectedDate ? formatDate(selectedDate, format) : '';

  return (
    <div className="relative inline-block w-full max-w-xs" ref={containerRef}>
      <div className="relative">
        <input
          type="text"
          value={displayValue}
          placeholder={placeholder}
          disabled={disabled}
          readOnly
          onClick={() => !disabled && setIsOpen(!isOpen)}
          className={`
            w-full pr-10 rounded-lg border border-gray-300 cursor-pointer
            focus:ring-2 focus:ring-blue-500 focus:border-blue-500 
            disabled:bg-gray-50 disabled:text-gray-500 disabled:cursor-not-allowed
            ${sizeClasses[size]}
          `}
        />
        <div className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 pointer-events-none">
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
          </svg>
        </div>
      </div>
=======
  const renderCalendar = () => {
    if (customCalendar) {
      return customCalendar;
    }

    const calendarElement = (
      <div
        ref={calendarRef}
        className={cn(
          "absolute bg-white border rounded-lg shadow-lg z-50",
          `position-${calendarPosition}`,
          animated && "animated",
          calendarPosition === "bottom" && "top-full mt-2",
          calendarPosition === "top" && "bottom-full mb-2",
          calendarPosition === "left" && "right-full mr-2",
          calendarPosition === "right" && "left-full ml-2",
        )}
        style={{ zIndex }}
        data-testid="datepicker-calendar"
        {...calendarProps}
      >
        <Calendar
          selectedDate={mode === "single" ? (internalValue as Date) : undefined}
          selectedRange={
            mode === "range" ? (internalValue as DateRange) : undefined
          }
          selectedDates={
            mode === "multiple" ? (internalValue as Date[]) : undefined
          }
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
            if (mode === "single" && internalValue) {
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

    if (portal && typeof window !== "undefined") {
      return createPortal(calendarElement, document.body);
    }

    return calendarElement;
  };

  if (loading) {
    return (
      <div
        className={cn("flex items-center", className)}
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
        className={cn("inline-datepicker", className)}
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
            selectedDate={
              mode === "single" ? (internalValue as Date) : undefined
            }
            selectedRange={
              mode === "range" ? (internalValue as DateRange) : undefined
            }
            selectedDates={
              mode === "multiple" ? (internalValue as Date[]) : undefined
            }
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
      className={cn("relative", `size-${size}`, `theme-${theme}`, className)}
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

      {error && typeof error === "string" && (
        <p className="mt-1 text-sm text-red-600">{error}</p>
      )}

      {helperText && !error && (
        <p className="mt-1 text-sm text-gray-600">{helperText}</p>
      )}
>>>>>>> origin/main

      {isOpen && renderCalendar()}
    </div>
  );
};

<<<<<<< HEAD
export default DatePicker;
=======
export default DatePicker;
>>>>>>> origin/main
