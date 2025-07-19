import type { Meta, StoryObj } from '@storybook/react'
import LoadingOverlay from './LoadingOverlay'

const meta: Meta<typeof LoadingOverlay> = {
  title: 'Common/LoadingOverlay',
  component: LoadingOverlay,
  parameters: {
    layout: 'padded',
    docs: {
      description: {
        component: 'A loading overlay component that can cover containers or the entire screen with a loading spinner and optional message.'
      }
    }
  },
  argTypes: {
    mode: {
      control: { type: 'select' },
      options: ['fullscreen', 'container'],
      description: 'Positioning mode of the overlay'
    },
    message: {
      control: { type: 'text' },
      description: 'Optional loading message to display'
    },
    backdrop: {
      control: { type: 'boolean' },
      description: 'Whether to show backdrop'
    },
    blur: {
      control: { type: 'boolean' },
      description: 'Whether to apply backdrop blur'
    },
    size: {
      control: { type: 'select' },
      options: ['small', 'medium', 'large'],
      description: 'Size of the spinner'
    },
    color: {
      control: { type: 'select' },
      options: ['primary', 'secondary', 'white'],
      description: 'Color theme of the spinner'
    }
  },
  tags: ['autodocs']
}

export default meta
type Story = StoryObj<typeof LoadingOverlay>

export const Default: Story = {
  args: {
    mode: 'container',
    backdrop: true,
    blur: true,
    size: 'medium',
    color: 'primary'
  },
  render: (args) => (
    <div className="relative h-64 w-96 bg-gray-100 border rounded-lg p-4">
      <h3 className="text-lg font-semibold mb-2">Container Content</h3>
      <p>This content is covered by the loading overlay.</p>
      <LoadingOverlay {...args} />
    </div>
  )
}

export const WithMessage: Story = {
  args: {
    mode: 'container',
    message: 'Loading data...',
    backdrop: true,
    blur: true,
    size: 'medium',
    color: 'primary'
  },
  render: (args) => (
    <div className="relative h-64 w-96 bg-gray-100 border rounded-lg p-4">
      <h3 className="text-lg font-semibold mb-2">Container Content</h3>
      <p>This content is covered by the loading overlay with a message.</p>
      <LoadingOverlay {...args} />
    </div>
  )
}

export const NoBackdrop: Story = {
  args: {
    mode: 'container',
    message: 'Loading...',
    backdrop: false,
    blur: false,
    size: 'medium',
    color: 'primary'
  },
  render: (args) => (
    <div className="relative h-64 w-96 bg-gray-100 border rounded-lg p-4">
      <h3 className="text-lg font-semibold mb-2">Container Content</h3>
      <p>This content is visible behind the loading overlay.</p>
      <LoadingOverlay {...args} />
    </div>
  )
}

export const WhiteSpinner: Story = {
  args: {
    mode: 'container',
    message: 'Processing...',
    backdrop: true,
    blur: true,
    size: 'large',
    color: 'white'
  },
  render: (args) => (
    <div className="relative h-64 w-96 bg-gradient-to-br from-blue-600 to-purple-600 rounded-lg p-4">
      <h3 className="text-lg font-semibold mb-2 text-white">Dark Container</h3>
      <p className="text-white">White spinner works well on dark backgrounds.</p>
      <LoadingOverlay {...args} />
    </div>
  )
}

export const DifferentSizes: Story = {
  render: () => (
    <div className="grid grid-cols-3 gap-4">
      {(['small', 'medium', 'large'] as const).map((size) => (
        <div key={size} className="relative h-32 w-32 bg-gray-100 border rounded-lg">
          <div className="absolute top-2 left-2 text-xs font-medium">{size}</div>
          <LoadingOverlay
            mode="container"
            size={size}
            color="primary"
            backdrop={true}
            blur={false}
          />
        </div>
      ))}
    </div>
  )
}

export const WithCustomContent: Story = {
  args: {
    mode: 'container',
    backdrop: true,
    blur: true,
    size: 'medium',
    color: 'primary'
  },
  render: (args) => (
    <div className="relative h-64 w-96 bg-gray-100 border rounded-lg p-4">
      <h3 className="text-lg font-semibold mb-2">Container Content</h3>
      <p>Loading overlay with custom additional content.</p>
      <LoadingOverlay {...args}>
        <div className="mt-4 text-center">
          <div className="text-sm text-gray-600">Please wait while we process your request</div>
          <div className="mt-2">
            <button className="px-4 py-2 text-sm bg-white bg-opacity-20 rounded hover:bg-opacity-30 transition-colors">
              Cancel
            </button>
          </div>
        </div>
      </LoadingOverlay>
    </div>
  )
}

export const Fullscreen: Story = {
  args: {
    mode: 'fullscreen',
    message: 'Loading application...',
    backdrop: true,
    blur: true,
    size: 'large',
    color: 'primary'
  },
  parameters: {
    docs: {
      description: {
        story: 'Fullscreen overlay that covers the entire viewport. Use sparingly for application-wide loading states.'
      }
    }
  }
}