import { render, fireEvent, screen, waitFor, act } from '@testing-library/react';
import { Drawer } from './Drawer';

describe('Drawer', () => {
  const defaultProps = {
    isOpen: true,
    onClose: jest.fn(),
    children: <div>Drawer content</div>
  };

  beforeEach(() => {
    jest.clearAllMocks();
    document.body.style.overflow = 'unset';
    jest.useFakeTimers();
  });

  afterEach(() => {
    document.body.style.overflow = 'unset';
    jest.runOnlyPendingTimers();
    jest.useRealTimers();
  });

  it('renders drawer content when open', () => {
    render(<Drawer {...defaultProps} />);
    expect(screen.getByText('Drawer content')).toBeInTheDocument();
  });

  it('does not render when closed initially', () => {
    render(<Drawer {...defaultProps} isOpen={false} />);
    expect(screen.queryByText('Drawer content')).not.toBeInTheDocument();
  });

  it('displays title when provided', () => {
    render(<Drawer {...defaultProps} title="Test Drawer" />);
    expect(screen.getByText('Test Drawer')).toBeInTheDocument();
  });

  it('shows close button by default', () => {
    render(<Drawer {...defaultProps} title="Test Drawer" />);
    const closeButton = screen.getByLabelText('Close drawer');
    expect(closeButton).toBeInTheDocument();
  });

  it('hides close button when disabled', () => {
    render(<Drawer {...defaultProps} title="Test Drawer" showCloseButton={false} />);
    expect(screen.queryByLabelText('Close drawer')).not.toBeInTheDocument();
  });

  it('calls onClose when close button is clicked', async () => {
    const onClose = jest.fn();
    render(<Drawer {...defaultProps} onClose={onClose} title="Test Drawer" />);
    
    const closeButton = screen.getByLabelText('Close drawer');
    fireEvent.click(closeButton);
    
    act(() => {
      jest.advanceTimersByTime(300);
    });
    
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it('calls onClose when overlay is clicked', async () => {
    const onClose = jest.fn();
    render(<Drawer {...defaultProps} onClose={onClose} />);
    
    const overlay = screen.getByRole('dialog').parentElement?.firstChild as HTMLElement;
    fireEvent.click(overlay);
    
    act(() => {
      jest.advanceTimersByTime(300);
    });
    
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it('does not close when clicking drawer content', () => {
    const onClose = jest.fn();
    render(<Drawer {...defaultProps} onClose={onClose} />);
    
    const content = screen.getByText('Drawer content');
    fireEvent.click(content);
    
    act(() => {
      jest.advanceTimersByTime(300);
    });
    
    expect(onClose).not.toHaveBeenCalled();
  });

  it('does not close on overlay click when disabled', async () => {
    const onClose = jest.fn();
    render(<Drawer {...defaultProps} onClose={onClose} closeOnOverlayClick={false} />);
    
    const overlay = screen.getByRole('dialog').parentElement?.firstChild as HTMLElement;
    fireEvent.click(overlay);
    
    act(() => {
      jest.advanceTimersByTime(300);
    });
    
    expect(onClose).not.toHaveBeenCalled();
  });

  it('calls onClose when Escape key is pressed', async () => {
    const onClose = jest.fn();
    render(<Drawer {...defaultProps} onClose={onClose} />);
    
    fireEvent.keyDown(document, { key: 'Escape' });
    
    act(() => {
      jest.advanceTimersByTime(300);
    });
    
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it('does not close on Escape when disabled', async () => {
    const onClose = jest.fn();
    render(<Drawer {...defaultProps} onClose={onClose} closeOnEscape={false} />);
    
    fireEvent.keyDown(document, { key: 'Escape' });
    
    act(() => {
      jest.advanceTimersByTime(300);
    });
    
    expect(onClose).not.toHaveBeenCalled();
  });

  it('prevents body scroll when open', () => {
    render(<Drawer {...defaultProps} />);
    expect(document.body.style.overflow).toBe('hidden');
  });

  it('restores body scroll on close', async () => {
    const { rerender } = render(<Drawer {...defaultProps} />);
    expect(document.body.style.overflow).toBe('hidden');
    
    rerender(<Drawer {...defaultProps} isOpen={false} />);
    act(() => {
      jest.advanceTimersByTime(300);
    });
    
    await waitFor(() => {
      expect(document.body.style.overflow).toBe('unset');
    });
  });

  it('renders footer when provided', () => {
    const footer = <button>Action Button</button>;
    render(<Drawer {...defaultProps} footer={footer} />);
    expect(screen.getByText('Action Button')).toBeInTheDocument();
  });

  it('applies right placement classes by default', () => {
    render(<Drawer {...defaultProps} />);
    const drawer = screen.getByRole('dialog');
    expect(drawer).toHaveClass('right-0', 'top-0', 'h-full');
  });

  it('applies left placement classes', () => {
    render(<Drawer {...defaultProps} placement="left" />);
    const drawer = screen.getByRole('dialog');
    expect(drawer).toHaveClass('left-0', 'top-0', 'h-full');
  });

  it('applies top placement classes', () => {
    render(<Drawer {...defaultProps} placement="top" />);
    const drawer = screen.getByRole('dialog');
    expect(drawer).toHaveClass('top-0', 'left-0', 'w-full');
  });

  it('applies bottom placement classes', () => {
    render(<Drawer {...defaultProps} placement="bottom" />);
    const drawer = screen.getByRole('dialog');
    expect(drawer).toHaveClass('bottom-0', 'left-0', 'w-full');
  });

  it('applies small size classes for horizontal placement', () => {
    render(<Drawer {...defaultProps} placement="right" size="sm" />);
    const drawer = screen.getByRole('dialog');
    expect(drawer).toHaveClass('w-80');
  });

  it('applies medium size classes for horizontal placement', () => {
    render(<Drawer {...defaultProps} placement="right" size="md" />);
    const drawer = screen.getByRole('dialog');
    expect(drawer).toHaveClass('w-96');
  });

  it('applies large size classes for horizontal placement', () => {
    render(<Drawer {...defaultProps} placement="right" size="lg" />);
    const drawer = screen.getByRole('dialog');
    expect(drawer).toHaveClass('w-[32rem]');
  });

  it('applies extra large size classes for horizontal placement', () => {
    render(<Drawer {...defaultProps} placement="right" size="xl" />);
    const drawer = screen.getByRole('dialog');
    expect(drawer).toHaveClass('w-[40rem]');
  });

  it('applies full size classes for horizontal placement', () => {
    render(<Drawer {...defaultProps} placement="right" size="full" />);
    const drawer = screen.getByRole('dialog');
    expect(drawer).toHaveClass('w-full');
  });

  it('applies small size classes for vertical placement', () => {
    render(<Drawer {...defaultProps} placement="top" size="sm" />);
    const drawer = screen.getByRole('dialog');
    expect(drawer).toHaveClass('h-80');
  });

  it('applies medium size classes for vertical placement', () => {
    render(<Drawer {...defaultProps} placement="top" size="md" />);
    const drawer = screen.getByRole('dialog');
    expect(drawer).toHaveClass('h-96');
  });

  it('applies large size classes for vertical placement', () => {
    render(<Drawer {...defaultProps} placement="top" size="lg" />);
    const drawer = screen.getByRole('dialog');
    expect(drawer).toHaveClass('h-[32rem]');
  });

  it('applies extra large size classes for vertical placement', () => {
    render(<Drawer {...defaultProps} placement="top" size="xl" />);
    const drawer = screen.getByRole('dialog');
    expect(drawer).toHaveClass('h-[40rem]');
  });

  it('applies full size classes for vertical placement', () => {
    render(<Drawer {...defaultProps} placement="top" size="full" />);
    const drawer = screen.getByRole('dialog');
    expect(drawer).toHaveClass('h-full');
  });

  it('applies custom className', () => {
    render(<Drawer {...defaultProps} className="custom-drawer" />);
    const drawer = screen.getByRole('dialog');
    expect(drawer).toHaveClass('custom-drawer');
  });

  it('applies custom overlay className', () => {
    render(<Drawer {...defaultProps} overlayClassName="custom-overlay" />);
    const overlay = screen.getByRole('dialog').parentElement?.firstChild as HTMLElement;
    expect(overlay).toHaveClass('custom-overlay');
  });

  it('applies custom content className', () => {
    render(<Drawer {...defaultProps} contentClassName="custom-content" />);
    const drawer = screen.getByRole('dialog');
    expect(drawer).toHaveClass('custom-content');
  });

  it('hides overlay when disabled', () => {
    render(<Drawer {...defaultProps} showOverlay={false} />);
    const container = screen.getByRole('dialog').parentElement;
    const overlay = container?.querySelector('[class*="bg-black"]');
    expect(overlay).not.toBeInTheDocument();
  });

  it('calls onOpen when drawer opens', () => {
    const onOpen = jest.fn();
    render(<Drawer {...defaultProps} onOpen={onOpen} />);
    expect(onOpen).toHaveBeenCalledTimes(1);
  });

  it('calls onClosed when drawer closes', async () => {
    const onClosed = jest.fn();
    const onClose = jest.fn();
    render(<Drawer {...defaultProps} onClose={onClose} onClosed={onClosed} />);
    
    const closeButton = screen.getByLabelText('Close drawer');
    fireEvent.click(closeButton);
    
    act(() => {
      jest.advanceTimersByTime(300);
    });
    
    expect(onClosed).toHaveBeenCalledTimes(1);
  });

  it('handles focus trap with Tab key', async () => {
    render(
      <Drawer {...defaultProps} title="Test Drawer">
        <button>First Button</button>
        <button>Second Button</button>
      </Drawer>
    );

    const firstButton = screen.getByText('First Button');
    const secondButton = screen.getByText('Second Button');
    const closeButton = screen.getByLabelText('Close drawer');

    firstButton.focus();
    expect(document.activeElement).toBe(firstButton);

    fireEvent.keyDown(document, { key: 'Tab' });
    await waitFor(() => {
      expect(document.activeElement).toBe(secondButton);
    });

    fireEvent.keyDown(document, { key: 'Tab' });
    await waitFor(() => {
      expect(document.activeElement).toBe(closeButton);
    });
  });

  it('handles reverse focus trap with Shift+Tab', async () => {
    render(
      <Drawer {...defaultProps} title="Test Drawer">
        <button>First Button</button>
        <button>Second Button</button>
      </Drawer>
    );

    const firstButton = screen.getByText('First Button');
    const closeButton = screen.getByLabelText('Close drawer');

    firstButton.focus();
    expect(document.activeElement).toBe(firstButton);

    fireEvent.keyDown(document, { key: 'Tab', shiftKey: true });
    await waitFor(() => {
      expect(document.activeElement).toBe(closeButton);
    });
  });

  it('sets proper ARIA attributes', () => {
    render(<Drawer {...defaultProps} title="Test Drawer" />);
    const drawer = screen.getByRole('dialog');
    
    expect(drawer).toHaveAttribute('aria-modal', 'true');
    expect(drawer).toHaveAttribute('aria-labelledby', 'drawer-title');
  });

  it('does not set aria-labelledby when no title', () => {
    render(<Drawer {...defaultProps} />);
    const drawer = screen.getByRole('dialog');
    
    expect(drawer).not.toHaveAttribute('aria-labelledby');
  });

  it('focuses first focusable element when opened', async () => {
    render(
      <Drawer {...defaultProps}>
        <button>First Button</button>
        <button>Second Button</button>
      </Drawer>
    );

    await waitFor(() => {
      const firstButton = screen.getByText('First Button');
      expect(document.activeElement).toBe(firstButton);
    });
  });

  it('applies transform classes for right placement', () => {
    render(<Drawer {...defaultProps} placement="right" />);
    const drawer = screen.getByRole('dialog');
    expect(drawer).toHaveClass('translate-x-0');
  });

  it('applies transform classes for left placement', () => {
    render(<Drawer {...defaultProps} placement="left" />);
    const drawer = screen.getByRole('dialog');
    expect(drawer).toHaveClass('translate-x-0');
  });

  it('applies transform classes for top placement', () => {
    render(<Drawer {...defaultProps} placement="top" />);
    const drawer = screen.getByRole('dialog');
    expect(drawer).toHaveClass('translate-y-0');
  });

  it('applies transform classes for bottom placement', () => {
    render(<Drawer {...defaultProps} placement="bottom" />);
    const drawer = screen.getByRole('dialog');
    expect(drawer).toHaveClass('translate-y-0');
  });

  it('prevents double closing during animation', async () => {
    const onClose = jest.fn();
    render(<Drawer {...defaultProps} onClose={onClose} title="Test Drawer" />);
    
    const closeButton = screen.getByLabelText('Close drawer');
    
    fireEvent.click(closeButton);
    fireEvent.click(closeButton);
    
    act(() => {
      jest.advanceTimersByTime(300);
    });
    
    expect(onClose).toHaveBeenCalledTimes(1);
  });
});