import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { vi } from 'vitest';
import { SearchBox } from './SearchBox';

describe('SearchBox', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  const mockSuggestions = [
    'Apple iPhone',
    'Samsung Galaxy',
    'Google Pixel',
    'OnePlus Nord',
    'Xiaomi Mi'
  ];

  const mockFilters = [
    { key: 'category', label: 'Category', options: ['Electronics', 'Books', 'Clothing'] },
    { key: 'price', label: 'Price Range', options: ['0-100', '100-500', '500+'] },
    { key: 'brand', label: 'Brand', options: ['Apple', 'Samsung', 'Google'] }
  ];

  it('renders search box with input', () => {
    render(<SearchBox />);
    
    expect(screen.getByTestId('searchbox-container')).toBeInTheDocument();
    expect(screen.getByTestId('searchbox-input')).toBeInTheDocument();
  });

  it('displays placeholder text', () => {
    render(<SearchBox placeholder="Search products..." />);
    
    const input = screen.getByTestId('searchbox-input');
    expect(input).toHaveAttribute('placeholder', 'Search products...');
  });

  it('shows search icon', () => {
    render(<SearchBox />);
    
    expect(screen.getByTestId('search-icon')).toBeInTheDocument();
  });

  it('handles input value changes', () => {
    const onChange = vi.fn();
    render(<SearchBox onChange={onChange} />);
    
    const input = screen.getByTestId('searchbox-input');
    fireEvent.change(input, { target: { value: 'test query' } });
    
    expect(onChange).toHaveBeenCalledWith('test query');
    expect(input).toHaveValue('test query');
  });

  it('shows suggestions when typing', () => {
    render(<SearchBox suggestions={mockSuggestions} />);
    
    const input = screen.getByTestId('searchbox-input');
    fireEvent.change(input, { target: { value: 'apple' } });
    
    expect(screen.getByTestId('suggestions-dropdown')).toBeInTheDocument();
    expect(screen.getByText('Apple iPhone')).toBeInTheDocument();
  });

  it('filters suggestions based on input', () => {
    render(<SearchBox suggestions={mockSuggestions} />);
    
    const input = screen.getByTestId('searchbox-input');
    fireEvent.change(input, { target: { value: 'samsung' } });
    
    expect(screen.getByText('Samsung Galaxy')).toBeInTheDocument();
    expect(screen.queryByText('Apple iPhone')).not.toBeInTheDocument();
  });

  it('handles suggestion selection', () => {
    const onSelect = vi.fn();
    render(<SearchBox suggestions={mockSuggestions} onSelect={onSelect} />);
    
    const input = screen.getByTestId('searchbox-input');
    fireEvent.change(input, { target: { value: 'apple' } });
    
    const suggestion = screen.getByText('Apple iPhone');
    fireEvent.click(suggestion);
    
    expect(onSelect).toHaveBeenCalledWith('Apple iPhone');
    expect(input).toHaveValue('Apple iPhone');
  });

  it('supports keyboard navigation in suggestions', () => {
    render(<SearchBox suggestions={mockSuggestions} />);
    
    const input = screen.getByTestId('searchbox-input');
    fireEvent.change(input, { target: { value: 'a' } });
    
    // Arrow down should highlight first suggestion
    fireEvent.keyDown(input, { key: 'ArrowDown' });
    expect(screen.getByText('Apple iPhone')).toHaveClass('highlighted');
    
    // Enter should select highlighted suggestion
    fireEvent.keyDown(input, { key: 'Enter' });
    expect(input).toHaveValue('Apple iPhone');
  });

  it('shows clear button when input has value', () => {
    render(<SearchBox clearable />);
    
    const input = screen.getByTestId('searchbox-input');
    fireEvent.change(input, { target: { value: 'test' } });
    
    expect(screen.getByTestId('clear-button')).toBeInTheDocument();
  });

  it('clears input when clear button clicked', () => {
    const onClear = vi.fn();
    render(<SearchBox clearable onClear={onClear} />);
    
    const input = screen.getByTestId('searchbox-input');
    fireEvent.change(input, { target: { value: 'test' } });
    
    const clearButton = screen.getByTestId('clear-button');
    fireEvent.click(clearButton);
    
    expect(input).toHaveValue('');
    expect(onClear).toHaveBeenCalled();
  });

  it('shows filter button when filters provided', () => {
    render(<SearchBox filters={mockFilters} />);
    
    expect(screen.getByTestId('filter-button')).toBeInTheDocument();
  });

  it('opens filter dropdown when filter button clicked', () => {
    render(<SearchBox filters={mockFilters} />);
    
    const filterButton = screen.getByTestId('filter-button');
    fireEvent.click(filterButton);
    
    expect(screen.getByTestId('filter-dropdown')).toBeInTheDocument();
  });

  it('displays filter options in dropdown', () => {
    render(<SearchBox filters={mockFilters} />);
    
    const filterButton = screen.getByTestId('filter-button');
    fireEvent.click(filterButton);
    
    expect(screen.getByText('Category')).toBeInTheDocument();
    expect(screen.getByText('Price Range')).toBeInTheDocument();
    expect(screen.getByText('Brand')).toBeInTheDocument();
  });

  it('handles filter selection', () => {
    const onFiltersChange = vi.fn();
    render(<SearchBox filters={mockFilters} onFiltersChange={onFiltersChange} />);
    
    const filterButton = screen.getByTestId('filter-button');
    fireEvent.click(filterButton);
    
    const filterOption = screen.getByText('Electronics');
    fireEvent.click(filterOption);
    
    expect(onFiltersChange).toHaveBeenCalledWith({ category: 'Electronics' });
  });

  it('shows active filter indicators', () => {
    const activeFilters = { category: 'Electronics', price: '100-500' };
    render(<SearchBox filters={mockFilters} activeFilters={activeFilters} />);
    
    expect(screen.getByTestId('active-filters')).toBeInTheDocument();
    expect(screen.getByText('Electronics')).toBeInTheDocument();
    expect(screen.getByText('100-500')).toBeInTheDocument();
  });

  it('allows removing active filters', () => {
    const onFiltersChange = vi.fn();
    const activeFilters = { category: 'Electronics' };
    render(<SearchBox filters={mockFilters} activeFilters={activeFilters} onFiltersChange={onFiltersChange} />);
    
    const removeFilterButton = screen.getByTestId('remove-filter-category');
    fireEvent.click(removeFilterButton);
    
    expect(onFiltersChange).toHaveBeenCalledWith({});
  });

  it('supports different sizes', () => {
    const sizes = ['sm', 'md', 'lg'] as const;
    
    sizes.forEach(size => {
      const { unmount } = render(<SearchBox size={size} />);
      const container = screen.getByTestId('searchbox-container');
      expect(container).toHaveClass(`size-${size}`);
      unmount();
    });
  });

  it('supports different themes', () => {
    const themes = ['light', 'dark'] as const;
    
    themes.forEach(theme => {
      const { unmount } = render(<SearchBox theme={theme} />);
      const container = screen.getByTestId('searchbox-container');
      expect(container).toHaveClass(`theme-${theme}`);
      unmount();
    });
  });

  it('handles search submission', () => {
    const onSearch = vi.fn();
    render(<SearchBox onSearch={onSearch} />);
    
    const input = screen.getByTestId('searchbox-input');
    fireEvent.change(input, { target: { value: 'test query' } });
    fireEvent.keyDown(input, { key: 'Enter' });
    
    expect(onSearch).toHaveBeenCalledWith('test query', {});
  });

  it('includes filters in search submission', () => {
    const onSearch = vi.fn();
    const activeFilters = { category: 'Electronics' };
    render(<SearchBox onSearch={onSearch} activeFilters={activeFilters} />);
    
    const input = screen.getByTestId('searchbox-input');
    fireEvent.change(input, { target: { value: 'laptop' } });
    fireEvent.keyDown(input, { key: 'Enter' });
    
    expect(onSearch).toHaveBeenCalledWith('laptop', activeFilters);
  });

  it('shows loading state', () => {
    render(<SearchBox loading />);
    
    expect(screen.getByTestId('search-loading')).toBeInTheDocument();
  });

  it('disables input when loading', () => {
    render(<SearchBox loading />);
    
    const input = screen.getByTestId('searchbox-input');
    expect(input).toBeDisabled();
  });

  it('supports async suggestions', async () => {
    const loadSuggestions = vi.fn().mockResolvedValue(mockSuggestions);
    render(<SearchBox loadSuggestions={loadSuggestions} />);
    
    const input = screen.getByTestId('searchbox-input');
    fireEvent.change(input, { target: { value: 'test' } });
    
    await waitFor(() => {
      expect(loadSuggestions).toHaveBeenCalledWith('test');
    });
  });

  it('debounces async suggestions', async () => {
    const loadSuggestions = vi.fn().mockResolvedValue(mockSuggestions);
    render(<SearchBox loadSuggestions={loadSuggestions} debounceMs={100} />);
    
    const input = screen.getByTestId('searchbox-input');
    fireEvent.change(input, { target: { value: 't' } });
    fireEvent.change(input, { target: { value: 'te' } });
    fireEvent.change(input, { target: { value: 'test' } });
    
    // Should not call immediately
    expect(loadSuggestions).not.toHaveBeenCalled();
    
    // Should call after debounce
    await waitFor(() => {
      expect(loadSuggestions).toHaveBeenCalledTimes(1);
      expect(loadSuggestions).toHaveBeenCalledWith('test');
    }, { timeout: 200 });
  });

  it('supports minimum search length', () => {
    render(<SearchBox suggestions={mockSuggestions} minSearchLength={3} />);
    
    const input = screen.getByTestId('searchbox-input');
    fireEvent.change(input, { target: { value: 'ap' } });
    
    expect(screen.queryByTestId('suggestions-dropdown')).not.toBeInTheDocument();
    
    fireEvent.change(input, { target: { value: 'app' } });
    expect(screen.getByTestId('suggestions-dropdown')).toBeInTheDocument();
  });

  it('shows recent searches when enabled', () => {
    const recentSearches = ['laptop', 'phone', 'tablet'];
    render(<SearchBox showRecentSearches recentSearches={recentSearches} />);
    
    const input = screen.getByTestId('searchbox-input');
    fireEvent.focus(input);
    
    expect(screen.getByTestId('recent-searches')).toBeInTheDocument();
    expect(screen.getByText('laptop')).toBeInTheDocument();
    expect(screen.getByText('phone')).toBeInTheDocument();
  });

  it('handles recent search selection', () => {
    const onSelect = vi.fn();
    const recentSearches = ['laptop'];
    render(<SearchBox showRecentSearches recentSearches={recentSearches} onSelect={onSelect} />);
    
    const input = screen.getByTestId('searchbox-input');
    fireEvent.focus(input);
    
    const recentSearch = screen.getByText('laptop');
    fireEvent.click(recentSearch);
    
    expect(onSelect).toHaveBeenCalledWith('laptop');
  });

  it('supports custom suggestion rendering', () => {
    const renderSuggestion = (suggestion: string) => (
      <div data-testid="custom-suggestion">
        <strong>{suggestion.toUpperCase()}</strong>
      </div>
    );
    
    render(<SearchBox suggestions={mockSuggestions} renderSuggestion={renderSuggestion} />);
    
    const input = screen.getByTestId('searchbox-input');
    fireEvent.change(input, { target: { value: 'apple' } });
    
    expect(screen.getByTestId('custom-suggestion')).toBeInTheDocument();
    expect(screen.getByText('APPLE IPHONE')).toBeInTheDocument();
  });

  it('shows search button', () => {
    render(<SearchBox showSearchButton />);
    
    expect(screen.getByTestId('search-button')).toBeInTheDocument();
  });

  it('handles search button click', () => {
    const onSearch = vi.fn();
    render(<SearchBox showSearchButton onSearch={onSearch} />);
    
    const input = screen.getByTestId('searchbox-input');
    fireEvent.change(input, { target: { value: 'test query' } });
    
    const searchButton = screen.getByTestId('search-button');
    fireEvent.click(searchButton);
    
    expect(onSearch).toHaveBeenCalledWith('test query', {});
  });

  it('supports voice search', () => {
    render(<SearchBox voiceSearch />);
    
    expect(screen.getByTestId('voice-search-button')).toBeInTheDocument();
  });

  it('handles voice search activation', () => {
    const onVoiceSearch = vi.fn();
    render(<SearchBox voiceSearch onVoiceSearch={onVoiceSearch} />);
    
    const voiceButton = screen.getByTestId('voice-search-button');
    fireEvent.click(voiceButton);
    
    expect(onVoiceSearch).toHaveBeenCalled();
  });

  it('shows search history when enabled', () => {
    const searchHistory = ['previous search', 'another search'];
    render(<SearchBox showHistory searchHistory={searchHistory} />);
    
    const input = screen.getByTestId('searchbox-input');
    fireEvent.focus(input);
    
    expect(screen.getByTestId('search-history')).toBeInTheDocument();
    expect(screen.getByText('previous search')).toBeInTheDocument();
  });

  it('supports search categories', () => {
    const categories = ['All', 'Products', 'Articles', 'Users'];
    render(<SearchBox categories={categories} />);
    
    expect(screen.getByTestId('category-selector')).toBeInTheDocument();
    categories.forEach(category => {
      expect(screen.getByText(category)).toBeInTheDocument();
    });
  });

  it('handles category selection', () => {
    const onCategoryChange = vi.fn();
    const categories = ['All', 'Products'];
    render(<SearchBox categories={categories} onCategoryChange={onCategoryChange} />);
    
    const categoryButton = screen.getByText('Products');
    fireEvent.click(categoryButton);
    
    expect(onCategoryChange).toHaveBeenCalledWith('Products');
  });

  it('supports advanced search mode', () => {
    render(<SearchBox advancedSearch />);
    
    const advancedButton = screen.getByTestId('advanced-search-button');
    fireEvent.click(advancedButton);
    
    expect(screen.getByTestId('advanced-search-modal')).toBeInTheDocument();
  });

  it('handles focus and blur events', () => {
    const onFocus = vi.fn();
    const onBlur = vi.fn();
    render(<SearchBox onFocus={onFocus} onBlur={onBlur} />);
    
    const input = screen.getByTestId('searchbox-input');
    fireEvent.focus(input);
    expect(onFocus).toHaveBeenCalled();
    
    fireEvent.blur(input);
    expect(onBlur).toHaveBeenCalled();
  });

  it('supports disabled state', () => {
    render(<SearchBox disabled />);
    
    const input = screen.getByTestId('searchbox-input');
    expect(input).toBeDisabled();
    
    const container = screen.getByTestId('searchbox-container');
    expect(container).toHaveClass('disabled');
  });

  it('supports readonly state', () => {
    render(<SearchBox readonly />);
    
    const input = screen.getByTestId('searchbox-input');
    expect(input).toHaveAttribute('readonly');
  });

  it('shows no results message', () => {
    render(<SearchBox suggestions={[]} />);
    
    const input = screen.getByTestId('searchbox-input');
    fireEvent.change(input, { target: { value: 'xyz' } });
    
    expect(screen.getByTestId('no-results')).toBeInTheDocument();
  });

  it('supports custom no results component', () => {
    const NoResultsComponent = () => <div data-testid="custom-no-results">No matches found</div>;
    render(<SearchBox suggestions={[]} noResultsComponent={<NoResultsComponent />} />);
    
    const input = screen.getByTestId('searchbox-input');
    fireEvent.change(input, { target: { value: 'xyz' } });
    
    expect(screen.getByTestId('custom-no-results')).toBeInTheDocument();
  });

  it('highlights search terms in suggestions', () => {
    render(<SearchBox suggestions={mockSuggestions} highlightMatch />);
    
    const input = screen.getByTestId('searchbox-input');
    fireEvent.change(input, { target: { value: 'apple' } });
    
    expect(screen.getByTestId('highlighted-text')).toBeInTheDocument();
  });

  it('supports custom styling', () => {
    render(<SearchBox className="custom-search" />);
    
    const container = screen.getByTestId('searchbox-container');
    expect(container).toHaveClass('custom-search');
  });

  it('supports custom data attributes', () => {
    render(<SearchBox data-category="search" data-id="main-search" />);
    
    const container = screen.getByTestId('searchbox-container');
    expect(container).toHaveAttribute('data-category', 'search');
    expect(container).toHaveAttribute('data-id', 'main-search');
  });

  it('handles click outside to close suggestions', () => {
    render(<SearchBox suggestions={mockSuggestions} />);
    
    const input = screen.getByTestId('searchbox-input');
    fireEvent.change(input, { target: { value: 'apple' } });
    
    expect(screen.getByTestId('suggestions-dropdown')).toBeInTheDocument();
    
    fireEvent.mouseDown(document.body);
    expect(screen.queryByTestId('suggestions-dropdown')).not.toBeInTheDocument();
  });

  it('supports search scopes', () => {
    const scopes = ['Title', 'Description', 'Content'];
    render(<SearchBox searchScopes={scopes} />);
    
    expect(screen.getByTestId('scope-selector')).toBeInTheDocument();
  });

  it('handles scope selection', () => {
    const onScopeChange = vi.fn();
    const scopes = ['Title', 'Description'];
    render(<SearchBox searchScopes={scopes} onScopeChange={onScopeChange} />);
    
    const scopeButton = screen.getByText('Description');
    fireEvent.click(scopeButton);
    
    expect(onScopeChange).toHaveBeenCalledWith('Description');
  });

  it('supports auto-complete functionality', () => {
    render(<SearchBox autoComplete suggestions={mockSuggestions} />);
    
    const input = screen.getByTestId('searchbox-input');
    fireEvent.change(input, { target: { value: 'apple' } });
    fireEvent.keyDown(input, { key: 'Tab' });
    
    expect(input).toHaveValue('Apple iPhone');
  });

  it('supports search shortcuts', () => {
    const shortcuts = [
      { key: 'ctrl+k', description: 'Focus search' },
      { key: 'ctrl+/', description: 'Show shortcuts' }
    ];
    render(<SearchBox shortcuts={shortcuts} />);
    
    expect(screen.getByTestId('shortcuts-hint')).toBeInTheDocument();
  });
});