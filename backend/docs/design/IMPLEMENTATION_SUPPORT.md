# Implementation Support Documentation

**Document ID**: ITDO-ERP-DD-ISD-001  
**Version**: 1.0  
**Date**: 2025-07-16  
**Author**: Claude Code AI  
**Issue**: #160  

---

## 1. Overview

This document provides comprehensive implementation support for the ITDO ERP2 UI component design system. It includes step-by-step guides, code examples, troubleshooting tips, and best practices for developers and designers working with the component library.

## 2. Getting Started

### 2.1 Prerequisites

#### 2.1.1 Development Environment
```bash
# Required software versions
Node.js: 18.18.2+
npm: 9.8.1+
TypeScript: 5.2.2+
React: 18.2.0+
Vite: 4.5.0+

# Development tools
Git: 2.40.0+
VS Code: 1.85.0+ (recommended)
```

#### 2.1.2 Required Extensions (VS Code)
```json
{
  "recommendations": [
    "bradlc.vscode-tailwindcss",
    "ms-vscode.vscode-typescript-next",
    "esbenp.prettier-vscode",
    "ms-vscode.vscode-eslint",
    "bradlc.vscode-tailwindcss",
    "unifiedjs.vscode-mdx",
    "steoates.autoimport-es6-ts"
  ]
}
```

### 2.2 Initial Setup

#### 2.2.1 Project Structure Setup
```bash
# Create component library structure
mkdir -p frontend/src/components/ui
mkdir -p frontend/src/components/forms
mkdir -p frontend/src/components/navigation
mkdir -p frontend/src/components/layout
mkdir -p frontend/src/components/feedback
mkdir -p frontend/src/components/data-display
mkdir -p frontend/src/components/providers
mkdir -p frontend/src/hooks
mkdir -p frontend/src/utils
mkdir -p frontend/src/constants
```

#### 2.2.2 Install Dependencies
```bash
# Navigate to frontend directory
cd frontend

# Install core dependencies
npm install class-variance-authority clsx tailwind-merge
npm install @radix-ui/react-slot @radix-ui/react-dialog @radix-ui/react-dropdown-menu
npm install lucide-react
npm install react-hook-form @hookform/resolvers
npm install @tanstack/react-query

# Install dev dependencies
npm install --save-dev @types/react @types/react-dom
npm install --save-dev @storybook/react @storybook/addon-essentials
npm install --save-dev @testing-library/react @testing-library/jest-dom
npm install --save-dev jsdom vitest @vitest/ui
```

#### 2.2.3 Configuration Files

**TypeScript Configuration (tsconfig.json)**
```json
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx",
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true,
    "baseUrl": ".",
    "paths": {
      "@/*": ["./src/*"],
      "@/components/*": ["./src/components/*"],
      "@/utils/*": ["./src/utils/*"],
      "@/hooks/*": ["./src/hooks/*"],
      "@/constants/*": ["./src/constants/*"]
    }
  },
  "include": ["src"],
  "references": [{ "path": "./tsconfig.node.json" }]
}
```

**Tailwind Configuration (tailwind.config.js)**
```javascript
/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#eff6ff',
          100: '#dbeafe',
          200: '#bfdbfe',
          300: '#93c5fd',
          400: '#60a5fa',
          500: '#3b82f6',
          600: '#2563eb',
          700: '#1d4ed8',
          800: '#1e40af',
          900: '#1e3a8a',
        },
        secondary: {
          50: '#f8fafc',
          100: '#f1f5f9',
          200: '#e2e8f0',
          300: '#cbd5e1',
          400: '#94a3b8',
          500: '#64748b',
          600: '#475569',
          700: '#334155',
          800: '#1e293b',
          900: '#0f172a',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
      fontSize: {
        xs: ['0.75rem', { lineHeight: '1rem' }],
        sm: ['0.875rem', { lineHeight: '1.25rem' }],
        base: ['1rem', { lineHeight: '1.5rem' }],
        lg: ['1.125rem', { lineHeight: '1.75rem' }],
        xl: ['1.25rem', { lineHeight: '1.75rem' }],
        '2xl': ['1.5rem', { lineHeight: '2rem' }],
        '3xl': ['1.875rem', { lineHeight: '2.25rem' }],
        '4xl': ['2.25rem', { lineHeight: '2.5rem' }],
      },
      spacing: {
        '18': '4.5rem',
        '88': '22rem',
      },
      borderRadius: {
        'sm': '0.125rem',
        'md': '0.375rem',
        'lg': '0.5rem',
        'xl': '0.75rem',
        '2xl': '1rem',
      },
      boxShadow: {
        'sm': '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
        'md': '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
        'lg': '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)',
        'xl': '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)',
      },
    },
  },
  plugins: [],
}
```

