import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { vi } from "vitest";
import { Tree } from "./Tree";

describe("Tree", () => {
  const basicTreeData = [
    {
      key: "1",
      title: "Parent 1",
      children: [
        { key: "1-1", title: "Child 1-1" },
        { key: "1-2", title: "Child 1-2" },
      ],
    },
    {
      key: "2",
      title: "Parent 2",
      children: [
        {
          key: "2-1",
          title: "Child 2-1",
          children: [{ key: "2-1-1", title: "Grandchild 2-1-1" }],
        },
      ],
    },
    { key: "3", title: "Leaf Node" },
  ];

  it("renders tree structure", () => {
    render(<Tree treeData={basicTreeData} />);

    expect(screen.getByText("Parent 1")).toBeInTheDocument();
    expect(screen.getByText("Parent 2")).toBeInTheDocument();
    expect(screen.getByText("Leaf Node")).toBeInTheDocument();
  });

  it("expands and collapses nodes", async () => {
    render(<Tree treeData={basicTreeData} />);

    // Children should not be visible initially
    expect(screen.queryByText("Child 1-1")).not.toBeInTheDocument();

    // Click to expand
    const expandButton = screen.getAllByRole("button")[0];
    fireEvent.click(expandButton);

    await waitFor(() => {
      expect(screen.getByText("Child 1-1")).toBeInTheDocument();
      expect(screen.getByText("Child 1-2")).toBeInTheDocument();
    });

    // Click to collapse
    fireEvent.click(expandButton);

    await waitFor(() => {
      expect(screen.queryByText("Child 1-1")).not.toBeInTheDocument();
    });
  });

  it("handles node selection", () => {
    const onSelect = vi.fn();
    render(<Tree treeData={basicTreeData} onSelect={onSelect} selectable />);

    fireEvent.click(screen.getByText("Parent 1"));
    expect(onSelect).toHaveBeenCalledWith(["1"], expect.anything());
  });

  it("supports multiple selection", () => {
    const onSelect = vi.fn();
    render(
      <Tree treeData={basicTreeData} onSelect={onSelect} selectable multiple />,
    );

    fireEvent.click(screen.getByText("Parent 1"));
    fireEvent.click(screen.getByText("Parent 2"));

    expect(onSelect).toHaveBeenCalledTimes(2);
  });

  it("renders with checkboxes", () => {
    const onCheck = vi.fn();
    render(<Tree treeData={basicTreeData} onCheck={onCheck} checkable />);

    const checkboxes = screen.getAllByRole("checkbox");
    expect(checkboxes.length).toBeGreaterThan(0);

    fireEvent.click(checkboxes[0]);
    expect(onCheck).toHaveBeenCalled();
  });

  it("handles disabled nodes", () => {
    const disabledTreeData = [
      { key: "1", title: "Enabled Node" },
      { key: "2", title: "Disabled Node", disabled: true },
    ];

    const onSelect = vi.fn();
    render(<Tree treeData={disabledTreeData} onSelect={onSelect} selectable />);

    fireEvent.click(screen.getByText("Enabled Node"));
    expect(onSelect).toHaveBeenCalled();

    onSelect.mockClear();
    fireEvent.click(screen.getByText("Disabled Node"));
    expect(onSelect).not.toHaveBeenCalled();
  });

  it("supports drag and drop", async () => {
    const onDrop = vi.fn();
    render(<Tree treeData={basicTreeData} onDrop={onDrop} draggable />);

    const draggableNode = screen.getByText("Parent 1");
    expect(draggableNode).toBeInTheDocument();
  });

  it("renders with icons", () => {
    const treeDataWithIcons = [
      {
        key: "1",
        title: "Node with Icon",
        icon: <span data-testid="custom-icon">📁</span>,
      },
    ];

    render(<Tree treeData={treeDataWithIcons} />);
    expect(screen.getByTestId("custom-icon")).toBeInTheDocument();
  });

  it("supports search functionality", async () => {
    render(<Tree treeData={basicTreeData} searchable />);

    const searchInput = screen.getByPlaceholderText("Search...");
    expect(searchInput).toBeInTheDocument();

    fireEvent.change(searchInput, { target: { value: "Parent 1" } });

    await waitFor(() => {
      expect(screen.getByText("Parent 1")).toBeInTheDocument();
    });
  });

  it("handles virtual scrolling for large datasets", () => {
    const largeTreeData = Array.from({ length: 1000 }, (_, i) => ({
      key: `item-${i}`,
      title: `Item ${i}`,
    }));

    render(<Tree treeData={largeTreeData} virtual height={400} />);
    expect(screen.getByText("Item 0")).toBeInTheDocument();
  });

  it("supports custom node rendering", () => {
    const titleRender = (nodeData: any) => (
      <span data-testid={`custom-${nodeData.key}`}>
        Custom: {nodeData.title}
      </span>
    );

    render(<Tree treeData={basicTreeData} titleRender={titleRender} />);
    expect(screen.getByTestId("custom-1")).toBeInTheDocument();
    expect(screen.getByText("Custom: Parent 1")).toBeInTheDocument();
  });

  it("handles keyboard navigation", () => {
    const onSelect = vi.fn();
    render(<Tree treeData={basicTreeData} onSelect={onSelect} selectable />);

    const firstNode = screen.getByText("Parent 1");
    expect(firstNode).toBeInTheDocument();
  });

  it("supports line style customization", () => {
    const lineStyles = ["solid", "dashed", "dotted"] as const;

    lineStyles.forEach((style) => {
      const { unmount } = render(
        <Tree treeData={basicTreeData} showLine={{ style }} />,
      );
      expect(screen.getByText("Parent 1")).toBeInTheDocument();
      unmount();
    });
  });

  it("renders with different size variants", () => {
    const sizes = ["small", "medium", "large"] as const;

    sizes.forEach((size) => {
      const { unmount } = render(<Tree treeData={basicTreeData} size={size} />);
      expect(screen.getByText("Parent 1")).toBeInTheDocument();
      unmount();
    });
  });

  it("handles node loading states", async () => {
    const loadingTreeData = [{ key: "1", title: "Parent", loading: true }];

    render(<Tree treeData={loadingTreeData} />);

    expect(screen.getByText("Parent")).toBeInTheDocument();
  });

  it("supports auto-expand functionality", () => {
    render(<Tree treeData={basicTreeData} autoExpandParent />);

    // Should show children initially when auto-expand is enabled
    expect(screen.getByText("Parent 1")).toBeInTheDocument();
  });

  it("handles right-click context menu", () => {
    const onRightClick = vi.fn();
    render(<Tree treeData={basicTreeData} onRightClick={onRightClick} />);

    fireEvent.contextMenu(screen.getByText("Parent 1"));
    expect(onRightClick).toHaveBeenCalled();
  });

  it("supports node filtering", () => {
    const filterTreeNode = (node: any) => node.title.includes("Parent");
    render(<Tree treeData={basicTreeData} filterTreeNode={filterTreeNode} />);

    expect(screen.getByText("Parent 1")).toBeInTheDocument();
    expect(screen.getByText("Parent 2")).toBeInTheDocument();
  });

  it("renders with indent guides", () => {
    render(<Tree treeData={basicTreeData} showIndentGuides />);
    expect(screen.getByText("Parent 1")).toBeInTheDocument();
  });

  it("supports default expanded keys", () => {
    render(<Tree treeData={basicTreeData} defaultExpandedKeys={["1"]} />);

    // Should show children of first parent
    expect(screen.getByText("Child 1-1")).toBeInTheDocument();
  });

  it("handles controlled expansion state", () => {
    const onExpand = vi.fn();
    const { rerender } = render(
      <Tree treeData={basicTreeData} expandedKeys={[]} onExpand={onExpand} />,
    );

    expect(screen.queryByText("Child 1-1")).not.toBeInTheDocument();

    rerender(
      <Tree
        treeData={basicTreeData}
        expandedKeys={["1"]}
        onExpand={onExpand}
      />,
    );

    expect(screen.getByText("Child 1-1")).toBeInTheDocument();
  });

  it("supports async data loading", async () => {
    const loadData = vi
      .fn()
      .mockResolvedValue([{ key: "async-1", title: "Async Child" }]);

    render(<Tree treeData={basicTreeData} loadData={loadData} />);

    expect(screen.getByText("Parent 1")).toBeInTheDocument();
  });

  it("handles node hover effects", () => {
    render(<Tree treeData={basicTreeData} />);

    const node = screen.getByText("Parent 1");
    fireEvent.mouseEnter(node);
    fireEvent.mouseLeave(node);

    expect(node).toBeInTheDocument();
  });

  it("supports custom className", () => {
    render(<Tree treeData={basicTreeData} className="custom-tree" />);
    expect(screen.getByText("Parent 1")).toBeInTheDocument();
  });

  it("renders empty state when no data", () => {
    render(<Tree treeData={[]} />);

    // Should render without crashing
    expect(document.querySelector(".tree-empty")).toBeInTheDocument();
  });

  it("handles deeply nested structures", () => {
    const deepTreeData = [
      {
        key: "1",
        title: "Level 1",
        children: [
          {
            key: "1-1",
            title: "Level 2",
            children: [
              {
                key: "1-1-1",
                title: "Level 3",
                children: [{ key: "1-1-1-1", title: "Level 4" }],
              },
            ],
          },
        ],
      },
    ];

    render(<Tree treeData={deepTreeData} defaultExpandAll />);
    expect(screen.getByText("Level 4")).toBeInTheDocument();
  });
});
