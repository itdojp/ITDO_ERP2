import React, { useState } from 'react';

// Design Tokens Definition
const designTokens = {
  colors: {
    primary: {
      50: '#fff7ed',   // 最も薄いオレンジ
      100: '#ffedd5',
      200: '#fed7aa',
      300: '#fdba74',
      400: '#fb923c',
      500: '#f97316',  // メインオレンジ
      600: '#ea580c',
      700: '#c2410c',
      800: '#9a3412',
      900: '#7c2d12'   // 最も濃いオレンジ
    },
    neutral: {
      50: '#fafafa',
      100: '#f5f5f5',
      200: '#e5e5e5',
      300: '#d4d4d4',
      400: '#a3a3a3',
      500: '#737373',
      600: '#525252',
      700: '#404040',
      800: '#262626',
      900: '#171717'
    },
    semantic: {
      success: '#22c55e',
      warning: '#eab308',
      error: '#ef4444',
      info: '#3b82f6'
    }
  },
  typography: {
    fontFamily: {
      sans: 'Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
      mono: '"JetBrains Mono", Consolas, monospace'
    },
    fontSize: {
      xs: '12px',
      sm: '14px',
      base: '16px',
      lg: '18px',
      xl: '20px',
      '2xl': '24px'
    },
    fontWeight: {
      normal: '400',
      medium: '500',
      semibold: '600',
      bold: '700'
    }
  },
  spacing: {
    unit: 8,
    scale: [0, 4, 8, 12, 16, 24, 32, 48, 64, 96, 128]
  }
};

// Button Component with all variants and states
const Button = ({ 
  variant = 'primary', 
  size = 'md', 
  disabled = false, 
  loading = false, 
  children, 
  onClick 
}) => {
  const baseStyles = {
    fontFamily: designTokens.typography.fontFamily.sans,
    fontWeight: designTokens.typography.fontWeight.medium,
    borderRadius: '6px',
    border: 'none',
    cursor: disabled ? 'not-allowed' : 'pointer',
    transition: 'all 0.2s ease',
    display: 'inline-flex',
    alignItems: 'center',
    justifyContent: 'center',
    gap: '8px'
  };

  const sizeStyles = {
    sm: { 
      height: '32px', 
      padding: '0 12px', 
      fontSize: designTokens.typography.fontSize.sm 
    },
    md: { 
      height: '40px', 
      padding: '0 16px', 
      fontSize: designTokens.typography.fontSize.base 
    },
    lg: { 
      height: '48px', 
      padding: '0 24px', 
      fontSize: designTokens.typography.fontSize.lg 
    }
  };

  const variantStyles = {
    primary: {
      backgroundColor: designTokens.colors.primary[500],
      color: 'white'
    },
    secondary: {
      backgroundColor: designTokens.colors.neutral[100],
      color: designTokens.colors.neutral[700]
    },
    outline: {
      backgroundColor: 'transparent',
      color: designTokens.colors.primary[500],
      border: `1px solid ${designTokens.colors.primary[500]}`
    },
    ghost: {
      backgroundColor: 'transparent',
      color: designTokens.colors.neutral[700]
    },
    danger: {
      backgroundColor: designTokens.colors.semantic.error,
      color: 'white'
    }
  };

  const styles = {
    ...baseStyles,
    ...sizeStyles[size],
    ...variantStyles[variant],
    opacity: disabled ? 0.5 : 1
  };

  return (
    <button
      style={styles}
      disabled={disabled}
      onClick={onClick}
    >
      {loading && <span>⏳</span>}
      {children}
    </button>
  );
};

