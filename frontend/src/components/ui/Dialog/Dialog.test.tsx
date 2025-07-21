import React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import userEvent from '@testing-library/user-event'

import Modal from './Modal'
import ConfirmDialog from './ConfirmDialog'

describe('Dialog Components', () => {
  describe('Modal', () => {
    it('renders when open', () => {
      render(
        <Modal isOpen={true} onClose={() => {}}>
          <div>Modal content</div>
        </Modal>
      )
      
      expect(screen.getByText('Modal content')).toBeInTheDocument()
      expect(screen.getByRole('dialog')).toBeInTheDocument()
    })

    it('does not render when closed', () => {
      render(
        <Modal isOpen={false} onClose={() => {}}>
          <div>Modal content</div>
        </Modal>
      )
      
      expect(screen.queryByText('Modal content')).not.toBeInTheDocument()
    })

    it('renders title and description', () => {
      render(
        <Modal 
          isOpen={true} 
          onClose={() => {}} 
          title="Test Modal"
          description="Test description"
        >
          <div>Content</div>
        </Modal>
      )
      
      expect(screen.getByText('Test Modal')).toBeInTheDocument()
      expect(screen.getByText('Test description')).toBeInTheDocument()
    })

    it('shows close button by default', () => {
      render(
        <Modal isOpen={true} onClose={() => {}}>
          <div>Content</div>
        </Modal>
      )
      
      expect(screen.getByLabelText('Close modal')).toBeInTheDocument()
    })

    it('hides close button when specified', () => {
      render(
        <Modal isOpen={true} onClose={() => {}} showCloseButton={false}>
          <div>Content</div>
        </Modal>
      )
      
      expect(screen.queryByLabelText('Close modal')).not.toBeInTheDocument()
    })

    it('calls onClose when close button is clicked', async () => {
      const user = userEvent.setup()
      const handleClose = vi.fn()
      
      render(
        <Modal isOpen={true} onClose={handleClose}>
          <div>Content</div>
        </Modal>
      )
      
      await user.click(screen.getByLabelText('Close modal'))
      expect(handleClose).toHaveBeenCalledTimes(1)
    })

    it('calls onClose when escape key is pressed', async () => {
      const user = userEvent.setup()
      const handleClose = vi.fn()
      
      render(
        <Modal isOpen={true} onClose={handleClose}>
          <div>Content</div>
        </Modal>
      )
      
      await user.keyboard('{Escape}')
      expect(handleClose).toHaveBeenCalledTimes(1)
    })

    it('does not close on escape when disabled', async () => {
      const user = userEvent.setup()
      const handleClose = vi.fn()
      
      render(
        <Modal isOpen={true} onClose={handleClose} closeOnEscape={false}>
          <div>Content</div>
        </Modal>
      )
      
      await user.keyboard('{Escape}')
      expect(handleClose).not.toHaveBeenCalled()
    })

    it('calls onClose when overlay is clicked', async () => {
      const user = userEvent.setup()
      const handleClose = vi.fn()
      
      render(
        <Modal isOpen={true} onClose={handleClose}>
          <div>Content</div>
        </Modal>
      )
      
      // Click on the overlay (backdrop)
      const dialog = screen.getByRole('dialog')
      const overlay = dialog.parentElement!
      await user.click(overlay)
      
      expect(handleClose).toHaveBeenCalledTimes(1)
    })

    it('does not close on overlay click when disabled', async () => {
      const user = userEvent.setup()
      const handleClose = vi.fn()
      
      render(
        <Modal isOpen={true} onClose={handleClose} closeOnOverlayClick={false}>
          <div>Content</div>
        </Modal>
      )
      
      // Click on the overlay (backdrop)
      const dialog = screen.getByRole('dialog')
      const overlay = dialog.parentElement!
      await user.click(overlay)
      
      expect(handleClose).not.toHaveBeenCalled()
    })

    it('applies correct size classes', () => {
      render(
        <Modal isOpen={true} onClose={() => {}} size="lg">
          <div>Content</div>
        </Modal>
      )
      
      const dialog = screen.getByRole('dialog')
      expect(dialog).toHaveClass('max-w-lg')
    })

    it('handles keyboard navigation correctly', async () => {
      const user = userEvent.setup()
      
      render(
        <Modal isOpen={true} onClose={() => {}}>
          <button>First Button</button>
          <button>Second Button</button>
        </Modal>
      )
      
      const firstButton = screen.getByText('First Button')
      const secondButton = screen.getByText('Second Button')
      
      // First focusable element should be focused initially
      await waitFor(() => {
        expect(firstButton).toHaveFocus()
      })
      
      // Tab should move to next element
      await user.tab()
      expect(secondButton).toHaveFocus()
      
      // Tab should move to close button
      await user.tab()
      expect(screen.getByLabelText('Close modal')).toHaveFocus()
    })
  })

  describe('ConfirmDialog', () => {
    it('renders when open', () => {
      render(
        <ConfirmDialog 
          isOpen={true} 
          onClose={() => {}} 
          onConfirm={() => {}}
        />
      )
      
      expect(screen.getByRole('dialog')).toBeInTheDocument()
      expect(screen.getByText('Confirm Action')).toBeInTheDocument()
      expect(screen.getByText('Are you sure you want to proceed?')).toBeInTheDocument()
    })

    it('renders custom title and description', () => {
      render(
        <ConfirmDialog 
          isOpen={true} 
          onClose={() => {}} 
          onConfirm={() => {}}
          title="Delete Item"
          description="This action cannot be undone."
        />
      )
      
      expect(screen.getByText('Delete Item')).toBeInTheDocument()
      expect(screen.getByText('This action cannot be undone.')).toBeInTheDocument()
    })

    it('renders custom button texts', () => {
      render(
        <ConfirmDialog 
          isOpen={true} 
          onClose={() => {}} 
          onConfirm={() => {}}
          confirmText="Delete"
          cancelText="Keep"
        />
      )
      
      expect(screen.getByText('Delete')).toBeInTheDocument()
      expect(screen.getByText('Keep')).toBeInTheDocument()
    })

    it('calls onConfirm when confirm button is clicked', async () => {
      const user = userEvent.setup()
      const handleConfirm = vi.fn()
      
      render(
        <ConfirmDialog 
          isOpen={true} 
          onClose={() => {}} 
          onConfirm={handleConfirm}
        />
      )
      
      await user.click(screen.getByText('Confirm'))
      expect(handleConfirm).toHaveBeenCalledTimes(1)
    })

    it('calls onClose when cancel button is clicked', async () => {
      const user = userEvent.setup()
      const handleClose = vi.fn()
      
      render(
        <ConfirmDialog 
          isOpen={true} 
          onClose={handleClose} 
          onConfirm={() => {}}
        />
      )
      
      await user.click(screen.getByText('Cancel'))
      expect(handleClose).toHaveBeenCalledTimes(1)
    })

    it('applies correct variant styling', () => {
      render(
        <ConfirmDialog 
          isOpen={true} 
          onClose={() => {}} 
          onConfirm={() => {}}
          variant="danger"
        />
      )
      
      // Should have danger icon and styling
      const confirmButton = screen.getByText('Confirm')
      expect(confirmButton).toHaveClass('bg-red-600')
    })

    it('shows loading state correctly', () => {
      render(
        <ConfirmDialog 
          isOpen={true} 
          onClose={() => {}} 
          onConfirm={() => {}}
          loading={true}
        />
      )
      
      const confirmButton = screen.getByText('Confirm')
      expect(confirmButton).toBeDisabled()
      
      const cancelButton = screen.getByText('Cancel')
      expect(cancelButton).toBeDisabled()
    })

    it('handles disabled state correctly', () => {
      render(
        <ConfirmDialog 
          isOpen={true} 
          onClose={() => {}} 
          onConfirm={() => {}}
          disabled={true}
        />
      )
      
      const confirmButton = screen.getByText('Confirm')
      expect(confirmButton).toBeDisabled()
    })

    it('focuses confirm button initially', async () => {
      render(
        <ConfirmDialog 
          isOpen={true} 
          onClose={() => {}} 
          onConfirm={() => {}}
        />
      )
      
      await waitFor(() => {
        expect(screen.getByText('Confirm')).toHaveFocus()
      })
    })

    it('renders correct icon for each variant', () => {
      const { rerender } = render(
        <ConfirmDialog 
          isOpen={true} 
          onClose={() => {}} 
          onConfirm={() => {}}
          variant="danger"
        />
      )
      
      // Check that an icon is rendered (we can't easily test specific icons without more setup)
      const dialog = screen.getByRole('dialog')
      expect(dialog.querySelector('svg')).toBeInTheDocument()
      
      rerender(
        <ConfirmDialog 
          isOpen={true} 
          onClose={() => {}} 
          onConfirm={() => {}}
          variant="success"
        />
      )
      
      expect(dialog.querySelector('svg')).toBeInTheDocument()
    })

    it('handles escape key correctly', async () => {
      const user = userEvent.setup()
      const handleClose = vi.fn()
      
      render(
        <ConfirmDialog 
          isOpen={true} 
          onClose={handleClose} 
          onConfirm={() => {}}
        />
      )
      
      await user.keyboard('{Escape}')
      expect(handleClose).toHaveBeenCalledTimes(1)
    })

    it('does not close on escape when disabled', async () => {
      const user = userEvent.setup()
      const handleClose = vi.fn()
      
      render(
        <ConfirmDialog 
          isOpen={true} 
          onClose={handleClose} 
          onConfirm={() => {}}
          closeOnEscape={false}
        />
      )
      
      await user.keyboard('{Escape}')
      expect(handleClose).not.toHaveBeenCalled()
    })
  })
})