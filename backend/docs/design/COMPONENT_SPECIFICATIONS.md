# Component Specifications

**Document ID**: ITDO-ERP-DD-CS-001  
**Version**: 1.0  
**Date**: 2025-07-16  
**Author**: Claude Code AI  
**Issue**: #160  

---

## 1. Overview

This document provides detailed specifications for all UI components required in the ITDO ERP2 system. Each component includes props, variants, states, accessibility requirements, and usage examples.

## 2. Core Components

### 2.1 Button Component

#### 2.1.1 Specification

```yaml
Component: Button
Description: Interactive element for user actions and form submissions
Category: Core
Priority: High

Props:
  - name: variant
    type: 'primary' | 'secondary' | 'outline' | 'ghost' | 'danger'
    required: false
    default: 'primary'
    description: Visual style variant

  - name: size
    type: 'sm' | 'md' | 'lg'
    required: false
    default: 'md'
    description: Button size

  - name: disabled
    type: boolean
    required: false
    default: false
    description: Disable button interactions

  - name: loading
    type: boolean
    required: false
    default: false
    description: Show loading spinner

  - name: icon
    type: LucideIcon
    required: false
    description: Icon component from lucide-react

  - name: iconPosition
    type: 'left' | 'right'
    required: false
    default: 'left'
    description: Icon position relative to text

  - name: fullWidth
    type: boolean
    required: false
    default: false
    description: Full width button

  - name: type
    type: 'button' | 'submit' | 'reset'
    required: false
    default: 'button'
    description: HTML button type

  - name: onClick
    type: (event: MouseEvent) => void
    required: false
    description: Click handler

  - name: children
    type: ReactNode
    required: false
    description: Button content

Variants:
  - primary: Blue background (#3b82f6), white text, high emphasis
  - secondary: Gray background (#6b7280), white text, medium emphasis
  - outline: Transparent background, colored border and text
  - ghost: Minimal styling, subtle hover effects
  - danger: Red background (#ef4444), white text, destructive actions

States:
  - default: Base appearance with appropriate variant styling
  - hover: Enhanced visual feedback (darker background, shadow)
  - active: Pressed state (slightly darker, inset shadow)
  - disabled: Reduced opacity (0.5), no interactions, cursor disabled
  - loading: Spinner animation, disabled interactions, maintains dimensions

Accessibility:
  - Focus ring with 2px offset and high contrast color
  - Minimum touch target 44x44px for mobile devices
  - ARIA labels for icon-only buttons
  - Proper disabled state with aria-disabled
  - Screen reader announcements for loading state
  - Keyboard navigation support (Enter and Space)

Animation:
  - Smooth color transitions (150ms ease-in-out)
  - Hover state transitions (100ms ease-in-out)
  - Loading spinner rotation (1s linear infinite)
  - Focus ring animation (100ms ease-in-out)

Testing:
  - Unit: Props rendering, event handlers, accessibility
  - Integration: Form submission, navigation actions
  - Visual: All variants, states, and responsive behavior
  - A11y: Screen reader compatibility, keyboard navigation
```

#### 2.1.2 Usage Examples

```typescript
// Basic usage
<Button>Click me</Button>

// With variant and size
<Button variant="secondary" size="lg">Large Secondary</Button>

// With icon
<Button icon={Plus} variant="primary">Add Item</Button>

// Loading state
<Button loading disabled>Processing...</Button>

// Icon-only button
<Button icon={Search} aria-label="Search" />

// Full width
<Button fullWidth variant="primary" type="submit">
  Submit Form
</Button>

// Danger action
<Button variant="danger" onClick={handleDelete}>
  Delete Item
</Button>
```

### 2.2 Input Component

#### 2.2.1 Specification

