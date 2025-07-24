import React, { useState, useRef, useEffect, useMemo } from "react";

interface TreeNodeData {
  key: string;
  title: string;
  children?: TreeNodeData[];
  icon?: React.ReactNode;
  disabled?: boolean;
  disableCheckbox?: boolean;
  selectable?: boolean;
  checkable?: boolean;
  loading?: boolean;
  isLeaf?: boolean;
}

interface TreeProps {
  treeData: TreeNodeData[];
  onSelect?: (selectedKeys: string[], info: any) => void;
  onCheck?: (checkedKeys: string[], info: any) => void;
  onExpand?: (expandedKeys: string[], info: any) => void;
  onDrop?: (info: any) => void;
  onRightClick?: (info: any) => void;
  loadData?: (node: TreeNodeData) => Promise<TreeNodeData[]>;
  titleRender?: (nodeData: TreeNodeData) => React.ReactNode;
  filterTreeNode?: (node: TreeNodeData) => boolean;
  selectedKeys?: string[];
  checkedKeys?: string[];
  expandedKeys?: string[];
  defaultSelectedKeys?: string[];
  defaultCheckedKeys?: string[];
  defaultExpandedKeys?: string[];
  defaultExpandAll?: boolean;
  autoExpandParent?: boolean;
  selectable?: boolean;
  checkable?: boolean;
  multiple?: boolean;
  draggable?: boolean;
  searchable?: boolean;
  virtual?: boolean;
  height?: number;
  showLine?: boolean | { style?: "solid" | "dashed" | "dotted" };
  showIndentGuides?: boolean;
  size?: "small" | "medium" | "large";
  className?: string;
}

