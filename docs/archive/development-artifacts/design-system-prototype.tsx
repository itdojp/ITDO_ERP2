import React, { useState } from 'react';

// Design Tokens Definition
const designTokens = {
  colors: {
    primary: {
      50: '#fff7ed',   // 最も薄いオレンジ
      100: '#ffedd5',
      200: '#fed7aa',
      300: '#fdba74',
      400: '#fb923c',
      500: '#f97316',  // メインオレンジ
      600: '#ea580c',
      700: '#c2410c',
      800: '#9a3412',
      900: '#7c2d12'   // 最も濃いオレンジ
    },
    neutral: {
      50: '#fafafa',
      100: '#f5f5f5',
      200: '#e5e5e5',
      300: '#d4d4d4',
      400: '#a3a3a3',
      500: '#737373',
      600: '#525252',
      700: '#404040',
      800: '#262626',
      900: '#171717'
    },
    semantic: {
      success: '#22c55e',
      warning: '#eab308',
      error: '#ef4444',
      info: '#3b82f6'
    }
  },
  typography: {
    fontFamily: {
      sans: 'Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
      mono: '"JetBrains Mono", Consolas, monospace'
    },
    fontSize: {
      xs: '12px',
      sm: '14px',
      base: '16px',
      lg: '18px',
      xl: '20px',
      '2xl': '24px'
    },
    fontWeight: {
      normal: '400',
      medium: '500',
      semibold: '600',
      bold: '700'
    }
  },
  spacing: {
    unit: 8,
    scale: [0, 4, 8, 12, 16, 24, 32, 48, 64, 96, 128]
  }
};

// Button Component with all variants and states
const Button = ({ 
  variant = 'primary', 
  size = 'md', 
  disabled = false, 
  loading = false, 
  children, 
  onClick 
}) => {
  const baseStyles = {
    fontFamily: designTokens.typography.fontFamily.sans,
    fontWeight: designTokens.typography.fontWeight.medium,
    borderRadius: '6px',
    border: 'none',
    cursor: disabled ? 'not-allowed' : 'pointer',
    transition: 'all 0.2s ease',
    display: 'inline-flex',
    alignItems: 'center',
    justifyContent: 'center',
    gap: '8px'
  };

  const sizeStyles = {
    sm: { 
      height: '32px', 
      padding: '0 12px', 
      fontSize: designTokens.typography.fontSize.sm 
    },
    md: { 
      height: '40px', 
      padding: '0 16px', 
      fontSize: designTokens.typography.fontSize.base 
    },
    lg: { 
      height: '48px', 
      padding: '0 24px', 
      fontSize: designTokens.typography.fontSize.lg 
    }
  };

  const variantStyles = {
    primary: {
      backgroundColor: disabled ? designTokens.colors.neutral[300] : designTokens.colors.primary[500],
      color: disabled ? designTokens.colors.neutral[500] : 'white',
      ':hover': !disabled && {
        backgroundColor: designTokens.colors.primary[600]
      }
    },
    secondary: {
      backgroundColor: disabled ? designTokens.colors.neutral[100] : designTokens.colors.neutral[100],
      color: disabled ? designTokens.colors.neutral[400] : designTokens.colors.neutral[700],
      ':hover': !disabled && {
        backgroundColor: designTokens.colors.neutral[200]
      }
    },
    outline: {
      backgroundColor: 'transparent',
      border: `1px solid ${disabled ? designTokens.colors.neutral[300] : designTokens.colors.primary[500]}`,
      color: disabled ? designTokens.colors.neutral[400] : designTokens.colors.primary[500],
      ':hover': !disabled && {
        backgroundColor: designTokens.colors.primary[50]
      }
    },
    ghost: {
      backgroundColor: 'transparent',
      color: disabled ? designTokens.colors.neutral[400] : designTokens.colors.neutral[600],
      ':hover': !disabled && {
        backgroundColor: designTokens.colors.neutral[100]
      }
    },
    danger: {
      backgroundColor: disabled ? designTokens.colors.neutral[300] : designTokens.colors.semantic.error,
      color: disabled ? designTokens.colors.neutral[500] : 'white',
      ':hover': !disabled && {
        backgroundColor: '#dc2626'
      }
    }
  };

  return (
    <button
      style={{
        ...baseStyles,
        ...sizeStyles[size],
        ...variantStyles[variant],
        opacity: disabled ? 0.6 : 1
      }}
      disabled={disabled}
      onClick={onClick}
    >
      {loading && <div style={{ 
        width: '16px', 
        height: '16px', 
        border: '2px solid currentColor',
        borderTop: '2px solid transparent',
        borderRadius: '50%',
        animation: 'spin 1s linear infinite'
      }} />}
      {children}
    </button>
  );
};

// Input Component
const Input = ({ 
  type = 'text', 
  placeholder, 
  disabled = false, 
  error = false, 
  icon,
  value,
  onChange
}) => {
  const [focused, setFocused] = useState(false);

  const containerStyles = {
    position: 'relative',
    display: 'inline-block',
    width: '100%'
  };

  const inputStyles = {
    width: '100%',
    height: '40px',
    padding: icon ? '0 40px 0 12px' : '0 12px',
    fontSize: designTokens.typography.fontSize.base,
    fontFamily: designTokens.typography.fontFamily.sans,
    border: `1px solid ${
      error ? designTokens.colors.semantic.error : 
      focused ? designTokens.colors.primary[500] : 
      designTokens.colors.neutral[300]
    }`,
    borderRadius: '6px',
    backgroundColor: disabled ? designTokens.colors.neutral[50] : 'white',
    color: disabled ? designTokens.colors.neutral[400] : designTokens.colors.neutral[800],
    outline: 'none',
    transition: 'all 0.2s ease'
  };

  return (
    <div style={containerStyles}>
      <input
        type={type}
        placeholder={placeholder}
        disabled={disabled}
        value={value}
        onChange={onChange}
        onFocus={() => setFocused(true)}
        onBlur={() => setFocused(false)}
        style={inputStyles}
      />
      {icon && (
        <div style={{
          position: 'absolute',
          right: '12px',
          top: '50%',
          transform: 'translateY(-50%)',
          color: designTokens.colors.neutral[400]
        }}>
          {icon}
        </div>
      )}
    </div>
  );
};

// Card Component
const Card = ({ children, header, footer, interactive = false }) => {
  const cardStyles = {
    backgroundColor: 'white',
    border: `1px solid ${designTokens.colors.neutral[200]}`,
    borderRadius: '8px',
    overflow: 'hidden',
    transition: 'all 0.2s ease',
    cursor: interactive ? 'pointer' : 'default',
    ':hover': interactive && {
      boxShadow: '0 4px 12px rgba(0, 0, 0, 0.1)',
      borderColor: designTokens.colors.neutral[300]
    }
  };

  return (
    <div style={cardStyles}>
      {header && (
        <div style={{
          padding: '16px 24px',
          borderBottom: `1px solid ${designTokens.colors.neutral[200]}`,
          backgroundColor: designTokens.colors.neutral[50]
        }}>
          {header}
        </div>
      )}
      <div style={{ padding: '24px' }}>
        {children}
      </div>
      {footer && (
        <div style={{
          padding: '16px 24px',
          borderTop: `1px solid ${designTokens.colors.neutral[200]}`,
          backgroundColor: designTokens.colors.neutral[50]
        }}>
          {footer}
        </div>
      )}
    </div>
  );
};

// Select/Dropdown Component
const Select = ({ 
  options = [], 
  value, 
  onChange, 
  placeholder = "Select option...",
  searchable = false,
  multiple = false,
  disabled = false,
  error = false 
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [focusedIndex, setFocusedIndex] = useState(-1);

  // Filter options based on search term
  const filteredOptions = searchable 
    ? options.filter(option => 
        option.label.toLowerCase().includes(searchTerm.toLowerCase())
      )
    : options;

  // Handle option selection
  const handleOptionSelect = (selectedOption) => {
    if (multiple) {
      const currentValues = Array.isArray(value) ? value : [];
      const isSelected = currentValues.some(v => v.value === selectedOption.value);
      
      if (isSelected) {
        // Remove from selection
        const newValue = currentValues.filter(v => v.value !== selectedOption.value);
        onChange(newValue);
      } else {
        // Add to selection
        onChange([...currentValues, selectedOption]);
      }
    } else {
      onChange(selectedOption);
      setIsOpen(false);
    }
    setSearchTerm('');
  };

  // Handle keyboard navigation
  const handleKeyDown = (e) => {
    if (!isOpen) {
      if (e.key === 'Enter' || e.key === ' ') {
        setIsOpen(true);
        e.preventDefault();
      }
      return;
    }

    switch (e.key) {
      case 'Escape':
        setIsOpen(false);
        setFocusedIndex(-1);
        break;
      case 'ArrowDown':
        setFocusedIndex(prev => 
          prev < filteredOptions.length - 1 ? prev + 1 : 0
        );
        e.preventDefault();
        break;
      case 'ArrowUp':
        setFocusedIndex(prev => 
          prev > 0 ? prev - 1 : filteredOptions.length - 1
        );
        e.preventDefault();
        break;
      case 'Enter':
        if (focusedIndex >= 0) {
          handleOptionSelect(filteredOptions[focusedIndex]);
        }
        e.preventDefault();
        break;
    }
  };

  // Get display value for the select trigger
  const getDisplayValue = () => {
    if (multiple) {
      const selectedValues = Array.isArray(value) ? value : [];
      if (selectedValues.length === 0) return placeholder;
      if (selectedValues.length === 1) return selectedValues[0].label;
      return `${selectedValues.length} items selected`;
    }
    return value ? value.label : placeholder;
  };

  return (
    <div style={{ position: 'relative', width: '100%' }}>
      {/* Select Trigger */}
      <div
        onClick={() => !disabled && setIsOpen(!isOpen)}
        onKeyDown={handleKeyDown}
        tabIndex={disabled ? -1 : 0}
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          width: '100%',
          height: '40px',
          padding: '0 12px',
          fontSize: designTokens.typography.fontSize.base,
          fontFamily: designTokens.typography.fontFamily.sans,
          border: `1px solid ${
            error ? designTokens.colors.semantic.error : 
            isOpen ? designTokens.colors.primary[500] : 
            designTokens.colors.neutral[300]
          }`,
          borderRadius: '6px',
          backgroundColor: disabled ? designTokens.colors.neutral[50] : 'white',
          color: disabled ? designTokens.colors.neutral[400] : designTokens.colors.neutral[800],
          cursor: disabled ? 'not-allowed' : 'pointer',
          outline: 'none',
          transition: 'all 0.2s ease'
        }}
      >
        <span style={{
          color: value ? designTokens.colors.neutral[800] : designTokens.colors.neutral[400],
          overflow: 'hidden',
          textOverflow: 'ellipsis',
          whiteSpace: 'nowrap'
        }}>
          {getDisplayValue()}
        </span>
        <span style={{
          transform: isOpen ? 'rotate(180deg)' : 'rotate(0deg)',
          transition: 'transform 0.2s ease',
          color: designTokens.colors.neutral[400]
        }}>
          ▼
        </span>
      </div>

      {/* Selected Items Display (for multiple mode) */}
      {multiple && Array.isArray(value) && value.length > 0 && (
        <div style={{
          display: 'flex',
          flexWrap: 'wrap',
          gap: '8px',
          marginTop: '8px'
        }}>
          {value.map((item, index) => (
            <div
              key={index}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                padding: '4px 8px',
                backgroundColor: designTokens.colors.primary[100],
                color: designTokens.colors.primary[700],
                borderRadius: '4px',
                fontSize: designTokens.typography.fontSize.sm
              }}
            >
              {item.label}
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  handleOptionSelect(item);
                }}
                style={{
                  background: 'none',
                  border: 'none',
                  color: designTokens.colors.primary[600],
                  cursor: 'pointer',
                  padding: 0,
                  fontSize: '12px'
                }}
              >
                ×
              </button>
            </div>
          ))}
        </div>
      )}

      {/* Dropdown Menu */}
      {isOpen && (
        <div style={{
          position: 'absolute',
          top: '100%',
          left: 0,
          right: 0,
          zIndex: 1000,
          marginTop: '4px',
          backgroundColor: 'white',
          border: `1px solid ${designTokens.colors.neutral[300]}`,
          borderRadius: '6px',
          boxShadow: '0 4px 12px rgba(0, 0, 0, 0.1)',
          maxHeight: '200px',
          overflow: 'auto'
        }}>
          {/* Search Input */}
          {searchable && (
            <div style={{ padding: '8px' }}>
              <input
                type="text"
                placeholder="Search options..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                style={{
                  width: '100%',
                  padding: '8px 12px',
                  border: `1px solid ${designTokens.colors.neutral[300]}`,
                  borderRadius: '4px',
                  fontSize: designTokens.typography.fontSize.sm,
                  outline: 'none'
                }}
                onClick={(e) => e.stopPropagation()}
              />
            </div>
          )}

          {/* Options List */}
          {filteredOptions.length === 0 ? (
            <div style={{
              padding: '12px',
              color: designTokens.colors.neutral[500],
              fontSize: designTokens.typography.fontSize.sm,
              textAlign: 'center'
            }}>
              No options found
            </div>
          ) : (
            filteredOptions.map((option, index) => {
              const isSelected = multiple 
                ? Array.isArray(value) && value.some(v => v.value === option.value)
                : value && value.value === option.value;
              const isFocused = index === focusedIndex;

              return (
                <div
                  key={option.value}
                  onClick={() => handleOptionSelect(option)}
                  style={{
                    padding: '12px',
                    cursor: 'pointer',
                    backgroundColor: isFocused 
                      ? designTokens.colors.primary[50] 
                      : isSelected 
                        ? designTokens.colors.primary[100] 
                        : 'transparent',
                    color: isSelected 
                      ? designTokens.colors.primary[700] 
                      : designTokens.colors.neutral[800],
                    borderLeft: isSelected 
                      ? `3px solid ${designTokens.colors.primary[500]}` 
                      : '3px solid transparent',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between'
                  }}
                >
                  {option.label}
                  {isSelected && <span style={{ fontSize: '14px' }}>✓</span>}
                </div>
              );
            })
          )}
        </div>
      )}
    </div>
  );
};

