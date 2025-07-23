import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { vi } from "vitest";
import { DatePicker } from "./DatePicker";

describe("DatePicker", () => {
  const mockDate = new Date("2023-07-15");

  beforeEach(() => {
    vi.clearAllMocks();
    vi.setSystemTime(mockDate);
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("renders date picker with input", () => {
    render(<DatePicker />);

    expect(screen.getByTestId("datepicker-container")).toBeInTheDocument();
    expect(screen.getByTestId("datepicker-input")).toBeInTheDocument();
  });

  it("shows placeholder text", () => {
    render(<DatePicker placeholder="Select a date" />);

    const input = screen.getByTestId("datepicker-input");
    expect(input).toHaveAttribute("placeholder", "Select a date");
  });

  it("displays selected date in input", () => {
    const selectedDate = new Date("2023-07-20");
    render(<DatePicker value={selectedDate} />);

    const input = screen.getByTestId("datepicker-input");
    expect(input).toHaveValue("07/20/2023");
  });

  it("opens calendar on input click", () => {
    render(<DatePicker />);

    const input = screen.getByTestId("datepicker-input");
    fireEvent.click(input);

    expect(screen.getByTestId("datepicker-calendar")).toBeInTheDocument();
  });

  it("opens calendar on icon click", () => {
    render(<DatePicker showIcon />);

    const icon = screen.getByTestId("datepicker-icon");
    fireEvent.click(icon);

    expect(screen.getByTestId("datepicker-calendar")).toBeInTheDocument();
  });

  it("closes calendar on outside click", async () => {
    render(<DatePicker />);

    const input = screen.getByTestId("datepicker-input");
    fireEvent.click(input);

    expect(screen.getByTestId("datepicker-calendar")).toBeInTheDocument();

    fireEvent.mouseDown(document.body);

    await waitFor(() => {
      expect(
        screen.queryByTestId("datepicker-calendar"),
      ).not.toBeInTheDocument();
    });
  });

  it("selects date from calendar", () => {
    const onChange = vi.fn();
    render(<DatePicker onChange={onChange} />);

    const input = screen.getByTestId("datepicker-input");
    fireEvent.click(input);

    const dayButton = screen.getByText("20");
    fireEvent.click(dayButton);

    expect(onChange).toHaveBeenCalledTimes(1);
    const calledDate = onChange.mock.calls[0][0];
    expect(calledDate.getDate()).toBe(20);
  });

  it("supports different date formats", () => {
    const selectedDate = new Date("2023-07-20");
    render(<DatePicker value={selectedDate} format="MM-dd-yyyy" />);

    const input = screen.getByTestId("datepicker-input");
    expect(input).toHaveValue("07-20-2023");
  });

  it("supports custom date format", () => {
    const selectedDate = new Date("2023-07-20");
    render(<DatePicker value={selectedDate} format="dd/MM/yyyy" />);

    const input = screen.getByTestId("datepicker-input");
    expect(input).toHaveValue("20/07/2023");
  });

  it("validates input on manual entry", () => {
    const onChange = vi.fn();
    render(<DatePicker onChange={onChange} />);

    const input = screen.getByTestId("datepicker-input");
    fireEvent.change(input, { target: { value: "07/25/2023" } });
    fireEvent.blur(input);

    expect(onChange).toHaveBeenCalledTimes(1);
  });

  it("handles invalid date input", () => {
    const onError = vi.fn();
    render(<DatePicker onError={onError} />);

    const input = screen.getByTestId("datepicker-input");
    fireEvent.change(input, { target: { value: "invalid date" } });
    fireEvent.blur(input);

    expect(onError).toHaveBeenCalledWith("Invalid date format");
  });

  it("supports minimum date restriction", () => {
    const minDate = new Date("2023-07-10");
    render(<DatePicker minDate={minDate} />);

    const input = screen.getByTestId("datepicker-input");
    fireEvent.click(input);

    expect(screen.getByTestId("datepicker-calendar")).toBeInTheDocument();
  });

  it("supports maximum date restriction", () => {
    const maxDate = new Date("2023-07-25");
    render(<DatePicker maxDate={maxDate} />);

    const input = screen.getByTestId("datepicker-input");
    fireEvent.click(input);

    expect(screen.getByTestId("datepicker-calendar")).toBeInTheDocument();
  });

  it("disables specific dates", () => {
    const disabledDates = [new Date("2023-07-15"), new Date("2023-07-20")];
    render(<DatePicker disabledDates={disabledDates} />);

    const input = screen.getByTestId("datepicker-input");
    fireEvent.click(input);

    expect(screen.getByTestId("datepicker-calendar")).toBeInTheDocument();
  });

  it("supports range selection mode", () => {
    const onRangeChange = vi.fn();
    render(<DatePicker mode="range" onRangeChange={onRangeChange} />);

    const input = screen.getByTestId("datepicker-input");
    fireEvent.click(input);

    const startDate = screen.getByText("10");
    const endDate = screen.getByText("15");

    fireEvent.click(startDate);
    fireEvent.click(endDate);

    expect(onRangeChange).toHaveBeenCalledTimes(1);
  });

  it("displays range in input field", () => {
    const range = {
      start: new Date("2023-07-10"),
      end: new Date("2023-07-15"),
    };
    render(<DatePicker mode="range" value={range} />);

    const input = screen.getByTestId("datepicker-input");
    expect(input).toHaveValue("07/10/2023 - 07/15/2023");
  });

  it("supports time selection", () => {
    render(<DatePicker showTime />);

    const input = screen.getByTestId("datepicker-input");
    fireEvent.click(input);

    expect(screen.getByTestId("datepicker-time-picker")).toBeInTheDocument();
  });

  it("displays time in input when selected", () => {
    const dateTime = new Date("2023-07-20T14:30:00");
    render(<DatePicker showTime value={dateTime} />);

    const input = screen.getByTestId("datepicker-input");
    expect(input).toHaveValue("07/20/2023 14:30");
  });

  it("supports different sizes", () => {
    const sizes = ["sm", "md", "lg"] as const;

    sizes.forEach((size) => {
      const { unmount } = render(<DatePicker size={size} />);
      const container = screen.getByTestId("datepicker-container");
      expect(container).toHaveClass(`size-${size}`);
      unmount();
    });
  });

  it("supports different themes", () => {
    const themes = ["light", "dark"] as const;

    themes.forEach((theme) => {
      const { unmount } = render(<DatePicker theme={theme} />);
      const container = screen.getByTestId("datepicker-container");
      expect(container).toHaveClass(`theme-${theme}`);
      unmount();
    });
  });

  it("supports disabled state", () => {
    render(<DatePicker disabled />);

    const input = screen.getByTestId("datepicker-input");
    expect(input).toBeDisabled();
  });

  it("supports readonly state", () => {
    render(<DatePicker readonly />);

    const input = screen.getByTestId("datepicker-input");
    expect(input).toHaveAttribute("readonly");
  });

  it("shows clear button when clearable", () => {
    const selectedDate = new Date("2023-07-20");
    render(<DatePicker value={selectedDate} clearable />);

    expect(screen.getByTestId("datepicker-clear")).toBeInTheDocument();
  });

  it("clears date when clear button clicked", () => {
    const onChange = vi.fn();
    const selectedDate = new Date("2023-07-20");
    render(<DatePicker value={selectedDate} clearable onChange={onChange} />);

    const clearButton = screen.getByTestId("datepicker-clear");
    fireEvent.click(clearButton);

    expect(onChange).toHaveBeenCalledWith(null);
  });

  it("supports keyboard navigation", () => {
    render(<DatePicker />);

    const input = screen.getByTestId("datepicker-input");
    fireEvent.keyDown(input, { key: "ArrowDown" });

    expect(screen.getByTestId("datepicker-calendar")).toBeInTheDocument();
  });

  it("closes calendar on Escape key", () => {
    render(<DatePicker />);

    const input = screen.getByTestId("datepicker-input");
    fireEvent.click(input);

    expect(screen.getByTestId("datepicker-calendar")).toBeInTheDocument();

    fireEvent.keyDown(input, { key: "Escape" });

    expect(screen.queryByTestId("datepicker-calendar")).not.toBeInTheDocument();
  });

  it("supports custom input component", () => {
    const CustomInput = React.forwardRef<HTMLInputElement, any>(
      (props, ref) => <input ref={ref} {...props} data-testid="custom-input" />,
    );

    render(<DatePicker customInput={<CustomInput />} />);

    expect(screen.getByTestId("custom-input")).toBeInTheDocument();
  });

  it("supports custom calendar component", () => {
    const CustomCalendar = () => (
      <div data-testid="custom-calendar">Custom Calendar</div>
    );

    render(<DatePicker customCalendar={<CustomCalendar />} />);

    const input = screen.getByTestId("datepicker-input");
    fireEvent.click(input);

    expect(screen.getByTestId("custom-calendar")).toBeInTheDocument();
  });

  it("handles focus and blur events", () => {
    const onFocus = vi.fn();
    const onBlur = vi.fn();
    render(<DatePicker onFocus={onFocus} onBlur={onBlur} />);

    const input = screen.getByTestId("datepicker-input");

    fireEvent.focus(input);
    expect(onFocus).toHaveBeenCalledTimes(1);

    fireEvent.blur(input);
    expect(onBlur).toHaveBeenCalledTimes(1);
  });

  it("supports loading state", () => {
    render(<DatePicker loading />);

    expect(screen.getByTestId("datepicker-loading")).toBeInTheDocument();
  });

  it("supports custom loading component", () => {
    const LoadingComponent = () => (
      <div data-testid="custom-loading">Loading...</div>
    );
    render(<DatePicker loading loadingComponent={<LoadingComponent />} />);

    expect(screen.getByTestId("custom-loading")).toBeInTheDocument();
  });

  it("supports error state", () => {
    render(<DatePicker error="Invalid date" />);

    const input = screen.getByTestId("datepicker-input");
    expect(input).toHaveClass("error");
    expect(screen.getByText("Invalid date")).toBeInTheDocument();
  });

  it("supports success state", () => {
    render(<DatePicker success />);

    const input = screen.getByTestId("datepicker-input");
    expect(input).toHaveClass("success");
  });

  it("supports warning state", () => {
    render(<DatePicker warning />);

    const input = screen.getByTestId("datepicker-input");
    expect(input).toHaveClass("warning");
  });

  it("supports helper text", () => {
    render(<DatePicker helperText="Select your birth date" />);

    expect(screen.getByText("Select your birth date")).toBeInTheDocument();
  });

  it("supports label", () => {
    render(<DatePicker label="Birth Date" />);

    expect(screen.getByText("Birth Date")).toBeInTheDocument();
  });

  it("marks required field", () => {
    render(<DatePicker label="Birth Date" required />);

    expect(screen.getByText("*")).toBeInTheDocument();
  });

  it("supports custom positioning", () => {
    render(<DatePicker position="top" />);

    const input = screen.getByTestId("datepicker-input");
    fireEvent.click(input);

    const calendar = screen.getByTestId("datepicker-calendar");
    expect(calendar).toHaveClass("position-top");
  });

  it("auto-adjusts position when space is limited", () => {
    render(<DatePicker autoAdjustPosition />);

    const input = screen.getByTestId("datepicker-input");
    fireEvent.click(input);

    expect(screen.getByTestId("datepicker-calendar")).toBeInTheDocument();
  });

  it("supports multiple date selection", () => {
    const onMultipleChange = vi.fn();
    render(<DatePicker mode="multiple" onMultipleChange={onMultipleChange} />);

    const input = screen.getByTestId("datepicker-input");
    fireEvent.click(input);

    const date1 = screen.getByText("10");
    const date2 = screen.getByText("15");

    fireEvent.click(date1);
    fireEvent.click(date2);

    expect(onMultipleChange).toHaveBeenCalledTimes(2);
  });

  it("displays multiple dates in input", () => {
    const dates = [
      new Date("2023-07-10"),
      new Date("2023-07-15"),
      new Date("2023-07-20"),
    ];
    render(<DatePicker mode="multiple" value={dates} />);

    const input = screen.getByTestId("datepicker-input");
    expect(input).toHaveValue("07/10/2023, 07/15/2023, 07/20/2023");
  });

  it("supports inline mode", () => {
    render(<DatePicker inline />);

    expect(screen.getByTestId("datepicker-calendar")).toBeInTheDocument();
    expect(screen.queryByTestId("datepicker-input")).not.toBeInTheDocument();
  });

  it("supports close on select", () => {
    render(<DatePicker closeOnSelect />);

    const input = screen.getByTestId("datepicker-input");
    fireEvent.click(input);

    const dayButton = screen.getByText("20");
    fireEvent.click(dayButton);

    expect(screen.queryByTestId("datepicker-calendar")).not.toBeInTheDocument();
  });

  it("keeps calendar open when closeOnSelect is false", () => {
    render(<DatePicker closeOnSelect={false} />);

    const input = screen.getByTestId("datepicker-input");
    fireEvent.click(input);

    const dayButton = screen.getByText("20");
    fireEvent.click(dayButton);

    expect(screen.getByTestId("datepicker-calendar")).toBeInTheDocument();
  });

  it("supports custom date validation", () => {
    const isDateValid = (date: Date) => date.getDay() !== 0; // No Sundays
    render(<DatePicker isDateValid={isDateValid} />);

    const input = screen.getByTestId("datepicker-input");
    fireEvent.click(input);

    expect(screen.getByTestId("datepicker-calendar")).toBeInTheDocument();
  });

  it("supports custom className", () => {
    render(<DatePicker className="custom-datepicker" />);

    const container = screen.getByTestId("datepicker-container");
    expect(container).toHaveClass("custom-datepicker");
  });

  it("supports custom input props", () => {
    render(<DatePicker inputProps={{ "data-custom": "value" }} />);

    const input = screen.getByTestId("datepicker-input");
    expect(input).toHaveAttribute("data-custom", "value");
  });

  it("supports custom calendar props", () => {
    render(<DatePicker calendarProps={{ "data-custom": "calendar" }} />);

    const input = screen.getByTestId("datepicker-input");
    fireEvent.click(input);

    const calendar = screen.getByTestId("datepicker-calendar");
    expect(calendar).toHaveAttribute("data-custom", "calendar");
  });

  it("handles portal rendering", () => {
    render(<DatePicker portal />);

    const input = screen.getByTestId("datepicker-input");
    fireEvent.click(input);

    expect(screen.getByTestId("datepicker-calendar")).toBeInTheDocument();
  });

  it("supports custom data attributes", () => {
    render(<DatePicker data-category="form-input" data-id="birth-date" />);

    const container = screen.getByTestId("datepicker-container");
    expect(container).toHaveAttribute("data-category", "form-input");
    expect(container).toHaveAttribute("data-id", "birth-date");
  });

  it("supports animation", () => {
    render(<DatePicker animated />);

    const input = screen.getByTestId("datepicker-input");
    fireEvent.click(input);

    const calendar = screen.getByTestId("datepicker-calendar");
    expect(calendar).toHaveClass("animated");
  });

  it("supports custom overlay z-index", () => {
    render(<DatePicker zIndex={9999} />);

    const input = screen.getByTestId("datepicker-input");
    fireEvent.click(input);

    const calendar = screen.getByTestId("datepicker-calendar");
    expect(calendar).toHaveStyle({ zIndex: "9999" });
  });
});
