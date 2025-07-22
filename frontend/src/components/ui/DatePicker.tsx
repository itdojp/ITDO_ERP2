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
}

export const DatePicker: React.FC<DatePickerProps> = ({
  value,
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
        setIsOpen(false);
      }
    };

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
        )}
      </div>
    );
  };

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

      {isOpen && renderCalendar()}
    </div>
  );
};

export default DatePicker;