// Table Component with sorting, pagination, and selection
const Table = ({ 
  data = [], 
  columns = [], 
  sortable = true, 
  selectable = false,
  pageSize = 10,
  onRowSelect,
  onSort,
  actions 
}) => {
  const [sortConfig, setSortConfig] = useState({ key: null, direction: 'asc' });
  const [selectedRows, setSelectedRows] = useState(new Set());
  const [currentPage, setCurrentPage] = useState(1);

  // Handle sorting logic
  const handleSort = (key) => {
    if (!sortable) return;
    
    let direction = 'asc';
    if (sortConfig.key === key && sortConfig.direction === 'asc') {
      direction = 'desc';
    }
    
    const newSortConfig = { key, direction };
    setSortConfig(newSortConfig);
    
    if (onSort) {
      onSort(newSortConfig);
    }
  };

  // Sort data based on current sort configuration
  const sortedData = React.useMemo(() => {
    if (!sortConfig.key) return data;
    
    return [...data].sort((a, b) => {
      const aValue = a[sortConfig.key];
      const bValue = b[sortConfig.key];
      
      if (aValue < bValue) {
        return sortConfig.direction === 'asc' ? -1 : 1;
      }
      if (aValue > bValue) {
        return sortConfig.direction === 'asc' ? 1 : -1;
      }
      return 0;
    });
  }, [data, sortConfig]);

  // Calculate pagination
  const totalPages = Math.ceil(sortedData.length / pageSize);
  const startIndex = (currentPage - 1) * pageSize;
  const paginatedData = sortedData.slice(startIndex, startIndex + pageSize);

  // Handle row selection
  const handleRowSelect = (rowId, checked) => {
    const newSelectedRows = new Set(selectedRows);
    if (checked) {
      newSelectedRows.add(rowId);
    } else {
      newSelectedRows.delete(rowId);
    }
    setSelectedRows(newSelectedRows);
    
    if (onRowSelect) {
      onRowSelect(Array.from(newSelectedRows));
    }
  };

  // Handle select all
  const handleSelectAll = (checked) => {
    if (checked) {
      const allIds = new Set(paginatedData.map(row => row.id));
      setSelectedRows(allIds);
      if (onRowSelect) {
        onRowSelect(Array.from(allIds));
      }
    } else {
      setSelectedRows(new Set());
      if (onRowSelect) {
        onRowSelect([]);
      }
    }
  };

  const isAllSelected = paginatedData.length > 0 && 
    paginatedData.every(row => selectedRows.has(row.id));
  const isIndeterminate = paginatedData.some(row => selectedRows.has(row.id)) && !isAllSelected;

  return (
    <div style={{ width: '100%' }}>
      {/* Table Container */}
      <div style={{ 
        border: `1px solid ${designTokens.colors.neutral[200]}`,
        borderRadius: '8px',
        overflow: 'hidden',
        backgroundColor: 'white'
      }}>
        <div style={{ overflowX: 'auto' }}>
          <table style={{ 
            width: '100%', 
            borderCollapse: 'collapse',
            fontFamily: designTokens.typography.fontFamily.sans
          }}>
            {/* Table Header */}
            <thead>
              <tr style={{ backgroundColor: designTokens.colors.neutral[50] }}>
                {selectable && (
                  <th style={{
                    width: '48px',
                    padding: '12px 16px',
                    textAlign: 'center',
                    borderBottom: `1px solid ${designTokens.colors.neutral[200]}`
                  }}>
                    <input
                      type="checkbox"
                      checked={isAllSelected}
                      ref={input => {
                        if (input) input.indeterminate = isIndeterminate;
                      }}
                      onChange={(e) => handleSelectAll(e.target.checked)}
                      style={{ cursor: 'pointer' }}
                    />
                  </th>
                )}
                
                {columns.map((column) => (
                  <th
                    key={column.key}
                    onClick={() => column.sortable !== false && handleSort(column.key)}
                    style={{
                      padding: '12px 16px',
                      textAlign: column.align || 'left',
                      fontSize: designTokens.typography.fontSize.sm,
                      fontWeight: designTokens.typography.fontWeight.semibold,
                      color: designTokens.colors.neutral[700],
                      cursor: column.sortable !== false && sortable ? 'pointer' : 'default',
                      borderBottom: `1px solid ${designTokens.colors.neutral[200]}`,
                      position: 'relative',
                      userSelect: 'none'
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      {column.label}
                      {column.sortable !== false && sortable && (
                        <span style={{
                          fontSize: '12px',
                          color: sortConfig.key === column.key 
                            ? designTokens.colors.primary[500] 
                            : designTokens.colors.neutral[400],
                          transform: sortConfig.key === column.key && sortConfig.direction === 'desc' 
                            ? 'rotate(180deg)' : 'rotate(0deg)',
                          transition: 'all 0.2s ease'
                        }}>
                          ▲
                        </span>
                      )}
                    </div>
                  </th>
                ))}
                
                {actions && (
                  <th style={{
                    width: '120px',
                    padding: '12px 16px',
                    textAlign: 'center',
                    fontSize: designTokens.typography.fontSize.sm,
                    fontWeight: designTokens.typography.fontWeight.semibold,
                    color: designTokens.colors.neutral[700],
                    borderBottom: `1px solid ${designTokens.colors.neutral[200]}`
                  }}>
                    Actions
                  </th>
                )}
              </tr>
            </thead>

            {/* Table Body */}
            <tbody>
              {paginatedData.map((row, rowIndex) => (
                <tr 
                  key={row.id}
                  style={{
                    backgroundColor: selectedRows.has(row.id) 
                      ? designTokens.colors.primary[50] 
                      : rowIndex % 2 === 0 
                        ? 'white' 
                        : designTokens.colors.neutral[25] || '#fafafa',
                    ':hover': {
                      backgroundColor: designTokens.colors.neutral[50]
                    }
                  }}
                >
                  {selectable && (
                    <td style={{
                      padding: '12px 16px',
                      textAlign: 'center',
                      borderBottom: `1px solid ${designTokens.colors.neutral[200]}`
                    }}>
                      <input
                        type="checkbox"
                        checked={selectedRows.has(row.id)}
                        onChange={(e) => handleRowSelect(row.id, e.target.checked)}
                        style={{ cursor: 'pointer' }}
                      />
                    </td>
                  )}
                  
                  {columns.map((column) => (
                    <td
                      key={column.key}
                      style={{
                        padding: '12px 16px',
                        textAlign: column.align || 'left',
                        fontSize: designTokens.typography.fontSize.sm,
                        color: designTokens.colors.neutral[700],
                        borderBottom: `1px solid ${designTokens.colors.neutral[200]}`
                      }}
                    >
                      {column.render ? column.render(row[column.key], row) : row[column.key]}
                    </td>
                  ))}
                  
                  {actions && (
                    <td style={{
                      padding: '12px 16px',
                      textAlign: 'center',
                      borderBottom: `1px solid ${designTokens.colors.neutral[200]}`
                    }}>
                      <div style={{ display: 'flex', gap: '8px', justifyContent: 'center' }}>
                        {actions.map((action, actionIndex) => (
                          <button
                            key={actionIndex}
                            onClick={() => action.onClick(row)}
                            style={{
                              padding: '4px 8px',
                              fontSize: '12px',
                              border: `1px solid ${designTokens.colors.neutral[300]}`,
                              borderRadius: '4px',
                              backgroundColor: 'white',
                              color: designTokens.colors.neutral[600],
                              cursor: 'pointer',
                              transition: 'all 0.2s ease'
                            }}
                            onMouseEnter={(e) => {
                              e.target.style.backgroundColor = designTokens.colors.neutral[50];
                            }}
                            onMouseLeave={(e) => {
                              e.target.style.backgroundColor = 'white';
                            }}
                          >
                            {action.label}
                          </button>
                        ))}
                      </div>
                    </td>
                  )}
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        {totalPages > 1 && (
          <div style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            padding: '16px 24px',
            borderTop: `1px solid ${designTokens.colors.neutral[200]}`,
            backgroundColor: designTokens.colors.neutral[50]
          }}>
            <div style={{
              fontSize: designTokens.typography.fontSize.sm,
              color: designTokens.colors.neutral[600]
            }}>
              Showing {startIndex + 1} to {Math.min(startIndex + pageSize, sortedData.length)} of {sortedData.length} entries
            </div>
            
            <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
              <button
                onClick={() => setCurrentPage(prev => Math.max(prev - 1, 1))}
                disabled={currentPage === 1}
                style={{
                  padding: '8px 12px',
                  fontSize: designTokens.typography.fontSize.sm,
                  border: `1px solid ${designTokens.colors.neutral[300]}`,
                  borderRadius: '4px',
                  backgroundColor: 'white',
                  color: currentPage === 1 ? designTokens.colors.neutral[400] : designTokens.colors.neutral[700],
                  cursor: currentPage === 1 ? 'not-allowed' : 'pointer'
                }}
              >
                Previous
              </button>
              
              <span style={{
                fontSize: designTokens.typography.fontSize.sm,
                color: designTokens.colors.neutral[600]
              }}>
                Page {currentPage} of {totalPages}
              </span>
              
              <button
                onClick={() => setCurrentPage(prev => Math.min(prev + 1, totalPages))}
                disabled={currentPage === totalPages}
                style={{
                  padding: '8px 12px',
                  fontSize: designTokens.typography.fontSize.sm,
                  border: `1px solid ${designTokens.colors.neutral[300]}`,
                  borderRadius: '4px',
                  backgroundColor: 'white',
                  color: currentPage === totalPages ? designTokens.colors.neutral[400] : designTokens.colors.neutral[700],
                  cursor: currentPage === totalPages ? 'not-allowed' : 'pointer'
                }}
              >
                Next
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

// Sidebar Navigation Component
const Sidebar = ({ collapsed = false, onToggle, menuItems = [] }) => {
  const [expandedItems, setExpandedItems] = useState(new Set());
  const [activeItem, setActiveItem] = useState('dashboard');

  // Toggle submenu expansion
  const toggleSubmenu = (itemKey) => {
    const newExpanded = new Set(expandedItems);
    if (newExpanded.has(itemKey)) {
      newExpanded.delete(itemKey);
    } else {
      newExpanded.add(itemKey);
    }
    setExpandedItems(newExpanded);
  };

  // Handle menu item click
  const handleItemClick = (item) => {
    if (item.children) {
      toggleSubmenu(item.key);
    } else {
      setActiveItem(item.key);
      if (item.onClick) {
        item.onClick(item);
      }
    }
  };

  // Render menu item with possible children
  const renderMenuItem = (item, level = 0) => {
    const hasChildren = item.children && item.children.length > 0;
    const isExpanded = expandedItems.has(item.key);
    const isActive = activeItem === item.key;
    const paddingLeft = collapsed ? 16 : 16 + (level * 20);

    return (
      <div key={item.key}>
        <div
          onClick={() => handleItemClick(item)}
          style={{
            display: 'flex',
            alignItems: 'center',
            padding: `12px ${paddingLeft}px`,
            cursor: 'pointer',
            backgroundColor: isActive ? designTokens.colors.primary[100] : 'transparent',
            borderRight: isActive ? `3px solid ${designTokens.colors.primary[500]}` : '3px solid transparent',
            color: isActive ? designTokens.colors.primary[700] : designTokens.colors.neutral[600],
            fontSize: designTokens.typography.fontSize.sm,
            fontWeight: isActive ? designTokens.typography.fontWeight.medium : designTokens.typography.fontWeight.normal,
            transition: 'all 0.2s ease',
            ':hover': {
              backgroundColor: designTokens.colors.neutral[100]
            }
          }}
          onMouseEnter={(e) => {
            if (!isActive) {
              e.target.style.backgroundColor = designTokens.colors.neutral[100];
            }
          }}
          onMouseLeave={(e) => {
            if (!isActive) {
              e.target.style.backgroundColor = 'transparent';
            }
          }}
        >
          {/* Icon */}
          <span style={{ 
            marginRight: collapsed ? 0 : 12,
            fontSize: '16px',
            minWidth: '16px'
          }}>
            {item.icon}
          </span>

          {/* Label (hidden when collapsed) */}
          {!collapsed && (
            <>
              <span style={{ flex: 1 }}>{item.label}</span>
              {hasChildren && (
                <span style={{
                  fontSize: '12px',
                  transform: isExpanded ? 'rotate(180deg)' : 'rotate(0deg)',
                  transition: 'transform 0.2s ease'
                }}>
                  ▼
                </span>
              )}
            </>
          )}
        </div>

        {/* Submenu (only shown when expanded and not collapsed) */}
        {hasChildren && isExpanded && !collapsed && (
          <div>
            {item.children.map(child => renderMenuItem(child, level + 1))}
          </div>
        )}
      </div>
    );
  };

  return (
    <div style={{
      width: collapsed ? '64px' : '280px',
      height: '100vh',
      backgroundColor: 'white',
      borderRight: `1px solid ${designTokens.colors.neutral[200]}`,
      transition: 'width 0.3s ease',
      overflowY: 'auto',
      position: 'fixed',
      left: 0,
      top: 0,
      zIndex: 1000
    }}>
      {/* Sidebar Header */}
      <div style={{
        padding: '16px',
        borderBottom: `1px solid ${designTokens.colors.neutral[200]}`,
        display: 'flex',
        alignItems: 'center',
        justifyContent: collapsed ? 'center' : 'space-between'
      }}>
        {!collapsed && (
          <div style={{
            fontSize: designTokens.typography.fontSize.lg,
            fontWeight: designTokens.typography.fontWeight.bold,
            color: designTokens.colors.primary[600]
          }}>
            ITDO ERP
          </div>
        )}
        
        <button
          onClick={onToggle}
          style={{
            background: 'none',
            border: 'none',
            cursor: 'pointer',
            padding: '8px',
            borderRadius: '4px',
            color: designTokens.colors.neutral[600],
            fontSize: '16px'
          }}
        >
          {collapsed ? '→' : '←'}
        </button>
      </div>

      {/* Menu Items */}
      <div style={{ padding: '16px 0' }}>
        {menuItems.map(item => renderMenuItem(item))}
      </div>
    </div>
  );
};

// Top Navigation Bar Component
const TopNavigation = ({ user, notifications = [], onSearch }) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [showNotifications, setShowNotifications] = useState(false);
  const [showUserMenu, setShowUserMenu] = useState(false);

  const unreadNotifications = notifications.filter(n => !n.read).length;

  return (
    <div style={{
      height: '64px',
      backgroundColor: 'white',
      borderBottom: `1px solid ${designTokens.colors.neutral[200]}`,
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      padding: '0 24px',
      position: 'fixed',
      top: 0,
      right: 0,
      left: '280px', // Adjust based on sidebar width
      zIndex: 999,
      transition: 'left 0.3s ease'
    }}>
      {/* Left Section - Search */}
      <div style={{ flex: 1, maxWidth: '400px' }}>
        <div style={{ position: 'relative' }}>
          <input
            type="text"
            placeholder="Search anything..."
            value={searchTerm}
            onChange={(e) => {
              setSearchTerm(e.target.value);
              if (onSearch) onSearch(e.target.value);
            }}
            style={{
              width: '100%',
              height: '40px',
              padding: '0 40px 0 12px',
              fontSize: designTokens.typography.fontSize.sm,
              border: `1px solid ${designTokens.colors.neutral[300]}`,
              borderRadius: '20px',
              backgroundColor: designTokens.colors.neutral[50],
              outline: 'none',
              transition: 'all 0.2s ease'
            }}
            onFocus={(e) => {
              e.target.style.borderColor = designTokens.colors.primary[500];
              e.target.style.backgroundColor = 'white';
            }}
            onBlur={(e) => {
              e.target.style.borderColor = designTokens.colors.neutral[300];
              e.target.style.backgroundColor = designTokens.colors.neutral[50];
            }}
          />
          <span style={{
            position: 'absolute',
            right: '12px',
            top: '50%',
            transform: 'translateY(-50%)',
            color: designTokens.colors.neutral[400],
            fontSize: '16px'
          }}>
            🔍
          </span>
        </div>
      </div>

      {/* Right Section - Notifications & User Menu */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
        {/* Notifications */}
        <div style={{ position: 'relative' }}>
          <button
            onClick={() => setShowNotifications(!showNotifications)}
            style={{
              position: 'relative',
              background: 'none',
              border: 'none',
              cursor: 'pointer',
              padding: '8px',
              borderRadius: '8px',
              color: designTokens.colors.neutral[600],
              fontSize: '20px'
            }}
          >
            🔔
            {unreadNotifications > 0 && (
              <span style={{
                position: 'absolute',
                top: '4px',
                right: '4px',
                backgroundColor: designTokens.colors.semantic.error,
                color: 'white',
                borderRadius: '50%',
                width: '18px',
                height: '18px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: '10px',
                fontWeight: designTokens.typography.fontWeight.bold
              }}>
                {unreadNotifications > 99 ? '99+' : unreadNotifications}
              </span>
            )}
          </button>

          {/* Notifications Dropdown */}
          {showNotifications && (
            <div style={{
              position: 'absolute',
              top: '100%',
              right: 0,
              width: '320px',
              marginTop: '8px',
              backgroundColor: 'white',
              border: `1px solid ${designTokens.colors.neutral[200]}`,
              borderRadius: '8px',
              boxShadow: '0 4px 12px rgba(0, 0, 0, 0.1)',
              maxHeight: '400px',
              overflowY: 'auto',
              zIndex: 1001
            }}>
              <div style={{
                padding: '16px',
                borderBottom: `1px solid ${designTokens.colors.neutral[200]}`,
                fontWeight: designTokens.typography.fontWeight.semibold
              }}>
                Notifications ({unreadNotifications} unread)
              </div>
              
              {notifications.length === 0 ? (
                <div style={{
                  padding: '24px',
                  textAlign: 'center',
                  color: designTokens.colors.neutral[500],
                  fontSize: designTokens.typography.fontSize.sm
                }}>
                  No notifications
                </div>
              ) : (
                notifications.map((notification, index) => (
                  <div
                    key={index}
                    style={{
                      padding: '16px',
                      borderBottom: index < notifications.length - 1 ? `1px solid ${designTokens.colors.neutral[200]}` : 'none',
                      backgroundColor: notification.read ? 'white' : designTokens.colors.primary[25] || '#fef7ed'
                    }}
                  >
                    <div style={{
                      fontWeight: notification.read ? designTokens.typography.fontWeight.normal : designTokens.typography.fontWeight.semibold,
                      fontSize: designTokens.typography.fontSize.sm,
                      marginBottom: '4px'
                    }}>
                      {notification.title}
                    </div>
                    <div style={{
                      fontSize: designTokens.typography.fontSize.xs,
                      color: designTokens.colors.neutral[600]
                    }}>
                      {notification.message}
                    </div>
                    <div style={{
                      fontSize: designTokens.typography.fontSize.xs,
                      color: designTokens.colors.neutral[500],
                      marginTop: '4px'
                    }}>
                      {notification.time}
                    </div>
                  </div>
                ))
              )}
            </div>
          )}
        </div>

        {/* User Menu */}
        <div style={{ position: 'relative' }}>
          <button
            onClick={() => setShowUserMenu(!showUserMenu)}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              background: 'none',
              border: 'none',
              cursor: 'pointer',
              padding: '8px',
              borderRadius: '8px'
            }}
          >
            <div style={{
              width: '32px',
              height: '32px',
              borderRadius: '50%',
              backgroundColor: designTokens.colors.primary[500],
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: 'white',
              fontSize: designTokens.typography.fontSize.sm,
              fontWeight: designTokens.typography.fontWeight.semibold
            }}>
              {user ? user.name.charAt(0).toUpperCase() : 'U'}
            </div>
            <span style={{
              fontSize: designTokens.typography.fontSize.sm,
              color: designTokens.colors.neutral[700]
            }}>
              {user ? user.name : 'User'}
            </span>
            <span style={{
              fontSize: '12px',
              color: designTokens.colors.neutral[400]
            }}>
              ▼
            </span>
          </button>

          {/* User Dropdown */}
          {showUserMenu && (
            <div style={{
              position: 'absolute',
              top: '100%',
              right: 0,
              width: '200px',
              marginTop: '8px',
              backgroundColor: 'white',
              border: `1px solid ${designTokens.colors.neutral[200]}`,
              borderRadius: '8px',
              boxShadow: '0 4px 12px rgba(0, 0, 0, 0.1)',
              zIndex: 1001
            }}>
              {[
                { label: 'Profile', icon: '👤' },
                { label: 'Settings', icon: '⚙️' },
                { label: 'Help', icon: '❓' },
                { label: 'Logout', icon: '🚪' }
              ].map((item, index) => (
                <div
                  key={index}
                  style={{
                    padding: '12px 16px',
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '12px',
                    fontSize: designTokens.typography.fontSize.sm,
                    color: designTokens.colors.neutral[700],
                    borderBottom: index < 3 ? `1px solid ${designTokens.colors.neutral[200]}` : 'none'
                  }}
                  onMouseEnter={(e) => {
                    e.target.style.backgroundColor = designTokens.colors.neutral[50];
                  }}
                  onMouseLeave={(e) => {
                    e.target.style.backgroundColor = 'white';
                  }}
                >
                  <span>{item.icon}</span>
                  <span>{item.label}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

// Checkbox Component
const Checkbox = ({ 
  checked = false, 
  onChange, 
  label, 
  disabled = false, 
  indeterminate = false,
  error = false 
}) => {
  const checkboxId = `checkbox-${Math.random().toString(36).substr(2, 9)}`;

  return (
    <div style={{ display: 'flex', alignItems: 'flex-start', gap: '8px' }}>
      <div style={{ position: 'relative', marginTop: '2px' }}>
        <input
          id={checkboxId}
          type="checkbox"
          checked={checked}
          onChange={onChange}
          disabled={disabled}
          ref={input => {
            if (input) input.indeterminate = indeterminate;
          }}
          style={{
            width: '16px',
            height: '16px',
            margin: 0,
            opacity: 0,
            position: 'absolute',
            cursor: disabled ? 'not-allowed' : 'pointer'
          }}
        />
        <div
          style={{
            width: '16px',
            height: '16px',
            borderRadius: '3px',
            border: `2px solid ${
              error ? designTokens.colors.semantic.error :
              checked || indeterminate ? designTokens.colors.primary[500] : 
              designTokens.colors.neutral[400]
            }`,
            backgroundColor: checked || indeterminate ? designTokens.colors.primary[500] : 'white',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            transition: 'all 0.2s ease',
            opacity: disabled ? 0.5 : 1,
            cursor: disabled ? 'not-allowed' : 'pointer'
          }}
        >
          {checked && (
            <span style={{ 
              color: 'white', 
              fontSize: '12px', 
              lineHeight: 1,
              fontWeight: 'bold'
            }}>
              ✓
            </span>
          )}
          {indeterminate && !checked && (
            <div style={{
              width: '8px',
              height: '2px',
              backgroundColor: 'white'
            }} />
          )}
        </div>
      </div>
      
      {label && (
        <label
          htmlFor={checkboxId}
          style={{
            fontSize: designTokens.typography.fontSize.sm,
            color: disabled ? designTokens.colors.neutral[400] : designTokens.colors.neutral[700],
            cursor: disabled ? 'not-allowed' : 'pointer',
            lineHeight: '1.4',
            userSelect: 'none'
          }}
        >
          {label}
        </label>
      )}
    </div>
  );
};

// Radio Button Component
const Radio = ({ 
  checked = false, 
  onChange, 
  value,
  name,
  label, 
  disabled = false,
  error = false 
}) => {
  const radioId = `radio-${Math.random().toString(36).substr(2, 9)}`;

  return (
    <div style={{ display: 'flex', alignItems: 'flex-start', gap: '8px' }}>
      <div style={{ position: 'relative', marginTop: '2px' }}>
        <input
          id={radioId}
          type="radio"
          checked={checked}
          onChange={onChange}
          value={value}
          name={name}
          disabled={disabled}
          style={{
            width: '16px',
            height: '16px',
            margin: 0,
            opacity: 0,
            position: 'absolute',
            cursor: disabled ? 'not-allowed' : 'pointer'
          }}
        />
        <div
          style={{
            width: '16px',
            height: '16px',
            borderRadius: '50%',
            border: `2px solid ${
              error ? designTokens.colors.semantic.error :
              checked ? designTokens.colors.primary[500] : 
              designTokens.colors.neutral[400]
            }`,
            backgroundColor: 'white',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            transition: 'all 0.2s ease',
            opacity: disabled ? 0.5 : 1,
            cursor: disabled ? 'not-allowed' : 'pointer'
          }}
        >
          {checked && (
            <div style={{
              width: '8px',
              height: '8px',
              borderRadius: '50%',
              backgroundColor: designTokens.colors.primary[500]
            }} />
          )}
        </div>
      </div>
      
      {label && (
        <label
          htmlFor={radioId}
          style={{
            fontSize: designTokens.typography.fontSize.sm,
            color: disabled ? designTokens.colors.neutral[400] : designTokens.colors.neutral[700],
            cursor: disabled ? 'not-allowed' : 'pointer',
            lineHeight: '1.4',
            userSelect: 'none'
          }}
        >
          {label}
        </label>
      )}
    </div>
  );
};

// Toggle Switch Component
const Toggle = ({ 
  checked = false, 
  onChange, 
  label, 
  disabled = false,
  size = 'md' // sm, md, lg
}) => {
  const toggleId = `toggle-${Math.random().toString(36).substr(2, 9)}`;
  
  const sizes = {
    sm: { width: 32, height: 18, dot: 14 },
    md: { width: 44, height: 24, dot: 20 },
    lg: { width: 56, height: 32, dot: 28 }
  };
  
  const currentSize = sizes[size];

  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
      <div style={{ position: 'relative' }}>
        <input
          id={toggleId}
          type="checkbox"
          checked={checked}
          onChange={onChange}
          disabled={disabled}
          style={{
            width: currentSize.width,
            height: currentSize.height,
            margin: 0,
            opacity: 0,
            position: 'absolute',
            cursor: disabled ? 'not-allowed' : 'pointer'
          }}
        />
        <div
          style={{
            width: currentSize.width,
            height: currentSize.height,
            borderRadius: currentSize.height / 2,
            backgroundColor: checked 
              ? designTokens.colors.primary[500] 
              : designTokens.colors.neutral[300],
            transition: 'all 0.3s ease',
            cursor: disabled ? 'not-allowed' : 'pointer',
            opacity: disabled ? 0.5 : 1,
            position: 'relative'
          }}
        >
          <div
            style={{
              width: currentSize.dot,
              height: currentSize.dot,
              borderRadius: '50%',
              backgroundColor: 'white',
              position: 'absolute',
              top: '50%',
              left: checked 
                ? `${currentSize.width - currentSize.dot - 2}px` 
                : '2px',
              transform: 'translateY(-50%)',
              transition: 'all 0.3s ease',
              boxShadow: '0 2px 4px rgba(0, 0, 0, 0.2)'
            }}
          />
        </div>
      </div>
      
      {label && (
        <label
          htmlFor={toggleId}
          style={{
            fontSize: designTokens.typography.fontSize.sm,
            color: disabled ? designTokens.colors.neutral[400] : designTokens.colors.neutral[700],
            cursor: disabled ? 'not-allowed' : 'pointer',
            lineHeight: '1.4',
            userSelect: 'none'
          }}
        >
          {label}
        </label>
      )}
    </div>
  );
};

// Date Picker Component (simplified version)
const DatePicker = ({ 
  value, 
  onChange, 
  placeholder = "Select date...",
  disabled = false,
  error = false,
  min,
  max
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [displayValue, setDisplayValue] = useState('');

  // Format date for display
  const formatDate = (dateStr) => {
    if (!dateStr) return '';
    const date = new Date(dateStr);
    return date.toLocaleDateString('ja-JP', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit'
    });
  };

  // Update display value when value changes
  React.useEffect(() => {
    setDisplayValue(value ? formatDate(value) : '');
  }, [value]);

  return (
    <div style={{ position: 'relative', width: '100%' }}>
      <div
        onClick={() => !disabled && setIsOpen(!isOpen)}
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          width: '100%',
          height: '40px',
          padding: '0 12px',
          fontSize: designTokens.typography.fontSize.base,
          fontFamily: designTokens.typography.fontFamily.sans,
          border: `1px solid ${
            error ? designTokens.colors.semantic.error : 
            isOpen ? designTokens.colors.primary[500] : 
            designTokens.colors.neutral[300]
          }`,
          borderRadius: '6px',
          backgroundColor: disabled ? designTokens.colors.neutral[50] : 'white',
          color: disabled ? designTokens.colors.neutral[400] : designTokens.colors.neutral[800],
          cursor: disabled ? 'not-allowed' : 'pointer',
          outline: 'none',
          transition: 'all 0.2s ease'
        }}
      >
        <span style={{
          color: displayValue ? designTokens.colors.neutral[800] : designTokens.colors.neutral[400]
        }}>
          {displayValue || placeholder}
        </span>
        <span style={{ color: designTokens.colors.neutral[400] }}>📅</span>
      </div>

      {/* Simple native date input overlay */}
      {isOpen && (
        <div style={{
          position: 'absolute',
          top: '100%',
          left: 0,
          right: 0,
          zIndex: 1000,
          marginTop: '4px',
          backgroundColor: 'white',
          border: `1px solid ${designTokens.colors.neutral[300]}`,
          borderRadius: '6px',
          padding: '16px',
          boxShadow: '0 4px 12px rgba(0, 0, 0, 0.1)'
        }}>
          <input
            type="date"
            value={value || ''}
            onChange={(e) => {
              onChange(e.target.value);
              setIsOpen(false);
            }}
            min={min}
            max={max}
            style={{
              width: '100%',
              padding: '8px',
              border: `1px solid ${designTokens.colors.neutral[300]}`,
              borderRadius: '4px',
              fontSize: designTokens.typography.fontSize.sm
            }}
            autoFocus
          />
        </div>
      )}
    </div>
  );
};

// Time Picker Component
const TimePicker = ({ 
  value, 
  onChange, 
  placeholder = "Select time...",
  disabled = false,
  error = false,
  format24 = true
}) => {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <div style={{ position: 'relative', width: '100%' }}>
      <div
        onClick={() => !disabled && setIsOpen(!isOpen)}
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          width: '100%',
          height: '40px',
          padding: '0 12px',
          fontSize: designTokens.typography.fontSize.base,
          fontFamily: designTokens.typography.fontFamily.sans,
          border: `1px solid ${
            error ? designTokens.colors.semantic.error : 
            isOpen ? designTokens.colors.primary[500] : 
            designTokens.colors.neutral[300]
          }`,
          borderRadius: '6px',
          backgroundColor: disabled ? designTokens.colors.neutral[50] : 'white',
          color: disabled ? designTokens.colors.neutral[400] : designTokens.colors.neutral[800],
          cursor: disabled ? 'not-allowed' : 'pointer',
          outline: 'none',
          transition: 'all 0.2s ease'
        }}
      >
        <span style={{
          color: value ? designTokens.colors.neutral[800] : designTokens.colors.neutral[400]
        }}>
          {value || placeholder}
        </span>
        <span style={{ color: designTokens.colors.neutral[400] }}>🕐</span>
      </div>

      {isOpen && (
        <div style={{
          position: 'absolute',
          top: '100%',
          left: 0,
          right: 0,
          zIndex: 1000,
          marginTop: '4px',
          backgroundColor: 'white',
          border: `1px solid ${designTokens.colors.neutral[300]}`,
          borderRadius: '6px',
          padding: '16px',
          boxShadow: '0 4px 12px rgba(0, 0, 0, 0.1)'
        }}>
          <input
            type="time"
            value={value || ''}
            onChange={(e) => {
              onChange(e.target.value);
              setIsOpen(false);
            }}
            style={{
              width: '100%',
              padding: '8px',
              border: `1px solid ${designTokens.colors.neutral[300]}`,
              borderRadius: '4px',
              fontSize: designTokens.typography.fontSize.sm
            }}
            autoFocus
          />
        </div>
      )}
    </div>
  );
};

// Modal/Dialog Component
const Modal = ({ 
  isOpen = false, 
  onClose, 
  title, 
  children, 
  size = 'md', // sm, md, lg, xl
  showCloseButton = true,
  footer,
  preventClosing = false
}) => {
  // Prevent background scrolling when modal is open
  React.useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = 'unset';
    }
    
    // Cleanup function to restore scrolling
    return () => {
      document.body.style.overflow = 'unset';
    };
  }, [isOpen]);

  // Handle ESC key press to close modal
  React.useEffect(() => {
    const handleEscapeKey = (event) => {
      if (event.key === 'Escape' && isOpen && !preventClosing) {
        onClose();
      }
    };

    document.addEventListener('keydown', handleEscapeKey);
    return () => document.removeEventListener('keydown', handleEscapeKey);
  }, [isOpen, onClose, preventClosing]);

  if (!isOpen) return null;

  // Define modal sizes
  const sizes = {
    sm: { maxWidth: '400px' },
    md: { maxWidth: '500px' },
    lg: { maxWidth: '700px' },
    xl: { maxWidth: '900px' }
  };

  return (
    <div 
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        backgroundColor: 'rgba(0, 0, 0, 0.5)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 9999,
        padding: '20px'
      }}
      onClick={(e) => {
        // Close modal when clicking on backdrop (unless prevented)
        if (e.target === e.currentTarget && !preventClosing) {
          onClose();
        }
      }}
    >
      <div
        style={{
          backgroundColor: 'white',
          borderRadius: '8px',
          boxShadow: '0 10px 25px rgba(0, 0, 0, 0.2)',
          width: '100%',
          ...sizes[size],
          maxHeight: '90vh',
          overflow: 'hidden',
          display: 'flex',
          flexDirection: 'column'
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Modal Header */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '20px 24px',
          borderBottom: `1px solid ${designTokens.colors.neutral[200]}`
        }}>
          <h2 style={{
            margin: 0,
            fontSize: designTokens.typography.fontSize.lg,
            fontWeight: designTokens.typography.fontWeight.semibold,
            color: designTokens.colors.neutral[800]
          }}>
            {title}
          </h2>
          
          {showCloseButton && (
            <button
              onClick={onClose}
              style={{
                background: 'none',
                border: 'none',
                fontSize: '24px',
                cursor: 'pointer',
                color: designTokens.colors.neutral[400],
                padding: '4px',
                borderRadius: '4px',
                lineHeight: 1
              }}
              onMouseEnter={(e) => {
                e.target.style.backgroundColor = designTokens.colors.neutral[100];
                e.target.style.color = designTokens.colors.neutral[600];
              }}
              onMouseLeave={(e) => {
                e.target.style.backgroundColor = 'transparent';
                e.target.style.color = designTokens.colors.neutral[400];
              }}
            >
              ×
            </button>
          )}
        </div>

        {/* Modal Body */}
        <div style={{
          padding: '24px',
          overflowY: 'auto',
          flex: 1
        }}>
          {children}
        </div>

        {/* Modal Footer */}
        {footer && (
          <div style={{
            padding: '16px 24px',
            borderTop: `1px solid ${designTokens.colors.neutral[200]}`,
            backgroundColor: designTokens.colors.neutral[25] || '#fafafa'
          }}>
            {footer}
          </div>
        )}
      </div>
    </div>
  );
};

// Alert/Notification Component
const Alert = ({ 
  type = 'info', // success, warning, error, info
  title, 
  message, 
  onClose,
  dismissible = true,
  icon = true
}) => {
  // Define alert configurations based on type
  const alertConfigs = {
    success: {
      backgroundColor: designTokens.colors.semantic.success + '15',
      borderColor: designTokens.colors.semantic.success + '30',
      textColor: '#065f46', // Dark green for better contrast
      icon: '✓'
    },
    warning: {
      backgroundColor: '#fef3c7', // Light yellow background
      borderColor: '#f59e0b30',
      textColor: '#92400e', // Dark yellow-brown for better contrast
      icon: '⚠'
    },
    error: {
      backgroundColor: designTokens.colors.semantic.error + '15',
      borderColor: designTokens.colors.semantic.error + '30',
      textColor: '#991b1b', // Dark red for better contrast
      icon: '✕'
    },
    info: {
      backgroundColor: designTokens.colors.semantic.info + '15',
      borderColor: designTokens.colors.semantic.info + '30',
      textColor: '#1e40af', // Dark blue for better contrast
      icon: 'ℹ'
    }
  };

  const config = alertConfigs[type];

  return (
    <div style={{
      display: 'flex',
      alignItems: 'flex-start',
      gap: '12px',
      padding: '16px',
      backgroundColor: config.backgroundColor,
      border: `1px solid ${config.borderColor}`,
      borderRadius: '6px',
      color: config.textColor,
      position: 'relative'
    }}>
      {/* Alert Icon */}
      {icon && (
        <div style={{
          marginTop: '2px',
          fontSize: '16px',
          fontWeight: 'bold'
        }}>
          {config.icon}
        </div>
      )}

      {/* Alert Content */}
      <div style={{ flex: 1 }}>
        {title && (
          <div style={{
            fontWeight: designTokens.typography.fontWeight.semibold,
            fontSize: designTokens.typography.fontSize.sm,
            marginBottom: message ? '4px' : 0
          }}>
            {title}
          </div>
        )}
        
        {message && (
          <div style={{
            fontSize: designTokens.typography.fontSize.sm,
            lineHeight: '1.4'
          }}>
            {message}
          </div>
        )}
      </div>

      {/* Close Button */}
      {dismissible && onClose && (
        <button
          onClick={onClose}
          style={{
            background: 'none',
            border: 'none',
            fontSize: '18px',
            cursor: 'pointer',
            color: config.textColor,
            padding: '2px',
            borderRadius: '2px',
            opacity: 0.7,
            lineHeight: 1
          }}
          onMouseEnter={(e) => {
            e.target.style.opacity = '1';
          }}
          onMouseLeave={(e) => {
            e.target.style.opacity = '0.7';
          }}
        >
          ×
        </button>
      )}
    </div>
  );
};

// Toast Notification Component
const Toast = ({ 
  type = 'info',
  title,
  message,
  duration = 5000,
  onClose,
  position = 'top-right' // top-right, top-left, bottom-right, bottom-left
}) => {
  const [isVisible, setIsVisible] = useState(true);

  // Auto-dismiss toast after duration
  React.useEffect(() => {
    if (duration > 0) {
      const timer = setTimeout(() => {
        setIsVisible(false);
        setTimeout(() => onClose && onClose(), 300); // Wait for animation
      }, duration);

      return () => clearTimeout(timer);
    }
  }, [duration, onClose]);

  // Position styles
  const positions = {
    'top-right': { top: '24px', right: '24px' },
    'top-left': { top: '24px', left: '24px' },
    'bottom-right': { bottom: '24px', right: '24px' },
    'bottom-left': { bottom: '24px', left: '24px' }
  };

  if (!isVisible) return null;

  return (
    <div style={{
      position: 'fixed',
      ...positions[position],
      zIndex: 10000,
      transform: isVisible ? 'translateX(0)' : 'translateX(100%)',
      transition: 'transform 0.3s ease',
      minWidth: '300px',
      maxWidth: '400px'
    }}>
      <Alert
        type={type}
        title={title}
        message={message}
        onClose={() => {
          setIsVisible(false);
          setTimeout(() => onClose && onClose(), 300);
        }}
        dismissible={true}
      />
    </div>
  );
};

// Loading States Components
const Spinner = ({ size = 'md', color = 'primary' }) => {
  const sizes = {
    sm: '16px',
    md: '24px',
    lg: '32px',
    xl: '48px'
  };

  const colors = {
    primary: designTokens.colors.primary[500],
    neutral: designTokens.colors.neutral[500],
    white: '#ffffff'
  };

  return (
    <div
      style={{
        width: sizes[size],
        height: sizes[size],
        border: `3px solid ${colors[color]}30`,
        borderTop: `3px solid ${colors[color]}`,
        borderRadius: '50%',
        animation: 'spin 1s linear infinite'
      }}
    />
  );
};

const SkeletonLoader = ({ 
  width = '100%', 
  height = '20px', 
  borderRadius = '4px',
  count = 1
}) => {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
      {Array.from({ length: count }).map((_, index) => (
        <div
          key={index}
          style={{
            width,
            height,
            borderRadius,
            backgroundColor: designTokens.colors.neutral[200],
            position: 'relative',
            overflow: 'hidden'
          }}
        >
          <div
            style={{
              position: 'absolute',
              top: 0,
              left: '-100%',
              width: '100%',
              height: '100%',
              background: `linear-gradient(90deg, transparent, ${designTokens.colors.neutral[100]}, transparent)`,
              animation: 'skeleton-loading 1.5s infinite'
            }}
          />
        </div>
      ))}
    </div>
  );
};

