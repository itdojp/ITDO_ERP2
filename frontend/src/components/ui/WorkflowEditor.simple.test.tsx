import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { WorkflowEditor } from './WorkflowEditor';

describe('WorkflowEditor Basic Tests', () => {
  const mockNodes = [
    {
      id: 'start-1',
      type: 'start' as const,
      label: 'Start',
      position: { x: 100, y: 100 }
    }
  ];

  const mockConnections = [];

  it('renders workflow editor', () => {
    render(<WorkflowEditor nodes={mockNodes} connections={mockConnections} />);
    expect(screen.getByTestId('workflow-editor')).toBeInTheDocument();
  });

  it('renders toolbar', () => {
    render(<WorkflowEditor nodes={mockNodes} connections={mockConnections} />);
    expect(screen.getByTestId('workflow-toolbar')).toBeInTheDocument();
  });

  it('renders nodes', () => {
    render(<WorkflowEditor nodes={mockNodes} connections={mockConnections} />);
    expect(screen.getByTestId('workflow-node-start-1')).toBeInTheDocument();
  });
});