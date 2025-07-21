import React from 'react'
import { ChevronDown, ChevronRight, Check } from 'lucide-react'
import { cn } from '../../../lib/utils'

export interface MenuItem {
  id: string
  label: string
  icon?: React.ReactNode
  disabled?: boolean
  type?: 'item' | 'separator' | 'header'
  children?: MenuItem[]
  onClick?: () => void
  href?: string
  target?: string
  shortcut?: string
  selected?: boolean
  description?: string
}

export interface MenuProps {
  items: MenuItem[]
  onItemClick?: (item: MenuItem) => void
  className?: string
  size?: 'sm' | 'md' | 'lg'
  variant?: 'default' | 'minimal' | 'bordered'
  showIcons?: boolean
  showShortcuts?: boolean
  maxHeight?: string
}

interface MenuContextValue {
  onItemClick?: (item: MenuItem) => void
  size: NonNullable<MenuProps['size']>
  variant: NonNullable<MenuProps['variant']>
  showIcons: boolean
  showShortcuts: boolean
}

const MenuContext = React.createContext<MenuContextValue | null>(null)

const useMenuContext = () => {
  const context = React.useContext(MenuContext)
  if (!context) {
    throw new Error('Menu components must be used within a Menu component')
  }
  return context
}

// Sub Menu Component
interface SubMenuProps {
  item: MenuItem
  level?: number
}

