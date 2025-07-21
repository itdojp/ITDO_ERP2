import React from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { useDebounce } from './useDebounce'
import { apiClient } from '../services/api'

export interface SearchFilter {
  field: string
  operator: FilterOperator
  value: any
  type?: 'string' | 'number' | 'date' | 'boolean' | 'enum'
  label?: string
}

export enum FilterOperator {
  EQUALS = 'eq',
  NOT_EQUALS = 'ne',
  GREATER_THAN = 'gt',
  GREATER_THAN_OR_EQUAL = 'gte',
  LESS_THAN = 'lt',
  LESS_THAN_OR_EQUAL = 'lte',
  CONTAINS = 'contains',
  NOT_CONTAINS = 'not_contains',
  STARTS_WITH = 'starts_with',
  ENDS_WITH = 'ends_with',
  IN = 'in',
  NOT_IN = 'not_in',
  IS_NULL = 'is_null',
  IS_NOT_NULL = 'is_not_null',
  BETWEEN = 'between',
  REGEX = 'regex',
}

export interface SearchSort {
  field: string
  direction: 'asc' | 'desc'
  label?: string
}

export interface SearchFacet {
  field: string
  label: string
  type: 'terms' | 'range' | 'date_histogram'
  size?: number
  interval?: string
}

export interface SearchOptions {
  query?: string
  filters?: SearchFilter[]
  sort?: SearchSort[]
  facets?: SearchFacet[]
  pagination?: {
    page: number
    limit: number
  }
  highlighting?: {
    fields: string[]
    fragmentSize?: number
    maxFragments?: number
  }
  suggestions?: {
    enabled: boolean
    fields: string[]
  }
}

export interface SearchResult<T = any> {
  id: string
  item: T
  score: number
  highlights?: Record<string, string[]>
  type: string
  snippet?: string
}

export interface FacetResult {
  field: string
  buckets: FacetBucket[]
  totalBuckets: number
}

export interface FacetBucket {
  key: string | number
  doc_count: number
  selected?: boolean
}

export interface SearchResponse<T = any> {
  results: SearchResult<T>[]
  total: number
  page: number
  limit: number
  totalPages: number
  executionTime: number
  query: string
  facets: FacetResult[]
  suggestions: string[]
  relatedQueries: string[]
}

export interface UseAdvancedSearchOptions {
  endpoint?: string
  debounceMs?: number
  enabled?: boolean
  queryKey?: string[]
  staleTime?: number
  cacheTime?: number
  minQueryLength?: number
}

export interface UseAdvancedSearchReturn<T = any> {
  // Search state
  query: string
  setQuery: (query: string) => void
  filters: SearchFilter[]
  setFilters: (filters: SearchFilter[]) => void
  addFilter: (filter: SearchFilter) => void
  removeFilter: (index: number) => void
  updateFilter: (index: number, filter: SearchFilter) => void
  clearFilters: () => void
  sort: SearchSort[]
  setSort: (sort: SearchSort[]) => void
  addSort: (sort: SearchSort) => void
  removeSort: (index: number) => void
  clearSort: () => void
  
  // Pagination
  page: number
  setPage: (page: number) => void
  limit: number
  setLimit: (limit: number) => void
  
  // Search results
  data: SearchResponse<T> | undefined
  results: SearchResult<T>[]
  facets: FacetResult[]
  suggestions: string[]
  total: number
  totalPages: number
  
  // Query state
  isLoading: boolean
  isError: boolean
  error: any
  isFetching: boolean
  
  // Actions
  search: (options?: Partial<SearchOptions>) => void
  refetch: () => void
  reset: () => void
  
  // Facet helpers
  getFacetByField: (field: string) => FacetResult | undefined
  toggleFacetValue: (field: string, value: string | number) => void
  clearFacet: (field: string) => void
  
  // Filter helpers
  getFiltersByField: (field: string) => SearchFilter[]
  hasFilter: (field: string, value?: any) => boolean
  
  // Search history
  searchHistory: string[]
  addToHistory: (query: string) => void
  clearHistory: () => void
}

