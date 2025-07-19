import Alert from './Alert'

interface Meta {
  title: string
  component: typeof Alert
  parameters?: Record<string, unknown>
  tags?: string[]
  argTypes?: Record<string, unknown>
}

interface StoryObj {
  args?: Record<string, unknown>
  parameters?: Record<string, unknown>
}

const meta: Meta = {
  title: 'UI/Alert',
  component: Alert,
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
  argTypes: {
    variant: {
      control: { type: 'select' },
      options: ['success', 'error', 'warning', 'info'],
      description: 'Visual style variant'
    },
    size: {
      control: { type: 'select' },
      options: ['sm', 'md', 'lg'],
      description: 'Size of the alert'
    },
    title: {
      control: { type: 'text' },
      description: 'Optional title for the alert'
    },
    message: {
      control: { type: 'text' },
      description: 'Alert message content'
    },
    closable: {
      control: { type: 'boolean' },
      description: 'Show close button'
    },
    showIcon: {
      control: { type: 'boolean' },
      description: 'Show variant icon'
    }
  },
}

export default meta
type Story = StoryObj

export const Default: Story = {
  args: {
    message: 'This is a default alert message.',
  },
}

export const Success: Story = {
  args: {
    variant: 'success',
    title: 'Success!',
    message: 'Your action was completed successfully.',
  },
}

export const Error: Story = {
  args: {
    variant: 'error',
    title: 'Error',
    message: 'Something went wrong. Please try again.',
  },
}

export const Warning: Story = {
  args: {
    variant: 'warning',
    title: 'Warning',
    message: 'Please review your input before proceeding.',
  },
}

export const Info: Story = {
  args: {
    variant: 'info',
    title: 'Information',
    message: 'Here is some important information for you.',
  },
}

export const WithoutIcon: Story = {
  args: {
    variant: 'success',
    title: 'No Icon',
    message: 'This alert does not display an icon.',
    showIcon: false,
  },
}

export const Closable: Story = {
  args: {
    variant: 'info',
    title: 'Dismissible Alert',
    message: 'You can close this alert by clicking the X button.',
    closable: true,
    onClose: () => alert('Alert closed!'),
  },
}

export const Small: Story = {
  args: {
    variant: 'warning',
    size: 'sm',
    title: 'Small Alert',
    message: 'This is a small-sized alert.',
  },
}

export const Large: Story = {
  args: {
    variant: 'error',
    size: 'lg',
    title: 'Large Alert',
    message: 'This is a large-sized alert with more prominent text.',
  },
}

export const MessageOnly: Story = {
  args: {
    variant: 'success',
    message: 'Alert with message only, no title.',
  },
}

export const LongMessage: Story = {
  args: {
    variant: 'info',
    title: 'Detailed Information',
    message: 'This is a longer alert message that demonstrates how the component handles more text content. It should wrap properly and maintain good readability across different screen sizes.',
  },
}