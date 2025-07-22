import React, { useState, useMemo } from 'react';
import { Button } from '../../components/ui/Button';
import { Select } from '../../components/ui/Select';
import { Badge } from '../../components/ui/Badge';
import { PageContainer, CardLayout, GridLayout } from '../../layouts/MainLayout/MainLayout';
import { useAuth } from '../../hooks/useAuth';
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';

interface DashboardMetrics {
  totalRevenue: number;
  totalOrders: number;
  totalProducts: number;
  totalUsers: number;
  revenueGrowth: number;
  orderGrowth: number;
  productGrowth: number;
  userGrowth: number;
  lowStockProducts: number;
  activeProjects: number;
}

interface SalesData {
  month: string;
  revenue: number;
  orders: number;
  profit: number;
}

interface ProductCategoryData {
  category: string;
  sales: number;
  products: number;
  color: string;
}

interface RecentActivity {
  id: string;
  type: 'order' | 'user' | 'product' | 'system';
  message: string;
  timestamp: string;
  user?: string;
  status: 'success' | 'warning' | 'error' | 'info';
}

interface TopProduct {
  id: string;
  name: string;
  category: string;
  sales: number;
  revenue: number;
  stock: number;
}

type TimeRange = '7d' | '30d' | '90d' | '1y';

export const Dashboard: React.FC = () => {
  const { user } = useAuth();
  const [timeRange, setTimeRange] = useState<TimeRange>('30d');
  const [selectedMetric, setSelectedMetric] = useState<'revenue' | 'orders' | 'profit'>('revenue');

  // モックデータ
  const dashboardMetrics: DashboardMetrics = {
    totalRevenue: 12450000,
    totalOrders: 248,
    totalProducts: 156,
    totalUsers: 45,
    revenueGrowth: 15.3,
    orderGrowth: 8.7,
    productGrowth: 12.1,
    userGrowth: 5.2,
    lowStockProducts: 8,
    activeProjects: 12,
  };

  const salesData: SalesData[] = [
    { month: '1月', revenue: 850000, orders: 18, profit: 255000 },
    { month: '2月', revenue: 920000, orders: 22, profit: 276000 },
    { month: '3月', revenue: 1100000, orders: 25, profit: 330000 },
    { month: '4月', revenue: 980000, orders: 21, profit: 294000 },
    { month: '5月', revenue: 1250000, orders: 28, profit: 375000 },
    { month: '6月', revenue: 1180000, orders: 26, profit: 354000 },
    { month: '7月', revenue: 1350000, orders: 31, profit: 405000 },
    { month: '8月', revenue: 1420000, orders: 33, profit: 426000 },
    { month: '9月', revenue: 1280000, orders: 29, profit: 384000 },
    { month: '10月', revenue: 1520000, orders: 35, profit: 456000 },
    { month: '11月', revenue: 1650000, orders: 38, profit: 495000 },
    { month: '12月', revenue: 1890000, orders: 42, profit: 567000 },
  ];

  const categoryData: ProductCategoryData[] = [
    { category: 'ノートパソコン', sales: 4500000, products: 25, color: '#3B82F6' },
    { category: 'モニター', sales: 2800000, products: 18, color: '#10B981' },
    { category: '周辺機器', sales: 1950000, products: 45, color: '#F59E0B' },
    { category: 'ソフトウェア', sales: 1850000, products: 32, color: '#EF4444' },
    { category: 'サービス', sales: 1350000, products: 12, color: '#8B5CF6' },
  ];

  const recentActivities: RecentActivity[] = [
    {
      id: '1',
      type: 'order',
      message: '新規注文が作成されました：ThinkPad X1 Carbon × 3台',
      timestamp: '5分前',
      user: '田中 太郎',
      status: 'success',
    },
    {
      id: '2',
      type: 'product',
      message: '商品在庫が最小レベルを下回りました：USB-C ハブ',
      timestamp: '15分前',
      status: 'warning',
    },
    {
      id: '3',
      type: 'user',
      message: '新しいユーザーが登録されました：佐藤 花子',
      timestamp: '1時間前',
      user: '管理者',
      status: 'info',
    },
    {
      id: '4',
      type: 'order',
      message: '注文が完了しました：Dell U2723QE × 2台',
      timestamp: '2時間前',
      user: '山田 次郎',
      status: 'success',
    },
    {
      id: '5',
      type: 'system',
      message: 'データベースの自動バックアップが完了しました',
      timestamp: '3時間前',
      status: 'info',
    },
    {
      id: '6',
      type: 'product',
      message: '商品情報が更新されました：MacBook Pro 14"',
      timestamp: '4時間前',
      user: '鈴木 三郎',
      status: 'info',
    },
  ];

  const topProducts: TopProduct[] = [
    {
      id: '1',
      name: 'ThinkPad X1 Carbon',
      category: 'ノートパソコン',
      sales: 15,
      revenue: 2970000,
      stock: 25,
    },
    {
      id: '2',
      name: 'Dell U2723QE',
      category: 'モニター',
      sales: 22,
      revenue: 1870000,
      stock: 15,
    },
    {
      id: '3',
      name: 'MacBook Pro 14"',
      category: 'ノートパソコン',
      sales: 8,
      revenue: 2384000,
      stock: 5,
    },
    {
      id: '4',
      name: 'HHKB Professional',
      category: '周辺機器',
      sales: 35,
      revenue: 1225000,
      stock: 8,
    },
    {
      id: '5',
      name: 'USB-C ハブ',
      category: '周辺機器',
      sales: 128,
      revenue: 1088000,
      stock: 35,
    },
  ];

  // 時間範囲に基づくデータフィルタリング
  const filteredSalesData = useMemo(() => {
    const ranges = {
      '7d': salesData.slice(-1),
      '30d': salesData.slice(-3),
      '90d': salesData.slice(-6),
      '1y': salesData,
    };
    return ranges[timeRange];
  }, [timeRange, salesData]);

  // メトリクスカード
  const MetricCard: React.FC<{
    title: string;
    value: string | number;
    growth?: number;
    icon: React.ReactNode;
    color: string;
  }> = ({ title, value, growth, icon, color }) => (
    <CardLayout className="p-6">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-gray-600">{title}</p>
          <p className="text-2xl font-bold text-gray-900 mt-1">{value}</p>
          {growth !== undefined && (
            <div className={`flex items-center mt-2 ${growth >= 0 ? 'text-green-600' : 'text-red-600'}`}>
              <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d={growth >= 0 ? "M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" : "M13 17h8m0 0V9m0 8l-8-8-4 4-6-6"}
                />
              </svg>
              <span className="text-sm font-medium">
                {growth > 0 ? '+' : ''}{growth}%
              </span>
            </div>
          )}
        </div>
        <div className={`p-3 rounded-full ${color}`}>
          {icon}
        </div>
      </div>
    </CardLayout>
  );

  // アクティビティアイコン
  const getActivityIcon = (type: RecentActivity['type']) => {
    switch (type) {
      case 'order':
        return <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 11V7a4 4 0 00-8 0v4M5 9h14l1 12H4L5 9z" />
        </svg>;
      case 'user':
        return <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
        </svg>;
      case 'product':
        return <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
        </svg>;
      case 'system':
        return <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
        </svg>;
      default:
        return null;
    }
  };

  const getActivityColor = (status: RecentActivity['status']) => {
    switch (status) {
      case 'success': return 'text-green-600';
      case 'warning': return 'text-yellow-600';
      case 'error': return 'text-red-600';
      case 'info': return 'text-blue-600';
      default: return 'text-gray-600';
    }
  };

  return (
    <PageContainer
      title={`おはようございます、${user?.name || 'ユーザー'}さん`}
      subtitle={`今日は${new Date().toLocaleDateString('ja-JP', { 
        year: 'numeric', 
        month: 'long', 
        day: 'numeric',
        weekday: 'long' 
      })}です`}
      actions={
        <div className="flex items-center space-x-3">
          <Select
            value={timeRange}
            onChange={(value) => setTimeRange(value as TimeRange)}
            className="w-32"
          >
            <Select.Option value="7d">過去7日</Select.Option>
            <Select.Option value="30d">過去30日</Select.Option>
            <Select.Option value="90d">過去90日</Select.Option>
            <Select.Option value="1y">過去1年</Select.Option>
          </Select>
          <Button variant="ghost">
            <svg className="h-4 w-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            レポート出力
          </Button>
        </div>
      }
    >
      <div className="space-y-6">
        {/* メトリクスカード */}
        <GridLayout cols={{ default: 1, sm: 2, lg: 4 }} gap="md">
          <MetricCard
            title="総売上"
            value={`¥${dashboardMetrics.totalRevenue.toLocaleString()}`}
            growth={dashboardMetrics.revenueGrowth}
            color="bg-blue-100"
            icon={
              <svg className="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1" />
              </svg>
            }
          />
          <MetricCard
            title="注文数"
            value={dashboardMetrics.totalOrders}
            growth={dashboardMetrics.orderGrowth}
            color="bg-green-100"
            icon={
              <svg className="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 11V7a4 4 0 00-8 0v4M5 9h14l1 12H4L5 9z" />
              </svg>
            }
          />
          <MetricCard
            title="商品数"
            value={dashboardMetrics.totalProducts}
            growth={dashboardMetrics.productGrowth}
            color="bg-purple-100"
            icon={
              <svg className="w-6 h-6 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
              </svg>
            }
          />
          <MetricCard
            title="ユーザー数"
            value={dashboardMetrics.totalUsers}
            growth={dashboardMetrics.userGrowth}
            color="bg-orange-100"
            icon={
              <svg className="w-6 h-6 text-orange-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197m13.5-9a2.5 2.5 0 11-5 0 2.5 2.5 0 015 0z" />
              </svg>
            }
          />
        </GridLayout>

        {/* チャートセクション */}
        <GridLayout cols={{ default: 1, lg: 3 }} gap="lg">
          {/* 売上推移グラフ */}
          <div className="lg:col-span-2">
            <CardLayout>
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold">売上推移</h3>
                <Select
                  value={selectedMetric}
                  onChange={(value) => setSelectedMetric(value as typeof selectedMetric)}
                  className="w-32"
                >
                  <Select.Option value="revenue">売上</Select.Option>
                  <Select.Option value="orders">注文数</Select.Option>
                  <Select.Option value="profit">利益</Select.Option>
                </Select>
              </div>
              <div style={{ height: '300px' }}>
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={filteredSalesData}>
                    <defs>
                      <linearGradient id="colorRevenue" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#3B82F6" stopOpacity={0.3}/>
                        <stop offset="95%" stopColor="#3B82F6" stopOpacity={0}/>
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="month" />
                    <YAxis />
                    <Tooltip 
                      formatter={(value: number) => {
                        if (selectedMetric === 'revenue' || selectedMetric === 'profit') {
                          return `¥${value.toLocaleString()}`;
                        }
                        return `${value}件`;
                      }}
                    />
                    <Area
                      type="monotone"
                      dataKey={selectedMetric}
                      stroke="#3B82F6"
                      strokeWidth={2}
                      fillOpacity={1}
                      fill="url(#colorRevenue)"
                    />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </CardLayout>
          </div>

          {/* カテゴリ別売上 */}
          <div>
            <CardLayout>
              <h3 className="text-lg font-semibold mb-4">カテゴリ別売上</h3>
              <div style={{ height: '300px' }}>
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={categoryData}
                      cx="50%"
                      cy="50%"
                      outerRadius={80}
                      fill="#8884d8"
                      dataKey="sales"
                      label={({ category, percent }) => `${category} ${(percent * 100).toFixed(0)}%`}
                    >
                      {categoryData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Pie>
                    <Tooltip formatter={(value: number) => `¥${value.toLocaleString()}`} />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            </CardLayout>
          </div>
        </GridLayout>

        <GridLayout cols={{ default: 1, lg: 2 }} gap="lg">
          {/* 売上トップ商品 */}
          <CardLayout>
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold">売上トップ商品</h3>
              <Button variant="ghost" size="sm">
                すべて表示
              </Button>
            </div>
            <div className="space-y-3">
              {topProducts.map((product, index) => (
                <div key={product.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <div className="flex items-center space-x-3">
                    <div className="flex items-center justify-center w-8 h-8 bg-blue-100 text-blue-600 rounded-full text-sm font-semibold">
                      {index + 1}
                    </div>
                    <div>
                      <p className="font-medium">{product.name}</p>
                      <p className="text-sm text-gray-500">{product.category}</p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="font-semibold">¥{product.revenue.toLocaleString()}</p>
                    <p className="text-sm text-gray-500">{product.sales}件売上</p>
                  </div>
                </div>
              ))}
            </div>
          </CardLayout>

          {/* 最近のアクティビティ */}
          <CardLayout>
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold">最近のアクティビティ</h3>
              <Button variant="ghost" size="sm">
                すべて表示
              </Button>
            </div>
            <div className="space-y-3 max-h-80 overflow-y-auto">
              {recentActivities.map(activity => (
                <div key={activity.id} className="flex items-start space-x-3 p-3 hover:bg-gray-50 rounded-lg">
                  <div className={`flex items-center justify-center w-8 h-8 rounded-full ${
                    activity.status === 'success' ? 'bg-green-100' :
                    activity.status === 'warning' ? 'bg-yellow-100' :
                    activity.status === 'error' ? 'bg-red-100' : 'bg-blue-100'
                  }`}>
                    <div className={getActivityColor(activity.status)}>
                      {getActivityIcon(activity.type)}
                    </div>
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm text-gray-900">{activity.message}</p>
                    <div className="flex items-center space-x-2 mt-1">
                      <span className="text-xs text-gray-500">{activity.timestamp}</span>
                      {activity.user && (
                        <>
                          <span className="text-xs text-gray-400">•</span>
                          <span className="text-xs text-gray-500">{activity.user}</span>
                        </>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </CardLayout>
        </GridLayout>

        {/* 警告とアラート */}
        <GridLayout cols={{ default: 1, lg: 3 }} gap="md">
          <CardLayout className="border-l-4 border-red-500 bg-red-50">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <svg className="h-5 w-5 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z" />
                </svg>
              </div>
              <div className="ml-3">
                <h4 className="text-sm font-medium text-red-800">在庫不足警告</h4>
                <p className="text-sm text-red-700 mt-1">
                  {dashboardMetrics.lowStockProducts}個の商品が最小在庫レベルを下回っています
                </p>
              </div>
            </div>
          </CardLayout>

          <CardLayout className="border-l-4 border-green-500 bg-green-50">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <svg className="h-5 w-5 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <div className="ml-3">
                <h4 className="text-sm font-medium text-green-800">進行中プロジェクト</h4>
                <p className="text-sm text-green-700 mt-1">
                  {dashboardMetrics.activeProjects}個のプロジェクトが順調に進行中です
                </p>
              </div>
            </div>
          </CardLayout>

          <CardLayout className="border-l-4 border-blue-500 bg-blue-50">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <svg className="h-5 w-5 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <div className="ml-3">
                <h4 className="text-sm font-medium text-blue-800">システム状況</h4>
                <p className="text-sm text-blue-700 mt-1">
                  すべてのシステムが正常に動作中です
                </p>
              </div>
            </div>
          </CardLayout>
        </GridLayout>
      </div>
    </PageContainer>
  );
};