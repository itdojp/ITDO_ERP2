import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import LoadingOverlay from './LoadingOverlay'

describe('LoadingOverlay', () => {
  it('renders with default props', () => {
    render(<LoadingOverlay />)
    
    const overlays = screen.getAllByRole('status')
    const overlay = overlays[0] // Main overlay
    expect(overlay).toBeInTheDocument()
    expect(overlay).toHaveClass('flex', 'flex-col', 'items-center', 'justify-center')
    expect(overlay).toHaveClass('absolute', 'inset-0', 'z-50')
  })

  it('renders in fullscreen mode', () => {
    render(<LoadingOverlay mode="fullscreen" />)
    
    const overlays = screen.getAllByRole('status')
    const overlay = overlays[0]
    expect(overlay).toHaveClass('fixed')
  })

  it('renders in container mode (default)', () => {
    render(<LoadingOverlay mode="container" />)
    
    const overlays = screen.getAllByRole('status')
    const overlay = overlays[0]
    expect(overlay).toHaveClass('absolute')
    expect(overlay).not.toHaveClass('fixed')
  })

  it('renders with message', () => {
    render(<LoadingOverlay message="Loading data..." />)
    
    expect(screen.getByText('Loading data...')).toBeInTheDocument()
    const overlays = screen.getAllByRole('status')
    const overlay = overlays[0]
    expect(overlay).toHaveAttribute('aria-label', 'Loading data...')
  })

  it('renders without backdrop', () => {
    render(<LoadingOverlay backdrop={false} />)
    
    const overlays = screen.getAllByRole('status')
    const overlay = overlays[0]
    expect(overlay).not.toHaveClass('bg-black/50')
  })

  it('renders with backdrop (default)', () => {
    render(<LoadingOverlay backdrop={true} />)
    
    const overlays = screen.getAllByRole('status')
    const overlay = overlays[0]
    expect(overlay).toHaveClass('bg-black/50')
  })

  it('renders with blur effect (default)', () => {
    render(<LoadingOverlay blur={true} />)
    
    const overlays = screen.getAllByRole('status')
    const overlay = overlays[0]
    expect(overlay).toHaveClass('backdrop-blur-sm')
  })

  it('renders without blur effect', () => {
    render(<LoadingOverlay blur={false} />)
    
    const overlays = screen.getAllByRole('status')
    const overlay = overlays[0]
    expect(overlay).not.toHaveClass('backdrop-blur-sm')
  })

  it('passes size prop to LoadingSpinner', () => {
    render(<LoadingOverlay size="large" />)
    
    const overlays = screen.getAllByRole('status')
    const spinner = overlays[1] // LoadingSpinner is the second status element
    expect(spinner).toHaveClass('h-8', 'w-8')
  })

  it('passes color prop to LoadingSpinner', () => {
    render(<LoadingOverlay color="white" />)
    
    const overlays = screen.getAllByRole('status')
    const spinner = overlays[1] // LoadingSpinner is the second status element
    expect(spinner).toHaveClass('border-white', 'border-t-transparent')
  })

  it('renders with white text color when color is white', () => {
    render(<LoadingOverlay message="Processing..." color="white" />)
    
    const message = screen.getByText('Processing...')
    expect(message).toHaveClass('text-white')
  })

  it('renders with gray text color for non-white colors', () => {
    render(<LoadingOverlay message="Processing..." color="primary" />)
    
    const message = screen.getByText('Processing...')
    expect(message).toHaveClass('text-gray-900')
  })

  it('applies custom className', () => {
    render(<LoadingOverlay className="custom-overlay" />)
    
    const overlays = screen.getAllByRole('status')
    const overlay = overlays[0]
    expect(overlay).toHaveClass('custom-overlay')
  })

  it('forwards ref correctly', () => {
    const ref = { current: null }
    render(<LoadingOverlay ref={ref} />)
    
    expect(ref.current).toBeInstanceOf(HTMLDivElement)
  })

  it('renders children content', () => {
    render(
      <LoadingOverlay>
        <div>Custom content</div>
      </LoadingOverlay>
    )
    
    expect(screen.getByText('Custom content')).toBeInTheDocument()
  })

  it('has proper accessibility attributes', () => {
    render(<LoadingOverlay message="Processing..." />)
    
    const overlays = screen.getAllByRole('status')
    const overlay = overlays[0]
    expect(overlay).toHaveAttribute('role', 'status')
    expect(overlay).toHaveAttribute('aria-label', 'Processing...')
  })

  it('uses default aria-label when no message provided', () => {
    render(<LoadingOverlay />)
    
    const overlays = screen.getAllByRole('status')
    const overlay = overlays[0]
    expect(overlay).toHaveAttribute('aria-label', 'Loading')
  })
})