import { useQuery } from '@tanstack/react-query'
import { apiClient } from '@/services/api'

export function HomePage() {
  const { data, isLoading, error } = useQuery(
    'health-check',
    () => apiClient.get('/health')
  )

  if (isLoading) return <div>Loading...</div>
  if (error) return <div>Error connecting to backend</div>

  return (
    <div className="px-4 py-6 sm:px-0">
      <div className="border-4 border-dashed border-gray-200 rounded-lg p-8">
        <h2 className="text-2xl font-bold mb-4">Welcome to ITDO ERP System</h2>
        <p className="text-gray-600 mb-4">
          Backend connection status: {data?.data?.status || 'Unknown'}
        </p>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-medium mb-2">Module 1</h3>
            <p className="text-gray-600">Coming soon...</p>
          </div>
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-medium mb-2">Module 2</h3>
            <p className="text-gray-600">Coming soon...</p>
          </div>
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-medium mb-2">Module 3</h3>
            <p className="text-gray-600">Coming soon...</p>
          </div>
        </div>
      </div>
    </div>
  )
}