## 3. Component Implementation Guide

### 3.1 Base Component Structure

#### 3.1.1 Component Template

```typescript
// components/ui/ComponentName/ComponentName.types.ts
export interface ComponentNameProps {
  variant?: 'primary' | 'secondary' | 'outline';
  size?: 'sm' | 'md' | 'lg';
  disabled?: boolean;
  loading?: boolean;
  children?: React.ReactNode;
  className?: string;
}

// components/ui/ComponentName/ComponentName.variants.ts
import { cva, type VariantProps } from 'class-variance-authority';

export const componentNameVariants = cva(
  // Base styles
  'inline-flex items-center justify-center rounded-md text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring disabled:pointer-events-none disabled:opacity-50',
  {
    variants: {
      variant: {
        primary: 'bg-primary-500 text-white hover:bg-primary-600',
        secondary: 'bg-secondary-500 text-white hover:bg-secondary-600',
        outline: 'border border-primary-500 text-primary-500 hover:bg-primary-50',
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

export type ComponentNameVariants = VariantProps<typeof componentNameVariants>;

// components/ui/ComponentName/ComponentName.tsx
import { forwardRef } from 'react';
import { cn } from '@/utils/cn';
import { componentNameVariants } from './ComponentName.variants';
import type { ComponentNameProps } from './ComponentName.types';

export const ComponentName = forwardRef<
  HTMLButtonElement,
  ComponentNameProps
>(({ variant, size, disabled, loading, className, children, ...props }, ref) => {
  return (
    <button
      ref={ref}
      disabled={disabled || loading}
      className={cn(componentNameVariants({ variant, size }), className)}
      {...props}
    >
      {loading && <LoadingSpinner />}
      {children}
    </button>
  );
});

ComponentName.displayName = 'ComponentName';

// components/ui/ComponentName/index.ts
export { ComponentName } from './ComponentName';
export type { ComponentNameProps } from './ComponentName.types';
```

#### 3.1.2 Utility Functions

```typescript
// utils/cn.ts
import { type ClassValue, clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

// utils/format.ts
export const formatDate = (date: Date): string => {
  return new Intl.DateTimeFormat('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  }).format(date);
};

export const formatCurrency = (amount: number): string => {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
  }).format(amount);
};

// utils/validation.ts
export const validateEmail = (email: string): boolean => {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email);
};

export const validatePassword = (password: string): {
  isValid: boolean;
  errors: string[];
} => {
  const errors: string[] = [];
  
  if (password.length < 8) {
    errors.push('Password must be at least 8 characters long');
  }
  
  if (!/[A-Z]/.test(password)) {
    errors.push('Password must contain at least one uppercase letter');
  }
  
  if (!/[a-z]/.test(password)) {
    errors.push('Password must contain at least one lowercase letter');
  }
  
  if (!/\d/.test(password)) {
    errors.push('Password must contain at least one number');
  }
  
  if (!/[!@#$%^&*(),.?":{}|<>]/.test(password)) {
    errors.push('Password must contain at least one special character');
  }
  
  return {
    isValid: errors.length === 0,
    errors,
  };
};
```

### 3.2 Component Development Workflow

#### 3.2.1 Step-by-Step Implementation

**Step 1: Create Component Structure**
```bash
# Create component directory
mkdir -p src/components/ui/Button

# Create component files
touch src/components/ui/Button/Button.tsx
touch src/components/ui/Button/Button.types.ts
touch src/components/ui/Button/Button.variants.ts
touch src/components/ui/Button/Button.stories.tsx
touch src/components/ui/Button/Button.test.tsx
touch src/components/ui/Button/index.ts
```

**Step 2: Implement Component Logic**
```typescript
// Follow the component template structure
// Implement props interface
// Add variant styles
// Include accessibility attributes
// Add proper TypeScript types
```

