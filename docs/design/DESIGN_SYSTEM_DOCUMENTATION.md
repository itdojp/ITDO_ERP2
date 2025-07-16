# Design System Documentation

**Document ID**: ITDO-ERP-DD-DSD-001  
**Version**: 1.0  
**Date**: 2025-07-16  
**Author**: Claude Code AI  
**Issue**: #160  

---

## 1. Overview

The ITDO ERP2 Design System is a comprehensive collection of reusable components, design tokens, and guidelines that ensure consistency, accessibility, and efficiency across the entire application. This documentation serves as the single source of truth for designers and developers working on the ITDO ERP2 project.

## 2. Design Principles

### 2.1 Core Principles

#### 2.1.1 Consistency
- **Visual Consistency**: All components follow the same design language
- **Behavioral Consistency**: Similar interactions behave the same way
- **Code Consistency**: Standardized implementation patterns
- **Documentation Consistency**: Uniform documentation structure

#### 2.1.2 Accessibility
- **WCAG 2.1 AA Compliance**: All components meet accessibility standards
- **Keyboard Navigation**: Full keyboard support for all interactions
- **Screen Reader Support**: Proper ARIA labels and semantic HTML
- **Color Contrast**: Minimum 4.5:1 contrast ratio for text

#### 2.1.3 Scalability
- **Component Composition**: Build complex UIs from simple components
- **Extensibility**: Easy to extend and customize components
- **Performance**: Optimized for bundle size and runtime performance
- **Maintainability**: Clear structure and documentation

#### 2.1.4 User Experience
- **Intuitive**: Components behave as users expect
- **Responsive**: Works across all device sizes
- **Fast**: Optimized for performance
- **Inclusive**: Accessible to users with disabilities

### 2.2 Design Philosophy

#### 2.2.1 Progressive Enhancement
- Start with basic HTML functionality
- Enhance with CSS for visual design
- Add JavaScript for interactivity
- Ensure fallbacks for all features

#### 2.2.2 Mobile-First Design
- Design for mobile devices first
- Progressively enhance for larger screens
- Touch-friendly interactions
- Responsive typography and spacing

#### 2.2.3 Content-First Approach
- Content determines design decisions
- Flexible layouts that adapt to content
- Clear information hierarchy
- Readable typography

## 3. Design Tokens

### 3.1 Token Categories

#### 3.1.1 Color System

**Primary Colors**
- Used for primary actions, links, and brand elements
- Base color: `#3b82f6` (blue-500)
- Range: 50-900 scale for various use cases

**Secondary Colors**
- Used for secondary actions and neutral elements
- Base color: `#64748b` (slate-500)
- Range: 50-900 scale for various use cases

**Semantic Colors**
- **Success**: `#22c55e` (green-500) - Success messages, confirmations
- **Warning**: `#f59e0b` (amber-500) - Warnings, cautionary messages
- **Error**: `#ef4444` (red-500) - Error messages, destructive actions
- **Info**: `#3b82f6` (blue-500) - Informational messages

**Usage Guidelines**
```css
/* Primary actions */
.btn-primary { background-color: var(--color-primary-500); }

/* Secondary actions */
.btn-secondary { background-color: var(--color-secondary-500); }

/* Text colors */
.text-primary { color: var(--color-neutral-900); }
.text-secondary { color: var(--color-neutral-700); }
.text-muted { color: var(--color-neutral-500); }

/* Semantic colors */
.alert-success { background-color: var(--color-success-50); }
.alert-error { background-color: var(--color-error-50); }
```

#### 3.1.2 Typography System

**Font Families**
- **Sans-serif**: Inter (primary), System UI (fallback)
- **Monospace**: JetBrains Mono (code), SF Mono (fallback)

**Font Sizes**
- **xs**: 12px - Small labels, captions
- **sm**: 14px - Secondary text, form labels
- **base**: 16px - Body text, default size
- **lg**: 18px - Subheadings, emphasized text
- **xl**: 20px - Card titles, section headers
- **2xl**: 24px - Page titles, major headings
- **3xl**: 30px - Hero titles, landing pages
- **4xl**: 36px - Display headings

