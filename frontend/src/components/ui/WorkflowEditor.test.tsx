import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { vi } from 'vitest';
import { WorkflowEditor } from './WorkflowEditor';

interface MockNode {
  id: string;
  type: 'start' | 'end' | 'task' | 'decision' | 'parallel' | 'merge' | 'delay' | 'webhook' | 'email' | 'approval' | 'custom';
  label: string;
  description?: string;
  position: { x: number; y: number };
  data?: Record<string, any>;
  status?: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';
}

interface MockConnection {
  id: string;
  sourceNodeId: string;
  targetNodeId: string;
  sourceHandle?: string;
  targetHandle?: string;
  label?: string;
  condition?: string;
  animated?: boolean;
}

describe('WorkflowEditor', () => {
  const mockNodes: MockNode[] = [
    {
      id: 'start-1',
      type: 'start',
      label: 'Start',
      position: { x: 100, y: 100 }
    },
    {
      id: 'task-1',
      type: 'task',
      label: 'Process Data',
      description: 'Process incoming data',
      position: { x: 300, y: 100 }
    },
    {
      id: 'decision-1',
      type: 'decision',
      label: 'Check Status',
      position: { x: 500, y: 100 }
    },
    {
      id: 'end-1',
      type: 'end',
      label: 'End',
      position: { x: 700, y: 100 }
    }
  ];

  const mockConnections: MockConnection[] = [
    {
      id: 'conn-1',
      sourceNodeId: 'start-1',
      targetNodeId: 'task-1'
    },
    {
      id: 'conn-2',
      sourceNodeId: 'task-1',
      targetNodeId: 'decision-1'
    },
    {
      id: 'conn-3',
      sourceNodeId: 'decision-1',
      targetNodeId: 'end-1'
    }
  ];

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders workflow editor with nodes and connections', () => {
    render(<WorkflowEditor nodes={mockNodes} connections={mockConnections} />);
    
    expect(screen.getByTestId('workflow-editor')).toBeInTheDocument();
    expect(screen.getByTestId('workflow-toolbar')).toBeInTheDocument();
    expect(screen.getByTestId('workflow-node-start-1')).toBeInTheDocument();
    expect(screen.getByTestId('workflow-node-task-1')).toBeInTheDocument();
    expect(screen.getByTestId('workflow-node-decision-1')).toBeInTheDocument();
    expect(screen.getByTestId('workflow-node-end-1')).toBeInTheDocument();
  });

  it('supports different node types', () => {
    const nodeTypes: MockNode['type'][] = ['start', 'end', 'task', 'decision', 'parallel', 'merge', 'delay', 'webhook', 'email', 'approval', 'custom'];
    
    const nodes = nodeTypes.map((type, index) => ({
      id: `node-${index}`,
      type,
      label: `${type} node`,
      position: { x: index * 150, y: 100 }
    }));
    
    render(<WorkflowEditor nodes={nodes} connections={[]} />);
    
    nodeTypes.forEach((type, index) => {
      expect(screen.getByTestId(`workflow-node-node-${index}`)).toBeInTheDocument();
    });
  });

  it('supports node selection', () => {
    const onNodeSelect = vi.fn();
    
    render(
      <WorkflowEditor 
        nodes={mockNodes} 
        connections={mockConnections}
        onNodeSelect={onNodeSelect}
      />
    );
    
    const taskNode = screen.getByTestId('workflow-node-task-1');
    fireEvent.click(taskNode);
    
    expect(onNodeSelect).toHaveBeenCalledWith('task-1');
  });

  it('supports node dragging', () => {
    const onNodesChange = vi.fn();
    
    render(
      <WorkflowEditor 
        nodes={mockNodes} 
        connections={mockConnections}
        onNodesChange={onNodesChange}
      />
    );
    
    const taskNode = screen.getByTestId('workflow-node-task-1');
    
    fireEvent.mouseDown(taskNode, { clientX: 300, clientY: 100 });
    fireEvent.mouseMove(document, { clientX: 350, clientY: 150 });
    fireEvent.mouseUp(document);
    
    expect(onNodesChange).toHaveBeenCalled();
  });

  it('supports connection creation', () => {
    const onConnectionAdd = vi.fn();
    
    render(
      <WorkflowEditor 
        nodes={mockNodes} 
        connections={[]}
        onConnectionAdd={onConnectionAdd}
      />
    );
    
    const startHandle = screen.getByTestId('node-handle-bottom-start-1');
    const endHandle = screen.getByTestId('node-handle-top-task-1');
    
    fireEvent.click(startHandle);
    fireEvent.click(endHandle);
    
    expect(onConnectionAdd).toHaveBeenCalledWith(
      expect.objectContaining({
        sourceNodeId: 'start-1',
        targetNodeId: 'task-1'
      })
    );
  });

  it('supports workflow validation', () => {
    const onWorkflowValidate = vi.fn();
    
    // Workflow without end node
    const invalidNodes = mockNodes.filter(n => n.type !== 'end');
    
    render(
      <WorkflowEditor 
        nodes={invalidNodes} 
        connections={mockConnections}
        onWorkflowValidate={onWorkflowValidate}
      />
    );
    
    expect(screen.getByTestId('validation-errors')).toBeInTheDocument();
    expect(screen.getByTestId('validation-error-panel')).toBeInTheDocument();
  });

  it('supports workflow execution', async () => {
    const onWorkflowExecute = vi.fn();
    
    render(
      <WorkflowEditor 
        nodes={mockNodes} 
        connections={mockConnections}
        onWorkflowExecute={onWorkflowExecute}
      />
    );
    
    const executeButton = screen.getByTestId('execute-workflow');
    fireEvent.click(executeButton);
    
    expect(executeButton).toHaveTextContent('Executing...');
    expect(onWorkflowExecute).toHaveBeenCalled();
  });

  it('supports workflow saving', () => {
    const onWorkflowSave = vi.fn();
    
    render(
      <WorkflowEditor 
        nodes={mockNodes} 
        connections={mockConnections}
        onWorkflowSave={onWorkflowSave}
      />
    );
    
    const saveButton = screen.getByTestId('save-workflow');
    fireEvent.click(saveButton);
    
    expect(onWorkflowSave).toHaveBeenCalledWith({
      nodes: mockNodes,
      connections: mockConnections,
      variables: [],
      triggers: []
    });
  });

  it('supports zoom controls', () => {
    const onZoomChange = vi.fn();
    
    render(
      <WorkflowEditor 
        nodes={mockNodes} 
        connections={mockConnections}
        controls
        onZoomChange={onZoomChange}
      />
    );
    
    expect(screen.getByTestId('workflow-controls')).toBeInTheDocument();
    
    const zoomInButton = screen.getByTestId('zoom-in');
    const zoomOutButton = screen.getByTestId('zoom-out');
    const zoomResetButton = screen.getByTestId('zoom-reset');
    
    fireEvent.click(zoomInButton);
    expect(onZoomChange).toHaveBeenCalledWith(1.1);
    
    fireEvent.click(zoomOutButton);
    expect(onZoomChange).toHaveBeenCalledWith(1.0);
    
    fireEvent.click(zoomResetButton);
  });

  it('supports grid functionality', () => {
    render(
      <WorkflowEditor 
        nodes={mockNodes} 
        connections={mockConnections}
        gridEnabled
        snapToGrid
        gridSize={25}
      />
    );
    
    expect(screen.getByTestId('workflow-editor')).toBeInTheDocument();
  });

  it('supports context menu', () => {
    const onNodeDelete = vi.fn();
    const onNodeAdd = vi.fn();
    
    render(
      <WorkflowEditor 
        nodes={mockNodes} 
        connections={mockConnections}
        onNodeDelete={onNodeDelete}
        onNodeAdd={onNodeAdd}
      />
    );
    
    const taskNode = screen.getByTestId('workflow-node-task-1');
    fireEvent.contextMenu(taskNode);
    
    expect(screen.getByTestId('workflow-context-menu')).toBeInTheDocument();
    
    const deleteButton = screen.getByTestId('delete-node');
    fireEvent.click(deleteButton);
    
    expect(onNodeDelete).toHaveBeenCalledWith('task-1');
  });

  it('supports node copying', () => {
    const onNodeAdd = vi.fn();
    
    render(
      <WorkflowEditor 
        nodes={mockNodes} 
        connections={mockConnections}
        onNodeAdd={onNodeAdd}
      />
    );
    
    const taskNode = screen.getByTestId('workflow-node-task-1');
    fireEvent.contextMenu(taskNode);
    
    const copyButton = screen.getByTestId('copy-node');
    fireEvent.click(copyButton);
    
    expect(onNodeAdd).toHaveBeenCalledWith(
      expect.objectContaining({
        id: 'task-1-copy',
        type: 'task',
        label: 'Process Data'
      })
    );
  });

  it('supports connection deletion', () => {
    const onConnectionDelete = vi.fn();
    
    render(
      <WorkflowEditor 
        nodes={mockNodes} 
        connections={mockConnections}
        onConnectionDelete={onConnectionDelete}
      />
    );
    
    const connection = screen.getByTestId('workflow-connection-conn-1');
    fireEvent.contextMenu(connection);
    
    const deleteButton = screen.getByTestId('delete-connection');
    fireEvent.click(deleteButton);
    
    expect(onConnectionDelete).toHaveBeenCalledWith('conn-1');
  });

  it('supports readonly mode', () => {
    render(
      <WorkflowEditor 
        nodes={mockNodes} 
        connections={mockConnections}
        readonly
      />
    );
    
    const executeButton = screen.getByTestId('execute-workflow');
    const saveButton = screen.getByTestId('save-workflow');
    
    expect(executeButton).toBeDisabled();
    expect(saveButton).toBeDisabled();
  });

  it('supports different themes', () => {
    const { rerender } = render(
      <WorkflowEditor nodes={mockNodes} connections={mockConnections} theme="light" />
    );
    
    let editor = screen.getByTestId('workflow-editor');
    expect(editor).not.toHaveClass('bg-gray-900');
    
    rerender(
      <WorkflowEditor nodes={mockNodes} connections={mockConnections} theme="dark" />
    );
    
    editor = screen.getByTestId('workflow-editor');
    expect(editor).toHaveClass('bg-gray-900');
  });

  it('supports custom node types', () => {
    const customNodeTypes = {
      customTask: () => <div>Custom Task</div>
    };
    
    render(
      <WorkflowEditor 
        nodes={mockNodes} 
        connections={mockConnections}
        nodeTypes={customNodeTypes}
      />
    );
    
    expect(screen.getByTestId('workflow-editor')).toBeInTheDocument();
  });

  it('supports workflow validation with custom validators', () => {
    const customValidator = vi.fn(() => ['Custom validation error']);
    
    render(
      <WorkflowEditor 
        nodes={mockNodes} 
        connections={mockConnections}
        validators={[customValidator]}
      />
    );
    
    expect(customValidator).toHaveBeenCalledWith({
      nodes: mockNodes,
      connections: mockConnections
    });
    
    expect(screen.getByText('Custom validation error')).toBeInTheDocument();
  });

  it('detects circular dependencies', () => {
    const circularConnections = [
      { id: 'conn-1', sourceNodeId: 'start-1', targetNodeId: 'task-1' },
      { id: 'conn-2', sourceNodeId: 'task-1', targetNodeId: 'decision-1' },
      { id: 'conn-3', sourceNodeId: 'decision-1', targetNodeId: 'task-1' } // Creates cycle
    ];
    
    render(
      <WorkflowEditor 
        nodes={mockNodes} 
        connections={circularConnections}
      />
    );
    
    expect(screen.getByText('Workflow contains circular dependencies')).toBeInTheDocument();
  });

  it('detects orphaned nodes', () => {
    const orphanedNode = {
      id: 'orphan-1',
      type: 'task' as const,
      label: 'Orphaned Task',
      position: { x: 900, y: 100 }
    };
    
    render(
      <WorkflowEditor 
        nodes={[...mockNodes, orphanedNode]} 
        connections={mockConnections}
      />
    );
    
    expect(screen.getByText(/Found 1 orphaned node/)).toBeInTheDocument();
  });

  it('supports auto-save functionality', async () => {
    const onWorkflowSave = vi.fn();
    
    render(
      <WorkflowEditor 
        nodes={mockNodes} 
        connections={mockConnections}
        autoSave
        onWorkflowSave={onWorkflowSave}
      />
    );
    
    // Auto-save should trigger after changes
    await waitFor(() => {
      expect(onWorkflowSave).toHaveBeenCalled();
    }, { timeout: 3000 });
  });

  it('supports collaborative mode', () => {
    render(
      <WorkflowEditor 
        nodes={mockNodes} 
        connections={mockConnections}
        collaborative
      />
    );
    
    expect(screen.getByTestId('workflow-editor')).toBeInTheDocument();
  });

  it('displays node status during execution', () => {
    const nodesWithStatus = mockNodes.map(node => ({
      ...node,
      status: 'running' as const
    }));
    
    render(
      <WorkflowEditor 
        nodes={nodesWithStatus} 
        connections={mockConnections}
      />
    );
    
    expect(screen.getByTestId('workflow-editor')).toBeInTheDocument();
  });

  it('supports minimap functionality', () => {
    render(
      <WorkflowEditor 
        nodes={mockNodes} 
        connections={mockConnections}
        minimap
      />
    );
    
    expect(screen.getByTestId('workflow-editor')).toBeInTheDocument();
  });

  it('supports variables and triggers', () => {
    const variables = [
      { id: 'var-1', name: 'inputData', type: 'string' as const, value: 'test', scope: 'global' as const }
    ];
    
    const triggers = [
      { id: 'trigger-1', type: 'manual' as const, name: 'Manual Trigger', config: {}, enabled: true }
    ];
    
    render(
      <WorkflowEditor 
        nodes={mockNodes} 
        connections={mockConnections}
        variables={variables}
        triggers={triggers}
      />
    );
    
    expect(screen.getByTestId('workflow-editor')).toBeInTheDocument();
  });

  it('supports workflow templates', () => {
    const templates = [
      {
        id: 'template-1',
        name: 'Basic Workflow',
        category: 'General',
        nodes: mockNodes,
        connections: mockConnections
      }
    ];
    
    render(
      <WorkflowEditor 
        nodes={mockNodes} 
        connections={mockConnections}
        templates={templates}
      />
    );
    
    expect(screen.getByTestId('workflow-editor')).toBeInTheDocument();
  });

  it('supports execution history', () => {
    const executions = [
      {
        id: 'exec-1',
        workflowId: 'workflow-1',
        status: 'completed' as const,
        startTime: new Date(),
        triggeredBy: 'user',
        context: {},
        logs: []
      }
    ];
    
    render(
      <WorkflowEditor 
        nodes={mockNodes} 
        connections={mockConnections}
        executions={executions}
      />
    );
    
    expect(screen.getByTestId('workflow-editor')).toBeInTheDocument();
  });

  it('handles workflow execution errors', async () => {
    const onError = vi.fn();
    
    // Mock execution to fail
    const failingNodes = mockNodes.map(node => ({
      ...node,
      config: { ...node.config, shouldFail: true }
    }));
    
    render(
      <WorkflowEditor 
        nodes={failingNodes} 
        connections={mockConnections}
        onError={onError}
      />
    );
    
    const executeButton = screen.getByTestId('execute-workflow');
    fireEvent.click(executeButton);
    
    // Wait for execution to complete
    await waitFor(() => {
      expect(executeButton).not.toHaveTextContent('Executing...');
    }, { timeout: 3000 });
  });

  it('supports custom styling', () => {
    render(
      <WorkflowEditor 
        nodes={mockNodes} 
        connections={mockConnections}
        className="custom-workflow-editor"
        style={{ border: '2px solid red' }}
      />
    );
    
    const editor = screen.getByTestId('workflow-editor');
    expect(editor).toHaveClass('custom-workflow-editor');
    expect(editor).toHaveStyle('border: 2px solid red');
  });

  it('supports different view modes', () => {
    const modes = ['edit', 'view', 'debug'] as const;
    
    modes.forEach(mode => {
      const { unmount } = render(
        <WorkflowEditor nodes={mockNodes} connections={mockConnections} mode={mode} />
      );
      expect(screen.getByTestId('workflow-editor')).toBeInTheDocument();
      unmount();
    });
  });

  it('supports fit view functionality', () => {
    render(
      <WorkflowEditor 
        nodes={mockNodes} 
        connections={mockConnections}
        fitView
      />
    );
    
    expect(screen.getByTestId('workflow-editor')).toBeInTheDocument();
  });

  it('supports zoom limits', () => {
    render(
      <WorkflowEditor 
        nodes={mockNodes} 
        connections={mockConnections}
        minZoom={0.5}
        maxZoom={2}
        controls
      />
    );
    
    const zoomInButton = screen.getByTestId('zoom-in');
    const zoomOutButton = screen.getByTestId('zoom-out');
    
    // Test zoom limits
    for (let i = 0; i < 20; i++) {
      fireEvent.click(zoomInButton);
    }
    
    for (let i = 0; i < 20; i++) {
      fireEvent.click(zoomOutButton);
    }
    
    expect(screen.getByTestId('workflow-controls')).toBeInTheDocument();
  });

  it('handles click outside to close context menu', () => {
    render(
      <WorkflowEditor 
        nodes={mockNodes} 
        connections={mockConnections}
      />
    );
    
    const taskNode = screen.getByTestId('workflow-node-task-1');
    fireEvent.contextMenu(taskNode);
    
    expect(screen.getByTestId('workflow-context-menu')).toBeInTheDocument();
    
    // Click outside
    fireEvent.mouseDown(document.body);
    
    expect(screen.queryByTestId('workflow-context-menu')).not.toBeInTheDocument();
  });

  it('displays toolbar statistics', () => {
    render(
      <WorkflowEditor 
        nodes={mockNodes} 
        connections={mockConnections}
        toolbar
      />
    );
    
    expect(screen.getByText('4 nodes, 3 connections')).toBeInTheDocument();
    expect(screen.getByText('Zoom: 100%')).toBeInTheDocument();
  });

  it('supports connection selection', () => {
    const onConnectionSelect = vi.fn();
    
    render(
      <WorkflowEditor 
        nodes={mockNodes} 
        connections={mockConnections}
        onConnectionSelect={onConnectionSelect}
      />
    );
    
    const connection = screen.getByTestId('workflow-connection-conn-1');
    fireEvent.click(connection);
    
    expect(onConnectionSelect).toHaveBeenCalledWith('conn-1');
  });

  it('supports animated connections', () => {
    const animatedConnections = mockConnections.map(conn => ({
      ...conn,
      animated: true
    }));
    
    render(
      <WorkflowEditor 
        nodes={mockNodes} 
        connections={animatedConnections}
      />
    );
    
    expect(screen.getByTestId('workflow-connection-conn-1')).toHaveClass('animate-pulse');
  });

  it('validates workflow without start node', () => {
    const nodesWithoutStart = mockNodes.filter(n => n.type !== 'start');
    
    render(
      <WorkflowEditor 
        nodes={nodesWithoutStart} 
        connections={mockConnections}
      />
    );
    
    expect(screen.getByText('Workflow must have at least one start node')).toBeInTheDocument();
  });

  it('validates workflow with multiple start nodes', () => {
    const multipleStartNodes = [
      ...mockNodes,
      { id: 'start-2', type: 'start' as const, label: 'Start 2', position: { x: 50, y: 200 } }
    ];
    
    render(
      <WorkflowEditor 
        nodes={multipleStartNodes} 
        connections={mockConnections}
      />
    );
    
    expect(screen.getByText('Workflow cannot have multiple start nodes')).toBeInTheDocument();
  });

  it('supports manual validation trigger', () => {
    const onWorkflowValidate = vi.fn();
    
    render(
      <WorkflowEditor 
        nodes={mockNodes} 
        connections={mockConnections}
        onWorkflowValidate={onWorkflowValidate}
      />
    );
    
    const validateButton = screen.getByTestId('validate-workflow');
    fireEvent.click(validateButton);
    
    expect(onWorkflowValidate).toHaveBeenCalled();
  });
});