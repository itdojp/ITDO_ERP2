import React, { useState, useMemo, useCallback } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { DataTable } from '../../components/DataTable';
import { TableFilters } from '../../components/DataTable/TableFilters';
import { Button } from '../../components/ui/Button';
import { Badge } from '../../components/ui/Badge';
import { PageContainer } from '../../layouts/MainLayout/MainLayout';
import { useAuth } from '../../hooks/useAuth';
import type { Column, SortConfig, FilterConfig, PaginationConfig } from '../../components/DataTable/types';

// ユーザーデータの型定義
interface User {
  id: string;
  username: string;
  email: string;
  firstName: string;
  lastName: string;
  roles: string[];
  department: string;
  status: 'active' | 'inactive' | 'pending';
  lastLoginAt?: string;
  createdAt: string;
  avatar?: string;
}

// モックデータ
const generateMockUsers = (count: number = 50): User[] => {
  const departments = ['営業部', '開発部', '人事部', '経理部', 'マーケティング部', '総務部'];
  const roles = ['admin', 'manager', 'user', 'viewer'];
  const statuses: User['status'][] = ['active', 'inactive', 'pending'];
  
  return Array.from({ length: count }, (_, index) => ({
    id: `user-${index + 1}`,
    username: `user${index + 1}`,
    email: `user${index + 1}@example.com`,
    firstName: `太郎${index + 1}`,
    lastName: '田中',
    roles: [roles[Math.floor(Math.random() * roles.length)]],
    department: departments[Math.floor(Math.random() * departments.length)],
    status: statuses[Math.floor(Math.random() * statuses.length)],
    lastLoginAt: Math.random() > 0.3 ? new Date(Date.now() - Math.random() * 30 * 24 * 60 * 60 * 1000).toISOString() : undefined,
    createdAt: new Date(Date.now() - Math.random() * 365 * 24 * 60 * 60 * 1000).toISOString(),
  }));
};