**Font Weights**
- **light**: 300 - Decorative text
- **normal**: 400 - Body text
- **medium**: 500 - Emphasized text
- **semibold**: 600 - Subheadings
- **bold**: 700 - Headings

**Line Heights**
- **tight**: 1.25 - Headings, compact text
- **normal**: 1.5 - Body text
- **relaxed**: 1.75 - Long-form content

**Usage Guidelines**
```css
/* Headings */
.heading-1 { font-size: var(--font-size-3xl); font-weight: var(--font-weight-bold); }
.heading-2 { font-size: var(--font-size-2xl); font-weight: var(--font-weight-semibold); }
.heading-3 { font-size: var(--font-size-xl); font-weight: var(--font-weight-medium); }

/* Body text */
.body-text { font-size: var(--font-size-base); line-height: var(--line-height-normal); }
.body-small { font-size: var(--font-size-sm); line-height: var(--line-height-normal); }

/* Code */
.code { font-family: var(--font-mono); font-size: var(--font-size-sm); }
```

#### 3.1.3 Spacing System

**8px Grid System**
- All spacing is based on 8px increments
- Consistent vertical rhythm
- Predictable layouts

**Spacing Scale**
- **0**: 0px - No spacing
- **1**: 4px - Minimal spacing
- **2**: 8px - Base unit
- **3**: 12px - Small spacing
- **4**: 16px - Medium spacing
- **6**: 24px - Large spacing
- **8**: 32px - Extra large spacing
- **12**: 48px - Section spacing
- **16**: 64px - Page spacing

**Usage Guidelines**
```css
/* Component spacing */
.btn { padding: var(--spacing-2) var(--spacing-4); }
.card { padding: var(--spacing-6); }
.form-field { margin-bottom: var(--spacing-4); }

/* Layout spacing */
.section { margin-bottom: var(--spacing-12); }
.page { padding: var(--spacing-8); }
```

#### 3.1.4 Shadow System

**Elevation Levels**
- **sm**: Subtle elevation for cards
- **md**: Standard elevation for dropdowns
- **lg**: High elevation for modals
- **xl**: Maximum elevation for overlays

**Usage Guidelines**
```css
/* Component shadows */
.card { box-shadow: var(--shadow-sm); }
.dropdown { box-shadow: var(--shadow-md); }
.modal { box-shadow: var(--shadow-lg); }
.tooltip { box-shadow: var(--shadow-xl); }
```

### 3.2 Token Usage

#### 3.2.1 Implementation in CSS

```css
:root {
  /* Colors */
  --color-primary-500: #3b82f6;
  --color-primary-600: #2563eb;
  --color-secondary-500: #64748b;
  --color-success-500: #22c55e;
  --color-error-500: #ef4444;
  
  /* Typography */
  --font-sans: 'Inter', system-ui, sans-serif;
  --font-mono: 'JetBrains Mono', monospace;
  --font-size-base: 1rem;
  --font-weight-normal: 400;
  --line-height-normal: 1.5;
  
  /* Spacing */
  --spacing-2: 0.5rem;
  --spacing-4: 1rem;
  --spacing-6: 1.5rem;
  --spacing-8: 2rem;
  
  /* Shadows */
  --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
  --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
}
```

#### 3.2.2 Implementation in JavaScript

