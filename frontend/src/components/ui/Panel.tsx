import React, { useState, useRef, useCallback, useEffect } from 'react';
import { cn } from '@/lib/utils';

export interface PanelAction {
  id: string;
  label: string;
  onClick: () => void;
}

export interface PanelTab {
  id: string;
  label: string;
  content: React.ReactNode;
}

export interface PanelBreadcrumb {
  label: string;
  href: string;
}

export interface PanelProps {
  title?: string;
  children?: React.ReactNode;
  content?: React.ReactNode;
  header?: React.ReactNode;
  footer?: React.ReactNode;
  toolbar?: React.ReactNode;
  icon?: React.ReactNode;
  badge?: string | number;
  size?: 'sm' | 'md' | 'lg';
  theme?: 'light' | 'dark';
  variant?: 'default' | 'bordered' | 'filled' | 'outlined';
  priority?: 'low' | 'normal' | 'high' | 'urgent';
  status?: 'active' | 'inactive' | 'warning' | 'error';
  collapsible?: boolean;
  defaultCollapsed?: boolean;
  minimizable?: boolean;
  closable?: boolean;
  resizable?: boolean;
  draggable?: boolean;
  fullscreen?: boolean;
  loading?: boolean;
  error?: string;
  empty?: boolean;
  emptyState?: React.ReactNode;
  scrollable?: boolean;
  maxHeight?: string;
  width?: string;
  height?: string;
  animated?: boolean;
  group?: string;
  breadcrumbs?: PanelBreadcrumb[];
  actions?: PanelAction[];
  tabs?: PanelTab[];
  progress?: number;
  helpText?: string;
  ariaLabel?: string;
  ariaDescribedBy?: string;
  onToggle?: (collapsed: boolean) => void;
  onMinimize?: (minimized: boolean) => void;
  onClose?: () => void;
  onResize?: (width: number, height: number) => void;
  onDrag?: (position: { x: number; y: number }) => void;
  className?: string;
  'data-testid'?: string;
  'data-category'?: string;
  'data-id'?: string;
}

