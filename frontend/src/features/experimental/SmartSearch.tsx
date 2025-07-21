import React from 'react'
import { 
  Search, 
  Filter, 
  Sparkles, 
  TrendingUp,
  Clock,
  Users,
  FileText,
  Settings,
  X,
  ArrowRight,
  Star
} from 'lucide-react'
import { cn } from '../../lib/utils'
import { useExperimentalFeature, useFeatureAnalytics } from './FeatureFlags'
import { useDebouncedCallback } from '../../hooks/useMemoizedCallback'

export interface SearchResult {
  id: string
  title: string
  description: string
  type: 'user' | 'project' | 'document' | 'page' | 'action'
  url?: string
  score: number
  metadata?: {
    category?: string
    tags?: string[]
    lastModified?: string
    author?: string
    popularity?: number
  }
  highlights?: {
    title?: string
    description?: string
  }
}

export interface SearchSuggestion {
  id: string
  text: string
  type: 'recent' | 'popular' | 'smart' | 'autocomplete'
  count?: number
  icon?: React.ReactNode
}

export interface SmartSearchProps {
  className?: string
  placeholder?: string
  onSearchResults?: (results: SearchResult[]) => void
  onResultSelect?: (result: SearchResult) => void
  maxResults?: number
  showSuggestions?: boolean
  showFilters?: boolean
  categories?: string[]
}

