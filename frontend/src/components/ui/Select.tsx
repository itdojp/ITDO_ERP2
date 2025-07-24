import React, {
  useState,
  useRef,
  useEffect,
  useCallback,
  forwardRef,
} from "react";

export interface SelectOption {
  value: string | number;
  label: string;
  disabled?: boolean;
  group?: string;
  icon?: React.ReactNode;
  description?: string;
}

interface SelectProps {
  options: SelectOption[];
  value?: string | number | (string | number)[];
  defaultValue?: string | number | (string | number)[];
  placeholder?: string;
  multiple?: boolean;
  searchable?: boolean;
  clearable?: boolean;
  disabled?: boolean;
  loading?: boolean;
  size?: "sm" | "md" | "lg";
  variant?: "default" | "filled" | "outlined";
  status?: "default" | "error" | "warning" | "success";
  maxTagCount?: number;
  allowCreate?: boolean;
  filterOption?: (inputValue: string, option: SelectOption) => boolean;
  onSearch?: (value: string) => void;
  onChange?: (
    value: string | number | (string | number)[],
    option?: SelectOption | SelectOption[],
  ) => void;
  onFocus?: (e: React.FocusEvent) => void;
  onBlur?: (e: React.FocusEvent) => void;
  onDropdownVisibleChange?: (visible: boolean) => void;
  className?: string;
  dropdownClassName?: string;
  optionClassName?: string;
  tagClassName?: string;
  notFoundContent?: React.ReactNode;
  dropdownMatchSelectWidth?: boolean;
  virtual?: boolean;
  showArrow?: boolean;
  bordered?: boolean;
}