const ProgressBar = ({ 
  value = 0, 
  max = 100, 
  size = 'md',
  showLabel = false,
  color = 'primary'
}) => {
  const percentage = Math.min(Math.max((value / max) * 100, 0), 100);
  
  const sizes = {
    sm: '4px',
    md: '8px',
    lg: '12px'
  };

  const colors = {
    primary: designTokens.colors.primary[500],
    success: designTokens.colors.semantic.success,
    warning: designTokens.colors.semantic.warning,
    error: designTokens.colors.semantic.error
  };

  return (
    <div>
      {showLabel && (
        <div style={{
          display: 'flex',
          justifyContent: 'space-between',
          marginBottom: '8px',
          fontSize: designTokens.typography.fontSize.sm,
          color: designTokens.colors.neutral[600]
        }}>
          <span>Progress</span>
          <span>{Math.round(percentage)}%</span>
        </div>
      )}
      
      <div style={{
        width: '100%',
        height: sizes[size],
        backgroundColor: designTokens.colors.neutral[200],
        borderRadius: sizes[size],
        overflow: 'hidden'
      }}>
        <div
          style={{
            width: `${percentage}%`,
            height: '100%',
            backgroundColor: colors[color],
            borderRadius: sizes[size],
            transition: 'width 0.3s ease'
          }}
        />
      </div>
    </div>
  );
};

