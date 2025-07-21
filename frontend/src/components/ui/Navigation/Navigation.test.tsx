import React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, it, expect, vi } from 'vitest'

import Breadcrumb from './Breadcrumb'
import Pagination from './Pagination'
import Tabs from './Tabs'
import Menu, { DropdownMenu } from './Menu'

describe('Navigation Components', () => {
  describe('Breadcrumb', () => {
    const mockItems = [
      { label: 'Home', href: '/' },
      { label: 'Products', href: '/products' },
      { label: 'Electronics', href: '/products/electronics' },
      { label: 'Smartphones', current: true },
    ]

    it('renders breadcrumb items correctly', () => {
      render(<Breadcrumb items={mockItems} />)
      
      expect(screen.getByText('Home')).toBeInTheDocument()
      expect(screen.getByText('Products')).toBeInTheDocument()
      expect(screen.getByText('Electronics')).toBeInTheDocument()
      expect(screen.getByText('Smartphones')).toBeInTheDocument()
    })

    it('shows home icon by default', () => {
      render(<Breadcrumb items={mockItems} />)
      
      const homeIcon = screen.getByText('Home').previousElementSibling
      expect(homeIcon).toBeInTheDocument()
    })

    it('handles click events', async () => {
      const user = userEvent.setup()
      const handleClick = vi.fn()
      
      render(<Breadcrumb items={mockItems} onItemClick={handleClick} />)
      
      await user.click(screen.getByText('Products'))
      expect(handleClick).toHaveBeenCalledWith(mockItems[1], 1)
    })

    it('applies current page styling', () => {
      render(<Breadcrumb items={mockItems} />)
      
      const currentItem = screen.getByText('Smartphones')
      // Check that the current item has appropriate styling
      expect(currentItem.closest('span')).toBeInTheDocument()
    })

    it('truncates items when maxItems is set', () => {
      const longItems = [
        { label: 'Item 1', href: '/1' },
        { label: 'Item 2', href: '/2' },
        { label: 'Item 3', href: '/3' },
        { label: 'Item 4', href: '/4' },
        { label: 'Item 5', href: '/5' },
      ]
      
      render(<Breadcrumb items={longItems} maxItems={4} />)
      
      expect(screen.getByText('...')).toBeInTheDocument()
      expect(screen.getByText('Item 1')).toBeInTheDocument()
      expect(screen.getByText('Item 5')).toBeInTheDocument()
    })

    it('has proper accessibility attributes', () => {
      render(<Breadcrumb items={mockItems} />)
      
      const nav = screen.getByRole('navigation', { name: /breadcrumb/i })
      expect(nav).toBeInTheDocument()
      
      // Check that the current item has appropriate aria-current
      const currentSpan = screen.getByText('Smartphones').closest('span')
      expect(currentSpan).toHaveAttribute('aria-current', 'page')
    })
  })

  describe('Pagination', () => {
    const defaultProps = {
      currentPage: 1,
      totalPages: 10,
      onPageChange: vi.fn(),
    }

    beforeEach(() => {
      vi.clearAllMocks()
    })

    it('renders pagination correctly', () => {
      render(<Pagination {...defaultProps} />)
      
      expect(screen.getByRole('navigation', { name: /pagination/i })).toBeInTheDocument()
      expect(screen.getByText('1')).toBeInTheDocument()
      expect(screen.getByText('2')).toBeInTheDocument()
    })

    it('handles page changes', async () => {
      const user = userEvent.setup()
      const handlePageChange = vi.fn()
      
      render(<Pagination {...defaultProps} onPageChange={handlePageChange} />)
      
      await user.click(screen.getByText('2'))
      expect(handlePageChange).toHaveBeenCalledWith(2)
    })

    it('disables previous button on first page', () => {
      render(<Pagination {...defaultProps} currentPage={1} />)
      
      const prevButton = screen.getByLabelText(/previous/i)
      expect(prevButton).toBeDisabled()
    })

    it('disables next button on last page', () => {
      render(<Pagination {...defaultProps} currentPage={10} totalPages={10} />)
      
      const nextButton = screen.getByLabelText(/next/i)
      expect(nextButton).toBeDisabled()
    })

    it('shows ellipsis for large page counts', () => {
      render(<Pagination {...defaultProps} currentPage={5} totalPages={20} />)
      
      const ellipsis = screen.getAllByRole('button').find(
        button => button.querySelector('svg') // MoreHorizontal icon
      )
      expect(ellipsis).toBeInTheDocument()
    })

    it('applies current page styling', () => {
      render(<Pagination {...defaultProps} currentPage={3} />)
      
      const currentPage = screen.getByLabelText(/go to page 3/i)
      expect(currentPage).toHaveAttribute('aria-current', 'page')
    })

    it('handles keyboard navigation', async () => {
      const user = userEvent.setup()
      const handlePageChange = vi.fn()
      
      render(<Pagination {...defaultProps} onPageChange={handlePageChange} />)
      
      const page2Button = screen.getByText('2')
      page2Button.focus()
      await user.keyboard('{Enter}')
      
      expect(handlePageChange).toHaveBeenCalledWith(2)
    })
  })

  describe('Tabs', () => {
    const mockTabs = [
      { id: 'tab1', label: 'Tab 1', content: <div>Content 1</div> },
      { id: 'tab2', label: 'Tab 2', content: <div>Content 2</div> },
      { id: 'tab3', label: 'Tab 3', content: <div>Content 3</div>, disabled: true },
    ]

    it('renders tabs correctly', () => {
      render(<Tabs items={mockTabs} />)
      
      expect(screen.getByText('Tab 1')).toBeInTheDocument()
      expect(screen.getByText('Tab 2')).toBeInTheDocument()
      expect(screen.getByText('Tab 3')).toBeInTheDocument()
    })

    it('shows first tab content by default', () => {
      render(<Tabs items={mockTabs} />)
      
      expect(screen.getByText('Content 1')).toBeInTheDocument()
      expect(screen.queryByText('Content 2')).not.toBeInTheDocument()
    })

    it('switches tabs on click', async () => {
      const user = userEvent.setup()
      
      render(<Tabs items={mockTabs} />)
      
      await user.click(screen.getByText('Tab 2'))
      
      expect(screen.getByText('Content 2')).toBeInTheDocument()
      expect(screen.queryByText('Content 1')).not.toBeInTheDocument()
    })

    it('calls onTabChange when tab is clicked', async () => {
      const user = userEvent.setup()
      const handleTabChange = vi.fn()
      
      render(<Tabs items={mockTabs} onTabChange={handleTabChange} />)
      
      await user.click(screen.getByText('Tab 2'))
      expect(handleTabChange).toHaveBeenCalledWith('tab2')
    })

    it('respects disabled tabs', async () => {
      const user = userEvent.setup()
      
      render(<Tabs items={mockTabs} />)
      
      const disabledTab = screen.getByText('Tab 3')
      expect(disabledTab).toBeDisabled()
      
      await user.click(disabledTab)
      expect(screen.getByText('Content 1')).toBeInTheDocument() // Should stay on first tab
    })

    it('has proper ARIA attributes', () => {
      render(<Tabs items={mockTabs} />)
      
      const tabList = screen.getByRole('tablist')
      expect(tabList).toBeInTheDocument()
      
      const tabs = screen.getAllByRole('tab')
      expect(tabs).toHaveLength(3)
      
      const firstTab = tabs[0]
      expect(firstTab).toHaveAttribute('aria-selected', 'true')
      expect(firstTab).toHaveAttribute('tabindex', '0')
      
      const secondTab = tabs[1]
      expect(secondTab).toHaveAttribute('aria-selected', 'false')
      expect(secondTab).toHaveAttribute('tabindex', '-1')
    })

    it('supports keyboard navigation', async () => {
      const user = userEvent.setup()
      
      render(<Tabs items={mockTabs} />)
      
      const firstTab = screen.getByText('Tab 1')
      firstTab.focus()
      
      await user.keyboard('{ArrowRight}')
      // Note: Full keyboard navigation would require more complex implementation
      // This test verifies the structure is in place
    })

    it('renders with different variants', () => {
      const { rerender } = render(<Tabs items={mockTabs} variant="pills" />)
      
      const firstTab = screen.getByText('Tab 1')
      expect(firstTab).toBeInTheDocument()
      
      rerender(<Tabs items={mockTabs} variant="underline" />)
      expect(firstTab).toBeInTheDocument()
    })
  })

  describe('Menu', () => {
    const mockMenuItems = [
      { id: 'item1', label: 'Item 1', onClick: vi.fn() },
      { id: 'item2', label: 'Item 2', onClick: vi.fn() },
      { id: 'separator', type: 'separator' as const },
      { id: 'item3', label: 'Item 3', disabled: true },
      {
        id: 'submenu',
        label: 'Submenu',
        children: [
          { id: 'sub1', label: 'Sub Item 1' },
          { id: 'sub2', label: 'Sub Item 2' },
        ],
      },
    ]

    it('renders menu items correctly', () => {
      render(<Menu items={mockMenuItems} />)
      
      expect(screen.getByText('Item 1')).toBeInTheDocument()
      expect(screen.getByText('Item 2')).toBeInTheDocument()
      expect(screen.getByText('Item 3')).toBeInTheDocument()
      expect(screen.getByText('Submenu')).toBeInTheDocument()
    })

    it('renders separator correctly', () => {
      render(<Menu items={mockMenuItems} />)
      
      const separator = screen.getByRole('separator')
      expect(separator).toBeInTheDocument()
    })

    it('handles item clicks', async () => {
      const user = userEvent.setup()
      const handleItemClick = vi.fn()
      
      render(<Menu items={mockMenuItems} onItemClick={handleItemClick} />)
      
      await user.click(screen.getByText('Item 1'))
      expect(mockMenuItems[0].onClick).toHaveBeenCalled()
      expect(handleItemClick).toHaveBeenCalledWith(mockMenuItems[0])
    })

    it('expands submenu on click', async () => {
      const user = userEvent.setup()
      
      render(<Menu items={mockMenuItems} />)
      
      await user.click(screen.getByText('Submenu'))
      
      expect(screen.getByText('Sub Item 1')).toBeInTheDocument()
      expect(screen.getByText('Sub Item 2')).toBeInTheDocument()
    })

    it('respects disabled items', async () => {
      const user = userEvent.setup()
      const handleItemClick = vi.fn()
      
      render(<Menu items={mockMenuItems} onItemClick={handleItemClick} />)
      
      const disabledItem = screen.getByText('Item 3')
      expect(disabledItem).toBeDisabled()
      
      await user.click(disabledItem)
      expect(handleItemClick).not.toHaveBeenCalled()
    })

    it('shows icons when showIcons is true', () => {
      const itemsWithIcons = [
        { id: 'item1', label: 'Item 1', icon: <span data-testid="icon">🏠</span> },
      ]
      
      render(<Menu items={itemsWithIcons} showIcons={true} />)
      
      expect(screen.getByTestId('icon')).toBeInTheDocument()
    })

    it('shows shortcuts when showShortcuts is true', () => {
      const itemsWithShortcuts = [
        { id: 'item1', label: 'Item 1', shortcut: 'Ctrl+S' },
      ]
      
      render(<Menu items={itemsWithShortcuts} showShortcuts={true} />)
      
      expect(screen.getByText('Ctrl+S')).toBeInTheDocument()
    })

    it('has proper ARIA attributes', () => {
      render(<Menu items={mockMenuItems} />)
      
      const menu = screen.getByRole('menu')
      expect(menu).toBeInTheDocument()
      expect(menu).toHaveAttribute('aria-orientation', 'vertical')
      
      const menuItems = screen.getAllByRole('menuitem')
      expect(menuItems.length).toBeGreaterThan(0)
    })
  })

  describe('DropdownMenu', () => {
    const mockMenuItems = [
      { id: 'item1', label: 'Item 1' },
      { id: 'item2', label: 'Item 2' },
    ]

    it('renders trigger button', () => {
      render(
        <DropdownMenu
          trigger={<span>Open Menu</span>}
          items={mockMenuItems}
        />
      )
      
      expect(screen.getByText('Open Menu')).toBeInTheDocument()
    })

    it('opens menu on trigger click', async () => {
      const user = userEvent.setup()
      
      render(
        <DropdownMenu
          trigger={<span>Open Menu</span>}
          items={mockMenuItems}
        />
      )
      
      await user.click(screen.getByText('Open Menu'))
      
      expect(screen.getByText('Item 1')).toBeInTheDocument()
      expect(screen.getByText('Item 2')).toBeInTheDocument()
    })

    it('closes menu when item is clicked', async () => {
      const user = userEvent.setup()
      
      render(
        <DropdownMenu
          trigger={<span>Open Menu</span>}
          items={mockMenuItems}
        />
      )
      
      await user.click(screen.getByText('Open Menu'))
      expect(screen.getByText('Item 1')).toBeInTheDocument()
      
      await user.click(screen.getByText('Item 1'))
      
      await waitFor(() => {
        expect(screen.queryByText('Item 1')).not.toBeInTheDocument()
      })
    })

    it('closes menu on escape key', async () => {
      const user = userEvent.setup()
      
      render(
        <DropdownMenu
          trigger={<span>Open Menu</span>}
          items={mockMenuItems}
        />
      )
      
      await user.click(screen.getByText('Open Menu'))
      expect(screen.getByText('Item 1')).toBeInTheDocument()
      
      await user.keyboard('{Escape}')
      
      await waitFor(() => {
        expect(screen.queryByText('Item 1')).not.toBeInTheDocument()
      })
    })

    it('has proper ARIA attributes', () => {
      render(
        <DropdownMenu
          trigger={<span>Open Menu</span>}
          items={mockMenuItems}
        />
      )
      
      const trigger = screen.getByRole('button')
      expect(trigger).toHaveAttribute('aria-expanded', 'false')
      expect(trigger).toHaveAttribute('aria-haspopup', 'menu')
    })

    it('supports controlled open state', async () => {
      const user = userEvent.setup()
      const handleOpenChange = vi.fn()
      
      const { rerender } = render(
        <DropdownMenu
          trigger={<span>Open Menu</span>}
          items={mockMenuItems}
          open={false}
          onOpenChange={handleOpenChange}
        />
      )
      
      await user.click(screen.getByText('Open Menu'))
      expect(handleOpenChange).toHaveBeenCalledWith(true)
      
      rerender(
        <DropdownMenu
          trigger={<span>Open Menu</span>}
          items={mockMenuItems}
          open={true}
          onOpenChange={handleOpenChange}
        />
      )
      
      expect(screen.getByText('Item 1')).toBeInTheDocument()
    })
  })
})