**Step 3: Add Storybook Documentation**
```typescript
// Button.stories.tsx
import type { Meta, StoryObj } from '@storybook/react';
import { Button } from './Button';

const meta: Meta<typeof Button> = {
  title: 'UI/Button',
  component: Button,
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
  argTypes: {
    variant: {
      control: 'select',
      options: ['primary', 'secondary', 'outline'],
    },
    size: {
      control: 'select',
      options: ['sm', 'md', 'lg'],
    },
    disabled: {
      control: 'boolean',
    },
    loading: {
      control: 'boolean',
    },
  },
};

export default meta;
type Story = StoryObj<typeof Button>;

export const Primary: Story = {
  args: {
    variant: 'primary',
    children: 'Button',
  },
};

export const Secondary: Story = {
  args: {
    variant: 'secondary',
    children: 'Button',
  },
};

export const AllVariants: Story = {
  render: () => (
    <div className="flex gap-4">
      <Button variant="primary">Primary</Button>
      <Button variant="secondary">Secondary</Button>
      <Button variant="outline">Outline</Button>
    </div>
  ),
};
```

**Step 4: Write Tests**
```typescript
// Button.test.tsx
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { Button } from './Button';

describe('Button', () => {
  it('renders correctly', () => {
    render(<Button>Click me</Button>);
    expect(screen.getByRole('button')).toBeInTheDocument();
    expect(screen.getByText('Click me')).toBeInTheDocument();
  });

  it('applies variant styles', () => {
    render(<Button variant="primary">Primary</Button>);
    expect(screen.getByRole('button')).toHaveClass('bg-primary-500');
  });

  it('handles click events', async () => {
    const user = userEvent.setup();
    const handleClick = jest.fn();
    
    render(<Button onClick={handleClick}>Click me</Button>);
    await user.click(screen.getByRole('button'));
    
    expect(handleClick).toHaveBeenCalledTimes(1);
  });

  it('is disabled when disabled prop is true', () => {
    render(<Button disabled>Disabled</Button>);
    expect(screen.getByRole('button')).toBeDisabled();
  });

  it('shows loading state', () => {
    render(<Button loading>Loading</Button>);
    expect(screen.getByRole('button')).toBeDisabled();
    expect(screen.getByText('Loading')).toBeInTheDocument();
  });
});
```

**Step 5: Export Component**
```typescript
// index.ts
export { Button } from './Button';
export type { ButtonProps } from './Button.types';

// components/ui/index.ts
export { Button } from './Button';
export type { ButtonProps } from './Button';
// ... other exports
```

### 3.3 Advanced Component Patterns

#### 3.3.1 Compound Components

```typescript
// components/ui/Select/Select.tsx
import { createContext, useContext, useState } from 'react';

interface SelectContextType {
  value: string;
  onChange: (value: string) => void;
  isOpen: boolean;
  setIsOpen: (isOpen: boolean) => void;
}

const SelectContext = createContext<SelectContextType | undefined>(undefined);

export const Select: React.FC<{
  value: string;
  onChange: (value: string) => void;
  children: React.ReactNode;
}> = ({ value, onChange, children }) => {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <SelectContext.Provider value={{ value, onChange, isOpen, setIsOpen }}>
      <div className="relative">{children}</div>
    </SelectContext.Provider>
  );
};

export const SelectTrigger: React.FC<{
  children: React.ReactNode;
  placeholder?: string;
}> = ({ children, placeholder }) => {
  const context = useContext(SelectContext);
  if (!context) {
    throw new Error('SelectTrigger must be used within Select');
  }

  return (
    <button
      onClick={() => context.setIsOpen(!context.isOpen)}
      className="flex items-center justify-between w-full px-3 py-2 text-left bg-white border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
    >
      {context.value || placeholder}
      <ChevronDown size={16} />
    </button>
  );
};

export const SelectContent: React.FC<{
  children: React.ReactNode;
}> = ({ children }) => {
  const context = useContext(SelectContext);
  if (!context) {
    throw new Error('SelectContent must be used within Select');
  }

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
  if (!context) {
    throw new Error('SelectItem must be used within Select');
  }

  return (
    <div
      onClick={() => {
        context.onChange(value);
        context.setIsOpen(false);
      }}
      className="px-3 py-2 hover:bg-gray-100 cursor-pointer"
    >
      {children}
    </div>
  );
};
```

#### 3.3.2 Polymorphic Components