```yaml
Component: Input
Description: Text input field for user data collection
Category: Core
Priority: High

Props:
  - name: type
    type: 'text' | 'email' | 'password' | 'number' | 'tel' | 'url' | 'search'
    required: false
    default: 'text'
    description: Input type

  - name: size
    type: 'sm' | 'md' | 'lg'
    required: false
    default: 'md'
    description: Input size

  - name: disabled
    type: boolean
    required: false
    default: false
    description: Disable input

  - name: readonly
    type: boolean
    required: false
    default: false
    description: Read-only input

  - name: required
    type: boolean
    required: false
    default: false
    description: Required field

  - name: placeholder
    type: string
    required: false
    description: Placeholder text

  - name: value
    type: string
    required: false
    description: Controlled value

  - name: defaultValue
    type: string
    required: false
    description: Uncontrolled default value

  - name: error
    type: string
    required: false
    description: Error message

  - name: helperText
    type: string
    required: false
    description: Helper text

  - name: label
    type: string
    required: false
    description: Input label

  - name: prefixIcon
    type: LucideIcon
    required: false
    description: Icon before input

  - name: suffixIcon
    type: LucideIcon
    required: false
    description: Icon after input

  - name: clearable
    type: boolean
    required: false
    default: false
    description: Show clear button

  - name: maxLength
    type: number
    required: false
    description: Maximum character length

  - name: showCount
    type: boolean
    required: false
    default: false
    description: Show character count

  - name: autoComplete
    type: string
    required: false
    description: HTML autocomplete attribute

  - name: autoFocus
    type: boolean
    required: false
    default: false
    description: Auto focus on mount

  - name: onChange
    type: (event: ChangeEvent) => void
    required: false
    description: Change handler

  - name: onBlur
    type: (event: FocusEvent) => void
    required: false
    description: Blur handler

  - name: onFocus
    type: (event: FocusEvent) => void
    required: false
    description: Focus handler

  - name: onKeyDown
    type: (event: KeyboardEvent) => void
    required: false
    description: Key down handler

States:
  - default: Standard input appearance
  - focus: Blue border (#3b82f6), focus ring, enhanced contrast
  - error: Red border (#ef4444), red background tint, error icon
  - disabled: Gray background, reduced opacity, disabled cursor
  - readonly: Light gray background, standard border, readonly cursor

Accessibility:
  - Label association with htmlFor or aria-labelledby
  - Error message association with aria-describedby
  - Required field indication with aria-required
  - Invalid state with aria-invalid
  - Helper text association with aria-describedby
  - Focus management and keyboard navigation
  - Screen reader announcements for state changes

Validation:
  - Built-in HTML5 validation support
  - Custom validation function support
  - Real-time validation feedback
  - Error message display
  - Success state indication
```

#### 2.2.2 Usage Examples

```typescript
// Basic input
<Input
  label="Email Address"
  type="email"
  placeholder="Enter your email"
  required
/>

// Input with icon and helper text
<Input
  label="Search"
  type="search"
  prefixIcon={Search}
  placeholder="Search users..."
  helperText="Search by name or email"
  clearable
/>

// Input with validation
<Input
  label="Password"
  type="password"
  error="Password must be at least 8 characters"
  suffixIcon={Eye}
  maxLength={100}
  showCount
/>

// Controlled input
<Input
  label="Username"
  value={username}
  onChange={(e) => setUsername(e.target.value)}
  onBlur={validateUsername}
/>
```

### 2.3 Select Component

#### 2.3.1 Specification

```yaml
Component: Select
Description: Dropdown selection component for choosing from predefined options
Category: Core
Priority: High

Props:
  - name: options
    type: SelectOption[]
    required: true
    description: Array of options to select from

  - name: value
    type: string | string[]
    required: false
    description: Selected value(s)

  - name: defaultValue
    type: string | string[]
    required: false
    description: Default selected value(s)

  - name: multiple
    type: boolean
    required: false
    default: false
    description: Allow multiple selection

  - name: searchable
    type: boolean
    required: false
    default: false
    description: Enable search functionality

  - name: placeholder
    type: string
    required: false
    default: 'Select...'
    description: Placeholder text

  - name: disabled
    type: boolean
    required: false
    default: false
    description: Disable select

  - name: loading
    type: boolean
    required: false
    default: false
    description: Show loading state

  - name: error
    type: string
    required: false
    description: Error message

  - name: label
    type: string
    required: false
    description: Select label

  - name: helperText
    type: string
    required: false
    description: Helper text

  - name: clearable
    type: boolean
    required: false
    default: false
    description: Show clear button

  - name: maxDisplayItems
    type: number
    required: false
    default: 100
    description: Maximum items to display

  - name: noOptionsMessage
    type: string
    required: false
    default: 'No options'
    description: Message when no options available

  - name: onChange
    type: (value: string | string[]) => void
    required: false
    description: Change handler

  - name: onSearch
    type: (query: string) => void
    required: false
    description: Search handler

Types:
  - SelectOption:
      value: string
      label: string
      disabled?: boolean
      group?: string

States:
  - closed: Dropdown closed, shows selected value or placeholder
  - open: Dropdown open, shows options list
  - loading: Loading spinner, disabled interactions
  - error: Error state with red border and error message
  - disabled: Disabled appearance, no interactions

Accessibility:
  - ARIA combobox role with proper expanded state
  - Keyboard navigation (Arrow keys, Enter, Escape)
  - Screen reader announcements for selection changes
  - Focus management between trigger and options
  - Proper labeling and descriptions
  - Support for ARIA live regions
```

