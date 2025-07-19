import React from 'react'
import { render, screen, fireEvent } from '@testing-library/react'
import Alert from './Alert'

describe('Alert', () => {
  it('renders with message', () => {
    render(<Alert message="Test alert message" />)
    expect(screen.getByText('Test alert message')).toBeInTheDocument()
    expect(screen.getByRole('alert')).toBeInTheDocument()
  })

  it('renders with title and message', () => {
    render(<Alert title="Alert Title" message="Alert message" />)
    expect(screen.getByText('Alert Title')).toBeInTheDocument()
    expect(screen.getByText('Alert message')).toBeInTheDocument()
  })

  it('applies variant classes correctly', () => {
    const { rerender } = render(<Alert message="test" variant="success" />)
    expect(screen.getByRole('alert')).toHaveClass('bg-green-50', 'border-green-200')

    rerender(<Alert message="test" variant="error" />)
    expect(screen.getByRole('alert')).toHaveClass('bg-red-50', 'border-red-200')

    rerender(<Alert message="test" variant="warning" />)
    expect(screen.getByRole('alert')).toHaveClass('bg-yellow-50', 'border-yellow-200')

    rerender(<Alert message="test" variant="info" />)
    expect(screen.getByRole('alert')).toHaveClass('bg-blue-50', 'border-blue-200')
  })

  it('applies size classes correctly', () => {
    const { rerender } = render(<Alert message="test" size="sm" />)
    expect(screen.getByRole('alert')).toHaveClass('text-sm')

    rerender(<Alert message="test" size="md" />)
    expect(screen.getByRole('alert')).toHaveClass('text-base')

    rerender(<Alert message="test" size="lg" />)
    expect(screen.getByRole('alert')).toHaveClass('text-lg')
  })

  it('shows appropriate icon for each variant', () => {
    const { rerender } = render(<Alert message="test" variant="success" />)
    expect(document.querySelector('.lucide-check-circle')).toBeInTheDocument()

    rerender(<Alert message="test" variant="error" />)
    expect(document.querySelector('.lucide-alert-circle')).toBeInTheDocument()

    rerender(<Alert message="test" variant="warning" />)
    expect(document.querySelector('.lucide-alert-triangle')).toBeInTheDocument()

    rerender(<Alert message="test" variant="info" />)
    expect(document.querySelector('.lucide-info')).toBeInTheDocument()
  })

  it('hides icon when showIcon is false', () => {
    render(<Alert message="test" showIcon={false} />)
    expect(document.querySelector('svg')).not.toBeInTheDocument()
  })

  it('renders close button when closable is true', () => {
    const onClose = vi.fn()
    render(<Alert message="test" closable onClose={onClose} />)
    
    const closeButton = screen.getByRole('button', { name: /close alert/i })
    expect(closeButton).toBeInTheDocument()
  })

  it('calls onClose when close button is clicked', () => {
    const onClose = vi.fn()
    render(<Alert message="test" closable onClose={onClose} />)
    
    const closeButton = screen.getByRole('button', { name: /close alert/i })
    fireEvent.click(closeButton)
    
    expect(onClose).toHaveBeenCalledTimes(1)
  })

  it('does not render close button when closable is false', () => {
    render(<Alert message="test" closable={false} />)
    expect(screen.queryByRole('button')).not.toBeInTheDocument()
  })

  it('does not render close button when onClose is not provided', () => {
    render(<Alert message="test" closable />)
    expect(screen.queryByRole('button')).not.toBeInTheDocument()
  })

  it('applies custom className', () => {
    render(<Alert message="test" className="custom-class" />)
    expect(screen.getByRole('alert')).toHaveClass('custom-class')
  })

  it('forwards ref correctly', () => {
    const ref = React.createRef<HTMLDivElement>()
    render(<Alert message="test" ref={ref} />)
    expect(ref.current).toBeInstanceOf(HTMLDivElement)
  })

  it('applies focus ring classes for close button variants', () => {
    const { rerender } = render(<Alert message="test" variant="success" closable onClose={() => {}} />)
    let closeButton = screen.getByRole('button', { name: /close alert/i })
    expect(closeButton).toHaveClass('focus:ring-green-500')

    rerender(<Alert message="test" variant="error" closable onClose={() => {}} />)
    closeButton = screen.getByRole('button', { name: /close alert/i })
    expect(closeButton).toHaveClass('focus:ring-red-500')

    rerender(<Alert message="test" variant="warning" closable onClose={() => {}} />)
    closeButton = screen.getByRole('button', { name: /close alert/i })
    expect(closeButton).toHaveClass('focus:ring-yellow-500')

    rerender(<Alert message="test" variant="info" closable onClose={() => {}} />)
    closeButton = screen.getByRole('button', { name: /close alert/i })
    expect(closeButton).toHaveClass('focus:ring-blue-500')
  })

  it('applies correct icon sizes for different alert sizes', () => {
    const { rerender } = render(<Alert message="test" size="sm" />)
    expect(document.querySelector('svg')).toHaveClass('h-4', 'w-4')

    rerender(<Alert message="test" size="md" />)
    expect(document.querySelector('svg')).toHaveClass('h-5', 'w-5')

    rerender(<Alert message="test" size="lg" />)
    expect(document.querySelector('svg')).toHaveClass('h-6', 'w-6')
  })

  it('passes through additional props', () => {
    render(<Alert message="test" data-testid="custom-alert" />)
    expect(screen.getByTestId('custom-alert')).toBeInTheDocument()
  })

  it('renders with only message when no title provided', () => {
    render(<Alert message="Only message" />)
    expect(screen.getByText('Only message')).toBeInTheDocument()
    expect(screen.queryByRole('heading')).not.toBeInTheDocument()
  })
})