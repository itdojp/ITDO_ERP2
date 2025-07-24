import React, { useState, useRef, useCallback, useEffect, useMemo } from 'react';
import { cn } from '@/lib/utils';

export interface NotificationItem {
  id: string;
  type: 'info' | 'success' | 'warning' | 'error' | 'system' | 'user' | 'reminder' | 'announcement';
  title: string;
  message: string;
  timestamp: Date;
  read: boolean;
  priority: 'low' | 'medium' | 'high' | 'urgent';
  category?: string;
  sender?: {
    id: string;
    name: string;
    avatar?: string;
    role?: string;
  };
  actions?: Array<{
    id: string;
    label: string;
    type: 'primary' | 'secondary' | 'danger';
    onClick: () => void;
  }>;
  data?: Record<string, any>;
  expiresAt?: Date;
  persistent?: boolean;
  dismissible?: boolean;
  icon?: React.ReactNode;
  image?: string;
  url?: string;
  tags?: string[];
}

export interface NotificationGroup {
  id: string;
  title: string;
  notifications: NotificationItem[];
  collapsed?: boolean;
  priority?: 'low' | 'medium' | 'high' | 'urgent';
}

export interface NotificationFilter {
  types?: NotificationItem['type'][];
  priorities?: NotificationItem['priority'][];
  categories?: string[];
  read?: boolean;
  dateRange?: {
    start: Date;
    end: Date;
  };
  sender?: string;
  tags?: string[];
}

export interface NotificationSettings {
  enabled: boolean;
  sound: boolean;
  desktop: boolean;
  email: boolean;
  push: boolean;
  frequency: 'immediate' | 'hourly' | 'daily' | 'weekly';
  quietHours: {
    enabled: boolean;
    start: string;
    end: string;
  };
  categories: Record<string, {
    enabled: boolean;
    sound: boolean;
    desktop: boolean;
    email: boolean;
  }>;
}

export interface NotificationCenterProps {
  notifications: NotificationItem[];
  groups?: NotificationGroup[];
  settings?: NotificationSettings;
  maxItems?: number;
  autoRefresh?: boolean;
  refreshInterval?: number;
  groupByDate?: boolean;
  groupByCategory?: boolean;
  groupByType?: boolean;
  groupBySender?: boolean;
  showUnreadOnly?: boolean;
  enableSearch?: boolean;
  enableFilters?: boolean;
  enableBulkActions?: boolean;
  enableSound?: boolean;
  enableDesktopNotifications?: boolean;
  theme?: 'light' | 'dark' | 'auto';
  position?: 'left' | 'right' | 'center';
  width?: number | string;
  height?: number | string;
  maxHeight?: number | string;
  className?: string;
  style?: React.CSSProperties;
  onNotificationClick?: (notification: NotificationItem) => void;
  onNotificationAction?: (notificationId: string, actionId: string) => void;
  onNotificationDismiss?: (notificationId: string) => void;
  onMarkAsRead?: (notificationId: string | string[]) => void;
  onMarkAsUnread?: (notificationId: string | string[]) => void;
  onDeleteNotification?: (notificationId: string | string[]) => void;
  onClearAll?: () => void;
  onSettingsChange?: (settings: NotificationSettings) => void;
  onRefresh?: () => void;
  onError?: (error: Error) => void;
  'data-testid'?: string;
}