export const Panel: React.FC<PanelProps> = ({
  title,
  children,
  content,
  header,
  footer,
  toolbar,
  icon,
  badge,
  size = 'md',
  theme = 'light',
  variant = 'default',
  priority = 'normal',
  status = 'active',
  collapsible = false,
  defaultCollapsed = false,
  minimizable = false,
  closable = false,
  resizable = false,
  draggable = false,
  fullscreen = false,
  loading = false,
  error,
  empty = false,
  emptyState,
  scrollable = false,
  maxHeight,
  width,
  height,
  animated = false,
  group,
  breadcrumbs,
  actions,
  tabs,
  progress,
  helpText,
  ariaLabel,
  ariaDescribedBy,
  onToggle,
  onMinimize,
  onClose,
  onResize,
  onDrag,
  className,
  'data-testid': dataTestId = 'panel-container',
  'data-category': dataCategory,
  'data-id': dataId,
  ...props
}) => {
  const [isCollapsed, setIsCollapsed] = useState(defaultCollapsed);
  const [isMinimized, setIsMinimized] = useState(false);
  const [selectedTab, setSelectedTab] = useState(tabs?.[0]?.id || '');
  const [dragPosition, setDragPosition] = useState({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = useState(false);

  const panelRef = useRef<HTMLDivElement>(null);
  const headerRef = useRef<HTMLDivElement>(null);
  const resizeRef = useRef<HTMLDivElement>(null);

  const sizeClasses = {
    sm: 'size-sm text-sm',
    md: 'size-md text-base',
    lg: 'size-lg text-lg'
  };

  const themeClasses = {
    light: 'theme-light bg-white border-gray-200 text-gray-900',
    dark: 'theme-dark bg-gray-800 border-gray-700 text-white'
  };

  const variantClasses = {
    default: 'variant-default border',
    bordered: 'variant-bordered border-2',
    filled: 'variant-filled bg-gray-50',
    outlined: 'variant-outlined border-2 border-dashed'
  };

  const priorityClasses = {
    low: 'priority-low',
    normal: 'priority-normal',
    high: 'priority-high border-blue-500',
    urgent: 'priority-urgent border-red-500'
  };

  const statusClasses = {
    active: 'status-active',
    inactive: 'status-inactive opacity-60',
    warning: 'status-warning border-yellow-500',
    error: 'status-error border-red-500'
  };

  // Handle collapse toggle
  const handleToggle = useCallback(() => {
    const newCollapsed = !isCollapsed;
    setIsCollapsed(newCollapsed);
    onToggle?.(newCollapsed);
  }, [isCollapsed, onToggle]);

  // Handle minimize toggle
  const handleMinimize = useCallback(() => {
    const newMinimized = !isMinimized;
    setIsMinimized(newMinimized);
    onMinimize?.(newMinimized);
  }, [isMinimized, onMinimize]);

  // Handle close
  const handleClose = useCallback(() => {
    onClose?.();
  }, [onClose]);

  // Handle drag
  const handleDragStart = useCallback((e: React.DragEvent) => {
    if (!draggable) return;
    setIsDragging(true);
    onDrag?.({ x: e.clientX, y: e.clientY });
  }, [draggable, onDrag]);

  const handleDragEnd = useCallback(() => {
    setIsDragging(false);
  }, []);

  // Handle keyboard events
  const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && collapsible) {
      handleToggle();
    }
  }, [collapsible, handleToggle]);

  // Handle tab selection
  const handleTabClick = useCallback((tabId: string) => {
    setSelectedTab(tabId);
  }, []);

  // Render header
  const renderHeader = () => {
    if (header) {
      return <div className="panel-header">{header}</div>;
    }

    if (!title && !icon && !actions && !collapsible && !minimizable && !closable) {
      return null;
    }

    return (
      <div
        ref={headerRef}
        className={cn(
          'flex items-center justify-between p-4 border-b',
          draggable && 'draggable cursor-move',
          themeClasses[theme].includes('dark') ? 'border-gray-700' : 'border-gray-200'
        )}
        data-testid="panel-header"
        draggable={draggable}
        onDragStart={handleDragStart}
        onDragEnd={handleDragEnd}
      >
        <div className="flex items-center space-x-2">
          {icon && (
            <div className="panel-icon" data-testid="panel-icon">
              {icon}
            </div>
          )}
          
          {title && (
            <h3 className="font-semibold">{title}</h3>
          )}
          
          {badge && (
            <span
              className="px-2 py-1 text-xs bg-blue-100 text-blue-800 rounded-full"
              data-testid="panel-badge"
            >
              {badge}
            </span>
          )}
        </div>

        <div className="flex items-center space-x-2">
          {actions && actions.map(action => (
            <button
              key={action.id}
              className="px-2 py-1 text-sm hover:bg-gray-100 rounded"
              onClick={action.onClick}
              data-testid={`panel-action-${action.id}`}
            >
              {action.label}
            </button>
          ))}
          
          {minimizable && (
            <button
              className="p-1 hover:bg-gray-100 rounded"
              onClick={handleMinimize}
              data-testid="panel-minimize"
            >
              −
            </button>
          )}
          
          {collapsible && (
            <button
              className="p-1 hover:bg-gray-100 rounded"
              onClick={handleToggle}
              onKeyDown={handleKeyDown}
              tabIndex={0}
              data-testid="panel-toggle"
            >
              {isCollapsed ? '▶' : '▼'}
            </button>
          )}
          
          {closable && (
            <button
              className="p-1 hover:bg-gray-100 rounded"
              onClick={handleClose}
              data-testid="panel-close"
            >
              ×
            </button>
          )}
        </div>
      </div>
    );
  };

  // Render breadcrumbs
  const renderBreadcrumbs = () => {
    if (!breadcrumbs || breadcrumbs.length === 0) return null;

    return (
      <div className="px-4 py-2 border-b text-sm" data-testid="panel-breadcrumbs">
        {breadcrumbs.map((crumb, index) => (
          <span key={index}>
            <a href={crumb.href} className="text-blue-600 hover:underline">
              {crumb.label}
            </a>
            {index < breadcrumbs.length - 1 && <span className="mx-2">/</span>}
          </span>
        ))}
      </div>
    );
  };

  // Render toolbar
  const renderToolbar = () => {
    if (!toolbar) return null;

    return (
      <div className="px-4 py-2 border-b" data-testid="panel-toolbar-wrapper">
        {toolbar}
      </div>
    );
  };

  // Render progress bar
  const renderProgress = () => {
    if (progress === undefined) return null;

    return (
      <div className="px-4 py-2">
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div
            className="bg-blue-600 h-2 rounded-full transition-all duration-300"
            style={{ width: `${progress}%` }}
            data-testid="panel-progress"
          />
        </div>
      </div>
    );
  };

  // Render tabs
  const renderTabs = () => {
    if (!tabs || tabs.length === 0) return null;

    return (
      <div className="border-b" data-testid="panel-tabs">
        <div className="flex">
          {tabs.map(tab => (
            <button
              key={tab.id}
              className={cn(
                'px-4 py-2 text-sm font-medium border-b-2 transition-colors',
                selectedTab === tab.id
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              )}
              onClick={() => handleTabClick(tab.id)}
            >
              {tab.label}
            </button>
          ))}
        </div>
      </div>
    );
  };

  // Render help text
  const renderHelpText = () => {
    if (!helpText) return null;

    return (
      <div className="px-4 py-2 text-sm text-gray-600" data-testid="panel-help">
        {helpText}
      </div>
    );
  };

  // Render content
  const renderContent = () => {
    if (loading) {
      return (
        <div className="flex items-center justify-center p-8" data-testid="panel-loading">
          <div className="w-6 h-6 border-2 border-gray-300 border-t-blue-500 rounded-full animate-spin"></div>
        </div>
      );
    }

    if (error) {
      return (
        <div className="p-4 text-red-600" data-testid="panel-error">
          {error}
        </div>
      );
    }

    if (empty && emptyState) {
      return emptyState;
    }

    if (tabs && tabs.length > 0) {
      const activeTab = tabs.find(tab => tab.id === selectedTab);
      return activeTab?.content || null;
    }

    return content || children;
  };

  // Render footer
  const renderFooter = () => {
    if (!footer) return null;

    return (
      <div className="border-t p-4" data-testid="panel-footer-wrapper">
        {footer}
      </div>
    );
  };

  // Render resize handle
  const renderResizeHandle = () => {
    if (!resizable) return null;

    return (
      <div
        ref={resizeRef}
        className="absolute bottom-0 right-0 w-4 h-4 cursor-se-resize"
        data-testid="panel-resize-handle"
      >
        <div className="w-2 h-2 bg-gray-400 rounded-full"></div>
      </div>
    );
  };

  const containerStyle = {
    width,
    height,
    maxHeight: scrollable ? maxHeight : undefined,
    transform: isDragging ? `translate(${dragPosition.x}px, ${dragPosition.y}px)` : undefined
  };

  return (
    <div
      ref={panelRef}
      className={cn(
        'panel relative',
        sizeClasses[size],
        themeClasses[theme],
        variantClasses[variant],
        priorityClasses[priority],
        statusClasses[status],
        fullscreen && 'fullscreen fixed inset-0 z-50',
        resizable && 'resizable',
        animated && 'animated transition-all duration-300',
        isDragging && 'dragging',
        className
      )}
      style={containerStyle}
      role="region"
      aria-label={ariaLabel}
      aria-describedby={ariaDescribedBy}
      data-testid={dataTestId}
      data-category={dataCategory}
      data-id={dataId}
      data-group={group}
      {...props}
    >
      {renderHeader()}
      {renderBreadcrumbs()}
      {renderToolbar()}
      {renderProgress()}
      {renderTabs()}
      {renderHelpText()}
      
      {!isCollapsed && !isMinimized && (
        <div
          className={cn(
            'panel-content',
            scrollable && 'scrollable overflow-auto'
          )}
          style={{ maxHeight: scrollable ? maxHeight : undefined }}
          data-testid="panel-content"
        >
          {renderContent()}
        </div>
      )}
      
      {renderFooter()}
      {renderResizeHandle()}
    </div>
  );
};

export default Panel;