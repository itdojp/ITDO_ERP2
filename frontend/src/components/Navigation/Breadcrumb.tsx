import React from 'react';
import { Link, useLocation } from 'react-router-dom';

export interface BreadcrumbItem {
  label: string;
  path?: string;
  icon?: React.ReactNode;
}

interface BreadcrumbProps {
  items?: BreadcrumbItem[];
  className?: string;
}

// ルートパスと表示名のマッピング
const routeLabels: Record<string, string> = {
  '/dashboard': 'ダッシュボード',
  '/users': 'ユーザー管理',
  '/users/create': 'ユーザー作成',
  '/users/roles': 'ロール管理',
  '/organizations': '組織管理',
  '/organizations/departments': '部署管理',
  '/products': '商品管理',
  '/products/categories': 'カテゴリ管理',
  '/products/inventory': '在庫管理',
  '/orders': '受注管理',
  '/reports': 'レポート',
  '/reports/sales': '売上レポート',
  '/reports/inventory': '在庫レポート',
  '/settings': '設定',
  '/profile': 'プロフィール',
};

// パスからアイコンを取得
const getPathIcon = (path: string): React.ReactNode => {
  if (path === '/dashboard') {
    return (
      <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2H5a2 2 0 00-2-2z" />
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 5a2 2 0 012-2h4a2 2 0 012 2v6H8V5z" />
      </svg>
    );
  }
  if (path.startsWith('/users')) {
    return (
      <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197m13.5-9a2.5 2.5 0 11-5 0 2.5 2.5 0 015 0z" />
      </svg>
    );
  }
  if (path.startsWith('/organizations')) {
    return (
      <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5" />
      </svg>
    );
  }
  if (path.startsWith('/products')) {
    return (
      <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
      </svg>
    );
  }
  if (path.startsWith('/orders')) {
    return (
      <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v10a2 2 0 002 2h8a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01" />
      </svg>
    );
  }
  if (path.startsWith('/reports')) {
    return (
      <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
      </svg>
    );
  }
  if (path.startsWith('/settings')) {
    return (
      <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
      </svg>
    );
  }
  
  return null;
};

export const Breadcrumb: React.FC<BreadcrumbProps> = ({ 
  items, 
  className = '' 
}) => {
  const location = useLocation();
  
  // 自動的にパンくずリストを生成（カスタムitemsが提供されていない場合）
  const generateBreadcrumbs = (): BreadcrumbItem[] => {
    const pathnames = location.pathname.split('/').filter(x => x);
    const breadcrumbs: BreadcrumbItem[] = [];
    
    // ホーム（ダッシュボード）を追加
    if (location.pathname !== '/dashboard') {
      breadcrumbs.push({
        label: 'ホーム',
        path: '/dashboard',
        icon: (
          <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
          </svg>
        ),
      });
    }
    
    // 現在のパスに基づいてパンくずリストを構築
    let currentPath = '';
    pathnames.forEach((pathname, index) => {
      currentPath += `/${pathname}`;
      const isLast = index === pathnames.length - 1;
      
      // ダイナミックセグメント（IDなど）の処理
      let label = routeLabels[currentPath];
      if (!label) {
        // IDや特殊なパラメータの場合
        if (/^\d+$/.test(pathname)) {
          label = `#${pathname}`;
        } else if (pathname === 'create') {
          label = '新規作成';
        } else if (pathname === 'edit') {
          label = '編集';
        } else {
          // フォールバック: パスのセグメントをそのまま使用
          label = pathname.charAt(0).toUpperCase() + pathname.slice(1);
        }
      }
      
      breadcrumbs.push({
        label,
        path: isLast ? undefined : currentPath, // 最後のアイテムはリンクなし
        icon: isLast ? getPathIcon(currentPath) : undefined,
      });
    });
    
    return breadcrumbs;
  };
  
  const breadcrumbItems = items || generateBreadcrumbs();
  
  if (breadcrumbItems.length === 0) {
    return null;
  }
  
  return (
    <nav className={`flex ${className}`} aria-label="パンくずリスト">
      <ol className="flex items-center space-x-2 text-sm">
        {breadcrumbItems.map((item, index) => {
          const isLast = index === breadcrumbItems.length - 1;
          
          return (
            <li key={index} className="flex items-center">
              {index > 0 && (
                <svg
                  className="flex-shrink-0 h-4 w-4 text-gray-400 mx-2"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M9 5l7 7-7 7"
                  />
                </svg>
              )}
              
              <div className="flex items-center">
                {item.icon && (
                  <span className={`mr-2 ${isLast ? 'text-blue-600' : 'text-gray-500'}`}>
                    {item.icon}
                  </span>
                )}
                
                {item.path && !isLast ? (
                  <Link
                    to={item.path}
                    className="text-gray-500 hover:text-gray-700 font-medium transition-colors duration-150 ease-in-out"
                  >
                    {item.label}
                  </Link>
                ) : (
                  <span
                    className={`font-medium ${
                      isLast 
                        ? 'text-gray-900' 
                        : 'text-gray-500'
                    }`}
                  >
                    {item.label}
                  </span>
                )}
              </div>
            </li>
          );
        })}
      </ol>
    </nav>
  );
};