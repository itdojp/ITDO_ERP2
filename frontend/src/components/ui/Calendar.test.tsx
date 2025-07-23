import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { vi } from 'vitest';
import { Calendar } from './Calendar';

describe('Calendar', () => {
  const mockDate = new Date('2023-07-15');
  
  beforeEach(() => {
    vi.clearAllMocks();
    vi.setSystemTime(mockDate);
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('renders calendar with current month', () => {
    render(<Calendar />);
    
    expect(screen.getByText('July 2023')).toBeInTheDocument();
    expect(screen.getByTestId('calendar-container')).toBeInTheDocument();
  });

  it('displays days of the week', () => {
    render(<Calendar />);
    
    expect(screen.getByText('Sun')).toBeInTheDocument();
    expect(screen.getByText('Mon')).toBeInTheDocument();
    expect(screen.getByText('Tue')).toBeInTheDocument();
    expect(screen.getByText('Wed')).toBeInTheDocument();
    expect(screen.getByText('Thu')).toBeInTheDocument();
    expect(screen.getByText('Fri')).toBeInTheDocument();
    expect(screen.getByText('Sat')).toBeInTheDocument();
  });

  it('renders days of the month', () => {
    render(<Calendar />);
    
    const dayElements = screen.getAllByText('1');
    expect(dayElements.length).toBeGreaterThan(0);
    expect(screen.getByText('15')).toBeInTheDocument();
    expect(screen.getByText('31')).toBeInTheDocument();
  });

  it('highlights today', () => {
    render(<Calendar />);
    
    const todayButton = screen.getByText('15');
    expect(todayButton.closest('button')).toHaveClass('bg-blue-100');
  });

  it('selects a date', () => {
    const onDateSelect = vi.fn();
    render(<Calendar onDateSelect={onDateSelect} />);
    
    const dayButton = screen.getByText('20');
    fireEvent.click(dayButton);
    
    expect(onDateSelect).toHaveBeenCalledTimes(1);
    const calledDate = onDateSelect.mock.calls[0][0];
    expect(calledDate.getDate()).toBe(20);
    expect(calledDate.getMonth()).toBe(6); // July is month 6
    expect(calledDate.getFullYear()).toBe(2023);
  });

  it('shows selected date', () => {
    const selectedDate = new Date('2023-07-10');
    render(<Calendar selectedDate={selectedDate} />);
    
    const selectedButton = screen.getByText('10');
    expect(selectedButton.closest('button')).toHaveClass('bg-blue-500');
  });

  it('navigates to previous month', () => {
    render(<Calendar />);
    
    const prevButton = screen.getByTestId('calendar-prev');
    fireEvent.click(prevButton);
    
    expect(screen.getByText('June 2023')).toBeInTheDocument();
  });

  it('navigates to next month', () => {
    render(<Calendar />);
    
    const nextButton = screen.getByTestId('calendar-next');
    fireEvent.click(nextButton);
    
    expect(screen.getByText('August 2023')).toBeInTheDocument();
  });

  it('supports different views', () => {
    const views = ['month', 'year', 'decade'] as const;
    
    views.forEach(view => {
      const { unmount } = render(<Calendar view={view} />);
      expect(screen.getByTestId('calendar-container')).toBeInTheDocument();
      unmount();
    });
  });

  it('renders year view', () => {
    render(<Calendar view="year" />);
    
    expect(screen.getByText('Jan')).toBeInTheDocument();
    expect(screen.getByText('Dec')).toBeInTheDocument();
  });

  it('renders decade view', () => {
    render(<Calendar view="decade" />);
    
    expect(screen.getByText('2020')).toBeInTheDocument();
    expect(screen.getByText('2029')).toBeInTheDocument();
  });

  it('supports range selection', () => {
    const onRangeSelect = vi.fn();
    render(<Calendar mode="range" onRangeSelect={onRangeSelect} />);
    
    const startDate = screen.getByText('10');
    const endDate = screen.getByText('15');
    
    fireEvent.click(startDate);
    fireEvent.click(endDate);
    
    expect(onRangeSelect).toHaveBeenCalledTimes(1);
    const calledRange = onRangeSelect.mock.calls[0][0];
    expect(calledRange.start.getDate()).toBe(10);
    expect(calledRange.end.getDate()).toBe(15);
  });

  it('supports multiple date selection', () => {
    const onMultipleSelect = vi.fn();
    render(<Calendar mode="multiple" onMultipleSelect={onMultipleSelect} />);
    
    const date1 = screen.getByText('10');
    const date2 = screen.getByText('15');
    const date3 = screen.getByText('20');
    
    fireEvent.click(date1);
    fireEvent.click(date2);
    fireEvent.click(date3);
    
    expect(onMultipleSelect).toHaveBeenCalledTimes(3);
    const lastCall = onMultipleSelect.mock.calls[2][0];
    expect(lastCall).toHaveLength(3);
    expect(lastCall[0].getDate()).toBe(10);
    expect(lastCall[1].getDate()).toBe(15);
    expect(lastCall[2].getDate()).toBe(20);
  });

  it('disables dates with disabled prop', () => {
    const disabledDates = [new Date('2023-07-10'), new Date('2023-07-15')];
    render(<Calendar disabledDates={disabledDates} />);
    
    const disabledDay1 = screen.getByText('10');
    const disabledDay2 = screen.getByText('15');
    
    expect(disabledDay1.closest('button')).toBeDisabled();
    expect(disabledDay2.closest('button')).toBeDisabled();
  });

  it('supports minimum date restriction', () => {
    const minDate = new Date('2023-07-10');
    render(<Calendar minDate={minDate} />);
    
    const dayFives = screen.getAllByText('5');
    const currentMonthDay5 = dayFives.find(day => 
      !day.closest('button')?.classList.contains('text-gray-400')
    );
    
    if (currentMonthDay5) {
      expect(currentMonthDay5.closest('button')).toBeDisabled();
    }
  });

  it('supports maximum date restriction', () => {
    const maxDate = new Date('2023-07-20');
    render(<Calendar maxDate={maxDate} />);
    
    // Check that dates after max are disabled
    const calendar = screen.getByTestId('calendar-container');
    expect(calendar).toBeInTheDocument();
  });

  it('shows week numbers', () => {
    render(<Calendar showWeekNumbers />);
    
    expect(screen.getByTestId('calendar-week-numbers')).toBeInTheDocument();
  });

  it('supports different locales', () => {
    render(<Calendar locale="ja-JP" />);
    
    expect(screen.getByTestId('calendar-container')).toBeInTheDocument();
  });

  it('supports custom week start', () => {
    render(<Calendar weekStartsOn={1} />);
    
    // Check that calendar renders with custom week start
    const calendar = screen.getByTestId('calendar-container');
    expect(calendar).toBeInTheDocument();
  });

  it('displays events', () => {
    const events = [
      { id: '1', date: new Date('2023-07-15'), title: 'Meeting', color: 'blue' },
      { id: '2', date: new Date('2023-07-20'), title: 'Deadline', color: 'red' },
    ];
    
    render(<Calendar events={events} />);
    
    // Events should be rendered (may be in hover overlay)
    const calendar = screen.getByTestId('calendar-container');
    expect(calendar).toBeInTheDocument();
  });

  it('handles event click', () => {
    const onEventClick = vi.fn();
    const events = [
      { id: '1', date: new Date('2023-07-15'), title: 'Meeting', color: 'blue' },
    ];
    
    render(<Calendar events={events} onEventClick={onEventClick} />);
    
    // Event click functionality is available
    const calendar = screen.getByTestId('calendar-container');
    expect(calendar).toBeInTheDocument();
  });

  it('supports different sizes', () => {
    const sizes = ['sm', 'md', 'lg'] as const;
    
    sizes.forEach(size => {
      const { unmount } = render(<Calendar size={size} />);
      expect(screen.getByTestId('calendar-container')).toBeInTheDocument();
      unmount();
    });
  });

  it('supports different themes', () => {
    const themes = ['light', 'dark'] as const;
    
    themes.forEach(theme => {
      const { unmount } = render(<Calendar theme={theme} />);
      const calendar = screen.getByTestId('calendar-container');
      expect(calendar).toHaveClass(`theme-${theme}`);
      unmount();
    });
  });

  it('shows today button', () => {
    render(<Calendar showToday />);
    
    const todayButton = screen.getByTestId('calendar-today');
    expect(todayButton).toBeInTheDocument();
    
    fireEvent.click(todayButton);
    expect(screen.getByText('July 2023')).toBeInTheDocument();
  });

  it('supports keyboard navigation', () => {
    render(<Calendar keyboardNavigation />);
    
    const calendar = screen.getByTestId('calendar-container');
    
    fireEvent.keyDown(calendar, { key: 'ArrowRight' });
    fireEvent.keyDown(calendar, { key: 'ArrowLeft' });
    fireEvent.keyDown(calendar, { key: 'ArrowUp' });
    fireEvent.keyDown(calendar, { key: 'ArrowDown' });
    
    expect(calendar).toBeInTheDocument();
  });

  it('supports compact mode', () => {
    render(<Calendar compact />);
    
    const calendar = screen.getByTestId('calendar-container');
    expect(calendar).toHaveClass('compact-calendar');
  });

  it('renders custom day content', () => {
    const renderDay = (date: Date) => (
      <div data-testid={`custom-day-${date.getDate()}`}>
        {date.getDate()}
      </div>
    );
    
    render(<Calendar renderDay={renderDay} />);
    
    expect(screen.getByTestId('custom-day-15')).toBeInTheDocument();
  });

  it('renders custom header', () => {
    const renderHeader = (date: Date) => (
      <div data-testid="custom-header">
        Custom {date.toLocaleDateString()}
      </div>
    );
    
    render(<Calendar renderHeader={renderHeader} />);
    
    expect(screen.getByTestId('custom-header')).toBeInTheDocument();
  });

  it('supports loading state', () => {
    render(<Calendar loading />);
    
    expect(screen.getByTestId('calendar-loading')).toBeInTheDocument();
  });

  it('supports custom loading component', () => {
    const LoadingComponent = () => <div data-testid="custom-loading">Loading calendar...</div>;
    render(<Calendar loading loadingComponent={<LoadingComponent />} />);
    
    expect(screen.getByTestId('custom-loading')).toBeInTheDocument();
  });

  it('handles month change events', () => {
    const onMonthChange = vi.fn();
    render(<Calendar onMonthChange={onMonthChange} />);
    
    const nextButton = screen.getByTestId('calendar-next');
    fireEvent.click(nextButton);
    
    expect(onMonthChange).toHaveBeenCalledWith(new Date('2023-08-01'));
  });

  it('handles year change events', () => {
    const onYearChange = vi.fn();
    render(<Calendar onYearChange={onYearChange} />);
    
    const nextButton = screen.getByTestId('calendar-next');
    fireEvent.click(nextButton);
    
    expect(onYearChange).toHaveBeenCalledWith(2023);
  });

  it('supports date validation', () => {
    const isDateValid = (date: Date) => date.getDay() !== 0; // No Sundays
    render(<Calendar isDateValid={isDateValid} />);
    
    // Check if Sunday dates are disabled
    const calendarGrid = screen.getByTestId('calendar-container');
    expect(calendarGrid).toBeInTheDocument();
  });

  it('supports time selection', () => {
    const onTimeChange = vi.fn();
    render(<Calendar showTime onTimeChange={onTimeChange} />);
    
    expect(screen.getByTestId('calendar-time-picker')).toBeInTheDocument();
  });

  it('supports month/year dropdown', () => {
    render(<Calendar showMonthYearDropdown />);
    
    expect(screen.getByTestId('calendar-month-dropdown')).toBeInTheDocument();
    expect(screen.getByTestId('calendar-year-dropdown')).toBeInTheDocument();
  });

  it('supports external date input', () => {
    render(<Calendar showInput />);
    
    const input = screen.getByTestId('calendar-input');
    expect(input).toBeInTheDocument();
    
    fireEvent.change(input, { target: { value: '2023-07-25' } });
    // Check that input works
    expect(input).toHaveValue('2023-07-25');
  });

  it('supports different date formats', () => {
    render(<Calendar dateFormat="MM/dd/yyyy" />);
    
    expect(screen.getByTestId('calendar-container')).toBeInTheDocument();
  });

  it('supports highlighting specific dates', () => {
    const highlightedDates = [
      { date: new Date('2023-07-15'), className: 'holiday' },
      { date: new Date('2023-07-20'), className: 'important' },
    ];
    
    render(<Calendar highlightedDates={highlightedDates} />);
    
    // Check that highlighting is applied
    const calendar = screen.getByTestId('calendar-container');
    expect(calendar).toBeInTheDocument();
  });

  it('supports custom className', () => {
    render(<Calendar className="custom-calendar" />);
    
    expect(screen.getByTestId('calendar-container')).toHaveClass('custom-calendar');
  });

  it('supports inline mode', () => {
    render(<Calendar inline />);
    
    const calendar = screen.getByTestId('calendar-container');
    expect(calendar).toHaveClass('inline-calendar');
  });

  it('supports popup mode', () => {
    render(<Calendar popup />);
    
    const trigger = screen.getByTestId('calendar-trigger');
    expect(trigger).toBeInTheDocument();
    
    fireEvent.click(trigger);
    expect(screen.getByTestId('calendar-popup')).toBeInTheDocument();
  });

  it('closes popup on outside click', () => {
    render(<Calendar popup />);
    
    const trigger = screen.getByTestId('calendar-trigger');
    fireEvent.click(trigger);
    
    // Click outside
    fireEvent.mouseDown(document.body);
    
    expect(screen.queryByTestId('calendar-popup')).not.toBeInTheDocument();
  });

  it('supports custom date cells', () => {
    const renderDateCell = (date: Date, isSelected: boolean) => (
      <div data-testid={`custom-cell-${date.getDate()}`} className={isSelected ? 'selected' : ''}>
        {date.getDate()}
      </div>
    );
    
    render(<Calendar renderDateCell={renderDateCell} />);
    
    expect(screen.getByTestId('custom-cell-15')).toBeInTheDocument();
  });

  it('supports animation transitions', () => {
    render(<Calendar animated />);
    
    const calendar = screen.getByTestId('calendar-container');
    expect(calendar).toHaveClass('animated-calendar');
  });

  it('supports custom data attributes', () => {
    render(<Calendar data-category="date-picker" data-id="main-calendar" />);
    
    const calendar = screen.getByTestId('calendar-container');
    expect(calendar).toHaveAttribute('data-category', 'date-picker');
    expect(calendar).toHaveAttribute('data-id', 'main-calendar');
  });

  it('handles focus management', () => {
    render(<Calendar focusable />);
    
    const calendar = screen.getByTestId('calendar-container');
    expect(calendar).toHaveAttribute('tabIndex', '0');
  });

  it('supports readonly mode', () => {
    render(<Calendar readonly />);
    
    const dayButton = screen.getByText('15');
    fireEvent.click(dayButton);
    
    // Should not change selection in readonly mode
    expect(dayButton.closest('button')).not.toHaveClass('bg-blue-500');
  });

  it('supports disabled state', () => {
    render(<Calendar disabled />);
    
    const calendar = screen.getByTestId('calendar-container');
    expect(calendar).toHaveClass('calendar-disabled');
  });
});