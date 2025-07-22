import React, { useState, useRef, useEffect } from 'react';

interface SelectOption {
  value: string;
  label: string;
  disabled?: boolean;
}

interface SelectProps {
  value?: string;
  defaultValue?: string;
  placeholder?: string;
  options?: SelectOption[];
  children?: React.ReactNode;
  onChange?: (value: string) => void;
  onSelect?: (value: string, option: SelectOption) => void;
  disabled?: boolean;
  loading?: boolean;
  error?: string;
  allowClear?: boolean;
  searchable?: boolean;
  size?: 'sm' | 'md' | 'lg';
  className?: string;
  dropdownClassName?: string;
  required?: boolean;
}

interface OptionProps {
  value: string;
  children: React.ReactNode;
  disabled?: boolean;
}

export const SelectOption: React.FC<OptionProps> = ({ value, children, disabled = false }) => {
  return <option value={value} disabled={disabled}>{children}</option>;
};

export const Select: React.FC<SelectProps> & { Option: React.FC<OptionProps> } = ({
  value: controlledValue,
  defaultValue,
  placeholder = '選択してください',
  options = [],
  children,
  onChange,
  onSelect,
  disabled = false,
  loading = false,
  error,
  allowClear = false,
  searchable = false,
  size = 'md',
  className = '',
  dropdownClassName = '',
  required = false,
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [internalValue, setInternalValue] = useState(controlledValue || defaultValue || '');
  const [searchQuery, setSearchQuery] = useState('');
  const selectRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const currentValue = controlledValue !== undefined ? controlledValue : internalValue;

  // Extract options from children or use provided options
  const allOptions: SelectOption[] = React.useMemo(() => {
    if (options.length > 0) return options;
    
    const childOptions: SelectOption[] = [];
    React.Children.forEach(children, (child) => {
      if (React.isValidElement(child) && child.type === SelectOption) {
        childOptions.push({
          value: child.props.value,
          label: child.props.children?.toString() || '',
          disabled: child.props.disabled,
        });
      }
    });
    return childOptions;
  }, [options, children]);

  // Filter options based on search query
  const filteredOptions = React.useMemo(() => {
    if (!searchQuery) return allOptions;
    return allOptions.filter(option => 
      option.label.toLowerCase().includes(searchQuery.toLowerCase())
    );
  }, [allOptions, searchQuery]);

  const selectedOption = allOptions.find(option => option.value === currentValue);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (selectRef.current && !selectRef.current.contains(event.target as Node)) {
        setIsOpen(false);
        setSearchQuery('');
      }
    };

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [isOpen]);

  const handleSelect = (option: SelectOption) => {
    if (option.disabled) return;

    const newValue = option.value;
    if (controlledValue === undefined) {
      setInternalValue(newValue);
    }
    
    onChange?.(newValue);
    onSelect?.(newValue, option);
    setIsOpen(false);
    setSearchQuery('');
  };

  const handleClear = (e: React.MouseEvent) => {
    e.stopPropagation();
    const newValue = '';
    
    if (controlledValue === undefined) {
      setInternalValue(newValue);
    }
    
    onChange?.(newValue);
    setSearchQuery('');
  };

  const handleToggle = () => {
    if (disabled || loading) return;
    setIsOpen(!isOpen);
    
    if (searchable && !isOpen) {
      setTimeout(() => inputRef.current?.focus(), 0);
    }
  };

  const sizeClasses = {
    sm: 'px-3 py-2 text-sm',
    md: 'px-3 py-2.5 text-sm',
    lg: 'px-4 py-3 text-base',
  };

  const selectClasses = `
    relative w-full bg-white border border-gray-300 rounded-md shadow-sm
    focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500
    ${sizeClasses[size]}
    ${disabled ? 'bg-gray-50 cursor-not-allowed' : 'cursor-pointer'}
    ${error ? 'border-red-300 focus:ring-red-500 focus:border-red-500' : ''}
    ${className}
  `;

  return (
    <div ref={selectRef} className="relative w-full">
      <div
        className={selectClasses}
        onClick={handleToggle}
        role="combobox"
        aria-expanded={isOpen}
        aria-haspopup="listbox"
        aria-required={required}
      >
        <div className="flex items-center justify-between">
          <div className="flex-1 truncate">
            {searchable && isOpen ? (
              <input
                ref={inputRef}
                type="text"
                className="w-full border-none outline-none bg-transparent"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder={placeholder}
                onClick={(e) => e.stopPropagation()}
              />
            ) : (
              <span className={selectedOption ? 'text-gray-900' : 'text-gray-500'}>
                {selectedOption ? selectedOption.label : placeholder}
              </span>
            )}
          </div>
          
          <div className="flex items-center space-x-1">
            {loading && (
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600" />
            )}
            
            {allowClear && currentValue && !disabled && !loading && (
              <button
                type="button"
                className="text-gray-400 hover:text-gray-600 focus:outline-none"
                onClick={handleClear}
                tabIndex={-1}
              >
                <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            )}
            
            <svg
              className={`h-4 w-4 text-gray-400 transition-transform ${isOpen ? 'rotate-180' : ''}`}
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          </div>
        </div>
      </div>

      {/* Dropdown */}
      {isOpen && (
        <div className={`
          absolute z-50 w-full mt-1 bg-white border border-gray-200 rounded-md shadow-lg
          max-h-60 overflow-auto
          ${dropdownClassName}
        `}>
          {filteredOptions.length === 0 ? (
            <div className="px-3 py-2 text-sm text-gray-500 text-center">
              {searchQuery ? '該当する項目がありません' : 'オプションがありません'}
            </div>
          ) : (
            <ul role="listbox">
              {filteredOptions.map((option) => (
                <li
                  key={option.value}
                  role="option"
                  aria-selected={option.value === currentValue}
                  className={`
                    px-3 py-2 cursor-pointer text-sm transition-colors
                    ${option.disabled 
                      ? 'text-gray-400 cursor-not-allowed' 
                      : 'text-gray-900 hover:bg-blue-50'
                    }
                    ${option.value === currentValue ? 'bg-blue-100 text-blue-600' : ''}
                  `}
                  onClick={() => handleSelect(option)}
                >
                  {option.label}
                </li>
              ))}
            </ul>
          )}
        </div>
      )}

      {error && (
        <p className="mt-1 text-sm text-red-600 flex items-center">
          <svg className="w-4 h-4 mr-1 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          {error}
        </p>
      )}
    </div>
  );
};

Select.Option = SelectOption;