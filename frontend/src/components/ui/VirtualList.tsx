import React, {
  useState,
  useRef,
  useCallback,
  useEffect,
  useMemo,
} from "react";
import { cn } from "@/lib/utils";

export interface ContextMenuItem {
  label: string;
  icon?: React.ReactNode;
  onClick: (item: any) => void;
  disabled?: boolean;
}

export interface VirtualListProps<T = any> {
  items: T[];
  itemHeight?: number;
  itemWidth?: number;
  getItemHeight?: (index: number) => number;
  getItemWidth?: (index: number) => number;
  height?: number;
  width?: number;
  direction?: "vertical" | "horizontal";
  overscan?: number;
  batchSize?: number;
  loading?: boolean;
  loadingState?: "initial" | "more" | "complete";
  infiniteScroll?: boolean;
  searchable?: boolean;
  searchQuery?: string;
  searchFilter?: (item: T, query: string) => boolean;
  selectable?: boolean;
  multiSelect?: boolean;
  selectedItems?: T[];
  draggable?: boolean;
  groupBy?: (item: T) => string;
  sortBy?: (a: T, b: T) => number;
  header?: React.ReactNode;
  footer?: React.ReactNode;
  emptyState?: React.ReactNode;
  contextMenu?: ContextMenuItem[];
  stickyHeader?: boolean;
  scrollToIndex?: number;
  scrollBehavior?: "auto" | "smooth";
  windowMode?: boolean;
  enableItemCache?: boolean;
  cacheSize?: number;
  enablePerformanceMonitoring?: boolean;
  renderItem: (item: T, index: number) => React.ReactNode;
  renderGroupHeader?: (group: string, items: T[]) => React.ReactNode;
  getItemKey?: (item: T, index: number) => string | number;
  ariaLabel?: string;
  ariaDescribedBy?: string;
  onScroll?: (scrollTop: number, scrollLeft: number) => void;
  onLoadMore?: () => void;
  onSearch?: (query: string) => void;
  onSelectionChange?: (selectedItems: T[]) => void;
  onReorder?: (fromIndex: number, toIndex: number) => void;
  onResize?: (width: number, height: number) => void;
  onPerformanceReport?: (metrics: any) => void;
  className?: string;
  "data-testid"?: string;
  "data-category"?: string;
  "data-id"?: string;
}

