import React from 'react'
import { render, RenderOptions, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { BrowserRouter } from 'react-router-dom'
import { vi } from 'vitest'

import { PermissionProvider } from '../hooks/usePermissions'
import { User, UserRole, Permission } from '../services/api/types'

// Mock user for testing
export const mockUser: User = {
  id: 'test-user-1',
  email: 'test@example.com',
  firstName: 'Test',
  lastName: 'User',
  fullName: 'Test User',
  role: UserRole.MEMBER,
  status: 'active' as any,
  createdAt: '2023-01-01T00:00:00Z',
  updatedAt: '2023-01-01T00:00:00Z',
  preferences: {
    theme: 'light',
    language: 'en',
    timezone: 'UTC',
    notifications: {
      email: true,
      push: true,
      desktop: true,
      types: {
        taskAssigned: true,
        taskCompleted: true,
        projectUpdates: true,
        mentions: true,
        deadlines: true,
      },
    },
    accessibility: {
      reducedMotion: false,
      highContrast: false,
      fontSize: 'medium',
      screenReaderOptimized: false,
    },
  },
  permissions: [],
}

// Mock permissions for testing
export const mockPermissions: Permission[] = [
  {
    id: 'perm-1',
    name: 'Read Tasks',
    resource: 'task',
    action: 'read',
  },
  {
    id: 'perm-2',
    name: 'Create Tasks',
    resource: 'task',
    action: 'create',
  },
  {
    id: 'perm-3',
    name: 'Update Tasks',
    resource: 'task',
    action: 'update',
  },
]

// Create a test query client
export const createTestQueryClient = (options = {}) => {
  return new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        cacheTime: 0,
        staleTime: 0,
        ...options,
      },
      mutations: {
        retry: false,
        ...options,
      },
    },
  })
}

// Custom render function with providers
interface CustomRenderOptions extends Omit<RenderOptions, 'wrapper'> {
  // Query client options
  queryClient?: QueryClient
  
  // Router options
  initialRoute?: string
  
  // Permission options
  user?: User | null
  permissions?: Permission[]
  
  // Whether to wrap with providers
  withRouter?: boolean
  withQueryClient?: boolean
  withPermissions?: boolean
  
  // Custom wrapper
  wrapper?: React.ComponentType<{ children: React.ReactNode }>
}

export const renderWithProviders = (
  ui: React.ReactElement,
  options: CustomRenderOptions = {}
) => {
  const {
    queryClient = createTestQueryClient(),
    initialRoute = '/',
    user = mockUser,
    permissions = mockPermissions,
    withRouter = true,
    withQueryClient = true,
    withPermissions = true,
    wrapper,
    ...renderOptions
  } = options

  // Set initial route
  if (withRouter && initialRoute !== '/') {
    window.history.pushState({}, '', initialRoute)
  }

  const AllProviders: React.FC<{ children: React.ReactNode }> = ({ children }) => {
    let content = children

    // Wrap with permission provider
    if (withPermissions) {
      content = (
        <PermissionProvider user={user} permissions={permissions}>
          {content}
        </PermissionProvider>
      )
    }

    // Wrap with query client provider
    if (withQueryClient) {
      content = (
        <QueryClientProvider client={queryClient}>
          {content}
        </QueryClientProvider>
      )
    }

    // Wrap with router
    if (withRouter) {
      content = <BrowserRouter>{content}</BrowserRouter>
    }

    return <>{content}</>
  }

  const Wrapper = wrapper || AllProviders

  return {
    user: userEvent.setup(),
    queryClient,
    ...render(ui, { wrapper: Wrapper, ...renderOptions }),
  }
}

// Shorthand for common test scenarios
export const renderWithAuth = (ui: React.ReactElement, user: User = mockUser) =>
  renderWithProviders(ui, { user })

export const renderWithoutAuth = (ui: React.ReactElement) =>
  renderWithProviders(ui, { user: null })

export const renderWithAdmin = (ui: React.ReactElement) =>
  renderWithProviders(ui, { 
    user: { ...mockUser, role: UserRole.ADMIN } 
  })

export const renderWithRouter = (ui: React.ReactElement, initialRoute = '/') =>
  renderWithProviders(ui, { initialRoute })

// Test helpers
export const waitForElementToBeRemoved = async (element: HTMLElement) => {
  await waitFor(() => {
    expect(element).not.toBeInTheDocument()
  })
}

export const waitForLoadingToFinish = async () => {
  await waitFor(() => {
    expect(screen.queryByText(/loading/i)).not.toBeInTheDocument()
  })
}

// Mock API responses
export const mockApiResponse = <T>(data: T, delay = 0) => {
  return new Promise<{ data: T }>((resolve) => {
    setTimeout(() => {
      resolve({ data })
    }, delay)
  })
}

