import React, { useState, useEffect, useRef } from 'react';
import { cn } from '@/lib/utils';

export interface NavItem {
  id: string;
  label: string;
  href?: string;
  current?: boolean;
  onClick?: (e: React.MouseEvent) => void;
}

export interface UserMenuItem {
  id: string;
  label: string;
  href?: string;
  icon?: React.ReactNode;
  onClick?: (e: React.MouseEvent) => void;
}

export interface BreadcrumbItem {
  id: string;
  label: string;
  href?: string;
  current?: boolean;
}

export interface QuickAction {
  id: string;
  label: string;
  icon?: React.ReactNode;
  onClick: (e: React.MouseEvent) => void;
}

export interface Language {
  code: string;
  label: string;
}

export interface HeaderProps {
  title?: string;
  pageTitle?: string;
  logo?: React.ReactNode;
  navItems?: NavItem[];
  userMenu?: UserMenuItem[];
  breadcrumbs?: BreadcrumbItem[];
  quickActions?: QuickAction[];
  languages?: Language[];
  currentLanguage?: string;
  variant?: 'default' | 'minimal' | 'transparent';
  size?: 'sm' | 'md' | 'lg';
  theme?: 'light' | 'dark';
  sticky?: boolean;
  fixed?: boolean;
  showSearch?: boolean;
  searchPlaceholder?: string;
  showNotifications?: boolean;
  notificationCount?: number;
  showMobileMenu?: boolean;
  collapsibleNav?: boolean;
  centerContent?: boolean;
  fullWidth?: boolean;
  showBorder?: boolean;
  shadow?: boolean;
  responsive?: boolean;
  scrollBehavior?: boolean;
  loading?: boolean;
  loadingComponent?: React.ReactNode;
  userAvatar?: string;
  userName?: string;
  announcement?: string;
  actions?: React.ReactNode;
  onSearch?: (query: string) => void;
  onNotificationClick?: () => void;
  onLanguageChange?: (langCode: string) => void;
  className?: string;
  'data-testid'?: string;
  'data-category'?: string;
  'data-id'?: string;
}

