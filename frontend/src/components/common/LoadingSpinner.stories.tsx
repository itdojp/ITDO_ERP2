import type { Meta, StoryObj } from '@storybook/react'
import LoadingSpinner from './LoadingSpinner'

const meta: Meta<typeof LoadingSpinner> = {
  title: 'Common/LoadingSpinner',
  component: LoadingSpinner,
  parameters: {
    layout: 'centered',
    docs: {
      description: {
        component: 'A customizable loading spinner component with different sizes and colors.'
      }
    }
  },
  argTypes: {
    size: {
      control: { type: 'select' },
      options: ['small', 'medium', 'large'],
      description: 'Size of the spinner'
    },
    color: {
      control: { type: 'select' },
      options: ['primary', 'secondary', 'white'],
      description: 'Color theme of the spinner'
    },
    className: {
      control: { type: 'text' },
      description: 'Additional CSS classes'
    }
  },
  tags: ['autodocs']
}

export default meta
type Story = StoryObj<typeof LoadingSpinner>

export const Default: Story = {
  args: {
    size: 'medium',
    color: 'primary'
  }
}

export const Small: Story = {
  args: {
    size: 'small',
    color: 'primary'
  }
}

export const Large: Story = {
  args: {
    size: 'large',
    color: 'primary'
  }
}

export const Secondary: Story = {
  args: {
    size: 'medium',
    color: 'secondary'
  }
}

export const White: Story = {
  args: {
    size: 'medium',
    color: 'white'
  },
  parameters: {
    backgrounds: { default: 'dark' }
  }
}

export const AllSizes: Story = {
  render: () => (
    <div className="flex items-center gap-4">
      <div className="text-center">
        <LoadingSpinner size="small" color="primary" />
        <p className="mt-2 text-sm">Small</p>
      </div>
      <div className="text-center">
        <LoadingSpinner size="medium" color="primary" />
        <p className="mt-2 text-sm">Medium</p>
      </div>
      <div className="text-center">
        <LoadingSpinner size="large" color="primary" />
        <p className="mt-2 text-sm">Large</p>
      </div>
    </div>
  )
}

export const AllColors: Story = {
  render: () => (
    <div className="flex items-center gap-8">
      <div className="text-center">
        <LoadingSpinner size="medium" color="primary" />
        <p className="mt-2 text-sm">Primary</p>
      </div>
      <div className="text-center">
        <LoadingSpinner size="medium" color="secondary" />
        <p className="mt-2 text-sm">Secondary</p>
      </div>
      <div className="text-center bg-gray-800 p-4 rounded">
        <LoadingSpinner size="medium" color="white" />
        <p className="mt-2 text-sm text-white">White</p>
      </div>
    </div>
  )
}

export const CustomClassName: Story = {
  args: {
    size: 'medium',
    color: 'primary',
    className: 'opacity-50'
  }
}