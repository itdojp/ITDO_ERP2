import React, { useState, useRef, useCallback, useEffect, useMemo } from 'react';
import { cn } from '@/lib/utils';

export interface WorkflowNode {
  id: string;
  type: 'start' | 'end' | 'task' | 'decision' | 'parallel' | 'merge' | 'delay' | 'webhook' | 'email' | 'approval' | 'custom';
  label: string;
  description?: string;
  position: { x: number; y: number };
  data?: Record<string, any>;
  config?: {
    timeout?: number;
    retries?: number;
    conditions?: Array<{ field: string; operator: string; value: any }>;
    assignees?: string[];
    template?: string;
    url?: string;
    method?: 'GET' | 'POST' | 'PUT' | 'DELETE';
    headers?: Record<string, string>;
    body?: any;
  };
  status?: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';
  inputs?: Array<{ name: string; type: string; required?: boolean; default?: any }>;
  outputs?: Array<{ name: string; type: string; description?: string }>;
  icon?: React.ReactNode;
  color?: string;
  width?: number;
  height?: number;
  resizable?: boolean;
  deletable?: boolean;
  copyable?: boolean;
}

export interface WorkflowConnection {
  id: string;
  sourceNodeId: string;
  targetNodeId: string;
  sourceHandle?: string;
  targetHandle?: string;
  label?: string;
  condition?: string;
  animated?: boolean;
  style?: React.CSSProperties;
  data?: Record<string, any>;
}

export interface WorkflowVariable {
  id: string;
  name: string;
  type: 'string' | 'number' | 'boolean' | 'object' | 'array';
  value: any;
  description?: string;
  scope: 'global' | 'local';
}

export interface WorkflowTrigger {
  id: string;
  type: 'manual' | 'schedule' | 'webhook' | 'event' | 'file' | 'email';
  name: string;
  config: Record<string, any>;
  enabled: boolean;
}

export interface WorkflowTemplate {
  id: string;
  name: string;
  description?: string;
  category: string;
  nodes: WorkflowNode[];
  connections: WorkflowConnection[];
  variables?: WorkflowVariable[];
  triggers?: WorkflowTrigger[];
  tags?: string[];
  version?: string;
  author?: string;
}

export interface WorkflowExecution {
  id: string;
  workflowId: string;
  status: 'running' | 'completed' | 'failed' | 'cancelled';
  startTime: Date;
  endTime?: Date;
  triggeredBy: string;
  context: Record<string, any>;
  logs: Array<{
    timestamp: Date;
    nodeId: string;
    level: 'info' | 'warn' | 'error';
    message: string;
    data?: any;
  }>;
}

export interface WorkflowEditorProps {
  nodes: WorkflowNode[];
  connections: WorkflowConnection[];
  variables?: WorkflowVariable[];
  triggers?: WorkflowTrigger[];
  templates?: WorkflowTemplate[];
  executions?: WorkflowExecution[];
  selectedNodeId?: string;
  selectedConnectionId?: string;
  mode?: 'edit' | 'view' | 'debug';
  theme?: 'light' | 'dark';
  gridEnabled?: boolean;
  gridSize?: number;
  snapToGrid?: boolean;
  minimap?: boolean;
  controls?: boolean;
  toolbar?: boolean;
  nodeTypes?: Record<string, React.ComponentType<any>>;
  connectionTypes?: Record<string, any>;
  validators?: Array<(workflow: { nodes: WorkflowNode[]; connections: WorkflowConnection[] }) => string[]>;
  autoSave?: boolean;
  collaborative?: boolean;
  version?: string;
  readonly?: boolean;
  zoom?: number;
  maxZoom?: number;
  minZoom?: number;
  fitView?: boolean;
  width?: number | string;
  height?: number | string;
  className?: string;
  style?: React.CSSProperties;
  onNodesChange?: (nodes: WorkflowNode[]) => void;
  onConnectionsChange?: (connections: WorkflowConnection[]) => void;
  onNodeSelect?: (nodeId: string | null) => void;
  onConnectionSelect?: (connectionId: string | null) => void;
  onNodeAdd?: (node: WorkflowNode) => void;
  onNodeDelete?: (nodeId: string) => void;
  onNodeUpdate?: (nodeId: string, updates: Partial<WorkflowNode>) => void;
  onConnectionAdd?: (connection: WorkflowConnection) => void;
  onConnectionDelete?: (connectionId: string) => void;
  onVariableAdd?: (variable: WorkflowVariable) => void;
  onVariableUpdate?: (variableId: string, updates: Partial<WorkflowVariable>) => void;
  onVariableDelete?: (variableId: string) => void;
  onTriggerAdd?: (trigger: WorkflowTrigger) => void;
  onTriggerUpdate?: (triggerId: string, updates: Partial<WorkflowTrigger>) => void;
  onTriggerDelete?: (triggerId: string) => void;
  onWorkflowSave?: (workflow: { nodes: WorkflowNode[]; connections: WorkflowConnection[]; variables?: WorkflowVariable[]; triggers?: WorkflowTrigger[] }) => void;
  onWorkflowLoad?: (template: WorkflowTemplate) => void;
  onWorkflowExecute?: (context?: Record<string, any>) => void;
  onWorkflowValidate?: (errors: string[]) => void;
  onZoomChange?: (zoom: number) => void;
  onError?: (error: Error) => void;
  'data-testid'?: string;
}

