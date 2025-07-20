import Dialog from './Dialog'

interface Meta {
  title: string
  component: typeof Dialog
  parameters?: Record<string, unknown>
  tags?: string[]
  argTypes?: Record<string, unknown>
}

interface StoryObj {
  args?: Record<string, unknown>
  parameters?: Record<string, unknown>
}

const meta: Meta = {
  title: 'UI/Dialog',
  component: Dialog,
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
  argTypes: {
    type: {
      control: { type: 'select' },
      options: ['confirm', 'alert', 'success', 'danger'],
      description: 'Dialog type'
    },
    isOpen: {
      control: { type: 'boolean' },
      description: 'Dialog visibility state'
    },
    title: {
      control: { type: 'text' },
      description: 'Dialog title'
    },
    description: {
      control: { type: 'text' },
      description: 'Dialog description'
    },
    confirmText: {
      control: { type: 'text' },
      description: 'Confirm button text'
    },
    cancelText: {
      control: { type: 'text' },
      description: 'Cancel button text'
    },
    loading: {
      control: { type: 'boolean' },
      description: 'Loading state'
    },
    closeOnOverlayClick: {
      control: { type: 'boolean' },
      description: 'Close dialog when clicking overlay'
    },
    closeOnEscape: {
      control: { type: 'boolean' },
      description: 'Close dialog when pressing Escape'
    }
  },
}

export default meta
type Story = StoryObj

export const Default: Story = {
  args: {
    isOpen: true,
    title: 'Confirm Action',
    description: 'Are you sure you want to perform this action?',
    onClose: () => console.log('Dialog closed'),
    onConfirm: () => console.log('Confirmed'),
    onCancel: () => console.log('Cancelled'),
  },
}

export const Success: Story = {
  args: {
    isOpen: true,
    type: 'success',
    title: 'Operation Successful',
    description: 'Your action has been completed successfully.',
    confirmText: 'Continue',
    cancelText: 'Close',
    onClose: () => console.log('Dialog closed'),
    onConfirm: () => console.log('Continue clicked'),
    onCancel: () => console.log('Close clicked'),
  },
}

export const Danger: Story = {
  args: {
    isOpen: true,
    type: 'danger',
    title: 'Delete User',
    description: 'Are you sure you want to delete this user? This action cannot be undone.',
    confirmText: 'Delete',
    cancelText: 'Cancel',
    onClose: () => console.log('Dialog closed'),
    onConfirm: () => console.log('Delete confirmed'),
    onCancel: () => console.log('Delete cancelled'),
  },
}

export const Alert: Story = {
  args: {
    isOpen: true,
    type: 'alert',
    title: 'Warning',
    description: 'Please review your input before proceeding. Some fields may be incomplete.',
    confirmText: 'Review',
    cancelText: 'Continue Anyway',
    onClose: () => console.log('Dialog closed'),
    onConfirm: () => console.log('Review clicked'),
    onCancel: () => console.log('Continue anyway clicked'),
  },
}

export const Loading: Story = {
  args: {
    isOpen: true,
    type: 'danger',
    title: 'Deleting User',
    description: 'Please wait while we delete the user account...',
    confirmText: 'Deleting...',
    cancelText: 'Cancel',
    loading: true,
    onClose: () => console.log('Dialog closed'),
    onConfirm: () => console.log('Delete in progress'),
    onCancel: () => console.log('Delete cancelled'),
  },
}

export const SimpleConfirm: Story = {
  args: {
    isOpen: true,
    title: 'Save Changes',
    onClose: () => console.log('Dialog closed'),
    onConfirm: () => console.log('Changes saved'),
    onCancel: () => console.log('Changes cancelled'),
  },
}

export const CustomButtons: Story = {
  args: {
    isOpen: true,
    type: 'success',
    title: 'Account Created',
    description: 'Your account has been successfully created. What would you like to do next?',
    confirmText: 'Go to Dashboard',
    cancelText: 'Stay Here',
    onClose: () => console.log('Dialog closed'),
    onConfirm: () => console.log('Go to dashboard'),
    onCancel: () => console.log('Stay here'),
  },
}

export const NoDescription: Story = {
  args: {
    isOpen: true,
    title: 'Logout',
    confirmText: 'Logout',
    cancelText: 'Stay',
    onClose: () => console.log('Dialog closed'),
    onConfirm: () => console.log('Logout confirmed'),
    onCancel: () => console.log('Stay logged in'),
  },
}

export const LongContent: Story = {
  args: {
    isOpen: true,
    type: 'alert',
    title: 'Terms and Conditions',
    description: 'Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.',
    confirmText: 'Accept',
    cancelText: 'Decline',
    onClose: () => console.log('Dialog closed'),
    onConfirm: () => console.log('Terms accepted'),
    onCancel: () => console.log('Terms declined'),
  },
}

export const NoOverlayClose: Story = {
  args: {
    isOpen: true,
    type: 'danger',
    title: 'Critical Operation',
    description: 'This is a critical operation that requires your explicit confirmation.',
    confirmText: 'Proceed',
    cancelText: 'Abort',
    closeOnOverlayClick: false,
    closeOnEscape: false,
    onClose: () => console.log('Dialog closed'),
    onConfirm: () => console.log('Operation proceeded'),
    onCancel: () => console.log('Operation aborted'),
  },
}