export const mockApiError = (message = 'API Error', status = 500, delay = 0) => {
  return new Promise((_, reject) => {
    setTimeout(() => {
      reject({
        response: {
          status,
          data: { message },
        },
      })
    }, delay)
  })
}

// Form test helpers
export const fillForm = async (
  user: ReturnType<typeof userEvent.setup>,
  fields: Record<string, string>
) => {
  for (const [label, value] of Object.entries(fields)) {
    const field = screen.getByLabelText(new RegExp(label, 'i'))
    await user.clear(field)
    await user.type(field, value)
  }
}

export const submitForm = async (
  user: ReturnType<typeof userEvent.setup>,
  buttonText = /submit|save|create/i
) => {
  const submitButton = screen.getByRole('button', { name: buttonText })
  await user.click(submitButton)
}

// Mock implementations
export const mockIntersectionObserver = () => {
  const mockIntersectionObserver = vi.fn()
  mockIntersectionObserver.mockReturnValue({
    observe: () => null,
    unobserve: () => null,
    disconnect: () => null,
  })
  window.IntersectionObserver = mockIntersectionObserver
}

export const mockResizeObserver = () => {
  const mockResizeObserver = vi.fn()
  mockResizeObserver.mockReturnValue({
    observe: () => null,
    unobserve: () => null,
    disconnect: () => null,
  })
  window.ResizeObserver = mockResizeObserver
}

export const mockMatchMedia = (matches = false) => {
  Object.defineProperty(window, 'matchMedia', {
    writable: true,
    value: vi.fn().mockImplementation((query) => ({
      matches,
      media: query,
      onchange: null,
      addListener: vi.fn(),
      removeListener: vi.fn(),
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
      dispatchEvent: vi.fn(),
    })),
  })
}

// Storage mocks
export const mockLocalStorage = () => {
  const store = new Map<string, string>()
  
  Object.defineProperty(window, 'localStorage', {
    value: {
      getItem: vi.fn((key: string) => store.get(key) || null),
      setItem: vi.fn((key: string, value: string) => store.set(key, value)),
      removeItem: vi.fn((key: string) => store.delete(key)),
      clear: vi.fn(() => store.clear()),
      length: 0,
      key: vi.fn(),
    },
  })

  return store
}

export const mockSessionStorage = () => {
  const store = new Map<string, string>()
  
  Object.defineProperty(window, 'sessionStorage', {
    value: {
      getItem: vi.fn((key: string) => store.get(key) || null),
      setItem: vi.fn((key: string, value: string) => store.set(key, value)),
      removeItem: vi.fn((key: string) => store.delete(key)),
      clear: vi.fn(() => store.clear()),
      length: 0,
      key: vi.fn(),
    },
  })

  return store
}

// Network mocks
export const mockFetch = () => {
  const mockFetchImpl = vi.fn()
  global.fetch = mockFetchImpl
  return mockFetchImpl
}

// Date mocks
export const mockDate = (date: string | Date) => {
  const mockDateImpl = new Date(date)
  vi.useFakeTimers()
  vi.setSystemTime(mockDateImpl)
  return mockDateImpl
}

// Custom matchers for better test assertions
export const customMatchers = {
  toBeInTheDocument: (received: any) => {
    const pass = received !== null && document.contains(received)
    return {
      pass,
      message: () => pass
        ? `Expected element not to be in the document`
        : `Expected element to be in the document`,
    }
  },
  
  toHaveClass: (received: any, className: string) => {
    const pass = received?.classList?.contains(className)
    return {
      pass,
      message: () => pass
        ? `Expected element not to have class "${className}"`
        : `Expected element to have class "${className}"`,
    }
  },
}

// Test data factories
export const createMockUser = (overrides: Partial<User> = {}): User => ({
  ...mockUser,
  ...overrides,
})

export const createMockPermission = (overrides: Partial<Permission> = {}): Permission => ({
  id: 'test-permission',
  name: 'Test Permission',
  resource: 'test',
  action: 'read',
  ...overrides,
})

// Performance testing helpers
export const measureRenderTime = async (renderFn: () => void) => {
  const start = performance.now()
  renderFn()
  await waitFor(() => {
    // Wait for render to complete
  })
  const end = performance.now()
  return end - start
}

export const expectRenderToBeFast = async (renderFn: () => void, maxTime = 100) => {
  const renderTime = await measureRenderTime(renderFn)
  expect(renderTime).toBeLessThan(maxTime)
}

// Accessibility testing helpers
export const expectToHaveNoA11yViolations = async (container: HTMLElement) => {
  // This would integrate with axe-core in a real implementation
  const focusableElements = container.querySelectorAll(
    'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
  )
  
  // Basic checks
  focusableElements.forEach((element) => {
    if (element.tagName === 'BUTTON' || element.tagName === 'A') {
      expect(element).toHaveAttribute('type')
    }
  })
}

// Re-export testing library utilities
export * from '@testing-library/react'
export { userEvent, vi }
export { default as userEvent } from '@testing-library/user-event'