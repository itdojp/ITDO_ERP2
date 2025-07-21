import React from 'react'
import { render, screen, fireEvent } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import Button from './Button'

describe('Button Component', () => {
  it('renders correctly with default props', () => {
    render(<Button>Click me</Button>)
    const button = screen.getByRole('button', { name: /click me/i })
    expect(button).toBeInTheDocument()
    expect(button).toHaveClass('h-10', 'px-4', 'py-2')
  })

  it('renders different variants correctly', () => {
    const { rerender } = render(<Button variant="primary">Primary</Button>)
    expect(screen.getByRole('button')).toHaveClass('bg-blue-600')

    rerender(<Button variant="secondary">Secondary</Button>)
    expect(screen.getByRole('button')).toHaveClass('bg-gray-100')

    rerender(<Button variant="danger">Danger</Button>)
    expect(screen.getByRole('button')).toHaveClass('bg-red-600')

    rerender(<Button variant="outline">Outline</Button>)
    expect(screen.getByRole('button')).toHaveClass('border', 'border-gray-300')

    rerender(<Button variant="ghost">Ghost</Button>)
    expect(screen.getByRole('button')).toHaveClass('bg-transparent')
  })

  it('renders different sizes correctly', () => {
    const { rerender } = render(<Button size="xs">Extra Small</Button>)
    expect(screen.getByRole('button')).toHaveClass('h-6', 'px-2', 'text-xs')

    rerender(<Button size="sm">Small</Button>)
    expect(screen.getByRole('button')).toHaveClass('h-8', 'px-3', 'text-sm')

    rerender(<Button size="md">Medium</Button>)
    expect(screen.getByRole('button')).toHaveClass('h-10', 'px-4', 'py-2', 'text-base')

    rerender(<Button size="lg">Large</Button>)
    expect(screen.getByRole('button')).toHaveClass('h-12', 'px-6', 'text-lg')

    rerender(<Button size="xl">Extra Large</Button>)
    expect(screen.getByRole('button')).toHaveClass('h-14', 'px-8', 'text-xl')
  })

  it('handles loading state correctly', () => {
    render(<Button loading>Loading Button</Button>)
    const button = screen.getByRole('button')
    
    expect(button).toBeDisabled()
    expect(button).toHaveAttribute('aria-busy', 'true')
    expect(button.querySelector('.animate-spin')).toBeInTheDocument()
  })

  it('handles disabled state correctly', () => {
    render(<Button disabled>Disabled Button</Button>)
    const button = screen.getByRole('button')
    
    expect(button).toBeDisabled()
    expect(button).toHaveClass('disabled:pointer-events-none', 'disabled:opacity-50')
  })

  it('renders full width correctly', () => {
    render(<Button fullWidth>Full Width</Button>)
    expect(screen.getByRole('button')).toHaveClass('w-full')
  })

  it('renders with left icon correctly', () => {
    const TestIcon = () => <span data-testid="test-icon">🔥</span>
    render(
      <Button icon={<TestIcon />} iconPosition="left">
        With Icon
      </Button>
    )
    
    const button = screen.getByRole('button')
    const icon = screen.getByTestId('test-icon')
    
    expect(button).toBeInTheDocument()
    expect(icon).toBeInTheDocument()
    expect(icon.parentElement).toHaveClass('mr-2')
  })

  it('renders with right icon correctly', () => {
    const TestIcon = () => <span data-testid="test-icon">🔥</span>
    render(
      <Button icon={<TestIcon />} iconPosition="right">
        With Icon
      </Button>
    )
    
    const icon = screen.getByTestId('test-icon')
    expect(icon.parentElement).toHaveClass('ml-2')
  })

  it('hides icon when loading', () => {
    const TestIcon = () => <span data-testid="test-icon">🔥</span>
    render(
      <Button icon={<TestIcon />} loading>
        Loading with Icon
      </Button>
    )
    
    const icon = screen.getByTestId('test-icon')
    expect(icon.parentElement).toHaveClass('opacity-0')
  })

  it('handles different rounded options', () => {
    const { rerender } = render(<Button rounded="none">Square</Button>)
    expect(screen.getByRole('button')).toHaveClass('rounded-none')

    rerender(<Button rounded="full">Pill</Button>)
    expect(screen.getByRole('button')).toHaveClass('rounded-full')

    rerender(<Button rounded="lg">Large Rounded</Button>)
    expect(screen.getByRole('button')).toHaveClass('rounded-lg')
  })

  it('handles click events correctly', () => {
    const handleClick = vi.fn()
    render(<Button onClick={handleClick}>Clickable</Button>)
    
    fireEvent.click(screen.getByRole('button'))
    expect(handleClick).toHaveBeenCalledTimes(1)
  })

  it('does not trigger click when disabled', () => {
    const handleClick = vi.fn()
    render(<Button onClick={handleClick} disabled>Disabled</Button>)
    
    fireEvent.click(screen.getByRole('button'))
    expect(handleClick).not.toHaveBeenCalled()
  })

  it('does not trigger click when loading', () => {
    const handleClick = vi.fn()
    render(<Button onClick={handleClick} loading>Loading</Button>)
    
    fireEvent.click(screen.getByRole('button'))
    expect(handleClick).not.toHaveBeenCalled()
  })

  it('forwards ref correctly', () => {
    const ref = React.createRef<HTMLButtonElement>()
    render(<Button ref={ref}>Ref Button</Button>)
    
    expect(ref.current).toBeInstanceOf(HTMLButtonElement)
    expect(ref.current?.textContent).toBe('Ref Button')
  })

  it('applies custom className correctly', () => {
    render(<Button className="custom-class">Custom</Button>)
    expect(screen.getByRole('button')).toHaveClass('custom-class')
  })

  it('passes through HTML button attributes', () => {
    render(
      <Button 
        type="submit" 
        name="test-button"
        data-testid="button-test"
        aria-label="Test button"
      >
        Submit
      </Button>
    )
    
    const button = screen.getByRole('button')
    expect(button).toHaveAttribute('type', 'submit')
    expect(button).toHaveAttribute('name', 'test-button')
    expect(button).toHaveAttribute('data-testid', 'button-test')
    expect(button).toHaveAttribute('aria-label', 'Test button')
  })

  it('has correct accessibility attributes', () => {
    render(<Button>Accessible Button</Button>)
    const button = screen.getByRole('button')
    
    expect(button).toHaveAttribute('type', 'button')
    expect(button).not.toHaveAttribute('aria-busy')
  })

  it('has correct accessibility attributes when loading', () => {
    render(<Button loading>Loading Button</Button>)
    const button = screen.getByRole('button')
    
    expect(button).toHaveAttribute('aria-busy', 'true')
  })
})