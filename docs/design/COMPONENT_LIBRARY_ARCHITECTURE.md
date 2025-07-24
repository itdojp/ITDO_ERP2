# Component Library Architecture

**Document ID**: ITDO-ERP-DD-CLA-001  
**Version**: 1.0  
**Date**: 2025-07-16  
**Author**: Claude Code AI  
**Issue**: #160  

---

## 1. Overview

This document defines the architectural structure and organization of the ITDO ERP2 component library, providing a scalable foundation for UI component development and maintenance.

## 2. Library Structure

### 2.1 Directory Organization

```
frontend/src/components/
├── ui/                     # Core UI components
│   ├── Button/
│   │   ├── Button.tsx
│   │   ├── Button.test.tsx
│   │   ├── Button.stories.tsx
│   │   ├── Button.types.ts
│   │   └── index.ts
│   ├── Input/
│   ├── Select/
│   ├── Card/
│   ├── Modal/
│   └── index.ts           # Barrel export
├── forms/                 # Form-specific components
│   ├── FormField/
│   ├── FormGroup/
│   ├── ValidationMessage/
│   └── index.ts
├── navigation/            # Navigation components
│   ├── Sidebar/
│   ├── TopNav/
│   ├── Breadcrumb/
│   └── index.ts
├── layout/               # Layout components
│   ├── Container/
│   ├── Grid/
│   ├── Stack/
│   └── index.ts
├── feedback/             # Feedback components
│   ├── Alert/
│   ├── Toast/
│   ├── Loading/
│   └── index.ts
├── data-display/         # Data display components
│   ├── Table/
│   ├── List/
│   ├── Chart/
│   └── index.ts
├── providers/            # Context providers
│   ├── ThemeProvider/
│   ├── ToastProvider/
│   └── index.ts
├── hooks/                # Custom hooks
│   ├── useTheme.ts
│   ├── useToast.ts
│   ├── useLocalStorage.ts
│   └── index.ts
├── utils/                # Utility functions
│   ├── cn.ts            # Class name utility
│   ├── variants.ts      # Variant utilities
│   └── index.ts
└── index.ts             # Main barrel export
```

### 2.2 Component File Structure

Each component follows a consistent structure:

```typescript
// Component.types.ts
export interface ComponentProps {
  variant?: 'primary' | 'secondary';
  size?: 'sm' | 'md' | 'lg';
  disabled?: boolean;
  children?: React.ReactNode;
}

// Component.tsx
import { ComponentProps } from './Component.types';

export const Component: React.FC<ComponentProps> = ({
  variant = 'primary',
  size = 'md',
  disabled = false,
  children,
  ...props
}) => {
  // Implementation
};

// Component.test.tsx
import { render, screen } from '@testing-library/react';
import { Component } from './Component';

describe('Component', () => {
  it('renders correctly', () => {
    render(<Component>Test</Component>);
    expect(screen.getByText('Test')).toBeInTheDocument();
  });
});

// Component.stories.tsx
import type { Meta, StoryObj } from '@storybook/react';
import { Component } from './Component';

const meta: Meta<typeof Component> = {
  title: 'UI/Component',
  component: Component,
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
};

export default meta;
type Story = StoryObj<typeof Component>;

export const Primary: Story = {
  args: {
    variant: 'primary',
    children: 'Button',
  },
};

// index.ts
export { Component } from './Component';
export type { ComponentProps } from './Component.types';
```

## 3. Design System Integration

### 3.1 Theme Provider

```typescript
// providers/ThemeProvider/ThemeProvider.tsx
import { createContext, useContext } from 'react';
import { designTokens } from '../../constants/design-tokens';

interface ThemeContextType {
  tokens: typeof designTokens;
  isDark: boolean;
  toggleTheme: () => void;
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

export const ThemeProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [isDark, setIsDark] = useState(false);

  const toggleTheme = () => {
    setIsDark(!isDark);
  };

  return (
    <ThemeContext.Provider value={{ tokens: designTokens, isDark, toggleTheme }}>
      {children}
    </ThemeContext.Provider>
  );
};

export const useTheme = () => {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
};
```

### 3.2 Design Token Integration

