import { render, fireEvent, screen, waitFor } from "@testing-library/react";
import { Popover } from "./Popover";

describe("Popover", () => {
  it("renders trigger element correctly", () => {
    render(
      <Popover content="Popover content">
        <button>Click me</button>
      </Popover>,
    );
    expect(screen.getByText("Click me")).toBeInTheDocument();
  });

  it("shows popover on click by default", async () => {
    render(
      <Popover content="Popover content">
        <button>Click me</button>
      </Popover>,
    );

    const trigger = screen.getByText("Click me");
    fireEvent.click(trigger);

    await waitFor(() => {
      expect(screen.getByText("Popover content")).toBeInTheDocument();
    });
  });

  it("hides popover on second click", async () => {
    render(
      <Popover content="Popover content">
        <button>Click me</button>
      </Popover>,
    );

    const trigger = screen.getByText("Click me");

    // First click - show
    fireEvent.click(trigger);
    await waitFor(() => {
      expect(screen.getByText("Popover content")).toBeInTheDocument();
    });

    // Second click - hide
    fireEvent.click(trigger);
    await waitFor(() => {
      expect(screen.queryByText("Popover content")).not.toBeInTheDocument();
    });
  });

  it("shows popover on hover when trigger is hover", async () => {
    render(
      <Popover content="Popover content" trigger="hover">
        <button>Hover me</button>
      </Popover>,
    );

    const trigger = screen.getByText("Hover me");
    fireEvent.mouseEnter(trigger);

    await waitFor(() => {
      expect(screen.getByText("Popover content")).toBeInTheDocument();
    });
  });

  it("hides popover on mouse leave when trigger is hover", async () => {
    render(
      <Popover content="Popover content" trigger="hover">
        <button>Hover me</button>
      </Popover>,
    );

    const trigger = screen.getByText("Hover me");
    fireEvent.mouseEnter(trigger);

    await waitFor(() => {
      expect(screen.getByText("Popover content")).toBeInTheDocument();
    });

    fireEvent.mouseLeave(trigger);

    await waitFor(() => {
      expect(screen.queryByText("Popover content")).not.toBeInTheDocument();
    });
  });

  it("shows popover on focus when trigger is focus", async () => {
    render(
      <Popover content="Popover content" trigger="focus">
        <button>Focus me</button>
      </Popover>,
    );

    const trigger = screen.getByText("Focus me");
    fireEvent.focus(trigger);

    await waitFor(() => {
      expect(screen.getByText("Popover content")).toBeInTheDocument();
    });
  });

  it("displays title when provided", async () => {
    render(
      <Popover content="Popover content" title="Popover Title">
        <button>Click me</button>
      </Popover>,
    );

    const trigger = screen.getByText("Click me");
    fireEvent.click(trigger);

    await waitFor(() => {
      expect(screen.getByText("Popover Title")).toBeInTheDocument();
      expect(screen.getByText("Popover content")).toBeInTheDocument();
    });
  });

  it("shows close button when enabled", async () => {
    render(
      <Popover content="Popover content" showCloseButton>
        <button>Click me</button>
      </Popover>,
    );

    const trigger = screen.getByText("Click me");
    fireEvent.click(trigger);

    await waitFor(() => {
      expect(screen.getByText("Popover content")).toBeInTheDocument();
      const closeButton = screen.getByRole("button", { name: "" }); // SVG button
      expect(closeButton).toBeInTheDocument();
    });
  });

  it("closes popover when close button is clicked", async () => {
    render(
      <Popover content="Popover content" showCloseButton>
        <button>Click me</button>
      </Popover>,
    );

    const trigger = screen.getByText("Click me");
    fireEvent.click(trigger);

    await waitFor(() => {
      expect(screen.getByText("Popover content")).toBeInTheDocument();
    });

    const closeButton = screen
      .getAllByRole("button")
      .find((btn) => btn !== trigger);
    if (closeButton) {
      fireEvent.click(closeButton);
    }

    await waitFor(() => {
      expect(screen.queryByText("Popover content")).not.toBeInTheDocument();
    });
  });

  it("hides close button when disabled", async () => {
    render(
      <Popover content="Popover content" showCloseButton={false}>
        <button>Click me</button>
      </Popover>,
    );

    const trigger = screen.getByText("Click me");
    fireEvent.click(trigger);

    await waitFor(() => {
      expect(screen.getByText("Popover content")).toBeInTheDocument();
    });

    // Should only have the trigger button
    const buttons = screen.getAllByRole("button");
    expect(buttons).toHaveLength(1);
    expect(buttons[0]).toBe(trigger);
  });

  it("does not show popover when disabled", () => {
    render(
      <Popover content="Popover content" disabled>
        <button>Click me</button>
      </Popover>,
    );

    const trigger = screen.getByText("Click me");
    fireEvent.click(trigger);

    expect(screen.queryByText("Popover content")).not.toBeInTheDocument();
  });

  it("calls onVisibilityChange when visibility changes", async () => {
    const handleVisibilityChange = jest.fn();

    render(
      <Popover
        content="Popover content"
        onVisibilityChange={handleVisibilityChange}
      >
        <button>Click me</button>
      </Popover>,
    );

    const trigger = screen.getByText("Click me");

    // Show popover
    fireEvent.click(trigger);
    await waitFor(() => {
      expect(handleVisibilityChange).toHaveBeenCalledWith(true);
    });

    // Hide popover
    fireEvent.click(trigger);
    await waitFor(() => {
      expect(handleVisibilityChange).toHaveBeenCalledWith(false);
    });
  });

  it("renders React node content correctly", async () => {
    const content = (
      <div>
        <p>Complex content</p>
        <button>Action button</button>
      </div>
    );

    render(
      <Popover content={content}>
        <button>Click me</button>
      </Popover>,
    );

    const trigger = screen.getByText("Click me");
    fireEvent.click(trigger);

    await waitFor(() => {
      expect(screen.getByText("Complex content")).toBeInTheDocument();
      expect(screen.getByText("Action button")).toBeInTheDocument();
    });
  });

  it("applies custom width when provided", async () => {
    render(
      <Popover content="Popover content" width={300}>
        <button>Click me</button>
      </Popover>,
    );

    const trigger = screen.getByText("Click me");
    fireEvent.click(trigger);

    await waitFor(() => {
      const popover = screen.getByText("Popover content").closest("div");
      expect(popover).toHaveStyle({ width: "300px" });
    });
  });

  it("applies custom className", async () => {
    render(
      <Popover content="Popover content" className="custom-popover">
        <button>Click me</button>
      </Popover>,
    );

    const trigger = screen.getByText("Click me");
    fireEvent.click(trigger);

    await waitFor(() => {
      const popover = screen.getByText("Popover content").closest("div");
      expect(popover).toHaveClass("custom-popover");
    });
  });

  it("closes on outside click for click trigger", async () => {
    render(
      <div>
        <Popover content="Popover content" trigger="click">
          <button>Click me</button>
        </Popover>
        <div>Outside element</div>
      </div>,
    );

    const trigger = screen.getByText("Click me");
    fireEvent.click(trigger);

    await waitFor(() => {
      expect(screen.getByText("Popover content")).toBeInTheDocument();
    });

    const outsideElement = screen.getByText("Outside element");
    fireEvent.mouseDown(outsideElement);

    await waitFor(() => {
      expect(screen.queryByText("Popover content")).not.toBeInTheDocument();
    });
  });
});
