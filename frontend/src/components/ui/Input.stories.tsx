import { Search as SearchIcon, User, Mail } from 'lucide-react'
import Input from './Input'

interface Meta {
  title: string
  component: typeof Input
  parameters?: Record<string, unknown>
  tags?: string[]
  argTypes?: Record<string, unknown>
}

interface StoryObj {
  args?: Record<string, unknown>
  parameters?: Record<string, unknown>
}

const meta: Meta = {
  title: 'UI/Input',
  component: Input,
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
      description: 'Size of the input'
    },
    type: {
      control: { type: 'select' },
      options: ['text', 'email', 'password', 'search', 'number', 'tel', 'url'],
      description: 'Input type'
    },
    label: {
      control: { type: 'text' },
      description: 'Input label'
    },
    placeholder: {
      control: { type: 'text' },
      description: 'Placeholder text'
    },
    helperText: {
      control: { type: 'text' },
      description: 'Helper text below input'
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
    placeholder: 'Enter text...',
  },
}

export const WithLabel: Story = {
  args: {
    label: 'Full Name',
    placeholder: 'Enter your full name',
  },
}

export const Email: Story = {
  args: {
    label: 'Email Address',
    type: 'email',
    placeholder: 'Enter your email',
    leftIcon: <Mail />,
  },
}

export const Password: Story = {
  args: {
    label: 'Password',
    type: 'password',
    placeholder: 'Enter your password',
  },
}

export const SearchInput: Story = {
  args: {
    type: 'search',
    placeholder: 'Search users...',
  },
}

export const WithHelperText: Story = {
  args: {
    label: 'Username',
    placeholder: 'Enter username',
    helperText: 'Username must be unique and contain only letters and numbers',
  },
}

export const Error: Story = {
  args: {
    label: 'Email',
    placeholder: 'Enter your email',
    error: true,
    errorMessage: 'Please enter a valid email address',
  },
}

export const WithLeftIcon: Story = {
  args: {
    label: 'Username',
    placeholder: 'Enter username',
    leftIcon: <User />,
  },
}

export const WithRightIcon: Story = {
  args: {
    label: 'Search',
    placeholder: 'Type to search...',
    rightIcon: <SearchIcon />,
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
    label: 'Filled Input',
    placeholder: 'Filled variant',
  },
}

export const OutlineVariant: Story = {
  args: {
    variant: 'outline',
    label: 'Outline Input',
    placeholder: 'Outline variant',
  },
}

export const SmallSize: Story = {
  args: {
    size: 'sm',
    label: 'Small Input',
    placeholder: 'Small size',
  },
}

export const LargeSize: Story = {
  args: {
    size: 'lg',
    label: 'Large Input',
    placeholder: 'Large size',
  },
}

export const FilledError: Story = {
  args: {
    variant: 'filled',
    label: 'Email',
    placeholder: 'Enter email',
    error: true,
    errorMessage: 'Email is required',
  },
}