```typescript
// components/ui/Button/Button.tsx
import { forwardRef, ElementType } from 'react';
import { Slot } from '@radix-ui/react-slot';

interface ButtonProps<T extends ElementType = 'button'> {
  as?: T;
  asChild?: boolean;
  variant?: 'primary' | 'secondary' | 'outline';
  size?: 'sm' | 'md' | 'lg';
  disabled?: boolean;
  children?: React.ReactNode;
  className?: string;
}

export const Button = forwardRef<
  HTMLButtonElement,
  ButtonProps
>(({ as: Component = 'button', asChild = false, variant = 'primary', size = 'md', className, ...props }, ref) => {
  const Comp = asChild ? Slot : Component;
  
  return (
    <Comp
      ref={ref}
      className={cn(buttonVariants({ variant, size }), className)}
      {...props}
    />
  );
});

// Usage examples
<Button>Regular Button</Button>
<Button as="a" href="/link">Link Button</Button>
<Button asChild>
  <Link to="/route">Router Link</Link>
</Button>
```

### 3.4 Form Component Integration

#### 3.4.1 React Hook Form Integration

```typescript
// components/forms/FormField/FormField.tsx
import { useFormContext } from 'react-hook-form';
import { cn } from '@/utils/cn';

interface FormFieldProps {
  name: string;
  label?: string;
  description?: string;
  required?: boolean;
  children: React.ReactNode;
  className?: string;
}

export const FormField = ({
  name,
  label,
  description,
  required,
  children,
  className,
}: FormFieldProps) => {
  const {
    formState: { errors },
  } = useFormContext();

  const error = errors[name];

  return (
    <div className={cn('space-y-2', className)}>
      {label && (
        <label
          htmlFor={name}
          className="block text-sm font-medium text-gray-700"
        >
          {label}
          {required && <span className="text-red-500 ml-1">*</span>}
        </label>
      )}
      
      <div className="relative">
        {children}
      </div>
      
      {description && (
        <p className="text-sm text-gray-500">{description}</p>
      )}
      
      {error && (
        <p className="text-sm text-red-600" role="alert">
          {error.message}
        </p>
      )}
    </div>
  );
};

// Usage with React Hook Form
const ExampleForm = () => {
  const form = useForm<FormData>({
    resolver: zodResolver(formSchema),
  });

  return (
    <FormProvider {...form}>
      <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
        <FormField
          name="email"
          label="Email Address"
          description="We'll never share your email with anyone else."
          required
        >
          <Input
            type="email"
            {...form.register('email')}
            placeholder="Enter your email"
          />
        </FormField>
        
        <FormField
          name="password"
          label="Password"
          required
        >
          <Input
            type="password"
            {...form.register('password')}
            placeholder="Enter your password"
          />
        </FormField>
        
        <Button type="submit" disabled={form.formState.isSubmitting}>
          {form.formState.isSubmitting ? 'Submitting...' : 'Submit'}
        </Button>
      </form>
    </FormProvider>
  );
};
```

## 4. Testing Strategy

### 4.1 Unit Testing

#### 4.1.1 Test Setup

```typescript
// src/test/setup.ts
import '@testing-library/jest-dom';
import { expect, afterEach } from 'vitest';
import { cleanup } from '@testing-library/react';

// Clean up after each test
afterEach(() => {
  cleanup();
});

// Add custom matchers
expect.extend({
  toHaveClass: (received, expected) => {
    const pass = received.classList.contains(expected);
    return {
      pass,
      message: () => 
        pass
          ? `Expected element not to have class "${expected}"`
          : `Expected element to have class "${expected}"`,
    };
  },
});
```

#### 4.1.2 Test Utilities

```typescript
// src/test/utils.tsx
import { render, RenderOptions } from '@testing-library/react';
import { ReactElement } from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter } from 'react-router-dom';

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

interface AllProvidersProps {
  children: React.ReactNode;
}

const AllProviders = ({ children }: AllProvidersProps) => {
  const queryClient = createTestQueryClient();

  return (
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>
        {children}
      </MemoryRouter>
    </QueryClientProvider>
  );
};

const customRender = (
  ui: ReactElement,
  options?: Omit<RenderOptions, 'wrapper'>
) => render(ui, { wrapper: AllProviders, ...options });

export * from '@testing-library/react';
export { customRender as render };
```

#### 4.1.3 Component Testing Patterns

