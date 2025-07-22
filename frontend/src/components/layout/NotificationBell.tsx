import React, { useState } from 'react';

export const NotificationBell: React.FC = () => {
  const [hasNotifications] = useState(true);
  const [showDropdown, setShowDropdown] = useState(false);

  const notifications = [
    { id: 1, message: '新しい注文が入りました', time: '5分前' },
    { id: 2, message: '在庫が少なくなっています', time: '1時間前' },
    { id: 3, message: '月次レポートが準備できました', time: '3時間前' },
  ];

  return (
    <div className="relative">
      <button
        onClick={() => setShowDropdown(!showDropdown)}
        className="relative p-2 text-gray-600 hover:bg-gray-100 rounded-lg"
      >
        <span className="text-xl">🔔</span>
        {hasNotifications && (
          <span className="absolute top-0 right-0 inline-flex items-center justify-center px-2 py-1 text-xs font-bold leading-none text-white transform translate-x-1/2 -translate-y-1/2 bg-red-500 rounded-full">
            3
          </span>
        )}
      </button>

      {showDropdown && (
        <div className="absolute right-0 mt-2 w-80 bg-white rounded-lg shadow-lg border border-gray-200 z-50">
          <div className="p-4 border-b border-gray-200">
            <h3 className="text-lg font-semibold">通知</h3>
          </div>
          <div className="max-h-96 overflow-y-auto">
            {notifications.map((notification) => (
              <div key={notification.id} className="p-4 border-b border-gray-100 hover:bg-gray-50">
                <p className="text-sm text-gray-900">{notification.message}</p>
                <p className="text-xs text-gray-500 mt-1">{notification.time}</p>
              </div>
            ))}
          </div>
          <div className="p-4 border-t border-gray-200">
            <button className="w-full text-center text-sm text-blue-600 hover:text-blue-800">
              すべての通知を見る
            </button>
          </div>
        </div>
      )}
    </div>
  );
};