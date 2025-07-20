import React from 'react'
import { cn } from '../../lib/utils'
import { ChevronDown, ChevronUp, Check, X, AlertCircle } from 'lucide-react'

export interface SelectOption {
  value: string
  label: string
  disabled?: boolean
}

export interface SelectProps extends Omit<React.SelectHTMLAttributes<HTMLSelectElement>, 'size' | 'value' | 'onChange'> {
  variant?: 'default' | 'filled' | 'outline'
  size?: 'sm' | 'md' | 'lg'
  options: SelectOption[]
  value?: string | string[]
  onChange?: (value: string | string[]) => void
  placeholder?: string
  error?: boolean
  errorMessage?: string
  label?: string
  helperText?: string
  loading?: boolean
  searchable?: boolean
  multiple?: boolean
  clearable?: boolean
}

const Select = React.forwardRef<HTMLDivElement, SelectProps>(
  ({
    className,
    variant = 'default',
    size = 'md',
    options = [],
    value,
    onChange,
    placeholder = 'Select option...',
    error = false,
    errorMessage,
    label,
    helperText,
    loading = false,
    searchable = false,
    multiple = false,
    clearable = false,
    disabled = false,
    id,
    name,
    ...props
  }, ref) => {
    const [isOpen, setIsOpen] = React.useState(false)
    const [searchTerm, setSearchTerm] = React.useState('')
    const [focusedIndex, setFocusedIndex] = React.useState(-1)
    const generatedId = React.useId()
    const selectId = id || generatedId
    const dropdownRef = React.useRef<HTMLDivElement>(null)
    const searchInputRef = React.useRef<HTMLInputElement>(null)

    // Filter options based on search term
    const filteredOptions = React.useMemo(() => {
      if (!searchable || !searchTerm) return options
      return options.filter(option => 
        option.label.toLowerCase().includes(searchTerm.toLowerCase())
      )
    }, [options, searchTerm, searchable])

    // Get selected option(s)
    const selectedOptions = React.useMemo(() => {
      if (!value) return []
      const values = Array.isArray(value) ? value : [value]
      return options.filter(option => values.includes(option.value))
    }, [value, options])

    // Close dropdown when clicking outside
    React.useEffect(() => {
      const handleClickOutside = (event: MouseEvent) => {
        if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
          setIsOpen(false)
          setSearchTerm('')
          setFocusedIndex(-1)
        }
      }

      document.addEventListener('mousedown', handleClickOutside)
      return () => document.removeEventListener('mousedown', handleClickOutside)
    }, [])

    // Handle keyboard navigation
    React.useEffect(() => {
      if (!isOpen) return

      const handleKeyDown = (event: KeyboardEvent) => {
        switch (event.key) {
          case 'ArrowDown':
            event.preventDefault()
            setFocusedIndex(prev => 
              prev < filteredOptions.length - 1 ? prev + 1 : 0
            )
            break
          case 'ArrowUp':
            event.preventDefault()
            setFocusedIndex(prev => 
              prev > 0 ? prev - 1 : filteredOptions.length - 1
            )
            break
          case 'Enter':
            event.preventDefault()
            if (focusedIndex >= 0 && focusedIndex < filteredOptions.length) {
              handleOptionSelect(filteredOptions[focusedIndex])
            }
            break
          case 'Escape':
            setIsOpen(false)
            setSearchTerm('')
            setFocusedIndex(-1)
            break
        }
      }

      document.addEventListener('keydown', handleKeyDown)
      return () => document.removeEventListener('keydown', handleKeyDown)
    }, [isOpen, focusedIndex, filteredOptions])

    // Focus search input when opened
    React.useEffect(() => {
      if (isOpen && searchable && searchInputRef.current) {
        searchInputRef.current.focus()
      }
    }, [isOpen, searchable])

    const handleOptionSelect = (option: SelectOption) => {
      if (option.disabled || loading) return

      let newValue: string | string[]

      if (multiple) {
        const currentValues = Array.isArray(value) ? value : value ? [value] : []
        if (currentValues.includes(option.value)) {
          newValue = currentValues.filter(v => v !== option.value)
        } else {
          newValue = [...currentValues, option.value]
        }
      } else {
        newValue = option.value
        setIsOpen(false)
        setSearchTerm('')
      }

      onChange?.(newValue)
      setFocusedIndex(-1)
    }

    const handleClear = (e: React.MouseEvent) => {
      e.stopPropagation()
      onChange?.(multiple ? [] : '')
      setSearchTerm('')
    }

    const handleToggle = () => {
      if (disabled || loading) return
      setIsOpen(!isOpen)
      setFocusedIndex(-1)
    }

    const baseStyles = [
      'relative flex w-full items-center justify-between rounded-md border transition-colors duration-200',
      'focus-within:outline-none focus-within:ring-2 focus-within:ring-offset-2',
      'disabled:cursor-not-allowed disabled:opacity-50'
    ]

    const variants = {
      default: [
        'border-gray-300 bg-white',
        'focus-within:border-blue-500 focus-within:ring-blue-500/20',
        error && 'border-red-500 focus-within:border-red-500 focus-within:ring-red-500/20'
      ],
      filled: [
        'border-transparent bg-gray-100',
        'focus-within:bg-white focus-within:border-blue-500 focus-within:ring-blue-500/20',
        error && 'bg-red-50 border-red-200 focus-within:border-red-500 focus-within:ring-red-500/20'
      ],
      outline: [
        'border-gray-200 bg-transparent',
        'focus-within:border-blue-500 focus-within:ring-blue-500/20',
        error && 'border-red-500 focus-within:border-red-500 focus-within:ring-red-500/20'
      ]
    }

    const sizes = {
      sm: {
        container: 'h-8 px-3 text-sm',
        dropdown: 'mt-1',
        option: 'px-3 py-1.5 text-sm'
      },
      md: {
        container: 'h-10 px-3 text-base',
        dropdown: 'mt-2',
        option: 'px-3 py-2 text-base'
      },
      lg: {
        container: 'h-12 px-4 text-lg',
        dropdown: 'mt-2',
        option: 'px-4 py-2.5 text-lg'
      }
    }

    const containerClasses = cn(
      baseStyles,
      variants[variant],
      sizes[size].container,
      isOpen && 'ring-2 ring-blue-500/20',
      disabled && 'cursor-not-allowed',
      className
    )

    const renderDisplayValue = () => {
      if (selectedOptions.length === 0) {
        return <span className="text-gray-500">{placeholder}</span>
      }

      if (multiple) {
        return (
          <div className="flex flex-wrap gap-1 max-w-full">
            {selectedOptions.map(option => (
              <span
                key={option.value}
                className="inline-flex items-center gap-1 px-2 py-0.5 text-xs bg-blue-100 text-blue-800 rounded"
              >
                {option.label}
                <button
                  type="button"
                  onClick={(e) => {
                    e.stopPropagation()
                    handleOptionSelect(option)
                  }}
                  className="hover:bg-blue-200 rounded"
                >
                  <X className="h-3 w-3" />
                </button>
              </span>
            ))}
          </div>
        )
      }

      return <span>{selectedOptions[0].label}</span>
    }

    return (
      <div className="space-y-1">
        {label && (
          <label
            htmlFor={selectId}
            className={cn(
              'block text-sm font-medium',
              error ? 'text-red-700' : 'text-gray-700'
            )}
          >
            {label}
          </label>
        )}

        <div ref={dropdownRef} className="relative">
          <div
            ref={ref}
            id={selectId}
            className={containerClasses}
            onClick={handleToggle}
            role="combobox"
            aria-expanded={isOpen}
            aria-haspopup="listbox"
            aria-labelledby={label ? `${selectId}-label` : undefined}
            tabIndex={disabled ? -1 : 0}
          >
            <div className="flex-1 min-w-0">
              {renderDisplayValue()}
            </div>

            <div className="flex items-center gap-1">
              {loading && (
                <div className="h-4 w-4 animate-spin rounded-full border-2 border-gray-300 border-t-blue-600" />
              )}
              
              {clearable && selectedOptions.length > 0 && !loading && (
                <button
                  type="button"
                  onClick={handleClear}
                  className="p-0.5 hover:bg-gray-100 rounded"
                  tabIndex={-1}
                >
                  <X className="h-4 w-4 text-gray-500" />
                </button>
              )}

              <div className="text-gray-500">
                {isOpen ? (
                  <ChevronUp className="h-4 w-4" />
                ) : (
                  <ChevronDown className="h-4 w-4" />
                )}
              </div>
            </div>
          </div>

          {isOpen && (
            <div className={cn(
              'absolute z-50 w-full bg-white border border-gray-200 rounded-md shadow-lg',
              sizes[size].dropdown
            )}>
              {searchable && (
                <div className="p-2 border-b border-gray-200">
                  <input
                    ref={searchInputRef}
                    type="text"
                    placeholder="Search options..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="w-full px-2 py-1 text-sm border border-gray-300 rounded focus:outline-none focus:border-blue-500"
                  />
                </div>
              )}

              <div className="max-h-60 overflow-y-auto">
                {filteredOptions.length === 0 ? (
                  <div className={cn('text-gray-500 text-center', sizes[size].option)}>
                    No options found
                  </div>
                ) : (
                  filteredOptions.map((option, index) => {
                    const isSelected = selectedOptions.some(selected => selected.value === option.value)
                    const isFocused = index === focusedIndex

                    return (
                      <div
                        key={option.value}
                        className={cn(
                          'flex items-center justify-between cursor-pointer transition-colors',
                          sizes[size].option,
                          isFocused && 'bg-blue-50',
                          isSelected && 'bg-blue-100',
                          option.disabled && 'opacity-50 cursor-not-allowed'
                        )}
                        onClick={() => handleOptionSelect(option)}
                        role="option"
                        aria-selected={isSelected}
                      >
                        <span>{option.label}</span>
                        {isSelected && (
                          <Check className="h-4 w-4 text-blue-600" />
                        )}
                      </div>
                    )
                  })
                )}
              </div>
            </div>
          )}

          {/* Hidden native select for form submission */}
          <select
            name={name}
            value={multiple ? (Array.isArray(value) ? value : []) : (value || '')}
            onChange={() => {}} // Controlled by our custom logic
            multiple={multiple}
            style={{ display: 'none' }}
            tabIndex={-1}
            {...props}
          >
            {selectedOptions.map(option => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>

          {error && errorMessage && (
            <div className="flex items-center gap-1 mt-1">
              <AlertCircle className="h-4 w-4 text-red-500" />
              <span className="text-sm text-red-600">{errorMessage}</span>
            </div>
          )}
        </div>

        {helperText && !error && (
          <p className="text-sm text-gray-600">{helperText}</p>
        )}
      </div>
    )
  }
)

Select.displayName = 'Select'

export default Select