import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import Card from './Card'

describe('Card', () => {
  it('renders with default props', () => {
    render(<Card>Default Content</Card>)
    
    const card = screen.getByText('Default Content')
    expect(card.parentElement).toBeInTheDocument()
    expect(card.parentElement).toHaveClass('bg-white', 'border', 'rounded-lg', 'shadow-sm')
  })

  it('renders with title prop', () => {
    render(<Card title="Test Title">Content</Card>)
    
    expect(screen.getByText('Test Title')).toBeInTheDocument()
    expect(screen.getByText('Content')).toBeInTheDocument()
  })

  it('renders with primary variant', () => {
    render(<Card variant="primary">Primary Content</Card>)
    
    const card = screen.getByText('Primary Content').parentElement
    expect(card).toHaveClass('border-blue-200', 'bg-blue-50')
  })

  it('renders with secondary variant', () => {
    render(<Card variant="secondary">Secondary Content</Card>)
    
    const card = screen.getByText('Secondary Content').parentElement
    expect(card).toHaveClass('border-gray-200', 'bg-gray-50')
  })

  it('renders with success variant', () => {
    render(<Card variant="success">Success Content</Card>)
    
    const card = screen.getByText('Success Content').parentElement
    expect(card).toHaveClass('border-green-200', 'bg-green-50')
  })

  it('renders with warning variant', () => {
    render(<Card variant="warning">Warning Content</Card>)
    
    const card = screen.getByText('Warning Content').parentElement
    expect(card).toHaveClass('border-yellow-200', 'bg-yellow-50')
  })

  it('renders with error variant', () => {
    render(<Card variant="error">Error Content</Card>)
    
    const card = screen.getByText('Error Content').parentElement
    expect(card).toHaveClass('border-red-200', 'bg-red-50')
  })

  it('renders with small size', () => {
    render(<Card size="sm">Small Card</Card>)
    
    const card = screen.getByText('Small Card').parentElement
    expect(card).toHaveClass('p-3')
  })

  it('renders with medium size (default)', () => {
    render(<Card size="md">Medium Card</Card>)
    
    const card = screen.getByText('Medium Card').parentElement
    expect(card).toHaveClass('p-4')
  })

  it('renders with large size', () => {
    render(<Card size="lg">Large Card</Card>)
    
    const card = screen.getByText('Large Card').parentElement
    expect(card).toHaveClass('p-6')
  })

  it('applies custom className', () => {
    render(<Card className="custom-card">Custom</Card>)
    
    const card = screen.getByText('Custom').parentElement
    expect(card).toHaveClass('custom-card')
  })

  it('forwards ref correctly', () => {
    const ref = { current: null }
    render(<Card ref={ref}>Ref Test</Card>)
    
    expect(ref.current).toBeInstanceOf(HTMLDivElement)
  })

  it('passes through additional props', () => {
    render(<Card data-testid="card" role="region">Props Test</Card>)
    
    const card = screen.getByTestId('card')
    expect(card).toHaveAttribute('role', 'region')
  })

  it('renders title and children with proper structure', () => {
    render(
      <Card title="Card Title">
        <p>Card content goes here</p>
      </Card>
    )
    
    const title = screen.getByText('Card Title')
    const content = screen.getByText('Card content goes here')
    
    expect(title).toBeInTheDocument()
    expect(content).toBeInTheDocument()
    expect(title.tagName).toBe('H3')
  })

  it('renders without title when not provided', () => {
    render(<Card>Only content</Card>)
    
    const card = screen.getByText('Only content').parentElement
    const titleElement = card?.querySelector('h3')
    expect(titleElement).toBeNull()
  })

  it('handles complex children content', () => {
    render(
      <Card title="Complex Card">
        <div>
          <span>Complex</span>
          <button>Action</button>
        </div>
      </Card>
    )
    
    expect(screen.getByText('Complex Card')).toBeInTheDocument()
    expect(screen.getByText('Complex')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Action' })).toBeInTheDocument()
  })

  it('combines variant and size classes correctly', () => {
    render(<Card variant="primary" size="lg">Large Primary</Card>)
    
    const card = screen.getByText('Large Primary').parentElement
    expect(card).toHaveClass('border-blue-200', 'bg-blue-50') // variant
    expect(card).toHaveClass('p-6') // size
  })
})