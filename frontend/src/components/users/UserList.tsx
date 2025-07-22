import React, { useState } from 'react';

interface User {
  id: string;
  username: string;
  email: string;
  fullName: string;
  role: string;
  department: string;
  status: 'active' | 'inactive' | 'suspended';
  lastLogin: string;
  createdAt: string;
}

const mockUsers: User[] = [
  {
    id: '1',
    username: 'yamada.taro',
    email: 'yamada@example.com',
    fullName: '山田太郎',
    role: '管理者',
    department: 'システム部',
    status: 'active',
    lastLogin: '2024-07-22T14:30:00Z',
    createdAt: '2024-01-15'
  },
  {
    id: '2',
    username: 'sato.hanako',
    email: 'sato@example.com',
    fullName: '佐藤花子',
    role: '一般ユーザー',
    department: '営業部',
    status: 'active',
    lastLogin: '2024-07-22T10:15:00Z',
    createdAt: '2024-02-20'
  },
  {
    id: '3',
    username: 'tanaka.ichiro',
    email: 'tanaka@example.com',
    fullName: '田中一郎',
    role: 'マネージャー',
    department: '営業部',
    status: 'active',
    lastLogin: '2024-07-21T16:45:00Z',
    createdAt: '2024-01-10'
  },
  {
    id: '4',
    username: 'suzuki.misaki',
    email: 'suzuki@example.com',
    fullName: '鈴木美咲',
    role: '一般ユーザー',
    department: '経理部',
    status: 'inactive',
    lastLogin: '2024-07-15T09:30:00Z',
    createdAt: '2024-03-05'
  },
  {
    id: '5',
    username: 'takahashi.kenta',
    email: 'takahashi@example.com',
    fullName: '高橋健太',
    role: '一般ユーザー',
    department: '総務部',
    status: 'suspended',
    lastLogin: '2024-07-10T14:20:00Z',
    createdAt: '2024-04-12'
  }
];

