import React from "react";
import { render, screen, fireEvent } from "@testing-library/react";
import { vi } from "vitest";
import { Avatar } from "./Avatar";

describe("Avatar", () => {
  it("renders with image src", () => {
    render(<Avatar src="https://example.com/avatar.jpg" alt="User Avatar" />);

    const avatar = screen.getByRole("img");
    expect(avatar).toHaveAttribute("src", "https://example.com/avatar.jpg");
    expect(avatar).toHaveAttribute("alt", "User Avatar");
  });

  it("renders with initials when no src provided", () => {
    render(<Avatar name="John Doe" />);

    expect(screen.getByText("JD")).toBeInTheDocument();
  });

  it("renders with custom initials", () => {
    render(<Avatar initials="AB" />);

    expect(screen.getByText("AB")).toBeInTheDocument();
  });

  it("falls back to initials when image fails to load", () => {
    render(<Avatar src="invalid-url.jpg" name="Jane Smith" />);

    const image = screen.getByRole("img");
    fireEvent.error(image);

    expect(screen.getByText("JS")).toBeInTheDocument();
  });

  it("applies size classes correctly", () => {
    const { rerender } = render(<Avatar size="sm" name="Test" />);
    let avatar = screen.getByText("T").parentElement;
    expect(avatar).toHaveClass("w-8", "h-8", "text-sm");

    rerender(<Avatar size="md" name="Test" />);
    avatar = screen.getByText("T").parentElement;
    expect(avatar).toHaveClass("w-10", "h-10", "text-base");

    rerender(<Avatar size="lg" name="Test" />);
    avatar = screen.getByText("T").parentElement;
    expect(avatar).toHaveClass("w-12", "h-12", "text-lg");

    rerender(<Avatar size="xl" name="Test" />);
    avatar = screen.getByText("T").parentElement;
    expect(avatar).toHaveClass("w-16", "h-16", "text-xl");
  });

  it("applies shape variants correctly", () => {
    const { rerender } = render(<Avatar shape="circle" name="Test" />);
    let avatar = screen.getByText("T").parentElement;
    expect(avatar).toHaveClass("rounded-full");

    rerender(<Avatar shape="square" name="Test" />);
    avatar = screen.getByText("T").parentElement;
    expect(avatar).toHaveClass("rounded-md");
  });

  it("displays online status indicator", () => {
    render(<Avatar name="Test" status="online" />);

    const indicator = screen.getByTestId("avatar-status");
    expect(indicator).toHaveClass("bg-green-400");
  });

  it("displays different status indicators", () => {
    const { rerender } = render(<Avatar name="Test" status="online" />);
    let indicator = screen.getByTestId("avatar-status");
    expect(indicator).toHaveClass("bg-green-400");

    rerender(<Avatar name="Test" status="away" />);
    indicator = screen.getByTestId("avatar-status");
    expect(indicator).toHaveClass("bg-yellow-400");

    rerender(<Avatar name="Test" status="busy" />);
    indicator = screen.getByTestId("avatar-status");
    expect(indicator).toHaveClass("bg-red-400");

    rerender(<Avatar name="Test" status="offline" />);
    indicator = screen.getByTestId("avatar-status");
    expect(indicator).toHaveClass("bg-gray-400");
  });

  it("renders avatar group", () => {
    render(
      <Avatar.Group max={3}>
        <Avatar name="User 1" />
        <Avatar name="User 2" />
        <Avatar name="User 3" />
        <Avatar name="User 4" />
        <Avatar name="User 5" />
      </Avatar.Group>,
    );

    const avatars = screen.getAllByText(/U/);
    expect(avatars).toHaveLength(3); // 3 avatars + 1 overflow
    expect(screen.getByText("+2")).toBeInTheDocument();
  });

  it("handles click events", () => {
    const onClick = vi.fn();
    render(<Avatar name="Test" onClick={onClick} />);

    const avatar = screen.getByText("T").parentElement;
    fireEvent.click(avatar!);

    expect(onClick).toHaveBeenCalled();
  });

  it("renders with custom icon", () => {
    const UserIcon = () => <span data-testid="user-icon">👤</span>;
    render(<Avatar icon={<UserIcon />} />);

    expect(screen.getByTestId("user-icon")).toBeInTheDocument();
  });

  it("applies custom background color", () => {
    render(<Avatar name="Test" backgroundColor="bg-purple-500" />);

    const avatar = screen.getByText("T").parentElement;
    expect(avatar).toHaveClass("bg-purple-500");
  });

  it("applies custom text color", () => {
    render(<Avatar name="Test" textColor="text-yellow-300" />);

    const avatarText = screen.getByText("T");
    expect(avatarText).toHaveClass("text-yellow-300");
  });

  it("generates background color from name", () => {
    render(<Avatar name="Alice" />);

    const avatar = screen.getByText("A").parentElement;
    expect(avatar).toHaveClass("bg-orange-500"); // Based on hash of "Alice"
  });

  it("renders with badge", () => {
    render(<Avatar name="Test" badge={<span data-testid="badge">5</span>} />);

    expect(screen.getByTestId("badge")).toBeInTheDocument();
  });

  it("handles draggable avatars", () => {
    const onDragStart = vi.fn();
    render(<Avatar name="Test" draggable onDragStart={onDragStart} />);

    const avatar = screen.getByText("T").parentElement;
    fireEvent.dragStart(avatar!);

    expect(onDragStart).toHaveBeenCalled();
  });

  it("applies custom className", () => {
    render(<Avatar name="Test" className="custom-avatar" />);

    const avatar = screen.getByText("T").closest(".custom-avatar");
    expect(avatar).toBeInTheDocument();
  });

  it("renders with tooltip", () => {
    render(<Avatar name="John Doe" showTooltip />);

    const avatar = screen.getByText("JD").parentElement;
    expect(avatar).toHaveAttribute("title", "John Doe");
  });

  it("handles loading state", () => {
    render(<Avatar loading />);

    const loader = screen.getByRole("img", { hidden: true });
    expect(loader).toHaveClass("animate-pulse");
  });

  it("renders with custom border", () => {
    render(<Avatar name="Test" border="border-2 border-blue-500" />);

    const avatar = screen.getByText("T").parentElement;
    expect(avatar).toHaveClass("border-2", "border-blue-500");
  });

  it("handles hover effects", () => {
    render(<Avatar name="Test" hover />);

    const avatar = screen.getByText("T").parentElement;
    expect(avatar).toHaveClass("hover:scale-110", "transition-transform");
  });

  it("renders with verified badge", () => {
    render(<Avatar name="Test" verified />);

    const verifiedBadge = screen.getByTestId("verified-badge");
    expect(verifiedBadge).toBeInTheDocument();
  });

  it("handles keyboard navigation", () => {
    const onClick = vi.fn();
    render(<Avatar name="Test" onClick={onClick} />);

    const avatar = screen.getByText("T").parentElement;
    avatar?.focus();
    fireEvent.keyDown(avatar!, { key: "Enter" });

    expect(onClick).toHaveBeenCalled();
  });

  it("supports multiple images for fallback", () => {
    render(
      <Avatar
        src={["invalid1.jpg", "invalid2.jpg", "valid.jpg"]}
        name="Test"
      />,
    );

    const images = screen.getAllByRole("img");
    expect(images).toHaveLength(1);
  });

  it("renders placeholder when no name or image", () => {
    render(<Avatar />);

    const placeholder = screen.getByTestId("avatar-placeholder");
    expect(placeholder).toBeInTheDocument();
  });

  it("applies accessibility attributes", () => {
    render(<Avatar name="Test User" role="button" aria-label="User profile" />);

    const avatar = screen.getByText("TU").parentElement;
    expect(avatar).toHaveAttribute("role", "button");
    expect(avatar).toHaveAttribute("aria-label", "User profile");
  });

  it("handles animation classes", () => {
    render(<Avatar name="Test" animate />);

    const avatar = screen.getByText("T").parentElement;
    expect(avatar).toHaveClass("animate-pulse");
  });

  it("renders with custom size", () => {
    render(<Avatar name="Test" customSize="w-20 h-20" />);

    const avatar = screen.getByText("T").parentElement;
    expect(avatar).toHaveClass("w-20", "h-20");
  });

  it("handles right-to-left text", () => {
    render(<Avatar name="أحمد محمد" />);

    expect(screen.getByText("أم")).toBeInTheDocument();
  });

  it("renders group with custom spacing", () => {
    render(
      <Avatar.Group spacing="-space-x-4">
        <Avatar name="User 1" />
        <Avatar name="User 2" />
      </Avatar.Group>,
    );

    const group = screen.getByTestId("avatar-group");
    expect(group).toHaveClass("-space-x-4");
  });

  it("handles image loading states", () => {
    render(<Avatar src="loading.jpg" name="Test" />);

    const image = screen.getByRole("img");
    expect(image).toHaveAttribute("loading", "lazy");
  });

  it("renders with gradient background", () => {
    render(<Avatar name="Test" gradient="from-blue-400 to-purple-500" />);

    const avatar = screen.getByText("T").parentElement;
    expect(avatar).toHaveClass(
      "bg-gradient-to-br",
      "from-blue-400",
      "to-purple-500",
    );
  });

  it("handles initials generation edge cases", () => {
    const { rerender } = render(<Avatar name="" />);
    expect(screen.getByTestId("avatar-placeholder")).toBeInTheDocument();

    rerender(<Avatar name="   " />);
    expect(screen.getByTestId("avatar-placeholder")).toBeInTheDocument();

    rerender(<Avatar name="A" />);
    expect(screen.getByText("A")).toBeInTheDocument();
  });

  it("handles custom alt text for images", () => {
    render(<Avatar src="test.jpg" alt="Custom alt text" />);

    const image = screen.getByRole("img");
    expect(image).toHaveAttribute("alt", "Custom alt text");
  });
});
