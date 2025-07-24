import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { vi } from 'vitest';
import { DataTable } from './EnhancedDataTable';

interface MockData {
  id: number;
  name: string;
  email: string;
  role: string;
  status: 'active' | 'inactive';
  created: string;
  salary: number;
}

describe('DataTable', () => {
  const mockData: MockData[] = [
    { id: 1, name: 'John Doe', email: 'john@example.com', role: 'Admin', status: 'active', created: '2023-01-15', salary: 75000 },
    { id: 2, name: 'Jane Smith', email: 'jane@example.com', role: 'User', status: 'active', created: '2023-02-20', salary: 65000 },
    { id: 3, name: 'Bob Johnson', email: 'bob@example.com', role: 'Manager', status: 'inactive', created: '2023-03-10', salary: 85000 },
    { id: 4, name: 'Alice Brown', email: 'alice@example.com', role: 'User', status: 'active', created: '2023-04-05', salary: 60000 },
    { id: 5, name: 'Charlie Wilson', email: 'charlie@example.com', role: 'Admin', status: 'active', created: '2023-05-12', salary: 80000 }
  ];

  const mockColumns = [
    { key: 'id', header: 'ID', sortable: true, width: 80 },
    { key: 'name', header: 'Name', sortable: true, filterable: true },
    { key: 'email', header: 'Email', sortable: true, filterable: true },
    { key: 'role', header: 'Role', filterable: true },
    { key: 'status', header: 'Status', filterable: true },
    { key: 'created', header: 'Created', sortable: true, type: 'date' as const },
    { key: 'salary', header: 'Salary', sortable: true, type: 'number' as const, align: 'right' as const }
  ];

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders data table with data', () => {
    render(<DataTable data={mockData} columns={mockColumns} />);
    
    expect(screen.getByTestId('datatable-container')).toBeInTheDocument();
    expect(screen.getByText('John Doe')).toBeInTheDocument();
    expect(screen.getByText('jane@example.com')).toBeInTheDocument();
    expect(screen.getByText('Manager')).toBeInTheDocument();
  });

  it('supports column sorting', () => {
    const onSort = vi.fn();
    
    render(
      <DataTable 
        data={mockData} 
        columns={mockColumns}
        sortable
        onSort={onSort}
      />
    );
    
    const nameHeader = screen.getByTestId('column-header-name');
    fireEvent.click(nameHeader);
    
    expect(onSort).toHaveBeenCalledWith('name', 'asc');
  });

  it('supports multi-column sorting', () => {
    const onMultiSort = vi.fn();
    
    render(
      <DataTable 
        data={mockData} 
        columns={mockColumns}
        sortable
        multiSort
        onMultiSort={onMultiSort}
      />
    );
    
    const nameHeader = screen.getByTestId('column-header-name');
    fireEvent.click(nameHeader);
    
    expect(onMultiSort).toHaveBeenCalledWith([{ key: 'name', direction: 'asc' }]);
  });

  it('supports global filtering', () => {
    const onFilter = vi.fn();
    
    render(
      <DataTable 
        data={mockData} 
        columns={mockColumns}
        filterable
        onFilter={onFilter}
      />
    );
    
    const filterInput = screen.getByTestId('global-filter-input');
    fireEvent.change(filterInput.querySelector('input')!, { target: { value: 'john' } });
    
    expect(onFilter).toHaveBeenCalledWith('john');
  });

  it('supports column-specific filtering', () => {
    const onColumnFilter = vi.fn();
    
    render(
      <DataTable 
        data={mockData} 
        columns={mockColumns}
        filterable
        onColumnFilter={onColumnFilter}
      />
    );
    
    expect(screen.getByTestId('datatable-container')).toBeInTheDocument();
  });

  it('supports row selection', () => {
    const onSelectionChange = vi.fn();
    
    render(
      <DataTable 
        data={mockData} 
        columns={mockColumns}
        selectable
        onSelectionChange={onSelectionChange}
      />
    );
    
    const firstRowCheckbox = screen.getByTestId('row-checkbox-1');
    fireEvent.click(firstRowCheckbox);
    
    expect(onSelectionChange).toHaveBeenCalledWith([1]);
  });

  it('supports select all functionality', () => {
    const onSelectionChange = vi.fn();
    
    render(
      <DataTable 
        data={mockData} 
        columns={mockColumns}
        selectable
        multiSelect
        onSelectionChange={onSelectionChange}
      />
    );
    
    const selectAllCheckbox = screen.getByTestId('select-all-checkbox');
    fireEvent.click(selectAllCheckbox);
    
    expect(onSelectionChange).toHaveBeenCalledWith([1, 2, 3, 4, 5]);
  });

  it('supports pagination', () => {
    const onPageChange = vi.fn();
    
    render(
      <DataTable 
        data={mockData} 
        columns={mockColumns}
        pagination
        pageSize={2}
        onPageChange={onPageChange}
      />
    );
    
    expect(screen.getByTestId('datatable-pagination')).toBeInTheDocument();
    
    const nextButton = screen.getByTestId('pagination-next');
    fireEvent.click(nextButton);
    
    expect(onPageChange).toHaveBeenCalledWith(2);
  });

  it('supports expandable rows', () => {
    const expandContent = (row: MockData) => <div data-testid={`expanded-${row.id}`}>Details for {row.name}</div>;
    
    render(
      <DataTable 
        data={mockData} 
        columns={mockColumns}
        expandable
        expandContent={expandContent}
      />
    );
    
    const expandButton = screen.getByTestId('expand-button-1');
    fireEvent.click(expandButton);
    
    expect(screen.getByTestId('expanded-1')).toBeInTheDocument();
    expect(screen.getByText('Details for John Doe')).toBeInTheDocument();
  });

  it('supports different table sizes', () => {
    const sizes = ['sm', 'md', 'lg'] as const;
    
    sizes.forEach(size => {
      const { unmount } = render(
        <DataTable data={mockData} columns={mockColumns} size={size} />
      );
      const container = screen.getByTestId('datatable-container');
      expect(container).toHaveClass(`size-${size}`);
      unmount();
    });
  });

  it('supports different table variants', () => {
    const variants = ['default', 'striped', 'bordered'] as const;
    
    variants.forEach(variant => {
      const { unmount } = render(
        <DataTable data={mockData} columns={mockColumns} variant={variant} />
      );
      const container = screen.getByTestId('datatable-container');
      expect(container).toHaveClass(`variant-${variant}`);
      unmount();
    });
  });

  it('supports hover effects', () => {
    render(<DataTable data={mockData} columns={mockColumns} hoverable />);
    
    const container = screen.getByTestId('datatable-container');
    expect(container).toHaveClass('hoverable');
  });

  it('supports loading state', () => {
    render(<DataTable data={mockData} columns={mockColumns} loading />);
    
    expect(screen.getByTestId('datatable-loading')).toBeInTheDocument();
  });

  it('supports empty state', () => {
    render(<DataTable data={[]} columns={mockColumns} />);
    
    expect(screen.getByTestId('datatable-empty')).toBeInTheDocument();
    expect(screen.getByText('No data available')).toBeInTheDocument();
  });

  it('supports custom empty state', () => {
    const customEmpty = <div data-testid="custom-empty">No users found</div>;
    
    render(<DataTable data={[]} columns={mockColumns} emptyState={customEmpty} />);
    
    expect(screen.getByTestId('custom-empty')).toBeInTheDocument();
    expect(screen.getByText('No users found')).toBeInTheDocument();
  });

  it('supports row grouping', () => {
    render(
      <DataTable 
        data={mockData} 
        columns={mockColumns}
        groupBy="role"
      />
    );
    
    expect(screen.getByTestId('group-Admin')).toBeInTheDocument();
    expect(screen.getByTestId('group-User')).toBeInTheDocument();
    expect(screen.getByTestId('group-Manager')).toBeInTheDocument();
  });

  it('supports virtual scrolling', () => {
    render(
      <DataTable 
        data={mockData} 
        columns={mockColumns}
        virtualScroll
        height={400}
      />
    );
    
    const container = screen.getByTestId('datatable-container');
    expect(container).toHaveClass('virtual-scroll');
  });

  it('supports sticky header', () => {
    render(<DataTable data={mockData} columns={mockColumns} stickyHeader />);
    
    const header = screen.getByTestId('datatable-header');
    expect(header).toHaveClass('sticky');
  });

  it('supports column resizing', () => {
    const onColumnResize = vi.fn();
    
    render(
      <DataTable 
        data={mockData} 
        columns={mockColumns}
        resizable
        onColumnResize={onColumnResize}
      />
    );
    
    const resizer = screen.getByTestId('column-resizer-name');
    expect(resizer).toBeInTheDocument();
  });

  it('supports column reordering', () => {
    const onColumnReorder = vi.fn();
    
    render(
      <DataTable 
        data={mockData} 
        columns={mockColumns}
        reorderable
        onColumnReorder={onColumnReorder}
      />
    );
    
    const nameHeader = screen.getByTestId('column-header-name');
    expect(nameHeader).toHaveAttribute('draggable', 'true');
  });

  it('supports row drag and drop', () => {
    const onRowReorder = vi.fn();
    
    render(
      <DataTable 
        data={mockData} 
        columns={mockColumns}
        draggableRows
        onRowReorder={onRowReorder}
      />
    );
    
    const firstRow = screen.getByTestId('data-row-1');
    expect(firstRow).toHaveAttribute('draggable', 'true');
  });

  it('supports cell editing', () => {
    const onCellEdit = vi.fn();
    
    render(
      <DataTable 
        data={mockData} 
        columns={mockColumns}
        editable
        onCellEdit={onCellEdit}
      />
    );
    
    const nameCell = screen.getByTestId('cell-1-name');
    fireEvent.doubleClick(nameCell);
    
    expect(screen.getByTestId('cell-editor-1-name')).toBeInTheDocument();
  });

  it('supports bulk actions', () => {
    const bulkActions = [
      { id: 'delete', label: 'Delete', onClick: vi.fn() },
      { id: 'export', label: 'Export', onClick: vi.fn() }
    ];
    
    render(
      <DataTable 
        data={mockData} 
        columns={mockColumns}
        selectable
        selectedRows={[1, 2]}
        bulkActions={bulkActions}
      />
    );
    
    expect(screen.getByTestId('bulk-actions')).toBeInTheDocument();
    
    const deleteAction = screen.getByTestId('bulk-action-delete');
    fireEvent.click(deleteAction);
    
    expect(bulkActions[0].onClick).toHaveBeenCalledWith([1, 2]);
  });

  it('supports context menu', () => {
    const contextMenu = [
      { label: 'Edit', onClick: vi.fn() },
      { label: 'Delete', onClick: vi.fn() }
    ];
    
    render(
      <DataTable 
        data={mockData} 
        columns={mockColumns}
        contextMenu={contextMenu}
      />
    );
    
    const firstRow = screen.getByTestId('data-row-1');
    fireEvent.contextMenu(firstRow);
    
    expect(screen.getByTestId('context-menu')).toBeInTheDocument();
  });

  it('supports export functionality', () => {
    const onExport = vi.fn();
    
    render(
      <DataTable 
        data={mockData} 
        columns={mockColumns}
        exportable
        onExport={onExport}
      />
    );
    
    const exportButton = screen.getByTestId('export-button');
    fireEvent.click(exportButton);
    
    expect(onExport).toHaveBeenCalledWith('csv');
  });

  it('supports column visibility toggle', () => {
    const onColumnVisibilityChange = vi.fn();
    
    render(
      <DataTable 
        data={mockData} 
        columns={mockColumns}
        columnVisibility
        onColumnVisibilityChange={onColumnVisibilityChange}
      />
    );
    
    const columnToggle = screen.getByTestId('column-visibility-toggle');
    expect(columnToggle).toBeInTheDocument();
  });

  it('supports keyboard navigation', () => {
    render(<DataTable data={mockData} columns={mockColumns} />);
    
    const firstCell = screen.getByTestId('cell-1-name');
    firstCell.focus();
    
    fireEvent.keyDown(firstCell, { key: 'ArrowDown' });
    
    const secondCell = screen.getByTestId('cell-2-name');
    expect(secondCell).toHaveClass('focused');
  });

  it('supports custom cell rendering', () => {
    const customColumns = [
      ...mockColumns,
      {
        key: 'actions',
        header: 'Actions',
        render: (row: MockData) => (
          <button data-testid={`action-${row.id}`}>Edit {row.name}</button>
        )
      }
    ];
    
    render(<DataTable data={mockData} columns={customColumns} />);
    
    expect(screen.getByTestId('action-1')).toBeInTheDocument();
    expect(screen.getByText('Edit John Doe')).toBeInTheDocument();
  });

  it('supports custom header rendering', () => {
    const customColumns = [
      {
        ...mockColumns[0],
        renderHeader: () => <span data-testid="custom-header">Custom ID</span>
      },
      ...mockColumns.slice(1)
    ];
    
    render(<DataTable data={mockData} columns={customColumns} />);
    
    expect(screen.getByTestId('custom-header')).toBeInTheDocument();
    expect(screen.getByText('Custom ID')).toBeInTheDocument();
  });

  it('supports frozen columns', () => {
    const frozenColumns = [
      { ...mockColumns[0], frozen: true },
      ...mockColumns.slice(1)
    ];
    
    render(<DataTable data={mockData} columns={frozenColumns} />);
    
    const idHeader = screen.getByTestId('column-header-id');
    expect(idHeader).toHaveClass('frozen');
  });

  it('supports row click events', () => {
    const onRowClick = vi.fn();
    
    render(
      <DataTable 
        data={mockData} 
        columns={mockColumns}
        onRowClick={onRowClick}
      />
    );
    
    const firstRow = screen.getByTestId('data-row-1');
    fireEvent.click(firstRow);
    
    expect(onRowClick).toHaveBeenCalledWith(mockData[0], expect.any(Object));
  });

  it('supports row double click events', () => {
    const onRowDoubleClick = vi.fn();
    
    render(
      <DataTable 
        data={mockData} 
        columns={mockColumns}
        onRowDoubleClick={onRowDoubleClick}
      />
    );
    
    const firstRow = screen.getByTestId('data-row-1');
    fireEvent.doubleClick(firstRow);
    
    expect(onRowDoubleClick).toHaveBeenCalledWith(mockData[0], expect.any(Object));
  });

  it('supports cell click events', () => {
    const onCellClick = vi.fn();
    
    render(
      <DataTable 
        data={mockData} 
        columns={mockColumns}
        onCellClick={onCellClick}
      />
    );
    
    const nameCell = screen.getByTestId('cell-1-name');
    fireEvent.click(nameCell);
    
    expect(onCellClick).toHaveBeenCalledWith(mockData[0], mockColumns[1], expect.any(Object));
  });

  it('supports custom row props', () => {
    const getRowProps = (row: MockData) => ({
      className: `status-${row.status}`,
      'data-role': row.role
    });
    
    render(
      <DataTable 
        data={mockData} 
        columns={mockColumns}
        getRowProps={getRowProps}
      />
    );
    
    const firstRow = screen.getByTestId('data-row-1');
    expect(firstRow).toHaveClass('status-active');
    expect(firstRow).toHaveAttribute('data-role', 'Admin');
  });

  it('supports custom cell props', () => {
    const getCellProps = (row: MockData, column: any) => ({
      className: column.key === 'status' ? `cell-${row.status}` : '',
      style: column.key === 'salary' ? { fontWeight: 'bold' } : {}
    });
    
    render(
      <DataTable 
        data={mockData} 
        columns={mockColumns}
        getCellProps={getCellProps}
      />
    );
    
    const statusCell = screen.getByTestId('cell-1-status');
    expect(statusCell).toHaveClass('cell-active');
  });

  it('supports accessibility features', () => {
    render(
      <DataTable 
        data={mockData} 
        columns={mockColumns}
        ariaLabel="User data table"
        ariaDescribedBy="table-description"
      />
    );
    
    const table = screen.getByRole('table');
    expect(table).toHaveAttribute('aria-label', 'User data table');
    expect(table).toHaveAttribute('aria-describedby', 'table-description');
  });

  it('supports custom styling', () => {
    render(<DataTable data={mockData} columns={mockColumns} className="custom-table" />);
    
    const container = screen.getByTestId('datatable-container');
    expect(container).toHaveClass('custom-table');
  });

  it('supports custom data attributes', () => {
    render(
      <DataTable 
        data={mockData} 
        columns={mockColumns}
        data-category="users"
        data-id="main-table"
      />
    );
    
    const container = screen.getByTestId('datatable-container');
    expect(container).toHaveAttribute('data-category', 'users');
    expect(container).toHaveAttribute('data-id', 'main-table');
  });

  it('handles server-side pagination', () => {
    const onPageChange = vi.fn();
    
    render(
      <DataTable 
        data={mockData} 
        columns={mockColumns}
        pagination
        totalPages={10}
        totalRows={50}
        currentPage={1}
        pageSize={5}
        onPageChange={onPageChange}
      />
    );
    
    expect(screen.getByText(/Showing 1 to \d+ of 50 entries/)).toBeInTheDocument();
  });

  it('supports page size changes', () => {
    const onPageSizeChange = vi.fn();
    
    render(
      <DataTable 
        data={mockData} 
        columns={mockColumns}
        pagination
        pageSize={10}
        onPageSizeChange={onPageSizeChange}
      />
    );
    
    expect(screen.getByTestId('datatable-pagination')).toBeInTheDocument();
  });

  it('supports column alignment', () => {
    render(<DataTable data={mockData} columns={mockColumns} />);
    
    const salaryCell = screen.getByTestId('cell-1-salary');
    expect(salaryCell).toHaveClass('text-right');
  });

  it('supports different column types', () => {
    render(<DataTable data={mockData} columns={mockColumns} />);
    
    // Number type
    expect(screen.getByText('75000')).toBeInTheDocument();
    
    // Date type
    expect(screen.getByText('2023-01-15')).toBeInTheDocument();
  });

  it('supports responsive design', () => {
    render(<DataTable data={mockData} columns={mockColumns} responsive />);
    
    const container = screen.getByTestId('datatable-container');
    expect(container).toHaveClass('responsive');
  });

  it('supports toolbar customization', () => {
    const customToolbar = <div data-testid="custom-toolbar">Custom Actions</div>;
    
    render(
      <DataTable 
        data={mockData} 
        columns={mockColumns}
        toolbar={customToolbar}
      />
    );
    
    expect(screen.getByTestId('custom-toolbar')).toBeInTheDocument();
  });

  it('handles large datasets efficiently', () => {
    const largeData = Array.from({ length: 1000 }, (_, i) => ({
      id: i + 1,
      name: `User ${i + 1}`,
      email: `user${i + 1}@example.com`,
      role: 'User',
      status: 'active' as const,
      created: '2023-01-01',
      salary: 50000 + i * 100
    }));
    
    render(
      <DataTable 
        data={largeData} 
        columns={mockColumns}
        virtualScroll
        height={400}
      />
    );
    
    expect(screen.getByTestId('datatable-container')).toBeInTheDocument();
  });

  it('supports column width constraints', () => {
    const constrainedColumns = [
      { ...mockColumns[0], minWidth: 100, maxWidth: 200 },
      ...mockColumns.slice(1)
    ];
    
    render(<DataTable data={mockData} columns={constrainedColumns} />);
    
    const idHeader = screen.getByTestId('column-header-id');
    expect(idHeader).toBeInTheDocument();
  });

  it('supports dynamic column visibility', () => {
    render(
      <DataTable 
        data={mockData} 
        columns={mockColumns}
        hiddenColumns={['email', 'created']}
      />
    );
    
    expect(screen.queryByText('Email')).not.toBeInTheDocument();
    expect(screen.queryByText('Created')).not.toBeInTheDocument();
    expect(screen.getByText('Name')).toBeInTheDocument();
  });

  it('supports performance monitoring', () => {
    const onPerformanceReport = vi.fn();
    
    render(
      <DataTable 
        data={mockData} 
        columns={mockColumns}
        enablePerformanceMonitoring
        onPerformanceReport={onPerformanceReport}
      />
    );
    
    expect(screen.getByTestId('datatable-container')).toBeInTheDocument();
  });
});