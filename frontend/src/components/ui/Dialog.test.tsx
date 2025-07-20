import React from 'react'
import { render, screen, fireEvent } from '@testing-library/react'
import { vi } from 'vitest'
import Dialog from './Dialog'

// Mock createPortal
vi.mock('react-dom', async () => {
  const actual = await vi.importActual('react-dom')
  return {
    ...(actual as Record<string, unknown>),
    createPortal: (children: React.ReactNode) => children,
  }
})

describe('Dialog', () => {
  const defaultProps = {
    isOpen: true,
    onClose: vi.fn(),
    title: 'Test Dialog',
  }

  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders with title', () => {
    render(<Dialog {...defaultProps} />)
    expect(screen.getByText('Test Dialog')).toBeInTheDocument()
  })

  it('renders with description', () => {
    render(<Dialog {...defaultProps} description="This is a test dialog" />)
    expect(screen.getByText('This is a test dialog')).toBeInTheDocument()
  })

  it('renders confirm and cancel buttons with default text', () => {
    render(<Dialog {...defaultProps} />)
    expect(screen.getByRole('button', { name: 'Confirm' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Cancel' })).toBeInTheDocument()
  })

  it('renders custom button text', () => {
    render(
      <Dialog 
        {...defaultProps} 
        confirmText="Delete" 
        cancelText="Keep" 
      />
    )
    expect(screen.getByRole('button', { name: 'Delete' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Keep' })).toBeInTheDocument()
  })

  it('calls onConfirm when confirm button is clicked', () => {
    const onConfirm = vi.fn()
    render(<Dialog {...defaultProps} onConfirm={onConfirm} />)
    
    fireEvent.click(screen.getByRole('button', { name: 'Confirm' }))
    expect(onConfirm).toHaveBeenCalledTimes(1)
  })

  it('calls onCancel and onClose when cancel button is clicked', () => {
    const onCancel = vi.fn()
    const onClose = vi.fn()
    render(<Dialog {...defaultProps} onCancel={onCancel} onClose={onClose} />)
    
    fireEvent.click(screen.getByRole('button', { name: 'Cancel' }))
    expect(onCancel).toHaveBeenCalledTimes(1)
    expect(onClose).toHaveBeenCalledTimes(1)
  })

  it('shows loading state on confirm button', () => {
    render(<Dialog {...defaultProps} loading />)
    
    const confirmButton = screen.getByRole('button', { name: 'Confirm' })
    const cancelButton = screen.getByRole('button', { name: 'Cancel' })
    
    expect(confirmButton).toBeDisabled()
    expect(cancelButton).toBeDisabled()
  })

  it('displays correct icon for each type', () => {
    const { rerender } = render(<Dialog {...defaultProps} type="confirm" />)
    expect(document.querySelector('.lucide-info')).toBeInTheDocument()

    rerender(<Dialog {...defaultProps} type="success" />)
    expect(document.querySelector('.lucide-check-circle')).toBeInTheDocument()

    rerender(<Dialog {...defaultProps} type="danger" />)
    expect(document.querySelector('.lucide-alert-triangle')).toBeInTheDocument()

    rerender(<Dialog {...defaultProps} type="alert" />)
    expect(document.querySelector('.lucide-alert-triangle')).toBeInTheDocument()
  })

  it('applies correct button variant for each type', () => {
    const { rerender } = render(<Dialog {...defaultProps} type="danger" />)
    expect(screen.getByRole('button', { name: 'Confirm' })).toHaveClass('bg-red-600')

    rerender(<Dialog {...defaultProps} type="success" />)
    expect(screen.getByRole('button', { name: 'Confirm' })).toHaveClass('bg-blue-600')

    rerender(<Dialog {...defaultProps} type="confirm" />)
    expect(screen.getByRole('button', { name: 'Confirm' })).toHaveClass('bg-blue-600')
  })

  it('forwards ref correctly', () => {
    const ref = React.createRef<HTMLDivElement>()
    render(<Dialog {...defaultProps} ref={ref} />)
    expect(ref.current).toBeInstanceOf(HTMLDivElement)
  })

  it('passes props to underlying Modal', () => {
    const onClose = vi.fn()
    render(
      <Dialog 
        {...defaultProps} 
        onClose={onClose}
        closeOnOverlayClick={false}
        closeOnEscape={false}
      />
    )
    
    // Test that escape key doesn't close (closeOnEscape=false)
    fireEvent.keyDown(document, { key: 'Escape' })
    expect(onClose).not.toHaveBeenCalled()
    
    // Test that overlay click doesn't close (closeOnOverlayClick=false)
    const overlay = document.querySelector('.fixed.inset-0.bg-black\\/50')
    fireEvent.click(overlay!)
    expect(onClose).not.toHaveBeenCalled()
  })

  it('has correct icon colors for each type', () => {
    const { rerender } = render(<Dialog {...defaultProps} type="success" />)
    expect(document.querySelector('.text-green-600')).toBeInTheDocument()

    rerender(<Dialog {...defaultProps} type="danger" />)
    expect(document.querySelector('.text-red-600')).toBeInTheDocument()

    rerender(<Dialog {...defaultProps} type="alert" />)
    expect(document.querySelector('.text-yellow-600')).toBeInTheDocument()

    rerender(<Dialog {...defaultProps} type="confirm" />)
    expect(document.querySelector('.text-blue-600')).toBeInTheDocument()
  })

  it('does not render when isOpen is false', () => {
    render(<Dialog {...defaultProps} isOpen={false} />)
    expect(screen.queryByText('Test Dialog')).not.toBeInTheDocument()
  })

  it('handles missing onConfirm callback', () => {
    render(<Dialog {...defaultProps} />)
    
    // Should not throw error when clicking confirm without onConfirm
    expect(() => {
      fireEvent.click(screen.getByRole('button', { name: 'Confirm' }))
    }).not.toThrow()
  })

  it('handles missing onCancel callback', () => {
    const onClose = vi.fn()
    render(<Dialog {...defaultProps} onClose={onClose} />)
    
    // Should still call onClose even without onCancel
    fireEvent.click(screen.getByRole('button', { name: 'Cancel' }))
    expect(onClose).toHaveBeenCalledTimes(1)
  })
})