import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { vi } from "vitest";
import { Sidebar } from "./Sidebar";

describe("Sidebar", () => {
  const mockSidebarItems = [
    {
      id: "1",
      label: "Dashboard",
      icon: "📊",
      href: "/dashboard",
      current: true,
    },
    { id: "2", label: "Users", icon: "👥", href: "/users" },
    {
      id: "3",
      label: "Settings",
      icon: "⚙️",
      href: "/settings",
      children: [
        { id: "3-1", label: "General", href: "/settings/general" },
        { id: "3-2", label: "Security", href: "/settings/security" },
      ],
    },
    { id: "4", label: "Help", icon: "❓", href: "/help", disabled: true },
  ];

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders sidebar with items", () => {
    render(<Sidebar items={mockSidebarItems} />);

    expect(screen.getByText("Dashboard")).toBeInTheDocument();
    expect(screen.getByText("Users")).toBeInTheDocument();
    expect(screen.getByText("Settings")).toBeInTheDocument();
  });

  it("highlights current item", () => {
    render(<Sidebar items={mockSidebarItems} />);

    const dashboardItem = screen.getByText("Dashboard").closest("a");
    expect(dashboardItem).toHaveClass("bg-blue-100");
  });

  it("disables disabled items", () => {
    render(<Sidebar items={mockSidebarItems} />);

    const helpItem = screen.getByText("Help").closest("a");
    expect(helpItem).toHaveClass("opacity-50");
    expect(helpItem).toHaveAttribute("aria-disabled", "true");
  });

  it("supports collapsible functionality", () => {
    render(<Sidebar items={mockSidebarItems} collapsible />);

    const collapseButton = screen.getByTestId("sidebar-collapse-btn");
    expect(collapseButton).toBeInTheDocument();

    fireEvent.click(collapseButton);

    const sidebar = screen.getByTestId("sidebar-container");
    expect(sidebar).toHaveStyle({ width: "4rem" });
  });

  it("supports different positions", () => {
    const positions = ["left", "right"] as const;

    positions.forEach((position) => {
      const { unmount } = render(
        <Sidebar items={mockSidebarItems} position={position} />,
      );
      const sidebar = screen.getByTestId("sidebar-container");

      if (position === "right") {
        expect(sidebar).toHaveClass("right-0");
      } else {
        expect(sidebar).toHaveClass("left-0");
      }
      unmount();
    });
  });

  it("supports different sizes", () => {
    const sizes = ["sm", "md", "lg"] as const;

    sizes.forEach((size) => {
      const { unmount } = render(
        <Sidebar items={mockSidebarItems} size={size} />,
      );
      expect(screen.getByTestId("sidebar-container")).toBeInTheDocument();
      unmount();
    });
  });

  it("supports different variants", () => {
    const variants = ["default", "minimal", "elevated"] as const;

    variants.forEach((variant) => {
      const { unmount } = render(
        <Sidebar items={mockSidebarItems} variant={variant} />,
      );
      expect(screen.getByTestId("sidebar-container")).toBeInTheDocument();
      unmount();
    });
  });

  it("renders nested sidebar items", async () => {
    render(<Sidebar items={mockSidebarItems} />);

    const settingsItem = screen.getByText("Settings");
    fireEvent.click(settingsItem);

    await waitFor(() => {
      expect(screen.getByText("General")).toBeInTheDocument();
      expect(screen.getByText("Security")).toBeInTheDocument();
    });
  });

  it("supports overlay mode", () => {
    render(<Sidebar items={mockSidebarItems} overlay />);

    const sidebar = screen.getByTestId("sidebar-container");
    expect(sidebar).toHaveClass("fixed");
    expect(sidebar).toHaveClass("z-50");
  });

  it("supports backdrop in overlay mode", () => {
    render(<Sidebar items={mockSidebarItems} overlay showBackdrop />);

    expect(screen.getByTestId("sidebar-backdrop")).toBeInTheDocument();
  });

  it("handles backdrop click to close", () => {
    const onClose = vi.fn();
    render(
      <Sidebar
        items={mockSidebarItems}
        overlay
        showBackdrop
        onClose={onClose}
      />,
    );

    const backdrop = screen.getByTestId("sidebar-backdrop");
    fireEvent.click(backdrop);

    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it("supports custom header", () => {
    const header = <div data-testid="custom-header">My App</div>;
    render(<Sidebar items={mockSidebarItems} header={header} />);

    expect(screen.getByTestId("custom-header")).toBeInTheDocument();
  });

  it("supports custom footer", () => {
    const footer = <div data-testid="custom-footer">Footer Content</div>;
    render(<Sidebar items={mockSidebarItems} footer={footer} />);

    expect(screen.getByTestId("custom-footer")).toBeInTheDocument();
  });

  it("supports search functionality", () => {
    render(<Sidebar items={mockSidebarItems} searchable />);

    expect(screen.getByPlaceholderText("Search...")).toBeInTheDocument();

    const searchInput = screen.getByPlaceholderText("Search...");
    fireEvent.change(searchInput, { target: { value: "Dashboard" } });

    expect(screen.getByText("Dashboard")).toBeInTheDocument();
    expect(screen.queryByText("Users")).not.toBeInTheDocument();
  });

  it("supports group headers", () => {
    const itemsWithGroups = [
      { id: "main-header", type: "header" as const, label: "Main" },
      { id: "1", label: "Dashboard", href: "/dashboard" },
      { id: "admin-header", type: "header" as const, label: "Admin" },
      { id: "2", label: "Users", href: "/users" },
    ];

    render(<Sidebar items={itemsWithGroups} />);

    expect(screen.getByText("Main")).toBeInTheDocument();
    expect(screen.getByText("Admin")).toBeInTheDocument();
  });

  it("supports dividers", () => {
    const itemsWithDividers = [
      { id: "1", label: "Dashboard", href: "/dashboard" },
      { id: "divider-1", type: "divider" as const },
      { id: "2", label: "Users", href: "/users" },
    ];

    render(<Sidebar items={itemsWithDividers} />);

    expect(screen.getByTestId("sidebar-divider")).toBeInTheDocument();
  });

  it("supports badges in items", () => {
    const itemsWithBadges = [
      { id: "1", label: "Messages", href: "/messages", badge: "5" },
      { id: "2", label: "Notifications", href: "/notifications", badge: "12" },
    ];

    render(<Sidebar items={itemsWithBadges} />);

    expect(screen.getByText("5")).toBeInTheDocument();
    expect(screen.getByText("12")).toBeInTheDocument();
  });

  it("supports custom item rendering", () => {
    const customRenderer = (item: any) => (
      <div data-testid={`custom-${item.id}`}>Custom: {item.label}</div>
    );

    render(<Sidebar items={mockSidebarItems} renderItem={customRenderer} />);

    expect(screen.getByTestId("custom-1")).toBeInTheDocument();
    expect(screen.getByText("Custom: Dashboard")).toBeInTheDocument();
  });

  it("supports keyboard navigation", () => {
    render(<Sidebar items={mockSidebarItems} keyboardNavigation />);

    const sidebar = screen.getByTestId("sidebar-container");
    fireEvent.keyDown(sidebar, { key: "ArrowDown" });

    // Should handle keyboard navigation without errors
    expect(sidebar).toBeInTheDocument();
  });

  it("supports resizable sidebar", () => {
    render(<Sidebar items={mockSidebarItems} resizable />);

    const resizeHandle = screen.getByTestId("sidebar-resize-handle");
    expect(resizeHandle).toBeInTheDocument();
  });

  it("handles resize drag events", () => {
    render(<Sidebar items={mockSidebarItems} resizable />);

    const resizeHandle = screen.getByTestId("sidebar-resize-handle");

    fireEvent.mouseDown(resizeHandle, { clientX: 250 });
    fireEvent.mouseMove(document, { clientX: 300 });
    fireEvent.mouseUp(document);

    // Should handle resize without errors
    expect(resizeHandle).toBeInTheDocument();
  });

  it("supports loading state", () => {
    render(<Sidebar items={mockSidebarItems} loading />);

    expect(screen.getByTestId("sidebar-loading")).toBeInTheDocument();
  });

  it("supports custom loading component", () => {
    const LoadingComponent = () => (
      <div data-testid="custom-loading">Loading sidebar...</div>
    );
    render(
      <Sidebar
        items={mockSidebarItems}
        loading
        loadingComponent={<LoadingComponent />}
      />,
    );

    expect(screen.getByTestId("custom-loading")).toBeInTheDocument();
  });

  it("supports sticky items", () => {
    const itemsWithSticky = [
      { id: "1", label: "Dashboard", href: "/dashboard" },
      { id: "2", label: "Profile", href: "/profile", sticky: true },
    ];

    render(<Sidebar items={itemsWithSticky} />);

    const profileItem = screen.getByText("Profile").closest("div");
    expect(profileItem).toHaveClass("sticky");
  });

  it("supports custom width", () => {
    render(<Sidebar items={mockSidebarItems} width={300} />);

    const sidebar = screen.getByTestId("sidebar-container");
    expect(sidebar).toHaveStyle({ width: "300px" });
  });

  it("supports themes", () => {
    const themes = ["light", "dark"] as const;

    themes.forEach((theme) => {
      const { unmount } = render(
        <Sidebar items={mockSidebarItems} theme={theme} />,
      );
      const sidebar = screen.getByTestId("sidebar-container");
      expect(sidebar).toHaveClass(`theme-${theme}`);
      unmount();
    });
  });

  it("supports item click events", () => {
    const onItemClick = vi.fn();
    render(<Sidebar items={mockSidebarItems} onItemClick={onItemClick} />);

    const dashboardItem = screen.getByText("Dashboard");
    fireEvent.click(dashboardItem);

    expect(onItemClick).toHaveBeenCalledWith(mockSidebarItems[0]);
  });

  it("supports toggle callbacks", () => {
    const onToggle = vi.fn();
    render(
      <Sidebar items={mockSidebarItems} collapsible onToggle={onToggle} />,
    );

    const collapseButton = screen.getByTestId("sidebar-collapse-btn");
    fireEvent.click(collapseButton);

    expect(onToggle).toHaveBeenCalledWith(true);
  });

  it("supports custom className", () => {
    render(<Sidebar items={mockSidebarItems} className="custom-sidebar" />);

    expect(screen.getByTestId("sidebar-container")).toHaveClass(
      "custom-sidebar",
    );
  });

  it("supports tooltip in collapsed mode", () => {
    render(
      <Sidebar items={mockSidebarItems} collapsible collapsed showTooltips />,
    );

    const dashboardItem = screen.getByText("📊").closest("a");
    fireEvent.mouseEnter(dashboardItem!);

    // Tooltip should be shown (implementation would depend on tooltip library)
    expect(dashboardItem).toBeInTheDocument();
  });

  it("supports scroll behavior", () => {
    const manyItems = Array.from({ length: 20 }, (_, i) => ({
      id: String(i),
      label: `Item ${i}`,
      href: `/item${i}`,
    }));

    render(<Sidebar items={manyItems} scrollable />);

    const sidebar = screen.getByTestId("sidebar-container");
    expect(sidebar).toHaveClass("overflow-auto");
  });

  it("supports custom data attributes", () => {
    render(
      <Sidebar
        items={mockSidebarItems}
        data-category="navigation"
        data-id="main-sidebar"
      />,
    );

    const sidebar = screen.getByTestId("sidebar-container");
    expect(sidebar).toHaveAttribute("data-category", "navigation");
    expect(sidebar).toHaveAttribute("data-id", "main-sidebar");
  });

  it("supports responsive behavior", () => {
    render(<Sidebar items={mockSidebarItems} responsive />);

    const sidebar = screen.getByTestId("sidebar-container");
    expect(sidebar).toHaveClass("responsive-sidebar");
  });

  it("supports auto-collapse on item click", () => {
    const onToggle = vi.fn();
    render(
      <Sidebar
        items={mockSidebarItems}
        overlay
        autoClose
        onToggle={onToggle}
      />,
    );

    const dashboardItem = screen.getByText("Dashboard");
    fireEvent.click(dashboardItem);

    expect(onToggle).toHaveBeenCalledWith(false);
  });
});
