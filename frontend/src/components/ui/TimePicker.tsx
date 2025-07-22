import React, { useState, useRef, useEffect } from 'react';

interface TimePickerProps {
  value?: string;
  onChange?: (time: string) => void;
  format?: '12' | '24';
  placeholder?: string;
  disabled?: boolean;
  size?: 'sm' | 'md' | 'lg';
  minuteStep?: number;
}

export const TimePicker: React.FC<TimePickerProps> = ({
  value,
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
        setIsOpen(false);
      }
    };

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
    </div>
  );
};

export default TimePicker;