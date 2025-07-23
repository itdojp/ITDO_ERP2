import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { vi } from 'vitest';
import { Toast } from './Toast';

describe('Toast', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.runOnlyPendingTimers();
    vi.useRealTimers();
  });

  it('renders toast with message', () => {
    render(<Toast message="Test toast" />);
    
    expect(screen.getByTestId('toast-container')).toBeInTheDocument();
    expect(screen.getByText('Test toast')).toBeInTheDocument();
  });

  it('displays different toast types', () => {
    const types = ['success', 'error', 'warning', 'info'] as const;
    
    types.forEach(type => {
      const { unmount } = render(<Toast message="Test" type={type} />);
      const container = screen.getByTestId('toast-container');
      expect(container).toHaveClass(`type-${type}`);
      unmount();
    });
  });

  it('shows title when provided', () => {
    render(<Toast title="Important" message="Test toast" />);
    
    expect(screen.getByTestId('toast-title')).toBeInTheDocument();
    expect(screen.getByText('Important')).toBeInTheDocument();
  });

  it('displays close button when closable', () => {
    render(<Toast message="Test" closable />);
    
    expect(screen.getByTestId('toast-close')).toBeInTheDocument();
  });

  it('calls onClose when close button clicked', () => {
    const onClose = vi.fn();
    render(<Toast message="Test" closable onClose={onClose} />);
    
    const closeButton = screen.getByTestId('toast-close');
    fireEvent.click(closeButton);
    
    expect(onClose).toHaveBeenCalled();
  });

  it('auto closes after duration', async () => {
    const onClose = vi.fn();
    render(<Toast message="Test" duration={1000} onClose={onClose} />);
    
    vi.advanceTimersByTime(1000);
    
    await waitFor(() => {
      expect(onClose).toHaveBeenCalled();
    });
  });

  it('does not auto close when duration is 0', () => {
    const onClose = vi.fn();
    render(<Toast message="Test" duration={0} onClose={onClose} />);
    
    vi.advanceTimersByTime(5000);
    
    expect(onClose).not.toHaveBeenCalled();
  });

  it('supports different positions', () => {
    const positions = ['top-right', 'top-left', 'bottom-right', 'bottom-left', 'top-center', 'bottom-center'] as const;
    
    positions.forEach(position => {
      const { unmount } = render(<Toast message="Test" position={position} />);
      const container = screen.getByTestId('toast-container');
      expect(container).toHaveClass(`position-${position}`);
      unmount();
    });
  });

  it('supports different sizes', () => {
    const sizes = ['sm', 'md', 'lg'] as const;
    
    sizes.forEach(size => {
      const { unmount } = render(<Toast message="Test" size={size} />);
      const container = screen.getByTestId('toast-container');
      expect(container).toHaveClass(`size-${size}`);
      unmount();
    });
  });

  it('supports different themes', () => {
    const themes = ['light', 'dark'] as const;
    
    themes.forEach(theme => {
      const { unmount } = render(<Toast message="Test" theme={theme} />);
      const container = screen.getByTestId('toast-container');
      expect(container).toHaveClass(`theme-${theme}`);
      unmount();
    });
  });

  it('shows action button when provided', () => {
    const onAction = vi.fn();
    render(
      <Toast 
        message="Test" 
        action={{ label: 'Undo', onClick: onAction }}
      />
    );
    
    const actionButton = screen.getByTestId('toast-action');
    expect(actionButton).toBeInTheDocument();
    expect(screen.getByText('Undo')).toBeInTheDocument();
    
    fireEvent.click(actionButton);
    expect(onAction).toHaveBeenCalled();
  });

  it('displays icon when provided', () => {
    render(<Toast message="Test" icon="🔔" />);
    
    expect(screen.getByTestId('toast-icon')).toBeInTheDocument();
    expect(screen.getByText('🔔')).toBeInTheDocument();
  });

  it('shows default icons for different types', () => {
    const typeIcons = [
      { type: 'success', expectedClass: 'icon-success' },
      { type: 'error', expectedClass: 'icon-error' },
      { type: 'warning', expectedClass: 'icon-warning' },
      { type: 'info', expectedClass: 'icon-info' }
    ] as const;
    
    typeIcons.forEach(({ type, expectedClass }) => {
      const { unmount } = render(<Toast message="Test" type={type} showDefaultIcon />);
      const iconContainer = screen.getByTestId('toast-icon');
      const iconElement = iconContainer.querySelector('div');
      expect(iconElement).toHaveClass(expectedClass);
      unmount();
    });
  });

  it('shows progress bar when showProgress is true', () => {
    render(<Toast message="Test" duration={2000} showProgress />);
    
    expect(screen.getByTestId('toast-progress')).toBeInTheDocument();
  });

  it('updates progress bar over time', async () => {
    render(<Toast message="Test" duration={1000} showProgress />);
    
    const progressBar = screen.getByTestId('toast-progress');
    
    expect(progressBar).toHaveStyle({ width: '100%' });
    
    vi.advanceTimersByTime(500);
    await waitFor(() => {
      expect(progressBar).toHaveStyle({ width: '50%' });
    });
  });

  it('pauses auto close on hover', async () => {
    const onClose = vi.fn();
    render(<Toast message="Test" duration={1000} pauseOnHover onClose={onClose} />);
    
    const container = screen.getByTestId('toast-container');
    
    vi.advanceTimersByTime(500);
    fireEvent.mouseEnter(container);
    
    vi.advanceTimersByTime(1000);
    expect(onClose).not.toHaveBeenCalled();
    
    fireEvent.mouseLeave(container);
    vi.advanceTimersByTime(500);
    
    await waitFor(() => {
      expect(onClose).toHaveBeenCalled();
    });
  });

  it('supports animation enter', () => {
    render(<Toast message="Test" animate />);
    
    const container = screen.getByTestId('toast-container');
    expect(container).toHaveClass('animate-enter');
  });

  it('handles animation exit', async () => {
    const onClose = vi.fn();
    render(<Toast message="Test" animate closable onClose={onClose} />);
    
    const closeButton = screen.getByTestId('toast-close');
    fireEvent.click(closeButton);
    
    const container = screen.getByTestId('toast-container');
    expect(container).toHaveClass('animate-exit');
  });

  it('supports RTL layout', () => {
    render(<Toast message="Test" rtl />);
    
    const container = screen.getByTestId('toast-container');
    expect(container).toHaveClass('rtl');
  });

  it('shows multiple lines for long messages', () => {
    const longMessage = 'This is a very long toast message that should wrap to multiple lines when displayed';
    render(<Toast message={longMessage} multiline />);
    
    const container = screen.getByTestId('toast-container');
    expect(container).toHaveClass('multiline');
  });

  it('supports priority levels', () => {
    const priorities = ['low', 'normal', 'high', 'urgent'] as const;
    
    priorities.forEach(priority => {
      const { unmount } = render(<Toast message="Test" priority={priority} />);
      const container = screen.getByTestId('toast-container');
      expect(container).toHaveClass(`priority-${priority}`);
      unmount();
    });
  });

  it('displays timestamp when showTimestamp is true', () => {
    render(<Toast message="Test" showTimestamp />);
    
    expect(screen.getByTestId('toast-timestamp')).toBeInTheDocument();
  });

  it('supports custom timestamp format', () => {
    const customTimestamp = '2023-01-01 12:00:00';
    render(<Toast message="Test" showTimestamp timestamp={customTimestamp} />);
    
    expect(screen.getByText(customTimestamp)).toBeInTheDocument();
  });

  it('handles keyboard accessibility', () => {
    const onClose = vi.fn();
    render(<Toast message="Test" closable onClose={onClose} />);
    
    const closeButton = screen.getByTestId('toast-close');
    
    expect(closeButton).toHaveAttribute('tabindex', '0');
    
    fireEvent.keyDown(closeButton, { key: 'Enter' });
    expect(onClose).toHaveBeenCalled();
  });

  it('supports custom close button', () => {
    const customCloseButton = <button data-testid="custom-close">×</button>;
    render(<Toast message="Test" closeButton={customCloseButton} />);
    
    expect(screen.getByTestId('custom-close')).toBeInTheDocument();
  });

  it('handles loading state', () => {
    render(<Toast message="Test" loading />);
    
    expect(screen.getByTestId('toast-loading')).toBeInTheDocument();
  });

  it('shows loading spinner', () => {
    render(<Toast message="Processing..." loading showLoadingSpinner />);
    
    expect(screen.getByTestId('loading-spinner')).toBeInTheDocument();
  });

  it('supports rich content rendering', () => {
    const richContent = (
      <div data-testid="rich-content">
        <strong>Bold text</strong> and <em>italic text</em>
      </div>
    );
    
    render(<Toast content={richContent} />);
    
    expect(screen.getByTestId('rich-content')).toBeInTheDocument();
  });

  it('supports stacking behavior', () => {
    render(<Toast message="Test" stackable stackIndex={2} />);
    
    const container = screen.getByTestId('toast-container');
    expect(container).toHaveClass('stackable');
    expect(container).toHaveAttribute('data-stack-index', '2');
  });

  it('handles dismiss on click outside', () => {
    const onClose = vi.fn();
    render(<Toast message="Test" dismissOnClickOutside onClose={onClose} />);
    
    fireEvent.mouseDown(document.body);
    
    expect(onClose).toHaveBeenCalled();
  });

  it('supports swipe to dismiss on mobile', () => {
    const onClose = vi.fn();
    render(<Toast message="Test" swipeToDismiss onClose={onClose} />);
    
    const container = screen.getByTestId('toast-container');
    
    fireEvent.touchStart(container, { touches: [{ clientX: 0, clientY: 0 }] });
    fireEvent.touchMove(container, { touches: [{ clientX: 150, clientY: 0 }] });
    fireEvent.touchEnd(container, { changedTouches: [{ clientX: 150, clientY: 0 }] });
    
    expect(onClose).toHaveBeenCalled();
  });

  it('supports persistent toasts', () => {
    const onClose = vi.fn();
    render(<Toast message="Test" persistent duration={1000} onClose={onClose} />);
    
    vi.advanceTimersByTime(2000);
    expect(onClose).not.toHaveBeenCalled();
  });

  it('handles error boundary for action failures', () => {
    const errorAction = {
      label: 'Error Action',
      onClick: () => { throw new Error('Action failed'); }
    };
    
    render(<Toast message="Test" action={errorAction} />);
    
    const actionButton = screen.getByTestId('toast-action');
    
    expect(() => fireEvent.click(actionButton)).not.toThrow();
  });

  it('supports custom styling', () => {
    render(<Toast message="Test" className="custom-toast" />);
    
    const container = screen.getByTestId('toast-container');
    expect(container).toHaveClass('custom-toast');
  });

  it('supports custom data attributes', () => {
    render(<Toast message="Test" data-category="system" data-id="toast-1" />);
    
    const container = screen.getByTestId('toast-container');
    expect(container).toHaveAttribute('data-category', 'system');
    expect(container).toHaveAttribute('data-id', 'toast-1');
  });

  it('handles visibility state changes', () => {
    const { rerender } = render(<Toast message="Test" visible={true} />);
    
    let container = screen.getByTestId('toast-container');
    expect(container).toBeVisible();
    
    rerender(<Toast message="Test" visible={false} />);
    
    expect(screen.queryByTestId('toast-container')).not.toBeInTheDocument();
  });

  it('supports sound notifications', () => {
    const mockPlay = vi.fn();
    global.Audio = vi.fn(() => ({ play: mockPlay })) as any;
    
    render(<Toast message="Test" playSound soundUrl="/toast.mp3" />);
    
    expect(global.Audio).toHaveBeenCalledWith('/toast.mp3');
    expect(mockPlay).toHaveBeenCalled();
  });

  it('handles focus management', () => {
    render(<Toast message="Test" autoFocus />);
    
    const container = screen.getByTestId('toast-container');
    expect(container).toHaveFocus();
  });

  it('supports accessibility labels', () => {
    render(
      <Toast 
        message="Test" 
        ariaLabel="System toast"
        ariaLive="polite"
      />
    );
    
    const container = screen.getByTestId('toast-container');
    expect(container).toHaveAttribute('aria-label', 'System toast');
    expect(container).toHaveAttribute('aria-live', 'polite');
  });

  it('supports toast queuing', () => {
    render(<Toast message="Test" queueable maxQueue={3} />);
    
    const container = screen.getByTestId('toast-container');
    expect(container).toHaveClass('queueable');
    expect(container).toHaveAttribute('data-max-queue', '3');
  });

  it('supports drag to reposition', () => {
    const onDrag = vi.fn();
    render(<Toast message="Test" draggable onDrag={onDrag} />);
    
    const container = screen.getByTestId('toast-container');
    expect(container).toHaveAttribute('draggable', 'true');
    
    fireEvent.dragStart(container);
    expect(onDrag).toHaveBeenCalled();
  });

  it('supports inline display', () => {
    render(<Toast message="Test" inline />);
    
    const container = screen.getByTestId('toast-container');
    expect(container).toHaveClass('inline');
  });

  it('supports different animation types', () => {
    const animations = ['slide', 'fade', 'bounce', 'zoom'] as const;
    
    animations.forEach(animation => {
      const { unmount } = render(<Toast message="Test" animationType={animation} />);
      const container = screen.getByTestId('toast-container');
      expect(container).toHaveClass(`animation-${animation}`);
      unmount();
    });
  });

  it('supports toast groups', () => {
    render(<Toast message="Test" group="notifications" />);
    
    const container = screen.getByTestId('toast-container');
    expect(container).toHaveAttribute('data-group', 'notifications');
  });

  it('handles maximum width', () => {
    render(<Toast message="Test" maxWidth="300px" />);
    
    const container = screen.getByTestId('toast-container');
    expect(container).toHaveStyle({ maxWidth: '300px' });
  });

  it('supports shadow and border customization', () => {
    render(<Toast message="Test" shadow="lg" border="thick" />);
    
    const container = screen.getByTestId('toast-container');
    expect(container).toHaveClass('shadow-lg', 'border-thick');
  });

  it('handles click to dismiss', () => {
    const onClose = vi.fn();
    render(<Toast message="Test" clickToDismiss onClose={onClose} />);
    
    const container = screen.getByTestId('toast-container');
    fireEvent.click(container);
    
    expect(onClose).toHaveBeenCalled();
  });

  it('supports escape key to dismiss', () => {
    const onClose = vi.fn();
    render(<Toast message="Test" escapeKeyToDismiss onClose={onClose} />);
    
    const container = screen.getByTestId('toast-container');
    container.focus();
    fireEvent.keyDown(container, { key: 'Escape' });
    
    expect(onClose).toHaveBeenCalled();
  });

  it('supports toast with image', () => {
    render(<Toast message="Test" image="/test-image.jpg" imageAlt="Test image" />);
    
    expect(screen.getByTestId('toast-image')).toBeInTheDocument();
    expect(screen.getByAltText('Test image')).toBeInTheDocument();
  });
});