export const WorkflowEditor: React.FC<WorkflowEditorProps> = ({
  nodes,
  connections,
  variables = [],
  triggers = [],
  templates = [],
  executions = [],
  selectedNodeId,
  selectedConnectionId,
  mode = 'edit',
  theme = 'light',
  gridEnabled = true,
  gridSize = 20,
  snapToGrid = true,
  minimap = true,
  controls = true,
  toolbar = true,
  nodeTypes = {},
  connectionTypes = {},
  validators = [],
  autoSave = false,
  collaborative = false,
  version = '1.0.0',
  readonly = false,
  zoom = 1,
  maxZoom = 3,
  minZoom = 0.1,
  fitView = false,
  width = '100%',
  height = 600,
  className,
  style,
  onNodesChange,
  onConnectionsChange,
  onNodeSelect,
  onConnectionSelect,
  onNodeAdd,
  onNodeDelete,
  onNodeUpdate,
  onConnectionAdd,
  onConnectionDelete,
  onVariableAdd,
  onVariableUpdate,
  onVariableDelete,
  onTriggerAdd,
  onTriggerUpdate,
  onTriggerDelete,
  onWorkflowSave,
  onWorkflowLoad,
  onWorkflowExecute,
  onWorkflowValidate,
  onZoomChange,
  onError,
  'data-testid': dataTestId = 'workflow-editor'
}) => {
  const [internalNodes, setInternalNodes] = useState<WorkflowNode[]>(nodes);
  const [internalConnections, setInternalConnections] = useState<WorkflowConnection[]>(connections);
  const [internalSelectedNodeId, setInternalSelectedNodeId] = useState<string | null>(selectedNodeId || null);
  const [internalSelectedConnectionId, setInternalSelectedConnectionId] = useState<string | null>(selectedConnectionId || null);
  const [internalZoom, setInternalZoom] = useState(zoom);
  const [panOffset, setPanOffset] = useState({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = useState(false);
  const [draggedNode, setDraggedNode] = useState<string | null>(null);
  const [isConnecting, setIsConnecting] = useState(false);
  const [connectionStart, setConnectionStart] = useState<{ nodeId: string; handle?: string } | null>(null);
  const [hoveredNode, setHoveredNode] = useState<string | null>(null);
  const [contextMenu, setContextMenu] = useState<{ x: number; y: number; nodeId?: string; connectionId?: string; visible: boolean }>({ x: 0, y: 0, visible: false });
  const [validationErrors, setValidationErrors] = useState<string[]>([]);
  const [isExecuting, setIsExecuting] = useState(false);
  const [executionProgress, setExecutionProgress] = useState<Record<string, 'pending' | 'running' | 'completed' | 'failed'>>({});

  const editorRef = useRef<HTMLDivElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const dragRef = useRef<{ startX: number; startY: number; nodeId: string | null }>({ startX: 0, startY: 0, nodeId: null });
  const autoSaveRef = useRef<NodeJS.Timeout | null>(null);

  // Node type configurations
  const nodeTypeConfigs = {
    start: { color: '#10B981', icon: '▶', width: 120, height: 60 },
    end: { color: '#EF4444', icon: '⏹', width: 120, height: 60 },
    task: { color: '#3B82F6', icon: '📋', width: 140, height: 80 },
    decision: { color: '#F59E0B', icon: '❓', width: 120, height: 80 },
    parallel: { color: '#8B5CF6', icon: '⚡', width: 130, height: 70 },
    merge: { color: '#06B6D4', icon: '🔗', width: 130, height: 70 },
    delay: { color: '#84CC16', icon: '⏱', width: 120, height: 70 },
    webhook: { color: '#F97316', icon: '🔗', width: 140, height: 80 },
    email: { color: '#EC4899', icon: '📧', width: 130, height: 80 },
    approval: { color: '#6366F1', icon: '✓', width: 140, height: 80 },
    custom: { color: '#6B7280', icon: '⚙', width: 140, height: 80 }
  };

  // Grid pattern
  const gridPattern = useMemo(() => {
    if (!gridEnabled) return '';
    
    const pattern = `
      <pattern id="grid" width="${gridSize}" height="${gridSize}" patternUnits="userSpaceOnUse">
        <path d="M ${gridSize} 0 L 0 0 0 ${gridSize}" fill="none" stroke="${theme === 'dark' ? '#374151' : '#E5E7EB'}" stroke-width="1"/>
      </pattern>
    `;
    
    return pattern;
  }, [gridEnabled, gridSize, theme]);

  // Snap position to grid
  const snapToGridPosition = useCallback((x: number, y: number) => {
    if (!snapToGrid) return { x, y };
    
    return {
      x: Math.round(x / gridSize) * gridSize,
      y: Math.round(y / gridSize) * gridSize
    };
  }, [snapToGrid, gridSize]);

  // Get node bounds
  const getNodeBounds = useCallback((node: WorkflowNode) => {
    const config = nodeTypeConfigs[node.type] || nodeTypeConfigs.custom;
    const width = node.width || config.width;
    const height = node.height || config.height;
    
    return {
      x: node.position.x,
      y: node.position.y,
      width,
      height,
      centerX: node.position.x + width / 2,
      centerY: node.position.y + height / 2
    };
  }, []);

  // Validate workflow
  const validateWorkflow = useCallback(() => {
    const errors: string[] = [];
    
    // Check for start node
    const startNodes = internalNodes.filter(node => node.type === 'start');
    if (startNodes.length === 0) {
      errors.push('Workflow must have at least one start node');
    } else if (startNodes.length > 1) {
      errors.push('Workflow cannot have multiple start nodes');
    }
    
    // Check for end node
    const endNodes = internalNodes.filter(node => node.type === 'end');
    if (endNodes.length === 0) {
      errors.push('Workflow must have at least one end node');
    }
    
    // Check for orphaned nodes
    const connectedNodeIds = new Set([
      ...internalConnections.map(c => c.sourceNodeId),
      ...internalConnections.map(c => c.targetNodeId)
    ]);
    
    const orphanedNodes = internalNodes.filter(node => 
      node.type !== 'start' && !connectedNodeIds.has(node.id)
    );
    
    if (orphanedNodes.length > 0) {
      errors.push(`Found ${orphanedNodes.length} orphaned node(s): ${orphanedNodes.map(n => n.label).join(', ')}`);
    }
    
    // Check for circular dependencies
    const visited = new Set<string>();
    const recursionStack = new Set<string>();
    
    const hasCycle = (nodeId: string): boolean => {
      if (recursionStack.has(nodeId)) return true;
      if (visited.has(nodeId)) return false;
      
      visited.add(nodeId);
      recursionStack.add(nodeId);
      
      const outgoingConnections = internalConnections.filter(c => c.sourceNodeId === nodeId);
      for (const connection of outgoingConnections) {
        if (hasCycle(connection.targetNodeId)) return true;
      }
      
      recursionStack.delete(nodeId);
      return false;
    };
    
    for (const node of internalNodes) {
      if (hasCycle(node.id)) {
        errors.push('Workflow contains circular dependencies');
        break;
      }
    }
    
    // Run custom validators
    for (const validator of validators) {
      try {
        const validatorErrors = validator({ nodes: internalNodes, connections: internalConnections });
        errors.push(...validatorErrors);
      } catch (error) {
        console.error('Validator error:', error);
      }
    }
    
    setValidationErrors(errors);
    onWorkflowValidate?.(errors);
    
    return errors.length === 0;
  }, [internalNodes, internalConnections, validators, onWorkflowValidate]);

  // Handle node drag
  const handleNodeDragStart = useCallback((e: React.MouseEvent, nodeId: string) => {
    if (readonly) return;
    
    e.preventDefault();
    setDraggedNode(nodeId);
    setIsDragging(true);
    
    const rect = editorRef.current?.getBoundingClientRect();
    if (rect) {
      dragRef.current = {
        startX: e.clientX - rect.left,
        startY: e.clientY - rect.top,
        nodeId
      };
    }
  }, [readonly]);

  const handleNodeDrag = useCallback((e: MouseEvent) => {
    if (!isDragging || !draggedNode) return;
    
    const rect = editorRef.current?.getBoundingClientRect();
    if (!rect) return;
    
    const currentX = e.clientX - rect.left;
    const currentY = e.clientY - rect.top;
    
    const deltaX = (currentX - dragRef.current.startX) / internalZoom;
    const deltaY = (currentY - dragRef.current.startY) / internalZoom;
    
    const node = internalNodes.find(n => n.id === draggedNode);
    if (!node) return;
    
    const newPosition = snapToGridPosition(
      node.position.x + deltaX,
      node.position.y + deltaY
    );
    
    const updatedNodes = internalNodes.map(n =>
      n.id === draggedNode
        ? { ...n, position: newPosition }
        : n
    );
    
    setInternalNodes(updatedNodes);
    onNodesChange?.(updatedNodes);
    
    dragRef.current.startX = currentX;
    dragRef.current.startY = currentY;
  }, [isDragging, draggedNode, internalNodes, internalZoom, snapToGridPosition, onNodesChange]);

  const handleNodeDragEnd = useCallback(() => {
    setIsDragging(false);
    setDraggedNode(null);
    dragRef.current = { startX: 0, startY: 0, nodeId: null };
  }, []);

  // Handle connection creation
  const handleConnectionStart = useCallback((nodeId: string, handle?: string) => {
    if (readonly) return;
    
    setIsConnecting(true);
    setConnectionStart({ nodeId, handle });
  }, [readonly]);

  const handleConnectionEnd = useCallback((targetNodeId: string, targetHandle?: string) => {
    if (!isConnecting || !connectionStart || connectionStart.nodeId === targetNodeId) {
      setIsConnecting(false);
      setConnectionStart(null);
      return;
    }
    
    const newConnection: WorkflowConnection = {
      id: `connection-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      sourceNodeId: connectionStart.nodeId,
      targetNodeId,
      sourceHandle: connectionStart.handle,
      targetHandle
    };
    
    const updatedConnections = [...internalConnections, newConnection];
    setInternalConnections(updatedConnections);
    onConnectionsChange?.(updatedConnections);
    onConnectionAdd?.(newConnection);
    
    setIsConnecting(false);
    setConnectionStart(null);
  }, [isConnecting, connectionStart, internalConnections, onConnectionsChange, onConnectionAdd]);

  // Handle node selection
  const handleNodeSelect = useCallback((nodeId: string | null) => {
    setInternalSelectedNodeId(nodeId);
    setInternalSelectedConnectionId(null);
    onNodeSelect?.(nodeId);
  }, [onNodeSelect]);

  // Handle connection selection
  const handleConnectionSelect = useCallback((connectionId: string | null) => {
    setInternalSelectedConnectionId(connectionId);
    setInternalSelectedNodeId(null);
    onConnectionSelect?.(connectionId);
  }, [onConnectionSelect]);

  // Handle zoom
  const handleZoom = useCallback((delta: number, centerX?: number, centerY?: number) => {
    const newZoom = Math.max(minZoom, Math.min(maxZoom, internalZoom + delta));
    setInternalZoom(newZoom);
    onZoomChange?.(newZoom);
  }, [internalZoom, minZoom, maxZoom, onZoomChange]);

  // Handle context menu
  const handleContextMenu = useCallback((e: React.MouseEvent, nodeId?: string, connectionId?: string) => {
    e.preventDefault();
    setContextMenu({
      x: e.clientX,
      y: e.clientY,
      nodeId,
      connectionId,
      visible: true
    });
  }, []);

  // Execute workflow
  const handleWorkflowExecute = useCallback(async (context: Record<string, any> = {}) => {
    if (readonly || !validateWorkflow()) return;
    
    setIsExecuting(true);
    setExecutionProgress({});
    
    try {
      // Simulate workflow execution
      const startNode = internalNodes.find(n => n.type === 'start');
      if (!startNode) throw new Error('No start node found');
      
      const executeNode = async (nodeId: string): Promise<void> => {
        setExecutionProgress(prev => ({ ...prev, [nodeId]: 'running' }));
        
        // Simulate processing time
        await new Promise(resolve => setTimeout(resolve, Math.random() * 2000 + 500));
        
        const node = internalNodes.find(n => n.id === nodeId);
        if (!node) throw new Error(`Node ${nodeId} not found`);
        
        // Simulate success/failure based on node type
        const shouldFail = Math.random() < 0.1; // 10% failure rate
        
        if (shouldFail) {
          setExecutionProgress(prev => ({ ...prev, [nodeId]: 'failed' }));
          throw new Error(`Node ${node.label} execution failed`);
        } else {
          setExecutionProgress(prev => ({ ...prev, [nodeId]: 'completed' }));
        }
        
        // Execute connected nodes
        const outgoingConnections = internalConnections.filter(c => c.sourceNodeId === nodeId);
        for (const connection of outgoingConnections) {
          await executeNode(connection.targetNodeId);
        }
      };
      
      await executeNode(startNode.id);
      
    } catch (error) {
      console.error('Workflow execution failed:', error);
      onError?.(error as Error);
    } finally {
      setIsExecuting(false);
    }
    
    onWorkflowExecute?.(context);
  }, [readonly, validateWorkflow, internalNodes, internalConnections, onWorkflowExecute, onError]);

  // Auto-save functionality
  useEffect(() => {
    if (autoSave && !readonly) {
      if (autoSaveRef.current) {
        clearTimeout(autoSaveRef.current);
      }
      
      autoSaveRef.current = setTimeout(() => {
        onWorkflowSave?.({
          nodes: internalNodes,
          connections: internalConnections,
          variables,
          triggers
        });
      }, 2000);
      
      return () => {
        if (autoSaveRef.current) {
          clearTimeout(autoSaveRef.current);
        }
      };
    }
  }, [internalNodes, internalConnections, variables, triggers, autoSave, readonly, onWorkflowSave]);

  // Mouse event handlers
  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      handleNodeDrag(e);
    };
    
    const handleMouseUp = () => {
      handleNodeDragEnd();
    };
    
    if (isDragging) {
      document.addEventListener('mousemove', handleMouseMove);
      document.addEventListener('mouseup', handleMouseUp);
      
      return () => {
        document.removeEventListener('mousemove', handleMouseMove);
        document.removeEventListener('mouseup', handleMouseUp);
      };
    }
  }, [isDragging, handleNodeDrag, handleNodeDragEnd]);

  // Click outside handler
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (editorRef.current && !editorRef.current.contains(event.target as Node)) {
        setContextMenu({ ...contextMenu, visible: false });
        setInternalSelectedNodeId(null);
        setInternalSelectedConnectionId(null);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [contextMenu]);

  // Validate on changes
  useEffect(() => {
    validateWorkflow();
  }, [validateWorkflow]);

  // Render toolbar
  const renderToolbar = () => {
    if (!toolbar) return null;
    
    return (
      <div className="flex items-center justify-between p-2 border-b bg-gray-50" data-testid="workflow-toolbar">
        <div className="flex items-center space-x-2">
          <button
            className="px-3 py-1 text-sm bg-blue-500 text-white rounded hover:bg-blue-600 disabled:opacity-50"
            onClick={() => handleWorkflowExecute()}
            disabled={readonly || isExecuting || validationErrors.length > 0}
            data-testid="execute-workflow"
          >
            {isExecuting ? 'Executing...' : 'Execute'}
          </button>
          
          <button
            className="px-3 py-1 text-sm bg-green-500 text-white rounded hover:bg-green-600 disabled:opacity-50"
            onClick={() => onWorkflowSave?.({ nodes: internalNodes, connections: internalConnections, variables, triggers })}
            disabled={readonly}
            data-testid="save-workflow"
          >
            Save
          </button>
          
          <button
            className="px-3 py-1 text-sm bg-gray-500 text-white rounded hover:bg-gray-600"
            onClick={() => validateWorkflow()}
            data-testid="validate-workflow"
          >
            Validate
          </button>
        </div>
        
        <div className="flex items-center space-x-2">
          <div className="text-xs text-gray-500">
            {internalNodes.length} nodes, {internalConnections.length} connections
          </div>
          
          {validationErrors.length > 0 && (
            <div className="text-xs text-red-500" data-testid="validation-errors">
              {validationErrors.length} error{validationErrors.length !== 1 ? 's' : ''}
            </div>
          )}
          
          <div className="text-xs text-gray-500">
            Zoom: {Math.round(internalZoom * 100)}%
          </div>
        </div>
      </div>
    );
  };

  // Render node
  const renderNode = (node: WorkflowNode) => {
    const config = nodeTypeConfigs[node.type] || nodeTypeConfigs.custom;
    const bounds = getNodeBounds(node);
    const isSelected = internalSelectedNodeId === node.id;
    const isHovered = hoveredNode === node.id;
    const executionStatus = executionProgress[node.id];
    
    return (
      <div
        key={node.id}
        className={cn(
          "absolute border-2 rounded-lg cursor-pointer transition-all duration-200",
          isSelected && "border-blue-500 shadow-lg",
          isHovered && "shadow-md",
          executionStatus === 'running' && "animate-pulse border-yellow-500",
          executionStatus === 'completed' && "border-green-500",
          executionStatus === 'failed' && "border-red-500",
          readonly && "cursor-default"
        )}
        style={{
          left: bounds.x,
          top: bounds.y,
          width: bounds.width,
          height: bounds.height,
          backgroundColor: node.color || config.color,
          transform: `scale(${internalZoom})`,
          transformOrigin: 'top left'
        }}
        onMouseDown={(e) => handleNodeDragStart(e, node.id)}
        onClick={() => handleNodeSelect(node.id)}
        onMouseEnter={() => setHoveredNode(node.id)}
        onMouseLeave={() => setHoveredNode(null)}
        onContextMenu={(e) => handleContextMenu(e, node.id)}
        data-testid={`workflow-node-${node.id}`}
      >
        <div className="flex flex-col items-center justify-center h-full p-2 text-white">
          <div className="text-lg mb-1">{node.icon || config.icon}</div>
          <div className="text-xs font-medium text-center">{node.label}</div>
          {node.description && (
            <div className="text-xs opacity-75 text-center mt-1">{node.description}</div>
          )}
        </div>
        
        {/* Connection handles */}
        <div
          className="absolute -top-2 left-1/2 transform -translate-x-1/2 w-4 h-4 bg-white border-2 border-gray-400 rounded-full cursor-crosshair"
          onClick={(e) => {
            e.stopPropagation();
            if (isConnecting) {
              handleConnectionEnd(node.id, 'top');
            } else {
              handleConnectionStart(node.id, 'top');
            }
          }}
          data-testid={`node-handle-top-${node.id}`}
        />
        <div
          className="absolute -bottom-2 left-1/2 transform -translate-x-1/2 w-4 h-4 bg-white border-2 border-gray-400 rounded-full cursor-crosshair"
          onClick={(e) => {
            e.stopPropagation();
            if (isConnecting) {
              handleConnectionEnd(node.id, 'bottom');
            } else {
              handleConnectionStart(node.id, 'bottom');
            }
          }}
          data-testid={`node-handle-bottom-${node.id}`}
        />
        <div
          className="absolute -left-2 top-1/2 transform -translate-y-1/2 w-4 h-4 bg-white border-2 border-gray-400 rounded-full cursor-crosshair"
          onClick={(e) => {
            e.stopPropagation();
            if (isConnecting) {
              handleConnectionEnd(node.id, 'left');
            } else {
              handleConnectionStart(node.id, 'left');
            }
          }}
          data-testid={`node-handle-left-${node.id}`}
        />
        <div
          className="absolute -right-2 top-1/2 transform -translate-y-1/2 w-4 h-4 bg-white border-2 border-gray-400 rounded-full cursor-crosshair"
          onClick={(e) => {
            e.stopPropagation();
            if (isConnecting) {
              handleConnectionEnd(node.id, 'right');
            } else {
              handleConnectionStart(node.id, 'right');
            }
          }}
          data-testid={`node-handle-right-${node.id}`}
        />
      </div>
    );
  };

  // Render connection
  const renderConnection = (connection: WorkflowConnection) => {
    const sourceNode = internalNodes.find(n => n.id === connection.sourceNodeId);
    const targetNode = internalNodes.find(n => n.id === connection.targetNodeId);
    
    if (!sourceNode || !targetNode) return null;
    
    const sourceBounds = getNodeBounds(sourceNode);
    const targetBounds = getNodeBounds(targetNode);
    
    const sourceX = sourceBounds.centerX;
    const sourceY = sourceBounds.centerY;
    const targetX = targetBounds.centerX;
    const targetY = targetBounds.centerY;
    
    const isSelected = internalSelectedConnectionId === connection.id;
    
    return (
      <line
        key={connection.id}
        x1={sourceX}
        y1={sourceY}
        x2={targetX}
        y2={targetY}
        stroke={isSelected ? '#3B82F6' : '#6B7280'}
        strokeWidth={isSelected ? 3 : 2}
        markerEnd="url(#arrowhead)"
        className={cn(
          "cursor-pointer",
          connection.animated && "animate-pulse"
        )}
        onClick={() => handleConnectionSelect(connection.id)}
        onContextMenu={(e) => handleContextMenu(e as any, undefined, connection.id)}
        data-testid={`workflow-connection-${connection.id}`}
      />
    );
  };

  // Render context menu
  const renderContextMenu = () => {
    if (!contextMenu.visible) return null;
    
    return (
      <div
        className="fixed z-50 bg-white border border-gray-200 rounded-md shadow-lg min-w-32"
        style={{ left: contextMenu.x, top: contextMenu.y }}
        data-testid="workflow-context-menu"
      >
        {contextMenu.nodeId && (
          <>
            <button
              className="w-full px-3 py-2 text-left text-sm hover:bg-gray-100"
              onClick={() => {
                onNodeDelete?.(contextMenu.nodeId!);
                setContextMenu({ ...contextMenu, visible: false });
              }}
              data-testid="delete-node"
            >
              Delete Node
            </button>
            <button
              className="w-full px-3 py-2 text-left text-sm hover:bg-gray-100"
              onClick={() => {
                const node = internalNodes.find(n => n.id === contextMenu.nodeId);
                if (node) {
                  const newNode = { ...node, id: `${node.id}-copy`, position: { x: node.position.x + 20, y: node.position.y + 20 } };
                  onNodeAdd?.(newNode);
                }
                setContextMenu({ ...contextMenu, visible: false });
              }}
              data-testid="copy-node"
            >
              Copy Node
            </button>
          </>
        )}
        
        {contextMenu.connectionId && (
          <button
            className="w-full px-3 py-2 text-left text-sm hover:bg-gray-100"
            onClick={() => {
              onConnectionDelete?.(contextMenu.connectionId!);
              setContextMenu({ ...contextMenu, visible: false });
            }}
            data-testid="delete-connection"
          >
            Delete Connection
          </button>
        )}
      </div>
    );
  };

  // Render controls
  const renderControls = () => {
    if (!controls) return null;
    
    return (
      <div className="absolute bottom-4 right-4 flex flex-col space-y-2" data-testid="workflow-controls">
        <button
          className="w-10 h-10 bg-white border border-gray-300 rounded-md shadow-sm hover:bg-gray-50 flex items-center justify-center"
          onClick={() => handleZoom(0.1)}
          data-testid="zoom-in"
        >
          +
        </button>
        <button
          className="w-10 h-10 bg-white border border-gray-300 rounded-md shadow-sm hover:bg-gray-50 flex items-center justify-center"
          onClick={() => handleZoom(-0.1)}
          data-testid="zoom-out"
        >
          −
        </button>
        <button
          className="w-10 h-10 bg-white border border-gray-300 rounded-md shadow-sm hover:bg-gray-50 flex items-center justify-center"
          onClick={() => setInternalZoom(1)}
          data-testid="zoom-reset"
        >
          1:1
        </button>
      </div>
    );
  };

  return (
    <div
      ref={editorRef}
      className={cn(
        "relative overflow-hidden border border-gray-200 rounded-lg",
        theme === 'dark' && "bg-gray-900 border-gray-700",
        className
      )}
      style={{ width, height, ...style }}
      data-testid={dataTestId}
    >
      {renderToolbar()}
      
      <div className="relative w-full h-full">
        <svg
          className="absolute inset-0 w-full h-full pointer-events-none"
          style={{ transform: `translate(${panOffset.x}px, ${panOffset.y}px)` }}
        >
          {gridEnabled && (
            <defs>
              <pattern
                id="grid"
                width={gridSize * internalZoom}
                height={gridSize * internalZoom}
                patternUnits="userSpaceOnUse"
              >
                <path
                  d={`M ${gridSize * internalZoom} 0 L 0 0 0 ${gridSize * internalZoom}`}
                  fill="none"
                  stroke={theme === 'dark' ? '#374151' : '#E5E7EB'}
                  strokeWidth="1"
                />
              </pattern>
              <rect width="100%" height="100%" fill="url(#grid)" />
            </defs>
          )}
          
          <defs>
            <marker
              id="arrowhead"
              markerWidth="10"
              markerHeight="7"
              refX="9"
              refY="3.5"
              orient="auto"
            >
              <polygon
                points="0 0, 10 3.5, 0 7"
                fill="#6B7280"
              />
            </marker>
          </defs>
          
          {internalConnections.map(renderConnection)}
        </svg>
        
        <div
          className="absolute inset-0"
          style={{
            transform: `translate(${panOffset.x}px, ${panOffset.y}px)`,
            transformOrigin: 'top left'
          }}
        >
          {internalNodes.map(renderNode)}
        </div>
        
        {renderControls()}
        {renderContextMenu()}
      </div>
      
      {validationErrors.length > 0 && (
        <div className="absolute top-0 right-0 m-4 max-w-xs" data-testid="validation-error-panel">
          <div className="bg-red-50 border border-red-200 rounded-lg p-3">
            <h4 className="text-sm font-medium text-red-800 mb-2">Validation Errors</h4>
            <ul className="text-xs text-red-600 space-y-1">
              {validationErrors.map((error, index) => (
                <li key={index}>• {error}</li>
              ))}
            </ul>
          </div>
        </div>
      )}
    </div>
  );
};

export default WorkflowEditor;