export interface ComponentDocumentation {
  name: string
  description: string
  category: 'Form' | 'Layout' | 'Navigation' | 'Feedback' | 'Data Display' | 'Overlay'
  props: ComponentProp[]
  examples: ComponentExample[]
  accessibility: AccessibilityNote[]
  dependencies?: string[]
  version: string
  status: 'stable' | 'beta' | 'deprecated'
}

export interface ComponentProp {
  name: string
  type: string
  required: boolean
  defaultValue?: string
  description: string
  options?: string[]
}

export interface ComponentExample {
  title: string
  description: string
  code: string
  preview?: boolean
}

export interface AccessibilityNote {
  type: 'keyboard' | 'screen-reader' | 'color-contrast' | 'focus-management'
  description: string
  implementation?: string
}

export const componentDocumentation: Record<string, ComponentDocumentation> = {
  Button: {
    name: 'Button',
    description: 'A versatile button component with multiple variants, sizes, and states. Optimized with React.memo for performance.',
    category: 'Form',
    version: '1.0.0',
    status: 'stable',
    props: [
      {
        name: 'variant',
        type: "'default' | 'primary' | 'secondary' | 'outline' | 'ghost' | 'destructive' | 'danger'",
        required: false,
        defaultValue: 'default',
        description: 'Visual style variant of the button',
        options: ['default', 'primary', 'secondary', 'outline', 'ghost', 'destructive', 'danger']
      },
      {
        name: 'size',
        type: "'xs' | 'sm' | 'md' | 'lg' | 'xl'",
        required: false,
        defaultValue: 'md',
        description: 'Size of the button',
        options: ['xs', 'sm', 'md', 'lg', 'xl']
      },
      {
        name: 'loading',
        type: 'boolean',
        required: false,
        defaultValue: 'false',
        description: 'Shows loading spinner and disables the button'
      },
      {
        name: 'disabled',
        type: 'boolean',
        required: false,
        defaultValue: 'false',
        description: 'Disables the button'
      },
      {
        name: 'rounded',
        type: 'boolean',
        required: false,
        defaultValue: 'false',
        description: 'Applies rounded styling'
      },
      {
        name: 'fullWidth',
        type: 'boolean',
        required: false,
        defaultValue: 'false',
        description: 'Makes button take full width of container'
      },
      {
        name: 'children',
        type: 'React.ReactNode',
        required: true,
        description: 'Button content'
      },
      {
        name: 'onClick',
        type: '(event: React.MouseEvent<HTMLButtonElement>) => void',
        required: false,
        description: 'Click event handler'
      }
    ],
    examples: [
      {
        title: 'Basic Usage',
        description: 'Simple button with different variants',
        code: `<Button variant="primary">Primary Button</Button>
<Button variant="secondary">Secondary Button</Button>
<Button variant="outline">Outline Button</Button>`
      },
      {
        title: 'Button Sizes',
        description: 'Buttons in different sizes',
        code: `<Button size="xs">Extra Small</Button>
<Button size="sm">Small</Button>
<Button size="md">Medium</Button>
<Button size="lg">Large</Button>
<Button size="xl">Extra Large</Button>`
      },
      {
        title: 'Button States',
        description: 'Loading and disabled states',
        code: `<Button loading>Loading...</Button>
<Button disabled>Disabled</Button>
<Button variant="destructive">Delete</Button>`
      }
    ],
    accessibility: [
      {
        type: 'keyboard',
        description: 'Buttons are focusable and activatable with Enter and Space keys',
        implementation: 'Uses native <button> element for automatic keyboard accessibility'
      },
      {
        type: 'screen-reader',
        description: 'Provides proper type attribute and aria-busy during loading',
        implementation: 'type="button" and conditional aria-busy="true" when loading'
      },
      {
        type: 'focus-management',
        description: 'Clear focus indication with outline and ring styles',
        implementation: 'focus:outline-none focus:ring-2 focus:ring-offset-2'
      }
    ]
  },

  TextInput: {
    name: 'TextInput',
    description: 'A comprehensive text input component with validation, help text, and multiple input types.',
    category: 'Form',
    version: '1.0.0',
    status: 'stable',
    props: [
      {
        name: 'label',
        type: 'string',
        required: false,
        description: 'Input label text'
      },
      {
        name: 'type',
        type: "'text' | 'email' | 'password' | 'number' | 'tel' | 'url'",
        required: false,
        defaultValue: 'text',
        description: 'HTML input type'
      },
      {
        name: 'placeholder',
        type: 'string',
        required: false,
        description: 'Placeholder text'
      },
      {
        name: 'helpText',
        type: 'string',
        required: false,
        description: 'Helper text shown below input'
      },
      {
        name: 'validation',
        type: '(value: string) => string | null',
        required: false,
        description: 'Validation function that returns error message or null'
      },
      {
        name: 'required',
        type: 'boolean',
        required: false,
        defaultValue: 'false',
        description: 'Marks field as required'
      },
      {
        name: 'disabled',
        type: 'boolean',
        required: false,
        defaultValue: 'false',
        description: 'Disables the input'
      },
      {
        name: 'showClearButton',
        type: 'boolean',
        required: false,
        defaultValue: 'true',
        description: 'Shows clear button when input has value'
      }
    ],
    examples: [
      {
        title: 'Basic Input',
        description: 'Simple text input with label and placeholder',
        code: `<TextInput 
  label="Full Name" 
  placeholder="Enter your full name" 
  helpText="First and last name"
/>`
      },
      {
        title: 'Password Input',
        description: 'Password input with toggle visibility',
        code: `<TextInput 
  type="password"
  label="Password" 
  placeholder="Enter password"
  required
/>`
      },
      {
        title: 'Input with Validation',
        description: 'Input with custom validation',
        code: `<TextInput 
  label="Email"
  type="email"
  validation={(value) => {
    if (!value.includes('@')) return 'Invalid email format'
    return null
  }}
  placeholder="your@email.com"
/>`
      }
    ],
    accessibility: [
      {
        type: 'screen-reader',
        description: 'Proper labeling with htmlFor relationship and aria-describedby for help text',
        implementation: 'label[htmlFor] -> input[id] and aria-describedby for help/error text'
      },
      {
        type: 'keyboard',
        description: 'Full keyboard navigation and password visibility toggle',
        implementation: 'Tab navigation, Enter for password toggle, Escape to clear'
      },
      {
        type: 'color-contrast',
        description: 'Error states meet WCAG contrast requirements',
        implementation: 'Red error text has 4.5:1 contrast ratio against white background'
      }
    ]
  },

  Modal: {
    name: 'Modal',
    description: 'A flexible modal component with focus management, animations, and accessibility features.',
    category: 'Overlay',
    version: '1.0.0',
    status: 'stable',
    props: [
      {
        name: 'isOpen',
        type: 'boolean',
        required: true,
        description: 'Controls modal visibility'
      },
      {
        name: 'onClose',
        type: '() => void',
        required: true,
        description: 'Called when modal should close'
      },
      {
        name: 'title',
        type: 'string',
        required: false,
        description: 'Modal title'
      },
      {
        name: 'description',
        type: 'string',
        required: false,
        description: 'Modal description'
      },
      {
        name: 'size',
        type: "'xs' | 'sm' | 'md' | 'lg' | 'xl' | 'full'",
        required: false,
        defaultValue: 'md',
        description: 'Modal size'
      },
      {
        name: 'closeOnOverlayClick',
        type: 'boolean',
        required: false,
        defaultValue: 'true',
        description: 'Whether clicking overlay closes modal'
      },
      {
        name: 'closeOnEscape',
        type: 'boolean',
        required: false,
        defaultValue: 'true',
        description: 'Whether Escape key closes modal'
      },
      {
        name: 'showCloseButton',
        type: 'boolean',
        required: false,
        defaultValue: 'true',
        description: 'Whether to show close button'
      },
      {
        name: 'animation',
        type: "'fade' | 'slide' | 'scale' | 'none'",
        required: false,
        defaultValue: 'fade',
        description: 'Animation type'
      }
    ],
    examples: [
      {
        title: 'Basic Modal',
        description: 'Simple modal with title and content',
        code: `<Modal 
  isOpen={isOpen}
  onClose={() => setIsOpen(false)}
  title="Confirm Action"
  description="Are you sure you want to continue?"
>
  <div className="space-y-4">
    <p>Modal content goes here...</p>
    <div className="flex justify-end gap-2">
      <Button variant="outline" onClick={() => setIsOpen(false)}>
        Cancel
      </Button>
      <Button variant="primary">Confirm</Button>
    </div>
  </div>
</Modal>`
      }
    ],
    accessibility: [
      {
        type: 'focus-management',
        description: 'Traps focus within modal and returns focus to trigger element',
        implementation: 'useEffect hooks manage focus on open/close with querySelector for focusable elements'
      },
      {
        type: 'keyboard',
        description: 'Escape key closes modal, Tab cycles through focusable elements',
        implementation: 'Keyboard event listeners for Escape and Tab key handling'
      },
      {
        type: 'screen-reader',
        description: 'Proper ARIA attributes and semantic structure',
        implementation: 'role="dialog" aria-modal="true" aria-labelledby aria-describedby'
      }
    ]
  },

  Card: {
    name: 'Card',
    description: 'A flexible card component with compound components for header, body, and footer sections.',
    category: 'Layout',
    version: '1.0.0',
    status: 'stable',
    props: [
      {
        name: 'variant',
        type: "'default' | 'elevated' | 'flat'",
        required: false,
        defaultValue: 'default',
        description: 'Visual style variant'
      },
      {
        name: 'className',
        type: 'string',
        required: false,
        description: 'Additional CSS classes'
      },
      {
        name: 'children',
        type: 'React.ReactNode',
        required: true,
        description: 'Card content'
      }
    ],
    examples: [
      {
        title: 'Basic Card',
        description: 'Card with header, body, and footer',
        code: `<Card>
  <Card.Header>
    <h3>Card Title</h3>
  </Card.Header>
  <Card.Body>
    <p>Card content goes here...</p>
  </Card.Body>
  <Card.Footer>
    <Button variant="primary">Action</Button>
  </Card.Footer>
</Card>`
      },
      {
        title: 'Card Variants',
        description: 'Different card styles',
        code: `<Card variant="elevated">
  <Card.Body>Elevated card with shadow</Card.Body>
</Card>

<Card variant="flat">
  <Card.Body>Flat card without shadow</Card.Body>
</Card>`
      }
    ],
    accessibility: [
      {
        type: 'screen-reader',
        description: 'Semantic structure with proper heading hierarchy',
        implementation: 'Use appropriate heading levels in Card.Header'
      }
    ]
  },

  Grid: {
    name: 'Grid',
    description: 'A responsive grid layout component with auto-fit capabilities and gap controls.',
    category: 'Layout',
    version: '1.0.0',
    status: 'stable',
    props: [
      {
        name: 'cols',
        type: 'number | { sm?: number; md?: number; lg?: number; xl?: number }',
        required: false,
        description: 'Number of columns or responsive breakpoint object'
      },
      {
        name: 'gap',
        type: 'number',
        required: false,
        defaultValue: '4',
        description: 'Gap between grid items (1-8)'
      },
      {
        name: 'autoFit',
        type: 'boolean',
        required: false,
        defaultValue: 'false',
        description: 'Enable auto-fit layout'
      },
      {
        name: 'minColWidth',
        type: 'string',
        required: false,
        defaultValue: '200px',
        description: 'Minimum column width for auto-fit'
      }
    ],
    examples: [
      {
        title: 'Basic Grid',
        description: 'Simple grid with fixed columns',
        code: `<Grid cols={3} gap={4}>
  <div>Item 1</div>
  <div>Item 2</div>
  <div>Item 3</div>
</Grid>`
      },
      {
        title: 'Responsive Grid',
        description: 'Grid with responsive breakpoints',
        code: `<Grid cols={{ sm: 1, md: 2, lg: 3, xl: 4 }} gap={6}>
  <div>Responsive Item 1</div>
  <div>Responsive Item 2</div>
  <div>Responsive Item 3</div>
  <div>Responsive Item 4</div>
</Grid>`
      },
      {
        title: 'Auto-Fit Grid',
        description: 'Grid that automatically fits items',
        code: `<Grid autoFit minColWidth="250px" gap={4}>
  <div>Auto-fit Item 1</div>
  <div>Auto-fit Item 2</div>
  <div>Auto-fit Item 3</div>
</Grid>`
      }
    ],
    accessibility: [
      {
        type: 'screen-reader',
        description: 'Grid layout is transparent to screen readers, content flows naturally',
        implementation: 'Uses CSS Grid which maintains document flow for assistive technologies'
      }
    ]
  },

  Stack: {
    name: 'Stack',
    description: 'A flexible layout component for arranging items in rows or columns with consistent spacing.',
    category: 'Layout',
    version: '1.0.0',
    status: 'stable',
    props: [
      {
        name: 'direction',
        type: "'row' | 'column' | 'row-reverse' | 'column-reverse'",
        required: false,
        defaultValue: 'column',
        description: 'Flex direction'
      },
      {
        name: 'align',
        type: "'start' | 'center' | 'end' | 'stretch' | 'baseline'",
        required: false,
        defaultValue: 'stretch',
        description: 'Cross-axis alignment'
      },
      {
        name: 'justify',
        type: "'start' | 'center' | 'end' | 'between' | 'around' | 'evenly'",
        required: false,
        defaultValue: 'start',
        description: 'Main-axis alignment'
      },
      {
        name: 'spacing',
        type: 'number',
        required: false,
        defaultValue: '4',
        description: 'Space between items (1-8)'
      },
      {
        name: 'wrap',
        type: 'boolean',
        required: false,
        defaultValue: 'false',
        description: 'Allow items to wrap'
      }
    ],
    examples: [
      {
        title: 'Vertical Stack',
        description: 'Stack items vertically',
        code: `<Stack direction="column" spacing={4}>
  <div>Item 1</div>
  <div>Item 2</div>
  <div>Item 3</div>
</Stack>`
      },
      {
        title: 'Horizontal Stack',
        description: 'Stack items horizontally with space between',
        code: `<Stack direction="row" justify="between" align="center">
  <div>Left Item</div>
  <div>Center Item</div>
  <div>Right Item</div>
</Stack>`
      }
    ],
    accessibility: [
      {
        type: 'screen-reader',
        description: 'Flexbox layout maintains logical content order',
        implementation: 'Uses CSS Flexbox which preserves semantic order for screen readers'
      }
    ]
  }
}

export const getComponentsByCategory = (category: ComponentDocumentation['category']) => {
  return Object.entries(componentDocumentation)
    .filter(([_, doc]) => doc.category === category)
    .map(([name, doc]) => ({ name, ...doc }))
}

export const getAllCategories = () => {
  const categories = new Set(Object.values(componentDocumentation).map(doc => doc.category))
  return Array.from(categories).sort()
}

export const searchComponents = (query: string) => {
  const lowercaseQuery = query.toLowerCase()
  return Object.entries(componentDocumentation)
    .filter(([name, doc]) => 
      name.toLowerCase().includes(lowercaseQuery) ||
      doc.description.toLowerCase().includes(lowercaseQuery) ||
      doc.props.some(prop => prop.name.toLowerCase().includes(lowercaseQuery))
    )
    .map(([name, doc]) => ({ name, ...doc }))
}