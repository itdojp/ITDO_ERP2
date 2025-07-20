import React from 'react'
import { render, screen, waitFor } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import { act } from 'react'
import userEvent from '@testing-library/user-event'
import Modal from '../../components/ui/Modal'
import LoadingSpinner from '../../components/common/LoadingSpinner'
import Button from '../../components/ui/Button'

describe('Modal + LoadingSpinner Integration Tests', () => {
  it('displays loading spinner inside modal during async operations', async () => {
    const user = userEvent.setup()
    let isLoading = false
    
    const TestComponent = () => {
      const [loading, setLoading] = React.useState(false)
      const [modalOpen, setModalOpen] = React.useState(false)
      
      const handleAsyncAction = async () => {
        setLoading(true)
        // Simulate async operation
        await new Promise(resolve => setTimeout(resolve, 100))
        setLoading(false)
      }
      
      return (
        <div>
          <Button onClick={() => setModalOpen(true)}>Open Modal</Button>
          <Modal
            isOpen={modalOpen}
            onClose={() => setModalOpen(false)}
            title="Async Operation"
          >
            {loading ? (
              <LoadingSpinner />
            ) : (
              <Button onClick={handleAsyncAction}>Start Operation</Button>
            )}
          </Modal>
        </div>
      )
    }
    
    act(() => {
      render(<TestComponent />)
    })
    
    // Open modal
    const openButton = screen.getByText('Open Modal')
    await user.click(openButton)
    
    // Verify modal is open
    expect(screen.getByText('Async Operation')).toBeInTheDocument()
    
    // Start async operation
    const actionButton = screen.getByText('Start Operation')
    await user.click(actionButton)
    
    // Verify loading spinner appears
    expect(screen.getByRole('status')).toBeInTheDocument()
    expect(screen.getByText('Loading...')).toBeInTheDocument()
    
    // Wait for operation to complete
    await waitFor(() => {
      expect(screen.queryByRole('status')).not.toBeInTheDocument()
    }, { timeout: 200 })
    
    // Verify action button reappears
    expect(screen.getByText('Start Operation')).toBeInTheDocument()
  })
  
  it('handles modal closing during loading state', async () => {
    const user = userEvent.setup()
    
    const TestComponent = () => {
      const [loading, setLoading] = React.useState(false)
      const [modalOpen, setModalOpen] = React.useState(true)
      
      const handleClose = () => {
        // Should be able to close even during loading
        setModalOpen(false)
        setLoading(false) // Reset loading state on close
      }
      
      return (
        <Modal
          isOpen={modalOpen}
          onClose={handleClose}
          title="Loading Test"
        >
          {loading ? (
            <LoadingSpinner />
          ) : (
            <Button onClick={() => setLoading(true)}>Start Loading</Button>
          )}
        </Modal>
      )
    }
    
    act(() => {
      render(<TestComponent />)
    })
    
    // Start loading
    const startButton = screen.getByText('Start Loading')
    await user.click(startButton)
    
    // Verify loading state
    expect(screen.getByRole('status')).toBeInTheDocument()
    
    // Close modal during loading
    const closeButton = screen.getByLabelText('Close modal')
    await user.click(closeButton)
    
    // Verify modal is closed and loading is reset
    expect(screen.queryByText('Loading Test')).not.toBeInTheDocument()
    expect(screen.queryByRole('status')).not.toBeInTheDocument()
  })
  
  it('maintains loading state across modal re-opens', async () => {
    const user = userEvent.setup()
    let persistentLoading = false
    
    const TestComponent = () => {
      const [modalOpen, setModalOpen] = React.useState(false)
      
      return (
        <div>
          <Button onClick={() => setModalOpen(true)}>Open Modal</Button>
          <Modal
            isOpen={modalOpen}
            onClose={() => setModalOpen(false)}
            title="Persistent Loading"
          >
            {persistentLoading ? (
              <LoadingSpinner />
            ) : (
              <Button 
                onClick={() => { persistentLoading = true }}
                data-testid="enable-loading"
              >
                Enable Loading
              </Button>
            )}
          </Modal>
        </div>
      )
    }
    
    act(() => {
      render(<TestComponent />)
    })
    
    // Open modal and enable loading
    await user.click(screen.getByText('Open Modal'))
    await user.click(screen.getByTestId('enable-loading'))
    
    // Close modal
    await user.click(screen.getByLabelText('Close modal'))
    
    // Re-open modal
    await user.click(screen.getByText('Open Modal'))
    
    // Verify loading state is maintained
    expect(screen.getByRole('status')).toBeInTheDocument()
  })
})