```typescript
// constants/design-tokens.ts
export const designTokens = {
  colors: {
    primary: {
      50: '#eff6ff',
      100: '#dbeafe',
      // ... rest of color scale
    },
    // ... other color schemes
  },
  typography: {
    fontFamily: {
      sans: ['Inter', 'system-ui', 'sans-serif'],
      mono: ['JetBrains Mono', 'monospace'],
    },
    fontSize: {
      xs: '0.75rem',
      sm: '0.875rem',
      // ... rest of sizes
    },
  },
  spacing: {
    // ... spacing values
  },
  // ... other token categories
};
```

### 3.3 Variant System

```typescript
// utils/variants.ts
import { cva, type VariantProps } from 'class-variance-authority';

export const buttonVariants = cva(
  'inline-flex items-center justify-center rounded-md text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50',
  {
    variants: {
      variant: {
        primary: 'bg-primary text-primary-foreground hover:bg-primary/90',
        secondary: 'bg-secondary text-secondary-foreground hover:bg-secondary/80',
        outline: 'border border-input hover:bg-accent hover:text-accent-foreground',
        ghost: 'hover:bg-accent hover:text-accent-foreground',
        danger: 'bg-destructive text-destructive-foreground hover:bg-destructive/90',
      },
      size: {
        sm: 'h-8 px-3 text-xs',
        md: 'h-10 px-4 py-2',
        lg: 'h-12 px-8 text-base',
      },
    },
    defaultVariants: {
      variant: 'primary',
      size: 'md',
    },
  }
);

export type ButtonVariants = VariantProps<typeof buttonVariants>;
```

## 4. Component Patterns

### 4.1 Compound Components

```typescript
// ui/Select/Select.tsx
import { createContext, useContext } from 'react';

interface SelectContextType {
  value: string;
  onChange: (value: string) => void;
  isOpen: boolean;
  toggleOpen: () => void;
}

const SelectContext = createContext<SelectContextType | undefined>(undefined);

export const Select: React.FC<{
  value: string;
  onChange: (value: string) => void;
  children: React.ReactNode;
}> = ({ value, onChange, children }) => {
  const [isOpen, setIsOpen] = useState(false);

  const toggleOpen = () => setIsOpen(!isOpen);

  return (
    <SelectContext.Provider value={{ value, onChange, isOpen, toggleOpen }}>
      <div className="relative">{children}</div>
    </SelectContext.Provider>
  );
};

export const SelectTrigger: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const context = useContext(SelectContext);
  if (!context) throw new Error('SelectTrigger must be used within Select');

  return (
    <button
      onClick={context.toggleOpen}
      className="flex items-center justify-between w-full px-3 py-2 text-left bg-white border border-gray-300 rounded-md"
    >
      {children}
    </button>
  );
};

export const SelectContent: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const context = useContext(SelectContext);
  if (!context) throw new Error('SelectContent must be used within Select');

  if (!context.isOpen) return null;

  return (
    <div className="absolute top-full left-0 right-0 mt-1 bg-white border border-gray-300 rounded-md shadow-lg z-50">
      {children}
    </div>
  );
};

export const SelectItem: React.FC<{
  value: string;
  children: React.ReactNode;
}> = ({ value, children }) => {
  const context = useContext(SelectContext);
  if (!context) throw new Error('SelectItem must be used within Select');

  return (
    <div
      onClick={() => {
        context.onChange(value);
        context.toggleOpen();
      }}
      className="px-3 py-2 hover:bg-gray-100 cursor-pointer"
    >
      {children}
    </div>
  );
};
```

### 4.2 Polymorphic Components

```typescript
// ui/Button/Button.tsx
import { forwardRef } from 'react';
import { Slot } from '@radix-ui/react-slot';

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  asChild?: boolean;
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost' | 'danger';
  size?: 'sm' | 'md' | 'lg';
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ asChild = false, variant = 'primary', size = 'md', className, ...props }, ref) => {
    const Comp = asChild ? Slot : 'button';
    
    return (
      <Comp
        ref={ref}
        className={cn(buttonVariants({ variant, size, className }))}
        {...props}
      />
    );
  }
);

Button.displayName = 'Button';
```

### 4.3 Render Props Pattern

```typescript
// ui/DataFetcher/DataFetcher.tsx
interface DataFetcherProps<T> {
  url: string;
  children: (data: {
    data: T | null;
    loading: boolean;
    error: string | null;
    refetch: () => void;
  }) => React.ReactNode;
}

export const DataFetcher = <T,>({ url, children }: DataFetcherProps<T>) => {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await fetch(url);
      if (!response.ok) throw new Error('Failed to fetch');
      const result = await response.json();
      setData(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  }, [url]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return <>{children({ data, loading, error, refetch: fetchData })}</>;
};
```

