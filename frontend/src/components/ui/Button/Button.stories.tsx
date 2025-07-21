import type { Meta, StoryObj } from '@storybook/react'
import Button from './Button'
import { Download, Heart, Plus, Trash2, Settings, Save } from 'lucide-react'

const meta: Meta<typeof Button> = {
  title: 'UI/Button',
  component: Button,
  parameters: {
    layout: 'centered',
    docs: {
      description: {
        component: 'A versatile button component with multiple variants, sizes, and states.',
      },
    },
  },
  argTypes: {
    variant: {
      control: 'select',
      options: ['default', 'primary', 'secondary', 'outline', 'ghost', 'destructive', 'danger'],
    },
    size: {
      control: 'select',
      options: ['xs', 'sm', 'md', 'lg', 'xl'],
    },
    rounded: {
      control: 'select',
      options: ['none', 'sm', 'md', 'lg', 'full'],
    },
    iconPosition: {
      control: 'select',
      options: ['left', 'right'],
    },
    loading: {
      control: 'boolean',
    },
    disabled: {
      control: 'boolean',
    },
    fullWidth: {
      control: 'boolean',
    },
  },
  tags: ['autodocs'],
}

export default meta
type Story = StoryObj<typeof Button>

export const Default: Story = {
  args: {
    children: 'Button',
  },
}

export const Variants: Story = {
  render: () => (
    <div className="flex flex-wrap gap-4">
      <Button variant="default">Default</Button>
      <Button variant="primary">Primary</Button>
      <Button variant="secondary">Secondary</Button>
      <Button variant="outline">Outline</Button>
      <Button variant="ghost">Ghost</Button>
      <Button variant="destructive">Destructive</Button>
      <Button variant="danger">Danger</Button>
    </div>
  ),
}

export const Sizes: Story = {
  render: () => (
    <div className="flex flex-wrap items-center gap-4">
      <Button size="xs">Extra Small</Button>
      <Button size="sm">Small</Button>
      <Button size="md">Medium</Button>
      <Button size="lg">Large</Button>
      <Button size="xl">Extra Large</Button>
    </div>
  ),
}

export const WithIcons: Story = {
  render: () => (
    <div className="flex flex-wrap gap-4">
      <Button icon={<Download />} iconPosition="left">
        Download
      </Button>
      <Button icon={<Heart />} iconPosition="right" variant="outline">
        Like
      </Button>
      <Button icon={<Plus />} variant="primary">
        Add New
      </Button>
      <Button icon={<Settings />} variant="ghost" size="sm">
        Settings
      </Button>
    </div>
  ),
}

export const LoadingStates: Story = {
  render: () => (
    <div className="flex flex-wrap gap-4">
      <Button loading>Loading</Button>
      <Button loading variant="primary">
        Saving...
      </Button>
      <Button loading variant="outline" icon={<Save />}>
        Saving Document
      </Button>
      <Button loading size="sm">
        Processing
      </Button>
    </div>
  ),
}

export const DisabledStates: Story = {
  render: () => (
    <div className="flex flex-wrap gap-4">
      <Button disabled>Disabled</Button>
      <Button disabled variant="primary">
        Primary Disabled
      </Button>
      <Button disabled variant="outline">
        Outline Disabled
      </Button>
      <Button disabled icon={<Trash2 />}>
        Delete Disabled
      </Button>
    </div>
  ),
}

export const RoundedOptions: Story = {
  render: () => (
    <div className="flex flex-wrap gap-4">
      <Button rounded="none">No Radius</Button>
      <Button rounded="sm">Small Radius</Button>
      <Button rounded="md">Medium Radius</Button>
      <Button rounded="lg">Large Radius</Button>
      <Button rounded="full">Pill Shape</Button>
    </div>
  ),
}

export const FullWidth: Story = {
  render: () => (
    <div className="w-96 space-y-4">
      <Button fullWidth variant="primary">
        Full Width Primary
      </Button>
      <Button fullWidth variant="outline">
        Full Width Outline
      </Button>
      <Button fullWidth icon={<Download />}>
        Full Width with Icon
      </Button>
    </div>
  ),
}

export const InteractiveExample: Story = {
  args: {
    children: 'Click me!',
    variant: 'primary',
    size: 'md',
  },
  parameters: {
    docs: {
      description: {
        story: 'Try changing the props in the controls panel below to see how the button responds.',
      },
    },
  },
}

export const ComplexButtons: Story = {
  render: () => (
    <div className="flex flex-wrap gap-4">
      <Button variant="primary" size="lg" icon={<Download />} rounded="lg">
        Download App
      </Button>
      <Button variant="destructive" size="sm" icon={<Trash2 />} iconPosition="right">
        Delete Item
      </Button>
      <Button variant="outline" size="md" icon={<Plus />} fullWidth>
        Add to Collection
      </Button>
      <Button variant="ghost" size="xs" icon={<Settings />} rounded="full" />
    </div>
  ),
}

export const ButtonGroup: Story = {
  render: () => (
    <div className="inline-flex rounded-md shadow-sm" role="group">
      <Button variant="outline" size="sm" rounded="none" className="rounded-l-md border-r-0">
        Left
      </Button>
      <Button variant="outline" size="sm" rounded="none" className="border-r-0">
        Center
      </Button>
      <Button variant="outline" size="sm" rounded="none" className="rounded-r-md">
        Right
      </Button>
    </div>
  ),
}