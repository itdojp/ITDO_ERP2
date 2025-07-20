import Loading from './Loading'

interface Meta {
  title: string
  component: typeof Loading
  parameters?: Record<string, unknown>
  tags?: string[]
  argTypes?: Record<string, unknown>
}

interface StoryObj {
  args?: Record<string, unknown>
  parameters?: Record<string, unknown>
  decorators?: Array<(Story: () => JSX.Element) => JSX.Element>
}

const meta: Meta = {
  title: 'UI/Loading',
  component: Loading,
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
  argTypes: {
    size: {
      control: { type: 'select' },
      options: ['sm', 'md', 'lg', 'xl'],
      description: 'Size of the loading spinner'
    },
    variant: {
      control: { type: 'select' },
      options: ['primary', 'secondary', 'light', 'dark'],
      description: 'Visual style variant'
    },
    message: {
      control: { type: 'text' },
      description: 'Optional loading message'
    },
    fullScreen: {
      control: { type: 'boolean' },
      description: 'Display as full screen overlay'
    },
    overlay: {
      control: { type: 'boolean' },
      description: 'Add background overlay'
    }
  },
}

export default meta
type Story = StoryObj

export const Default: Story = {
  args: {},
}

export const WithMessage: Story = {
  args: {
    message: 'Loading data...',
  },
}

export const Small: Story = {
  args: {
    size: 'sm',
    message: 'Loading...',
  },
}

export const Large: Story = {
  args: {
    size: 'lg',
    message: 'Processing...',
  },
}

export const ExtraLarge: Story = {
  args: {
    size: 'xl',
    message: 'Please wait...',
  },
}

export const Primary: Story = {
  args: {
    variant: 'primary',
    message: 'Primary loading',
  },
}

export const Secondary: Story = {
  args: {
    variant: 'secondary',
    message: 'Secondary loading',
  },
}

export const Light: Story = {
  args: {
    variant: 'light',
    message: 'Light loading',
  },
  parameters: {
    backgrounds: { default: 'dark' },
  },
}

export const Dark: Story = {
  args: {
    variant: 'dark',
    message: 'Dark loading',
  },
}

export const WithOverlay: Story = {
  args: {
    overlay: true,
    message: 'Loading with overlay...',
  },
  decorators: [
    (Story) => (
      <div className="relative h-64 w-96 bg-gray-100 rounded-lg p-4">
        <div className="text-center">Content behind overlay</div>
        <Story />
      </div>
    ),
  ],
}

export const FullScreen: Story = {
  args: {
    fullScreen: true,
    message: 'Full screen loading...',
  },
  parameters: {
    layout: 'fullscreen',
  },
}