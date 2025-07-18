import { render, screen, fireEvent } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import Button from './Button'

describe('Button', () => {
  it('renders with default props', () => {
    render(<Button>Click me</Button>)
    const button = screen.getByRole('button', { name: 'Click me' })
    expect(button).toBeInTheDocument()
    expect(button).toHaveClass('inline-flex', 'items-center', 'justify-center')
  })

  it('handles click events', () => {
    const handleClick = vi.fn()
    render(<Button onClick={handleClick}>Click me</Button>)
    
    fireEvent.click(screen.getByRole('button'))
    expect(handleClick).toHaveBeenCalledTimes(1)
  })

  it('applies variant styles correctly', () => {
    render(<Button variant="primary">Primary</Button>)
    const button = screen.getByRole('button')
    expect(button).toHaveClass('bg-blue-600', 'text-white')
  })

  it('applies size styles correctly', () => {
    render(<Button size="lg">Large</Button>)
    const button = screen.getByRole('button')
    expect(button).toHaveClass('h-12', 'px-6', 'text-lg')
  })

  it('applies fullWidth correctly', () => {
    render(<Button fullWidth>Full Width</Button>)
    const button = screen.getByRole('button')
    expect(button).toHaveClass('w-full')
  })

  it('shows loading state', () => {
    render(<Button loading>Loading</Button>)
    const button = screen.getByRole('button')
    expect(button).toBeDisabled()
    expect(button.querySelector('.animate-spin')).toBeInTheDocument()
  })

  it('is disabled when disabled prop is true', () => {
    render(<Button disabled>Disabled</Button>)
    const button = screen.getByRole('button')
    expect(button).toBeDisabled()
    expect(button).toHaveClass('disabled:pointer-events-none', 'disabled:opacity-50')
  })

  it('renders icon on the left by default', () => {
    const icon = <span data-testid="icon">🚀</span>
    render(<Button icon={icon}>With Icon</Button>)
    
    const iconElement = screen.getByTestId('icon')
    expect(iconElement).toBeInTheDocument()
    
    // Check if icon is before text
    const iconParent = iconElement.parentElement
    expect(iconParent).toHaveClass('mr-2')
  })

  it('renders icon on the right when iconPosition is right', () => {
    const icon = <span data-testid="icon">🚀</span>
    render(<Button icon={icon} iconPosition="right">With Icon</Button>)
    
    const iconElement = screen.getByTestId('icon')
    const iconParent = iconElement.parentElement
    expect(iconParent).toHaveClass('ml-2')
  })

  it('hides icon when loading', () => {
    const icon = <span data-testid="icon">🚀</span>
    render(<Button icon={icon} loading>Loading</Button>)
    
    const iconElement = screen.getByTestId('icon')
    const iconParent = iconElement.parentElement
    expect(iconParent).toHaveClass('opacity-0')
  })

  it('applies custom className', () => {
    render(<Button className="custom-class">Custom</Button>)
    const button = screen.getByRole('button')
    expect(button).toHaveClass('custom-class')
  })

  it('forwards ref correctly', () => {
    const ref = vi.fn()
    render(<Button ref={ref}>Ref Button</Button>)
    expect(ref).toHaveBeenCalled()
  })

  it('passes through button props', () => {
    render(<Button type="submit" name="submit-button">Submit</Button>)
    const button = screen.getByRole('button')
    expect(button).toHaveAttribute('type', 'submit')
    expect(button).toHaveAttribute('name', 'submit-button')
  })

  describe('variants', () => {
    const variants = [
      { variant: 'default' as const, expectedClasses: ['bg-primary', 'text-primary-foreground'] },
      { variant: 'primary' as const, expectedClasses: ['bg-blue-600', 'text-white'] },
      { variant: 'secondary' as const, expectedClasses: ['bg-gray-100', 'text-gray-900'] },
      { variant: 'outline' as const, expectedClasses: ['border', 'border-input'] },
      { variant: 'ghost' as const, expectedClasses: ['hover:bg-accent'] },
      { variant: 'destructive' as const, expectedClasses: ['bg-red-600', 'text-white'] }
    ]

    variants.forEach(({ variant, expectedClasses }) => {
      it(`renders ${variant} variant correctly`, () => {
        render(<Button variant={variant}>{variant}</Button>)
        const button = screen.getByRole('button')
        expectedClasses.forEach(className => {
          expect(button).toHaveClass(className)
        })
      })
    })
  })

  describe('sizes', () => {
    const sizes = [
      { size: 'sm' as const, expectedClasses: ['h-8', 'px-3', 'text-sm'] },
      { size: 'md' as const, expectedClasses: ['h-10', 'px-4', 'py-2'] },
      { size: 'lg' as const, expectedClasses: ['h-12', 'px-6', 'text-lg'] }
    ]

    sizes.forEach(({ size, expectedClasses }) => {
      it(`renders ${size} size correctly`, () => {
        render(<Button size={size}>{size}</Button>)
        const button = screen.getByRole('button')
        expectedClasses.forEach(className => {
          expect(button).toHaveClass(className)
        })
      })
    })
  })
})