#### 2.3.2 Usage Examples

```typescript
// Basic select
<Select
  label="Country"
  options={[
    { value: 'us', label: 'United States' },
    { value: 'ca', label: 'Canada' },
    { value: 'uk', label: 'United Kingdom' }
  ]}
  placeholder="Select country"
/>

// Searchable select
<Select
  label="User"
  options={userOptions}
  searchable
  placeholder="Search and select user..."
  onSearch={handleUserSearch}
/>

// Multiple select
<Select
  label="Skills"
  options={skillOptions}
  multiple
  placeholder="Select skills"
  value={selectedSkills}
  onChange={setSelectedSkills}
/>

// With groups
<Select
  label="Category"
  options={[
    { value: 'design', label: 'Design', group: 'Creative' },
    { value: 'development', label: 'Development', group: 'Technical' },
    { value: 'marketing', label: 'Marketing', group: 'Business' }
  ]}
/>
```

### 2.4 Card Component

#### 2.4.1 Specification

```yaml
Component: Card
Description: Container component for grouping related content
Category: Core
Priority: High

Props:
  - name: variant
    type: 'default' | 'outlined' | 'elevated' | 'interactive'
    required: false
    default: 'default'
    description: Card visual style

  - name: padding
    type: 'none' | 'sm' | 'md' | 'lg'
    required: false
    default: 'md'
    description: Internal padding

  - name: shadow
    type: 'none' | 'sm' | 'md' | 'lg'
    required: false
    default: 'sm'
    description: Shadow depth

  - name: border
    type: boolean
    required: false
    default: false
    description: Show border

  - name: borderRadius
    type: 'none' | 'sm' | 'md' | 'lg'
    required: false
    default: 'md'
    description: Border radius

  - name: clickable
    type: boolean
    required: false
    default: false
    description: Make card clickable

  - name: disabled
    type: boolean
    required: false
    default: false
    description: Disable card interactions

  - name: loading
    type: boolean
    required: false
    default: false
    description: Show loading state

  - name: header
    type: ReactNode
    required: false
    description: Card header content

  - name: footer
    type: ReactNode
    required: false
    description: Card footer content

  - name: actions
    type: ReactNode
    required: false
    description: Card action buttons

  - name: children
    type: ReactNode
    required: false
    description: Card body content

  - name: onClick
    type: (event: MouseEvent) => void
    required: false
    description: Click handler for clickable cards

Variants:
  - default: White background, subtle shadow
  - outlined: White background, border, no shadow
  - elevated: White background, prominent shadow
  - interactive: Hover effects, cursor pointer

States:
  - default: Standard card appearance
  - hover: Enhanced shadow, slight scale (for interactive)
  - active: Pressed state (for interactive)
  - disabled: Reduced opacity, no interactions
  - loading: Skeleton content or spinner

Accessibility:
  - Proper semantic structure (article, section)
  - Keyboard navigation for clickable cards
  - Focus indicators
  - Screen reader friendly content structure
  - ARIA labels for interactive elements
```

#### 2.4.2 Usage Examples

```typescript
// Basic card
<Card>
  <h3>Card Title</h3>
  <p>Card content goes here...</p>
</Card>

// Card with header and footer
<Card
  header={
    <div className="flex justify-between items-center">
      <h3>User Profile</h3>
      <Button variant="ghost" size="sm">Edit</Button>
    </div>
  }
  footer={
    <div className="text-sm text-gray-500">
      Last updated: 2 hours ago
    </div>
  }
>
  <UserProfileContent />
</Card>

// Interactive card
<Card
  variant="interactive"
  clickable
  onClick={() => navigate('/user/123')}
>
  <UserCardContent />
</Card>

// Loading card
<Card loading>
  <CardSkeleton />
</Card>
```

### 2.5 Modal Component

#### 2.5.1 Specification

