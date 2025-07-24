import { render, fireEvent, screen, waitFor } from "@testing-library/react";
import { Accordion, AccordionItem } from "./Accordion";

describe("Accordion", () => {
  const mockItems: AccordionItem[] = [
    { id: "item1", title: "Item 1", content: <div>Content 1</div> },
    { id: "item2", title: "Item 2", content: <div>Content 2</div> },
    {
      id: "item3",
      title: "Item 3",
      content: <div>Content 3</div>,
      disabled: true,
    },
    { id: "item4", title: "Item 4", content: <div>Content 4</div> },
  ];

  const defaultProps = {
    items: mockItems,
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("renders all accordion items", () => {
    render(<Accordion {...defaultProps} />);

    expect(screen.getByText("Item 1")).toBeInTheDocument();
    expect(screen.getByText("Item 2")).toBeInTheDocument();
    expect(screen.getByText("Item 3")).toBeInTheDocument();
    expect(screen.getByText("Item 4")).toBeInTheDocument();
  });

  it("starts with no items expanded by default", () => {
    render(<Accordion {...defaultProps} />);

    expect(screen.queryByText("Content 1")).not.toBeInTheDocument();
    expect(screen.queryByText("Content 2")).not.toBeInTheDocument();
    expect(screen.queryByText("Content 4")).not.toBeInTheDocument();
  });

  it("expands default items when specified", () => {
    render(
      <Accordion {...defaultProps} defaultExpandedItems={["item1", "item2"]} />,
    );

    expect(screen.getByText("Content 1")).toBeInTheDocument();
    expect(screen.getByText("Content 2")).toBeInTheDocument();
  });

  it("respects controlled expandedItems prop", () => {
    render(<Accordion {...defaultProps} expandedItems={["item2"]} />);

    expect(screen.queryByText("Content 1")).not.toBeInTheDocument();
    expect(screen.getByText("Content 2")).toBeInTheDocument();
  });

  it("expands item when clicked", () => {
    render(<Accordion {...defaultProps} />);

    fireEvent.click(screen.getByText("Item 1"));

    expect(screen.getByText("Content 1")).toBeInTheDocument();
  });

  it("collapses item when clicked again in single mode", () => {
    render(<Accordion {...defaultProps} />);

    const item1 = screen.getByText("Item 1");

    fireEvent.click(item1);
    expect(screen.getByText("Content 1")).toBeInTheDocument();

    fireEvent.click(item1);
    expect(screen.queryByText("Content 1")).not.toBeInTheDocument();
  });

  it("does not collapse item when collapsible is false", () => {
    render(
      <Accordion
        {...defaultProps}
        collapsible={false}
        defaultExpandedItems={["item1"]}
      />,
    );

    const item1 = screen.getByText("Item 1");

    fireEvent.click(item1);
    expect(screen.getByText("Content 1")).toBeInTheDocument();
  });

  it("allows multiple items expanded when allowMultiple is true", () => {
    render(<Accordion {...defaultProps} allowMultiple={true} />);

    fireEvent.click(screen.getByText("Item 1"));
    fireEvent.click(screen.getByText("Item 2"));

    expect(screen.getByText("Content 1")).toBeInTheDocument();
    expect(screen.getByText("Content 2")).toBeInTheDocument();
  });

  it("collapses other items in single mode", () => {
    render(<Accordion {...defaultProps} />);

    fireEvent.click(screen.getByText("Item 1"));
    expect(screen.getByText("Content 1")).toBeInTheDocument();

    fireEvent.click(screen.getByText("Item 2"));
    expect(screen.queryByText("Content 1")).not.toBeInTheDocument();
    expect(screen.getByText("Content 2")).toBeInTheDocument();
  });

  it("calls onItemToggle when item is toggled", () => {
    const onItemToggle = jest.fn();
    render(<Accordion {...defaultProps} onItemToggle={onItemToggle} />);

    fireEvent.click(screen.getByText("Item 1"));

    expect(onItemToggle).toHaveBeenCalledWith("item1", true);
  });

  it("does not expand disabled items", () => {
    const onItemToggle = jest.fn();
    render(<Accordion {...defaultProps} onItemToggle={onItemToggle} />);

    fireEvent.click(screen.getByText("Item 3"));

    expect(onItemToggle).not.toHaveBeenCalled();
    expect(screen.queryByText("Content 3")).not.toBeInTheDocument();
  });

  it("displays item icons when provided", () => {
    const itemsWithIcons: AccordionItem[] = [
      {
        id: "item1",
        title: "Item 1",
        content: <div>Content 1</div>,
        icon: <span data-testid="icon-1">🏠</span>,
      },
    ];

    render(<Accordion items={itemsWithIcons} />);

    expect(screen.getByTestId("icon-1")).toBeInTheDocument();
  });

  it("displays item badges when provided", () => {
    const itemsWithBadges: AccordionItem[] = [
      {
        id: "item1",
        title: "Item 1",
        content: <div>Content 1</div>,
        badge: "New",
      },
    ];

    render(<Accordion items={itemsWithBadges} />);

    expect(screen.getByText("New")).toBeInTheDocument();
  });

  it("applies default variant classes", () => {
    render(<Accordion {...defaultProps} variant="default" />);

    const firstItem = screen.getByText("Item 1").closest("div");
    expect(firstItem).toHaveClass("border", "border-gray-200", "rounded-lg");
  });

  it("applies bordered variant classes", () => {
    render(<Accordion {...defaultProps} variant="bordered" />);

    const firstItem = screen.getByText("Item 1").closest("div");
    expect(firstItem).toHaveClass("border", "border-gray-200");
    expect(firstItem).not.toHaveClass("rounded-lg");
  });

  it("applies filled variant classes", () => {
    render(<Accordion {...defaultProps} variant="filled" />);

    const firstItem = screen.getByText("Item 1").closest("div");
    expect(firstItem).toHaveClass(
      "bg-gray-50",
      "border",
      "border-gray-200",
      "rounded-lg",
    );
  });

  it("applies flush variant classes", () => {
    render(<Accordion {...defaultProps} variant="flush" />);

    const firstItem = screen.getByText("Item 1").closest("div");
    expect(firstItem).toHaveClass("border-0");
  });

  it("applies small size classes", () => {
    render(<Accordion {...defaultProps} size="sm" />);

    const button = screen.getByText("Item 1");
    expect(button).toHaveClass("text-sm", "px-3", "py-2");
  });

  it("applies medium size classes", () => {
    render(<Accordion {...defaultProps} size="md" />);

    const button = screen.getByText("Item 1");
    expect(button).toHaveClass("text-base", "px-4", "py-3");
  });

  it("applies large size classes", () => {
    render(<Accordion {...defaultProps} size="lg" />);

    const button = screen.getByText("Item 1");
    expect(button).toHaveClass("text-lg", "px-6", "py-4");
  });

  it("applies custom className", () => {
    render(<Accordion {...defaultProps} className="custom-accordion" />);

    const accordion = screen.getByRole("presentation");
    expect(accordion).toHaveClass("custom-accordion");
  });

  it("applies custom itemClassName", () => {
    render(<Accordion {...defaultProps} itemClassName="custom-item" />);

    const firstItem = screen.getByText("Item 1").closest("div");
    expect(firstItem).toHaveClass("custom-item");
  });

  it("applies custom headerClassName", () => {
    render(<Accordion {...defaultProps} headerClassName="custom-header" />);

    const button = screen.getByText("Item 1");
    expect(button).toHaveClass("custom-header");
  });

  it("applies custom contentClassName", () => {
    render(
      <Accordion
        {...defaultProps}
        contentClassName="custom-content"
        defaultExpandedItems={["item1"]}
      />,
    );

    const content = screen.getByText("Content 1").closest("div");
    expect(content).toHaveClass("custom-content");
  });

  it("hides expand/collapse icon when showIcon is false", () => {
    render(<Accordion {...defaultProps} showIcon={false} />);

    const button = screen.getByText("Item 1");
    const svg = button.querySelector("svg");
    expect(svg).not.toBeInTheDocument();
  });

  it("uses custom expand/collapse icons when provided", () => {
    const customIcon = {
      expanded: <span data-testid="custom-expanded">▼</span>,
      collapsed: <span data-testid="custom-collapsed">▶</span>,
    };

    render(<Accordion {...defaultProps} customIcon={customIcon} />);

    expect(screen.getByTestId("custom-collapsed")).toBeInTheDocument();

    fireEvent.click(screen.getByText("Item 1"));

    expect(screen.getByTestId("custom-expanded")).toBeInTheDocument();
  });

  it("handles keyboard navigation with Enter key", () => {
    render(<Accordion {...defaultProps} />);

    const button = screen.getByText("Item 1");
    button.focus();

    fireEvent.keyDown(button, { key: "Enter" });

    expect(screen.getByText("Content 1")).toBeInTheDocument();
  });

  it("handles keyboard navigation with Space key", () => {
    render(<Accordion {...defaultProps} />);

    const button = screen.getByText("Item 1");
    button.focus();

    fireEvent.keyDown(button, { key: " " });

    expect(screen.getByText("Content 1")).toBeInTheDocument();
  });

  it("handles keyboard navigation with arrow keys", () => {
    render(<Accordion {...defaultProps} />);

    const button1 = screen.getByText("Item 1");
    const button2 = screen.getByText("Item 2");

    button1.focus();

    fireEvent.keyDown(button1, { key: "ArrowDown" });
    expect(document.activeElement).toBe(button2);

    fireEvent.keyDown(button2, { key: "ArrowUp" });
    expect(document.activeElement).toBe(button1);
  });

  it("handles keyboard navigation with Home and End keys", () => {
    render(<Accordion {...defaultProps} />);

    const button2 = screen.getByText("Item 2");
    const button1 = screen.getByText("Item 1");
    const button4 = screen.getByText("Item 4");

    button2.focus();

    fireEvent.keyDown(button2, { key: "Home" });
    expect(document.activeElement).toBe(button1);

    fireEvent.keyDown(button1, { key: "End" });
    expect(document.activeElement).toBe(button4);
  });

  it("skips disabled items in keyboard navigation", () => {
    render(<Accordion {...defaultProps} />);

    const button2 = screen.getByText("Item 2");
    const button4 = screen.getByText("Item 4");

    button2.focus();

    fireEvent.keyDown(button2, { key: "ArrowDown" });
    // Should skip item3 (disabled) and go to item4
    expect(document.activeElement).toBe(button4);
  });

  it("sets proper ARIA attributes", () => {
    render(<Accordion {...defaultProps} defaultExpandedItems={["item1"]} />);

    const button = screen.getByText("Item 1");
    expect(button).toHaveAttribute("aria-expanded", "true");
    expect(button).toHaveAttribute("aria-controls", "accordion-content-item1");
    expect(button).toHaveAttribute("role", "button");

    const content = screen.getByRole("region");
    expect(content).toHaveAttribute(
      "aria-labelledby",
      "accordion-header-item1",
    );
    expect(content).toHaveAttribute("aria-hidden", "false");

    const disabledButton = screen.getByText("Item 3");
    expect(disabledButton).toHaveAttribute("aria-disabled", "true");
  });

  it("handles disabled state properly", () => {
    render(<Accordion {...defaultProps} />);

    const disabledButton = screen.getByText("Item 3");
    expect(disabledButton).toHaveAttribute("disabled");
    expect(disabledButton).toHaveClass("opacity-50", "cursor-not-allowed");
  });

  it("does not respond to keyboard events on disabled items", () => {
    const onItemToggle = jest.fn();
    render(<Accordion {...defaultProps} onItemToggle={onItemToggle} />);

    const disabledButton = screen.getByText("Item 3");
    disabledButton.focus();

    fireEvent.keyDown(disabledButton, { key: "Enter" });
    fireEvent.keyDown(disabledButton, { key: " " });

    expect(onItemToggle).not.toHaveBeenCalled();
  });

  it("applies animation classes when animated is true", () => {
    render(<Accordion {...defaultProps} animated={true} />);

    fireEvent.click(screen.getByText("Item 1"));

    const content = screen.getByRole("region");
    expect(content).toHaveClass(
      "transition-all",
      "duration-300",
      "ease-in-out",
    );
  });

  it("does not apply animation classes when animated is false", () => {
    render(<Accordion {...defaultProps} animated={false} />);

    fireEvent.click(screen.getByText("Item 1"));

    const content = screen.getByRole("region");
    expect(content).not.toHaveClass("transition-all");
  });

  it("wraps around to first item when navigating down from last item", () => {
    render(<Accordion {...defaultProps} />);

    const button4 = screen.getByText("Item 4");
    const button1 = screen.getByText("Item 1");

    button4.focus();

    fireEvent.keyDown(button4, { key: "ArrowDown" });
    expect(document.activeElement).toBe(button1);
  });

  it("wraps around to last enabled item when navigating up from first item", () => {
    render(<Accordion {...defaultProps} />);

    const button1 = screen.getByText("Item 1");
    const button4 = screen.getByText("Item 4");

    button1.focus();

    fireEvent.keyDown(button1, { key: "ArrowUp" });
    expect(document.activeElement).toBe(button4);
  });
});
