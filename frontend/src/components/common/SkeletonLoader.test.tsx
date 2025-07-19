import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import SkeletonLoader from './SkeletonLoader'

describe('SkeletonLoader', () => {
  it('renders with default props', () => {
    render(<SkeletonLoader />)
    
    const skeleton = screen.getByRole('status')
    expect(skeleton).toBeInTheDocument()
    expect(skeleton).toHaveClass('bg-gray-200', 'animate-pulse', 'h-4', 'rounded')
  })

  it('renders text variant with single line', () => {
    render(<SkeletonLoader variant="text" />)
    
    const skeleton = screen.getByRole('status')
    expect(skeleton).toHaveClass('h-4', 'rounded')
  })

  it('renders text variant with multiple lines', () => {
    render(<SkeletonLoader variant="text" lines={3} />)
    
    // Should render container with multiple skeleton lines
    const container = screen.getByTestId('skeleton-container')
    expect(container).toHaveClass('space-y-2')
    
    // Should have 3 skeleton elements
    const skeletons = container?.querySelectorAll('.bg-gray-200')
    expect(skeletons).toHaveLength(3)
  })

  it('renders card variant with image and text', () => {
    render(<SkeletonLoader variant="card" />)
    
    // Should render container with card structure
    const container = screen.getByTestId('skeleton-container')
    expect(container).toHaveClass('space-y-3')
    
    // Should have main skeleton with card height
    const mainSkeleton = container?.querySelector('.h-32')
    expect(mainSkeleton).toBeInTheDocument()
  })

  it('renders avatar variant', () => {
    render(<SkeletonLoader variant="avatar" />)
    
    const skeleton = screen.getByRole('status')
    expect(skeleton).toHaveClass('h-10', 'w-10', 'rounded-full')
  })

  it('renders table variant with multiple rows', () => {
    render(<SkeletonLoader variant="table" lines={2} />)
    
    // Should render container with table structure
    const container = screen.getByTestId('skeleton-container')
    expect(container).toHaveClass('space-y-2')
    
    // Should have rows with flex layout
    const rows = container?.querySelectorAll('.flex.space-x-4')
    expect(rows).toHaveLength(2)
  })

  it('disables animation when animate is false', () => {
    render(<SkeletonLoader animate={false} />)
    
    const skeleton = screen.getByRole('status')
    expect(skeleton).not.toHaveClass('animate-pulse')
  })

  it('applies rounded styling when rounded is true', () => {
    render(<SkeletonLoader rounded={true} />)
    
    const skeleton = screen.getByRole('status')
    expect(skeleton).toHaveClass('rounded-md')
  })

  it('applies custom width', () => {
    render(<SkeletonLoader width="200px" />)
    
    const skeleton = screen.getByRole('status')
    expect(skeleton).toHaveStyle({ width: '200px' })
  })

  it('applies custom height', () => {
    render(<SkeletonLoader height="100px" />)
    
    const skeleton = screen.getByRole('status')
    expect(skeleton).toHaveStyle({ height: '100px' })
  })

  it('applies custom className', () => {
    render(<SkeletonLoader className="custom-skeleton" />)
    
    const skeleton = screen.getByRole('status')
    expect(skeleton).toHaveClass('custom-skeleton')
  })

  it('forwards ref correctly', () => {
    const ref = { current: null }
    render(<SkeletonLoader ref={ref} />)
    
    expect(ref.current).toBeInstanceOf(HTMLDivElement)
  })

  it('has proper accessibility attributes', () => {
    render(<SkeletonLoader />)
    
    const skeleton = screen.getByRole('status')
    expect(skeleton).toHaveAttribute('role', 'status')
    expect(skeleton).toHaveAttribute('aria-label', 'Loading content...')
  })

  it('applies shimmer animation classes when animate is true', () => {
    render(<SkeletonLoader animate={true} />)
    
    const skeleton = screen.getByRole('status')
    expect(skeleton).toHaveClass('relative', 'overflow-hidden')
  })

  it('text variant last line is shorter', () => {
    render(<SkeletonLoader variant="text" lines={2} />)
    
    const container = screen.getByTestId('skeleton-container')
    const skeletons = container?.querySelectorAll('.bg-gray-200')
    
    // Last skeleton should have w-3/4 class
    expect(skeletons?.[1]).toHaveClass('w-3/4')
  })

  it('avatar variant has fixed dimensions', () => {
    render(<SkeletonLoader variant="avatar" width="custom" />)
    
    const skeleton = screen.getByRole('status')
    // Avatar should ignore custom width and use fixed dimensions
    expect(skeleton).toHaveClass('h-10', 'w-10')
  })
})