```yaml
Component: Modal
Description: Overlay dialog for focused user interactions
Category: Feedback
Priority: High

Props:
  - name: open
    type: boolean
    required: true
    description: Modal open state

  - name: onClose
    type: () => void
    required: true
    description: Close handler

  - name: title
    type: string
    required: false
    description: Modal title

  - name: size
    type: 'sm' | 'md' | 'lg' | 'xl' | 'full'
    required: false
    default: 'md'
    description: Modal size

  - name: closeOnOverlayClick
    type: boolean
    required: false
    default: true
    description: Close modal on overlay click

  - name: closeOnEscape
    type: boolean
    required: false
    default: true
    description: Close modal on escape key

  - name: showCloseButton
    type: boolean
    required: false
    default: true
    description: Show close button

  - name: preventScroll
    type: boolean
    required: false
    default: true
    description: Prevent body scroll when open

  - name: children
    type: ReactNode
    required: false
    description: Modal content

  - name: footer
    type: ReactNode
    required: false
    description: Modal footer actions

Sizes:
  - sm: 400px max-width
  - md: 600px max-width
  - lg: 800px max-width
  - xl: 1000px max-width
  - full: Full screen

States:
  - closed: Hidden, no interaction
  - opening: Fade in animation
  - open: Fully visible, interactive
  - closing: Fade out animation

Accessibility:
  - Focus trap within modal
  - Focus restoration on close
  - ARIA dialog role
  - ARIA labeling with title
  - Screen reader announcements
  - Keyboard navigation (Tab, Escape)
  - Proper heading structure

Animation:
  - Backdrop fade in/out (200ms)
  - Modal scale and fade (300ms)
  - Smooth transitions
  - Reduced motion support
```

#### 2.5.2 Usage Examples

```typescript
// Basic modal
<Modal
  open={isOpen}
  onClose={setIsOpen}
  title="Confirm Action"
>
  <p>Are you sure you want to delete this item?</p>
</Modal>

// Modal with footer actions
<Modal
  open={isOpen}
  onClose={setIsOpen}
  title="Edit User"
  size="lg"
  footer={
    <div className="flex gap-2">
      <Button variant="outline" onClick={handleCancel}>
        Cancel
      </Button>
      <Button onClick={handleSave}>
        Save Changes
      </Button>
    </div>
  }
>
  <UserEditForm />
</Modal>

// Full screen modal
<Modal
  open={isOpen}
  onClose={setIsOpen}
  size="full"
  title="Document Viewer"
>
  <DocumentViewer />
</Modal>
```

## 3. Navigation Components

### 3.1 Sidebar Component

#### 3.1.1 Specification

```yaml
Component: Sidebar
Description: Main navigation sidebar with collapsible menu items
Category: Navigation
Priority: High

Props:
  - name: collapsed
    type: boolean
    required: false
    default: false
    description: Sidebar collapsed state

  - name: width
    type: number
    required: false
    default: 240
    description: Sidebar width in pixels

  - name: collapsedWidth
    type: number
    required: false
    default: 60
    description: Collapsed width in pixels

  - name: overlay
    type: boolean
    required: false
    default: false
    description: Show as overlay (mobile)

  - name: items
    type: SidebarItem[]
    required: true
    description: Navigation items

  - name: activeItem
    type: string
    required: false
    description: Active item identifier

  - name: onItemClick
    type: (item: SidebarItem) => void
    required: false
    description: Item click handler

  - name: onToggle
    type: () => void
    required: false
    description: Toggle collapsed state

Types:
  - SidebarItem:
      id: string
      label: string
      icon?: LucideIcon
      path?: string
      children?: SidebarItem[]
      disabled?: boolean
      badge?: string | number

States:
  - expanded: Full width, shows labels and icons
  - collapsed: Minimal width, icons only
  - overlay: Full screen overlay (mobile)
  - hidden: Completely hidden

Accessibility:
  - Proper navigation landmarks
  - Keyboard navigation
  - Screen reader support
  - Focus management
  - ARIA expanded states
  - Skip navigation links
```

#### 3.1.2 Usage Examples

