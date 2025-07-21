import React from 'react'
import { Search, Filter, X, ChevronDown, Calendar, Hash, Type, Toggle, List } from 'lucide-react'
import { cn } from '../../../lib/utils'
import { useAdvancedSearch, SearchFilter, SearchSort, FilterOperator } from '../../../hooks/useAdvancedSearch'

export interface AdvancedSearchProps {
  className?: string
  placeholder?: string
  onSearch?: (query: string, filters: SearchFilter[], sort: SearchSort[]) => void
  onResultSelect?: (result: any) => void
  showFilters?: boolean
  showSort?: boolean
  showFacets?: boolean
  availableFields?: FieldConfig[]
}

export interface FieldConfig {
  field: string
  label: string
  type: 'string' | 'number' | 'date' | 'boolean' | 'enum'
  operators?: FilterOperator[]
  options?: { value: any; label: string }[]
  sortable?: boolean
}

const DEFAULT_FIELDS: FieldConfig[] = [
  {
    field: 'title',
    label: 'Title',
    type: 'string',
    operators: [FilterOperator.CONTAINS, FilterOperator.EQUALS, FilterOperator.STARTS_WITH],
    sortable: true,
  },
  {
    field: 'status',
    label: 'Status',
    type: 'enum',
    operators: [FilterOperator.EQUALS, FilterOperator.IN],
    options: [
      { value: 'active', label: 'Active' },
      { value: 'inactive', label: 'Inactive' },
      { value: 'pending', label: 'Pending' },
    ],
    sortable: true,
  },
  {
    field: 'createdAt',
    label: 'Created Date',
    type: 'date',
    operators: [FilterOperator.GREATER_THAN, FilterOperator.LESS_THAN, FilterOperator.BETWEEN],
    sortable: true,
  },
  {
    field: 'priority',
    label: 'Priority',
    type: 'enum',
    operators: [FilterOperator.EQUALS, FilterOperator.IN],
    options: [
      { value: 'low', label: 'Low' },
      { value: 'medium', label: 'Medium' },
      { value: 'high', label: 'High' },
      { value: 'critical', label: 'Critical' },
    ],
    sortable: true,
  },
]

const OPERATOR_LABELS: Record<FilterOperator, string> = {
  [FilterOperator.EQUALS]: 'equals',
  [FilterOperator.NOT_EQUALS]: 'not equals',
  [FilterOperator.GREATER_THAN]: 'greater than',
  [FilterOperator.GREATER_THAN_OR_EQUAL]: 'greater than or equal',
  [FilterOperator.LESS_THAN]: 'less than',
  [FilterOperator.LESS_THAN_OR_EQUAL]: 'less than or equal',
  [FilterOperator.CONTAINS]: 'contains',
  [FilterOperator.NOT_CONTAINS]: 'does not contain',
  [FilterOperator.STARTS_WITH]: 'starts with',
  [FilterOperator.ENDS_WITH]: 'ends with',
  [FilterOperator.IN]: 'in',
  [FilterOperator.NOT_IN]: 'not in',
  [FilterOperator.IS_NULL]: 'is null',
  [FilterOperator.IS_NOT_NULL]: 'is not null',
  [FilterOperator.BETWEEN]: 'between',
  [FilterOperator.REGEX]: 'matches regex',
}

