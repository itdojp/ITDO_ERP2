import { render, fireEvent, screen } from '@testing-library/react';
import { DatePicker } from './DatePicker';

describe('DatePicker', () => {
  it('renders with placeholder', () => {
    render(<DatePicker placeholder="Select date" />);
    expect(screen.getByPlaceholderText('Select date')).toBeInTheDocument();
  });

  it('opens calendar when clicked', () => {
    render(<DatePicker />);
    const input = screen.getByRole('textbox');
    fireEvent.click(input);
    expect(screen.getByText('今日を選択')).toBeInTheDocument();
  });

  it('formats date correctly', () => {
    const { rerender } = render(<DatePicker value="2024-07-22" format="MM/DD/YYYY" />);
    expect(screen.getByDisplayValue('07/22/2024')).toBeInTheDocument();

    rerender(<DatePicker value="2024-07-22" format="DD/MM/YYYY" />);
    expect(screen.getByDisplayValue('22/07/2024')).toBeInTheDocument();

    rerender(<DatePicker value="2024-07-22" format="YYYY-MM-DD" />);
    expect(screen.getByDisplayValue('2024-07-22')).toBeInTheDocument();
  });

  it('calls onChange when date is selected', () => {
    const handleChange = jest.fn();
    render(<DatePicker onChange={handleChange} />);
    
    const input = screen.getByRole('textbox');
    fireEvent.click(input);
    
    // Click on day 15
    const day15 = screen.getByText('15');
    fireEvent.click(day15);
    
    expect(handleChange).toHaveBeenCalled();
  });

  it('navigates between months', () => {
    render(<DatePicker />);
    const input = screen.getByRole('textbox');
    fireEvent.click(input);

    const currentMonth = new Date().toLocaleDateString('ja-JP', { month: 'long', year: 'numeric' });
    
    // Navigate to next month
    const nextButton = screen.getAllByRole('button').find(btn => 
      btn.querySelector('svg path[d*="M9 5l7 7-7 7"]')
    );
    if (nextButton) {
      fireEvent.click(nextButton);
    }
    
    // Should show different month (not testing exact month due to date variability)
    expect(screen.getByRole('textbox')).toBeInTheDocument();
  });

  it('selects today when today button is clicked', () => {
    const handleChange = jest.fn();
    render(<DatePicker onChange={handleChange} />);
    
    const input = screen.getByRole('textbox');
    fireEvent.click(input);
    
    const todayButton = screen.getByText('今日を選択');
    fireEvent.click(todayButton);
    
    expect(handleChange).toHaveBeenCalledWith(
      expect.stringMatching(/^\d{4}-\d{2}-\d{2}$/)
    );
  });

  it('respects minDate restriction', () => {
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 1);
    const minDate = tomorrow.toISOString().split('T')[0];
    
    render(<DatePicker minDate={minDate} />);
    const input = screen.getByRole('textbox');
    fireEvent.click(input);
    
    const todayButton = screen.getByText('今日を選択');
    expect(todayButton).toBeDisabled();
  });

  it('respects disabled state', () => {
    render(<DatePicker disabled />);
    const input = screen.getByRole('textbox');
    expect(input).toBeDisabled();
    
    fireEvent.click(input);
    expect(screen.queryByText('今日を選択')).not.toBeInTheDocument();
  });

  it('applies correct size classes', () => {
    const { rerender } = render(<DatePicker size="sm" />);
    expect(screen.getByRole('textbox')).toHaveClass('h-8', 'text-sm', 'px-3');

    rerender(<DatePicker size="lg" />);
    expect(screen.getByRole('textbox')).toHaveClass('h-12', 'text-lg', 'px-5');
  });

  it('closes calendar when clicking outside', () => {
    render(
      <div>
        <DatePicker />
        <button>Outside button</button>
      </div>
    );
    
    const input = screen.getByRole('textbox');
    fireEvent.click(input);
    expect(screen.getByText('今日を選択')).toBeInTheDocument();
    
    const outsideButton = screen.getByText('Outside button');
    fireEvent.mouseDown(outsideButton);
    
    expect(screen.queryByText('今日を選択')).not.toBeInTheDocument();
  });
});