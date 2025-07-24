import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { vi } from "vitest";
import { BackTop } from "./BackTop";

// Mock scrollTo
Object.defineProperty(window, "scrollTo", {
  value: vi.fn(),
  writable: true,
});

describe("BackTop", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    // Reset scroll position
    Object.defineProperty(window, "pageYOffset", {
      value: 0,
      writable: true,
    });
  });

  it("renders back to top button", () => {
    render(<BackTop />);
    const button = screen.getByRole("button");
    expect(button).toBeInTheDocument();
  });

  it("shows button when scrolled past threshold", async () => {
    render(<BackTop visibilityHeight={100} />);

    // Initially hidden
    const button = screen.getByRole("button");
    expect(button).toHaveClass("opacity-0");

    // Simulate scroll
    Object.defineProperty(window, "pageYOffset", {
      value: 150,
      writable: true,
    });
    fireEvent.scroll(window);

    await waitFor(() => {
      expect(button).toHaveClass("opacity-100");
    });
  });

  it("scrolls to top when clicked", () => {
    render(<BackTop />);
    const button = screen.getByRole("button");

    fireEvent.click(button);
    expect(window.scrollTo).toHaveBeenCalledWith({
      top: 0,
      behavior: "smooth",
    });
  });

  it("supports custom click handler", () => {
    const onClick = vi.fn();
    render(<BackTop onClick={onClick} />);

    const button = screen.getByRole("button");
    fireEvent.click(button);

    expect(onClick).toHaveBeenCalled();
  });

  it("renders with custom children", () => {
    render(<BackTop>Go to Top</BackTop>);
    expect(screen.getByText("Go to Top")).toBeInTheDocument();
  });

  it("supports different sizes", () => {
    const sizes = ["small", "medium", "large"] as const;

    sizes.forEach((size) => {
      const { unmount } = render(<BackTop size={size} />);
      const button = screen.getByRole("button");
      expect(button).toBeInTheDocument();
      unmount();
    });
  });

  it("supports different shapes", () => {
    const shapes = ["circle", "square"] as const;

    shapes.forEach((shape) => {
      const { unmount } = render(<BackTop shape={shape} />);
      const button = screen.getByRole("button");
      expect(button).toBeInTheDocument();
      unmount();
    });
  });

  it("supports different positions", () => {
    const positions = [
      "bottom-right",
      "bottom-left",
      "top-right",
      "top-left",
    ] as const;

    positions.forEach((position) => {
      const { unmount } = render(<BackTop position={position} />);
      const button = screen.getByRole("button");
      expect(button).toBeInTheDocument();
      unmount();
    });
  });

  it("supports custom target element", async () => {
    const targetRef = { current: document.createElement("div") };
    const scrollToSpy = vi.fn();
    targetRef.current.scrollTo = scrollToSpy;

    render(<BackTop target={() => targetRef.current} />);

    const button = screen.getByRole("button");
    fireEvent.click(button);

    expect(scrollToSpy).toHaveBeenCalledWith({
      top: 0,
      behavior: "smooth",
    });
  });

  it("supports custom duration for scroll animation", () => {
    render(<BackTop duration={1000} />);
    const button = screen.getByRole("button");

    fireEvent.click(button);
    expect(window.scrollTo).toHaveBeenCalled();
  });

  it("renders with custom icon", () => {
    const icon = <span data-testid="custom-icon">↑</span>;
    render(<BackTop icon={icon} />);
    expect(screen.getByTestId("custom-icon")).toBeInTheDocument();
  });

  it("supports custom className", () => {
    render(<BackTop className="custom-backtop" />);
    const button = screen.getByRole("button");
    expect(button).toHaveClass("custom-backtop");
  });

  it("supports disabled state", () => {
    render(<BackTop disabled />);
    const button = screen.getByRole("button");
    expect(button).toBeDisabled();
  });

  it("supports custom tooltip", async () => {
    render(<BackTop tooltip="Back to top" />);
    const button = screen.getByRole("button");

    fireEvent.mouseEnter(button);
    await waitFor(() => {
      expect(screen.getByText("Back to top")).toBeInTheDocument();
    });
  });

  it("supports smooth scroll behavior", () => {
    render(<BackTop smooth />);
    const button = screen.getByRole("button");

    fireEvent.click(button);
    expect(window.scrollTo).toHaveBeenCalledWith({
      top: 0,
      behavior: "smooth",
    });
  });

  it("supports animated appearance", () => {
    render(<BackTop animated />);
    const button = screen.getByRole("button");
    expect(button).toBeInTheDocument();
  });

  it("supports custom offset from edges", () => {
    render(<BackTop right={20} bottom={20} />);
    const button = screen.getByRole("button");
    expect(button).toBeInTheDocument();
  });

  it("supports custom z-index", () => {
    render(<BackTop zIndex={9999} />);
    const button = screen.getByRole("button");
    expect(button).toBeInTheDocument();
  });

  it("supports fade animation type", () => {
    render(<BackTop animationType="fade" />);
    const button = screen.getByRole("button");
    expect(button).toBeInTheDocument();
  });

  it("supports slide animation type", () => {
    render(<BackTop animationType="slide" />);
    const button = screen.getByRole("button");
    expect(button).toBeInTheDocument();
  });

  it("supports scale animation type", () => {
    render(<BackTop animationType="scale" />);
    const button = screen.getByRole("button");
    expect(button).toBeInTheDocument();
  });

  it("calls onShow when button becomes visible", async () => {
    const onShow = vi.fn();
    render(<BackTop visibilityHeight={100} onShow={onShow} />);

    Object.defineProperty(window, "pageYOffset", {
      value: 150,
      writable: true,
    });
    fireEvent.scroll(window);

    await waitFor(() => {
      expect(onShow).toHaveBeenCalled();
    });
  });

  it("calls onHide when button becomes hidden", async () => {
    const onHide = vi.fn();
    render(<BackTop visibilityHeight={100} onHide={onHide} />);

    // Show first
    Object.defineProperty(window, "pageYOffset", {
      value: 150,
      writable: true,
    });
    fireEvent.scroll(window);

    // Then hide
    Object.defineProperty(window, "pageYOffset", { value: 50, writable: true });
    fireEvent.scroll(window);

    await waitFor(() => {
      expect(onHide).toHaveBeenCalled();
    });
  });

  it("supports custom scroll offset target", () => {
    render(<BackTop scrollOffset={500} />);
    const button = screen.getByRole("button");

    fireEvent.click(button);
    expect(window.scrollTo).toHaveBeenCalledWith({
      top: 500,
      behavior: "smooth",
    });
  });

  it("supports custom styles", () => {
    const customStyle = { backgroundColor: "red" };
    render(<BackTop style={customStyle} />);
    const button = screen.getByRole("button");
    expect(button).toBeInTheDocument();
  });

  it("supports hover effects", () => {
    render(<BackTop hoverEffect />);
    const button = screen.getByRole("button");
    expect(button).toBeInTheDocument();
  });

  it("supports pulse effect", () => {
    render(<BackTop pulse />);
    const button = screen.getByRole("button");
    expect(button).toBeInTheDocument();
  });

  it("supports custom scroll container", async () => {
    const container = document.createElement("div");
    const scrollToSpy = vi.fn();
    container.scrollTo = scrollToSpy;

    render(<BackTop scrollContainer={() => container} />);

    const button = screen.getByRole("button");
    fireEvent.click(button);

    expect(scrollToSpy).toHaveBeenCalledWith({
      top: 0,
      behavior: "smooth",
    });
  });

  it("supports keyboard interaction", () => {
    render(<BackTop />);
    const button = screen.getByRole("button");

    fireEvent.keyDown(button, { key: "Enter" });
    expect(window.scrollTo).toHaveBeenCalled();
  });

  it("supports double click prevention", () => {
    render(<BackTop />);
    const button = screen.getByRole("button");

    fireEvent.click(button);
    fireEvent.click(button);

    expect(window.scrollTo).toHaveBeenCalledTimes(1);
  });

  it("renders with text content", () => {
    render(<BackTop text="Top" />);
    expect(screen.getByText("Top")).toBeInTheDocument();
  });

  it("supports custom aria label", () => {
    render(<BackTop ariaLabel="Scroll to top of page" />);
    const button = screen.getByRole("button");
    expect(button).toHaveAttribute("aria-label", "Scroll to top of page");
  });

  it("supports custom data attributes", () => {
    render(<BackTop data-testid="custom-backtop" data-tracking="scroll-top" />);
    const button = screen.getByTestId("custom-backtop");
    expect(button).toHaveAttribute("data-tracking", "scroll-top");
  });
});
