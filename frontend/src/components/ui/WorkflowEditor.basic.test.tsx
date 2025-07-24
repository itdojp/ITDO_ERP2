import { render, screen, fireEvent } from '@testing-library/react';
import { vi } from 'vitest';
import { WorkflowEditor } from './WorkflowEditor';

describe('WorkflowEditor', () => {
  const mockNodes = [
    {
      id: 'start-1',
      type: 'start' as const,
      label: 'Start',
      position: { x: 100, y: 100 }
    },
    {
      id: 'end-1',
      type: 'end' as const,
      label: 'End',
      position: { x: 300, y: 100 }
    }
  ];

  const mockConnections = [
    {
      id: 'conn-1',
      sourceNodeId: 'start-1',
      targetNodeId: 'end-1'
    }
  ];

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders workflow editor with basic elements', () => {
    render(<WorkflowEditor nodes={mockNodes} connections={mockConnections} />);
    
    expect(screen.getByTestId('workflow-editor')).toBeInTheDocument();
    expect(screen.getByTestId('workflow-toolbar')).toBeInTheDocument();
  });

  it('renders nodes correctly', () => {
    render(<WorkflowEditor nodes={mockNodes} connections={mockConnections} />);
    
    expect(screen.getByTestId('workflow-node-start-1')).toBeInTheDocument();
    expect(screen.getByTestId('workflow-node-end-1')).toBeInTheDocument();
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
    
    const startNode = screen.getByTestId('workflow-node-start-1');
    fireEvent.click(startNode);
    
    expect(onNodeSelect).toHaveBeenCalledWith('start-1');
  });

  it('displays toolbar with controls', () => {
    render(<WorkflowEditor nodes={mockNodes} connections={mockConnections} />);
    
    expect(screen.getByTestId('execute-workflow')).toBeInTheDocument();
    expect(screen.getByTestId('save-workflow')).toBeInTheDocument();
    expect(screen.getByTestId('validate-workflow')).toBeInTheDocument();
  });

  it('supports zoom controls', () => {
    render(
      <WorkflowEditor 
        nodes={mockNodes} 
        connections={mockConnections}
        controls
      />
    );
    
    expect(screen.getByTestId('workflow-controls')).toBeInTheDocument();
    expect(screen.getByTestId('zoom-in')).toBeInTheDocument();
    expect(screen.getByTestId('zoom-out')).toBeInTheDocument();
    expect(screen.getByTestId('zoom-reset')).toBeInTheDocument();
  });

  it('shows validation errors for invalid workflow', () => {
    const nodesWithoutEnd = mockNodes.filter(n => n.type !== 'end');
    
    render(
      <WorkflowEditor 
        nodes={nodesWithoutEnd} 
        connections={mockConnections}
      />
    );
    
    expect(screen.getByTestId('validation-errors')).toBeInTheDocument();
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

  it('handles workflow execution', () => {
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
    
    expect(onWorkflowExecute).toHaveBeenCalled();
  });

  it('handles workflow saving', () => {
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

  it('supports custom styling', () => {
    render(
      <WorkflowEditor 
        nodes={mockNodes} 
        connections={mockConnections}
        className="custom-workflow"
        style={{ background: 'red' }}
      />
    );
    
    const editor = screen.getByTestId('workflow-editor');
    expect(editor).toHaveClass('custom-workflow');
    expect(editor).toHaveStyle('background: red');
  });

  it('displays workflow statistics', () => {
    render(<WorkflowEditor nodes={mockNodes} connections={mockConnections} />);
    
    expect(screen.getByText('2 nodes, 1 connections')).toBeInTheDocument();
    expect(screen.getByText('Zoom: 100%')).toBeInTheDocument();
  });

  it('handles zoom changes', () => {
    const onZoomChange = vi.fn();
    
    render(
      <WorkflowEditor 
        nodes={mockNodes} 
        connections={mockConnections}
        controls
        onZoomChange={onZoomChange}
      />
    );
    
    const zoomInButton = screen.getByTestId('zoom-in');
    fireEvent.click(zoomInButton);
    
    expect(onZoomChange).toHaveBeenCalledWith(1.1);
  });

  it('supports node types configuration', () => {
    const nodeTypes = {
      customTask: () => null
    };
    
    render(
      <WorkflowEditor 
        nodes={mockNodes} 
        connections={mockConnections}
        nodeTypes={nodeTypes}
      />
    );
    
    expect(screen.getByTestId('workflow-editor')).toBeInTheDocument();
  });

  it('supports workflow validation', () => {
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

  it('shows node connection handles', () => {
    render(<WorkflowEditor nodes={mockNodes} connections={mockConnections} />);
    
    expect(screen.getByTestId('node-handle-top-start-1')).toBeInTheDocument();
    expect(screen.getByTestId('node-handle-bottom-start-1')).toBeInTheDocument();
    expect(screen.getByTestId('node-handle-left-start-1')).toBeInTheDocument();
    expect(screen.getByTestId('node-handle-right-start-1')).toBeInTheDocument();
  });

  it('renders connections between nodes', () => {
    render(<WorkflowEditor nodes={mockNodes} connections={mockConnections} />);
    
    expect(screen.getByTestId('workflow-connection-conn-1')).toBeInTheDocument();
  });

  it('supports different node types with correct styling', () => {
    const allNodeTypes = [
      { id: 'start', type: 'start' as const, label: 'Start', position: { x: 0, y: 0 } },
      { id: 'end', type: 'end' as const, label: 'End', position: { x: 100, y: 0 } },
      { id: 'task', type: 'task' as const, label: 'Task', position: { x: 200, y: 0 } },
      { id: 'decision', type: 'decision' as const, label: 'Decision', position: { x: 300, y: 0 } }
    ];
    
    render(<WorkflowEditor nodes={allNodeTypes} connections={[]} />);
    
    allNodeTypes.forEach(node => {
      expect(screen.getByTestId(`workflow-node-${node.id}`)).toBeInTheDocument();
    });
  });

  it('supports grid functionality', () => {
    render(
      <WorkflowEditor 
        nodes={mockNodes} 
        connections={mockConnections}
        gridEnabled
        snapToGrid
      />
    );
    
    expect(screen.getByTestId('workflow-editor')).toBeInTheDocument();
  });

  it('handles empty workflow state', () => {
    render(<WorkflowEditor nodes={[]} connections={[]} />);
    
    expect(screen.getByTestId('workflow-editor')).toBeInTheDocument();
    expect(screen.getByText('0 nodes, 0 connections')).toBeInTheDocument();
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

  it('supports auto-save functionality', () => {
    render(
      <WorkflowEditor 
        nodes={mockNodes} 
        connections={mockConnections}
        autoSave
      />
    );
    
    expect(screen.getByTestId('workflow-editor')).toBeInTheDocument();
  });
});