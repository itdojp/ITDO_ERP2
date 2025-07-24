import { render, screen, fireEvent } from "@testing-library/react";
import { vi } from "vitest";
import { Badge } from "./Badge";

describe("Badge", () => {
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
    expect(badge).toHaveClass("bg-gray-500", "text-white");

    rerender(<Badge variant="success">Test</Badge>);
    badge = screen.getByText("Test").parentElement;
    expect(badge).toHaveClass("bg-green-500", "text-white");

    rerender(<Badge variant="warning">Test</Badge>);
    badge = screen.getByText("Test").parentElement;
    expect(badge).toHaveClass("bg-yellow-500", "text-white");

    rerender(<Badge variant="danger">Test</Badge>);
    badge = screen.getByText("Test").parentElement;
    expect(badge).toHaveClass("bg-red-500", "text-white");
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
    expect(dot).toHaveClass("w-2", "h-2", "rounded-full");
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

  it("applies hover effects when clickable", () => {
    const onClick = vi.fn();
    render(<Badge onClick={onClick}>Hoverable</Badge>);

    const badge = screen.getByText("Hoverable").parentElement;
    expect(badge).toHaveClass("hover:opacity-80", "cursor-pointer");
  });

  it("renders with custom shape", () => {
    const { rerender } = render(<Badge shape="rounded">Test</Badge>);
    let badge = screen.getByText("Test").parentElement;
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
});
