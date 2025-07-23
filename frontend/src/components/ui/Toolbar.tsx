import React, { useState, useRef, useCallback, useEffect } from 'react';
import { cn } from '@/lib/utils';

export interface ToolbarMenuItem {
  id: string;
  label: string;
  onClick: () => void;
}

export interface ToolbarTool {
  id: string;
  label: string;
  icon?: React.ReactNode;
  type?: 'button' | 'toggle' | 'dropdown' | 'group';
  active?: boolean;
  selected?: boolean;
  disabled?: boolean;
  visible?: boolean;
  group?: string;
  badge?: number | string;
  shortcut?: string;
  description?: string;
  onClick?: () => void;
  items?: ToolbarMenuItem[];
  tools?: ToolbarTool[];
  contextMenu?: ToolbarMenuItem[];
  render?: () => React.ReactNode;
}

export interface ToolbarProps {
  tools: ToolbarTool[];
  orientation?: 'horizontal' | 'vertical';
  position?: 'top' | 'bottom' | 'left' | 'right';
  size?: 'sm' | 'md' | 'lg';
  theme?: 'light' | 'dark';
  variant?: 'default' | 'ghost' | 'outline';
  spacing?: 'sm' | 'md' | 'lg';
  showIcons?: boolean;
  showLabels?: boolean;
  showTooltips?: boolean;
  showSeparators?: boolean;
  showShortcuts?: boolean;
  showDescriptions?: boolean;
  showOverflow?: boolean;
  compact?: boolean;
  sticky?: boolean;
  floating?: boolean;
  responsive?: boolean;
  animated?: boolean;
  searchable?: boolean;
  customizable?: boolean;
  reorderable?: boolean;
  loading?: boolean;
  maxVisibleTools?: number;
  ariaLabel?: string;
  onCustomize?: () => void;
  onReorder?: (tools: ToolbarTool[]) => void;
  className?: string;
  'data-testid'?: string;
  'data-category'?: string;
  'data-id'?: string;
}

