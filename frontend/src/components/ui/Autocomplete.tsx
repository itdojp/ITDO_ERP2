import React, { useState, useRef, useCallback, useEffect, useMemo } from 'react';
import { cn } from '@/lib/utils';

export interface AutocompleteOption {
  value: string;
  label: string;
  group?: string;
}

export interface AutocompleteProps {
  options?: AutocompleteOption[];
  value?: string;
  defaultValue?: string;
  placeholder?: string;
  size?: 'sm' | 'md' | 'lg';
  theme?: 'light' | 'dark';
  disabled?: boolean;
  loading?: boolean;
  clearable?: boolean;
  multiple?: boolean;
  required?: boolean;
  error?: string | boolean;
  label?: string;
  helperText?: string;
  maxOptions?: number;
  minSearchLength?: number;
  debounceMs?: number;
  highlightMatch?: boolean;
  groupBy?: string;
  allowCreate?: boolean;
  virtualized?: boolean;
  filterFunction?: (option: AutocompleteOption, inputValue: string) => boolean;
  loadOptions?: (inputValue: string) => Promise<AutocompleteOption[]>;
  renderOption?: (option: AutocompleteOption) => React.ReactNode;
  loadingComponent?: React.ReactNode;
  noResultsComponent?: React.ReactNode;
  prefix?: React.ReactNode;
  suffix?: React.ReactNode;
  inputProps?: React.InputHTMLAttributes<HTMLInputElement>;
  onSelect?: (option: AutocompleteOption | AutocompleteOption[]) => void;
  onChange?: (value: string) => void;
  onFocus?: (e: React.FocusEvent<HTMLInputElement>) => void;
  onBlur?: (e: React.FocusEvent<HTMLInputElement>) => void;
  onClear?: () => void;
  onCreate?: (value: string) => void;
  className?: string;
  'data-testid'?: string;
  'data-category'?: string;
  'data-id'?: string;
}