```typescript
// Design tokens as JavaScript object
export const designTokens = {
  colors: {
    primary: {
      500: '#3b82f6',
      600: '#2563eb',
    },
    secondary: {
      500: '#64748b',
    },
    success: {
      500: '#22c55e',
    },
    error: {
      500: '#ef4444',
    },
  },
  typography: {
    fontFamily: {
      sans: ['Inter', 'system-ui', 'sans-serif'],
      mono: ['JetBrains Mono', 'monospace'],
    },
    fontSize: {
      base: '1rem',
      lg: '1.125rem',
    },
  },
  spacing: {
    2: '0.5rem',
    4: '1rem',
    6: '1.5rem',
    8: '2rem',
  },
};

// Usage in components
const Button = styled.button`
  background-color: ${props => 
    props.variant === 'primary' 
      ? designTokens.colors.primary[500] 
      : designTokens.colors.secondary[500]
  };
  padding: ${designTokens.spacing[2]} ${designTokens.spacing[4]};
  font-family: ${designTokens.typography.fontFamily.sans.join(', ')};
`;
```

## 4. Component Guidelines

### 4.1 Component Structure

#### 4.1.1 File Organization

```
Component/
├── Component.tsx          # Main component implementation
├── Component.types.ts     # TypeScript type definitions
├── Component.stories.tsx  # Storybook stories
├── Component.test.tsx     # Unit tests
├── Component.module.css   # Component styles (if needed)
└── index.ts              # Barrel export
```

#### 4.1.2 Component Template

```typescript
// Component.types.ts
export interface ComponentProps {
  variant?: 'primary' | 'secondary';
  size?: 'sm' | 'md' | 'lg';
  disabled?: boolean;
  children?: React.ReactNode;
  className?: string;
}

// Component.tsx
import { forwardRef } from 'react';
import { cn } from '../utils/cn';
import { componentVariants } from './Component.variants';
import type { ComponentProps } from './Component.types';

export const Component = forwardRef<HTMLButtonElement, ComponentProps>(
  ({ variant = 'primary', size = 'md', disabled = false, className, children, ...props }, ref) => {
    return (
      <button
        ref={ref}
        disabled={disabled}
        className={cn(componentVariants({ variant, size, disabled }), className)}
        {...props}
      >
        {children}
      </button>
    );
  }
);

Component.displayName = 'Component';

// Component.variants.ts
import { cva } from 'class-variance-authority';

export const componentVariants = cva(
  'base-styles',
  {
    variants: {
      variant: {
        primary: 'primary-styles',
        secondary: 'secondary-styles',
      },
      size: {
        sm: 'small-styles',
        md: 'medium-styles',
        lg: 'large-styles',
      },
    },
    defaultVariants: {
      variant: 'primary',
      size: 'md',
    },
  }
);
```

### 4.2 Naming Conventions

#### 4.2.1 Component Names
- **PascalCase**: `Button`, `InputField`, `DataTable`
- **Descriptive**: Names should clearly indicate purpose
- **Consistent**: Follow established patterns

#### 4.2.2 Props
- **camelCase**: `variant`, `isDisabled`, `onClick`
- **Boolean Props**: Prefix with `is`, `has`, `should` where appropriate
- **Event Handlers**: Prefix with `on` (e.g., `onClick`, `onSubmit`)

#### 4.2.3 CSS Classes
- **kebab-case**: `btn-primary`, `form-field`, `data-table`
- **BEM Methodology**: `component__element--modifier`
- **Utility Classes**: Follow Tailwind CSS conventions

### 4.3 State Management

#### 4.3.1 Component State
```typescript
// Simple state
const [isOpen, setIsOpen] = useState(false);

// Complex state with useReducer
const [state, dispatch] = useReducer(reducer, initialState);

// State with validation
const [value, setValue] = useState('');
const [error, setError] = useState<string | null>(null);

const handleChange = (newValue: string) => {
  setValue(newValue);
  validateValue(newValue);
};
```

#### 4.3.2 Form State
```typescript
// Using React Hook Form
const {
  register,
  handleSubmit,
  formState: { errors, isSubmitting },
} = useForm<FormData>();

// Custom form hook
const useFormField = (name: string, validation: ValidationRules) => {
  const [value, setValue] = useState('');
  const [error, setError] = useState<string | null>(null);
  
  const validate = (value: string) => {
    // Validation logic
  };
  
  return { value, setValue, error, validate };
};
```

### 4.4 Accessibility Implementation

