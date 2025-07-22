import React, { useState, useMemo, useCallback, useRef, useEffect } from 'react';
import { 
  DataTableProps, 
  Column, 
  SortConfig, 
  FilterConfig, 
  PaginationConfig, 
  SelectionConfig 
} from './types';
import { TablePagination } from './TablePagination';
import { TableFilters } from './TableFilters';
import { LoadingSpinner } from '../ui/LoadingSpinner';
import { Button } from '../ui/Button';
import { theme } from '../../styles/theme';

export function DataTable<T = any>({
  columns,
  dataSource,
  rowKey = 'id',
  loading = false,
  pagination,
  selection,
  sortConfig,
  filterConfig,
  onSort,
  onFilter,
  onRowClick,
  onRowDoubleClick,
  expandable,
  scroll,
  size = 'middle',
  bordered = false,
  showHeader = true,
  title,
  footer,
  emptyText,
  className = '',
  rowClassName,
  onResize,
}: DataTableProps<T>) {
  const [internalSortConfig, setInternalSortConfig] = useState<SortConfig | undefined>(sortConfig);
  const [internalFilterConfig, setInternalFilterConfig] = useState<FilterConfig>(filterConfig || {});
  const [selectedRowKeys, setSelectedRowKeys] = useState<React.Key[]>(selection?.selectedRowKeys || []);
  const [expandedRowKeys, setExpandedRowKeys] = useState<React.Key[]>(expandable?.expandedRowKeys || []);
  
  const tableRef = useRef<HTMLDivElement>(null);
  const [tableWidth, setTableWidth] = useState<number>(0);

  // テーブルサイズの監視
  useEffect(() => {
    const updateTableWidth = () => {
      if (tableRef.current) {
        setTableWidth(tableRef.current.offsetWidth);
      }
    };

    updateTableWidth();
    window.addEventListener('resize', updateTableWidth);
    return () => window.removeEventListener('resize', updateTableWidth);
  }, []);

  // 行キーの取得
  const getRowKey = useCallback((record: T, index: number): string => {
    if (typeof rowKey === 'function') {
      return rowKey(record);
    }
    return String((record as any)[rowKey] || index);
  }, [rowKey]);

  // ソート処理
  const handleSort = useCallback((key: string) => {
    let direction: 'asc' | 'desc' = 'asc';
    
    if (internalSortConfig?.key === key) {
      direction = internalSortConfig.direction === 'asc' ? 'desc' : 'asc';
    }
    
    const newSortConfig = { key, direction };
    setInternalSortConfig(newSortConfig);
    
    if (onSort) {
      onSort(newSortConfig);
    }
  }, [internalSortConfig, onSort]);

  // フィルター処理
  const handleFilter = useCallback((filters: FilterConfig) => {
    setInternalFilterConfig(filters);
    if (onFilter) {
      onFilter(filters);
    }
  }, [onFilter]);

  // 選択処理
  const handleSelectChange = useCallback((keys: React.Key[], rows: T[]) => {
    setSelectedRowKeys(keys);
    if (selection?.onChange) {
      selection.onChange(keys, rows);
    }
  }, [selection]);

  const handleSelectAll = useCallback((checked: boolean) => {
    const keys = checked ? dataSource.map((record, index) => getRowKey(record, index)) : [];
    const rows = checked ? dataSource : [];
    
    setSelectedRowKeys(keys);
    if (selection?.onSelectAll) {
      selection.onSelectAll(checked, rows, dataSource);
    }
  }, [dataSource, getRowKey, selection]);

  const handleRowSelect = useCallback((record: T, index: number, checked: boolean) => {
    const key = getRowKey(record, index);
    const newKeys = checked 
      ? [...selectedRowKeys, key]
      : selectedRowKeys.filter(k => k !== key);
    
    const newRows = dataSource.filter((_, idx) => 
      newKeys.includes(getRowKey(dataSource[idx], idx))
    );
    
    setSelectedRowKeys(newKeys);
    if (selection?.onSelect) {
      selection.onSelect(record, checked, newRows, new Event('click'));
    }
  }, [selectedRowKeys, dataSource, getRowKey, selection]);

  // 展開処理
  const handleExpand = useCallback((record: T, expanded: boolean) => {
    const key = getRowKey(record, dataSource.indexOf(record));
    const newExpandedKeys = expanded
      ? [...expandedRowKeys, key]
      : expandedRowKeys.filter(k => k !== key);
    
    setExpandedRowKeys(newExpandedKeys);
    if (expandable?.onExpand) {
      expandable.onExpand(expanded, record);
    }
  }, [expandedRowKeys, expandable, dataSource, getRowKey]);

  // レンダリング用データの計算
  const renderData = useMemo(() => {
    return dataSource;
  }, [dataSource]);

  // 選択状態の計算
  const selectedRowsData = useMemo(() => {
    return dataSource.filter((record, index) => 
      selectedRowKeys.includes(getRowKey(record, index))
    );
  }, [dataSource, selectedRowKeys, getRowKey]);

  const allSelected = dataSource.length > 0 && selectedRowKeys.length === dataSource.length;
  const someSelected = selectedRowKeys.length > 0 && selectedRowKeys.length < dataSource.length;

  // スタイルクラス
  const sizeClasses = {
    small: 'text-sm',
    middle: '',
    large: 'text-base',
  };

  const tableClasses = `
    w-full bg-white 
    ${bordered ? 'border border-gray-200' : ''} 
    ${sizeClasses[size]}
    ${className}
  `;

  // ヘッダーセルのレンダリング
  const renderHeaderCell = (column: Column<T>) => {
    const canSort = column.sortable && onSort;
    const isActiveSorted = internalSortConfig?.key === column.key;
    const sortDirection = isActiveSorted ? internalSortConfig.direction : undefined;
    
    const headerClasses = `
      px-4 py-3 text-left font-medium text-gray-900 
      ${canSort ? 'cursor-pointer hover:bg-gray-50 select-none' : ''}
      ${column.headerClassName || ''}
      ${column.align === 'center' ? 'text-center' : ''}
      ${column.align === 'right' ? 'text-right' : ''}
    `;

    return (
      <th
        key={column.key}
        className={headerClasses}
        style={{ width: column.width, minWidth: column.minWidth }}
        onClick={canSort ? () => handleSort(column.key) : undefined}
      >
        <div className="flex items-center space-x-1">
          <span className={column.ellipsis ? 'truncate' : ''}>
            {column.title}
          </span>
          
          {canSort && (
            <div className="flex flex-col">
              <svg 
                className={`h-3 w-3 ${isActiveSorted && sortDirection === 'asc' ? 'text-blue-600' : 'text-gray-400'}`}
                fill="currentColor" 
                viewBox="0 0 20 20"
              >
                <path d="M14.707 12.707a1 1 0 01-1.414 0L10 9.414l-3.293 3.293a1 1 0 01-1.414-1.414l4-4a1 1 0 011.414 0l4 4a1 1 0 010 1.414z" />
              </svg>
              <svg 
                className={`h-3 w-3 -mt-1 ${isActiveSorted && sortDirection === 'desc' ? 'text-blue-600' : 'text-gray-400'}`}
                fill="currentColor" 
                viewBox="0 0 20 20"
              >
                <path d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" />
              </svg>
            </div>
          )}
        </div>
      </th>
    );
  };

  // データセルのレンダリング
  const renderCell = (column: Column<T>, record: T, index: number) => {
    const value = column.dataIndex ? (record as any)[column.dataIndex] : record;
    const cellContent = column.render ? column.render(value, record, index) : value;
    
    const cellClasses = `
      px-4 py-3 border-t border-gray-200
      ${column.className || ''}
      ${column.align === 'center' ? 'text-center' : ''}
      ${column.align === 'right' ? 'text-right' : ''}
    `;

    return (
      <td key={column.key} className={cellClasses}>
        <div className={column.ellipsis ? 'truncate' : ''}>
          {cellContent}
        </div>
      </td>
    );
  };

  // 選択列のレンダリング
  const renderSelectionColumn = () => {
    if (!selection) return null;

    const headerCell = (
      <th className="px-4 py-3 w-12" style={{ width: selection.columnWidth }}>
        {selection.type !== 'radio' && (
          <input
            type="checkbox"
            checked={allSelected}
            onChange={(e) => handleSelectAll(e.target.checked)}
            className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
            ref={(input) => {
              if (input) {
                input.indeterminate = someSelected;
              }
            }}
          />
        )}
      </th>
    );

    return { headerCell };
  };

  // 展開列のレンダリング
  const renderExpandColumn = () => {
    if (!expandable?.expandedRowRender) return null;

    const headerCell = (
      <th className="px-4 py-3 w-12"></th>
    );

    return { headerCell };
  };

  // 行クラス名の取得
  const getRowClassName = useCallback((record: T, index: number) => {
    let classes = 'hover:bg-gray-50 transition-colors';
    
    if (typeof rowClassName === 'string') {
      classes += ` ${rowClassName}`;
    } else if (typeof rowClassName === 'function') {
      classes += ` ${rowClassName(record, index)}`;
    }
    
    const key = getRowKey(record, index);
    if (selectedRowKeys.includes(key)) {
      classes += ' bg-blue-50';
    }
    
    return classes;
  }, [rowClassName, selectedRowKeys, getRowKey]);

  return (
    <div ref={tableRef} className="relative">
      {/* テーブルヘッダー（タイトル・フィルター等） */}
      {(title || selection?.selectedRowKeys?.length) && (
        <div className="mb-4 flex items-center justify-between">
          <div>
            {title && title()}
          </div>
          
          {/* 選択情報表示 */}
          {selection && selectedRowKeys.length > 0 && (
            <div className="flex items-center space-x-2 text-sm text-gray-600">
              <span>{selectedRowKeys.length} 件選択中</span>
              <Button 
                size="sm" 
                variant="ghost"
                onClick={() => handleSelectChange([], [])}
              >
                クリア
              </Button>
            </div>
          )}
        </div>
      )}

      {/* テーブル本体 */}
      <div className={`overflow-auto ${scroll?.y ? `max-h-[${scroll.y}px]` : ''}`}>
        <div className={scroll?.x ? `min-w-[${scroll.x}px]` : ''}>
          <table className={tableClasses}>
            {/* ヘッダー */}
            {showHeader && (
              <thead className="bg-gray-50">
                <tr>
                  {/* 展開列 */}
                  {expandable?.expandedRowRender && renderExpandColumn()?.headerCell}
                  
                  {/* 選択列 */}
                  {selection && renderSelectionColumn()?.headerCell}
                  
                  {/* データ列 */}
                  {columns.map(column => renderHeaderCell(column))}
                </tr>
              </thead>
            )}

            {/* ボディ */}
            <tbody className="bg-white divide-y divide-gray-200">
              {loading ? (
                <tr>
                  <td 
                    colSpan={columns.length + (selection ? 1 : 0) + (expandable?.expandedRowRender ? 1 : 0)}
                    className="px-4 py-8 text-center"
                  >
                    <LoadingSpinner size="md" />
                    <p className="mt-2 text-gray-500">データを読み込んでいます...</p>
                  </td>
                </tr>
              ) : renderData.length === 0 ? (
                <tr>
                  <td 
                    colSpan={columns.length + (selection ? 1 : 0) + (expandable?.expandedRowRender ? 1 : 0)}
                    className="px-4 py-8 text-center text-gray-500"
                  >
                    {emptyText || 'データがありません'}
                  </td>
                </tr>
              ) : (
                renderData.map((record, index) => {
                  const key = getRowKey(record, index);
                  const isExpanded = expandedRowKeys.includes(key);
                  const isSelected = selectedRowKeys.includes(key);
                  
                  return (
                    <React.Fragment key={key}>
                      {/* メインの行 */}
                      <tr
                        className={getRowClassName(record, index)}
                        onClick={onRowClick ? () => onRowClick(record, index) : undefined}
                        onDoubleClick={onRowDoubleClick ? () => onRowDoubleClick(record, index) : undefined}
                      >
                        {/* 展開セル */}
                        {expandable?.expandedRowRender && (
                          <td className="px-4 py-3 w-12">
                            {(!expandable.rowExpandable || expandable.rowExpandable(record)) && (
                              <button
                                className="text-gray-400 hover:text-gray-600"
                                onClick={(e) => {
                                  e.stopPropagation();
                                  handleExpand(record, !isExpanded);
                                }}
                              >
                                <svg 
                                  className={`h-4 w-4 transform transition-transform ${isExpanded ? 'rotate-90' : ''}`}
                                  fill="none" 
                                  stroke="currentColor" 
                                  viewBox="0 0 24 24"
                                >
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                                </svg>
                              </button>
                            )}
                          </td>
                        )}
                        
                        {/* 選択セル */}
                        {selection && (
                          <td className="px-4 py-3 w-12">
                            <input
                              type={selection.type || 'checkbox'}
                              name={selection.type === 'radio' ? 'table-selection' : undefined}
                              checked={isSelected}
                              onChange={(e) => handleRowSelect(record, index, e.target.checked)}
                              onClick={(e) => e.stopPropagation()}
                              className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                              {...(selection.getCheckboxProps ? selection.getCheckboxProps(record) : {})}
                            />
                          </td>
                        )}
                        
                        {/* データセル */}
                        {columns.map(column => renderCell(column, record, index))}
                      </tr>
                      
                      {/* 展開された行 */}
                      {expandable?.expandedRowRender && isExpanded && (
                        <tr>
                          <td 
                            colSpan={columns.length + (selection ? 1 : 0) + 1}
                            className="px-4 py-4 bg-gray-50"
                          >
                            {expandable.expandedRowRender(record, index)}
                          </td>
                        </tr>
                      )}
                    </React.Fragment>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* フッター */}
      {footer && (
        <div className="mt-4">
          {footer()}
        </div>
      )}

      {/* ページネーション */}
      {pagination && pagination !== false && (
        <div className="mt-4">
          <TablePagination {...pagination} />
        </div>
      )}
    </div>
  );
}