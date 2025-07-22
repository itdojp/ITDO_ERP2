import { render, fireEvent, waitFor } from '@testing-library/react';
import { SearchInput } from './SearchInput';

describe('SearchInput', () => {
  it('renders with placeholder', () => {
    const { getByPlaceholderText } = render(
      <SearchInput placeholder="Search items..." />
    );
    expect(getByPlaceholderText('Search items...')).toBeInTheDocument();
  });

  it('calls onChange when input value changes', () => {
    const handleChange = jest.fn();
    const { getByRole } = render(
      <SearchInput onChange={handleChange} />
    );
    
    const input = getByRole('textbox');
    fireEvent.change(input, { target: { value: 'test' } });
    
    expect(handleChange).toHaveBeenCalledWith('test');
  });

  it('calls onSearch when Enter is pressed', () => {
    const handleSearch = jest.fn();
    const { getByRole } = render(
      <SearchInput onSearch={handleSearch} />
    );
    
    const input = getByRole('textbox');
    fireEvent.change(input, { target: { value: 'test' } });
    fireEvent.keyPress(input, { key: 'Enter' });
    
    expect(handleSearch).toHaveBeenCalledWith('test');
  });

  it('debounces search calls', async () => {
    const handleSearch = jest.fn();
    const { getByRole } = render(
      <SearchInput onSearch={handleSearch} debounceMs={300} />
    );
    
    const input = getByRole('textbox');
    fireEvent.change(input, { target: { value: 'test' } });
    
    expect(handleSearch).not.toHaveBeenCalled();
    
    await waitFor(() => {
      expect(handleSearch).toHaveBeenCalledWith('test');
    }, { timeout: 400 });
  });

  it('shows clear button when there is text', () => {
    const { getByRole, container } = render(
      <SearchInput value="test" showClearButton />
    );
    
    const clearButton = container.querySelector('button');
    expect(clearButton).toBeInTheDocument();
  });

  it('clears input when clear button is clicked', () => {
    const handleChange = jest.fn();
    const handleClear = jest.fn();
    const { container } = render(
      <SearchInput value="test" onChange={handleChange} onClear={handleClear} />
    );
    
    const clearButton = container.querySelector('button');
    fireEvent.click(clearButton!);
    
    expect(handleChange).toHaveBeenCalledWith('');
    expect(handleClear).toHaveBeenCalled();
  });

  it('shows loading spinner when loading', () => {
    const { container } = render(
      <SearchInput loading />
    );
    
    const spinner = container.querySelector('.animate-spin');
    expect(spinner).toBeInTheDocument();
  });

  it('applies correct size classes', () => {
    const { getByRole } = render(
      <SearchInput size="lg" />
    );
    
    const input = getByRole('textbox');
    expect(input).toHaveClass('h-12', 'text-lg', 'px-5');
  });
});