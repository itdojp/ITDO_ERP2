import { render, fireEvent, screen, waitFor, act } from '@testing-library/react';
import { Alert } from './Alert';

describe('Alert', () => {
  beforeEach(() => {
    jest.useFakeTimers();
  });

  afterEach(() => {
    jest.runOnlyPendingTimers();
    jest.useRealTimers();
  });

  it('renders alert content', () => {
    render(<Alert>Alert message</Alert>);
    expect(screen.getByText('Alert message')).toBeInTheDocument();
  });

  it('renders title when provided', () => {
    render(<Alert title="Alert Title">Alert message</Alert>);
    expect(screen.getByText('Alert Title')).toBeInTheDocument();
  });

  it('applies info variant classes by default', () => {
    render(<Alert>Alert message</Alert>);
    const alert = screen.getByRole('alert');
    expect(alert).toHaveClass('bg-blue-50', 'text-blue-800', 'border-blue-200');
  });

  it('applies success variant classes', () => {
    render(<Alert variant="success">Success message</Alert>);
    const alert = screen.getByRole('alert');
    expect(alert).toHaveClass('bg-green-50', 'text-green-800', 'border-green-200');
  });

  it('applies warning variant classes', () => {
    render(<Alert variant="warning">Warning message</Alert>);
    const alert = screen.getByRole('alert');
    expect(alert).toHaveClass('bg-yellow-50', 'text-yellow-800', 'border-yellow-200');
  });

  it('applies error variant classes', () => {
    render(<Alert variant="error">Error message</Alert>);
    const alert = screen.getByRole('alert');
    expect(alert).toHaveClass('bg-red-50', 'text-red-800', 'border-red-200');
  });

  it('applies small size classes', () => {
    render(<Alert size="sm">Alert message</Alert>);
    const alert = screen.getByRole('alert');
    expect(alert).toHaveClass('p-3', 'text-sm');
  });

  it('applies medium size classes', () => {
    render(<Alert size="md">Alert message</Alert>);
    const alert = screen.getByRole('alert');
    expect(alert).toHaveClass('p-4', 'text-sm');
  });

  it('applies large size classes', () => {
    render(<Alert size="lg">Alert message</Alert>);
    const alert = screen.getByRole('alert');
    expect(alert).toHaveClass('p-6', 'text-base');
  });

  it('renders default icon by default', () => {
    render(<Alert>Alert message</Alert>);
    const icon = screen.getByRole('alert').querySelector('svg');
    expect(icon).toBeInTheDocument();
  });

  it('renders custom icon when provided', () => {
    render(<Alert icon={<span data-testid="custom-icon">🔥</span>}>Alert message</Alert>);
    expect(screen.getByTestId('custom-icon')).toBeInTheDocument();
  });

  it('hides icon when icon is false', () => {
    render(<Alert icon={false}>Alert message</Alert>);
    const alert = screen.getByRole('alert');
    const icon = alert.querySelector('svg');
    expect(icon).not.toBeInTheDocument();
  });

  it('shows close button when closable is true', () => {
    render(<Alert closable>Alert message</Alert>);
    expect(screen.getByLabelText('Close alert')).toBeInTheDocument();
  });

  it('calls onClose when close button is clicked', () => {
    const onClose = jest.fn();
    render(<Alert closable onClose={onClose}>Alert message</Alert>);
    
    fireEvent.click(screen.getByLabelText('Close alert'));
    
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it('hides alert when close button is clicked', () => {
    render(<Alert closable>Alert message</Alert>);
    
    fireEvent.click(screen.getByLabelText('Close alert'));
    
    expect(screen.queryByText('Alert message')).not.toBeInTheDocument();
  });

  it('closes alert on Escape key when closable', () => {
    const onClose = jest.fn();
    render(<Alert closable onClose={onClose}>Alert message</Alert>);
    
    const alert = screen.getByRole('alert');
    fireEvent.keyDown(alert, { key: 'Escape' });
    
    expect(onClose).toHaveBeenCalledTimes(1);
    expect(screen.queryByText('Alert message')).not.toBeInTheDocument();
  });

  it('does not close on Escape when not closable', () => {
    const onClose = jest.fn();
    render(<Alert onClose={onClose}>Alert message</Alert>);
    
    const alert = screen.getByRole('alert');
    fireEvent.keyDown(alert, { key: 'Escape' });
    
    expect(onClose).not.toHaveBeenCalled();
    expect(screen.getByText('Alert message')).toBeInTheDocument();
  });

  it('applies border when bordered is true', () => {
    render(<Alert bordered>Alert message</Alert>);
    const alert = screen.getByRole('alert');
    expect(alert).toHaveClass('border');
  });

  it('applies rounded corners by default', () => {
    render(<Alert>Alert message</Alert>);
    const alert = screen.getByRole('alert');
    expect(alert).toHaveClass('rounded-md');
  });

  it('removes rounded corners when rounded is false', () => {
    render(<Alert rounded={false}>Alert message</Alert>);
    const alert = screen.getByRole('alert');
    expect(alert).not.toHaveClass('rounded-md');
  });

  it('auto-closes after specified delay', async () => {
    const onClose = jest.fn();
    render(
      <Alert autoClose autoCloseDelay={1000} onClose={onClose}>
        Alert message
      </Alert>
    );
    
    expect(screen.getByText('Alert message')).toBeInTheDocument();
    
    act(() => {
      jest.advanceTimersByTime(1000);
    });
    
    await waitFor(() => {
      expect(onClose).toHaveBeenCalledTimes(1);
    });
  });

  it('does not auto-close when autoClose is false', () => {
    const onClose = jest.fn();
    render(
      <Alert autoClose={false} autoCloseDelay={1000} onClose={onClose}>
        Alert message
      </Alert>
    );
    
    act(() => {
      jest.advanceTimersByTime(1000);
    });
    
    expect(onClose).not.toHaveBeenCalled();
    expect(screen.getByText('Alert message')).toBeInTheDocument();
  });

  it('applies custom className', () => {
    render(<Alert className="custom-alert">Alert message</Alert>);
    const alert = screen.getByRole('alert');
    expect(alert).toHaveClass('custom-alert');
  });

  it('applies custom titleClassName', () => {
    render(<Alert title="Title" titleClassName="custom-title">Alert message</Alert>);
    const title = screen.getByText('Title');
    expect(title).toHaveClass('custom-title');
  });

  it('applies custom contentClassName', () => {
    render(<Alert contentClassName="custom-content">Alert message</Alert>);
    const content = screen.getByText('Alert message');
    expect(content).toHaveClass('custom-content');
  });

  it('applies custom iconClassName', () => {
    render(<Alert iconClassName="custom-icon">Alert message</Alert>);
    const alert = screen.getByRole('alert');
    const iconContainer = alert.querySelector('.custom-icon');
    expect(iconContainer).toBeInTheDocument();
  });

  it('applies custom closeButtonClassName', () => {
    render(<Alert closable closeButtonClassName="custom-close">Alert message</Alert>);
    const closeButton = screen.getByLabelText('Close alert');
    expect(closeButton).toHaveClass('custom-close');
  });

  it('sets custom role when provided', () => {
    render(<Alert role="alertdialog">Alert message</Alert>);
    expect(screen.getByRole('alertdialog')).toBeInTheDocument();
  });

  it('sets tabIndex to 0 when closable', () => {
    render(<Alert closable>Alert message</Alert>);
    const alert = screen.getByRole('alert');
    expect(alert).toHaveAttribute('tabindex', '0');
  });

  it('sets tabIndex to -1 when not closable', () => {
    render(<Alert>Alert message</Alert>);
    const alert = screen.getByRole('alert');
    expect(alert).toHaveAttribute('tabindex', '-1');
  });

  it('renders different default icons for each variant', () => {
    const { rerender } = render(<Alert variant="info">Info message</Alert>);
    const infoIcon = screen.getByRole('alert').querySelector('svg');
    
    rerender(<Alert variant="success">Success message</Alert>);
    const successIcon = screen.getByRole('alert').querySelector('svg');
    
    rerender(<Alert variant="warning">Warning message</Alert>);
    const warningIcon = screen.getByRole('alert').querySelector('svg');
    
    rerender(<Alert variant="error">Error message</Alert>);
    const errorIcon = screen.getByRole('alert').querySelector('svg');
    
    // All should have different path data (different icons)
    expect(infoIcon?.querySelector('path')?.getAttribute('d')).not.toBe(
      successIcon?.querySelector('path')?.getAttribute('d')
    );
    expect(successIcon?.querySelector('path')?.getAttribute('d')).not.toBe(
      warningIcon?.querySelector('path')?.getAttribute('d')
    );
    expect(warningIcon?.querySelector('path')?.getAttribute('d')).not.toBe(
      errorIcon?.querySelector('path')?.getAttribute('d')
    );
  });

  it('clears auto-close timer on unmount', () => {
    const onClose = jest.fn();
    const { unmount } = render(
      <Alert autoClose autoCloseDelay={1000} onClose={onClose}>
        Alert message
      </Alert>
    );
    
    unmount();
    
    act(() => {
      jest.advanceTimersByTime(1000);
    });
    
    expect(onClose).not.toHaveBeenCalled();
  });

  it('applies correct focus ring colors for each variant', () => {
    const { rerender } = render(<Alert closable variant="info">Info message</Alert>);
    let closeButton = screen.getByLabelText('Close alert');
    expect(closeButton).toHaveClass('focus:ring-blue-500');
    
    rerender(<Alert closable variant="success">Success message</Alert>);
    closeButton = screen.getByLabelText('Close alert');
    expect(closeButton).toHaveClass('focus:ring-green-500');
    
    rerender(<Alert closable variant="warning">Warning message</Alert>);
    closeButton = screen.getByLabelText('Close alert');
    expect(closeButton).toHaveClass('focus:ring-yellow-500');
    
    rerender(<Alert closable variant="error">Error message</Alert>);
    closeButton = screen.getByLabelText('Close alert');
    expect(closeButton).toHaveClass('focus:ring-red-500');
  });

  it('handles complex content with JSX', () => {
    render(
      <Alert title="Complex Alert">
        <div>
          <p>This is a complex alert with multiple elements.</p>
          <button>Action Button</button>
        </div>
      </Alert>
    );
    
    expect(screen.getByText('Complex Alert')).toBeInTheDocument();
    expect(screen.getByText('This is a complex alert with multiple elements.')).toBeInTheDocument();
    expect(screen.getByText('Action Button')).toBeInTheDocument();
  });

  it('does not auto-close with delay of 0', () => {
    const onClose = jest.fn();
    render(
      <Alert autoClose autoCloseDelay={0} onClose={onClose}>
        Alert message
      </Alert>
    );
    
    act(() => {
      jest.advanceTimersByTime(1000);
    });
    
    expect(onClose).not.toHaveBeenCalled();
  });
});