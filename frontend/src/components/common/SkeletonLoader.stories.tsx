// Storybook types - temporary definitions since @storybook/react is not installed
interface Meta<T> {
  title: string;
  component: T;
  parameters?: any;
  argTypes?: any;
  tags?: string[];
}

interface StoryObj {
  args?: any;
  render?: (args: any) => React.ReactElement;
  parameters?: any;
}

import React from 'react';
import SkeletonLoader from './SkeletonLoader'

const meta: Meta<typeof SkeletonLoader> = {
  title: 'Common/SkeletonLoader',
  component: SkeletonLoader,
  parameters: {
    layout: 'padded',
    docs: {
      description: {
        component: 'A skeleton loader component that provides placeholder content while data is loading. Supports multiple variants for different content types.'
      }
    }
  },
  argTypes: {
    variant: {
      control: { type: 'select' },
      options: ['text', 'card', 'avatar', 'table'],
      description: 'Type of skeleton to display'
    },
    lines: {
      control: { type: 'number', min: 1, max: 10 },
      description: 'Number of lines for text and table variants'
    },
    width: {
      control: { type: 'text' },
      description: 'Custom width (CSS value)'
    },
    height: {
      control: { type: 'text' },
      description: 'Custom height (CSS value)'
    },
    rounded: {
      control: { type: 'boolean' },
      description: 'Whether to apply rounded corners'
    },
    animate: {
      control: { type: 'boolean' },
      description: 'Whether to show pulse animation'
    }
  },
  tags: ['autodocs']
}

export default meta
type Story = StoryObj

export const Default: Story = {
  args: {
    variant: 'text',
    lines: 1,
    animate: true,
    rounded: false
  }
}

export const TextSingleLine: Story = {
  args: {
    variant: 'text',
    lines: 1
  }
}

export const TextMultiLine: Story = {
  args: {
    variant: 'text',
    lines: 3
  }
}

export const Card: Story = {
  args: {
    variant: 'card'
  }
}

export const Avatar: Story = {
  args: {
    variant: 'avatar'
  }
}

export const Table: Story = {
  args: {
    variant: 'table',
    lines: 4
  }
}

export const CustomDimensions: Story = {
  args: {
    variant: 'text',
    width: '200px',
    height: '20px',
    rounded: true
  }
}

export const NoAnimation: Story = {
  args: {
    variant: 'text',
    lines: 2,
    animate: false
  }
}

export const AllVariants: Story = {
  render: () => (
    <div className="space-y-8">
      <div>
        <h3 className="text-lg font-semibold mb-4">Text Skeletons</h3>
        <div className="space-y-4">
          <div>
            <h4 className="text-sm font-medium mb-2">Single Line</h4>
            <SkeletonLoader variant="text" lines={1} />
          </div>
          <div>
            <h4 className="text-sm font-medium mb-2">Multiple Lines</h4>
            <SkeletonLoader variant="text" lines={3} />
          </div>
        </div>
      </div>

      <div>
        <h3 className="text-lg font-semibold mb-4">Avatar Skeleton</h3>
        <div className="flex items-center space-x-4">
          <SkeletonLoader variant="avatar" />
          <div className="flex-1">
            <SkeletonLoader variant="text" lines={2} />
          </div>
        </div>
      </div>

      <div>
        <h3 className="text-lg font-semibold mb-4">Card Skeleton</h3>
        <div className="max-w-sm">
          <SkeletonLoader variant="card" />
        </div>
      </div>

      <div>
        <h3 className="text-lg font-semibold mb-4">Table Skeleton</h3>
        <SkeletonLoader variant="table" lines={5} />
      </div>
    </div>
  )
}

export const UserProfileCard: Story = {
  render: () => (
    <div className="max-w-sm bg-white border rounded-lg p-6">
      <div className="flex items-center space-x-4 mb-4">
        <SkeletonLoader variant="avatar" />
        <div className="flex-1">
          <SkeletonLoader variant="text" lines={1} width="120px" />
          <div className="mt-1">
            <SkeletonLoader variant="text" lines={1} width="80px" />
          </div>
        </div>
      </div>
      <SkeletonLoader variant="text" lines={3} />
      <div className="mt-4 flex space-x-2">
        <SkeletonLoader width="80px" height="32px" rounded />
        <SkeletonLoader width="100px" height="32px" rounded />
      </div>
    </div>
  )
}

export const ArticleList: Story = {
  render: () => (
    <div className="space-y-6">
      {Array.from({ length: 3 }, (_, i) => (
        <div key={i} className="border-b pb-6">
          <div className="flex space-x-4">
            <SkeletonLoader width="120px" height="80px" rounded />
            <div className="flex-1">
              <SkeletonLoader variant="text" lines={1} width="60%" />
              <div className="mt-2">
                <SkeletonLoader variant="text" lines={2} />
              </div>
              <div className="mt-3 flex items-center space-x-4">
                <SkeletonLoader variant="avatar" />
                <SkeletonLoader variant="text" lines={1} width="100px" />
                <SkeletonLoader variant="text" lines={1} width="80px" />
              </div>
            </div>
          </div>
        </div>
      ))}
    </div>
  )
}

export const DataTable: Story = {
  render: () => (
    <div className="bg-white border rounded-lg overflow-hidden">
      <div className="px-6 py-4 border-b">
        <SkeletonLoader variant="text" lines={1} width="200px" />
      </div>
      <div className="divide-y">
        {Array.from({ length: 5 }, (_, i) => (
          <div key={i} className="px-6 py-4 flex items-center space-x-4">
            <SkeletonLoader variant="avatar" />
            <div className="flex-1 grid grid-cols-4 gap-4">
              <SkeletonLoader variant="text" lines={1} />
              <SkeletonLoader variant="text" lines={1} />
              <SkeletonLoader variant="text" lines={1} />
              <SkeletonLoader variant="text" lines={1} width="60px" />
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}