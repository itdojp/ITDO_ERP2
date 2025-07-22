import React, { useState, useRef, useEffect } from 'react';
import { Button } from '../ui/Button';
import { Input } from '../ui/Input';
import { Select } from '../ui/Select';
import { AdvancedFilterConfig, SearchConfig, FilterConfig } from './types';

interface TableFiltersProps {
  searchConfig?: SearchConfig;
  advancedFilters?: AdvancedFilterConfig;
  onSearch?: (searchValue: string) => void;
  onFilter?: (filters: FilterConfig) => void;
  onReset?: () => void;
  className?: string;
}

export const TableFilters: React.FC<TableFiltersProps> = ({
  searchConfig,
  advancedFilters,
  onSearch,
  onFilter,
  onReset,
  className = '',
}) => {
  const [searchValue, setSearchValue] = useState(searchConfig?.searchValue || '');
  const [filterValues, setFilterValues] = useState<FilterConfig>({});
  const [showAdvancedFilters, setShowAdvancedFilters] = useState(false);
  const [hasActiveFilters, setHasActiveFilters] = useState(false);

  // 検索処理
  const handleSearch = (value: string) => {
    setSearchValue(value);
    onSearch?.(value);
  };

  // フィルター変更処理
  const handleFilterChange = (key: string, value: any) => {
    const newFilters = { ...filterValues, [key]: value };
    setFilterValues(newFilters);
    
    // 空の値は削除
    if (value === '' || value === null || value === undefined) {
      delete newFilters[key];
    }
    
    onFilter?.(newFilters);
    
    // アクティブフィルターの状態更新
    const hasFilters = Object.keys(newFilters).some(k => 
      newFilters[k] !== '' && newFilters[k] !== null && newFilters[k] !== undefined
    );
    setHasActiveFilters(hasFilters || searchValue !== '');
  };

  // リセット処理
  const handleReset = () => {
    setSearchValue('');
    setFilterValues({});
    setHasActiveFilters(false);
    onReset?.();
    onSearch?.('');
    onFilter?.({});
  };

  // 検索値変更の監視
  useEffect(() => {
    setHasActiveFilters(searchValue !== '' || Object.keys(filterValues).length > 0);
  }, [searchValue, filterValues]);

  // 高度なフィルターの表示切替
  const hasAdvancedFilters = advancedFilters && Object.keys(advancedFilters).length > 0;

  // フィルター入力フィールドのレンダリング
  const renderFilterField = (key: string, config: AdvancedFilterConfig[string]) => {
    const value = filterValues[key] || '';

    switch (config.type) {
      case 'text':
        return (
          <Input
            placeholder={config.placeholder}
            value={value}
            onChange={(e) => handleFilterChange(key, e.target.value)}
            size="sm"
          />
        );

      case 'select':
        return (
          <Select
            placeholder={config.placeholder}
            value={value}
            onChange={(val) => handleFilterChange(key, val)}
            size="sm"
            allowClear
          >
            {config.options?.map(option => (
              <Select.Option key={option.value} value={option.value}>
                {option.label}
              </Select.Option>
            ))}
          </Select>
        );

      case 'date':
        return (
          <Input
            type="date"
            placeholder={config.placeholder}
            value={value}
            onChange={(e) => handleFilterChange(key, e.target.value)}
            size="sm"
          />
        );

      case 'daterange':
        return (
          <div className="flex space-x-2">
            <Input
              type="date"
              placeholder="開始日"
              value={value?.start || ''}
              onChange={(e) => handleFilterChange(key, { ...value, start: e.target.value })}
              size="sm"
            />
            <Input
              type="date"
              placeholder="終了日"
              value={value?.end || ''}
              onChange={(e) => handleFilterChange(key, { ...value, end: e.target.value })}
              size="sm"
            />
          </div>
        );

      case 'number':
        return (
          <Input
            type="number"
            placeholder={config.placeholder}
            value={value}
            onChange={(e) => handleFilterChange(key, e.target.value)}
            size="sm"
          />
        );

      case 'boolean':
        return (
          <Select
            placeholder={config.placeholder}
            value={value}
            onChange={(val) => handleFilterChange(key, val)}
            size="sm"
            allowClear
          >
            <Select.Option value={true}>はい</Select.Option>
            <Select.Option value={false}>いいえ</Select.Option>
          </Select>
        );

      default:
        return null;
    }
  };

  return (
    <div className={`space-y-4 ${className}`}>
      {/* 検索バー */}
      {searchConfig && (
        <div className="flex items-center space-x-3">
          <div className="flex-1">
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <svg className="h-5 w-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
              </div>
              <Input
                placeholder={searchConfig.placeholder || '検索...'}
                value={searchValue}
                onChange={(e) => handleSearch(e.target.value)}
                className="pl-10"
                onKeyPress={(e) => {
                  if (e.key === 'Enter') {
                    handleSearch(searchValue);
                  }
                }}
              />
            </div>
          </div>
          
          {/* フィルター切替ボタン */}
          {hasAdvancedFilters && (
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setShowAdvancedFilters(!showAdvancedFilters)}
              className="flex items-center space-x-2"
            >
              <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 100 4m0-4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 100 4m0-4v2m0-6V4" />
              </svg>
              <span>フィルター</span>
              {showAdvancedFilters ? (
                <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 15l7-7 7 7" />
                </svg>
              ) : (
                <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
              )}
            </Button>
          )}
          
          {/* リセットボタン */}
          {hasActiveFilters && (
            <Button
              variant="ghost"
              size="sm"
              onClick={handleReset}
              className="text-gray-500 hover:text-gray-700"
            >
              <svg className="h-4 w-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
              クリア
            </Button>
          )}
        </div>
      )}

      {/* 高度なフィルター */}
      {hasAdvancedFilters && showAdvancedFilters && (
        <div className="bg-gray-50 rounded-lg p-4 border">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
            {Object.entries(advancedFilters!).map(([key, config]) => (
              <div key={key} className="space-y-1">
                <label className="block text-sm font-medium text-gray-700">
                  {config.label}
                </label>
                {renderFilterField(key, config)}
              </div>
            ))}
          </div>
          
          {/* フィルターアクション */}
          <div className="flex items-center justify-end space-x-2 mt-4 pt-4 border-t border-gray-200">
            <Button
              variant="ghost"
              size="sm"
              onClick={handleReset}
            >
              リセット
            </Button>
            <Button
              size="sm"
              onClick={() => {
                // 現在のフィルター値で強制適用
                onFilter?.(filterValues);
              }}
            >
              適用
            </Button>
          </div>
        </div>
      )}

      {/* アクティブフィルターの表示 */}
      {hasActiveFilters && (
        <div className="flex flex-wrap items-center gap-2">
          <span className="text-sm text-gray-500">アクティブフィルター:</span>
          
          {searchValue && (
            <div className="inline-flex items-center px-2 py-1 rounded-full text-xs bg-blue-100 text-blue-800">
              <span>検索: {searchValue}</span>
              <button
                onClick={() => handleSearch('')}
                className="ml-1 hover:text-blue-600"
              >
                <svg className="h-3 w-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
          )}
          
          {Object.entries(filterValues).map(([key, value]) => {
            if (!value || value === '') return null;
            
            const config = advancedFilters?.[key];
            let displayValue = value;
            
            if (config?.type === 'select') {
              const option = config.options?.find(opt => opt.value === value);
              displayValue = option?.label || value;
            } else if (config?.type === 'daterange' && typeof value === 'object') {
              displayValue = `${value.start || ''} - ${value.end || ''}`;
            } else if (config?.type === 'boolean') {
              displayValue = value ? 'はい' : 'いいえ';
            }
            
            return (
              <div
                key={key}
                className="inline-flex items-center px-2 py-1 rounded-full text-xs bg-gray-100 text-gray-800"
              >
                <span>{config?.label || key}: {String(displayValue)}</span>
                <button
                  onClick={() => handleFilterChange(key, '')}
                  className="ml-1 hover:text-gray-600"
                >
                  <svg className="h-3 w-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};