```typescript
// Example component test
import { render, screen } from '@/test/utils';
import userEvent from '@testing-library/user-event';
import { Button } from './Button';

describe('Button Component', () => {
  it('renders with correct variant classes', () => {
    render(<Button variant="primary">Click me</Button>);
    expect(screen.getByRole('button')).toHaveClass('bg-primary-500');
  });

  it('handles click events correctly', async () => {
    const user = userEvent.setup();
    const handleClick = jest.fn();
    
    render(<Button onClick={handleClick}>Click me</Button>);
    await user.click(screen.getByRole('button'));
    
    expect(handleClick).toHaveBeenCalledTimes(1);
  });

  it('is accessible', () => {
    render(<Button aria-label="Custom button">Click me</Button>);
    expect(screen.getByRole('button')).toHaveAccessibleName('Custom button');
  });

  it('forwards refs correctly', () => {
    const ref = React.createRef<HTMLButtonElement>();
    render(<Button ref={ref}>Click me</Button>);
    expect(ref.current).toBeInstanceOf(HTMLButtonElement);
  });
});
```

### 4.2 Integration Testing

#### 4.2.1 Form Integration Tests

```typescript
// components/forms/UserForm/UserForm.test.tsx
import { render, screen, waitFor } from '@/test/utils';
import userEvent from '@testing-library/user-event';
import { UserForm } from './UserForm';

describe('UserForm Integration', () => {
  it('submits form with valid data', async () => {
    const user = userEvent.setup();
    const mockSubmit = jest.fn();
    
    render(<UserForm onSubmit={mockSubmit} />);
    
    await user.type(screen.getByLabelText(/name/i), 'John Doe');
    await user.type(screen.getByLabelText(/email/i), 'john@example.com');
    await user.click(screen.getByRole('button', { name: /submit/i }));
    
    await waitFor(() => {
      expect(mockSubmit).toHaveBeenCalledWith({
        name: 'John Doe',
        email: 'john@example.com',
      });
    });
  });

  it('shows validation errors for invalid data', async () => {
    const user = userEvent.setup();
    
    render(<UserForm />);
    
    await user.type(screen.getByLabelText(/email/i), 'invalid-email');
    await user.click(screen.getByRole('button', { name: /submit/i }));
    
    expect(screen.getByText(/please enter a valid email/i)).toBeInTheDocument();
  });
});
```

### 4.3 Accessibility Testing

#### 4.3.1 Automated Accessibility Tests

```typescript
// src/test/accessibility.test.tsx
import { render } from '@/test/utils';
import { axe, toHaveNoViolations } from 'jest-axe';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { FormField } from '@/components/forms/FormField';

expect.extend(toHaveNoViolations);

describe('Accessibility Tests', () => {
  it('Button has no accessibility violations', async () => {
    const { container } = render(<Button>Click me</Button>);
    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });

  it('Input with label has no accessibility violations', async () => {
    const { container } = render(
      <FormField name="email" label="Email Address">
        <Input type="email" />
      </FormField>
    );
    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });
});
```

## 5. Performance Optimization

### 5.1 Bundle Optimization

#### 5.1.1 Tree Shaking

```typescript
// components/ui/index.ts - Proper barrel exports
export { Button } from './Button';
export type { ButtonProps } from './Button';
export { Input } from './Input';
export type { InputProps } from './Input';
export { Card } from './Card';
export type { CardProps } from './Card';

// Usage - Import only what you need
import { Button, Input } from '@/components/ui';

// Instead of importing everything
import * as UI from '@/components/ui';
```

#### 5.1.2 Code Splitting

```typescript
// Lazy load heavy components
const LazyChart = lazy(() => import('@/components/data-display/Chart'));
const LazyTable = lazy(() => import('@/components/data-display/Table'));

// Use with Suspense
const Dashboard = () => {
  return (
    <div>
      <Suspense fallback={<ChartSkeleton />}>
        <LazyChart data={chartData} />
      </Suspense>
      
      <Suspense fallback={<TableSkeleton />}>
        <LazyTable data={tableData} />
      </Suspense>
    </div>
  );
};
```

### 5.2 Runtime Performance

#### 5.2.1 Memoization

