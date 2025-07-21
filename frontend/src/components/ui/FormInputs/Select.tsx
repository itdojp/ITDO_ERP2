import React from 'react'
import { cn } from '../../../lib/utils'
import { ChevronDown, Search, X, Check, AlertCircle } from 'lucide-react'

export interface SelectOption {
  value: string
  label: string
  disabled?: boolean
  group?: string
}

export interface SelectProps {
  options: SelectOption[]
  value?: string | string[]
  onChange?: (value: string | string[]) => void
  placeholder?: string
  label?: string
  error?: boolean
  errorMessage?: string
  helperText?: string
  size?: 'sm' | 'md' | 'lg'
  variant?: 'default' | 'filled' | 'outline'
  multiple?: boolean
  searchable?: boolean
  clearable?: boolean
  disabled?: boolean
  loading?: boolean
  maxHeight?: number
  onSearch?: (query: string) => void
  emptyMessage?: string
  groupBy?: (option: SelectOption) => string
  className?: string
  id?: string
}

const Select = React.memo(React.forwardRef<HTMLDivElement, SelectProps>(
  ({
    options = [],
    value,
    onChange,
    placeholder = 'Select an option...',
    label,
    error = false,
    errorMessage,
    helperText,
    size = 'md',
    variant = 'default',
    multiple = false,
    searchable = false,
    clearable = false,
    disabled = false,
    loading = false,
    maxHeight = 200,
    onSearch,
    emptyMessage = 'No options found',
    groupBy,
    className,
    id,
  }, ref) => {
    const [isOpen, setIsOpen] = React.useState(false)
    const [searchQuery, setSearchQuery] = React.useState('')
    const [focusedIndex, setFocusedIndex] = React.useState(-1)
    const generatedId = React.useId()
    const selectId = id || generatedId
    
    const containerRef = React.useRef<HTMLDivElement>(null)
    const searchInputRef = React.useRef<HTMLInputElement>(null)
    const optionsRef = React.useRef<HTMLDivElement>(null)

    const selectedValues = React.useMemo(() => {
      if (multiple) {
        return Array.isArray(value) ? value : []
      }
      return typeof value === 'string' ? [value] : []
    }, [value, multiple])

    const filteredOptions = React.useMemo(() => {
      if (!searchQuery.trim()) return options
      return options.filter(option =>
        option.label.toLowerCase().includes(searchQuery.toLowerCase()) ||
        option.value.toLowerCase().includes(searchQuery.toLowerCase())
      )
    }, [options, searchQuery])

    const groupedOptions = React.useMemo(() => {
      if (!groupBy) return { '': filteredOptions }
      
      return filteredOptions.reduce((groups, option) => {
        const group = groupBy(option)
        if (!groups[group]) groups[group] = []
        groups[group].push(option)
        return groups
      }, {} as Record<string, SelectOption[]>)
    }, [filteredOptions, groupBy])

    const selectedOption = React.useMemo(() => {
      if (multiple) return null
      return options.find(opt => opt.value === value)
    }, [options, value, multiple])

    const selectedOptions = React.useMemo(() => {
      if (!multiple) return []
      return options.filter(opt => selectedValues.includes(opt.value))
    }, [options, selectedValues, multiple])

    React.useEffect(() => {
      if (onSearch) {
        onSearch(searchQuery)
      }
    }, [searchQuery, onSearch])

    React.useEffect(() => {
      const handleClickOutside = (event: MouseEvent) => {
        if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
          setIsOpen(false)
          setSearchQuery('')
          setFocusedIndex(-1)
        }
      }

      if (isOpen) {
        document.addEventListener('mousedown', handleClickOutside)
        if (searchable && searchInputRef.current) {
          searchInputRef.current.focus()
        }
      }

      return () => {
        document.removeEventListener('mousedown', handleClickOutside)
      }
    }, [isOpen, searchable])

    const handleSelect = (option: SelectOption) => {
      if (option.disabled) return

      if (multiple) {
        const newValues = selectedValues.includes(option.value)
          ? selectedValues.filter(v => v !== option.value)
          : [...selectedValues, option.value]
        onChange?.(newValues)
      } else {
        onChange?.(option.value)
        setIsOpen(false)
        setSearchQuery('')
      }
    }

    const handleClear = (e: React.MouseEvent) => {
      e.stopPropagation()
      onChange?.(multiple ? [] : '')
    }

    const handleKeyDown = (e: React.KeyboardEvent) => {
      if (disabled) return

      switch (e.key) {
        case 'Enter':
        case ' ':
          e.preventDefault()
          if (!isOpen) {
            setIsOpen(true)
          } else if (focusedIndex >= 0 && filteredOptions[focusedIndex]) {
            handleSelect(filteredOptions[focusedIndex])
          }
          break
        case 'Escape':
          setIsOpen(false)
          setSearchQuery('')
          setFocusedIndex(-1)
          break
        case 'ArrowDown':
          e.preventDefault()
          if (!isOpen) {
            setIsOpen(true)
          } else {
            setFocusedIndex(prev => 
              prev < filteredOptions.length - 1 ? prev + 1 : 0
            )
          }
          break
        case 'ArrowUp':
          e.preventDefault()
          if (isOpen) {
            setFocusedIndex(prev => 
              prev > 0 ? prev - 1 : filteredOptions.length - 1
            )
          }
          break
      }
    }

    const sizes = {
      sm: {
        container: 'h-8',
        text: 'text-sm',
        padding: 'px-3 py-1',
        icon: 'h-4 w-4'
      },
      md: {
        container: 'h-10',
        text: 'text-base',
        padding: 'px-3 py-2',
        icon: 'h-5 w-5'
      },
      lg: {
        container: 'h-12',
        text: 'text-lg',
        padding: 'px-4 py-3',
        icon: 'h-6 w-6'
      }
    }

    const variants = {
      default: [
        'border border-gray-300 bg-white',
        'focus-within:border-blue-500 focus-within:ring-2 focus-within:ring-blue-500/20',
        error && 'border-red-500 focus-within:border-red-500 focus-within:ring-red-500/20'
      ],
      filled: [
        'border border-transparent bg-gray-100',
        'focus-within:bg-white focus-within:border-blue-500 focus-within:ring-2 focus-within:ring-blue-500/20',
        error && 'bg-red-50 border-red-200 focus-within:border-red-500 focus-within:ring-red-500/20'
      ],
      outline: [
        'border-2 border-gray-200 bg-transparent',
        'focus-within:border-blue-500 focus-within:ring-2 focus-within:ring-blue-500/20',
        error && 'border-red-500 focus-within:border-red-500 focus-within:ring-red-500/20'
      ]
    }

    const containerClasses = cn(
      'relative w-full rounded-md transition-all duration-200 cursor-pointer',
      'focus-within:outline-none',
      'disabled:cursor-not-allowed disabled:opacity-50',
      variants[variant],
      sizes[size].container,
      className
    )

    const renderSelectedContent = () => {
      if (multiple && selectedOptions.length > 0) {
        if (selectedOptions.length === 1) {
          return selectedOptions[0].label
        }
        return `${selectedOptions.length} selected`
      }

      if (!multiple && selectedOption) {
        return selectedOption.label
      }

      return placeholder
    }

    const renderOption = (option: SelectOption, index: number) => {
      const isSelected = selectedValues.includes(option.value)
      const isFocused = index === focusedIndex

      return (
        <div
          key={option.value}
          className={cn(
            'flex items-center justify-between px-3 py-2 cursor-pointer transition-colors',
            sizes[size].text,
            option.disabled && 'opacity-50 cursor-not-allowed',
            isFocused && 'bg-blue-100',
            isSelected && 'bg-blue-50 text-blue-700',
            !option.disabled && !isFocused && !isSelected && 'hover:bg-gray-100'
          )}
          onClick={() => handleSelect(option)}
        >
          <span className="flex-1">{option.label}</span>
          {isSelected && (
            <Check className={cn('text-blue-600', sizes[size].icon)} />
          )}
        </div>
      )
    }

    return (
      <div className="w-full">
        {label && (
          <label
            htmlFor={selectId}
            className={cn(
              'block text-sm font-medium mb-1',
              error ? 'text-red-700' : 'text-gray-700'
            )}
          >
            {label}
          </label>
        )}

        <div ref={containerRef} className="relative">
          <div
            ref={ref}
            id={selectId}
            className={containerClasses}
            onClick={() => !disabled && setIsOpen(!isOpen)}
            onKeyDown={handleKeyDown}
            tabIndex={disabled ? -1 : 0}
            role="combobox"
            aria-expanded={isOpen}
            aria-haspopup="listbox"
            aria-invalid={error}
          >
            <div className={cn('flex items-center justify-between', sizes[size].padding)}>
              <span className={cn(
                'flex-1 truncate',
                sizes[size].text,
                (!selectedOption && !selectedOptions.length) && 'text-gray-500'
              )}>
                {renderSelectedContent()}
              </span>
              
              <div className="flex items-center gap-2">
                {clearable && (selectedOption || selectedOptions.length > 0) && (
                  <button
                    type="button"
                    onClick={handleClear}
                    className={cn(
                      'text-gray-400 hover:text-gray-600 focus:outline-none',
                      sizes[size].icon
                    )}
                    tabIndex={-1}
                  >
                    <X className={sizes[size].icon} />
                  </button>
                )}
                
                {loading ? (
                  <div className={cn(
                    'animate-spin rounded-full border-2 border-gray-300 border-t-blue-600',
                    sizes[size].icon
                  )} />
                ) : (
                  <ChevronDown 
                    className={cn(
                      'text-gray-400 transition-transform',
                      sizes[size].icon,
                      isOpen && 'rotate-180'
                    )} 
                  />
                )}
              </div>
            </div>
          </div>

          {isOpen && (
            <div 
              ref={optionsRef}
              className={cn(
                'absolute z-50 w-full mt-1 bg-white border border-gray-200 rounded-md shadow-lg',
                'max-h-60 overflow-auto'
              )}
              style={{ maxHeight: `${maxHeight}px` }}
            >
              {searchable && (
                <div className="p-2 border-b border-gray-100">
                  <div className="relative">
                    <Search className={cn(
                      'absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400',
                      sizes[size].icon
                    )} />
                    <input
                      ref={searchInputRef}
                      type="text"
                      className={cn(
                        'w-full pl-10 pr-3 py-2 border border-gray-200 rounded-md',
                        'focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500',
                        sizes[size].text
                      )}
                      placeholder="Search options..."
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                    />
                  </div>
                </div>
              )}

              <div className="max-h-48 overflow-auto">
                {Object.keys(groupedOptions).length === 0 ? (
                  <div className={cn(
                    'px-3 py-2 text-gray-500 text-center',
                    sizes[size].text
                  )}>
                    {emptyMessage}
                  </div>
                ) : (
                  Object.entries(groupedOptions).map(([groupName, groupOptions]) => (
                    <div key={groupName}>
                      {groupName && (
                        <div className="px-3 py-2 text-xs font-semibold text-gray-500 uppercase bg-gray-50">
                          {groupName}
                        </div>
                      )}
                      {groupOptions.map((option, index) => renderOption(option, index))}
                    </div>
                  ))
                )}
              </div>
            </div>
          )}
        </div>

        {error && errorMessage && (
          <div className="flex items-center gap-1 mt-1">
            <AlertCircle className="h-4 w-4 text-red-500" />
            <span className="text-sm text-red-600">{errorMessage}</span>
          </div>
        )}
        
        {helperText && !error && (
          <p className="text-sm text-gray-600 mt-1">{helperText}</p>
        )}
      </div>
    )
  }
))

Select.displayName = 'Select'

export default Select