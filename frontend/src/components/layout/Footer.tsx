import React from 'react';

export const Footer: React.FC = () => {
  return (
    <footer className="bg-white border-t border-gray-200">
      <div className="px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="text-sm text-gray-500">
            © 2024 ITDO ERP System v2.0
          </div>
          <div className="flex items-center space-x-4 text-sm text-gray-500">
            <a href="/privacy" className="hover:text-gray-700">
              プライバシーポリシー
            </a>
            <a href="/terms" className="hover:text-gray-700">
              利用規約
            </a>
            <a href="/support" className="hover:text-gray-700">
              サポート
            </a>
          </div>
        </div>
      </div>
    </footer>
  );
};