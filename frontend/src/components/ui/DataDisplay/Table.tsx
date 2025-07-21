import React from 'react'
import { ChevronUp, ChevronDown, ArrowUpDown, Search, Filter, MoreHorizontal } from 'lucide-react'
import { cn } from '../../../lib/utils'

export interface TableColumn<T = any> {
  id: string
  header: string
  accessor?: keyof T | ((row: T) => any)
  cell?: (value: any, row: T, index: number) => React.ReactNode
  sortable?: boolean
  filterable?: boolean
  width?: string | number
  minWidth?: string | number
  maxWidth?: string | number
  align?: 'left' | 'center' | 'right'
  sticky?: 'left' | 'right'
  className?: string
  headerClassName?: string
}

export interface TableProps<T = any> {
  data: T[]
  columns: TableColumn<T>[]
  loading?: boolean
  error?: string | null
  emptyMessage?: string
  pageSize?: number
  currentPage?: number
  totalPages?: number
  totalItems?: number
  onPageChange?: (page: number) => void
  onSort?: (columnId: string, direction: 'asc' | 'desc') => void
  onFilter?: (columnId: string, value: string) => void
  onRowClick?: (row: T, index: number) => void
  onRowSelect?: (selectedRows: T[]) => void
  selectable?: boolean
  striped?: boolean
  bordered?: boolean
  hover?: boolean
  compact?: boolean
  sticky?: boolean
  maxHeight?: string
  className?: string
  tableClassName?: string
  headerClassName?: string
  bodyClassName?: string
  rowClassName?: string | ((row: T, index: number) => string)
  cellClassName?: string
}

interface TableState {
  sortColumn: string | null
  sortDirection: 'asc' | 'desc'
  filters: Record<string, string>
  selectedRows: Set<number>
  searchTerm: string
}

