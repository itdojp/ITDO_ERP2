import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { vi } from 'vitest';
import { Panel } from './Panel';

describe('Panel', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders panel with content', () => {
    render(
      <Panel title="Test Panel">
        <div>Panel content</div>
      </Panel>
    );
    
    expect(screen.getByTestId('panel-container')).toBeInTheDocument();
    expect(screen.getByText('Test Panel')).toBeInTheDocument();
    expect(screen.getByText('Panel content')).toBeInTheDocument();
  });

  it('supports collapsible panels', () => {
    render(
      <Panel title="Collapsible Panel" collapsible>
        <div>Collapsible content</div>
      </Panel>
    );
    
    const toggleButton = screen.getByTestId('panel-toggle');
    expect(screen.getByText('Collapsible content')).toBeInTheDocument();
    
    fireEvent.click(toggleButton);
    expect(screen.queryByText('Collapsible content')).not.toBeInTheDocument();
    
    fireEvent.click(toggleButton);
    expect(screen.getByText('Collapsible content')).toBeInTheDocument();
  });

  it('starts collapsed when defaultCollapsed is true', () => {
    render(
      <Panel title="Default Collapsed" collapsible defaultCollapsed>
        <div>Hidden content</div>
      </Panel>
    );
    
    expect(screen.queryByText('Hidden content')).not.toBeInTheDocument();
    
    const toggleButton = screen.getByTestId('panel-toggle');
    fireEvent.click(toggleButton);
    
    expect(screen.getByText('Hidden content')).toBeInTheDocument();
  });

  it('calls onToggle when collapsed state changes', () => {
    const onToggle = vi.fn();
    render(
      <Panel title="Toggle Panel" collapsible onToggle={onToggle}>
        <div>Content</div>
      </Panel>
    );
    
    const toggleButton = screen.getByTestId('panel-toggle');
    fireEvent.click(toggleButton);
    
    expect(onToggle).toHaveBeenCalledWith(true);
    
    fireEvent.click(toggleButton);
    expect(onToggle).toHaveBeenCalledWith(false);
  });

  it('supports different sizes', () => {
    const sizes = ['sm', 'md', 'lg'] as const;
    
    sizes.forEach(size => {
      const { unmount } = render(<Panel title="Test" size={size}>Content</Panel>);
      const container = screen.getByTestId('panel-container');
      expect(container).toHaveClass(`size-${size}`);
      unmount();
    });
  });

  it('supports different themes', () => {
    const themes = ['light', 'dark'] as const;
    
    themes.forEach(theme => {
      const { unmount } = render(<Panel title="Test" theme={theme}>Content</Panel>);
      const container = screen.getByTestId('panel-container');
      expect(container).toHaveClass(`theme-${theme}`);
      unmount();
    });
  });

  it('supports different variants', () => {
    const variants = ['default', 'bordered', 'filled', 'outlined'] as const;
    
    variants.forEach(variant => {
      const { unmount } = render(<Panel title="Test" variant={variant}>Content</Panel>);
      const container = screen.getByTestId('panel-container');
      expect(container).toHaveClass(`variant-${variant}`);
      unmount();
    });
  });

  it('displays header actions when provided', () => {
    const actions = [
      { id: 'edit', label: 'Edit', onClick: vi.fn() },
      { id: 'delete', label: 'Delete', onClick: vi.fn() }
    ];
    
    render(
      <Panel title="Panel with Actions" actions={actions}>
        <div>Content</div>
      </Panel>
    );
    
    expect(screen.getByTestId('panel-action-edit')).toBeInTheDocument();
    expect(screen.getByTestId('panel-action-delete')).toBeInTheDocument();
  });

  it('handles action clicks', () => {
    const editAction = vi.fn();
    const actions = [
      { id: 'edit', label: 'Edit', onClick: editAction }
    ];
    
    render(
      <Panel title="Panel with Actions" actions={actions}>
        <div>Content</div>
      </Panel>
    );
    
    fireEvent.click(screen.getByTestId('panel-action-edit'));
    expect(editAction).toHaveBeenCalled();
  });

  it('displays panel icon when provided', () => {
    render(
      <Panel title="Panel with Icon" icon="📋">
        <div>Content</div>
      </Panel>
    );
    
    expect(screen.getByTestId('panel-icon')).toBeInTheDocument();
    expect(screen.getByText('📋')).toBeInTheDocument();
  });

  it('supports custom header content', () => {
    const customHeader = <div data-testid="custom-header">Custom Header</div>;
    
    render(
      <Panel header={customHeader}>
        <div>Content</div>
      </Panel>
    );
    
    expect(screen.getByTestId('custom-header')).toBeInTheDocument();
  });

  it('supports footer content', () => {
    const footer = <div data-testid="panel-footer">Footer content</div>;
    
    render(
      <Panel title="Panel with Footer" footer={footer}>
        <div>Content</div>
      </Panel>
    );
    
    expect(screen.getByTestId('panel-footer')).toBeInTheDocument();
  });

  it('supports loading state', () => {
    render(
      <Panel title="Loading Panel" loading>
        <div>Content</div>
      </Panel>
    );
    
    expect(screen.getByTestId('panel-loading')).toBeInTheDocument();
    expect(screen.queryByText('Content')).not.toBeInTheDocument();
  });

  it('supports error state', () => {
    render(
      <Panel title="Error Panel" error="Something went wrong">
        <div>Content</div>
      </Panel>
    );
    
    expect(screen.getByTestId('panel-error')).toBeInTheDocument();
    expect(screen.getByText('Something went wrong')).toBeInTheDocument();
    expect(screen.queryByText('Content')).not.toBeInTheDocument();
  });

  it('supports empty state', () => {
    const emptyState = <div data-testid="empty-state">No data available</div>;
    
    render(
      <Panel title="Empty Panel" empty emptyState={emptyState}>
        <div>Content</div>
      </Panel>
    );
    
    expect(screen.getByTestId('empty-state')).toBeInTheDocument();
    expect(screen.queryByText('Content')).not.toBeInTheDocument();
  });

  it('supports scrollable content', () => {
    render(
      <Panel title="Scrollable Panel" scrollable maxHeight="200px">
        <div>Long content that should scroll</div>
      </Panel>
    );
    
    const content = screen.getByTestId('panel-content');
    expect(content).toHaveClass('scrollable');
    expect(content).toHaveStyle({ maxHeight: '200px' });
  });

  it('supports resizable panels', () => {
    const onResize = vi.fn();
    render(
      <Panel title="Resizable Panel" resizable onResize={onResize}>
        <div>Resizable content</div>
      </Panel>
    );
    
    const container = screen.getByTestId('panel-container');
    expect(container).toHaveClass('resizable');
    
    const resizeHandle = screen.getByTestId('panel-resize-handle');
    expect(resizeHandle).toBeInTheDocument();
  });

  it('supports draggable panels', () => {
    const onDrag = vi.fn();
    render(
      <Panel title="Draggable Panel" draggable onDrag={onDrag}>
        <div>Draggable content</div>
      </Panel>
    );
    
    const header = screen.getByTestId('panel-header');
    expect(header).toHaveClass('draggable');
  });

  it('supports panel with toolbar', () => {
    const toolbar = <div data-testid="panel-toolbar">Toolbar content</div>;
    
    render(
      <Panel title="Panel with Toolbar" toolbar={toolbar}>
        <div>Content</div>
      </Panel>
    );
    
    expect(screen.getByTestId('panel-toolbar')).toBeInTheDocument();
  });

  it('supports tabs within panel', () => {
    const tabs = [
      { id: 'tab1', label: 'Tab 1', content: <div>Tab 1 content</div> },
      { id: 'tab2', label: 'Tab 2', content: <div>Tab 2 content</div> }
    ];
    
    render(
      <Panel title="Panel with Tabs" tabs={tabs}>
        <div>Default content</div>
      </Panel>
    );
    
    expect(screen.getByTestId('panel-tabs')).toBeInTheDocument();
    expect(screen.getByText('Tab 1')).toBeInTheDocument();
    expect(screen.getByText('Tab 2')).toBeInTheDocument();
  });

  it('handles tab switching', () => {
    const tabs = [
      { id: 'tab1', label: 'Tab 1', content: <div>Tab 1 content</div> },
      { id: 'tab2', label: 'Tab 2', content: <div>Tab 2 content</div> }
    ];
    
    render(
      <Panel title="Panel with Tabs" tabs={tabs} />
    );
    
    expect(screen.getByText('Tab 1 content')).toBeInTheDocument();
    expect(screen.queryByText('Tab 2 content')).not.toBeInTheDocument();
    
    fireEvent.click(screen.getByText('Tab 2'));
    
    expect(screen.queryByText('Tab 1 content')).not.toBeInTheDocument();
    expect(screen.getByText('Tab 2 content')).toBeInTheDocument();
  });

  it('supports panel nesting', () => {
    render(
      <Panel title="Parent Panel">
        <Panel title="Child Panel">
          <div>Nested content</div>
        </Panel>
      </Panel>
    );
    
    expect(screen.getByText('Parent Panel')).toBeInTheDocument();
    expect(screen.getByText('Child Panel')).toBeInTheDocument();
    expect(screen.getByText('Nested content')).toBeInTheDocument();
  });

  it('supports panel with breadcrumbs', () => {
    const breadcrumbs = [
      { label: 'Home', href: '/' },
      { label: 'Section', href: '/section' },
      { label: 'Current', href: '/section/current' }
    ];
    
    render(
      <Panel title="Panel with Breadcrumbs" breadcrumbs={breadcrumbs}>
        <div>Content</div>
      </Panel>
    );
    
    expect(screen.getByTestId('panel-breadcrumbs')).toBeInTheDocument();
    expect(screen.getByText('Home')).toBeInTheDocument();
    expect(screen.getByText('Section')).toBeInTheDocument();
    expect(screen.getByText('Current')).toBeInTheDocument();
  });

  it('supports fullscreen mode', () => {
    render(
      <Panel title="Fullscreen Panel" fullscreen>
        <div>Fullscreen content</div>
      </Panel>
    );
    
    const container = screen.getByTestId('panel-container');
    expect(container).toHaveClass('fullscreen');
  });

  it('supports minimizable panels', () => {
    const onMinimize = vi.fn();
    render(
      <Panel title="Minimizable Panel" minimizable onMinimize={onMinimize}>
        <div>Content</div>
      </Panel>
    );
    
    const minimizeButton = screen.getByTestId('panel-minimize');
    fireEvent.click(minimizeButton);
    
    expect(onMinimize).toHaveBeenCalledWith(true);
  });

  it('supports closable panels', () => {
    const onClose = vi.fn();
    render(
      <Panel title="Closable Panel" closable onClose={onClose}>
        <div>Content</div>
      </Panel>
    );
    
    const closeButton = screen.getByTestId('panel-close');
    fireEvent.click(closeButton);
    
    expect(onClose).toHaveBeenCalled();
  });

  it('supports panel with badge', () => {
    render(
      <Panel title="Panel with Badge" badge="5">
        <div>Content</div>
      </Panel>
    );
    
    expect(screen.getByTestId('panel-badge')).toBeInTheDocument();
    expect(screen.getByText('5')).toBeInTheDocument();
  });

  it('supports keyboard navigation', () => {
    render(
      <Panel title="Keyboard Panel" collapsible>
        <div>Content</div>
      </Panel>
    );
    
    const toggleButton = screen.getByTestId('panel-toggle');
    toggleButton.focus();
    
    fireEvent.keyDown(toggleButton, { key: 'Enter' });
    expect(screen.queryByText('Content')).not.toBeInTheDocument();
  });

  it('supports custom styling', () => {
    render(
      <Panel title="Custom Panel" className="custom-panel">
        <div>Content</div>
      </Panel>
    );
    
    const container = screen.getByTestId('panel-container');
    expect(container).toHaveClass('custom-panel');
  });

  it('supports custom data attributes', () => {
    render(
      <Panel title="Test Panel" data-category="ui" data-id="main-panel">
        <div>Content</div>
      </Panel>
    );
    
    const container = screen.getByTestId('panel-container');
    expect(container).toHaveAttribute('data-category', 'ui');
    expect(container).toHaveAttribute('data-id', 'main-panel');
  });

  it('supports panel groups', () => {
    render(
      <Panel title="Panel Group" group="settings">
        <div>Content</div>
      </Panel>
    );
    
    const container = screen.getByTestId('panel-container');
    expect(container).toHaveAttribute('data-group', 'settings');
  });

  it('supports panel priorities', () => {
    const priorities = ['low', 'normal', 'high', 'urgent'] as const;
    
    priorities.forEach(priority => {
      const { unmount } = render(
        <Panel title="Test Panel" priority={priority}>
          <div>Content</div>
        </Panel>
      );
      const container = screen.getByTestId('panel-container');
      expect(container).toHaveClass(`priority-${priority}`);
      unmount();
    });
  });

  it('supports panel with help text', () => {
    render(
      <Panel title="Panel with Help" helpText="This is help text">
        <div>Content</div>
      </Panel>
    );
    
    expect(screen.getByTestId('panel-help')).toBeInTheDocument();
    expect(screen.getByText('This is help text')).toBeInTheDocument();
  });

  it('supports panel with status indicator', () => {
    const statuses = ['active', 'inactive', 'warning', 'error'] as const;
    
    statuses.forEach(status => {
      const { unmount } = render(
        <Panel title="Test Panel" status={status}>
          <div>Content</div>
        </Panel>
      );
      const container = screen.getByTestId('panel-container');
      expect(container).toHaveClass(`status-${status}`);
      unmount();
    });
  });

  it('supports panel with progress indicator', () => {
    render(
      <Panel title="Panel with Progress" progress={75}>
        <div>Content</div>
      </Panel>
    );
    
    const progressBar = screen.getByTestId('panel-progress');
    expect(progressBar).toBeInTheDocument();
    expect(progressBar).toHaveStyle({ width: '75%' });
  });

  it('supports animated panel transitions', () => {
    render(
      <Panel title="Animated Panel" animated collapsible>
        <div>Content</div>
      </Panel>
    );
    
    const container = screen.getByTestId('panel-container');
    expect(container).toHaveClass('animated');
  });

  it('supports panel with custom width and height', () => {
    render(
      <Panel title="Sized Panel" width="400px" height="300px">
        <div>Content</div>
      </Panel>
    );
    
    const container = screen.getByTestId('panel-container');
    expect(container).toHaveStyle({ width: '400px', height: '300px' });
  });

  it('supports accessibility attributes', () => {
    render(
      <Panel 
        title="Accessible Panel" 
        ariaLabel="Main content panel"
        ariaDescribedBy="panel-description"
      >
        <div>Content</div>
      </Panel>
    );
    
    const container = screen.getByTestId('panel-container');
    expect(container).toHaveAttribute('aria-label', 'Main content panel');
    expect(container).toHaveAttribute('aria-describedby', 'panel-description');
  });
});