export const VirtualList = <T extends any>({
  items,
  itemHeight = 50,
  itemWidth = 200,
  getItemHeight,
  getItemWidth,
  height = 400,
  width = 300,
  direction = "vertical",
  overscan = 3,
  batchSize = 10,
  loading = false,
  loadingState = "initial",
  infiniteScroll = false,
  searchable = false,
  searchQuery = "",
  searchFilter,
  selectable = false,
  multiSelect = false,
  selectedItems = [],
  draggable = false,
  groupBy,
  sortBy,
  header,
  footer,
  emptyState,
  contextMenu = [],
  stickyHeader = false,
  scrollToIndex,
  scrollBehavior = "auto",
  windowMode = false,
  enableItemCache = false,
  cacheSize = 100,
  enablePerformanceMonitoring = false,
  renderItem,
  renderGroupHeader,
  getItemKey,
  ariaLabel = "Virtual list",
  ariaDescribedBy,
  onScroll,
  onLoadMore,
  onSearch,
  onSelectionChange,
  onReorder,
  onResize,
  onPerformanceReport,
  className,
  "data-testid": dataTestId = "virtual-list-container",
  "data-category": dataCategory,
  "data-id": dataId,
  ...props
}: VirtualListProps<T>) => {
  const [scrollTop, setScrollTop] = useState(0);
  const [scrollLeft, setScrollLeft] = useState(0);
  const [internalSearchQuery, setInternalSearchQuery] = useState(searchQuery);
  const [internalSelectedItems, setInternalSelectedItems] =
    useState<T[]>(selectedItems);
  const [contextMenuPosition, setContextMenuPosition] = useState<{
    x: number;
    y: number;
    item: T;
  } | null>(null);
  const [focusedIndex, setFocusedIndex] = useState(-1);
  const [draggedIndex, setDraggedIndex] = useState<number | null>(null);
  const [itemCache, setItemCache] = useState<Map<string, React.ReactNode>>(
    new Map(),
  );

  const containerRef = useRef<HTMLDivElement>(null);
  const scrollContainerRef = useRef<HTMLDivElement>(null);
  const performanceRef = useRef({
    renderStart: 0,
    renderEnd: 0,
    scrollCount: 0,
  });

  // Calculate item dimensions
  const getItemSize = useCallback(
    (index: number) => {
      if (direction === "vertical") {
        return getItemHeight ? getItemHeight(index) : itemHeight;
      } else {
        return getItemWidth ? getItemWidth(index) : itemWidth;
      }
    },
    [direction, getItemHeight, getItemWidth, itemHeight, itemWidth],
  );

  // Filter and sort items
  const processedItems = useMemo(() => {
    let filtered = [...items];

    // Apply search filter
    if (internalSearchQuery && searchFilter) {
      filtered = filtered.filter((item) =>
        searchFilter(item, internalSearchQuery),
      );
    }

    // Apply sorting
    if (sortBy) {
      filtered.sort(sortBy);
    }

    return filtered;
  }, [items, internalSearchQuery, searchFilter, sortBy]);

  // Group items if needed
  const groupedItems = useMemo(() => {
    if (!groupBy) return { ungrouped: processedItems };

    const groups: Record<string, T[]> = {};
    processedItems.forEach((item) => {
      const group = groupBy(item);
      if (!groups[group]) {
        groups[group] = [];
      }
      groups[group].push(item);
    });

    return groups;
  }, [processedItems, groupBy]);

  // Calculate visible range
  const { startIndex, endIndex, totalSize } = useMemo(() => {
    if (processedItems.length === 0) {
      return { startIndex: 0, endIndex: 0, totalSize: 0 };
    }

    const scroll = direction === "vertical" ? scrollTop : scrollLeft;
    const containerSize = direction === "vertical" ? height : width;

    let currentOffset = 0;
    let start = 0;
    let end = 0;
    let total = 0;

    // Find start index
    for (let i = 0; i < processedItems.length; i++) {
      const size = getItemSize(i);
      if (currentOffset + size > scroll) {
        start = Math.max(0, i - overscan);
        break;
      }
      currentOffset += size;
    }

    // Find end index
    currentOffset = 0;
    for (let i = 0; i < processedItems.length; i++) {
      const size = getItemSize(i);
      currentOffset += size;
      if (i >= start && currentOffset > scroll + containerSize) {
        end = Math.min(processedItems.length - 1, i + overscan);
        break;
      }
    }

    // Calculate total size
    for (let i = 0; i < processedItems.length; i++) {
      total += getItemSize(i);
    }

    return { startIndex: start, endIndex: end, totalSize: total };
  }, [
    processedItems.length,
    scrollTop,
    scrollLeft,
    direction,
    height,
    width,
    getItemSize,
    overscan,
  ]);

  // Handle scroll
  const handleScroll = useCallback(
    (e: React.UIEvent<HTMLDivElement>) => {
      const target = e.currentTarget;
      const newScrollTop = target.scrollTop;
      const newScrollLeft = target.scrollLeft;

      setScrollTop(newScrollTop);
      setScrollLeft(newScrollLeft);
      onScroll?.(newScrollTop, newScrollLeft);

      if (enablePerformanceMonitoring) {
        performanceRef.current.scrollCount++;
      }

      // Infinite scroll
      if (infiniteScroll && onLoadMore) {
        const scrollBottom =
          target.scrollHeight - target.scrollTop - target.clientHeight;
        if (scrollBottom < 100) {
          onLoadMore();
        }
      }
    },
    [onScroll, infiniteScroll, onLoadMore, enablePerformanceMonitoring],
  );

  // Handle search
  const handleSearch = useCallback(
    (query: string) => {
      setInternalSearchQuery(query);
      onSearch?.(query);
    },
    [onSearch],
  );

  // Handle selection
  const handleItemSelect = useCallback(
    (item: T, event: React.MouseEvent) => {
      let newSelection: T[];

      if (multiSelect && (event.ctrlKey || event.metaKey)) {
        const isSelected = internalSelectedItems.includes(item);
        newSelection = isSelected
          ? internalSelectedItems.filter((selected) => selected !== item)
          : [...internalSelectedItems, item];
      } else {
        newSelection = [item];
      }

      setInternalSelectedItems(newSelection);
      onSelectionChange?.(newSelection);
    },
    [internalSelectedItems, multiSelect, onSelectionChange],
  );

  // Handle context menu
  const handleContextMenu = useCallback(
    (e: React.MouseEvent, item: T) => {
      if (contextMenu.length === 0) return;

      e.preventDefault();
      setContextMenuPosition({
        x: e.clientX,
        y: e.clientY,
        item,
      });
    },
    [contextMenu],
  );

  // Handle keyboard navigation
  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      switch (e.key) {
        case "ArrowDown":
          e.preventDefault();
          setFocusedIndex((prev) =>
            Math.min(processedItems.length - 1, prev + 1),
          );
          break;
        case "ArrowUp":
          e.preventDefault();
          setFocusedIndex((prev) => Math.max(0, prev - 1));
          break;
        case "Enter":
          if (focusedIndex >= 0 && selectable) {
            handleItemSelect(processedItems[focusedIndex], e as any);
          }
          break;
        case "Escape":
          setContextMenuPosition(null);
          break;
      }
    },
    [processedItems, focusedIndex, selectable, handleItemSelect],
  );

  // Handle drag and drop
  const handleDragStart = useCallback(
    (e: React.DragEvent, index: number) => {
      if (!draggable) return;
      setDraggedIndex(index);
      e.dataTransfer.effectAllowed = "move";
    },
    [draggable],
  );

  const handleDragOver = useCallback(
    (e: React.DragEvent, index: number) => {
      if (!draggable || draggedIndex === null) return;
      e.preventDefault();
      e.dataTransfer.dropEffect = "move";
    },
    [draggable, draggedIndex],
  );

  const handleDrop = useCallback(
    (e: React.DragEvent, dropIndex: number) => {
      if (!draggable || draggedIndex === null) return;
      e.preventDefault();

      if (draggedIndex !== dropIndex) {
        onReorder?.(draggedIndex, dropIndex);
      }

      setDraggedIndex(null);
    },
    [draggable, draggedIndex, onReorder],
  );

  // Scroll to specific index
  useEffect(() => {
    if (
      scrollToIndex !== undefined &&
      scrollContainerRef.current &&
      scrollContainerRef.current.scrollTo
    ) {
      let offset = 0;
      for (let i = 0; i < scrollToIndex; i++) {
        offset += getItemSize(i);
      }

      try {
        if (direction === "vertical") {
          scrollContainerRef.current.scrollTo({
            top: offset,
            behavior: scrollBehavior,
          });
        } else {
          scrollContainerRef.current.scrollTo({
            left: offset,
            behavior: scrollBehavior,
          });
        }
      } catch (error) {
        // Fallback for environments that don't support scrollTo
        if (direction === "vertical") {
          scrollContainerRef.current.scrollTop = offset;
        } else {
          scrollContainerRef.current.scrollLeft = offset;
        }
      }
    }
  }, [scrollToIndex, getItemSize, direction, scrollBehavior]);

  // Performance monitoring
  useEffect(() => {
    if (enablePerformanceMonitoring) {
      performanceRef.current.renderStart = performance.now();

      return () => {
        performanceRef.current.renderEnd = performance.now();
        const renderTime =
          performanceRef.current.renderEnd - performanceRef.current.renderStart;

        onPerformanceReport?.({
          renderTime,
          scrollCount: performanceRef.current.scrollCount,
          visibleItems: endIndex - startIndex + 1,
          totalItems: processedItems.length,
        });
      };
    }
  }, [
    enablePerformanceMonitoring,
    onPerformanceReport,
    startIndex,
    endIndex,
    processedItems.length,
  ]);

  // Handle resize
  useEffect(() => {
    if (!onResize) return;

    const handleResize = () => {
      if (containerRef.current) {
        const rect = containerRef.current.getBoundingClientRect();
        onResize(rect.width, rect.height);
      }
    };

    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
  }, [onResize]);

  // Click outside handler
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        containerRef.current &&
        !containerRef.current.contains(event.target as Node)
      ) {
        setContextMenuPosition(null);
      }
    };

    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  // Render search input
  const renderSearch = () => {
    if (!searchable) return null;

    return (
      <div className="p-2 border-b" data-testid="virtual-list-search">
        <input
          type="text"
          placeholder="Search items..."
          value={internalSearchQuery}
          onChange={(e) => handleSearch(e.target.value)}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          data-testid="search-input"
        />
      </div>
    );
  };

  // Render header
  const renderHeader = () => {
    if (!header) return null;

    return (
      <div
        className={cn("border-b", stickyHeader && "sticky top-0 z-10 bg-white")}
        data-testid="virtual-list-header"
      >
        {header}
      </div>
    );
  };

  // Render items
  const renderItems = () => {
    if (loading) {
      return (
        <div
          className={cn(
            "flex items-center justify-center",
            `loading-${loadingState}`,
          )}
          style={{ height: direction === "vertical" ? height : "auto" }}
          data-testid="virtual-list-loading"
        >
          <div className="w-8 h-8 border-2 border-gray-300 border-t-blue-500 rounded-full animate-spin"></div>
        </div>
      );
    }

    if (processedItems.length === 0) {
      return (
        <div
          className="flex items-center justify-center text-gray-500"
          style={{ height: direction === "vertical" ? height : "auto" }}
          data-testid="virtual-list-empty"
        >
          {emptyState || <div>No items to display</div>}
        </div>
      );
    }

    if (groupBy) {
      return renderGroupedItems();
    }

    const visibleItems = [];
    let currentOffset = 0;

    // Calculate offset for items before visible range
    for (let i = 0; i < startIndex; i++) {
      currentOffset += getItemSize(i);
    }

    // Render visible items
    for (let i = startIndex; i <= endIndex; i++) {
      const item = processedItems[i];
      const key = getItemKey ? getItemKey(item, i) : i;
      const itemSize = getItemSize(i);
      const isSelected = internalSelectedItems.includes(item);
      const isFocused = i === focusedIndex;
      const isDragged = i === draggedIndex;

      let renderedItem: React.ReactNode;

      // Use cache if enabled
      if (enableItemCache) {
        const cacheKey = `${key}-${JSON.stringify(item)}`;
        if (itemCache.has(cacheKey)) {
          renderedItem = itemCache.get(cacheKey);
        } else {
          renderedItem = renderItem(item, i);
          if (itemCache.size < cacheSize) {
            setItemCache((prev) => new Map(prev).set(cacheKey, renderedItem));
          }
        }
      } else {
        renderedItem = renderItem(item, i);
      }

      visibleItems.push(
        <div
          key={key}
          className={cn(
            "virtual-list-item",
            isSelected && "selected bg-blue-50",
            isFocused && "focused ring-2 ring-blue-500",
            isDragged && "dragging opacity-50",
          )}
          style={{
            position: "absolute",
            [direction === "vertical" ? "top" : "left"]: currentOffset,
            [direction === "vertical" ? "height" : "width"]: itemSize,
            [direction === "vertical" ? "width" : "height"]:
              direction === "vertical" ? "100%" : itemSize,
          }}
          onClick={(e) => selectable && handleItemSelect(item, e)}
          onContextMenu={(e) => handleContextMenu(e, item)}
          draggable={draggable}
          onDragStart={(e) => handleDragStart(e, i)}
          onDragOver={(e) => handleDragOver(e, i)}
          onDrop={(e) => handleDrop(e, i)}
          data-testid={`virtual-item-${getItemKey ? getItemKey(item, i) : i}`}
        >
          {renderedItem}
        </div>,
      );

      currentOffset += itemSize;
    }

    return (
      <div
        className="relative"
        style={{
          [direction === "vertical" ? "height" : "width"]: totalSize,
          [direction === "vertical" ? "width" : "height"]: "100%",
        }}
      >
        {visibleItems}
      </div>
    );
  };

  // Render grouped items
  const renderGroupedItems = () => {
    const groups = Object.entries(groupedItems);
    const currentOffset = 0;
    const visibleElements = [];

    groups.forEach(([groupName, groupItems]) => {
      // Render group header
      const groupHeader = renderGroupHeader ? (
        renderGroupHeader(groupName, groupItems)
      ) : (
        <div className="font-semibold p-2 bg-gray-100">{groupName}</div>
      );

      visibleElements.push(
        <div
          key={`group-${groupName}`}
          className="group-header sticky top-0 z-5 bg-white"
          data-testid={`group-${groupName}`}
        >
          {groupHeader}
        </div>,
      );

      // Render group items
      groupItems.forEach((item, index) => {
        const globalIndex = processedItems.indexOf(item);
        const key = getItemKey ? getItemKey(item, globalIndex) : globalIndex;
        const isSelected = internalSelectedItems.includes(item);

        visibleElements.push(
          <div
            key={key}
            className={cn("group-item", isSelected && "selected bg-blue-50")}
            onClick={(e) => selectable && handleItemSelect(item, e)}
            onContextMenu={(e) => handleContextMenu(e, item)}
            draggable={draggable}
            data-testid={`virtual-item-${key}`}
          >
            {renderItem(item, globalIndex)}
          </div>,
        );
      });
    });

    return <div className="grouped-content">{visibleElements}</div>;
  };

  // Render context menu
  const renderContextMenu = () => {
    if (!contextMenuPosition) return null;

    return (
      <div
        className="fixed z-50 bg-white border border-gray-200 rounded-md shadow-lg min-w-32"
        style={{ left: contextMenuPosition.x, top: contextMenuPosition.y }}
        data-testid="context-menu"
      >
        {contextMenu.map((menuItem, index) => (
          <button
            key={index}
            className="w-full px-3 py-2 text-left text-sm hover:bg-gray-100 first:rounded-t-md last:rounded-b-md disabled:opacity-50"
            disabled={menuItem.disabled}
            onClick={() => {
              menuItem.onClick(contextMenuPosition.item);
              setContextMenuPosition(null);
            }}
          >
            {menuItem.icon && <span className="mr-2">{menuItem.icon}</span>}
            {menuItem.label}
          </button>
        ))}
      </div>
    );
  };

  return (
    <div
      ref={containerRef}
      className={cn(
        "virtual-list",
        `direction-${direction}`,
        direction === "horizontal" && "horizontal-scroll",
        windowMode && "window-mode",
        className,
      )}
      style={{
        height: direction === "vertical" ? height : "auto",
        width: direction === "horizontal" ? width : "auto",
      }}
      tabIndex={0}
      onKeyDown={handleKeyDown}
      role="listbox"
      aria-label={ariaLabel}
      aria-describedby={ariaDescribedBy}
      data-testid={dataTestId}
      data-category={dataCategory}
      data-id={dataId}
      {...props}
    >
      {renderSearch()}
      {renderHeader()}

      <div
        ref={scrollContainerRef}
        className="scroll-container overflow-auto"
        style={{
          height: direction === "vertical" ? height : "auto",
          width: direction === "horizontal" ? width : "auto",
          scrollBehavior,
        }}
        onScroll={handleScroll}
        data-testid="virtual-list-scroll"
      >
        {renderItems()}
      </div>

      {footer && <div className="border-t p-2">{footer}</div>}

      {renderContextMenu()}
    </div>
  );
};

export default VirtualList;
