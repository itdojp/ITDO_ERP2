import React, { useState } from 'react';

interface UserDetailProps {
  userId: string;
}

interface UserDetail {
  id: string;
  username: string;
  email: string;
  fullName: string;
  role: string;
  department: string;
  status: 'active' | 'inactive' | 'suspended';
  lastLogin: string;
  createdAt: string;
  phone?: string;
  address?: string;
  emergencyContact?: string;
  permissions: string[];
  loginHistory: Array<{
    id: string;
    timestamp: string;
    ip: string;
    device: string;
    success: boolean;
  }>;
  activityLog: Array<{
    id: string;
    action: string;
    target: string;
    timestamp: string;
  }>;
}

const mockUserDetail: UserDetail = {
  id: '1',
  username: 'yamada.taro',
  email: 'yamada@example.com',
  fullName: '山田太郎',
  role: '管理者',
  department: 'システム部',
  status: 'active',
  lastLogin: '2024-07-22T14:30:00Z',
  createdAt: '2024-01-15',
  phone: '090-1234-5678',
  address: '東京都渋谷区',
  emergencyContact: '山田花子 (配偶者) 090-8765-4321',
  permissions: ['user.read', 'user.write', 'product.read', 'product.write', 'order.read', 'order.write', 'report.read', 'system.admin'],
  loginHistory: [
    {
      id: '1',
      timestamp: '2024-07-22T14:30:00Z',
      ip: '192.168.1.100',
      device: 'Chrome on Windows 11',
      success: true
    },
    {
      id: '2',
      timestamp: '2024-07-22T09:15:00Z',
      ip: '192.168.1.100',
      device: 'Chrome on Windows 11',
      success: true
    },
    {
      id: '3',
      timestamp: '2024-07-21T16:45:00Z',
      ip: '192.168.1.100',
      device: 'Chrome on Windows 11',
      success: true
    },
    {
      id: '4',
      timestamp: '2024-07-20T13:20:00Z',
      ip: '192.168.1.101',
      device: 'Safari on iPhone',
      success: false
    }
  ],
  activityLog: [
    {
      id: '1',
      action: '商品を登録',
      target: 'ThinkPad X1 Carbon',
      timestamp: '2024-07-22T14:30:00Z'
    },
    {
      id: '2',
      action: 'ユーザーを編集',
      target: '佐藤花子',
      timestamp: '2024-07-22T11:15:00Z'
    },
    {
      id: '3',
      action: 'レポートを出力',
      target: '月次売上レポート',
      timestamp: '2024-07-21T15:30:00Z'
    }
  ]
};

