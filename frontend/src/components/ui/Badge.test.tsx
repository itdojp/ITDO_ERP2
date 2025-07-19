import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import Badge from './Badge'

describe('Badge', () => {
  it('renders with default props', () => {
    render(<Badge>Default</Badge>)
    
    const badge = screen.getByText('Default')
    expect(badge).toBeInTheDocument()
    expect(badge).toHaveClass('inline-flex', 'items-center', 'font-medium', 'rounded-full')
  })

  it('renders with primary variant (default)', () => {
    render(<Badge variant="primary">Primary</Badge>)
    
    const badge = screen.getByText('Primary')
    expect(badge).toHaveClass('bg-blue-100', 'text-blue-800', 'border-blue-200')
  })

  it('renders with secondary variant', () => {
    render(<Badge variant="secondary">Secondary</Badge>)
    
    const badge = screen.getByText('Secondary')
    expect(badge).toHaveClass('bg-gray-100', 'text-gray-800', 'border-gray-200')
  })

  it('renders with success variant', () => {
    render(<Badge variant="success">Success</Badge>)
    
    const badge = screen.getByText('Success')
    expect(badge).toHaveClass('bg-green-100', 'text-green-800', 'border-green-200')
  })

  it('renders with warning variant', () => {
    render(<Badge variant="warning">Warning</Badge>)
    
    const badge = screen.getByText('Warning')
    expect(badge).toHaveClass('bg-yellow-100', 'text-yellow-800', 'border-yellow-200')
  })

  it('renders with error variant', () => {
    render(<Badge variant="error">Error</Badge>)
    
    const badge = screen.getByText('Error')
    expect(badge).toHaveClass('bg-red-100', 'text-red-800', 'border-red-200')
  })

  it('renders with info variant', () => {
    render(<Badge variant="info">Info</Badge>)
    
    const badge = screen.getByText('Info')
    expect(badge).toHaveClass('bg-cyan-100', 'text-cyan-800', 'border-cyan-200')
  })

  it('renders with small size', () => {
    render(<Badge size="sm">Small</Badge>)
    
    const badge = screen.getByText('Small')
    expect(badge).toHaveClass('text-xs', 'px-2', 'py-0.5')
  })

  it('renders with medium size (default)', () => {
    render(<Badge size="md">Medium</Badge>)
    
    const badge = screen.getByText('Medium')
    expect(badge).toHaveClass('text-sm', 'px-2.5', 'py-1')
  })

  it('renders with large size', () => {
    render(<Badge size="lg">Large</Badge>)
    
    const badge = screen.getByText('Large')
    expect(badge).toHaveClass('text-base', 'px-3', 'py-1.5')
  })

  it('applies custom className', () => {
    render(<Badge className="custom-badge">Custom</Badge>)
    
    const badge = screen.getByText('Custom')
    expect(badge).toHaveClass('custom-badge')
  })

  it('forwards ref correctly', () => {
    const ref = { current: null }
    render(<Badge ref={ref}>Ref Test</Badge>)
    
    expect(ref.current).toBeInstanceOf(HTMLSpanElement)
  })

  it('passes through additional props', () => {
    render(<Badge data-testid="badge" title="Badge tooltip">Props</Badge>)
    
    const badge = screen.getByTestId('badge')
    expect(badge).toHaveAttribute('title', 'Badge tooltip')
  })

  it('renders children content correctly', () => {
    render(
      <Badge>
        <span>Complex</span> Content
      </Badge>
    )
    
    expect(screen.getByText('Complex')).toBeInTheDocument()
    expect(screen.getByText('Content')).toBeInTheDocument()
  })

  it('combines variant and size classes correctly', () => {
    render(<Badge variant="success" size="lg">Large Success</Badge>)
    
    const badge = screen.getByText('Large Success')
    expect(badge).toHaveClass('bg-green-100', 'text-green-800') // variant
    expect(badge).toHaveClass('text-base', 'px-3', 'py-1.5') // size
  })

  it('has proper semantic structure', () => {
    render(<Badge>Semantic</Badge>)
    
    const badge = screen.getByText('Semantic')
    expect(badge.tagName).toBe('SPAN')
  })
})