import { render, fireEvent, screen } from '@testing-library/react';
import { TimePicker } from './TimePicker';

describe('TimePicker', () => {
  it('renders with placeholder', () => {
    render(<TimePicker placeholder="Select time" />);
    expect(screen.getByPlaceholderText('Select time')).toBeInTheDocument();
  });

  it('opens dropdown when clicked', () => {
    render(<TimePicker />);
    const input = screen.getByRole('textbox');
    fireEvent.click(input);
    expect(screen.getByText('現在の時刻を選択')).toBeInTheDocument();
  });

  it('formats time correctly in 24-hour format', () => {
    render(<TimePicker value="14:30" format="24" />);
    expect(screen.getByDisplayValue('14:30')).toBeInTheDocument();
  });

  it('formats time correctly in 12-hour format', () => {
    render(<TimePicker value="14:30" format="12" />);
    expect(screen.getByDisplayValue('2:30 PM')).toBeInTheDocument();
  });

  it('calls onChange when time is selected', () => {
    const handleChange = jest.fn();
    render(<TimePicker onChange={handleChange} />);
    
    const input = screen.getByRole('textbox');
    fireEvent.click(input);
    
    // Select a time option
    const timeOption = screen.getByText('09:00');
    fireEvent.click(timeOption);
    
    expect(handleChange).toHaveBeenCalledWith('09:00');
  });

  it('selects current time when "now" button is clicked', () => {
    const handleChange = jest.fn();
    render(<TimePicker onChange={handleChange} />);
    
    const input = screen.getByRole('textbox');
    fireEvent.click(input);
    
    const nowButton = screen.getByText('現在の時刻を選択');
    fireEvent.click(nowButton);
    
    expect(handleChange).toHaveBeenCalledWith(
      expect.stringMatching(/^\d{2}:\d{2}$/)
    );
  });

  it('respects minute step configuration', () => {
    render(<TimePicker minuteStep={30} />);
    const input = screen.getByRole('textbox');
    fireEvent.click(input);
    
    // Should have options like 00:00, 00:30, 01:00, 01:30, etc.
    expect(screen.getByText('00:30')).toBeInTheDocument();
    expect(screen.getByText('01:30')).toBeInTheDocument();
    expect(screen.queryByText('00:15')).not.toBeInTheDocument();
  });

  it('respects disabled state', () => {
    render(<TimePicker disabled />);
    const input = screen.getByRole('textbox');
    expect(input).toBeDisabled();
    
    fireEvent.click(input);
    expect(screen.queryByText('現在の時刻を選択')).not.toBeInTheDocument();
  });

  it('applies correct size classes', () => {
    const { rerender } = render(<TimePicker size="sm" />);
    expect(screen.getByRole('textbox')).toHaveClass('h-8', 'text-sm', 'px-3');

    rerender(<TimePicker size="lg" />);
    expect(screen.getByRole('textbox')).toHaveClass('h-12', 'text-lg', 'px-5');
  });

  it('closes dropdown when clicking outside', () => {
    render(
      <div>
        <TimePicker />
        <button>Outside button</button>
      </div>
    );
    
    const input = screen.getByRole('textbox');
    fireEvent.click(input);
    expect(screen.getByText('現在の時刻を選択')).toBeInTheDocument();
    
    const outsideButton = screen.getByText('Outside button');
    fireEvent.mouseDown(outsideButton);
    
    expect(screen.queryByText('現在の時刻を選択')).not.toBeInTheDocument();
  });

  it('highlights selected time in dropdown', () => {
    render(<TimePicker value="10:00" />);
    const input = screen.getByRole('textbox');
    fireEvent.click(input);
    
    const selectedOption = screen.getByText('10:00');
    expect(selectedOption).toHaveClass('bg-blue-100', 'text-blue-700');
  });
});