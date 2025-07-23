import { render, screen } from '@testing-library/react';
import { Divider } from './Divider';

describe('Divider', () => {
  it('renders horizontal divider by default', () => {
    render(<Divider />);
    const divider = screen.getByRole('separator');
    expect(divider).toBeInTheDocument();
  });

  it('renders with text content', () => {
    render(<Divider>Section Break</Divider>);
    expect(screen.getByText('Section Break')).toBeInTheDocument();
  });

  it('renders vertical divider', () => {
    render(<Divider orientation="vertical" />);
    const divider = screen.getByRole('separator');
    expect(divider).toHaveAttribute('aria-orientation', 'vertical');
  });

  it('supports different text alignments', () => {
    const alignments = ['left', 'center', 'right'] as const;
    
    alignments.forEach(align => {
      const { unmount } = render(<Divider textAlign={align}>Aligned Text</Divider>);
      expect(screen.getByText('Aligned Text')).toBeInTheDocument();
      unmount();
    });
  });

  it('renders with different variants', () => {
    const variants = ['solid', 'dashed', 'dotted'] as const;
    
    variants.forEach(variant => {
      const { unmount } = render(<Divider variant={variant} />);
      const divider = screen.getByRole('separator');
      expect(divider).toBeInTheDocument();
      unmount();
    });
  });

  it('supports different thickness options', () => {
    const thicknesses = ['thin', 'medium', 'thick'] as const;
    
    thicknesses.forEach(thickness => {
      const { unmount } = render(<Divider thickness={thickness} />);
      const divider = screen.getByRole('separator');
      expect(divider).toBeInTheDocument();
      unmount();
    });
  });

  it('renders with custom colors', () => {
    const colors = ['gray', 'red', 'blue', 'green'] as const;
    
    colors.forEach(color => {
      const { unmount } = render(<Divider color={color} />);
      const divider = screen.getByRole('separator');
      expect(divider).toBeInTheDocument();
      unmount();
    });
  });

  it('supports custom spacing', () => {
    const spacings = ['small', 'medium', 'large'] as const;
    
    spacings.forEach(spacing => {
      const { unmount } = render(<Divider spacing={spacing} />);
      const divider = screen.getByRole('separator');
      expect(divider).toBeInTheDocument();
      unmount();
    });
  });

  it('renders with icon', () => {
    const icon = <span data-testid="divider-icon">⭐</span>;
    render(<Divider icon={icon} />);
    expect(screen.getByTestId('divider-icon')).toBeInTheDocument();
  });

  it('supports custom className', () => {
    render(<Divider className="custom-divider">Custom</Divider>);
    expect(screen.getByText('Custom')).toBeInTheDocument();
  });

  it('renders plain divider without text', () => {
    render(<Divider plain />);
    const divider = screen.getByRole('separator');
    expect(divider).toBeInTheDocument();
  });

  it('supports flex layout integration', () => {
    render(<Divider flex />);
    const divider = screen.getByRole('separator');
    expect(divider).toBeInTheDocument();
  });

  it('renders with gradient effect', () => {
    render(<Divider gradient />);
    const divider = screen.getByRole('separator');
    expect(divider).toBeInTheDocument();
  });

  it('supports animated divider', () => {
    render(<Divider animated />);
    const divider = screen.getByRole('separator');
    expect(divider).toBeInTheDocument();
  });

  it('renders with custom width/height', () => {
    render(<Divider width="50%" height="2px" />);
    const divider = screen.getByRole('separator');
    expect(divider).toBeInTheDocument();
  });

  it('supports margin customization', () => {
    render(<Divider margin="10px 20px" />);
    const divider = screen.getByRole('separator');
    expect(divider).toBeInTheDocument();
  });

  it('renders with shadow effect', () => {
    render(<Divider shadow />);
    const divider = screen.getByRole('separator');
    expect(divider).toBeInTheDocument();
  });

  it('supports borderless style', () => {
    render(<Divider borderless>Borderless</Divider>);
    expect(screen.getByText('Borderless')).toBeInTheDocument();
  });

  it('renders with custom content element', () => {
    const customContent = <div data-testid="custom-content">Custom Element</div>;
    render(<Divider>{customContent}</Divider>);
    expect(screen.getByTestId('custom-content')).toBeInTheDocument();
  });

  it('supports inset divider', () => {
    render(<Divider inset />);
    const divider = screen.getByRole('separator');
    expect(divider).toBeInTheDocument();
  });

  it('renders with rounded caps', () => {
    render(<Divider rounded />);
    const divider = screen.getByRole('separator');
    expect(divider).toBeInTheDocument();
  });

  it('supports opacity customization', () => {
    render(<Divider opacity={0.5} />);
    const divider = screen.getByRole('separator');
    expect(divider).toBeInTheDocument();
  });

  it('renders with text and icon together', () => {
    const icon = <span data-testid="combo-icon">🔹</span>;
    render(<Divider icon={icon}>With Icon</Divider>);
    expect(screen.getByText('With Icon')).toBeInTheDocument();
    expect(screen.getByTestId('combo-icon')).toBeInTheDocument();
  });

  it('supports custom line pattern', () => {
    render(<Divider pattern="wavy" />);
    const divider = screen.getByRole('separator');
    expect(divider).toBeInTheDocument();
  });

  it('handles very long text content', () => {
    const longText = 'This is a very long text content that should be handled properly by the divider component';
    render(<Divider>{longText}</Divider>);
    expect(screen.getByText(longText)).toBeInTheDocument();
  });

  it('renders section divider variant', () => {
    render(<Divider type="section">Section Title</Divider>);
    expect(screen.getByText('Section Title')).toBeInTheDocument();
  });

  it('supports responsive behavior', () => {
    render(<Divider responsive />);
    const divider = screen.getByRole('separator');
    expect(divider).toBeInTheDocument();
  });

  it('renders with custom data attributes', () => {
    render(<Divider data-testid="custom-divider" data-section="header" />);
    const divider = screen.getByTestId('custom-divider');
    expect(divider).toHaveAttribute('data-section', 'header');
  });
});