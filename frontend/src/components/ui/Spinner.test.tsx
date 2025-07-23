import React from 'react';
import { render, screen } from '@testing-library/react';
import { Spinner } from './Spinner';

describe('Spinner', () => {
  it('renders default spinner', () => {
    render(<Spinner />);
    
    const spinner = screen.getByRole('img', { hidden: true });
    expect(spinner).toBeInTheDocument();
    expect(spinner).toHaveClass('animate-spin');
  });

  it('applies size classes correctly', () => {
    const { rerender } = render(<Spinner size="sm" />);
    let spinner = screen.getByRole('img', { hidden: true });
    expect(spinner).toHaveClass('w-4', 'h-4');
    
    rerender(<Spinner size="md" />);
    spinner = screen.getByRole('img', { hidden: true });
    expect(spinner).toHaveClass('w-6', 'h-6');
    
    rerender(<Spinner size="lg" />);
    spinner = screen.getByRole('img', { hidden: true });
    expect(spinner).toHaveClass('w-8', 'h-8');
    
    rerender(<Spinner size="xl" />);
    spinner = screen.getByRole('img', { hidden: true });
    expect(spinner).toHaveClass('w-12', 'h-12');
  });

  it('applies color variants correctly', () => {
    const { rerender } = render(<Spinner color="primary" />);
    let spinner = screen.getByRole('img', { hidden: true });
    expect(spinner).toHaveClass('text-blue-500');
    
    rerender(<Spinner color="success" />);
    spinner = screen.getByRole('img', { hidden: true });
    expect(spinner).toHaveClass('text-green-500');
    
    rerender(<Spinner color="warning" />);
    spinner = screen.getByRole('img', { hidden: true });
    expect(spinner).toHaveClass('text-yellow-500');
    
    rerender(<Spinner color="danger" />);
    spinner = screen.getByRole('img', { hidden: true });
    expect(spinner).toHaveClass('text-red-500');
  });

  it('displays loading text', () => {
    render(<Spinner text="Loading..." showText />);
    
    expect(screen.getByText('Loading...')).toBeInTheDocument();
  });

  it('hides text when showText is false', () => {
    render(<Spinner text="Loading..." showText={false} />);
    
    expect(screen.queryByText('Loading...')).not.toBeInTheDocument();
  });

  it('displays default loading text', () => {
    render(<Spinner showText />);
    
    expect(screen.getByText('Loading...')).toBeInTheDocument();
  });

  it('renders different spinner types', () => {
    const { rerender } = render(<Spinner type="spin" />);
    let spinner = screen.getByRole('img', { hidden: true });
    expect(spinner).toHaveClass('animate-spin');
    
    rerender(<Spinner type="pulse" />);
    spinner = screen.getByRole('img', { hidden: true });
    expect(spinner).toHaveClass('animate-pulse');
    
    rerender(<Spinner type="bounce" />);
    spinner = screen.getByRole('img', { hidden: true });
    expect(spinner).toHaveClass('animate-bounce');
    
    rerender(<Spinner type="dots" />);
    const dots = screen.getAllByTestId('spinner-dot');
    expect(dots).toHaveLength(3);
  });

  it('renders custom icon', () => {
    const CustomIcon = () => <span data-testid="custom-icon">⚡</span>;
    render(<Spinner icon={<CustomIcon />} />);
    
    expect(screen.getByTestId('custom-icon')).toBeInTheDocument();
  });

  it('applies custom className', () => {
    render(<Spinner className="custom-spinner" />);
    
    const container = screen.getByRole('img', { hidden: true }).closest('.custom-spinner');
    expect(container).toBeInTheDocument();
  });

  it('centers spinner when centered prop is true', () => {
    render(<Spinner centered />);
    
    const container = screen.getByRole('img', { hidden: true }).parentElement;
    expect(container).toHaveClass('flex', 'items-center', 'justify-center');
  });

  it('renders inline spinner', () => {
    render(<Spinner inline />);
    
    const container = screen.getByRole('img', { hidden: true }).parentElement;
    expect(container).toHaveClass('inline-flex');
  });

  it('displays with overlay', () => {
    render(<Spinner overlay />);
    
    const overlay = screen.getByTestId('spinner-overlay');
    expect(overlay).toHaveClass('fixed', 'inset-0', 'bg-black/50');
  });

  it('handles different speeds', () => {
    const { rerender } = render(<Spinner speed="slow" />);
    let spinner = screen.getByRole('img', { hidden: true });
    expect(spinner).toHaveClass('animate-slow-spin');
    
    rerender(<Spinner speed="normal" />);
    spinner = screen.getByRole('img', { hidden: true });
    expect(spinner).toHaveClass('animate-spin');
    
    rerender(<Spinner speed="fast" />);
    spinner = screen.getByRole('img', { hidden: true });
    expect(spinner).toHaveClass('animate-fast-spin');
  });

  it('renders bars spinner type', () => {
    render(<Spinner type="bars" />);
    
    const bars = screen.getAllByTestId('spinner-bar');
    expect(bars).toHaveLength(5);
    bars.forEach(bar => {
      expect(bar).toHaveClass('animate-pulse');
    });
  });

  it('renders ring spinner type', () => {
    render(<Spinner type="ring" strokeWidth={4} />);
    
    const ring = screen.getByRole('img', { hidden: true });
    expect(ring).toHaveClass('border-4', 'border-t-transparent', 'rounded-full');
  });

  it('renders grid spinner type', () => {
    render(<Spinner type="grid" />);
    
    const gridItems = screen.getAllByTestId('spinner-grid-item');
    expect(gridItems).toHaveLength(9);
  });

  it('displays description text', () => {
    render(<Spinner text="Loading..." description="Please wait while we process your request" showText />);
    
    expect(screen.getByText('Loading...')).toBeInTheDocument();
    expect(screen.getByText('Please wait while we process your request')).toBeInTheDocument();
  });

  it('handles accessibility attributes', () => {
    render(<Spinner 
      aria-label="Loading content" 
      aria-describedby="loading-description" 
    />);
    
    const spinner = screen.getByRole('img', { hidden: true });
    expect(spinner).toHaveAttribute('aria-label', 'Loading content');
    expect(spinner).toHaveAttribute('aria-describedby', 'loading-description');
  });

  it('renders with stroke width customization', () => {
    render(<Spinner type="ring" strokeWidth={3} />);
    
    const spinner = screen.getByRole('img', { hidden: true });
    expect(spinner).toHaveClass('border-3');
  });

  it('applies custom style', () => {
    render(<Spinner style={{ opacity: 0.5 }} />);
    
    const spinner = screen.getByRole('img', { hidden: true });
    expect(spinner).toHaveStyle({ opacity: '0.5' });
  });

  it('handles delay prop', () => {
    render(<Spinner delay={500} />);
    
    // With delay, the component should still render but with delayed visibility
    const spinner = screen.getByRole('img', { hidden: true });
    expect(spinner).toBeInTheDocument();
  });

  it('renders different dot patterns', () => {
    render(<Spinner type="dots" dotCount={5} />);
    
    const dots = screen.getAllByTestId('spinner-dot');
    expect(dots).toHaveLength(5);
  });

  it('handles minimum display time', () => {
    render(<Spinner minTime={1000} />);
    
    const spinner = screen.getByRole('img', { hidden: true });
    expect(spinner).toBeInTheDocument();
  });

  it('renders with custom border colors', () => {
    render(<Spinner 
      type="ring" 
      borderColor="border-purple-500" 
      borderTopColor="border-t-purple-200" 
    />);
    
    const spinner = screen.getByRole('img', { hidden: true });
    expect(spinner).toHaveClass('border-purple-500', 'border-t-purple-200');
  });

  it('displays progress indicator', () => {
    render(<Spinner progress={65} />);
    
    expect(screen.getByText('65%')).toBeInTheDocument();
  });

  it('renders with backdrop blur', () => {
    render(<Spinner overlay backdropBlur />);
    
    const overlay = screen.getByTestId('spinner-overlay');
    expect(overlay).toHaveClass('backdrop-blur-sm');
  });

  it('handles different positions', () => {
    const { rerender } = render(<Spinner position="top" overlay />);
    let overlay = screen.getByTestId('spinner-overlay');
    expect(overlay).toHaveClass('justify-start');
    
    rerender(<Spinner position="bottom" overlay />);
    overlay = screen.getByTestId('spinner-overlay');
    expect(overlay).toHaveClass('justify-end');
    
    rerender(<Spinner position="center" overlay />);
    overlay = screen.getByTestId('spinner-overlay');
    expect(overlay).toHaveClass('justify-center');
  });

  it('renders pulsing dots variant', () => {
    render(<Spinner type="pulsing-dots" />);
    
    const dots = screen.getAllByTestId('spinner-dot');
    expect(dots).toHaveLength(3);
    dots.forEach(dot => {
      expect(dot).toHaveClass('animate-pulse');
    });
  });

  it('applies theme variants', () => {
    const { rerender } = render(<Spinner theme="light" />);
    let spinner = screen.getByRole('img', { hidden: true });
    expect(spinner).toHaveClass('text-gray-600');
    
    rerender(<Spinner theme="dark" />);
    spinner = screen.getByRole('img', { hidden: true });
    expect(spinner).toHaveClass('text-white');
  });

  it('renders with title attribute for tooltip', () => {
    render(<Spinner title="Loading data..." />);
    
    const spinner = screen.getByRole('img', { hidden: true });
    expect(spinner).toHaveAttribute('title', 'Loading data...');
  });

  it('handles conditional rendering', () => {
    const { rerender } = render(<Spinner show={false} />);
    
    expect(screen.queryByRole('img', { hidden: true })).not.toBeInTheDocument();
    
    rerender(<Spinner show={true} />);
    expect(screen.getByRole('img', { hidden: true })).toBeInTheDocument();
  });

  it('renders with custom animation duration', () => {
    render(<Spinner animationDuration="2s" />);
    
    const spinner = screen.getByRole('img', { hidden: true });
    expect(spinner.style.animationDuration).toBe('2s');
  });

  it('displays indeterminate progress', () => {
    render(<Spinner indeterminate />);
    
    const spinner = screen.getByRole('img', { hidden: true });
    expect(spinner).toHaveClass('animate-spin');
  });
});