import { render, screen, fireEvent } from "@testing-library/react";
import { vi } from "vitest";
import { Badge } from "./Badge";

describe("Badge", () => {
  // Helper function to get the badge element (parent of text)
  const getBadgeElement = (text: string) => {
    return screen.getByText(text).parentElement;
  };

  it("renders with text content", () => {
    render(<Badge>New</Badge>);
    expect(screen.getByText("New")).toBeInTheDocument();
  });

  it("renders with number content", () => {
    render(<Badge count={5} />);
    expect(screen.getByText("5")).toBeInTheDocument();
  });

  it("applies variant classes correctly", () => {
    const { rerender } = render(<Badge variant="primary">Test</Badge>);
    let badge = screen.getByText("Test").parentElement;
    expect(badge).toHaveClass("bg-blue-500", "text-white");

    rerender(<Badge variant="secondary">Test</Badge>);
    badge = screen.getByText("Test").parentElement;
    expect(badge).toHaveClass("bg-gray-600", "text-white");

    rerender(<Badge variant="success">Test</Badge>);
    badge = screen.getByText("Test").parentElement;
    expect(badge).toHaveClass("bg-green-500", "text-white");

    rerender(<Badge variant="warning">Test</Badge>);
    badge = screen.getByText("Test").parentElement;
    expect(badge).toHaveClass("bg-yellow-500", "text-white");

    rerender(<Badge variant="danger">Test</Badge>);
    badge = screen.getByText("Test").parentElement;
    expect(badge).toHaveClass("bg-red-500", "text-white");

    rerender(<Badge variant="info">Test</Badge>);
    badge = screen.getByText("Test").parentElement;
    expect(badge).toHaveClass("bg-cyan-500", "text-white");
  });

  it("applies default variant classes", () => {
    render(<Badge variant="default">Default Badge</Badge>);
    const badge = getBadgeElement("Default Badge");
    expect(badge).toHaveClass("bg-gray-100", "text-gray-800");
  });

  it("applies size classes correctly", () => {
    const { rerender } = render(<Badge size="sm">Test</Badge>);
    let badge = screen.getByText("Test").parentElement;
    expect(badge).toHaveClass("text-xs", "px-2", "py-0.5");

    rerender(<Badge size="md">Test</Badge>);
    badge = screen.getByText("Test").parentElement;
    expect(badge).toHaveClass("text-sm", "px-2.5", "py-1");

    rerender(<Badge size="lg">Test</Badge>);
    badge = screen.getByText("Test").parentElement;
    expect(badge).toHaveClass("text-base", "px-3", "py-1.5");
  });

  it("renders with dot indicator", () => {
    render(<Badge dot />);
    const dot = screen.getByTestId("badge-dot");
    expect(dot).toHaveClass("w-3", "h-3", "rounded-full");
  });

  it("renders with outlined style", () => {
    render(
      <Badge variant="primary" outlined>
        Test
      </Badge>,
    );

    const badge = screen.getByText("Test").parentElement;
    expect(badge).toHaveClass(
      "border-blue-500",
      "text-blue-500",
      "bg-transparent",
    );
  });

  it("displays max count when count exceeds max", () => {
    render(<Badge count={150} max={99} />);
    expect(screen.getByText("99+")).toBeInTheDocument();
  });

  it("hides badge when count is 0 and showZero is false", () => {
    render(<Badge count={0} />);
    expect(screen.queryByText("0")).not.toBeInTheDocument();
  });

  it("shows badge when count is 0 and showZero is true", () => {
    render(<Badge count={0} showZero />);
    expect(screen.getByText("0")).toBeInTheDocument();
  });

  it("renders with icon", () => {
    const StarIcon = () => <span data-testid="star-icon">⭐</span>;
    render(<Badge icon={<StarIcon />}>Favorite</Badge>);

    expect(screen.getByTestId("star-icon")).toBeInTheDocument();
    expect(screen.getByText("Favorite")).toBeInTheDocument();
  });

  it("renders icon on the left by default", () => {
    render(
      <Badge icon={<span data-testid="test-icon">🔥</span>}>
        Badge with Icon
      </Badge>,
    );
    expect(screen.getByTestId("test-icon")).toBeInTheDocument();
  });

  it("renders icon on the right when iconPosition is right", () => {
    render(
      <Badge
        icon={<span data-testid="test-icon">🔥</span>}
        iconPosition="right"
      >
        Badge with Icon
      </Badge>,
    );
    expect(screen.getByTestId("test-icon")).toBeInTheDocument();
  });

  it("renders as closable with close button", () => {
    const onClose = vi.fn();
    render(
      <Badge closable onClose={onClose}>
        Closable
      </Badge>,
    );

    const closeButton = screen.getByRole("button");
    fireEvent.click(closeButton);

    expect(onClose).toHaveBeenCalled();
  });

  it("shows remove button when removable is true", () => {
    render(<Badge removable>Removable Badge</Badge>);
    expect(screen.getByLabelText("Remove badge")).toBeInTheDocument();
  });

  it("calls onRemove when remove button is clicked", () => {
    const onRemove = vi.fn();
    render(
      <Badge removable onRemove={onRemove}>
        Removable Badge
      </Badge>,
    );

    fireEvent.click(screen.getByLabelText("Remove badge"));

    expect(onRemove).toHaveBeenCalledTimes(1);
  });

  it("applies custom className", () => {
    render(<Badge className="custom-badge">Test</Badge>);

    const badge = screen.getByText("Test").parentElement;
    expect(badge).toHaveClass("custom-badge");
  });

  it("renders with pulsing animation", () => {
    render(<Badge pulse>Live</Badge>);

    const badge = screen.getByText("Live").parentElement;
    expect(badge).toHaveClass("animate-pulse");
  });

  it("renders as a status indicator", () => {
    render(<Badge status="processing">Processing</Badge>);

    const statusDot = screen.getByTestId("badge-status");
    expect(statusDot).toHaveClass("bg-blue-500");
    expect(screen.getByText("Processing")).toBeInTheDocument();
  });

  it("handles different status types", () => {
    const { rerender } = render(<Badge status="success">Success</Badge>);
    let statusDot = screen.getByTestId("badge-status");
    expect(statusDot).toHaveClass("bg-green-500");

    rerender(<Badge status="error">Error</Badge>);
    statusDot = screen.getByTestId("badge-status");
    expect(statusDot).toHaveClass("bg-red-500");

    rerender(<Badge status="warning">Warning</Badge>);
    statusDot = screen.getByTestId("badge-status");
    expect(statusDot).toHaveClass("bg-yellow-500");
  });

  it("renders with gradient background", () => {
    render(<Badge gradient="from-purple-400 to-pink-400">Gradient</Badge>);

    const badge = screen.getByText("Gradient").parentElement;
    expect(badge).toHaveClass(
      "bg-gradient-to-r",
      "from-purple-400",
      "to-pink-400",
    );
  });

  it("handles click events", () => {
    const onClick = vi.fn();
    render(<Badge onClick={onClick}>Clickable</Badge>);

    const badge = screen.getByText("Clickable");
    fireEvent.click(badge);

    expect(onClick).toHaveBeenCalled();
  });

  it("calls onClick when badge is clicked", () => {
    const onClick = vi.fn();
    render(<Badge onClick={onClick}>Clickable Badge</Badge>);

    fireEvent.click(screen.getByText("Clickable Badge"));

    expect(onClick).toHaveBeenCalledTimes(1);
  });

  it("renders as button when onClick is provided", () => {
    render(<Badge onClick={vi.fn()}>Button Badge</Badge>);
    const badge = screen.getByRole("button");
    expect(badge).toBeInTheDocument();
    expect(badge).toHaveAttribute("type", "button");
  });

  it("renders as link when href is provided", () => {
    render(<Badge href="/test">Link Badge</Badge>);
    const badge = screen.getByRole("link");
    expect(badge).toBeInTheDocument();
    expect(badge).toHaveAttribute("href", "/test");
  });

  it("handles keyboard navigation with Enter key", () => {
    const onClick = vi.fn();
    render(<Badge onClick={onClick}>Keyboard Badge</Badge>);

    const badge = screen.getByRole("button");
    fireEvent.keyDown(badge, { key: "Enter" });

    expect(onClick).toHaveBeenCalledTimes(1);
  });

  it("handles keyboard navigation with Space key", () => {
    const onClick = vi.fn();
    render(<Badge onClick={onClick}>Keyboard Badge</Badge>);

    const badge = screen.getByRole("button");
    fireEvent.keyDown(badge, { key: " " });

    expect(onClick).toHaveBeenCalledTimes(1);
  });

  it("applies disabled state correctly", () => {
    const onClick = vi.fn();
    render(
      <Badge onClick={onClick} disabled>
        Disabled Badge
      </Badge>,
    );

    const badge = getBadgeElement("Disabled Badge");
    expect(badge).toHaveClass("opacity-50", "cursor-not-allowed");
    expect(badge).toHaveAttribute("aria-disabled", "true");

    fireEvent.click(badge!);
    expect(onClick).not.toHaveBeenCalled();
  });

  it("does not render as link when disabled and href is provided", () => {
    render(
      <Badge href="/test" disabled>
        Disabled Link
      </Badge>,
    );
    const badge = screen.getByText("Disabled Link");
    expect(badge.tagName).not.toBe("A");
  });

  it("applies animated classes when animated is true", () => {
    render(<Badge animated>Animated Badge</Badge>);
    const badge = getBadgeElement("Animated Badge");
    expect(badge).toHaveClass("transition-all", "duration-300", "ease-in-out");
  });

  it("applies hover effects when clickable", () => {
    const onClick = vi.fn();
    render(<Badge onClick={onClick}>Hoverable</Badge>);

    const badge = screen.getByText("Hoverable").parentElement;
    expect(badge).toHaveClass("cursor-pointer");
  });

  it("applies focus styles when clickable", () => {
    render(<Badge onClick={vi.fn()}>Clickable Badge</Badge>);
    const badge = screen.getByRole("button");
    expect(badge).toHaveClass(
      "focus:outline-none",
      "focus:ring-2",
      "focus:ring-offset-2",
      "focus:ring-blue-500",
    );
  });

  it("does not apply focus styles when not clickable", () => {
    render(<Badge>Static Badge</Badge>);
    const badge = getBadgeElement("Static Badge");
    expect(badge).not.toHaveClass("focus:outline-none");
  });

  it("sets tabIndex to -1 when disabled and clickable", () => {
    render(
      <Badge onClick={vi.fn()} disabled>
        Disabled Clickable
      </Badge>,
    );
    const badge = getBadgeElement("Disabled Clickable");
    expect(badge).toHaveAttribute("tabindex", "-1");
  });

  it("sets tabIndex to 0 when clickable and not disabled", () => {
    render(<Badge onClick={vi.fn()}>Clickable Badge</Badge>);
    const badge = screen.getByRole("button");
    expect(badge).toHaveAttribute("tabindex", "0");
  });

  it("truncates long text content", () => {
    render(<Badge>Very Long Badge Text That Should Be Truncated</Badge>);
    const textElement = screen.getByText(
      "Very Long Badge Text That Should Be Truncated",
    );
    expect(textElement).toHaveClass("truncate");
  });

  it("does not handle keyboard events when disabled", () => {
    const onClick = vi.fn();
    render(
      <Badge onClick={onClick} disabled>
        Disabled Badge
      </Badge>,
    );

    const badge = screen.getByText("Disabled Badge");
    fireEvent.keyDown(badge, { key: "Enter" });
    fireEvent.keyDown(badge, { key: " " });

    expect(onClick).not.toHaveBeenCalled();
  });

  it("renders with custom shape", () => {
    const { rerender } = render(<Badge shape="rounded">Test</Badge>);
    let badge = screen.getByText("Test").parentElement;
    expect(badge).toHaveClass("rounded-md");

    rerender(<Badge shape="pill">Test</Badge>);
    badge = screen.getByText("Test").parentElement;
    expect(badge).toHaveClass("rounded-full");

    rerender(<Badge shape="square">Test</Badge>);
    badge = screen.getByText("Test").parentElement;
    expect(badge).toHaveClass("rounded-none");
  });

  it("displays loading state", () => {
    render(<Badge loading>Loading</Badge>);

    const spinner = screen.getByRole("img", { hidden: true });
    expect(spinner).toHaveClass("animate-spin");
  });

  it("renders with position relative to parent", () => {
    render(
      <div style={{ position: "relative" }}>
        <span>Content</span>
        <Badge position="top-right">5</Badge>
      </div>,
    );

    const badge = screen.getByText("5").parentElement;
    expect(badge).toHaveClass("absolute", "-top-1", "-right-1");
  });

  it("handles different positions", () => {
    const { rerender } = render(<Badge position="top-left">1</Badge>);
    let badge = screen.getByText("1").parentElement;
    expect(badge).toHaveClass("-top-1", "-left-1");

    rerender(<Badge position="bottom-right">2</Badge>);
    badge = screen.getByText("2").parentElement;
    expect(badge).toHaveClass("-bottom-1", "-right-1");
  });

  it("renders with text transformation", () => {
    render(<Badge textTransform="uppercase">test</Badge>);

    const badge = screen.getByText("test").parentElement;
    expect(badge).toHaveClass("uppercase");
  });

  it("handles accessibility attributes", () => {
    render(
      <Badge role="status" aria-label="Notification count">
        3
      </Badge>,
    );

    const badge = screen.getByText("3").parentElement;
    expect(badge).toHaveAttribute("role", "status");
    expect(badge).toHaveAttribute("aria-label", "Notification count");
  });

  it("renders with custom colors", () => {
    render(<Badge color="purple">Custom</Badge>);

    const badge = screen.getByText("Custom").parentElement;
    expect(badge).toHaveClass("bg-purple-500");
  });

  it("applies border styles", () => {
    render(<Badge border="border-2 border-dashed">Bordered</Badge>);

    const badge = screen.getByText("Bordered").parentElement;
    expect(badge).toHaveClass("border-2", "border-dashed");
  });

  it("applies border when bordered is true", () => {
    render(<Badge bordered>Bordered Badge</Badge>);
    const badge = getBadgeElement("Bordered Badge");
    expect(badge).toHaveClass("border");
  });

  it("renders ribbon style", () => {
    render(<Badge ribbon="top-left">Ribbon</Badge>);

    const badge = screen.getByText("Ribbon").parentElement;
    expect(badge).toHaveClass("absolute");
  });

  it("handles overflow text with title", () => {
    render(<Badge title="Very long badge text that overflows">Long...</Badge>);

    const badge = screen.getByText("Long...").parentElement;
    expect(badge).toHaveAttribute(
      "title",
      "Very long badge text that overflows",
    );
  });

  it("renders with shadow effects", () => {
    render(<Badge shadow="lg">Shadow</Badge>);

    const badge = screen.getByText("Shadow").parentElement;
    expect(badge).toHaveClass("shadow-lg");
  });

  it("handles animation on value change", () => {
    const { rerender } = render(<Badge count={5} animateChange />);

    rerender(<Badge count={6} animateChange />);

    const badge = screen.getByText("6").parentElement;
    expect(badge).toHaveClass("animate-bounce");
  });

  it("renders with custom maxCount", () => {
    render(
      <Badge count={250} max={200}>
        High Count Badge
      </Badge>,
    );
    expect(screen.getByText("200+")).toBeInTheDocument();
  });

  it("applies hover styles for interactive variants", () => {
    render(<Badge variant="success">Success Badge</Badge>);
    const badge = getBadgeElement("Success Badge");
    expect(badge).toHaveClass("hover:bg-green-600");
  });

  it("applies hover styles for outline variants", () => {
    render(
      <Badge variant="success" outlined>
        Outline Success Badge
      </Badge>,
    );
    const badge = getBadgeElement("Outline Success Badge");
    expect(badge).toHaveClass("hover:bg-green-50");
  });

  it("renders group of badges", () => {
    render(
      <Badge.Group>
        <Badge>First</Badge>
        <Badge>Second</Badge>
        <Badge>Third</Badge>
      </Badge.Group>,
    );

    expect(screen.getByText("First")).toBeInTheDocument();
    expect(screen.getByText("Second")).toBeInTheDocument();
    expect(screen.getByText("Third")).toBeInTheDocument();
  });

  it("handles empty content gracefully", () => {
    render(<Badge />);

    const badge = screen.getByTestId("empty-badge");
    expect(badge).toBeInTheDocument();
  });

  it("applies theme variants", () => {
    render(<Badge theme="dark">Dark Theme</Badge>);

    const badge = screen.getByText("Dark Theme").parentElement;
    expect(badge).toHaveClass("bg-gray-800", "text-white");
  });

  it("prevents remove button click from triggering badge click", () => {
    const onClick = vi.fn();
    const onRemove = vi.fn();

    render(
      <Badge onClick={onClick} removable onRemove={onRemove}>
        Badge with Remove
      </Badge>,
    );

    fireEvent.click(screen.getByLabelText("Remove badge"));

    expect(onRemove).toHaveBeenCalledTimes(1);
    expect(onClick).not.toHaveBeenCalled();
  });

  it("applies ping animation to dot when pulse is true", () => {
    render(
      <Badge dot pulse>
        Pulse Dot
      </Badge>,
    );
    const badge = screen.getByLabelText("Pulse Dot");
    expect(badge).toHaveClass("animate-pulse");
  });
});