```typescript
// Basic sidebar
<Sidebar
  items={[
    { id: 'dashboard', label: 'Dashboard', icon: Home, path: '/' },
    { id: 'users', label: 'Users', icon: Users, path: '/users' },
    { id: 'settings', label: 'Settings', icon: Settings, path: '/settings' }
  ]}
  activeItem="dashboard"
  onItemClick={handleNavigation}
/>

// Collapsible sidebar
<Sidebar
  collapsed={sidebarCollapsed}
  onToggle={toggleSidebar}
  items={navigationItems}
  activeItem={currentPath}
/>

// Sidebar with nested items
<Sidebar
  items={[
    {
      id: 'dashboard',
      label: 'Dashboard',
      icon: Home,
      path: '/'
    },
    {
      id: 'users',
      label: 'User Management',
      icon: Users,
      children: [
        { id: 'users-list', label: 'All Users', path: '/users' },
        { id: 'users-roles', label: 'Roles', path: '/users/roles' }
      ]
    }
  ]}
/>
```

### 3.2 Breadcrumb Component

#### 3.2.1 Specification

```yaml
Component: Breadcrumb
Description: Navigation path indicator showing current location
Category: Navigation
Priority: Medium

Props:
  - name: items
    type: BreadcrumbItem[]
    required: true
    description: Breadcrumb items

  - name: separator
    type: ReactNode
    required: false
    default: '/'
    description: Separator between items

  - name: maxItems
    type: number
    required: false
    description: Maximum items to show

  - name: showRoot
    type: boolean
    required: false
    default: true
    description: Show root item

  - name: onClick
    type: (item: BreadcrumbItem) => void
    required: false
    description: Item click handler

Types:
  - BreadcrumbItem:
      label: string
      path?: string
      disabled?: boolean
      icon?: LucideIcon

Accessibility:
  - Proper navigation structure
  - ARIA current for active item
  - Screen reader friendly
  - Keyboard navigation
  - Semantic HTML structure
```

#### 3.2.2 Usage Examples

```typescript
// Basic breadcrumb
<Breadcrumb
  items={[
    { label: 'Dashboard', path: '/' },
    { label: 'Users', path: '/users' },
    { label: 'John Doe' }
  ]}
  onClick={handleBreadcrumbClick}
/>

// Breadcrumb with icons
<Breadcrumb
  items={[
    { label: 'Home', path: '/', icon: Home },
    { label: 'Projects', path: '/projects', icon: Folder },
    { label: 'Project Alpha' }
  ]}
  separator={<ChevronRight size={16} />}
/>
```

## 4. Form Components

### 4.1 FormField Component

#### 4.1.1 Specification

```yaml
Component: FormField
Description: Wrapper component for form inputs with label, error, and help text
Category: Forms
Priority: High

Props:
  - name: label
    type: string
    required: false
    description: Field label

  - name: required
    type: boolean
    required: false
    default: false
    description: Required field indicator

  - name: error
    type: string
    required: false
    description: Error message

  - name: helperText
    type: string
    required: false
    description: Helper text

  - name: layout
    type: 'vertical' | 'horizontal'
    required: false
    default: 'vertical'
    description: Label layout

  - name: labelWidth
    type: number
    required: false
    default: 140
    description: Label width for horizontal layout

  - name: children
    type: ReactNode
    required: true
    description: Form input component

Accessibility:
  - Label association with form controls
  - Error message association
  - Helper text association
  - Required field indication
  - Proper ARIA attributes
```

#### 4.1.2 Usage Examples

```typescript
// Basic form field
<FormField label="Email Address" required>
  <Input type="email" />
</FormField>

// Form field with error
<FormField
  label="Password"
  error="Password is required"
  helperText="Must be at least 8 characters"
>
  <Input type="password" />
</FormField>

// Horizontal layout
<FormField
  label="Username"
  layout="horizontal"
  labelWidth={120}
>
  <Input />
</FormField>
```

### 4.2 Checkbox Component

#### 4.2.1 Specification

```yaml
Component: Checkbox
Description: Boolean input for true/false selections
Category: Forms
Priority: High

Props:
  - name: checked
    type: boolean
    required: false
    description: Checked state

  - name: defaultChecked
    type: boolean
    required: false
    description: Default checked state

  - name: indeterminate
    type: boolean
    required: false
    default: false
    description: Indeterminate state

  - name: disabled
    type: boolean
    required: false
    default: false
    description: Disabled state

  - name: label
    type: string
    required: false
    description: Checkbox label

  - name: description
    type: string
    required: false
    description: Additional description

  - name: size
    type: 'sm' | 'md' | 'lg'
    required: false
    default: 'md'
    description: Checkbox size

  - name: color
    type: 'primary' | 'secondary' | 'success' | 'danger'
    required: false
    default: 'primary'
    description: Checkbox color

  - name: onChange
    type: (checked: boolean) => void
    required: false
    description: Change handler

States:
  - unchecked: Empty checkbox
  - checked: Checked with checkmark
  - indeterminate: Partially checked state
  - disabled: Disabled appearance

Accessibility:
  - Proper checkbox role
  - Keyboard navigation
  - Screen reader support
  - Focus indicators
  - Label association
```

