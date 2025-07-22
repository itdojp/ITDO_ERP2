import React from 'react';

// データテーブルの基本型定義
export interface Column<T = any> {
  key: string;
  title: string;
  dataIndex?: keyof T;
  width?: string | number;
  minWidth?: string | number;
  align?: 'left' | 'center' | 'right';
  sortable?: boolean;
  filterable?: boolean;
  render?: (value: any, record: T, index: number) => React.ReactNode;
  className?: string;
  headerClassName?: string;
  fixed?: 'left' | 'right';
  ellipsis?: boolean;
}

export interface SortConfig {
  key: string;
  direction: 'asc' | 'desc';
}

export interface FilterConfig {
  [key: string]: any;
}

export interface PaginationConfig {
  current: number;
  pageSize: number;
  total: number;
  showSizeChanger?: boolean;
  showQuickJumper?: boolean;
  showTotal?: boolean;
  pageSizeOptions?: number[];
}

export interface SelectionConfig<T> {
  type?: 'checkbox' | 'radio';
  selectedRowKeys?: React.Key[];
  onChange?: (selectedRowKeys: React.Key[], selectedRows: T[]) => void;
  onSelect?: (record: T, selected: boolean, selectedRows: T[], nativeEvent: Event) => void;
  onSelectAll?: (selected: boolean, selectedRows: T[], changeRows: T[]) => void;
  getCheckboxProps?: (record: T) => { disabled?: boolean; name?: string };
  columnWidth?: string | number;
  fixed?: boolean;
}

export interface DataTableProps<T = any> {
  columns: Column<T>[];
  dataSource: T[];
  rowKey?: string | ((record: T) => string);
  loading?: boolean;
  pagination?: PaginationConfig | false;
  selection?: SelectionConfig<T>;
  sortConfig?: SortConfig;
  filterConfig?: FilterConfig;
  onSort?: (sortConfig: SortConfig) => void;
  onFilter?: (filterConfig: FilterConfig) => void;
  onRowClick?: (record: T, index: number) => void;
  onRowDoubleClick?: (record: T, index: number) => void;
  expandable?: {
    expandedRowRender?: (record: T, index: number) => React.ReactNode;
    expandedRowKeys?: React.Key[];
    onExpand?: (expanded: boolean, record: T) => void;
    onExpandedRowsChange?: (expandedKeys: React.Key[]) => void;
    rowExpandable?: (record: T) => boolean;
  };
  scroll?: {
    x?: string | number;
    y?: string | number;
  };
  size?: 'small' | 'middle' | 'large';
  bordered?: boolean;
  showHeader?: boolean;
  title?: () => React.ReactNode;
  footer?: () => React.ReactNode;
  emptyText?: React.ReactNode;
  className?: string;
  rowClassName?: string | ((record: T, index: number) => string);
  onResize?: () => void;
}

// フィルターコンポーネントの型定義
export interface FilterDropdownProps {
  prefixCls?: string;
  setSelectedKeys: (selectedKeys: React.Key[]) => void;
  selectedKeys: React.Key[];
  confirm: () => void;
  clearFilters?: () => void;
  filters?: FilterOption[];
  visible?: boolean;
  column: Column;
}

export interface FilterOption {
  text: string;
  value: any;
  children?: FilterOption[];
}

// 検索・フィルター関連
export interface SearchConfig {
  placeholder?: string;
  onSearch?: (value: string) => void;
  searchValue?: string;
}

export interface AdvancedFilterConfig {
  [key: string]: {
    type: 'text' | 'select' | 'date' | 'daterange' | 'number' | 'boolean';
    label: string;
    options?: { label: string; value: any }[];
    placeholder?: string;
    value?: any;
  };
}

// 一括操作関連
export interface BulkActionConfig<T> {
  key: string;
  label: string;
  icon?: React.ReactNode;
  onClick: (selectedRows: T[], selectedRowKeys: React.Key[]) => void;
  disabled?: boolean;
  danger?: boolean;
  confirm?: {
    title: string;
    content?: string;
  };
}

// エクスポート関連
export interface ExportConfig {
  filename?: string;
  sheetName?: string;
  format?: 'csv' | 'excel';
  columns?: string[];
  excludeColumns?: string[];
}

// テーブル設定関連
export interface TableSettings {
  density: 'compact' | 'middle' | 'large';
  bordered: boolean;
  showHeader: boolean;
  pageSize: number;
  visibleColumns: string[];
  columnOrder: string[];
  columnWidths: { [key: string]: number };
}

export interface TableContextValue {
  settings: TableSettings;
  updateSettings: (settings: Partial<TableSettings>) => void;
  resetSettings: () => void;
}