export const useAdvancedSearch = <T = any>(
  options: UseAdvancedSearchOptions = {}
): UseAdvancedSearchReturn<T> => {
  const {
    endpoint = '/search',
    debounceMs = 300,
    enabled = true,
    queryKey = ['search'],
    staleTime = 30000,
    cacheTime = 300000,
    minQueryLength = 2,
  } = options

  const queryClient = useQueryClient()

  // Search state
  const [query, setQuery] = React.useState('')
  const [filters, setFilters] = React.useState<SearchFilter[]>([])
  const [sort, setSort] = React.useState<SearchSort[]>([])
  const [page, setPage] = React.useState(1)
  const [limit, setLimit] = React.useState(20)
  const [searchHistory, setSearchHistory] = React.useState<string[]>([])

  // Debounced query
  const debouncedQuery = useDebounce(query, debounceMs)

  // Build search options
  const searchOptions = React.useMemo((): SearchOptions => ({
    query: debouncedQuery,
    filters,
    sort,
    pagination: { page, limit },
    highlighting: {
      fields: ['title', 'description', 'content'],
      fragmentSize: 150,
      maxFragments: 3,
    },
    suggestions: {
      enabled: true,
      fields: ['title', 'tags', 'description'],
    },
  }), [debouncedQuery, filters, sort, page, limit])

  // Search query
  const {
    data,
    isLoading,
    isError,
    error,
    isFetching,
    refetch,
  } = useQuery({
    queryKey: [...queryKey, searchOptions],
    queryFn: async () => {
      if (!debouncedQuery || debouncedQuery.length < minQueryLength) {
        return {
          results: [],
          total: 0,
          page: 1,
          limit,
          totalPages: 0,
          executionTime: 0,
          query: '',
          facets: [],
          suggestions: [],
          relatedQueries: [],
        } as SearchResponse<T>
      }

      const response = await apiClient.post<SearchResponse<T>>(endpoint, searchOptions)
      return response.data
    },
    enabled: enabled && (debouncedQuery.length >= minQueryLength || filters.length > 0),
    staleTime,
    cacheTime,
    keepPreviousData: true,
  })

  // Derived state
  const results = data?.results || []
  const facets = data?.facets || []
  const suggestions = data?.suggestions || []
  const total = data?.total || 0
  const totalPages = data?.totalPages || 0

  // Filter management
  const addFilter = React.useCallback((filter: SearchFilter) => {
    setFilters(prev => [...prev, filter])
    setPage(1) // Reset to first page when filters change
  }, [])

  const removeFilter = React.useCallback((index: number) => {
    setFilters(prev => prev.filter((_, i) => i !== index))
    setPage(1)
  }, [])

  const updateFilter = React.useCallback((index: number, filter: SearchFilter) => {
    setFilters(prev => prev.map((f, i) => i === index ? filter : f))
    setPage(1)
  }, [])

  const clearFilters = React.useCallback(() => {
    setFilters([])
    setPage(1)
  }, [])

  // Sort management
  const addSort = React.useCallback((sortOption: SearchSort) => {
    setSort(prev => {
      // Remove existing sort for the same field
      const filtered = prev.filter(s => s.field !== sortOption.field)
      return [...filtered, sortOption]
    })
  }, [])

  const removeSort = React.useCallback((index: number) => {
    setSort(prev => prev.filter((_, i) => i !== index))
  }, [])

  const clearSort = React.useCallback(() => {
    setSort([])
  }, [])

  // Search actions
  const search = React.useCallback((customOptions?: Partial<SearchOptions>) => {
    if (customOptions) {
      // Temporarily override options for this search
      const tempOptions = { ...searchOptions, ...customOptions }
      queryClient.fetchQuery({
        queryKey: [...queryKey, tempOptions],
        queryFn: async () => {
          const response = await apiClient.post<SearchResponse<T>>(endpoint, tempOptions)
          return response.data
        },
        staleTime,
        cacheTime,
      })
    } else {
      refetch()
    }
  }, [searchOptions, queryClient, queryKey, endpoint, staleTime, cacheTime, refetch])

  const reset = React.useCallback(() => {
    setQuery('')
    setFilters([])
    setSort([])
    setPage(1)
    setLimit(20)
  }, [])

  // Facet helpers
  const getFacetByField = React.useCallback((field: string) => {
    return facets.find(f => f.field === field)
  }, [facets])

  const toggleFacetValue = React.useCallback((field: string, value: string | number) => {
    const existingFilterIndex = filters.findIndex(f => 
      f.field === field && f.operator === FilterOperator.EQUALS && f.value === value
    )

    if (existingFilterIndex >= 0) {
      // Remove filter if it exists
      removeFilter(existingFilterIndex)
    } else {
      // Add filter if it doesn't exist
      addFilter({
        field,
        operator: FilterOperator.EQUALS,
        value,
        type: 'string',
      })
    }
  }, [filters, addFilter, removeFilter])

  const clearFacet = React.useCallback((field: string) => {
    setFilters(prev => prev.filter(f => f.field !== field))
    setPage(1)
  }, [])

  // Filter helpers
  const getFiltersByField = React.useCallback((field: string) => {
    return filters.filter(f => f.field === field)
  }, [filters])

  const hasFilter = React.useCallback((field: string, value?: any) => {
    if (value !== undefined) {
      return filters.some(f => f.field === field && f.value === value)
    }
    return filters.some(f => f.field === field)
  }, [filters])

  // Search history management
  const addToHistory = React.useCallback((searchQuery: string) => {
    if (!searchQuery.trim() || searchQuery.length < minQueryLength) return

    setSearchHistory(prev => {
      const filtered = prev.filter(q => q !== searchQuery)
      return [searchQuery, ...filtered].slice(0, 10) // Keep last 10 searches
    })
  }, [minQueryLength])

  const clearHistory = React.useCallback(() => {
    setSearchHistory([])
  }, [])

  // Add successful searches to history
  React.useEffect(() => {
    if (data && data.total > 0 && debouncedQuery) {
      addToHistory(debouncedQuery)
    }
  }, [data, debouncedQuery, addToHistory])

  // Reset page when query changes
  React.useEffect(() => {
    setPage(1)
  }, [debouncedQuery])

  return {
    // Search state
    query,
    setQuery,
    filters,
    setFilters,
    addFilter,
    removeFilter,
    updateFilter,
    clearFilters,
    sort,
    setSort,
    addSort,
    removeSort,
    clearSort,
    
    // Pagination
    page,
    setPage,
    limit,
    setLimit,
    
    // Search results
    data,
    results,
    facets,
    suggestions,
    total,
    totalPages,
    
    // Query state
    isLoading,
    isError,
    error,
    isFetching,
    
    // Actions
    search,
    refetch,
    reset,
    
    // Facet helpers
    getFacetByField,
    toggleFacetValue,
    clearFacet,
    
    // Filter helpers
    getFiltersByField,
    hasFilter,
    
    // Search history
    searchHistory,
    addToHistory,
    clearHistory,
  }
}

export default useAdvancedSearch