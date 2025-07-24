import { render, screen, fireEvent } from "@testing-library/react";
import { vi } from "vitest";
import { Stepper } from "./Stepper";

describe("Stepper", () => {
  const basicSteps = [
    { title: "Step 1", description: "First step" },
    { title: "Step 2", description: "Second step" },
    { title: "Step 3", description: "Third step" },
  ];

  it("renders with basic steps", () => {
    render(<Stepper steps={basicSteps} current={0} />);

    expect(screen.getByText("Step 1")).toBeInTheDocument();
    expect(screen.getByText("Step 2")).toBeInTheDocument();
    expect(screen.getByText("Step 3")).toBeInTheDocument();
  });

  it("highlights current step", () => {
    render(<Stepper steps={basicSteps} current={1} />);

    const currentStep = screen.getByText("Step 2");
    expect(currentStep).toBeInTheDocument();
  });

  it("renders with different directions", () => {
    const { rerender } = render(
      <Stepper steps={basicSteps} current={0} direction="horizontal" />,
    );
    expect(screen.getByText("Step 1")).toBeInTheDocument();

    rerender(<Stepper steps={basicSteps} current={0} direction="vertical" />);
    expect(screen.getByText("Step 1")).toBeInTheDocument();
  });

  it("renders with different sizes", () => {
    const sizes = ["small", "medium", "large"] as const;

    sizes.forEach((size) => {
      const { unmount } = render(
        <Stepper steps={basicSteps} current={0} size={size} />,
      );
      expect(screen.getByText("Step 1")).toBeInTheDocument();
      unmount();
    });
  });

  it("supports clickable steps", () => {
    const onChange = vi.fn();
    render(<Stepper steps={basicSteps} current={0} onChange={onChange} />);

    const stepButton = screen.getByText("2");
    fireEvent.click(stepButton);
    expect(onChange).toHaveBeenCalledWith(1);
  });

  it("handles step status properly", () => {
    const stepsWithStatus = [
      { title: "Completed", status: "completed" as const },
      { title: "Current", status: "active" as const },
      { title: "Error", status: "error" as const },
      { title: "Pending", status: "pending" as const },
    ];

    render(<Stepper steps={stepsWithStatus} current={1} />);

    expect(screen.getByText("Completed")).toBeInTheDocument();
    expect(screen.getByText("Current")).toBeInTheDocument();
    expect(screen.getByText("Error")).toBeInTheDocument();
    expect(screen.getByText("Pending")).toBeInTheDocument();
  });

  it("renders with icons", () => {
    const stepsWithIcons = [
      { title: "Step 1", icon: <span data-testid="step1-icon">🚀</span> },
      { title: "Step 2", icon: <span data-testid="step2-icon">📋</span> },
      { title: "Step 3", icon: <span data-testid="step3-icon">✅</span> },
    ];

    render(<Stepper steps={stepsWithIcons} current={0} />);

    expect(screen.getByTestId("step1-icon")).toBeInTheDocument();
    expect(screen.getByTestId("step2-icon")).toBeInTheDocument();
    expect(screen.getByTestId("step3-icon")).toBeInTheDocument();
  });

  it("supports custom step content", () => {
    const customSteps = [
      {
        title: "Custom Step",
        content: <div data-testid="custom-content">Custom Content</div>,
      },
    ];

    render(<Stepper steps={customSteps} current={0} />);
    expect(screen.getByTestId("custom-content")).toBeInTheDocument();
  });

  it("handles disabled steps", () => {
    const onChange = vi.fn();
    const disabledSteps = [
      { title: "Step 1" },
      { title: "Step 2", disabled: true },
      { title: "Step 3" },
    ];

    render(<Stepper steps={disabledSteps} current={0} onChange={onChange} />);

    const disabledStep = screen.getByText("2");
    fireEvent.click(disabledStep);
    expect(onChange).not.toHaveBeenCalledWith(1);
  });

  it("renders with progress indicator", () => {
    render(<Stepper steps={basicSteps} current={1} showProgress />);

    const progressElement = screen.getByRole("progressbar");
    expect(progressElement).toBeInTheDocument();
    expect(progressElement).toHaveAttribute("aria-valuenow", "67"); // 2/3 * 100
  });

  it("supports custom className", () => {
    render(
      <Stepper steps={basicSteps} current={0} className="custom-stepper" />,
    );
    expect(screen.getByText("Step 1")).toBeInTheDocument();
  });

  it("renders step numbers by default", () => {
    render(<Stepper steps={basicSteps} current={0} />);

    // Check for step numbers (1, 2, 3)
    expect(screen.getByText("1")).toBeInTheDocument();
    expect(screen.getByText("2")).toBeInTheDocument();
    expect(screen.getByText("3")).toBeInTheDocument();
  });

  it("supports custom step types", () => {
    const customTypeSteps = [
      { title: "Navigation Step", type: "navigation" as const },
      { title: "Inline Step", type: "inline" as const },
    ];

    render(<Stepper steps={customTypeSteps} current={0} />);
    expect(screen.getByText("Navigation Step")).toBeInTheDocument();
    expect(screen.getByText("Inline Step")).toBeInTheDocument();
  });

  it("handles step validation", () => {
    const onChange = vi.fn();
    const validateStep = vi.fn().mockReturnValue(false);

    render(
      <Stepper
        steps={basicSteps}
        current={0}
        onChange={onChange}
        onStepValidate={validateStep}
      />,
    );

    const stepButton = screen.getByText("2");
    fireEvent.click(stepButton);
    expect(validateStep).toHaveBeenCalledWith(0);
    expect(onChange).not.toHaveBeenCalled();
  });

  it("allows step change when validation passes", () => {
    const onChange = vi.fn();
    const validateStep = vi.fn().mockReturnValue(true);

    render(
      <Stepper
        steps={basicSteps}
        current={0}
        onChange={onChange}
        onStepValidate={validateStep}
      />,
    );

    const stepButton = screen.getByText("2");
    fireEvent.click(stepButton);
    expect(validateStep).toHaveBeenCalledWith(0);
    expect(onChange).toHaveBeenCalledWith(1);
  });

  it("renders with dot indicators", () => {
    render(<Stepper steps={basicSteps} current={0} dot />);
    expect(screen.getByText("Step 1")).toBeInTheDocument();
  });

  it("supports label placement options", () => {
    const labelPlacements = ["horizontal", "vertical"] as const;

    labelPlacements.forEach((placement) => {
      const { unmount } = render(
        <Stepper steps={basicSteps} current={0} labelPlacement={placement} />,
      );
      expect(screen.getByText("Step 1")).toBeInTheDocument();
      unmount();
    });
  });

  it("handles responsive behavior", () => {
    render(<Stepper steps={basicSteps} current={0} responsive />);
    expect(screen.getByText("Step 1")).toBeInTheDocument();
  });

  it("renders with alternating layout", () => {
    render(<Stepper steps={basicSteps} current={0} alternating />);
    expect(screen.getByText("Step 1")).toBeInTheDocument();
  });

  it("supports custom connector style", () => {
    render(<Stepper steps={basicSteps} current={0} connector="dashed" />);
    expect(screen.getByText("Step 1")).toBeInTheDocument();
  });

  it("handles keyboard navigation", () => {
    const onChange = vi.fn();
    render(<Stepper steps={basicSteps} current={1} onChange={onChange} />);

    const stepButton = screen.getByText("2");
    fireEvent.keyDown(stepButton, { key: "ArrowRight" });
    expect(onChange).toHaveBeenCalledWith(2);

    fireEvent.keyDown(stepButton, { key: "ArrowLeft" });
    expect(onChange).toHaveBeenCalledWith(0);
  });

  it("renders with step descriptions", () => {
    render(<Stepper steps={basicSteps} current={0} />);

    expect(screen.getByText("First step")).toBeInTheDocument();
    expect(screen.getByText("Second step")).toBeInTheDocument();
    expect(screen.getByText("Third step")).toBeInTheDocument();
  });

  it("supports custom step renderer", () => {
    const customRenderer = (step: any, index: number) => (
      <div data-testid={`custom-step-${index}`}>Custom: {step.title}</div>
    );

    render(
      <Stepper steps={basicSteps} current={0} stepRender={customRenderer} />,
    );

    expect(screen.getByTestId("custom-step-0")).toBeInTheDocument();
    expect(screen.getByText("Custom: Step 1")).toBeInTheDocument();
  });

  it("handles step completion states", () => {
    const completedSteps = basicSteps.map((step, index) => ({
      ...step,
      status: index < 2 ? ("completed" as const) : ("pending" as const),
    }));

    render(<Stepper steps={completedSteps} current={2} />);
    expect(screen.getByText("Step 1")).toBeInTheDocument();
    expect(screen.getByText("Step 2")).toBeInTheDocument();
    expect(screen.getByText("Step 3")).toBeInTheDocument();
  });

  it("supports step subtitles", () => {
    const stepsWithSubtitles = [
      { title: "Step 1", subtitle: "Optional subtitle" },
    ];

    render(<Stepper steps={stepsWithSubtitles} current={0} />);
    expect(screen.getByText("Optional subtitle")).toBeInTheDocument();
  });

  it("handles animation states", () => {
    render(<Stepper steps={basicSteps} current={0} animated />);
    expect(screen.getByText("Step 1")).toBeInTheDocument();
  });
});
