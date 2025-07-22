import React from 'react';

interface User {
  id: string;
  email: string;
  username: string;
  fullName: string;
  isActive: boolean;
}

export const UserListPage: React.FC = () => {
  // Mock data
  const users: User[] = [
    { id: '1', email: 'tanaka@itdo.jp', username: 'tanaka', fullName: '田中 太郎', isActive: true },
    { id: '2', email: 'sato@itdo.jp', username: 'sato', fullName: '佐藤 花子', isActive: true },
    { id: '3', email: 'yamada@itdo.jp', username: 'yamada', fullName: '山田 次郎', isActive: false },
  ];

  return (
    <div className="min-h-screen bg-gray-100">
      {/* Simple header */}
      <div className="bg-white shadow">
        <div className="px-4 py-6">
          <h1 className="text-2xl font-bold text-gray-900">ITDO ERP - ユーザー管理</h1>
        </div>
      </div>

      {/* Main content */}
      <div className="py-8 px-4 sm:px-6 lg:px-8">
        <div className="bg-white shadow rounded-lg">
          <div className="px-4 py-5 sm:px-6 border-b border-gray-200">
            <h3 className="text-lg font-medium leading-6 text-gray-900">ユーザー一覧</h3>
            <p className="mt-1 max-w-2xl text-sm text-gray-500">
              システムユーザーの一覧と管理
            </p>
          </div>
          <div className="overflow-hidden">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    ユーザー名
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    メールアドレス
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    フルネーム
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    状態
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {users.map((user) => (
                  <tr key={user.id}>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                      {user.username}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {user.email}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {user.fullName}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                        user.isActive 
                          ? 'bg-green-100 text-green-800' 
                          : 'bg-red-100 text-red-800'
                      }`}>
                        {user.isActive ? '有効' : '無効'}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
};