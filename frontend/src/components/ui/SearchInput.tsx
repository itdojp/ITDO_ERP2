import React, { useState, useCallback } from 'react';

interface SearchInputProps {
  placeholder?: string;
  value?: string;
  onChange?: (value: string) => void;
  onSearch?: (value: string) => void;
  onClear?: () => void;
  disabled?: boolean;
  loading?: boolean;
  size?: 'sm' | 'md' | 'lg';
  showClearButton?: boolean;
  debounceMs?: number;
}

export const SearchInput: React.FC<SearchInputProps> = ({
  placeholder = '検索...',
  value: controlledValue,
  onChange,
  onSearch,
  onClear,
  disabled = false,
  loading = false,
  size = 'md',
  showClearButton = true,
  debounceMs = 300
}) => {
  const [internalValue, setInternalValue] = useState('');
  const [debounceTimer, setDebounceTimer] = useState<NodeJS.Timeout | null>(null);

  const value = controlledValue !== undefined ? controlledValue : internalValue;

  const sizeClasses = {
    sm: 'h-8 text-sm px-3',
    md: 'h-10 text-base px-4',
    lg: 'h-12 text-lg px-5'
  };

  const iconSize = {
    sm: 'w-4 h-4',
    md: 'w-5 h-5',
    lg: 'w-6 h-6'
  };

  const handleInputChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const newValue = e.target.value;
    
    if (controlledValue === undefined) {
      setInternalValue(newValue);
    }
    
    onChange?.(newValue);

    // デバウンス機能
    if (debounceTimer) {
      clearTimeout(debounceTimer);
    }

    if (onSearch && debounceMs > 0) {
      const timer = setTimeout(() => {
        onSearch(newValue);
      }, debounceMs);
      setDebounceTimer(timer);
    }
  }, [controlledValue, onChange, onSearch, debounceMs, debounceTimer]);

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && onSearch) {
      if (debounceTimer) {
        clearTimeout(debounceTimer);
        setDebounceTimer(null);
      }
      onSearch(value);
    }
  };

  const handleClear = () => {
    const newValue = '';
    
    if (controlledValue === undefined) {
      setInternalValue(newValue);
    }
    
    onChange?.(newValue);
    onClear?.();
    onSearch?.(newValue);

    if (debounceTimer) {
      clearTimeout(debounceTimer);
      setDebounceTimer(null);
    }
  };

  const handleSearchClick = () => {
    if (onSearch) {
      if (debounceTimer) {
        clearTimeout(debounceTimer);
        setDebounceTimer(null);
      }
      onSearch(value);
    }
  };

  return (
    <div className="relative inline-flex items-center w-full max-w-md">
      {/* 検索アイコン */}
      <div className={`absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 ${iconSize[size]}`}>
        {loading ? (
          <div className={`animate-spin rounded-full border-2 border-gray-300 border-t-blue-600 ${iconSize[size]}`} />
        ) : (
          <svg className={iconSize[size]} fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
        )}
      </div>

      {/* 入力フィールド */}
      <input
        type="text"
        value={value}
        onChange={handleInputChange}
        onKeyPress={handleKeyPress}
        placeholder={placeholder}
        disabled={disabled}
        className={`
          w-full pl-10 pr-10 rounded-lg border border-gray-300 
          focus:ring-2 focus:ring-blue-500 focus:border-blue-500 
          disabled:bg-gray-50 disabled:text-gray-500 disabled:cursor-not-allowed
          ${sizeClasses[size]}
        `}
      />

      {/* クリアボタン */}
      {showClearButton && value && !disabled && (
        <button
          onClick={handleClear}
          className={`absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600 ${iconSize[size]}`}
          type="button"
        >
          <svg className={iconSize[size]} fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      )}

      {/* 検索ボタン（オプション） */}
      {onSearch && !showClearButton && (
        <button
          onClick={handleSearchClick}
          disabled={disabled}
          className={`absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-blue-600 disabled:cursor-not-allowed ${iconSize[size]}`}
          type="button"
        >
          <svg className={iconSize[size]} fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
        </button>
      )}
    </div>
  );
};

export default SearchInput;