export const Header: React.FC<HeaderProps> = ({
  title,
  pageTitle,
  logo,
  navItems = [],
  userMenu = [],
  breadcrumbs = [],
  quickActions = [],
  languages = [],
  currentLanguage,
  variant = 'default',
  size = 'md',
  theme = 'light',
  sticky = false,
  fixed = false,
  showSearch = false,
  searchPlaceholder = 'Search...',
  showNotifications = false,
  notificationCount = 0,
  showMobileMenu = false,
  collapsibleNav = false,
  centerContent = false,
  fullWidth = true,
  showBorder = true,
  shadow = false,
  responsive = true,
  scrollBehavior = false,
  loading = false,
  loadingComponent,
  userAvatar,
  userName,
  announcement,
  actions,
  onSearch,
  onNotificationClick,
  onLanguageChange,
  className,
  'data-testid': dataTestId = 'header-container',
  'data-category': dataCategory,
  'data-id': dataId,
  ...props
}) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [userMenuOpen, setUserMenuOpen] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [languageMenuOpen, setLanguageMenuOpen] = useState(false);
  const [scrolled, setScrolled] = useState(false);
  const headerRef = useRef<HTMLElement>(null);

  const sizeClasses = {
    sm: 'h-12 px-4 text-sm',
    md: 'h-16 px-6 text-base',
    lg: 'h-20 px-8 text-lg'
  };

  const variantClasses = {
    default: 'bg-white',
    minimal: 'bg-transparent',
    transparent: 'bg-transparent backdrop-blur-sm'
  };

  const themeClasses = {
    light: 'bg-white text-gray-900 border-gray-200',
    dark: 'bg-gray-900 text-white border-gray-700'
  };

  // Handle scroll behavior
  useEffect(() => {
    if (!scrollBehavior) return;

    const handleScroll = () => {
      setScrolled(window.scrollY > 10);
    };

    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, [scrollBehavior]);

  // Handle search
  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setSearchQuery(value);
    onSearch?.(value);
  };

  // Close dropdowns when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (headerRef.current && !headerRef.current.contains(event.target as Node)) {
        setUserMenuOpen(false);
        setLanguageMenuOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const renderNavItems = () => (
    <nav className="hidden md:flex items-center space-x-6">
      {navItems.map(item => (
        <a
          key={item.id}
          href={item.href}
          className={cn(
            'font-medium transition-colors hover:text-blue-600',
            item.current ? 'text-blue-600' : 'text-gray-700'
          )}
          onClick={item.onClick}
        >
          {item.label}
        </a>
      ))}
    </nav>
  );

  const renderUserMenu = () => (
    <div className="relative">
      <button
        data-testid="user-menu-button"
        onClick={() => setUserMenuOpen(!userMenuOpen)}
        className="flex items-center space-x-2 p-2 rounded-md hover:bg-gray-100 transition-colors"
      >
        {userAvatar ? (
          <img
            data-testid="user-avatar"
            src={userAvatar}
            alt={userName || 'User'}
            className="w-8 h-8 rounded-full"
          />
        ) : (
          <div className="w-8 h-8 bg-gray-300 rounded-full flex items-center justify-center">
            👤
          </div>
        )}
        {userName && (
          <span className="hidden sm:block text-sm font-medium">{userName}</span>
        )}
        <span className="text-gray-400">▼</span>
      </button>

      {userMenuOpen && (
        <div className="absolute right-0 mt-2 w-48 bg-white rounded-md shadow-lg py-1 z-50 border">
          {userMenu.map(item => (
            <a
              key={item.id}
              href={item.href}
              className="flex items-center px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 transition-colors"
              onClick={(e) => {
                item.onClick?.(e);
                setUserMenuOpen(false);
              }}
            >
              {item.icon && <span className="mr-3">{item.icon}</span>}
              {item.label}
            </a>
          ))}
        </div>
      )}
    </div>
  );

  const renderLanguageSelector = () => (
    <div className="relative">
      <button
        data-testid="language-selector"
        onClick={() => setLanguageMenuOpen(!languageMenuOpen)}
        className="flex items-center space-x-1 p-2 rounded-md hover:bg-gray-100 transition-colors"
      >
        <span className="text-sm">
          {languages.find(lang => lang.code === currentLanguage)?.label || 'EN'}
        </span>
        <span className="text-gray-400">▼</span>
      </button>

      {languageMenuOpen && (
        <div className="absolute right-0 mt-2 w-32 bg-white rounded-md shadow-lg py-1 z-50 border">
          {languages.map(lang => (
            <button
              key={lang.code}
              onClick={() => {
                onLanguageChange?.(lang.code);
                setLanguageMenuOpen(false);
              }}
              className={cn(
                'block w-full text-left px-4 py-2 text-sm hover:bg-gray-100 transition-colors',
                lang.code === currentLanguage ? 'text-blue-600 bg-blue-50' : 'text-gray-700'
              )}
            >
              {lang.label}
            </button>
          ))}
        </div>
      )}
    </div>
  );

  const renderBreadcrumbs = () => (
    <nav className="flex items-center space-x-2 text-sm">
      {breadcrumbs.map((item, index) => (
        <React.Fragment key={item.id}>
          {item.href && !item.current ? (
            <a
              href={item.href}
              className="text-gray-500 hover:text-gray-700 transition-colors"
            >
              {item.label}
            </a>
          ) : (
            <span className={cn(item.current ? 'text-gray-900 font-medium' : 'text-gray-500')}>
              {item.label}
            </span>
          )}
          {index < breadcrumbs.length - 1 && (
            <span className="text-gray-400">/</span>
          )}
        </React.Fragment>
      ))}
    </nav>
  );

  const renderQuickActions = () => (
    <div className="flex items-center space-x-2">
      {quickActions.map(action => (
        <button
          key={action.id}
          onClick={action.onClick}
          className="flex items-center space-x-1 px-3 py-1 text-sm bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
        >
          {action.icon && <span>{action.icon}</span>}
          <span>{action.label}</span>
        </button>
      ))}
    </div>
  );

  if (loading) {
    return (
      <header
        data-testid="header-loading"
        className={cn(
          'flex items-center justify-center',
          sizeClasses[size],
          variantClasses[variant],
          themeClasses[theme],
          showBorder && 'border-b',
          shadow && 'shadow-md',
          className
        )}
      >
        {loadingComponent || (
          <div className="flex items-center space-x-2">
            <div className="w-5 h-5 border-2 border-gray-300 border-t-blue-500 rounded-full animate-spin"></div>
            <span className="text-gray-500">Loading...</span>
          </div>
        )}
      </header>
    );
  }

  return (
    <>
      {/* Announcement Bar */}
      {announcement && (
        <div className="bg-blue-600 text-white text-center py-2 px-4 text-sm">
          {announcement}
        </div>
      )}

      {/* Main Header */}
      <header
        ref={headerRef}
        className={cn(
          'flex items-center justify-between transition-all duration-200',
          sizeClasses[size],
          variantClasses[variant],
          themeClasses[theme],
          `theme-${theme}`,
          sticky && 'sticky top-0 z-40',
          fixed && 'fixed top-0 left-0 right-0 z-40',
          showBorder && 'border-b',
          shadow && 'shadow-md',
          scrollBehavior && scrolled && 'shadow-lg',
          centerContent && 'justify-center',
          fullWidth && 'w-full',
          responsive && 'responsive-header',
          className
        )}
        data-testid={dataTestId}
        data-category={dataCategory}
        data-id={dataId}
        {...props}
      >
        {/* Left Section */}
        <div className="flex items-center space-x-4">
          {/* Mobile Menu Toggle */}
          {showMobileMenu && (
            <button
              data-testid="mobile-menu-toggle"
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="md:hidden p-2 rounded-md hover:bg-gray-100"
            >
              <span className="sr-only">Toggle menu</span>
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
              </svg>
            </button>
          )}

          {/* Logo */}
          {logo && <div className="flex-shrink-0">{logo}</div>}

          {/* Title */}
          {title && (
            <h1 className="text-xl font-bold truncate">
              {title}
            </h1>
          )}

          {/* Navigation */}
          {!centerContent && renderNavItems()}
        </div>

        {/* Center Section */}
        {centerContent && (
          <div className="flex items-center space-x-6">
            {renderNavItems()}
          </div>
        )}

        {/* Right Section */}
        <div className="flex items-center space-x-4">
          {/* Search */}
          {showSearch && (
            <div className="hidden sm:block">
              <input
                type="text"
                placeholder={searchPlaceholder}
                value={searchQuery}
                onChange={handleSearchChange}
                className="px-3 py-1 border border-gray-300 rounded-md focus:outline-none focus:ring-1 focus:ring-blue-500 text-sm"
              />
            </div>
          )}

          {/* Quick Actions */}
          {quickActions.length > 0 && renderQuickActions()}

          {/* Notifications */}
          {showNotifications && (
            <button
              data-testid="notification-button"
              onClick={onNotificationClick}
              className="relative p-2 rounded-md hover:bg-gray-100 transition-colors"
            >
              <span className="text-xl">🔔</span>
              {notificationCount > 0 && (
                <span className="absolute -top-1 -right-1 bg-red-500 text-white text-xs rounded-full min-w-[20px] h-5 flex items-center justify-center">
                  {notificationCount > 99 ? '99+' : notificationCount}
                </span>
              )}
            </button>
          )}

          {/* Language Selector */}
          {languages.length > 0 && renderLanguageSelector()}

          {/* Custom Actions */}
          {actions}

          {/* User Menu */}
          {(userMenu.length > 0 || userAvatar || userName) && renderUserMenu()}
        </div>
      </header>

      {/* Page Title & Breadcrumbs */}
      {(pageTitle || breadcrumbs.length > 0) && (
        <div className={cn(
          'bg-gray-50 border-b px-6 py-4',
          theme === 'dark' && 'bg-gray-800 border-gray-700'
        )}>
          {pageTitle && (
            <h2 className="text-2xl font-bold text-gray-900 mb-2">{pageTitle}</h2>
          )}
          {breadcrumbs.length > 0 && renderBreadcrumbs()}
        </div>
      )}

      {/* Mobile Menu */}
      {showMobileMenu && (
        <div
          data-testid="mobile-menu"
          className={cn(
            'md:hidden border-b bg-white',
            mobileMenuOpen ? 'block' : 'hidden'
          )}
        >
          <nav className="px-4 py-2 space-y-2">
            {navItems.map(item => (
              <a
                key={item.id}
                href={item.href}
                className={cn(
                  'block px-3 py-2 rounded-md text-base font-medium transition-colors',
                  item.current 
                    ? 'text-blue-600 bg-blue-50' 
                    : 'text-gray-700 hover:text-gray-900 hover:bg-gray-50'
                )}
                onClick={(e) => {
                  item.onClick?.(e);
                  setMobileMenuOpen(false);
                }}
              >
                {item.label}
              </a>
            ))}
          </nav>
        </div>
      )}
    </>
  );
};

export default Header;