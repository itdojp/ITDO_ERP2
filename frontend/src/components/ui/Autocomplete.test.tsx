import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { vi } from 'vitest';
import { Autocomplete } from './Autocomplete';

describe('Autocomplete', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  const mockOptions = [
    { value: 'apple', label: 'Apple' },
    { value: 'banana', label: 'Banana' },
    { value: 'cherry', label: 'Cherry' },
    { value: 'date', label: 'Date' },
    { value: 'elderberry', label: 'Elderberry' }
  ];

  it('renders autocomplete input', () => {
    render(<Autocomplete options={mockOptions} />);
    
    expect(screen.getByTestId('autocomplete-container')).toBeInTheDocument();
    expect(screen.getByTestId('autocomplete-input')).toBeInTheDocument();
  });

  it('shows dropdown when focused', () => {
    render(<Autocomplete options={mockOptions} />);
    
    const input = screen.getByTestId('autocomplete-input');
    fireEvent.focus(input);
    
    expect(screen.getByTestId('autocomplete-dropdown')).toBeInTheDocument();
  });

  it('filters options based on input', () => {
    render(<Autocomplete options={mockOptions} />);
    
    const input = screen.getByTestId('autocomplete-input');
    fireEvent.focus(input);
    fireEvent.change(input, { target: { value: 'ap' } });
    
    expect(screen.getByText('Apple')).toBeInTheDocument();
    expect(screen.queryByText('Banana')).not.toBeInTheDocument();
  });

  it('handles option selection', () => {
    const onSelect = vi.fn();
    render(<Autocomplete options={mockOptions} onSelect={onSelect} />);
    
    const input = screen.getByTestId('autocomplete-input');
    fireEvent.focus(input);
    
    const option = screen.getByText('Apple');
    fireEvent.click(option);
    
    expect(onSelect).toHaveBeenCalledWith({ value: 'apple', label: 'Apple' });
    expect(input).toHaveValue('Apple');
  });

  it('supports keyboard navigation', () => {
    render(<Autocomplete options={mockOptions} />);
    
    const input = screen.getByTestId('autocomplete-input');
    fireEvent.focus(input);
    
    // Arrow down should highlight first option
    fireEvent.keyDown(input, { key: 'ArrowDown' });
    expect(screen.getByText('Apple')).toHaveClass('highlighted');
    
    // Arrow down again should highlight second option
    fireEvent.keyDown(input, { key: 'ArrowDown' });
    expect(screen.getByText('Banana')).toHaveClass('highlighted');
    
    // Arrow up should go back to first option
    fireEvent.keyDown(input, { key: 'ArrowUp' });
    expect(screen.getByText('Apple')).toHaveClass('highlighted');
  });

  it('selects option with Enter key', () => {
    const onSelect = vi.fn();
    render(<Autocomplete options={mockOptions} onSelect={onSelect} />);
    
    const input = screen.getByTestId('autocomplete-input');
    fireEvent.focus(input);
    fireEvent.keyDown(input, { key: 'ArrowDown' });
    fireEvent.keyDown(input, { key: 'Enter' });
    
    expect(onSelect).toHaveBeenCalledWith({ value: 'apple', label: 'Apple' });
  });

  it('closes dropdown with Escape key', () => {
    render(<Autocomplete options={mockOptions} />);
    
    const input = screen.getByTestId('autocomplete-input');
    fireEvent.focus(input);
    
    expect(screen.getByTestId('autocomplete-dropdown')).toBeInTheDocument();
    
    fireEvent.keyDown(input, { key: 'Escape' });
    expect(screen.queryByTestId('autocomplete-dropdown')).not.toBeInTheDocument();
  });

  it('supports custom filtering', () => {
    const customFilter = (option: any, inputValue: string) => 
      option.label.toLowerCase().includes(inputValue.toLowerCase());
    
    render(<Autocomplete options={mockOptions} filterFunction={customFilter} />);
    
    const input = screen.getByTestId('autocomplete-input');
    fireEvent.focus(input);
    fireEvent.change(input, { target: { value: 'err' } });
    
    expect(screen.getByText('Cherry')).toBeInTheDocument();
    expect(screen.getByText('Elderberry')).toBeInTheDocument();
  });

  it('supports multiple selection', () => {
    const onSelect = vi.fn();
    render(<Autocomplete options={mockOptions} multiple onSelect={onSelect} />);
    
    const input = screen.getByTestId('autocomplete-input');
    fireEvent.focus(input);
    
    fireEvent.click(screen.getByText('Apple'));
    fireEvent.click(screen.getByText('Banana'));
    
    expect(onSelect).toHaveBeenCalledTimes(2);
    expect(screen.getByTestId('selected-items')).toBeInTheDocument();
  });

  it('displays loading state', () => {
    render(<Autocomplete options={[]} loading />);
    
    expect(screen.getByTestId('autocomplete-loading')).toBeInTheDocument();
  });

  it('shows no results message', () => {
    render(<Autocomplete options={mockOptions} />);
    
    const input = screen.getByTestId('autocomplete-input');
    fireEvent.focus(input);
    fireEvent.change(input, { target: { value: 'xyz' } });
    
    expect(screen.getByTestId('no-results')).toBeInTheDocument();
  });

  it('supports async options loading', async () => {
    const asyncOptions = vi.fn().mockResolvedValue(mockOptions);
    render(<Autocomplete loadOptions={asyncOptions} />);
    
    const input = screen.getByTestId('autocomplete-input');
    fireEvent.focus(input);
    fireEvent.change(input, { target: { value: 'ap' } });
    
    await waitFor(() => {
      expect(asyncOptions).toHaveBeenCalledWith('ap');
    });
  });

  it('supports grouping options', () => {
    const groupedOptions = [
      { value: 'red', label: 'Red', group: 'Colors' },
      { value: 'blue', label: 'Blue', group: 'Colors' },
      { value: 'apple', label: 'Apple', group: 'Fruits' },
      { value: 'banana', label: 'Banana', group: 'Fruits' }
    ];
    
    render(<Autocomplete options={groupedOptions} groupBy="group" />);
    
    const input = screen.getByTestId('autocomplete-input');
    fireEvent.focus(input);
    
    expect(screen.getByText('Colors')).toBeInTheDocument();
    expect(screen.getByText('Fruits')).toBeInTheDocument();
  });

  it('handles disabled state', () => {
    render(<Autocomplete options={mockOptions} disabled />);
    
    const input = screen.getByTestId('autocomplete-input');
    expect(input).toBeDisabled();
    
    fireEvent.focus(input);
    expect(screen.queryByTestId('autocomplete-dropdown')).not.toBeInTheDocument();
  });

  it('supports placeholder text', () => {
    render(<Autocomplete options={mockOptions} placeholder="Search items..." />);
    
    const input = screen.getByTestId('autocomplete-input');
    expect(input).toHaveAttribute('placeholder', 'Search items...');
  });

  it('supports different sizes', () => {
    const sizes = ['sm', 'md', 'lg'] as const;
    
    sizes.forEach(size => {
      const { unmount } = render(<Autocomplete options={mockOptions} size={size} />);
      const container = screen.getByTestId('autocomplete-container');
      expect(container).toHaveClass(`size-${size}`);
      unmount();
    });
  });

  it('supports different themes', () => {
    const themes = ['light', 'dark'] as const;
    
    themes.forEach(theme => {
      const { unmount } = render(<Autocomplete options={mockOptions} theme={theme} />);
      const container = screen.getByTestId('autocomplete-container');
      expect(container).toHaveClass(`theme-${theme}`);
      unmount();
    });
  });

  it('shows clear button when clearable', () => {
    render(<Autocomplete options={mockOptions} clearable />);
    
    const input = screen.getByTestId('autocomplete-input');
    fireEvent.change(input, { target: { value: 'test' } });
    
    expect(screen.getByTestId('clear-button')).toBeInTheDocument();
  });

  it('clears input when clear button clicked', () => {
    const onClear = vi.fn();
    render(<Autocomplete options={mockOptions} clearable onClear={onClear} />);
    
    const input = screen.getByTestId('autocomplete-input');
    fireEvent.change(input, { target: { value: 'test' } });
    
    const clearButton = screen.getByTestId('clear-button');
    fireEvent.click(clearButton);
    
    expect(input).toHaveValue('');
    expect(onClear).toHaveBeenCalled();
  });

  it('supports custom option rendering', () => {
    const renderOption = (option: any) => (
      <div data-testid="custom-option">
        <strong>{option.label}</strong> - {option.value}
      </div>
    );
    
    render(<Autocomplete options={mockOptions} renderOption={renderOption} />);
    
    const input = screen.getByTestId('autocomplete-input');
    fireEvent.focus(input);
    
    expect(screen.getAllByTestId('custom-option')).toHaveLength(mockOptions.length);
  });

  it('supports value prop for controlled component', () => {
    const { rerender } = render(<Autocomplete options={mockOptions} value="apple" />);
    
    const input = screen.getByTestId('autocomplete-input');
    expect(input).toHaveValue('Apple');
    
    rerender(<Autocomplete options={mockOptions} value="banana" />);
    expect(input).toHaveValue('Banana');
  });

  it('supports defaultValue prop', () => {
    render(<Autocomplete options={mockOptions} defaultValue="cherry" />);
    
    const input = screen.getByTestId('autocomplete-input');
    expect(input).toHaveValue('Cherry');
  });

  it('handles focus and blur events', () => {
    const onFocus = vi.fn();
    const onBlur = vi.fn();
    render(<Autocomplete options={mockOptions} onFocus={onFocus} onBlur={onBlur} />);
    
    const input = screen.getByTestId('autocomplete-input');
    fireEvent.focus(input);
    expect(onFocus).toHaveBeenCalled();
    
    fireEvent.blur(input);
    expect(onBlur).toHaveBeenCalled();
  });

  it('shows helper text', () => {
    render(<Autocomplete options={mockOptions} helperText="Start typing to search" />);
    
    expect(screen.getByText('Start typing to search')).toBeInTheDocument();
  });

  it('shows error state', () => {
    render(<Autocomplete options={mockOptions} error="Invalid selection" />);
    
    const container = screen.getByTestId('autocomplete-container');
    expect(container).toHaveClass('error');
    expect(screen.getByText('Invalid selection')).toBeInTheDocument();
  });

  it('supports label', () => {
    render(<Autocomplete options={mockOptions} label="Select item" />);
    
    expect(screen.getByText('Select item')).toBeInTheDocument();
  });

  it('marks required field', () => {
    render(<Autocomplete options={mockOptions} label="Select item" required />);
    
    expect(screen.getByText('*')).toBeInTheDocument();
  });

  it('supports custom input props', () => {
    render(<Autocomplete options={mockOptions} inputProps={{ 'data-custom': 'test' }} />);
    
    const input = screen.getByTestId('autocomplete-input');
    expect(input).toHaveAttribute('data-custom', 'test');
  });

  it('handles click outside to close dropdown', () => {
    render(<Autocomplete options={mockOptions} />);
    
    const input = screen.getByTestId('autocomplete-input');
    fireEvent.focus(input);
    
    expect(screen.getByTestId('autocomplete-dropdown')).toBeInTheDocument();
    
    fireEvent.mouseDown(document.body);
    expect(screen.queryByTestId('autocomplete-dropdown')).not.toBeInTheDocument();
  });

  it('supports maximum options display', () => {
    render(<Autocomplete options={mockOptions} maxOptions={3} />);
    
    const input = screen.getByTestId('autocomplete-input');
    fireEvent.focus(input);
    
    const options = screen.getAllByRole('option');
    expect(options).toHaveLength(3);
  });

  it('highlights search text in options', () => {
    render(<Autocomplete options={mockOptions} highlightMatch />);
    
    const input = screen.getByTestId('autocomplete-input');
    fireEvent.focus(input);
    fireEvent.change(input, { target: { value: 'ap' } });
    
    expect(screen.getByTestId('highlighted-text')).toBeInTheDocument();
  });

  it('supports custom loading component', () => {
    const LoadingComponent = () => <div data-testid="custom-loading">Searching...</div>;
    render(<Autocomplete options={[]} loading loadingComponent={<LoadingComponent />} />);
    
    expect(screen.getByTestId('custom-loading')).toBeInTheDocument();
  });

  it('supports custom no results component', () => {
    const NoResultsComponent = () => <div data-testid="custom-no-results">No matches found</div>;
    render(<Autocomplete options={mockOptions} noResultsComponent={<NoResultsComponent />} />);
    
    const input = screen.getByTestId('autocomplete-input');
    fireEvent.focus(input);
    fireEvent.change(input, { target: { value: 'xyz' } });
    
    expect(screen.getByTestId('custom-no-results')).toBeInTheDocument();
  });

  it('supports minimum search length', () => {
    render(<Autocomplete options={mockOptions} minSearchLength={3} />);
    
    const input = screen.getByTestId('autocomplete-input');
    fireEvent.focus(input);
    fireEvent.change(input, { target: { value: 'ap' } });
    
    expect(screen.queryByText('Apple')).not.toBeInTheDocument();
    
    fireEvent.change(input, { target: { value: 'app' } });
    expect(screen.getByText('Apple')).toBeInTheDocument();
  });

  it('supports creation of new options', () => {
    const onCreate = vi.fn();
    render(<Autocomplete options={mockOptions} allowCreate onCreate={onCreate} />);
    
    const input = screen.getByTestId('autocomplete-input');
    fireEvent.focus(input);
    fireEvent.change(input, { target: { value: 'new item' } });
    
    const createOption = screen.getByTestId('create-option');
    fireEvent.click(createOption);
    
    expect(onCreate).toHaveBeenCalledWith('new item');
  });

  it('supports debounced search', async () => {
    const loadOptions = vi.fn().mockResolvedValue(mockOptions);
    render(<Autocomplete loadOptions={loadOptions} debounceMs={100} />);
    
    const input = screen.getByTestId('autocomplete-input');
    fireEvent.focus(input);
    fireEvent.change(input, { target: { value: 'a' } });
    fireEvent.change(input, { target: { value: 'ap' } });
    fireEvent.change(input, { target: { value: 'app' } });
    
    // Should not call immediately
    expect(loadOptions).not.toHaveBeenCalled();
    
    // Should call after debounce
    await waitFor(() => {
      expect(loadOptions).toHaveBeenCalledWith('app');
    }, { timeout: 200 });
  });

  it('supports custom styling', () => {
    render(<Autocomplete options={mockOptions} className="custom-autocomplete" />);
    
    const container = screen.getByTestId('autocomplete-container');
    expect(container).toHaveClass('custom-autocomplete');
  });

  it('supports custom data attributes', () => {
    render(<Autocomplete options={mockOptions} data-category="search" data-id="main-search" />);
    
    const container = screen.getByTestId('autocomplete-container');
    expect(container).toHaveAttribute('data-category', 'search');
    expect(container).toHaveAttribute('data-id', 'main-search');
  });

  it('handles empty options array', () => {
    render(<Autocomplete options={[]} />);
    
    const input = screen.getByTestId('autocomplete-input');
    fireEvent.focus(input);
    
    expect(screen.getByTestId('no-results')).toBeInTheDocument();
  });

  it('supports prefix and suffix components', () => {
    render(
      <Autocomplete 
        options={mockOptions} 
        prefix={<span data-testid="prefix">🔍</span>}
        suffix={<span data-testid="suffix">⬇️</span>}
      />
    );
    
    expect(screen.getByTestId('prefix')).toBeInTheDocument();
    expect(screen.getByTestId('suffix')).toBeInTheDocument();
  });

  it('handles virtualization for large option lists', () => {
    const largeOptions = Array.from({ length: 1000 }, (_, i) => ({
      value: `item-${i}`,
      label: `Item ${i}`
    }));
    
    render(<Autocomplete options={largeOptions} virtualized />);
    
    const input = screen.getByTestId('autocomplete-input');
    fireEvent.focus(input);
    
    expect(screen.getByTestId('virtualized-list')).toBeInTheDocument();
  });
});