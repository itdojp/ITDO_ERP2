import React, { useMemo } from 'react';

interface PaginationProps {
  currentPage: number;
  totalPages: number;
  onPageChange: (page: number) => void;
  pageSize?: number;
  totalItems?: number;
  onPageSizeChange?: (pageSize: number) => void;
  showPageSizeSelect?: boolean;
  pageSizeOptions?: number[];
  variant?: 'default' | 'simple' | 'compact';
  size?: 'sm' | 'md' | 'lg';
  showFirstLast?: boolean;
  showPrevNext?: boolean;
  showPageNumbers?: boolean;
  showInfo?: boolean;
  maxVisiblePages?: number;
  className?: string;
  buttonClassName?: string;
  activeButtonClassName?: string;
  infoClassName?: string;
  disabled?: boolean;
  labels?: {
    first?: string;
    previous?: string;
    next?: string;
    last?: string;
    page?: string;
    of?: string;
    items?: string;
    showing?: string;
    to?: string;
    resultsPerPage?: string;
  };
}

export const Pagination: React.FC<PaginationProps> = ({
  currentPage,
  totalPages,
  onPageChange,
  pageSize = 10,
  totalItems,
  onPageSizeChange,
  showPageSizeSelect = false,
  pageSizeOptions = [10, 25, 50, 100],
  variant = 'default',
  size = 'md',
  showFirstLast = true,
  showPrevNext = true,
  showPageNumbers = true,
  showInfo = false,
  maxVisiblePages = 7,
  className = '',
  buttonClassName = '',
  activeButtonClassName = '',
  infoClassName = '',
  disabled = false,
  labels = {}
}) => {
  const defaultLabels = {
    first: 'First',
    previous: 'Previous',
    next: 'Next',
    last: 'Last',
    page: 'Page',
    of: 'of',
    items: 'items',
    showing: 'Showing',
    to: 'to',
    resultsPerPage: 'Results per page',
    ...labels
  };

  const getSizeClasses = () => {
    const sizeMap = {
      sm: 'px-2 py-1 text-xs',
      md: 'px-3 py-2 text-sm',
      lg: 'px-4 py-3 text-base'
    };
    return sizeMap[size];
  };

  const getVariantClasses = (isActive: boolean, isDisabled: boolean) => {
    const baseClasses = `
      inline-flex items-center justify-center border transition-colors duration-200
      ${getSizeClasses()}
      ${isDisabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
      ${buttonClassName}
    `;

    if (isActive) {
      return `${baseClasses} ${
        activeButtonClassName || 'bg-blue-600 border-blue-600 text-white hover:bg-blue-700'
      }`;
    }

    switch (variant) {
      case 'simple':
        return `${baseClasses} bg-white border-gray-300 text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500`;
      case 'compact':
        return `${baseClasses} bg-transparent border-transparent text-gray-600 hover:text-gray-900 hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500`;
      default:
        return `${baseClasses} bg-white border-gray-300 text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500`;
    }
  };

  const getVisiblePages = useMemo(() => {
    if (totalPages <= maxVisiblePages) {
      return Array.from({ length: totalPages }, (_, i) => i + 1);
    }

    const halfVisible = Math.floor(maxVisiblePages / 2);
    let startPage = Math.max(currentPage - halfVisible, 1);
    let endPage = Math.min(startPage + maxVisiblePages - 1, totalPages);

    if (endPage - startPage + 1 < maxVisiblePages) {
      startPage = Math.max(endPage - maxVisiblePages + 1, 1);
    }

    const pages: (number | string)[] = [];

    if (startPage > 1) {
      pages.push(1);
      if (startPage > 2) {
        pages.push('...');
      }
    }

    for (let i = startPage; i <= endPage; i++) {
      pages.push(i);
    }

    if (endPage < totalPages) {
      if (endPage < totalPages - 1) {
        pages.push('...');
      }
      pages.push(totalPages);
    }

    return pages;
  }, [currentPage, totalPages, maxVisiblePages]);

  const handlePageChange = (page: number) => {
    if (disabled || page === currentPage || page < 1 || page > totalPages) {
      return;
    }
    onPageChange(page);
  };

  const handleKeyDown = (event: React.KeyboardEvent, page: number) => {
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault();
      handlePageChange(page);
    }
  };

  const renderPageButton = (page: number | string, key: string) => {
    if (page === '...') {
      return (
        <span
          key={key}
          className={`${getSizeClasses()} px-3 text-gray-500`}
          aria-hidden="true"
        >
          {page}
        </span>
      );
    }

    const pageNum = page as number;
    const isActive = pageNum === currentPage;
    const isDisabled = disabled;

    return (
      <button
        key={key}
        className={getVariantClasses(isActive, isDisabled)}
        onClick={() => handlePageChange(pageNum)}
        onKeyDown={(e) => handleKeyDown(e, pageNum)}
        disabled={isDisabled}
        aria-current={isActive ? 'page' : undefined}
        aria-label={`${defaultLabels.page} ${pageNum}`}
        type="button"
      >
        {pageNum}
      </button>
    );
  };

  const renderNavigationButton = (
    onClick: () => void,
    disabled: boolean,
    label: string,
    icon?: React.ReactNode,
    ariaLabel?: string
  ) => {
    return (
      <button
        className={getVariantClasses(false, disabled)}
        onClick={onClick}
        disabled={disabled}
        aria-label={ariaLabel || label}
        type="button"
      >
        <span className="flex items-center gap-1">
          {icon}
          {variant !== 'compact' && <span>{label}</span>}
        </span>
      </button>
    );
  };

  const renderInfo = () => {
    if (!showInfo || !totalItems) return null;

    const startItem = (currentPage - 1) * pageSize + 1;
    const endItem = Math.min(currentPage * pageSize, totalItems);

    return (
      <div className={`text-sm text-gray-700 ${infoClassName}`}>
        {defaultLabels.showing} {startItem} {defaultLabels.to} {endItem} {defaultLabels.of} {totalItems} {defaultLabels.items}
      </div>
    );
  };

  const renderPageSizeSelect = () => {
    if (!showPageSizeSelect || !onPageSizeChange) return null;

    return (
      <div className="flex items-center gap-2">
        <label htmlFor="page-size-select" className="text-sm text-gray-700">
          {defaultLabels.resultsPerPage}:
        </label>
        <select
          id="page-size-select"
          value={pageSize}
          onChange={(e) => onPageSizeChange(Number(e.target.value))}
          className="border border-gray-300 rounded px-2 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          disabled={disabled}
        >
          {pageSizeOptions.map((option) => (
            <option key={option} value={option}>
              {option}
            </option>
          ))}
        </select>
      </div>
    );
  };

  if (totalPages <= 1 && !showInfo && !showPageSizeSelect) {
    return null;
  }

  const firstIcon = (
    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 19l-7-7 7-7m8 14l-7-7 7-7" />
    </svg>
  );

  const previousIcon = (
    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
    </svg>
  );

  const nextIcon = (
    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
    </svg>
  );

  const lastIcon = (
    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 5l7 7-7 7M5 5l7 7-7 7" />
    </svg>
  );

  return (
    <div className={`flex flex-col sm:flex-row items-center justify-between gap-4 ${className}`}>
      <div className="flex items-center gap-4">
        {renderInfo()}
        {renderPageSizeSelect()}
      </div>
      
      <nav className="flex items-center gap-1" aria-label="Pagination navigation">
        {totalPages > 1 && (
          <>
            {showFirstLast && (
              renderNavigationButton(
                () => handlePageChange(1),
                disabled || currentPage === 1,
                defaultLabels.first,
                variant === 'compact' ? firstIcon : undefined,
                `Go to first page`
              )
            )}

            {showPrevNext && (
              renderNavigationButton(
                () => handlePageChange(currentPage - 1),
                disabled || currentPage === 1,
                defaultLabels.previous,
                variant === 'compact' ? previousIcon : undefined,
                `Go to previous page`
              )
            )}

            {showPageNumbers && getVisiblePages.map((page, index) => 
              renderPageButton(page, `page-${index}`)
            )}

            {showPrevNext && (
              renderNavigationButton(
                () => handlePageChange(currentPage + 1),
                disabled || currentPage === totalPages,
                defaultLabels.next,
                variant === 'compact' ? nextIcon : undefined,
                `Go to next page`
              )
            )}

            {showFirstLast && (
              renderNavigationButton(
                () => handlePageChange(totalPages),
                disabled || currentPage === totalPages,
                defaultLabels.last,
                variant === 'compact' ? lastIcon : undefined,
                `Go to last page`
              )
            )}
          </>
        )}
      </nav>
    </div>
  );
};

export default Pagination;