#### 4.2.2 Usage Examples

```typescript
// Basic checkbox
<Checkbox
  label="I agree to the terms"
  checked={agreed}
  onChange={setAgreed}
/>

// Checkbox group
<CheckboxGroup
  label="Select options"
  options={[
    { value: 'option1', label: 'Option 1' },
    { value: 'option2', label: 'Option 2' },
    { value: 'option3', label: 'Option 3' }
  ]}
  value={selectedOptions}
  onChange={setSelectedOptions}
/>

// Indeterminate checkbox
<Checkbox
  label="Select all"
  checked={allSelected}
  indeterminate={someSelected}
  onChange={handleSelectAll}
/>
```

## 5. Data Display Components

### 5.1 Table Component

#### 5.1.1 Specification

```yaml
Component: Table
Description: Data table with sorting, pagination, and row selection
Category: Data Display
Priority: High

Props:
  - name: columns
    type: TableColumn[]
    required: true
    description: Table column definitions

  - name: data
    type: any[]
    required: true
    description: Table data

  - name: sortable
    type: boolean
    required: false
    default: false
    description: Enable sorting

  - name: selectable
    type: boolean
    required: false
    default: false
    description: Enable row selection

  - name: pagination
    type: boolean
    required: false
    default: false
    description: Enable pagination

  - name: pageSize
    type: number
    required: false
    default: 10
    description: Items per page

  - name: loading
    type: boolean
    required: false
    default: false
    description: Loading state

  - name: empty
    type: ReactNode
    required: false
    description: Empty state content

  - name: onSort
    type: (column: string, direction: 'asc' | 'desc') => void
    required: false
    description: Sort handler

  - name: onSelect
    type: (selected: any[]) => void
    required: false
    description: Selection handler

Types:
  - TableColumn:
      key: string
      title: string
      sortable?: boolean
      width?: number
      align?: 'left' | 'center' | 'right'
      render?: (value: any, row: any) => ReactNode

Accessibility:
  - Proper table structure
  - Column headers
  - Sort indicators
  - Screen reader support
  - Keyboard navigation
  - Focus management
```

#### 5.1.2 Usage Examples

```typescript
// Basic table
<Table
  columns={[
    { key: 'name', title: 'Name', sortable: true },
    { key: 'email', title: 'Email' },
    { key: 'role', title: 'Role' },
    {
      key: 'actions',
      title: 'Actions',
      render: (_, row) => (
        <Button size="sm" onClick={() => editUser(row.id)}>
          Edit
        </Button>
      )
    }
  ]}
  data={users}
  sortable
  selectable
  pagination
  pageSize={20}
/>

// Table with loading state
<Table
  columns={columns}
  data={data}
  loading={isLoading}
  empty={<EmptyState message="No users found" />}
/>
```

### 5.2 List Component

#### 5.2.1 Specification

```yaml
Component: List
Description: Flexible list component for displaying items
Category: Data Display
Priority: Medium

Props:
  - name: items
    type: any[]
    required: true
    description: List items

  - name: renderItem
    type: (item: any, index: number) => ReactNode
    required: true
    description: Item render function

  - name: keyExtractor
    type: (item: any, index: number) => string
    required: false
    description: Key extraction function

  - name: divided
    type: boolean
    required: false
    default: false
    description: Show dividers between items

  - name: spacing
    type: 'none' | 'sm' | 'md' | 'lg'
    required: false
    default: 'md'
    description: Spacing between items

  - name: loading
    type: boolean
    required: false
    default: false
    description: Loading state

  - name: empty
    type: ReactNode
    required: false
    description: Empty state content

  - name: virtualScroll
    type: boolean
    required: false
    default: false
    description: Enable virtual scrolling

  - name: maxHeight
    type: number
    required: false
    description: Maximum height for scrolling

Accessibility:
  - Proper list structure
  - Keyboard navigation
  - Screen reader support
  - Focus management
  - ARIA labeling
```

