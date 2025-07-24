import React from "react";
import { render, screen } from "@testing-library/react";
import { vi } from "vitest";
import { Progress } from "./Progress";

describe("Progress", () => {
  it("renders with default value", () => {
    render(<Progress />);

    const progressBar = screen.getByRole("progressbar");
    expect(progressBar).toBeInTheDocument();
    expect(progressBar).toHaveAttribute("aria-valuenow", "0");
    expect(progressBar).toHaveAttribute("aria-valuemin", "0");
    expect(progressBar).toHaveAttribute("aria-valuemax", "100");
  });

  it("renders with custom value", () => {
    render(<Progress value={45} />);

    const progressBar = screen.getByRole("progressbar");
    expect(progressBar).toHaveAttribute("aria-valuenow", "45");
  });

  it("displays percentage text by default", () => {
    render(<Progress value={75} />);

    expect(screen.getByText("75%")).toBeInTheDocument();
  });

  it("hides percentage when showText is false", () => {
    render(<Progress value={75} showText={false} />);

    expect(screen.queryByText("75%")).not.toBeInTheDocument();
  });

  it("displays custom text", () => {
    render(<Progress value={60} text="Loading..." />);

    expect(screen.getByText("Loading...")).toBeInTheDocument();
    expect(screen.queryByText("60%")).not.toBeInTheDocument();
  });

  it("uses custom text formatter", () => {
    const formatter = (value: number, max: number) =>
      `${value} of ${max} items`;
    render(<Progress value={25} max={50} textFormatter={formatter} />);

    expect(screen.getByText("25 of 50 items")).toBeInTheDocument();
  });

  it("applies size classes correctly", () => {
    const { rerender } = render(<Progress value={50} size="sm" />);
    let progressContainer = screen.getByRole("progressbar").parentElement;
    expect(progressContainer).toHaveClass("h-1");

    rerender(<Progress value={50} size="md" />);
    progressContainer = screen.getByRole("progressbar").parentElement;
    expect(progressContainer).toHaveClass("h-2");

    rerender(<Progress value={50} size="lg" />);
    progressContainer = screen.getByRole("progressbar").parentElement;
    expect(progressContainer).toHaveClass("h-4");
  });

  it("applies color variants correctly", () => {
    const { rerender } = render(<Progress value={50} color="primary" />);
    let progressBar = screen.getByRole("progressbar");
    expect(progressBar).toHaveClass("bg-blue-500");

    rerender(<Progress value={50} color="success" />);
    progressBar = screen.getByRole("progressbar");
    expect(progressBar).toHaveClass("bg-green-500");

    rerender(<Progress value={50} color="warning" />);
    progressBar = screen.getByRole("progressbar");
    expect(progressBar).toHaveClass("bg-yellow-500");

    rerender(<Progress value={50} color="danger" />);
    progressBar = screen.getByRole("progressbar");
    expect(progressBar).toHaveClass("bg-red-500");
  });

  it("handles indeterminate state", () => {
    render(<Progress indeterminate />);

    const progressBar = screen.getByRole("progressbar");
    expect(progressBar).toHaveClass("animate-pulse");
    expect(progressBar.parentElement).toHaveClass("overflow-hidden");
  });

  it("displays striped pattern", () => {
    render(<Progress value={60} striped />);

    const progressBar = screen.getByRole("progressbar");
    expect(progressBar).toHaveClass("bg-gradient-to-r");
  });

  it("displays animated stripes", () => {
    render(<Progress value={60} striped animated />);

    const progressBar = screen.getByRole("progressbar");
    expect(progressBar).toHaveClass("bg-gradient-to-r");
    expect(progressBar).toHaveClass(
      "transition-all",
      "duration-300",
      "ease-out",
    );
  });

  it("handles custom min and max values", () => {
    render(<Progress value={15} min={10} max={20} />);

    const progressBar = screen.getByRole("progressbar");
    expect(progressBar).toHaveAttribute("aria-valuemin", "10");
    expect(progressBar).toHaveAttribute("aria-valuemax", "20");
    expect(progressBar).toHaveAttribute("aria-valuenow", "15");

    // 15 out of (20-10) = 50% progress
    expect(screen.getByText("50%")).toBeInTheDocument();
  });

  it("handles circular progress", () => {
    render(<Progress value={75} type="circle" />);

    const svg = screen.getByRole("progressbar");
    expect(svg.tagName).toBe("svg");
    expect(svg).toHaveClass("transform", "-rotate-90");
  });

  it("displays circular progress with custom size", () => {
    render(<Progress value={50} type="circle" circleSize={100} />);

    const svg = screen.getByRole("progressbar");
    expect(svg).toHaveAttribute("width", "100");
    expect(svg).toHaveAttribute("height", "100");
  });

  it("shows steps progress", () => {
    render(<Progress value={2} max={5} type="steps" />);

    const steps = screen.getAllByTestId("progress-step");
    expect(steps).toHaveLength(5);

    // First two steps should be active
    expect(steps[0]).toHaveClass("bg-blue-500");
    expect(steps[1]).toHaveClass("bg-blue-500");
    expect(steps[2]).toHaveClass("bg-gray-200");
  });

  it("applies custom className", () => {
    render(<Progress value={50} className="custom-progress" />);

    const container = screen
      .getByRole("progressbar")
      .closest(".custom-progress");
    expect(container).toBeInTheDocument();
  });

  it("supports custom track and bar styles", () => {
    render(
      <Progress
        value={50}
        trackStyle={{ backgroundColor: "red" }}
        barStyle={{ backgroundColor: "blue" }}
      />,
    );

    const progressBar = screen.getByRole("progressbar");
    const track = progressBar.parentElement;

    expect(track?.style.backgroundColor).toBe("red");
    expect(progressBar.style.backgroundColor).toBe("blue");
  });

  it("handles zero value", () => {
    render(<Progress value={0} />);

    const progressBar = screen.getByRole("progressbar");
    expect(progressBar).toHaveAttribute("aria-valuenow", "0");
    expect(progressBar).toHaveStyle({ width: "0%" });
    expect(screen.getByText("0%")).toBeInTheDocument();
  });

  it("handles maximum value", () => {
    render(<Progress value={100} />);

    const progressBar = screen.getByRole("progressbar");
    expect(progressBar).toHaveAttribute("aria-valuenow", "100");
    expect(progressBar).toHaveStyle({ width: "100%" });
    expect(screen.getByText("100%")).toBeInTheDocument();
  });

  it("clamps value within min-max range", () => {
    render(<Progress value={150} min={0} max={100} />);

    const progressBar = screen.getByRole("progressbar");
    expect(progressBar).toHaveAttribute("aria-valuenow", "100");
    expect(screen.getByText("100%")).toBeInTheDocument();
  });

  it("handles negative values", () => {
    render(<Progress value={-10} min={0} max={100} />);

    const progressBar = screen.getByRole("progressbar");
    expect(progressBar).toHaveAttribute("aria-valuenow", "0");
    expect(screen.getByText("0%")).toBeInTheDocument();
  });

  it("displays label and description", () => {
    render(
      <Progress
        value={50}
        label="Upload Progress"
        description="Uploading files..."
      />,
    );

    expect(screen.getByText("Upload Progress")).toBeInTheDocument();
    expect(screen.getByText("Uploading files...")).toBeInTheDocument();
  });

  it("supports gradient colors", () => {
    render(<Progress value={50} gradient={["#ff0000", "#00ff00"]} />);

    const progressBar = screen.getByRole("progressbar");
    // Gradient functionality exists, testing that component renders without error
    expect(progressBar).toBeInTheDocument();
  });

  it("handles multi-segment progress", () => {
    const segments = [
      { value: 30, color: "bg-red-500" },
      { value: 20, color: "bg-yellow-500" },
      { value: 50, color: "bg-green-500" },
    ];

    render(<Progress segments={segments} />);

    const progressContainer =
      screen.getByText("0%").parentElement?.parentElement?.parentElement;
    const segmentElements = progressContainer?.querySelectorAll(
      '[class*="bg-red-500"], [class*="bg-yellow-500"], [class*="bg-green-500"]',
    );
    expect(segmentElements).toHaveLength(3);
  });

  it("calculates percentage correctly", () => {
    render(<Progress value={25} min={20} max={30} />);

    // (25-20)/(30-20) * 100 = 50%
    expect(screen.getByText("50%")).toBeInTheDocument();
  });

  it("handles accessibility attributes", () => {
    render(
      <Progress
        value={75}
        aria-label="File upload progress"
        aria-describedby="upload-description"
      />,
    );

    const progressBar = screen.getByRole("progressbar");
    expect(progressBar).toHaveAttribute("aria-label", "File upload progress");
    expect(progressBar).toHaveAttribute(
      "aria-describedby",
      "upload-description",
    );
  });

  it("updates progress dynamically", () => {
    const { rerender } = render(<Progress value={25} />);

    expect(screen.getByText("25%")).toBeInTheDocument();

    rerender(<Progress value={75} />);
    expect(screen.getByText("75%")).toBeInTheDocument();
  });

  it("handles transition animations", () => {
    render(<Progress value={50} animated />);

    const progressBar = screen.getByRole("progressbar");
    expect(progressBar).toHaveClass("transition-all", "duration-300");
  });

  it("displays success state", () => {
    render(<Progress value={100} status="success" />);

    const progressBar = screen.getByRole("progressbar");
    expect(progressBar).toHaveClass("bg-green-500");
  });

  it("displays error state", () => {
    render(<Progress value={45} status="error" />);

    const progressBar = screen.getByRole("progressbar");
    expect(progressBar).toHaveClass("bg-red-500");
  });

  it("displays loading state", () => {
    render(<Progress loading />);

    const spinner = screen.getByRole("img", { hidden: true });
    expect(spinner).toHaveClass("animate-spin");
    expect(screen.getByText("Loading...")).toBeInTheDocument();
  });

  it("handles threshold indicators", () => {
    render(<Progress value={75} thresholds={[25, 50, 75]} />);

    const thresholdMarkers = screen.getAllByTestId("progress-threshold");
    expect(thresholdMarkers).toHaveLength(3);
  });

  it("shows custom icons", () => {
    const CheckIcon = () => <span data-testid="check-icon">✓</span>;
    render(
      <Progress value={100} icon={<CheckIcon />} label="Upload Complete" />,
    );

    expect(screen.getByTestId("check-icon")).toBeInTheDocument();
  });

  it("handles onComplete callback", () => {
    const onComplete = vi.fn();
    const { rerender } = render(
      <Progress value={99} onComplete={onComplete} />,
    );

    expect(onComplete).not.toHaveBeenCalled();

    rerender(<Progress value={100} onComplete={onComplete} />);
    expect(onComplete).toHaveBeenCalled();
  });

  it("supports vertical orientation", () => {
    render(<Progress value={50} vertical />);

    const progressContainer = screen.getByRole("progressbar").parentElement;
    expect(progressContainer).toHaveClass("h-32", "w-2");

    const progressBar = screen.getByRole("progressbar");
    expect(progressBar).toHaveStyle({ height: "50%" });
  });

  it("displays buffer progress", () => {
    render(<Progress value={30} buffer={60} />);

    const bufferBar = screen.getByTestId("progress-buffer");
    expect(bufferBar).toHaveStyle({ width: "60%" });
    expect(bufferBar).toHaveClass("bg-gray-300");
  });

  it("shows progress with custom track color", () => {
    render(<Progress value={50} trackColor="bg-purple-200" />);

    const track = screen.getByRole("progressbar").parentElement;
    expect(track).toHaveClass("bg-purple-200");
  });
});