// Input Component
const Input = ({ 
  label, 
  placeholder, 
  value, 
  onChange, 
  error, 
  disabled = false, 
  type = 'text' 
}) => {
  const containerStyles = {
    display: 'flex',
    flexDirection: 'column',
    gap: '4px'
  };

  const inputStyles = {
    fontFamily: designTokens.typography.fontFamily.sans,
    fontSize: designTokens.typography.fontSize.base,
    padding: '8px 12px',
    borderRadius: '4px',
    border: `1px solid ${error ? designTokens.colors.semantic.error : designTokens.colors.neutral[300]}`,
    backgroundColor: disabled ? designTokens.colors.neutral[50] : 'white',
    color: designTokens.colors.neutral[700],
    outline: 'none',
    transition: 'border-color 0.2s ease'
  };

  const labelStyles = {
    fontFamily: designTokens.typography.fontFamily.sans,
    fontSize: designTokens.typography.fontSize.sm,
    fontWeight: designTokens.typography.fontWeight.medium,
    color: designTokens.colors.neutral[700]
  };

  const errorStyles = {
    fontFamily: designTokens.typography.fontFamily.sans,
    fontSize: designTokens.typography.fontSize.xs,
    color: designTokens.colors.semantic.error
  };

  return (
    <div style={containerStyles}>
      {label && <label style={labelStyles}>{label}</label>}
      <input
        style={inputStyles}
        type={type}
        placeholder={placeholder}
        value={value}
        onChange={onChange}
        disabled={disabled}
      />
      {error && <span style={errorStyles}>{error}</span>}
    </div>
  );
};

// Card Component
const Card = ({ children, header, footer, interactive = false }) => {
  const cardStyles = {
    backgroundColor: 'white',
    border: `1px solid ${designTokens.colors.neutral[200]}`,
    borderRadius: '8px',
    boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)',
    overflow: 'hidden',
    cursor: interactive ? 'pointer' : 'default',
    transition: 'box-shadow 0.2s ease'
  };

  const headerStyles = {
    padding: '16px',
    borderBottom: `1px solid ${designTokens.colors.neutral[200]}`,
    fontWeight: designTokens.typography.fontWeight.semibold
  };

  const contentStyles = {
    padding: '16px'
  };

  const footerStyles = {
    padding: '16px',
    borderTop: `1px solid ${designTokens.colors.neutral[200]}`,
    backgroundColor: designTokens.colors.neutral[50]
  };

  return (
    <div style={cardStyles}>
      {header && <div style={headerStyles}>{header}</div>}
      <div style={contentStyles}>{children}</div>
      {footer && <div style={footerStyles}>{footer}</div>}
    </div>
  );
};

