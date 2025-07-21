import React from 'react'
import { cn } from '../../../lib/utils'

export interface TabItem {
  id: string
  label: string
  content?: React.ReactNode
  icon?: React.ReactNode
  disabled?: boolean
  badge?: string | number
}

export interface TabsProps {
  items: TabItem[]
  activeTab?: string
  defaultTab?: string
  onTabChange?: (tabId: string) => void
  variant?: 'default' | 'pills' | 'underline'
  size?: 'sm' | 'md' | 'lg'
  orientation?: 'horizontal' | 'vertical'
  className?: string
  tabListClassName?: string
  tabPanelClassName?: string
  fullWidth?: boolean
}

interface TabsContextValue {
  activeTab: string
  setActiveTab: (tabId: string) => void
  variant: NonNullable<TabsProps['variant']>
  size: NonNullable<TabsProps['size']>
  orientation: NonNullable<TabsProps['orientation']>
}

const TabsContext = React.createContext<TabsContextValue | null>(null)

const useTabsContext = () => {
  const context = React.useContext(TabsContext)
  if (!context) {
    throw new Error('Tab components must be used within a Tabs component')
  }
  return context
}

// Tab List Component
interface TabListProps {
  children: React.ReactNode
  className?: string
}

const TabList = React.memo<TabListProps>(({ children, className }) => {
  const { orientation } = useTabsContext()
  
  return (
    <div
      role="tablist"
      aria-orientation={orientation}
      className={cn(
        'flex',
        orientation === 'horizontal' ? 'border-b border-gray-200' : 'flex-col border-r border-gray-200 w-48',
        className
      )}
    >
      {children}
    </div>
  )
})

TabList.displayName = 'TabList'

// Tab Component
interface TabProps {
  id: string
  children: React.ReactNode
  disabled?: boolean
  className?: string
}

const Tab = React.memo<TabProps>(({ id, children, disabled = false, className }) => {
  const { activeTab, setActiveTab, variant, size, orientation } = useTabsContext()
  const isActive = activeTab === id

  const handleClick = () => {
    if (!disabled) {
      setActiveTab(id)
    }
  }

  const handleKeyDown = (event: React.KeyboardEvent) => {
    if (disabled) return

    switch (event.key) {
      case 'Enter':
      case ' ':
        event.preventDefault()
        setActiveTab(id)
        break
      case 'ArrowLeft':
      case 'ArrowUp':
        event.preventDefault()
        // Handle previous tab navigation
        break
      case 'ArrowRight':
      case 'ArrowDown':
        event.preventDefault()
        // Handle next tab navigation
        break
    }
  }

  const sizes = {
    sm: 'px-3 py-2 text-sm',
    md: 'px-4 py-2.5 text-sm',
    lg: 'px-6 py-3 text-base',
  }

  const variants = {
    default: {
      base: 'border-b-2 transition-colors duration-200',
      active: 'border-blue-600 text-blue-600',
      inactive: 'border-transparent text-gray-600 hover:text-gray-900 hover:border-gray-300',
      disabled: 'border-transparent text-gray-400 cursor-not-allowed',
    },
    pills: {
      base: 'rounded-md transition-colors duration-200',
      active: 'bg-blue-600 text-white',
      inactive: 'text-gray-600 hover:text-gray-900 hover:bg-gray-100',
      disabled: 'text-gray-400 cursor-not-allowed',
    },
    underline: {
      base: 'border-b-2 transition-colors duration-200 bg-transparent',
      active: 'border-blue-600 text-blue-600 bg-blue-50',
      inactive: 'border-transparent text-gray-600 hover:text-gray-900 hover:bg-gray-50',
      disabled: 'border-transparent text-gray-400 cursor-not-allowed',
    },
  }

  const variantClasses = variants[variant]
  const sizeClasses = sizes[size]

  const buttonClasses = cn(
    'inline-flex items-center justify-center font-medium whitespace-nowrap',
    'focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2',
    sizeClasses,
    variantClasses.base,
    disabled ? variantClasses.disabled : isActive ? variantClasses.active : variantClasses.inactive,
    className
  )

  return (
    <button
      role="tab"
      type="button"
      id={`tab-${id}`}
      aria-controls={`panel-${id}`}
      aria-selected={isActive}
      tabIndex={isActive ? 0 : -1}
      disabled={disabled}
      className={buttonClasses}
      onClick={handleClick}
      onKeyDown={handleKeyDown}
    >
      {children}
    </button>
  )
})

