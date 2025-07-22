import React from 'react';
import { NavLink } from './NavLink';

interface SidebarProps {
  isOpen: boolean;
  onToggle: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ isOpen }) => {
  const menuItems = [
    { icon: '📊', label: 'ダッシュボード', path: '/dashboard' },
    { icon: '👥', label: 'ユーザー管理', path: '/users' },
    { icon: '🏢', label: '組織管理', path: '/organizations' },
    { icon: '📦', label: '商品管理', path: '/products' },
    { icon: '📋', label: '在庫管理', path: '/inventory' },
    { icon: '💰', label: '販売管理', path: '/sales' },
    { icon: '🛒', label: '購買管理', path: '/purchases' },
    { icon: '📈', label: 'レポート', path: '/reports' },
    { icon: '⚙️', label: '設定', path: '/settings' },
  ];

  return (
    <aside className={`fixed left-0 top-0 h-full bg-gray-900 text-white transition-all duration-300 ${isOpen ? 'w-64' : 'w-16'}`}>
      <div className="p-4">
        <h1 className={`text-xl font-bold ${isOpen ? 'block' : 'hidden'}`}>ITDO ERP</h1>
      </div>
      <nav className="mt-8">
        {menuItems.map((item) => (
          <NavLink key={item.path} {...item} showLabel={isOpen} />
        ))}
      </nav>
    </aside>
  );
};