const LoadingOverlay = ({ 
  isLoading = false, 
  message = "Loading...",
  children 
}) => {
  return (
    <div style={{ position: 'relative' }}>
      {children}
      
      {isLoading && (
        <div style={{
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: 'rgba(255, 255, 255, 0.8)',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          gap: '16px',
          zIndex: 1000
        }}>
          <Spinner size="lg" />
          {message && (
            <div style={{
              fontSize: designTokens.typography.fontSize.sm,
              color: designTokens.colors.neutral[600]
            }}>
              {message}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

// Chart Components (Simple implementations for demonstration)
const LineChart = ({ data = [], width = 400, height = 200, color = 'primary' }) => {
  // This is a simplified chart implementation for demonstration
  // In a real application, you would use a library like recharts or d3
  
  const maxValue = Math.max(...data.map(d => d.value));
  const minValue = Math.min(...data.map(d => d.value));
  const range = maxValue - minValue || 1;
  
  // Generate SVG path for the line
  const generatePath = () => {
    return data.map((point, index) => {
      const x = (index / (data.length - 1)) * (width - 40) + 20;
      const y = height - 40 - ((point.value - minValue) / range) * (height - 80);
      return `${index === 0 ? 'M' : 'L'} ${x} ${y}`;
    }).join(' ');
  };

  const colors = {
    primary: designTokens.colors.primary[500],
    success: designTokens.colors.semantic.success,
    warning: designTokens.colors.semantic.warning,
    error: designTokens.colors.semantic.error
  };

  return (
    <div style={{ 
      backgroundColor: 'white',
      border: `1px solid ${designTokens.colors.neutral[200]}`,
      borderRadius: '6px',
      padding: '16px'
    }}>
      <svg width={width} height={height} style={{ overflow: 'visible' }}>
        {/* Grid lines */}
        {[0, 0.25, 0.5, 0.75, 1].map(ratio => {
          const y = height - 40 - ratio * (height - 80);
          return (
            <line
              key={ratio}
              x1={20}
              y1={y}
              x2={width - 20}
              y2={y}
              stroke={designTokens.colors.neutral[200]}
              strokeWidth={1}
            />
          );
        })}
        
        {/* Chart line */}
        <path
          d={generatePath()}
          stroke={colors[color]}
          strokeWidth={3}
          fill="none"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
        
        {/* Data points */}
        {data.map((point, index) => {
          const x = (index / (data.length - 1)) * (width - 40) + 20;
          const y = height - 40 - ((point.value - minValue) / range) * (height - 80);
          
          return (
            <circle
              key={index}
              cx={x}
              cy={y}
              r={4}
              fill={colors[color]}
              stroke="white"
              strokeWidth={2}
            />
          );
        })}
        
        {/* Y-axis labels */}
        {[minValue, maxValue].map((value, index) => {
          const y = height - 40 - index * (height - 80);
          return (
            <text
              key={index}
              x={15}
              y={y + 4}
              textAnchor="end"
              fontSize={12}
              fill={designTokens.colors.neutral[600]}
            >
              {value.toLocaleString()}
            </text>
          );
        })}
      </svg>
    </div>
  );
};

const BarChart = ({ data = [], width = 400, height = 200, color = 'primary' }) => {
  const maxValue = Math.max(...data.map(d => d.value));
  const barWidth = (width - 80) / data.length;
  
  const colors = {
    primary: designTokens.colors.primary[500],
    success: designTokens.colors.semantic.success,
    warning: designTokens.colors.semantic.warning,
    error: designTokens.colors.semantic.error
  };

  return (
    <div style={{ 
      backgroundColor: 'white',
      border: `1px solid ${designTokens.colors.neutral[200]}`,
      borderRadius: '6px',
      padding: '16px'
    }}>
      <svg width={width} height={height}>
        {/* Bars */}
        {data.map((item, index) => {
          const barHeight = (item.value / maxValue) * (height - 80);
          const x = 40 + index * barWidth + barWidth * 0.1;
          const y = height - 40 - barHeight;
          
          return (
            <g key={index}>
              <rect
                x={x}
                y={y}
                width={barWidth * 0.8}
                height={barHeight}
                fill={colors[color]}
                rx={2}
              />
              
              {/* Value labels */}
              <text
                x={x + (barWidth * 0.4)}
                y={y - 5}
                textAnchor="middle"
                fontSize={12}
                fill={designTokens.colors.neutral[600]}
              >
                {item.value}
              </text>
              
              {/* Category labels */}
              <text
                x={x + (barWidth * 0.4)}
                y={height - 25}
                textAnchor="middle"
                fontSize={12}
                fill={designTokens.colors.neutral[600]}
              >
                {item.label}
              </text>
            </g>
          );
        })}
      </svg>
    </div>
  );
};

// Stats/Metrics Components
const StatCard = ({ 
  title, 
  value, 
  change, 
  changeType = 'neutral', // positive, negative, neutral
  icon,
  color = 'primary'
}) => {
  const changeColors = {
    positive: designTokens.colors.semantic.success,
    negative: designTokens.colors.semantic.error,
    neutral: designTokens.colors.neutral[500]
  };

  const colors = {
    primary: designTokens.colors.primary[500],
    success: designTokens.colors.semantic.success,
    warning: designTokens.colors.semantic.warning,
    error: designTokens.colors.semantic.error,
    info: designTokens.colors.semantic.info
  };

  return (
    <Card>
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between' }}>
        <div style={{ flex: 1 }}>
          <div style={{
            fontSize: designTokens.typography.fontSize.sm,
            color: designTokens.colors.neutral[600],
            marginBottom: '8px',
            fontWeight: designTokens.typography.fontWeight.medium
          }}>
            {title}
          </div>
          
          <div style={{
            fontSize: '32px',
            fontWeight: designTokens.typography.fontWeight.bold,
            color: colors[color],
            marginBottom: '8px',
            lineHeight: 1
          }}>
            {value}
          </div>
          
          {change && (
            <div style={{
              fontSize: designTokens.typography.fontSize.sm,
              color: changeColors[changeType],
              display: 'flex',
              alignItems: 'center',
              gap: '4px'
            }}>
              <span>{changeType === 'positive' ? '↑' : changeType === 'negative' ? '↓' : '→'}</span>
              <span>{change}</span>
            </div>
          )}
        </div>
        
        {icon && (
          <div style={{
            fontSize: '24px',
            color: colors[color],
            opacity: 0.7
          }}>
            {icon}
          </div>
        )}
      </div>
    </Card>
  );
};

const MetricsList = ({ metrics = [] }) => {
  return (
    <Card>
      <div style={{ display: 'flex', flexDirection: 'column' }}>
        {metrics.map((metric, index) => (
          <div
            key={index}
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              padding: '12px 0',
              borderBottom: index < metrics.length - 1 ? `1px solid ${designTokens.colors.neutral[200]}` : 'none'
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              {metric.icon && (
                <div style={{
                  width: '8px',
                  height: '8px',
                  borderRadius: '50%',
                  backgroundColor: metric.color || designTokens.colors.neutral[400]
                }} />
              )}
              <span style={{
                fontSize: designTokens.typography.fontSize.sm,
                color: designTokens.colors.neutral[700]
              }}>
                {metric.label}
              </span>
            </div>
            
            <span style={{
              fontSize: designTokens.typography.fontSize.sm,
              fontWeight: designTokens.typography.fontWeight.semibold,
              color: designTokens.colors.neutral[800]
            }}>
              {metric.value}
            </span>
          </div>
        ))}
      </div>
    </Card>
  );
};

// List Components
const ListItem = ({ 
  title, 
  subtitle, 
  description, 
  avatar, 
  actions, 
  status,
  onClick 
}) => {
  return (
    <div
      onClick={onClick}
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: '16px',
        padding: '16px',
        borderBottom: `1px solid ${designTokens.colors.neutral[200]}`,
        cursor: onClick ? 'pointer' : 'default',
        transition: 'background-color 0.2s ease'
      }}
      onMouseEnter={(e) => {
        if (onClick) {
          e.target.style.backgroundColor = designTokens.colors.neutral[50];
        }
      }}
      onMouseLeave={(e) => {
        if (onClick) {
          e.target.style.backgroundColor = 'transparent';
        }
      }}
    >
      {/* Avatar/Icon */}
      {avatar && (
        <div style={{
          width: '40px',
          height: '40px',
          borderRadius: '50%',
          backgroundColor: designTokens.colors.primary[100],
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontSize: '16px',
          color: designTokens.colors.primary[600],
          flexShrink: 0
        }}>
          {avatar}
        </div>
      )}
      
      {/* Content */}
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{
          fontSize: designTokens.typography.fontSize.base,
          fontWeight: designTokens.typography.fontWeight.medium,
          color: designTokens.colors.neutral[800],
          marginBottom: subtitle || description ? '4px' : 0
        }}>
          {title}
        </div>
        
        {subtitle && (
          <div style={{
            fontSize: designTokens.typography.fontSize.sm,
            color: designTokens.colors.neutral[600],
            marginBottom: description ? '2px' : 0
          }}>
            {subtitle}
          </div>
        )}
        
        {description && (
          <div style={{
            fontSize: designTokens.typography.fontSize.sm,
            color: designTokens.colors.neutral[500],
            lineHeight: '1.4'
          }}>
            {description}
          </div>
        )}
      </div>
      
      {/* Status */}
      {status && (
        <div style={{
          padding: '4px 8px',
          borderRadius: '4px',
          fontSize: designTokens.typography.fontSize.xs,
          fontWeight: designTokens.typography.fontWeight.medium,
          backgroundColor: status.type === 'success' ? designTokens.colors.semantic.success + '20' : 
                          status.type === 'warning' ? designTokens.colors.semantic.warning + '20' :
                          status.type === 'error' ? designTokens.colors.semantic.error + '20' :
                          designTokens.colors.neutral[200],
          color: status.type === 'success' ? designTokens.colors.semantic.success : 
                 status.type === 'warning' ? designTokens.colors.semantic.warning :
                 status.type === 'error' ? designTokens.colors.semantic.error :
                 designTokens.colors.neutral[600]
        }}>
          {status.label}
        </div>
      )}
      
      {/* Actions */}
      {actions && (
        <div style={{ display: 'flex', gap: '8px', flexShrink: 0 }}>
          {actions}
        </div>
      )}
    </div>
  );
};

const List = ({ items = [], showDividers = true }) => {
  return (
    <Card>
      <div style={{ margin: '-24px' }}>
        {items.map((item, index) => (
          <ListItem
            key={index}
            {...item}
            style={{
              borderBottom: showDividers && index < items.length - 1 ? 
                `1px solid ${designTokens.colors.neutral[200]}` : 'none'
            }}
          />
        ))}
      </div>
    </Card>
  );
};

// Demo Page Component
const DesignSystemDemo = () => {
  const [inputValue, setInputValue] = useState('');
  const [singleSelectValue, setSingleSelectValue] = useState(null);
  const [multiSelectValue, setMultiSelectValue] = useState([]);
  const [searchableSelectValue, setSearchableSelectValue] = useState(null);
  const [selectedTableRows, setSelectedTableRows] = useState([]);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  
  // Form component states
  const [singleCheckbox, setSingleCheckbox] = useState(false);
  const [checkboxGroup, setCheckboxGroup] = useState({
    option1: false,
    option2: true,
    option3: false
  });
  const [radioValue, setRadioValue] = useState('option1');
  const [toggleValue, setToggleValue] = useState(false);
  const [dateValue, setDateValue] = useState('');
  const [timeValue, setTimeValue] = useState('');

  // Feedback component states
  const [modalOpen, setModalOpen] = useState(false);
  const [confirmModalOpen, setConfirmModalOpen] = useState(false);
  const [alerts, setAlerts] = useState([]);
  const [toasts, setToasts] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [progressValue, setProgressValue] = useState(65);

  // Functions to handle feedback interactions
  const showAlert = (type, title, message) => {
    const newAlert = {
      id: Date.now(),
      type,
      title,
      message
    };
    setAlerts(prev => [...prev, newAlert]);
  };

  const removeAlert = (id) => {
    setAlerts(prev => prev.filter(alert => alert.id !== id));
  };

  const showToast = (type, title, message) => {
    const newToast = {
      id: Date.now(),
      type,
      title,
      message
    };
    setToasts(prev => [...prev, newToast]);
  };

  const removeToast = (id) => {
    setToasts(prev => prev.filter(toast => toast.id !== id));
  };

  const simulateLoading = () => {
    setIsLoading(true);
    setTimeout(() => {
      setIsLoading(false);
      showToast('success', 'Complete!', 'Operation completed successfully.');
    }, 3000);
  };

  // Sample data for charts and displays
  const salesData = [
    { label: 'Jan', value: 45000 },
    { label: 'Feb', value: 52000 },
    { label: 'Mar', value: 48000 },
    { label: 'Apr', value: 61000 },
    { label: 'May', value: 55000 },
    { label: 'Jun', value: 67000 }
  ];

  const departmentData = [
    { label: 'Engineering', value: 45 },
    { label: 'Sales', value: 32 },
    { label: 'Marketing', value: 28 },
    { label: 'HR', value: 15 },
    { label: 'Finance', value: 12 }
  ];

  const kpiMetrics = [
    { label: 'Active Users', value: '12,458', color: designTokens.colors.semantic.success },
    { label: 'Revenue Growth', value: '+15.3%', color: designTokens.colors.primary[500] },
    { label: 'Customer Satisfaction', value: '4.8/5', color: designTokens.colors.semantic.info },
    { label: 'Support Tickets', value: '23', color: designTokens.colors.semantic.warning },
    { label: 'System Uptime', value: '99.9%', color: designTokens.colors.semantic.success }
  ];

  const recentActivities = [
    {
      title: 'New Order #12345',
      subtitle: 'ABC Corporation',
      description: 'Order value: ¥285,000 • 15 items',
      avatar: '📦',
      status: { type: 'success', label: 'Confirmed' },
      actions: <Button variant="ghost" size="sm">View</Button>
    },
    {
      title: 'Payment Received',
      subtitle: 'Invoice #INV-001',
      description: 'Payment of ¥150,000 received via bank transfer',
      avatar: '💰',
      status: { type: 'success', label: 'Processed' },
      actions: <Button variant="ghost" size="sm">Details</Button>
    },
    {
      title: 'Support Ticket',
      subtitle: 'Technical Issue #T-456',
      description: 'Customer reports login difficulties',
      avatar: '🎫',
      status: { type: 'warning', label: 'In Progress' },
      actions: <Button variant="ghost" size="sm">Assign</Button>
    },
    {
      title: 'Inventory Alert',
      subtitle: 'Product A-001',
      description: 'Stock level below minimum threshold (5 units remaining)',
      avatar: '⚠️',
      status: { type: 'error', label: 'Low Stock' },
      actions: <Button variant="ghost" size="sm">Reorder</Button>
    }
  ];

  // Sample options for selects
  const sampleOptions = [
    { value: 'option1', label: 'Option 1' },
    { value: 'option2', label: 'Option 2' },
    { value: 'option3', label: 'Option 3' },
    { value: 'option4', label: 'Very Long Option Name That Might Overflow' },
  ];

  const departmentOptions = [
    { value: 'sales', label: 'Sales Department' },
    { value: 'marketing', label: 'Marketing Department' },
    { value: 'engineering', label: 'Engineering Department' },
    { value: 'hr', label: 'Human Resources Department' },
    { value: 'finance', label: 'Finance Department' },
    { value: 'operations', label: 'Operations Department' },
  ];

  // Sample data for table
  const tableData = [
    { id: 1, name: 'John Smith', department: 'Engineering', role: 'Senior Developer', status: 'Active', salary: 95000 },
    { id: 2, name: 'Sarah Johnson', department: 'Marketing', role: 'Marketing Manager', status: 'Active', salary: 85000 },
    { id: 3, name: 'Mike Chen', department: 'Sales', role: 'Sales Representative', status: 'Active', salary: 75000 },
    { id: 4, name: 'Emily Davis', department: 'HR', role: 'HR Specialist', status: 'Inactive', salary: 65000 },
    { id: 5, name: 'David Wilson', department: 'Finance', role: 'Financial Analyst', status: 'Active', salary: 70000 },
    { id: 6, name: 'Lisa Brown', department: 'Engineering', role: 'UI/UX Designer', status: 'Active', salary: 80000 },
    { id: 7, name: 'Tom Anderson', department: 'Operations', role: 'Operations Manager', status: 'Active', salary: 90000 },
    { id: 8, name: 'Jennifer White', department: 'Marketing', role: 'Content Specialist', status: 'Active', salary: 60000 },
    { id: 9, name: 'Robert Taylor', department: 'Sales', role: 'Sales Manager', status: 'Active', salary: 95000 },
    { id: 10, name: 'Amanda Clark', department: 'Finance', role: 'Accountant', status: 'Active', salary: 55000 },
    { id: 11, name: 'Chris Martinez', department: 'Engineering', role: 'DevOps Engineer', status: 'Active', salary: 85000 },
    { id: 12, name: 'Rachel Green', department: 'HR', role: 'Recruiter', status: 'Active', salary: 65000 },
  ];

  // Table column configuration
  const tableColumns = [
    { 
      key: 'name', 
      label: 'Employee Name',
      sortable: true 
    },
    { 
      key: 'department', 
      label: 'Department',
      sortable: true 
    },
    { 
      key: 'role', 
      label: 'Role',
      sortable: true 
    },
    { 
      key: 'status', 
      label: 'Status',
      sortable: true,
      render: (value) => (
        <span style={{
          padding: '4px 8px',
          borderRadius: '4px',
          fontSize: '12px',
          fontWeight: designTokens.typography.fontWeight.medium,
          backgroundColor: value === 'Active' ? designTokens.colors.semantic.success + '20' : designTokens.colors.neutral[200],
          color: value === 'Active' ? designTokens.colors.semantic.success : designTokens.colors.neutral[600]
        }}>
          {value}
        </span>
      )
    },
    { 
      key: 'salary', 
      label: 'Salary',
      align: 'right',
      sortable: true,
      render: (value) => `¥${value.toLocaleString()}`
    }
  ];

  // Table actions
  const tableActions = [
    {
      label: 'Edit',
      onClick: (row) => alert(`Edit employee: ${row.name}`)
    },
    {
      label: 'Delete',
      onClick: (row) => alert(`Delete employee: ${row.name}`)
    }
  ];

  // Sample menu items for sidebar
  const menuItems = [
    {
      key: 'dashboard',
      label: 'Dashboard',
      icon: '📊',
      onClick: (item) => console.log('Navigate to:', item.key)
    },
    {
      key: 'sales',
      label: 'Sales',
      icon: '💰',
      children: [
        { key: 'orders', label: 'Orders', icon: '📋' },
        { key: 'customers', label: 'Customers', icon: '👥' },
        { key: 'invoices', label: 'Invoices', icon: '🧾' }
      ]
    },
    {
      key: 'inventory',
      label: 'Inventory',
      icon: '📦',
      children: [
        { key: 'products', label: 'Products', icon: '🏷️' },
        { key: 'warehouse', label: 'Warehouse', icon: '🏢' },
        { key: 'suppliers', label: 'Suppliers', icon: '🚚' }
      ]
    },
    {
      key: 'hr',
      label: 'Human Resources',
      icon: '👤',
      children: [
        { key: 'employees', label: 'Employees', icon: '👥' },
        { key: 'payroll', label: 'Payroll', icon: '💵' },
        { key: 'recruitment', label: 'Recruitment', icon: '📝' }
      ]
    },
    {
      key: 'finance',
      label: 'Finance',
      icon: '📈',
      children: [
        { key: 'accounting', label: 'Accounting', icon: '📚' },
        { key: 'reports', label: 'Reports', icon: '📄' },
        { key: 'budgets', label: 'Budgets', icon: '💳' }
      ]
    },
    {
      key: 'settings',
      label: 'Settings',
      icon: '⚙️',
      onClick: (item) => console.log('Navigate to:', item.key)
    }
  ];

  // Sample user and notifications
  const currentUser = {
    name: 'Kazuhiko Oota',
    email: 'k.oota@itdo.jp',
    role: 'Administrator'
  };

  const sampleNotifications = [
    {
      title: 'New Order Received',
      message: 'Order #12345 from ABC Corp has been received.',
      time: '5 minutes ago',
      read: false
    },
    {
      title: 'System Maintenance',
      message: 'Scheduled maintenance will begin at 2:00 AM.',
      time: '1 hour ago',
      read: false
    },
    {
      title: 'Report Generated',
      message: 'Monthly sales report has been generated.',
      time: '3 hours ago',
      read: true
    }
  ];
  
  return (
    <div style={{ 
      fontFamily: designTokens.typography.fontFamily.sans,
      backgroundColor: designTokens.colors.neutral[50],
      minHeight: '100vh',
      padding: '32px'
    }}>
      {/* Design Tokens Display */}
      <div style={{ marginBottom: '48px' }}>
        <h1 style={{ 
          color: designTokens.colors.neutral[800],
          fontSize: designTokens.typography.fontSize['2xl'],
          fontWeight: designTokens.typography.fontWeight.bold,
          marginBottom: '24px'
        }}>
          ITDO ERP2 Design System
        </h1>
        
        {/* Color Palette */}
        <Card header={<h2 style={{ margin: 0, fontSize: '18px' }}>Color Palette</h2>}>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '24px' }}>
            <div>
              <h3 style={{ margin: '0 0 16px 0', color: designTokens.colors.neutral[600] }}>Primary (Orange)</h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                {Object.entries(designTokens.colors.primary).map(([shade, color]) => (
                  <div key={shade} style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '12px'
                  }}>
                    <div style={{
                      width: '32px',
                      height: '32px',
                      backgroundColor: color,
                      borderRadius: '4px',
                      border: `1px solid ${designTokens.colors.neutral[200]}`
                    }} />
                    <span style={{ fontSize: '14px', fontFamily: designTokens.typography.fontFamily.mono }}>
                      {shade}: {color}
                    </span>
                  </div>
                ))}
              </div>
            </div>
            
            <div>
              <h3 style={{ margin: '0 0 16px 0', color: designTokens.colors.neutral[600] }}>Semantic Colors</h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                {Object.entries(designTokens.colors.semantic).map(([name, color]) => (
                  <div key={name} style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '12px'
                  }}>
                    <div style={{
                      width: '32px',
                      height: '32px',
                      backgroundColor: color,
                      borderRadius: '4px'
                    }} />
                    <span style={{ fontSize: '14px', textTransform: 'capitalize' }}>{name}: {color}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </Card>
      </div>

      {/* Button Components */}
      <div style={{ marginBottom: '48px' }}>
        <Card header={<h2 style={{ margin: 0, fontSize: '18px' }}>Button Components</h2>}>
          <div style={{ display: 'grid', gap: '24px' }}>
            {/* Button Variants */}
            <div>
              <h3 style={{ margin: '0 0 16px 0', fontSize: '16px', color: designTokens.colors.neutral[600] }}>Variants</h3>
              <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
                <Button variant="primary">Primary</Button>
                <Button variant="secondary">Secondary</Button>
                <Button variant="outline">Outline</Button>
                <Button variant="ghost">Ghost</Button>
                <Button variant="danger">Danger</Button>
              </div>
            </div>

            {/* Button Sizes */}
            <div>
              <h3 style={{ margin: '0 0 16px 0', fontSize: '16px', color: designTokens.colors.neutral[600] }}>Sizes</h3>
              <div style={{ display: 'flex', gap: '12px', alignItems: 'end' }}>
                <Button size="sm">Small</Button>
                <Button size="md">Medium</Button>
                <Button size="lg">Large</Button>
              </div>
            </div>

            {/* Button States */}
            <div>
              <h3 style={{ margin: '0 0 16px 0', fontSize: '16px', color: designTokens.colors.neutral[600] }}>States</h3>
              <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
                <Button>Default</Button>
                <Button disabled>Disabled</Button>
                <Button loading>Loading</Button>
              </div>
            </div>
          </div>
        </Card>
      </div>

      {/* Input Components */}
      <div style={{ marginBottom: '48px' }}>
        <Card header={<h2 style={{ margin: 0, fontSize: '18px' }}>Input Components</h2>}>
          <div style={{ display: 'grid', gap: '24px', maxWidth: '400px' }}>
            <div>
              <label style={{ 
                display: 'block', 
                marginBottom: '8px', 
                fontSize: '14px',
                fontWeight: designTokens.typography.fontWeight.medium,
                color: designTokens.colors.neutral[700]
              }}>
                Default Input
              </label>
              <Input 
                placeholder="Enter text here..."
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
              />
            </div>
            
            <div>
              <label style={{ 
                display: 'block', 
                marginBottom: '8px', 
                fontSize: '14px',
                fontWeight: designTokens.typography.fontWeight.medium,
                color: designTokens.colors.neutral[700]
              }}>
                Input with Icon
              </label>
              <Input 
                placeholder="Search..."
                icon={<span>🔍</span>}
              />
            </div>
            
            <div>
              <label style={{ 
                display: 'block', 
                marginBottom: '8px', 
                fontSize: '14px',
                fontWeight: designTokens.typography.fontWeight.medium,
                color: designTokens.colors.neutral[700]
              }}>
                Error State
              </label>
              <Input 
                placeholder="Invalid input"
                error={true}
              />
            </div>
            
            <div>
              <label style={{ 
                display: 'block', 
                marginBottom: '8px', 
                fontSize: '14px',
                fontWeight: designTokens.typography.fontWeight.medium,
                color: designTokens.colors.neutral[400]
              }}>
                Disabled Input
              </label>
              <Input 
                placeholder="Disabled field"
                disabled={true}
                value="Cannot edit this"
              />
            </div>
          </div>
        </Card>
      </div>

      {/* Select/Dropdown Components */}
      <div style={{ marginBottom: '48px' }}>
        <Card header={<h2 style={{ margin: 0, fontSize: '18px' }}>Select/Dropdown Components</h2>}>
          <div style={{ display: 'grid', gap: '24px', maxWidth: '400px' }}>
            <div>
              <label style={{ 
                display: 'block', 
                marginBottom: '8px', 
                fontSize: '14px',
                fontWeight: designTokens.typography.fontWeight.medium,
                color: designTokens.colors.neutral[700]
              }}>
                Single Select
              </label>
              <Select 
                options={sampleOptions}
                value={singleSelectValue}
                onChange={setSingleSelectValue}
                placeholder="Choose an option..."
              />
            </div>
            
            <div>
              <label style={{ 
                display: 'block', 
                marginBottom: '8px', 
                fontSize: '14px',
                fontWeight: designTokens.typography.fontWeight.medium,
                color: designTokens.colors.neutral[700]
              }}>
                Multi Select
              </label>
              <Select 
                options={sampleOptions}
                value={multiSelectValue}
                onChange={setMultiSelectValue}
                placeholder="Choose multiple options..."
                multiple={true}
              />
            </div>
            
            <div>
              <label style={{ 
                display: 'block', 
                marginBottom: '8px', 
                fontSize: '14px',
                fontWeight: designTokens.typography.fontWeight.medium,
                color: designTokens.colors.neutral[700]
              }}>
                Searchable Select
              </label>
              <Select 
                options={departmentOptions}
                value={searchableSelectValue}
                onChange={setSearchableSelectValue}
                placeholder="Search departments..."
                searchable={true}
              />
            </div>
            
            <div>
              <label style={{ 
                display: 'block', 
                marginBottom: '8px', 
                fontSize: '14px',
                fontWeight: designTokens.typography.fontWeight.medium,
                color: designTokens.colors.neutral[400]
              }}>
                Disabled Select
              </label>
              <Select 
                options={sampleOptions}
                placeholder="Cannot select"
                disabled={true}
              />
            </div>
          </div>
        </Card>
      </div>

              {/* Form Components */}
        <div style={{ marginBottom: '48px' }}>
          <Card header={<h2 style={{ margin: 0, fontSize: '18px' }}>Form Components</h2>}>
            <div style={{ display: 'grid', gap: '32px' }}>
              
              {/* Checkbox Components */}
              <div>
                <h3 style={{ margin: '0 0 16px 0', fontSize: '16px', color: designTokens.colors.neutral[600] }}>
                  Checkbox Components
                </h3>
                
                <div style={{ display: 'grid', gap: '20px', maxWidth: '400px' }}>
                  {/* Single Checkbox */}
                  <div>
                    <h4 style={{ margin: '0 0 8px 0', fontSize: '14px', color: designTokens.colors.neutral[700] }}>
                      Single Checkbox
                    </h4>
                    <Checkbox 
                      checked={singleCheckbox}
                      onChange={(e) => setSingleCheckbox(e.target.checked)}
                      label="I agree to the terms and conditions"
                    />
                  </div>

                  {/* Checkbox Group */}
                  <div>
                    <h4 style={{ margin: '0 0 8px 0', fontSize: '14px', color: designTokens.colors.neutral[700] }}>
                      Checkbox Group
                    </h4>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                      <Checkbox 
                        checked={checkboxGroup.option1}
                        onChange={(e) => setCheckboxGroup(prev => ({ ...prev, option1: e.target.checked }))}
                        label="Email notifications"
                      />
                      <Checkbox 
                        checked={checkboxGroup.option2}
                        onChange={(e) => setCheckboxGroup(prev => ({ ...prev, option2: e.target.checked }))}
                        label="SMS notifications"
                      />
                      <Checkbox 
                        checked={checkboxGroup.option3}
                        onChange={(e) => setCheckboxGroup(prev => ({ ...prev, option3: e.target.checked }))}
                        label="Push notifications"
                      />
                    </div>
                  </div>

                  {/* Special States */}
                  <div>
                    <h4 style={{ margin: '0 0 8px 0', fontSize: '14px', color: designTokens.colors.neutral[700] }}>
                      Special States
                    </h4>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                      <Checkbox 
                        checked={false}
                        indeterminate={true}
                        onChange={() => {}}
                        label="Indeterminate state (partial selection)"
                      />
                      <Checkbox 
                        checked={false}
                        disabled={true}
                        onChange={() => {}}
                        label="Disabled checkbox"
                      />
                      <Checkbox 
                        checked={false}
                        error={true}
                        onChange={() => {}}
                        label="Error state checkbox"
                      />
                    </div>
                  </div>
                </div>
              </div>

              {/* Radio Button Components */}
              <div>
                <h3 style={{ margin: '0 0 16px 0', fontSize: '16px', color: designTokens.colors.neutral[600] }}>
                  Radio Button Components
                </h3>
                
                <div style={{ display: 'grid', gap: '20px', maxWidth: '400px' }}>
                  <div>
                    <h4 style={{ margin: '0 0 8px 0', fontSize: '14px', color: designTokens.colors.neutral[700] }}>
                      Payment Method
                    </h4>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                      <Radio 
                        checked={radioValue === 'credit'}
                        onChange={(e) => setRadioValue('credit')}
                        value="credit"
                        name="payment"
                        label="Credit Card"
                      />
                      <Radio 
                        checked={radioValue === 'bank'}
                        onChange={(e) => setRadioValue('bank')}
                        value="bank"
                        name="payment"
                        label="Bank Transfer"
                      />
                      <Radio 
                        checked={radioValue === 'cash'}
                        onChange={(e) => setRadioValue('cash')}
                        value="cash"
                        name="payment"
                        label="Cash on Delivery"
                      />
                    </div>
                  </div>

                  <div>
                    <h4 style={{ margin: '0 0 8px 0', fontSize: '14px', color: designTokens.colors.neutral[700] }}>
                      Special States
                    </h4>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                      <Radio 
                        checked={false}
                        disabled={true}
                        onChange={() => {}}
                        label="Disabled radio button"
                      />
                      <Radio 
                        checked={false}
                        error={true}
                        onChange={() => {}}
                        label="Error state radio"
                      />
                    </div>
                  </div>
                </div>
              </div>

              {/* Toggle Switch Components */}
              <div>
                <h3 style={{ margin: '0 0 16px 0', fontSize: '16px', color: designTokens.colors.neutral[600] }}>
                  Toggle Switch Components
                </h3>
                
                <div style={{ display: 'grid', gap: '20px', maxWidth: '400px' }}>
                  <div>
                    <h4 style={{ margin: '0 0 8px 0', fontSize: '14px', color: designTokens.colors.neutral[700] }}>
                      Settings
                    </h4>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                      <Toggle 
                        checked={toggleValue}
                        onChange={(e) => setToggleValue(e.target.checked)}
                        label="Enable notifications"
                        size="md"
                      />
                    </div>
                  </div>

                  <div>
                    <h4 style={{ margin: '0 0 8px 0', fontSize: '14px', color: designTokens.colors.neutral[700] }}>
                      Different Sizes
                    </h4>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                      <Toggle 
                        checked={true}
                        onChange={() => {}}
                        label="Small toggle"
                        size="sm"
                      />
                      <Toggle 
                        checked={true}
                        onChange={() => {}}
                        label="Medium toggle"
                        size="md"
                      />
                      <Toggle 
                        checked={true}
                        onChange={() => {}}
                        label="Large toggle"
                        size="lg"
                      />
                      <Toggle 
                        checked={false}
                        disabled={true}
                        onChange={() => {}}
                        label="Disabled toggle"
                        size="md"
                      />
                    </div>
                  </div>
                </div>
              </div>

              {/* Date/Time Picker Components */}
              <div>
                <h3 style={{ margin: '0 0 16px 0', fontSize: '16px', color: designTokens.colors.neutral[600] }}>
                  Date/Time Picker Components
                </h3>
                
                <div style={{ display: 'grid', gap: '20px', maxWidth: '400px' }}>
                  <div>
                    <h4 style={{ margin: '0 0 8px 0', fontSize: '14px', color: designTokens.colors.neutral[700] }}>
                      Date Selection
                    </h4>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                      <div>
                        <label style={{ 
                          display: 'block', 
                          marginBottom: '8px', 
                          fontSize: '14px',
                          fontWeight: designTokens.typography.fontWeight.medium,
                          color: designTokens.colors.neutral[700]
                        }}>
                          Start Date
                        </label>
                        <DatePicker 
                          value={dateValue}
                          onChange={setDateValue}
                          placeholder="Select start date..."
                        />
                      </div>
                      
                      <div>
                        <label style={{ 
                          display: 'block', 
                          marginBottom: '8px', 
                          fontSize: '14px',
                          fontWeight: designTokens.typography.fontWeight.medium,
                          color: designTokens.colors.neutral[700]
                        }}>
                          Meeting Time
                        </label>
                        <TimePicker 
                          value={timeValue}
                          onChange={setTimeValue}
                          placeholder="Select meeting time..."
                        />
                      </div>
                      
                      <div>
                        <label style={{ 
                          display: 'block', 
                          marginBottom: '8px', 
                          fontSize: '14px',
                          fontWeight: designTokens.typography.fontWeight.medium,
                          color: designTokens.colors.neutral[400]
                        }}>
                          Disabled Date Picker
                        </label>
                        <DatePicker 
                          value=""
                          onChange={() => {}}
                          placeholder="Cannot select date"
                          disabled={true}
                        />
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </Card>
        </div>
      <div style={{ marginBottom: '48px' }}>
        <Card header={<h2 style={{ margin: 0, fontSize: '18px' }}>Table Component</h2>}>
          <div style={{ marginBottom: '16px' }}>
            <h3 style={{ margin: '0 0 16px 0', fontSize: '16px', color: designTokens.colors.neutral[600] }}>
              Employee Management Table
            </h3>
            <p style={{ 
              margin: '0 0 16px 0', 
              fontSize: '14px', 
              color: designTokens.colors.neutral[600],
              lineHeight: '1.5'
            }}>
              Features: Sortable columns, row selection, pagination, and action buttons. 
              Selected rows: {selectedTableRows.length}
            </p>
          </div>
          
          <Table
            data={tableData}
            columns={tableColumns}
            selectable={true}
            sortable={true}
            pageSize={5}
            actions={tableActions}
            onRowSelect={setSelectedTableRows}
          />
        </Card>
      </div>
      <div style={{ marginBottom: '48px' }}>
        <Card header={<h2 style={{ margin: 0, fontSize: '18px' }}>Layout Examples</h2>}>
          <div style={{ display: 'grid', gap: '24px' }}>
            
            {/* Stats Cards */}
            <div>
              <h3 style={{ margin: '0 0 16px 0', fontSize: '16px', color: designTokens.colors.neutral[600] }}>Dashboard Stats</h3>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px' }}>
                <Card>
                  <div style={{ textAlign: 'center' }}>
                    <div style={{ 
                      fontSize: '32px', 
                      fontWeight: designTokens.typography.fontWeight.bold,
                      color: designTokens.colors.primary[500],
                      marginBottom: '8px'
                    }}>
                      1,234
                    </div>
                    <div style={{ color: designTokens.colors.neutral[600] }}>Total Orders</div>
                  </div>
                </Card>
                
                <Card>
                  <div style={{ textAlign: 'center' }}>
                    <div style={{ 
                      fontSize: '32px', 
                      fontWeight: designTokens.typography.fontWeight.bold,
                      color: designTokens.colors.semantic.success,
                      marginBottom: '8px'
                    }}>
                      ¥987,654
                    </div>
                    <div style={{ color: designTokens.colors.neutral[600] }}>Monthly Revenue</div>
                  </div>
                </Card>
                
                <Card>
                  <div style={{ textAlign: 'center' }}>
                    <div style={{ 
                      fontSize: '32px', 
                      fontWeight: designTokens.typography.fontWeight.bold,
                      color: designTokens.colors.semantic.info,
                      marginBottom: '8px'
                    }}>
                      456
                    </div>
                    <div style={{ color: designTokens.colors.neutral[600] }}>Active Users</div>
                  </div>
                </Card>
              </div>
            </div>

            {/* Form Layout */}
            <div>
              <h3 style={{ margin: '0 0 16px 0', fontSize: '16px', color: designTokens.colors.neutral[600] }}>Form Layout</h3>
              <Card>
                <div style={{ display: 'grid', gap: '16px', maxWidth: '500px' }}>
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
                    <div>
                      <label style={{ 
                        display: 'block', 
                        marginBottom: '8px', 
                        fontSize: '14px',
                        fontWeight: designTokens.typography.fontWeight.medium,
                        color: designTokens.colors.neutral[700]
                      }}>
                        First Name
                      </label>
                      <Input placeholder="John" />
                    </div>
                    <div>
                      <label style={{ 
                        display: 'block', 
                        marginBottom: '8px', 
                        fontSize: '14px',
                        fontWeight: designTokens.typography.fontWeight.medium,
                        color: designTokens.colors.neutral[700]
                      }}>
                        Last Name
                      </label>
                      <Input placeholder="Doe" />
                    </div>
                  </div>
                  <div>
                    <label style={{ 
                      display: 'block', 
                      marginBottom: '8px', 
                      fontSize: '14px',
                      fontWeight: designTokens.typography.fontWeight.medium,
                      color: designTokens.colors.neutral[700]
                    }}>
                      Email
                    </label>
                    <Input type="email" placeholder="john.doe@example.com" />
                  </div>
                  <div style={{ display: 'flex', gap: '12px', justifyContent: 'flex-end' }}>
                    <Button variant="ghost">Cancel</Button>
                    <Button variant="primary">Save Changes</Button>
                  </div>
                </div>
              </Card>
            </div>
          </div>
        </Card>
      </div>

      {/* CSS Custom Properties */}
      <div>
        <Card header={<h2 style={{ margin: 0, fontSize: '18px' }}>Design Tokens (JSON Format)</h2>}>
          <pre style={{
            backgroundColor: designTokens.colors.neutral[900],
            color: '#fff',
            padding: '16px',
            borderRadius: '6px',
            overflow: 'auto',
            fontSize: '12px',
            fontFamily: designTokens.typography.fontFamily.mono
          }}>
            {JSON.stringify(designTokens, null, 2)}
          </pre>
        </Card>
      </div>
      
      <style jsx>{`
        @keyframes spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
};

export default DesignSystemDemo;