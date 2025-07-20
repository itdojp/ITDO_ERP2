import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import { act } from 'react'
import LoadingSpinner from './LoadingSpinner'

describe('LoadingSpinner', () => {
  it('renders with default props', () => {
    act(() => {
      render(<LoadingSpinner />)
    })
    
    const spinner = screen.getByRole('status')
    expect(spinner).toBeInTheDocument()
    expect(spinner).toHaveAttribute('aria-label', 'Loading...')
    expect(spinner).toHaveClass('animate-spin', 'rounded-full', 'border-2')
  })

  it('renders with small size', () => {
    act(() => {
      render(<LoadingSpinner size="small" />)
    })
    
    const spinner = screen.getByRole('status')
    expect(spinner).toHaveClass('h-4', 'w-4')
  })

  it('renders with medium size (default)', () => {
    act(() => {
      render(<LoadingSpinner size="medium" />)
    })
    
    const spinner = screen.getByRole('status')
    expect(spinner).toHaveClass('h-6', 'w-6')
  })

  it('renders with large size', () => {
    act(() => {
      render(<LoadingSpinner size="large" />)
    })
    
    const spinner = screen.getByRole('status')
    expect(spinner).toHaveClass('h-8', 'w-8')
  })

  it('renders with primary color (default)', () => {
    act(() => {
      render(<LoadingSpinner color="primary" />)
    })
    
    const spinner = screen.getByRole('status')
    expect(spinner).toHaveClass('border-blue-600', 'border-t-transparent')
  })

  it('renders with secondary color', () => {
    act(() => {
      render(<LoadingSpinner color="secondary" />)
    })
    
    const spinner = screen.getByRole('status')
    expect(spinner).toHaveClass('border-gray-500', 'border-t-transparent')
  })

  it('renders with white color', () => {
    act(() => {
      render(<LoadingSpinner color="white" />)
    })
    
    const spinner = screen.getByRole('status')
    expect(spinner).toHaveClass('border-white', 'border-t-transparent')
  })

  it('applies custom className', () => {
    act(() => {
      render(<LoadingSpinner className="custom-class" />)
    })
    
    const spinner = screen.getByRole('status')
    expect(spinner).toHaveClass('custom-class')
  })

  it('forwards ref correctly', () => {
    const ref = { current: null }
    act(() => {
      render(<LoadingSpinner ref={ref} />)
    })
    
    expect(ref.current).toBeInstanceOf(HTMLDivElement)
  })

  it('passes through additional props', () => {
    act(() => {
      render(<LoadingSpinner data-testid="spinner" />)
    })
    
    const spinner = screen.getByTestId('spinner')
    expect(spinner).toBeInTheDocument()
  })

  it('contains screen reader text', () => {
    act(() => {
      render(<LoadingSpinner />)
    })
    
    const srText = screen.getByText('Loading...')
    expect(srText).toHaveClass('sr-only')
  })

  it('has proper accessibility attributes', () => {
    act(() => {
      render(<LoadingSpinner />)
    })
    
    const spinner = screen.getByRole('status')
    expect(spinner).toHaveAttribute('role', 'status')
    expect(spinner).toHaveAttribute('aria-label', 'Loading...')
  })
})