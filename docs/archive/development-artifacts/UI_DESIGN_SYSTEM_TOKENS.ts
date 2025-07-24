// ITDO ERP Design System Tokens
// Phoenix Rising - Beautiful Code Day Foundation

export const designTokens = {
  // Color System
  colors: {
    // Primary Palette
    primary: {
      50: '#e3f2fd',
      100: '#bbdefb',
      200: '#90caf9',
      300: '#64b5f6',
      400: '#42a5f5',
      500: '#2196f3', // Main
      600: '#1e88e5',
      700: '#1976d2',
      800: '#1565c0',
      900: '#0d47a1',
    },
    
    // Secondary Palette
    secondary: {
      50: '#fce4ec',
      100: '#f8bbd0',
      200: '#f48fb1',
      300: '#f06292',
      400: '#ec407a',
      500: '#e91e63', // Main
      600: '#d81b60',
      700: '#c2185b',
      800: '#ad1457',
      900: '#880e4f',
    },
    
    // Success
    success: {
      50: '#e8f5e9',
      100: '#c8e6c9',
      200: '#a5d6a7',
      300: '#81c784',
      400: '#66bb6a',
      500: '#4caf50', // Main
      600: '#43a047',
      700: '#388e3c',
      800: '#2e7d32',
      900: '#1b5e20',
    },
    
    // Warning
    warning: {
      50: '#fff3e0',
      100: '#ffe0b2',
      200: '#ffcc80',
      300: '#ffb74d',
      400: '#ffa726',
      500: '#ff9800', // Main
      600: '#fb8c00',
      700: '#f57c00',
      800: '#ef6c00',
      900: '#e65100',
    },
    
    // Error/Danger
    error: {
      50: '#ffebee',
      100: '#ffcdd2',
      200: '#ef9a9a',
      300: '#e57373',
      400: '#ef5350',
      500: '#f44336', // Main
      600: '#e53935',
      700: '#d32f2f',
      800: '#c62828',
      900: '#b71c1c',
    },
    
    // Neutral/Gray
    gray: {
      50: '#fafafa',
      100: '#f5f5f5',
      200: '#eeeeee',
      300: '#e0e0e0',
      400: '#bdbdbd',
      500: '#9e9e9e',
      600: '#757575',
      700: '#616161',
      800: '#424242',
      900: '#212121',
    },
    
    // Semantic Colors
    background: {
      default: '#ffffff',
      paper: '#fafafa',
      dark: '#121212',
    },
    
    text: {
      primary: 'rgba(0, 0, 0, 0.87)',
      secondary: 'rgba(0, 0, 0, 0.6)',
      disabled: 'rgba(0, 0, 0, 0.38)',
      hint: 'rgba(0, 0, 0, 0.38)',
      dark: {
        primary: 'rgba(255, 255, 255, 0.87)',
        secondary: 'rgba(255, 255, 255, 0.6)',
        disabled: 'rgba(255, 255, 255, 0.38)',
      },
    },
  },
  
  // Typography System
  typography: {
    fontFamily: {
      sans: "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
      serif: "'Merriweather', 'Georgia', serif",
      mono: "'Fira Code', 'Monaco', 'Courier New', monospace",
    },
    
    fontSize: {
      xs: '0.75rem',    // 12px
      sm: '0.875rem',   // 14px
      base: '1rem',     // 16px
      lg: '1.125rem',   // 18px
      xl: '1.25rem',    // 20px
      '2xl': '1.5rem',  // 24px
      '3xl': '1.875rem',// 30px
      '4xl': '2.25rem', // 36px
      '5xl': '3rem',    // 48px
      '6xl': '3.75rem', // 60px
      '7xl': '4.5rem',  // 72px
      '8xl': '6rem',    // 96px
      '9xl': '8rem',    // 128px
    },
    
    fontWeight: {
      thin: 100,
      extralight: 200,
      light: 300,
      normal: 400,
      medium: 500,
      semibold: 600,
      bold: 700,
      extrabold: 800,
      black: 900,
    },
    
    lineHeight: {
      none: 1,
      tight: 1.25,
      snug: 1.375,
      normal: 1.5,
      relaxed: 1.625,
      loose: 2,
    },
    
    letterSpacing: {
      tighter: '-0.05em',
      tight: '-0.025em',
      normal: '0em',
      wide: '0.025em',
      wider: '0.05em',
      widest: '0.1em',
    },
  },
  
  // Spacing System (8px base)
  spacing: {
    px: '1px',
    0: '0px',
    0.5: '0.125rem', // 2px
    1: '0.25rem',    // 4px
    1.5: '0.375rem', // 6px
    2: '0.5rem',     // 8px
    2.5: '0.625rem', // 10px
    3: '0.75rem',    // 12px
    3.5: '0.875rem', // 14px
    4: '1rem',       // 16px
    5: '1.25rem',    // 20px
    6: '1.5rem',     // 24px
    7: '1.75rem',    // 28px
    8: '2rem',       // 32px
    9: '2.25rem',    // 36px
    10: '2.5rem',    // 40px
    11: '2.75rem',   // 44px
    12: '3rem',      // 48px
    14: '3.5rem',    // 56px
    16: '4rem',      // 64px
    20: '5rem',      // 80px
    24: '6rem',      // 96px
    28: '7rem',      // 112px
    32: '8rem',      // 128px
    36: '9rem',      // 144px
    40: '10rem',     // 160px
    44: '11rem',     // 176px
    48: '12rem',     // 192px
    52: '13rem',     // 208px
    56: '14rem',     // 224px
    60: '15rem',     // 240px
    64: '16rem',     // 256px
    72: '18rem',     // 288px
    80: '20rem',     // 320px
    96: '24rem',     // 384px
  },
  
  // Border Radius
  borderRadius: {
    none: '0px',
    sm: '0.125rem',  // 2px
    DEFAULT: '0.25rem', // 4px
    md: '0.375rem',  // 6px
    lg: '0.5rem',    // 8px
    xl: '0.75rem',   // 12px
    '2xl': '1rem',   // 16px
    '3xl': '1.5rem', // 24px
    full: '9999px',
  },
  
  // Box Shadow
  boxShadow: {
    xs: '0 0 0 1px rgba(0, 0, 0, 0.05)',
    sm: '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
    DEFAULT: '0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06)',
    md: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
    lg: '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)',
    xl: '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)',
    '2xl': '0 25px 50px -12px rgba(0, 0, 0, 0.25)',
    inner: 'inset 0 2px 4px 0 rgba(0, 0, 0, 0.06)',
    none: 'none',
  },
  
  // Z-Index Scale
  zIndex: {
    auto: 'auto',
    0: '0',
    10: '10',
    20: '20',
    30: '30',
    40: '40',
    50: '50',
    dropdown: '1000',
    sticky: '1020',
    fixed: '1030',
    modalBackdrop: '1040',
    modal: '1050',
    popover: '1060',
    tooltip: '1070',
  },
  
  // Animation
  animation: {
    duration: {
      fast: '150ms',
      base: '300ms',
      slow: '450ms',
      slower: '600ms',
    },
    
    timing: {
      ease: 'cubic-bezier(0.4, 0, 0.2, 1)',
      easeIn: 'cubic-bezier(0.4, 0, 1, 1)',
      easeOut: 'cubic-bezier(0, 0, 0.2, 1)',
      easeInOut: 'cubic-bezier(0.4, 0, 0.2, 1)',
      linear: 'linear',
    },
  },
  
  // Breakpoints
  breakpoints: {
    xs: '475px',
    sm: '640px',
    md: '768px',
    lg: '1024px',
    xl: '1280px',
    '2xl': '1536px',
  },
  
  // Component-specific tokens
  components: {
    button: {
      height: {
        sm: '32px',
        md: '40px',
        lg: '48px',
      },
      padding: {
        sm: '0 12px',
        md: '0 16px',
        lg: '0 24px',
      },
    },
    
    input: {
      height: {
        sm: '32px',
        md: '40px',
        lg: '48px',
      },
      padding: '0 12px',
    },
    
    card: {
      padding: {
        sm: '16px',
        md: '24px',
        lg: '32px',
      },
    },
    
    modal: {
      width: {
        sm: '400px',
        md: '600px',
        lg: '800px',
        xl: '1000px',
      },
    },
  },
}

