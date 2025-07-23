import React, { useState, useEffect, useRef, useCallback } from 'react';
import { cn } from '@/lib/utils';

export interface CalendarEvent {
  id: string;
  date: Date;
  title: string;
  color?: string;
  description?: string;
}

export interface DateRange {
  start: Date;
  end: Date;
}

export interface HighlightedDate {
  date: Date;
  className?: string;
  style?: React.CSSProperties;
}

export interface CalendarProps {
  selectedDate?: Date;
  selectedDates?: Date[];
  selectedRange?: DateRange;
  defaultDate?: Date;
  minDate?: Date;
  maxDate?: Date;
  disabledDates?: Date[];
  highlightedDates?: HighlightedDate[];
  events?: CalendarEvent[];
  mode?: 'single' | 'multiple' | 'range';
  view?: 'month' | 'year' | 'decade';
  size?: 'sm' | 'md' | 'lg';
  theme?: 'light' | 'dark';
  locale?: string;
  weekStartsOn?: 0 | 1 | 2 | 3 | 4 | 5 | 6;
  dateFormat?: string;
  showWeekNumbers?: boolean;
  showToday?: boolean;
  showTime?: boolean;
  showInput?: boolean;
  showMonthYearDropdown?: boolean;
  keyboardNavigation?: boolean;
  compact?: boolean;
  inline?: boolean;
  popup?: boolean;
  animated?: boolean;
  focusable?: boolean;
  readonly?: boolean;
  disabled?: boolean;
  loading?: boolean;
  loadingComponent?: React.ReactNode;
  isDateValid?: (date: Date) => boolean;
  renderDay?: (date: Date) => React.ReactNode;
  renderHeader?: (date: Date) => React.ReactNode;
  renderDateCell?: (date: Date, isSelected: boolean) => React.ReactNode;
  onDateSelect?: (date: Date) => void;
  onMultipleSelect?: (dates: Date[]) => void;
  onRangeSelect?: (range: DateRange) => void;
  onMonthChange?: (date: Date) => void;
  onYearChange?: (year: number) => void;
  onTimeChange?: (time: { hours: number; minutes: number }) => void;
  onEventClick?: (event: CalendarEvent) => void;
  className?: string;
  'data-testid'?: string;
  'data-category'?: string;
  'data-id'?: string;
}

