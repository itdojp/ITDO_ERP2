import React from 'react'
import { render, screen } from '@testing-library/react'
import Loading from './Loading'

describe('Loading', () => {
  it('renders with default props', () => {
    render(<Loading />)
    const loading = screen.getByRole('status')
    expect(loading).toBeInTheDocument()
    expect(loading).toHaveAttribute('aria-label', 'Loading')
  })

  it('renders with custom message', () => {
    render(<Loading message="Please wait..." />)
    expect(screen.getByText('Please wait...')).toBeInTheDocument()
    expect(screen.getByRole('status')).toHaveAttribute('aria-label', 'Please wait...')
  })

  it('applies size classes correctly', () => {
    const { rerender } = render(<Loading size="sm" />)
    expect(document.querySelector('.h-4.w-4')).toBeInTheDocument()

    rerender(<Loading size="lg" />)
    expect(document.querySelector('.h-8.w-8')).toBeInTheDocument()

    rerender(<Loading size="xl" />)
    expect(document.querySelector('.h-12.w-12')).toBeInTheDocument()
  })

  it('applies variant classes correctly', () => {
    const { rerender } = render(<Loading variant="primary" />)
    expect(document.querySelector('.border-blue-600')).toBeInTheDocument()

    rerender(<Loading variant="secondary" />)
    expect(document.querySelector('.border-gray-600')).toBeInTheDocument()

    rerender(<Loading variant="light" />)
    expect(document.querySelector('.border-white')).toBeInTheDocument()

    rerender(<Loading variant="dark" />)
    expect(document.querySelector('.border-gray-900')).toBeInTheDocument()
  })

  it('renders fullScreen loading correctly', () => {
    render(<Loading fullScreen />)
    const loading = screen.getByRole('status')
    expect(loading).toHaveClass('fixed', 'inset-0', 'z-50')
  })

  it('renders with overlay correctly', () => {
    render(<Loading overlay />)
    const loading = screen.getByRole('status')
    expect(loading).toHaveClass('bg-black/20')
  })

  it('combines fullScreen and overlay correctly', () => {
    render(<Loading fullScreen overlay />)
    const loading = screen.getByRole('status')
    expect(loading).toHaveClass('fixed', 'inset-0', 'z-50')
    expect(loading).toHaveClass('bg-black/20')
  })

  it('applies custom className', () => {
    render(<Loading className="custom-class" />)
    const loading = screen.getByRole('status')
    expect(loading).toHaveClass('custom-class')
  })

  it('forwards ref correctly', () => {
    const ref = React.createRef<HTMLDivElement>()
    render(<Loading ref={ref} />)
    expect(ref.current).toBeInstanceOf(HTMLDivElement)
  })

  it('renders message with correct text size', () => {
    const { rerender } = render(<Loading size="sm" message="Small" />)
    expect(screen.getByText('Small')).toHaveClass('text-sm')

    rerender(<Loading size="lg" message="Large" />)
    expect(screen.getByText('Large')).toHaveClass('text-lg')
  })

  it('renders message with correct text variant', () => {
    const { rerender } = render(<Loading variant="primary" message="Primary" />)
    expect(screen.getByText('Primary')).toHaveClass('text-blue-600')

    rerender(<Loading variant="light" message="Light" />)
    expect(screen.getByText('Light')).toHaveClass('text-white')
  })

  it('has correct spinner animation classes', () => {
    render(<Loading />)
    expect(document.querySelector('.animate-spin')).toBeInTheDocument()
    expect(document.querySelector('.rounded-full')).toBeInTheDocument()
    expect(document.querySelector('.border-2')).toBeInTheDocument()
  })

  it('has accessible spinner with transparent border top', () => {
    render(<Loading variant="primary" />)
    expect(document.querySelector('.border-t-transparent')).toBeInTheDocument()
  })

  it('passes through additional props', () => {
    render(<Loading data-testid="custom-loading" />)
    expect(screen.getByTestId('custom-loading')).toBeInTheDocument()
  })
})