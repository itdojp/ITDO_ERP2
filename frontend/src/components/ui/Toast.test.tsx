import React from 'react'
import { render, screen, fireEvent, act } from '@testing-library/react'
import { vi } from 'vitest'
import Toast from './Toast'

// Mock timers for testing auto-close functionality
beforeEach(() => {
  vi.useFakeTimers()
})

afterEach(() => {
  vi.useRealTimers()
})

describe('Toast', () => {
  it('renders with message', () => {
    render(<Toast message="Test toast message" />)
    expect(screen.getByText('Test toast message')).toBeInTheDocument()
    expect(screen.getByRole('alert')).toBeInTheDocument()
  })

  it('renders with title and message', () => {
    render(<Toast title="Toast Title" message="Toast message" />)
    expect(screen.getByText('Toast Title')).toBeInTheDocument()
    expect(screen.getByText('Toast message')).toBeInTheDocument()
  })

  it('applies variant border classes correctly', () => {
    const { rerender } = render(<Toast message="test" variant="success" />)
    expect(screen.getByRole('alert')).toHaveClass('border-green-200')

    rerender(<Toast message="test" variant="error" />)
    expect(screen.getByRole('alert')).toHaveClass('border-red-200')

    rerender(<Toast message="test" variant="warning" />)
    expect(screen.getByRole('alert')).toHaveClass('border-yellow-200')

    rerender(<Toast message="test" variant="info" />)
    expect(screen.getByRole('alert')).toHaveClass('border-blue-200')
  })

  it('applies position classes correctly', () => {
    const { rerender } = render(<Toast message="test" position="top-right" />)
    expect(screen.getByRole('alert')).toHaveClass('top-4', 'right-4')

    rerender(<Toast message="test" position="top-left" />)
    expect(screen.getByRole('alert')).toHaveClass('top-4', 'left-4')

    rerender(<Toast message="test" position="bottom-right" />)
    expect(screen.getByRole('alert')).toHaveClass('bottom-4', 'right-4')

    rerender(<Toast message="test" position="bottom-left" />)
    expect(screen.getByRole('alert')).toHaveClass('bottom-4', 'left-4')

    rerender(<Toast message="test" position="top-center" />)
    expect(screen.getByRole('alert')).toHaveClass('top-4', 'left-1/2')

    rerender(<Toast message="test" position="bottom-center" />)
    expect(screen.getByRole('alert')).toHaveClass('bottom-4', 'left-1/2')
  })

  it('shows appropriate icon for each variant', () => {
    const { rerender } = render(<Toast message="test" variant="success" />)
    expect(document.querySelector('.lucide-check-circle')).toBeInTheDocument()

    rerender(<Toast message="test" variant="error" />)
    expect(document.querySelector('.lucide-alert-circle')).toBeInTheDocument()

    rerender(<Toast message="test" variant="warning" />)
    expect(document.querySelector('.lucide-alert-triangle')).toBeInTheDocument()

    rerender(<Toast message="test" variant="info" />)
    expect(document.querySelector('.lucide-info')).toBeInTheDocument()
  })

  it('hides variant icon when showIcon is false', () => {
    render(<Toast message="test" showIcon={false} closable={false} />)
    expect(document.querySelector('.lucide-info')).not.toBeInTheDocument()
    expect(document.querySelector('.lucide-check-circle')).not.toBeInTheDocument()
    expect(document.querySelector('.lucide-alert-circle')).not.toBeInTheDocument()
    expect(document.querySelector('.lucide-alert-triangle')).not.toBeInTheDocument()
  })

  it('renders close button when closable is true', () => {
    render(<Toast message="test" closable />)
    const closeButton = screen.getByRole('button', { name: /close toast/i })
    expect(closeButton).toBeInTheDocument()
  })

  it('calls onClose when close button is clicked', () => {
    const onClose = vi.fn()
    render(<Toast message="test" closable onClose={onClose} duration={0} />)
    
    const closeButton = screen.getByRole('button', { name: /close toast/i })
    
    act(() => {
      fireEvent.click(closeButton)
    })
    
    // Wait for the exit animation
    act(() => {
      vi.advanceTimersByTime(200)
    })
    
    expect(onClose).toHaveBeenCalledTimes(1)
  })

  it('does not render close button when closable is false', () => {
    render(<Toast message="test" closable={false} />)
    expect(screen.queryByRole('button')).not.toBeInTheDocument()
  })

  it('auto-closes after duration', async () => {
    const onClose = vi.fn()
    render(<Toast message="test" duration={3000} onClose={onClose} />)
    
    // Fast-forward time
    act(() => {
      vi.advanceTimersByTime(3000)
    })
    
    // Wait for the exit animation
    act(() => {
      vi.advanceTimersByTime(200)
    })
    
    expect(onClose).toHaveBeenCalledTimes(1)
  })

  it('does not auto-close when duration is 0', () => {
    const onClose = vi.fn()
    render(<Toast message="test" duration={0} onClose={onClose} />)
    
    // Fast-forward time significantly
    vi.advanceTimersByTime(10000)
    
    expect(onClose).not.toHaveBeenCalled()
    expect(screen.getByRole('alert')).toBeInTheDocument()
  })

  it('applies custom className', () => {
    render(<Toast message="test" className="custom-class" />)
    expect(screen.getByRole('alert')).toHaveClass('custom-class')
  })

  it('forwards ref correctly', () => {
    const ref = React.createRef<HTMLDivElement>()
    render(<Toast message="test" ref={ref} />)
    expect(ref.current).toBeInstanceOf(HTMLDivElement)
  })

  it('applies text variant classes for title and message', () => {
    const { rerender } = render(<Toast title="Title" message="Message" variant="success" />)
    expect(screen.getByText('Title')).toHaveClass('text-green-800')
    expect(screen.getByText('Message')).toHaveClass('text-green-800')

    rerender(<Toast title="Title" message="Message" variant="error" />)
    expect(screen.getByText('Title')).toHaveClass('text-red-800')
    expect(screen.getByText('Message')).toHaveClass('text-red-800')
  })

  it('has correct accessibility attributes', () => {
    render(<Toast message="test" />)
    const toast = screen.getByRole('alert')
    expect(toast).toHaveAttribute('aria-live', 'polite')
  })

  it('shows exit animation when closing', () => {
    const onClose = vi.fn()
    render(<Toast message="test" closable onClose={onClose} duration={0} />)
    
    const closeButton = screen.getByRole('button', { name: /close toast/i })
    fireEvent.click(closeButton)
    
    const toast = screen.getByRole('alert')
    expect(toast).toHaveClass('opacity-0', 'scale-95')
  })

  it('passes through additional props', () => {
    render(<Toast message="test" data-testid="custom-toast" />)
    expect(screen.getByTestId('custom-toast')).toBeInTheDocument()
  })

  it('renders with only message when no title provided', () => {
    render(<Toast message="Only message" />)
    expect(screen.getByText('Only message')).toBeInTheDocument()
    expect(screen.queryByRole('heading')).not.toBeInTheDocument()
  })
})