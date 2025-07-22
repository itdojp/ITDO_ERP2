import { render, fireEvent, screen, waitFor } from '@testing-library/react';
import { Tooltip } from './Tooltip';

describe('Tooltip', () => {
  it('renders children correctly', () => {
    render(
      <Tooltip content="Tooltip content">
        <button>Hover me</button>
      </Tooltip>
    );
    expect(screen.getByText('Hover me')).toBeInTheDocument();
  });

  it('shows tooltip on hover by default', async () => {
    render(
      <Tooltip content="Tooltip content">
        <button>Hover me</button>
      </Tooltip>
    );
    
    const trigger = screen.getByText('Hover me');
    fireEvent.mouseEnter(trigger);
    
    await waitFor(() => {
      expect(screen.getByText('Tooltip content')).toBeInTheDocument();
    });
  });

  it('hides tooltip on mouse leave', async () => {
    render(
      <Tooltip content="Tooltip content">
        <button>Hover me</button>
      </Tooltip>
    );
    
    const trigger = screen.getByText('Hover me');
    fireEvent.mouseEnter(trigger);
    
    await waitFor(() => {
      expect(screen.getByText('Tooltip content')).toBeInTheDocument();
    });

    fireEvent.mouseLeave(trigger);
    
    await waitFor(() => {
      expect(screen.queryByText('Tooltip content')).not.toBeInTheDocument();
    });
  });

  it('shows tooltip on click when trigger is click', async () => {
    render(
      <Tooltip content="Tooltip content" trigger="click">
        <button>Click me</button>
      </Tooltip>
    );
    
    const trigger = screen.getByText('Click me');
    fireEvent.click(trigger);
    
    await waitFor(() => {
      expect(screen.getByText('Tooltip content')).toBeInTheDocument();
    });
  });

  it('toggles tooltip on multiple clicks', async () => {
    render(
      <Tooltip content="Tooltip content" trigger="click">
        <button>Click me</button>
      </Tooltip>
    );
    
    const trigger = screen.getByText('Click me');
    
    // First click - show
    fireEvent.click(trigger);
    await waitFor(() => {
      expect(screen.getByText('Tooltip content')).toBeInTheDocument();
    });

    // Second click - hide
    fireEvent.click(trigger);
    await waitFor(() => {
      expect(screen.queryByText('Tooltip content')).not.toBeInTheDocument();
    });
  });

  it('shows tooltip on focus when trigger is focus', async () => {
    render(
      <Tooltip content="Tooltip content" trigger="focus">
        <button>Focus me</button>
      </Tooltip>
    );
    
    const trigger = screen.getByText('Focus me');
    fireEvent.focus(trigger);
    
    await waitFor(() => {
      expect(screen.getByText('Tooltip content')).toBeInTheDocument();
    });
  });

  it('hides tooltip on blur when trigger is focus', async () => {
    render(
      <Tooltip content="Tooltip content" trigger="focus">
        <button>Focus me</button>
      </Tooltip>
    );
    
    const trigger = screen.getByText('Focus me');
    fireEvent.focus(trigger);
    
    await waitFor(() => {
      expect(screen.getByText('Tooltip content')).toBeInTheDocument();
    });

    fireEvent.blur(trigger);
    
    await waitFor(() => {
      expect(screen.queryByText('Tooltip content')).not.toBeInTheDocument();
    });
  });

  it('respects delay prop', async () => {
    render(
      <Tooltip content="Tooltip content" delay={100}>
        <button>Hover me</button>
      </Tooltip>
    );
    
    const trigger = screen.getByText('Hover me');
    fireEvent.mouseEnter(trigger);
    
    // Should not show immediately
    expect(screen.queryByText('Tooltip content')).not.toBeInTheDocument();
    
    // Should show after delay
    await waitFor(() => {
      expect(screen.getByText('Tooltip content')).toBeInTheDocument();
    }, { timeout: 200 });
  });

  it('does not show tooltip when disabled', () => {
    render(
      <Tooltip content="Tooltip content" disabled>
        <button>Hover me</button>
      </Tooltip>
    );
    
    const trigger = screen.getByText('Hover me');
    fireEvent.mouseEnter(trigger);
    
    expect(screen.queryByText('Tooltip content')).not.toBeInTheDocument();
  });

  it('renders React node content correctly', async () => {
    const tooltipContent = (
      <div>
        <strong>Bold text</strong>
        <br />
        <span>Regular text</span>
      </div>
    );

    render(
      <Tooltip content={tooltipContent}>
        <button>Hover me</button>
      </Tooltip>
    );
    
    const trigger = screen.getByText('Hover me');
    fireEvent.mouseEnter(trigger);
    
    await waitFor(() => {
      expect(screen.getByText('Bold text')).toBeInTheDocument();
      expect(screen.getByText('Regular text')).toBeInTheDocument();
    });
  });

  it('applies custom className', async () => {
    render(
      <Tooltip content="Tooltip content" className="custom-tooltip">
        <button>Hover me</button>
      </Tooltip>
    );
    
    const trigger = screen.getByText('Hover me');
    fireEvent.mouseEnter(trigger);
    
    await waitFor(() => {
      const tooltip = screen.getByText('Tooltip content');
      expect(tooltip).toHaveClass('custom-tooltip');
    });
  });

  it('handles different placement options', async () => {
    const { rerender } = render(
      <Tooltip content="Tooltip content" placement="bottom">
        <button>Hover me</button>
      </Tooltip>
    );
    
    const trigger = screen.getByText('Hover me');
    fireEvent.mouseEnter(trigger);
    
    await waitFor(() => {
      expect(screen.getByText('Tooltip content')).toBeInTheDocument();
    });

    // Test different placements
    for (const placement of ['left', 'right', 'top']) {
      rerender(
        <Tooltip content="Tooltip content" placement={placement as any}>
          <button>Hover me</button>
        </Tooltip>
      );
    }
  });

  it('shows/hides arrow based on arrow prop', async () => {
    const { container, rerender } = render(
      <Tooltip content="Tooltip content" arrow={true}>
        <button>Hover me</button>
      </Tooltip>
    );
    
    const trigger = screen.getByText('Hover me');
    fireEvent.mouseEnter(trigger);
    
    await waitFor(() => {
      expect(screen.getByText('Tooltip content')).toBeInTheDocument();
    });

    // Check for arrow element
    let arrow = container.querySelector('[style*="border"]');
    expect(arrow).toBeInTheDocument();

    fireEvent.mouseLeave(trigger);
    
    await waitFor(() => {
      expect(screen.queryByText('Tooltip content')).not.toBeInTheDocument();
    });

    // Test without arrow
    rerender(
      <Tooltip content="Tooltip content" arrow={false}>
        <button>Hover me</button>
      </Tooltip>
    );

    fireEvent.mouseEnter(trigger);
    
    await waitFor(() => {
      expect(screen.getByText('Tooltip content')).toBeInTheDocument();
    });
  });
});