export const Select = forwardRef<HTMLDivElement, SelectProps>(
  (
    {
      options,
      value,
      defaultValue,
      placeholder = "Select an option",
      multiple = false,
      searchable = false,
      clearable = false,
      disabled = false,
      loading = false,
      size = "md",
      variant = "default",
      status = "default",
      maxTagCount,
      allowCreate = false,
      filterOption,
      onSearch,
      onChange,
      onFocus,
      onBlur,
      onDropdownVisibleChange,
      className = "",
      dropdownClassName = "",
      optionClassName = "",
      tagClassName = "",
      notFoundContent = "No data",
      dropdownMatchSelectWidth = true,
      virtual = false,
      showArrow = true,
      bordered = true,
    },
    ref,
  ) => {
    const [isOpen, setIsOpen] = useState(false);
    const [searchValue, setSearchValue] = useState("");
    const [internalValue, setInternalValue] = useState(() => {
      if (defaultValue !== undefined) return defaultValue;
      return multiple ? [] : "";
    });
    const [highlightedIndex, setHighlightedIndex] = useState(0);

    const selectRef = useRef<HTMLDivElement>(null);
    const dropdownRef = useRef<HTMLDivElement>(null);
    const searchInputRef = useRef<HTMLInputElement>(null);

    const currentValue = value !== undefined ? value : internalValue;
    const selectedValues = Array.isArray(currentValue)
      ? currentValue
      : [currentValue].filter((v) => v !== "");

    const getSizeClasses = () => {
      const sizeMap = {
        sm: "px-2 py-1 text-sm min-h-[32px]",
        md: "px-3 py-2 text-sm min-h-[40px]",
        lg: "px-4 py-3 text-base min-h-[48px]",
      };
      return sizeMap[size];
    };

    const getVariantClasses = () => {
      const variantMap = {
        default: "bg-white border border-gray-300",
        filled: "bg-gray-50 border-0",
        outlined: "bg-transparent border-2 border-gray-300",
      };
      return variantMap[variant];
    };

    const getStatusClasses = () => {
      if (disabled) return "border-gray-200 bg-gray-50 cursor-not-allowed";

      const statusMap = {
        default:
          "focus-within:border-blue-500 focus-within:ring-1 focus-within:ring-blue-500",
        error:
          "border-red-500 focus-within:border-red-500 focus-within:ring-red-500",
        warning:
          "border-yellow-500 focus-within:border-yellow-500 focus-within:ring-yellow-500",
        success:
          "border-green-500 focus-within:border-green-500 focus-within:ring-green-500",
      };
      return statusMap[status];
    };

    const filteredOptions = useCallback(() => {
      let filtered = options;

      if (searchValue && searchable) {
        filtered = options.filter((option) => {
          if (filterOption) {
            return filterOption(searchValue, option);
          }
          return option.label.toLowerCase().includes(searchValue.toLowerCase());
        });
      }

      // Add create option if allowCreate is true and search value doesn't match any option
      if (
        allowCreate &&
        searchValue &&
        !filtered.some(
          (opt) => opt.label.toLowerCase() === searchValue.toLowerCase(),
        )
      ) {
        filtered = [
          {
            value: searchValue,
            label: `Create "${searchValue}"`,
            group: "__create__",
          },
          ...filtered,
        ];
      }

      return filtered;
    }, [options, searchValue, searchable, filterOption, allowCreate]);

    const groupedOptions = useCallback(() => {
      const filtered = filteredOptions();
      const grouped: { [key: string]: SelectOption[] } = {};
      const ungrouped: SelectOption[] = [];

      filtered.forEach((option) => {
        if (option.group) {
          if (!grouped[option.group]) grouped[option.group] = [];
          grouped[option.group].push(option);
        } else {
          ungrouped.push(option);
        }
      });

      return { grouped, ungrouped };
    }, [filteredOptions]);

    const getSelectedOption = (
      val: string | number,
    ): SelectOption | undefined => {
      return options.find((opt) => opt.value === val);
    };

    const handleSelect = (option: SelectOption) => {
      if (option.disabled) return;

      let newValue: string | number | (string | number)[];
      let newOption: SelectOption | SelectOption[];

      if (multiple) {
        const currentArray = Array.isArray(currentValue) ? currentValue : [];
        const isSelected = currentArray.includes(option.value);

        if (isSelected) {
          newValue = currentArray.filter((v) => v !== option.value);
          newOption = options.filter((opt) => newValue.includes(opt.value));
        } else {
          newValue = [...currentArray, option.value];
          newOption = options.filter((opt) => newValue.includes(opt.value));
        }
      } else {
        newValue = option.value;
        newOption = option;
        setIsOpen(false);
        setSearchValue("");
      }

      if (value === undefined) {
        setInternalValue(newValue);
      }

      onChange?.(newValue, newOption);
    };

    const handleClear = (e: React.MouseEvent) => {
      e.stopPropagation();
      const newValue = multiple ? [] : "";

      if (value === undefined) {
        setInternalValue(newValue);
      }

      onChange?.(newValue, multiple ? [] : undefined);
      setSearchValue("");
    };

    const handleRemoveTag = (
      optionValue: string | number,
      e: React.MouseEvent,
    ) => {
      e.stopPropagation();
      if (!multiple) return;

      const currentArray = Array.isArray(currentValue) ? currentValue : [];
      const newValue = currentArray.filter((v) => v !== optionValue);
      const newOption = options.filter((opt) => newValue.includes(opt.value));

      if (value === undefined) {
        setInternalValue(newValue);
      }

      onChange?.(newValue, newOption);
    };

    const handleKeyDown = (e: React.KeyboardEvent) => {
      const filtered = filteredOptions();

      switch (e.key) {
        case "ArrowDown":
          e.preventDefault();
          if (!isOpen) {
            setIsOpen(true);
          } else {
            setHighlightedIndex((prev) => (prev + 1) % filtered.length);
          }
          break;
        case "ArrowUp":
          e.preventDefault();
          if (isOpen) {
            setHighlightedIndex((prev) =>
              prev > 0 ? prev - 1 : filtered.length - 1,
            );
          }
          break;
        case "Enter":
          e.preventDefault();
          if (isOpen && filtered[highlightedIndex]) {
            handleSelect(filtered[highlightedIndex]);
          } else if (!isOpen) {
            setIsOpen(true);
          }
          break;
        case "Escape":
          if (isOpen) {
            setIsOpen(false);
            setSearchValue("");
          }
          break;
        case "Tab":
          if (isOpen) {
            setIsOpen(false);
          }
          break;
      }
    };

    const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
      const newValue = e.target.value;
      setSearchValue(newValue);
      setHighlightedIndex(0);
      onSearch?.(newValue);

      if (!isOpen && newValue) {
        setIsOpen(true);
      }
    };

    const toggleDropdown = () => {
      if (disabled) return;

      const newOpen = !isOpen;
      setIsOpen(newOpen);
      onDropdownVisibleChange?.(newOpen);

      if (newOpen && searchable) {
        setTimeout(() => searchInputRef.current?.focus(), 0);
      }
    };

    // Close dropdown when clicking outside
    useEffect(() => {
      const handleClickOutside = (event: MouseEvent) => {
        if (
          selectRef.current &&
          dropdownRef.current &&
          !selectRef.current.contains(event.target as Node) &&
          !dropdownRef.current.contains(event.target as Node)
        ) {
          setIsOpen(false);
          setSearchValue("");
        }
      };

      document.addEventListener("mousedown", handleClickOutside);
      return () =>
        document.removeEventListener("mousedown", handleClickOutside);
    }, []);

    const renderSelectedContent = () => {
      if (loading) {
        return (
          <div className="flex items-center gap-2 text-gray-500">
            <div className="w-4 h-4 border-2 border-gray-300 border-t-blue-500 rounded-full animate-spin" />
            <span>Loading...</span>
          </div>
        );
      }

      if (searchable && isOpen) {
        return (
          <input
            ref={searchInputRef}
            type="text"
            value={searchValue}
            onChange={handleSearchChange}
            className="flex-1 outline-none bg-transparent"
            placeholder={selectedValues.length === 0 ? placeholder : ""}
          />
        );
      }

      if (selectedValues.length === 0) {
        return <span className="text-gray-400">{placeholder}</span>;
      }

      if (multiple) {
        const displayValues =
          maxTagCount && selectedValues.length > maxTagCount
            ? selectedValues.slice(0, maxTagCount)
            : selectedValues;

        const remainingCount =
          selectedValues.length - (maxTagCount || selectedValues.length);

        return (
          <div className="flex flex-wrap gap-1 items-center">
            {displayValues.map((val) => {
              const option = getSelectedOption(val);
              return (
                <span
                  key={val}
                  className={`inline-flex items-center gap-1 px-2 py-0.5 bg-blue-100 text-blue-800 text-xs rounded ${tagClassName}`}
                >
                  {option?.label || val}
                  <button
                    type="button"
                    onClick={(e) => handleRemoveTag(val, e)}
                    className="hover:bg-blue-200 rounded p-0.5"
                  >
                    <svg
                      className="w-3 h-3"
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
                </span>
              );
            })}
            {remainingCount > 0 && (
              <span className="text-gray-500 text-xs">
                +{remainingCount} more
              </span>
            )}
          </div>
        );
      }

      const selectedOption = getSelectedOption(selectedValues[0]);
      return (
        <div className="flex items-center gap-2">
          {selectedOption?.icon && <span>{selectedOption.icon}</span>}
          <span>{selectedOption?.label || selectedValues[0]}</span>
        </div>
      );
    };

    const renderDropdown = () => {
      if (!isOpen) return null;

      const { grouped, ungrouped } = groupedOptions();
      const hasResults =
        ungrouped.length > 0 || Object.keys(grouped).length > 0;

      return (
        <div
          ref={dropdownRef}
          className={`
          absolute z-50 mt-1 bg-white border border-gray-200 rounded-md shadow-lg max-h-60 overflow-auto
          ${dropdownMatchSelectWidth ? "w-full" : "min-w-full"}
          ${dropdownClassName}
        `}
          style={{ top: "100%" }}
        >
          {!hasResults ? (
            <div className="px-3 py-2 text-gray-500 text-sm">
              {notFoundContent}
            </div>
          ) : (
            <>
              {ungrouped.map((option, index) => renderOption(option, index))}
              {Object.entries(grouped).map(([groupName, groupOptions]) => (
                <div key={groupName}>
                  {groupName !== "__create__" && (
                    <div className="px-3 py-1 text-xs font-semibold text-gray-500 bg-gray-50">
                      {groupName}
                    </div>
                  )}
                  {groupOptions.map((option, index) =>
                    renderOption(option, ungrouped.length + index),
                  )}
                </div>
              ))}
            </>
          )}
        </div>
      );
    };

    const renderOption = (option: SelectOption, index: number) => {
      const isSelected = selectedValues.includes(option.value);
      const isHighlighted = index === highlightedIndex;
      const isCreateOption = option.group === "__create__";

      return (
        <div
          key={`${option.value}-${index}`}
          onClick={() => handleSelect(option)}
          className={`
          px-3 py-2 cursor-pointer flex items-center justify-between transition-colors
          ${isHighlighted ? "bg-blue-50" : ""}
          ${isSelected ? "bg-blue-100 text-blue-800" : "hover:bg-gray-50"}
          ${option.disabled ? "opacity-50 cursor-not-allowed" : ""}
          ${isCreateOption ? "font-medium text-blue-600" : ""}
          ${optionClassName}
        `}
        >
          <div className="flex items-center gap-2 flex-1 min-w-0">
            {option.icon && !isCreateOption && (
              <span className="flex-shrink-0">{option.icon}</span>
            )}
            <div className="min-w-0 flex-1">
              <div className="truncate">{option.label}</div>
              {option.description && (
                <div className="text-xs text-gray-500 truncate">
                  {option.description}
                </div>
              )}
            </div>
          </div>
          {multiple && isSelected && (
            <svg
              className="w-4 h-4 text-blue-600 flex-shrink-0"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M5 13l4 4L19 7"
              />
            </svg>
          )}
        </div>
      );
    };

    const shouldShowClear = clearable && selectedValues.length > 0 && !disabled;

    return (
      <div
        ref={ref}
        className={`relative ${className}`}
        onFocus={onFocus}
        onBlur={onBlur}
      >
        <div
          ref={selectRef}
          onClick={toggleDropdown}
          onKeyDown={handleKeyDown}
          tabIndex={disabled ? -1 : 0}
          className={`
          flex items-center cursor-pointer transition-colors duration-200 rounded-md
          ${getSizeClasses()}
          ${getVariantClasses()}
          ${getStatusClasses()}
          ${bordered ? "" : "border-0"}
          ${disabled ? "opacity-50 cursor-not-allowed" : ""}
        `}
          role="combobox"
          aria-expanded={isOpen}
          aria-haspopup="listbox"
          aria-disabled={disabled}
        >
          <div className="flex-1 min-w-0">{renderSelectedContent()}</div>

          <div className="flex items-center gap-1 ml-2">
            {shouldShowClear && (
              <button
                type="button"
                onClick={handleClear}
                className="p-1 hover:bg-gray-100 rounded text-gray-400 hover:text-gray-600 transition-colors"
                tabIndex={-1}
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

            {showArrow && (
              <svg
                className={`w-4 h-4 text-gray-400 transition-transform duration-200 ${isOpen ? "rotate-180" : ""}`}
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M19 9l-7 7-7-7"
                />
              </svg>
            )}
          </div>
        </div>

        {renderDropdown()}
      </div>
    );
  },
);

Select.displayName = "Select";

export default Select;
