import React from 'react'
import { render, screen, fireEvent } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import ErrorDisplay, { 
  NetworkErrorDisplay,
  ValidationErrorDisplay,
  AuthErrorDisplay,
  ServerErrorDisplay,
  ErrorList
} from './ErrorDisplay'
import { ErrorDetails } from '../../../hooks/useErrorHandler'

describe('ErrorDisplay', () => {
  const mockError = new Error('Test error message')
  const mockErrorDetails: ErrorDetails = {
    id: 'test-error-id',
    type: 'network',
    message: 'Network error occurred',
    status: 500,
    code: 'NETWORK_ERROR',
    timestamp: new Date('2023-01-01T00:00:00Z'),
    context: 'Test context',
  }

  it('renders basic error display', () => {
    render(<ErrorDisplay error={mockError} />)
    
    expect(screen.getByRole('alert')).toBeInTheDocument()
    expect(screen.getByText('Test error message')).toBeInTheDocument()
  })

  it('renders with custom title and description', () => {
    render(
      <ErrorDisplay
        title="Custom Title"
        description="Custom description"
      />
    )
    
    expect(screen.getByText('Custom Title')).toBeInTheDocument()
    expect(screen.getByText('Custom description')).toBeInTheDocument()
  })

  it('applies correct severity styles', () => {
    const { rerender } = render(
      <ErrorDisplay 
        error={mockError} 
        severity="critical"
      />
    )
    
    const alertElement = screen.getByRole('alert')
    expect(alertElement).toHaveClass('bg-red-50', 'border-red-200')
    
    rerender(
      <ErrorDisplay 
        error={mockError} 
        severity="low"
      />
    )
    
    expect(alertElement).toHaveClass('bg-blue-50', 'border-blue-200')
  })

  it('applies correct variant styles', () => {
    const { rerender } = render(
      <ErrorDisplay 
        error={mockError} 
        variant="banner"
      />
    )
    
    const alertElement = screen.getByRole('alert')
    expect(alertElement).toHaveClass('border-l-4')
    
    rerender(
      <ErrorDisplay 
        error={mockError} 
        variant="toast"
      />
    )
    
    expect(alertElement).toHaveClass('shadow-lg')
  })

  it('shows retry button when enabled', () => {
    const onRetry = vi.fn()
    
    render(
      <ErrorDisplay
        error={mockError}
        showRetry={true}
        onRetry={onRetry}
      />
    )
    
    const retryButton = screen.getByRole('button', { name: /retry/i })
    expect(retryButton).toBeInTheDocument()
    
    fireEvent.click(retryButton)
    expect(onRetry).toHaveBeenCalledTimes(1)
  })

  it('shows dismiss button when enabled', () => {
    const onDismiss = vi.fn()
    
    render(
      <ErrorDisplay
        error={mockError}
        showDismiss={true}
        onDismiss={onDismiss}
      />
    )
    
    const dismissButton = screen.getByRole('button', { name: /dismiss/i })
    expect(dismissButton).toBeInTheDocument()
    
    fireEvent.click(dismissButton)
    expect(onDismiss).toHaveBeenCalledTimes(1)
  })

  it('toggles error details when enabled', () => {
    render(
      <ErrorDisplay
        error={mockError}
        errorDetails={mockErrorDetails}
        showDetails={true}
      />
    )
    
    const detailsToggle = screen.getByRole('button', { name: /error details/i })
    expect(detailsToggle).toBeInTheDocument()
    
    // Details should be collapsed initially
    expect(screen.queryByText('test-error-id')).not.toBeInTheDocument()
    
    // Expand details
    fireEvent.click(detailsToggle)
    expect(screen.getByText('test-error-id')).toBeInTheDocument()
    expect(screen.getByText('network')).toBeInTheDocument()
    expect(screen.getByText('NETWORK_ERROR')).toBeInTheDocument()
  })

  it('displays stack trace when available', () => {
    const errorWithStack = new Error('Test error')
    errorWithStack.stack = 'Error: Test error\n  at test.js:1:1'
    
    render(
      <ErrorDisplay
        error={errorWithStack}
        errorDetails={mockErrorDetails}
        showDetails={true}
      />
    )
    
    const detailsToggle = screen.getByRole('button', { name: /error details/i })
    fireEvent.click(detailsToggle)
    
    expect(screen.getByText(/Error: Test error/)).toBeInTheDocument()
  })

  it('renders custom actions', () => {
    const customActions = (
      <button data-testid="custom-action">Custom Action</button>
    )
    
    render(
      <ErrorDisplay
        error={mockError}
        actions={customActions}
      />
    )
    
    expect(screen.getByTestId('custom-action')).toBeInTheDocument()
  })
})

