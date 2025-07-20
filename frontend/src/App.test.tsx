import { render, screen, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { MemoryRouter } from 'react-router-dom'
import { vi } from 'vitest'
import type { AxiosResponse } from 'axios'
import { HomePage } from './pages/HomePage'

// Mock API client with hoisted declaration
const mockApiClient = vi.hoisted(() => ({
  get: vi.fn<[string], Promise<AxiosResponse<{ status: string }>>>(() => 
    Promise.resolve({ data: { status: 'healthy' } } as AxiosResponse<{ status: string }>)
  )
}))

vi.mock('@/services/api', () => ({
  apiClient: mockApiClient
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
  beforeEach(() => {
    // Reset to default successful response
    mockApiClient.get.mockResolvedValue({ data: { status: 'healthy' } } as AxiosResponse<{ status: string }>)
  })

  it('renders welcome message', async () => {
    renderWithProviders(<HomePage />)
    await waitFor(() => {
      expect(screen.getByText('Welcome to ITDO ERP System')).toBeInTheDocument()
    })
  })

  it('displays modules sections', async () => {
    renderWithProviders(<HomePage />)
    await waitFor(() => {
      expect(screen.getByText('Module 1')).toBeInTheDocument()
      expect(screen.getByText('Module 2')).toBeInTheDocument()
      expect(screen.getByText('Module 3')).toBeInTheDocument()
    })
  })

  it('shows loading state', () => {
    // Reset mock and make it never resolve
    mockApiClient.get.mockImplementation(() => new Promise<AxiosResponse<{ status: string }>>(() => {}))
    
    renderWithProviders(<HomePage />)
    expect(screen.getByText('Connecting to backend...')).toBeInTheDocument()
  })

  it('shows error state when API fails', async () => {
    // Reset mock and make it reject
    mockApiClient.get.mockRejectedValue(new Error('API Error'))
    
    renderWithProviders(<HomePage />)
    await waitFor(() => {
      expect(screen.getByText('Connection Error')).toBeInTheDocument()
      expect(screen.getByText('Error connecting to backend')).toBeInTheDocument()
    })
  })
})