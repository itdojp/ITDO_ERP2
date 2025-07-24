import React, { useState, useMemo, useCallback } from "react";

export interface Column<T = any> {
  key: string;
  title: string;
  dataIndex?: string;
  render?: (value: any, record: T, index: number) => React.ReactNode;
  sortable?: boolean;
  filterable?: boolean;
  width?: number | string;
  align?: "left" | "center" | "right";
  fixed?: "left" | "right";
  className?: string;
  headerClassName?: string;
  ellipsis?: boolean;
}

export interface SortConfig {
  key: string;
  direction: "asc" | "desc";
}

interface DataTableProps<T = any> {
  columns: Column<T>[];
  dataSource: T[];
  loading?: boolean;
  pagination?: {
    current: number;
    pageSize: number;
    total: number;
    showSizeChanger?: boolean;
    onChange?: (page: number, pageSize?: number) => void;
  };
  rowKey?: string | ((record: T) => string);
  onRow?: (
    record: T,
    index: number,
  ) => {
    onClick?: (event: React.MouseEvent) => void;
    onDoubleClick?: (event: React.MouseEvent) => void;
    className?: string;
  };
  rowSelection?: {
    type?: "checkbox" | "radio";
    selectedRowKeys?: string[];
    onChange?: (selectedRowKeys: string[], selectedRows: T[]) => void;
    onSelectAll?: (
      selected: boolean,
      selectedRows: T[],
      changeRows: T[],
    ) => void;
    getCheckboxProps?: (record: T) => {
      disabled?: boolean;
      name?: string;
    };
  };
  expandable?: {
    expandedRowKeys?: string[];
    onExpand?: (expanded: boolean, record: T) => void;
    expandedRowRender?: (record: T, index: number) => React.ReactNode;
    rowExpandable?: (record: T) => boolean;
  };
  scroll?: {
    x?: number | string;
    y?: number | string;
  };
  size?: "sm" | "md" | "lg";
  bordered?: boolean;
  hoverable?: boolean;
  striped?: boolean;
  className?: string;
  tableClassName?: string;
  headerClassName?: string;
  bodyClassName?: string;
  emptyText?: React.ReactNode;
  sortConfig?: SortConfig;
  onSortChange?: (sortConfig: SortConfig | null) => void;
}

