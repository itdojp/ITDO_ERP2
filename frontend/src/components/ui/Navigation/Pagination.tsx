import React from 'react'
import { ChevronLeft, ChevronRight, MoreHorizontal } from 'lucide-react'
import { cn } from '../../../lib/utils'

export interface PaginationProps {
  currentPage: number
  totalPages: number
  onPageChange: (page: number) => void
  showFirstLast?: boolean
  showPrevNext?: boolean
  siblingCount?: number
  className?: string
  size?: 'sm' | 'md' | 'lg'
  variant?: 'default' | 'outlined' | 'minimal'
}

const Pagination = React.memo<PaginationProps>(({
  currentPage,
  totalPages,
  onPageChange,
  showFirstLast = true,
  showPrevNext = true,
  siblingCount = 1,
  className,
  size = 'md',
  variant = 'default',
}) => {
  const generatePageNumbers = React.useMemo(() => {
    const totalNumbers = siblingCount * 2 + 3 // siblings + current + first + last
    const totalBlocks = totalNumbers + 2 // + 2 for ellipsis

    if (totalPages <= totalBlocks) {
      return Array.from({ length: totalPages }, (_, i) => i + 1)
    }

    const leftSiblingIndex = Math.max(currentPage - siblingCount, 1)
    const rightSiblingIndex = Math.min(currentPage + siblingCount, totalPages)

    const shouldShowLeftEllipsis = leftSiblingIndex > 2
    const shouldShowRightEllipsis = rightSiblingIndex < totalPages - 2

    const firstPageIndex = 1
    const lastPageIndex = totalPages

    if (!shouldShowLeftEllipsis && shouldShowRightEllipsis) {
      const leftItemCount = 3 + 2 * siblingCount
      const leftRange = Array.from({ length: leftItemCount }, (_, i) => i + 1)
      return [...leftRange, '...', totalPages]
    }

    if (shouldShowLeftEllipsis && !shouldShowRightEllipsis) {
      const rightItemCount = 3 + 2 * siblingCount
      const rightRange = Array.from(
        { length: rightItemCount },
        (_, i) => totalPages - rightItemCount + i + 1
      )
      return [firstPageIndex, '...', ...rightRange]
    }

    if (shouldShowLeftEllipsis && shouldShowRightEllipsis) {
      const middleRange = Array.from(
        { length: rightSiblingIndex - leftSiblingIndex + 1 },
        (_, i) => leftSiblingIndex + i
      )
      return [firstPageIndex, '...', ...middleRange, '...', lastPageIndex]
    }

    return []
  }, [currentPage, totalPages, siblingCount])

  const sizes = {
    sm: {
      button: 'h-8 px-3 text-sm',
      nav: 'gap-1',
    },
    md: {
      button: 'h-10 px-4 text-sm',
      nav: 'gap-1',
    },
    lg: {
      button: 'h-12 px-6 text-base',
      nav: 'gap-2',
    },
  }

  const variants = {
    default: {
      button: 'bg-white border border-gray-300 text-gray-700 hover:bg-gray-50',
      active: 'bg-blue-600 border-blue-600 text-white hover:bg-blue-700',
      disabled: 'bg-gray-100 border-gray-200 text-gray-400 cursor-not-allowed',
    },
    outlined: {
      button: 'bg-transparent border border-gray-300 text-gray-700 hover:bg-gray-50',
      active: 'bg-blue-50 border-blue-600 text-blue-600 hover:bg-blue-100',
      disabled: 'bg-transparent border-gray-200 text-gray-400 cursor-not-allowed',
    },
    minimal: {
      button: 'bg-transparent border-0 text-gray-700 hover:bg-gray-100',
      active: 'bg-blue-100 border-0 text-blue-600 hover:bg-blue-200',
      disabled: 'bg-transparent border-0 text-gray-400 cursor-not-allowed',
    },
  }

  const sizeClasses = sizes[size]
  const variantClasses = variants[variant]

  const baseButtonClasses = cn(
    'inline-flex items-center justify-center font-medium rounded-md transition-colors',
    'focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2',
    sizeClasses.button
  )

  const getButtonClasses = (isActive: boolean, isDisabled: boolean) => {
    if (isDisabled) {
      return cn(baseButtonClasses, variantClasses.disabled)
    }
    if (isActive) {
      return cn(baseButtonClasses, variantClasses.active)
    }
    return cn(baseButtonClasses, variantClasses.button)
  }

  const handlePageChange = (page: number | string) => {
    if (typeof page === 'number' && page !== currentPage) {
      onPageChange(page)
    }
  }

  const canGoPrevious = currentPage > 1
  const canGoNext = currentPage < totalPages

  return (
    <nav
      className={cn('flex items-center', sizeClasses.nav, className)}
      aria-label="Pagination"
    >
      {/* First Page */}
      {showFirstLast && totalPages > 5 && (
        <button
          type="button"
          className={getButtonClasses(false, !canGoPrevious)}
          onClick={() => handlePageChange(1)}
          disabled={!canGoPrevious}
          aria-label="Go to first page"
        >
          First
        </button>
      )}

      {/* Previous Page */}
      {showPrevNext && (
        <button
          type="button"
          className={getButtonClasses(false, !canGoPrevious)}
          onClick={() => handlePageChange(currentPage - 1)}
          disabled={!canGoPrevious}
          aria-label="Go to previous page"
        >
          <ChevronLeft className="h-4 w-4" />
          <span className="sr-only">Previous</span>
        </button>
      )}

      {/* Page Numbers */}
      {generatePageNumbers.map((pageNumber, index) => {
        if (pageNumber === '...') {
          return (
            <span
              key={`ellipsis-${index}`}
              className={cn(
                baseButtonClasses,
                'cursor-default',
                variantClasses.button
              )}
              aria-hidden="true"
            >
              <MoreHorizontal className="h-4 w-4" />
            </span>
          )
        }

        const isActive = pageNumber === currentPage
        return (
          <button
            key={pageNumber}
            type="button"
            className={getButtonClasses(isActive, false)}
            onClick={() => handlePageChange(pageNumber)}
            aria-label={`Go to page ${pageNumber}`}
            aria-current={isActive ? 'page' : undefined}
          >
            {pageNumber}
          </button>
        )
      })}

      {/* Next Page */}
      {showPrevNext && (
        <button
          type="button"
          className={getButtonClasses(false, !canGoNext)}
          onClick={() => handlePageChange(currentPage + 1)}
          disabled={!canGoNext}
          aria-label="Go to next page"
        >
          <ChevronRight className="h-4 w-4" />
          <span className="sr-only">Next</span>
        </button>
      )}

      {/* Last Page */}
      {showFirstLast && totalPages > 5 && (
        <button
          type="button"
          className={getButtonClasses(false, !canGoNext)}
          onClick={() => handlePageChange(totalPages)}
          disabled={!canGoNext}
          aria-label="Go to last page"
        >
          Last
        </button>
      )}
    </nav>
  )
})

Pagination.displayName = 'Pagination'

export default Pagination