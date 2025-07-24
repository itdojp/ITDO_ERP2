import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { apiClient } from '@/services/api';

interface InventoryStatistics {
  total_items: number;
  total_value: number;
  low_stock_items: number;
  out_of_stock_items: number;
  excess_stock_items: number;
  avg_turnover_rate: number;
  last_updated: string;
}

interface RecentMovement {
  id: number;
  product_code: string;
  product_name: string;
  movement_type: 'adjustment' | 'receipt' | 'issue' | 'transfer';
  quantity_change: number;
  current_quantity: number;
  reason: string;
  created_at: string;
  created_by: string;
}

interface AlertItem {
  id: number;
  product_code: string;
  product_name: string;
  current_stock: number;
  minimum_stock: number;
  alert_type: 'low_stock' | 'out_of_stock' | 'excess_stock';
  location: string;
}

export const InventoryOverview: React.FC = () => {
  const navigate = useNavigate();

  // Fetch inventory statistics
  const { data: statistics } = useQuery({
    queryKey: ['inventory-statistics'],
    queryFn: async (): Promise<InventoryStatistics> => {
      const response = await apiClient.get('/api/v1/inventory/statistics');
      return response.data || {
        total_items: 0,
        total_value: 0,
        low_stock_items: 0,
        out_of_stock_items: 0,
        excess_stock_items: 0,
        avg_turnover_rate: 0,
        last_updated: new Date().toISOString()
      };
    },
  });

  // Fetch recent movements
  const { data: recentMovements } = useQuery({
    queryKey: ['recent-movements'],
    queryFn: async (): Promise<RecentMovement[]> => {
      const response = await apiClient.get('/api/v1/inventory/movements/recent?limit=10');
      return response.data || [];
    },
  });

  // Fetch alert items
  const { data: alertItems } = useQuery({
    queryKey: ['inventory-alerts'],
    queryFn: async (): Promise<AlertItem[]> => {
      const response = await apiClient.get('/api/v1/inventory/alerts');
      return response.data || [];
    },
  });

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(amount);
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString() + ' ' + 
           new Date(dateString).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  const getMovementTypeLabel = (type: string) => {
    switch (type) {
      case 'adjustment': return 'Adjustment';
      case 'receipt': return 'Receipt';
      case 'issue': return 'Issue';
      case 'transfer': return 'Transfer';
      default: return type;
    }
  };

  const getMovementTypeColor = (type: string) => {
    switch (type) {
      case 'adjustment': return 'bg-blue-100 text-blue-800';
      case 'receipt': return 'bg-green-100 text-green-800';
      case 'issue': return 'bg-red-100 text-red-800';
      case 'transfer': return 'bg-purple-100 text-purple-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getAlertTypeLabel = (type: string) => {
    switch (type) {
      case 'low_stock': return 'Low Stock';
      case 'out_of_stock': return 'Out of Stock';
      case 'excess_stock': return 'Excess Stock';
      default: return type;
    }
  };

  const getAlertTypeColor = (type: string) => {
    switch (type) {
      case 'low_stock': return 'bg-yellow-100 text-yellow-800';
      case 'out_of_stock': return 'bg-red-100 text-red-800';
      case 'excess_stock': return 'bg-blue-100 text-blue-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Inventory Overview</h1>
          <p className="text-gray-600">Real-time inventory dashboard and analytics</p>
        </div>
        <div className="flex space-x-3">
          <button
            onClick={() => navigate('/inventory/adjust')}
            className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 flex items-center gap-2"
          >
            <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
            </svg>
            Stock Adjustment
          </button>
          <button
            onClick={() => navigate('/inventory')}
            className="bg-gray-600 text-white px-4 py-2 rounded-lg hover:bg-gray-700 flex items-center gap-2"
          >
            <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 10h16M4 14h16M4 18h16" />
            </svg>
            View All Items
          </button>
        </div>
      </div>

      {/* Statistics Cards */}
      {statistics && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className="p-2 bg-blue-100 rounded-lg">
                <svg className="h-8 w-8 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
                </svg>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Total Items</p>
                <p className="text-2xl font-bold text-gray-900">{statistics.total_items.toLocaleString()}</p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className="p-2 bg-green-100 rounded-lg">
                <svg className="h-8 w-8 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1" />
                </svg>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Total Value</p>
                <p className="text-2xl font-bold text-gray-900">{formatCurrency(statistics.total_value)}</p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className="p-2 bg-yellow-100 rounded-lg">
                <svg className="h-8 w-8 text-yellow-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z" />
                </svg>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Low Stock Items</p>
                <p className="text-2xl font-bold text-gray-900">{statistics.low_stock_items}</p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className="p-2 bg-red-100 rounded-lg">
                <svg className="h-8 w-8 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Out of Stock</p>
                <p className="text-2xl font-bold text-gray-900">{statistics.out_of_stock_items}</p>
              </div>
            </div>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent Movements */}
        <div className="bg-white rounded-lg shadow">
          <div className="p-6 border-b border-gray-200">
            <div className="flex justify-between items-center">
              <h2 className="text-lg font-semibold text-gray-900">Recent Movements</h2>
              <button
                onClick={() => navigate('/inventory/movements')}
                className="text-sm text-blue-600 hover:text-blue-800"
              >
                View All →
              </button>
            </div>
          </div>
          <div className="p-6">
            {recentMovements && recentMovements.length > 0 ? (
              <div className="space-y-4">
                {recentMovements.slice(0, 5).map((movement) => (
                  <div key={movement.id} className="flex items-center justify-between py-3 border-b border-gray-100 last:border-b-0">
                    <div className="flex-1">
                      <div className="flex items-center space-x-3">
                        <span className={`inline-flex px-2 py-1 text-xs font-medium rounded-full ${getMovementTypeColor(movement.movement_type)}`}>
                          {getMovementTypeLabel(movement.movement_type)}
                        </span>
                        <span className="text-sm font-medium text-gray-900">{movement.product_name}</span>
                      </div>
                      <div className="mt-1 text-xs text-gray-500">
                        {movement.product_code} • {movement.reason}
                      </div>
                    </div>
                    <div className="text-right">
                      <div className={`text-sm font-medium ${movement.quantity_change >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                        {movement.quantity_change >= 0 ? '+' : ''}{movement.quantity_change}
                      </div>
                      <div className="text-xs text-gray-500">
                        {formatDate(movement.created_at)}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8 text-gray-500">
                <svg className="mx-auto h-12 w-12 text-gray-400 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v10a2 2 0 002 2h8a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                </svg>
                <p>No recent movements</p>
              </div>
            )}
          </div>
        </div>

        {/* Inventory Alerts */}
        <div className="bg-white rounded-lg shadow">
          <div className="p-6 border-b border-gray-200">
            <h2 className="text-lg font-semibold text-gray-900">Inventory Alerts</h2>
          </div>
          <div className="p-6">
            {alertItems && alertItems.length > 0 ? (
              <div className="space-y-4">
                {alertItems.slice(0, 5).map((alert) => (
                  <div key={alert.id} className="flex items-center justify-between py-3 border-b border-gray-100 last:border-b-0">
                    <div className="flex-1">
                      <div className="flex items-center space-x-3">
                        <span className={`inline-flex px-2 py-1 text-xs font-medium rounded-full ${getAlertTypeColor(alert.alert_type)}`}>
                          {getAlertTypeLabel(alert.alert_type)}
                        </span>
                        <span className="text-sm font-medium text-gray-900">{alert.product_name}</span>
                      </div>
                      <div className="mt-1 text-xs text-gray-500">
                        {alert.product_code} • {alert.location}
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="text-sm font-medium text-gray-900">
                        {alert.current_stock}
                      </div>
                      <div className="text-xs text-gray-500">
                        Min: {alert.minimum_stock}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8 text-gray-500">
                <svg className="mx-auto h-12 w-12 text-green-400 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <p>No inventory alerts</p>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Additional Metrics */}
      {statistics && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Turnover Rate</h3>
            <div className="text-3xl font-bold text-blue-600">
              {statistics.avg_turnover_rate.toFixed(1)}x
            </div>
            <p className="text-sm text-gray-600 mt-2">Average inventory turnover per year</p>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Excess Stock</h3>
            <div className="text-3xl font-bold text-purple-600">
              {statistics.excess_stock_items}
            </div>
            <p className="text-sm text-gray-600 mt-2">Items above maximum levels</p>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Last Updated</h3>
            <div className="text-lg font-medium text-gray-900">
              {formatDate(statistics.last_updated)}
            </div>
            <p className="text-sm text-gray-600 mt-2">Latest inventory sync</p>
          </div>
        </div>
      )}
    </div>
  );
};

export default InventoryOverview;