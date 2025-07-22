import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { Button } from '../../components/ui/Button';
import { Badge } from '../../components/ui/Badge';
import { LoadingSpinner } from '../../components/ui/LoadingSpinner';
import { Alert } from '../../components/ui/Alert';
import { PageContainer, CardLayout } from '../../layouts/MainLayout/MainLayout';
import { useAuth } from '../../hooks/useAuth';

interface User {
  id: string;
  username: string;
  email: string;
  firstName: string;
  lastName: string;
  roles: string[];
  department: string;
  position?: string;
  phoneNumber?: string;
  status: 'active' | 'inactive' | 'pending';
  lastLoginAt?: string;
  createdAt: string;
  updatedAt: string;
  avatar?: string;
  bio?: string;
  permissions: string[];
}

interface UserActivity {
  id: string;
  type: 'login' | 'logout' | 'update' | 'create' | 'delete';
  description: string;
  timestamp: string;
  ipAddress?: string;
  userAgent?: string;
}

export const UserDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { hasPermission } = useAuth();
  
  const [user, setUser] = useState<User | null>(null);
  const [activities, setActivities] = useState<UserActivity[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [deleteLoading, setDeleteLoading] = useState(false);

  // ユーザーデータの読み込み（モック）
  useEffect(() => {
    const fetchUser = async () => {
      try {
        setLoading(true);
        
        // モックAPI呼び出し
        await new Promise(resolve => setTimeout(resolve, 1000));
        
        if (id === 'not-found') {
          throw new Error('ユーザーが見つかりません');
        }
        
        // モックユーザーデータ
        const mockUser: User = {
          id: id || 'user-1',
          username: `user${id}`,
          email: `user${id}@example.com`,
          firstName: '太郎',
          lastName: '田中',
          roles: ['manager', 'user'],
          department: '開発部',
          position: 'シニアエンジニア',
          phoneNumber: '03-1234-5678',
          status: 'active',
          lastLoginAt: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
          createdAt: new Date(Date.now() - 365 * 24 * 60 * 60 * 1000).toISOString(),
          updatedAt: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString(),
          bio: 'フルスタックエンジニアとして5年の経験があります。React、Node.js、Pythonを得意としています。',
          permissions: ['users.read', 'projects.read', 'projects.create', 'reports.read'],
        };

        // モック活動履歴
        const mockActivities: UserActivity[] = [
          {
            id: '1',
            type: 'login',
            description: 'ログイン',
            timestamp: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
            ipAddress: '192.168.1.100',
            userAgent: 'Chrome/120.0.0.0',
          },
          {
            id: '2',
            type: 'update',
            description: 'プロフィール情報を更新',
            timestamp: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString(),
            ipAddress: '192.168.1.100',
          },
          {
            id: '3',
            type: 'create',
            description: 'プロジェクト「新システム開発」を作成',
            timestamp: new Date(Date.now() - 14 * 24 * 60 * 60 * 1000).toISOString(),
          },
          {
            id: '4',
            type: 'login',
            description: 'ログイン',
            timestamp: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString(),
            ipAddress: '192.168.1.100',
          },
        ];

        setUser(mockUser);
        setActivities(mockActivities);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'エラーが発生しました');
      } finally {
        setLoading(false);
      }
    };

    if (id) {
      fetchUser();
    }
  }, [id]);

  // ユーザー削除処理
  const handleDelete = async () => {
    if (!user) return;
    
    const confirmed = window.confirm(
      `ユーザー「${user.lastName} ${user.firstName}」を削除しますか？\nこの操作は取り消せません。`
    );
    
    if (confirmed) {
      try {
        setDeleteLoading(true);
        
        // モックAPI呼び出し
        await new Promise(resolve => setTimeout(resolve, 1500));
        
        navigate('/users', { 
          state: { message: 'ユーザーが削除されました' }
        });
      } catch (err) {
        setError('削除に失敗しました');
      } finally {
        setDeleteLoading(false);
      }
    }
  };

  // ステータス切り替え
  const handleStatusToggle = async () => {
    if (!user) return;
    
    const newStatus = user.status === 'active' ? 'inactive' : 'active';
    const actionText = newStatus === 'active' ? '有効化' : '無効化';
    
    if (window.confirm(`ユーザーを${actionText}しますか？`)) {
      try {
        // モックAPI呼び出し
        await new Promise(resolve => setTimeout(resolve, 500));
        
        setUser(prev => prev ? { ...prev, status: newStatus } : null);
      } catch (err) {
        setError(`${actionText}に失敗しました`);
      }
    }
  };

  // 日時フォーマット
  const formatDateTime = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleString('ja-JP');
  };

  // 相対時間フォーマット
  const formatRelativeTime = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMinutes = Math.floor(diffMs / (1000 * 60));
    const diffHours = Math.floor(diffMinutes / 60);
    const diffDays = Math.floor(diffHours / 24);
    
    if (diffMinutes < 60) return `${diffMinutes}分前`;
    if (diffHours < 24) return `${diffHours}時間前`;
    if (diffDays < 30) return `${diffDays}日前`;
    
    return formatDateTime(dateString);
  };

  // ステータスバッジ
  const renderStatusBadge = (status: User['status']) => {
    const config = {
      active: { label: 'アクティブ', variant: 'success' as const },
      inactive: { label: '無効', variant: 'error' as const },
      pending: { label: '保留中', variant: 'warning' as const },
    };
    
    const { label, variant } = config[status];
    return <Badge variant={variant}>{label}</Badge>;
  };

  // アクティビティアイコン
  const getActivityIcon = (type: UserActivity['type']) => {
    const iconClass = "h-4 w-4";
    
    switch (type) {
      case 'login':
        return (
          <svg className={`${iconClass} text-green-500`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 16l-4-4m0 0l4-4m-4 4h14m-5 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h7a3 3 0 013 3v1" />
          </svg>
        );
      case 'logout':
        return (
          <svg className={`${iconClass} text-gray-500`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h7a3 3 0 013 3v1" />
          </svg>
        );
      case 'update':
        return (
          <svg className={`${iconClass} text-blue-500`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
          </svg>
        );
      case 'create':
        return (
          <svg className={`${iconClass} text-green-500`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
          </svg>
        );
      case 'delete':
        return (
          <svg className={`${iconClass} text-red-500`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
          </svg>
        );
      default:
        return (
          <svg className={`${iconClass} text-gray-500`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        );
    }
  };

  if (loading) {
    return (
      <PageContainer>
        <div className="flex items-center justify-center py-12">
          <LoadingSpinner size="lg" />
          <span className="ml-3 text-gray-600">ユーザー情報を読み込んでいます...</span>
        </div>
      </PageContainer>
    );
  }

  if (error || !user) {
    return (
      <PageContainer>
        <Alert variant="error" title="エラー">
          {error || 'ユーザーが見つかりません'}
        </Alert>
        <div className="mt-4">
          <Button variant="ghost" onClick={() => navigate('/users')}>
            ← ユーザー一覧に戻る
          </Button>
        </div>
      </PageContainer>
    );
  }

  return (
    <PageContainer
      title={`${user.lastName} ${user.firstName}`}
      subtitle={user.position || user.department}
      actions={
        <div className="flex items-center space-x-3">
          {hasPermission('users.edit') && (
            <Button variant="ghost" onClick={handleStatusToggle}>
              {user.status === 'active' ? '無効化' : '有効化'}
            </Button>
          )}
          {hasPermission('users.edit') && (
            <Button variant="ghost" asChild>
              <Link to={`/users/${user.id}/edit`}>
                <svg className="h-4 w-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                </svg>
                編集
              </Link>
            </Button>
          )}
          {hasPermission('users.delete') && (
            <Button 
              variant="ghost" 
              onClick={handleDelete}
              disabled={deleteLoading}
              className="text-red-600 hover:text-red-700"
            >
              {deleteLoading ? (
                <>
                  <LoadingSpinner size="sm" className="mr-2" />
                  削除中...
                </>
              ) : (
                <>
                  <svg className="h-4 w-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                  </svg>
                  削除
                </>
              )}
            </Button>
          )}
        </div>
      }
    >
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* 左側: プロフィール情報 */}
        <div className="lg:col-span-2 space-y-6">
          {/* 基本情報 */}
          <CardLayout>
            <div className="flex items-start space-x-6">
              {/* アバター */}
              <div className="flex-shrink-0">
                <div className="h-24 w-24 bg-gray-300 rounded-full flex items-center justify-center">
                  {user.avatar ? (
                    <img
                      src={user.avatar}
                      alt={`${user.firstName} ${user.lastName}`}
                      className="h-24 w-24 rounded-full"
                    />
                  ) : (
                    <span className="text-2xl font-medium text-gray-700">
                      {user.firstName[0]}{user.lastName[0]}
                    </span>
                  )}
                </div>
              </div>

              {/* 基本情報 */}
              <div className="flex-1 space-y-4">
                <div>
                  <div className="flex items-center space-x-3 mb-2">
                    <h2 className="text-2xl font-bold text-gray-900">
                      {user.lastName} {user.firstName}
                    </h2>
                    {renderStatusBadge(user.status)}
                  </div>
                  <p className="text-gray-600">@{user.username}</p>
                </div>

                {user.bio && (
                  <p className="text-gray-700">{user.bio}</p>
                )}

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                  <div>
                    <span className="text-gray-500">メールアドレス:</span>
                    <p className="font-medium">{user.email}</p>
                  </div>
                  {user.phoneNumber && (
                    <div>
                      <span className="text-gray-500">電話番号:</span>
                      <p className="font-medium">{user.phoneNumber}</p>
                    </div>
                  )}
                  <div>
                    <span className="text-gray-500">部署:</span>
                    <p className="font-medium">{user.department}</p>
                  </div>
                  <div>
                    <span className="text-gray-500">最終ログイン:</span>
                    <p className="font-medium">
                      {user.lastLoginAt ? formatRelativeTime(user.lastLoginAt) : '未ログイン'}
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </CardLayout>

          {/* ロールと権限 */}
          <CardLayout>
            <h3 className="text-lg font-semibold mb-4">ロールと権限</h3>
            <div className="space-y-4">
              <div>
                <span className="text-sm text-gray-500 mb-2 block">ロール:</span>
                <div className="flex flex-wrap gap-2">
                  {user.roles.map(role => (
                    <Badge key={role} variant="info">{role}</Badge>
                  ))}
                </div>
              </div>
              
              <div>
                <span className="text-sm text-gray-500 mb-2 block">権限:</span>
                <div className="flex flex-wrap gap-2">
                  {user.permissions.map(permission => (
                    <Badge key={permission} variant="secondary" size="sm">
                      {permission}
                    </Badge>
                  ))}
                </div>
              </div>
            </div>
          </CardLayout>

          {/* 活動履歴 */}
          <CardLayout>
            <h3 className="text-lg font-semibold mb-4">最近の活動</h3>
            <div className="space-y-4">
              {activities.map(activity => (
                <div key={activity.id} className="flex items-start space-x-3 py-3 border-b border-gray-100 last:border-0">
                  <div className="flex-shrink-0 mt-1">
                    {getActivityIcon(activity.type)}
                  </div>
                  <div className="flex-1">
                    <p className="text-sm font-medium text-gray-900">
                      {activity.description}
                    </p>
                    <div className="flex items-center space-x-4 mt-1">
                      <span className="text-xs text-gray-500">
                        {formatRelativeTime(activity.timestamp)}
                      </span>
                      {activity.ipAddress && (
                        <span className="text-xs text-gray-400">
                          IP: {activity.ipAddress}
                        </span>
                      )}
                      {activity.userAgent && (
                        <span className="text-xs text-gray-400">
                          {activity.userAgent}
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </CardLayout>
        </div>

        {/* 右側: サマリー情報 */}
        <div className="space-y-6">
          {/* システム情報 */}
          <CardLayout>
            <h3 className="text-lg font-semibold mb-4">システム情報</h3>
            <div className="space-y-3 text-sm">
              <div>
                <span className="text-gray-500">ユーザーID:</span>
                <p className="font-mono text-xs bg-gray-100 p-1 rounded mt-1">{user.id}</p>
              </div>
              <div>
                <span className="text-gray-500">作成日時:</span>
                <p className="font-medium">{formatDateTime(user.createdAt)}</p>
              </div>
              <div>
                <span className="text-gray-500">更新日時:</span>
                <p className="font-medium">{formatDateTime(user.updatedAt)}</p>
              </div>
            </div>
          </CardLayout>

          {/* 統計情報 */}
          <CardLayout>
            <h3 className="text-lg font-semibold mb-4">統計情報</h3>
            <div className="space-y-3">
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-500">総ログイン回数</span>
                <span className="font-semibold">42回</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-500">作成プロジェクト数</span>
                <span className="font-semibold">8件</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-500">最終活動</span>
                <span className="font-semibold">2時間前</span>
              </div>
            </div>
          </CardLayout>

          {/* クイックアクション */}
          <CardLayout>
            <h3 className="text-lg font-semibold mb-4">クイックアクション</h3>
            <div className="space-y-2">
              {hasPermission('users.edit') && (
                <Button variant="ghost" size="sm" className="w-full justify-start">
                  <svg className="h-4 w-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 1.95L17 12l-6.11 2.05L3 16v-8z" />
                  </svg>
                  メッセージ送信
                </Button>
              )}
              <Button variant="ghost" size="sm" className="w-full justify-start">
                <svg className="h-4 w-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                活動履歴出力
              </Button>
              {hasPermission('users.edit') && (
                <Button variant="ghost" size="sm" className="w-full justify-start">
                  <svg className="h-4 w-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1121 9z" />
                  </svg>
                  パスワードリセット
                </Button>
              )}
            </div>
          </CardLayout>
        </div>
      </div>
    </PageContainer>
  );
};