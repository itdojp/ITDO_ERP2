import { render, fireEvent, screen } from '@testing-library/react';
import { Button } from './Button';
import React from 'react';

describe('Button', () => {
  it('renders button with children', () => {
    render(<Button>Click me</Button>);
    expect(screen.getByText('Click me')).toBeInTheDocument();
  });

  it('handles click events', () => {
    const onClick = jest.fn();
    render(<Button onClick={onClick}>Click me</Button>);
    
    fireEvent.click(screen.getByRole('button'));
    expect(onClick).toHaveBeenCalledTimes(1);
  });

  it('applies primary variant classes by default', () => {
    render(<Button>Primary Button</Button>);
    const button = screen.getByRole('button');
    expect(button).toHaveClass('bg-blue-600', 'text-white', 'border-blue-600');
  });

  it('applies secondary variant classes', () => {
    render(<Button variant="secondary">Secondary Button</Button>);
    const button = screen.getByRole('button');
    expect(button).toHaveClass('bg-gray-100', 'text-gray-900', 'border-gray-300');
  });

  it('applies outline variant classes', () => {
    render(<Button variant="outline">Outline Button</Button>);
    const button = screen.getByRole('button');
    expect(button).toHaveClass('bg-transparent', 'text-blue-600', 'border-blue-600');
  });

  it('applies ghost variant classes', () => {
    render(<Button variant="ghost">Ghost Button</Button>);
    const button = screen.getByRole('button');
    expect(button).toHaveClass('bg-transparent', 'text-gray-600', 'border-transparent');
  });

  it('applies link variant classes', () => {
    render(<Button variant="link">Link Button</Button>);
    const button = screen.getByRole('button');
    expect(button).toHaveClass('bg-transparent', 'text-blue-600', 'border-transparent');
  });

  it('applies danger variant classes', () => {
    render(<Button variant="danger">Danger Button</Button>);
    const button = screen.getByRole('button');
    expect(button).toHaveClass('bg-red-600', 'text-white', 'border-red-600');
  });

  it('applies size classes correctly', () => {
    const { rerender } = render(<Button size="sm">Small</Button>);
    let button = screen.getByRole('button');
    expect(button).toHaveClass('px-3', 'py-1.5', 'text-sm');

    rerender(<Button size="md">Medium</Button>);
    button = screen.getByRole('button');
    expect(button).toHaveClass('px-4', 'py-2', 'text-sm');

    rerender(<Button size="lg">Large</Button>);
    button = screen.getByRole('button');
    expect(button).toHaveClass('px-6', 'py-3', 'text-base');

    rerender(<Button size="xl">Extra Large</Button>);
    button = screen.getByRole('button');
    expect(button).toHaveClass('px-8', 'py-4', 'text-lg');
  });

  it('applies shape classes correctly', () => {
    const { rerender } = render(<Button shape="default">Default</Button>);
    let button = screen.getByRole('button');
    expect(button).toHaveClass('rounded-md');

    rerender(<Button shape="circle">Circle</Button>);
    button = screen.getByRole('button');
    expect(button).toHaveClass('rounded-full');

    rerender(<Button shape="round">Round</Button>);
    button = screen.getByRole('button');
    expect(button).toHaveClass('rounded-full');
  });

  it('applies circle size classes correctly', () => {
    const { rerender } = render(<Button shape="circle" size="sm">S</Button>);
    let button = screen.getByRole('button');
    expect(button).toHaveClass('w-8', 'h-8', 'p-0');

    rerender(<Button shape="circle" size="md">M</Button>);
    button = screen.getByRole('button');
    expect(button).toHaveClass('w-10', 'h-10', 'p-0');

    rerender(<Button shape="circle" size="lg">L</Button>);
    button = screen.getByRole('button');
    expect(button).toHaveClass('w-12', 'h-12', 'p-0');

    rerender(<Button shape="circle" size="xl">XL</Button>);
    button = screen.getByRole('button');
    expect(button).toHaveClass('w-14', 'h-14', 'p-0');
  });

  it('renders with icon on the left', () => {
    render(
      <Button icon={<span data-testid="icon">🏠</span>}>
        Home
      </Button>
    );
    
    const icon = screen.getByTestId('icon');
    const text = screen.getByText('Home');
    
    expect(icon).toBeInTheDocument();
    expect(text).toBeInTheDocument();
  });

  it('renders with icon on the right', () => {
    render(
      <Button icon={<span data-testid="icon">→</span>} iconPosition="right">
        Next
      </Button>
    );
    
    const icon = screen.getByTestId('icon');
    const text = screen.getByText('Next');
    
    expect(icon).toBeInTheDocument();
    expect(text).toBeInTheDocument();
  });

  it('renders icon only when no children', () => {
    render(<Button icon={<span data-testid="icon">🏠</span>} />);
    
    expect(screen.getByTestId('icon')).toBeInTheDocument();
    expect(screen.queryByText('Home')).not.toBeInTheDocument();
  });

  it('shows loading spinner when loading', () => {
    render(<Button loading>Loading</Button>);
    
    const button = screen.getByRole('button');
    const spinner = button.querySelector('.animate-spin');
    
    expect(spinner).toBeInTheDocument();
    expect(button).toHaveClass('pointer-events-none', 'opacity-75');
  });

  it('prevents click when loading', () => {
    const onClick = jest.fn();
    render(<Button loading onClick={onClick}>Loading</Button>);
    
    fireEvent.click(screen.getByRole('button'));
    expect(onClick).not.toHaveBeenCalled();
  });

  it('handles disabled state', () => {
    const onClick = jest.fn();
    render(<Button disabled onClick={onClick}>Disabled</Button>);
    
    const button = screen.getByRole('button');
    expect(button).toBeDisabled();
    expect(button).toHaveAttribute('aria-disabled', 'true');
    
    fireEvent.click(button);
    expect(onClick).not.toHaveBeenCalled();
  });

  it('applies block styling', () => {
    render(<Button block>Block Button</Button>);
    
    const button = screen.getByRole('button');
    expect(button).toHaveClass('w-full');
  });

  it('renders as anchor when href is provided', () => {
    render(<Button href="/test">Link Button</Button>);
    
    const link = screen.getByRole('button');
    expect(link.tagName).toBe('A');
    expect(link).toHaveAttribute('href', '/test');
  });

  it('renders as anchor with target', () => {
    render(<Button href="/test" target="_blank">External Link</Button>);
    
    const link = screen.getByRole('button');
    expect(link).toHaveAttribute('target', '_blank');
  });

  it('does not render as anchor when disabled', () => {
    render(<Button href="/test" disabled>Disabled Link</Button>);
    
    const button = screen.getByRole('button');
    expect(button.tagName).toBe('BUTTON');
  });

  it('does not render as anchor when loading', () => {
    render(<Button href="/test" loading>Loading Link</Button>);
    
    const button = screen.getByRole('button');
    expect(button.tagName).toBe('BUTTON');
  });

  it('applies custom className', () => {
    render(<Button className="custom-button">Custom</Button>);
    
    const button = screen.getByRole('button');
    expect(button).toHaveClass('custom-button');
  });

  it('sets correct button type', () => {
    const { rerender } = render(<Button htmlType="submit">Submit</Button>);
    let button = screen.getByRole('button');
    expect(button).toHaveAttribute('type', 'submit');

    rerender(<Button htmlType="reset">Reset</Button>);
    button = screen.getByRole('button');
    expect(button).toHaveAttribute('type', 'reset');

    rerender(<Button htmlType="button">Button</Button>);
    button = screen.getByRole('button');
    expect(button).toHaveAttribute('type', 'button');
  });

  it('sets aria-busy when loading', () => {
    render(<Button loading>Loading</Button>);
    
    const button = screen.getByRole('button');
    expect(button).toHaveAttribute('aria-busy', 'true');
  });

  it('forwards ref to button element', () => {
    const ref = React.createRef<HTMLButtonElement>();
    render(<Button ref={ref}>Button</Button>);
    
    expect(ref.current).toBeInstanceOf(HTMLButtonElement);
  });

  it('forwards ref to anchor element when href is provided', () => {
    const ref = React.createRef<HTMLAnchorElement>();
    render(<Button ref={ref} href="/test">Link</Button>);
    
    expect(ref.current).toBeInstanceOf(HTMLAnchorElement);
  });

  it('handles circle shape with icon only', () => {
    render(<Button shape="circle" icon={<span data-testid="icon">+</span>} />);
    
    const button = screen.getByRole('button');
    const icon = screen.getByTestId('icon');
    
    expect(button).toHaveClass('rounded-full');
    expect(icon).toBeInTheDocument();
  });

  it('handles circle shape with children only', () => {
    render(<Button shape="circle">+</Button>);
    
    const button = screen.getByRole('button');
    expect(button).toHaveClass('rounded-full');
    expect(screen.getByText('+')).toBeInTheDocument();
  });
});

