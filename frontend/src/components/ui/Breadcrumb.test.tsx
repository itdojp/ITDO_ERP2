import { render, fireEvent, screen } from "@testing-library/react";
import { Breadcrumb, BreadcrumbItem } from "./Breadcrumb";

describe("Breadcrumb", () => {
  const mockItems: BreadcrumbItem[] = [
    { id: "home", label: "Home", href: "/" },
    { id: "products", label: "Products", href: "/products" },
    { id: "category", label: "Electronics", href: "/products/electronics" },
    { id: "current", label: "Laptops", current: true },
  ];

  const defaultProps = {
    items: mockItems,
  };

  it("renders all breadcrumb items", () => {
    render(<Breadcrumb {...defaultProps} />);

    expect(screen.getByText("Home")).toBeInTheDocument();
    expect(screen.getByText("Products")).toBeInTheDocument();
    expect(screen.getByText("Electronics")).toBeInTheDocument();
    expect(screen.getByText("Laptops")).toBeInTheDocument();
  });

  it("renders separators between items", () => {
    render(<Breadcrumb {...defaultProps} />);

    const separators = screen.getAllByRole("img", { hidden: true });
    expect(separators).toHaveLength(3); // 4 items = 3 separators
  });

  it("uses custom separator when provided", () => {
    render(<Breadcrumb {...defaultProps} separator={<span>/</span>} />);

    expect(screen.getAllByText("/")).toHaveLength(3);
  });

  it("marks current item with aria-current", () => {
    render(<Breadcrumb {...defaultProps} />);

    const currentItem = screen.getByText("Laptops");
    expect(currentItem).toHaveAttribute("aria-current", "page");
  });

  it("marks last item as current when no current is specified", () => {
    const itemsWithoutCurrent = mockItems.map((item) => ({
      ...item,
      current: undefined,
    }));
    render(<Breadcrumb items={itemsWithoutCurrent} />);

    const lastItem = screen.getByText("Laptops");
    expect(lastItem).toHaveAttribute("aria-current", "page");
  });

  it("renders items as links when href is provided and not current", () => {
    render(<Breadcrumb {...defaultProps} />);

    const homeLink = screen.getByRole("link", { name: /home/i });
    expect(homeLink).toHaveAttribute("href", "/");

    const productsLink = screen.getByRole("link", { name: /products/i });
    expect(productsLink).toHaveAttribute("href", "/products");
  });

  it("does not render current item as link", () => {
    render(<Breadcrumb {...defaultProps} />);

    const currentItem = screen.getByText("Laptops");
    expect(currentItem.tagName).toBe("SPAN");
    expect(currentItem).not.toHaveAttribute("href");
  });

  it("calls onItemClick when item is clicked", () => {
    const onItemClick = jest.fn();
    render(<Breadcrumb {...defaultProps} onItemClick={onItemClick} />);

    fireEvent.click(screen.getByText("Home"));

    expect(onItemClick).toHaveBeenCalledWith(
      expect.objectContaining({ id: "home", label: "Home" }),
    );
  });

  it("calls item onClick when provided", () => {
    const itemOnClick = jest.fn();
    const itemsWithOnClick = [
      { ...mockItems[0], onClick: itemOnClick },
      ...mockItems.slice(1),
    ];

    render(<Breadcrumb items={itemsWithOnClick} />);

    fireEvent.click(screen.getByText("Home"));

    expect(itemOnClick).toHaveBeenCalledTimes(1);
  });

  it("does not call onClick for disabled items", () => {
    const onItemClick = jest.fn();
    const itemsWithDisabled = [
      { ...mockItems[0], disabled: true },
      ...mockItems.slice(1),
    ];

    render(<Breadcrumb items={itemsWithDisabled} onItemClick={onItemClick} />);

    fireEvent.click(screen.getByText("Home"));

    expect(onItemClick).not.toHaveBeenCalled();
  });

  it("does not call onClick for current items", () => {
    const onItemClick = jest.fn();
    render(<Breadcrumb {...defaultProps} onItemClick={onItemClick} />);

    fireEvent.click(screen.getByText("Laptops"));

    expect(onItemClick).not.toHaveBeenCalled();
  });

  it("handles keyboard navigation with Enter key", () => {
    const onItemClick = jest.fn();
    render(<Breadcrumb {...defaultProps} onItemClick={onItemClick} />);

    const homeItem = screen.getByText("Home");
    fireEvent.keyDown(homeItem, { key: "Enter" });

    expect(onItemClick).toHaveBeenCalledWith(
      expect.objectContaining({ id: "home", label: "Home" }),
    );
  });

  it("handles keyboard navigation with Space key", () => {
    const onItemClick = jest.fn();
    render(<Breadcrumb {...defaultProps} onItemClick={onItemClick} />);

    const homeItem = screen.getByText("Home");
    fireEvent.keyDown(homeItem, { key: " " });

    expect(onItemClick).toHaveBeenCalledWith(
      expect.objectContaining({ id: "home", label: "Home" }),
    );
  });

  it("displays item icons when provided", () => {
    const itemsWithIcons: BreadcrumbItem[] = [
      {
        id: "home",
        label: "Home",
        icon: <span data-testid="home-icon">🏠</span>,
      },
    ];

    render(<Breadcrumb items={itemsWithIcons} />);

    expect(screen.getByTestId("home-icon")).toBeInTheDocument();
  });

  it("applies default variant classes", () => {
    render(<Breadcrumb {...defaultProps} variant="default" />);

    const currentItem = screen.getByText("Laptops");
    expect(currentItem).toHaveClass("text-gray-900", "font-medium");
  });

  it("applies underline variant classes", () => {
    render(<Breadcrumb {...defaultProps} variant="underline" />);

    const currentItem = screen.getByText("Laptops");
    expect(currentItem).toHaveClass(
      "text-blue-600",
      "border-b-2",
      "border-blue-600",
    );
  });

  it("applies pills variant classes", () => {
    render(<Breadcrumb {...defaultProps} variant="pills" />);

    const currentItem = screen.getByText("Laptops");
    expect(currentItem).toHaveClass(
      "rounded-full",
      "bg-blue-100",
      "text-blue-700",
    );
  });

  it("applies small size classes", () => {
    render(<Breadcrumb {...defaultProps} size="sm" />);

    const item = screen.getByText("Home");
    expect(item).toHaveClass("text-xs", "px-2", "py-1");
  });

  it("applies medium size classes", () => {
    render(<Breadcrumb {...defaultProps} size="md" />);

    const item = screen.getByText("Home");
    expect(item).toHaveClass("text-sm", "px-3", "py-1.5");
  });

  it("applies large size classes", () => {
    render(<Breadcrumb {...defaultProps} size="lg" />);

    const item = screen.getByText("Home");
    expect(item).toHaveClass("text-base", "px-4", "py-2");
  });

  it("applies custom className", () => {
    render(<Breadcrumb {...defaultProps} className="custom-breadcrumb" />);

    const nav = screen.getByRole("navigation");
    expect(nav).toHaveClass("custom-breadcrumb");
  });

  it("applies custom itemClassName", () => {
    render(<Breadcrumb {...defaultProps} itemClassName="custom-item" />);

    const item = screen.getByText("Home");
    expect(item).toHaveClass("custom-item");
  });

  it("applies custom linkClassName", () => {
    render(<Breadcrumb {...defaultProps} linkClassName="custom-link" />);

    const link = screen.getByRole("link", { name: /home/i });
    expect(link).toHaveClass("custom-link");
  });

  it("applies custom currentItemClassName", () => {
    render(
      <Breadcrumb {...defaultProps} currentItemClassName="custom-current" />,
    );

    const currentItem = screen.getByText("Laptops");
    expect(currentItem).toHaveClass("custom-current");
  });

  it("applies custom separatorClassName", () => {
    render(
      <Breadcrumb {...defaultProps} separatorClassName="custom-separator" />,
    );

    const separators = document.querySelectorAll(".custom-separator");
    expect(separators.length).toBeGreaterThan(0);
  });

  it("shows home icon when showHome is true", () => {
    render(<Breadcrumb {...defaultProps} showHome={true} />);

    const homeIcons = screen.getAllByRole("img", { hidden: true });
    expect(homeIcons.length).toBeGreaterThan(3); // Original separators plus home icon
  });

  it("uses custom home icon when provided", () => {
    render(
      <Breadcrumb
        {...defaultProps}
        showHome={true}
        homeIcon={<span data-testid="custom-home">🏠</span>}
      />,
    );

    expect(screen.getByTestId("custom-home")).toBeInTheDocument();
  });

  it("truncates items when maxItems is specified", () => {
    render(<Breadcrumb {...defaultProps} maxItems={3} truncate={true} />);

    // Should show ellipsis for truncation
    expect(screen.getByText("...")).toBeInTheDocument();
  });

  it("truncates long labels when truncate is true", () => {
    const itemsWithLongLabels: BreadcrumbItem[] = [
      { id: "1", label: "Very Long Label That Should Be Truncated" },
    ];

    render(<Breadcrumb items={itemsWithLongLabels} truncate={true} />);

    const item = screen.getByText("Very Long Label That Should Be Truncated");
    expect(item).toHaveClass("truncate", "max-w-[8rem]");
  });

  it("handles disabled state properly", () => {
    const itemsWithDisabled: BreadcrumbItem[] = [
      { id: "1", label: "Disabled", disabled: true },
    ];

    render(<Breadcrumb items={itemsWithDisabled} />);

    const disabledItem = screen.getByText("Disabled");
    expect(disabledItem).toHaveClass("opacity-50", "cursor-not-allowed");
    expect(disabledItem).toHaveAttribute("aria-disabled", "true");
    expect(disabledItem).toHaveAttribute("tabindex", "-1");
  });

  it("sets proper ARIA attributes", () => {
    render(<Breadcrumb {...defaultProps} />);

    const nav = screen.getByRole("navigation");
    expect(nav).toHaveAttribute("aria-label", "Breadcrumb");

    const links = screen.getAllByRole("link");
    links.forEach((link) => {
      expect(link).toHaveAttribute("tabindex", "0");
    });
  });

  it("prevents default behavior for items with onClick", () => {
    const preventDefault = jest.fn();
    const itemOnClick = jest.fn();
    const itemsWithOnClick = [
      { ...mockItems[0], onClick: itemOnClick },
      ...mockItems.slice(1),
    ];

    render(<Breadcrumb items={itemsWithOnClick} />);

    const homeItem = screen.getByText("Home");
    fireEvent.click(homeItem, { preventDefault });

    expect(itemOnClick).toHaveBeenCalledTimes(1);
  });

  it("renders without items", () => {
    render(<Breadcrumb items={[]} />);

    const nav = screen.getByRole("navigation");
    expect(nav).toBeInTheDocument();
  });

  it("handles ellipsis position start", () => {
    const manyItems: BreadcrumbItem[] = [
      { id: "1", label: "Item 1" },
      { id: "2", label: "Item 2" },
      { id: "3", label: "Item 3" },
      { id: "4", label: "Item 4" },
      { id: "5", label: "Item 5" },
    ];

    render(
      <Breadcrumb
        items={manyItems}
        maxItems={3}
        truncate={true}
        ellipsisPosition="start"
      />,
    );

    expect(screen.getByText("Item 1")).toBeInTheDocument();
    expect(screen.getByText("...")).toBeInTheDocument();
    expect(screen.getByText("Item 5")).toBeInTheDocument();
  });

  it("handles ellipsis position end", () => {
    const manyItems: BreadcrumbItem[] = [
      { id: "1", label: "Item 1" },
      { id: "2", label: "Item 2" },
      { id: "3", label: "Item 3" },
      { id: "4", label: "Item 4" },
      { id: "5", label: "Item 5" },
    ];

    render(
      <Breadcrumb
        items={manyItems}
        maxItems={3}
        truncate={true}
        ellipsisPosition="end"
      />,
    );

    expect(screen.getByText("Item 1")).toBeInTheDocument();
    expect(screen.getByText("Item 2")).toBeInTheDocument();
    expect(screen.getByText("...")).toBeInTheDocument();
    expect(screen.queryByText("Item 5")).not.toBeInTheDocument();
  });

  it("does not truncate when items length is less than maxItems", () => {
    render(<Breadcrumb {...defaultProps} maxItems={10} truncate={true} />);

    expect(screen.queryByText("...")).not.toBeInTheDocument();
    expect(screen.getByText("Home")).toBeInTheDocument();
    expect(screen.getByText("Products")).toBeInTheDocument();
    expect(screen.getByText("Electronics")).toBeInTheDocument();
    expect(screen.getByText("Laptops")).toBeInTheDocument();
  });
});
