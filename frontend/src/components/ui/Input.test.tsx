import React from 'react'
import { render, screen, fireEvent } from '@testing-library/react'
import { vi } from 'vitest'
import { Search, User } from 'lucide-react'
import Input from './Input'

describe('Input', () => {
  it('renders with default props', () => {
    render(<Input placeholder="Enter text" />)
    const input = screen.getByPlaceholderText('Enter text')
    expect(input).toBeInTheDocument()
    expect(input).toHaveClass('text-base')
  })

  it('renders with label', () => {
    render(<Input label="Username" placeholder="Enter username" />)
    expect(screen.getByLabelText('Username')).toBeInTheDocument()
    expect(screen.getByText('Username')).toBeInTheDocument()
  })

  it('applies variant classes correctly', () => {
    const { rerender } = render(<Input variant="default" />)
    expect(screen.getByRole('textbox').parentElement).toHaveClass('border-gray-300', 'bg-white')

    rerender(<Input variant="filled" />)
    expect(screen.getByRole('textbox').parentElement).toHaveClass('border-transparent', 'bg-gray-100')

    rerender(<Input variant="outline" />)
    expect(screen.getByRole('textbox').parentElement).toHaveClass('border-gray-200', 'bg-transparent')
  })

  it('applies size classes correctly', () => {
    const { rerender } = render(<Input size="sm" />)
    expect(screen.getByRole('textbox').parentElement).toHaveClass('h-8')
    expect(screen.getByRole('textbox')).toHaveClass('text-sm')

    rerender(<Input size="md" />)
    expect(screen.getByRole('textbox').parentElement).toHaveClass('h-10')
    expect(screen.getByRole('textbox')).toHaveClass('text-base')

    rerender(<Input size="lg" />)
    expect(screen.getByRole('textbox').parentElement).toHaveClass('h-12')
    expect(screen.getByRole('textbox')).toHaveClass('text-lg')
  })

  it('shows error state correctly', () => {
    render(<Input error errorMessage="This field is required" />)
    expect(screen.getByRole('textbox').parentElement).toHaveClass('border-red-500')
    expect(screen.getByText('This field is required')).toBeInTheDocument()
    expect(document.querySelector('.lucide-alert-circle')).toBeInTheDocument()
  })

  it('shows helper text when no error', () => {
    render(<Input helperText="Enter your email address" />)
    expect(screen.getByText('Enter your email address')).toBeInTheDocument()
  })

  it('hides helper text when error is present', () => {
    render(<Input helperText="Helper text" error errorMessage="Error message" />)
    expect(screen.queryByText('Helper text')).not.toBeInTheDocument()
    expect(screen.getByText('Error message')).toBeInTheDocument()
  })

  it('renders left icon correctly', () => {
    render(<Input leftIcon={<User data-testid="user-icon" />} />)
    expect(screen.getByTestId('user-icon')).toBeInTheDocument()
    expect(screen.getByRole('textbox')).toHaveClass('pl-10')
  })

  it('renders right icon correctly', () => {
    render(<Input rightIcon={<Search data-testid="search-icon" />} />)
    expect(screen.getByTestId('search-icon')).toBeInTheDocument()
    expect(screen.getByRole('textbox')).toHaveClass('pr-10')
  })

  it('shows search icon for search type', () => {
    render(<Input type="search" />)
    expect(document.querySelector('.lucide-search')).toBeInTheDocument()
    expect(screen.getByRole('searchbox')).toHaveClass('pl-10')
  })

  it('shows password toggle for password type', () => {
    render(<Input type="password" />)
    const toggleButton = document.querySelector('button')
    expect(toggleButton).toBeInTheDocument()
    expect(document.querySelector('.lucide-eye')).toBeInTheDocument()
  })

  it('toggles password visibility', () => {
    render(<Input type="password" />)
    const input = document.querySelector('input[type="password"]') as HTMLInputElement
    const toggleButton = document.querySelector('button')

    expect(input).toHaveAttribute('type', 'password')

    fireEvent.click(toggleButton!)
    expect(input).toHaveAttribute('type', 'text')
    expect(document.querySelector('.lucide-eye-off')).toBeInTheDocument()

    fireEvent.click(toggleButton!)
    expect(input).toHaveAttribute('type', 'password')
    expect(document.querySelector('.lucide-eye')).toBeInTheDocument()
  })

  it('shows loading spinner when loading', () => {
    render(<Input loading />)
    expect(document.querySelector('.animate-spin')).toBeInTheDocument()
    expect(screen.getByRole('textbox')).toBeDisabled()
  })

  it('disables input when disabled prop is true', () => {
    render(<Input disabled />)
    expect(screen.getByRole('textbox')).toBeDisabled()
  })

  it('applies custom className', () => {
    render(<Input className="custom-class" />)
    expect(screen.getByRole('textbox').parentElement).toHaveClass('custom-class')
  })

  it('forwards ref correctly', () => {
    const ref = React.createRef<HTMLInputElement>()
    render(<Input ref={ref} />)
    expect(ref.current).toBeInstanceOf(HTMLInputElement)
  })

  it('calls onChange handler', () => {
    const onChange = vi.fn()
    render(<Input onChange={onChange} />)
    
    const input = screen.getByRole('textbox')
    fireEvent.change(input, { target: { value: 'test' } })
    
    expect(onChange).toHaveBeenCalledTimes(1)
  })

  it('handles focus and blur events', () => {
    const onFocus = vi.fn()
    const onBlur = vi.fn()
    render(<Input onFocus={onFocus} onBlur={onBlur} />)
    
    const input = screen.getByRole('textbox')
    fireEvent.focus(input)
    expect(onFocus).toHaveBeenCalledTimes(1)
    
    fireEvent.blur(input)
    expect(onBlur).toHaveBeenCalledTimes(1)
  })

  it('generates unique id when not provided', () => {
    render(<Input label="Test" />)
    const input = screen.getByRole('textbox')
    const label = screen.getByText('Test')
    
    expect(input).toHaveAttribute('id')
    expect(label).toHaveAttribute('for', input.getAttribute('id'))
  })

  it('uses provided id', () => {
    render(<Input id="custom-id" label="Test" />)
    const input = screen.getByRole('textbox')
    const label = screen.getByText('Test')
    
    expect(input).toHaveAttribute('id', 'custom-id')
    expect(label).toHaveAttribute('for', 'custom-id')
  })

  it('does not show search icon when leftIcon is provided for search type', () => {
    render(<Input type="search" leftIcon={<User />} />)
    expect(document.querySelectorAll('.lucide-search')).toHaveLength(0)
    expect(document.querySelector('.lucide-user')).toBeInTheDocument()
  })

  it('prioritizes loading over right icon', () => {
    render(<Input loading rightIcon={<Search />} />)
    expect(document.querySelector('.animate-spin')).toBeInTheDocument()
    expect(document.querySelectorAll('.lucide-search')).toHaveLength(0)
  })

  it('prioritizes loading over password toggle', () => {
    render(<Input type="password" loading />)
    expect(document.querySelector('.animate-spin')).toBeInTheDocument()
    expect(document.querySelectorAll('.lucide-eye')).toHaveLength(0)
  })
})