const Tree: React.FC<TreeProps> = ({
  treeData,
  onSelect,
  onCheck,
  onExpand,
  onDrop,
  onRightClick,
  loadData,
  titleRender,
  filterTreeNode,
  selectedKeys: controlledSelectedKeys,
  checkedKeys: controlledCheckedKeys,
  expandedKeys: controlledExpandedKeys,
  defaultSelectedKeys = [],
  defaultCheckedKeys = [],
  defaultExpandedKeys = [],
  defaultExpandAll = false,
  autoExpandParent = false,
  selectable = false,
  checkable = false,
  multiple = false,
  draggable = false,
  searchable = false,
  virtual = false,
  height = 400,
  showLine = false,
  showIndentGuides = false,
  size = "medium",
  className = "",
}) => {
  const [internalSelectedKeys, setInternalSelectedKeys] =
    useState<string[]>(defaultSelectedKeys);
  const [internalCheckedKeys, setInternalCheckedKeys] =
    useState<string[]>(defaultCheckedKeys);
  const [internalExpandedKeys, setInternalExpandedKeys] = useState<string[]>(
    defaultExpandAll ? getAllKeys(treeData) : defaultExpandedKeys,
  );
  const [searchValue, setSearchValue] = useState("");
  const [loadingKeys, setLoadingKeys] = useState<Set<string>>(new Set());
  const [dragOverKey, setDragOverKey] = useState<string | null>(null);

  const treeRef = useRef<HTMLDivElement>(null);

  // Controlled vs uncontrolled state management
  const isControlledSelected = controlledSelectedKeys !== undefined;
  const isControlledChecked = controlledCheckedKeys !== undefined;
  const isControlledExpanded = controlledExpandedKeys !== undefined;

  const selectedKeys = isControlledSelected
    ? controlledSelectedKeys
    : internalSelectedKeys;
  const checkedKeys = isControlledChecked
    ? controlledCheckedKeys
    : internalCheckedKeys;
  const expandedKeys = isControlledExpanded
    ? controlledExpandedKeys
    : internalExpandedKeys;

  function getAllKeys(nodes: TreeNodeData[]): string[] {
    const keys: string[] = [];
    const traverse = (nodeList: TreeNodeData[]) => {
      nodeList.forEach((node) => {
        keys.push(node.key);
        if (node.children) {
          traverse(node.children);
        }
      });
    };
    traverse(nodes);
    return keys;
  }

  const filteredTreeData = useMemo(() => {
    if (!searchValue && !filterTreeNode) return treeData;

    const filterNodes = (nodes: TreeNodeData[]): TreeNodeData[] => {
      return nodes.reduce((acc: TreeNodeData[], node) => {
        const matchesSearch =
          !searchValue ||
          node.title.toLowerCase().includes(searchValue.toLowerCase());
        const matchesFilter = !filterTreeNode || filterTreeNode(node);

        if (matchesSearch && matchesFilter) {
          acc.push({
            ...node,
            children: node.children ? filterNodes(node.children) : undefined,
          });
        } else if (node.children) {
          const filteredChildren = filterNodes(node.children);
          if (filteredChildren.length > 0) {
            acc.push({
              ...node,
              children: filteredChildren,
            });
          }
        }

        return acc;
      }, []);
    };

    return filterNodes(treeData);
  }, [treeData, searchValue, filterTreeNode]);

  const getSizeClasses = () => {
    const sizeMap = {
      small: {
        node: "py-1 px-2 text-sm",
        icon: "w-3 h-3",
        indent: "ml-4",
      },
      medium: {
        node: "py-2 px-3 text-base",
        icon: "w-4 h-4",
        indent: "ml-6",
      },
      large: {
        node: "py-3 px-4 text-lg",
        icon: "w-5 h-5",
        indent: "ml-8",
      },
    };
    return sizeMap[size];
  };

  const handleNodeClick = (node: TreeNodeData, event: React.MouseEvent) => {
    if (node.disabled) return;

    if (selectable && onSelect) {
      let newSelectedKeys: string[];

      if (multiple) {
        newSelectedKeys = selectedKeys.includes(node.key)
          ? selectedKeys.filter((key) => key !== node.key)
          : [...selectedKeys, node.key];
      } else {
        newSelectedKeys = [node.key];
      }

      if (!isControlledSelected) {
        setInternalSelectedKeys(newSelectedKeys);
      }
      onSelect(newSelectedKeys, { node, event });
    }
  };

  const handleNodeCheck = (node: TreeNodeData, checked: boolean) => {
    if (node.disabled || node.disableCheckbox) return;

    if (checkable && onCheck) {
      let newCheckedKeys: string[];

      if (checked) {
        newCheckedKeys = [...checkedKeys, node.key];
      } else {
        newCheckedKeys = checkedKeys.filter((key) => key !== node.key);
      }

      if (!isControlledChecked) {
        setInternalCheckedKeys(newCheckedKeys);
      }
      onCheck(newCheckedKeys, { node, checked });
    }
  };

  const handleNodeExpand = async (node: TreeNodeData, expanded: boolean) => {
    if (node.disabled) return;

    let newExpandedKeys: string[];

    if (expanded) {
      newExpandedKeys = [...expandedKeys, node.key];

      // Handle async data loading
      if (loadData && (!node.children || node.children.length === 0)) {
        setLoadingKeys((prev) => new Set(prev).add(node.key));
        try {
          const childNodes = await loadData(node);
          // In a real implementation, you'd update the tree data with the loaded children
          setLoadingKeys((prev) => {
            const newSet = new Set(prev);
            newSet.delete(node.key);
            return newSet;
          });
        } catch (error) {
          setLoadingKeys((prev) => {
            const newSet = new Set(prev);
            newSet.delete(node.key);
            return newSet;
          });
        }
      }
    } else {
      newExpandedKeys = expandedKeys.filter((key) => key !== node.key);
    }

    if (!isControlledExpanded) {
      setInternalExpandedKeys(newExpandedKeys);
    }
    onExpand?.(newExpandedKeys, { node, expanded });
  };

  const handleRightClick = (node: TreeNodeData, event: React.MouseEvent) => {
    event.preventDefault();
    onRightClick?.({ node, event });
  };

  const handleDragStart = (node: TreeNodeData, event: React.DragEvent) => {
    if (!draggable || node.disabled) return;
    event.dataTransfer.setData("text/plain", node.key);
  };

  const handleDragOver = (node: TreeNodeData, event: React.DragEvent) => {
    if (!draggable) return;
    event.preventDefault();
    setDragOverKey(node.key);
  };

  const handleDragLeave = () => {
    setDragOverKey(null);
  };

  const handleDrop = (node: TreeNodeData, event: React.DragEvent) => {
    if (!draggable) return;
    event.preventDefault();
    setDragOverKey(null);

    const draggedKey = event.dataTransfer.getData("text/plain");
    onDrop?.({ dragNode: { key: draggedKey }, node, dropPosition: 0 });
  };

  const renderExpandIcon = (
    node: TreeNodeData,
    isExpanded: boolean,
    hasChildren: boolean,
  ) => {
    const sizeClasses = getSizeClasses();

    if (loadingKeys.has(node.key)) {
      return (
        <svg
          className={`${sizeClasses.icon} animate-spin text-gray-400`}
          fill="none"
          viewBox="0 0 24 24"
          role="img"
          aria-hidden="true"
        >
          <circle
            className="opacity-25"
            cx="12"
            cy="12"
            r="10"
            stroke="currentColor"
            strokeWidth="4"
          />
          <path
            className="opacity-75"
            fill="currentColor"
            d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
          />
        </svg>
      );
    }

    if (!hasChildren) {
      return <div className={sizeClasses.icon} />;
    }

    return (
      <button
        className={`${sizeClasses.icon} flex items-center justify-center hover:bg-gray-100 rounded transition-colors`}
        onClick={(e) => {
          e.stopPropagation();
          handleNodeExpand(node, !isExpanded);
        }}
      >
        <svg
          className={`w-3 h-3 transition-transform ${isExpanded ? "rotate-90" : ""}`}
          fill="currentColor"
          viewBox="0 0 20 20"
        >
          <path
            fillRule="evenodd"
            d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z"
            clipRule="evenodd"
          />
        </svg>
      </button>
    );
  };

  const renderNode = (
    node: TreeNodeData,
    level: number = 0,
  ): React.ReactNode => {
    const sizeClasses = getSizeClasses();
    const isExpanded = expandedKeys.includes(node.key);
    const isSelected = selectedKeys.includes(node.key);
    const isChecked = checkedKeys.includes(node.key);
    const hasChildren = node.children && node.children.length > 0;
    const isDragOver = dragOverKey === node.key;

    const nodeClasses = [
      "flex items-center hover:bg-gray-50 transition-colors cursor-pointer",
      sizeClasses.node,
      isSelected ? "bg-blue-50 text-blue-600" : "",
      node.disabled ? "opacity-50 cursor-not-allowed" : "",
      isDragOver ? "bg-blue-100" : "",
    ]
      .filter(Boolean)
      .join(" ");

    const indentStyle = { paddingLeft: `${level * 24}px` };

    return (
      <div key={node.key}>
        <div
          className={nodeClasses}
          style={indentStyle}
          onClick={(e) => handleNodeClick(node, e)}
          onContextMenu={(e) => handleRightClick(node, e)}
          onDragStart={(e) => handleDragStart(node, e)}
          onDragOver={(e) => handleDragOver(node, e)}
          onDragLeave={handleDragLeave}
          onDrop={(e) => handleDrop(node, e)}
          draggable={draggable && !node.disabled}
        >
          {renderExpandIcon(node, isExpanded, hasChildren)}

          {checkable && !node.disableCheckbox && (
            <input
              type="checkbox"
              checked={isChecked}
              onChange={(e) => handleNodeCheck(node, e.target.checked)}
              disabled={node.disabled}
              className="mr-2"
              onClick={(e) => e.stopPropagation()}
            />
          )}

          {node.icon && <span className="mr-2">{node.icon}</span>}

          <span className="flex-1">
            {titleRender ? titleRender(node) : node.title}
          </span>
        </div>

        {isExpanded && hasChildren && (
          <div>
            {node.children!.map((child) => renderNode(child, level + 1))}
          </div>
        )}
      </div>
    );
  };

  const renderTree = () => {
    if (filteredTreeData.length === 0) {
      return (
        <div className="tree-empty flex items-center justify-center py-8 text-gray-500">
          No data
        </div>
      );
    }

    if (virtual) {
      // Simplified virtual scrolling - in a real implementation, you'd use a library like react-window
      return (
        <div
          className="overflow-auto"
          style={{ height: `${height}px` }}
          ref={treeRef}
        >
          {filteredTreeData.map((node) => renderNode(node))}
        </div>
      );
    }

    return (
      <div ref={treeRef}>
        {filteredTreeData.map((node) => renderNode(node))}
      </div>
    );
  };

  const treeClasses = [
    "tree",
    showLine ? "tree-show-line" : "",
    showIndentGuides ? "tree-indent-guides" : "",
    className,
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <div className={treeClasses}>
      {searchable && (
        <div className="mb-4">
          <input
            type="text"
            placeholder="Search..."
            value={searchValue}
            onChange={(e) => setSearchValue(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
      )}

      {renderTree()}
    </div>
  );
};

export { Tree };
export default Tree;
