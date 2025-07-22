import React, { useState, useMemo } from 'react';
import { Button } from '../ui/Button';
import { Select } from '../ui/Select';
import { PaginationConfig } from './types';

interface TablePaginationProps extends PaginationConfig {
  onChange?: (page: number, pageSize: number) => void;
  onShowSizeChange?: (current: number, size: number) => void;
  className?: string;
}

export const TablePagination: React.FC<TablePaginationProps> = ({
  current = 1,
  pageSize = 10,
  total = 0,
  showSizeChanger = true,
  showQuickJumper = false,
  showTotal: showTotalProp = true,
  pageSizeOptions = [10, 20, 50, 100],
  onChange,
  onShowSizeChange,
  className = '',
}) => {
  const [jumpPage, setJumpPage] = useState('');

  // ページ数の計算
  const totalPages = Math.ceil(total / pageSize);
  const startIndex = (current - 1) * pageSize + 1;
  const endIndex = Math.min(current * pageSize, total);

  // 表示するページ番号の計算（5個まで表示）
  const pageNumbers = useMemo(() => {
    const pages: (number | string)[] = [];
    const maxVisiblePages = 5;
    
    if (totalPages <= maxVisiblePages) {
      // 総ページ数が少ない場合はすべて表示
      for (let i = 1; i <= totalPages; i++) {
        pages.push(i);
      }
    } else {
      // 多い場合は省略表示
      const halfVisible = Math.floor(maxVisiblePages / 2);
      let start = Math.max(1, current - halfVisible);
      let end = Math.min(totalPages, current + halfVisible);
      
      // 開始位置の調整
      if (end - start + 1 < maxVisiblePages) {
        if (start === 1) {
          end = Math.min(totalPages, start + maxVisiblePages - 1);
        } else {
          start = Math.max(1, end - maxVisiblePages + 1);
        }
      }
      
      // 最初のページと省略記号
      if (start > 1) {
        pages.push(1);
        if (start > 2) {
          pages.push('...');
        }
      }
      
      // 中間のページ
      for (let i = start; i <= end; i++) {
        pages.push(i);
      }
      
      // 最後のページと省略記号
      if (end < totalPages) {
        if (end < totalPages - 1) {
          pages.push('...');
        }
        pages.push(totalPages);
      }
    }
    
    return pages;
  }, [current, totalPages]);

  // ページ変更処理
  const handlePageChange = (page: number) => {
    if (page !== current && page >= 1 && page <= totalPages) {
      onChange?.(page, pageSize);
    }
  };

  // ページサイズ変更処理
  const handlePageSizeChange = (newPageSize: number) => {
    const newCurrent = Math.min(current, Math.ceil(total / newPageSize));
    onShowSizeChange?.(newCurrent, newPageSize);
    onChange?.(newCurrent, newPageSize);
  };

  // クイックジャンプ処理
  const handleQuickJump = () => {
    const page = parseInt(jumpPage, 10);
    if (page && page >= 1 && page <= totalPages) {
      handlePageChange(page);
      setJumpPage('');
    }
  };

  // 総数表示テキスト
  const showTotal = (total: number, range: [number, number]) => {
    return `${range[0]}-${range[1]} / ${total} 件`;
  };

  if (total === 0) {
    return null;
  }

  return (
    <div className={`flex items-center justify-between ${className}`}>
      {/* 左側: 総数表示 */}
      <div className="flex items-center space-x-4 text-sm text-gray-600">
        {showTotalProp && (
          <span>
            {showTotal(total, [startIndex, endIndex])}
          </span>
        )}
        
        {/* ページサイズ変更 */}
        {showSizeChanger && (
          <div className="flex items-center space-x-2">
            <span>表示件数:</span>
            <Select
              value={pageSize}
              onChange={handlePageSizeChange}
              size="sm"
              className="w-20"
            >
              {pageSizeOptions.map(size => (
                <Select.Option key={size} value={size}>
                  {size}
                </Select.Option>
              ))}
            </Select>
            <span>件</span>
          </div>
        )}
      </div>

      {/* 右側: ページネーション */}
      <div className="flex items-center space-x-2">
        {/* クイックジャンプ */}
        {showQuickJumper && (
          <div className="flex items-center space-x-2 text-sm mr-4">
            <span>ページ:</span>
            <input
              type="number"
              min={1}
              max={totalPages}
              value={jumpPage}
              onChange={(e) => setJumpPage(e.target.value)}
              onKeyPress={(e) => {
                if (e.key === 'Enter') {
                  handleQuickJump();
                }
              }}
              className="w-16 px-2 py-1 border border-gray-300 rounded text-center focus:outline-none focus:ring-1 focus:ring-blue-500"
              placeholder={String(current)}
            />
            <Button
              size="sm"
              variant="ghost"
              onClick={handleQuickJump}
              disabled={!jumpPage}
            >
              移動
            </Button>
          </div>
        )}

        {/* 前のページボタン */}
        <Button
          size="sm"
          variant="ghost"
          disabled={current <= 1}
          onClick={() => handlePageChange(current - 1)}
          className="px-2"
        >
          <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
          </svg>
        </Button>

        {/* ページ番号 */}
        <div className="flex items-center space-x-1">
          {pageNumbers.map((page, index) => (
            <React.Fragment key={index}>
              {page === '...' ? (
                <span className="px-3 py-1 text-gray-500">...</span>
              ) : (
                <Button
                  size="sm"
                  variant={page === current ? 'primary' : 'ghost'}
                  onClick={() => handlePageChange(page as number)}
                  className="min-w-[2rem] px-2"
                >
                  {page}
                </Button>
              )}
            </React.Fragment>
          ))}
        </div>

        {/* 次のページボタン */}
        <Button
          size="sm"
          variant="ghost"
          disabled={current >= totalPages}
          onClick={() => handlePageChange(current + 1)}
          className="px-2"
        >
          <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
          </svg>
        </Button>

        {/* 最初・最後のページボタン（ページ数が多い場合） */}
        {totalPages > 10 && (
          <>
            <div className="w-px h-4 bg-gray-300 mx-1" />
            <Button
              size="sm"
              variant="ghost"
              disabled={current <= 1}
              onClick={() => handlePageChange(1)}
              title="最初のページ"
            >
              <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 19l-7-7 7-7M21 19l-7-7 7-7" />
              </svg>
            </Button>
            <Button
              size="sm"
              variant="ghost"
              disabled={current >= totalPages}
              onClick={() => handlePageChange(totalPages)}
              title="最後のページ"
            >
              <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 5l7 7-7 7M3 5l7 7-7 7" />
              </svg>
            </Button>
          </>
        )}
      </div>
    </div>
  );
};