describe('Specialized Error Components', () => {
  const mockError = new Error('Test error')

  it('renders NetworkErrorDisplay with correct props', () => {
    const onRetry = vi.fn()
    
    render(
      <NetworkErrorDisplay
        error={mockError}
        onRetry={onRetry}
      />
    )
    
    expect(screen.getByText('Connection Problem')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /retry/i })).toBeInTheDocument()
  })

  it('renders ValidationErrorDisplay with correct props', () => {
    render(<ValidationErrorDisplay error={mockError} />)
    
    expect(screen.getByText('Invalid Input')).toBeInTheDocument()
  })

  it('renders AuthErrorDisplay with login link', () => {
    render(<AuthErrorDisplay error={mockError} />)
    
    expect(screen.getByText('Authentication Required')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /login/i })).toHaveAttribute('href', '/login')
  })

  it('renders ServerErrorDisplay with details and retry', () => {
    const onRetry = vi.fn()
    
    render(<ServerErrorDisplay error={mockError} onRetry={onRetry} />)
    
    expect(screen.getByText('Server Error')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /retry/i })).toBeInTheDocument()
  })
})

describe('ErrorList', () => {
  const mockErrors: ErrorDetails[] = [
    {
      id: 'error-1',
      type: 'network',
      message: 'First error',
      timestamp: new Date('2023-01-01T00:00:00Z'),
    },
    {
      id: 'error-2',
      type: 'validation',
      message: 'Second error',
      timestamp: new Date('2023-01-01T01:00:00Z'),
    },
    {
      id: 'error-3',
      type: 'server',
      message: 'Third error',
      timestamp: new Date('2023-01-01T02:00:00Z'),
    },
  ]

  it('renders empty state when no errors', () => {
    const { container } = render(<ErrorList errors={[]} />)
    expect(container.firstChild).toBeNull()
  })

  it('renders error count and clear all button', () => {
    const onClearAll = vi.fn()
    
    render(
      <ErrorList
        errors={mockErrors}
        onClearAll={onClearAll}
      />
    )
    
    expect(screen.getByText('Recent Errors (3)')).toBeInTheDocument()
    
    const clearAllButton = screen.getByRole('button', { name: /clear all/i })
    fireEvent.click(clearAllButton)
    expect(onClearAll).toHaveBeenCalledTimes(1)
  })

  it('limits visible errors and shows expand button', () => {
    render(
      <ErrorList
        errors={mockErrors}
        maxVisible={2}
      />
    )
    
    // Should show first 2 errors
    expect(screen.getByText('First error')).toBeInTheDocument()
    expect(screen.getByText('Second error')).toBeInTheDocument()
    expect(screen.queryByText('Third error')).not.toBeInTheDocument()
    
    // Should show expand button
    const expandButton = screen.getByRole('button', { name: /show 1 more/i })
    expect(expandButton).toBeInTheDocument()
    
    // Expand to show all errors
    fireEvent.click(expandButton)
    expect(screen.getByText('Third error')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /show less/i })).toBeInTheDocument()
  })

  it('handles individual error clearing', () => {
    const onClearError = vi.fn()
    
    render(
      <ErrorList
        errors={mockErrors}
        onClearError={onClearError}
      />
    )
    
    // Each error should have a dismiss button
    const dismissButtons = screen.getAllByRole('button', { name: /dismiss/i })
    expect(dismissButtons).toHaveLength(3)
    
    // Click first dismiss button
    fireEvent.click(dismissButtons[0])
    expect(onClearError).toHaveBeenCalledWith('error-1')
  })

  it('does not show clear all button when only one error', () => {
    render(
      <ErrorList
        errors={[mockErrors[0]]}
        onClearAll={vi.fn()}
      />
    )
    
    expect(screen.queryByRole('button', { name: /clear all/i })).not.toBeInTheDocument()
  })
})