export const Autocomplete: React.FC<AutocompleteProps> = ({
  options = [],
  value,
  defaultValue,
  placeholder = 'Type to search...',
  size = 'md',
  theme = 'light',
  disabled = false,
  loading = false,
  clearable = false,
  multiple = false,
  required = false,
  error,
  label,
  helperText,
  maxOptions,
  minSearchLength = 0,
  debounceMs = 0,
  highlightMatch = false,
  groupBy,
  allowCreate = false,
  virtualized = false,
  filterFunction,
  loadOptions,
  renderOption,
  loadingComponent,
  noResultsComponent,
  prefix,
  suffix,
  inputProps,
  onSelect,
  onChange,
  onFocus,
  onBlur,
  onClear,
  onCreate,
  className,
  'data-testid': dataTestId = 'autocomplete-container',
  'data-category': dataCategory,
  'data-id': dataId,
  ...props
}) => {
  const [inputValue, setInputValue] = useState(() => {
    if (value && options.length > 0) {
      const selectedOption = options.find(opt => opt.value === value);
      return selectedOption?.label || '';
    }
    if (defaultValue && options.length > 0) {
      const selectedOption = options.find(opt => opt.value === defaultValue);
      return selectedOption?.label || '';
    }
    return '';
  });
  const [isOpen, setIsOpen] = useState(false);
  const [highlightedIndex, setHighlightedIndex] = useState(-1);
  const [selectedOptions, setSelectedOptions] = useState<AutocompleteOption[]>([]);
  const [asyncOptions, setAsyncOptions] = useState<AutocompleteOption[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  const inputRef = useRef<HTMLInputElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const debounceTimeoutRef = useRef<NodeJS.Timeout>();

  const sizeClasses = {
    sm: 'size-sm text-sm',
    md: 'size-md text-base',
    lg: 'size-lg text-lg'
  };

  const themeClasses = {
    light: 'theme-light bg-white border-gray-300 text-gray-900',
    dark: 'theme-dark bg-gray-800 border-gray-600 text-white'
  };

  // Update input value when controlled value changes
  useEffect(() => {
    if (value !== undefined && options.length > 0) {
      const selectedOption = options.find(opt => opt.value === value);
      setInputValue(selectedOption?.label || '');
    }
  }, [value, options]);

  // Default filter function
  const defaultFilter = useCallback((option: AutocompleteOption, searchValue: string) => {
    return option.label.toLowerCase().includes(searchValue.toLowerCase());
  }, []);

  // Filter options based on input
  const filteredOptions = useMemo(() => {
    const currentOptions = loadOptions ? asyncOptions : options;
    
    let result;
    if (!inputValue || inputValue.length < minSearchLength) {
      result = minSearchLength > 0 ? [] : currentOptions;
    } else {
      result = currentOptions.filter(option => 
        filterFunction ? filterFunction(option, inputValue) : defaultFilter(option, inputValue)
      );
    }

    return maxOptions ? result.slice(0, maxOptions) : result;
  }, [options, asyncOptions, inputValue, minSearchLength, filterFunction, defaultFilter, maxOptions, loadOptions]);

  // Group options if groupBy is specified
  const groupedOptions = useMemo(() => {
    if (!groupBy) return { '': filteredOptions };

    return filteredOptions.reduce((groups, option) => {
      const group = (option as any)[groupBy] || '';
      if (!groups[group]) {
        groups[group] = [];
      }
      groups[group].push(option);
      return groups;
    }, {} as Record<string, AutocompleteOption[]>);
  }, [filteredOptions, groupBy]);

  // Debounced async options loading
  const loadAsyncOptions = useCallback(async (searchValue: string) => {
    if (!loadOptions) return;

    if (debounceTimeoutRef.current) {
      clearTimeout(debounceTimeoutRef.current);
    }

    debounceTimeoutRef.current = setTimeout(async () => {
      setIsLoading(true);
      try {
        const results = await loadOptions(searchValue);
        setAsyncOptions(results);
      } catch (error) {
        console.error('Failed to load options:', error);
        setAsyncOptions([]);
      } finally {
        setIsLoading(false);
      }
    }, debounceMs);
  }, [loadOptions, debounceMs]);

  // Handle input change
  const handleInputChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const newValue = e.target.value;
    setInputValue(newValue);
    setHighlightedIndex(-1);
    
    if (!isOpen && newValue) {
      setIsOpen(true);
    }

    onChange?.(newValue);

    if (loadOptions) {
      loadAsyncOptions(newValue);
    }
  }, [isOpen, onChange, loadOptions, loadAsyncOptions]);

  // Handle input focus
  const handleInputFocus = useCallback((e: React.FocusEvent<HTMLInputElement>) => {
    if (!disabled) {
      setIsOpen(true);
      if (loadOptions && !inputValue) {
        loadAsyncOptions('');
      }
    }
    onFocus?.(e);
  }, [disabled, onFocus, loadOptions, inputValue, loadAsyncOptions]);

  // Handle input blur
  const handleInputBlur = useCallback((e: React.FocusEvent<HTMLInputElement>) => {
    // Delay closing to allow option clicks
    setTimeout(() => {
      setIsOpen(false);
      setHighlightedIndex(-1);
    }, 150);
    onBlur?.(e);
  }, [onBlur]);

  // Handle option selection
  const handleOptionSelect = useCallback((option: AutocompleteOption) => {
    if (multiple) {
      const newSelection = selectedOptions.find(opt => opt.value === option.value)
        ? selectedOptions.filter(opt => opt.value !== option.value)
        : [...selectedOptions, option];
      
      setSelectedOptions(newSelection);
      onSelect?.(newSelection);
      setInputValue('');
    } else {
      setInputValue(option.label);
      setIsOpen(false);
      onSelect?.(option);
    }
    setHighlightedIndex(-1);
  }, [multiple, selectedOptions, onSelect]);

  // Handle keyboard navigation
  const handleKeyDown = useCallback((e: React.KeyboardEvent<HTMLInputElement>) => {
    if (!isOpen) {
      if (e.key === 'ArrowDown' || e.key === 'Enter') {
        e.preventDefault();
        setIsOpen(true);
      }
      return;
    }

    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault();
        setHighlightedIndex(prev => 
          prev < filteredOptions.length - 1 ? prev + 1 : 0
        );
        break;
      
      case 'ArrowUp':
        e.preventDefault();
        setHighlightedIndex(prev => 
          prev > 0 ? prev - 1 : filteredOptions.length - 1
        );
        break;
      
      case 'Enter':
        e.preventDefault();
        if (highlightedIndex >= 0 && filteredOptions[highlightedIndex]) {
          handleOptionSelect(filteredOptions[highlightedIndex]);
        } else if (allowCreate && inputValue && onCreate) {
          onCreate(inputValue);
          setIsOpen(false);
        }
        break;
      
      case 'Escape':
        e.preventDefault();
        setIsOpen(false);
        setHighlightedIndex(-1);
        inputRef.current?.blur();
        break;
    }
  }, [isOpen, filteredOptions, highlightedIndex, handleOptionSelect, allowCreate, inputValue, onCreate]);

  // Handle clear button
  const handleClear = useCallback(() => {
    setInputValue('');
    setSelectedOptions([]);
    setIsOpen(false);
    onClear?.();
    inputRef.current?.focus();
  }, [onClear]);

  // Handle create new option
  const handleCreateOption = useCallback(() => {
    if (allowCreate && inputValue && onCreate) {
      onCreate(inputValue);
      setIsOpen(false);
    }
  }, [allowCreate, inputValue, onCreate]);

  // Click outside handler
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setIsOpen(false);
        setHighlightedIndex(-1);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Highlight matching text
  const highlightText = useCallback((text: string, searchValue: string) => {
    if (!highlightMatch || !searchValue) {
      return text;
    }

    const regex = new RegExp(`(${searchValue})`, 'gi');
    const parts = text.split(regex);

    return parts.map((part, index) =>
      regex.test(part) ? (
        <mark key={index} className="bg-yellow-200" data-testid="highlighted-text">
          {part}
        </mark>
      ) : (
        part
      )
    );
  }, [highlightMatch]);

  // Render option
  const renderOptionContent = useCallback((option: AutocompleteOption, index: number) => {
    const isHighlighted = index === highlightedIndex;
    
    if (renderOption) {
      return (
        <div
          key={option.value}
          role="option"
          aria-selected={isHighlighted}
          className={cn(
            'px-3 py-2 cursor-pointer transition-colors',
            isHighlighted && 'highlighted bg-blue-100 text-blue-900'
          )}
          onClick={() => handleOptionSelect(option)}
        >
          {renderOption(option)}
        </div>
      );
    }

    return (
      <div
        key={option.value}
        role="option"
        aria-selected={isHighlighted}
        className={cn(
          'px-3 py-2 cursor-pointer transition-colors hover:bg-gray-100',
          isHighlighted && 'highlighted bg-blue-100 text-blue-900'
        )}
        onClick={() => handleOptionSelect(option)}
      >
        {highlightText(option.label, inputValue)}
      </div>
    );
  }, [highlightedIndex, renderOption, handleOptionSelect, highlightText, inputValue]);

  // Render dropdown content
  const renderDropdownContent = () => {
    if (isLoading || loading) {
      return (
        <div className="p-3 text-center text-gray-500" data-testid="autocomplete-loading">
          {loadingComponent || (
            <div className="flex items-center justify-center space-x-2">
              <div className="w-4 h-4 border-2 border-gray-300 border-t-blue-500 rounded-full animate-spin"></div>
              <span>Loading...</span>
            </div>
          )}
        </div>
      );
    }

    if (filteredOptions.length === 0) {
      // Show create option if allowed and search text exists
      if (allowCreate && inputValue && inputValue.length >= minSearchLength && !options.some(opt => opt.label.toLowerCase() === inputValue.toLowerCase())) {
        return (
          <div
            className="px-3 py-2 cursor-pointer bg-gray-50 text-blue-600 hover:bg-gray-100"
            onClick={handleCreateOption}
            data-testid="create-option"
          >
            Create "{inputValue}"
          </div>
        );
      }
      
      return (
        <div className="p-3 text-center text-gray-500" data-testid="no-results">
          {noResultsComponent || 'No results found'}
        </div>
      );
    }

    if (virtualized) {
      return (
        <div data-testid="virtualized-list" className="max-h-60 overflow-auto">
          {filteredOptions.slice(0, 10).map((option, index) => renderOptionContent(option, index))}
        </div>
      );
    }

    if (groupBy) {
      let globalIndex = 0;
      return (
        <div className="max-h-60 overflow-auto">
          {Object.entries(groupedOptions).map(([group, groupOptions]) => (
            <div key={group}>
              {group && (
                <div className="px-3 py-1 text-xs font-semibold text-gray-500 bg-gray-50">
                  {group}
                </div>
              )}
              {groupOptions.map((option) => {
                const content = renderOptionContent(option, globalIndex);
                globalIndex++;
                return content;
              })}
            </div>
          ))}
        </div>
      );
    }

    return (
      <div className="max-h-60 overflow-auto">
        {filteredOptions.map((option, index) => renderOptionContent(option, index))}
        {allowCreate && inputValue && inputValue.length >= minSearchLength && !filteredOptions.some(opt => opt.label.toLowerCase() === inputValue.toLowerCase()) && (
          <div
            className="px-3 py-2 cursor-pointer bg-gray-50 border-t text-blue-600 hover:bg-gray-100"
            onClick={handleCreateOption}
            data-testid="create-option"
          >
            Create "{inputValue}"
          </div>
        )}
      </div>
    );
  };

  // Render selected items for multiple selection
  const renderSelectedItems = () => {
    if (!multiple || selectedOptions.length === 0) return null;

    return (
      <div className="flex flex-wrap gap-1 mb-2" data-testid="selected-items">
        {selectedOptions.map(option => (
          <span
            key={option.value}
            className="inline-flex items-center gap-1 px-2 py-1 bg-blue-100 text-blue-800 rounded-full text-sm"
          >
            {option.label}
            <button
              type="button"
              onClick={() => handleOptionSelect(option)}
              className="hover:text-blue-600"
            >
              ✕
            </button>
          </span>
        ))}
      </div>
    );
  };

  return (
    <div
      ref={containerRef}
      className={cn(
        'relative',
        sizeClasses[size],
        themeClasses[theme],
        error && 'error',
        className
      )}
      data-testid={dataTestId}
      data-category={dataCategory}
      data-id={dataId}
      {...props}
    >
      {label && (
        <label className="block text-sm font-medium text-gray-700 mb-1">
          {label}
          {required && <span className="text-red-500 ml-1">*</span>}
        </label>
      )}

      {renderSelectedItems()}

      <div className="relative">
        <div className="flex items-center">
          {prefix && <div className="pl-3">{prefix}</div>}
          
          <input
            ref={inputRef}
            type="text"
            value={inputValue}
            placeholder={placeholder}
            disabled={disabled}
            className={cn(
              'w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
              sizeClasses[size],
              themeClasses[theme],
              error && 'border-red-500',
              disabled && 'bg-gray-100 cursor-not-allowed',
              prefix && 'pl-0',
              (suffix || clearable) && 'pr-8'
            )}
            onChange={handleInputChange}
            onFocus={handleInputFocus}
            onBlur={handleInputBlur}
            onKeyDown={handleKeyDown}
            data-testid="autocomplete-input"
            {...inputProps}
          />

          <div className="flex items-center pr-3">
            {clearable && inputValue && (
              <button
                type="button"
                onClick={handleClear}
                className="text-gray-400 hover:text-gray-600 mr-1"
                data-testid="clear-button"
              >
                ✕
              </button>
            )}
            {suffix}
          </div>
        </div>

        {(isOpen || loading) && (
          <div
            ref={dropdownRef}
            className="absolute z-50 w-full mt-1 bg-white border border-gray-300 rounded-md shadow-lg"
            data-testid="autocomplete-dropdown"
          >
            {renderDropdownContent()}
          </div>
        )}
      </div>

      {error && typeof error === 'string' && (
        <p className="mt-1 text-sm text-red-600">{error}</p>
      )}

      {helperText && !error && (
        <p className="mt-1 text-sm text-gray-600">{helperText}</p>
      )}
    </div>
  );
};

export default Autocomplete;