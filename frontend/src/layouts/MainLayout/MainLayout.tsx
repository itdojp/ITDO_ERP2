import React, { useState, useEffect } from 'react';
import { Outlet, Navigate } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';
import { Header } from '../../components/Navigation/Header';
import { Sidebar } from '../../components/Navigation/Sidebar';
import { Breadcrumb } from '../../components/Navigation/Breadcrumb';
import { LoadingSpinner } from '../../components/ui/LoadingSpinner';
import { theme } from '../../styles/theme';

interface MainLayoutProps {
  children?: React.ReactNode;
}

export const MainLayout: React.FC<MainLayoutProps> = ({ children }) => {
  const { isAuthenticated, isLoading } = useAuth();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  
  // 画面サイズに応じてサイドバーの初期状態を設定
  useEffect(() => {
    const handleResize = () => {
      if (window.innerWidth >= 1024) { // lg breakpoint
        setSidebarOpen(false);
      }
    };
    
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  // 認証状態の確認中はローディング画面を表示
  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <LoadingSpinner size="lg" className="mx-auto mb-4" />
          <p className="text-gray-600">システムを初期化しています...</p>
        </div>
      </div>
    );
  }

  // 未認証の場合はログインページにリダイレクト
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return (
    <div className="h-screen flex overflow-hidden bg-gray-50">
      {/* サイドバー */}
      <Sidebar 
        isOpen={sidebarOpen} 
        onClose={() => setSidebarOpen(false)} 
      />

      {/* メインコンテンツエリア */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* ヘッダー */}
        <Header 
          onMenuToggle={() => setSidebarOpen(!sidebarOpen)}
          isMobileMenuOpen={sidebarOpen}
        />

        {/* メインコンテンツ */}
        <main className="flex-1 overflow-y-auto focus:outline-none">
          <div className="py-6">
            <div className="max-w-full mx-auto px-4 sm:px-6 md:px-8">
              {/* パンくずリスト */}
              <div className="mb-6">
                <Breadcrumb />
              </div>

              {/* ページコンテンツ */}
              <div className="space-y-6">
                {children || <Outlet />}
              </div>
            </div>
          </div>
        </main>

        {/* フッター（オプション） */}
        <footer className="flex-shrink-0 bg-white border-t border-gray-200 px-4 py-4">
          <div className="max-w-full mx-auto sm:px-6 md:px-8">
            <div className="flex items-center justify-between text-sm text-gray-500">
              <div>
                <p>© 2024 ITDO Corporation. All rights reserved.</p>
              </div>
              <div className="flex items-center space-x-4">
                <span>Version 2.0.0</span>
                <div className="flex items-center">
                  <div className="h-2 w-2 bg-green-500 rounded-full mr-2"></div>
                  <span>システム稼働中</span>
                </div>
              </div>
            </div>
          </div>
        </footer>
      </div>

      {/* キーボードナビゲーション用のスキップリンク */}
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:absolute focus:top-0 focus:left-0 bg-blue-600 text-white px-4 py-2 z-50"
      >
        メインコンテンツにスキップ
      </a>
    </div>
  );
};

// レスポンシブ対応のコンテナコンポーネント
interface PageContainerProps {
  children: React.ReactNode;
  title?: string;
  subtitle?: string;
  actions?: React.ReactNode;
  breadcrumbItems?: Array<{ label: string; path?: string }>;
  className?: string;
}

export const PageContainer: React.FC<PageContainerProps> = ({
  children,
  title,
  subtitle,
  actions,
  breadcrumbItems,
  className = '',
}) => {
  return (
    <div className={`space-y-6 ${className}`} id="main-content">
      {/* カスタムパンくずリスト */}
      {breadcrumbItems && (
        <Breadcrumb items={breadcrumbItems} />
      )}

      {/* ページヘッダー */}
      {(title || subtitle || actions) && (
        <div className="bg-white shadow rounded-lg">
          <div className="px-6 py-4">
            <div className="flex items-center justify-between">
              <div>
                {title && (
                  <h1 className="text-2xl font-bold text-gray-900 mb-1">
                    {title}
                  </h1>
                )}
                {subtitle && (
                  <p className="text-gray-600">
                    {subtitle}
                  </p>
                )}
              </div>
              {actions && (
                <div className="flex items-center space-x-3">
                  {actions}
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* ページコンテンツ */}
      <div>
        {children}
      </div>
    </div>
  );
};

// カードレイアウトコンポーネント
interface CardLayoutProps {
  children: React.ReactNode;
  className?: string;
  padding?: 'none' | 'sm' | 'md' | 'lg';
  shadow?: 'none' | 'sm' | 'md' | 'lg';
}

export const CardLayout: React.FC<CardLayoutProps> = ({
  children,
  className = '',
  padding = 'md',
  shadow = 'md',
}) => {
  const paddingClasses = {
    none: '',
    sm: 'p-4',
    md: 'p-6',
    lg: 'p-8',
  };

  const shadowClasses = {
    none: '',
    sm: 'shadow-sm',
    md: 'shadow',
    lg: 'shadow-lg',
  };

  return (
    <div className={`bg-white rounded-lg ${shadowClasses[shadow]} ${paddingClasses[padding]} ${className}`}>
      {children}
    </div>
  );
};

// グリッドレイアウトコンポーネント
interface GridLayoutProps {
  children: React.ReactNode;
  cols?: {
    default?: number;
    sm?: number;
    md?: number;
    lg?: number;
    xl?: number;
  };
  gap?: 'sm' | 'md' | 'lg' | 'xl';
  className?: string;
}

export const GridLayout: React.FC<GridLayoutProps> = ({
  children,
  cols = { default: 1, md: 2, lg: 3 },
  gap = 'md',
  className = '',
}) => {
  const gapClasses = {
    sm: 'gap-4',
    md: 'gap-6',
    lg: 'gap-8',
    xl: 'gap-12',
  };

  const colsClasses = {
    1: 'grid-cols-1',
    2: 'grid-cols-2', 
    3: 'grid-cols-3',
    4: 'grid-cols-4',
    5: 'grid-cols-5',
    6: 'grid-cols-6',
  };

  const getColsClass = () => {
    const classes: string[] = [];
    
    if (cols.default) classes.push(colsClasses[cols.default as keyof typeof colsClasses]);
    if (cols.sm) classes.push(`sm:${colsClasses[cols.sm as keyof typeof colsClasses]}`);
    if (cols.md) classes.push(`md:${colsClasses[cols.md as keyof typeof colsClasses]}`);
    if (cols.lg) classes.push(`lg:${colsClasses[cols.lg as keyof typeof colsClasses]}`);
    if (cols.xl) classes.push(`xl:${colsClasses[cols.xl as keyof typeof colsClasses]}`);

    return classes.join(' ');
  };

  return (
    <div className={`grid ${getColsClass()} ${gapClasses[gap]} ${className}`}>
      {children}
    </div>
  );
};