import React, { useState, useEffect } from 'react';

interface TabItem {
  key: string;
  label: string;
  children: React.ReactNode;
  disabled?: boolean;
  closable?: boolean;
}

interface TabsProps {
  items: TabItem[];
  activeKey?: string;
  defaultActiveKey?: string;
  onChange?: (key: string) => void;
  onEdit?: (targetKey: string, action: 'add' | 'remove') => void;
  type?: 'line' | 'card' | 'editable-card';
  size?: 'small' | 'default' | 'large';
  tabPosition?: 'top' | 'bottom' | 'left' | 'right';
  className?: string;
  animated?: boolean;
}

export const Tabs: React.FC<TabsProps> = ({
  items,
  activeKey: controlledActiveKey,
  defaultActiveKey,
  onChange,
  onEdit,
  type = 'line',
  size = 'default',
  tabPosition = 'top',
  className = '',
  animated = true,
}) => {
  const [activeKey, setActiveKey] = useState<string>(
    controlledActiveKey || defaultActiveKey || items[0]?.key || ''
  );

  useEffect(() => {
    if (controlledActiveKey !== undefined) {
      setActiveKey(controlledActiveKey);
    }
  }, [controlledActiveKey]);

  const handleTabClick = (key: string, disabled?: boolean) => {
    if (disabled) return;
    
    if (controlledActiveKey === undefined) {
      setActiveKey(key);
    }
    onChange?.(key);
  };

  const handleTabRemove = (key: string, e: React.MouseEvent) => {
    e.stopPropagation();
    onEdit?.(key, 'remove');
  };

  // タイプごとのスタイル
  const getTabTypeStyles = () => {
    switch (type) {
      case 'card':
        return {
          container: 'border-b border-gray-200',
          tab: 'px-4 py-2 border-t border-l border-r rounded-t-lg mr-1',
          activeTab: 'bg-white border-gray-200 border-b-white',
          inactiveTab: 'bg-gray-50 border-gray-200 hover:bg-gray-100',
        };
      case 'editable-card':
        return {
          container: 'border-b border-gray-200',
          tab: 'px-4 py-2 border-t border-l border-r rounded-t-lg mr-1 flex items-center',
          activeTab: 'bg-white border-gray-200 border-b-white',
          inactiveTab: 'bg-gray-50 border-gray-200 hover:bg-gray-100',
        };
      default: // line
        return {
          container: 'border-b border-gray-200',
          tab: 'px-4 py-2 relative',
          activeTab: 'text-blue-600 border-b-2 border-blue-600',
          inactiveTab: 'text-gray-500 hover:text-gray-700',
        };
    }
  };

  // サイズごとのスタイル
  const getSizeStyles = () => {
    switch (size) {
      case 'small':
        return 'px-3 py-1 text-sm';
      case 'large':
        return 'px-6 py-3 text-lg';
      default:
        return 'px-4 py-2';
    }
  };

  const typeStyles = getTabTypeStyles();
  const sizeStyle = getSizeStyles();

  const activeTabContent = items.find(item => item.key === activeKey);

  // タブの方向によるレイアウト調整
  const isVertical = tabPosition === 'left' || tabPosition === 'right';
  const containerClasses = `
    ${isVertical ? 'flex' : 'block'}
    ${className}
  `;

  const tabListClasses = `
    flex
    ${isVertical ? 'flex-col min-w-max mr-4' : 'flex-row'}
    ${typeStyles.container}
  `;

  return (
    <div className={containerClasses}>
      {/* タブリスト */}
      <div className={tabListClasses} role="tablist">
        {items.map(item => {
          const isActive = item.key === activeKey;
          const tabClasses = `
            cursor-pointer transition-colors duration-200 select-none
            ${typeStyles.tab}
            ${sizeStyle}
            ${isActive ? typeStyles.activeTab : typeStyles.inactiveTab}
            ${item.disabled ? 'opacity-50 cursor-not-allowed' : ''}
          `;

          return (
            <div
              key={item.key}
              className={tabClasses}
              role="tab"
              tabIndex={item.disabled ? -1 : 0}
              aria-selected={isActive}
              onClick={() => handleTabClick(item.key, item.disabled)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                  e.preventDefault();
                  handleTabClick(item.key, item.disabled);
                }
              }}
            >
              <span className="truncate">{item.label}</span>
              
              {/* 閉じるボタン（編集可能なタブの場合） */}
              {(type === 'editable-card' || item.closable) && (
                <button
                  className="ml-2 p-1 rounded hover:bg-gray-200 focus:outline-none"
                  onClick={(e) => handleTabRemove(item.key, e)}
                  aria-label={`Close ${item.label} tab`}
                >
                  <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              )}
            </div>
          );
        })}
        
        {/* 新規タブ追加ボタン（編集可能なタブの場合） */}
        {type === 'editable-card' && (
          <button
            className="px-3 py-2 text-gray-400 hover:text-gray-600 focus:outline-none"
            onClick={() => onEdit?.('', 'add')}
            aria-label="Add new tab"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
            </svg>
          </button>
        )}
      </div>

      {/* タブコンテンツ */}
      <div 
        className={`
          flex-1
          ${animated ? 'transition-opacity duration-200' : ''}
          ${isVertical ? 'ml-4' : 'mt-4'}
        `}
        role="tabpanel"
      >
        {activeTabContent?.children}
      </div>
    </div>
  );
};