// Utility function to get nested token values
export const getToken = (path: string): any => {
  return path.split('.').reduce((obj, key) => obj?.[key], designTokens)
}

// CSS custom properties generator
export const generateCSSVariables = () => {
  const cssVars: Record<string, string> = {}
  
  // Colors
  Object.entries(designTokens.colors).forEach(([colorName, colorValues]) => {
    if (typeof colorValues === 'object' && !Array.isArray(colorValues)) {
      Object.entries(colorValues).forEach(([shade, value]) => {
        cssVars[`--color-${colorName}-${shade}`] = value as string
      })
    }
  })
  
  // Spacing
  Object.entries(designTokens.spacing).forEach(([key, value]) => {
    cssVars[`--spacing-${key}`] = value
  })
  
  // Typography
  Object.entries(designTokens.typography.fontSize).forEach(([key, value]) => {
    cssVars[`--font-size-${key}`] = value
  })
  
  // Border Radius
  Object.entries(designTokens.borderRadius).forEach(([key, value]) => {
    cssVars[`--radius-${key}`] = value
  })
  
  // Shadows
  Object.entries(designTokens.boxShadow).forEach(([key, value]) => {
    cssVars[`--shadow-${key}`] = value
  })
  
  return cssVars
}

// Tailwind config extension
export const tailwindExtend = {
  colors: designTokens.colors,
  spacing: designTokens.spacing,
  fontFamily: designTokens.typography.fontFamily,
  fontSize: designTokens.typography.fontSize,
  fontWeight: designTokens.typography.fontWeight,
  lineHeight: designTokens.typography.lineHeight,
  letterSpacing: designTokens.typography.letterSpacing,
  borderRadius: designTokens.borderRadius,
  boxShadow: designTokens.boxShadow,
  zIndex: designTokens.zIndex,
  screens: designTokens.breakpoints,
}