export const Calendar: React.FC<CalendarProps> = ({
  selectedDate,
  selectedDates = [],
  selectedRange,
  defaultDate = new Date(),
  minDate,
  maxDate,
  disabledDates = [],
  highlightedDates = [],
  events = [],
  mode = 'single',
  view = 'month',
  size = 'md',
  theme = 'light',
  locale = 'en-US',
  weekStartsOn = 0,
  dateFormat = 'MM/dd/yyyy',
  showWeekNumbers = false,
  showToday = false,
  showTime = false,
  showInput = false,
  showMonthYearDropdown = false,
  keyboardNavigation = false,
  compact = false,
  inline = true,
  popup = false,
  animated = false,
  focusable = false,
  readonly = false,
  disabled = false,
  loading = false,
  loadingComponent,
  isDateValid,
  renderDay,
  renderHeader,
  renderDateCell,
  onDateSelect,
  onMultipleSelect,
  onRangeSelect,
  onMonthChange,
  onYearChange,
  onTimeChange,
  onEventClick,
  className,
  'data-testid': dataTestId = 'calendar-container',
  'data-category': dataCategory,
  'data-id': dataId,
  ...props
}) => {
  const [currentDate, setCurrentDate] = useState(defaultDate);
  const [currentView, setCurrentView] = useState(view);
  const [isPopupOpen, setIsPopupOpen] = useState(!popup);
  const [internalSelectedDates, setInternalSelectedDates] = useState<Date[]>(selectedDates);
  const [rangeStart, setRangeStart] = useState<Date | null>(selectedRange?.start || null);
  const [rangeEnd, setRangeEnd] = useState<Date | null>(selectedRange?.end || null);
  const [focusedDate, setFocusedDate] = useState<Date>(selectedDate || defaultDate);

  const calendarRef = useRef<HTMLDivElement>(null);
  const popupRef = useRef<HTMLDivElement>(null);

  const sizeClasses = {
    sm: 'text-sm p-2',
    md: 'text-base p-4',
    lg: 'text-lg p-6'
  };

  const themeClasses = {
    light: 'bg-white border-gray-200 text-gray-900',
    dark: 'bg-gray-900 border-gray-700 text-white'
  };

  // Close popup on outside click
  useEffect(() => {
    if (!popup) return;

    const handleClickOutside = (event: MouseEvent) => {
      if (popupRef.current && !popupRef.current.contains(event.target as Node)) {
        setIsPopupOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [popup]);

  // Keyboard navigation
  useEffect(() => {
    if (!keyboardNavigation) return;

    const handleKeyDown = (event: KeyboardEvent) => {
      if (!isPopupOpen) return;

      const newDate = new Date(focusedDate);
      
      switch (event.key) {
        case 'ArrowLeft':
          event.preventDefault();
          newDate.setDate(newDate.getDate() - 1);
          setFocusedDate(newDate);
          break;
        case 'ArrowRight':
          event.preventDefault();
          newDate.setDate(newDate.getDate() + 1);
          setFocusedDate(newDate);
          break;
        case 'ArrowUp':
          event.preventDefault();
          newDate.setDate(newDate.getDate() - 7);
          setFocusedDate(newDate);
          break;
        case 'ArrowDown':
          event.preventDefault();
          newDate.setDate(newDate.getDate() + 7);
          setFocusedDate(newDate);
          break;
        case 'Enter':
        case ' ':
          event.preventDefault();
          handleDateSelect(focusedDate);
          break;
        case 'Escape':
          if (popup) setIsPopupOpen(false);
          break;
      }
    };

    if (calendarRef.current) {
      calendarRef.current.addEventListener('keydown', handleKeyDown);
      return () => calendarRef.current?.removeEventListener('keydown', handleKeyDown);
    }
  }, [keyboardNavigation, focusedDate, isPopupOpen, popup]);

  const isDateDisabled = useCallback((date: Date) => {
    if (disabled) return true;
    if (minDate && date < minDate) return true;
    if (maxDate && date > maxDate) return true;
    if (disabledDates.some(d => isSameDay(d, date))) return true;
    if (isDateValid && !isDateValid(date)) return true;
    return false;
  }, [disabled, minDate, maxDate, disabledDates, isDateValid]);

  const isSameDay = (date1: Date, date2: Date) => {
    return date1.getFullYear() === date2.getFullYear() &&
           date1.getMonth() === date2.getMonth() &&
           date1.getDate() === date2.getDate();
  };

  const isToday = (date: Date) => {
    return isSameDay(date, new Date());
  };

  const isSelected = (date: Date) => {
    if (mode === 'single') {
      return selectedDate ? isSameDay(date, selectedDate) : false;
    }
    if (mode === 'multiple') {
      return internalSelectedDates.some(d => isSameDay(d, date));
    }
    if (mode === 'range') {
      if (rangeStart && rangeEnd) {
        return date >= rangeStart && date <= rangeEnd;
      }
      return rangeStart ? isSameDay(date, rangeStart) : false;
    }
    return false;
  };

  const handleDateSelect = (date: Date) => {
    if (readonly || isDateDisabled(date)) return;

    // Create new date at local midnight to avoid timezone issues
    const localDate = new Date(date.getFullYear(), date.getMonth(), date.getDate());

    if (mode === 'single') {
      onDateSelect?.(localDate);
    } else if (mode === 'multiple') {
      const newDates = internalSelectedDates.some(d => isSameDay(d, localDate))
        ? internalSelectedDates.filter(d => !isSameDay(d, localDate))
        : [...internalSelectedDates, localDate];
      
      setInternalSelectedDates(newDates);
      onMultipleSelect?.(newDates);
    } else if (mode === 'range') {
      if (!rangeStart || (rangeStart && rangeEnd)) {
        setRangeStart(localDate);
        setRangeEnd(null);
      } else {
        const start = localDate < rangeStart ? localDate : rangeStart;
        const end = localDate < rangeStart ? rangeStart : localDate;
        setRangeStart(start);
        setRangeEnd(end);
        onRangeSelect?.({ start, end });
      }
    }

    if (popup && mode === 'single') {
      setIsPopupOpen(false);
    }
  };

  const navigateMonth = (direction: 'prev' | 'next') => {
    const newDate = new Date(currentDate);
    if (direction === 'prev') {
      newDate.setMonth(newDate.getMonth() - 1);
    } else {
      newDate.setMonth(newDate.getMonth() + 1);
    }
    // Set to first day of month for consistency
    newDate.setDate(1);
    setCurrentDate(newDate);
    onMonthChange?.(newDate);
    onYearChange?.(newDate.getFullYear());
  };

  const goToToday = () => {
    const today = new Date();
    setCurrentDate(today);
    setFocusedDate(today);
    onMonthChange?.(today);
  };

  const getMonthDays = () => {
    const year = currentDate.getFullYear();
    const month = currentDate.getMonth();
    const firstDay = new Date(year, month, 1);
    const lastDay = new Date(year, month + 1, 0);
    const startDate = new Date(firstDay);
    
    // Adjust for week start
    const dayOfWeek = (firstDay.getDay() + 7 - weekStartsOn) % 7;
    startDate.setDate(startDate.getDate() - dayOfWeek);

    const days: Date[] = [];
    const current = new Date(startDate);

    // Generate 6 weeks (42 days) to ensure consistent layout
    for (let i = 0; i < 42; i++) {
      days.push(new Date(current));
      current.setDate(current.getDate() + 1);
    }

    return days;
  };

  const getWeekDays = () => {
    const days = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
    const reorderedDays = [...days.slice(weekStartsOn), ...days.slice(0, weekStartsOn)];
    return reorderedDays;
  };

  const getEventsForDate = (date: Date) => {
    return events.filter(event => isSameDay(event.date, date));
  };

  const getHighlightForDate = (date: Date) => {
    return highlightedDates.find(highlight => isSameDay(highlight.date, date));
  };

  const renderMonthView = () => {
    const days = getMonthDays();
    const weekDays = getWeekDays();

    return (
      <div className="calendar-month">
        {/* Header */}
        <div className="flex items-center justify-between mb-4">
          <button
            data-testid="calendar-prev"
            onClick={() => navigateMonth('prev')}
            className="p-2 hover:bg-gray-100 rounded-md transition-colors"
          >
            ‹
          </button>
          
          {renderHeader ? (
            renderHeader(currentDate)
          ) : (
            <h2 className="text-lg font-semibold">
              {currentDate.toLocaleDateString(locale, { month: 'long', year: 'numeric' })}
            </h2>
          )}
          
          <button
            data-testid="calendar-next"
            onClick={() => navigateMonth('next')}
            className="p-2 hover:bg-gray-100 rounded-md transition-colors"
          >
            ›
          </button>
        </div>

        {/* Month/Year Dropdowns */}
        {showMonthYearDropdown && (
          <div className="flex gap-2 mb-4">
            <select
              data-testid="calendar-month-dropdown"
              value={currentDate.getMonth()}
              onChange={(e) => {
                const newDate = new Date(currentDate);
                newDate.setMonth(parseInt(e.target.value));
                setCurrentDate(newDate);
              }}
              className="px-3 py-1 border rounded-md"
            >
              {Array.from({ length: 12 }, (_, i) => (
                <option key={i} value={i}>
                  {new Date(2000, i, 1).toLocaleDateString(locale, { month: 'long' })}
                </option>
              ))}
            </select>
            
            <select
              data-testid="calendar-year-dropdown"
              value={currentDate.getFullYear()}
              onChange={(e) => {
                const newDate = new Date(currentDate);
                newDate.setFullYear(parseInt(e.target.value));
                setCurrentDate(newDate);
              }}
              className="px-3 py-1 border rounded-md"
            >
              {Array.from({ length: 21 }, (_, i) => {
                const year = currentDate.getFullYear() - 10 + i;
                return (
                  <option key={year} value={year}>
                    {year}
                  </option>
                );
              })}
            </select>
          </div>
        )}

        {/* Week days header */}
        <div className={cn('grid grid-cols-7 gap-1 mb-2', showWeekNumbers && 'grid-cols-8')}>
          {showWeekNumbers && <div className="text-xs text-gray-500 p-2">Wk</div>}
          {weekDays.map(day => (
            <div key={day} className="text-xs text-gray-500 p-2 text-center font-medium">
              {day}
            </div>
          ))}
        </div>

        {/* Calendar grid */}
        <div className={cn('grid gap-1', showWeekNumbers ? 'grid-cols-8' : 'grid-cols-7')}>
          {showWeekNumbers && (
            <div data-testid="calendar-week-numbers" className="col-span-1">
              {Array.from({ length: 6 }, (_, weekIndex) => {
                const weekStart = days[weekIndex * 7];
                const weekNumber = getWeekNumber(weekStart);
                return (
                  <div key={weekIndex} className="text-xs text-gray-500 p-2 text-center">
                    {weekNumber}
                  </div>
                );
              })}
            </div>
          )}
          
          {days.map((date, index) => {
            const isCurrentMonth = date.getMonth() === currentDate.getMonth();
            const dayEvents = getEventsForDate(date);
            const highlight = getHighlightForDate(date);
            
            return (
              <div key={index} className="relative">
                <button
                  onClick={() => handleDateSelect(date)}
                  disabled={isDateDisabled(date)}
                  className={cn(
                    'w-full h-10 text-sm rounded-md transition-colors relative',
                    'hover:bg-gray-100 focus:ring-2 focus:ring-blue-500',
                    !isCurrentMonth && 'text-gray-400',
                    isToday(date) && 'bg-blue-100 text-blue-800',
                    isSelected(date) && 'bg-blue-500 text-white',
                    isDateDisabled(date) && 'opacity-50 cursor-not-allowed',
                    highlight?.className
                  )}
                  style={highlight?.style}
                >
                  {renderDay ? renderDay(date) : renderDateCell ? renderDateCell(date, isSelected(date)) : date.getDate()}
                  
                  {/* Events indicator */}
                  {dayEvents.length > 0 && (
                    <div className="absolute bottom-1 right-1 flex gap-0.5">
                      {dayEvents.slice(0, 3).map(event => (
                        <div
                          key={event.id}
                          className={cn(
                            'w-1.5 h-1.5 rounded-full',
                            event.color === 'red' && 'bg-red-500',
                            event.color === 'blue' && 'bg-blue-500',
                            event.color === 'green' && 'bg-green-500',
                            !event.color && 'bg-gray-500'
                          )}
                          onClick={(e) => {
                            e.stopPropagation();
                            onEventClick?.(event);
                          }}
                        />
                      ))}
                    </div>
                  )}
                </button>
                
                {/* Event list */}
                {dayEvents.length > 0 && !compact && (
                  <div className="absolute top-full left-0 z-10 bg-white border rounded-md shadow-lg p-2 min-w-max">
                    {dayEvents.map(event => (
                      <div
                        key={event.id}
                        className="text-xs py-1 px-2 rounded cursor-pointer hover:bg-gray-100"
                        onClick={() => onEventClick?.(event)}
                      >
                        {event.title}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            );
          })}
        </div>

        {/* Today button */}
        {showToday && (
          <button
            data-testid="calendar-today"
            onClick={goToToday}
            className="mt-4 px-4 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600 transition-colors"
          >
            Today
          </button>
        )}

        {/* Time picker */}
        {showTime && (
          <div data-testid="calendar-time-picker" className="mt-4 flex gap-2 items-center">
            <select
              onChange={(e) => onTimeChange?.({ hours: parseInt(e.target.value), minutes: 0 })}
              className="px-2 py-1 border rounded"
            >
              {Array.from({ length: 24 }, (_, i) => (
                <option key={i} value={i}>
                  {i.toString().padStart(2, '0')}
                </option>
              ))}
            </select>
            <span>:</span>
            <select
              onChange={(e) => onTimeChange?.({ hours: 0, minutes: parseInt(e.target.value) })}
              className="px-2 py-1 border rounded"
            >
              {Array.from({ length: 60 }, (_, i) => (
                <option key={i} value={i}>
                  {i.toString().padStart(2, '0')}
                </option>
              ))}
            </select>
          </div>
        )}
      </div>
    );
  };

  const renderYearView = () => {
    const months = Array.from({ length: 12 }, (_, i) => {
      const date = new Date(currentDate.getFullYear(), i, 1);
      return {
        date,
        name: date.toLocaleDateString(locale, { month: 'short' })
      };
    });

    return (
      <div className="calendar-year">
        <div className="flex items-center justify-between mb-4">
          <button onClick={() => navigateMonth('prev')}>‹</button>
          <h2 className="text-lg font-semibold">{currentDate.getFullYear()}</h2>
          <button onClick={() => navigateMonth('next')}>›</button>
        </div>
        
        <div className="grid grid-cols-3 gap-2">
          {months.map(({ date, name }, index) => (
            <button
              key={index}
              onClick={() => {
                setCurrentDate(date);
                setCurrentView('month');
              }}
              className="p-4 rounded-md hover:bg-gray-100 transition-colors"
            >
              {name}
            </button>
          ))}
        </div>
      </div>
    );
  };

  const renderDecadeView = () => {
    const startYear = Math.floor(currentDate.getFullYear() / 10) * 10;
    const years = Array.from({ length: 10 }, (_, i) => startYear + i);

    return (
      <div className="calendar-decade">
        <div className="flex items-center justify-between mb-4">
          <button onClick={() => {
            const newDate = new Date(currentDate);
            newDate.setFullYear(startYear - 10);
            setCurrentDate(newDate);
          }}>
            ‹
          </button>
          <h2 className="text-lg font-semibold">{startYear} - {startYear + 9}</h2>
          <button onClick={() => {
            const newDate = new Date(currentDate);
            newDate.setFullYear(startYear + 10);
            setCurrentDate(newDate);
          }}>
            ›
          </button>
        </div>
        
        <div className="grid grid-cols-2 gap-2">
          {years.map(year => (
            <button
              key={year}
              onClick={() => {
                const newDate = new Date(currentDate);
                newDate.setFullYear(year);
                setCurrentDate(newDate);
                setCurrentView('year');
              }}
              className="p-4 rounded-md hover:bg-gray-100 transition-colors"
            >
              {year}
            </button>
          ))}
        </div>
      </div>
    );
  };

  const getWeekNumber = (date: Date) => {
    const firstDay = new Date(date.getFullYear(), 0, 1);
    const days = Math.floor((date.getTime() - firstDay.getTime()) / (24 * 60 * 60 * 1000));
    return Math.ceil((days + firstDay.getDay() + 1) / 7);
  };

  const renderCalendarContent = () => {
    if (loading) {
      return (
        <div data-testid="calendar-loading" className="flex items-center justify-center py-8">
          {loadingComponent || (
            <div className="flex items-center space-x-2">
              <div className="w-5 h-5 border-2 border-gray-300 border-t-blue-500 rounded-full animate-spin"></div>
              <span className="text-gray-500">Loading...</span>
            </div>
          )}
        </div>
      );
    }

    switch (currentView) {
      case 'year':
        return renderYearView();
      case 'decade':
        return renderDecadeView();
      default:
        return renderMonthView();
    }
  };

  const calendarElement = (
    <div
      ref={calendarRef}
      className={cn(
        'calendar border rounded-lg',
        sizeClasses[size],
        themeClasses[theme],
        `theme-${theme}`,
        compact && 'compact-calendar',
        inline && 'inline-calendar',
        animated && 'animated-calendar',
        disabled && 'calendar-disabled',
        className
      )}
      data-testid={dataTestId}
      data-category={dataCategory}
      data-id={dataId}
      tabIndex={focusable ? 0 : undefined}
      {...props}
    >
      {showInput && (
        <input
          data-testid="calendar-input"
          type="date"
          className="w-full p-2 border rounded-md mb-4"
          onChange={(e) => {
            const date = new Date(e.target.value);
            setCurrentDate(date);
            setFocusedDate(date);
          }}
        />
      )}
      
      {renderCalendarContent()}
    </div>
  );

  if (!popup) {
    return calendarElement;
  }

  return (
    <div className="calendar-popup-container" ref={popupRef}>
      <button
        data-testid="calendar-trigger"
        onClick={() => setIsPopupOpen(!isPopupOpen)}
        className="px-4 py-2 border rounded-md hover:bg-gray-50 transition-colors"
      >
        {selectedDate ? selectedDate.toLocaleDateString(locale) : 'Select date'}
      </button>
      
      {isPopupOpen && (
        <div
          data-testid="calendar-popup"
          className="absolute z-50 mt-2 bg-white border rounded-lg shadow-lg"
        >
          {calendarElement}
        </div>
      )}
    </div>
  );
};

export default Calendar;