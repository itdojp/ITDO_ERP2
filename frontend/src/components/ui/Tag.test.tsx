import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { vi } from 'vitest';
import { Tag } from './Tag';

describe('Tag', () => {
  it('renders with basic text', () => {
    render(<Tag>Basic Tag</Tag>);
    expect(screen.getByText('Basic Tag')).toBeInTheDocument();
  });

  it('renders with different colors', () => {
    const colors = ['default', 'primary', 'secondary', 'success', 'warning', 'error', 'info'] as const;
    
    colors.forEach(color => {
      const { unmount } = render(<Tag color={color}>Tag {color}</Tag>);
      expect(screen.getByText(`Tag ${color}`)).toBeInTheDocument();
      unmount();
    });
  });

  it('renders with different sizes', () => {
    const sizes = ['small', 'medium', 'large'] as const;
    
    sizes.forEach(size => {
      const { unmount } = render(<Tag size={size}>Tag {size}</Tag>);
      expect(screen.getByText(`Tag ${size}`)).toBeInTheDocument();
      unmount();
    });
  });

  it('renders with different variants', () => {
    const variants = ['solid', 'outlined', 'subtle'] as const;
    
    variants.forEach(variant => {
      const { unmount } = render(<Tag variant={variant}>Tag {variant}</Tag>);
      expect(screen.getByText(`Tag ${variant}`)).toBeInTheDocument();
      unmount();
    });
  });

  it('handles closable functionality', async () => {
    const onClose = vi.fn();
    render(
      <Tag closable onClose={onClose}>
        Closable Tag
      </Tag>
    );

    const closeButton = screen.getByRole('button');
    expect(closeButton).toBeInTheDocument();

    fireEvent.click(closeButton);
    expect(onClose).toHaveBeenCalled();
  });

  it('renders with icon', () => {
    const icon = <span data-testid="tag-icon">🏷️</span>;
    render(<Tag icon={icon}>Tag with Icon</Tag>);
    
    expect(screen.getByTestId('tag-icon')).toBeInTheDocument();
    expect(screen.getByText('Tag with Icon')).toBeInTheDocument();
  });

  it('supports custom className', () => {
    render(<Tag className="custom-tag">Custom Tag</Tag>);
    
    const tag = screen.getByText('Custom Tag');
    expect(tag).toBeInTheDocument();
  });

  it('handles click events when clickable', () => {
    const onClick = vi.fn();
    render(
      <Tag clickable onClick={onClick}>
        Clickable Tag
      </Tag>
    );

    const tag = screen.getByText('Clickable Tag');
    fireEvent.click(tag);
    expect(onClick).toHaveBeenCalled();
  });

  it('renders with loading state', () => {
    render(<Tag loading>Loading Tag</Tag>);
    
    const spinner = screen.getByRole('img', { hidden: true });
    expect(spinner).toBeInTheDocument();
    expect(spinner).toHaveClass('animate-spin');
  });

  it('supports disabled state', () => {
    const onClick = vi.fn();
    render(
      <Tag disabled clickable onClick={onClick}>
        Disabled Tag
      </Tag>
    );

    const tag = screen.getByText('Disabled Tag');
    fireEvent.click(tag);
    expect(onClick).not.toHaveBeenCalled();
  });

  it('renders with border radius variants', () => {
    const radiusVariants = ['none', 'small', 'medium', 'large', 'full'] as const;
    
    radiusVariants.forEach(radius => {
      const { unmount } = render(<Tag radius={radius}>Tag {radius}</Tag>);
      expect(screen.getByText(`Tag ${radius}`)).toBeInTheDocument();
      unmount();
    });
  });

  it('supports custom styles', () => {
    const customStyle = { backgroundColor: 'purple', color: 'white' };
    render(<Tag style={customStyle}>Styled Tag</Tag>);
    
    expect(screen.getByText('Styled Tag')).toBeInTheDocument();
  });

  it('renders with dot indicator', () => {
    render(<Tag dot>Dot Tag</Tag>);
    
    expect(screen.getByText('Dot Tag')).toBeInTheDocument();
    const dotElement = document.querySelector('[data-testid="tag-dot"]');
    expect(dotElement).toBeInTheDocument();
  });

  it('handles animation on mount', async () => {
    render(<Tag animated>Animated Tag</Tag>);
    
    await waitFor(() => {
      expect(screen.getByText('Animated Tag')).toBeInTheDocument();
    });
  });

  it('renders with custom close icon', () => {
    const customCloseIcon = <span data-testid="custom-close">×</span>;
    const onClose = vi.fn();
    
    render(
      <Tag closable onClose={onClose} closeIcon={customCloseIcon}>
        Custom Close Tag
      </Tag>
    );

    expect(screen.getByTestId('custom-close')).toBeInTheDocument();
  });

  it('supports checkable functionality', () => {
    const onChange = vi.fn();
    render(
      <Tag checkable onChange={onChange}>
        Checkable Tag
      </Tag>
    );

    const tag = screen.getByText('Checkable Tag');
    fireEvent.click(tag);
    expect(onChange).toHaveBeenCalledWith(true);
  });

  it('supports controlled checkable state', () => {
    const onChange = vi.fn();
    const { rerender } = render(
      <Tag checkable checked={false} onChange={onChange}>
        Controlled Tag
      </Tag>
    );

    const tag = screen.getByText('Controlled Tag');
    fireEvent.click(tag);
    expect(onChange).toHaveBeenCalledWith(true);

    rerender(
      <Tag checkable checked={true} onChange={onChange}>
        Controlled Tag
      </Tag>
    );
    
    expect(screen.getByText('Controlled Tag')).toBeInTheDocument();
  });

  it('renders with maximum width and truncation', () => {
    render(
      <Tag maxWidth={100} truncate>
        Very long tag text that should be truncated
      </Tag>
    );
    
    expect(screen.getByText('Very long tag text that should be truncated')).toBeInTheDocument();
  });

  it('supports tooltip on hover', async () => {
    render(
      <Tag tooltip="Tag tooltip">
        Tag with Tooltip
      </Tag>
    );

    const tag = screen.getByText('Tag with Tooltip');
    fireEvent.mouseEnter(tag);
    
    await waitFor(() => {
      expect(screen.getByText('Tag tooltip')).toBeInTheDocument();
    });
  });

  it('handles group selection', () => {
    const onGroupChange = vi.fn();
    
    render(
      <Tag.Group onChange={onGroupChange}>
        <Tag value="tag1">Tag 1</Tag>
        <Tag value="tag2">Tag 2</Tag>
        <Tag value="tag3">Tag 3</Tag>
      </Tag.Group>
    );

    fireEvent.click(screen.getByText('Tag 1'));
    expect(onGroupChange).toHaveBeenCalledWith(['tag1']);
  });

  it('renders with predefined status tags', () => {
    render(<Tag.Status status="active">Active Status</Tag.Status>);
    expect(screen.getByText('Active Status')).toBeInTheDocument();
  });

  it('supports custom data attributes', () => {
    render(
      <Tag data-testid="custom-tag" data-value="test">
        Custom Data Tag
      </Tag>
    );
    
    const tag = screen.getByTestId('custom-tag');
    expect(tag).toHaveAttribute('data-value', 'test');
  });

  it('handles keyboard navigation for checkable tags', () => {
    const onChange = vi.fn();
    render(
      <Tag checkable onChange={onChange}>
        Keyboard Tag
      </Tag>
    );

    const tag = screen.getByText('Keyboard Tag');
    fireEvent.keyDown(tag, { key: 'Enter' });
    expect(onChange).toHaveBeenCalledWith(true);

    fireEvent.keyDown(tag, { key: ' ' });
    expect(onChange).toHaveBeenCalledWith(false);
  });

  it('prevents close when beforeClose returns false', async () => {
    const beforeClose = vi.fn().mockReturnValue(false);
    const onClose = vi.fn();
    
    render(
      <Tag closable onClose={onClose} beforeClose={beforeClose}>
        Protected Tag
      </Tag>
    );

    const closeButton = screen.getByRole('button');
    fireEvent.click(closeButton);
    
    expect(beforeClose).toHaveBeenCalled();
    expect(onClose).not.toHaveBeenCalled();
  });

  it('allows close when beforeClose returns true', async () => {
    const beforeClose = vi.fn().mockReturnValue(true);
    const onClose = vi.fn();
    
    render(
      <Tag closable onClose={onClose} beforeClose={beforeClose}>
        Allowed Tag
      </Tag>
    );

    const closeButton = screen.getByRole('button');
    fireEvent.click(closeButton);
    
    expect(beforeClose).toHaveBeenCalled();
    expect(onClose).toHaveBeenCalled();
  });
});