describe('Button.Group', () => {
  it('renders button group', () => {
    render(
      <Button.Group>
        <Button>First</Button>
        <Button>Second</Button>
        <Button>Third</Button>
      </Button.Group>
    );

    expect(screen.getByText('First')).toBeInTheDocument();
    expect(screen.getByText('Second')).toBeInTheDocument();
    expect(screen.getByText('Third')).toBeInTheDocument();
  });

  it('applies size to all buttons in group', () => {
    render(
      <Button.Group size="lg">
        <Button>First</Button>
        <Button>Second</Button>
      </Button.Group>
    );

    const buttons = screen.getAllByRole('button');
    buttons.forEach(button => {
      expect(button).toHaveClass('px-6', 'py-3', 'text-base');
    });
  });

  it('applies variant to all buttons in group', () => {
    render(
      <Button.Group variant="outline">
        <Button>First</Button>
        <Button>Second</Button>
      </Button.Group>
    );

    const buttons = screen.getAllByRole('button');
    buttons.forEach(button => {
      expect(button).toHaveClass('text-blue-600', 'border-blue-600');
    });
  });

  it('respects individual button props over group props', () => {
    render(
      <Button.Group variant="outline" size="lg">
        <Button variant="primary" size="sm">Custom</Button>
        <Button>Default</Button>
      </Button.Group>
    );

    const customButton = screen.getByText('Custom');
    const defaultButton = screen.getByText('Default');

    expect(customButton).toHaveClass('bg-blue-600'); // primary variant
    expect(customButton).toHaveClass('px-3', 'py-1.5'); // small size

    expect(defaultButton).toHaveClass('text-blue-600'); // outline variant from group
    expect(defaultButton).toHaveClass('px-6', 'py-3'); // large size from group
  });

  it('applies proper border radius for horizontal group', () => {
    render(
      <Button.Group>
        <Button>First</Button>
        <Button>Middle</Button>
        <Button>Last</Button>
      </Button.Group>
    );

    const buttons = screen.getAllByRole('button');
    expect(buttons[0]).toHaveClass('rounded-r-none'); // first
    expect(buttons[1]).toHaveClass('rounded-none'); // middle
    expect(buttons[2]).toHaveClass('rounded-l-none'); // last
  });

  it('applies proper border radius for vertical group', () => {
    render(
      <Button.Group vertical>
        <Button>First</Button>
        <Button>Middle</Button>
        <Button>Last</Button>
      </Button.Group>
    );

    const buttons = screen.getAllByRole('button');
    expect(buttons[0]).toHaveClass('rounded-b-none'); // first
    expect(buttons[1]).toHaveClass('rounded-none'); // middle
    expect(buttons[2]).toHaveClass('rounded-t-none'); // last
  });

  it('applies vertical layout classes', () => {
    render(
      <Button.Group vertical>
        <Button>First</Button>
        <Button>Second</Button>
      </Button.Group>
    );

    const group = screen.getAllByRole('button')[0].parentElement;
    expect(group).toHaveClass('flex-col');
  });

  it('applies horizontal layout classes by default', () => {
    render(
      <Button.Group>
        <Button>First</Button>
        <Button>Second</Button>
      </Button.Group>
    );

    const group = screen.getAllByRole('button')[0].parentElement;
    expect(group).toHaveClass('flex-row');
  });

  it('applies custom className to group', () => {
    render(
      <Button.Group className="custom-group">
        <Button>First</Button>
        <Button>Second</Button>
      </Button.Group>
    );

    const group = screen.getAllByRole('button')[0].parentElement;
    expect(group).toHaveClass('custom-group');
  });

  it('applies border adjustments for horizontal group', () => {
    render(
      <Button.Group>
        <Button>First</Button>
        <Button>Second</Button>
        <Button>Third</Button>
      </Button.Group>
    );

    const buttons = screen.getAllByRole('button');
    expect(buttons[0]).toHaveClass('-mr-px');
    expect(buttons[1]).toHaveClass('-mr-px');
    expect(buttons[2]).not.toHaveClass('-mr-px'); // last button
  });

  it('applies border adjustments for vertical group', () => {
    render(
      <Button.Group vertical>
        <Button>First</Button>
        <Button>Second</Button>
        <Button>Third</Button>
      </Button.Group>
    );

    const buttons = screen.getAllByRole('button');
    expect(buttons[0]).toHaveClass('-mb-px');
    expect(buttons[1]).toHaveClass('-mb-px');
    expect(buttons[2]).not.toHaveClass('-mb-px'); // last button
  });

  it('sets role="group" on group container', () => {
    render(
      <Button.Group>
        <Button>First</Button>
        <Button>Second</Button>
      </Button.Group>
    );

    const group = screen.getAllByRole('button')[0].parentElement;
    expect(group).toHaveAttribute('role', 'group');
  });
});