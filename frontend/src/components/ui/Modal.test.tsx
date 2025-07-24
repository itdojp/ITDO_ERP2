import { render, fireEvent, screen, waitFor } from '@testing-library/react';
import { Modal } from './Modal';

describe('Modal', () => {
  const defaultProps = {
    isOpen: true,
    onClose: jest.fn(),
    children: <div>Modal content</div>
  };

  beforeEach(() => {
    jest.clearAllMocks();
    document.body.style.overflow = 'unset';
  });

  afterEach(() => {
    document.body.style.overflow = 'unset';
  });

  it('renders modal content when open', () => {
    render(<Modal {...defaultProps} />);
    expect(screen.getByText('Modal content')).toBeInTheDocument();
  });

  it('does not render when closed', () => {
    render(<Modal {...defaultProps} isOpen={false} />);
    expect(screen.queryByText('Modal content')).not.toBeInTheDocument();
  });

  it('displays title when provided', () => {
    render(<Modal {...defaultProps} title="Test Modal" />);
    expect(screen.getByText('Test Modal')).toBeInTheDocument();
  });

  it('shows close button by default', () => {
    render(<Modal {...defaultProps} title="Test Modal" />);
    const closeButton = screen.getByLabelText('Close modal');
    expect(closeButton).toBeInTheDocument();
  });

  it('hides close button when disabled', () => {
    render(<Modal {...defaultProps} title="Test Modal" showCloseButton={false} />);
    expect(screen.queryByLabelText('Close modal')).not.toBeInTheDocument();
  });

  it('calls onClose when close button is clicked', () => {
    const onClose = jest.fn();
    render(<Modal {...defaultProps} onClose={onClose} title="Test Modal" />);
    
    const closeButton = screen.getByLabelText('Close modal');
    fireEvent.click(closeButton);
    
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it('calls onClose when overlay is clicked', () => {
    const onClose = jest.fn();
    render(<Modal {...defaultProps} onClose={onClose} />);
    
    const overlay = screen.getByRole('dialog');
    fireEvent.click(overlay);
    
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it('does not close when clicking modal content', () => {
    const onClose = jest.fn();
    render(<Modal {...defaultProps} onClose={onClose} />);
    
    const content = screen.getByText('Modal content');
    fireEvent.click(content);
    
    expect(onClose).not.toHaveBeenCalled();
  });

  it('does not close on overlay click when disabled', () => {
    const onClose = jest.fn();
    render(<Modal {...defaultProps} onClose={onClose} closeOnOverlayClick={false} />);
    
    const overlay = screen.getByRole('dialog');
    fireEvent.click(overlay);
    
    expect(onClose).not.toHaveBeenCalled();
  });

  it('calls onClose when Escape key is pressed', () => {
    const onClose = jest.fn();
    render(<Modal {...defaultProps} onClose={onClose} />);
    
    fireEvent.keyDown(document, { key: 'Escape' });
    
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it('does not close on Escape when disabled', () => {
    const onClose = jest.fn();
    render(<Modal {...defaultProps} onClose={onClose} closeOnEscape={false} />);
    
    fireEvent.keyDown(document, { key: 'Escape' });
    
    expect(onClose).not.toHaveBeenCalled();
  });

  it('prevents body scroll when enabled', () => {
    render(<Modal {...defaultProps} preventScroll={true} />);
    expect(document.body.style.overflow).toBe('hidden');
  });

  it('does not prevent body scroll when disabled', () => {
    render(<Modal {...defaultProps} preventScroll={false} />);
    expect(document.body.style.overflow).toBe('unset');
  });

  it('restores body scroll on unmount', () => {
    const { unmount } = render(<Modal {...defaultProps} preventScroll={true} />);
    expect(document.body.style.overflow).toBe('hidden');
    
    unmount();
    expect(document.body.style.overflow).toBe('unset');
  });

  it('renders footer when provided', () => {
    const footer = <button>Action Button</button>;
    render(<Modal {...defaultProps} footer={footer} />);
    expect(screen.getByText('Action Button')).toBeInTheDocument();
  });

  it('applies small size classes', () => {
    render(<Modal {...defaultProps} size="sm" />);
    const modal = screen.getByRole('dialog').firstChild as HTMLElement;
    expect(modal).toHaveClass('max-w-md');
  });

  it('applies medium size classes', () => {
    render(<Modal {...defaultProps} size="md" />);
    const modal = screen.getByRole('dialog').firstChild as HTMLElement;
    expect(modal).toHaveClass('max-w-lg');
  });

  it('applies large size classes', () => {
    render(<Modal {...defaultProps} size="lg" />);
    const modal = screen.getByRole('dialog').firstChild as HTMLElement;
    expect(modal).toHaveClass('max-w-2xl');
  });

  it('applies extra large size classes', () => {
    render(<Modal {...defaultProps} size="xl" />);
    const modal = screen.getByRole('dialog').firstChild as HTMLElement;
    expect(modal).toHaveClass('max-w-4xl');
  });

  it('applies full size classes', () => {
    render(<Modal {...defaultProps} size="full" />);
    const modal = screen.getByRole('dialog').firstChild as HTMLElement;
    expect(modal).toHaveClass('max-w-full', 'w-full', 'h-full');
  });

  it('applies custom className', () => {
    render(<Modal {...defaultProps} className="custom-modal" />);
    const modal = screen.getByRole('dialog').firstChild as HTMLElement;
    expect(modal).toHaveClass('custom-modal');
  });

  it('applies custom overlay className', () => {
    render(<Modal {...defaultProps} overlayClassName="custom-overlay" />);
    const overlay = screen.getByRole('dialog');
    expect(overlay).toHaveClass('custom-overlay');
  });

  it('applies custom content className', () => {
    render(<Modal {...defaultProps} contentClassName="custom-content" />);
    const modal = screen.getByRole('dialog').firstChild as HTMLElement;
    expect(modal).toHaveClass('custom-content');
  });

  it('centers modal by default', () => {
    render(<Modal {...defaultProps} />);
    const overlay = screen.getByRole('dialog');
    expect(overlay).toHaveClass('items-center');
  });

  it('positions modal at top when not centered', () => {
    render(<Modal {...defaultProps} centered={false} />);
    const overlay = screen.getByRole('dialog');
    expect(overlay).toHaveClass('items-start', 'pt-20');
  });

  it('handles focus trap with Tab key', async () => {
    render(
      <Modal {...defaultProps} title="Test Modal">
        <button>First Button</button>
        <button>Second Button</button>
      </Modal>
    );

    const firstButton = screen.getByText('First Button');
    const secondButton = screen.getByText('Second Button');
    const closeButton = screen.getByLabelText('Close modal');

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
      <Modal {...defaultProps} title="Test Modal">
        <button>First Button</button>
        <button>Second Button</button>
      </Modal>
    );

    const firstButton = screen.getByText('First Button');
    const closeButton = screen.getByLabelText('Close modal');

    firstButton.focus();
    expect(document.activeElement).toBe(firstButton);

    fireEvent.keyDown(document, { key: 'Tab', shiftKey: true });
    await waitFor(() => {
      expect(document.activeElement).toBe(closeButton);
    });
  });

  it('sets proper ARIA attributes', () => {
    render(<Modal {...defaultProps} title="Test Modal" />);
    const modal = screen.getByRole('dialog');
    
    expect(modal).toHaveAttribute('aria-modal', 'true');
    expect(modal).toHaveAttribute('aria-labelledby', 'modal-title');
  });

  it('does not set aria-labelledby when no title', () => {
    render(<Modal {...defaultProps} />);
    const modal = screen.getByRole('dialog');
    
    expect(modal).not.toHaveAttribute('aria-labelledby');
  });

  it('focuses first focusable element when opened', async () => {
    render(
      <Modal {...defaultProps}>
        <button>First Button</button>
        <button>Second Button</button>
      </Modal>
    );

    await waitFor(() => {
      const firstButton = screen.getByText('First Button');
      expect(document.activeElement).toBe(firstButton);
    });
  });

  it('handles animation fade', () => {
    render(<Modal {...defaultProps} animation="fade" />);
    const modal = screen.getByRole('dialog').firstChild as HTMLElement;
    expect(modal).toHaveClass('opacity-100');
  });

  it('handles animation slide', () => {
    render(<Modal {...defaultProps} animation="slide" />);
    const modal = screen.getByRole('dialog').firstChild as HTMLElement;
    expect(modal).toHaveClass('translate-y-0');
  });

  it('handles animation zoom', () => {
    render(<Modal {...defaultProps} animation="zoom" />);
    const modal = screen.getByRole('dialog').firstChild as HTMLElement;
    expect(modal).toHaveClass('scale-100');
  });

  it('handles no animation', () => {
    render(<Modal {...defaultProps} animation="none" />);
    const modal = screen.getByRole('dialog').firstChild as HTMLElement;
    expect(modal).not.toHaveClass('transition-all');
  });
});