// DesignSystemDemo Component
const DesignSystemDemo = () => {
  const [inputValue, setInputValue] = useState('');
  const [selectValue, setSelectValue] = useState('');
  const [checkboxValue, setCheckboxValue] = useState(false);

  const containerStyles = {
    fontFamily: designTokens.typography.fontFamily.sans,
    maxWidth: '1200px',
    margin: '0 auto',
    padding: '32px'
  };

  const sectionStyles = {
    marginBottom: '48px'
  };

  const titleStyles = {
    fontSize: designTokens.typography.fontSize['2xl'],
    fontWeight: designTokens.typography.fontWeight.bold,
    marginBottom: '24px',
    color: designTokens.colors.neutral[800]
  };

  const subtitleStyles = {
    fontSize: designTokens.typography.fontSize.lg,
    fontWeight: designTokens.typography.fontWeight.semibold,
    marginBottom: '16px',
    color: designTokens.colors.neutral[700]
  };

  const gridStyles = {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
    gap: '16px',
    marginBottom: '24px'
  };

  const colorBoxStyles = (color) => ({
    width: '100%',
    height: '60px',
    backgroundColor: color,
    borderRadius: '4px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    color: 'white',
    fontSize: designTokens.typography.fontSize.sm,
    fontWeight: designTokens.typography.fontWeight.medium
  });

  return (
    <div style={containerStyles}>
      <h1 style={titleStyles}>ITDO ERP Design System</h1>
      
      {/* Design Tokens */}
      <section style={sectionStyles}>
        <h2 style={subtitleStyles}>Design Tokens</h2>
        
        <h3 style={{ ...subtitleStyles, fontSize: designTokens.typography.fontSize.base }}>
          Primary Colors
        </h3>
        <div style={gridStyles}>
          {Object.entries(designTokens.colors.primary).map(([key, color]) => (
            <div key={key} style={colorBoxStyles(color)}>
              {key}: {color}
            </div>
          ))}
        </div>

        <h3 style={{ ...subtitleStyles, fontSize: designTokens.typography.fontSize.base }}>
          Semantic Colors
        </h3>
        <div style={gridStyles}>
          {Object.entries(designTokens.colors.semantic).map(([key, color]) => (
            <div key={key} style={colorBoxStyles(color)}>
              {key}: {color}
            </div>
          ))}
        </div>
      </section>

      {/* Buttons */}
      <section style={sectionStyles}>
        <h2 style={subtitleStyles}>Buttons</h2>
        
        <div style={{ display: 'flex', gap: '16px', marginBottom: '16px' }}>
          <Button variant="primary">Primary</Button>
          <Button variant="secondary">Secondary</Button>
          <Button variant="outline">Outline</Button>
          <Button variant="ghost">Ghost</Button>
          <Button variant="danger">Danger</Button>
        </div>

        <div style={{ display: 'flex', gap: '16px', marginBottom: '16px' }}>
          <Button size="sm">Small</Button>
          <Button size="md">Medium</Button>
          <Button size="lg">Large</Button>
        </div>

        <div style={{ display: 'flex', gap: '16px' }}>
          <Button disabled>Disabled</Button>
          <Button loading>Loading</Button>
        </div>
      </section>

      {/* Inputs */}
      <section style={sectionStyles}>
        <h2 style={subtitleStyles}>Form Components</h2>
        
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '16px' }}>
          <Input
            label="Username"
            placeholder="Enter username"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
          />
          <Input
            label="Email"
            placeholder="Enter email"
            type="email"
            error="Please enter a valid email"
          />
          <Input
            label="Disabled Field"
            placeholder="This field is disabled"
            disabled
          />
        </div>
      </section>

      {/* Cards */}
      <section style={sectionStyles}>
        <h2 style={subtitleStyles}>Cards</h2>
        
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '16px' }}>
          <Card
            header="Simple Card"
            footer="Card Footer"
          >
            <p>This is a simple card with header and footer.</p>
          </Card>
          
          <Card
            header="Interactive Card"
            interactive
          >
            <p>This card is interactive - try clicking on it.</p>
          </Card>
          
          <Card>
            <p>This card has no header or footer.</p>
          </Card>
        </div>
      </section>

      {/* Typography */}
      <section style={sectionStyles}>
        <h2 style={subtitleStyles}>Typography</h2>
        
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <div style={{ fontSize: designTokens.typography.fontSize['2xl'], fontWeight: designTokens.typography.fontWeight.bold }}>
            Heading 1 - 2xl Bold
          </div>
          <div style={{ fontSize: designTokens.typography.fontSize.xl, fontWeight: designTokens.typography.fontWeight.semibold }}>
            Heading 2 - xl Semibold
          </div>
          <div style={{ fontSize: designTokens.typography.fontSize.lg, fontWeight: designTokens.typography.fontWeight.medium }}>
            Heading 3 - lg Medium
          </div>
          <div style={{ fontSize: designTokens.typography.fontSize.base, fontWeight: designTokens.typography.fontWeight.normal }}>
            Body Text - base Normal
          </div>
          <div style={{ fontSize: designTokens.typography.fontSize.sm, fontWeight: designTokens.typography.fontWeight.normal }}>
            Small Text - sm Normal
          </div>
          <div style={{ fontSize: designTokens.typography.fontSize.xs, fontWeight: designTokens.typography.fontWeight.normal }}>
            Extra Small Text - xs Normal
          </div>
        </div>
      </section>

      {/* Spacing */}
      <section style={sectionStyles}>
        <h2 style={subtitleStyles}>Spacing Scale</h2>
        
        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
          {designTokens.spacing.scale.map((space, index) => (
            <div key={index} style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
              <div style={{ width: '40px', fontSize: designTokens.typography.fontSize.sm }}>
                {space}px
              </div>
              <div 
                style={{ 
                  width: `${space}px`, 
                  height: '24px', 
                  backgroundColor: designTokens.colors.primary[500],
                  borderRadius: '2px'
                }}
              />
            </div>
          ))}
        </div>
      </section>
    </div>
  );
};

export default DesignSystemDemo;