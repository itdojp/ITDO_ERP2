import { render, screen, fireEvent } from "@testing-library/react";
import { vi } from "vitest";
import { Result } from "./Result";

describe("Result", () => {
  it("renders success result by default", () => {
    render(<Result title="Success" />);
    expect(screen.getByText("Success")).toBeInTheDocument();
    const icon = screen.getByRole("img", { hidden: true });
    expect(icon).toBeInTheDocument();
  });

  it("renders different status types", () => {
    const statuses = [
      "success",
      "error",
      "info",
      "warning",
      "404",
      "403",
      "500",
    ] as const;

    statuses.forEach((status) => {
      const { unmount } = render(
        <Result status={status} title={`Status ${status}`} />,
      );
      expect(screen.getByText(`Status ${status}`)).toBeInTheDocument();
      unmount();
    });
  });

  it("renders with subtitle", () => {
    render(
      <Result title="Success" subTitle="Operation completed successfully" />,
    );
    expect(screen.getByText("Success")).toBeInTheDocument();
    expect(
      screen.getByText("Operation completed successfully"),
    ).toBeInTheDocument();
  });

  it("renders with extra content", () => {
    const extra = <div data-testid="extra-content">Additional info</div>;
    render(<Result title="Success" extra={extra} />);
    expect(screen.getByTestId("extra-content")).toBeInTheDocument();
  });

  it("supports custom icon", () => {
    const customIcon = <span data-testid="custom-icon">🎉</span>;
    render(<Result icon={customIcon} title="Custom" />);
    expect(screen.getByTestId("custom-icon")).toBeInTheDocument();
  });

  it("renders with action button", () => {
    const onClick = vi.fn();
    const action = <button onClick={onClick}>Try Again</button>;
    render(<Result title="Error" action={action} />);

    const button = screen.getByText("Try Again");
    expect(button).toBeInTheDocument();

    fireEvent.click(button);
    expect(onClick).toHaveBeenCalled();
  });

  it("supports multiple actions", () => {
    const actions = [
      <button key="1">Action 1</button>,
      <button key="2">Action 2</button>,
    ];
    render(<Result title="Success" actions={actions} />);

    expect(screen.getByText("Action 1")).toBeInTheDocument();
    expect(screen.getByText("Action 2")).toBeInTheDocument();
  });

  it("renders with custom className", () => {
    render(<Result title="Test" className="custom-result" />);
    const container = screen.getByTestId("result-container");
    expect(container).toHaveClass("custom-result");
  });

  it("supports different sizes", () => {
    const sizes = ["small", "medium", "large"] as const;

    sizes.forEach((size) => {
      const { unmount } = render(<Result size={size} title={`Size ${size}`} />);
      expect(screen.getByText(`Size ${size}`)).toBeInTheDocument();
      unmount();
    });
  });

  it("renders with description", () => {
    render(
      <Result
        title="Success"
        description="Your request has been processed successfully and all data has been saved."
      />,
    );
    expect(
      screen.getByText(/Your request has been processed/),
    ).toBeInTheDocument();
  });

  it("supports custom styles", () => {
    const customStyle = { backgroundColor: "lightblue" };
    render(<Result title="Test" style={customStyle} />);
    const container = screen.getByTestId("result-container");
    expect(container).toBeInTheDocument();
  });

  it("renders without icon when icon is false", () => {
    render(<Result icon={false} title="No Icon" />);
    expect(screen.queryByRole("img", { hidden: true })).not.toBeInTheDocument();
    expect(screen.getByText("No Icon")).toBeInTheDocument();
  });

  it("supports loading state", () => {
    render(<Result loading title="Loading Result" />);
    const spinner = screen.getByRole("img", { hidden: true });
    expect(spinner).toHaveClass("animate-spin");
  });

  it("renders with children content", () => {
    render(
      <Result title="Success">
        <div data-testid="children-content">Custom children content</div>
      </Result>,
    );
    expect(screen.getByTestId("children-content")).toBeInTheDocument();
  });

  it("supports different layouts", () => {
    const layouts = ["vertical", "horizontal"] as const;

    layouts.forEach((layout) => {
      const { unmount } = render(
        <Result layout={layout} title={`Layout ${layout}`} />,
      );
      expect(screen.getByText(`Layout ${layout}`)).toBeInTheDocument();
      unmount();
    });
  });

  it("renders with progress indicator", () => {
    render(<Result title="Processing" progress={75} />);
    expect(screen.getByText("75%")).toBeInTheDocument();

    const progressBar = screen.getByRole("progressbar");
    expect(progressBar).toBeInTheDocument();
    expect(progressBar).toHaveAttribute("aria-valuenow", "75");
  });

  it("supports bordered style", () => {
    render(<Result title="Bordered" bordered />);
    const container = screen.getByTestId("result-container");
    expect(container).toHaveClass("border");
  });

  it("renders with background", () => {
    render(<Result title="Background" background />);
    const container = screen.getByTestId("result-container");
    expect(container).toBeInTheDocument();
  });

  it("supports centered layout", () => {
    render(<Result title="Centered" centered />);
    const container = screen.getByTestId("result-container");
    expect(container).toHaveClass("justify-center");
  });

  it("renders with footer content", () => {
    const footer = <div data-testid="footer-content">Footer information</div>;
    render(<Result title="Success" footer={footer} />);
    expect(screen.getByTestId("footer-content")).toBeInTheDocument();
  });

  it("supports custom colors", () => {
    render(<Result title="Custom Color" color="#ff0000" />);
    const container = screen.getByTestId("result-container");
    expect(container).toBeInTheDocument();
  });

  it("renders with timestamp", () => {
    const timestamp = new Date("2023-01-01T12:00:00Z");
    render(<Result title="Timed Result" timestamp={timestamp} />);
    expect(screen.getByText(/2023/)).toBeInTheDocument();
  });

  it("supports collapsible content", () => {
    render(
      <Result title="Collapsible" collapsible>
        <div>Collapsible content</div>
      </Result>,
    );

    const toggleButton = screen.getByRole("button");
    expect(toggleButton).toBeInTheDocument();

    fireEvent.click(toggleButton);
    expect(screen.getByText("Collapsible content")).toBeInTheDocument();
  });

  it("renders with status message mapping", () => {
    render(<Result status="404" showDetails />);
    expect(screen.getByText("404")).toBeInTheDocument();
    expect(
      screen.getByText("Sorry, the page you visited does not exist."),
    ).toBeInTheDocument();
  });

  it("supports animated transitions", () => {
    render(<Result title="Animated" animated />);
    const container = screen.getByTestId("result-container");
    expect(container).toBeInTheDocument();
  });

  it("renders with custom icon size", () => {
    render(<Result title="Large Icon" iconSize="large" />);
    const container = screen.getByTestId("result-container");
    expect(container).toBeInTheDocument();
  });

  it("supports inline layout", () => {
    render(<Result title="Inline" inline />);
    const container = screen.getByTestId("result-container");
    expect(container).toBeInTheDocument();
  });

  it("renders with overlay mode", () => {
    render(<Result title="Overlay" overlay />);
    const container = screen.getByTestId("result-container");
    expect(container).toBeInTheDocument();
  });

  it("supports custom icon color", () => {
    render(<Result title="Colored Icon" iconColor="#00ff00" />);
    const container = screen.getByTestId("result-container");
    expect(container).toBeInTheDocument();
  });

  it("renders with help text", () => {
    render(
      <Result title="Help" helpText="Need assistance? Contact support." />,
    );
    expect(
      screen.getByText("Need assistance? Contact support."),
    ).toBeInTheDocument();
  });

  it("supports responsive behavior", () => {
    render(<Result title="Responsive" responsive />);
    const container = screen.getByTestId("result-container");
    expect(container).toBeInTheDocument();
  });

  it("renders with custom data attributes", () => {
    render(
      <Result
        title="Data Attrs"
        data-testid="custom-result"
        data-status="success"
      />,
    );
    const container = screen.getByTestId("custom-result");
    expect(container).toHaveAttribute("data-status", "success");
  });

  it("handles retry functionality", () => {
    const onRetry = vi.fn();
    render(<Result status="error" title="Failed" onRetry={onRetry} />);

    const retryButton = screen.getByText("Retry");
    expect(retryButton).toBeInTheDocument();

    fireEvent.click(retryButton);
    expect(onRetry).toHaveBeenCalled();
  });

  it("supports custom title element", () => {
    const customTitle = (
      <h1 data-testid="custom-title">Custom Title Element</h1>
    );
    render(<Result title={customTitle} />);
    expect(screen.getByTestId("custom-title")).toBeInTheDocument();
  });

  it("renders with status code details", () => {
    render(<Result status="500" showDetails />);
    expect(screen.getByText("500")).toBeInTheDocument();
    expect(
      screen.getByText("Sorry, something went wrong."),
    ).toBeInTheDocument();
  });
});
