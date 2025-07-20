import React from 'react'
import { render, screen, fireEvent } from '@testing-library/react'
import { vi } from 'vitest'
import Textarea from './Textarea'

describe('Textarea', () => {
  it('renders with default props', () => {
    render(<Textarea placeholder="Enter description" />)
    const textarea = screen.getByPlaceholderText('Enter description')
    expect(textarea).toBeInTheDocument()
    expect(textarea).toHaveClass('text-base')
    expect(textarea).toHaveAttribute('rows', '3')
  })

  it('renders with label', () => {
    render(<Textarea label="Description" placeholder="Enter description" />)
    expect(screen.getByLabelText('Description')).toBeInTheDocument()
    expect(screen.getByText('Description')).toBeInTheDocument()
  })

  it('applies variant classes correctly', () => {
    const { rerender } = render(<Textarea variant="default" />)
    expect(screen.getByRole('textbox')).toHaveClass('border-gray-300', 'bg-white')

    rerender(<Textarea variant="filled" />)
    expect(screen.getByRole('textbox')).toHaveClass('border-transparent', 'bg-gray-100')

    rerender(<Textarea variant="outline" />)
    expect(screen.getByRole('textbox')).toHaveClass('border-gray-200', 'bg-transparent')
  })

  it('applies size classes correctly', () => {
    const { rerender } = render(<Textarea size="sm" />)
    expect(screen.getByRole('textbox')).toHaveClass('text-sm', 'px-3', 'py-2')

    rerender(<Textarea size="md" />)
    expect(screen.getByRole('textbox')).toHaveClass('text-base', 'px-3', 'py-2')

    rerender(<Textarea size="lg" />)
    expect(screen.getByRole('textbox')).toHaveClass('text-lg', 'px-4', 'py-3')
  })

  it('applies resize classes correctly', () => {
    const { rerender } = render(<Textarea resize="none" />)
    expect(screen.getByRole('textbox')).toHaveClass('resize-none')

    rerender(<Textarea resize="vertical" />)
    expect(screen.getByRole('textbox')).toHaveClass('resize-y')

    rerender(<Textarea resize="horizontal" />)
    expect(screen.getByRole('textbox')).toHaveClass('resize-x')

    rerender(<Textarea resize="both" />)
    expect(screen.getByRole('textbox')).toHaveClass('resize')
  })

  it('shows error state correctly', () => {
    render(<Textarea error errorMessage="This field is required" />)
    expect(screen.getByRole('textbox')).toHaveClass('border-red-500')
    expect(screen.getByText('This field is required')).toBeInTheDocument()
    expect(document.querySelector('.lucide-alert-circle')).toBeInTheDocument()
  })

  it('shows helper text when no error', () => {
    render(<Textarea helperText="Enter a detailed description" />)
    expect(screen.getByText('Enter a detailed description')).toBeInTheDocument()
  })

  it('hides helper text when error is present', () => {
    render(<Textarea helperText="Helper text" error errorMessage="Error message" />)
    expect(screen.queryByText('Helper text')).not.toBeInTheDocument()
    expect(screen.getByText('Error message')).toBeInTheDocument()
  })

  it('shows loading spinner when loading', () => {
    render(<Textarea loading />)
    expect(document.querySelector('.animate-spin')).toBeInTheDocument()
    expect(screen.getByRole('textbox')).toBeDisabled()
  })

  it('disables textarea when disabled prop is true', () => {
    render(<Textarea disabled />)
    expect(screen.getByRole('textbox')).toBeDisabled()
  })

  it('applies custom className', () => {
    render(<Textarea className="custom-class" />)
    expect(screen.getByRole('textbox')).toHaveClass('custom-class')
  })

  it('forwards ref correctly', () => {
    const ref = React.createRef<HTMLTextAreaElement>()
    render(<Textarea ref={ref} />)
    expect(ref.current).toBeInstanceOf(HTMLTextAreaElement)
  })

  it('calls onChange handler', () => {
    const onChange = vi.fn()
    render(<Textarea onChange={onChange} />)
    
    const textarea = screen.getByRole('textbox')
    fireEvent.change(textarea, { target: { value: 'test' } })
    
    expect(onChange).toHaveBeenCalledTimes(1)
  })

  it('handles focus and blur events', () => {
    const onFocus = vi.fn()
    const onBlur = vi.fn()
    render(<Textarea onFocus={onFocus} onBlur={onBlur} />)
    
    const textarea = screen.getByRole('textbox')
    fireEvent.focus(textarea)
    expect(onFocus).toHaveBeenCalledTimes(1)
    
    fireEvent.blur(textarea)
    expect(onBlur).toHaveBeenCalledTimes(1)
  })

  it('generates unique id when not provided', () => {
    render(<Textarea label="Test" />)
    const textarea = screen.getByRole('textbox')
    const label = screen.getByText('Test')
    
    expect(textarea).toHaveAttribute('id')
    expect(label).toHaveAttribute('for', textarea.getAttribute('id'))
  })

  it('uses provided id', () => {
    render(<Textarea id="custom-id" label="Test" />)
    const textarea = screen.getByRole('textbox')
    const label = screen.getByText('Test')
    
    expect(textarea).toHaveAttribute('id', 'custom-id')
    expect(label).toHaveAttribute('for', 'custom-id')
  })

  it('uses custom rows value', () => {
    render(<Textarea rows={5} />)
    expect(screen.getByRole('textbox')).toHaveAttribute('rows', '5')
  })

  it('applies error styles with filled variant', () => {
    render(<Textarea variant="filled" error />)
    expect(screen.getByRole('textbox')).toHaveClass('bg-red-50', 'border-red-200')
  })

  it('applies error styles with outline variant', () => {
    render(<Textarea variant="outline" error />)
    expect(screen.getByRole('textbox')).toHaveClass('border-red-500')
  })

  it('shows correct label color for error state', () => {
    render(<Textarea label="Description" error />)
    expect(screen.getByText('Description')).toHaveClass('text-red-700')
  })

  it('shows correct label color for normal state', () => {
    render(<Textarea label="Description" />)
    expect(screen.getByText('Description')).toHaveClass('text-gray-700')
  })
})