const SmartSearch: React.FC<SmartSearchProps> = ({
  className,
  placeholder = 'Search anything... (Try natural language)',
  onSearchResults,
  onResultSelect,
  maxResults = 10,
  showSuggestions = true,
  showFilters = true,
  categories = ['all', 'users', 'projects', 'documents', 'pages']
}) => {
  const isEnabled = useExperimentalFeature('smart-search')
  const { trackFeatureUsage } = useFeatureAnalytics()

  const [query, setQuery] = React.useState('')
  const [isLoading, setIsLoading] = React.useState(false)
  const [results, setResults] = React.useState<SearchResult[]>([])
  const [suggestions, setSuggestions] = React.useState<SearchSuggestion[]>([])
  const [selectedCategory, setSelectedCategory] = React.useState('all')
  const [showResults, setShowResults] = React.useState(false)
  const [focusedIndex, setFocusedIndex] = React.useState(-1)

  const searchInputRef = React.useRef<HTMLInputElement>(null)
  const resultsRef = React.useRef<HTMLDivElement>(null)

  // Debounced search function
  const debouncedSearch = useDebouncedCallback(async (searchQuery: string) => {
    if (!searchQuery.trim()) {
      setResults([])
      setShowResults(false)
      return
    }

    setIsLoading(true)
    try {
      const searchResults = await performSmartSearch(searchQuery, selectedCategory, maxResults)
      setResults(searchResults)
      setShowResults(true)
      onSearchResults?.(searchResults)
      
      trackFeatureUsage('smart-search', 'search_performed', {
        query: searchQuery,
        category: selectedCategory,
        resultCount: searchResults.length
      })
    } catch (error) {
      console.error('Search error:', error)
    } finally {
      setIsLoading(false)
    }
  }, 300, [selectedCategory, maxResults, onSearchResults, trackFeatureUsage])

  // Load suggestions on focus
  const loadSuggestions = React.useCallback(async () => {
    if (!showSuggestions) return
    
    const smartSuggestions = await getSmartSuggestions(query)
    setSuggestions(smartSuggestions)
  }, [query, showSuggestions])

  // Handle search input changes
  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value
    setQuery(value)
    setFocusedIndex(-1)
    
    if (value.trim()) {
      debouncedSearch(value)
    } else {
      setResults([])
      setShowResults(false)
    }
  }

  // Handle keyboard navigation
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (!showResults) return

    const totalItems = results.length + (showSuggestions ? suggestions.length : 0)

    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault()
        setFocusedIndex(prev => (prev + 1) % totalItems)
        break
      case 'ArrowUp':
        e.preventDefault()
        setFocusedIndex(prev => (prev - 1 + totalItems) % totalItems)
        break
      case 'Enter':
        e.preventDefault()
        if (focusedIndex >= 0) {
          if (focusedIndex < suggestions.length) {
            // Select suggestion
            const suggestion = suggestions[focusedIndex]
            handleSuggestionSelect(suggestion)
          } else {
            // Select result
            const result = results[focusedIndex - suggestions.length]
            handleResultSelect(result)
          }
        }
        break
      case 'Escape':
        setShowResults(false)
        setFocusedIndex(-1)
        searchInputRef.current?.blur()
        break
    }
  }

  const handleSuggestionSelect = (suggestion: SearchSuggestion) => {
    setQuery(suggestion.text)
    debouncedSearch(suggestion.text)
    trackFeatureUsage('smart-search', 'suggestion_selected', {
      suggestionType: suggestion.type,
      suggestionText: suggestion.text
    })
  }

  const handleResultSelect = (result: SearchResult) => {
    onResultSelect?.(result)
    setShowResults(false)
    setQuery('')
    trackFeatureUsage('smart-search', 'result_selected', {
      resultType: result.type,
      resultId: result.id,
      score: result.score
    })
  }

  const handleCategoryChange = (category: string) => {
    setSelectedCategory(category)
    if (query.trim()) {
      debouncedSearch(query)
    }
  }

  // Click outside handler
  React.useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (resultsRef.current && !resultsRef.current.contains(event.target as Node)) {
        setShowResults(false)
        setFocusedIndex(-1)
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  if (!isEnabled) {
    // Fallback to regular search
    return (
      <div className={cn('relative', className)}>
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
          <input
            type="text"
            placeholder="Search..."
            className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
      </div>
    )
  }

  return (
    <div className={cn('relative', className)} ref={resultsRef}>
      {/* Search Input */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
        <Sparkles className="absolute left-8 top-1/2 transform -translate-y-1/2 h-3 w-3 text-blue-500" />
        <input
          ref={searchInputRef}
          type="text"
          value={query}
          onChange={handleInputChange}
          onKeyDown={handleKeyDown}
          onFocus={loadSuggestions}
          placeholder={placeholder}
          className="w-full pl-14 pr-10 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        />
        {query && (
          <button
            onClick={() => {
              setQuery('')
              setResults([])
              setShowResults(false)
            }}
            className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600"
          >
            <X className="h-4 w-4" />
          </button>
        )}
        {isLoading && (
          <div className="absolute right-3 top-1/2 transform -translate-y-1/2">
            <div className="animate-spin rounded-full h-4 w-4 border-2 border-blue-500 border-t-transparent" />
          </div>
        )}
      </div>

      {/* Category Filters */}
      {showFilters && (
        <div className="flex items-center space-x-2 mt-2">
          <Filter className="h-4 w-4 text-gray-400" />
          {categories.map(category => (
            <button
              key={category}
              onClick={() => handleCategoryChange(category)}
              className={cn(
                'px-3 py-1 rounded-full text-xs font-medium transition-colors',
                selectedCategory === category
                  ? 'bg-blue-100 text-blue-800'
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              )}
            >
              {category.charAt(0).toUpperCase() + category.slice(1)}
            </button>
          ))}
        </div>
      )}

      {/* Search Results */}
      {showResults && (
        <div className="absolute top-full left-0 right-0 mt-2 bg-white border border-gray-200 rounded-lg shadow-lg z-50 max-h-96 overflow-y-auto">
          {/* Suggestions */}
          {showSuggestions && suggestions.length > 0 && query.length < 3 && (
            <div className="p-3 border-b border-gray-100">
              <div className="text-xs font-medium text-gray-500 mb-2">Suggestions</div>
              {suggestions.map((suggestion, index) => (
                <SuggestionItem
                  key={suggestion.id}
                  suggestion={suggestion}
                  isSelected={index === focusedIndex}
                  onClick={() => handleSuggestionSelect(suggestion)}
                />
              ))}
            </div>
          )}

          {/* Search Results */}
          {results.length > 0 ? (
            <div className="p-2">
              {query && (
                <div className="px-2 py-1 text-xs text-gray-500">
                  {results.length} result{results.length !== 1 ? 's' : ''} for "{query}"
                </div>
              )}
              {results.map((result, index) => (
                <SearchResultItem
                  key={result.id}
                  result={result}
                  isSelected={index + suggestions.length === focusedIndex}
                  onClick={() => handleResultSelect(result)}
                />
              ))}
            </div>
          ) : query.trim() && !isLoading ? (
            <div className="p-6 text-center text-gray-500">
              <Search className="h-8 w-8 mx-auto mb-2 text-gray-300" />
              <p className="text-sm">No results found for "{query}"</p>
              <p className="text-xs mt-1">Try different keywords or check spelling</p>
            </div>
          ) : null}
        </div>
      )}
    </div>
  )
}

interface SuggestionItemProps {
  suggestion: SearchSuggestion
  isSelected: boolean
  onClick: () => void
}

const SuggestionItem: React.FC<SuggestionItemProps> = ({
  suggestion,
  isSelected,
  onClick
}) => {
  const getIcon = () => {
    if (suggestion.icon) return suggestion.icon
    
    switch (suggestion.type) {
      case 'recent': return <Clock className="h-4 w-4 text-gray-400" />
      case 'popular': return <TrendingUp className="h-4 w-4 text-green-500" />
      case 'smart': return <Sparkles className="h-4 w-4 text-blue-500" />
      default: return <Search className="h-4 w-4 text-gray-400" />
    }
  }

  return (
    <button
      onClick={onClick}
      className={cn(
        'flex items-center space-x-3 w-full px-2 py-1 rounded text-left text-sm hover:bg-gray-50 transition-colors',
        isSelected && 'bg-blue-50'
      )}
    >
      {getIcon()}
      <span className="flex-1">{suggestion.text}</span>
      {suggestion.count && (
        <span className="text-xs text-gray-400">{suggestion.count}</span>
      )}
    </button>
  )
}

interface SearchResultItemProps {
  result: SearchResult
  isSelected: boolean
  onClick: () => void
}

const SearchResultItem: React.FC<SearchResultItemProps> = ({
  result,
  isSelected,
  onClick
}) => {
  const getTypeIcon = () => {
    switch (result.type) {
      case 'user': return <Users className="h-4 w-4 text-blue-500" />
      case 'project': return <FileText className="h-4 w-4 text-green-500" />
      case 'document': return <FileText className="h-4 w-4 text-orange-500" />
      case 'page': return <Settings className="h-4 w-4 text-purple-500" />
      case 'action': return <ArrowRight className="h-4 w-4 text-gray-500" />
      default: return <Search className="h-4 w-4 text-gray-400" />
    }
  }

  return (
    <button
      onClick={onClick}
      className={cn(
        'flex items-start space-x-3 w-full p-3 rounded-md text-left hover:bg-gray-50 transition-colors',
        isSelected && 'bg-blue-50'
      )}
    >
      <div className="flex-shrink-0 mt-0.5">
        {getTypeIcon()}
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-center space-x-2">
          <h3 className="text-sm font-medium text-gray-900 truncate">
            {result.highlights?.title ? (
              <span dangerouslySetInnerHTML={{ __html: result.highlights.title }} />
            ) : (
              result.title
            )}
          </h3>
          {result.score > 0.8 && (
            <Star className="h-3 w-3 text-yellow-500 fill-current" />
          )}
        </div>
        <p className="text-xs text-gray-600 mt-1 line-clamp-2">
          {result.highlights?.description ? (
            <span dangerouslySetInnerHTML={{ __html: result.highlights.description }} />
          ) : (
            result.description
          )}
        </p>
        {result.metadata && (
          <div className="flex items-center space-x-2 mt-2 text-xs text-gray-400">
            {result.metadata.category && (
              <span className="bg-gray-100 px-1 rounded">{result.metadata.category}</span>
            )}
            {result.metadata.lastModified && (
              <span>{new Date(result.metadata.lastModified).toLocaleDateString()}</span>
            )}
            {result.metadata.popularity && (
              <span> {result.metadata.popularity}</span>
            )}
          </div>
        )}
      </div>
      <div className="flex-shrink-0">
        <ArrowRight className="h-4 w-4 text-gray-400" />
      </div>
    </button>
  )
}

// Mock smart search function (replace with actual implementation)
const performSmartSearch = async (
  query: string, 
  category: string, 
  maxResults: number
): Promise<SearchResult[]> => {
  // Simulate API delay
  await new Promise(resolve => setTimeout(resolve, 200 + Math.random() * 300))

  // Mock results with ML-like scoring
  const mockResults: SearchResult[] = [
    {
      id: '1',
      title: 'User Analytics Dashboard',
      description: 'View comprehensive user analytics and behavior patterns',
      type: 'page',
      url: '/analytics/users',
      score: 0.95,
      metadata: {
        category: 'Analytics',
        tags: ['users', 'analytics', 'dashboard'],
        popularity: 4.8
      }
    },
    {
      id: '2',
      title: 'John Smith',
      description: 'Senior Developer in the Engineering team',
      type: 'user',
      url: '/users/john-smith',
      score: 0.87,
      metadata: {
        category: 'Users',
        tags: ['developer', 'engineering'],
        lastModified: '2024-01-15'
      }
    },
    {
      id: '3',
      title: 'Project Alpha',
      description: 'Next-generation ERP system development project',
      type: 'project',
      url: '/projects/alpha',
      score: 0.82,
      metadata: {
        category: 'Projects',
        tags: ['erp', 'development', 'alpha'],
        lastModified: '2024-01-20'
      }
    }
  ]

  // Filter by category
  const filteredResults = category === 'all' 
    ? mockResults 
    : mockResults.filter(result => result.type === category.slice(0, -1)) // Remove 's' from category

  // Add search highlighting
  const highlightedResults = filteredResults.map(result => ({
    ...result,
    highlights: {
      title: highlightMatches(result.title, query),
      description: highlightMatches(result.description, query)
    }
  }))

  return highlightedResults.slice(0, maxResults)
}

// Mock suggestions function
const getSmartSuggestions = async (query: string): Promise<SearchSuggestion[]> => {
  const suggestions: SearchSuggestion[] = [
    {
      id: '1',
      text: 'user analytics',
      type: 'popular',
      count: 156,
      icon: <TrendingUp className="h-4 w-4 text-green-500" />
    },
    {
      id: '2',
      text: 'project reports',
      type: 'recent',
      icon: <Clock className="h-4 w-4 text-gray-400" />
    },
    {
      id: '3',
      text: 'show me performance metrics',
      type: 'smart',
      icon: <Sparkles className="h-4 w-4 text-blue-500" />
    },
    {
      id: '4',
      text: 'create new user',
      type: 'smart',
      icon: <Sparkles className="h-4 w-4 text-blue-500" />
    }
  ]

  return suggestions.filter(s => !query || s.text.toLowerCase().includes(query.toLowerCase()))
}

// Helper function to highlight search matches
const highlightMatches = (text: string, query: string): string => {
  if (!query.trim()) return text
  
  const regex = new RegExp(`(${query.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, 'gi')
  return text.replace(regex, '<mark class="bg-yellow-200">$1</mark>')
}

export default SmartSearch