const Table = React.memo(<T,>({
  data,
  columns,
  loading = false,
  error = null,
  emptyMessage = 'No data available',
  pageSize,
  currentPage,
  totalPages,
  totalItems,
  onPageChange,
  onSort,
  onFilter,
  onRowClick,
  onRowSelect,
  selectable = false,
  striped = false,
  bordered = false,
  hover = true,
  compact = false,
  sticky = false,
  maxHeight,
  className,
  tableClassName,
  headerClassName,
  bodyClassName,
  rowClassName,
  cellClassName,
}: TableProps<T>) => {
  const [state, setState] = React.useState<TableState>({
    sortColumn: null,
    sortDirection: 'asc',
    filters: {},
    selectedRows: new Set(),
    searchTerm: '',
  })

  const handleSort = React.useCallback((columnId: string) => {
    const column = columns.find(col => col.id === columnId)
    if (!column?.sortable) return

    const newDirection = 
      state.sortColumn === columnId && state.sortDirection === 'asc' 
        ? 'desc' 
        : 'asc'

    setState(prev => ({
      ...prev,
      sortColumn: columnId,
      sortDirection: newDirection,
    }))

    onSort?.(columnId, newDirection)
  }, [columns, state.sortColumn, state.sortDirection, onSort])

  const handleFilter = React.useCallback((columnId: string, value: string) => {
    setState(prev => ({
      ...prev,
      filters: { ...prev.filters, [columnId]: value },
    }))

    onFilter?.(columnId, value)
  }, [onFilter])

  const handleRowSelect = React.useCallback((index: number, checked: boolean) => {
    setState(prev => {
      const newSelectedRows = new Set(prev.selectedRows)
      if (checked) {
        newSelectedRows.add(index)
      } else {
        newSelectedRows.delete(index)
      }

      const selectedData = data.filter((_, idx) => newSelectedRows.has(idx))
      onRowSelect?.(selectedData)

      return { ...prev, selectedRows: newSelectedRows }
    })
  }, [data, onRowSelect])

  const handleSelectAll = React.useCallback((checked: boolean) => {
    setState(prev => {
      const newSelectedRows = checked 
        ? new Set(data.map((_, index) => index))
        : new Set<number>()

      const selectedData = checked ? data : []
      onRowSelect?.(selectedData)

      return { ...prev, selectedRows: newSelectedRows }
    })
  }, [data, onRowSelect])

  const getCellValue = React.useCallback((row: T, column: TableColumn<T>) => {
    if (column.accessor) {
      if (typeof column.accessor === 'function') {
        return column.accessor(row)
      }
      return row[column.accessor]
    }
    return ''
  }, [])

  const renderCell = React.useCallback((row: T, column: TableColumn<T>, rowIndex: number) => {
    const value = getCellValue(row, column)
    
    if (column.cell) {
      return column.cell(value, row, rowIndex)
    }
    
    return value
  }, [getCellValue])

  const tableContainerClasses = cn(
    'relative overflow-auto',
    maxHeight && 'max-h-[var(--max-height)]',
    bordered && 'border border-gray-200 rounded-lg',
    className
  )

  const tableClasses = cn(
    'w-full divide-y divide-gray-200',
    sticky && 'table-fixed',
    tableClassName
  )

  const headerClasses = cn(
    'bg-gray-50',
    sticky && 'sticky top-0 z-10',
    headerClassName
  )

  const bodyClasses = cn(
    'bg-white divide-y divide-gray-200',
    bodyClassName
  )

  const getRowClasses = (row: T, index: number) => {
    const base = cn(
      'transition-colors duration-150',
      hover && 'hover:bg-gray-50',
      striped && index % 2 === 1 && 'bg-gray-50',
      onRowClick && 'cursor-pointer',
      state.selectedRows.has(index) && 'bg-blue-50',
    )

    if (typeof rowClassName === 'function') {
      return cn(base, rowClassName(row, index))
    }
    
    return cn(base, rowClassName)
  }

  const getCellClasses = (column: TableColumn<T>) => {
    return cn(
      'px-6 py-4 text-sm',
      compact && 'px-4 py-2',
      column.align === 'center' && 'text-center',
      column.align === 'right' && 'text-right',
      column.sticky === 'left' && 'sticky left-0 bg-white z-10',
      column.sticky === 'right' && 'sticky right-0 bg-white z-10',
      column.className,
      cellClassName
    )
  }

  const renderSortIcon = (column: TableColumn<T>) => {
    if (!column.sortable) return null

    if (state.sortColumn === column.id) {
      return state.sortDirection === 'asc' 
        ? <ChevronUp className="h-4 w-4" />
        : <ChevronDown className="h-4 w-4" />
    }

    return <ArrowUpDown className="h-4 w-4 opacity-50" />
  }

  if (error) {
    return (
      <div className="text-center py-8">
        <div className="text-red-600 text-sm">{error}</div>
      </div>
    )
  }

  return (
    <div 
      className={tableContainerClasses}
      style={maxHeight ? { '--max-height': maxHeight } as React.CSSProperties : undefined}
    >
      <table className={tableClasses}>
        <thead className={headerClasses}>
          <tr>
            {selectable && (
              <th className={getCellClasses({ id: 'select', header: '', align: 'center' } as TableColumn<T>)}>
                <input
                  type="checkbox"
                  checked={state.selectedRows.size === data.length && data.length > 0}
                  onChange={(e) => handleSelectAll(e.target.checked)}
                  className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                  aria-label="Select all rows"
                />
              </th>
            )}
            {columns.map((column) => (
              <th
                key={column.id}
                className={cn(
                  getCellClasses(column),
                  'font-medium text-gray-900 tracking-wider uppercase',
                  column.sortable && 'cursor-pointer select-none',
                  column.headerClassName
                )}
                style={{
                  width: column.width,
                  minWidth: column.minWidth,
                  maxWidth: column.maxWidth,
                }}
                onClick={() => column.sortable && handleSort(column.id)}
              >
                <div className="flex items-center justify-between">
                  <span>{column.header}</span>
                  <div className="flex items-center ml-2">
                    {renderSortIcon(column)}
                    {column.filterable && (
                      <Filter className="h-4 w-4 opacity-50 ml-1" />
                    )}
                  </div>
                </div>
              </th>
            ))}
          </tr>
        </thead>
        <tbody className={bodyClasses}>
          {loading ? (
            <tr>
              <td 
                colSpan={columns.length + (selectable ? 1 : 0)}
                className="px-6 py-8 text-center"
              >
                <div className="flex items-center justify-center">
                  <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600"></div>
                  <span className="ml-2 text-gray-600">Loading...</span>
                </div>
              </td>
            </tr>
          ) : data.length === 0 ? (
            <tr>
              <td 
                colSpan={columns.length + (selectable ? 1 : 0)}
                className="px-6 py-8 text-center text-gray-500"
              >
                {emptyMessage}
              </td>
            </tr>
          ) : (
            data.map((row, rowIndex) => (
              <tr
                key={rowIndex}
                className={getRowClasses(row, rowIndex)}
                onClick={() => onRowClick?.(row, rowIndex)}
              >
                {selectable && (
                  <td className={getCellClasses({ id: 'select', header: '', align: 'center' } as TableColumn<T>)}>
                    <input
                      type="checkbox"
                      checked={state.selectedRows.has(rowIndex)}
                      onChange={(e) => handleRowSelect(rowIndex, e.target.checked)}
                      className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                      aria-label={`Select row ${rowIndex + 1}`}
                    />
                  </td>
                )}
                {columns.map((column) => (
                  <td
                    key={column.id}
                    className={getCellClasses(column)}
                    style={{
                      width: column.width,
                      minWidth: column.minWidth,
                      maxWidth: column.maxWidth,
                    }}
                  >
                    {renderCell(row, column, rowIndex)}
                  </td>
                ))}
              </tr>
            ))
          )}
        </tbody>
      </table>

      {/* Pagination Info */}
      {(totalItems !== undefined || totalPages !== undefined) && (
        <div className="bg-white px-4 py-3 border-t border-gray-200 flex items-center justify-between">
          <div className="flex-1 flex justify-between sm:hidden">
            <button
              disabled={currentPage === 1}
              className="relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:bg-gray-100 disabled:text-gray-400"
            >
              Previous
            </button>
            <button
              disabled={currentPage === totalPages}
              className="ml-3 relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:bg-gray-100 disabled:text-gray-400"
            >
              Next
            </button>
          </div>
          <div className="hidden sm:flex-1 sm:flex sm:items-center sm:justify-between">
            <div>
              <p className="text-sm text-gray-700">
                Showing{' '}
                <span className="font-medium">
                  {((currentPage || 1) - 1) * (pageSize || data.length) + 1}
                </span>{' '}
                to{' '}
                <span className="font-medium">
                  {Math.min((currentPage || 1) * (pageSize || data.length), totalItems || data.length)}
                </span>{' '}
                of{' '}
                <span className="font-medium">{totalItems || data.length}</span>{' '}
                results
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  )
})

Table.displayName = 'Table'

export default Table