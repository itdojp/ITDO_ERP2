import React, { useState, useRef } from 'react';
import { TreeNodeProps } from './types';
import { LoadingSpinner } from '../ui/LoadingSpinner';

export const TreeNode: React.FC<TreeNodeProps> = ({
  id,
  title,
  children = [],
  icon,
  level = 0,
  expanded = false,
  selected = false,
  checked = false,
  halfChecked = false,
  loading = false,
  disabled = false,
  selectable = true,
  checkable = false,
  disableCheckbox = false,
  dragOver = false,
  dragOverGapTop = false,
  dragOverGapBottom = false,
  isLeaf = false,
  pos,
  eventKey,
  showLine = false,
  showIcon = true,
  draggable = false,
  searchValue,
  filterTreeNode,
  onExpand,
  onSelect,
  onCheck,
  onLoad,
  onRightClick,
  onDragStart,
  onDragEnter,
  onDragOver,
  onDragLeave,
  onDragEnd,
  onDrop,
  titleRender,
  className = '',
  style,
  data,
}) => {
  const [isDragging, setIsDragging] = useState(false);
  const nodeRef = useRef<HTMLDivElement>(null);
  
  const hasChildren = children && children.length > 0;
  const canExpand = hasChildren || !isLeaf;
  const isExpandable = canExpand && !loading;

  // インデントレベル
  const indentSize = 18;
  const indent = level * indentSize;

  // 展開アイコン
  const renderSwitcher = () => {
    if (loading) {
      return <LoadingSpinner size="sm" className="w-4 h-4" />;
    }

    if (!canExpand) {
      return <div className="w-4 h-4" />;
    }

    return (
      <button
        type="button"
        className={`
          w-4 h-4 flex items-center justify-center transition-transform duration-200
          ${expanded ? 'rotate-90' : 'rotate-0'}
          ${disabled ? 'text-gray-300 cursor-not-allowed' : 'text-gray-600 hover:text-gray-800'}
        `}
        onClick={(e) => {
          e.stopPropagation();
          if (onExpand && !disabled) {
            onExpand(!expanded, { id, title, children, data });
          }
        }}
        disabled={disabled}
      >
        <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" className="w-3 h-3">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
        </svg>
      </button>
    );
  };

  // チェックボックス
  const renderCheckbox = () => {
    if (!checkable || disableCheckbox) {
      return null;
    }

    return (
      <input
        type="checkbox"
        checked={checked}
        onChange={(e) => {
          e.stopPropagation();
          if (onCheck && !disabled) {
            onCheck(e.target.checked, { id, title, children, data });
          }
        }}
        disabled={disabled}
        className={`
          w-4 h-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded
          ${halfChecked ? 'opacity-50' : ''}
          ${disabled ? 'cursor-not-allowed' : 'cursor-pointer'}
        `}
        ref={(input) => {
          if (input) {
            input.indeterminate = halfChecked;
          }
        }}
      />
    );
  };

  // アイコン
  const renderIcon = () => {
    if (!showIcon) return null;

    if (icon) {
      return <span className="w-4 h-4 flex items-center justify-center">{icon}</span>;
    }

    // デフォルトアイコン
    if (hasChildren) {
      return (
        <svg className="w-4 h-4 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2H5a2 2 0 00-2-2z" />
        </svg>
      );
    } else {
      return (
        <svg className="w-4 h-4 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
      );
    }
  };

  // タイトルのハイライト
  const renderTitle = () => {
    if (titleRender) {
      return titleRender({ id, title, children, data });
    }

    if (searchValue && title.toLowerCase().includes(searchValue.toLowerCase())) {
      const index = title.toLowerCase().indexOf(searchValue.toLowerCase());
      const beforeStr = title.substring(0, index);
      const searchStr = title.substring(index, index + searchValue.length);
      const afterStr = title.substring(index + searchValue.length);

      return (
        <span>
          {beforeStr}
          <span className="bg-yellow-200 text-yellow-800">{searchStr}</span>
          {afterStr}
        </span>
      );
    }

    return title;
  };

  // ドラッグ&ドロップイベント
  const handleDragStart = (e: React.DragEvent) => {
    if (!draggable || disabled) return;
    
    setIsDragging(true);
    e.dataTransfer.effectAllowed = 'move';
    e.dataTransfer.setData('text/plain', id);
    
    if (onDragStart) {
      onDragStart(e, { id, title, children, data });
    }
  };

  const handleDragEnd = (e: React.DragEvent) => {
    setIsDragging(false);
    
    if (onDragEnd) {
      onDragEnd(e, { id, title, children, data });
    }
  };

  const handleDragEnter = (e: React.DragEvent) => {
    e.preventDefault();
    
    if (onDragEnter) {
      onDragEnter(e, { id, title, children, data });
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
    
    if (onDragOver) {
      onDragOver(e, { id, title, children, data });
    }
  };

  const handleDragLeave = (e: React.DragEvent) => {
    if (onDragLeave) {
      onDragLeave(e, { id, title, children, data });
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    
    if (onDrop) {
      onDrop(e, { id, title, children, data });
    }
  };

  // クリックイベント
  const handleClick = (e: React.MouseEvent) => {
    if (disabled || !selectable) return;
    
    if (onSelect) {
      onSelect(!selected, { id, title, children, data });
    }
  };

  const handleRightClick = (e: React.MouseEvent) => {
    e.preventDefault();
    
    if (onRightClick && !disabled) {
      onRightClick(e, { id, title, children, data });
    }
  };

  // ノードのスタイル
  const nodeClasses = `
    relative flex items-center min-h-[28px] px-2 py-1 cursor-pointer transition-colors group
    ${selected ? 'bg-blue-50 text-blue-700' : 'hover:bg-gray-50'}
    ${disabled ? 'cursor-not-allowed opacity-50' : ''}
    ${isDragging ? 'opacity-50' : ''}
    ${dragOver ? 'bg-blue-100' : ''}
    ${className}
  `;

  return (
    <div
      ref={nodeRef}
      className={nodeClasses}
      style={{ paddingLeft: `${indent + 8}px`, ...style }}
      onClick={handleClick}
      onContextMenu={handleRightClick}
      onDragStart={handleDragStart}
      onDragEnd={handleDragEnd}
      onDragEnter={handleDragEnter}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
      draggable={draggable && !disabled}
      role="treeitem"
      aria-expanded={canExpand ? expanded : undefined}
      aria-selected={selectable ? selected : undefined}
      aria-disabled={disabled}
      tabIndex={disabled ? -1 : 0}
    >
      {/* ドラッグオーバーインジケーター */}
      {dragOverGapTop && (
        <div className="absolute top-0 left-0 right-0 h-0.5 bg-blue-500" />
      )}
      {dragOverGapBottom && (
        <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-blue-500" />
      )}

      {/* 接続線 */}
      {showLine && level > 0 && (
        <div className="absolute left-0 top-0 bottom-0 flex items-center">
          <div
            className="border-l border-gray-300"
            style={{ marginLeft: `${(level - 1) * indentSize + 8}px`, height: '100%' }}
          />
          <div
            className="border-b border-gray-300"
            style={{ width: `${indentSize - 8}px` }}
          />
        </div>
      )}

      {/* コンテンツ */}
      <div className="flex items-center space-x-2 flex-1 min-w-0">
        {/* 展開アイコン */}
        {renderSwitcher()}

        {/* チェックボックス */}
        {renderCheckbox()}

        {/* アイコン */}
        {renderIcon()}

        {/* タイトル */}
        <span className="flex-1 text-sm truncate">
          {renderTitle()}
        </span>
      </div>

      {/* アクションボタン（ホバー時表示） */}
      <div className="opacity-0 group-hover:opacity-100 transition-opacity">
        {/* 追加のアクションボタンをここに配置 */}
      </div>
    </div>
  );
};