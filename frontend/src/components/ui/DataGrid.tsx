import React, { useState, useRef, useCallback, useEffect, useMemo } from 'react';
import { cn } from '@/lib/utils';

export interface DataGridColumn<T = any> {
  key: string;
  header: string;
  width?: number;
  minWidth?: number;
  maxWidth?: number;
  sortable?: boolean;
  filterable?: boolean;
  resizable?: boolean;
  frozen?: boolean;
  visible?: boolean;
  render?: (row: T, value: any) => React.ReactNode;
  renderHeader?: () => React.ReactNode;
  align?: 'left' | 'center' | 'right';
  type?: 'text' | 'number' | 'date' | 'boolean';
}

export interface BulkAction {
  id: string;
  label: string;
  icon?: React.ReactNode;
  onClick: (selectedRows: any[]) => void;
}

export interface ContextMenuItem {
  label: string;
  icon?: React.ReactNode;
  onClick: (row: any) => void;
  disabled?: boolean;
}

export interface SortConfig {
  key: string;
  direction: 'asc' | 'desc';
}

export interface DataGridProps<T = any> {
  data: T[];
  columns: DataGridColumn<T>[];
  loading?: boolean;
  size?: 'sm' | 'md' | 'lg';
  variant?: 'default' | 'striped' | 'bordered';
  hoverable?: boolean;
  selectable?: boolean;
  multiSelect?: boolean;
  selectedRows?: any[];
  sortable?: boolean;
  multiSort?: boolean;
  sortConfig?: SortConfig[];
  filterable?: boolean;
  globalFilter?: string;
  columnFilters?: Record<string, any>;
  pagination?: boolean;
  pageSize?: number;
  currentPage?: number;
  totalPages?: number;
  totalRows?: number;
  expandable?: boolean;
  expandedRows?: any[];
  expandContent?: (row: T) => React.ReactNode;
  groupBy?: string;
  virtualScroll?: boolean;
  height?: number;
  stickyHeader?: boolean;
  resizable?: boolean;
  reorderable?: boolean;
  draggableRows?: boolean;
  editable?: boolean;
  toolbar?: React.ReactNode;
  bulkActions?: BulkAction[];
  contextMenu?: ContextMenuItem[];
  columnVisibility?: boolean;
  hiddenColumns?: string[];
  exportable?: boolean;
  exportFormats?: string[];
  emptyState?: React.ReactNode;
  rowKey?: string;
  getRowProps?: (row: T) => React.HTMLAttributes<HTMLTableRowElement>;
  getCellProps?: (row: T, column: DataGridColumn<T>) => React.HTMLAttributes<HTMLTableCellElement>;
  ariaLabel?: string;
  ariaDescribedBy?: string;
  onSort?: (key: string, direction: 'asc' | 'desc') => void;
  onMultiSort?: (sortConfig: SortConfig[]) => void;
  onFilter?: (value: string) => void;
  onColumnFilter?: (columnKey: string, value: any) => void;
  onPageChange?: (page: number) => void;
  onPageSizeChange?: (pageSize: number) => void;
  onSelectionChange?: (selectedRows: any[]) => void;
  onRowClick?: (row: T, event: React.MouseEvent) => void;
  onRowDoubleClick?: (row: T, event: React.MouseEvent) => void;
  onCellClick?: (row: T, column: DataGridColumn<T>, event: React.MouseEvent) => void;
  onCellEdit?: (rowId: any, columnKey: string, value: any) => void;
  onExpandChange?: (expandedRows: any[]) => void;
  onColumnResize?: (columnKey: string, width: number) => void;
  onColumnReorder?: (fromIndex: number, toIndex: number) => void;
  onRowReorder?: (fromIndex: number, toIndex: number) => void;
  onColumnVisibilityChange?: (hiddenColumns: string[]) => void;
  onExport?: (format: string) => void;
  className?: string;
  'data-testid'?: string;
  'data-category'?: string;
  'data-id'?: string;
}

