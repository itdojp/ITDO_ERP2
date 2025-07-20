import Textarea from './Textarea'

interface Meta {
  title: string
  component: typeof Textarea
  parameters?: Record<string, unknown>
  tags?: string[]
  argTypes?: Record<string, unknown>
}

interface StoryObj {
  args?: Record<string, unknown>
  parameters?: Record<string, unknown>
}

const meta: Meta = {
  title: 'UI/Textarea',
  component: Textarea,
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
  argTypes: {
    variant: {
      control: { type: 'select' },
      options: ['default', 'filled', 'outline'],
      description: 'Visual style variant'
    },
    size: {
      control: { type: 'select' },
      options: ['sm', 'md', 'lg'],
      description: 'Size of the textarea'
    },
    resize: {
      control: { type: 'select' },
      options: ['none', 'vertical', 'horizontal', 'both'],
      description: 'Resize behavior'
    },
    rows: {
      control: { type: 'number' },
      description: 'Number of visible rows'
    },
    label: {
      control: { type: 'text' },
      description: 'Textarea label'
    },
    placeholder: {
      control: { type: 'text' },
      description: 'Placeholder text'
    },
    helperText: {
      control: { type: 'text' },
      description: 'Helper text below textarea'
    },
    error: {
      control: { type: 'boolean' },
      description: 'Error state'
    },
    errorMessage: {
      control: { type: 'text' },
      description: 'Error message text'
    },
    disabled: {
      control: { type: 'boolean' },
      description: 'Disabled state'
    },
    loading: {
      control: { type: 'boolean' },
      description: 'Loading state'
    }
  },
}

export default meta
type Story = StoryObj

export const Default: Story = {
  args: {
    placeholder: 'Enter description...',
  },
}

export const WithLabel: Story = {
  args: {
    label: 'Description',
    placeholder: 'Enter a detailed description',
  },
}

export const WithHelperText: Story = {
  args: {
    label: 'Comments',
    placeholder: 'Add your comments...',
    helperText: 'Please provide detailed feedback (minimum 10 characters)',
  },
}

export const Error: Story = {
  args: {
    label: 'Description',
    placeholder: 'Enter description',
    error: true,
    errorMessage: 'Description is required and must be at least 10 characters',
  },
}

export const Loading: Story = {
  args: {
    label: 'Processing',
    placeholder: 'Please wait...',
    loading: true,
  },
}

export const Disabled: Story = {
  args: {
    label: 'Disabled Field',
    placeholder: 'This field is disabled',
    disabled: true,
  },
}

export const FilledVariant: Story = {
  args: {
    variant: 'filled',
    label: 'Filled Textarea',
    placeholder: 'Filled variant',
  },
}

export const OutlineVariant: Story = {
  args: {
    variant: 'outline',
    label: 'Outline Textarea',
    placeholder: 'Outline variant',
  },
}

export const SmallSize: Story = {
  args: {
    size: 'sm',
    label: 'Small Textarea',
    placeholder: 'Small size',
    rows: 2,
  },
}

export const LargeSize: Story = {
  args: {
    size: 'lg',
    label: 'Large Textarea',
    placeholder: 'Large size',
    rows: 4,
  },
}

export const NoResize: Story = {
  args: {
    label: 'Fixed Size',
    placeholder: 'Cannot be resized',
    resize: 'none',
  },
}

export const HorizontalResize: Story = {
  args: {
    label: 'Horizontal Resize',
    placeholder: 'Can be resized horizontally',
    resize: 'horizontal',
  },
}

export const BothResize: Story = {
  args: {
    label: 'Both Resize',
    placeholder: 'Can be resized in both directions',
    resize: 'both',
  },
}

export const ManyRows: Story = {
  args: {
    label: 'Large Text Area',
    placeholder: 'Enter a long description...',
    rows: 8,
  },
}

export const FilledError: Story = {
  args: {
    variant: 'filled',
    label: 'Comments',
    placeholder: 'Enter comments',
    error: true,
    errorMessage: 'Comments are required',
  },
}