## 5. State Management

### 5.1 Component State

```typescript
// hooks/useToggle.ts
export const useToggle = (initialValue: boolean = false) => {
  const [value, setValue] = useState(initialValue);

  const toggle = useCallback(() => setValue(prev => !prev), []);
  const setTrue = useCallback(() => setValue(true), []);
  const setFalse = useCallback(() => setValue(false), []);

  return { value, toggle, setTrue, setFalse };
};

// hooks/useLocalStorage.ts
export const useLocalStorage = <T>(key: string, initialValue: T) => {
  const [storedValue, setStoredValue] = useState<T>(() => {
    try {
      const item = window.localStorage.getItem(key);
      return item ? JSON.parse(item) : initialValue;
    } catch (error) {
      console.warn(`Error reading localStorage key "${key}":`, error);
      return initialValue;
    }
  });

  const setValue = useCallback((value: T | ((val: T) => T)) => {
    try {
      const valueToStore = value instanceof Function ? value(storedValue) : value;
      setStoredValue(valueToStore);
      window.localStorage.setItem(key, JSON.stringify(valueToStore));
    } catch (error) {
      console.warn(`Error setting localStorage key "${key}":`, error);
    }
  }, [key, storedValue]);

  return [storedValue, setValue] as const;
};
```

### 5.2 Global State

```typescript
// providers/AppProvider.tsx
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ThemeProvider } from './ThemeProvider';
import { ToastProvider } from './ToastProvider';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 3,
      staleTime: 5 * 60 * 1000, // 5 minutes
    },
  },
});

export const AppProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider>
        <ToastProvider>
          {children}
        </ToastProvider>
      </ThemeProvider>
    </QueryClientProvider>
  );
};
```

## 6. Accessibility Architecture

### 6.1 Focus Management

```typescript
// hooks/useFocusManagement.ts
export const useFocusManagement = () => {
  const previousActiveElement = useRef<HTMLElement | null>(null);

  const trapFocus = useCallback((containerRef: React.RefObject<HTMLElement>) => {
    const container = containerRef.current;
    if (!container) return;

    const focusableElements = container.querySelectorAll(
      'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
    );

    const firstElement = focusableElements[0] as HTMLElement;
    const lastElement = focusableElements[focusableElements.length - 1] as HTMLElement;

    const handleTabKey = (e: KeyboardEvent) => {
      if (e.key === 'Tab') {
        if (e.shiftKey) {
          if (document.activeElement === firstElement) {
            lastElement.focus();
            e.preventDefault();
          }
        } else {
          if (document.activeElement === lastElement) {
            firstElement.focus();
            e.preventDefault();
          }
        }
      }
    };

    document.addEventListener('keydown', handleTabKey);
    return () => document.removeEventListener('keydown', handleTabKey);
  }, []);

  const restoreFocus = useCallback(() => {
    if (previousActiveElement.current) {
      previousActiveElement.current.focus();
      previousActiveElement.current = null;
    }
  }, []);

  const saveFocus = useCallback(() => {
    previousActiveElement.current = document.activeElement as HTMLElement;
  }, []);

  return { trapFocus, restoreFocus, saveFocus };
};
```

### 6.2 ARIA Utilities

```typescript
// utils/aria.ts
export const generateId = (prefix: string = 'id') => {
  return `${prefix}-${Math.random().toString(36).substr(2, 9)}`;
};

export const getAriaProps = (props: Record<string, any>) => {
  return Object.keys(props).reduce((acc, key) => {
    if (key.startsWith('aria-') || key === 'role') {
      acc[key] = props[key];
    }
    return acc;
  }, {} as Record<string, any>);
};

export const useAriaLive = () => {
  const [message, setMessage] = useState('');
  const [politeness, setPoliteness] = useState<'polite' | 'assertive'>('polite');

  const announce = useCallback((text: string, priority: 'polite' | 'assertive' = 'polite') => {
    setPoliteness(priority);
    setMessage(text);
    
    // Clear message after announcement
    setTimeout(() => setMessage(''), 1000);
  }, []);

  return { message, politeness, announce };
};
```

## 7. Testing Architecture

### 7.1 Test Utilities

