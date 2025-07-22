import React from 'react';

interface DashboardMetrics {
  totalRevenue: number;
  totalOrders: number;
  totalProducts: number;
  totalUsers: number;
}

export const DashboardPage: React.FC = () => {
  // Mock dashboard metrics
  const metrics: DashboardMetrics = {
    totalRevenue: 12450000,
    totalOrders: 248,
    totalProducts: 156,
    totalUsers: 45,
  };

  return (
    <div className="min-h-screen bg-gray-100">
      {/* Header */}
      <div className="bg-white shadow">
        <div className="px-4 py-6">
          <h1 className="text-2xl font-bold text-gray-900">ITDO ERP - ダッシュボード</h1>
        </div>
      </div>

      {/* Main content */}
      <div className="py-8 px-4 sm:px-6 lg:px-8">
        {/* Metrics Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          {/* Total Revenue */}
          <div className="bg-white overflow-hidden shadow rounded-lg">
            <div className="p-5">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <div className="w-8 h-8 bg-blue-500 rounded-md flex items-center justify-center">
                    <span className="text-white text-lg font-bold">¥</span>
                  </div>
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-500 truncate">総売上</dt>
                    <dd className="text-lg font-medium text-gray-900">¥{metrics.totalRevenue.toLocaleString()}</dd>
                  </dl>
                </div>
              </div>
            </div>
          </div>

          {/* Total Orders */}
          <div className="bg-white overflow-hidden shadow rounded-lg">
            <div className="p-5">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <div className="w-8 h-8 bg-green-500 rounded-md flex items-center justify-center">
                    <span className="text-white text-sm font-bold">#</span>
                  </div>
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-500 truncate">注文数</dt>
                    <dd className="text-lg font-medium text-gray-900">{metrics.totalOrders}件</dd>
                  </dl>
                </div>
              </div>
            </div>
          </div>

          {/* Total Products */}
          <div className="bg-white overflow-hidden shadow rounded-lg">
            <div className="p-5">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <div className="w-8 h-8 bg-purple-500 rounded-md flex items-center justify-center">
                    <span className="text-white text-sm font-bold">📦</span>
                  </div>
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-500 truncate">商品数</dt>
                    <dd className="text-lg font-medium text-gray-900">{metrics.totalProducts}個</dd>
                  </dl>
                </div>
              </div>
            </div>
          </div>

          {/* Total Users */}
          <div className="bg-white overflow-hidden shadow rounded-lg">
            <div className="p-5">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <div className="w-8 h-8 bg-orange-500 rounded-md flex items-center justify-center">
                    <span className="text-white text-sm font-bold">👤</span>
                  </div>
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-500 truncate">ユーザー数</dt>
                    <dd className="text-lg font-medium text-gray-900">{metrics.totalUsers}名</dd>
                  </dl>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Recent Activity */}
        <div className="bg-white shadow rounded-lg">
          <div className="px-4 py-5 sm:px-6 border-b border-gray-200">
            <h3 className="text-lg font-medium leading-6 text-gray-900">最近のアクティビティ</h3>
            <p className="mt-1 max-w-2xl text-sm text-gray-500">システムの最新の動向</p>
          </div>
          <div className="px-4 py-5">
            <div className="space-y-4">
              <div className="flex items-center space-x-3">
                <span className="flex-shrink-0 w-2 h-2 bg-green-500 rounded-full"></span>
                <span className="text-sm text-gray-900">新規注文: ThinkPad X1 Carbon × 3台</span>
                <span className="text-xs text-gray-500">5分前</span>
              </div>
              <div className="flex items-center space-x-3">
                <span className="flex-shrink-0 w-2 h-2 bg-blue-500 rounded-full"></span>
                <span className="text-sm text-gray-900">ユーザー登録: 佐藤 花子</span>
                <span className="text-xs text-gray-500">1時間前</span>
              </div>
              <div className="flex items-center space-x-3">
                <span className="flex-shrink-0 w-2 h-2 bg-yellow-500 rounded-full"></span>
                <span className="text-sm text-gray-900">在庫警告: USB-C ハブ (残り8個)</span>
                <span className="text-xs text-gray-500">2時間前</span>
              </div>
              <div className="flex items-center space-x-3">
                <span className="flex-shrink-0 w-2 h-2 bg-purple-500 rounded-full"></span>
                <span className="text-sm text-gray-900">商品更新: MacBook Pro 14"</span>
                <span className="text-xs text-gray-500">4時間前</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};