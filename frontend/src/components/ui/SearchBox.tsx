import React, {
  useState,
  useRef,
  useCallback,
  useEffect,
  useMemo,
} from "react";
import { cn } from "@/lib/utils";

export interface SearchBoxFilter {
  key: string;
  label: string;
  options: string[];
}

export interface SearchBoxShortcut {
  key: string;
  description: string;
}

export interface SearchBoxProps {
  value?: string;
  placeholder?: string;
  size?: "sm" | "md" | "lg";
  theme?: "light" | "dark";
  disabled?: boolean;
  readonly?: boolean;
  loading?: boolean;
  clearable?: boolean;
  showSearchButton?: boolean;
  voiceSearch?: boolean;
  showRecentSearches?: boolean;
  showHistory?: boolean;
  advancedSearch?: boolean;
  autoComplete?: boolean;
  highlightMatch?: boolean;
  minSearchLength?: number;
  debounceMs?: number;
  suggestions?: string[];
  recentSearches?: string[];
  searchHistory?: string[];
  filters?: SearchBoxFilter[];
  activeFilters?: Record<string, string>;
  categories?: string[];
  selectedCategory?: string;
  searchScopes?: string[];
  selectedScope?: string;
  shortcuts?: SearchBoxShortcut[];
  noResultsComponent?: React.ReactNode;
  renderSuggestion?: (suggestion: string) => React.ReactNode;
  loadSuggestions?: (query: string) => Promise<string[]>;
  onChange?: (value: string) => void;
  onSearch?: (query: string, filters: Record<string, string>) => void;
  onSelect?: (value: string) => void;
  onClear?: () => void;
  onFocus?: (e: React.FocusEvent<HTMLInputElement>) => void;
  onBlur?: (e: React.FocusEvent<HTMLInputElement>) => void;
  onFiltersChange?: (filters: Record<string, string>) => void;
  onCategoryChange?: (category: string) => void;
  onScopeChange?: (scope: string) => void;
  onVoiceSearch?: () => void;
  className?: string;
  "data-testid"?: string;
  "data-category"?: string;
  "data-id"?: string;
}