```typescript
// test/utils.tsx
import { render, RenderOptions } from '@testing-library/react';
import { ReactElement } from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ThemeProvider } from '../components/providers/ThemeProvider';

const createTestQueryClient = () => new QueryClient({
  defaultOptions: {
    queries: {
      retry: false,
    },
    mutations: {
      retry: false,
    },
  },
});

const AllTheProviders: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const queryClient = createTestQueryClient();

  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider>
        {children}
      </ThemeProvider>
    </QueryClientProvider>
  );
};

const customRender = (
  ui: ReactElement,
  options?: Omit<RenderOptions, 'wrapper'>
) => render(ui, { wrapper: AllTheProviders, ...options });

export * from '@testing-library/react';
export { customRender as render };
```

### 7.2 Component Testing Patterns

```typescript
// ui/Button/Button.test.tsx
import { render, screen } from '../../test/utils';
import userEvent from '@testing-library/user-event';
import { Button } from './Button';

describe('Button', () => {
  it('renders with correct variant classes', () => {
    render(<Button variant="primary">Click me</Button>);
    expect(screen.getByRole('button')).toHaveClass('bg-primary');
  });

  it('handles click events', async () => {
    const user = userEvent.setup();
    const handleClick = jest.fn();
    
    render(<Button onClick={handleClick}>Click me</Button>);
    await user.click(screen.getByRole('button'));
    
    expect(handleClick).toHaveBeenCalledTimes(1);
  });

  it('is disabled when disabled prop is true', () => {
    render(<Button disabled>Click me</Button>);
    expect(screen.getByRole('button')).toBeDisabled();
  });

  it('has correct accessibility attributes', () => {
    render(<Button aria-label="Custom label">Click me</Button>);
    expect(screen.getByRole('button')).toHaveAccessibleName('Custom label');
  });
});
```

## 8. Performance Optimization

### 8.1 Code Splitting

```typescript
// components/lazy.ts
import { lazy } from 'react';

export const LazyChart = lazy(() => import('./data-display/Chart'));
export const LazyTable = lazy(() => import('./data-display/Table'));
export const LazyModal = lazy(() => import('./feedback/Modal'));
```

### 8.2 Memoization

```typescript
// ui/Button/Button.tsx
import { memo, forwardRef } from 'react';

export const Button = memo(
  forwardRef<HTMLButtonElement, ButtonProps>(
    ({ variant = 'primary', size = 'md', className, ...props }, ref) => {
      return (
        <button
          ref={ref}
          className={cn(buttonVariants({ variant, size, className }))}
          {...props}
        />
      );
    }
  )
);

Button.displayName = 'Button';
```

### 8.3 Virtual Scrolling

```typescript
// ui/VirtualList/VirtualList.tsx
import { FixedSizeList as List } from 'react-window';

interface VirtualListProps<T> {
  items: T[];
  height: number;
  itemHeight: number;
  renderItem: (item: T, index: number) => React.ReactNode;
}

export const VirtualList = <T,>({ items, height, itemHeight, renderItem }: VirtualListProps<T>) => {
  const Row = ({ index, style }: { index: number; style: React.CSSProperties }) => (
    <div style={style}>
      {renderItem(items[index], index)}
    </div>
  );

  return (
    <List
      height={height}
      itemCount={items.length}
      itemSize={itemHeight}
      width="100%"
    >
      {Row}
    </List>
  );
};
```

## 9. Build and Bundle Strategy

### 9.1 Vite Configuration

```typescript
// vite.config.ts
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import { resolve } from 'path';

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': resolve(__dirname, './src'),
      '@/components': resolve(__dirname, './src/components'),
      '@/utils': resolve(__dirname, './src/utils'),
      '@/hooks': resolve(__dirname, './src/hooks'),
    },
  },
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          'react-vendor': ['react', 'react-dom'],
          'ui-components': ['./src/components/ui/index.ts'],
          'form-components': ['./src/components/forms/index.ts'],
          'data-display': ['./src/components/data-display/index.ts'],
        },
      },
    },
  },
});
```

### 9.2 Tree Shaking

```typescript
// components/index.ts
// Named exports for better tree shaking
export { Button } from './ui/Button';
export { Input } from './ui/Input';
export { Select } from './ui/Select';
export { Card } from './ui/Card';
export { Modal } from './feedback/Modal';
export { Table } from './data-display/Table';

// Type exports
export type { ButtonProps } from './ui/Button';
export type { InputProps } from './ui/Input';
export type { SelectProps } from './ui/Select';
```