export const DataTable = <T extends Record<string, any>>({
  columns,
  dataSource,
  loading = false,
  pagination,
  rowKey = "id",
  onRow,
  rowSelection,
  expandable,
  scroll,
  size = "md",
  bordered = true,
  hoverable = true,
  striped = false,
  className = "",
  tableClassName = "",
  headerClassName = "",
  bodyClassName = "",
  emptyText = "No data",
  sortConfig,
  onSortChange,
}: DataTableProps<T>) => {
  const [internalSortConfig, setInternalSortConfig] =
    useState<SortConfig | null>(null);
  const [expandedRowKeys, setExpandedRowKeys] = useState<string[]>(
    expandable?.expandedRowKeys || [],
  );

  const currentSortConfig = sortConfig || internalSortConfig;

  const getRowKey = useCallback(
    (record: T, index: number): string => {
      if (typeof rowKey === "function") {
        return rowKey(record);
      }
      return record[rowKey] ?? index.toString();
    },
    [rowKey],
  );

  const getSizeClasses = () => {
    const sizeMap = {
      sm: "text-sm",
      md: "text-sm",
      lg: "text-base",
    };
    return sizeMap[size];
  };

  const getCellPadding = () => {
    const paddingMap = {
      sm: "px-3 py-2",
      md: "px-4 py-3",
      lg: "px-6 py-4",
    };
    return paddingMap[size];
  };

  const sortedData = useMemo(() => {
    if (!currentSortConfig) return dataSource;

    const { key, direction } = currentSortConfig;
    const column = columns.find((col) => col.key === key);
    if (!column?.sortable) return dataSource;

    const dataIndex = column.dataIndex || key;

    return [...dataSource].sort((a, b) => {
      const aVal = a[dataIndex];
      const bVal = b[dataIndex];

      if (aVal === bVal) return 0;
      if (aVal == null) return direction === "asc" ? -1 : 1;
      if (bVal == null) return direction === "asc" ? 1 : -1;

      if (typeof aVal === "string" && typeof bVal === "string") {
        return direction === "asc"
          ? aVal.localeCompare(bVal)
          : bVal.localeCompare(aVal);
      }

      return direction === "asc"
        ? aVal < bVal
          ? -1
          : 1
        : aVal > bVal
          ? -1
          : 1;
    });
  }, [dataSource, currentSortConfig, columns]);

  const handleSort = (column: Column<T>) => {
    if (!column.sortable) return;

    let newSortConfig: SortConfig | null;

    if (currentSortConfig?.key === column.key) {
      newSortConfig =
        currentSortConfig.direction === "asc"
          ? { key: column.key, direction: "desc" }
          : null;
    } else {
      newSortConfig = { key: column.key, direction: "asc" };
    }

    if (!sortConfig) {
      setInternalSortConfig(newSortConfig);
    }

    onSortChange?.(newSortConfig);
  };

  const handleExpandRow = (record: T) => {
    const key = getRowKey(record, 0);
    const isExpanded = expandedRowKeys.includes(key);

    const newExpandedKeys = isExpanded
      ? expandedRowKeys.filter((k) => k !== key)
      : [...expandedRowKeys, key];

    setExpandedRowKeys(newExpandedKeys);
    expandable?.onExpand?.(!isExpanded, record);
  };

  const isRowExpanded = (record: T): boolean => {
    const key = getRowKey(record, 0);
    return expandedRowKeys.includes(key);
  };

  const handleSelectAll = (checked: boolean) => {
    if (!rowSelection) return;

    const allRowKeys = dataSource.map((record, index) =>
      getRowKey(record, index),
    );
    const newSelectedKeys = checked ? allRowKeys : [];
    const newSelectedRows = checked ? dataSource : [];

    rowSelection.onChange?.(newSelectedKeys, newSelectedRows);
    rowSelection.onSelectAll?.(checked, newSelectedRows, dataSource);
  };

  const handleSelectRow = (record: T, index: number) => {
    if (!rowSelection) return;

    const key = getRowKey(record, index);
    const currentSelected = rowSelection.selectedRowKeys || [];

    let newSelectedKeys: string[];
    let newSelectedRows: T[];

    if (rowSelection.type === "radio") {
      newSelectedKeys = [key];
      newSelectedRows = [record];
    } else {
      const isSelected = currentSelected.includes(key);
      newSelectedKeys = isSelected
        ? currentSelected.filter((k) => k !== key)
        : [...currentSelected, key];
      newSelectedRows = dataSource.filter((_, idx) =>
        newSelectedKeys.includes(getRowKey(dataSource[idx], idx)),
      );
    }

    rowSelection.onChange?.(newSelectedKeys, newSelectedRows);
  };

  const renderSortIcon = (column: Column<T>) => {
    if (!column.sortable) return null;

    const isSorted = currentSortConfig?.key === column.key;
    const direction = currentSortConfig?.direction;

    return (
      <span className="ml-2 inline-flex flex-col">
        <svg
          className={`w-3 h-3 -mb-1 ${
            isSorted && direction === "asc" ? "text-blue-600" : "text-gray-400"
          }`}
          fill="currentColor"
          viewBox="0 0 20 20"
        >
          <path d="M14.707 12.707a1 1 0 01-1.414 0L10 9.414l-3.293 3.293a1 1 0 01-1.414-1.414l4-4a1 1 0 011.414 0l4 4a1 1 0 010 1.414z" />
        </svg>
        <svg
          className={`w-3 h-3 ${
            isSorted && direction === "desc" ? "text-blue-600" : "text-gray-400"
          }`}
          fill="currentColor"
          viewBox="0 0 20 20"
        >
          <path d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" />
        </svg>
      </span>
    );
  };

  const renderCell = (column: Column<T>, record: T, index: number) => {
    const dataIndex = column.dataIndex || column.key;
    const value = record[dataIndex];

    const cellContent = column.render
      ? column.render(value, record, index)
      : value?.toString() || "";

    const alignClass =
      column.align === "center"
        ? "text-center"
        : column.align === "right"
          ? "text-right"
          : "text-left";

    return (
      <td
        key={column.key}
        className={`
          ${getCellPadding()}
          ${alignClass}
          ${column.ellipsis ? "truncate" : ""}
          ${column.className || ""}
          border-b border-gray-200
        `}
        style={{ width: column.width }}
      >
        <div className={column.ellipsis ? "truncate" : ""}>{cellContent}</div>
      </td>
    );
  };

  const renderLoadingRow = () => (
    <tr>
      <td
        colSpan={columns.length + (rowSelection ? 1 : 0) + (expandable ? 1 : 0)}
        className={`${getCellPadding()} text-center border-b border-gray-200`}
      >
        <div className="flex items-center justify-center gap-2 text-gray-500">
          <div className="w-4 h-4 border-2 border-gray-300 border-t-blue-500 rounded-full animate-spin"></div>
          <span>Loading...</span>
        </div>
      </td>
    </tr>
  );

  const renderEmptyRow = () => (
    <tr>
      <td
        colSpan={columns.length + (rowSelection ? 1 : 0) + (expandable ? 1 : 0)}
        className={`${getCellPadding()} text-center text-gray-500 border-b border-gray-200`}
      >
        {emptyText}
      </td>
    </tr>
  );

  if (loading && !dataSource.length) {
    return (
      <div className={`${className}`}>
        <div
          className={`overflow-auto ${scroll?.x ? "overflow-x-auto" : ""} ${scroll?.y ? "overflow-y-auto" : ""}`}
          style={{ maxHeight: scroll?.y }}
        >
          <table
            className={`w-full ${getSizeClasses()} ${bordered ? "border-collapse border border-gray-200" : ""} ${tableClassName}`}
          >
            <thead className={`bg-gray-50 ${headerClassName}`}>
              <tr>
                {columns.map((column) => (
                  <th
                    key={column.key}
                    className={`${getCellPadding()} text-left font-medium text-gray-900 border-b border-gray-200`}
                  >
                    {column.title}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className={bodyClassName}>{renderLoadingRow()}</tbody>
          </table>
        </div>
      </div>
    );
  }

  return (
    <div className={`${className}`}>
      <div
        className={`overflow-auto ${scroll?.x ? "overflow-x-auto" : ""} ${scroll?.y ? "overflow-y-auto" : ""}`}
        style={{ maxHeight: scroll?.y }}
      >
        <table
          className={`w-full ${getSizeClasses()} ${bordered ? "border-collapse border border-gray-200" : ""} ${tableClassName}`}
        >
          <thead className={`bg-gray-50 ${headerClassName}`}>
            <tr>
              {rowSelection && (
                <th
                  className={`${getCellPadding()} text-left font-medium text-gray-900 border-b border-gray-200`}
                  style={{ width: "40px" }}
                >
                  {rowSelection.type !== "radio" && (
                    <input
                      type="checkbox"
                      checked={
                        rowSelection.selectedRowKeys?.length ===
                          dataSource.length && dataSource.length > 0
                      }
                      onChange={(e) => handleSelectAll(e.target.checked)}
                      className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                    />
                  )}
                </th>
              )}
              {expandable && (
                <th
                  className={`${getCellPadding()} text-left font-medium text-gray-900 border-b border-gray-200`}
                  style={{ width: "40px" }}
                ></th>
              )}
              {columns.map((column) => (
                <th
                  key={column.key}
                  className={`
                    ${getCellPadding()}
                    text-left font-medium text-gray-900 border-b border-gray-200
                    ${column.sortable ? "cursor-pointer hover:bg-gray-100 select-none" : ""}
                    ${column.headerClassName || ""}
                  `}
                  style={{ width: column.width }}
                  onClick={() => handleSort(column)}
                >
                  <div className="flex items-center">
                    <span>{column.title}</span>
                    {renderSortIcon(column)}
                  </div>
                </th>
              ))}
            </tr>
          </thead>
          <tbody
            className={`${bodyClassName} ${hoverable ? "divide-y divide-gray-200" : ""}`}
          >
            {loading && renderLoadingRow()}
            {!loading && !sortedData.length && renderEmptyRow()}
            {!loading &&
              sortedData.map((record, index) => {
                const key = getRowKey(record, index);
                const rowProps = onRow?.(record, index);
                const isExpanded = isRowExpanded(record);
                const isSelected = rowSelection?.selectedRowKeys?.includes(key);

                return (
                  <React.Fragment key={key}>
                    <tr
                      className={`
                      ${hoverable ? "hover:bg-gray-50" : ""}
                      ${striped && index % 2 === 1 ? "bg-gray-50" : ""}
                      ${isSelected ? "bg-blue-50" : ""}
                      ${rowProps?.className || ""}
                    `}
                      onClick={rowProps?.onClick}
                      onDoubleClick={rowProps?.onDoubleClick}
                    >
                      {rowSelection && (
                        <td
                          className={`${getCellPadding()} border-b border-gray-200`}
                        >
                          <input
                            type={rowSelection.type || "checkbox"}
                            checked={isSelected}
                            onChange={() => handleSelectRow(record, index)}
                            disabled={
                              rowSelection.getCheckboxProps?.(record)?.disabled
                            }
                            className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                          />
                        </td>
                      )}
                      {expandable && (
                        <td
                          className={`${getCellPadding()} border-b border-gray-200`}
                        >
                          {expandable.rowExpandable?.(record) !== false && (
                            <button
                              onClick={() => handleExpandRow(record)}
                              className="p-1 rounded hover:bg-gray-200 transition-colors"
                            >
                              <svg
                                className={`w-4 h-4 transition-transform ${isExpanded ? "rotate-90" : ""}`}
                                fill="none"
                                stroke="currentColor"
                                viewBox="0 0 24 24"
                              >
                                <path
                                  strokeLinecap="round"
                                  strokeLinejoin="round"
                                  strokeWidth={2}
                                  d="M9 5l7 7-7 7"
                                />
                              </svg>
                            </button>
                          )}
                        </td>
                      )}
                      {columns.map((column) =>
                        renderCell(column, record, index),
                      )}
                    </tr>
                    {expandable &&
                      isExpanded &&
                      expandable.expandedRowRender && (
                        <tr>
                          <td
                            colSpan={
                              columns.length + (rowSelection ? 1 : 0) + 1
                            }
                            className="p-0 border-b border-gray-200"
                          >
                            <div className="bg-gray-50 p-4">
                              {expandable.expandedRowRender(record, index)}
                            </div>
                          </td>
                        </tr>
                      )}
                  </React.Fragment>
                );
              })}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default DataTable;
