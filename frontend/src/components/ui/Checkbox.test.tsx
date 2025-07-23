import { render, screen, fireEvent } from "@testing-library/react";
import { vi } from "vitest";
import { Checkbox } from "./Checkbox";

describe("Checkbox", () => {
  it("renders with label", () => {
    render(<Checkbox label="Accept terms" />);

    expect(screen.getByText("Accept terms")).toBeInTheDocument();
    expect(screen.getByRole("checkbox")).toBeInTheDocument();
  });

  it("renders without label", () => {
    render(<Checkbox />);

    expect(screen.getByRole("checkbox")).toBeInTheDocument();
  });

  it("handles checked state changes", () => {
    const onChange = vi.fn();
    render(<Checkbox label="Test" onChange={onChange} />);

    const checkbox = screen.getByRole("checkbox");
    fireEvent.click(checkbox);

    expect(onChange).toHaveBeenCalledWith(true);
  });

  it("renders as controlled component", () => {
    const onChange = vi.fn();
    const { rerender } = render(
      <Checkbox label="Test" checked={false} onChange={onChange} />,
    );

    let checkbox = screen.getByRole("checkbox");
    expect(checkbox).not.toBeChecked();

    rerender(<Checkbox label="Test" checked={true} onChange={onChange} />);
    checkbox = screen.getByRole("checkbox");
    expect(checkbox).toBeChecked();
  });

  it("renders in different sizes", () => {
    const { rerender } = render(<Checkbox label="Small" size="sm" />);
    let checkbox = screen.getByRole("checkbox");
    expect(checkbox).toHaveClass("w-4", "h-4");

    rerender(<Checkbox label="Medium" size="md" />);
    checkbox = screen.getByRole("checkbox");
    expect(checkbox).toHaveClass("w-5", "h-5");

    rerender(<Checkbox label="Large" size="lg" />);
    checkbox = screen.getByRole("checkbox");
    expect(checkbox).toHaveClass("w-6", "h-6");
  });

  it("applies different variants", () => {
    const { rerender } = render(<Checkbox label="Primary" variant="primary" />);
    let checkbox = screen.getByRole("checkbox");
    expect(checkbox).toHaveClass("text-blue-600", "focus:ring-blue-500");

    rerender(<Checkbox label="Secondary" variant="secondary" />);
    checkbox = screen.getByRole("checkbox");
    expect(checkbox).toHaveClass("text-gray-600", "focus:ring-gray-500");

    rerender(<Checkbox label="Success" variant="success" />);
    checkbox = screen.getByRole("checkbox");
    expect(checkbox).toHaveClass("text-green-600", "focus:ring-green-500");
  });

  it("renders as disabled", () => {
    render(<Checkbox label="Disabled" disabled />);

    const checkbox = screen.getByRole("checkbox");
    expect(checkbox).toBeDisabled();
    expect(checkbox).toHaveClass("opacity-50", "cursor-not-allowed");
  });

  it("renders as readonly", () => {
    render(<Checkbox label="Readonly" readonly />);

    const checkbox = screen.getByRole("checkbox");
    expect(checkbox).toHaveAttribute("readonly");
  });

  it("renders as required", () => {
    render(<Checkbox label="Required" required />);

    const checkbox = screen.getByRole("checkbox");
    expect(checkbox).toBeRequired();
  });

  it("handles indeterminate state", () => {
    render(<Checkbox label="Indeterminate" indeterminate />);

    const checkbox = screen.getByRole("checkbox") as HTMLInputElement;
    expect(checkbox.indeterminate).toBe(true);
  });

  it("renders with custom className", () => {
    render(<Checkbox label="Custom" className="custom-checkbox" />);

    const container = screen.getByText("Custom").closest(".custom-checkbox");
    expect(container).toHaveClass("custom-checkbox");
  });

  it("renders with description", () => {
    render(<Checkbox label="Test" description="Additional info" />);

    expect(screen.getByText("Additional info")).toBeInTheDocument();
  });

  it("renders with error state", () => {
    render(<Checkbox label="Test" error="Required field" />);

    expect(screen.getByText("Required field")).toBeInTheDocument();
    const checkbox = screen.getByRole("checkbox");
    expect(checkbox).toHaveClass("border-red-500", "text-red-600");
  });

  it("renders with success state", () => {
    render(<Checkbox label="Test" success="Valid input" />);

    expect(screen.getByText("Valid input")).toBeInTheDocument();
    const checkbox = screen.getByRole("checkbox");
    expect(checkbox).toHaveClass("border-green-500", "text-green-600");
  });

  it("renders with warning state", () => {
    render(<Checkbox label="Test" warning="Check this field" />);

    expect(screen.getByText("Check this field")).toBeInTheDocument();
    const checkbox = screen.getByRole("checkbox");
    expect(checkbox).toHaveClass("border-yellow-500", "text-yellow-600");
  });

  it("renders with icon", () => {
    const icon = <span data-testid="test-icon">📧</span>;
    render(<Checkbox label="Test" icon={icon} />);

    expect(screen.getByTestId("test-icon")).toBeInTheDocument();
  });

  it("handles keyboard navigation", () => {
    const onChange = vi.fn();
    render(<Checkbox label="Test" onChange={onChange} />);

    const checkbox = screen.getByRole("checkbox");
    fireEvent.keyDown(checkbox, { key: " " });

    expect(onChange).toHaveBeenCalled();
  });

  it("renders as loading state", () => {
    render(<Checkbox label="Loading" loading />);

    const spinner = screen.getByRole("img", { hidden: true });
    expect(spinner).toBeInTheDocument();
    expect(spinner).toHaveClass("animate-spin");
  });

  it("applies different colors", () => {
    const { rerender } = render(<Checkbox label="Red" color="red" />);
    let checkbox = screen.getByRole("checkbox");
    expect(checkbox).toHaveClass("text-red-600", "focus:ring-red-500");

    rerender(<Checkbox label="Blue" color="blue" />);
    checkbox = screen.getByRole("checkbox");
    expect(checkbox).toHaveClass("text-blue-600", "focus:ring-blue-500");
  });

  it("renders with custom background", () => {
    const { container } = render(
      <Checkbox label="Custom BG" background="bg-gray-100" />,
    );

    const bgContainer = container.querySelector(".bg-gray-100");
    expect(bgContainer).toBeInTheDocument();
  });

  it("renders with rounded corners", () => {
    render(<Checkbox label="Rounded" rounded />);

    const checkbox = screen.getByRole("checkbox");
    expect(checkbox).toHaveClass("rounded-lg");
  });

  it("handles focus and blur events", () => {
    const onFocus = vi.fn();
    const onBlur = vi.fn();
    render(<Checkbox label="Test" onFocus={onFocus} onBlur={onBlur} />);

    const checkbox = screen.getByRole("checkbox");
    fireEvent.focus(checkbox);
    expect(onFocus).toHaveBeenCalled();

    fireEvent.blur(checkbox);
    expect(onBlur).toHaveBeenCalled();
  });

  it("renders group of checkboxes", () => {
    render(
      <Checkbox.Group label="Choose options">
        <Checkbox label="Option 1" value="1" />
        <Checkbox label="Option 2" value="2" />
        <Checkbox label="Option 3" value="3" />
      </Checkbox.Group>,
    );

    expect(screen.getByText("Choose options")).toBeInTheDocument();
    expect(screen.getByText("Option 1")).toBeInTheDocument();
    expect(screen.getByText("Option 2")).toBeInTheDocument();
    expect(screen.getByText("Option 3")).toBeInTheDocument();
  });

  it("handles group value changes", () => {
    const onChange = vi.fn();
    render(
      <Checkbox.Group label="Choose options" value={["1"]} onChange={onChange}>
        <Checkbox label="Option 1" value="1" />
        <Checkbox label="Option 2" value="2" />
      </Checkbox.Group>,
    );

    const option2 = screen.getByLabelText("Option 2");
    fireEvent.click(option2);

    expect(onChange).toHaveBeenCalledWith(["1", "2"]);
  });

  it("handles group validation", () => {
    render(
      <Checkbox.Group
        label="Choose options"
        error="Please select at least one option"
      >
        <Checkbox label="Option 1" value="1" />
        <Checkbox label="Option 2" value="2" />
      </Checkbox.Group>,
    );

    expect(
      screen.getByText("Please select at least one option"),
    ).toBeInTheDocument();
  });

  it("renders with accessibility attributes", () => {
    render(
      <Checkbox
        label="Test"
        aria-describedby="help-text"
        aria-required="true"
        role="checkbox"
      />,
    );

    const checkbox = screen.getByRole("checkbox");
    expect(checkbox).toHaveAttribute("aria-describedby", "help-text");
    expect(checkbox).toHaveAttribute("aria-required", "true");
  });

  it("renders with tooltip", () => {
    render(<Checkbox label="Test" tooltip="This is a tooltip" />);

    const checkbox = screen.getByRole("checkbox");
    expect(checkbox).toHaveAttribute("title", "This is a tooltip");
  });

  it("handles animation on state change", () => {
    const { rerender } = render(
      <Checkbox label="Test" checked={false} animate />,
    );

    rerender(<Checkbox label="Test" checked={true} animate />);

    const checkbox = screen.getByRole("checkbox");
    expect(checkbox).toHaveClass("transition-all");
  });

  it("renders with label position variations", () => {
    const { rerender, container } = render(
      <Checkbox label="Test" labelPosition="right" />,
    );
    let flexContainer = container.querySelector(".flex-row");
    expect(flexContainer).toBeInTheDocument();

    rerender(<Checkbox label="Test" labelPosition="left" />);
    flexContainer = container.querySelector(".flex-row-reverse");
    expect(flexContainer).toBeInTheDocument();
  });

  it("renders with custom check icon", () => {
    const customCheck = <span data-testid="custom-check">✓</span>;
    render(<Checkbox label="Test" checked checkIcon={customCheck} />);

    expect(screen.getByTestId("custom-check")).toBeInTheDocument();
  });

  it("handles group select all functionality", () => {
    const onChange = vi.fn();
    render(
      <Checkbox.Group
        label="Choose options"
        selectAll
        selectAllLabel="Select All"
        onChange={onChange}
      >
        <Checkbox label="Option 1" value="1" />
        <Checkbox label="Option 2" value="2" />
      </Checkbox.Group>,
    );

    expect(screen.getByText("Select All")).toBeInTheDocument();

    const selectAll = screen.getByLabelText("Select All");
    fireEvent.click(selectAll);

    expect(onChange).toHaveBeenCalledWith(["1", "2"]);
  });
});
