import React from 'react';
import { SearchBar } from './SearchBar';
import { NotificationBell } from './NotificationBell';

interface HeaderProps {
  onMenuClick: () => void;
}

export const Header: React.FC<HeaderProps> = ({ onMenuClick }) => {
  return (
    <header className="bg-white shadow-sm border-b border-gray-200">
      <div className="flex items-center justify-between px-6 py-4">
        <div className="flex items-center">
          <button
            onClick={onMenuClick}
            className="p-2 rounded-md text-gray-600 hover:bg-gray-100"
          >
            <span className="text-xl">☰</span>
          </button>
          <div className="ml-4">
            <h1 className="text-lg font-semibold text-gray-900">ITDO ERP System</h1>
          </div>
        </div>

        <div className="flex items-center space-x-4">
          <SearchBar />
          <NotificationBell />
          <div className="flex items-center">
            <img
              className="h-8 w-8 rounded-full"
              src="https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=facearea&facepad=2&w=256&h=256&q=80"
              alt="User avatar"
            />
            <span className="ml-2 text-sm font-medium text-gray-700">山田太郎</span>
          </div>
        </div>
      </div>
    </header>
  );
};