#### 4.4.1 ARIA Attributes
```typescript
// Button with ARIA label
<button aria-label="Close dialog" onClick={onClose}>
  <X size={16} />
</button>

// Form field with ARIA descriptions
<input
  aria-labelledby="field-label"
  aria-describedby="field-help field-error"
  aria-invalid={!!error}
  aria-required={required}
/>

// Modal with ARIA dialog
<div
  role="dialog"
  aria-labelledby="modal-title"
  aria-describedby="modal-description"
  aria-modal="true"
>
  <h2 id="modal-title">Modal Title</h2>
  <p id="modal-description">Modal content</p>
</div>
```

#### 4.4.2 Keyboard Navigation
```typescript
// Keyboard event handler
const handleKeyDown = (event: KeyboardEvent) => {
  switch (event.key) {
    case 'Enter':
    case ' ':
      event.preventDefault();
      onClick();
      break;
    case 'Escape':
      event.preventDefault();
      onClose();
      break;
  }
};

// Focus management
const useFocusManagement = () => {
  const previousFocus = useRef<HTMLElement | null>(null);
  
  const trapFocus = (container: HTMLElement) => {
    previousFocus.current = document.activeElement as HTMLElement;
    // Focus trap logic
  };
  
  const restoreFocus = () => {
    if (previousFocus.current) {
      previousFocus.current.focus();
    }
  };
  
  return { trapFocus, restoreFocus };
};
```

## 5. Layout System

### 5.1 Grid System

#### 5.1.1 CSS Grid Layout
```css
/* 12-column grid */
.grid {
  display: grid;
  grid-template-columns: repeat(12, 1fr);
  gap: var(--spacing-4);
}

.grid-col-1 { grid-column: span 1; }
.grid-col-2 { grid-column: span 2; }
.grid-col-3 { grid-column: span 3; }
.grid-col-4 { grid-column: span 4; }
.grid-col-6 { grid-column: span 6; }
.grid-col-12 { grid-column: span 12; }

/* Responsive grid */
@media (max-width: 768px) {
  .grid { grid-template-columns: 1fr; }
  .grid-col-1,
  .grid-col-2,
  .grid-col-3,
  .grid-col-4,
  .grid-col-6 { grid-column: span 1; }
}
```

#### 5.1.2 Flexbox Layout
```css
/* Flex utilities */
.flex { display: flex; }
.flex-col { flex-direction: column; }
.flex-wrap { flex-wrap: wrap; }

.items-center { align-items: center; }
.items-start { align-items: flex-start; }
.items-end { align-items: flex-end; }

.justify-center { justify-content: center; }
.justify-between { justify-content: space-between; }
.justify-end { justify-content: flex-end; }

.flex-1 { flex: 1; }
.flex-auto { flex: auto; }
.flex-none { flex: none; }
```

### 5.2 Container System

#### 5.2.1 Page Container
```css
.container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 var(--spacing-4);
}

@media (min-width: 640px) {
  .container { padding: 0 var(--spacing-6); }
}

@media (min-width: 1024px) {
  .container { padding: 0 var(--spacing-8); }
}
```

#### 5.2.2 Section Container
```css
.section {
  margin-bottom: var(--spacing-12);
}

.section-header {
  margin-bottom: var(--spacing-6);
}

.section-content {
  margin-bottom: var(--spacing-8);
}
```

### 5.3 Responsive Design

#### 5.3.1 Breakpoints
```css
/* Mobile first approach */
@media (min-width: 640px) { /* sm */ }
@media (min-width: 768px) { /* md */ }
@media (min-width: 1024px) { /* lg */ }
@media (min-width: 1280px) { /* xl */ }
@media (min-width: 1536px) { /* 2xl */ }
```

