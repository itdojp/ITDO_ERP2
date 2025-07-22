import React, { useState, useEffect, useMemo, useCallback } from 'react';
import { TreeNode as TreeNodeComponent } from './TreeNode';
import { TreeViewProps, TreeNode } from './types';

export const TreeView: React.FC<TreeViewProps> = ({
  treeData,
  expandedKeys: controlledExpandedKeys,
  selectedKeys: controlledSelectedKeys,
  checkedKeys: controlledCheckedKeys,
  defaultExpandedKeys = [],
  defaultSelectedKeys = [],
  defaultCheckedKeys = [],
  defaultExpandAll = false,
  autoExpandParent = true,
  checkable = false,
  checkStrictly = false,
  selectable = true,
  multiple = false,
  disabled = false,
  showIcon = true,
  showLine = false,
  searchValue = '',
  onExpand,
  onSelect,
  onCheck,
  onLoad,
  loadData,
  onRightClick,
  onDragStart,
  onDragEnter,
  onDragOver,
  onDragLeave,
  onDragEnd,
  onDrop,
  draggable = false,
  allowDrop,
  titleRender,
  filterTreeNode,
  className = '',
  style,
  height,
  virtual = false,
}) => {
  // 内部状態
  const [internalExpandedKeys, setInternalExpandedKeys] = useState<string[]>(
    controlledExpandedKeys || (defaultExpandAll ? getAllKeys(treeData) : defaultExpandedKeys)
  );
  const [internalSelectedKeys, setInternalSelectedKeys] = useState<string[]>(
    controlledSelectedKeys || defaultSelectedKeys
  );
  const [internalCheckedKeys, setInternalCheckedKeys] = useState<string[]>(
    controlledCheckedKeys || defaultCheckedKeys
  );
  const [loadingKeys, setLoadingKeys] = useState<string[]>([]);
  const [dragOverKey, setDragOverKey] = useState<string | null>(null);
  const [dragOverGap, setDragOverGap] = useState<{
    key: string;
    top: boolean;
    bottom: boolean;
  } | null>(null);

  // 制御された値か内部状態かを判定
  const expandedKeys = controlledExpandedKeys ?? internalExpandedKeys;
  const selectedKeys = controlledSelectedKeys ?? internalSelectedKeys;
  const checkedKeys = controlledCheckedKeys ?? internalCheckedKeys;

  // すべてのキーを取得するヘルパー関数
  function getAllKeys(nodes: TreeNode[]): string[] {
    const keys: string[] = [];
    
    function traverse(nodes: TreeNode[]) {
      nodes.forEach(node => {
        keys.push(node.id);
        if (node.children && node.children.length > 0) {
          traverse(node.children);
        }
      });
    }
    
    traverse(nodes);
    return keys;
  }

  // ノードを平坦化
  const flattenedNodes = useMemo(() => {
    const flattened: Array<TreeNode & { level: number; pos: string; parentKey?: string }> = [];
    
    function traverse(nodes: TreeNode[], level: number = 0, parentKey?: string, pos: string = '0') {
      nodes.forEach((node, index) => {
        const currentPos = `${pos}-${index}`;
        const nodeWithMeta = {
          ...node,
          level,
          pos: currentPos,
          parentKey,
        };
        
        flattened.push(nodeWithMeta);
        
        if (node.children && expandedKeys.includes(node.id)) {
          traverse(node.children, level + 1, node.id, currentPos);
        }
      });
    }
    
    traverse(treeData);
    return flattened;
  }, [treeData, expandedKeys]);

  // フィルタリングされたノード
  const filteredNodes = useMemo(() => {
    if (!searchValue && !filterTreeNode) {
      return flattenedNodes;
    }

    return flattenedNodes.filter(node => {
      if (filterTreeNode) {
        return filterTreeNode(node);
      }
      
      if (searchValue) {
        return node.title.toLowerCase().includes(searchValue.toLowerCase());
      }
      
      return true;
    });
  }, [flattenedNodes, searchValue, filterTreeNode]);

  // 展開処理
  const handleExpand = useCallback((expanded: boolean, node: TreeNode) => {
    const newExpandedKeys = expanded
      ? [...expandedKeys, node.id]
      : expandedKeys.filter(key => key !== node.id);

    if (!controlledExpandedKeys) {
      setInternalExpandedKeys(newExpandedKeys);
    }

    // 遅延読み込み処理
    if (expanded && loadData && node.children?.length === 0) {
      setLoadingKeys(prev => [...prev, node.id]);
      
      loadData(node).then(() => {
        setLoadingKeys(prev => prev.filter(key => key !== node.id));
      }).catch(error => {
        console.error('Failed to load data:', error);
        setLoadingKeys(prev => prev.filter(key => key !== node.id));
      });
    }

    onExpand?.(newExpandedKeys, { expanded, node });
  }, [expandedKeys, controlledExpandedKeys, loadData, onExpand]);

  // 選択処理
  const handleSelect = useCallback((selected: boolean, node: TreeNode) => {
    let newSelectedKeys: string[];

    if (multiple) {
      if (selected) {
        newSelectedKeys = [...selectedKeys, node.id];
      } else {
        newSelectedKeys = selectedKeys.filter(key => key !== node.id);
      }
    } else {
      newSelectedKeys = selected ? [node.id] : [];
    }

    if (!controlledSelectedKeys) {
      setInternalSelectedKeys(newSelectedKeys);
    }

    onSelect?.(newSelectedKeys, { selected, node });
  }, [selectedKeys, controlledSelectedKeys, multiple, onSelect]);

  // チェック処理
  const handleCheck = useCallback((checked: boolean, node: TreeNode) => {
    let newCheckedKeys = [...checkedKeys];

    if (checkStrictly) {
      // 厳密チェックモード
      if (checked) {
        newCheckedKeys.push(node.id);
      } else {
        newCheckedKeys = newCheckedKeys.filter(key => key !== node.id);
      }
    } else {
      // 親子連動チェックモード
      const updateCheckedKeys = (nodeId: string, isChecked: boolean, nodes: TreeNode[]) => {
        for (const n of nodes) {
          if (n.id === nodeId) {
            if (isChecked) {
              // 子要素もすべてチェック
              const addChildrenKeys = (children?: TreeNode[]) => {
                children?.forEach(child => {
                  if (!newCheckedKeys.includes(child.id)) {
                    newCheckedKeys.push(child.id);
                  }
                  addChildrenKeys(child.children);
                });
              };
              
              if (!newCheckedKeys.includes(nodeId)) {
                newCheckedKeys.push(nodeId);
              }
              addChildrenKeys(n.children);
            } else {
              // 子要素もすべてチェック解除
              const removeChildrenKeys = (children?: TreeNode[]) => {
                children?.forEach(child => {
                  newCheckedKeys = newCheckedKeys.filter(key => key !== child.id);
                  removeChildrenKeys(child.children);
                });
              };
              
              newCheckedKeys = newCheckedKeys.filter(key => key !== nodeId);
              removeChildrenKeys(n.children);
            }
            break;
          }
          
          if (n.children) {
            updateCheckedKeys(nodeId, isChecked, n.children);
          }
        }
      };

      updateCheckedKeys(node.id, checked, treeData);
    }

    if (!controlledCheckedKeys) {
      setInternalCheckedKeys(newCheckedKeys);
    }

    onCheck?.(newCheckedKeys, { checked, node });
  }, [checkedKeys, controlledCheckedKeys, checkStrictly, treeData, onCheck]);

  // ドラッグ&ドロップ処理
  const handleDragStart = useCallback((event: React.DragEvent, node: TreeNode) => {
    onDragStart?.({ event, node });
  }, [onDragStart]);

  const handleDragEnter = useCallback((event: React.DragEvent, node: TreeNode) => {
    setDragOverKey(node.id);
    onDragEnter?.({ event, node });
  }, [onDragEnter]);

  const handleDragOver = useCallback((event: React.DragEvent, node: TreeNode) => {
    event.preventDefault();
    
    const rect = (event.currentTarget as HTMLElement).getBoundingClientRect();
    const y = event.clientY - rect.top;
    const height = rect.height;
    
    const gap = height * 0.25;
    
    if (y < gap) {
      setDragOverGap({ key: node.id, top: true, bottom: false });
    } else if (y > height - gap) {
      setDragOverGap({ key: node.id, top: false, bottom: true });
    } else {
      setDragOverGap(null);
    }
    
    onDragOver?.({ event, node });
  }, [onDragOver]);

  const handleDragLeave = useCallback((event: React.DragEvent, node: TreeNode) => {
    const rect = (event.currentTarget as HTMLElement).getBoundingClientRect();
    const { clientX, clientY } = event;
    
    if (
      clientX < rect.left ||
      clientX > rect.right ||
      clientY < rect.top ||
      clientY > rect.bottom
    ) {
      setDragOverKey(null);
      setDragOverGap(null);
    }
    
    onDragLeave?.({ event, node });
  }, [onDragLeave]);

  const handleDragEnd = useCallback((event: React.DragEvent, node: TreeNode) => {
    setDragOverKey(null);
    setDragOverGap(null);
    onDragEnd?.({ event, node });
  }, [onDragEnd]);

  const handleDrop = useCallback((event: React.DragEvent, node: TreeNode) => {
    event.preventDefault();
    
    const dragNodeId = event.dataTransfer.getData('text/plain');
    const dragNode = flattenedNodes.find(n => n.id === dragNodeId);
    
    if (dragNode && onDrop) {
      const dropPosition = dragOverGap ? (dragOverGap.top ? -1 : 1) : 0;
      
      onDrop({
        event,
        node,
        dragNode,
        dragNodesKeys: [dragNodeId],
        dropPosition,
        dropToGap: !!dragOverGap,
      });
    }
    
    setDragOverKey(null);
    setDragOverGap(null);
  }, [flattenedNodes, dragOverGap, onDrop]);

  // 検索値が変更された時に親ノードを自動展開
  useEffect(() => {
    if (searchValue && autoExpandParent) {
      const keysToExpand = new Set(expandedKeys);
      
      filteredNodes.forEach(node => {
        // 検索にマッチしたノードの親を展開
        let parentKey = node.parentKey;
        while (parentKey) {
          keysToExpand.add(parentKey);
          const parent = flattenedNodes.find(n => n.id === parentKey);
          parentKey = parent?.parentKey;
        }
      });
      
      const newExpandedKeys = Array.from(keysToExpand);
      if (newExpandedKeys.length !== expandedKeys.length || 
          !newExpandedKeys.every(key => expandedKeys.includes(key))) {
        if (!controlledExpandedKeys) {
          setInternalExpandedKeys(newExpandedKeys);
        }
        onExpand?.(newExpandedKeys, { expanded: true, node: treeData[0] });
      }
    }
  }, [searchValue, filteredNodes, flattenedNodes, expandedKeys, controlledExpandedKeys, autoExpandParent, treeData, onExpand]);

  const containerClasses = `
    tree-view select-none
    ${className}
  `;

  const treeClasses = `
    tree-content
    ${height ? 'overflow-y-auto' : ''}
  `;

  return (
    <div 
      className={containerClasses}
      style={{ ...style, height }}
      role="tree"
      aria-multiselectable={multiple}
    >
      <div className={treeClasses} style={{ height }}>
        {filteredNodes.map(node => (
          <TreeNodeComponent
            key={node.id}
            {...node}
            eventKey={node.id}
            expanded={expandedKeys.includes(node.id)}
            selected={selectedKeys.includes(node.id)}
            checked={checkedKeys.includes(node.id)}
            loading={loadingKeys.includes(node.id)}
            dragOver={dragOverKey === node.id}
            dragOverGapTop={dragOverGap?.key === node.id && dragOverGap.top}
            dragOverGapBottom={dragOverGap?.key === node.id && dragOverGap.bottom}
            showLine={showLine}
            showIcon={showIcon}
            checkable={checkable}
            selectable={selectable}
            draggable={draggable}
            disabled={disabled}
            searchValue={searchValue}
            filterTreeNode={filterTreeNode}
            titleRender={titleRender}
            onExpand={handleExpand}
            onSelect={handleSelect}
            onCheck={handleCheck}
            onLoad={onLoad}
            onRightClick={onRightClick}
            onDragStart={handleDragStart}
            onDragEnter={handleDragEnter}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDragEnd={handleDragEnd}
            onDrop={handleDrop}
          />
        ))}
        
        {filteredNodes.length === 0 && (
          <div className="text-center text-gray-500 py-8">
            {searchValue ? '検索結果がありません' : 'データがありません'}
          </div>
        )}
      </div>
    </div>
  );
};