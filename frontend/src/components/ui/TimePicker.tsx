<<<<<<< HEAD
import React, { useState, useRef, useEffect } from 'react';

interface TimePickerProps {
  value?: string;
  onChange?: (time: string) => void;
  format?: '12' | '24';
  placeholder?: string;
  disabled?: boolean;
  size?: 'sm' | 'md' | 'lg';
  minuteStep?: number;
=======
import React, { useState, useEffect, useRef, useCallback } from "react";
import { createPortal } from "react-dom";
import { cn } from "@/lib/utils";

export interface TimeValue {
  hours: number;
  minutes: number;
  seconds?: number;
}

export interface TimeRange {
  start: TimeValue;
  end: TimeValue;
}

export interface TimePickerProps {
  value?: TimeValue | TimeRange | null;
  defaultValue?: TimeValue | TimeRange | null;
  mode?: "single" | "range";
  format?: "12" | "24";
  placeholder?: string;
  size?: "sm" | "md" | "lg";
  theme?: "light" | "dark";
  disabled?: boolean;
  readonly?: boolean;
  required?: boolean;
  clearable?: boolean;
  showIcon?: boolean;
  showSeconds?: boolean;
  showNow?: boolean;
  inline?: boolean;
  portal?: boolean;
  animated?: boolean;
  closeOnSelect?: boolean;
  loading?: boolean;
  error?: string | boolean;
  success?: boolean;
  warning?: boolean;
  label?: string;
  helperText?: string;
  position?: "bottom" | "top" | "left" | "right";
  hourStep?: number;
  minuteStep?: number;
  secondStep?: number;
  minTime?: TimeValue;
  maxTime?: TimeValue;
  disabledTimes?: TimeValue[];
  customFormat?: (hours: number, minutes: number, seconds?: number) => string;
  loadingComponent?: React.ReactNode;
  customInput?: React.ReactElement;
  onChange?: (time: TimeValue | null) => void;
  onRangeChange?: (range: TimeRange | null) => void;
  onFocus?: (e: React.FocusEvent<HTMLInputElement>) => void;
  onBlur?: (e: React.FocusEvent<HTMLInputElement>) => void;
  onError?: (error: string) => void;
  className?: string;
  "data-testid"?: string;
  "data-category"?: string;
  "data-id"?: string;
>>>>>>> origin/main
}

export const TimePicker: React.FC<TimePickerProps> = ({
  value,
<<<<<<< HEAD
  onChange,
  format = '24',
  placeholder = '時刻を選択',
  disabled = false,
  size = 'md',
  minuteStep = 15
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [selectedTime, setSelectedTime] = useState<string>(value || '');
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
  format = "24",
  placeholder = "Select time",
  size = "md",
  theme = "light",
  disabled = false,
  readonly = false,
  required = false,
  clearable = false,
  showIcon = true,
  showSeconds = false,
  showNow = false,
  inline = false,
  portal = false,
  animated = false,
  closeOnSelect = true,
  loading = false,
  error,
  success = false,
  warning = false,
  label,
  helperText,
  position = "bottom",
  hourStep = 1,
  minuteStep = 1,
  secondStep = 1,
  minTime,
  maxTime,
  disabledTimes = [],
  customFormat,
  loadingComponent,
  customInput,
  onChange,
  onRangeChange,
  onFocus,
  onBlur,
  onError,
  className,
  "data-testid": dataTestId = "timepicker-container",
  "data-category": dataCategory,
  "data-id": dataId,
  ...props
}) => {
  const [isOpen, setIsOpen] = useState(inline);
  const [internalValue, setInternalValue] = useState<
    TimeValue | TimeRange | null
  >(value || defaultValue || null);
  const [inputValue, setInputValue] = useState("");
  const [rangeStart, setRangeStart] = useState<TimeValue | null>(null);

  const containerRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const dropdownRef = useRef<HTMLDivElement>(null);

  const sizeClasses = {
    sm: "size-sm text-sm px-3 py-1.5",
    md: "size-md text-base px-4 py-2",
    lg: "size-lg text-lg px-5 py-3",
  };

  const themeClasses = {
    light: "theme-light bg-white border-gray-300 text-gray-900",
    dark: "theme-dark bg-gray-800 border-gray-600 text-white",
  };

  // Format time for display
  const formatTime = useCallback(
    (time: TimeValue | null): string => {
      if (!time) return "";

      if (customFormat) {
        return customFormat(time.hours, time.minutes, time.seconds);
      }

      let hours = time.hours;
      let ampm = "";

      if (format === "12") {
        ampm = hours >= 12 ? "PM" : "AM";
        hours = hours === 0 ? 12 : hours > 12 ? hours - 12 : hours;
      }

      const h =
        format === "12" ? hours.toString() : hours.toString().padStart(2, "0");
      const m = time.minutes.toString().padStart(2, "0");
      const s =
        showSeconds && time.seconds
          ? time.seconds.toString().padStart(2, "0")
          : "";

      let timeStr = `${h}:${m}`;
      if (showSeconds && s) {
        timeStr += `:${s}`;
      }
      if (format === "12") {
        timeStr += ` ${ampm}`;
      }

      return timeStr;
    },
    [format, showSeconds, customFormat],
  );

  // Parse time from string
  const parseTime = (timeStr: string): TimeValue | null => {
    if (!timeStr) return null;

    const timeRegex = showSeconds
      ? /^(\d{1,2}):(\d{2}):(\d{2})(\s*(AM|PM))?$/i
      : /^(\d{1,2}):(\d{2})(\s*(AM|PM))?$/i;

    const match = timeStr.match(timeRegex);
    if (!match) return null;

    let hours = parseInt(match[1], 10);
    const minutes = parseInt(match[2], 10);
    const seconds = showSeconds ? parseInt(match[3] || "0", 10) : 0;
    const ampm = match[showSeconds ? 5 : 4];

    if (minutes > 59 || (showSeconds && seconds > 59)) return null;

    if (format === "12") {
      if (hours > 12 || hours < 1) return null;
      if (ampm?.toUpperCase() === "PM" && hours !== 12) {
        hours += 12;
      } else if (ampm?.toUpperCase() === "AM" && hours === 12) {
        hours = 0;
      }
    } else {
      if (hours > 23) return null;
    }

    return { hours, minutes, seconds: showSeconds ? seconds : undefined };
  };

  // Update input value when internal value changes
  useEffect(() => {
    if (mode === "single") {
      const singleValue = internalValue as TimeValue | null;
      setInputValue(singleValue ? formatTime(singleValue) : "");
    } else if (mode === "range") {
      const rangeValue = internalValue as TimeRange | null;
      if (rangeValue?.start && rangeValue?.end) {
        setInputValue(
          `${formatTime(rangeValue.start)} - ${formatTime(rangeValue.end)}`,
        );
      } else {
        setInputValue("");
      }
    }
  }, [internalValue, formatTime, mode]);

  // Close dropdown on outside click
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

  const generateTimeOptions = () => {
    const options = [];
    const totalMinutes = 24 * 60;
    
    for (let i = 0; i < totalMinutes; i += minuteStep) {
      const hours = Math.floor(i / 60);
      const minutes = i % 60;
      
      let timeString;
      if (format === '12') {
        const displayHours = hours === 0 ? 12 : hours > 12 ? hours - 12 : hours;
        const ampm = hours < 12 ? 'AM' : 'PM';
        timeString = `${displayHours}:${minutes.toString().padStart(2, '0')} ${ampm}`;
      } else {
        timeString = `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}`;
      }
      
      options.push({
        value: `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}`,
        display: timeString
      });
    }
    
    return options;
  };

  const formatDisplayTime = (time: string) => {
    if (!time) return '';
    
    const [hours, minutes] = time.split(':').map(Number);
    
    if (format === '12') {
      const displayHours = hours === 0 ? 12 : hours > 12 ? hours - 12 : hours;
      const ampm = hours < 12 ? 'AM' : 'PM';
      return `${displayHours}:${minutes.toString().padStart(2, '0')} ${ampm}`;
    }
    
    return time;
  };

  const handleTimeSelect = (time: string) => {
    setSelectedTime(time);
    onChange?.(time);
    setIsOpen(false);
  };

  const handleNowSelect = () => {
    const now = new Date();
    const hours = now.getHours().toString().padStart(2, '0');
    const minutes = Math.floor(now.getMinutes() / minuteStep) * minuteStep;
    const timeString = `${hours}:${minutes.toString().padStart(2, '0')}`;
    
    handleTimeSelect(timeString);
  };

  const timeOptions = generateTimeOptions();
  const displayValue = formatDisplayTime(selectedTime);

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
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        </div>
      </div>

      {isOpen && (
        <div className="absolute top-full left-0 mt-1 bg-white border border-gray-200 rounded-lg shadow-lg z-10 w-full">
          <div className="p-2 border-b border-gray-100">
            <button
              onClick={handleNowSelect}
              className="w-full text-sm text-blue-600 hover:text-blue-800 py-2 px-3 hover:bg-blue-50 rounded"
              type="button"
            >
              現在の時刻を選択
            </button>
          </div>
          
          <div className="max-h-60 overflow-y-auto">
            {timeOptions.map((option) => (
              <button
                key={option.value}
                onClick={() => handleTimeSelect(option.value)}
                className={`
                  w-full text-left px-3 py-2 text-sm hover:bg-gray-50 transition-colors
                  ${selectedTime === option.value ? 'bg-blue-100 text-blue-700' : ''}
                `}
                type="button"
              >
                {option.display}
              </button>
            ))}
          </div>
        </div>
      )}
=======
    if (isOpen) {
      document.addEventListener("mousedown", handleClickOutside);
      return () =>
        document.removeEventListener("mousedown", handleClickOutside);
    }
  }, [isOpen, inline]);

  const isTimeDisabled = (time: TimeValue): boolean => {
    if (
      minTime &&
      (time.hours < minTime.hours ||
        (time.hours === minTime.hours && time.minutes < minTime.minutes))
    ) {
      return true;
    }
    if (
      maxTime &&
      (time.hours > maxTime.hours ||
        (time.hours === maxTime.hours && time.minutes > maxTime.minutes))
    ) {
      return true;
    }
    return disabledTimes.some(
      (dt) => dt.hours === time.hours && dt.minutes === time.minutes,
    );
  };

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

    const timeValue = parseTime(e.target.value);
    if (timeValue) {
      setInternalValue(timeValue);
      onChange?.(timeValue);
    } else if (e.target.value && e.target.value.trim() !== "") {
      onError?.("Invalid time format");
    }

    onBlur?.(e);
  };

  const handleInputKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "ArrowDown" && !isOpen) {
      setIsOpen(true);
    } else if (e.key === "Escape" && isOpen) {
      setIsOpen(false);
    } else if (e.key === "ArrowUp" || e.key === "ArrowDown") {
      e.preventDefault();
      const currentTime = internalValue as TimeValue | null;
      if (currentTime) {
        const newHours =
          e.key === "ArrowUp"
            ? Math.min(23, currentTime.hours + 1)
            : Math.max(0, currentTime.hours - 1);
        const newTime = { ...currentTime, hours: newHours };
        setInternalValue(newTime);
        onChange?.(newTime);
      }
    }
  };

  const handleTimeSelect = (time: TimeValue) => {
    if (mode === "single") {
      setInternalValue(time);
      onChange?.(time);
      if (closeOnSelect) {
        setIsOpen(false);
      }
    } else if (mode === "range") {
      if (!rangeStart) {
        setRangeStart(time);
      } else {
        const range: TimeRange = {
          start: rangeStart,
          end: time,
        };
        if (
          time.hours < rangeStart.hours ||
          (time.hours === rangeStart.hours && time.minutes < rangeStart.minutes)
        ) {
          range.start = time;
          range.end = rangeStart;
        }
        setInternalValue(range);
        onRangeChange?.(range);
        setRangeStart(null);
        if (closeOnSelect) {
          setIsOpen(false);
        }
      }
    }
  };

  const handleClear = () => {
    setInternalValue(null);
    setInputValue("");
    setRangeStart(null);
    if (mode === "single") {
      onChange?.(null);
    } else if (mode === "range") {
      onRangeChange?.(null);
    }
  };

  const handleNow = () => {
    const now = new Date();
    const currentTime: TimeValue = {
      hours: now.getHours(),
      minutes: now.getMinutes(),
      seconds: showSeconds ? now.getSeconds() : undefined,
    };
    setInternalValue(currentTime);
    onChange?.(currentTime);
  };

  const generateHours = () => {
    const hours: number[] = [];
    const maxHour = format === "12" ? 12 : 23;
    const minHour = format === "12" ? 1 : 0;

    for (let i = minHour; i <= maxHour; i += hourStep) {
      hours.push(i);
    }
    return hours;
  };

  const generateMinutes = () => {
    const minutes: number[] = [];
    for (let i = 0; i < 60; i += minuteStep) {
      minutes.push(i);
    }
    return minutes;
  };

  const generateSeconds = () => {
    const seconds: number[] = [];
    for (let i = 0; i < 60; i += secondStep) {
      seconds.push(i);
    }
    return seconds;
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
        "data-testid": "timepicker-input",
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
          data-testid="timepicker-input"
        />

        {showIcon && (
          <button
            type="button"
            onClick={handleInputClick}
            disabled={disabled}
            className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
            data-testid="timepicker-icon"
          >
            🕐
          </button>
        )}

        {clearable && internalValue && (
          <button
            type="button"
            onClick={handleClear}
            className="absolute right-8 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
            data-testid="timepicker-clear"
          >
            ✕
          </button>
        )}
      </div>
    );
  };

  const renderTimePicker = () => {
    const hours = generateHours();
    const minutes = generateMinutes();
    const seconds = showSeconds ? generateSeconds() : [];

    const currentTime = mode === "single" ? (internalValue as TimeValue) : null;

    const dropdownElement = (
      <div
        ref={dropdownRef}
        className={cn(
          "absolute bg-white border rounded-lg shadow-lg z-50 p-4",
          `position-${position}`,
          animated && "animated",
          position === "bottom" && "top-full mt-2",
          position === "top" && "bottom-full mb-2",
          position === "left" && "right-full mr-2",
          position === "right" && "left-full ml-2",
        )}
        data-testid="timepicker-dropdown"
      >
        <div className="flex space-x-4">
          {/* Hours */}
          <div className="flex flex-col">
            <div className="text-xs font-medium text-gray-500 mb-2">Hours</div>
            <div className="max-h-32 overflow-y-auto space-y-1">
              {hours.map((hour) => {
                const timeValue: TimeValue = { hours: hour, minutes: 0 };
                const isDisabled = isTimeDisabled(timeValue);
                return (
                  <button
                    key={hour}
                    onClick={() =>
                      !isDisabled &&
                      handleTimeSelect({
                        hours: hour,
                        minutes: currentTime?.minutes || 0,
                      })
                    }
                    disabled={isDisabled}
                    className={cn(
                      "w-12 h-8 text-sm rounded hover:bg-blue-100 transition-colors",
                      currentTime?.hours === hour && "bg-blue-500 text-white",
                      isDisabled && "opacity-50 cursor-not-allowed",
                    )}
                  >
                    {hour.toString().padStart(2, "0")}
                  </button>
                );
              })}
            </div>
          </div>

          {/* Minutes */}
          <div className="flex flex-col">
            <div className="text-xs font-medium text-gray-500 mb-2">
              Minutes
            </div>
            <div className="max-h-32 overflow-y-auto space-y-1">
              {minutes.map((minute) => {
                const timeValue: TimeValue = {
                  hours: currentTime?.hours || 0,
                  minutes: minute,
                };
                const isDisabled = isTimeDisabled(timeValue);
                return (
                  <button
                    key={minute}
                    onClick={() =>
                      !isDisabled &&
                      handleTimeSelect({
                        hours: currentTime?.hours || 0,
                        minutes: minute,
                      })
                    }
                    disabled={isDisabled}
                    className={cn(
                      "w-12 h-8 text-sm rounded hover:bg-blue-100 transition-colors",
                      currentTime?.minutes === minute &&
                        "bg-blue-500 text-white",
                      isDisabled && "opacity-50 cursor-not-allowed",
                    )}
                  >
                    {minute.toString().padStart(2, "0")}
                  </button>
                );
              })}
            </div>
          </div>

          {/* Seconds */}
          {showSeconds && (
            <div className="flex flex-col" data-testid="timepicker-seconds">
              <div className="text-xs font-medium text-gray-500 mb-2">
                Seconds
              </div>
              <div className="max-h-32 overflow-y-auto space-y-1">
                {seconds.map((second) => (
                  <button
                    key={second}
                    onClick={() =>
                      handleTimeSelect({
                        hours: currentTime?.hours || 0,
                        minutes: currentTime?.minutes || 0,
                        seconds: second,
                      })
                    }
                    className={cn(
                      "w-12 h-8 text-sm rounded hover:bg-blue-100 transition-colors",
                      currentTime?.seconds === second &&
                        "bg-blue-500 text-white",
                    )}
                  >
                    {second.toString().padStart(2, "0")}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* AM/PM */}
          {format === "12" && (
            <div className="flex flex-col" data-testid="timepicker-ampm">
              <div className="text-xs font-medium text-gray-500 mb-2">
                AM/PM
              </div>
              <div className="space-y-1">
                <button
                  onClick={() => {
                    const hours = currentTime?.hours || 0;
                    const newHours = hours >= 12 ? hours - 12 : hours;
                    handleTimeSelect({
                      ...currentTime,
                      hours: newHours,
                    } as TimeValue);
                  }}
                  className={cn(
                    "w-12 h-8 text-sm rounded hover:bg-blue-100 transition-colors",
                    currentTime &&
                      currentTime.hours < 12 &&
                      "bg-blue-500 text-white",
                  )}
                >
                  AM
                </button>
                <button
                  onClick={() => {
                    const hours = currentTime?.hours || 0;
                    const newHours = hours < 12 ? hours + 12 : hours;
                    handleTimeSelect({
                      ...currentTime,
                      hours: newHours,
                    } as TimeValue);
                  }}
                  className={cn(
                    "w-12 h-8 text-sm rounded hover:bg-blue-100 transition-colors",
                    currentTime &&
                      currentTime.hours >= 12 &&
                      "bg-blue-500 text-white",
                  )}
                >
                  PM
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Now button */}
        {showNow && (
          <div className="mt-4 pt-4 border-t">
            <button
              onClick={handleNow}
              className="w-full px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 transition-colors"
              data-testid="timepicker-now"
            >
              Now
            </button>
          </div>
        )}
      </div>
    );

    if (portal && typeof window !== "undefined") {
      return createPortal(dropdownElement, document.body);
    }

    return dropdownElement;
  };

  if (loading) {
    return (
      <div
        className={cn("flex items-center", className)}
        data-testid="timepicker-loading"
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
        className={cn("inline-timepicker", className)}
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

        {renderTimePicker()}

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

      {isOpen && renderTimePicker()}
>>>>>>> origin/main
    </div>
  );
};

<<<<<<< HEAD
export default TimePicker;
=======
export default TimePicker;
>>>>>>> origin/main
