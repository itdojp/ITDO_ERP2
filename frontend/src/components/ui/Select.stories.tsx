import Select, { SelectOption } from './Select'

interface Meta {
  title: string
  component: typeof Select
  parameters?: Record<string, unknown>
  tags?: string[]
  argTypes?: Record<string, unknown>
}

interface StoryObj {
  args?: Record<string, unknown>
  parameters?: Record<string, unknown>
}

const sampleOptions: SelectOption[] = [
  { value: 'admin', label: 'Administrator' },
  { value: 'user', label: 'User' },
  { value: 'moderator', label: 'Moderator' },
  { value: 'guest', label: 'Guest' },
  { value: 'disabled', label: 'Disabled Option', disabled: true },
]

const industryOptions: SelectOption[] = [
  { value: 'tech', label: 'Technology' },
  { value: 'finance', label: 'Finance' },
  { value: 'healthcare', label: 'Healthcare' },
  { value: 'education', label: 'Education' },
  { value: 'retail', label: 'Retail' },
  { value: 'manufacturing', label: 'Manufacturing' },
]

const priorityOptions: SelectOption[] = [
  { value: 'low', label: 'Low Priority' },
  { value: 'medium', label: 'Medium Priority' },
  { value: 'high', label: 'High Priority' },
  { value: 'urgent', label: 'Urgent' },
]

const meta: Meta = {
  title: 'UI/Select',
  component: Select,
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
      description: 'Size of the select'
    },
    label: {
      control: { type: 'text' },
      description: 'Select label'
    },
    placeholder: {
      control: { type: 'text' },
      description: 'Placeholder text'
    },
    helperText: {
      control: { type: 'text' },
      description: 'Helper text below select'
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
    },
    searchable: {
      control: { type: 'boolean' },
      description: 'Enable search functionality'
    },
    multiple: {
      control: { type: 'boolean' },
      description: 'Allow multiple selection'
    },
    clearable: {
      control: { type: 'boolean' },
      description: 'Show clear button'
    }
  },
}

export default meta
type Story = StoryObj

export const Default: Story = {
  args: {
    options: sampleOptions,
    placeholder: 'Select an option...',
  },
}

export const WithLabel: Story = {
  args: {
    options: sampleOptions,
    label: 'User Role',
    placeholder: 'Choose a role',
  },
}

export const WithValue: Story = {
  args: {
    options: sampleOptions,
    label: 'Selected Role',
    value: 'admin',
  },
}

export const WithHelperText: Story = {
  args: {
    options: sampleOptions,
    label: 'User Role',
    placeholder: 'Choose a role',
    helperText: 'Select the appropriate role for this user',
  },
}

export const Error: Story = {
  args: {
    options: sampleOptions,
    label: 'User Role',
    placeholder: 'Choose a role',
    error: true,
    errorMessage: 'Please select a role',
  },
}

export const Loading: Story = {
  args: {
    options: sampleOptions,
    label: 'Loading Options',
    loading: true,
  },
}

export const Disabled: Story = {
  args: {
    options: sampleOptions,
    label: 'Disabled Select',
    disabled: true,
    value: 'user',
  },
}

export const Searchable: Story = {
  args: {
    options: industryOptions,
    label: 'Industry',
    placeholder: 'Search and select industry...',
    searchable: true,
  },
}

export const Multiple: Story = {
  args: {
    options: sampleOptions,
    label: 'Multiple Roles',
    placeholder: 'Select multiple roles...',
    multiple: true,
  },
}

export const MultipleWithValues: Story = {
  args: {
    options: sampleOptions,
    label: 'Selected Roles',
    value: ['admin', 'moderator'],
    multiple: true,
  },
}

export const Clearable: Story = {
  args: {
    options: sampleOptions,
    label: 'Clearable Select',
    value: 'user',
    clearable: true,
  },
}

export const SearchableMultiple: Story = {
  args: {
    options: industryOptions,
    label: 'Industries',
    placeholder: 'Search and select industries...',
    searchable: true,
    multiple: true,
    clearable: true,
  },
}

export const Priority: Story = {
  args: {
    options: priorityOptions,
    label: 'Task Priority',
    placeholder: 'Select priority level...',
    name: 'priority',
  },
}

export const FilledVariant: Story = {
  args: {
    options: sampleOptions,
    variant: 'filled',
    label: 'Filled Select',
    placeholder: 'Choose option...',
  },
}

export const OutlineVariant: Story = {
  args: {
    options: sampleOptions,
    variant: 'outline',
    label: 'Outline Select',
    placeholder: 'Choose option...',
  },
}

export const SmallSize: Story = {
  args: {
    options: sampleOptions,
    size: 'sm',
    label: 'Small Select',
    placeholder: 'Small size...',
  },
}

export const LargeSize: Story = {
  args: {
    options: sampleOptions,
    size: 'lg',
    label: 'Large Select',
    placeholder: 'Large size...',
  },
}

export const WithDisabledOptions: Story = {
  args: {
    options: sampleOptions,
    label: 'Select with Disabled Options',
    placeholder: 'Some options are disabled...',
  },
}

export const EmptyOptions: Story = {
  args: {
    options: [],
    label: 'Empty Select',
    placeholder: 'No options available...',
  },
}