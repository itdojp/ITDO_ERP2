import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { vi } from "vitest";
import { Notification } from "./Notification";

describe("Notification", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.runOnlyPendingTimers();
    vi.useRealTimers();
  });

  it("renders notification with message", () => {
    render(<Notification message="Test notification" />);

    expect(screen.getByTestId("notification-container")).toBeInTheDocument();
    expect(screen.getByText("Test notification")).toBeInTheDocument();
  });

  it("displays different notification types", () => {
    const types = ["success", "error", "warning", "info"] as const;

    types.forEach((type) => {
      const { unmount } = render(<Notification message="Test" type={type} />);
      const container = screen.getByTestId("notification-container");
      expect(container).toHaveClass(`type-${type}`);
      unmount();
    });
  });

  it("shows title when provided", () => {
    render(<Notification title="Important" message="Test notification" />);

    expect(screen.getByTestId("notification-title")).toBeInTheDocument();
    expect(screen.getByText("Important")).toBeInTheDocument();
  });

  it("displays close button when closable", () => {
    render(<Notification message="Test" closable />);

    expect(screen.getByTestId("notification-close")).toBeInTheDocument();
  });

  it("calls onClose when close button clicked", () => {
    const onClose = vi.fn();
    render(<Notification message="Test" closable onClose={onClose} />);

    const closeButton = screen.getByTestId("notification-close");
    fireEvent.click(closeButton);

    expect(onClose).toHaveBeenCalled();
  });

  it("auto closes after duration", async () => {
    const onClose = vi.fn();
    render(<Notification message="Test" duration={1000} onClose={onClose} />);

    // Fast forward time
    vi.advanceTimersByTime(1000);

    await waitFor(() => {
      expect(onClose).toHaveBeenCalled();
    });
  });

  it("does not auto close when duration is 0", () => {
    const onClose = vi.fn();
    render(<Notification message="Test" duration={0} onClose={onClose} />);

    vi.advanceTimersByTime(5000);

    expect(onClose).not.toHaveBeenCalled();
  });

  it("shows action button when provided", () => {
    const onAction = vi.fn();
    render(
      <Notification
        message="Test"
        action={{ label: "Undo", onClick: onAction }}
      />,
    );

    const actionButton = screen.getByTestId("notification-action");
    expect(actionButton).toBeInTheDocument();
    expect(screen.getByText("Undo")).toBeInTheDocument();

    fireEvent.click(actionButton);
    expect(onAction).toHaveBeenCalled();
  });

  it("displays icon when provided", () => {
    render(<Notification message="Test" icon="🔔" />);

    expect(screen.getByTestId("notification-icon")).toBeInTheDocument();
    expect(screen.getByText("🔔")).toBeInTheDocument();
  });

  it("shows default icons for different types", () => {
    const typeIcons = [
      { type: "success", expectedClass: "icon-success" },
      { type: "error", expectedClass: "icon-error" },
      { type: "warning", expectedClass: "icon-warning" },
      { type: "info", expectedClass: "icon-info" },
    ] as const;

    typeIcons.forEach(({ type, expectedClass }) => {
      const { unmount } = render(
        <Notification message="Test" type={type} showDefaultIcon />,
      );
      const iconContainer = screen.getByTestId("notification-icon");
      const iconElement = iconContainer.querySelector("div");
      expect(iconElement).toHaveClass(expectedClass);
      unmount();
    });
  });

  it("supports different positions", () => {
    const positions = [
      "top-right",
      "top-left",
      "bottom-right",
      "bottom-left",
      "top-center",
      "bottom-center",
    ] as const;

    positions.forEach((position) => {
      const { unmount } = render(
        <Notification message="Test" position={position} />,
      );
      const container = screen.getByTestId("notification-container");
      expect(container).toHaveClass(`position-${position}`);
      unmount();
    });
  });

  it("supports different sizes", () => {
    const sizes = ["sm", "md", "lg"] as const;

    sizes.forEach((size) => {
      const { unmount } = render(<Notification message="Test" size={size} />);
      const container = screen.getByTestId("notification-container");
      expect(container).toHaveClass(`size-${size}`);
      unmount();
    });
  });

  it("supports different themes", () => {
    const themes = ["light", "dark"] as const;

    themes.forEach((theme) => {
      const { unmount } = render(<Notification message="Test" theme={theme} />);
      const container = screen.getByTestId("notification-container");
      expect(container).toHaveClass(`theme-${theme}`);
      unmount();
    });
  });

  it("shows progress bar when showProgress is true", () => {
    render(<Notification message="Test" duration={2000} showProgress />);

    expect(screen.getByTestId("notification-progress")).toBeInTheDocument();
  });

  it("updates progress bar over time", async () => {
    render(<Notification message="Test" duration={1000} showProgress />);

    const progressBar = screen.getByTestId("notification-progress");

    // Initially should be at 100%
    expect(progressBar).toHaveStyle({ width: "100%" });

    // After half the duration, should be at 50%
    vi.advanceTimersByTime(500);
    await waitFor(() => {
      expect(progressBar).toHaveStyle({ width: "50%" });
    });
  });

  it("pauses auto close on hover", async () => {
    const onClose = vi.fn();
    render(
      <Notification
        message="Test"
        duration={1000}
        pauseOnHover
        onClose={onClose}
      />,
    );

    const container = screen.getByTestId("notification-container");

    // Hover after 500ms
    vi.advanceTimersByTime(500);
    fireEvent.mouseEnter(container);

    // Advance past original duration
    vi.advanceTimersByTime(1000);
    expect(onClose).not.toHaveBeenCalled();

    // Resume on mouse leave
    fireEvent.mouseLeave(container);
    vi.advanceTimersByTime(500);

    await waitFor(() => {
      expect(onClose).toHaveBeenCalled();
    });
  });

  it("supports custom styling", () => {
    render(<Notification message="Test" className="custom-notification" />);

    const container = screen.getByTestId("notification-container");
    expect(container).toHaveClass("custom-notification");
  });

  it("handles animation enter", () => {
    render(<Notification message="Test" animate />);

    const container = screen.getByTestId("notification-container");
    expect(container).toHaveClass("animate-enter");
  });

  it("handles animation exit", async () => {
    const onClose = vi.fn();
    render(<Notification message="Test" animate closable onClose={onClose} />);

    const closeButton = screen.getByTestId("notification-close");
    fireEvent.click(closeButton);

    const container = screen.getByTestId("notification-container");
    expect(container).toHaveClass("animate-exit");
  });

  it("supports RTL layout", () => {
    render(<Notification message="Test" rtl />);

    const container = screen.getByTestId("notification-container");
    expect(container).toHaveClass("rtl");
  });

  it("shows multiple lines for long messages", () => {
    const longMessage =
      "This is a very long notification message that should wrap to multiple lines when displayed";
    render(<Notification message={longMessage} multiline />);

    const container = screen.getByTestId("notification-container");
    expect(container).toHaveClass("multiline");
  });

  it("supports priority levels", () => {
    const priorities = ["low", "normal", "high", "urgent"] as const;

    priorities.forEach((priority) => {
      const { unmount } = render(
        <Notification message="Test" priority={priority} />,
      );
      const container = screen.getByTestId("notification-container");
      expect(container).toHaveClass(`priority-${priority}`);
      unmount();
    });
  });

  it("displays timestamp when showTimestamp is true", () => {
    render(<Notification message="Test" showTimestamp />);

    expect(screen.getByTestId("notification-timestamp")).toBeInTheDocument();
  });

  it("supports custom timestamp format", () => {
    const customTimestamp = "2023-01-01 12:00:00";
    render(
      <Notification message="Test" showTimestamp timestamp={customTimestamp} />,
    );

    expect(screen.getByText(customTimestamp)).toBeInTheDocument();
  });

  it("handles keyboard accessibility", () => {
    const onClose = vi.fn();
    render(<Notification message="Test" closable onClose={onClose} />);

    const closeButton = screen.getByTestId("notification-close");

    // Should be focusable
    expect(closeButton).toHaveAttribute("tabindex", "0");

    // Should respond to Enter key
    fireEvent.keyDown(closeButton, { key: "Enter" });
    expect(onClose).toHaveBeenCalled();
  });

  it("supports custom close button", () => {
    const customCloseButton = <button data-testid="custom-close">×</button>;
    render(<Notification message="Test" closeButton={customCloseButton} />);

    expect(screen.getByTestId("custom-close")).toBeInTheDocument();
  });

  it("handles loading state", () => {
    render(<Notification message="Test" loading />);

    expect(screen.getByTestId("notification-loading")).toBeInTheDocument();
  });

  it("shows loading spinner", () => {
    render(<Notification message="Processing..." loading showLoadingSpinner />);

    expect(screen.getByTestId("loading-spinner")).toBeInTheDocument();
  });

  it("supports rich content rendering", () => {
    const richContent = (
      <div data-testid="rich-content">
        <strong>Bold text</strong> and <em>italic text</em>
      </div>
    );

    render(<Notification content={richContent} />);

    expect(screen.getByTestId("rich-content")).toBeInTheDocument();
  });

  it("supports stacking behavior", () => {
    render(<Notification message="Test" stackable stackIndex={2} />);

    const container = screen.getByTestId("notification-container");
    expect(container).toHaveClass("stackable");
    expect(container).toHaveAttribute("data-stack-index", "2");
  });

  it("handles dismiss on click outside", () => {
    const onClose = vi.fn();
    render(
      <Notification message="Test" dismissOnClickOutside onClose={onClose} />,
    );

    // Click outside the notification
    fireEvent.mouseDown(document.body);

    expect(onClose).toHaveBeenCalled();
  });

  it("supports swipe to dismiss on mobile", () => {
    const onClose = vi.fn();
    render(<Notification message="Test" swipeToDismiss onClose={onClose} />);

    const container = screen.getByTestId("notification-container");

    // Simulate swipe gesture
    fireEvent.touchStart(container, { touches: [{ clientX: 0, clientY: 0 }] });
    fireEvent.touchMove(container, { touches: [{ clientX: 150, clientY: 0 }] });
    fireEvent.touchEnd(container, {
      changedTouches: [{ clientX: 150, clientY: 0 }],
    });

    expect(onClose).toHaveBeenCalled();
  });

  it("supports persistent notifications", () => {
    const onClose = vi.fn();
    render(
      <Notification
        message="Test"
        persistent
        duration={1000}
        onClose={onClose}
      />,
    );

    // Should not auto close even with duration
    vi.advanceTimersByTime(2000);
    expect(onClose).not.toHaveBeenCalled();
  });

  it("handles error boundary for action failures", () => {
    const errorAction = {
      label: "Error Action",
      onClick: () => {
        throw new Error("Action failed");
      },
    };

    render(<Notification message="Test" action={errorAction} />);

    const actionButton = screen.getByTestId("notification-action");

    // Should not crash when action throws error
    expect(() => fireEvent.click(actionButton)).not.toThrow();
  });

  it("supports custom data attributes", () => {
    render(
      <Notification message="Test" data-category="system" data-id="notif-1" />,
    );

    const container = screen.getByTestId("notification-container");
    expect(container).toHaveAttribute("data-category", "system");
    expect(container).toHaveAttribute("data-id", "notif-1");
  });

  it("handles visibility state changes", () => {
    const { rerender } = render(<Notification message="Test" visible={true} />);

    const container = screen.getByTestId("notification-container");
    expect(container).toBeVisible();

    rerender(<Notification message="Test" visible={false} />);

    // When visible=false and no animation, component should not render
    expect(
      screen.queryByTestId("notification-container"),
    ).not.toBeInTheDocument();
  });

  it("supports sound notifications", () => {
    const mockPlay = vi.fn();
    global.Audio = vi.fn(() => ({ play: mockPlay })) as any;

    render(
      <Notification message="Test" playSound soundUrl="/notification.mp3" />,
    );

    expect(global.Audio).toHaveBeenCalledWith("/notification.mp3");
    expect(mockPlay).toHaveBeenCalled();
  });

  it("handles focus management", () => {
    render(<Notification message="Test" autoFocus />);

    const container = screen.getByTestId("notification-container");
    expect(container).toHaveFocus();
  });

  it("supports accessibility labels", () => {
    render(
      <Notification
        message="Test"
        ariaLabel="System notification"
        ariaLive="polite"
      />,
    );

    const container = screen.getByTestId("notification-container");
    expect(container).toHaveAttribute("aria-label", "System notification");
    expect(container).toHaveAttribute("aria-live", "polite");
  });

  it("handles notification queuing", () => {
    render(<Notification message="Test" queueable maxQueue={3} />);

    const container = screen.getByTestId("notification-container");
    expect(container).toHaveClass("queueable");
    expect(container).toHaveAttribute("data-max-queue", "3");
  });

  it("supports drag to reposition", () => {
    const onDrag = vi.fn();
    render(<Notification message="Test" draggable onDrag={onDrag} />);

    const container = screen.getByTestId("notification-container");
    expect(container).toHaveAttribute("draggable", "true");

    fireEvent.dragStart(container);
    expect(onDrag).toHaveBeenCalled();
  });
});
