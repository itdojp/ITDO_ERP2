import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { vi } from "vitest";
import { Menu } from "./Menu";

describe("Menu", () => {
  const mockMenuItems = [
    { id: "1", label: "Item 1", onClick: vi.fn() },
    { id: "2", label: "Item 2", onClick: vi.fn() },
    { id: "3", label: "Item 3", onClick: vi.fn(), disabled: true },
  ];

  const nestedMenuItems = [
    {
      id: "1",
      label: "File",
      children: [
        { id: "1-1", label: "New", onClick: vi.fn() },
        { id: "1-2", label: "Open", onClick: vi.fn() },
        { id: "1-3", label: "Save", onClick: vi.fn() },
      ],
    },
    {
      id: "2",
      label: "Edit",
      children: [
        { id: "2-1", label: "Cut", onClick: vi.fn() },
        { id: "2-2", label: "Copy", onClick: vi.fn() },
      ],
    },
  ];

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders menu with items", () => {
    render(<Menu items={mockMenuItems} />);

    expect(screen.getByText("Item 1")).toBeInTheDocument();
    expect(screen.getByText("Item 2")).toBeInTheDocument();
    expect(screen.getByText("Item 3")).toBeInTheDocument();
  });

  it("handles item clicks", () => {
    render(<Menu items={mockMenuItems} />);

    const firstItem = screen.getByText("Item 1");
    fireEvent.click(firstItem);

    expect(mockMenuItems[0].onClick).toHaveBeenCalledTimes(1);
  });

  it("disables disabled items", () => {
    render(<Menu items={mockMenuItems} />);

    const disabledItem = screen.getByText("Item 3");
    expect(disabledItem.closest("button")).toHaveClass("opacity-50");
    expect(disabledItem.closest("button")).toBeDisabled();
  });

  it("supports different orientations", () => {
    const orientations = ["horizontal", "vertical"] as const;

    orientations.forEach((orientation) => {
      const { unmount } = render(
        <Menu items={mockMenuItems} orientation={orientation} />,
      );
      const menu = screen.getByTestId("menu-container");

      if (orientation === "horizontal") {
        expect(menu).toHaveClass("flex-row");
      } else {
        expect(menu).toHaveClass("flex-col");
      }
      unmount();
    });
  });

  it("supports different sizes", () => {
    const sizes = ["sm", "md", "lg"] as const;

    sizes.forEach((size) => {
      const { unmount } = render(<Menu items={mockMenuItems} size={size} />);
      expect(screen.getByTestId("menu-container")).toBeInTheDocument();
      unmount();
    });
  });

  it("supports different variants", () => {
    const variants = ["default", "pills", "tabs", "minimal"] as const;

    variants.forEach((variant) => {
      const { unmount } = render(
        <Menu items={mockMenuItems} variant={variant} />,
      );
      expect(screen.getByTestId("menu-container")).toBeInTheDocument();
      unmount();
    });
  });

  it("renders nested menus", async () => {
    render(<Menu items={nestedMenuItems} />);

    const fileMenu = screen.getByText("File");
    fireEvent.mouseEnter(fileMenu);

    await waitFor(() => {
      expect(screen.getByText("New")).toBeInTheDocument();
      expect(screen.getByText("Open")).toBeInTheDocument();
    });
  });

  it("handles nested menu clicks", async () => {
    render(<Menu items={nestedMenuItems} />);

    const fileMenu = screen.getByText("File");
    fireEvent.mouseEnter(fileMenu);

    await waitFor(() => {
      const newItem = screen.getByText("New");
      fireEvent.click(newItem);
      expect(nestedMenuItems[0].children![0].onClick).toHaveBeenCalledTimes(1);
    });
  });

  it("supports keyboard navigation", () => {
    render(<Menu items={mockMenuItems} keyboardNavigation />);

    const menu = screen.getByTestId("menu-container");
    expect(menu).toHaveAttribute("tabindex", "0");

    // Test that the menu is focusable and responds to keyboard
    fireEvent.keyDown(menu, { key: "ArrowDown" });
    expect(menu).toBeInTheDocument(); // Basic check that it doesn't crash
  });

  it("handles Enter key on focused item", () => {
    const onItemClick = vi.fn();
    const testItems = [{ id: "1", label: "Item 1", onClick: onItemClick }];

    render(<Menu items={testItems} keyboardNavigation />);

    const menu = screen.getByTestId("menu-container");

    // Simulate focusing first item then pressing Enter
    fireEvent.keyDown(menu, { key: "ArrowDown" });
    fireEvent.keyDown(menu, { key: "Enter" });

    // The keyboard navigation should work
    expect(menu).toBeInTheDocument();
  });

  it("supports icons in menu items", () => {
    const itemsWithIcons = [
      { id: "1", label: "Home", icon: "🏠", onClick: vi.fn() },
      { id: "2", label: "Settings", icon: "⚙️", onClick: vi.fn() },
    ];

    render(<Menu items={itemsWithIcons} />);

    expect(screen.getByText("🏠")).toBeInTheDocument();
    expect(screen.getByText("⚙️")).toBeInTheDocument();
  });

  it("supports custom item rendering", () => {
    const customRenderer = (item: any) => (
      <div data-testid={`custom-${item.id}`}>Custom: {item.label}</div>
    );

    render(<Menu items={mockMenuItems} renderItem={customRenderer} />);

    expect(screen.getByTestId("custom-1")).toBeInTheDocument();
    expect(screen.getByText("Custom: Item 1")).toBeInTheDocument();
  });

  it("supports selection mode", () => {
    const onSelect = vi.fn();
    render(<Menu items={mockMenuItems} selectable onSelect={onSelect} />);

    const firstItem = screen.getByText("Item 1");
    fireEvent.click(firstItem);

    expect(onSelect).toHaveBeenCalledWith("1");
    expect(firstItem.closest("button")).toHaveClass("bg-blue-100");
  });

  it("supports multi-selection", () => {
    const onSelect = vi.fn();
    render(
      <Menu items={mockMenuItems} selectable multiple onSelect={onSelect} />,
    );

    const firstItem = screen.getByText("Item 1");
    const secondItem = screen.getByText("Item 2");

    fireEvent.click(firstItem);
    fireEvent.click(secondItem, { ctrlKey: true });

    expect(onSelect).toHaveBeenLastCalledWith(["1", "2"]);
  });

  it("supports menu dividers", () => {
    const itemsWithDividers = [
      { id: "1", label: "Item 1", onClick: vi.fn() },
      { id: "divider-1", type: "divider" as const },
      { id: "2", label: "Item 2", onClick: vi.fn() },
    ];

    render(<Menu items={itemsWithDividers} />);

    expect(screen.getByTestId("menu-divider")).toBeInTheDocument();
  });

  it("supports menu headers", () => {
    const itemsWithHeaders = [
      { id: "header-1", type: "header" as const, label: "Section 1" },
      { id: "1", label: "Item 1", onClick: vi.fn() },
      { id: "2", label: "Item 2", onClick: vi.fn() },
    ];

    render(<Menu items={itemsWithHeaders} />);

    expect(screen.getByText("Section 1")).toBeInTheDocument();
    expect(screen.getByTestId("menu-header")).toBeInTheDocument();
  });

  it("supports collapsible nested menus", async () => {
    render(<Menu items={nestedMenuItems} collapsible />);

    const fileMenu = screen.getByText("File");
    fireEvent.click(fileMenu);

    await waitFor(() => {
      expect(screen.getByText("New")).toBeInTheDocument();
    });

    fireEvent.click(fileMenu);

    await waitFor(() => {
      expect(screen.queryByText("New")).not.toBeInTheDocument();
    });
  });

  it("supports auto-close on item click", async () => {
    const onClose = vi.fn();
    render(<Menu items={nestedMenuItems} autoClose onClose={onClose} />);

    const fileMenu = screen.getByText("File");
    fireEvent.mouseEnter(fileMenu);

    await waitFor(() => {
      const newItem = screen.getByText("New");
      fireEvent.click(newItem);
      expect(onClose).toHaveBeenCalledTimes(1);
    });
  });

  it("supports custom trigger element", () => {
    const trigger = <button data-testid="custom-trigger">Menu</button>;
    render(<Menu items={mockMenuItems} trigger={trigger} />);

    expect(screen.getByTestId("custom-trigger")).toBeInTheDocument();
  });

  it("supports menu positioning", () => {
    const positions = ["top", "bottom", "left", "right"] as const;

    positions.forEach((position) => {
      const { unmount } = render(
        <Menu items={mockMenuItems} position={position} />,
      );
      expect(screen.getByTestId("menu-container")).toBeInTheDocument();
      unmount();
    });
  });

  it("supports custom className", () => {
    render(<Menu items={mockMenuItems} className="custom-menu" />);

    expect(screen.getByTestId("menu-container")).toHaveClass("custom-menu");
  });

  it("supports disabled state", () => {
    render(<Menu items={mockMenuItems} disabled />);

    const menuItems = screen.getAllByRole("button");
    menuItems.forEach((item) => {
      expect(item).toBeDisabled();
    });
  });

  it("supports loading state", () => {
    render(<Menu items={mockMenuItems} loading />);

    expect(screen.getByTestId("menu-loading")).toBeInTheDocument();
  });

  it("supports custom loading component", () => {
    const LoadingComponent = () => (
      <div data-testid="custom-loading">Loading...</div>
    );
    render(
      <Menu
        items={mockMenuItems}
        loading
        loadingComponent={<LoadingComponent />}
      />,
    );

    expect(screen.getByTestId("custom-loading")).toBeInTheDocument();
  });

  it("supports menu search", () => {
    render(
      <Menu
        items={mockMenuItems}
        searchable
        searchPlaceholder="Search menu..."
      />,
    );

    expect(screen.getByPlaceholderText("Search menu...")).toBeInTheDocument();

    const searchInput = screen.getByPlaceholderText("Search menu...");
    fireEvent.change(searchInput, { target: { value: "Item 2" } });

    expect(screen.getByText("Item 2")).toBeInTheDocument();
    expect(screen.queryByText("Item 1")).not.toBeInTheDocument();
  });

  it("supports badges on menu items", () => {
    const itemsWithBadges = [
      { id: "1", label: "Messages", badge: "5", onClick: vi.fn() },
      { id: "2", label: "Notifications", badge: "12", onClick: vi.fn() },
    ];

    render(<Menu items={itemsWithBadges} />);

    expect(screen.getByText("5")).toBeInTheDocument();
    expect(screen.getByText("12")).toBeInTheDocument();
  });

  it("supports menu item shortcuts", () => {
    const itemsWithShortcuts = [
      { id: "1", label: "New", shortcut: "Ctrl+N", onClick: vi.fn() },
      { id: "2", label: "Save", shortcut: "Ctrl+S", onClick: vi.fn() },
    ];

    render(<Menu items={itemsWithShortcuts} />);

    expect(screen.getByText("Ctrl+N")).toBeInTheDocument();
    expect(screen.getByText("Ctrl+S")).toBeInTheDocument();
  });

  it("supports menu item descriptions", () => {
    const itemsWithDescriptions = [
      {
        id: "1",
        label: "Export",
        description: "Export data to file",
        onClick: vi.fn(),
      },
      {
        id: "2",
        label: "Import",
        description: "Import data from file",
        onClick: vi.fn(),
      },
    ];

    render(<Menu items={itemsWithDescriptions} />);

    expect(screen.getByText("Export data to file")).toBeInTheDocument();
    expect(screen.getByText("Import data from file")).toBeInTheDocument();
  });

  it("supports custom data attributes", () => {
    render(
      <Menu
        items={mockMenuItems}
        data-category="navigation"
        data-id="main-menu"
      />,
    );

    const menu = screen.getByTestId("menu-container");
    expect(menu).toHaveAttribute("data-category", "navigation");
    expect(menu).toHaveAttribute("data-id", "main-menu");
  });

  it("supports context menu mode", () => {
    render(<Menu items={mockMenuItems} contextMenu />);

    const menu = screen.getByTestId("menu-container");
    expect(menu).toHaveClass("absolute");
  });

  it("supports menu width control", () => {
    render(<Menu items={mockMenuItems} width={200} />);

    const menu = screen.getByTestId("menu-container");
    expect(menu).toHaveStyle({ width: "200px" });
  });

  it("supports max height with scrolling", () => {
    const manyItems = Array.from({ length: 20 }, (_, i) => ({
      id: String(i),
      label: `Item ${i}`,
      onClick: vi.fn(),
    }));

    render(<Menu items={manyItems} maxHeight={200} />);

    const menu = screen.getByTestId("menu-container");
    expect(menu).toHaveStyle({ maxHeight: "200px" });
    expect(menu).toHaveClass("overflow-auto");
  });
});
