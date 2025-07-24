import { render, screen, fireEvent } from "@testing-library/react";
import { vi } from "vitest";
import { Radio } from "./Radio";

describe("Radio", () => {
  it("renders with label", () => {
    render(<Radio label="Option 1" value="1" />);

    expect(screen.getByText("Option 1")).toBeInTheDocument();
    expect(screen.getByRole("radio")).toBeInTheDocument();
  });

  it("renders without label", () => {
    render(<Radio value="test" />);

    expect(screen.getByRole("radio")).toBeInTheDocument();
  });

  it("handles selection changes", () => {
    const onChange = vi.fn();
    render(<Radio label="Test" value="test" onChange={onChange} />);

    const radio = screen.getByRole("radio");
    fireEvent.click(radio);

    expect(onChange).toHaveBeenCalledWith("test");
  });

  it("renders as controlled component", () => {
    const onChange = vi.fn();
    const { rerender } = render(
      <Radio label="Test" value="test" checked={false} onChange={onChange} />,
    );

    let radio = screen.getByRole("radio");
    expect(radio).not.toBeChecked();

    rerender(
      <Radio label="Test" value="test" checked={true} onChange={onChange} />,
    );
    radio = screen.getByRole("radio");
    expect(radio).toBeChecked();
  });

  it("renders in different sizes", () => {
    const { rerender } = render(<Radio label="Small" value="sm" size="sm" />);
    let radio = screen.getByRole("radio");
    expect(radio).toHaveClass("w-4", "h-4");

    rerender(<Radio label="Medium" value="md" size="md" />);
    radio = screen.getByRole("radio");
    expect(radio).toHaveClass("w-5", "h-5");

    rerender(<Radio label="Large" value="lg" size="lg" />);
    radio = screen.getByRole("radio");
    expect(radio).toHaveClass("w-6", "h-6");
  });

  it("applies different variants", () => {
    const { rerender } = render(
      <Radio label="Primary" value="1" variant="primary" />,
    );
    let radio = screen.getByRole("radio");
    expect(radio).toHaveClass("text-blue-600", "focus:ring-blue-500");

    rerender(<Radio label="Secondary" value="2" variant="secondary" />);
    radio = screen.getByRole("radio");
    expect(radio).toHaveClass("text-gray-600", "focus:ring-gray-500");

    rerender(<Radio label="Success" value="3" variant="success" />);
    radio = screen.getByRole("radio");
    expect(radio).toHaveClass("text-green-600", "focus:ring-green-500");
  });

  it("renders as disabled", () => {
    render(<Radio label="Disabled" value="disabled" disabled />);

    const radio = screen.getByRole("radio");
    expect(radio).toBeDisabled();
    expect(radio).toHaveClass("opacity-50", "cursor-not-allowed");
  });

  it("renders as readonly", () => {
    render(<Radio label="Readonly" value="readonly" readonly />);

    const radio = screen.getByRole("radio");
    expect(radio).toHaveAttribute("readonly");
  });

  it("renders as required", () => {
    render(<Radio label="Required" value="required" required />);

    const radio = screen.getByRole("radio");
    expect(radio).toBeRequired();
  });

  it("renders with custom className", () => {
    render(<Radio label="Custom" value="custom" className="custom-radio" />);

    const container = screen.getByText("Custom").closest(".custom-radio");
    expect(container).toHaveClass("custom-radio");
  });

  it("renders with description", () => {
    render(<Radio label="Test" value="test" description="Additional info" />);

    expect(screen.getByText("Additional info")).toBeInTheDocument();
  });

  it("renders with error state", () => {
    render(<Radio label="Test" value="test" error="Required field" />);

    expect(screen.getByText("Required field")).toBeInTheDocument();
    const radio = screen.getByRole("radio");
    expect(radio).toHaveClass("border-red-500", "text-red-600");
  });

  it("renders with success state", () => {
    render(<Radio label="Test" value="test" success="Valid input" />);

    expect(screen.getByText("Valid input")).toBeInTheDocument();
    const radio = screen.getByRole("radio");
    expect(radio).toHaveClass("border-green-500", "text-green-600");
  });

  it("renders with warning state", () => {
    render(<Radio label="Test" value="test" warning="Check this field" />);

    expect(screen.getByText("Check this field")).toBeInTheDocument();
    const radio = screen.getByRole("radio");
    expect(radio).toHaveClass("border-yellow-500", "text-yellow-600");
  });

  it("renders with icon", () => {
    const icon = <span data-testid="test-icon">📧</span>;
    render(<Radio label="Test" value="test" icon={icon} />);

    expect(screen.getByTestId("test-icon")).toBeInTheDocument();
  });

  it("handles keyboard navigation", () => {
    const onChange = vi.fn();
    render(<Radio label="Test" value="test" onChange={onChange} />);

    const radio = screen.getByRole("radio");
    fireEvent.keyDown(radio, { key: " " });

    expect(onChange).toHaveBeenCalled();
  });

  it("renders as loading state", () => {
    render(<Radio label="Loading" value="loading" loading />);

    const spinner = screen.getByRole("img", { hidden: true });
    expect(spinner).toBeInTheDocument();
    expect(spinner).toHaveClass("animate-spin");
  });

  it("applies different colors", () => {
    const { rerender } = render(<Radio label="Red" value="red" color="red" />);
    let radio = screen.getByRole("radio");
    expect(radio).toHaveClass("text-red-600", "focus:ring-red-500");

    rerender(<Radio label="Blue" value="blue" color="blue" />);
    radio = screen.getByRole("radio");
    expect(radio).toHaveClass("text-blue-600", "focus:ring-blue-500");
  });

  it("renders with custom background", () => {
    const { container } = render(
      <Radio label="Custom BG" value="custom" background="bg-gray-100" />,
    );

    const bgContainer = container.querySelector(".bg-gray-100");
    expect(bgContainer).toBeInTheDocument();
  });

  it("renders with rounded corners", () => {
    render(<Radio label="Rounded" value="rounded" rounded />);

    const radio = screen.getByRole("radio");
    expect(radio).toHaveClass("rounded-lg");
  });

  it("handles focus and blur events", () => {
    const onFocus = vi.fn();
    const onBlur = vi.fn();
    render(
      <Radio label="Test" value="test" onFocus={onFocus} onBlur={onBlur} />,
    );

    const radio = screen.getByRole("radio");
    fireEvent.focus(radio);
    expect(onFocus).toHaveBeenCalled();

    fireEvent.blur(radio);
    expect(onBlur).toHaveBeenCalled();
  });

  it("renders group of radio buttons", () => {
    render(
      <Radio.Group label="Choose option" name="options">
        <Radio label="Option 1" value="1" />
        <Radio label="Option 2" value="2" />
        <Radio label="Option 3" value="3" />
      </Radio.Group>,
    );

    expect(screen.getByText("Choose option")).toBeInTheDocument();
    expect(screen.getByText("Option 1")).toBeInTheDocument();
    expect(screen.getByText("Option 2")).toBeInTheDocument();
    expect(screen.getByText("Option 3")).toBeInTheDocument();
  });

  it("handles group value changes", () => {
    const onChange = vi.fn();
    render(
      <Radio.Group
        label="Choose option"
        value="1"
        onChange={onChange}
        name="test"
      >
        <Radio label="Option 1" value="1" />
        <Radio label="Option 2" value="2" />
      </Radio.Group>,
    );

    const option2 = screen.getByLabelText("Option 2");
    fireEvent.click(option2);

    expect(onChange).toHaveBeenCalledWith("2");
  });

  it("handles group validation", () => {
    render(
      <Radio.Group
        label="Choose option"
        error="Please select an option"
        name="test"
      >
        <Radio label="Option 1" value="1" />
        <Radio label="Option 2" value="2" />
      </Radio.Group>,
    );

    expect(screen.getByText("Please select an option")).toBeInTheDocument();
  });

  it("renders with accessibility attributes", () => {
    render(
      <Radio
        label="Test"
        value="test"
        aria-describedby="help-text"
        aria-required="true"
        role="radio"
      />,
    );

    const radio = screen.getByRole("radio");
    expect(radio).toHaveAttribute("aria-describedby", "help-text");
    expect(radio).toHaveAttribute("aria-required", "true");
  });

  it("renders with tooltip", () => {
    render(<Radio label="Test" value="test" tooltip="This is a tooltip" />);

    const radio = screen.getByRole("radio");
    expect(radio).toHaveAttribute("title", "This is a tooltip");
  });

  it("handles animation on state change", () => {
    const { rerender } = render(
      <Radio label="Test" value="test" checked={false} animate />,
    );

    rerender(<Radio label="Test" value="test" checked={true} animate />);

    const radio = screen.getByRole("radio");
    expect(radio).toHaveClass("transition-all");
  });

  it("renders with label position variations", () => {
    const { rerender, container } = render(
      <Radio label="Test" value="test" labelPosition="right" />,
    );
    let flexContainer = container.querySelector(".flex-row");
    expect(flexContainer).toBeInTheDocument();

    rerender(<Radio label="Test" value="test" labelPosition="left" />);
    flexContainer = container.querySelector(".flex-row-reverse");
    expect(flexContainer).toBeInTheDocument();
  });

  it("ensures only one radio is selected in group", () => {
    const onChange = vi.fn();
    render(
      <Radio.Group label="Choose option" onChange={onChange} name="exclusive">
        <Radio label="Option 1" value="1" />
        <Radio label="Option 2" value="2" />
        <Radio label="Option 3" value="3" />
      </Radio.Group>,
    );

    const option1 = screen.getByLabelText("Option 1");
    const option2 = screen.getByLabelText("Option 2");

    fireEvent.click(option1);
    expect(onChange).toHaveBeenCalledWith("1");

    fireEvent.click(option2);
    expect(onChange).toHaveBeenCalledWith("2");
  });

  it("renders with card-style layout", () => {
    const { container } = render(
      <Radio label="Card Style" value="card" card />,
    );

    const cardContainer = container.querySelector(".border.rounded-lg.p-4");
    expect(cardContainer).toBeInTheDocument();
  });

  it("renders inline layout in group", () => {
    const { container } = render(
      <Radio.Group label="Inline options" inline name="inline">
        <Radio label="Option 1" value="1" />
        <Radio label="Option 2" value="2" />
      </Radio.Group>,
    );

    const groupContainer = container.querySelector(".flex-row");
    expect(groupContainer).toBeInTheDocument();
  });
});
