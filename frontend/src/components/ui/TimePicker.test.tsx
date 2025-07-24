<<<<<<< HEAD
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
=======
import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { vi } from "vitest";
import { TimePicker } from "./TimePicker";

describe("TimePicker", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders time picker with default time", () => {
    render(<TimePicker />);

    expect(screen.getByTestId("timepicker-container")).toBeInTheDocument();
    expect(screen.getByTestId("timepicker-input")).toBeInTheDocument();
  });

  it("displays selected time in input", () => {
    const time = { hours: 14, minutes: 30 };
    render(<TimePicker value={time} />);

    const input = screen.getByTestId("timepicker-input");
    expect(input).toHaveValue("14:30");
  });

  it("displays 12-hour format when specified", () => {
    const time = { hours: 14, minutes: 30 };
    render(<TimePicker value={time} format="12" />);

    const input = screen.getByTestId("timepicker-input");
    expect(input).toHaveValue("2:30 PM");
  });

  it("opens time picker on input click", () => {
    render(<TimePicker />);

    const input = screen.getByTestId("timepicker-input");
    fireEvent.click(input);

    expect(screen.getByTestId("timepicker-dropdown")).toBeInTheDocument();
  });

  it("opens time picker on icon click", () => {
    render(<TimePicker showIcon />);

    const icon = screen.getByTestId("timepicker-icon");
    fireEvent.click(icon);

    expect(screen.getByTestId("timepicker-dropdown")).toBeInTheDocument();
  });

  it("closes dropdown on outside click", async () => {
    render(<TimePicker />);

    const input = screen.getByTestId("timepicker-input");
    fireEvent.click(input);

    expect(screen.getByTestId("timepicker-dropdown")).toBeInTheDocument();

    fireEvent.mouseDown(document.body);

    await waitFor(() => {
      expect(
        screen.queryByTestId("timepicker-dropdown"),
      ).not.toBeInTheDocument();
    });
  });

  it("selects hour from dropdown", () => {
    const onChange = vi.fn();
    render(<TimePicker onChange={onChange} />);

    const input = screen.getByTestId("timepicker-input");
    fireEvent.click(input);

    // Find hour button specifically within the hours column
    const hoursColumn = screen.getByText("Hours").parentElement;
    const hourOption = hoursColumn?.querySelector("button:nth-child(15)"); // 14th button (0-indexed)
    if (hourOption) {
      fireEvent.click(hourOption);
    }

    expect(onChange).toHaveBeenCalledWith({ hours: 14, minutes: 0 });
  });

  it("selects minute from dropdown", () => {
    const onChange = vi.fn();
    render(<TimePicker onChange={onChange} />);

    const input = screen.getByTestId("timepicker-input");
    fireEvent.click(input);

    // Find minute button specifically within the minutes column
    const minutesColumn = screen.getByText("Minutes").parentElement;
    const minuteOption = minutesColumn?.querySelector("button:nth-child(31)"); // 30th button (0-indexed)
    if (minuteOption) {
      fireEvent.click(minuteOption);
    }

    expect(onChange).toHaveBeenCalledWith({ hours: 0, minutes: 30 });
  });

  it("supports minute step intervals", () => {
    render(<TimePicker minuteStep={15} />);

    const input = screen.getByTestId("timepicker-input");
    fireEvent.click(input);

    const minutesColumn = screen.getByText("Minutes").parentElement;

    expect(minutesColumn?.textContent).toContain("00");
    expect(minutesColumn?.textContent).toContain("15");
    expect(minutesColumn?.textContent).toContain("30");
    expect(minutesColumn?.textContent).toContain("45");
    expect(minutesColumn?.textContent).not.toContain("05");
  });

  it("supports hour step intervals", () => {
    render(<TimePicker hourStep={2} />);

    const input = screen.getByTestId("timepicker-input");
    fireEvent.click(input);

    const hoursColumn = screen.getByText("Hours").parentElement;

    expect(hoursColumn?.textContent).toContain("00");
    expect(hoursColumn?.textContent).toContain("02");
    expect(hoursColumn?.textContent).toContain("04");
    // Check for specific buttons instead of text content to avoid '01' in '10'
    const hourButtons = hoursColumn?.querySelectorAll("button");
    const buttonTexts = Array.from(hourButtons || []).map(
      (btn: any) => btn.textContent,
    );
    expect(buttonTexts).not.toContain("01");
  });

  it("supports seconds selection", () => {
    render(<TimePicker showSeconds />);

    const input = screen.getByTestId("timepicker-input");
    fireEvent.click(input);

    expect(screen.getByTestId("timepicker-seconds")).toBeInTheDocument();
  });

  it("displays seconds in input when enabled", () => {
    const time = { hours: 14, minutes: 30, seconds: 45 };
    render(<TimePicker value={time} showSeconds />);

    const input = screen.getByTestId("timepicker-input");
    expect(input).toHaveValue("14:30:45");
  });

  it("supports AM/PM selection in 12-hour format", () => {
    render(<TimePicker format="12" />);

    const input = screen.getByTestId("timepicker-input");
    fireEvent.click(input);

    expect(screen.getByTestId("timepicker-ampm")).toBeInTheDocument();
  });

  it("toggles AM/PM correctly", () => {
    const onChange = vi.fn();
    const time = { hours: 9, minutes: 30 };
    render(<TimePicker value={time} format="12" onChange={onChange} />);

    const input = screen.getByTestId("timepicker-input");
    fireEvent.click(input);

    const ampmColumn = screen.getByTestId("timepicker-ampm");
    const pmButton = ampmColumn.querySelector("button:last-child");
    if (pmButton) {
      fireEvent.click(pmButton);
    }

    expect(onChange).toHaveBeenCalledWith({ hours: 21, minutes: 30 });
  });

  it("supports different sizes", () => {
    const sizes = ["sm", "md", "lg"] as const;

    sizes.forEach((size) => {
      const { unmount } = render(<TimePicker size={size} />);
      const container = screen.getByTestId("timepicker-container");
      expect(container).toHaveClass(`size-${size}`);
      unmount();
    });
  });

  it("supports different themes", () => {
    const themes = ["light", "dark"] as const;

    themes.forEach((theme) => {
      const { unmount } = render(<TimePicker theme={theme} />);
      const container = screen.getByTestId("timepicker-container");
      expect(container).toHaveClass(`theme-${theme}`);
      unmount();
    });
  });

  it("supports disabled state", () => {
    render(<TimePicker disabled />);

    const input = screen.getByTestId("timepicker-input");
    expect(input).toBeDisabled();
  });

  it("supports readonly state", () => {
    render(<TimePicker readonly />);

    const input = screen.getByTestId("timepicker-input");
    expect(input).toHaveAttribute("readonly");
  });

  it("shows clear button when clearable", () => {
    const time = { hours: 14, minutes: 30 };
    render(<TimePicker value={time} clearable />);

    expect(screen.getByTestId("timepicker-clear")).toBeInTheDocument();
  });

  it("clears time when clear button clicked", () => {
    const onChange = vi.fn();
    const time = { hours: 14, minutes: 30 };
    render(<TimePicker value={time} clearable onChange={onChange} />);

    const clearButton = screen.getByTestId("timepicker-clear");
    fireEvent.click(clearButton);

    expect(onChange).toHaveBeenCalledWith(null);
  });

  it("validates manual time input", () => {
    const onChange = vi.fn();
    render(<TimePicker onChange={onChange} />);

    const input = screen.getByTestId("timepicker-input");
    fireEvent.change(input, { target: { value: "14:30" } });
    fireEvent.blur(input);

    expect(onChange).toHaveBeenCalledWith({ hours: 14, minutes: 30 });
  });

  it("handles invalid time input", () => {
    const onError = vi.fn();
    render(<TimePicker onError={onError} />);

    const input = screen.getByTestId("timepicker-input");
    fireEvent.change(input, { target: { value: "25:70" } });
    fireEvent.blur(input);

    expect(onError).toHaveBeenCalledWith("Invalid time format");
  });

  it("supports minimum time restriction", () => {
    const minTime = { hours: 9, minutes: 0 };
    render(<TimePicker minTime={minTime} />);

    const input = screen.getByTestId("timepicker-input");
    fireEvent.click(input);

    // Hours before 9 should be disabled - find hour 08 in the hours column
    const hoursColumn = screen.getByText("Hours").parentElement;
    const disabledHour = hoursColumn?.querySelector("button:nth-child(9)"); // 8th button (08)
    expect(disabledHour).toBeDisabled();
  });

  it("supports maximum time restriction", () => {
    const maxTime = { hours: 17, minutes: 0 };
    render(<TimePicker maxTime={maxTime} />);

    const input = screen.getByTestId("timepicker-input");
    fireEvent.click(input);

    // Hours after 17 should be disabled - find hour 18 in the hours column
    const hoursColumn = screen.getByText("Hours").parentElement;
    const disabledHour = hoursColumn?.querySelector("button:nth-child(19)"); // 18th button (18)
    expect(disabledHour).toBeDisabled();
  });

  it("supports keyboard navigation", () => {
    render(<TimePicker />);

    const input = screen.getByTestId("timepicker-input");
    fireEvent.keyDown(input, { key: "ArrowDown" });

    expect(screen.getByTestId("timepicker-dropdown")).toBeInTheDocument();
  });

  it("closes dropdown on Escape key", () => {
    render(<TimePicker />);

    const input = screen.getByTestId("timepicker-input");
    fireEvent.click(input);

    expect(screen.getByTestId("timepicker-dropdown")).toBeInTheDocument();

    fireEvent.keyDown(input, { key: "Escape" });

    expect(screen.queryByTestId("timepicker-dropdown")).not.toBeInTheDocument();
  });

  it("supports up/down arrow keys for time adjustment", () => {
    const onChange = vi.fn();
    const time = { hours: 14, minutes: 30 };
    render(<TimePicker value={time} onChange={onChange} />);

    const input = screen.getByTestId("timepicker-input");
    fireEvent.keyDown(input, { key: "ArrowUp" });

    expect(onChange).toHaveBeenCalledWith({ hours: 15, minutes: 30 });
  });

  it("supports inline mode", () => {
    render(<TimePicker inline />);

    expect(screen.getByTestId("timepicker-dropdown")).toBeInTheDocument();
    expect(screen.queryByTestId("timepicker-input")).not.toBeInTheDocument();
  });

  it("supports custom time format", () => {
    const time = { hours: 14, minutes: 30 };
    render(<TimePicker value={time} customFormat={(h, m) => `${h}h ${m}m`} />);

    const input = screen.getByTestId("timepicker-input");
    expect(input).toHaveValue("14h 30m");
  });

  it("supports placeholder text", () => {
    render(<TimePicker placeholder="Select time" />);

    const input = screen.getByTestId("timepicker-input");
    expect(input).toHaveAttribute("placeholder", "Select time");
  });

  it("supports label", () => {
    render(<TimePicker label="Meeting Time" />);

    expect(screen.getByText("Meeting Time")).toBeInTheDocument();
  });

  it("marks required field", () => {
    render(<TimePicker label="Meeting Time" required />);

    expect(screen.getByText("*")).toBeInTheDocument();
  });

  it("supports helper text", () => {
    render(<TimePicker helperText="Select your preferred time" />);

    expect(screen.getByText("Select your preferred time")).toBeInTheDocument();
  });

  it("supports error state", () => {
    render(<TimePicker error="Invalid time" />);

    const input = screen.getByTestId("timepicker-input");
    expect(input).toHaveClass("error");
    expect(screen.getByText("Invalid time")).toBeInTheDocument();
  });

  it("supports success state", () => {
    render(<TimePicker success />);

    const input = screen.getByTestId("timepicker-input");
    expect(input).toHaveClass("success");
  });

  it("supports warning state", () => {
    render(<TimePicker warning />);

    const input = screen.getByTestId("timepicker-input");
    expect(input).toHaveClass("warning");
  });

  it("supports loading state", () => {
    render(<TimePicker loading />);

    expect(screen.getByTestId("timepicker-loading")).toBeInTheDocument();
  });

  it("supports custom loading component", () => {
    const LoadingComponent = () => (
      <div data-testid="custom-loading">Loading...</div>
    );
    render(<TimePicker loading loadingComponent={<LoadingComponent />} />);

    expect(screen.getByTestId("custom-loading")).toBeInTheDocument();
  });

  it("handles focus and blur events", () => {
    const onFocus = vi.fn();
    const onBlur = vi.fn();
    render(<TimePicker onFocus={onFocus} onBlur={onBlur} />);

    const input = screen.getByTestId("timepicker-input");

    fireEvent.focus(input);
    expect(onFocus).toHaveBeenCalledTimes(1);

    fireEvent.blur(input);
    expect(onBlur).toHaveBeenCalledTimes(1);
  });

  it("supports custom input component", () => {
    const CustomInput = React.forwardRef<HTMLInputElement, any>(
      (props, ref) => <input ref={ref} {...props} data-testid="custom-input" />,
    );

    render(<TimePicker customInput={<CustomInput />} />);

    expect(screen.getByTestId("custom-input")).toBeInTheDocument();
  });

  it("supports close on select", () => {
    render(<TimePicker closeOnSelect />);

    const input = screen.getByTestId("timepicker-input");
    fireEvent.click(input);

    const hoursColumn = screen.getByText("Hours").parentElement;
    const hourOption = hoursColumn?.querySelector("button:nth-child(15)"); // 14th button
    if (hourOption) {
      fireEvent.click(hourOption);
    }

    expect(screen.queryByTestId("timepicker-dropdown")).not.toBeInTheDocument();
  });

  it("keeps dropdown open when closeOnSelect is false", () => {
    render(<TimePicker closeOnSelect={false} />);

    const input = screen.getByTestId("timepicker-input");
    fireEvent.click(input);

    const hoursColumn = screen.getByText("Hours").parentElement;
    const hourOption = hoursColumn?.querySelector("button:nth-child(15)"); // 14th button
    if (hourOption) {
      fireEvent.click(hourOption);
    }

    expect(screen.getByTestId("timepicker-dropdown")).toBeInTheDocument();
  });

  it("supports custom className", () => {
    render(<TimePicker className="custom-timepicker" />);

    const container = screen.getByTestId("timepicker-container");
    expect(container).toHaveClass("custom-timepicker");
  });

  it("supports now button", () => {
    render(<TimePicker showNow />);

    const input = screen.getByTestId("timepicker-input");
    fireEvent.click(input);

    expect(screen.getByTestId("timepicker-now")).toBeInTheDocument();
  });

  it("sets current time when now button clicked", () => {
    const onChange = vi.fn();
    vi.setSystemTime(new Date("2023-07-15T14:30:45"));

    render(<TimePicker onChange={onChange} showNow />);

    const input = screen.getByTestId("timepicker-input");
    fireEvent.click(input);

    const nowButton = screen.getByTestId("timepicker-now");
    fireEvent.click(nowButton);

    expect(onChange).toHaveBeenCalledWith({ hours: 14, minutes: 30 });
  });

  it("supports time range selection", () => {
    const onRangeChange = vi.fn();
    render(<TimePicker mode="range" onRangeChange={onRangeChange} />);

    const input = screen.getByTestId("timepicker-input");
    fireEvent.click(input);

    const hoursColumn = screen.getByText("Hours").parentElement;
    const startTime = hoursColumn?.querySelector("button:nth-child(10)"); // 9th button (09)
    const endTime = hoursColumn?.querySelector("button:nth-child(18)"); // 17th button (17)

    if (startTime) fireEvent.click(startTime);
    if (endTime) fireEvent.click(endTime);

    expect(onRangeChange).toHaveBeenCalledWith({
      start: { hours: 9, minutes: 0 },
      end: { hours: 17, minutes: 0 },
    });
  });

  it("displays time range in input", () => {
    const range = {
      start: { hours: 9, minutes: 0 },
      end: { hours: 17, minutes: 30 },
    };
    render(<TimePicker mode="range" value={range} />);

    const input = screen.getByTestId("timepicker-input");
    expect(input).toHaveValue("09:00 - 17:30");
  });

  it("supports disabled time slots", () => {
    const disabledTimes = [
      { hours: 12, minutes: 0 },
      { hours: 13, minutes: 0 },
    ];
    render(<TimePicker disabledTimes={disabledTimes} />);

    const input = screen.getByTestId("timepicker-input");
    fireEvent.click(input);

    const hoursColumn = screen.getByText("Hours").parentElement;
    const disabledHour = hoursColumn?.querySelector("button:nth-child(13)"); // 12th button (12)
    expect(disabledHour).toBeDisabled();
  });

  it("supports custom data attributes", () => {
    render(<TimePicker data-category="time-input" data-id="meeting-time" />);

    const container = screen.getByTestId("timepicker-container");
    expect(container).toHaveAttribute("data-category", "time-input");
    expect(container).toHaveAttribute("data-id", "meeting-time");
  });

  it("supports portal rendering", () => {
    render(<TimePicker portal />);

    const input = screen.getByTestId("timepicker-input");
    fireEvent.click(input);

    expect(screen.getByTestId("timepicker-dropdown")).toBeInTheDocument();
  });

  it("supports custom position", () => {
    render(<TimePicker position="top" />);

    const input = screen.getByTestId("timepicker-input");
    fireEvent.click(input);

    const dropdown = screen.getByTestId("timepicker-dropdown");
    expect(dropdown).toHaveClass("position-top");
  });

  it("supports animation", () => {
    render(<TimePicker animated />);

    const input = screen.getByTestId("timepicker-input");
    fireEvent.click(input);

    const dropdown = screen.getByTestId("timepicker-dropdown");
    expect(dropdown).toHaveClass("animated");
  });
});
>>>>>>> origin/main