Tab.displayName = 'Tab'

// Tab Panel Component
interface TabPanelProps {
  id: string
  children: React.ReactNode
  className?: string
}

const TabPanel = React.memo<TabPanelProps>(({ id, children, className }) => {
  const { activeTab } = useTabsContext()
  const isActive = activeTab === id

  if (!isActive) return null

  return (
    <div
      role="tabpanel"
      id={`panel-${id}`}
      aria-labelledby={`tab-${id}`}
      className={cn('focus:outline-none', className)}
      tabIndex={0}
    >
      {children}
    </div>
  )
})

TabPanel.displayName = 'TabPanel'

// Main Tabs Component
const Tabs = React.memo<TabsProps>(({
  items,
  activeTab: controlledActiveTab,
  defaultTab,
  onTabChange,
  variant = 'default',
  size = 'md',
  orientation = 'horizontal',
  className,
  tabListClassName,
  tabPanelClassName,
  fullWidth = false,
}) => {
  const [internalActiveTab, setInternalActiveTab] = React.useState(
    defaultTab || items[0]?.id || ''
  )

  const activeTab = controlledActiveTab ?? internalActiveTab
  const isControlled = controlledActiveTab !== undefined

  const setActiveTab = React.useCallback((tabId: string) => {
    if (!isControlled) {
      setInternalActiveTab(tabId)
    }
    onTabChange?.(tabId)
  }, [isControlled, onTabChange])

  const contextValue = React.useMemo((): TabsContextValue => ({
    activeTab,
    setActiveTab,
    variant,
    size,
    orientation,
  }), [activeTab, setActiveTab, variant, size, orientation])

  const containerClasses = cn(
    'w-full',
    orientation === 'horizontal' ? 'space-y-4' : 'flex gap-6',
    className
  )

  const tabListClasses = cn(
    orientation === 'horizontal' && fullWidth && 'grid',
    orientation === 'horizontal' && fullWidth && `grid-cols-${items.length}`,
    tabListClassName
  )

  return (
    <TabsContext.Provider value={contextValue}>
      <div className={containerClasses}>
        <TabList className={tabListClasses}>
          {items.map((item) => (
            <Tab
              key={item.id}
              id={item.id}
              disabled={item.disabled}
              className={fullWidth && orientation === 'horizontal' ? 'flex-1' : undefined}
            >
              <span className="flex items-center gap-2">
                {item.icon && <span aria-hidden="true">{item.icon}</span>}
                <span>{item.label}</span>
                {item.badge && (
                  <span
                    className={cn(
                      'inline-flex items-center justify-center px-2 py-0.5 text-xs font-medium rounded-full',
                      activeTab === item.id
                        ? 'bg-white text-blue-600'
                        : 'bg-gray-100 text-gray-600'
                    )}
                  >
                    {item.badge}
                  </span>
                )}
              </span>
            </Tab>
          ))}
        </TabList>

        <div className={cn('flex-1', tabPanelClassName)}>
          {items.map((item) => (
            <TabPanel key={item.id} id={item.id}>
              {item.content}
            </TabPanel>
          ))}
        </div>
      </div>
    </TabsContext.Provider>
  )
})

Tabs.displayName = 'Tabs'

// Compound component exports
const TabsCompound = Object.assign(Tabs, {
  List: TabList,
  Tab: Tab,
  Panel: TabPanel,
})

export default TabsCompound
export { TabList, Tab, TabPanel }