const FilterInput: React.FC<{
  filter: SearchFilter
  fieldConfig?: FieldConfig
  onChange: (filter: SearchFilter) => void
}> = ({ filter, fieldConfig, onChange }) => {
  const handleValueChange = (value: any) => {
    onChange({ ...filter, value })
  }

  if (filter.operator === FilterOperator.IS_NULL || filter.operator === FilterOperator.IS_NOT_NULL) {
    return null // No value input needed
  }

  if (filter.operator === FilterOperator.BETWEEN) {
    const [start, end] = Array.isArray(filter.value) ? filter.value : ['', '']
    return (
      <div className="flex space-x-2">
        <input
          type={fieldConfig?.type === 'date' ? 'date' : fieldConfig?.type === 'number' ? 'number' : 'text'}
          value={start}
          onChange={(e) => handleValueChange([e.target.value, end])}
          className="flex-1 px-2 py-1 border border-gray-300 rounded text-sm"
          placeholder="From"
        />
        <input
          type={fieldConfig?.type === 'date' ? 'date' : fieldConfig?.type === 'number' ? 'number' : 'text'}
          value={end}
          onChange={(e) => handleValueChange([start, e.target.value])}
          className="flex-1 px-2 py-1 border border-gray-300 rounded text-sm"
          placeholder="To"
        />
      </div>
    )
  }

  if (fieldConfig?.type === 'enum' && fieldConfig.options) {
    if (filter.operator === FilterOperator.IN || filter.operator === FilterOperator.NOT_IN) {
      const selectedValues = Array.isArray(filter.value) ? filter.value : [filter.value].filter(Boolean)
      return (
        <div className="space-y-1">
          {fieldConfig.options.map((option) => (
            <label key={option.value} className="flex items-center space-x-2">
              <input
                type="checkbox"
                checked={selectedValues.includes(option.value)}
                onChange={(e) => {
                  if (e.target.checked) {
                    handleValueChange([...selectedValues, option.value])
                  } else {
                    handleValueChange(selectedValues.filter(v => v !== option.value))
                  }
                }}
                className="h-3 w-3"
              />
              <span className="text-sm">{option.label}</span>
            </label>
          ))}
        </div>
      )
    } else {
      return (
        <select
          value={filter.value || ''}
          onChange={(e) => handleValueChange(e.target.value)}
          className="w-full px-2 py-1 border border-gray-300 rounded text-sm"
        >
          <option value="">Select...</option>
          {fieldConfig.options.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
      )
    }
  }

  if (fieldConfig?.type === 'boolean') {
    return (
      <select
        value={filter.value || ''}
        onChange={(e) => handleValueChange(e.target.value === 'true')}
        className="w-full px-2 py-1 border border-gray-300 rounded text-sm"
      >
        <option value="">Select...</option>
        <option value="true">True</option>
        <option value="false">False</option>
      </select>
    )
  }

  return (
    <input
      type={fieldConfig?.type === 'date' ? 'date' : fieldConfig?.type === 'number' ? 'number' : 'text'}
      value={filter.value || ''}
      onChange={(e) => handleValueChange(fieldConfig?.type === 'number' ? Number(e.target.value) : e.target.value)}
      className="w-full px-2 py-1 border border-gray-300 rounded text-sm"
      placeholder="Enter value..."
    />
  )
}

const AdvancedSearch = React.memo<AdvancedSearchProps>(({
  className,
  placeholder = "Search...",
  onSearch,
  onResultSelect,
  showFilters = true,
  showSort = true,
  showFacets = true,
  availableFields = DEFAULT_FIELDS,
}) => {
  const {
    query,
    setQuery,
    filters,
    addFilter,
    removeFilter,
    updateFilter,
    clearFilters,
    sort,
    addSort,
    removeSort,
    clearSort,
    results,
    facets,
    suggestions,
    isLoading,
    total,
  } = useAdvancedSearch()

  const [showFilterPanel, setShowFilterPanel] = React.useState(false)
  const [newFilter, setNewFilter] = React.useState<Partial<SearchFilter>>({
    field: '',
    operator: FilterOperator.CONTAINS,
    value: '',
  })

  // Handle search input
  const handleQueryChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setQuery(e.target.value)
    onSearch?.(e.target.value, filters, sort)
  }

  // Handle adding new filter
  const handleAddFilter = () => {
    if (newFilter.field && newFilter.operator) {
      const fieldConfig = availableFields.find(f => f.field === newFilter.field)
      addFilter({
        field: newFilter.field,
        operator: newFilter.operator,
        value: newFilter.value,
        type: fieldConfig?.type || 'string',
        label: fieldConfig?.label,
      })
      setNewFilter({ field: '', operator: FilterOperator.CONTAINS, value: '' })
    }
  }

  // Handle adding sort
  const handleAddSort = (field: string, direction: 'asc' | 'desc') => {
    const fieldConfig = availableFields.find(f => f.field === field)
    addSort({
      field,
      direction,
      label: fieldConfig?.label,
    })
  }

  // Get available operators for field
  const getAvailableOperators = (fieldType: string) => {
    switch (fieldType) {
      case 'string':
        return [FilterOperator.CONTAINS, FilterOperator.EQUALS, FilterOperator.STARTS_WITH, FilterOperator.ENDS_WITH]
      case 'number':
        return [FilterOperator.EQUALS, FilterOperator.GREATER_THAN, FilterOperator.LESS_THAN, FilterOperator.BETWEEN]
      case 'date':
        return [FilterOperator.EQUALS, FilterOperator.GREATER_THAN, FilterOperator.LESS_THAN, FilterOperator.BETWEEN]
      case 'boolean':
        return [FilterOperator.EQUALS]
      case 'enum':
        return [FilterOperator.EQUALS, FilterOperator.IN]
      default:
        return [FilterOperator.EQUALS, FilterOperator.CONTAINS]
    }
  }

  const getFieldIcon = (type: string) => {
    switch (type) {
      case 'string': return <Type className="h-4 w-4" />
      case 'number': return <Hash className="h-4 w-4" />
      case 'date': return <Calendar className="h-4 w-4" />
      case 'boolean': return <Toggle className="h-4 w-4" />
      case 'enum': return <List className="h-4 w-4" />
      default: return <Type className="h-4 w-4" />
    }
  }

  return (
    <div className={cn('w-full', className)}>
      {/* Search Input */}
      <div className="relative">
        <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
          <Search className="h-5 w-5 text-gray-400" />
        </div>
        
        <input
          type="text"
          value={query}
          onChange={handleQueryChange}
          className="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md leading-5 bg-white placeholder-gray-500 focus:outline-none focus:placeholder-gray-400 focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
          placeholder={placeholder}
        />

        {/* Filter Toggle */}
        {showFilters && (
          <div className="absolute inset-y-0 right-0 pr-3 flex items-center">
            <button
              onClick={() => setShowFilterPanel(!showFilterPanel)}
              className={cn(
                'p-1 rounded hover:bg-gray-100',
                (filters.length > 0 || sort.length > 0) && 'text-blue-600'
              )}
            >
              <Filter className="h-4 w-4" />
              {(filters.length > 0 || sort.length > 0) && (
                <span className="absolute -top-1 -right-1 h-4 w-4 bg-blue-600 text-white text-xs rounded-full flex items-center justify-center">
                  {filters.length + sort.length}
                </span>
              )}
            </button>
          </div>
        )}
      </div>

      {/* Search Stats */}
      {(query || filters.length > 0) && (
        <div className="mt-2 text-sm text-gray-600">
          {isLoading ? 'Searching...' : `${total.toLocaleString()} results found`}
        </div>
      )}

      {/* Active Filters */}
      {(filters.length > 0 || sort.length > 0) && (
        <div className="mt-3 flex flex-wrap gap-2">
          {filters.map((filter, index) => (
            <div
              key={index}
              className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800"
            >
              <span>{filter.label || filter.field} {OPERATOR_LABELS[filter.operator]} {filter.value}</span>
              <button
                onClick={() => removeFilter(index)}
                className="ml-2 h-3 w-3 text-blue-600 hover:text-blue-800"
              >
                <X className="h-3 w-3" />
              </button>
            </div>
          ))}
          
          {sort.map((sortItem, index) => (
            <div
              key={index}
              className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800"
            >
              <span>Sort by {sortItem.label || sortItem.field} ({sortItem.direction})</span>
              <button
                onClick={() => removeSort(index)}
                className="ml-2 h-3 w-3 text-green-600 hover:text-green-800"
              >
                <X className="h-3 w-3" />
              </button>
            </div>
          ))}

          {(filters.length > 0 || sort.length > 0) && (
            <button
              onClick={() => { clearFilters(); clearSort() }}
              className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-800 hover:bg-gray-200"
            >
              Clear all
            </button>
          )}
        </div>
      )}

      {/* Filter Panel */}
      {showFilterPanel && (
        <div className="mt-4 p-4 border border-gray-200 rounded-lg bg-gray-50">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Add Filter */}
            <div>
              <h3 className="text-sm font-medium text-gray-900 mb-3">Add Filter</h3>
              <div className="space-y-3">
                {/* Field Selection */}
                <div>
                  <label className="block text-xs font-medium text-gray-700 mb-1">Field</label>
                  <select
                    value={newFilter.field || ''}
                    onChange={(e) => {
                      const fieldConfig = availableFields.find(f => f.field === e.target.value)
                      setNewFilter({
                        field: e.target.value,
                        operator: fieldConfig ? getAvailableOperators(fieldConfig.type)[0] : FilterOperator.CONTAINS,
                        value: '',
                      })
                    }}
                    className="w-full px-2 py-1 border border-gray-300 rounded text-sm"
                  >
                    <option value="">Select field...</option>
                    {availableFields.map((field) => (
                      <option key={field.field} value={field.field}>
                        {field.label}
                      </option>
                    ))}
                  </select>
                </div>

                {/* Operator Selection */}
                {newFilter.field && (
                  <div>
                    <label className="block text-xs font-medium text-gray-700 mb-1">Operator</label>
                    <select
                      value={newFilter.operator || ''}
                      onChange={(e) => setNewFilter(prev => ({ ...prev, operator: e.target.value as FilterOperator }))}
                      className="w-full px-2 py-1 border border-gray-300 rounded text-sm"
                    >
                      {getAvailableOperators(availableFields.find(f => f.field === newFilter.field)?.type || 'string').map((op) => (
                        <option key={op} value={op}>
                          {OPERATOR_LABELS[op]}
                        </option>
                      ))}
                    </select>
                  </div>
                )}

                {/* Value Input */}
                {newFilter.field && newFilter.operator && (
                  <div>
                    <label className="block text-xs font-medium text-gray-700 mb-1">Value</label>
                    <FilterInput
                      filter={newFilter as SearchFilter}
                      fieldConfig={availableFields.find(f => f.field === newFilter.field)}
                      onChange={(filter) => setNewFilter(filter)}
                    />
                  </div>
                )}

                <button
                  onClick={handleAddFilter}
                  disabled={!newFilter.field || !newFilter.operator}
                  className="w-full px-3 py-2 bg-blue-600 text-white text-sm rounded disabled:bg-gray-300 disabled:cursor-not-allowed"
                >
                  Add Filter
                </button>
              </div>
            </div>

            {/* Add Sort */}
            {showSort && (
              <div>
                <h3 className="text-sm font-medium text-gray-900 mb-3">Sort Options</h3>
                <div className="space-y-2">
                  {availableFields.filter(f => f.sortable).map((field) => (
                    <div key={field.field} className="flex items-center justify-between">
                      <div className="flex items-center space-x-2">
                        {getFieldIcon(field.type)}
                        <span className="text-sm">{field.label}</span>
                      </div>
                      <div className="flex space-x-1">
                        <button
                          onClick={() => handleAddSort(field.field, 'asc')}
                          className="px-2 py-1 text-xs bg-gray-200 hover:bg-gray-300 rounded"
                        >
                          Asc
                        </button>
                        <button
                          onClick={() => handleAddSort(field.field, 'desc')}
                          className="px-2 py-1 text-xs bg-gray-200 hover:bg-gray-300 rounded"
                        >
                          Desc
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Facets */}
          {showFacets && facets.length > 0 && (
            <div className="mt-6">
              <h3 className="text-sm font-medium text-gray-900 mb-3">Refine Results</h3>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {facets.map((facet) => (
                  <div key={facet.field} className="space-y-2">
                    <h4 className="text-xs font-medium text-gray-700">{facet.field}</h4>
                    <div className="space-y-1">
                      {facet.buckets.slice(0, 5).map((bucket) => (
                        <label key={bucket.key} className="flex items-center space-x-2">
                          <input
                            type="checkbox"
                            checked={bucket.selected || false}
                            onChange={() => {
                              // Toggle facet value logic would go here
                            }}
                            className="h-3 w-3"
                          />
                          <span className="text-xs">{bucket.key} ({bucket.doc_count})</span>
                        </label>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Search Results */}
      {results.length > 0 && (
        <div className="mt-4 space-y-2">
          {results.map((result) => (
            <div
              key={result.id}
              className="p-3 border border-gray-200 rounded-lg hover:bg-gray-50 cursor-pointer"
              onClick={() => onResultSelect?.(result.item)}
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <h3 className="text-sm font-medium text-gray-900">
                    {result.item.title || result.item.name || 'Untitled'}
                  </h3>
                  {result.snippet && (
                    <p className="text-xs text-gray-600 mt-1">{result.snippet}</p>
                  )}
                  {result.highlights && (
                    <div className="mt-2">
                      {Object.entries(result.highlights).map(([field, highlights]) => (
                        <div key={field} className="text-xs">
                          <span className="font-medium">{field}:</span>{' '}
                          <span dangerouslySetInnerHTML={{ __html: highlights.join('... ') }} />
                        </div>
                      ))}
                    </div>
                  )}
                </div>
                <div className="text-xs text-gray-500 ml-4">
                  Score: {result.score.toFixed(2)}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Suggestions */}
      {suggestions.length > 0 && (
        <div className="mt-4">
          <h3 className="text-sm font-medium text-gray-900 mb-2">Suggestions</h3>
          <div className="flex flex-wrap gap-2">
            {suggestions.map((suggestion, index) => (
              <button
                key={index}
                onClick={() => setQuery(suggestion)}
                className="px-3 py-1 text-xs bg-gray-100 hover:bg-gray-200 rounded-full"
              >
                {suggestion}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  )
})

AdvancedSearch.displayName = 'AdvancedSearch'

export default AdvancedSearch