```typescript
// Memoize expensive components
const ExpensiveComponent = React.memo(({ data, onAction }) => {
  const processedData = useMemo(() => {
    return data.map(item => ({
      ...item,
      processed: true,
    }));
  }, [data]);

  const handleAction = useCallback((id: string) => {
    onAction(id);
  }, [onAction]);

  return (
    <div>
      {processedData.map(item => (
        <Item key={item.id} {...item} onAction={handleAction} />
      ))}
    </div>
  );
});
```

#### 5.2.2 Virtual Scrolling

```typescript
// components/data-display/VirtualList/VirtualList.tsx
import { FixedSizeList as List } from 'react-window';

interface VirtualListProps<T> {
  items: T[];
  itemHeight: number;
  height: number;
  renderItem: (item: T, index: number) => React.ReactNode;
}

export const VirtualList = <T,>({
  items,
  itemHeight,
  height,
  renderItem,
}: VirtualListProps<T>) => {
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

## 6. Debugging and Troubleshooting

### 6.1 Common Issues and Solutions

#### 6.1.1 TypeScript Errors

**Error: Property 'xxx' does not exist on type 'ButtonProps'**
```typescript
// Problem: Missing prop in interface
interface ButtonProps {
  variant?: 'primary' | 'secondary';
  // Missing 'size' prop
}

// Solution: Add missing prop
interface ButtonProps {
  variant?: 'primary' | 'secondary';
  size?: 'sm' | 'md' | 'lg';
}
```

**Error: Type 'string' is not assignable to type 'never'**
```typescript
// Problem: Union type not properly defined
const variants = ['primary', 'secondary'] as const;
type Variant = typeof variants[number]; // 'primary' | 'secondary'

// Solution: Use proper union type
type Variant = 'primary' | 'secondary';
```

#### 6.1.2 Styling Issues

**Tailwind classes not applying**
```typescript
// Problem: Dynamic classes not recognized
const buttonClass = `bg-${color}-500`; // Won't work

// Solution: Use complete class names
const buttonClass = color === 'primary' ? 'bg-primary-500' : 'bg-secondary-500';

// Or use safelist in tailwind.config.js
module.exports = {
  content: ['./src/**/*.{js,ts,jsx,tsx}'],
  safelist: [
    'bg-primary-500',
    'bg-secondary-500',
    'bg-success-500',
    'bg-error-500',
  ],
};
```

**CSS specificity issues**
```typescript
// Problem: Styles not overriding
<Button className="bg-red-500">Custom</Button> // Might not work

// Solution: Use !important or adjust specificity
<Button className="!bg-red-500">Custom</Button>

// Or use cn utility properly
<Button className={cn('bg-red-500', someCondition && 'bg-blue-500')}>
  Custom
</Button>
```

### 6.2 Debugging Tools

#### 6.2.1 React Developer Tools

```typescript
// Add displayName for better debugging
const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ variant, size, ...props }, ref) => {
    // Component implementation
  }
);

Button.displayName = 'Button';
```

#### 6.2.2 Custom Debug Utilities

```typescript
// utils/debug.ts
export const debugRender = (componentName: string, props: any) => {
  if (process.env.NODE_ENV === 'development') {
    console.log(`[${componentName}] Rendering with props:`, props);
  }
};

// Usage in component
const Button = ({ variant, size, ...props }: ButtonProps) => {
  debugRender('Button', { variant, size });
  
  return (
    <button {...props} />
  );
};
```

### 6.3 Performance Debugging

#### 6.3.1 React Profiler

```typescript
// Wrap components with Profiler in development
const ProfiledButton = ({ children, ...props }: ButtonProps) => {
  const onRenderCallback = (id: string, phase: string, actualDuration: number) => {
    if (process.env.NODE_ENV === 'development') {
      console.log(`[Profiler] ${id} ${phase}: ${actualDuration}ms`);
    }
  };

  return (
    <Profiler id="Button" onRender={onRenderCallback}>
      <Button {...props}>{children}</Button>
    </Profiler>
  );
};
```

#### 6.3.2 Bundle Analysis

```bash
# Add to package.json scripts
"analyze": "npx vite-bundle-analyzer"

