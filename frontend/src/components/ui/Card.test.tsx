import { render, fireEvent, screen } from '@testing-library/react';
import { Card } from './Card';

describe('Card', () => {
  it('renders card content', () => {
    render(<Card>Card content</Card>);
    expect(screen.getByText('Card content')).toBeInTheDocument();
  });

  it('applies default variant classes', () => {
    render(<Card>Default card</Card>);
    const card = screen.getByText('Default card').closest('div');
    expect(card).toHaveClass('bg-white');
  });

  it('applies outlined variant classes', () => {
    render(<Card variant="outlined">Outlined card</Card>);
    const card = screen.getByText('Outlined card').closest('div');
    expect(card).toHaveClass('bg-white', 'border', 'border-gray-200');
  });

  it('applies elevated variant classes', () => {
    render(<Card variant="elevated">Elevated card</Card>);
    const card = screen.getByText('Elevated card').closest('div');
    expect(card).toHaveClass('bg-white');
  });

  it('applies filled variant classes', () => {
    render(<Card variant="filled">Filled card</Card>);
    const card = screen.getByText('Filled card').closest('div');
    expect(card).toHaveClass('bg-gray-50');
  });

  it('applies small size classes', () => {
    render(<Card size="sm">Small card</Card>);
    const cardContent = screen.getByText('Small card').parentElement;
    expect(cardContent).toHaveClass('p-4');
  });

  it('applies medium size classes', () => {
    render(<Card size="md">Medium card</Card>);
    const cardContent = screen.getByText('Medium card').parentElement;
    expect(cardContent).toHaveClass('p-6');
  });

  it('applies large size classes', () => {
    render(<Card size="lg">Large card</Card>);
    const cardContent = screen.getByText('Large card').parentElement;
    expect(cardContent).toHaveClass('p-8');
  });

  it('applies compact padding when compact is true', () => {
    render(<Card compact>Compact card</Card>);
    const cardContent = screen.getByText('Compact card').parentElement;
    expect(cardContent).toHaveClass('p-3');
  });

  it('applies rounded corners by default', () => {
    render(<Card>Rounded card</Card>);
    const card = screen.getByText('Rounded card').closest('div');
    expect(card).toHaveClass('rounded-lg');
  });

  it('removes rounded corners when rounded is false', () => {
    render(<Card rounded={false}>Square card</Card>);
    const card = screen.getByText('Square card').closest('div');
    expect(card).not.toHaveClass('rounded-lg');
  });

  it('applies shadow classes', () => {
    render(<Card shadow="lg">Shadow card</Card>);
    const card = screen.getByText('Shadow card').closest('div');
    expect(card).toHaveClass('shadow-lg');
  });

  it('applies no shadow when shadow is none', () => {
    render(<Card shadow="none">No shadow card</Card>);
    const card = screen.getByText('No shadow card').closest('div');
    expect(card).not.toHaveClass('shadow-sm', 'shadow-md', 'shadow-lg', 'shadow-xl');
  });

  it('applies border when bordered is true', () => {
    render(<Card bordered>Bordered card</Card>);
    const card = screen.getByText('Bordered card').closest('div');
    expect(card).toHaveClass('border', 'border-gray-200');
  });

  it('applies hover effects when hoverable is true', () => {
    render(<Card hoverable>Hoverable card</Card>);
    const card = screen.getByText('Hoverable card').closest('div');
    expect(card).toHaveClass('transition-all', 'duration-200', 'hover:shadow-lg', 'hover:-translate-y-1');
  });

  it('applies hover effects when clickable is true', () => {
    render(<Card clickable onClick={jest.fn()}>Clickable card</Card>);
    const card = screen.getByText('Clickable card').closest('div');
    expect(card).toHaveClass('transition-all', 'duration-200', 'hover:shadow-lg', 'hover:-translate-y-1');
  });

  it('renders as button when onClick is provided', () => {
    render(<Card onClick={jest.fn()}>Button card</Card>);
    const card = screen.getByRole('button');
    expect(card).toBeInTheDocument();
    expect(card).toHaveAttribute('type', 'button');
  });

  it('renders as link when href is provided', () => {
    render(<Card href="/test">Link card</Card>);
    const card = screen.getByRole('link');
    expect(card).toBeInTheDocument();
    expect(card).toHaveAttribute('href', '/test');
  });

  it('calls onClick when card is clicked', () => {
    const onClick = jest.fn();
    render(<Card onClick={onClick}>Clickable card</Card>);
    
    fireEvent.click(screen.getByRole('button'));
    
    expect(onClick).toHaveBeenCalledTimes(1);
  });

  it('handles keyboard navigation with Enter key', () => {
    const onClick = jest.fn();
    render(<Card onClick={onClick}>Keyboard card</Card>);
    
    const card = screen.getByRole('button');
    fireEvent.keyDown(card, { key: 'Enter' });
    
    expect(onClick).toHaveBeenCalledTimes(1);
  });

  it('handles keyboard navigation with Space key', () => {
    const onClick = jest.fn();
    render(<Card onClick={onClick}>Keyboard card</Card>);
    
    const card = screen.getByRole('button');
    fireEvent.keyDown(card, { key: ' ' });
    
    expect(onClick).toHaveBeenCalledTimes(1);
  });

  it('applies disabled state correctly', () => {
    const onClick = jest.fn();
    render(<Card onClick={onClick} disabled>Disabled card</Card>);
    
    const card = screen.getByText('Disabled card').closest('div');
    expect(card).toHaveClass('opacity-50', 'cursor-not-allowed');
    expect(card).toHaveAttribute('aria-disabled', 'true');
    
    fireEvent.click(card!);
    expect(onClick).not.toHaveBeenCalled();
  });

  it('applies loading state correctly', () => {
    render(<Card loading>Loading card</Card>);
    
    const card = screen.getByText('Loading card').closest('div');
    expect(card).toHaveClass('animate-pulse', 'cursor-wait');
    expect(card).toHaveAttribute('aria-busy', 'true');
    expect(screen.getByText('Loading...')).toBeInTheDocument();
  });

  it('renders header when provided', () => {
    render(<Card header={<div>Custom header</div>}>Card content</Card>);
    expect(screen.getByText('Custom header')).toBeInTheDocument();
  });

  it('renders title and subtitle', () => {
    render(<Card title="Card Title" subtitle="Card subtitle">Card content</Card>);
    expect(screen.getByText('Card Title')).toBeInTheDocument();
    expect(screen.getByText('Card subtitle')).toBeInTheDocument();
  });

  it('renders footer when provided', () => {
    render(<Card footer={<div>Custom footer</div>}>Card content</Card>);
    expect(screen.getByText('Custom footer')).toBeInTheDocument();
  });

  it('renders actions when provided', () => {
    render(<Card actions={<button>Action</button>}>Card content</Card>);
    expect(screen.getByText('Action')).toBeInTheDocument();
  });

  it('renders image at top position', () => {
    render(<Card image="/test.jpg" imageAlt="Test image" imagePosition="top">Card content</Card>);
    const image = screen.getByAltText('Test image');
    expect(image).toBeInTheDocument();
    expect(image).toHaveAttribute('src', '/test.jpg');
  });

  it('renders image at bottom position', () => {
    render(<Card image="/test.jpg" imageAlt="Test image" imagePosition="bottom">Card content</Card>);
    const image = screen.getByAltText('Test image');
    expect(image).toBeInTheDocument();
  });

  it('renders image at left position', () => {
    render(<Card image="/test.jpg" imageAlt="Test image" imagePosition="left">Card content</Card>);
    const image = screen.getByAltText('Test image');
    expect(image).toBeInTheDocument();
  });

  it('renders image at right position', () => {
    render(<Card image="/test.jpg" imageAlt="Test image" imagePosition="right">Card content</Card>);
    const image = screen.getByAltText('Test image');
    expect(image).toBeInTheDocument();
  });

  it('renders custom React node as image', () => {
    render(<Card image={<div data-testid="custom-image">Custom Image</div>}>Card content</Card>);
    expect(screen.getByTestId('custom-image')).toBeInTheDocument();
  });

  it('applies custom className', () => {
    render(<Card className="custom-card">Card content</Card>);
    const card = screen.getByText('Card content').closest('div');
    expect(card).toHaveClass('custom-card');
  });

  it('applies custom headerClassName', () => {
    render(<Card title="Title" headerClassName="custom-header">Card content</Card>);
    const header = screen.getByText('Title').closest('div');
    expect(header).toHaveClass('custom-header');
  });

  it('applies custom bodyClassName', () => {
    render(<Card bodyClassName="custom-body">Card content</Card>);
    const body = screen.getByText('Card content');
    expect(body).toHaveClass('custom-body');
  });

  it('applies custom footerClassName', () => {
    render(<Card footer={<div>Footer</div>} footerClassName="custom-footer">Card content</Card>);
    const footer = screen.getByText('Footer').closest('div');
    expect(footer).toHaveClass('custom-footer');
  });

  it('applies custom imageClassName', () => {
    render(<Card image="/test.jpg" imageClassName="custom-image">Card content</Card>);
    const image = screen.getByRole('img');
    expect(image).toHaveClass('custom-image');
  });

  it('applies custom titleClassName', () => {
    render(<Card title="Title" titleClassName="custom-title">Card content</Card>);
    const title = screen.getByText('Title');
    expect(title).toHaveClass('custom-title');
  });

  it('applies custom subtitleClassName', () => {
    render(<Card subtitle="Subtitle" subtitleClassName="custom-subtitle">Card content</Card>);
    const subtitle = screen.getByText('Subtitle');
    expect(subtitle).toHaveClass('custom-subtitle');
  });

  it('does not render header when no title, subtitle, or header provided', () => {
    render(<Card>Card content</Card>);
    const cardElement = screen.getByText('Card content').closest('div');
    // Check that there's no header element
    expect(cardElement?.querySelector('.mb-4')).not.toBeInTheDocument();
  });

  it('does not render footer when no footer or actions provided', () => {
    render(<Card>Card content</Card>);
    const cardElement = screen.getByText('Card content').closest('div');
    // Check that there's no footer element
    expect(cardElement?.querySelector('.mt-4')).not.toBeInTheDocument();
  });

  it('does not render image when image is not provided', () => {
    render(<Card>Card content</Card>);
    expect(screen.queryByRole('img')).not.toBeInTheDocument();
  });

  it('applies focus styles when interactive', () => {
    render(<Card onClick={jest.fn()}>Interactive card</Card>);
    const card = screen.getByRole('button');
    expect(card).toHaveClass('focus:outline-none', 'focus:ring-2', 'focus:ring-blue-500', 'focus:ring-offset-2');
  });

  it('does not apply focus styles when not interactive', () => {
    render(<Card>Static card</Card>);
    const card = screen.getByText('Static card').closest('div');
    expect(card).not.toHaveClass('focus:outline-none');
  });

  it('sets tabIndex to -1 when disabled and interactive', () => {
    render(<Card onClick={jest.fn()} disabled>Disabled interactive</Card>);
    const card = screen.getByText('Disabled interactive').closest('div');
    expect(card).toHaveAttribute('tabindex', '-1');
  });

  it('sets tabIndex to 0 when interactive and not disabled', () => {
    render(<Card onClick={jest.fn()}>Interactive card</Card>);
    const card = screen.getByRole('button');
    expect(card).toHaveAttribute('tabindex', '0');
  });

  it('does not render as link when disabled and href is provided', () => {
    render(<Card href="/test" disabled>Disabled link</Card>);
    const card = screen.getByText('Disabled link').closest('div');
    expect(card?.tagName).not.toBe('A');
  });

  it('prevents click when loading', () => {
    const onClick = jest.fn();
    render(<Card onClick={onClick} loading>Loading card</Card>);
    
    const card = screen.getByText('Loading card').closest('div');
    fireEvent.click(card!);
    
    expect(onClick).not.toHaveBeenCalled();
  });

  it('does not handle keyboard events when disabled', () => {
    const onClick = jest.fn();
    render(<Card onClick={onClick} disabled>Disabled card</Card>);
    
    const card = screen.getByText('Disabled card').closest('div');
    fireEvent.keyDown(card!, { key: 'Enter' });
    fireEvent.keyDown(card!, { key: ' ' });
    
    expect(onClick).not.toHaveBeenCalled();
  });

  it('does not handle keyboard events when loading', () => {
    const onClick = jest.fn();
    render(<Card onClick={onClick} loading>Loading card</Card>);
    
    const card = screen.getByText('Loading card').closest('div');
    fireEvent.keyDown(card!, { key: 'Enter' });
    fireEvent.keyDown(card!, { key: ' ' });
    
    expect(onClick).not.toHaveBeenCalled();
  });

  it('does not apply hover effects when disabled', () => {
    render(<Card hoverable disabled>Disabled hoverable</Card>);
    const card = screen.getByText('Disabled hoverable').closest('div');
    expect(card).not.toHaveClass('hover:shadow-lg');
  });

  it('does not apply hover effects when loading', () => {
    render(<Card hoverable loading>Loading hoverable</Card>);
    const card = screen.getByText('Loading hoverable').closest('div');
    expect(card).not.toHaveClass('hover:shadow-lg');
  });

  it('renders loading overlay with spinner', () => {
    render(<Card loading>Loading card</Card>);
    
    const spinner = screen.getByText('Loading card').closest('div')?.querySelector('.animate-spin');
    expect(spinner).toBeInTheDocument();
  });

  it('adjusts spacing for compact mode', () => {
    render(
      <Card compact title="Title" footer={<div>Footer</div>}>
        Content
      </Card>
    );
    
    const header = screen.getByText('Title').closest('div');
    const footer = screen.getByText('Footer').closest('div');
    
    expect(header).toHaveClass('mb-2');
    expect(footer).toHaveClass('mt-2');
  });

  it('uses default imageAlt when not provided', () => {
    render(<Card image="/test.jpg">Card content</Card>);
    const image = screen.getByRole('img');
    expect(image).toHaveAttribute('alt', '');
  });
});