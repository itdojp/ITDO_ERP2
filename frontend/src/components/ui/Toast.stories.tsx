import Toast from './Toast'

interface Meta {
  title: string
  component: typeof Toast
  parameters?: Record<string, unknown>
  tags?: string[]
  argTypes?: Record<string, unknown>
}

interface StoryObj {
  args?: Record<string, unknown>
  parameters?: Record<string, unknown>
}

const meta: Meta = {
  title: 'UI/Toast',
  component: Toast,
  parameters: {
    layout: 'fullscreen',
  },
  tags: ['autodocs'],
  argTypes: {
    variant: {
      control: { type: 'select' },
      options: ['success', 'error', 'warning', 'info'],
      description: 'Visual style variant'
    },
    position: {
      control: { type: 'select' },
      options: ['top-right', 'top-left', 'bottom-right', 'bottom-left', 'top-center', 'bottom-center'],
      description: 'Position on screen'
    },
    title: {
      control: { type: 'text' },
      description: 'Optional title for the toast'
    },
    message: {
      control: { type: 'text' },
      description: 'Toast message content'
    },
    duration: {
      control: { type: 'number' },
      description: 'Auto-close duration in milliseconds (0 to disable)'
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
    message: 'This is a default toast message.',
    duration: 0, // Disable auto-close for demo
  },
}

export const Success: Story = {
  args: {
    variant: 'success',
    title: 'Success!',
    message: 'Your action was completed successfully.',
    duration: 0,
  },
}

export const Error: Story = {
  args: {
    variant: 'error',
    title: 'Error',
    message: 'Something went wrong. Please try again.',
    duration: 0,
  },
}

export const Warning: Story = {
  args: {
    variant: 'warning',
    title: 'Warning',
    message: 'Please review your input before proceeding.',
    duration: 0,
  },
}

export const Info: Story = {
  args: {
    variant: 'info',
    title: 'Information',
    message: 'Here is some important information for you.',
    duration: 0,
  },
}

export const TopLeft: Story = {
  args: {
    variant: 'success',
    position: 'top-left',
    title: 'Top Left',
    message: 'Toast positioned at top left.',
    duration: 0,
  },
}

export const BottomRight: Story = {
  args: {
    variant: 'info',
    position: 'bottom-right',
    title: 'Bottom Right',
    message: 'Toast positioned at bottom right.',
    duration: 0,
  },
}

export const TopCenter: Story = {
  args: {
    variant: 'warning',
    position: 'top-center',
    title: 'Top Center',
    message: 'Toast positioned at top center.',
    duration: 0,
  },
}

export const AutoClose: Story = {
  args: {
    variant: 'success',
    title: 'Auto Close',
    message: 'This toast will auto-close after 3 seconds.',
    duration: 3000,
  },
}

export const NoAutoClose: Story = {
  args: {
    variant: 'error',
    title: 'Manual Close',
    message: 'This toast requires manual closing.',
    duration: 0,
  },
}

export const WithoutIcon: Story = {
  args: {
    variant: 'info',
    title: 'No Icon',
    message: 'This toast does not display an icon.',
    showIcon: false,
    duration: 0,
  },
}

export const NotClosable: Story = {
  args: {
    variant: 'warning',
    title: 'Not Closable',
    message: 'This toast cannot be manually closed.',
    closable: false,
    duration: 0,
  },
}

export const MessageOnly: Story = {
  args: {
    variant: 'success',
    message: 'Toast with message only, no title.',
    duration: 0,
  },
}