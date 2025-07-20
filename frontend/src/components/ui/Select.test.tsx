import React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { vi } from 'vitest'
import Select, { SelectOption } from './Select'

const mockOptions: SelectOption[] = [
  { value: 'option1', label: 'Option 1' },
  { value: 'option2', label: 'Option 2' },
  { value: 'option3', label: 'Option 3' },
  { value: 'option4', label: 'Option 4', disabled: true },
]

describe('Select', () => {
  it('renders with default props', () => {
    render(<Select options={mockOptions} />)
    expect(screen.getByRole('combobox')).toBeInTheDocument()
    expect(screen.getByText('Select option...')).toBeInTheDocument()
  })

  it('renders with label', () => {
    render(<Select options={mockOptions} label="Choose option" />)
    expect(screen.getByText('Choose option')).toBeInTheDocument()
  })

  it('opens dropdown when clicked', () => {
    render(<Select options={mockOptions} />)
    const combobox = screen.getByRole('combobox')
    
    fireEvent.click(combobox)
    
    expect(screen.getByRole('option', { name: 'Option 1' })).toBeInTheDocument()
    expect(screen.getByRole('option', { name: 'Option 2' })).toBeInTheDocument()
    expect(screen.getByRole('option', { name: 'Option 3' })).toBeInTheDocument()
  })

  it('selects option when clicked', () => {
    const onChange = vi.fn()
    render(<Select options={mockOptions} onChange={onChange} />)
    
    fireEvent.click(screen.getByRole('combobox'))
    fireEvent.click(screen.getByRole('option', { name: 'Option 1' }))
    
    expect(onChange).toHaveBeenCalledWith('option1')
  })

  it('shows placeholder when no value selected', () => {
    render(<Select options={mockOptions} placeholder="Custom placeholder" />)
    expect(screen.getByText('Custom placeholder')).toBeInTheDocument()
  })

  it('displays selected value', () => {
    render(<Select options={mockOptions} value="option2" />)
    
    // The combobox should show the selected value instead of placeholder
    const combobox = screen.getByRole('combobox')
    expect(combobox).toHaveTextContent('Option 2')
  })

  it('handles multiple selection', () => {
    const onChange = vi.fn()
    render(<Select options={mockOptions} multiple onChange={onChange} />)
    
    fireEvent.click(screen.getByRole('combobox'))
    fireEvent.click(screen.getByRole('option', { name: 'Option 1' }))
    
    expect(onChange).toHaveBeenNthCalledWith(1, ['option1'])
    
    fireEvent.click(screen.getByRole('option', { name: 'Option 2' }))
    expect(onChange).toHaveBeenNthCalledWith(2, ['option2'])
  })

  it('shows multiple selected values as tags', () => {
    render(<Select options={mockOptions} value={['option1', 'option2']} multiple />)
    
    // Check for specific tag text content (avoiding hidden select options)
    const tags = screen.getAllByText('Option 1').filter(el => el.closest('.bg-blue-100'))
    expect(tags).toHaveLength(1)
    
    const tags2 = screen.getAllByText('Option 2').filter(el => el.closest('.bg-blue-100'))
    expect(tags2).toHaveLength(1)
  })

  it('removes selected option in multiple mode', () => {
    const onChange = vi.fn()
    render(
      <Select 
        options={mockOptions} 
        value={['option1', 'option2']} 
        multiple 
        onChange={onChange} 
      />
    )
    
    // Find X buttons within the tags and click the first one
    const removeButtons = screen.getAllByRole('button')
    const firstTagRemoveButton = removeButtons.find(button => button.querySelector('svg.lucide-x'))
    fireEvent.click(firstTagRemoveButton!)
    
    expect(onChange).toHaveBeenCalledWith(['option2'])
  })

  it('shows search input when searchable', () => {
    render(<Select options={mockOptions} searchable />)
    
    fireEvent.click(screen.getByRole('combobox'))
    
    expect(screen.getByPlaceholderText('Search options...')).toBeInTheDocument()
  })

  it('filters options when searching', () => {
    render(<Select options={mockOptions} searchable />)
    
    fireEvent.click(screen.getByRole('combobox'))
    
    const searchInput = screen.getByPlaceholderText('Search options...')
    fireEvent.change(searchInput, { target: { value: 'Option 1' } })
    
    expect(screen.getByRole('option', { name: 'Option 1' })).toBeInTheDocument()
    expect(screen.queryByRole('option', { name: 'Option 2' })).not.toBeInTheDocument()
  })

  it('shows "No options found" when search has no results', () => {
    render(<Select options={mockOptions} searchable />)
    
    fireEvent.click(screen.getByRole('combobox'))
    
    const searchInput = screen.getByPlaceholderText('Search options...')
    fireEvent.change(searchInput, { target: { value: 'nonexistent' } })
    
    expect(screen.getByText('No options found')).toBeInTheDocument()
  })

  it('shows clear button when clearable and has value', () => {
    render(<Select options={mockOptions} value="option1" clearable />)
    
    expect(screen.getByRole('button')).toBeInTheDocument()
  })

  it('clears value when clear button is clicked', () => {
    const onChange = vi.fn()
    render(<Select options={mockOptions} value="option1" clearable onChange={onChange} />)
    
    fireEvent.click(screen.getByRole('button'))
    
    expect(onChange).toHaveBeenCalledWith('')
  })

  it('shows loading spinner when loading', () => {
    render(<Select options={mockOptions} loading />)
    expect(document.querySelector('.animate-spin')).toBeInTheDocument()
  })

  it('disables interaction when disabled', () => {
    render(<Select options={mockOptions} disabled />)
    const combobox = screen.getByRole('combobox')
    
    expect(combobox).toHaveAttribute('tabIndex', '-1')
    fireEvent.click(combobox)
    
    expect(screen.queryByRole('option')).not.toBeInTheDocument()
  })

  it('shows error state correctly', () => {
    render(<Select options={mockOptions} error errorMessage="This field is required" />)
    expect(screen.getByText('This field is required')).toBeInTheDocument()
    expect(document.querySelector('.lucide-alert-circle')).toBeInTheDocument()
  })

  it('shows helper text when no error', () => {
    render(<Select options={mockOptions} helperText="Choose your preferred option" />)
    expect(screen.getByText('Choose your preferred option')).toBeInTheDocument()
  })

  it('hides helper text when error is present', () => {
    render(
      <Select 
        options={mockOptions} 
        helperText="Helper text" 
        error 
        errorMessage="Error message" 
      />
    )
    expect(screen.queryByText('Helper text')).not.toBeInTheDocument()
    expect(screen.getByText('Error message')).toBeInTheDocument()
  })

  it('handles keyboard navigation', () => {
    const onChange = vi.fn()
    render(<Select options={mockOptions} onChange={onChange} />)
    const combobox = screen.getByRole('combobox')
    
    fireEvent.click(combobox)
    
    // Arrow Down should focus first option
    fireEvent.keyDown(document, { key: 'ArrowDown' })
    // Enter should select focused option
    fireEvent.keyDown(document, { key: 'Enter' })
    
    expect(onChange).toHaveBeenCalledWith('option1')
  })

  it('closes dropdown on Escape key', () => {
    render(<Select options={mockOptions} />)
    
    fireEvent.click(screen.getByRole('combobox'))
    expect(screen.getByRole('option', { name: 'Option 1' })).toBeInTheDocument()
    
    fireEvent.keyDown(document, { key: 'Escape' })
    
    expect(screen.queryByRole('option')).not.toBeInTheDocument()
  })

  it('closes dropdown when clicking outside', async () => {
    render(
      <div>
        <Select options={mockOptions} />
        <div data-testid="outside">Outside</div>
      </div>
    )
    
    fireEvent.click(screen.getByRole('combobox'))
    expect(screen.getByRole('option', { name: 'Option 1' })).toBeInTheDocument()
    
    fireEvent.mouseDown(screen.getByTestId('outside'))
    
    await waitFor(() => {
      expect(screen.queryByRole('option')).not.toBeInTheDocument()
    })
  })

  it('skips disabled options', () => {
    const onChange = vi.fn()
    render(<Select options={mockOptions} onChange={onChange} />)
    
    fireEvent.click(screen.getByRole('combobox'))
    fireEvent.click(screen.getByRole('option', { name: 'Option 4' }))
    
    expect(onChange).not.toHaveBeenCalled()
  })

  it('applies variant classes correctly', () => {
    const { rerender } = render(<Select options={mockOptions} variant="filled" />)
    expect(screen.getByRole('combobox')).toHaveClass('bg-gray-100')
    
    rerender(<Select options={mockOptions} variant="outline" />)
    expect(screen.getByRole('combobox')).toHaveClass('bg-transparent')
  })

  it('applies size classes correctly', () => {
    const { rerender } = render(<Select options={mockOptions} size="sm" />)
    expect(screen.getByRole('combobox')).toHaveClass('h-8', 'text-sm')
    
    rerender(<Select options={mockOptions} size="lg" />)
    expect(screen.getByRole('combobox')).toHaveClass('h-12', 'text-lg')
  })

  it('forwards ref correctly', () => {
    const ref = React.createRef<HTMLDivElement>()
    render(<Select options={mockOptions} ref={ref} />)
    expect(ref.current).toBeInstanceOf(HTMLDivElement)
  })

  it('generates unique id when not provided', () => {
    render(<Select options={mockOptions} label="Test" />)
    const combobox = screen.getByRole('combobox')
    const label = screen.getByText('Test')
    
    expect(combobox).toHaveAttribute('id')
    expect(label).toHaveAttribute('for', combobox.getAttribute('id'))
  })

  it('uses provided id', () => {
    render(<Select options={mockOptions} id="custom-id" label="Test" />)
    const combobox = screen.getByRole('combobox')
    const label = screen.getByText('Test')
    
    expect(combobox).toHaveAttribute('id', 'custom-id')
    expect(label).toHaveAttribute('for', 'custom-id')
  })

  it('applies custom className', () => {
    render(<Select options={mockOptions} className="custom-class" />)
    expect(screen.getByRole('combobox')).toHaveClass('custom-class')
  })
})