const SubMenu = React.memo<SubMenuProps>(({ item, level = 0 }) => {
  const [isOpen, setIsOpen] = React.useState(false)
  const { onItemClick, size, variant, showIcons, showShortcuts } = useMenuContext()
  const hasChildren = item.children && item.children.length > 0

  const toggleOpen = () => {
    if (hasChildren) {
      setIsOpen(!isOpen)
    }
  }

  const handleItemClick = (e: React.MouseEvent) => {
    if (item.disabled) {
      e.preventDefault()
      return
    }

    if (hasChildren) {
      e.preventDefault()
      toggleOpen()
    } else {
      if (item.onClick) {
        e.preventDefault()
        item.onClick()
      }
      onItemClick?.(item)
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (item.disabled) return

    switch (e.key) {
      case 'Enter':
      case ' ':
        e.preventDefault()
        handleItemClick(e as any)
        break
      case 'ArrowRight':
        if (hasChildren && !isOpen) {
          e.preventDefault()
          setIsOpen(true)
        }
        break
      case 'ArrowLeft':
        if (hasChildren && isOpen) {
          e.preventDefault()
          setIsOpen(false)
        }
        break
      case 'Escape':
        if (isOpen) {
          e.preventDefault()
          setIsOpen(false)
        }
        break
    }
  }

  const sizes = {
    sm: 'px-3 py-1.5 text-sm',
    md: 'px-4 py-2 text-sm',
    lg: 'px-6 py-3 text-base',
  }

  const variants = {
    default: {
      item: 'hover:bg-gray-100 text-gray-700',
      selected: 'bg-blue-50 text-blue-700',
      disabled: 'text-gray-400 cursor-not-allowed',
    },
    minimal: {
      item: 'hover:bg-gray-50 text-gray-700',
      selected: 'bg-blue-50 text-blue-700',
      disabled: 'text-gray-400 cursor-not-allowed',
    },
    bordered: {
      item: 'hover:bg-gray-100 text-gray-700 border-l-2 border-transparent hover:border-gray-300',
      selected: 'bg-blue-50 text-blue-700 border-l-2 border-blue-500',
      disabled: 'text-gray-400 cursor-not-allowed border-l-2 border-transparent',
    },
  }

  const sizeClasses = sizes[size]
  const variantClasses = variants[variant]

  const itemClasses = cn(
    'flex items-center justify-between w-full transition-colors duration-150',
    'focus:outline-none focus:bg-gray-100',
    sizeClasses,
    item.disabled
      ? variantClasses.disabled
      : item.selected
      ? variantClasses.selected
      : variantClasses.item,
    level > 0 && 'pl-8'
  )

  if (item.type === 'separator') {
    return <div className="my-1 border-t border-gray-200" role="separator" />
  }

  if (item.type === 'header') {
    return (
      <div className={cn('px-4 py-2 text-xs font-semibold text-gray-500 uppercase tracking-wider')}>
        {item.label}
      </div>
    )
  }

  const ItemContent = (
    <>
      <div className="flex items-center gap-3 flex-1 min-w-0">
        {showIcons && (
          <div className="flex-shrink-0 w-4 h-4 flex items-center justify-center">
            {item.selected && !item.icon ? (
              <Check className="h-4 w-4" />
            ) : (
              item.icon && <span aria-hidden="true">{item.icon}</span>
            )}
          </div>
        )}
        <div className="flex-1 min-w-0">
          <div className="truncate">{item.label}</div>
          {item.description && (
            <div className="text-xs text-gray-500 truncate">{item.description}</div>
          )}
        </div>
      </div>

      <div className="flex items-center gap-2 flex-shrink-0">
        {showShortcuts && item.shortcut && (
          <span className="text-xs text-gray-400 font-mono">{item.shortcut}</span>
        )}
        {hasChildren && (
          <ChevronRight
            className={cn(
              'h-4 w-4 text-gray-400 transition-transform',
              isOpen && 'rotate-90'
            )}
          />
        )}
      </div>
    </>
  )

  const commonProps = {
    className: itemClasses,
    onClick: handleItemClick,
    onKeyDown: handleKeyDown,
    'aria-expanded': hasChildren ? isOpen : undefined,
    'aria-haspopup': hasChildren ? 'menu' : undefined,
    disabled: item.disabled,
  }

  return (
    <>
      {item.href && !item.disabled ? (
        <a
          href={item.href}
          target={item.target}
          role="menuitem"
          {...commonProps}
          tabIndex={0}
        >
          {ItemContent}
        </a>
      ) : (
        <button
          type="button"
          role="menuitem"
          {...commonProps}
          tabIndex={0}
        >
          {ItemContent}
        </button>
      )}

      {hasChildren && isOpen && (
        <div
          role="menu"
          className={cn('bg-white', level === 0 && 'border-l border-gray-200 ml-4')}
        >
          {item.children!.map((childItem) => (
            <SubMenu
              key={childItem.id}
              item={childItem}
              level={level + 1}
            />
          ))}
        </div>
      )}
    </>
  )
})

SubMenu.displayName = 'SubMenu'

// Main Menu Component
const Menu = React.memo<MenuProps>(({
  items,
  onItemClick,
  className,
  size = 'md',
  variant = 'default',
  showIcons = true,
  showShortcuts = true,
  maxHeight,
}) => {
  const contextValue = React.useMemo((): MenuContextValue => ({
    onItemClick,
    size,
    variant,
    showIcons,
    showShortcuts,
  }), [onItemClick, size, variant, showIcons, showShortcuts])

  const menuClasses = cn(
    'bg-white rounded-md shadow-lg border border-gray-200 py-1',
    'focus:outline-none',
    variant === 'minimal' && 'shadow-sm border-gray-100',
    variant === 'bordered' && 'border-2',
    className
  )

  const containerStyle = maxHeight ? { maxHeight, overflowY: 'auto' as const } : undefined

  return (
    <MenuContext.Provider value={contextValue}>
      <div
        role="menu"
        className={menuClasses}
        style={containerStyle}
        aria-orientation="vertical"
      >
        {items.map((item) => (
          <SubMenu key={item.id} item={item} />
        ))}
      </div>
    </MenuContext.Provider>
  )
})

Menu.displayName = 'Menu'

// Dropdown Menu Component (Menu with trigger)
interface DropdownMenuProps extends MenuProps {
  trigger: React.ReactNode
  open?: boolean
  onOpenChange?: (open: boolean) => void
  placement?: 'bottom-start' | 'bottom-end' | 'top-start' | 'top-end'
  triggerClassName?: string
}

const DropdownMenu = React.memo<DropdownMenuProps>(({
  trigger,
  open: controlledOpen,
  onOpenChange,
  placement = 'bottom-start',
  triggerClassName,
  ...menuProps
}) => {
  const [internalOpen, setInternalOpen] = React.useState(false)
  const isControlled = controlledOpen !== undefined
  const isOpen = isControlled ? controlledOpen : internalOpen

  const dropdownRef = React.useRef<HTMLDivElement>(null)
  const triggerRef = React.useRef<HTMLButtonElement>(null)

  const setOpen = React.useCallback((open: boolean) => {
    if (!isControlled) {
      setInternalOpen(open)
    }
    onOpenChange?.(open)
  }, [isControlled, onOpenChange])

  const handleTriggerClick = () => {
    setOpen(!isOpen)
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    switch (e.key) {
      case 'Escape':
        e.preventDefault()
        setOpen(false)
        triggerRef.current?.focus()
        break
      case 'ArrowDown':
        if (!isOpen) {
          e.preventDefault()
          setOpen(true)
        }
        break
    }
  }

  // Close menu when clicking outside
  React.useEffect(() => {
    if (!isOpen) return

    const handleClickOutside = (event: MouseEvent) => {
      if (
        dropdownRef.current &&
        !dropdownRef.current.contains(event.target as Node)
      ) {
        setOpen(false)
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [isOpen, setOpen])

  const placementClasses = {
    'bottom-start': 'top-full left-0 mt-1',
    'bottom-end': 'top-full right-0 mt-1',
    'top-start': 'bottom-full left-0 mb-1',
    'top-end': 'bottom-full right-0 mb-1',
  }

  return (
    <div ref={dropdownRef} className="relative inline-block">
      <button
        ref={triggerRef}
        type="button"
        className={cn(
          'inline-flex items-center gap-2',
          'focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2',
          triggerClassName
        )}
        onClick={handleTriggerClick}
        onKeyDown={handleKeyDown}
        aria-expanded={isOpen}
        aria-haspopup="menu"
      >
        {trigger}
        <ChevronDown className="h-4 w-4" />
      </button>

      {isOpen && (
        <div
          className={cn(
            'absolute z-50 min-w-48',
            placementClasses[placement]
          )}
        >
          <Menu
            {...menuProps}
            onItemClick={(item) => {
              menuProps.onItemClick?.(item)
              setOpen(false)
            }}
          />
        </div>
      )}
    </div>
  )
})

DropdownMenu.displayName = 'DropdownMenu'

export default Menu
export { DropdownMenu }