import { render, screen, waitFor } from '@testing-library/react';
import { vi } from 'vitest';
import { Loading } from './Loading';

describe('Loading', () => {
  it('renders loading spinner by default', () => {
    render(<Loading />);
    const spinner = screen.getByRole('img', { hidden: true });
    expect(spinner).toBeInTheDocument();
    expect(spinner).toHaveClass('animate-spin');
  });

  it('renders with loading text', () => {
    render(<Loading>Loading data...</Loading>);
    expect(screen.getByText('Loading data...')).toBeInTheDocument();
  });

  it('supports different sizes', () => {
    const sizes = ['small', 'medium', 'large'] as const;
    
    sizes.forEach(size => {
      const { unmount } = render(<Loading size={size} />);
      const spinner = screen.getByRole('img', { hidden: true });
      expect(spinner).toBeInTheDocument();
      unmount();
    });
  });

  it('renders different spinner types', () => {
    const types = ['spinner', 'dots', 'bars', 'pulse', 'ring', 'wave'] as const;
    
    types.forEach(type => {
      const { unmount } = render(<Loading type={type} />);
      expect(document.querySelector('.loading-component')).toBeInTheDocument();
      unmount();
    });
  });

  it('supports different colors', () => {
    const colors = ['blue', 'green', 'red', 'yellow', 'purple', 'gray'] as const;
    
    colors.forEach(color => {
      const { unmount } = render(<Loading color={color} />);
      const spinner = screen.getByRole('img', { hidden: true });
      expect(spinner).toBeInTheDocument();
      unmount();
    });
  });

  it('renders overlay loading', () => {
    render(<Loading overlay />);
    const overlay = screen.getByTestId('loading-overlay');
    expect(overlay).toBeInTheDocument();
  });

  it('shows loading indicator when active', () => {
    const { rerender } = render(<Loading loading={false} />);
    expect(screen.queryByRole('img', { hidden: true })).not.toBeInTheDocument();
    
    rerender(<Loading loading={true} />);
    expect(screen.getByRole('img', { hidden: true })).toBeInTheDocument();
  });

  it('supports custom delay', async () => {
    const { rerender } = render(<Loading loading={false} delay={100} />);
    expect(screen.queryByRole('img', { hidden: true })).not.toBeInTheDocument();
    
    rerender(<Loading loading={true} delay={100} />);
    expect(screen.queryByRole('img', { hidden: true })).not.toBeInTheDocument();
    
    await waitFor(() => {
      expect(screen.getByRole('img', { hidden: true })).toBeInTheDocument();
    }, { timeout: 200 });
  });

  it('renders with custom icon', () => {
    const customIcon = <span data-testid="custom-spinner">⏳</span>;
    render(<Loading icon={customIcon} />);
    expect(screen.getByTestId('custom-spinner')).toBeInTheDocument();
  });

  it('supports tip text', () => {
    render(<Loading tip="Please wait..." />);
    expect(screen.getByText('Please wait...')).toBeInTheDocument();
  });

  it('renders full page loading', () => {
    render(<Loading fullPage />);
    const container = screen.getByTestId('loading-container');
    expect(container).toHaveClass('fixed', 'inset-0');
  });

  it('supports custom className', () => {
    render(<Loading className="custom-loading" />);
    const container = screen.getByTestId('loading-container');
    expect(container).toHaveClass('custom-loading');
  });

  it('renders with progress indicator', () => {
    render(<Loading progress={50} />);
    expect(screen.getByText('50%')).toBeInTheDocument();
    
    const progressBar = screen.getByRole('progressbar');
    expect(progressBar).toBeInTheDocument();
    expect(progressBar).toHaveAttribute('aria-valuenow', '50');
  });

  it('handles indeterminate progress', () => {
    render(<Loading progress />);
    const progressBar = screen.getByRole('progressbar');
    expect(progressBar).toBeInTheDocument();
  });

  it('supports custom wrapper', () => {
    render(
      <Loading wrapper={<div data-testid="custom-wrapper" />}>
        Content
      </Loading>
    );
    expect(screen.getByText('Content')).toBeInTheDocument();
  });

  it('renders skeletal loading', () => {
    render(<Loading type="skeleton" />);
    const skeleton = screen.getByTestId('skeleton-loader');
    expect(skeleton).toBeInTheDocument();
  });

  it('supports spinning content', () => {
    render(
      <Loading spinning>
        <div>Content to wrap</div>
      </Loading>
    );
    expect(screen.getByText('Content to wrap')).toBeInTheDocument();
  });

  it('controls spinning state', () => {
    const { rerender } = render(
      <Loading spinning={false}>
        <div>Content</div>
      </Loading>
    );
    expect(screen.getByText('Content')).toBeInTheDocument();
    
    rerender(
      <Loading spinning={true}>
        <div>Content</div>
      </Loading>
    );
    expect(screen.getByRole('img', { hidden: true })).toBeInTheDocument();
  });

  it('renders with custom animation duration', () => {
    render(<Loading duration={1000} />);
    const spinner = screen.getByRole('img', { hidden: true });
    expect(spinner).toBeInTheDocument();
  });

  it('supports minimum display time', async () => {
    const onFinish = vi.fn();
    const { rerender } = render(
      <Loading loading={true} minTime={100} onFinish={onFinish} />
    );
    
    rerender(<Loading loading={false} minTime={100} onFinish={onFinish} />);
    
    await waitFor(() => {
      expect(onFinish).toHaveBeenCalled();
    }, { timeout: 200 });
  });

  it('renders with backdrop', () => {
    render(<Loading backdrop />);
    const backdrop = screen.getByTestId('loading-backdrop');
    expect(backdrop).toBeInTheDocument();
  });

  it('supports custom loading states', () => {
    const states = ['loading', 'success', 'error'] as const;
    
    states.forEach(state => {
      const { unmount } = render(<Loading state={state} />);
      const container = screen.getByTestId('loading-container');
      expect(container).toBeInTheDocument();
      unmount();
    });
  });

  it('renders with percentage text format', () => {
    render(<Loading progress={75} format="Loading: {percent}%" />);
    expect(screen.getByText('Loading: 75%')).toBeInTheDocument();
  });

  it('supports centered layout', () => {
    render(<Loading centered />);
    const container = screen.getByTestId('loading-container');
    expect(container).toHaveClass('justify-center', 'items-center');
  });

  it('renders inline loading', () => {
    render(<Loading inline />);
    const container = screen.getByTestId('loading-container');
    expect(container).toHaveClass('inline-flex');
  });

  it('supports opacity control', () => {
    render(<Loading opacity={0.5} overlay />);
    const overlay = screen.getByTestId('loading-overlay');
    expect(overlay).toBeInTheDocument();
  });

  it('handles loading completion callback', async () => {
    const onComplete = vi.fn();
    const { rerender } = render(<Loading loading={true} onComplete={onComplete} />);
    
    rerender(<Loading loading={false} onComplete={onComplete} />);
    
    await waitFor(() => {
      expect(onComplete).toHaveBeenCalled();
    });
  });

  it('renders with custom content area', () => {
    render(
      <Loading>
        <Loading.Content>
          <div>Custom loading content</div>
        </Loading.Content>
      </Loading>
    );
    expect(screen.getByText('Custom loading content')).toBeInTheDocument();
  });

  it('supports auto-hide after timeout', async () => {
    const onTimeout = vi.fn();
    render(<Loading timeout={100} onTimeout={onTimeout} />);
    
    await waitFor(() => {
      expect(onTimeout).toHaveBeenCalled();
    }, { timeout: 200 });
  });

  it('renders with error state', () => {
    render(<Loading state="error" errorMessage="Failed to load" />);
    expect(screen.getByText('Failed to load')).toBeInTheDocument();
  });

  it('supports retry functionality', () => {
    const onRetry = vi.fn();
    render(<Loading state="error" onRetry={onRetry} />);
    
    const retryButton = screen.getByText('Retry');
    expect(retryButton).toBeInTheDocument();
  });

  it('renders success state with message', () => {
    render(<Loading state="success" successMessage="Loaded successfully!" />);
    expect(screen.getByText('Loaded successfully!')).toBeInTheDocument();
  });
});