export const UserList: React.FC = () => {
  const navigate = useNavigate();
  const { hasPermission } = useAuth();
  
  const [loading, setLoading] = useState(false);
  const [searchValue, setSearchValue] = useState('');
  const [sortConfig, setSortConfig] = useState<SortConfig>({ key: 'createdAt', direction: 'desc' });
  const [filterConfig, setFilterConfig] = useState<FilterConfig>({});
  const [selectedRowKeys, setSelectedRowKeys] = useState<React.Key[]>([]);
  const [pagination, setPagination] = useState<PaginationConfig>({
    current: 1,
    pageSize: 20,
    total: 0,
  });

  // モックデータの生成
  const allUsers = useMemo(() => generateMockUsers(100), []);

  // フィルタリング・ソート・ページング処理
  const processedData = useMemo(() => {
    let filteredData = [...allUsers];

    // 検索フィルター
    if (searchValue) {
      filteredData = filteredData.filter(user => 
        user.username.toLowerCase().includes(searchValue.toLowerCase()) ||
        user.email.toLowerCase().includes(searchValue.toLowerCase()) ||
        user.firstName.toLowerCase().includes(searchValue.toLowerCase()) ||
        user.lastName.toLowerCase().includes(searchValue.toLowerCase()) ||
        user.department.toLowerCase().includes(searchValue.toLowerCase())
      );
    }

    // 高度なフィルター
    Object.entries(filterConfig).forEach(([key, value]) => {
      if (value && value !== '') {
        filteredData = filteredData.filter(user => {
          const userValue = (user as any)[key];
          if (Array.isArray(userValue)) {
            return userValue.includes(value);
          }
          return userValue === value;
        });
      }
    });

    // ソート
    if (sortConfig) {
      filteredData.sort((a, b) => {
        const aValue = (a as any)[sortConfig.key];
        const bValue = (b as any)[sortConfig.key];
        
        if (aValue === bValue) return 0;
        if (aValue === null || aValue === undefined) return 1;
        if (bValue === null || bValue === undefined) return -1;
        
        const result = aValue < bValue ? -1 : 1;
        return sortConfig.direction === 'asc' ? result : -result;
      });
    }

    // ページング
    const start = (pagination.current - 1) * pagination.pageSize;
    const paginatedData = filteredData.slice(start, start + pagination.pageSize);

    return {
      data: paginatedData,
      total: filteredData.length,
    };
  }, [allUsers, searchValue, filterConfig, sortConfig, pagination.current, pagination.pageSize]);

  // ページネーション設定の更新
  const currentPagination = useMemo(() => ({
    ...pagination,
    total: processedData.total,
  }), [pagination, processedData.total]);

  // ステータスバッジのレンダリング
  const renderStatusBadge = (status: User['status']) => {
    const config = {
      active: { label: 'アクティブ', variant: 'success' as const },
      inactive: { label: '無効', variant: 'error' as const },
      pending: { label: '保留中', variant: 'warning' as const },
    };
    
    const { label, variant } = config[status];
    return <Badge variant={variant}>{label}</Badge>;
  };

  // 最終ログイン時間のフォーマット
  const formatLastLogin = (dateString?: string) => {
    if (!dateString) return '未ログイン';
    
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
    
    if (diffDays === 0) return '今日';
    if (diffDays === 1) return '昨日';
    if (diffDays < 30) return `${diffDays}日前`;
    
    return date.toLocaleDateString('ja-JP');
  };

  // テーブルカラム定義
  const columns: Column<User>[] = [
    {
      key: 'user',
      title: 'ユーザー',
      dataIndex: 'username',
      sortable: true,
      width: 250,
      render: (_, record) => (
        <div className="flex items-center space-x-3">
          <div className="h-8 w-8 bg-gray-300 rounded-full flex items-center justify-center">
            {record.avatar ? (
              <img
                src={record.avatar}
                alt={`${record.firstName} ${record.lastName}`}
                className="h-8 w-8 rounded-full"
              />
            ) : (
              <span className="text-sm font-medium text-gray-700">
                {record.firstName[0]}{record.lastName[0]}
              </span>
            )}
          </div>
          <div>
            <div className="font-medium text-gray-900">
              {record.lastName} {record.firstName}
            </div>
            <div className="text-sm text-gray-500">@{record.username}</div>
          </div>
        </div>
      ),
    },
    {
      key: 'email',
      title: 'メールアドレス',
      dataIndex: 'email',
      sortable: true,
      width: 200,
      ellipsis: true,
    },
    {
      key: 'department',
      title: '部署',
      dataIndex: 'department',
      sortable: true,
      filterable: true,
      width: 120,
    },
    {
      key: 'roles',
      title: 'ロール',
      dataIndex: 'roles',
      width: 120,
      render: (roles: string[]) => (
        <div className="flex flex-wrap gap-1">
          {roles.map(role => (
            <Badge key={role} variant="info" size="sm">
              {role}
            </Badge>
          ))}
        </div>
      ),
    },
    {
      key: 'status',
      title: 'ステータス',
      dataIndex: 'status',
      sortable: true,
      filterable: true,
      width: 100,
      render: (status: User['status']) => renderStatusBadge(status),
    },
    {
      key: 'lastLoginAt',
      title: '最終ログイン',
      dataIndex: 'lastLoginAt',
      sortable: true,
      width: 120,
      render: (lastLoginAt: string) => (
        <span className="text-sm text-gray-600">
          {formatLastLogin(lastLoginAt)}
        </span>
      ),
    },
    {
      key: 'actions',
      title: 'アクション',
      width: 150,
      render: (_, record) => (
        <div className="flex items-center space-x-2">
          <Button
            size="sm"
            variant="ghost"
            onClick={() => navigate(`/users/${record.id}`)}
          >
            詳細
          </Button>
          {hasPermission('users.edit') && (
            <Button
              size="sm"
              variant="ghost"
              onClick={() => navigate(`/users/${record.id}/edit`)}
            >
              編集
            </Button>
          )}
        </div>
      ),
    },
  ];

  // イベントハンドラー
  const handleSearch = useCallback((value: string) => {
    setSearchValue(value);
    setPagination(prev => ({ ...prev, current: 1 }));
  }, []);

  const handleFilter = useCallback((filters: FilterConfig) => {
    setFilterConfig(filters);
    setPagination(prev => ({ ...prev, current: 1 }));
  }, []);

  const handleSort = useCallback((sort: SortConfig) => {
    setSortConfig(sort);
  }, []);

  const handlePaginationChange = useCallback((page: number, pageSize: number) => {
    setPagination(prev => ({ ...prev, current: page, pageSize }));
  }, []);

  const handleSelectionChange = useCallback((keys: React.Key[], rows: User[]) => {
    setSelectedRowKeys(keys);
  }, []);

  const handleRowClick = useCallback((record: User) => {
    navigate(`/users/${record.id}`);
  }, [navigate]);

  // 一括削除処理
  const handleBulkDelete = useCallback(async () => {
    if (window.confirm(`選択した${selectedRowKeys.length}件のユーザーを削除しますか？`)) {
      setLoading(true);
      try {
        // API呼び出し（モック）
        await new Promise(resolve => setTimeout(resolve, 1000));
        setSelectedRowKeys([]);
        // データの再読み込み処理
      } catch (error) {
        console.error('削除に失敗しました:', error);
      } finally {
        setLoading(false);
      }
    }
  }, [selectedRowKeys]);

  // フィルター設定
  const searchConfig = {
    placeholder: 'ユーザー名、メール、部署で検索...',
    searchValue,
  };

  const advancedFilters = {
    department: {
      type: 'select' as const,
      label: '部署',
      options: [
        { label: '営業部', value: '営業部' },
        { label: '開発部', value: '開発部' },
        { label: '人事部', value: '人事部' },
        { label: '経理部', value: '経理部' },
        { label: 'マーケティング部', value: 'マーケティング部' },
        { label: '総務部', value: '総務部' },
      ],
    },
    status: {
      type: 'select' as const,
      label: 'ステータス',
      options: [
        { label: 'アクティブ', value: 'active' },
        { label: '無効', value: 'inactive' },
        { label: '保留中', value: 'pending' },
      ],
    },
    roles: {
      type: 'select' as const,
      label: 'ロール',
      options: [
        { label: '管理者', value: 'admin' },
        { label: 'マネージャー', value: 'manager' },
        { label: 'ユーザー', value: 'user' },
        { label: '閲覧者', value: 'viewer' },
      ],
    },
  };

  return (
    <PageContainer
      title="ユーザー管理"
      subtitle="システムユーザーの管理と設定"
      actions={
        <div className="flex items-center space-x-3">
          {selectedRowKeys.length > 0 && hasPermission('users.delete') && (
            <Button
              variant="ghost"
              onClick={handleBulkDelete}
              className="text-red-600 hover:text-red-700"
              disabled={loading}
            >
              {selectedRowKeys.length}件削除
            </Button>
          )}
          {hasPermission('users.create') && (
            <Button asChild>
              <Link to="/users/create">
                <svg className="h-4 w-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                </svg>
                新規ユーザー
              </Link>
            </Button>
          )}
        </div>
      }
    >
      <div className="space-y-6">
        {/* 検索・フィルター */}
        <div className="bg-white rounded-lg shadow p-6">
          <TableFilters
            searchConfig={searchConfig}
            advancedFilters={advancedFilters}
            onSearch={handleSearch}
            onFilter={handleFilter}
            onReset={() => {
              setSearchValue('');
              setFilterConfig({});
              setPagination(prev => ({ ...prev, current: 1 }));
            }}
          />
        </div>

        {/* データテーブル */}
        <div className="bg-white rounded-lg shadow">
          <DataTable
            columns={columns}
            dataSource={processedData.data}
            loading={loading}
            pagination={{
              ...currentPagination,
              showSizeChanger: true,
              showTotal: true,
            }}
            selection={{
              selectedRowKeys,
              onChange: handleSelectionChange,
              getCheckboxProps: (record) => ({
                disabled: !hasPermission('users.delete'),
              }),
            }}
            sortConfig={sortConfig}
            onSort={handleSort}
            onRowClick={handleRowClick}
            onFilter={handleFilter}
            size="middle"
            className="border-0"
          />
        </div>
      </div>
    </PageContainer>
  );
};