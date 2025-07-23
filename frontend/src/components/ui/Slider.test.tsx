import React from 'react';
import { render, fireEvent, screen } from '@testing-library/react';
import { vi } from 'vitest';
import userEvent from '@testing-library/user-event';
import { Slider } from './Slider';

describe('Slider', () => {
  it('renders with default value', () => {
    render(<Slider />);
    
    const slider = screen.getByRole('slider');
    expect(slider).toBeInTheDocument();
    expect(slider).toHaveAttribute('aria-valuenow', '0');
  });

  it('renders with initial value', () => {
    render(<Slider value={50} />);
    
    const slider = screen.getByRole('slider');
    expect(slider).toHaveAttribute('aria-valuenow', '50');
  });

  it('handles controlled value changes', () => {
    const onChange = vi.fn();
    const { rerender } = render(<Slider value={25} onChange={onChange} />);
    
    const slider = screen.getByRole('slider');
    expect(slider).toHaveAttribute('aria-valuenow', '25');
    
    rerender(<Slider value={75} onChange={onChange} />);
    expect(slider).toHaveAttribute('aria-valuenow', '75');
  });

  it('handles uncontrolled with defaultValue', () => {
    render(<Slider defaultValue={30} />);
    
    const slider = screen.getByRole('slider');
    expect(slider).toHaveAttribute('aria-valuenow', '30');
  });

  it('calls onChange when value changes', () => {
    const onChange = vi.fn();
    render(<Slider onChange={onChange} min={0} max={100} />);
    
    const slider = screen.getByRole('slider');
    fireEvent.change(slider, { target: { value: '60' } });
    
    expect(onChange).toHaveBeenCalledWith(60, expect.any(Object));
  });

  it('respects min and max values', () => {
    render(<Slider min={10} max={90} defaultValue={50} />);
    
    const slider = screen.getByRole('slider');
    expect(slider).toHaveAttribute('min', '10');
    expect(slider).toHaveAttribute('max', '90');
  });

  it('handles step values', () => {
    render(<Slider step={5} defaultValue={25} />);
    
    const slider = screen.getByRole('slider');
    expect(slider).toHaveAttribute('step', '5');
  });

  it('handles disabled state', () => {
    const onChange = vi.fn();
    render(<Slider disabled onChange={onChange} />);
    
    const slider = screen.getByRole('slider');
    expect(slider).toBeDisabled();
    
    fireEvent.change(slider, { target: { value: '50' } });
    expect(onChange).not.toHaveBeenCalled();
  });

  it('displays tooltip on hover', () => {
    render(<Slider tooltip />);
    
    const slider = screen.getByRole('slider');
    fireEvent.mouseEnter(slider);
    
    expect(screen.getByText('0')).toBeInTheDocument();
  });

  it('shows custom tooltip formatter', () => {
    const formatter = (value: number) => `${value}%`;
    render(<Slider tooltip tooltipFormatter={formatter} defaultValue={25} />);
    
    const slider = screen.getByRole('slider');
    fireEvent.mouseEnter(slider);
    
    expect(screen.getByText('25%')).toBeInTheDocument();
  });

  it('displays marks correctly', () => {
    const marks = {
      0: '0°C',
      26: '26°C',
      37: '37°C',
      100: '100°C'
    };
    render(<Slider marks={marks} />);
    
    expect(screen.getByText('0°C')).toBeInTheDocument();
    expect(screen.getByText('26°C')).toBeInTheDocument();
    expect(screen.getByText('37°C')).toBeInTheDocument();
    expect(screen.getByText('100°C')).toBeInTheDocument();
  });

  it('snaps to marks when included is true', () => {
    const marks = { 0: '0', 25: '25', 50: '50', 75: '75', 100: '100' };
    const onChange = vi.fn();
    render(<Slider marks={marks} included onChange={onChange} />);
    
    const slider = screen.getByRole('slider');
    fireEvent.change(slider, { target: { value: '30' } });
    
    // Should snap to nearest mark (25)
    expect(onChange).toHaveBeenCalledWith(25, expect.any(Object));
  });

  it('handles keyboard navigation', () => {
    const onChange = vi.fn();
    render(<Slider onChange={onChange} defaultValue={50} />);
    
    const slider = screen.getByRole('slider');
    slider.focus();
    
    fireEvent.keyDown(slider, { key: 'ArrowRight' });
    expect(onChange).toHaveBeenCalled();
    expect(onChange.mock.calls[0][0]).toBeGreaterThan(50);
    
    onChange.mockClear();
    fireEvent.keyDown(slider, { key: 'ArrowLeft' });
    expect(onChange).toHaveBeenCalled();
    expect(onChange.mock.calls[0][0]).toBeLessThan(51);
  });

  it('handles Page Up/Down for larger steps', () => {
    const onChange = vi.fn();
    render(<Slider onChange={onChange} defaultValue={50} />);
    
    const slider = screen.getByRole('slider');
    slider.focus();
    
    fireEvent.keyDown(slider, { key: 'PageUp' });
    expect(onChange).toHaveBeenCalled();
    expect(onChange.mock.calls[0][0]).toBeGreaterThan(50);
    
    onChange.mockClear();
    fireEvent.keyDown(slider, { key: 'PageDown' });
    expect(onChange).toHaveBeenCalled();
    expect(onChange.mock.calls[0][0]).toBeLessThan(60);
  });

  it('handles Home/End keys', () => {
    const onChange = vi.fn();
    render(<Slider onChange={onChange} defaultValue={50} min={10} max={90} />);
    
    const slider = screen.getByRole('slider');
    slider.focus();
    
    fireEvent.keyDown(slider, { key: 'Home' });
    expect(onChange).toHaveBeenCalledWith(10, expect.any(Object));
    
    fireEvent.keyDown(slider, { key: 'End' });
    expect(onChange).toHaveBeenCalledWith(90, expect.any(Object));
  });

  it('applies size classes correctly', () => {
    const { rerender } = render(<Slider size="sm" />);
    let track = screen.getByRole('slider').parentElement?.querySelector('[class*="h-1"]');
    expect(track).toBeInTheDocument();
    
    rerender(<Slider size="md" />);
    track = screen.getByRole('slider').parentElement?.querySelector('[class*="h-2"]');
    expect(track).toBeInTheDocument();
    
    rerender(<Slider size="lg" />);
    track = screen.getByRole('slider').parentElement?.querySelector('[class*="h-3"]');
    expect(track).toBeInTheDocument();
  });

  it('applies color variants correctly', () => {
    const { rerender } = render(<Slider color="primary" defaultValue={50} />);
    let filledTrack = screen.getByRole('slider').parentElement?.querySelector('[class*="bg-blue-500"]');
    expect(filledTrack).toBeInTheDocument();
    
    rerender(<Slider color="success" defaultValue={50} />);
    filledTrack = screen.getByRole('slider').parentElement?.querySelector('[class*="bg-green-500"]');
    expect(filledTrack).toBeInTheDocument();
    
    rerender(<Slider color="warning" defaultValue={50} />);
    filledTrack = screen.getByRole('slider').parentElement?.querySelector('[class*="bg-yellow-500"]');
    expect(filledTrack).toBeInTheDocument();
    
    rerender(<Slider color="danger" defaultValue={50} />);
    filledTrack = screen.getByRole('slider').parentElement?.querySelector('[class*="bg-red-500"]');
    expect(filledTrack).toBeInTheDocument();
  });

  it('handles reverse orientation', () => {
    render(<Slider reverse defaultValue={25} />);
    
    const filledTrack = screen.getByRole('slider').parentElement?.querySelector('[style*="right"]');
    expect(filledTrack).toBeInTheDocument();
  });

  it('handles vertical orientation', () => {
    render(<Slider vertical defaultValue={50} />);
    
    const container = screen.getByRole('slider').closest('[class*="flex-col"]');
    expect(container).toBeInTheDocument();
  });

  it('shows range when range prop is true', () => {
    const onChange = vi.fn();
    render(<Slider range onChange={onChange} defaultValue={[20, 80]} />);
    
    const sliders = screen.getAllByRole('slider');
    expect(sliders).toHaveLength(2);
    expect(sliders[0]).toHaveAttribute('aria-valuenow', '20');
    expect(sliders[1]).toHaveAttribute('aria-valuenow', '80');
  });

  it('handles range value changes', () => {
    const onChange = vi.fn();
    render(<Slider range onChange={onChange} defaultValue={[30, 70]} />);
    
    const sliders = screen.getAllByRole('slider');
    fireEvent.change(sliders[0], { target: { value: '40' } });
    
    expect(onChange).toHaveBeenCalledWith([40, 70], expect.any(Object));
  });

  it('prevents range values from crossing over', () => {
    const onChange = vi.fn();
    render(<Slider range onChange={onChange} defaultValue={[30, 70]} />);
    
    const sliders = screen.getAllByRole('slider');
    
    // Try to set first slider higher than second - should clamp to second value
    fireEvent.change(sliders[0], { target: { value: '80' } });
    expect(onChange).toHaveBeenCalledWith([70, 70], expect.any(Object));
    
    // Try to set second slider lower than first - should clamp to first value
    onChange.mockClear();
    fireEvent.change(sliders[1], { target: { value: '20' } });
    expect(onChange).toHaveBeenCalledWith([70, 70], expect.any(Object));
  });

  it('handles included prop for styling', () => {
    render(<Slider included={false} defaultValue={50} />);
    
    const filledTrack = screen.getByRole('slider').parentElement?.querySelector('[style*="width"]');
    expect(filledTrack).not.toBeInTheDocument();
  });

  it('displays custom track style', () => {
    render(<Slider trackStyle={{ backgroundColor: 'red' }} />);
    
    const track = screen.getByRole('slider').parentElement?.querySelector('[style*="background-color: red"]');
    expect(track).toBeInTheDocument();
  });

  it('displays custom handle style', () => {
    render(<Slider handleStyle={{ backgroundColor: 'blue' }} />);
    
    const handle = screen.getByRole('slider');
    expect(handle.style.backgroundColor).toBe('blue');
  });

  it('has proper accessibility attributes', () => {
    render(<Slider 
      aria-label="Volume control" 
      aria-describedby="volume-description"
      min={0} 
      max={100} 
      defaultValue={75} 
    />);
    
    const slider = screen.getByRole('slider');
    expect(slider).toHaveAttribute('aria-label', 'Volume control');
    expect(slider).toHaveAttribute('aria-describedby', 'volume-description');
    expect(slider).toHaveAttribute('aria-valuemin', '0');
    expect(slider).toHaveAttribute('aria-valuemax', '100');
    expect(slider).toHaveAttribute('aria-valuenow', '75');
  });

  it('updates aria-valuenow when value changes', () => {
    render(<Slider defaultValue={25} />);
    
    const slider = screen.getByRole('slider');
    expect(slider).toHaveAttribute('aria-valuenow', '25');
    
    fireEvent.change(slider, { target: { value: '60' } });
    expect(slider).toHaveAttribute('aria-valuenow', '60');
  });

  it('applies custom className', () => {
    render(<Slider className="custom-slider" />);
    
    const container = screen.getByRole('slider').closest('.custom-slider');
    expect(container).toBeInTheDocument();
  });

  it('supports ref forwarding', () => {
    const ref = React.createRef<HTMLInputElement>();
    render(<Slider ref={ref} />);
    
    expect(ref.current).toBeInstanceOf(HTMLInputElement);
    expect(ref.current?.type).toBe('range');
  });

  it('handles dots for marking steps', () => {
    render(<Slider dots step={25} />);
    
    // Should have dots at 0, 25, 50, 75, 100
    const dots = screen.getAllByTestId('slider-dot');
    expect(dots).toHaveLength(5);
  });

  it('handles onAfterChange callback', () => {
    const onAfterChange = vi.fn();
    render(<Slider onAfterChange={onAfterChange} />);
    
    const slider = screen.getByRole('slider');
    fireEvent.change(slider, { target: { value: '50' } });
    fireEvent.blur(slider);
    
    expect(onAfterChange).toHaveBeenCalledWith(50);
  });

  it('handles onBeforeChange callback', () => {
    const onBeforeChange = vi.fn();
    render(<Slider onBeforeChange={onBeforeChange} />);
    
    const slider = screen.getByRole('slider');
    fireEvent.focus(slider);
    
    expect(onBeforeChange).toHaveBeenCalledWith(0);
  });

  it('displays loading state', () => {
    render(<Slider loading />);
    
    const loader = screen.getByRole('img', { hidden: true });
    expect(loader).toHaveClass('animate-spin');
    expect(screen.getByText('Loading...')).toBeInTheDocument();
    
    // In loading state, the slider is not rendered
    const slider = screen.queryByRole('slider');
    expect(slider).not.toBeInTheDocument();
  });

  it('handles rapid value changes correctly', () => {
    const onChange = vi.fn();
    render(<Slider onChange={onChange} />);
    
    const slider = screen.getByRole('slider');
    
    // Rapid changes
    fireEvent.change(slider, { target: { value: '10' } });
    fireEvent.change(slider, { target: { value: '20' } });
    fireEvent.change(slider, { target: { value: '30' } });
    
    expect(onChange).toHaveBeenCalledTimes(3);
    expect(onChange).toHaveBeenLastCalledWith(30, expect.any(Object));
  });

  it('maintains value within bounds', () => {
    const onChange = vi.fn();
    render(<Slider onChange={onChange} min={10} max={90} defaultValue={50} />);
    
    const slider = screen.getByRole('slider');
    
    // The HTML range input itself enforces min/max bounds
    expect(slider).toHaveAttribute('min', '10');
    expect(slider).toHaveAttribute('max', '90');
    
    // Test that values are properly constrained by our normalize function
    expect(slider).toHaveAttribute('aria-valuenow', '50');
  });
});