export const Toolbar: React.FC<ToolbarProps> = ({
  tools,
  orientation = 'horizontal',
  position = 'top',
  size = 'md',
  theme = 'light',
  variant = 'default',
  spacing = 'md',
  showIcons = true,
  showLabels = false,
  showTooltips = true,
  showSeparators = false,
  showShortcuts = false,
  showDescriptions = false,
  showOverflow = false,
  compact = false,
  sticky = false,
  floating = false,
  responsive = false,
  animated = false,
  searchable = false,
  customizable = false,
  reorderable = false,
  loading = false,
  maxVisibleTools = 8,
  ariaLabel = 'Toolbar',
  onCustomize,
  onReorder,
  className,
  'data-testid': dataTestId = 'toolbar-container',
  'data-category': dataCategory,
  'data-id': dataId,
  ...props
}) => {
  const [openDropdown, setOpenDropdown] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [hoveredTool, setHoveredTool] = useState<string | null>(null);
  const [contextMenu, setContextMenu] = useState<{ toolId: string; x: number; y: number } | null>(null);
  const [draggedTool, setDraggedTool] = useState<string | null>(null);
  const [focusedIndex, setFocusedIndex] = useState(-1);

  const containerRef = useRef<HTMLDivElement>(null);
  const toolRefs = useRef<{ [key: string]: HTMLButtonElement | null }>({});

  const sizeClasses = {
    sm: 'size-sm gap-1',
    md: 'size-md gap-2',
    lg: 'size-lg gap-3'
  };

  const themeClasses = {
    light: 'theme-light bg-white border-gray-200 text-gray-900',
    dark: 'theme-dark bg-gray-800 border-gray-700 text-white'
  };

  const orientationClasses = {
    horizontal: 'orientation-horizontal flex-row',
    vertical: 'orientation-vertical flex-col'
  };

  const positionClasses = {
    top: 'position-top',
    bottom: 'position-bottom',
    left: 'position-left',
    right: 'position-right'
  };

  const variantClasses = {
    default: 'variant-default',
    ghost: 'variant-ghost',
    outline: 'variant-outline'
  };

  const spacingClasses = {
    sm: 'spacing-sm',
    md: 'spacing-md',
    lg: 'spacing-lg'
  };

  // Filter visible tools
  const visibleTools = tools.filter(tool => tool.visible !== false);

  // Filter tools based on search query
  const filteredTools = searchQuery
    ? visibleTools.filter(tool =>
        tool.label.toLowerCase().includes(searchQuery.toLowerCase()) ||
        tool.description?.toLowerCase().includes(searchQuery.toLowerCase())
      )
    : visibleTools;

  // Split tools for overflow handling
  const visibleToolsList = showOverflow && filteredTools.length > maxVisibleTools
    ? filteredTools.slice(0, maxVisibleTools)
    : filteredTools;

  const overflowTools = showOverflow && filteredTools.length > maxVisibleTools
    ? filteredTools.slice(maxVisibleTools)
    : [];

  // Handle keyboard navigation
  const handleKeyDown = useCallback((e: React.KeyboardEvent, toolIndex: number) => {
    const totalTools = visibleToolsList.length;
    
    switch (e.key) {
      case 'ArrowRight':
      case 'ArrowDown':
        e.preventDefault();
        const nextIndex = orientation === 'horizontal' 
          ? (e.key === 'ArrowRight' ? (toolIndex + 1) % totalTools : toolIndex)
          : (e.key === 'ArrowDown' ? (toolIndex + 1) % totalTools : toolIndex);
        setFocusedIndex(nextIndex);
        const nextTool = visibleToolsList[nextIndex];
        if (nextTool && toolRefs.current[nextTool.id]) {
          toolRefs.current[nextTool.id]?.focus();
        }
        break;
      
      case 'ArrowLeft':
      case 'ArrowUp':
        e.preventDefault();
        const prevIndex = orientation === 'horizontal'
          ? (e.key === 'ArrowLeft' ? (toolIndex - 1 + totalTools) % totalTools : toolIndex)
          : (e.key === 'ArrowUp' ? (toolIndex - 1 + totalTools) % totalTools : toolIndex);
        setFocusedIndex(prevIndex);
        const prevTool = visibleToolsList[prevIndex];
        if (prevTool && toolRefs.current[prevTool.id]) {
          toolRefs.current[prevTool.id]?.focus();
        }
        break;
      
      case 'Enter':
      case ' ':
        e.preventDefault();
        const currentTool = visibleToolsList[toolIndex];
        if (currentTool && !currentTool.disabled) {
          handleToolClick(currentTool);
        }
        break;
    }
  }, [orientation, visibleToolsList]);

  // Handle tool click
  const handleToolClick = useCallback((tool: ToolbarTool) => {
    if (tool.disabled) return;

    if (tool.type === 'dropdown') {
      setOpenDropdown(openDropdown === tool.id ? null : tool.id);
    } else {
      tool.onClick?.();
      setOpenDropdown(null);
    }
  }, [openDropdown]);

  // Handle dropdown item click
  const handleDropdownItemClick = useCallback((item: ToolbarMenuItem) => {
    item.onClick();
    setOpenDropdown(null);
  }, []);

  // Handle context menu
  const handleContextMenu = useCallback((e: React.MouseEvent, tool: ToolbarTool) => {
    if (!tool.contextMenu || tool.contextMenu.length === 0) return;
    
    e.preventDefault();
    setContextMenu({
      toolId: tool.id,
      x: e.clientX,
      y: e.clientY
    });
  }, []);

  // Handle drag and drop
  const handleDragStart = useCallback((e: React.DragEvent, tool: ToolbarTool) => {
    if (!reorderable) return;
    setDraggedTool(tool.id);
    if (e.dataTransfer) {
      e.dataTransfer.setData('text/plain', tool.id);
    }
  }, [reorderable]);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    if (!reorderable) return;
    e.preventDefault();
  }, [reorderable]);

  const handleDrop = useCallback((e: React.DragEvent, targetTool: ToolbarTool) => {
    if (!reorderable || !draggedTool) return;
    
    e.preventDefault();
    const draggedIndex = tools.findIndex(t => t.id === draggedTool);
    const targetIndex = tools.findIndex(t => t.id === targetTool.id);
    
    if (draggedIndex !== -1 && targetIndex !== -1 && draggedIndex !== targetIndex) {
      const newTools = [...tools];
      const [draggedItem] = newTools.splice(draggedIndex, 1);
      newTools.splice(targetIndex, 0, draggedItem);
      onReorder?.(newTools);
    }
    
    setDraggedTool(null);
  }, [reorderable, draggedTool, tools, onReorder]);

  // Click outside handler
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setOpenDropdown(null);
        setContextMenu(null);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Escape key handler
  useEffect(() => {
    const handleEscapeKey = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        setOpenDropdown(null);
        setContextMenu(null);
      }
    };

    document.addEventListener('keydown', handleEscapeKey);
    return () => document.removeEventListener('keydown', handleEscapeKey);
  }, []);

  // Group tools by group property
  const groupedTools = visibleToolsList.reduce((groups, tool) => {
    const group = tool.group || 'default';
    if (!groups[group]) {
      groups[group] = [];
    }
    groups[group].push(tool);
    return groups;
  }, {} as Record<string, ToolbarTool[]>);

  const groupKeys = Object.keys(groupedTools);

  // Render tool icon
  const renderToolIcon = (tool: ToolbarTool) => {
    if (!showIcons || !tool.icon) return null;
    return (
      <span className="tool-icon" data-testid={`tool-icon-${tool.id}`}>
        {tool.icon}
      </span>
    );
  };

  // Render tool label
  const renderToolLabel = (tool: ToolbarTool) => {
    if (!showLabels && !tool.render) return null;
    return (
      <span className="tool-label" data-testid={`tool-label-${tool.id}`}>
        {tool.label}
      </span>
    );
  };

  // Render tool badge
  const renderToolBadge = (tool: ToolbarTool) => {
    if (!tool.badge) return null;
    return (
      <span
        className="absolute -top-1 -right-1 bg-red-500 text-white text-xs px-1 rounded-full min-w-4 h-4 flex items-center justify-center"
        data-testid={`tool-badge-${tool.id}`}
      >
        {tool.badge}
      </span>
    );
  };

  // Render tool shortcut
  const renderToolShortcut = (tool: ToolbarTool) => {
    if (!showShortcuts || !tool.shortcut) return null;
    return (
      <span className="text-xs text-gray-500 ml-2" data-testid={`tool-shortcut-${tool.id}`}>
        {tool.shortcut}
      </span>
    );
  };

  // Render tool description
  const renderToolDescription = (tool: ToolbarTool) => {
    if (!showDescriptions || !tool.description) return null;
    return (
      <div className="text-xs text-gray-600 mt-1" data-testid={`tool-description-${tool.id}`}>
        {tool.description}
      </div>
    );
  };

  // Render tooltip
  const renderTooltip = (tool: ToolbarTool) => {
    if (!showTooltips || hoveredTool !== tool.id) return null;
    return (
      <div
        className="absolute z-50 px-2 py-1 text-xs bg-gray-900 text-white rounded shadow-lg pointer-events-none"
        style={{ bottom: '100%', left: '50%', transform: 'translateX(-50%)', marginBottom: '4px' }}
        data-testid={`tooltip-${tool.id}`}
      >
        {tool.label}
        {tool.shortcut && (
          <span className="ml-2 text-gray-300">({tool.shortcut})</span>
        )}
      </div>
    );
  };

  // Render dropdown
  const renderDropdown = (tool: ToolbarTool) => {
    if (tool.type !== 'dropdown' || openDropdown !== tool.id || !tool.items) return null;
    
    return (
      <div
        className="absolute z-50 mt-1 bg-white border border-gray-200 rounded-md shadow-lg min-w-32"
        data-testid={`dropdown-${tool.id}`}
      >
        {tool.items.map(item => (
          <button
            key={item.id}
            className="w-full px-3 py-2 text-left text-sm hover:bg-gray-100 first:rounded-t-md last:rounded-b-md"
            onClick={() => handleDropdownItemClick(item)}
          >
            {item.label}
          </button>
        ))}
      </div>
    );
  };

  // Render context menu
  const renderContextMenu = () => {
    if (!contextMenu) return null;
    
    const tool = tools.find(t => t.id === contextMenu.toolId);
    if (!tool || !tool.contextMenu) return null;

    return (
      <div
        className="fixed z-50 bg-white border border-gray-200 rounded-md shadow-lg min-w-32"
        style={{ left: contextMenu.x, top: contextMenu.y }}
        data-testid={`context-menu-${tool.id}`}
      >
        {tool.contextMenu.map((item, index) => (
          <button
            key={index}
            className="w-full px-3 py-2 text-left text-sm hover:bg-gray-100 first:rounded-t-md last:rounded-b-md"
            onClick={() => {
              item.onClick();
              setContextMenu(null);
            }}
          >
            {item.label}
          </button>
        ))}
      </div>
    );
  };

  // Render tool group
  const renderToolGroup = (tool: ToolbarTool) => {
    if (tool.type !== 'group' || !tool.tools) return null;
    
    return (
      <div className="flex gap-1" data-testid={`tool-group-${tool.id}`}>
        {tool.tools.map(subTool => renderTool(subTool))}
      </div>
    );
  };

  // Render individual tool
  const renderTool = (tool: ToolbarTool, index?: number) => {
    if (tool.render) {
      return (
        <div key={tool.id} data-testid={`tool-${tool.id}`}>
          {tool.render()}
        </div>
      );
    }

    if (tool.type === 'group') {
      return (
        <div key={tool.id}>
          {renderToolGroup(tool)}
        </div>
      );
    }

    const isActive = tool.type === 'toggle' ? tool.active : false;
    const isSelected = tool.selected || false;

    return (
      <div key={tool.id} className="relative">
        <button
          ref={(el) => { toolRefs.current[tool.id] = el; }}
          className={cn(
            'relative flex items-center justify-center px-3 py-2 rounded transition-colors',
            'hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500',
            tool.disabled && 'opacity-50 cursor-not-allowed',
            isActive && 'bg-blue-100 text-blue-700 active',
            isSelected && 'bg-gray-200 selected',
            draggedTool === tool.id && 'opacity-50'
          )}
          disabled={tool.disabled}
          draggable={reorderable}
          data-testid={`tool-${tool.id}`}
          onClick={() => handleToolClick(tool)}
          onContextMenu={(e) => handleContextMenu(e, tool)}
          onMouseEnter={() => setHoveredTool(tool.id)}
          onMouseLeave={() => setHoveredTool(null)}
          onKeyDown={(e) => index !== undefined && handleKeyDown(e, index)}
          onDragStart={(e) => handleDragStart(e, tool)}
          onDragOver={handleDragOver}
          onDrop={(e) => handleDrop(e, tool)}
        >
          {renderToolIcon(tool)}
          {renderToolLabel(tool)}
          {renderToolShortcut(tool)}
          {renderToolBadge(tool)}
          
          {tool.type === 'dropdown' && (
            <span className="ml-1 text-xs">▼</span>
          )}
        </button>
        
        {renderToolDescription(tool)}
        {renderTooltip(tool)}
        {renderDropdown(tool)}
      </div>
    );
  };

  // Render separator
  const renderSeparator = (key: string) => (
    <div
      key={`separator-${key}`}
      className={cn(
        'border-gray-300',
        orientation === 'horizontal' ? 'border-l h-6' : 'border-t w-6'
      )}
      data-testid={`separator-${key}`}
    />
  );

  // Render overflow menu
  const renderOverflowMenu = () => {
    if (!showOverflow || overflowTools.length === 0) return null;

    return (
      <div className="relative">
        <button
          className="flex items-center justify-center px-3 py-2 rounded hover:bg-gray-100"
          onClick={() => setOpenDropdown(openDropdown === 'overflow' ? null : 'overflow')}
          data-testid="more-tools-button"
        >
          ⋯
        </button>
        
        {openDropdown === 'overflow' && (
          <div
            className="absolute z-50 mt-1 bg-white border border-gray-200 rounded-md shadow-lg min-w-48"
            data-testid="overflow-menu"
          >
            {overflowTools.map(tool => (
              <button
                key={tool.id}
                className="w-full px-3 py-2 text-left text-sm hover:bg-gray-100 first:rounded-t-md last:rounded-b-md flex items-center"
                disabled={tool.disabled}
                onClick={() => {
                  handleToolClick(tool);
                  setOpenDropdown(null);
                }}
              >
                {tool.icon && <span className="mr-2">{tool.icon}</span>}
                {tool.label}
                {tool.shortcut && (
                  <span className="ml-auto text-xs text-gray-500">{tool.shortcut}</span>
                )}
              </button>
            ))}
          </div>
        )}
      </div>
    );
  };

  // Render search box
  const renderSearchBox = () => {
    if (!searchable) return null;

    return (
      <div className="flex items-center px-2" data-testid="toolbar-search">
        <input
          type="text"
          placeholder="Search tools..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="px-2 py-1 text-sm border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500"
          data-testid="toolbar-search-input"
        />
      </div>
    );
  };

  // Render customize button
  const renderCustomizeButton = () => {
    if (!customizable) return null;

    return (
      <button
        className="flex items-center justify-center px-3 py-2 rounded hover:bg-gray-100"
        onClick={onCustomize}
        data-testid="customize-button"
      >
        ⚙️
      </button>
    );
  };

  if (loading) {
    return (
      <div
        className={cn(
          'flex items-center justify-center p-4',
          themeClasses[theme],
          className
        )}
        data-testid="toolbar-loading"
      >
        <div className="w-6 h-6 border-2 border-gray-300 border-t-blue-500 rounded-full animate-spin"></div>
      </div>
    );
  }

  return (
    <div
      ref={containerRef}
      className={cn(
        'toolbar flex items-center border',
        sizeClasses[size],
        themeClasses[theme],
        orientationClasses[orientation],
        positionClasses[position],
        variantClasses[variant],
        spacingClasses[spacing],
        compact && 'compact p-1',
        sticky && 'sticky',
        floating && 'floating shadow-lg rounded-lg',
        responsive && 'responsive',
        animated && 'animated',
        className
      )}
      role="toolbar"
      aria-label={ariaLabel}
      data-testid={dataTestId}
      data-category={dataCategory}
      data-id={dataId}
      {...props}
    >
      {renderSearchBox()}
      
      {showSeparators && groupKeys.length > 1 ? (
        groupKeys.map((groupKey, groupIndex) => (
          <React.Fragment key={groupKey}>
            {groupIndex > 0 && renderSeparator(`${groupKeys[groupIndex - 1]}-${groupKey}`)}
            {groupedTools[groupKey].map((tool, toolIndex) => renderTool(tool, toolIndex))}
          </React.Fragment>
        ))
      ) : (
        visibleToolsList.map((tool, index) => renderTool(tool, index))
      )}
      
      {renderOverflowMenu()}
      {renderCustomizeButton()}
      {renderContextMenu()}
    </div>
  );
};

export default Toolbar;