import Modal from './Modal'
import Button from './Button'
import Input from './Input'

interface Meta {
  title: string
  component: typeof Modal
  parameters?: Record<string, unknown>
  tags?: string[]
  argTypes?: Record<string, unknown>
}

interface StoryObj {
  args?: Record<string, unknown>
  parameters?: Record<string, unknown>
}

const meta: Meta = {
  title: 'UI/Modal',
  component: Modal,
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
  argTypes: {
    size: {
      control: { type: 'select' },
      options: ['sm', 'md', 'lg', 'xl', 'full'],
      description: 'Size of the modal'
    },
    isOpen: {
      control: { type: 'boolean' },
      description: 'Modal visibility state'
    },
    title: {
      control: { type: 'text' },
      description: 'Modal title'
    },
    description: {
      control: { type: 'text' },
      description: 'Modal description'
    },
    closeOnOverlayClick: {
      control: { type: 'boolean' },
      description: 'Close modal when clicking overlay'
    },
    closeOnEscape: {
      control: { type: 'boolean' },
      description: 'Close modal when pressing Escape'
    },
    showCloseButton: {
      control: { type: 'boolean' },
      description: 'Show close button in header'
    }
  },
}

export default meta
type Story = StoryObj

export const Default: Story = {
  args: {
    isOpen: true,
    title: 'Default Modal',
    onClose: () => console.log('Modal closed'),
    children: (
      <div>
        <p className="mb-4">This is a default modal with some content.</p>
        <Button>Action Button</Button>
      </div>
    ),
  },
}

export const WithDescription: Story = {
  args: {
    isOpen: true,
    title: 'Modal with Description',
    description: 'This modal includes both a title and a description.',
    onClose: () => console.log('Modal closed'),
    children: (
      <div>
        <p>Modal content goes here.</p>
      </div>
    ),
  },
}

export const Small: Story = {
  args: {
    isOpen: true,
    size: 'sm',
    title: 'Small Modal',
    onClose: () => console.log('Modal closed'),
    children: (
      <div>
        <p>This is a small modal.</p>
      </div>
    ),
  },
}

export const Large: Story = {
  args: {
    isOpen: true,
    size: 'lg',
    title: 'Large Modal',
    onClose: () => console.log('Modal closed'),
    children: (
      <div>
        <p className="mb-4">This is a large modal with more content space.</p>
        <p className="mb-4">It can accommodate more complex layouts and longer content.</p>
        <div className="grid grid-cols-2 gap-4">
          <Button>Action 1</Button>
          <Button variant="outline">Action 2</Button>
        </div>
      </div>
    ),
  },
}

export const ExtraLarge: Story = {
  args: {
    isOpen: true,
    size: 'xl',
    title: 'Extra Large Modal',
    onClose: () => console.log('Modal closed'),
    children: (
      <div>
        <p className="mb-6">This is an extra large modal suitable for complex forms or detailed content.</p>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <h3 className="text-lg font-medium mb-4">Left Column</h3>
            <p className="mb-4">Content for the left side of the modal.</p>
            <Button>Left Action</Button>
          </div>
          <div>
            <h3 className="text-lg font-medium mb-4">Right Column</h3>
            <p className="mb-4">Content for the right side of the modal.</p>
            <Button variant="outline">Right Action</Button>
          </div>
        </div>
      </div>
    ),
  },
}

export const FullScreen: Story = {
  args: {
    isOpen: true,
    size: 'full',
    title: 'Full Screen Modal',
    description: 'This modal takes up most of the screen space.',
    onClose: () => console.log('Modal closed'),
    children: (
      <div>
        <p className="mb-6">This is a full-screen modal suitable for complex applications or detailed views.</p>
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="space-y-4">
            <h3 className="text-lg font-medium">Section 1</h3>
            <p>Content for section 1.</p>
            <Button>Action 1</Button>
          </div>
          <div className="space-y-4">
            <h3 className="text-lg font-medium">Section 2</h3>
            <p>Content for section 2.</p>
            <Button variant="outline">Action 2</Button>
          </div>
          <div className="space-y-4">
            <h3 className="text-lg font-medium">Section 3</h3>
            <p>Content for section 3.</p>
            <Button variant="ghost">Action 3</Button>
          </div>
        </div>
      </div>
    ),
  },
}

export const FormModal: Story = {
  args: {
    isOpen: true,
    title: 'User Registration',
    description: 'Please fill out the form below to create a new account.',
    onClose: () => console.log('Modal closed'),
    children: (
      <form className="space-y-4">
        <Input
          label="Full Name"
          placeholder="Enter your full name"
          required
        />
        <Input
          label="Email"
          type="email"
          placeholder="Enter your email"
          required
        />
        <Input
          label="Password"
          type="password"
          placeholder="Enter your password"
          required
        />
        <div className="flex gap-3 pt-4">
          <Button type="submit" className="flex-1">
            Create Account
          </Button>
          <Button type="button" variant="outline" className="flex-1">
            Cancel
          </Button>
        </div>
      </form>
    ),
  },
}

export const NoCloseButton: Story = {
  args: {
    isOpen: true,
    title: 'Modal without Close Button',
    showCloseButton: false,
    onClose: () => console.log('Modal closed'),
    children: (
      <div>
        <p className="mb-4">This modal doesn't have a close button in the header.</p>
        <p className="mb-4">Users must use the action buttons or press Escape to close.</p>
        <Button onClick={() => console.log('Modal closed')}>
          Close Modal
        </Button>
      </div>
    ),
  },
}

export const NoOverlayClose: Story = {
  args: {
    isOpen: true,
    title: 'Modal with Restricted Closing',
    closeOnOverlayClick: false,
    closeOnEscape: false,
    onClose: () => console.log('Modal closed'),
    children: (
      <div>
        <p className="mb-4">This modal cannot be closed by clicking the overlay or pressing Escape.</p>
        <p className="mb-4">Users must use the close button or action buttons.</p>
        <Button onClick={() => console.log('Modal closed')}>
          Close Modal
        </Button>
      </div>
    ),
  },
}

export const LongContent: Story = {
  args: {
    isOpen: true,
    title: 'Modal with Scrollable Content',
    description: 'This modal demonstrates how content scrolling works.',
    onClose: () => console.log('Modal closed'),
    children: (
      <div className="space-y-4">
        {Array.from({ length: 20 }, (_, i) => (
          <p key={i} className="p-4 bg-gray-50 rounded">
            This is paragraph {i + 1}. Lorem ipsum dolor sit amet, consectetur adipiscing elit. 
            Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim 
            veniam, quis nostrud exercitation ullamco laboris.
          </p>
        ))}
        <Button className="w-full">
          Action at Bottom
        </Button>
      </div>
    ),
  },
}