#### 5.3.2 Responsive Components
```typescript
// Responsive hook
const useResponsive = () => {
  const [isMobile, setIsMobile] = useState(false);
  const [isTablet, setIsTablet] = useState(false);
  
  useEffect(() => {
    const handleResize = () => {
      setIsMobile(window.innerWidth < 768);
      setIsTablet(window.innerWidth >= 768 && window.innerWidth < 1024);
    };
    
    handleResize();
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);
  
  return { isMobile, isTablet };
};

// Responsive component
const ResponsiveComponent = () => {
  const { isMobile, isTablet } = useResponsive();
  
  return (
    <div className={cn(
      'grid',
      isMobile && 'grid-cols-1',
      isTablet && 'grid-cols-2',
      !isMobile && !isTablet && 'grid-cols-3'
    )}>
      {/* Content */}
    </div>
  );
};
```

## 6. Animation and Transitions

### 6.1 Animation Principles

#### 6.1.1 Easing Functions
```css
/* Easing variables */
:root {
  --ease-in: cubic-bezier(0.4, 0, 1, 1);
  --ease-out: cubic-bezier(0, 0, 0.2, 1);
  --ease-in-out: cubic-bezier(0.4, 0, 0.2, 1);
}

/* Common transitions */
.transition-fast { transition: all 150ms var(--ease-out); }
.transition-normal { transition: all 300ms var(--ease-in-out); }
.transition-slow { transition: all 500ms var(--ease-in-out); }
```

#### 6.1.2 Micro-animations
```css
/* Hover effects */
.btn:hover {
  transform: translateY(-1px);
  box-shadow: var(--shadow-md);
}

/* Focus effects */
.input:focus {
  outline: 2px solid var(--color-primary-500);
  outline-offset: 2px;
}

/* Loading animations */
@keyframes spin {
  to { transform: rotate(360deg); }
}

.spinner {
  animation: spin 1s linear infinite;
}
```

### 6.2 Page Transitions

#### 6.2.1 Route Transitions
```typescript
// Page transition component
const PageTransition = ({ children }: { children: React.ReactNode }) => {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
      transition={{ duration: 0.3 }}
    >
      {children}
    </motion.div>
  );
};
```

#### 6.2.2 Modal Transitions
```typescript
// Modal with animation
const AnimatedModal = ({ isOpen, onClose, children }: ModalProps) => {
  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="modal-backdrop"
        >
          <motion.div
            initial={{ scale: 0.9, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0.9, opacity: 0 }}
            transition={{ type: 'spring', stiffness: 300, damping: 30 }}
            className="modal-content"
          >
            {children}
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
};
```

## 7. Testing Guidelines

### 7.1 Component Testing

#### 7.1.1 Unit Tests
```typescript
// Basic component test
describe('Button', () => {
  it('renders correctly', () => {
    render(<Button>Click me</Button>);
    expect(screen.getByRole('button')).toBeInTheDocument();
  });
  
  it('applies correct variant styles', () => {
    render(<Button variant="primary">Primary</Button>);
    expect(screen.getByRole('button')).toHaveClass('btn-primary');
  });
  
  it('handles click events', async () => {
    const handleClick = jest.fn();
    const user = userEvent.setup();
    
    render(<Button onClick={handleClick}>Click me</Button>);
    await user.click(screen.getByRole('button'));
    
    expect(handleClick).toHaveBeenCalledTimes(1);
  });
});
```

#### 7.1.2 Accessibility Tests
```typescript
// Accessibility testing
describe('Button accessibility', () => {
  it('has proper ARIA attributes', () => {
    render(<Button aria-label="Close dialog">×</Button>);
    expect(screen.getByRole('button')).toHaveAccessibleName('Close dialog');
  });
  
  it('supports keyboard navigation', async () => {
    const handleClick = jest.fn();
    const user = userEvent.setup();
    
    render(<Button onClick={handleClick}>Click me</Button>);
    
    const button = screen.getByRole('button');
    button.focus();
    await user.keyboard('{Enter}');
    
    expect(handleClick).toHaveBeenCalled();
  });
});
```

### 7.2 Integration Testing