export const DataGrid = <T extends Record<string, any>>({
  data,
  columns,
  loading = false,
  size = 'md',
  variant = 'default',
  hoverable = false,
  selectable = false,
  multiSelect = true,
  selectedRows = [],
  sortable = false,
  multiSort = false,
  sortConfig = [],
  filterable = false,
  globalFilter = '',
  columnFilters = {},
  pagination = false,
  pageSize = 10,
  currentPage = 1,
  totalPages,
  totalRows,
  expandable = false,
  expandedRows = [],
  expandContent,
  groupBy,
  virtualScroll = false,
  height = 400,
  stickyHeader = false,
  resizable = false,
  reorderable = false,
  draggableRows = false,
  editable = false,
  toolbar,
  bulkActions = [],
  contextMenu = [],
  columnVisibility = false,
  hiddenColumns = [],
  exportable = false,
  exportFormats = ['csv'],
  emptyState,
  rowKey = 'id',
  getRowProps,
  getCellProps,
  ariaLabel = 'Data grid',
  ariaDescribedBy,
  onSort,
  onMultiSort,
  onFilter,
  onColumnFilter,
  onPageChange,
  onPageSizeChange,
  onSelectionChange,
  onRowClick,
  onRowDoubleClick,
  onCellClick,
  onCellEdit,
  onExpandChange,
  onColumnResize,
  onColumnReorder,
  onRowReorder,
  onColumnVisibilityChange,
  onExport,
  className,
  'data-testid': dataTestId = 'datagrid-container',
  'data-category': dataCategory,
  'data-id': dataId,
  ...props
}: DataGridProps<T>) => {
  const [internalSortConfig, setInternalSortConfig] = useState<SortConfig[]>(sortConfig);
  const [internalSelectedRows, setInternalSelectedRows] = useState<any[]>(selectedRows);
  const [internalExpandedRows, setInternalExpandedRows] = useState<any[]>(expandedRows);
  const [internalGlobalFilter, setInternalGlobalFilter] = useState(globalFilter);
  const [internalCurrentPage, setInternalCurrentPage] = useState(currentPage);
  const [editingCell, setEditingCell] = useState<{ rowId: any; columnKey: string } | null>(null);
  const [editingValue, setEditingValue] = useState('');
  const [contextMenuPosition, setContextMenuPosition] = useState<{ x: number; y: number; row: T } | null>(null);
  const [draggedColumn, setDraggedColumn] = useState<string | null>(null);
  const [columnWidths, setColumnWidths] = useState<Record<string, number>>({});

  const tableRef = useRef<HTMLTableElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  const sizeClasses = {
    sm: 'size-sm text-sm',
    md: 'size-md text-base',
    lg: 'size-lg text-lg'
  };

  const variantClasses = {
    default: 'variant-default',
    striped: 'variant-striped',
    bordered: 'variant-bordered border'
  };

  // Get visible columns
  const visibleColumns = useMemo(() => {
    return columns.filter(col => col.visible !== false && !hiddenColumns.includes(col.key));
  }, [columns, hiddenColumns]);

  // Filter data based on global filter and column filters
  const filteredData = useMemo(() => {
    let filtered = [...data];

    // Apply global filter
    if (internalGlobalFilter) {
      filtered = filtered.filter(row =>
        Object.values(row).some(value =>
          String(value).toLowerCase().includes(internalGlobalFilter.toLowerCase())
        )
      );
    }

    // Apply column filters
    Object.entries(columnFilters).forEach(([columnKey, filterValue]) => {
      if (filterValue !== undefined && filterValue !== '') {
        filtered = filtered.filter(row =>
          String(row[columnKey]).toLowerCase().includes(String(filterValue).toLowerCase())
        );
      }
    });

    return filtered;
  }, [data, internalGlobalFilter, columnFilters]);

  // Sort data
  const sortedData = useMemo(() => {
    if (internalSortConfig.length === 0) return filteredData;

    return [...filteredData].sort((a, b) => {
      for (const sort of internalSortConfig) {
        const aValue = a[sort.key];
        const bValue = b[sort.key];
        
        let comparison = 0;
        if (aValue < bValue) comparison = -1;
        if (aValue > bValue) comparison = 1;
        
        if (comparison !== 0) {
          return sort.direction === 'desc' ? -comparison : comparison;
        }
      }
      return 0;
    });
  }, [filteredData, internalSortConfig]);

  // Group data if needed
  const groupedData = useMemo(() => {
    if (!groupBy) return sortedData;

    const groups: Record<string, T[]> = {};
    sortedData.forEach(row => {
      const groupValue = row[groupBy];
      if (!groups[groupValue]) {
        groups[groupValue] = [];
      }
      groups[groupValue].push(row);
    });

    return groups;
  }, [sortedData, groupBy]);

  // Paginate data
  const paginatedData = useMemo(() => {
    if (!pagination) return sortedData;

    const startIndex = (internalCurrentPage - 1) * pageSize;
    const endIndex = startIndex + pageSize;
    return sortedData.slice(startIndex, endIndex);
  }, [sortedData, pagination, internalCurrentPage, pageSize]);

  const displayData = pagination ? paginatedData : sortedData;
  const calculatedTotalPages = totalPages || Math.ceil(sortedData.length / pageSize);

  // Handle sorting
  const handleSort = useCallback((columnKey: string) => {
    if (!sortable) return;

    const existingSort = internalSortConfig.find(s => s.key === columnKey);
    let newSortConfig: SortConfig[];

    if (multiSort) {
      if (existingSort) {
        if (existingSort.direction === 'asc') {
          newSortConfig = internalSortConfig.map(s =>
            s.key === columnKey ? { ...s, direction: 'desc' as const } : s
          );
        } else {
          newSortConfig = internalSortConfig.filter(s => s.key !== columnKey);
        }
      } else {
        newSortConfig = [...internalSortConfig, { key: columnKey, direction: 'asc' as const }];
      }
      onMultiSort?.(newSortConfig);
    } else {
      const direction = existingSort?.direction === 'asc' ? 'desc' : 'asc';
      newSortConfig = [{ key: columnKey, direction }];
      onSort?.(columnKey, direction);
    }

    setInternalSortConfig(newSortConfig);
  }, [sortable, multiSort, internalSortConfig, onSort, onMultiSort]);

  // Handle selection
  const handleRowSelection = useCallback((rowId: any, checked: boolean) => {
    let newSelection: any[];

    if (checked) {
      newSelection = multiSelect ? [...internalSelectedRows, rowId] : [rowId];
    } else {
      newSelection = internalSelectedRows.filter(id => id !== rowId);
    }

    setInternalSelectedRows(newSelection);
    onSelectionChange?.(newSelection);
  }, [internalSelectedRows, multiSelect, onSelectionChange]);

  // Handle select all
  const handleSelectAll = useCallback((checked: boolean) => {
    const newSelection = checked ? displayData.map(row => row[rowKey]) : [];
    setInternalSelectedRows(newSelection);
    onSelectionChange?.(newSelection);
  }, [displayData, rowKey, onSelectionChange]);

  // Handle pagination
  const handlePageChange = useCallback((page: number) => {
    setInternalCurrentPage(page);
    onPageChange?.(page);
  }, [onPageChange]);

  // Handle row expansion
  const handleRowExpand = useCallback((rowId: any) => {
    const newExpanded = internalExpandedRows.includes(rowId)
      ? internalExpandedRows.filter(id => id !== rowId)
      : [...internalExpandedRows, rowId];
    
    setInternalExpandedRows(newExpanded);
    onExpandChange?.(newExpanded);
  }, [internalExpandedRows, onExpandChange]);

  // Handle cell editing
  const handleCellEdit = useCallback((rowId: any, columnKey: string, value: any) => {
    setEditingCell({ rowId, columnKey });
    setEditingValue(String(value));
  }, []);

  const handleCellSave = useCallback(() => {
    if (editingCell) {
      onCellEdit?.(editingCell.rowId, editingCell.columnKey, editingValue);
      setEditingCell(null);
      setEditingValue('');
    }
  }, [editingCell, editingValue, onCellEdit]);

  // Handle context menu
  const handleContextMenu = useCallback((e: React.MouseEvent, row: T) => {
    if (contextMenu.length === 0) return;
    
    e.preventDefault();
    setContextMenuPosition({
      x: e.clientX,
      y: e.clientY,
      row
    });
  }, [contextMenu]);

  // Handle keyboard navigation
  const handleKeyDown = useCallback((e: React.KeyboardEvent, rowIndex: number, colIndex: number) => {
    const totalRows = displayData.length;
    const totalCols = visibleColumns.length;

    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault();
        if (rowIndex < totalRows - 1) {
          const nextCell = document.querySelector(`[data-testid="cell-${displayData[rowIndex + 1][rowKey]}-${visibleColumns[colIndex].key}"]`) as HTMLElement;
          nextCell?.focus();
        }
        break;
      
      case 'ArrowUp':
        e.preventDefault();
        if (rowIndex > 0) {
          const prevCell = document.querySelector(`[data-testid="cell-${displayData[rowIndex - 1][rowKey]}-${visibleColumns[colIndex].key}"]`) as HTMLElement;
          prevCell?.focus();
        }
        break;
      
      case 'ArrowRight':
        e.preventDefault();
        if (colIndex < totalCols - 1) {
          const rightCell = document.querySelector(`[data-testid="cell-${displayData[rowIndex][rowKey]}-${visibleColumns[colIndex + 1].key}"]`) as HTMLElement;
          rightCell?.focus();
        }
        break;
      
      case 'ArrowLeft':
        e.preventDefault();
        if (colIndex > 0) {
          const leftCell = document.querySelector(`[data-testid="cell-${displayData[rowIndex][rowKey]}-${visibleColumns[colIndex - 1].key}"]`) as HTMLElement;
          leftCell?.focus();
        }
        break;
      
      case 'Enter':
        if (editable && editingCell) {
          handleCellSave();
        }
        break;
      
      case 'Escape':
        setEditingCell(null);
        setEditingValue('');
        break;
    }
  }, [displayData, visibleColumns, rowKey, editable, editingCell, handleCellSave]);

  // Click outside handler
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setContextMenuPosition(null);
        setEditingCell(null);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Render toolbar
  const renderToolbar = () => {
    if (!toolbar && !filterable && !exportable && !columnVisibility) return null;

    return (
      <div className="flex items-center justify-between p-4 border-b">
        <div className="flex items-center space-x-2">
          {filterable && (
            <div data-testid="global-filter-input">
              <input
                type="text"
                placeholder="Search..."
                value={internalGlobalFilter}
                onChange={(e) => {
                  setInternalGlobalFilter(e.target.value);
                  onFilter?.(e.target.value);
                }}
                className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          )}
        </div>

        <div className="flex items-center space-x-2">
          {exportable && (
            <div className="relative">
              <button
                className="px-3 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
                onClick={() => onExport?.(exportFormats[0])}
                data-testid="export-button"
              >
                Export
              </button>
              {exportFormats.length > 1 && (
                <div className="absolute right-0 mt-1 bg-white border rounded shadow-lg z-10">
                  {exportFormats.map(format => (
                    <button
                      key={format}
                      className="block w-full px-4 py-2 text-left hover:bg-gray-100"
                      onClick={() => onExport?.(format)}
                      data-testid={`export-${format}`}
                    >
                      {format.toUpperCase()}
                    </button>
                  ))}
                </div>
              )}
            </div>
          )}

          {columnVisibility && (
            <button
              className="px-3 py-2 border border-gray-300 rounded hover:bg-gray-50"
              data-testid="column-visibility-toggle"
            >
              Columns
            </button>
          )}

          {toolbar}
        </div>
      </div>
    );
  };

  // Render bulk actions
  const renderBulkActions = () => {
    if (!selectable || internalSelectedRows.length === 0 || bulkActions.length === 0) return null;

    return (
      <div className="flex items-center space-x-2 p-2 bg-blue-50 border-b" data-testid="bulk-actions">
        <span className="text-sm text-gray-600">
          {internalSelectedRows.length} selected
        </span>
        {bulkActions.map(action => (
          <button
            key={action.id}
            className="px-3 py-1 text-sm bg-white border border-gray-300 rounded hover:bg-gray-50"
            onClick={() => action.onClick(internalSelectedRows)}
            data-testid={`bulk-action-${action.id}`}
          >
            {action.icon && <span className="mr-1">{action.icon}</span>}
            {action.label}
          </button>
        ))}
      </div>
    );
  };

  // Render table header
  const renderHeader = () => (
    <thead className={cn('bg-gray-50', stickyHeader && 'sticky top-0 z-10')} data-testid="datagrid-header">
      <tr>
        {selectable && (
          <th className="w-10 px-4 py-3">
            <input
              type="checkbox"
              checked={internalSelectedRows.length === displayData.length && displayData.length > 0}
              onChange={(e) => handleSelectAll(e.target.checked)}
              data-testid="select-all-checkbox"
            />
          </th>
        )}
        
        {expandable && (
          <th className="w-10 px-4 py-3"></th>
        )}

        {visibleColumns.map((column, index) => (
          <th
            key={column.key}
            className={cn(
              'px-4 py-3 text-left font-medium text-gray-900 border-r border-gray-200 last:border-r-0',
              column.frozen && 'frozen sticky left-0 bg-gray-50 z-20',
              sortable && column.sortable !== false && 'cursor-pointer hover:bg-gray-100',
              resizable && 'relative'
            )}
            style={{ width: columnWidths[column.key] || column.width }}
            onClick={() => sortable && column.sortable !== false && handleSort(column.key)}
            draggable={reorderable}
            data-testid={`column-header-${column.key}`}
          >
            <div className="flex items-center justify-between">
              {column.renderHeader ? column.renderHeader() : column.header}
              
              {sortable && column.sortable !== false && (
                <div className="flex flex-col ml-2">
                  {internalSortConfig.find(s => s.key === column.key)?.direction === 'asc' && (
                    <span className="text-blue-500">▲</span>
                  )}
                  {internalSortConfig.find(s => s.key === column.key)?.direction === 'desc' && (
                    <span className="text-blue-500">▼</span>
                  )}
                </div>
              )}
            </div>
            
            {resizable && (
              <div
                className="absolute right-0 top-0 bottom-0 w-1 cursor-col-resize hover:bg-blue-500"
                data-testid={`column-resizer-${column.key}`}
              />
            )}
          </th>
        ))}
      </tr>
    </thead>
  );

  // Render table row
  const renderRow = (row: T, rowIndex: number) => {
    const rowId = row[rowKey];
    const isSelected = internalSelectedRows.includes(rowId);
    const isExpanded = internalExpandedRows.includes(rowId);
    const rowProps = getRowProps?.(row) || {};

    return (
      <React.Fragment key={rowId}>
        <tr
          className={cn(
            'border-b border-gray-200',
            hoverable && 'hover:bg-gray-50',
            isSelected && 'bg-blue-50',
            variant === 'striped' && rowIndex % 2 === 1 && 'bg-gray-50',
            rowProps.className
          )}
          onClick={(e) => onRowClick?.(row, e)}
          onDoubleClick={(e) => onRowDoubleClick?.(row, e)}
          onContextMenu={(e) => handleContextMenu(e, row)}
          draggable={draggableRows}
          data-testid={`data-row-${rowId}`}
          {...rowProps}
        >
          {selectable && (
            <td className="w-10 px-4 py-3">
              <input
                type="checkbox"
                checked={isSelected}
                onChange={(e) => handleRowSelection(rowId, e.target.checked)}
                data-testid={`row-checkbox-${rowId}`}
              />
            </td>
          )}
          
          {expandable && (
            <td className="w-10 px-4 py-3">
              <button
                className="p-1 hover:bg-gray-100 rounded"
                onClick={() => handleRowExpand(rowId)}
                data-testid={`expand-button-${rowId}`}
              >
                {isExpanded ? '−' : '+'}
              </button>
            </td>
          )}

          {visibleColumns.map((column, colIndex) => {
            const value = row[column.key];
            const isEditing = editingCell?.rowId === rowId && editingCell?.columnKey === column.key;
            const cellProps = getCellProps?.(row, column) || {};

            return (
              <td
                key={column.key}
                className={cn(
                  'px-4 py-3 border-r border-gray-200 last:border-r-0',
                  column.frozen && 'frozen sticky left-0 bg-white z-10',
                  column.align === 'center' && 'text-center',
                  column.align === 'right' && 'text-right',
                  cellProps.className
                )}
                style={{ width: columnWidths[column.key] || column.width, ...cellProps.style }}
                tabIndex={0}
                onClick={(e) => onCellClick?.(row, column, e)}
                onDoubleClick={() => editable && handleCellEdit(rowId, column.key, value)}
                onKeyDown={(e) => handleKeyDown(e, rowIndex, colIndex)}
                data-testid={`cell-${rowId}-${column.key}`}
                {...cellProps}
              >
                {isEditing ? (
                  <input
                    type="text"
                    value={editingValue}
                    onChange={(e) => setEditingValue(e.target.value)}
                    onBlur={handleCellSave}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter') handleCellSave();
                      if (e.key === 'Escape') {
                        setEditingCell(null);
                        setEditingValue('');
                      }
                    }}
                    className="w-full p-1 border border-blue-500 rounded"
                    autoFocus
                    data-testid={`cell-editor-${rowId}-${column.key}`}
                  />
                ) : (
                  column.render ? column.render(row, value) : String(value || '')
                )}
              </td>
            );
          })}
        </tr>

        {expandable && isExpanded && expandContent && (
          <tr>
            <td colSpan={visibleColumns.length + (selectable ? 1 : 0) + 1} className="p-0">
              <div className="p-4 bg-gray-50 border-b">
                {expandContent(row)}
              </div>
            </td>
          </tr>
        )}
      </React.Fragment>
    );
  };

  // Render grouped rows
  const renderGroupedRows = () => {
    if (!groupBy || typeof groupedData !== 'object') return null;

    return Object.entries(groupedData as Record<string, T[]>).map(([groupValue, groupRows]) => (
      <React.Fragment key={groupValue}>
        <tr className="bg-gray-100 font-semibold">
          <td 
            colSpan={visibleColumns.length + (selectable ? 1 : 0) + (expandable ? 1 : 0)}
            className="px-4 py-2"
            data-testid={`group-${groupValue}`}
          >
            {groupValue} ({groupRows.length})
          </td>
        </tr>
        {groupRows.map((row, index) => renderRow(row, index))}
      </React.Fragment>
    ));
  };

  // Render pagination
  const renderPagination = () => {
    if (!pagination) return null;

    return (
      <div className="flex items-center justify-between p-4 border-t" data-testid="datagrid-pagination">
        <div className="text-sm text-gray-600">
          Showing {(internalCurrentPage - 1) * pageSize + 1} to {Math.min(internalCurrentPage * pageSize, totalRows || sortedData.length)} of {totalRows || sortedData.length} entries
        </div>
        
        <div className="flex items-center space-x-2">
          <button
            className="px-3 py-1 border border-gray-300 rounded hover:bg-gray-50 disabled:opacity-50"
            disabled={internalCurrentPage === 1}
            onClick={() => handlePageChange(internalCurrentPage - 1)}
            data-testid="pagination-prev"
          >
            Previous
          </button>
          
          <span className="px-3 py-1">
            Page {internalCurrentPage} of {calculatedTotalPages}
          </span>
          
          <button
            className="px-3 py-1 border border-gray-300 rounded hover:bg-gray-50 disabled:opacity-50"
            disabled={internalCurrentPage === calculatedTotalPages}
            onClick={() => handlePageChange(internalCurrentPage + 1)}
            data-testid="pagination-next"
          >
            Next
          </button>
        </div>
      </div>
    );
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
        {contextMenu.map((item, index) => (
          <button
            key={index}
            className="w-full px-3 py-2 text-left text-sm hover:bg-gray-100 first:rounded-t-md last:rounded-b-md disabled:opacity-50"
            disabled={item.disabled}
            onClick={() => {
              item.onClick(contextMenuPosition.row);
              setContextMenuPosition(null);
            }}
          >
            {item.icon && <span className="mr-2">{item.icon}</span>}
            {item.label}
          </button>
        ))}
      </div>
    );
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64" data-testid="datagrid-loading">
        <div className="w-8 h-8 border-2 border-gray-300 border-t-blue-500 rounded-full animate-spin"></div>
      </div>
    );
  }

  if (data.length === 0) {
    return (
      <div className="flex items-center justify-center h-64" data-testid="datagrid-empty">
        {emptyState || <div className="text-gray-500">No data available</div>}
      </div>
    );
  }

  return (
    <div
      ref={containerRef}
      className={cn(
        'datagrid',
        sizeClasses[size],
        variantClasses[variant],
        hoverable && 'hoverable',
        virtualScroll && 'virtual-scroll overflow-auto',
        className
      )}
      style={{ height: virtualScroll ? height : undefined }}
      data-testid={dataTestId}
      data-category={dataCategory}
      data-id={dataId}
      {...props}
    >
      {renderToolbar()}
      {renderBulkActions()}
      
      <div className="overflow-auto">
        <table
          ref={tableRef}
          className="w-full"
          role="table"
          aria-label={ariaLabel}
          aria-describedby={ariaDescribedBy}
        >
          {renderHeader()}
          <tbody>
            {groupBy ? renderGroupedRows() : displayData.map((row, index) => renderRow(row, index))}
          </tbody>
        </table>
      </div>
      
      {renderPagination()}
      {renderContextMenu()}
    </div>
  );
};

export default DataGrid;