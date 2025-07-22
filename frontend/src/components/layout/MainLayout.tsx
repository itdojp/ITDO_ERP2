import React from 'react';

interface MainLayoutProps {
  children: React.ReactNode;
}

export const MainLayout: React.FC<MainLayoutProps> = ({ children }) => {
  return (
    <div className="min-h-screen bg-gray-100">
      <nav className="bg-white shadow">
        <div className="px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              <h1 className="text-xl font-semibold text-gray-900">ITDO ERP</h1>
            </div>
            <div className="flex items-center space-x-4">
              <button className="text-gray-700 hover:text-gray-900 px-3 py-2 rounded-md text-sm font-medium">
                ダッシュボード
              </button>
              <button className="text-gray-700 hover:text-gray-900 px-3 py-2 rounded-md text-sm font-medium">
                ユーザー管理
              </button>
              <button className="text-gray-700 hover:text-gray-900 px-3 py-2 rounded-md text-sm font-medium">
                商品管理
              </button>
            </div>
          </div>
        </div>
      </nav>
      <main className="py-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          {children}
        </div>
      </main>
    </div>
  );
};