#### 7.2.1 Form Testing
```typescript
// Form integration test
describe('User form', () => {
  it('submits form with valid data', async () => {
    const mockSubmit = jest.fn();
    const user = userEvent.setup();
    
    render(<UserForm onSubmit={mockSubmit} />);
    
    await user.type(screen.getByLabelText(/name/i), 'John Doe');
    await user.type(screen.getByLabelText(/email/i), 'john@example.com');
    await user.click(screen.getByRole('button', { name: /submit/i }));
    
    expect(mockSubmit).toHaveBeenCalledWith({
      name: 'John Doe',
      email: 'john@example.com'
    });
  });
});
```

### 7.3 Visual Testing

#### 7.3.1 Storybook Testing
```typescript
// Visual regression testing with Storybook
export default {
  title: 'Components/Button',
  component: Button,
  parameters: {
    chromatic: { disableSnapshot: false },
  },
} as Meta;

export const AllVariants: Story = () => (
  <div className="space-y-4">
    <Button variant="primary">Primary</Button>
    <Button variant="secondary">Secondary</Button>
    <Button variant="outline">Outline</Button>
  </div>
);

export const AllStates: Story = () => (
  <div className="space-y-4">
    <Button>Default</Button>
    <Button disabled>Disabled</Button>
    <Button loading>Loading</Button>
  </div>
);
```

## 8. Performance Guidelines

### 8.1 Component Optimization

#### 8.1.1 Memoization
```typescript
// Memoized component
const ExpensiveComponent = React.memo(({ data, onAction }: Props) => {
  const processedData = useMemo(() => {
    return data.map(item => ({ ...item, processed: true }));
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

#### 8.1.2 Lazy Loading
```typescript
// Lazy loaded components
const LazyChart = lazy(() => import('./Chart'));
const LazyTable = lazy(() => import('./Table'));

// Usage with Suspense
<Suspense fallback={<LoadingSpinner />}>
  <LazyChart data={chartData} />
</Suspense>
```

### 8.2 Bundle Optimization

#### 8.2.1 Tree Shaking
```typescript
// Optimized imports
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';

// Instead of
import * as UI from '@/components/ui';
```

#### 8.2.2 Code Splitting
```typescript
// Route-based code splitting
const Dashboard = lazy(() => import('./pages/Dashboard'));
const Users = lazy(() => import('./pages/Users'));
const Settings = lazy(() => import('./pages/Settings'));
```

## 9. Documentation Standards

### 9.1 Component Documentation

#### 9.1.1 Storybook Stories
```typescript
// Complete story documentation
export default {
  title: 'Components/Button',
  component: Button,
  parameters: {
    docs: {
      description: {
        component: 'The Button component is used to trigger actions.',
      },
    },
  },
  argTypes: {
    variant: {
      control: 'select',
      options: ['primary', 'secondary', 'outline'],
      description: 'The visual style of the button',
    },
  },
} as Meta;

export const Primary: Story = {
  args: {
    children: 'Button',
    variant: 'primary',
  },
};

export const WithIcon: Story = {
  args: {
    children: 'Add Item',
    icon: Plus,
    variant: 'primary',
  },
};
```

#### 9.1.2 API Documentation
```typescript
/**
 * Button component for triggering actions
 * 
 * @param variant - Visual style variant
 * @param size - Button size
 * @param disabled - Whether the button is disabled
 * @param loading - Whether the button is in loading state
 * @param icon - Icon to display
 * @param children - Button content
 * @param onClick - Click handler
 * 
 * @example
 * <Button variant="primary" onClick={handleClick}>
 *   Click me
 * </Button>
 */
export const Button = ({ variant, size, disabled, loading, icon, children, onClick }: ButtonProps) => {
  // Implementation
};
```

### 9.2 Usage Examples

#### 9.2.1 Basic Usage
```typescript
// Import the component
import { Button } from '@/components/ui/Button';

// Basic usage
<Button>Click me</Button>

// With props
<Button variant="primary" size="lg" onClick={handleClick}>
  Large Primary Button