export const SearchBox: React.FC<SearchBoxProps> = ({
  value,
  placeholder = "Search...",
  size = "md",
  theme = "light",
  disabled = false,
  readonly = false,
  loading = false,
  clearable = false,
  showSearchButton = false,
  voiceSearch = false,
  showRecentSearches = false,
  showHistory = false,
  advancedSearch = false,
  autoComplete = false,
  highlightMatch = false,
  minSearchLength = 0,
  debounceMs = 300,
  suggestions = [],
  recentSearches = [],
  searchHistory = [],
  filters = [],
  activeFilters = {},
  categories = [],
  selectedCategory,
  searchScopes = [],
  selectedScope,
  shortcuts = [],
  noResultsComponent,
  renderSuggestion,
  loadSuggestions,
  onChange,
  onSearch,
  onSelect,
  onClear,
  onFocus,
  onBlur,
  onFiltersChange,
  onCategoryChange,
  onScopeChange,
  onVoiceSearch,
  className,
  "data-testid": dataTestId = "searchbox-container",
  "data-category": dataCategory,
  "data-id": dataId,
  ...props
}) => {
  const [inputValue, setInputValue] = useState(value || "");
  const [isOpen, setIsOpen] = useState(false);
  const [highlightedIndex, setHighlightedIndex] = useState(-1);
  const [showFilters, setShowFilters] = useState(false);
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [asyncSuggestions, setAsyncSuggestions] = useState<string[]>([]);
  const [isLoadingSuggestions, setIsLoadingSuggestions] = useState(false);

  const inputRef = useRef<HTMLInputElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const debounceTimeoutRef = useRef<NodeJS.Timeout>();

  const sizeClasses = {
    sm: "size-sm text-sm h-8",
    md: "size-md text-base h-10",
    lg: "size-lg text-lg h-12",
  };

  const themeClasses = {
    light: "theme-light bg-white border-gray-300 text-gray-900",
    dark: "theme-dark bg-gray-800 border-gray-600 text-white",
  };

  // Update input value when controlled value changes
  useEffect(() => {
    if (value !== undefined) {
      setInputValue(value);
    }
  }, [value]);

  // Filter suggestions based on input
  const filteredSuggestions = useMemo(() => {
    const currentSuggestions = loadSuggestions ? asyncSuggestions : suggestions;

    if (!inputValue || inputValue.length < minSearchLength) {
      return [];
    }

    return currentSuggestions.filter((suggestion) =>
      suggestion.toLowerCase().includes(inputValue.toLowerCase()),
    );
  }, [
    suggestions,
    asyncSuggestions,
    inputValue,
    minSearchLength,
    loadSuggestions,
  ]);

  // Load async suggestions with debounce
  const loadAsyncSuggestions = useCallback(
    async (query: string) => {
      if (!loadSuggestions || query.length < minSearchLength) return;

      if (debounceTimeoutRef.current) {
        clearTimeout(debounceTimeoutRef.current);
      }

      debounceTimeoutRef.current = setTimeout(async () => {
        setIsLoadingSuggestions(true);
        try {
          const results = await loadSuggestions(query);
          setAsyncSuggestions(results);
        } catch (error) {
          console.error("Failed to load suggestions:", error);
          setAsyncSuggestions([]);
        } finally {
          setIsLoadingSuggestions(false);
        }
      }, debounceMs);
    },
    [loadSuggestions, minSearchLength, debounceMs],
  );

  // Handle input change
  const handleInputChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const newValue = e.target.value;
      setInputValue(newValue);
      setHighlightedIndex(-1);

      if (!isOpen && newValue) {
        setIsOpen(true);
      }

      onChange?.(newValue);

      if (loadSuggestions) {
        loadAsyncSuggestions(newValue);
      }
    },
    [isOpen, onChange, loadSuggestions, loadAsyncSuggestions],
  );

  // Handle input focus
  const handleInputFocus = useCallback(
    (e: React.FocusEvent<HTMLInputElement>) => {
      if (!disabled && !readonly) {
        setIsOpen(true);
      }
      onFocus?.(e);
    },
    [disabled, readonly, onFocus],
  );

  // Handle input blur
  const handleInputBlur = useCallback(
    (e: React.FocusEvent<HTMLInputElement>) => {
      // Delay closing to allow clicks on suggestions
      setTimeout(() => {
        setIsOpen(false);
        setHighlightedIndex(-1);
      }, 150);
      onBlur?.(e);
    },
    [onBlur],
  );

  // Handle suggestion selection
  const handleSuggestionSelect = useCallback(
    (suggestion: string) => {
      setInputValue(suggestion);
      setIsOpen(false);
      onSelect?.(suggestion);
    },
    [onSelect],
  );

  // Handle keyboard navigation
  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent<HTMLInputElement>) => {
      if (!isOpen) {
        if (e.key === "ArrowDown" || e.key === "Enter") {
          e.preventDefault();
          setIsOpen(true);
        }
        return;
      }

      const currentSuggestions =
        filteredSuggestions.length > 0
          ? filteredSuggestions
          : showRecentSearches && recentSearches.length > 0
            ? recentSearches
            : [];

      switch (e.key) {
        case "ArrowDown":
          e.preventDefault();
          setHighlightedIndex((prev) =>
            prev < currentSuggestions.length - 1 ? prev + 1 : 0,
          );
          break;

        case "ArrowUp":
          e.preventDefault();
          setHighlightedIndex((prev) =>
            prev > 0 ? prev - 1 : currentSuggestions.length - 1,
          );
          break;

        case "Enter":
          e.preventDefault();
          if (highlightedIndex >= 0 && currentSuggestions[highlightedIndex]) {
            handleSuggestionSelect(currentSuggestions[highlightedIndex]);
          } else {
            handleSearch();
          }
          break;

        case "Escape":
          e.preventDefault();
          setIsOpen(false);
          setHighlightedIndex(-1);
          inputRef.current?.blur();
          break;

        case "Tab":
          if (autoComplete && currentSuggestions.length > 0) {
            e.preventDefault();
            const suggestionToSelect =
              highlightedIndex >= 0
                ? currentSuggestions[highlightedIndex]
                : currentSuggestions[0];
            handleSuggestionSelect(suggestionToSelect);
          }
          break;
      }
    },
    [
      isOpen,
      filteredSuggestions,
      highlightedIndex,
      handleSuggestionSelect,
      showRecentSearches,
      recentSearches,
      autoComplete,
    ],
  );

  // Handle search execution
  const handleSearch = useCallback(() => {
    onSearch?.(inputValue, activeFilters);
    setIsOpen(false);
  }, [inputValue, activeFilters, onSearch]);

  // Handle clear
  const handleClear = useCallback(() => {
    setInputValue("");
    setIsOpen(false);
    onClear?.();
    inputRef.current?.focus();
  }, [onClear]);

  // Handle filter change
  const handleFilterChange = useCallback(
    (filterKey: string, value: string) => {
      if (value === "") {
        const newFilters = { ...activeFilters };
        delete newFilters[filterKey];
        onFiltersChange?.(newFilters);
      } else {
        const newFilters = { ...activeFilters, [filterKey]: value };
        onFiltersChange?.(newFilters);
      }
    },
    [activeFilters, onFiltersChange],
  );

  // Handle filter removal
  const handleFilterRemove = useCallback(
    (filterKey: string) => {
      const newFilters = { ...activeFilters };
      delete newFilters[filterKey];
      onFiltersChange?.(newFilters);
    },
    [activeFilters, onFiltersChange],
  );

  // Click outside handler
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        containerRef.current &&
        !containerRef.current.contains(event.target as Node)
      ) {
        setIsOpen(false);
        setShowFilters(false);
        setHighlightedIndex(-1);
      }
    };

    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  // Highlight matching text
  const highlightText = useCallback(
    (text: string, searchValue: string) => {
      if (!highlightMatch || !searchValue) {
        return text;
      }

      const regex = new RegExp(`(${searchValue})`, "gi");
      const parts = text.split(regex);

      return parts.map((part, index) =>
        regex.test(part) ? (
          <mark
            key={index}
            className="bg-yellow-200"
            data-testid="highlighted-text"
          >
            {part}
          </mark>
        ) : (
          part
        ),
      );
    },
    [highlightMatch],
  );

  // Render suggestion item
  const renderSuggestionItem = useCallback(
    (suggestion: string, index: number) => {
      const isHighlighted = index === highlightedIndex;

      return (
        <div
          key={suggestion}
          className={cn(
            "px-3 py-2 cursor-pointer transition-colors",
            isHighlighted && "highlighted bg-blue-100 text-blue-900",
            !isHighlighted && "hover:bg-gray-100",
          )}
          onClick={() => handleSuggestionSelect(suggestion)}
        >
          {renderSuggestion
            ? renderSuggestion(suggestion)
            : highlightText(suggestion, inputValue)}
        </div>
      );
    },
    [
      highlightedIndex,
      renderSuggestion,
      highlightText,
      inputValue,
      handleSuggestionSelect,
    ],
  );

  // Render suggestions dropdown
  const renderSuggestions = () => {
    if (!isOpen) return null;

    const hasFiltered = filteredSuggestions.length > 0;
    const hasRecent =
      showRecentSearches && recentSearches.length > 0 && !inputValue;
    const hasHistory = showHistory && searchHistory.length > 0 && !inputValue;

    if (!hasFiltered && !hasRecent && !hasHistory) {
      if (inputValue && inputValue.length >= minSearchLength) {
        return (
          <div className="absolute z-50 w-full mt-1 bg-white border border-gray-300 rounded-md shadow-lg">
            <div
              className="p-3 text-center text-gray-500"
              data-testid="no-results"
            >
              {noResultsComponent || "No results found"}
            </div>
          </div>
        );
      }
      return null;
    }

    return (
      <div
        className="absolute z-50 w-full mt-1 bg-white border border-gray-300 rounded-md shadow-lg"
        data-testid="suggestions-dropdown"
      >
        <div className="max-h-60 overflow-auto">
          {hasFiltered && (
            <>
              {isLoadingSuggestions && (
                <div className="p-3 text-center text-gray-500">
                  <div className="flex items-center justify-center space-x-2">
                    <div className="w-4 h-4 border-2 border-gray-300 border-t-blue-500 rounded-full animate-spin"></div>
                    <span>Loading...</span>
                  </div>
                </div>
              )}
              {filteredSuggestions.map((suggestion, index) =>
                renderSuggestionItem(suggestion, index),
              )}
            </>
          )}

          {hasRecent && (
            <div data-testid="recent-searches">
              <div className="px-3 py-1 text-xs font-semibold text-gray-500 bg-gray-50">
                Recent Searches
              </div>
              {recentSearches.map((search, index) => (
                <div
                  key={search}
                  className="px-3 py-2 cursor-pointer hover:bg-gray-100"
                  onClick={() => handleSuggestionSelect(search)}
                >
                  <span className="text-gray-400 mr-2">🕒</span>
                  {search}
                </div>
              ))}
            </div>
          )}

          {hasHistory && (
            <div data-testid="search-history">
              <div className="px-3 py-1 text-xs font-semibold text-gray-500 bg-gray-50">
                Search History
              </div>
              {searchHistory.map((search, index) => (
                <div
                  key={search}
                  className="px-3 py-2 cursor-pointer hover:bg-gray-100"
                  onClick={() => handleSuggestionSelect(search)}
                >
                  <span className="text-gray-400 mr-2">📝</span>
                  {search}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    );
  };

  // Render active filters
  const renderActiveFilters = () => {
    const activeFilterKeys = Object.keys(activeFilters);
    if (activeFilterKeys.length === 0) return null;

    return (
      <div className="flex flex-wrap gap-1 mt-2" data-testid="active-filters">
        {activeFilterKeys.map((filterKey) => (
          <span
            key={filterKey}
            className="inline-flex items-center gap-1 px-2 py-1 bg-blue-100 text-blue-800 rounded-full text-xs"
          >
            {activeFilters[filterKey]}
            <button
              type="button"
              onClick={() => handleFilterRemove(filterKey)}
              className="hover:text-blue-600"
              data-testid={`remove-filter-${filterKey}`}
            >
              ✕
            </button>
          </span>
        ))}
      </div>
    );
  };

  // Render filter dropdown
  const renderFilterDropdown = () => {
    if (!showFilters || filters.length === 0) return null;

    return (
      <div
        className="absolute z-50 right-0 mt-1 w-64 bg-white border border-gray-300 rounded-md shadow-lg"
        data-testid="filter-dropdown"
      >
        <div className="p-4 space-y-4">
          {filters.map((filter) => (
            <div key={filter.key}>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {filter.label}
              </label>
              <div className="space-y-1">
                {filter.options.map((option) => (
                  <button
                    key={option}
                    type="button"
                    className="block w-full text-left px-2 py-1 text-sm hover:bg-gray-100 rounded"
                    onClick={() => handleFilterChange(filter.key, option)}
                  >
                    {option}
                  </button>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  };

  // Render categories
  const renderCategories = () => {
    if (categories.length === 0) return null;

    return (
      <div
        className="flex items-center space-x-1 mb-2"
        data-testid="category-selector"
      >
        {categories.map((category) => (
          <button
            key={category}
            className={cn(
              "px-3 py-1 text-sm rounded-full border transition-colors",
              selectedCategory === category
                ? "bg-blue-500 text-white border-blue-500"
                : "bg-white text-gray-700 border-gray-300 hover:bg-gray-50",
            )}
            onClick={() => onCategoryChange?.(category)}
          >
            {category}
          </button>
        ))}
      </div>
    );
  };

  // Render search scopes
  const renderSearchScopes = () => {
    if (searchScopes.length === 0) return null;

    return (
      <div
        className="flex items-center space-x-1 mb-2"
        data-testid="scope-selector"
      >
        {searchScopes.map((scope) => (
          <button
            key={scope}
            className={cn(
              "px-2 py-1 text-xs rounded border transition-colors",
              selectedScope === scope
                ? "bg-green-500 text-white border-green-500"
                : "bg-white text-gray-600 border-gray-300 hover:bg-gray-50",
            )}
            onClick={() => onScopeChange?.(scope)}
          >
            {scope}
          </button>
        ))}
      </div>
    );
  };

  // Render shortcuts hint
  const renderShortcuts = () => {
    if (shortcuts.length === 0) return null;

    return (
      <div className="mt-2 text-xs text-gray-500" data-testid="shortcuts-hint">
        {shortcuts.map((shortcut) => (
          <div key={shortcut.key} className="flex justify-between">
            <span>{shortcut.description}</span>
            <kbd className="px-1 bg-gray-100 rounded">{shortcut.key}</kbd>
          </div>
        ))}
      </div>
    );
  };

  return (
    <div
      ref={containerRef}
      className={cn(
        "relative",
        sizeClasses[size],
        themeClasses[theme],
        disabled && "disabled opacity-50",
        className,
      )}
      data-testid={dataTestId}
      data-category={dataCategory}
      data-id={dataId}
      {...props}
    >
      {renderCategories()}
      {renderSearchScopes()}

      <div className="relative">
        <div
          className={cn(
            "flex items-center border rounded-lg",
            sizeClasses[size],
            themeClasses[theme],
            "focus-within:ring-2 focus-within:ring-blue-500",
          )}
        >
          {/* Search Icon */}
          <div className="pl-3 flex-shrink-0" data-testid="search-icon">
            {loading ? (
              <div
                className="w-5 h-5 border-2 border-gray-300 border-t-blue-500 rounded-full animate-spin"
                data-testid="search-loading"
              />
            ) : (
              <svg
                className="w-5 h-5 text-gray-400"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
                />
              </svg>
            )}
          </div>

          {/* Input */}
          <input
            ref={inputRef}
            type="text"
            value={inputValue}
            placeholder={placeholder}
            disabled={disabled || loading}
            readOnly={readonly}
            className="flex-1 px-3 py-2 bg-transparent border-none outline-none"
            onChange={handleInputChange}
            onFocus={handleInputFocus}
            onBlur={handleInputBlur}
            onKeyDown={handleKeyDown}
            data-testid="searchbox-input"
          />

          {/* Clear Button */}
          {clearable && inputValue && (
            <button
              type="button"
              onClick={handleClear}
              className="p-1 text-gray-400 hover:text-gray-600"
              data-testid="clear-button"
            >
              <svg
                className="w-4 h-4"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M6 18L18 6M6 6l12 12"
                />
              </svg>
            </button>
          )}

          {/* Voice Search Button */}
          {voiceSearch && (
            <button
              type="button"
              onClick={onVoiceSearch}
              className="p-1 text-gray-400 hover:text-gray-600"
              data-testid="voice-search-button"
            >
              <svg
                className="w-4 h-4"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z"
                />
              </svg>
            </button>
          )}

          {/* Filter Button */}
          {filters.length > 0 && (
            <button
              type="button"
              onClick={() => setShowFilters(!showFilters)}
              className="p-1 text-gray-400 hover:text-gray-600"
              data-testid="filter-button"
            >
              <svg
                className="w-4 h-4"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z"
                />
              </svg>
            </button>
          )}

          {/* Advanced Search Button */}
          {advancedSearch && (
            <button
              type="button"
              onClick={() => setShowAdvanced(true)}
              className="p-1 text-gray-400 hover:text-gray-600"
              data-testid="advanced-search-button"
            >
              <svg
                className="w-4 h-4"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 100 4m0-4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 100 4m0-4v2m0-6V4"
                />
              </svg>
            </button>
          )}

          {/* Search Button */}
          {showSearchButton && (
            <button
              type="button"
              onClick={handleSearch}
              className="px-3 py-1 bg-blue-500 text-white rounded-r-lg hover:bg-blue-600 transition-colors"
              data-testid="search-button"
            >
              Search
            </button>
          )}
        </div>

        {renderSuggestions()}
        {renderFilterDropdown()}
      </div>

      {renderActiveFilters()}
      {renderShortcuts()}

      {/* Advanced Search Modal */}
      {showAdvanced && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div
            className="bg-white p-6 rounded-lg shadow-lg w-96"
            data-testid="advanced-search-modal"
          >
            <h3 className="text-lg font-semibold mb-4">Advanced Search</h3>
            <div className="space-y-4">
              <input
                type="text"
                placeholder="Search terms..."
                className="w-full px-3 py-2 border border-gray-300 rounded-md"
              />
              <div className="flex gap-2">
                <button
                  className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
                  onClick={() => setShowAdvanced(false)}
                >
                  Search
                </button>
                <button
                  className="px-4 py-2 bg-gray-500 text-white rounded hover:bg-gray-600"
                  onClick={() => setShowAdvanced(false)}
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default SearchBox;
