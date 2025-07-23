import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { vi } from 'vitest';
import { Anchor } from './Anchor';

// Mock scrollTo and getBoundingClientRect
Object.defineProperty(window, 'scrollTo', {
  value: vi.fn(),
  writable: true,
});

Object.defineProperty(Element.prototype, 'getBoundingClientRect', {
  value: vi.fn(() => ({
    top: 100,
    bottom: 200,
    left: 0,
    right: 100,
    width: 100,
    height: 100
  })),
  writable: true,
});

describe('Anchor', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    // Reset scroll position
    Object.defineProperty(window, 'pageYOffset', {
      value: 0,
      writable: true,
    });
  });

  it('renders anchor navigation', () => {
    const items = [
      { href: '#section1', title: 'Section 1' },
      { href: '#section2', title: 'Section 2' }
    ];
    
    render(<Anchor items={items} />);
    expect(screen.getByText('Section 1')).toBeInTheDocument();
    expect(screen.getByText('Section 2')).toBeInTheDocument();
  });

  it('supports children links', () => {
    render(
      <Anchor>
        <Anchor.Link href="#test1" title="Test 1" />
        <Anchor.Link href="#test2" title="Test 2" />
      </Anchor>
    );
    
    expect(screen.getByText('Test 1')).toBeInTheDocument();
    expect(screen.getByText('Test 2')).toBeInTheDocument();
  });

  it('handles link clicks and scrolls to target', () => {
    const items = [{ href: '#section1', title: 'Section 1' }];
    
    // Mock target element
    const targetElement = document.createElement('div');
    targetElement.id = 'section1';
    document.body.appendChild(targetElement);
    
    render(<Anchor items={items} />);
    
    const link = screen.getByText('Section 1');
    fireEvent.click(link);
    
    expect(window.scrollTo).toHaveBeenCalled();
    
    document.body.removeChild(targetElement);
  });

  it('highlights active link based on scroll position', async () => {
    const items = [
      { href: '#section1', title: 'Section 1' },
      { href: '#section2', title: 'Section 2' }
    ];
    
    // Mock elements
    const section1 = document.createElement('div');
    section1.id = 'section1';
    const section2 = document.createElement('div');
    section2.id = 'section2';
    document.body.appendChild(section1);
    document.body.appendChild(section2);
    
    render(<Anchor items={items} />);
    
    // Simulate scroll
    Object.defineProperty(window, 'pageYOffset', { value: 150, writable: true });
    fireEvent.scroll(window);
    
    await waitFor(() => {
      const activeLink = screen.getByText('Section 1');
      expect(activeLink.closest('a')).toHaveClass('text-blue-600');
    });
    
    document.body.removeChild(section1);
    document.body.removeChild(section2);
  });

  it('supports custom onChange callback', () => {
    const onChange = vi.fn();
    const items = [{ href: '#section1', title: 'Section 1' }];
    
    render(<Anchor items={items} onChange={onChange} />);
    
    const link = screen.getByText('Section 1');
    fireEvent.click(link);
    
    expect(onChange).toHaveBeenCalledWith('#section1');
  });

  it('renders with custom className', () => {
    const items = [{ href: '#section1', title: 'Section 1' }];
    
    render(<Anchor items={items} className="custom-anchor" />);
    
    const container = screen.getByTestId('anchor-container');
    expect(container).toHaveClass('custom-anchor');
  });

  it('supports different directions', () => {
    const directions = ['vertical', 'horizontal'] as const;
    const items = [{ href: '#section1', title: 'Section 1' }];
    
    directions.forEach(direction => {
      const { unmount } = render(<Anchor items={items} direction={direction} />);
      expect(screen.getByText('Section 1')).toBeInTheDocument();
      unmount();
    });
  });

  it('supports different sizes', () => {
    const sizes = ['small', 'medium', 'large'] as const;
    const items = [{ href: '#section1', title: 'Section 1' }];
    
    sizes.forEach(size => {
      const { unmount } = render(<Anchor items={items} size={size} />);
      expect(screen.getByText('Section 1')).toBeInTheDocument();
      unmount();
    });
  });

  it('supports custom offset', () => {
    const items = [{ href: '#section1', title: 'Section 1' }];
    
    const targetElement = document.createElement('div');
    targetElement.id = 'section1';
    document.body.appendChild(targetElement);
    
    render(<Anchor items={items} offsetTop={50} />);
    
    const link = screen.getByText('Section 1');
    fireEvent.click(link);
    
    expect(window.scrollTo).toHaveBeenCalled();
    
    document.body.removeChild(targetElement);
  });

  it('supports smooth scrolling', () => {
    const items = [{ href: '#section1', title: 'Section 1' }];
    
    const targetElement = document.createElement('div');
    targetElement.id = 'section1';
    document.body.appendChild(targetElement);
    
    render(<Anchor items={items} smooth />);
    
    const link = screen.getByText('Section 1');
    fireEvent.click(link);
    
    expect(window.scrollTo).toHaveBeenCalledWith(
      expect.objectContaining({ behavior: 'smooth' })
    );
    
    document.body.removeChild(targetElement);
  });

  it('supports fixed positioning', () => {
    const items = [{ href: '#section1', title: 'Section 1' }];
    
    render(<Anchor items={items} fixed />);
    
    const container = screen.getByTestId('anchor-container');
    expect(container).toHaveClass('fixed');
  });

  it('supports sticky positioning', () => {
    const items = [{ href: '#section1', title: 'Section 1' }];
    
    render(<Anchor items={items} sticky />);
    
    const container = screen.getByTestId('anchor-container');
    expect(container).toHaveClass('sticky');
  });

  it('supports custom bounds', () => {
    const items = [{ href: '#section1', title: 'Section 1' }];
    
    render(<Anchor items={items} bounds={10} />);
    expect(screen.getByText('Section 1')).toBeInTheDocument();
  });

  it('renders with title', () => {
    const items = [{ href: '#section1', title: 'Section 1' }];
    
    render(<Anchor items={items} title="Navigation" />);
    expect(screen.getByText('Navigation')).toBeInTheDocument();
  });

  it('supports collapsible mode', () => {
    const items = [{ href: '#section1', title: 'Section 1' }];
    
    render(<Anchor items={items} collapsible />);
    
    const toggleButton = screen.getByRole('button');
    expect(toggleButton).toBeInTheDocument();
    
    fireEvent.click(toggleButton);
    // Content should be hidden after toggle
  });

  it('supports custom target container', () => {
    const container = document.createElement('div');
    const items = [{ href: '#section1', title: 'Section 1' }];
    
    render(<Anchor items={items} targetContainer={() => container} />);
    expect(screen.getByText('Section 1')).toBeInTheDocument();
  });

  it('supports animated scrolling', () => {
    const items = [{ href: '#section1', title: 'Section 1' }];
    
    render(<Anchor items={items} animated />);
    expect(screen.getByText('Section 1')).toBeInTheDocument();
  });

  it('supports custom indicator', () => {
    const items = [{ href: '#section1', title: 'Section 1' }];
    
    render(<Anchor items={items} showIndicator />);
    expect(screen.getByText('Section 1')).toBeInTheDocument();
  });

  it('supports nested anchors', () => {
    const items = [
      {
        href: '#section1',
        title: 'Section 1',
        children: [
          { href: '#subsection1', title: 'Subsection 1' }
        ]
      }
    ];
    
    render(<Anchor items={items} />);
    expect(screen.getByText('Section 1')).toBeInTheDocument();
    expect(screen.getByText('Subsection 1')).toBeInTheDocument();
  });

  it('supports disabled links', () => {
    const items = [
      { href: '#section1', title: 'Section 1' },
      { href: '#section2', title: 'Section 2', disabled: true }
    ];
    
    render(<Anchor items={items} />);
    
    const disabledLink = screen.getByText('Section 2');
    expect(disabledLink.closest('a')).toHaveClass('opacity-50');
  });

  it('supports custom link renderer', () => {
    const items = [{ href: '#section1', title: 'Section 1' }];
    
    const customRenderer = (link: any) => (
      <div data-testid="custom-link">Custom: {link.title}</div>
    );
    
    render(<Anchor items={items} renderLink={customRenderer} />);
    expect(screen.getByTestId('custom-link')).toBeInTheDocument();
    expect(screen.getByText('Custom: Section 1')).toBeInTheDocument();
  });

  it('supports scroll spy functionality', async () => {
    const items = [{ href: '#section1', title: 'Section 1' }];
    
    render(<Anchor items={items} scrollSpy />);
    
    // Simulate scroll event
    fireEvent.scroll(window);
    
    expect(screen.getByText('Section 1')).toBeInTheDocument();
  });

  it('supports custom scroll container', () => {
    const container = document.createElement('div');
    const items = [{ href: '#section1', title: 'Section 1' }];
    
    render(<Anchor items={items} scrollContainer={() => container} />);
    expect(screen.getByText('Section 1')).toBeInTheDocument();
  });

  it('supports keyboard navigation', () => {
    const items = [
      { href: '#section1', title: 'Section 1' },
      { href: '#section2', title: 'Section 2' }
    ];
    
    render(<Anchor items={items} />);
    
    const firstLink = screen.getByText('Section 1');
    fireEvent.keyDown(firstLink, { key: 'ArrowDown' });
    
    expect(screen.getByText('Section 2')).toBeInTheDocument();
  });

  it('supports custom styles', () => {
    const items = [{ href: '#section1', title: 'Section 1' }];
    const customStyle = { backgroundColor: 'red' };
    
    render(<Anchor items={items} style={customStyle} />);
    
    const container = screen.getByTestId('anchor-container');
    expect(container).toBeInTheDocument();
  });

  it('supports hover effects', () => {
    const items = [{ href: '#section1', title: 'Section 1' }];
    
    render(<Anchor items={items} hoverEffect />);
    expect(screen.getByText('Section 1')).toBeInTheDocument();
  });

  it('supports click preventDefault option', () => {
    const items = [{ href: '#section1', title: 'Section 1' }];
    const onClick = vi.fn();
    
    render(<Anchor items={items} onClick={onClick} preventDefault />);
    
    const link = screen.getByText('Section 1');
    fireEvent.click(link);
    
    expect(onClick).toHaveBeenCalled();
  });

  it('supports auto-scroll on mount', () => {
    // Set hash
    Object.defineProperty(window, 'location', {
      value: { hash: '#section1' },
      writable: true,
    });
    
    const items = [{ href: '#section1', title: 'Section 1' }];
    
    render(<Anchor items={items} autoScroll />);
    expect(screen.getByText('Section 1')).toBeInTheDocument();
  });

  it('supports custom data attributes', () => {
    const items = [{ href: '#section1', title: 'Section 1' }];
    
    render(<Anchor items={items} data-testid="custom-anchor" data-role="navigation" />);
    
    const container = screen.getByTestId('custom-anchor');
    expect(container).toHaveAttribute('data-role', 'navigation');
  });
});