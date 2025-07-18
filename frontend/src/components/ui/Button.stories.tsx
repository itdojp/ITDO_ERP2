import Button from './Button'

// Storybook configuration for Button component
// Note: This is a placeholder for when Storybook is configured
export default {
  title: 'UI/Button',
  component: Button,
  parameters: {
    layout: 'centered',
    docs: {
      description: {
        component: 'A versatile button component with multiple variants, sizes, and states.'
      }
    }
  }
}

// Story examples for different button variants
export const ButtonStories = {
  Default: () => <Button>Button</Button>,
  Primary: () => <Button variant="primary">Primary Button</Button>,
  Secondary: () => <Button variant="secondary">Secondary Button</Button>,
  Outline: () => <Button variant="outline">Outline Button</Button>,
  Ghost: () => <Button variant="ghost">Ghost Button</Button>,
  Destructive: () => <Button variant="destructive">Delete</Button>,
  Small: () => <Button size="sm">Small Button</Button>,
  Large: () => <Button size="lg">Large Button</Button>,
  Loading: () => <Button loading>Loading...</Button>,
  Disabled: () => <Button disabled>Disabled Button</Button>,
  FullWidth: () => <Button fullWidth>Full Width Button</Button>,
  WithIcon: () => (
    <Button icon={
      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
      </svg>
    }>
      Add Item
    </Button>
  ),
  WithIconRight: () => (
    <Button 
      icon={
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
        </svg>
      }
      iconPosition="right"
    >
      Next
    </Button>
  )
}