export const UserList: React.FC = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedStatus, setSelectedStatus] = useState<'all' | 'active' | 'inactive' | 'suspended'>('all');
  const [selectedRole, setSelectedRole] = useState<'all' | '管理者' | 'マネージャー' | '一般ユーザー'>('all');

  const filteredUsers = mockUsers.filter(user => {
    const matchesSearch = 
      user.fullName.toLowerCase().includes(searchTerm.toLowerCase()) ||
      user.username.toLowerCase().includes(searchTerm.toLowerCase()) ||
      user.email.toLowerCase().includes(searchTerm.toLowerCase()) ||
      user.department.toLowerCase().includes(searchTerm.toLowerCase());
    
    const matchesStatus = selectedStatus === 'all' || user.status === selectedStatus;
    const matchesRole = selectedRole === 'all' || user.role === selectedRole;

    return matchesSearch && matchesStatus && matchesRole;
  });

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

  const getRoleColor = (role: string) => {
    switch (role) {
      case '管理者': return 'text-purple-700 bg-purple-100';
      case 'マネージャー': return 'text-blue-700 bg-blue-100';
      case '一般ユーザー': return 'text-gray-700 bg-gray-100';
      default: return 'text-gray-700 bg-gray-100';
    }
  };

  const formatLastLogin = (timestamp: string) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffInHours = Math.floor((now.getTime() - date.getTime()) / (1000 * 60 * 60));

    if (diffInHours < 1) return '1時間以内';
    if (diffInHours < 24) return `${diffInHours}時間前`;
    if (diffInHours < 168) return `${Math.floor(diffInHours / 24)}日前`;
    return date.toLocaleDateString('ja-JP');
  };

  const activeCount = mockUsers.filter(u => u.status === 'active').length;
  const inactiveCount = mockUsers.filter(u => u.status === 'inactive').length;
  const suspendedCount = mockUsers.filter(u => u.status === 'suspended').length;

  return (
    <div className="bg-white rounded-lg shadow">
      {/* ヘッダー */}
      <div className="px-6 py-4 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-xl font-semibold text-gray-900">ユーザー管理</h2>
            <p className="text-sm text-gray-500">システム利用者の管理</p>
          </div>
          <button className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 flex items-center space-x-2">
            <span>➕</span>
            <span>新規ユーザー</span>
          </button>
        </div>
      </div>

      {/* 統計サマリー */}
      <div className="px-6 py-4 bg-gray-50 border-b border-gray-200">
        <div className="grid grid-cols-4 gap-4">
          <div className="text-center">
            <div className="text-2xl font-bold text-gray-900">{mockUsers.length}</div>
            <div className="text-sm text-gray-500">総ユーザー数</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-green-600">{activeCount}</div>
            <div className="text-sm text-gray-500">アクティブ</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-gray-600">{inactiveCount}</div>
            <div className="text-sm text-gray-500">非アクティブ</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-red-600">{suspendedCount}</div>
            <div className="text-sm text-gray-500">停止中</div>
          </div>
        </div>
      </div>

      {/* フィルター */}
      <div className="px-6 py-4 border-b border-gray-200">
        <div className="flex flex-wrap items-center gap-4">
          <div className="flex-1 min-w-64">
            <input
              type="text"
              placeholder="ユーザー名、メール、部署で検索..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
          <div>
            <select
              value={selectedStatus}
              onChange={(e) => setSelectedStatus(e.target.value as any)}
              className="px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="all">すべてのステータス</option>
              <option value="active">アクティブ</option>
              <option value="inactive">非アクティブ</option>
              <option value="suspended">停止中</option>
            </select>
          </div>
          <div>
            <select
              value={selectedRole}
              onChange={(e) => setSelectedRole(e.target.value as any)}
              className="px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="all">すべての役割</option>
              <option value="管理者">管理者</option>
              <option value="マネージャー">マネージャー</option>
              <option value="一般ユーザー">一般ユーザー</option>
            </select>
          </div>
        </div>
      </div>

      {/* ユーザーリスト */}
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                ユーザー
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                役割・部署
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                ステータス
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                最終ログイン
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                登録日
              </th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                操作
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {filteredUsers.map((user) => (
              <tr key={user.id} className="hover:bg-gray-50">
                <td className="px-6 py-4">
                  <div className="flex items-center">
                    <div className="flex-shrink-0 h-10 w-10">
                      <div className="h-10 w-10 rounded-full bg-gray-300 flex items-center justify-center">
                        <span className="text-sm font-medium text-gray-700">
                          {user.fullName.charAt(0)}
                        </span>
                      </div>
                    </div>
                    <div className="ml-4">
                      <div className="text-sm font-medium text-gray-900">{user.fullName}</div>
                      <div className="text-sm text-gray-500">{user.email}</div>
                      <div className="text-xs text-gray-400">@{user.username}</div>
                    </div>
                  </div>
                </td>
                <td className="px-6 py-4">
                  <div>
                    <span className={`inline-flex px-2 py-1 text-xs font-medium rounded-full ${getRoleColor(user.role)}`}>
                      {user.role}
                    </span>
                    <div className="text-sm text-gray-500 mt-1">{user.department}</div>
                  </div>
                </td>
                <td className="px-6 py-4">
                  <span className={`inline-flex px-2 py-1 text-xs font-medium rounded-full ${getStatusColor(user.status)}`}>
                    {getStatusText(user.status)}
                  </span>
                </td>
                <td className="px-6 py-4 text-sm text-gray-500">
                  {formatLastLogin(user.lastLogin)}
                </td>
                <td className="px-6 py-4 text-sm text-gray-500">
                  {new Date(user.createdAt).toLocaleDateString('ja-JP')}
                </td>
                <td className="px-6 py-4 text-right text-sm font-medium">
                  <div className="flex justify-end space-x-2">
                    <button className="text-blue-600 hover:text-blue-900">編集</button>
                    <button className="text-gray-600 hover:text-gray-900">詳細</button>
                    {user.status === 'active' ? (
                      <button className="text-red-600 hover:text-red-900">停止</button>
                    ) : (
                      <button className="text-green-600 hover:text-green-900">有効化</button>
                    )}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {filteredUsers.length === 0 && (
        <div className="text-center py-12">
          <div className="text-gray-500">
            <div className="text-4xl mb-4">👤</div>
            <p>該当するユーザーが見つかりません</p>
            <p className="text-sm mt-2">検索条件を変更してください</p>
          </div>
        </div>
      )}

      {/* フッター */}
      <div className="px-6 py-4 border-t border-gray-200 bg-gray-50">
        <div className="flex items-center justify-between">
          <div className="text-sm text-gray-500">
            {filteredUsers.length}件中 1-{Math.min(filteredUsers.length, 10)}件を表示
          </div>
          <div className="flex space-x-2">
            <button className="px-3 py-1 border border-gray-300 rounded text-sm hover:bg-gray-50">
              前へ
            </button>
            <button className="px-3 py-1 border border-gray-300 rounded text-sm hover:bg-gray-50">
              次へ
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};