export const UserDetail: React.FC<UserDetailProps> = ({ userId }) => {
  const [activeTab, setActiveTab] = useState<'overview' | 'permissions' | 'activity' | 'security'>('overview');

  const user = mockUserDetail; // 実際の実装では、userIdを使ってAPIからデータを取得

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'text-green-700 bg-green-100';
      case 'inactive': return 'text-gray-700 bg-gray-100';
      case 'suspended': return 'text-red-700 bg-red-100';
      default: return 'text-gray-700 bg-gray-100';
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case 'active': return 'アクティブ';
      case 'inactive': return '非アクティブ';
      case 'suspended': return '停止中';
      default: return '不明';
    }
  };

  const formatDateTime = (timestamp: string) => {
    return new Date(timestamp).toLocaleString('ja-JP');
  };

  const tabs = [
    { key: 'overview', label: '概要', icon: '👤' },
    { key: 'permissions', label: '権限', icon: '🔐' },
    { key: 'activity', label: '活動履歴', icon: '📋' },
    { key: 'security', label: 'セキュリティ', icon: '🛡️' }
  ];

  return (
    <div className="bg-white rounded-lg shadow">
      {/* ヘッダー */}
      <div className="px-6 py-4 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <div className="h-16 w-16 rounded-full bg-gray-300 flex items-center justify-center">
              <span className="text-xl font-bold text-gray-700">
                {user.fullName.charAt(0)}
              </span>
            </div>
            <div>
              <h2 className="text-2xl font-semibold text-gray-900">{user.fullName}</h2>
              <p className="text-sm text-gray-500">{user.email}</p>
              <div className="flex items-center space-x-2 mt-1">
                <span className={`inline-flex px-2 py-1 text-xs font-medium rounded-full ${getStatusColor(user.status)}`}>
                  {getStatusText(user.status)}
                </span>
                <span className="text-sm text-gray-500">
                  {user.role} • {user.department}
                </span>
              </div>
            </div>
          </div>
          <div className="flex space-x-2">
            <button className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700">
              編集
            </button>
            <button className="bg-gray-200 text-gray-700 px-4 py-2 rounded-md hover:bg-gray-300">
              削除
            </button>
          </div>
        </div>
      </div>

      {/* タブナビゲーション */}
      <div className="border-b border-gray-200">
        <nav className="flex space-x-8 px-6">
          {tabs.map((tab) => (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key as any)}
              className={`
                py-4 px-1 border-b-2 font-medium text-sm flex items-center space-x-2
                ${activeTab === tab.key
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }
              `}
            >
              <span>{tab.icon}</span>
              <span>{tab.label}</span>
            </button>
          ))}
        </nav>
      </div>

      {/* タブコンテンツ */}
      <div className="p-6">
        {activeTab === 'overview' && (
          <div className="space-y-6">
            <div className="grid grid-cols-2 gap-6">
              <div>
                <h3 className="text-lg font-medium text-gray-900 mb-4">基本情報</h3>
                <dl className="space-y-3">
                  <div>
                    <dt className="text-sm font-medium text-gray-500">ユーザー名</dt>
                    <dd className="text-sm text-gray-900">{user.username}</dd>
                  </div>
                  <div>
                    <dt className="text-sm font-medium text-gray-500">メールアドレス</dt>
                    <dd className="text-sm text-gray-900">{user.email}</dd>
                  </div>
                  <div>
                    <dt className="text-sm font-medium text-gray-500">電話番号</dt>
                    <dd className="text-sm text-gray-900">{user.phone || '未設定'}</dd>
                  </div>
                  <div>
                    <dt className="text-sm font-medium text-gray-500">住所</dt>
                    <dd className="text-sm text-gray-900">{user.address || '未設定'}</dd>
                  </div>
                  <div>
                    <dt className="text-sm font-medium text-gray-500">緊急連絡先</dt>
                    <dd className="text-sm text-gray-900">{user.emergencyContact || '未設定'}</dd>
                  </div>
                </dl>
              </div>
              <div>
                <h3 className="text-lg font-medium text-gray-900 mb-4">システム情報</h3>
                <dl className="space-y-3">
                  <div>
                    <dt className="text-sm font-medium text-gray-500">役割</dt>
                    <dd className="text-sm text-gray-900">{user.role}</dd>
                  </div>
                  <div>
                    <dt className="text-sm font-medium text-gray-500">部署</dt>
                    <dd className="text-sm text-gray-900">{user.department}</dd>
                  </div>
                  <div>
                    <dt className="text-sm font-medium text-gray-500">ステータス</dt>
                    <dd>
                      <span className={`inline-flex px-2 py-1 text-xs font-medium rounded-full ${getStatusColor(user.status)}`}>
                        {getStatusText(user.status)}
                      </span>
                    </dd>
                  </div>
                  <div>
                    <dt className="text-sm font-medium text-gray-500">登録日</dt>
                    <dd className="text-sm text-gray-900">
                      {new Date(user.createdAt).toLocaleDateString('ja-JP')}
                    </dd>
                  </div>
                  <div>
                    <dt className="text-sm font-medium text-gray-500">最終ログイン</dt>
                    <dd className="text-sm text-gray-900">
                      {formatDateTime(user.lastLogin)}
                    </dd>
                  </div>
                </dl>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'permissions' && (
          <div>
            <h3 className="text-lg font-medium text-gray-900 mb-4">権限設定</h3>
            <div className="grid grid-cols-2 gap-4">
              {user.permissions.map((permission) => (
                <div key={permission} className="flex items-center justify-between p-3 border border-gray-200 rounded-lg">
                  <span className="text-sm text-gray-900">{permission}</span>
                  <span className="text-green-600 text-sm">✓ 許可</span>
                </div>
              ))}
            </div>
            <div className="mt-6">
              <button className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700">
                権限を編集
              </button>
            </div>
          </div>
        )}

        {activeTab === 'activity' && (
          <div>
            <h3 className="text-lg font-medium text-gray-900 mb-4">最近の活動</h3>
            <div className="space-y-4">
              {user.activityLog.map((activity) => (
                <div key={activity.id} className="flex items-start space-x-3 p-4 border border-gray-200 rounded-lg">
                  <div className="flex-shrink-0 w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
                    <span className="text-blue-600 text-sm">📝</span>
                  </div>
                  <div className="flex-1">
                    <p className="text-sm text-gray-900">
                      <span className="font-medium">{activity.action}</span>
                      {activity.target && (
                        <>
                          <span className="mx-1">:</span>
                          <span className="text-blue-600">{activity.target}</span>
                        </>
                      )}
                    </p>
                    <p className="text-xs text-gray-500 mt-1">
                      {formatDateTime(activity.timestamp)}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {activeTab === 'security' && (
          <div>
            <h3 className="text-lg font-medium text-gray-900 mb-4">ログイン履歴</h3>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                      日時
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                      IPアドレス
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                      デバイス
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                      結果
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {user.loginHistory.map((login) => (
                    <tr key={login.id}>
                      <td className="px-4 py-4 text-sm text-gray-900">
                        {formatDateTime(login.timestamp)}
                      </td>
                      <td className="px-4 py-4 text-sm text-gray-500">
                        {login.ip}
                      </td>
                      <td className="px-4 py-4 text-sm text-gray-500">
                        {login.device}
                      </td>
                      <td className="px-4 py-4">
                        <span className={`inline-flex px-2 py-1 text-xs font-medium rounded-full ${
                          login.success 
                            ? 'text-green-700 bg-green-100' 
                            : 'text-red-700 bg-red-100'
                        }`}>
                          {login.success ? '成功' : '失敗'}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};