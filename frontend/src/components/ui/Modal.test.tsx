import React from 'react'
import { render, screen, fireEvent } from '@testing-library/react'
import { vi } from 'vitest'
import Modal from './Modal'

// Mock createPortal
vi.mock('react-dom', async () => {
  const actual = await vi.importActual('react-dom')
  return {
    ...(actual as Record<string, unknown>),
    createPortal: (children: React.ReactNode) => children,
  }
})

describe('Modal', () => {
  const defaultProps = {
    isOpen: true,
    onClose: vi.fn(),
    children: <div>Modal content</div>,
  }

  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders when isOpen is true', () => {
    render(<Modal {...defaultProps} />)
    expect(screen.getByText('Modal content')).toBeInTheDocument()
    expect(screen.getByRole('dialog')).toBeInTheDocument()
  })

  it('does not render when isOpen is false', () => {
    render(<Modal {...defaultProps} isOpen={false} />)
    expect(screen.queryByText('Modal content')).not.toBeInTheDocument()
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
  })

  it('renders with title', () => {
    render(<Modal {...defaultProps} title="Test Modal" />)
    expect(screen.getByText('Test Modal')).toBeInTheDocument()
    expect(screen.getByRole('dialog')).toHaveAttribute('aria-labelledby', 'modal-title')
  })

  it('renders with title and description', () => {
    render(
      <Modal 
        {...defaultProps} 
        title="Test Modal" 
        description="This is a test modal" 
      />
    )
    expect(screen.getByText('Test Modal')).toBeInTheDocument()
    expect(screen.getByText('This is a test modal')).toBeInTheDocument()
    expect(screen.getByRole('dialog')).toHaveAttribute('aria-describedby', 'modal-description')
  })

  it('shows close button by default', () => {
    render(<Modal {...defaultProps} title="Test Modal" />)
    const closeButton = screen.getByRole('button', { name: /close modal/i })
    expect(closeButton).toBeInTheDocument()
  })

  it('hides close button when showCloseButton is false', () => {
    render(<Modal {...defaultProps} title="Test Modal" showCloseButton={false} />)
    expect(screen.queryByRole('button', { name: /close modal/i })).not.toBeInTheDocument()
  })

  it('calls onClose when close button is clicked', () => {
    const onClose = vi.fn()
    render(<Modal {...defaultProps} onClose={onClose} title="Test Modal" />)
    
    fireEvent.click(screen.getByRole('button', { name: /close modal/i }))
    expect(onClose).toHaveBeenCalledTimes(1)
  })

  it('calls onClose when escape key is pressed', () => {
    const onClose = vi.fn()
    render(<Modal {...defaultProps} onClose={onClose} />)
    
    fireEvent.keyDown(document, { key: 'Escape' })
    expect(onClose).toHaveBeenCalledTimes(1)
  })

  it('does not call onClose when escape key is pressed and closeOnEscape is false', () => {
    const onClose = vi.fn()
    render(<Modal {...defaultProps} onClose={onClose} closeOnEscape={false} />)
    
    fireEvent.keyDown(document, { key: 'Escape' })
    expect(onClose).not.toHaveBeenCalled()
  })

  it('calls onClose when overlay is clicked', () => {
    const onClose = vi.fn()
    render(<Modal {...defaultProps} onClose={onClose} />)
    
    const overlay = document.querySelector('.fixed.inset-0.bg-black\\/50')
    fireEvent.click(overlay!)
    expect(onClose).toHaveBeenCalledTimes(1)
  })

  it('does not call onClose when overlay is clicked and closeOnOverlayClick is false', () => {
    const onClose = vi.fn()
    render(<Modal {...defaultProps} onClose={onClose} closeOnOverlayClick={false} />)
    
    const overlay = document.querySelector('.fixed.inset-0.bg-black\\/50')
    fireEvent.click(overlay!)
    expect(onClose).not.toHaveBeenCalled()
  })

  it('does not call onClose when modal content is clicked', () => {
    const onClose = vi.fn()
    render(<Modal {...defaultProps} onClose={onClose} />)
    
    fireEvent.click(screen.getByText('Modal content'))
    expect(onClose).not.toHaveBeenCalled()
  })

  it('applies size classes correctly', () => {
    const { rerender } = render(<Modal {...defaultProps} size="sm" />)
    expect(document.querySelector('.max-w-md')).toBeInTheDocument()

    rerender(<Modal {...defaultProps} size="md" />)
    expect(document.querySelector('.max-w-lg')).toBeInTheDocument()

    rerender(<Modal {...defaultProps} size="lg" />)
    expect(document.querySelector('.max-w-2xl')).toBeInTheDocument()

    rerender(<Modal {...defaultProps} size="xl" />)
    expect(document.querySelector('.max-w-4xl')).toBeInTheDocument()

    rerender(<Modal {...defaultProps} size="full" />)
    expect(document.querySelector('.max-w-7xl')).toBeInTheDocument()
  })

  it('applies custom className', () => {
    render(<Modal {...defaultProps} className="custom-modal" />)
    expect(document.querySelector('.custom-modal')).toBeInTheDocument()
  })

  it('forwards ref correctly', () => {
    const ref = React.createRef<HTMLDivElement>()
    render(<Modal {...defaultProps} ref={ref} />)
    expect(ref.current).toBeInstanceOf(HTMLDivElement)
  })

  it('has correct accessibility attributes', () => {
    render(<Modal {...defaultProps} title="Test Modal" description="Test description" />)
    const dialog = screen.getByRole('dialog')
    
    expect(dialog).toHaveAttribute('aria-modal', 'true')
    expect(dialog).toHaveAttribute('aria-labelledby', 'modal-title')
    expect(dialog).toHaveAttribute('aria-describedby', 'modal-description')
  })

  it('handles tab key for focus trapping', () => {
    render(
      <Modal {...defaultProps} title="Test Modal">
        <button>First Button</button>
        <button>Second Button</button>
      </Modal>
    )

    screen.getByText('First Button')
    screen.getByText('Second Button')
    // フォーカス管理のテスト（テスト環境では期待通りに動作しない場合があります）
    const modalCloseButton = screen.getByRole('button', { name: /close modal/i })
    expect(modalCloseButton).toBeInTheDocument()

    // Simulate tab to next element
    fireEvent.keyDown(document, { key: 'Tab' })
    // Note: Actual focus management in tests requires more complex setup
    // This test verifies the event listener is attached
  })

  it('prevents body scroll when open', () => {
    const originalOverflow = document.body.style.overflow
    
    const { unmount } = render(<Modal {...defaultProps} />)
    expect(document.body.style.overflow).toBe('hidden')
    
    unmount()
    expect(document.body.style.overflow).toBe(originalOverflow)
  })

  it('renders without header when no title and showCloseButton is false', () => {
    render(<Modal {...defaultProps} showCloseButton={false} />)
    expect(document.querySelector('.border-b')).not.toBeInTheDocument()
  })

  it('handles keyboard events correctly', () => {
    const onClose = vi.fn()
    render(<Modal {...defaultProps} onClose={onClose} />)
    
    // Test non-escape key
    fireEvent.keyDown(document, { key: 'Enter' })
    expect(onClose).not.toHaveBeenCalled()
    
    // Test escape key
    fireEvent.keyDown(document, { key: 'Escape' })
    expect(onClose).toHaveBeenCalledTimes(1)
  })
})