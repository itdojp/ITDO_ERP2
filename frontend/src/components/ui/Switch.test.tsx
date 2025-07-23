import React from 'react';
import { render, fireEvent, screen, act } from '@testing-library/react';
import { vi } from 'vitest';
import { Switch } from './Switch';

describe('Switch', () => {
  it('renders with default state', () => {
    render(<Switch />);
    
    const switchElement = screen.getByRole('switch');
    expect(switchElement).toBeInTheDocument();
    expect(switchElement).not.toBeChecked();
  });

  it('renders with initial checked state', () => {
    render(<Switch checked />);
    
    const switchElement = screen.getByRole('switch');
    expect(switchElement).toBeChecked();
  });

  it('handles controlled checked state', () => {
    const { rerender } = render(<Switch checked={false} />);
    
    const switchElement = screen.getByRole('switch');
    expect(switchElement).not.toBeChecked();
    
    rerender(<Switch checked={true} />);
    expect(switchElement).toBeChecked();
  });

  it('handles uncontrolled with defaultChecked', () => {
    render(<Switch defaultChecked />);
    
    const switchElement = screen.getByRole('switch');
    expect(switchElement).toBeChecked();
  });

  it('calls onChange when clicked', () => {
    const onChange = vi.fn();
    render(<Switch onChange={onChange} />);
    
    const switchElement = screen.getByRole('switch');
    fireEvent.click(switchElement);
    
    expect(onChange).toHaveBeenCalledWith(true, expect.any(Object));
  });

  it('toggles state in uncontrolled mode', () => {
    render(<Switch />);
    
    const switchElement = screen.getByRole('switch');
    expect(switchElement).not.toBeChecked();
    
    fireEvent.click(switchElement);
    expect(switchElement).toBeChecked();
    
    fireEvent.click(switchElement);
    expect(switchElement).not.toBeChecked();
  });

  it('handles disabled state', () => {
    const onChange = vi.fn();
    render(<Switch disabled onChange={onChange} />);
    
    const switchElement = screen.getByRole('switch');
    expect(switchElement).toBeDisabled();
    
    fireEvent.click(switchElement);
    expect(onChange).not.toHaveBeenCalled();
  });

  it('applies size classes correctly', () => {
    const { rerender } = render(<Switch size="sm" />);
    let switchTrack = screen.getByRole('switch').parentElement?.querySelector('[class*="w-8"]');
    expect(switchTrack).toHaveClass('w-8', 'h-4');
    
    rerender(<Switch size="md" />);
    switchTrack = screen.getByRole('switch').parentElement?.querySelector('[class*="w-12"]');
    expect(switchTrack).toHaveClass('w-12', 'h-6');
    
    rerender(<Switch size="lg" />);
    switchTrack = screen.getByRole('switch').parentElement?.querySelector('[class*="w-16"]');
    expect(switchTrack).toHaveClass('w-16', 'h-8');
  });

  it('applies color variants correctly', () => {
    const { rerender } = render(<Switch checked color="primary" />);
    let switchTrack = screen.getByRole('switch').parentElement?.querySelector('[class*="bg-blue-600"]');
    expect(switchTrack).toHaveClass('bg-blue-600');
    
    rerender(<Switch checked color="success" />);
    switchTrack = screen.getByRole('switch').parentElement?.querySelector('[class*="bg-green-600"]');
    expect(switchTrack).toHaveClass('bg-green-600');
    
    rerender(<Switch checked color="warning" />);
    switchTrack = screen.getByRole('switch').parentElement?.querySelector('[class*="bg-yellow-600"]');
    expect(switchTrack).toHaveClass('bg-yellow-600');
    
    rerender(<Switch checked color="danger" />);
    switchTrack = screen.getByRole('switch').parentElement?.querySelector('[class*="bg-red-600"]');
    expect(switchTrack).toHaveClass('bg-red-600');
  });

  it('displays labels correctly', () => {
    render(<Switch checkedLabel="ON" uncheckedLabel="OFF" />);
    
    const switchElement = screen.getByRole('switch');
    expect(screen.getByText('OFF')).toBeInTheDocument();
    
    fireEvent.click(switchElement);
    expect(screen.getByText('ON')).toBeInTheDocument();
    expect(screen.queryByText('OFF')).not.toBeInTheDocument();
  });

  it('displays icons correctly', () => {
    const CheckIcon = () => <span data-testid="check-icon">✓</span>;
    const XIcon = () => <span data-testid="x-icon">✗</span>;
    
    render(<Switch checkedIcon={<CheckIcon />} uncheckedIcon={<XIcon />} />);
    
    const switchElement = screen.getByRole('switch');
    expect(screen.getByTestId('x-icon')).toBeInTheDocument();
    
    fireEvent.click(switchElement);
    expect(screen.getByTestId('check-icon')).toBeInTheDocument();
    expect(screen.queryByTestId('x-icon')).not.toBeInTheDocument();
  });

  it('handles keyboard interactions', () => {
    const onChange = vi.fn();
    render(<Switch onChange={onChange} />);
    
    const switchElement = screen.getByRole('switch');
    switchElement.focus();
    
    fireEvent.keyDown(switchElement, { key: 'Enter' });
    expect(onChange).toHaveBeenCalledWith(true, expect.any(Object));
    
    onChange.mockClear();
    fireEvent.keyDown(switchElement, { key: ' ' });
    expect(onChange).toHaveBeenCalledWith(false, expect.any(Object));
  });

  it('does not respond to keyboard when disabled', () => {
    const onChange = vi.fn();
    render(<Switch disabled onChange={onChange} />);
    
    const switchElement = screen.getByRole('switch');
    switchElement.focus();
    
    fireEvent.keyDown(switchElement, { key: 'Enter' });
    expect(onChange).not.toHaveBeenCalled();
  });

  it('shows loading state', () => {
    render(<Switch loading />);
    
    const loader = screen.getByRole('img', { hidden: true });
    expect(loader).toHaveClass('animate-spin');
    
    const switchElement = screen.getByRole('switch');
    expect(switchElement).toBeDisabled();
  });

  it('applies custom className', () => {
    render(<Switch className="custom-switch" />);
    
    const container = screen.getByRole('switch').closest('.custom-switch');
    expect(container).toBeInTheDocument();
  });

  it('displays description text', () => {
    render(<Switch description="Toggle this setting" />);
    
    expect(screen.getByText('Toggle this setting')).toBeInTheDocument();
  });

  it('has proper accessibility attributes', () => {
    render(<Switch aria-label="Toggle notifications" />);
    
    const switchElement = screen.getByRole('switch');
    expect(switchElement).toHaveAttribute('aria-label', 'Toggle notifications');
    expect(switchElement).toHaveAttribute('aria-checked', 'false');
  });

  it('updates aria-checked when toggled', () => {
    render(<Switch />);
    
    const switchElement = screen.getByRole('switch');
    expect(switchElement).toHaveAttribute('aria-checked', 'false');
    
    fireEvent.click(switchElement);
    expect(switchElement).toHaveAttribute('aria-checked', 'true');
  });

  it('handles async onChange', async () => {
    const asyncOnChange = vi.fn(() => Promise.resolve());
    render(<Switch onChange={asyncOnChange} />);
    
    const switchElement = screen.getByRole('switch');
    
    await act(async () => {
      fireEvent.click(switchElement);
    });
    
    expect(asyncOnChange).toHaveBeenCalled();
  });

  it('prevents multiple clicks during loading', () => {
    const onChange = vi.fn();
    render(<Switch loading onChange={onChange} />);
    
    const switchElement = screen.getByRole('switch');
    fireEvent.click(switchElement);
    fireEvent.click(switchElement);
    fireEvent.click(switchElement);
    
    expect(onChange).not.toHaveBeenCalled();
  });

  it('applies focus styles correctly', () => {
    render(<Switch />);
    
    const switchElement = screen.getByRole('switch');
    switchElement.focus();
    
    expect(switchElement).toHaveFocus();
    const switchTrack = switchElement.parentElement?.querySelector('[class*="focus-visible:ring-2"]');
    expect(switchTrack).toHaveClass('focus-visible:ring-2');
  });

  it('handles controlled mode correctly', () => {
    const onChange = vi.fn();
    const { rerender } = render(<Switch checked={false} onChange={onChange} />);
    
    const switchElement = screen.getByRole('switch');
    expect(switchElement).not.toBeChecked();
    
    fireEvent.click(switchElement);
    expect(onChange).toHaveBeenCalledWith(true, expect.any(Object));
    
    // In controlled mode, state doesn't change until parent updates props
    expect(switchElement).not.toBeChecked();
    
    rerender(<Switch checked={true} onChange={onChange} />);
    expect(switchElement).toBeChecked();
  });

  it('supports ref forwarding', () => {
    const ref = React.createRef<HTMLInputElement>();
    render(<Switch ref={ref} />);
    
    expect(ref.current).toBeInstanceOf(HTMLInputElement);
    expect(ref.current?.type).toBe('checkbox');
  });

  it('displays before and after content', () => {
    render(<Switch before={<span>Before</span>} after={<span>After</span>} />);
    
    expect(screen.getByText('Before')).toBeInTheDocument();
    expect(screen.getByText('After')).toBeInTheDocument();
  });

  it('handles rapid toggling correctly', () => {
    const onChange = vi.fn();
    render(<Switch onChange={onChange} />);
    
    const switchElement = screen.getByRole('switch');
    
    // Rapid clicking
    fireEvent.click(switchElement);
    fireEvent.click(switchElement);
    fireEvent.click(switchElement);
    fireEvent.click(switchElement);
    
    expect(onChange).toHaveBeenCalledTimes(4);
    expect(onChange).toHaveBeenNthCalledWith(1, true, expect.any(Object));
    expect(onChange).toHaveBeenNthCalledWith(2, false, expect.any(Object));
    expect(onChange).toHaveBeenNthCalledWith(3, true, expect.any(Object));
    expect(onChange).toHaveBeenNthCalledWith(4, false, expect.any(Object));
  });

  it('maintains consistent thumb position animation', () => {
    render(<Switch />);
    
    const switchElement = screen.getByRole('switch');
    const thumb = switchElement.parentElement?.querySelector('[class*="translate-x"]');
    
    expect(thumb).toHaveClass('translate-x-0.5');
    
    fireEvent.click(switchElement);
    
    // After animation, thumb should be in checked position
    expect(thumb).toHaveClass('translate-x-6');
  });

  it('applies disabled styles correctly', () => {
    render(<Switch disabled />);
    
    const switchTrack = screen.getByRole('switch').parentElement?.querySelector('[class*="opacity-50"]');
    expect(switchTrack).toHaveClass('opacity-50', 'cursor-not-allowed');
  });
});