export const NotificationCenter: React.FC<NotificationCenterProps> = ({
  notifications,
  groups = [],
  settings,
  maxItems = 100,
  autoRefresh = false,
  refreshInterval = 30000,
  groupByDate = false,
  groupByCategory = false,
  groupByType = false,
  groupBySender = false,
  showUnreadOnly = false,
  enableSearch = true,
  enableFilters = true,
  enableBulkActions = true,
  enableSound = true,
  enableDesktopNotifications = true,
  theme = 'light',
  position = 'right',
  width = 400,
  height = 600,
  maxHeight = '80vh',
  className,
  style,
  onNotificationClick,
  onNotificationAction,
  onNotificationDismiss,
  onMarkAsRead,
  onMarkAsUnread,
  onDeleteNotification,
  onClearAll,
  onSettingsChange,
  onRefresh,
  onError,
  'data-testid': dataTestId = 'notification-center'
}) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedFilter, setSelectedFilter] = useState<NotificationFilter>({});
  const [selectedNotifications, setSelectedNotifications] = useState<string[]>([]);
  const [showSettings, setShowSettings] = useState(false);
  const [showFilters, setShowFilters] = useState(false);
  const [internalSettings, setInternalSettings] = useState<NotificationSettings>(
    settings || {
      enabled: true,
      sound: true,
      desktop: true,
      email: false,
      push: false,
      frequency: 'immediate',
      quietHours: { enabled: false, start: '22:00', end: '08:00' },
      categories: {}
    }
  );
  const [audioContext, setAudioContext] = useState<AudioContext | null>(null);
  const [expandedGroups, setExpandedGroups] = useState<Set<string>>(new Set());
  const [sortBy, setSortBy] = useState<'timestamp' | 'priority' | 'type'>('timestamp');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');

  const centerRef = useRef<HTMLDivElement>(null);
  const refreshIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  // Notification type icons and colors
  const typeConfig = {
    info: { icon: 'ℹ️', color: 'blue', bgColor: 'bg-blue-50', borderColor: 'border-blue-200' },
    success: { icon: '✅', color: 'green', bgColor: 'bg-green-50', borderColor: 'border-green-200' },
    warning: { icon: '⚠️', color: 'yellow', bgColor: 'bg-yellow-50', borderColor: 'border-yellow-200' },
    error: { icon: '❌', color: 'red', bgColor: 'bg-red-50', borderColor: 'border-red-200' },
    system: { icon: '⚙️', color: 'gray', bgColor: 'bg-gray-50', borderColor: 'border-gray-200' },
    user: { icon: '👤', color: 'purple', bgColor: 'bg-purple-50', borderColor: 'border-purple-200' },
    reminder: { icon: '⏰', color: 'orange', bgColor: 'bg-orange-50', borderColor: 'border-orange-200' },
    announcement: { icon: '📢', color: 'indigo', bgColor: 'bg-indigo-50', borderColor: 'border-indigo-200' }
  };

  // Priority levels
  const priorityConfig = {
    low: { label: 'Low', color: 'gray', indicator: '●' },
    medium: { label: 'Medium', color: 'blue', indicator: '●●' },
    high: { label: 'High', color: 'orange', indicator: '●●●' },
    urgent: { label: 'Urgent', color: 'red', indicator: '🔴' }
  };

  // Filter and sort notifications
  const filteredNotifications = useMemo(() => {
    let filtered = [...notifications];

    // Apply search filter
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(notification =>
        notification.title.toLowerCase().includes(query) ||
        notification.message.toLowerCase().includes(query) ||
        notification.category?.toLowerCase().includes(query) ||
        notification.sender?.name.toLowerCase().includes(query)
      );
    }

    // Apply filters
    if (selectedFilter.types?.length) {
      filtered = filtered.filter(n => selectedFilter.types!.includes(n.type));
    }

    if (selectedFilter.priorities?.length) {
      filtered = filtered.filter(n => selectedFilter.priorities!.includes(n.priority));
    }

    if (selectedFilter.categories?.length) {
      filtered = filtered.filter(n => n.category && selectedFilter.categories!.includes(n.category));
    }

    if (selectedFilter.read !== undefined) {
      filtered = filtered.filter(n => n.read === selectedFilter.read);
    }

    if (selectedFilter.sender) {
      filtered = filtered.filter(n => n.sender?.id === selectedFilter.sender);
    }

    if (selectedFilter.tags?.length) {
      filtered = filtered.filter(n => 
        n.tags?.some(tag => selectedFilter.tags!.includes(tag))
      );
    }

    if (selectedFilter.dateRange) {
      filtered = filtered.filter(n => 
        n.timestamp >= selectedFilter.dateRange!.start &&
        n.timestamp <= selectedFilter.dateRange!.end
      );
    }

    // Show unread only
    if (showUnreadOnly) {
      filtered = filtered.filter(n => !n.read);
    }

    // Remove expired notifications
    const now = new Date();
    filtered = filtered.filter(n => !n.expiresAt || n.expiresAt > now);

    // Sort notifications
    filtered.sort((a, b) => {
      let comparison = 0;

      switch (sortBy) {
        case 'timestamp':
          comparison = a.timestamp.getTime() - b.timestamp.getTime();
          break;
        case 'priority':
          const priorityOrder = { urgent: 4, high: 3, medium: 2, low: 1 };
          comparison = priorityOrder[a.priority] - priorityOrder[b.priority];
          break;
        case 'type':
          comparison = a.type.localeCompare(b.type);
          break;
      }

      return sortOrder === 'desc' ? -comparison : comparison;
    });

    // Limit items
    return filtered.slice(0, maxItems);
  }, [notifications, searchQuery, selectedFilter, showUnreadOnly, sortBy, sortOrder, maxItems]);

  // Group notifications
  const groupedNotifications = useMemo(() => {
    if (!groupByDate && !groupByCategory && !groupByType && !groupBySender) {
      return { 'All Notifications': filteredNotifications };
    }

    const grouped: Record<string, NotificationItem[]> = {};

    filteredNotifications.forEach(notification => {
      let groupKey = 'Other';

      if (groupByDate) {
        const date = notification.timestamp.toDateString();
        groupKey = date === new Date().toDateString() ? 'Today' : 
                   date === new Date(Date.now() - 86400000).toDateString() ? 'Yesterday' : date;
      } else if (groupByCategory && notification.category) {
        groupKey = notification.category;
      } else if (groupByType) {
        groupKey = typeConfig[notification.type].icon + ' ' + notification.type.charAt(0).toUpperCase() + notification.type.slice(1);
      } else if (groupBySender && notification.sender) {
        groupKey = notification.sender.name;
      }

      if (!grouped[groupKey]) {
        grouped[groupKey] = [];
      }
      grouped[groupKey].push(notification);
    });

    return grouped;
  }, [filteredNotifications, groupByDate, groupByCategory, groupByType, groupBySender]);

  // Play notification sound
  const playNotificationSound = useCallback(() => {
    if (!enableSound || !internalSettings.sound) return;

    try {
      if (!audioRef.current) {
        audioRef.current = new Audio();
        audioRef.current.src = 'data:audio/wav;base64,UklGRnoGAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQoGAACBhYqFbF1fdJivrJBhNjVgodDbq2EcBj+a2/LDciUFLIHO8tiJNwgZaLvt559NEAxQp+PwtmMcBjiR1/LMeSwFJHfH8N2QQAoUXrTp66hVFApGn+DyvmIcBw==';
      }
      audioRef.current.play().catch(() => {
        // Ignore audio play errors (browser restrictions)
      });
    } catch (error) {
      console.warn('Failed to play notification sound:', error);
    }
  }, [enableSound, internalSettings.sound]);

  // Request desktop notification permission
  const requestNotificationPermission = useCallback(async () => {
    if (!enableDesktopNotifications || !internalSettings.desktop) return false;

    if ('Notification' in window) {
      if (Notification.permission === 'granted') {
        return true;
      } else if (Notification.permission !== 'denied') {
        const permission = await Notification.requestPermission();
        return permission === 'granted';
      }
    }
    return false;
  }, [enableDesktopNotifications, internalSettings.desktop]);

  // Show desktop notification
  const showDesktopNotification = useCallback(async (notification: NotificationItem) => {
    const hasPermission = await requestNotificationPermission();
    if (!hasPermission) return;

    try {
      const desktopNotification = new Notification(notification.title, {
        body: notification.message,
        icon: notification.image || typeConfig[notification.type].icon,
        tag: notification.id,
        requireInteraction: notification.priority === 'urgent',
        silent: !internalSettings.sound
      });

      desktopNotification.onclick = () => {
        window.focus();
        onNotificationClick?.(notification);
        desktopNotification.close();
      };

      // Auto-close after 5 seconds for non-urgent notifications
      if (notification.priority !== 'urgent') {
        setTimeout(() => desktopNotification.close(), 5000);
      }
    } catch (error) {
      console.warn('Failed to show desktop notification:', error);
    }
  }, [requestNotificationPermission, internalSettings.sound, onNotificationClick]);

  // Handle new notifications
  useEffect(() => {
    const newNotifications = notifications.filter(n => 
      n.timestamp.getTime() > Date.now() - 1000 && !n.read
    );

    newNotifications.forEach(notification => {
      playNotificationSound();
      showDesktopNotification(notification);
    });
  }, [notifications, playNotificationSound, showDesktopNotification]);

  // Auto-refresh
  useEffect(() => {
    if (autoRefresh) {
      refreshIntervalRef.current = setInterval(() => {
        onRefresh?.();
      }, refreshInterval);

      return () => {
        if (refreshIntervalRef.current) {
          clearInterval(refreshIntervalRef.current);
        }
      };
    }
  }, [autoRefresh, refreshInterval, onRefresh]);

  // Handle notification selection
  const handleNotificationSelect = useCallback((notificationId: string, selected: boolean) => {
    setSelectedNotifications(prev => 
      selected 
        ? [...prev, notificationId]
        : prev.filter(id => id !== notificationId)
    );
  }, []);

  // Handle select all
  const handleSelectAll = useCallback((selected: boolean) => {
    setSelectedNotifications(selected ? filteredNotifications.map(n => n.id) : []);
  }, [filteredNotifications]);

  // Handle bulk actions
  const handleBulkMarkAsRead = useCallback(() => {
    if (selectedNotifications.length > 0) {
      onMarkAsRead?.(selectedNotifications);
      setSelectedNotifications([]);
    }
  }, [selectedNotifications, onMarkAsRead]);

  const handleBulkDelete = useCallback(() => {
    if (selectedNotifications.length > 0) {
      onDeleteNotification?.(selectedNotifications);
      setSelectedNotifications([]);
    }
  }, [selectedNotifications, onDeleteNotification]);

  // Format timestamp
  const formatTimestamp = useCallback((timestamp: Date) => {
    const now = new Date();
    const diff = now.getTime() - timestamp.getTime();
    const minutes = Math.floor(diff / 60000);
    const hours = Math.floor(diff / 3600000);
    const days = Math.floor(diff / 86400000);

    if (minutes < 1) return 'Just now';
    if (minutes < 60) return `${minutes}m ago`;
    if (hours < 24) return `${hours}h ago`;
    if (days < 7) return `${days}d ago`;
    return timestamp.toLocaleDateString();
  }, []);

  // Render notification item
  const renderNotification = useCallback((notification: NotificationItem) => {
    const config = typeConfig[notification.type];
    const priorityInfo = priorityConfig[notification.priority];
    const isSelected = selectedNotifications.includes(notification.id);

    return (
      <div
        key={notification.id}
        className={cn(
          "relative p-3 border-l-4 hover:bg-gray-50 transition-colors",
          config.bgColor,
          config.borderColor,
          !notification.read && "bg-opacity-100",
          notification.read && "bg-opacity-30",
          isSelected && "ring-2 ring-blue-500"
        )}
        data-testid={`notification-${notification.id}`}
      >
        <div className="flex items-start space-x-3">
          {enableBulkActions && (
            <input
              type="checkbox"
              checked={isSelected}
              onChange={(e) => handleNotificationSelect(notification.id, e.target.checked)}
              className="mt-1"
              data-testid={`notification-checkbox-${notification.id}`}
            />
          )}

          <div className="flex-shrink-0">
            <div className="w-8 h-8 rounded-full bg-white shadow-sm flex items-center justify-center">
              {notification.icon || config.icon}
            </div>
          </div>

          <div className="flex-1 min-w-0">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <h4 className={cn(
                  "text-sm font-medium",
                  !notification.read && "font-semibold"
                )}>
                  {notification.title}
                </h4>
                {notification.priority !== 'low' && (
                  <span className={cn(
                    "text-xs px-1.5 py-0.5 rounded-full",
                    `text-${priorityInfo.color}-600 bg-${priorityInfo.color}-100`
                  )}>
                    {priorityInfo.label}
                  </span>
                )}
              </div>
              <div className="flex items-center space-x-2">
                <span className="text-xs text-gray-500">
                  {formatTimestamp(notification.timestamp)}
                </span>
                {!notification.read && (
                  <div className="w-2 h-2 bg-blue-500 rounded-full" data-testid="unread-indicator" />
                )}
              </div>
            </div>

            <p className="mt-1 text-sm text-gray-600 line-clamp-2">
              {notification.message}
            </p>

            {notification.sender && (
              <div className="mt-1 flex items-center space-x-1 text-xs text-gray-500">
                <span>From:</span>
                <span className="font-medium">{notification.sender.name}</span>
                {notification.sender.role && (
                  <span className="text-gray-400">({notification.sender.role})</span>
                )}
              </div>
            )}

            {notification.category && (
              <div className="mt-1">
                <span className="inline-block px-2 py-1 text-xs bg-gray-100 text-gray-600 rounded">
                  {notification.category}
                </span>
              </div>
            )}

            {notification.tags && notification.tags.length > 0 && (
              <div className="mt-1 flex flex-wrap gap-1">
                {notification.tags.map(tag => (
                  <span
                    key={tag}
                    className="inline-block px-1.5 py-0.5 text-xs bg-gray-200 text-gray-600 rounded"
                  >
                    #{tag}
                  </span>
                ))}
              </div>
            )}

            {notification.actions && notification.actions.length > 0 && (
              <div className="mt-2 flex space-x-2">
                {notification.actions.map(action => (
                  <button
                    key={action.id}
                    className={cn(
                      "px-3 py-1 text-xs rounded border transition-colors",
                      action.type === 'primary' && "bg-blue-500 text-white border-blue-500 hover:bg-blue-600",
                      action.type === 'secondary' && "bg-white text-gray-700 border-gray-300 hover:bg-gray-50",
                      action.type === 'danger' && "bg-red-500 text-white border-red-500 hover:bg-red-600"
                    )}
                    onClick={() => onNotificationAction?.(notification.id, action.id)}
                    data-testid={`notification-action-${notification.id}-${action.id}`}
                  >
                    {action.label}
                  </button>
                ))}
              </div>
            )}

            <div className="mt-2 flex items-center justify-between">
              <div className="flex space-x-2">
                <button
                  className="text-xs text-blue-600 hover:text-blue-800"
                  onClick={() => onNotificationClick?.(notification)}
                  data-testid={`notification-click-${notification.id}`}
                >
                  View
                </button>
                {!notification.read && (
                  <button
                    className="text-xs text-green-600 hover:text-green-800"
                    onClick={() => onMarkAsRead?.(notification.id)}
                    data-testid={`mark-read-${notification.id}`}
                  >
                    Mark as read
                  </button>
                )}
                {notification.read && (
                  <button
                    className="text-xs text-gray-600 hover:text-gray-800"
                    onClick={() => onMarkAsUnread?.(notification.id)}
                    data-testid={`mark-unread-${notification.id}`}
                  >
                    Mark as unread
                  </button>
                )}
              </div>
              {notification.dismissible !== false && (
                <button
                  className="text-xs text-red-600 hover:text-red-800"
                  onClick={() => onNotificationDismiss?.(notification.id)}
                  data-testid={`dismiss-${notification.id}`}
                >
                  Dismiss
                </button>
              )}
            </div>
          </div>
        </div>
      </div>
    );
  }, [selectedNotifications, enableBulkActions, handleNotificationSelect, formatTimestamp, onNotificationClick, onNotificationAction, onMarkAsRead, onMarkAsUnread, onNotificationDismiss]);

  // Render header
  const renderHeader = () => (
    <div className="p-4 border-b border-gray-200 bg-white" data-testid="notification-header">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold">Notifications</h2>
        <div className="flex items-center space-x-2">
          {notifications.filter(n => !n.read).length > 0 && (
            <span className="px-2 py-1 text-xs bg-blue-100 text-blue-800 rounded-full">
              {notifications.filter(n => !n.read).length} new
            </span>
          )}
          <button
            className="p-1 hover:bg-gray-100 rounded"
            onClick={() => setShowSettings(!showSettings)}
            data-testid="settings-toggle"
          >
            ⚙️
          </button>
          <button
            className="p-1 hover:bg-gray-100 rounded"
            onClick={() => onRefresh?.()}
            data-testid="refresh-button"
          >
            🔄
          </button>
        </div>
      </div>

      {enableSearch && (
        <div className="mt-3">
          <input
            type="text"
            placeholder="Search notifications..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            data-testid="search-input"
          />
        </div>
      )}

      {enableFilters && (
        <div className="mt-3 flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <button
              className={cn(
                "px-3 py-1 text-xs rounded border transition-colors",
                showUnreadOnly
                  ? "bg-blue-500 text-white border-blue-500"
                  : "bg-white text-gray-700 border-gray-300 hover:bg-gray-50"
              )}
              onClick={() => setShowUnreadOnly(!showUnreadOnly)}
              data-testid="unread-only-toggle"
            >
              Unread only
            </button>
            <button
              className="px-3 py-1 text-xs bg-white text-gray-700 border border-gray-300 rounded hover:bg-gray-50"
              onClick={() => setShowFilters(!showFilters)}
              data-testid="filters-toggle"
            >
              Filters
            </button>
          </div>

          <div className="flex items-center space-x-2">
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value as any)}
              className="text-xs border border-gray-300 rounded px-2 py-1"
              data-testid="sort-by-select"
            >
              <option value="timestamp">Time</option>
              <option value="priority">Priority</option>
              <option value="type">Type</option>
            </select>
            <button
              className="text-xs px-2 py-1 border border-gray-300 rounded hover:bg-gray-50"
              onClick={() => setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc')}
              data-testid="sort-order-toggle"
            >
              {sortOrder === 'desc' ? '↓' : '↑'}
            </button>
          </div>
        </div>
      )}

      {enableBulkActions && selectedNotifications.length > 0 && (
        <div className="mt-3 p-2 bg-blue-50 rounded-md" data-testid="bulk-actions">
          <div className="flex items-center justify-between">
            <span className="text-sm text-blue-800">
              {selectedNotifications.length} selected
            </span>
            <div className="flex space-x-2">
              <button
                className="px-2 py-1 text-xs bg-blue-500 text-white rounded hover:bg-blue-600"
                onClick={handleBulkMarkAsRead}
                data-testid="bulk-mark-read"
              >
                Mark as read
              </button>
              <button
                className="px-2 py-1 text-xs bg-red-500 text-white rounded hover:bg-red-600"
                onClick={handleBulkDelete}
                data-testid="bulk-delete"
              >
                Delete
              </button>
            </div>
          </div>
        </div>
      )}

      {enableBulkActions && filteredNotifications.length > 0 && (
        <div className="mt-2">
          <label className="flex items-center text-sm">
            <input
              type="checkbox"
              checked={selectedNotifications.length === filteredNotifications.length}
              onChange={(e) => handleSelectAll(e.target.checked)}
              className="mr-2"
              data-testid="select-all-checkbox"
            />
            Select all
          </label>
        </div>
      )}
    </div>
  );

  // Render notifications list
  const renderNotificationsList = () => {
    if (filteredNotifications.length === 0) {
      return (
        <div className="flex flex-col items-center justify-center h-48 text-gray-500" data-testid="empty-state">
          <div className="text-4xl mb-2">🔔</div>
          <div className="text-sm">No notifications</div>
          <div className="text-xs mt-1">You're all caught up!</div>
        </div>
      );
    }

    return (
      <div className="divide-y divide-gray-200" data-testid="notifications-list">
        {Object.entries(groupedNotifications).map(([groupTitle, groupNotifications]) => (
          <div key={groupTitle}>
            {Object.keys(groupedNotifications).length > 1 && (
              <div
                className="px-4 py-2 bg-gray-50 text-sm font-medium text-gray-700 cursor-pointer hover:bg-gray-100"
                onClick={() => {
                  const newExpanded = new Set(expandedGroups);
                  if (newExpanded.has(groupTitle)) {
                    newExpanded.delete(groupTitle);
                  } else {
                    newExpanded.add(groupTitle);
                  }
                  setExpandedGroups(newExpanded);
                }}
                data-testid={`group-header-${groupTitle}`}
              >
                <div className="flex items-center justify-between">
                  <span>{groupTitle}</span>
                  <div className="flex items-center space-x-2">
                    <span className="text-xs text-gray-500">
                      {groupNotifications.length} notification{groupNotifications.length !== 1 ? 's' : ''}
                    </span>
                    <span className="text-xs">
                      {expandedGroups.has(groupTitle) ? '▼' : '▶'}
                    </span>
                  </div>
                </div>
              </div>
            )}
            {(Object.keys(groupedNotifications).length === 1 || expandedGroups.has(groupTitle)) && (
              <div>
                {groupNotifications.map(renderNotification)}
              </div>
            )}
          </div>
        ))}
      </div>
    );
  };

  return (
    <div
      ref={centerRef}
      className={cn(
        "bg-white border border-gray-200 rounded-lg shadow-lg overflow-hidden",
        theme === 'dark' && "bg-gray-900 border-gray-700",
        className
      )}
      style={{ width, height, maxHeight, ...style }}
      data-testid={dataTestId}
    >
      {renderHeader()}
      
      <div className="flex-1 overflow-y-auto">
        {renderNotificationsList()}
      </div>

      {notifications.length > maxItems && (
        <div className="p-3 text-center text-sm text-gray-500 border-t border-gray-200">
          Showing {Math.min(filteredNotifications.length, maxItems)} of {notifications.length} notifications
        </div>
      )}

      {filteredNotifications.length > 0 && (
        <div className="p-3 border-t border-gray-200">
          <button
            className="w-full px-3 py-2 text-sm text-gray-600 hover:text-gray-800 hover:bg-gray-50 rounded"
            onClick={onClearAll}
            data-testid="clear-all-button"
          >
            Clear all notifications
          </button>
        </div>
      )}
    </div>
  );
};

export default NotificationCenter;