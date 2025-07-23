import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { vi } from 'vitest';
import { List } from './List';

// Mock IntersectionObserver for infinite scroll tests
const mockIntersectionObserver = vi.fn();
mockIntersectionObserver.mockReturnValue({
  observe: vi.fn(),
  unobserve: vi.fn(),
  disconnect: vi.fn(),
});
window.IntersectionObserver = mockIntersectionObserver;

describe('List', () => {
  const mockItems = [
    { id: 1, name: 'Item 1', value: 'value1' },
    { id: 2, name: 'Item 2', value: 'value2' },
    { id: 3, name: 'Item 3', value: 'value3' },
  ];

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders list with items', () => {
    render(
      <List
        items={mockItems}
        renderItem={(item) => <div key={item.id}>{item.name}</div>}
      />
    );
    
    expect(screen.getByText('Item 1')).toBeInTheDocument();
    expect(screen.getByText('Item 2')).toBeInTheDocument();
    expect(screen.getByText('Item 3')).toBeInTheDocument();
  });

  it('renders empty state when no items', () => {
    render(
      <List
        items={[]}
        renderItem={(item) => <div key={item.id}>{item.name}</div>}
        emptyText="No items found"
      />
    );
    
    expect(screen.getByText('No items found')).toBeInTheDocument();
  });

  it('renders custom empty component', () => {
    const EmptyComponent = () => <div data-testid="empty">Custom empty</div>;
    render(
      <List
        items={[]}
        renderItem={(item) => <div key={item.id}>{item.name}</div>}
        emptyComponent={<EmptyComponent />}
      />
    );
    
    expect(screen.getByTestId('empty')).toBeInTheDocument();
  });

  it('supports different list styles', () => {
    const variants = ['default', 'bordered', 'divided', 'flush'] as const;
    
    variants.forEach(variant => {
      const { unmount } = render(
        <List
          items={mockItems}
          renderItem={(item) => <div key={item.id}>{item.name}</div>}
          variant={variant}
        />
      );
      expect(screen.getByTestId('list-container')).toBeInTheDocument();
      unmount();
    });
  });

  it('supports different sizes', () => {
    const sizes = ['sm', 'md', 'lg'] as const;
    
    sizes.forEach(size => {
      const { unmount } = render(
        <List
          items={mockItems}
          renderItem={(item) => <div key={item.id}>{item.name}</div>}
          size={size}
        />
      );
      expect(screen.getByTestId('list-container')).toBeInTheDocument();
      unmount();
    });
  });

  it('supports hover effects', () => {
    render(
      <List
        items={mockItems}
        renderItem={(item) => <div key={item.id}>{item.name}</div>}
        hoverable
      />
    );
    
    const listItems = screen.getAllByRole('listitem');
    expect(listItems[0]).toHaveClass('hover:bg-gray-50');
  });

  it('supports selection mode', () => {
    const onSelect = vi.fn();
    render(
      <List
        items={mockItems}
        renderItem={(item) => <div key={item.id}>{item.name}</div>}
        selectable
        onSelect={onSelect}
      />
    );
    
    const firstItem = screen.getAllByRole('listitem')[0];
    fireEvent.click(firstItem);
    
    expect(onSelect).toHaveBeenCalledWith([mockItems[0]]);
  });

  it('supports multi-selection', () => {
    const onSelect = vi.fn();
    render(
      <List
        items={mockItems}
        renderItem={(item) => <div key={item.id}>{item.name}</div>}
        selectable
        multiple
        onSelect={onSelect}
      />
    );
    
    const items = screen.getAllByRole('listitem');
    fireEvent.click(items[0]);
    fireEvent.click(items[1], { ctrlKey: true });
    
    expect(onSelect).toHaveBeenLastCalledWith([mockItems[0], mockItems[1]]);
  });

  it('supports loading state', () => {
    render(
      <List
        items={mockItems}
        renderItem={(item) => <div key={item.id}>{item.name}</div>}
        loading
      />
    );
    
    expect(screen.getByTestId('list-loading')).toBeInTheDocument();
  });

  it('supports custom loading component', () => {
    const LoadingComponent = () => <div data-testid="custom-loading">Loading...</div>;
    render(
      <List
        items={mockItems}
        renderItem={(item) => <div key={item.id}>{item.name}</div>}
        loading
        loadingComponent={<LoadingComponent />}
      />
    );
    
    expect(screen.getByTestId('custom-loading')).toBeInTheDocument();
  });

  it('supports virtual scrolling', () => {
    const manyItems = Array.from({ length: 1000 }, (_, i) => ({
      id: i,
      name: `Item ${i}`,
      value: `value${i}`
    }));
    
    render(
      <List
        items={manyItems}
        renderItem={(item) => <div key={item.id}>{item.name}</div>}
        virtual
        itemHeight={50}
        containerHeight={300}
      />
    );
    
    expect(screen.getByTestId('virtual-list')).toBeInTheDocument();
  });

  it('supports infinite scroll', () => {
    const onLoadMore = vi.fn();
    render(
      <List
        items={mockItems}
        renderItem={(item) => <div key={item.id}>{item.name}</div>}
        infiniteScroll
        onLoadMore={onLoadMore}
        hasMore
      />
    );
    
    expect(mockIntersectionObserver).toHaveBeenCalled();
  });

  it('shows loading more indicator', () => {
    render(
      <List
        items={mockItems}
        renderItem={(item) => <div key={item.id}>{item.name}</div>}
        infiniteScroll
        hasMore
        loadingMore
      />
    );
    
    expect(screen.getByTestId('loading-more')).toBeInTheDocument();
  });

  it('supports drag and drop', () => {
    const onReorder = vi.fn();
    render(
      <List
        items={mockItems}
        renderItem={(item) => <div key={item.id}>{item.name}</div>}
        draggable
        onReorder={onReorder}
      />
    );
    
    const items = screen.getAllByRole('listitem');
    expect(items[0]).toHaveAttribute('draggable', 'true');
  });

  it('supports search/filter', () => {
    render(
      <List
        items={mockItems}
        renderItem={(item) => <div key={item.id}>{item.name}</div>}
        searchable
        searchPlaceholder="Search items..."
      />
    );
    
    expect(screen.getByPlaceholderText('Search items...')).toBeInTheDocument();
    
    const searchInput = screen.getByPlaceholderText('Search items...');
    fireEvent.change(searchInput, { target: { value: 'Item 2' } });
    
    expect(screen.getByText('Item 2')).toBeInTheDocument();
    expect(screen.queryByText('Item 1')).not.toBeInTheDocument();
  });

  it('supports custom search function', () => {
    const customSearch = (item: any, query: string) => 
      item.value.toLowerCase().includes(query.toLowerCase());
    
    render(
      <List
        items={mockItems}
        renderItem={(item) => <div key={item.id}>{item.name}</div>}
        searchable
        searchFunction={customSearch}
      />
    );
    
    const searchInput = screen.getByRole('textbox');
    fireEvent.change(searchInput, { target: { value: 'value2' } });
    
    expect(screen.getByText('Item 2')).toBeInTheDocument();
    expect(screen.queryByText('Item 1')).not.toBeInTheDocument();
  });

  it('supports sorting', () => {
    render(
      <List
        items={mockItems}
        renderItem={(item) => <div key={item.id}>{item.name}</div>}
        sortable
        sortBy="name"
        sortOrder="desc"
      />
    );
    
    const items = screen.getAllByRole('listitem');
    expect(items[0]).toHaveTextContent('Item 3');
    expect(items[2]).toHaveTextContent('Item 1');
  });

  it('supports custom sort function', () => {
    const customSort = (a: any, b: any) => b.id - a.id;
    
    render(
      <List
        items={mockItems}
        renderItem={(item) => <div key={item.id}>{item.name}</div>}
        sortable
        sortFunction={customSort}
      />
    );
    
    const items = screen.getAllByRole('listitem');
    expect(items[0]).toHaveTextContent('Item 3');
    expect(items[2]).toHaveTextContent('Item 1');
  });

  it('supports pagination', () => {
    const manyItems = Array.from({ length: 25 }, (_, i) => ({
      id: i,
      name: `Item ${i}`,
      value: `value${i}`
    }));
    
    render(
      <List
        items={manyItems}
        renderItem={(item) => <div key={item.id}>{item.name}</div>}
        paginated
        pageSize={10}
      />
    );
    
    expect(screen.getByText('Item 0')).toBeInTheDocument();
    expect(screen.getByText('Item 9')).toBeInTheDocument();
    expect(screen.queryByText('Item 10')).not.toBeInTheDocument();
    
    const nextButton = screen.getByRole('button', { name: /next/i });
    fireEvent.click(nextButton);
    
    expect(screen.getByText('Item 10')).toBeInTheDocument();
  });

  it('supports group headers', () => {
    const groupedItems = [
      { id: 1, name: 'Item 1', group: 'Group A' },
      { id: 2, name: 'Item 2', group: 'Group A' },
      { id: 3, name: 'Item 3', group: 'Group B' },
    ];
    
    render(
      <List
        items={groupedItems}
        renderItem={(item) => <div key={item.id}>{item.name}</div>}
        groupBy="group"
        renderGroup={(group) => <div data-testid={`group-${group}`}>{group}</div>}
      />
    );
    
    expect(screen.getByTestId('group-Group A')).toBeInTheDocument();
    expect(screen.getByTestId('group-Group B')).toBeInTheDocument();
  });

  it('supports item actions', () => {
    const onEdit = vi.fn();
    const onDelete = vi.fn();
    
    render(
      <List
        items={mockItems}
        renderItem={(item) => <div key={item.id}>{item.name}</div>}
        actions={[
          { label: 'Edit', onClick: onEdit },
          { label: 'Delete', onClick: onDelete, variant: 'danger' }
        ]}
      />
    );
    
    const editButtons = screen.getAllByText('Edit');
    fireEvent.click(editButtons[0]);
    
    expect(onEdit).toHaveBeenCalledWith(mockItems[0]);
  });

  it('supports keyboard navigation', () => {
    render(
      <List
        items={mockItems}
        renderItem={(item) => <div key={item.id}>{item.name}</div>}
        keyboardNavigation
      />
    );
    
    const list = screen.getByTestId('list-container');
    fireEvent.keyDown(list, { key: 'ArrowDown' });
    
    const firstItem = screen.getAllByRole('listitem')[0];
    expect(firstItem).toHaveClass('ring-2');
  });

  it('supports custom className', () => {
    render(
      <List
        items={mockItems}
        renderItem={(item) => <div key={item.id}>{item.name}</div>}
        className="custom-list"
      />
    );
    
    expect(screen.getByTestId('list-container')).toHaveClass('custom-list');
  });

  it('supports custom item key extraction', () => {
    render(
      <List
        items={mockItems}
        renderItem={(item) => <div key={item.id}>{item.name}</div>}
        getItemKey={(item) => `custom-${item.id}`}
      />
    );
    
    expect(screen.getByText('Item 1')).toBeInTheDocument();
  });

  it('supports header and footer', () => {
    render(
      <List
        items={mockItems}
        renderItem={(item) => <div key={item.id}>{item.name}</div>}
        header={<div data-testid="list-header">Header</div>}
        footer={<div data-testid="list-footer">Footer</div>}
      />
    );
    
    expect(screen.getByTestId('list-header')).toBeInTheDocument();
    expect(screen.getByTestId('list-footer')).toBeInTheDocument();
  });

  it('supports item click events', () => {
    const onItemClick = vi.fn();
    render(
      <List
        items={mockItems}
        renderItem={(item) => <div key={item.id}>{item.name}</div>}
        onItemClick={onItemClick}
      />
    );
    
    const firstItem = screen.getAllByRole('listitem')[0];
    fireEvent.click(firstItem);
    
    expect(onItemClick).toHaveBeenCalledWith(mockItems[0], 0);
  });

  it('supports disabled items', () => {
    const itemsWithDisabled = [
      { id: 1, name: 'Item 1', disabled: false },
      { id: 2, name: 'Item 2', disabled: true },
      { id: 3, name: 'Item 3', disabled: false },
    ];
    
    render(
      <List
        items={itemsWithDisabled}
        renderItem={(item) => <div key={item.id}>{item.name}</div>}
        getItemDisabled={(item) => item.disabled}
      />
    );
    
    const items = screen.getAllByRole('listitem');
    expect(items[1]).toHaveClass('opacity-50');
  });

  it('supports custom data attributes', () => {
    render(
      <List
        items={mockItems}
        renderItem={(item) => <div key={item.id}>{item.name}</div>}
        data-category="product-list"
        data-id="main-list"
      />
    );
    
    const list = screen.getByTestId('list-container');
    expect(list).toHaveAttribute('data-category', 'product-list');
    expect(list).toHaveAttribute('data-id', 'main-list');
  });
});