</Button>
```

#### 9.2.2 Advanced Usage
```typescript
// Complex form example
const ContactForm = () => {
  const { register, handleSubmit, formState: { errors } } = useForm();
  
  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
      <FormField
        label="Name"
        error={errors.name?.message}
        required
      >
        <Input {...register('name', { required: 'Name is required' })} />
      </FormField>
      
      <FormField
        label="Email"
        error={errors.email?.message}
        required
      >
        <Input
          type="email"
          {...register('email', { required: 'Email is required' })}
        />
      </FormField>
      
      <div className="flex gap-2">
        <Button type="button" variant="outline" onClick={onCancel}>
          Cancel
        </Button>
        <Button type="submit" variant="primary">
          Submit
        </Button>
      </div>
    </form>
  );
};
```

## 10. Migration Guide

### 10.1 From Legacy Components

#### 10.1.1 Button Migration
```typescript
// Old button
<button className="btn btn-primary" onClick={handleClick}>
  Click me
</button>

// New button
<Button variant="primary" onClick={handleClick}>
  Click me
</Button>
```

#### 10.1.2 Form Migration
```typescript
// Old form structure
<div className="form-group">
  <label htmlFor="email">Email</label>
  <input id="email" type="email" className="form-control" />
  <div className="error-message">Error message</div>
</div>

// New form structure
<FormField
  label="Email"
  error="Error message"
  required
>
  <Input type="email" />
</FormField>
```

### 10.2 Breaking Changes

#### 10.2.1 Props Changes
```typescript
// Old props
<Button type="primary" large disabled>
  Click me
</Button>

// New props
<Button variant="primary" size="lg" disabled>
  Click me
</Button>
```

#### 10.2.2 CSS Changes
```css
/* Old classes */
.btn-primary { }
.btn-large { }

/* New classes */
.btn { }
.btn-primary { }
.btn-lg { }
```

## 11. Best Practices

### 11.1 Component Development

#### 11.1.1 Do's
- Use TypeScript for type safety
- Follow accessibility guidelines
- Write comprehensive tests
- Document components in Storybook
- Use design tokens consistently
- Implement proper error handling
- Follow naming conventions
- Use semantic HTML

#### 11.1.2 Don'ts
- Don't hardcode values
- Don't skip accessibility features
- Don't create overly complex components
- Don't ignore responsive design
- Don't skip testing
- Don't use inline styles
- Don't create components without documentation

### 11.2 Usage Guidelines

#### 11.2.1 When to Create New Components
- When you need to reuse UI patterns
- When existing components don't meet requirements
- When you need to enforce consistency
- When you want to abstract complexity

#### 11.2.2 When to Extend Existing Components
- When you need slight variations
- When you need additional functionality
- When you need to maintain consistency
- When you want to avoid code duplication

## 12. Future Enhancements

### 12.1 Planned Features

#### 12.1.1 Theme System
- Dark mode support
- High contrast mode
- Custom theme creation
- Theme switching

#### 12.1.2 Advanced Components
- Data visualization components
- Advanced form components
- Layout components
- Animation components

#### 12.1.3 Developer Tools
- Design token generator
- Component inspector
- Performance monitoring
- Accessibility checker

### 12.2 Roadmap

#### 12.2.1 Phase 1: Foundation (Completed)
- Design token system
- Core components
- Basic documentation
- Testing framework

#### 12.2.2 Phase 2: Enhancement (Current)
- Advanced components
- Theme system
- Performance optimization
- Accessibility improvements

#### 12.2.3 Phase 3: Expansion (Future)
- Advanced animations
- Complex layouts
- Data visualization
- Developer tools

---

**Document Status**: ✅ Complete and Ready for Use  
**Last Updated**: 2025-07-16  
**Next Review**: 2025-08-16  

---

*This design system documentation serves as the comprehensive guide for implementing consistent, accessible, and performant UI components in the ITDO ERP2 project. It should be regularly updated as the system evolves.*