## 10. Documentation Strategy

### 10.1 Storybook Configuration

```typescript
// .storybook/main.ts
import type { StorybookConfig } from '@storybook/react-vite';

const config: StorybookConfig = {
  stories: ['../src/**/*.stories.@(js|jsx|ts|tsx)'],
  addons: [
    '@storybook/addon-essentials',
    '@storybook/addon-a11y',
    '@storybook/addon-design-tokens',
  ],
  framework: {
    name: '@storybook/react-vite',
    options: {},
  },
  features: {
    autodocs: true,
  },
};

export default config;
```

### 10.2 Component Documentation

```typescript
// ui/Button/Button.stories.tsx
import type { Meta, StoryObj } from '@storybook/react';
import { Button } from './Button';

const meta: Meta<typeof Button> = {
  title: 'UI/Button',
  component: Button,
  parameters: {
    layout: 'centered',
    docs: {
      description: {
        component: 'The Button component is used to trigger actions or events.',
      },
    },
  },
  argTypes: {
    variant: {
      control: 'select',
      options: ['primary', 'secondary', 'outline', 'ghost', 'danger'],
    },
    size: {
      control: 'select',
      options: ['sm', 'md', 'lg'],
    },
    disabled: {
      control: 'boolean',
    },
  },
  tags: ['autodocs'],
};

export default meta;
type Story = StoryObj<typeof Button>;

export const Primary: Story = {
  args: {
    variant: 'primary',
    children: 'Button',
  },
};

export const AllVariants: Story = {
  render: () => (
    <div className="flex gap-4">
      <Button variant="primary">Primary</Button>
      <Button variant="secondary">Secondary</Button>
      <Button variant="outline">Outline</Button>
      <Button variant="ghost">Ghost</Button>
      <Button variant="danger">Danger</Button>
    </div>
  ),
};
```

## 11. Maintenance and Scalability

### 11.1 Version Management

```json
// package.json
{
  "name": "@itdo/ui-components",
  "version": "1.0.0",
  "peerDependencies": {
    "react": "^18.0.0",
    "react-dom": "^18.0.0"
  },
  "dependencies": {
    "@radix-ui/react-slot": "^1.0.2",
    "class-variance-authority": "^0.7.0",
    "clsx": "^2.0.0",
    "tailwind-merge": "^2.0.0"
  }
}
```

### 11.2 Migration Strategy

```typescript
// utils/migration.ts
export const DEPRECATED_COMPONENTS = {
  OldButton: 'Use Button from @itdo/ui-components instead',
  LegacyModal: 'Use Modal from @itdo/ui-components instead',
};

export const warnDeprecation = (componentName: string) => {
  const message = DEPRECATED_COMPONENTS[componentName as keyof typeof DEPRECATED_COMPONENTS];
  if (message && process.env.NODE_ENV === 'development') {
    console.warn(`[DEPRECATED] ${componentName}: ${message}`);
  }
};
```

### 11.3 Component Registry

```typescript
// registry/components.ts
export const COMPONENT_REGISTRY = {
  'ui/button': () => import('../components/ui/Button'),
  'ui/input': () => import('../components/ui/Input'),
  'ui/select': () => import('../components/ui/Select'),
  'feedback/modal': () => import('../components/feedback/Modal'),
  'data-display/table': () => import('../components/data-display/Table'),
} as const;

export type ComponentKey = keyof typeof COMPONENT_REGISTRY;

export const loadComponent = async (key: ComponentKey) => {
  const loader = COMPONENT_REGISTRY[key];
  return await loader();
};
```

## 12. Conclusion

This component library architecture provides:

1. **Scalability**: Organized structure supports growth and maintenance
2. **Consistency**: Standardized patterns across all components
3. **Performance**: Optimized for bundle size and runtime performance
4. **Accessibility**: Built-in accessibility patterns and testing
5. **Developer Experience**: TypeScript support, testing utilities, and documentation
6. **Maintainability**: Clear organization and deprecation strategies

The architecture supports the current needs of the ITDO ERP2 project while providing a foundation for future enhancements and scaling.

---

**Document Status**: ✅ Ready for Implementation  
**Next Steps**: Component implementation following this architecture  
**Dependencies**: Design tokens, UI specifications, testing framework  

---

*This architecture document serves as the foundation for all component development in the ITDO ERP2 project.*