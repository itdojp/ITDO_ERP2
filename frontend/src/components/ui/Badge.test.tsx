import { render, fireEvent, screen } from '@testing-library/react';
import { vi } from 'vitest';
import { Badge } from './Badge';

describe('Badge', () => {
  // Helper function to get the badge element (parent of text)
  const getBadgeElement = (text: string) => {
    return screen.getByText(text).parentElement;
  };
  it('renders badge content', () => {
    render(<Badge>Badge Text</Badge>);
    expect(screen.getByText('Badge Text')).toBeInTheDocument();
  });

  it('applies default variant classes', () => {
    render(<Badge>Default Badge</Badge>);
    const badge = getBadgeElement('Default Badge');
    expect(badge).toHaveClass('bg-gray-100', 'text-gray-800');
  });

  it('applies success variant classes', () => {
    render(<Badge variant="success">Success Badge</Badge>);
    const badge = getBadgeElement('Success Badge');
    expect(badge).toHaveClass('bg-green-500', 'text-white');
  });

  it('applies warning variant classes', () => {
    render(<Badge variant="warning">Warning Badge</Badge>);
    const badge = getBadgeElement('Warning Badge');
    expect(badge).toHaveClass('bg-yellow-500', 'text-white');
  });

  it('applies error variant classes', () => {
    render(<Badge variant="error">Error Badge</Badge>);
    const badge = getBadgeElement('Error Badge');
    expect(badge).toHaveClass('bg-red-500', 'text-white');
  });

  it('applies info variant classes', () => {
    render(<Badge variant="info">Info Badge</Badge>);
    const badge = getBadgeElement('Info Badge');
    expect(badge).toHaveClass('bg-blue-500', 'text-white');
  });

  it('applies secondary variant classes', () => {
    render(<Badge variant="secondary">Secondary Badge</Badge>);
    const badge = getBadgeElement('Secondary Badge');
    expect(badge).toHaveClass('bg-gray-600', 'text-white');
  });

  it('applies outline style when outline is true', () => {
    render(<Badge variant="success" outline>Outline Badge</Badge>);
    const badge = getBadgeElement('Outline Badge');
    expect(badge).toHaveClass('border-2', 'bg-transparent', 'border-green-500', 'text-green-600');
  });

  it('applies small size classes', () => {
    render(<Badge size="sm">Small Badge</Badge>);
    const badge = getBadgeElement('Small Badge');
    expect(badge).toHaveClass('px-2', 'py-0.5', 'text-xs');
  });

  it('applies medium size classes', () => {
    render(<Badge size="md">Medium Badge</Badge>);
    const badge = getBadgeElement('Medium Badge');
    expect(badge).toHaveClass('px-2.5', 'py-1', 'text-sm');
  });

  it('applies large size classes', () => {
    render(<Badge size="lg">Large Badge</Badge>);
    const badge = getBadgeElement('Large Badge');
    expect(badge).toHaveClass('px-3', 'py-1.5', 'text-base');
  });

  it('applies rounded shape by default', () => {
    render(<Badge>Rounded Badge</Badge>);
    const badge = getBadgeElement('Rounded Badge');
    expect(badge).toHaveClass('rounded-md');
  });

  it('applies pill shape classes', () => {
    render(<Badge shape="pill">Pill Badge</Badge>);
    const badge = getBadgeElement('Pill Badge');
    expect(badge).toHaveClass('rounded-full');
  });

  it('applies square shape classes', () => {
    render(<Badge shape="square">Square Badge</Badge>);
    const badge = getBadgeElement('Square Badge');
    expect(badge).toHaveClass('rounded-none');
  });

  it('renders as dot when dot is true', () => {
    render(<Badge dot>Dot Badge</Badge>);
    const badge = screen.getByLabelText('Dot Badge');
    expect(badge).toHaveClass('w-3', 'h-3', 'rounded-full');
    expect(screen.queryByText('Dot Badge')).not.toBeInTheDocument();
  });

  it('renders icon on the left by default', () => {
    render(<Badge icon={<span data-testid="test-icon">🔥</span>}>Badge with Icon</Badge>);
    expect(screen.getByTestId('test-icon')).toBeInTheDocument();
  });

  it('renders icon on the right when iconPosition is right', () => {
    render(<Badge icon={<span data-testid="test-icon">🔥</span>} iconPosition="right">Badge with Icon</Badge>);
    expect(screen.getByTestId('test-icon')).toBeInTheDocument();
  });

  it('shows remove button when removable is true', () => {
    render(<Badge removable>Removable Badge</Badge>);
    expect(screen.getByLabelText('Remove badge')).toBeInTheDocument();
  });

  it('calls onRemove when remove button is clicked', () => {
    const onRemove = vi.fn();
    render(<Badge removable onRemove={onRemove}>Removable Badge</Badge>);
    
    fireEvent.click(screen.getByLabelText('Remove badge'));
    
    expect(onRemove).toHaveBeenCalledTimes(1);
  });

  it('calls onClick when badge is clicked', () => {
    const onClick = vi.fn();
    render(<Badge onClick={onClick}>Clickable Badge</Badge>);
    
    fireEvent.click(screen.getByText('Clickable Badge'));
    
    expect(onClick).toHaveBeenCalledTimes(1);
  });

  it('renders as button when onClick is provided', () => {
    render(<Badge onClick={vi.fn()}>Button Badge</Badge>);
    const badge = screen.getByRole('button');
    expect(badge).toBeInTheDocument();
    expect(badge).toHaveAttribute('type', 'button');
  });

  it('renders as link when href is provided', () => {
    render(<Badge href="/test">Link Badge</Badge>);
    const badge = screen.getByRole('link');
    expect(badge).toBeInTheDocument();
    expect(badge).toHaveAttribute('href', '/test');
  });

  it('handles keyboard navigation with Enter key', () => {
    const onClick = vi.fn();
    render(<Badge onClick={onClick}>Keyboard Badge</Badge>);
    
    const badge = screen.getByRole('button');
    fireEvent.keyDown(badge, { key: 'Enter' });
    
    expect(onClick).toHaveBeenCalledTimes(1);
  });

  it('handles keyboard navigation with Space key', () => {
    const onClick = vi.fn();
    render(<Badge onClick={onClick}>Keyboard Badge</Badge>);
    
    const badge = screen.getByRole('button');
    fireEvent.keyDown(badge, { key: ' ' });
    
    expect(onClick).toHaveBeenCalledTimes(1);
  });

  it('applies disabled state correctly', () => {
    const onClick = vi.fn();
    render(<Badge onClick={onClick} disabled>Disabled Badge</Badge>);
    
    const badge = getBadgeElement('Disabled Badge');
    expect(badge).toHaveClass('opacity-50', 'cursor-not-allowed');
    expect(badge).toHaveAttribute('aria-disabled', 'true');
    
    fireEvent.click(badge!);
    expect(onClick).not.toHaveBeenCalled();
  });

  it('does not render as link when disabled and href is provided', () => {
    render(<Badge href="/test" disabled>Disabled Link</Badge>);
    const badge = screen.getByText('Disabled Link');
    expect(badge.tagName).not.toBe('A');
  });

  it('applies animated classes when animated is true', () => {
    render(<Badge animated>Animated Badge</Badge>);
    const badge = getBadgeElement('Animated Badge');
    expect(badge).toHaveClass('transition-all', 'duration-300', 'ease-in-out');
  });

  it('applies pulse animation when pulse is true', () => {
    render(<Badge pulse>Pulse Badge</Badge>);
    const badge = getBadgeElement('Pulse Badge');
    expect(badge).toHaveClass('animate-pulse');
  });

  it('applies ping animation to dot when pulse is true', () => {
    render(<Badge dot pulse>Pulse Dot</Badge>);
    const badge = screen.getByLabelText('Pulse Dot');
    expect(badge).toHaveClass('animate-ping');
  });

  it('applies border when bordered is true', () => {
    render(<Badge bordered>Bordered Badge</Badge>);
    const badge = getBadgeElement('Bordered Badge');
    expect(badge).toHaveClass('border');
  });

  it('applies custom className', () => {
    render(<Badge className="custom-badge">Custom Badge</Badge>);
    const badge = getBadgeElement('Custom Badge');
    expect(badge).toHaveClass('custom-badge');
  });

  it('displays count when count is provided', () => {
    render(<Badge count={5}>Count Badge</Badge>);
    expect(screen.getByText('5')).toBeInTheDocument();
  });

  it('displays count with plus when count exceeds maxCount', () => {
    render(<Badge count={150} maxCount={99}>Count Badge</Badge>);
    expect(screen.getByText('99+')).toBeInTheDocument();
  });

  it('does not render when count is 0 and showZero is false', () => {
    const { container } = render(<Badge count={0}>Count Badge</Badge>);
    expect(container.firstChild).toBeNull();
  });

  it('renders when count is 0 and showZero is true', () => {
    render(<Badge count={0} showZero>Count Badge</Badge>);
    expect(screen.getByText('0')).toBeInTheDocument();
  });

  it('prevents remove button click from triggering badge click', () => {
    const onClick = vi.fn();
    const onRemove = vi.fn();
    
    render(
      <Badge onClick={onClick} removable onRemove={onRemove}>
        Badge with Remove
      </Badge>
    );
    
    fireEvent.click(screen.getByLabelText('Remove badge'));
    
    expect(onRemove).toHaveBeenCalledTimes(1);
    expect(onClick).not.toHaveBeenCalled();
  });

  it('applies focus styles when clickable', () => {
    render(<Badge onClick={vi.fn()}>Clickable Badge</Badge>);
    const badge = screen.getByRole('button');
    expect(badge).toHaveClass('focus:outline-none', 'focus:ring-2', 'focus:ring-offset-2', 'focus:ring-blue-500');
  });

  it('does not apply focus styles when not clickable', () => {
    render(<Badge>Static Badge</Badge>);
    const badge = getBadgeElement('Static Badge');
    expect(badge).not.toHaveClass('focus:outline-none');
  });

  it('sets tabIndex to -1 when disabled and clickable', () => {
    render(<Badge onClick={vi.fn()} disabled>Disabled Clickable</Badge>);
    const badge = getBadgeElement('Disabled Clickable');
    expect(badge).toHaveAttribute('tabindex', '-1');
  });

  it('sets tabIndex to 0 when clickable and not disabled', () => {
    render(<Badge onClick={vi.fn()}>Clickable Badge</Badge>);
    const badge = screen.getByRole('button');
    expect(badge).toHaveAttribute('tabindex', '0');
  });

  it('truncates long text content', () => {
    render(<Badge>Very Long Badge Text That Should Be Truncated</Badge>);
    const textElement = screen.getByText('Very Long Badge Text That Should Be Truncated');
    expect(textElement).toHaveClass('truncate');
  });

  it('does not handle keyboard events when disabled', () => {
    const onClick = vi.fn();
    render(<Badge onClick={onClick} disabled>Disabled Badge</Badge>);
    
    const badge = screen.getByText('Disabled Badge');
    fireEvent.keyDown(badge, { key: 'Enter' });
    fireEvent.keyDown(badge, { key: ' ' });
    
    expect(onClick).not.toHaveBeenCalled();
  });

  it('renders with custom maxCount', () => {
    render(<Badge count={250} maxCount={200}>High Count Badge</Badge>);
    expect(screen.getByText('200+')).toBeInTheDocument();
  });

  it('applies hover styles for interactive variants', () => {
    render(<Badge variant="success">Success Badge</Badge>);
    const badge = getBadgeElement('Success Badge');
    expect(badge).toHaveClass('hover:bg-green-600');
  });

  it('applies hover styles for outline variants', () => {
    render(<Badge variant="success" outline>Outline Success Badge</Badge>);
    const badge = getBadgeElement('Outline Success Badge');
    expect(badge).toHaveClass('hover:bg-green-50');
  });
});