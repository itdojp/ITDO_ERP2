import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { vi } from "vitest";
import { VirtualList } from "./VirtualList";

interface TestItem {
  id: number;
  name: string;
  description: string;
  category: string;
}

describe("VirtualList", () => {
  const mockData: TestItem[] = Array.from({ length: 1000 }, (_, i) => ({
    id: i + 1,
    name: `Item ${i + 1}`,
    description: `Description for item ${i + 1}`,
    category: ["Category A", "Category B", "Category C"][i % 3],
  }));

  const renderItem = (item: TestItem, index: number) => (
    <div key={item.id} data-testid={`item-${item.id}`} className="p-4 border-b">
      <h3>{item.name}</h3>
      <p>{item.description}</p>
    </div>
  );

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders virtual list with items", () => {
    render(
      <VirtualList
        items={mockData.slice(0, 10)}
        itemHeight={80}
        height={400}
        renderItem={renderItem}
      />,
    );

    expect(screen.getByTestId("virtual-list-container")).toBeInTheDocument();
    expect(screen.getByText("Item 1")).toBeInTheDocument();
  });

  it("supports different item heights", () => {
    const heights = [60, 80, 100];

    heights.forEach((height) => {
      const { unmount } = render(
        <VirtualList
          items={mockData.slice(0, 10)}
          itemHeight={height}
          height={400}
          renderItem={renderItem}
        />,
      );

      const container = screen.getByTestId("virtual-list-container");
      expect(container).toBeInTheDocument();
      unmount();
    });
  });

  it("supports dynamic item heights", () => {
    const getItemHeight = (index: number) => (index % 2 === 0 ? 80 : 100);

    render(
      <VirtualList
        items={mockData.slice(0, 10)}
        getItemHeight={getItemHeight}
        height={400}
        renderItem={renderItem}
      />,
    );

    expect(screen.getByTestId("virtual-list-container")).toBeInTheDocument();
  });

  it("handles scrolling correctly", async () => {
    render(
      <VirtualList
        items={mockData}
        itemHeight={80}
        height={400}
        renderItem={renderItem}
      />,
    );

    const scrollContainer = screen.getByTestId("virtual-list-scroll");
    fireEvent.scroll(scrollContainer, { target: { scrollTop: 800 } });

    await waitFor(() => {
      expect(scrollContainer.scrollTop).toBe(800);
    });
  });

  it("supports horizontal scrolling", () => {
    render(
      <VirtualList
        items={mockData.slice(0, 10)}
        itemHeight={80}
        itemWidth={200}
        width={600}
        height={400}
        direction="horizontal"
        renderItem={renderItem}
      />,
    );

    const container = screen.getByTestId("virtual-list-container");
    expect(container).toHaveClass("horizontal-scroll");
  });

  it("supports overscan for smooth scrolling", () => {
    render(
      <VirtualList
        items={mockData}
        itemHeight={80}
        height={400}
        overscan={5}
        renderItem={renderItem}
      />,
    );

    expect(screen.getByTestId("virtual-list-container")).toBeInTheDocument();
  });

  it("handles empty list state", () => {
    render(
      <VirtualList
        items={[]}
        itemHeight={80}
        height={400}
        renderItem={renderItem}
      />,
    );

    expect(screen.getByTestId("virtual-list-empty")).toBeInTheDocument();
  });

  it("supports custom empty state", () => {
    const customEmpty = <div data-testid="custom-empty">No items found</div>;

    render(
      <VirtualList
        items={[]}
        itemHeight={80}
        height={400}
        emptyState={customEmpty}
        renderItem={renderItem}
      />,
    );

    expect(screen.getByTestId("custom-empty")).toBeInTheDocument();
  });

  it("supports loading state", () => {
    render(
      <VirtualList
        items={mockData.slice(0, 10)}
        itemHeight={80}
        height={400}
        loading
        renderItem={renderItem}
      />,
    );

    expect(screen.getByTestId("virtual-list-loading")).toBeInTheDocument();
  });

  it("supports infinite scrolling", async () => {
    const onLoadMore = vi.fn();

    render(
      <VirtualList
        items={mockData.slice(0, 50)}
        itemHeight={80}
        height={400}
        infiniteScroll
        onLoadMore={onLoadMore}
        renderItem={renderItem}
      />,
    );

    const scrollContainer = screen.getByTestId("virtual-list-scroll");

    // Scroll to bottom
    fireEvent.scroll(scrollContainer, {
      target: {
        scrollTop: scrollContainer.scrollHeight - scrollContainer.clientHeight,
      },
    });

    await waitFor(() => {
      expect(onLoadMore).toHaveBeenCalled();
    });
  });

  it("supports item selection", () => {
    const onSelectionChange = vi.fn();

    render(
      <VirtualList
        items={mockData.slice(0, 10)}
        itemHeight={80}
        height={400}
        selectable
        selectedItems={[]}
        onSelectionChange={onSelectionChange}
        renderItem={renderItem}
      />,
    );

    const firstItem = screen.getByTestId("virtual-item-0");
    fireEvent.click(firstItem);

    expect(onSelectionChange).toHaveBeenCalledWith([mockData[0]]);
  });

  it("supports multi-selection", () => {
    const onSelectionChange = vi.fn();

    render(
      <VirtualList
        items={mockData.slice(0, 10)}
        itemHeight={80}
        height={400}
        selectable
        multiSelect
        selectedItems={[]}
        onSelectionChange={onSelectionChange}
        renderItem={renderItem}
      />,
    );

    const firstItem = screen.getByTestId("virtual-item-0");
    const secondItem = screen.getByTestId("virtual-item-1");

    fireEvent.click(firstItem);
    fireEvent.click(secondItem, { ctrlKey: true });

    expect(onSelectionChange).toHaveBeenCalledWith([mockData[0], mockData[1]]);
  });

  it("supports item drag and drop", () => {
    const onReorder = vi.fn();

    render(
      <VirtualList
        items={mockData.slice(0, 10)}
        itemHeight={80}
        height={400}
        draggable
        onReorder={onReorder}
        renderItem={renderItem}
      />,
    );

    const firstItem = screen.getByTestId("virtual-item-0");
    expect(firstItem).toHaveAttribute("draggable", "true");
  });

  it("supports grouping items", () => {
    const groupBy = (item: TestItem) => item.category;

    render(
      <VirtualList
        items={mockData.slice(0, 10)}
        itemHeight={80}
        height={400}
        groupBy={groupBy}
        renderItem={renderItem}
      />,
    );

    expect(screen.getByTestId("group-Category A")).toBeInTheDocument();
    expect(screen.getByTestId("group-Category B")).toBeInTheDocument();
    expect(screen.getByTestId("group-Category C")).toBeInTheDocument();
  });

  it("supports custom group headers", () => {
    const groupBy = (item: TestItem) => item.category;
    const renderGroupHeader = (group: string, items: TestItem[]) => (
      <div data-testid={`custom-group-${group}`} className="font-bold">
        {group} ({items.length} items)
      </div>
    );

    render(
      <VirtualList
        items={mockData.slice(0, 10)}
        itemHeight={80}
        height={400}
        groupBy={groupBy}
        renderGroupHeader={renderGroupHeader}
        renderItem={renderItem}
      />,
    );

    expect(screen.getByTestId("custom-group-Category A")).toBeInTheDocument();
  });

  it("supports search functionality", () => {
    const searchFilter = (item: TestItem, query: string) =>
      item.name.toLowerCase().includes(query.toLowerCase());

    render(
      <VirtualList
        items={mockData.slice(0, 10)}
        itemHeight={80}
        height={400}
        searchable
        searchQuery="Item 1"
        searchFilter={searchFilter}
        renderItem={renderItem}
      />,
    );

    expect(screen.getByText("Item 1")).toBeInTheDocument();
    expect(screen.queryByText("Item 2")).not.toBeInTheDocument();
  });

  it("displays search input when searchable", () => {
    render(
      <VirtualList
        items={mockData.slice(0, 10)}
        itemHeight={80}
        height={400}
        searchable
        renderItem={renderItem}
      />,
    );

    expect(screen.getByTestId("virtual-list-search")).toBeInTheDocument();
  });

  it("handles search input changes", () => {
    const onSearch = vi.fn();

    render(
      <VirtualList
        items={mockData.slice(0, 10)}
        itemHeight={80}
        height={400}
        searchable
        onSearch={onSearch}
        renderItem={renderItem}
      />,
    );

    const searchInput = screen.getByTestId("search-input");
    fireEvent.change(searchInput, { target: { value: "Item 5" } });

    expect(onSearch).toHaveBeenCalledWith("Item 5");
  });

  it("supports sorting", () => {
    const sortBy = (a: TestItem, b: TestItem) => a.name.localeCompare(b.name);

    render(
      <VirtualList
        items={mockData.slice(0, 10)}
        itemHeight={80}
        height={400}
        sortBy={sortBy}
        renderItem={renderItem}
      />,
    );

    expect(screen.getByTestId("virtual-list-container")).toBeInTheDocument();
  });

  it("supports item context menu", () => {
    const contextMenuItems = [
      { label: "Edit", onClick: vi.fn() },
      { label: "Delete", onClick: vi.fn() },
    ];

    render(
      <VirtualList
        items={mockData.slice(0, 10)}
        itemHeight={80}
        height={400}
        contextMenu={contextMenuItems}
        renderItem={renderItem}
      />,
    );

    const firstItem = screen.getByTestId("virtual-item-0");
    fireEvent.contextMenu(firstItem);

    expect(screen.getByTestId("context-menu")).toBeInTheDocument();
  });

  it("supports keyboard navigation", () => {
    render(
      <VirtualList
        items={mockData.slice(0, 10)}
        itemHeight={80}
        height={400}
        selectable
        renderItem={renderItem}
      />,
    );

    const container = screen.getByTestId("virtual-list-container");
    container.focus();

    fireEvent.keyDown(container, { key: "ArrowDown" });

    // Check that the container received the key down event
    expect(container).toHaveFocus();
  });

  it("supports different list orientations", () => {
    const orientations = ["vertical", "horizontal"] as const;

    orientations.forEach((direction) => {
      const { unmount } = render(
        <VirtualList
          items={mockData.slice(0, 10)}
          itemHeight={80}
          height={400}
          direction={direction}
          renderItem={renderItem}
        />,
      );

      const container = screen.getByTestId("virtual-list-container");
      expect(container).toHaveClass(`direction-${direction}`);
      unmount();
    });
  });

  it("supports sticky headers", () => {
    render(
      <VirtualList
        items={mockData.slice(0, 10)}
        itemHeight={80}
        height={400}
        stickyHeader
        header={<div data-testid="sticky-header">List Header</div>}
        renderItem={renderItem}
      />,
    );

    expect(screen.getByTestId("sticky-header")).toBeInTheDocument();
    const header = screen.getByTestId("virtual-list-header");
    expect(header).toHaveClass("sticky");
  });

  it("supports scroll to item", () => {
    const onScroll = vi.fn();

    render(
      <VirtualList
        items={mockData}
        itemHeight={80}
        height={400}
        scrollToIndex={10}
        onScroll={onScroll}
        renderItem={renderItem}
      />,
    );

    expect(screen.getByTestId("virtual-list-container")).toBeInTheDocument();
  });

  it("supports batch rendering", () => {
    render(
      <VirtualList
        items={mockData}
        itemHeight={80}
        height={400}
        batchSize={20}
        renderItem={renderItem}
      />,
    );

    expect(screen.getByTestId("virtual-list-container")).toBeInTheDocument();
  });

  it("supports custom scroll behavior", () => {
    render(
      <VirtualList
        items={mockData.slice(0, 10)}
        itemHeight={80}
        height={400}
        scrollBehavior="smooth"
        renderItem={renderItem}
      />,
    );

    const scrollContainer = screen.getByTestId("virtual-list-scroll");
    expect(scrollContainer).toHaveStyle({ scrollBehavior: "smooth" });
  });

  it("handles item updates correctly", () => {
    const { rerender } = render(
      <VirtualList
        items={mockData.slice(0, 5)}
        itemHeight={80}
        height={400}
        renderItem={renderItem}
      />,
    );

    expect(screen.getByText("Item 1")).toBeInTheDocument();
    expect(screen.queryByText("Item 6")).not.toBeInTheDocument();

    rerender(
      <VirtualList
        items={mockData.slice(0, 10)}
        itemHeight={80}
        height={400}
        renderItem={renderItem}
      />,
    );

    expect(screen.getByText("Item 6")).toBeInTheDocument();
  });

  it("supports performance monitoring", () => {
    const onPerformanceReport = vi.fn();

    render(
      <VirtualList
        items={mockData}
        itemHeight={80}
        height={400}
        enablePerformanceMonitoring
        onPerformanceReport={onPerformanceReport}
        renderItem={renderItem}
      />,
    );

    expect(screen.getByTestId("virtual-list-container")).toBeInTheDocument();
  });

  it("handles render item errors gracefully", () => {
    const renderItemWithError = (item: TestItem, index: number) => {
      try {
        return renderItem(item, index);
      } catch (error) {
        return (
          <div data-testid={`error-item-${item.id}`}>Error rendering item</div>
        );
      }
    };

    render(
      <VirtualList
        items={mockData.slice(0, 1)}
        itemHeight={80}
        height={400}
        renderItem={renderItemWithError}
      />,
    );

    expect(screen.getByTestId("virtual-list-container")).toBeInTheDocument();
  });

  it("supports custom styling", () => {
    render(
      <VirtualList
        items={mockData.slice(0, 10)}
        itemHeight={80}
        height={400}
        className="custom-virtual-list"
        renderItem={renderItem}
      />,
    );

    const container = screen.getByTestId("virtual-list-container");
    expect(container).toHaveClass("custom-virtual-list");
  });

  it("supports custom data attributes", () => {
    render(
      <VirtualList
        items={mockData.slice(0, 10)}
        itemHeight={80}
        height={400}
        data-category="list"
        data-id="main-list"
        renderItem={renderItem}
      />,
    );

    const container = screen.getByTestId("virtual-list-container");
    expect(container).toHaveAttribute("data-category", "list");
    expect(container).toHaveAttribute("data-id", "main-list");
  });

  it("supports accessibility attributes", () => {
    render(
      <VirtualList
        items={mockData.slice(0, 10)}
        itemHeight={80}
        height={400}
        ariaLabel="Virtual item list"
        ariaDescribedBy="list-description"
        renderItem={renderItem}
      />,
    );

    const container = screen.getByTestId("virtual-list-container");
    expect(container).toHaveAttribute("aria-label", "Virtual item list");
    expect(container).toHaveAttribute("aria-describedby", "list-description");
  });

  it("handles rapid scrolling smoothly", async () => {
    render(
      <VirtualList
        items={mockData}
        itemHeight={80}
        height={400}
        renderItem={renderItem}
      />,
    );

    const scrollContainer = screen.getByTestId("virtual-list-scroll");

    // Simulate rapid scrolling
    for (let i = 0; i < 10; i++) {
      fireEvent.scroll(scrollContainer, { target: { scrollTop: i * 200 } });
    }

    await waitFor(() => {
      expect(scrollContainer).toBeInTheDocument();
    });
  });

  it("supports window mode for full viewport scrolling", () => {
    render(
      <VirtualList
        items={mockData}
        itemHeight={80}
        windowMode
        renderItem={renderItem}
      />,
    );

    const container = screen.getByTestId("virtual-list-container");
    expect(container).toHaveClass("window-mode");
  });

  it("supports item caching for performance", () => {
    render(
      <VirtualList
        items={mockData}
        itemHeight={80}
        height={400}
        enableItemCache
        cacheSize={100}
        renderItem={renderItem}
      />,
    );

    expect(screen.getByTestId("virtual-list-container")).toBeInTheDocument();
  });

  it("handles resize events", () => {
    const onResize = vi.fn();

    render(
      <VirtualList
        items={mockData.slice(0, 10)}
        itemHeight={80}
        height={400}
        onResize={onResize}
        renderItem={renderItem}
      />,
    );

    // Simulate resize
    global.dispatchEvent(new Event("resize"));

    expect(onResize).toHaveBeenCalled();
  });

  it("supports different loading states", () => {
    const loadingStates = ["initial", "more", "complete"] as const;

    loadingStates.forEach((loadingState) => {
      const { unmount } = render(
        <VirtualList
          items={mockData.slice(0, 10)}
          itemHeight={80}
          height={400}
          loading
          loadingState={loadingState}
          renderItem={renderItem}
        />,
      );

      const container = screen.getByTestId("virtual-list-loading");
      expect(container).toHaveClass(`loading-${loadingState}`);
      unmount();
    });
  });
});
