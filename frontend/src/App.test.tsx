import { render, screen } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { MemoryRouter } from 'react-router-dom'
import { vi } from 'vitest'
import { HomePage } from './pages/HomePage'

// Mock API client
vi.mock('./services/api', () => ({
  apiClient: {
    get: vi.fn(() => Promise.resolve({ data: { status: 'healthy' } }))
  }
}))

function renderWithProviders(component: React.ReactElement) {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  })

  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>
        {component}
      </MemoryRouter>
    </QueryClientProvider>
  )
}

describe('HomePage', () => {
  it('renders welcome message', async () => {
    renderWithProviders(<HomePage />)
    expect(await screen.findByText('Welcome to ITDO ERP System')).toBeInTheDocument()
  })

  it('displays modules sections', async () => {
    renderWithProviders(<HomePage />)
    expect(await screen.findByText('Module 1')).toBeInTheDocument()
    expect(await screen.findByText('Module 2')).toBeInTheDocument()
    expect(await screen.findByText('Module 3')).toBeInTheDocument()
  })
})