# Run bundle analysis
npm run analyze
```

## 7. Best Practices Summary

### 7.1 Component Development

#### 7.1.1 Do's
- Use TypeScript for type safety
- Follow accessibility guidelines (WCAG 2.1 AA)
- Write comprehensive tests
- Use semantic HTML elements
- Implement proper error handling
- Follow the single responsibility principle
- Use design tokens consistently
- Document components with Storybook

#### 7.1.2 Don'ts
- Don't hardcode values (use design tokens)
- Don't skip accessibility testing
- Don't create overly complex components
- Don't ignore responsive design
- Don't use any types in TypeScript
- Don't skip error boundaries
- Don't forget to handle loading states
- Don't ignore performance implications

### 7.2 Code Quality

#### 7.2.1 Naming Conventions
- Components: PascalCase (`Button`, `UserProfile`)
- Props: camelCase (`variant`, `isDisabled`)
- Files: PascalCase for components, camelCase for utilities
- CSS classes: kebab-case (`btn-primary`, `form-field`)

#### 7.2.2 File Organization
```
components/
├── ui/
│   ├── Button/
│   │   ├── Button.tsx
│   │   ├── Button.types.ts
│   │   ├── Button.variants.ts
│   │   ├── Button.stories.tsx
│   │   ├── Button.test.tsx
│   │   └── index.ts
│   └── index.ts
├── forms/
├── navigation/
└── layout/
```

### 7.3 Performance Guidelines

#### 7.3.1 Optimization Strategies
- Use React.memo for expensive components
- Implement proper memoization with useMemo and useCallback
- Use virtual scrolling for large lists
- Implement code splitting for large components
- Optimize images and assets
- Use proper error boundaries
- Implement loading states and skeleton screens

#### 7.3.2 Monitoring
- Set up performance monitoring
- Track bundle sizes
- Monitor Core Web Vitals
- Use React DevTools Profiler
- Implement error tracking

## 8. Deployment and Maintenance

### 8.1 Build Process

#### 8.1.1 Production Build

```bash
# Build for production
npm run build

# Preview production build
npm run preview

# Test production build
npm run test:production
```

#### 8.1.2 Build Optimization

```typescript
// vite.config.ts
export default defineConfig({
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['react', 'react-dom'],
          ui: ['./src/components/ui/index.ts'],
          forms: ['./src/components/forms/index.ts'],
        },
      },
    },
  },
});
```

### 8.2 Maintenance Guidelines

#### 8.2.1 Regular Updates
- Keep dependencies updated
- Monitor security vulnerabilities
- Update design tokens as needed
- Review and update documentation
- Refactor components based on usage patterns

#### 8.2.2 Version Management
```json
{
  "version": "1.0.0",
  "changelog": {
    "1.0.0": "Initial release with core components",
    "1.1.0": "Added form components and validation",
    "1.2.0": "Performance improvements and bug fixes"
  }
}
```

## 9. Support and Resources

### 9.1 Documentation Links

- [React Documentation](https://react.dev/)
- [TypeScript Handbook](https://www.typescriptlang.org/docs/)
- [Tailwind CSS Documentation](https://tailwindcss.com/docs)
- [Storybook Documentation](https://storybook.js.org/docs)
- [Testing Library Documentation](https://testing-library.com/docs/)
- [Accessibility Guidelines](https://www.w3.org/WAI/WCAG21/quickref/)

### 9.2 Community Resources

- [React TypeScript Cheatsheet](https://react-typescript-cheatsheet.netlify.app/)
- [Tailwind UI Components](https://tailwindui.com/components)
- [Headless UI](https://headlessui.com/)
- [Radix UI](https://www.radix-ui.com/)

### 9.3 Getting Help

#### 9.3.1 Internal Support
- Design System Team: design-system@itdo.co.jp
- Frontend Team: frontend@itdo.co.jp
- Documentation: Internal Wiki

#### 9.3.2 Issue Reporting
```markdown
## Bug Report Template

**Component**: [Component Name]
**Version**: [Version Number]
**Environment**: [Development/Production]

**Description**: Brief description of the issue

**Steps to Reproduce**:
1. Step 1
2. Step 2
3. Step 3

**Expected Behavior**: What should happen

**Actual Behavior**: What actually happens

**Screenshots**: If applicable

**Additional Context**: Any other relevant information
```

---

**Document Status**: ✅ Complete and Ready for Use  
**Last Updated**: 2025-07-16  
**Next Review**: 2025-08-16  

---

*This implementation support documentation provides comprehensive guidance for developers working with the ITDO ERP2 design system. It should be regularly updated as the system evolves and new patterns emerge.*