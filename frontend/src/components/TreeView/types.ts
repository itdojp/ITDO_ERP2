import { ReactNode } from 'react';

export interface TreeNode {
  id: string;
  title: string;
  key?: string;
  children?: TreeNode[];
  icon?: ReactNode;
  disabled?: boolean;
  selectable?: boolean;
  checkable?: boolean;
  disableCheckbox?: boolean;
  data?: any;
  className?: string;
  style?: React.CSSProperties;
  isLeaf?: boolean;
}

export interface TreeViewProps {
  treeData: TreeNode[];
  expandedKeys?: string[];
  selectedKeys?: string[];
  checkedKeys?: string[];
  loadedKeys?: string[];
  defaultExpandedKeys?: string[];
  defaultSelectedKeys?: string[];
  defaultCheckedKeys?: string[];
  defaultExpandAll?: boolean;
  autoExpandParent?: boolean;
  checkable?: boolean;
  checkStrictly?: boolean;
  selectable?: boolean;
  multiple?: boolean;
  disabled?: boolean;
  showIcon?: boolean;
  showLine?: boolean;
  onExpand?: (expandedKeys: string[], info: { expanded: boolean; node: TreeNode }) => void;
  onSelect?: (selectedKeys: string[], info: { selected: boolean; node: TreeNode }) => void;
  onCheck?: (checkedKeys: string[], info: { checked: boolean; node: TreeNode }) => void;
  onLoad?: (loadedKeys: string[], info: { node: TreeNode }) => Promise<void>;
  loadData?: (node: TreeNode) => Promise<void>;
  onRightClick?: (info: { event: React.MouseEvent; node: TreeNode }) => void;
  onDragStart?: (info: { event: React.DragEvent; node: TreeNode }) => void;
  onDragEnter?: (info: { event: React.DragEvent; node: TreeNode }) => void;
  onDragOver?: (info: { event: React.DragEvent; node: TreeNode }) => void;
  onDragLeave?: (info: { event: React.DragEvent; node: TreeNode }) => void;
  onDragEnd?: (info: { event: React.DragEvent; node: TreeNode }) => void;
  onDrop?: (info: { 
    event: React.DragEvent; 
    node: TreeNode; 
    dragNode: TreeNode; 
    dragNodesKeys: string[];
    dropPosition: number;
    dropToGap: boolean;
  }) => void;
  draggable?: boolean;
  allowDrop?: (info: { dropNode: TreeNode; dragNode: TreeNode; dropPosition: number }) => boolean;
  titleRender?: (node: TreeNode) => ReactNode;
  className?: string;
  style?: React.CSSProperties;
  height?: number;
  itemHeight?: number;
  virtual?: boolean;
  searchValue?: string;
  filterTreeNode?: (node: TreeNode) => boolean;
  treeNodeFilterProp?: string;
}

export interface TreeNodeProps extends TreeNode {
  level: number;
  expanded?: boolean;
  selected?: boolean;
  checked?: boolean;
  halfChecked?: boolean;
  loading?: boolean;
  dragOver?: boolean;
  dragOverGapTop?: boolean;
  dragOverGapBottom?: boolean;
  pos: string;
  eventKey: string;
  onExpand?: (expanded: boolean, node: TreeNode) => void;
  onSelect?: (selected: boolean, node: TreeNode) => void;
  onCheck?: (checked: boolean, node: TreeNode) => void;
  onLoad?: (node: TreeNode) => void;
  onRightClick?: (event: React.MouseEvent, node: TreeNode) => void;
  onDragStart?: (event: React.DragEvent, node: TreeNode) => void;
  onDragEnter?: (event: React.DragEvent, node: TreeNode) => void;
  onDragOver?: (event: React.DragEvent, node: TreeNode) => void;
  onDragLeave?: (event: React.DragEvent, node: TreeNode) => void;
  onDragEnd?: (event: React.DragEvent, node: TreeNode) => void;
  onDrop?: (event: React.DragEvent, node: TreeNode) => void;
  titleRender?: (node: TreeNode) => ReactNode;
  showLine?: boolean;
  showIcon?: boolean;
  checkable?: boolean;
  selectable?: boolean;
  draggable?: boolean;
  disabled?: boolean;
  searchValue?: string;
  filterTreeNode?: (node: TreeNode) => boolean;
}

export interface TreeSelectProps {
  value?: string | string[];
  defaultValue?: string | string[];
  placeholder?: string;
  disabled?: boolean;
  allowClear?: boolean;
  multiple?: boolean;
  treeData: TreeNode[];
  treeCheckable?: boolean;
  showCheckedStrategy?: 'SHOW_ALL' | 'SHOW_PARENT' | 'SHOW_CHILD';
  treeDefaultExpandAll?: boolean;
  treeDefaultExpandedKeys?: string[];
  dropdownStyle?: React.CSSProperties;
  onChange?: (value: string | string[], label?: any, extra?: any) => void;
  onSelect?: (value: string, node: TreeNode) => void;
  onTreeExpand?: (expandedKeys: string[]) => void;
  searchValue?: string;
  onSearch?: (value: string) => void;
  filterTreeNode?: (inputValue: string, treeNode: TreeNode) => boolean;
  notFoundContent?: ReactNode;
  className?: string;
  style?: React.CSSProperties;
}