#### 5.2.2 Usage Examples

```typescript
// Basic list
<List
  items={users}
  renderItem={(user) => (
    <div className="flex items-center space-x-3">
      <Avatar src={user.avatar} />
      <div>
        <p className="font-medium">{user.name}</p>
        <p className="text-sm text-gray-500">{user.email}</p>
      </div>
    </div>
  )}
  divided
  spacing="md"
/>

// Virtual scrolling list
<List
  items={largeDataset}
  renderItem={renderLargeItem}
  virtualScroll
  maxHeight={400}
  keyExtractor={(item) => item.id}
/>
```

## 6. Implementation Guidelines

### 6.1 TypeScript Requirements

```typescript
// Component props interface
interface ComponentProps extends React.HTMLAttributes<HTMLElement> {
  // Component-specific props
  variant?: 'primary' | 'secondary';
  size?: 'sm' | 'md' | 'lg';
  disabled?: boolean;
  
  // Common props
  className?: string;
  children?: React.ReactNode;
}

// Forward ref pattern
const Component = React.forwardRef<HTMLElement, ComponentProps>(
  ({ variant = 'primary', size = 'md', className, children, ...props }, ref) => {
    return (
      <element
        ref={ref}
        className={cn(componentVariants({ variant, size }), className)}
        {...props}
      >
        {children}
      </element>
    );
  }
);

Component.displayName = 'Component';
```

### 6.2 Styling Standards

```typescript
// Using class-variance-authority for variants
import { cva, type VariantProps } from 'class-variance-authority';

const componentVariants = cva(
  'base-classes',
  {
    variants: {
      variant: {
        primary: 'primary-classes',
        secondary: 'secondary-classes',
      },
      size: {
        sm: 'small-classes',
        md: 'medium-classes',
        lg: 'large-classes',
      },
    },
    defaultVariants: {
      variant: 'primary',
      size: 'md',
    },
  }
);

export type ComponentVariants = VariantProps<typeof componentVariants>;
```

### 6.3 Testing Requirements

```typescript
// Component test template
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { Component } from './Component';

describe('Component', () => {
  it('renders with correct props', () => {
    render(<Component variant="primary" size="lg">Test</Component>);
    
    const component = screen.getByRole('button');
    expect(component).toHaveClass('primary-classes', 'large-classes');
    expect(component).toHaveTextContent('Test');
  });

  it('handles user interactions', async () => {
    const user = userEvent.setup();
    const handleClick = jest.fn();
    
    render(<Component onClick={handleClick}>Click me</Component>);
    
    await user.click(screen.getByRole('button'));
    expect(handleClick).toHaveBeenCalledTimes(1);
  });

  it('is accessible', () => {
    render(<Component aria-label="Test button">Click me</Component>);
    
    const component = screen.getByRole('button');
    expect(component).toHaveAccessibleName('Test button');
  });
});
```

## 7. Component Checklist

### 7.1 Pre-Implementation Checklist
- [ ] Review component specification
- [ ] Understand design requirements
- [ ] Identify accessibility needs
- [ ] Plan component API
- [ ] Consider responsive behavior
- [ ] Plan testing strategy

### 7.2 Implementation Checklist
- [ ] Create component structure
- [ ] Implement variants and states
- [ ] Add accessibility attributes
- [ ] Implement keyboard navigation
- [ ] Add proper TypeScript types
- [ ] Style with design tokens
- [ ] Add responsive behavior
- [ ] Implement animations

### 7.3 Testing Checklist
- [ ] Write unit tests
- [ ] Test all variants and states
- [ ] Test user interactions
- [ ] Test accessibility
- [ ] Test keyboard navigation
- [ ] Test responsive behavior
- [ ] Test error states
- [ ] Visual regression testing

### 7.4 Documentation Checklist
- [ ] Create Storybook stories
- [ ] Document component API
- [ ] Add usage examples
- [ ] Document accessibility features
- [ ] Create migration guide (if applicable)
- [ ] Update design system documentation

---

**Document Status**: ✅ Complete and Ready for Implementation  
**Total Components**: 15 core components with detailed specifications  
**Next Steps**: Begin component implementation following specifications  

---

*This document provides the foundation for implementing all required UI components in the ITDO ERP2 system. Each component specification should be followed precisely to ensure consistency and quality.*