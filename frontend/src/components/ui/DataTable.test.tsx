import { render, fireEvent, screen } from '@testing-library/react';
import { DataTable, Column } from './DataTable';

interface TestData {
  id: string;
  name: string;
  age: number;
  email: string;
  status: 'active' | 'inactive';
}

const mockData: TestData[] = [
  { id: '1', name: 'John Doe', age: 30, email: 'john@example.com', status: 'active' },
  { id: '2', name: 'Jane Smith', age: 25, email: 'jane@example.com', status: 'inactive' },
  { id: '3', name: 'Bob Johnson', age: 35, email: 'bob@example.com', status: 'active' }
];

const mockColumns: Column<TestData>[] = [
  { key: 'name', title: 'Name', dataIndex: 'name', sortable: true },
  { key: 'age', title: 'Age', dataIndex: 'age', sortable: true },
  { key: 'email', title: 'Email', dataIndex: 'email' },
  { 
    key: 'status', 
    title: 'Status', 
    dataIndex: 'status',
    render: (value) => (
      <span className={value === 'active' ? 'text-green-600' : 'text-red-600'}>
        {value}
      </span>
    )
  }
];

describe('DataTable', () => {
  it('renders table with data', () => {
    render(<DataTable columns={mockColumns} dataSource={mockData} />);
    
    expect(screen.getByText('John Doe')).toBeInTheDocument();
    expect(screen.getByText('Jane Smith')).toBeInTheDocument();
    expect(screen.getByText('Bob Johnson')).toBeInTheDocument();
  });

  it('renders column headers', () => {
    render(<DataTable columns={mockColumns} dataSource={mockData} />);
    
    expect(screen.getByText('Name')).toBeInTheDocument();
    expect(screen.getByText('Age')).toBeInTheDocument();
    expect(screen.getByText('Email')).toBeInTheDocument();
    expect(screen.getByText('Status')).toBeInTheDocument();
  });

  it('renders custom cell content with render function', () => {
    render(<DataTable columns={mockColumns} dataSource={mockData} />);
    
    const activeStatus = screen.getAllByText('active');
    expect(activeStatus[0]).toHaveClass('text-green-600');
    
    const inactiveStatus = screen.getByText('inactive');
    expect(inactiveStatus).toHaveClass('text-red-600');
  });

  it('shows loading state', () => {
    render(<DataTable columns={mockColumns} dataSource={[]} loading={true} />);
    
    expect(screen.getByText('Loading...')).toBeInTheDocument();
    expect(screen.getByRole('img', { hidden: true })).toHaveClass('animate-spin');
  });

  it('shows empty state when no data', () => {
    render(<DataTable columns={mockColumns} dataSource={[]} />);
    
    expect(screen.getByText('No data')).toBeInTheDocument();
  });

  it('shows custom empty text', () => {
    render(<DataTable columns={mockColumns} dataSource={[]} emptyText="No records found" />);
    
    expect(screen.getByText('No records found')).toBeInTheDocument();
  });

  it('handles sorting on sortable columns', () => {
    const onSortChange = jest.fn();
    render(<DataTable columns={mockColumns} dataSource={mockData} onSortChange={onSortChange} />);
    
    const nameHeader = screen.getByText('Name');
    fireEvent.click(nameHeader);
    
    expect(onSortChange).toHaveBeenCalledWith({ key: 'name', direction: 'asc' });
    
    fireEvent.click(nameHeader);
    expect(onSortChange).toHaveBeenCalledWith({ key: 'name', direction: 'desc' });
    
    fireEvent.click(nameHeader);
    expect(onSortChange).toHaveBeenCalledWith(null);
  });

  it('applies small size classes', () => {
    render(<DataTable columns={mockColumns} dataSource={mockData} size="sm" />);
    
    const table = screen.getByRole('table');
    expect(table).toHaveClass('text-sm');
  });

  it('applies large size classes', () => {
    render(<DataTable columns={mockColumns} dataSource={mockData} size="lg" />);
    
    const table = screen.getByRole('table');
    expect(table).toHaveClass('text-base');
  });

  it('applies bordered style', () => {
    render(<DataTable columns={mockColumns} dataSource={mockData} bordered={true} />);
    
    const table = screen.getByRole('table');
    expect(table).toHaveClass('border-collapse', 'border', 'border-gray-200');
  });

  it('applies striped rows', () => {
    render(<DataTable columns={mockColumns} dataSource={mockData} striped={true} />);
    
    const rows = screen.getAllByRole('row');
    const dataRows = rows.slice(1); // Skip header row
    
    expect(dataRows[1]).toHaveClass('bg-gray-50');
  });

  it('handles row selection with checkboxes', () => {
    const onChange = jest.fn();
    const rowSelection = {
      selectedRowKeys: ['1'],
      onChange
    };
    
    render(<DataTable columns={mockColumns} dataSource={mockData} rowSelection={rowSelection} />);
    
    const checkboxes = screen.getAllByRole('checkbox');
    expect(checkboxes).toHaveLength(4); // 3 data rows + 1 select all
    
    fireEvent.click(checkboxes[1]); // Click first data row checkbox
    expect(onChange).toHaveBeenCalled();
  });

  it('handles select all checkbox', () => {
    const onChange = jest.fn();
    const onSelectAll = jest.fn();
    const rowSelection = {
      selectedRowKeys: [],
      onChange,
      onSelectAll
    };
    
    render(<DataTable columns={mockColumns} dataSource={mockData} rowSelection={rowSelection} />);
    
    const selectAllCheckbox = screen.getAllByRole('checkbox')[0];
    fireEvent.click(selectAllCheckbox);
    
    expect(onSelectAll).toHaveBeenCalledWith(true, mockData, mockData);
  });

  it('handles radio button selection', () => {
    const onChange = jest.fn();
    const rowSelection = {
      type: 'radio' as const,
      selectedRowKeys: [],
      onChange
    };
    
    render(<DataTable columns={mockColumns} dataSource={mockData} rowSelection={rowSelection} />);
    
    const radios = screen.getAllByRole('radio');
    expect(radios).toHaveLength(3); // No select all for radio
    
    fireEvent.click(radios[0]);
    expect(onChange).toHaveBeenCalledWith(['1'], [mockData[0]]);
  });

  it('handles expandable rows', () => {
    const onExpand = jest.fn();
    const expandable = {
      onExpand,
      expandedRowRender: (record: TestData) => <div>Expanded content for {record.name}</div>
    };
    
    render(<DataTable columns={mockColumns} dataSource={mockData} expandable={expandable} />);
    
    const expandButtons = screen.getAllByRole('button');
    fireEvent.click(expandButtons[0]);
    
    expect(onExpand).toHaveBeenCalledWith(true, mockData[0]);
    expect(screen.getByText('Expanded content for John Doe')).toBeInTheDocument();
  });

  it('handles row click events', () => {
    const onClick = jest.fn();
    const onRow = () => ({ onClick });
    
    render(<DataTable columns={mockColumns} dataSource={mockData} onRow={onRow} />);
    
    const firstDataRow = screen.getAllByRole('row')[1]; // Skip header
    fireEvent.click(firstDataRow);
    
    expect(onClick).toHaveBeenCalled();
  });

  it('applies custom row className', () => {
    const onRow = (record: TestData) => ({ 
      className: record.status === 'active' ? 'bg-green-100' : 'bg-red-100' 
    });
    
    render(<DataTable columns={mockColumns} dataSource={mockData} onRow={onRow} />);
    
    const dataRows = screen.getAllByRole('row').slice(1);
    expect(dataRows[0]).toHaveClass('bg-green-100'); // John Doe - active
    expect(dataRows[1]).toHaveClass('bg-red-100'); // Jane Smith - inactive
  });

  it('applies column alignment', () => {
    const alignedColumns: Column<TestData>[] = [
      { key: 'name', title: 'Name', align: 'left' },
      { key: 'age', title: 'Age', align: 'center' },
      { key: 'email', title: 'Email', align: 'right' }
    ];
    
    render(<DataTable columns={alignedColumns} dataSource={mockData} />);
    
    const cells = screen.getAllByRole('cell');
    // Check data cells (skip header cells)
    expect(cells[3]).toHaveClass('text-left'); // name
    expect(cells[4]).toHaveClass('text-center'); // age
    expect(cells[5]).toHaveClass('text-right'); // email
  });

  it('applies ellipsis to long content', () => {
    const ellipsisColumns: Column<TestData>[] = [
      { key: 'email', title: 'Email', dataIndex: 'email', ellipsis: true }
    ];
    
    render(<DataTable columns={ellipsisColumns} dataSource={mockData} />);
    
    const emailCells = screen.getAllByRole('cell').slice(1); // Skip header
    expect(emailCells[0]).toHaveClass('truncate');
  });

  it('applies custom className', () => {
    render(<DataTable columns={mockColumns} dataSource={mockData} className="custom-table" />);
    
    const tableContainer = screen.getByRole('table').parentElement;
    expect(tableContainer).toHaveClass('custom-table');
  });

  it('applies scroll styles', () => {
    const scroll = { x: 800, y: 400 };
    render(<DataTable columns={mockColumns} dataSource={mockData} scroll={scroll} />);
    
    const scrollContainer = screen.getByRole('table').parentElement;
    expect(scrollContainer).toHaveClass('overflow-auto', 'overflow-x-auto', 'overflow-y-auto');
    expect(scrollContainer).toHaveStyle({ maxHeight: '400' });
  });

  it('handles disabled row selection', () => {
    const rowSelection = {
      selectedRowKeys: [],
      onChange: jest.fn(),
      getCheckboxProps: (record: TestData) => ({
        disabled: record.status === 'inactive'
      })
    };
    
    render(<DataTable columns={mockColumns} dataSource={mockData} rowSelection={rowSelection} />);
    
    const checkboxes = screen.getAllByRole('checkbox').slice(1); // Skip select all
    expect(checkboxes[0]).not.toBeDisabled(); // John Doe - active
    expect(checkboxes[1]).toBeDisabled(); // Jane Smith - inactive
    expect(checkboxes[2]).not.toBeDisabled(); // Bob Johnson - active
  });

  it('sorts data correctly', () => {
    render(<DataTable columns={mockColumns} dataSource={mockData} />);
    
    // Click to sort by name ascending
    const nameHeader = screen.getByText('Name');
    fireEvent.click(nameHeader);
    
    const nameColumns = screen.getAllByRole('cell').filter(cell => 
      ['Bob Johnson', 'Jane Smith', 'John Doe'].includes(cell.textContent || '')
    );
    
    // Should be sorted alphabetically
    expect(nameColumns[0]).toHaveTextContent('Bob Johnson');
    expect(nameColumns[1]).toHaveTextContent('Jane Smith');
    expect(nameColumns[2]).toHaveTextContent('John Doe');
  });

  it('displays sort indicators', () => {
    render(<DataTable columns={mockColumns} dataSource={mockData} />);
    
    const nameHeader = screen.getByText('Name');
    expect(nameHeader.parentElement?.querySelector('svg')).toBeInTheDocument();
    
    // Email column should not have sort indicators (not sortable)
    const emailHeader = screen.getByText('Email');
    expect(emailHeader.parentElement?.querySelector('svg')).not.toBeInTheDocument();
  });

  it('handles custom rowKey function', () => {
    const customRowKey = (record: TestData) => `custom-${record.id}`;
    
    render(<DataTable columns={mockColumns} dataSource={mockData} rowKey={customRowKey} />);
    
    // Should render without errors and use custom row keys internally
    expect(screen.getByText('John Doe')).toBeInTheDocument();
  });

  it('handles expandable row conditions', () => {
    const expandable = {
      expandedRowRender: (record: TestData) => <div>Expanded {record.name}</div>,
      rowExpandable: (record: TestData) => record.status === 'active'
    };
    
    render(<DataTable columns={mockColumns} dataSource={mockData} expandable={expandable} />);
    
    const expandButtons = screen.queryAllByRole('button');
    // Only active users should have expand buttons (John Doe and Bob Johnson)
    expect(expandButtons).toHaveLength(2);
  });

  it('shows selected row background', () => {
    const rowSelection = {
      selectedRowKeys: ['1', '3'],
      onChange: jest.fn()
    };
    
    render(<DataTable columns={mockColumns} dataSource={mockData} rowSelection={rowSelection} />);
    
    const dataRows = screen.getAllByRole('row').slice(1); // Skip header
    expect(dataRows[0]).toHaveClass('bg-blue-50'); // Selected
    expect(dataRows[1]).not.toHaveClass('bg-blue-50'); // Not selected
    expect(dataRows[2]).toHaveClass('bg-blue-50'); // Selected
  });

  it('handles double click events', () => {
    const onDoubleClick = jest.fn();
    const onRow = () => ({ onDoubleClick });
    
    render(<DataTable columns={mockColumns} dataSource={mockData} onRow={onRow} />);
    
    const firstDataRow = screen.getAllByRole('row')[1];
    fireEvent.doubleClick(firstDataRow);
    
    expect(onDoubleClick).toHaveBeenCalled();
  });
});