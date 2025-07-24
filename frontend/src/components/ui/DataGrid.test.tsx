import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { vi } from "vitest";
import { DataGrid } from "./DataGrid";

interface TestRowData {
  id: number;
  name: string;
  email: string;
  age: number;
  status: "active" | "inactive";
  role: string;
}

describe("DataGrid", () => {
  const mockData: TestRowData[] = [
    {
      id: 1,
      name: "John Doe",
      email: "john@example.com",
      age: 30,
      status: "active",
      role: "admin",
    },
    {
      id: 2,
      name: "Jane Smith",
      email: "jane@example.com",
      age: 25,
      status: "inactive",
      role: "user",
    },
    {
      id: 3,
      name: "Bob Johnson",
      email: "bob@example.com",
      age: 35,
      status: "active",
      role: "editor",
    },
    {
      id: 4,
      name: "Alice Brown",
      email: "alice@example.com",
      age: 28,
      status: "active",
      role: "user",
    },
    {
      id: 5,
      name: "Charlie Wilson",
      email: "charlie@example.com",
      age: 32,
      status: "inactive",
      role: "admin",
    },
  ];

  const mockColumns = [
    { key: "id", header: "ID", sortable: true, width: 80 },
    { key: "name", header: "Name", sortable: true, width: 150 },
    { key: "email", header: "Email", sortable: true, width: 200 },
    { key: "age", header: "Age", sortable: true, width: 100 },
    { key: "status", header: "Status", sortable: true, width: 120 },
    { key: "role", header: "Role", sortable: true, width: 100 },
  ];

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders data grid with data", () => {
    render(<DataGrid data={mockData} columns={mockColumns} />);

    expect(screen.getByTestId("datagrid-container")).toBeInTheDocument();
    expect(screen.getByText("John Doe")).toBeInTheDocument();
    expect(screen.getByText("jane@example.com")).toBeInTheDocument();
  });

  it("displays column headers", () => {
    render(<DataGrid data={mockData} columns={mockColumns} />);

    expect(screen.getByText("ID")).toBeInTheDocument();
    expect(screen.getByText("Name")).toBeInTheDocument();
    expect(screen.getByText("Email")).toBeInTheDocument();
    expect(screen.getByText("Age")).toBeInTheDocument();
    expect(screen.getByText("Status")).toBeInTheDocument();
    expect(screen.getByText("Role")).toBeInTheDocument();
  });

  it("supports column sorting", () => {
    const onSort = vi.fn();
    render(
      <DataGrid
        data={mockData}
        columns={mockColumns}
        onSort={onSort}
        sortable
      />,
    );

    const nameHeader = screen.getByTestId("column-header-name");
    fireEvent.click(nameHeader);

    expect(onSort).toHaveBeenCalledWith("name", "asc");
  });

  it("toggles sort direction on multiple clicks", () => {
    const onSort = vi.fn();
    render(
      <DataGrid
        data={mockData}
        columns={mockColumns}
        onSort={onSort}
        sortable
      />,
    );

    const nameHeader = screen.getByTestId("column-header-name");
    fireEvent.click(nameHeader);
    expect(onSort).toHaveBeenCalledWith("name", "asc");

    fireEvent.click(nameHeader);
    expect(onSort).toHaveBeenCalledWith("name", "desc");
  });

  it("supports row selection", () => {
    const onSelectionChange = vi.fn();
    render(
      <DataGrid
        data={mockData}
        columns={mockColumns}
        selectable
        onSelectionChange={onSelectionChange}
      />,
    );

    const firstCheckbox = screen.getByTestId("row-checkbox-1");
    fireEvent.click(firstCheckbox);

    expect(onSelectionChange).toHaveBeenCalledWith([1]);
  });

  it("supports select all functionality", () => {
    const onSelectionChange = vi.fn();
    render(
      <DataGrid
        data={mockData}
        columns={mockColumns}
        selectable
        onSelectionChange={onSelectionChange}
      />,
    );

    const selectAllCheckbox = screen.getByTestId("select-all-checkbox");
    fireEvent.click(selectAllCheckbox);

    expect(onSelectionChange).toHaveBeenCalledWith([1, 2, 3, 4, 5]);
  });

  it("supports pagination", () => {
    render(
      <DataGrid
        data={mockData}
        columns={mockColumns}
        pagination
        pageSize={2}
      />,
    );

    expect(screen.getByTestId("datagrid-pagination")).toBeInTheDocument();
    expect(screen.getByText("John Doe")).toBeInTheDocument();
    expect(screen.getByText("Jane Smith")).toBeInTheDocument();
    expect(screen.queryByText("Bob Johnson")).not.toBeInTheDocument();
  });

  it("handles page navigation", () => {
    const onPageChange = vi.fn();
    render(
      <DataGrid
        data={mockData}
        columns={mockColumns}
        pagination
        pageSize={2}
        onPageChange={onPageChange}
      />,
    );

    const nextButton = screen.getByTestId("pagination-next");
    fireEvent.click(nextButton);

    expect(onPageChange).toHaveBeenCalledWith(2);
  });

  it("supports row click events", () => {
    const onRowClick = vi.fn();
    render(
      <DataGrid
        data={mockData}
        columns={mockColumns}
        onRowClick={onRowClick}
      />,
    );

    const firstRow = screen.getByTestId("data-row-1");
    fireEvent.click(firstRow);

    expect(onRowClick).toHaveBeenCalledWith(mockData[0], expect.any(Object));
  });

  it("supports custom cell rendering", () => {
    const customColumns = [
      ...mockColumns,
      {
        key: "actions",
        header: "Actions",
        render: (row: TestRowData) => (
          <button data-testid={`action-${row.id}`}>Edit</button>
        ),
      },
    ];

    render(<DataGrid data={mockData} columns={customColumns} />);

    expect(screen.getByTestId("action-1")).toBeInTheDocument();
    expect(screen.getAllByText("Edit")).toHaveLength(5);
  });

  it("supports filtering", () => {
    render(
      <DataGrid
        data={mockData}
        columns={mockColumns}
        filterable
        globalFilter="john"
      />,
    );

    expect(screen.getByText("John Doe")).toBeInTheDocument();
    expect(screen.getByText("Bob Johnson")).toBeInTheDocument();
    expect(screen.queryByText("Jane Smith")).not.toBeInTheDocument();
  });

  it("displays filter input when filterable", () => {
    render(<DataGrid data={mockData} columns={mockColumns} filterable />);

    expect(screen.getByTestId("global-filter-input")).toBeInTheDocument();
  });

  it("supports column filtering", () => {
    const onFilter = vi.fn();
    render(
      <DataGrid
        data={mockData}
        columns={mockColumns}
        filterable
        onFilter={onFilter}
      />,
    );

    const filterInput = screen
      .getByTestId("global-filter-input")
      .querySelector("input");
    fireEvent.change(filterInput!, { target: { value: "admin" } });

    expect(onFilter).toHaveBeenCalledWith("admin");
  });

  it("supports loading state", () => {
    render(<DataGrid data={[]} columns={mockColumns} loading />);

    expect(screen.getByTestId("datagrid-loading")).toBeInTheDocument();
    expect(screen.queryByText("John Doe")).not.toBeInTheDocument();
  });

  it("supports empty state", () => {
    render(<DataGrid data={[]} columns={mockColumns} />);

    expect(screen.getByTestId("datagrid-empty")).toBeInTheDocument();
  });

  it("supports custom empty state", () => {
    const customEmpty = <div data-testid="custom-empty">No data found</div>;
    render(
      <DataGrid data={[]} columns={mockColumns} emptyState={customEmpty} />,
    );

    expect(screen.getByTestId("custom-empty")).toBeInTheDocument();
  });

  it("supports different sizes", () => {
    const sizes = ["sm", "md", "lg"] as const;

    sizes.forEach((size) => {
      const { unmount } = render(
        <DataGrid data={mockData} columns={mockColumns} size={size} />,
      );
      const container = screen.getByTestId("datagrid-container");
      expect(container).toHaveClass(`size-${size}`);
      unmount();
    });
  });

  it("supports different variants", () => {
    const variants = ["default", "striped", "bordered"] as const;

    variants.forEach((variant) => {
      const { unmount } = render(
        <DataGrid data={mockData} columns={mockColumns} variant={variant} />,
      );
      const container = screen.getByTestId("datagrid-container");
      expect(container).toHaveClass(`variant-${variant}`);
      unmount();
    });
  });

  it("supports row hover effects", () => {
    render(<DataGrid data={mockData} columns={mockColumns} hoverable />);

    const container = screen.getByTestId("datagrid-container");
    expect(container).toHaveClass("hoverable");
  });

  it("supports sticky headers", () => {
    render(<DataGrid data={mockData} columns={mockColumns} stickyHeader />);

    const header = screen.getByTestId("datagrid-header");
    expect(header).toHaveClass("sticky");
  });

  it("supports column resizing", () => {
    const onColumnResize = vi.fn();
    render(
      <DataGrid
        data={mockData}
        columns={mockColumns}
        resizable
        onColumnResize={onColumnResize}
      />,
    );

    expect(screen.getByTestId("column-resizer-name")).toBeInTheDocument();
  });

  it("supports column reordering", () => {
    const onColumnReorder = vi.fn();
    render(
      <DataGrid
        data={mockData}
        columns={mockColumns}
        reorderable
        onColumnReorder={onColumnReorder}
      />,
    );

    const nameHeader = screen.getByTestId("column-header-name");
    expect(nameHeader).toHaveAttribute("draggable", "true");
  });

  it("supports expandable rows", () => {
    const expandContent = (row: TestRowData) => (
      <div data-testid={`expand-${row.id}`}>Details for {row.name}</div>
    );

    render(
      <DataGrid
        data={mockData}
        columns={mockColumns}
        expandable
        expandContent={expandContent}
      />,
    );

    const expandButton = screen.getByTestId("expand-button-1");
    fireEvent.click(expandButton);

    expect(screen.getByTestId("expand-1")).toBeInTheDocument();
  });

  it("supports row grouping", () => {
    render(<DataGrid data={mockData} columns={mockColumns} groupBy="role" />);

    expect(screen.getByTestId("group-admin")).toBeInTheDocument();
    expect(screen.getByTestId("group-user")).toBeInTheDocument();
    expect(screen.getByTestId("group-editor")).toBeInTheDocument();
  });

  it("supports virtual scrolling", () => {
    render(
      <DataGrid
        data={mockData}
        columns={mockColumns}
        virtualScroll
        height={400}
      />,
    );

    const container = screen.getByTestId("datagrid-container");
    expect(container).toHaveClass("virtual-scroll");
  });

  it("supports toolbar actions", () => {
    const toolbar = (
      <div data-testid="custom-toolbar">
        <button>Export</button>
        <button>Import</button>
      </div>
    );

    render(
      <DataGrid data={mockData} columns={mockColumns} toolbar={toolbar} />,
    );

    expect(screen.getByTestId("custom-toolbar")).toBeInTheDocument();
  });

  it("supports bulk actions", () => {
    const bulkActions = [
      { id: "delete", label: "Delete", onClick: vi.fn() },
      { id: "export", label: "Export", onClick: vi.fn() },
    ];

    render(
      <DataGrid
        data={mockData}
        columns={mockColumns}
        selectable
        bulkActions={bulkActions}
        selectedRows={[1, 2]}
      />,
    );

    expect(screen.getByTestId("bulk-actions")).toBeInTheDocument();
    expect(screen.getByText("Delete")).toBeInTheDocument();
    expect(screen.getByText("Export")).toBeInTheDocument();
  });

  it("handles bulk action clicks", () => {
    const deleteAction = vi.fn();
    const bulkActions = [
      { id: "delete", label: "Delete", onClick: deleteAction },
    ];

    render(
      <DataGrid
        data={mockData}
        columns={mockColumns}
        selectable
        bulkActions={bulkActions}
        selectedRows={[1, 2]}
      />,
    );

    const deleteButton = screen.getByTestId("bulk-action-delete");
    fireEvent.click(deleteButton);

    expect(deleteAction).toHaveBeenCalledWith([1, 2]);
  });

  it("supports column visibility toggle", () => {
    const onColumnVisibilityChange = vi.fn();
    render(
      <DataGrid
        data={mockData}
        columns={mockColumns}
        columnVisibility
        onColumnVisibilityChange={onColumnVisibilityChange}
      />,
    );

    expect(screen.getByTestId("column-visibility-toggle")).toBeInTheDocument();
  });

  it("supports export functionality", () => {
    const onExport = vi.fn();
    render(
      <DataGrid
        data={mockData}
        columns={mockColumns}
        exportable
        onExport={onExport}
      />,
    );

    const exportButton = screen.getByTestId("export-button");
    fireEvent.click(exportButton);

    expect(onExport).toHaveBeenCalledWith("csv");
  });

  it("supports different export formats", () => {
    const onExport = vi.fn();
    render(
      <DataGrid
        data={mockData}
        columns={mockColumns}
        exportable
        exportFormats={["csv", "xlsx", "json"]}
        onExport={onExport}
      />,
    );

    const exportButton = screen.getByTestId("export-button");
    fireEvent.click(exportButton);

    const xlsxOption = screen.getByTestId("export-xlsx");
    fireEvent.click(xlsxOption);

    expect(onExport).toHaveBeenCalledWith("xlsx");
  });

  it("supports keyboard navigation", () => {
    render(<DataGrid data={mockData} columns={mockColumns} />);

    const firstCell = screen.getByTestId("cell-1-name");
    firstCell.focus();

    fireEvent.keyDown(firstCell, { key: "ArrowDown" });

    const secondCell = screen.getByTestId("cell-2-name");
    expect(secondCell).toHaveFocus();
  });

  it("supports cell editing", () => {
    const onCellEdit = vi.fn();
    render(
      <DataGrid
        data={mockData}
        columns={mockColumns}
        editable
        onCellEdit={onCellEdit}
      />,
    );

    const nameCell = screen.getByTestId("cell-1-name");
    fireEvent.doubleClick(nameCell);

    const input = screen.getByTestId("cell-editor-1-name");
    fireEvent.change(input, { target: { value: "Updated Name" } });
    fireEvent.keyDown(input, { key: "Enter" });

    expect(onCellEdit).toHaveBeenCalledWith(1, "name", "Updated Name");
  });

  it("supports row drag and drop", () => {
    const onRowReorder = vi.fn();
    render(
      <DataGrid
        data={mockData}
        columns={mockColumns}
        draggableRows
        onRowReorder={onRowReorder}
      />,
    );

    const firstRow = screen.getByTestId("data-row-1");
    expect(firstRow).toHaveAttribute("draggable", "true");
  });

  it("supports custom row styling", () => {
    const getRowProps = (row: TestRowData) => ({
      className: row.status === "active" ? "active-row" : "inactive-row",
    });

    render(
      <DataGrid
        data={mockData}
        columns={mockColumns}
        getRowProps={getRowProps}
      />,
    );

    const activeRow = screen.getByTestId("data-row-1");
    expect(activeRow).toHaveClass("active-row");
  });

  it("supports context menu", () => {
    const contextMenuItems = [
      { label: "Edit", onClick: vi.fn() },
      { label: "Delete", onClick: vi.fn() },
    ];

    render(
      <DataGrid
        data={mockData}
        columns={mockColumns}
        contextMenu={contextMenuItems}
      />,
    );

    const firstRow = screen.getByTestId("data-row-1");
    fireEvent.contextMenu(firstRow);

    expect(screen.getByTestId("context-menu")).toBeInTheDocument();
  });

  it("supports frozen columns", () => {
    const columnsWithFrozen = mockColumns.map((col, index) => ({
      ...col,
      frozen: index < 2,
    }));

    render(<DataGrid data={mockData} columns={columnsWithFrozen} />);

    const frozenColumn = screen.getByTestId("column-header-id");
    expect(frozenColumn).toHaveClass("frozen");
  });

  it("supports multi-sort", () => {
    const onMultiSort = vi.fn();
    render(
      <DataGrid
        data={mockData}
        columns={mockColumns}
        sortable
        multiSort
        onMultiSort={onMultiSort}
      />,
    );

    const nameHeader = screen.getByTestId("column-header-name");
    fireEvent.click(nameHeader);

    expect(onMultiSort).toHaveBeenCalledWith([
      { key: "name", direction: "asc" },
    ]);
  });

  it("supports custom styling", () => {
    render(
      <DataGrid
        data={mockData}
        columns={mockColumns}
        className="custom-grid"
      />,
    );

    const container = screen.getByTestId("datagrid-container");
    expect(container).toHaveClass("custom-grid");
  });

  it("supports custom data attributes", () => {
    render(
      <DataGrid
        data={mockData}
        columns={mockColumns}
        data-category="user-management"
        data-id="main-grid"
      />,
    );

    const container = screen.getByTestId("datagrid-container");
    expect(container).toHaveAttribute("data-category", "user-management");
    expect(container).toHaveAttribute("data-id", "main-grid");
  });

  it("supports accessibility attributes", () => {
    render(
      <DataGrid
        data={mockData}
        columns={mockColumns}
        ariaLabel="User data table"
        ariaDescribedBy="table-description"
      />,
    );

    const table = screen.getByRole("table");
    expect(table).toHaveAttribute("aria-label", "User data table");
    expect(table).toHaveAttribute("aria-describedby", "table-description");
  });

  it("handles large datasets efficiently", () => {
    const largeDataset = Array.from({ length: 1000 }, (_, i) => ({
      id: i + 1,
      name: `User ${i + 1}`,
      email: `user${i + 1}@example.com`,
      age: 20 + (i % 50),
      status: i % 2 === 0 ? ("active" as const) : ("inactive" as const),
      role: ["admin", "user", "editor"][i % 3],
    }));

    render(
      <DataGrid
        data={largeDataset}
        columns={mockColumns}
        virtualScroll
        height={400}
      />,
    );

    expect(screen.getByTestId("datagrid-container")).toBeInTheDocument();
    expect(screen.getByText("User 1")).toBeInTheDocument();
  });
});
