import React, { useState, useCallback, useMemo } from 'react';
import { TreeView } from '../../components/TreeView';
import { Button } from '../../components/ui/Button';
import { Input } from '../../components/ui/Input';
import { Modal } from '../../components/ui/Modal';
import { Select } from '../../components/ui/Select';
import { Badge } from '../../components/ui/Badge';
import { PageContainer, CardLayout, GridLayout } from '../../layouts/MainLayout/MainLayout';
import { useAuth } from '../../hooks/useAuth';
import type { TreeNode } from '../../components/TreeView/types';

interface Organization {
  id: string;
  name: string;
  code: string;
  type: 'company' | 'division' | 'department' | 'team';
  parentId?: string;
  managerId?: string;
  managerName?: string;
  description?: string;
  memberCount: number;
  status: 'active' | 'inactive';
  createdAt: string;
}

interface OrganizationFormData {
  name: string;
  code: string;
  type: Organization['type'];
  parentId?: string;
  managerId?: string;
  description: string;
  status: Organization['status'];
}

export const OrganizationList: React.FC = () => {
  const { hasPermission } = useAuth();
  
  // 状態管理
  const [selectedKeys, setSelectedKeys] = useState<string[]>([]);
  const [expandedKeys, setExpandedKeys] = useState<string[]>(['org-1', 'org-2']);
  const [searchValue, setSearchValue] = useState('');
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [editingOrg, setEditingOrg] = useState<Organization | null>(null);
  const [formData, setFormData] = useState<OrganizationFormData>({
    name: '',
    code: '',
    type: 'department',
    parentId: '',
    managerId: '',
    description: '',
    status: 'active',
  });
  const [loading, setLoading] = useState(false);

  // モック組織データ
  const mockOrganizations: Organization[] = [
    {
      id: 'org-1',
      name: 'ITDO Corporation',
      code: 'ITDO',
      type: 'company',
      memberCount: 120,
      status: 'active',
      createdAt: '2020-01-01',
      description: 'ITDOコーポレーション本社',
    },
    {
      id: 'org-2',
      name: '技術本部',
      code: 'TECH',
      type: 'division',
      parentId: 'org-1',
      managerId: 'user-1',
      managerName: '田中 太郎',
      memberCount: 45,
      status: 'active',
      createdAt: '2020-01-15',
      description: '技術開発および運用を担当する本部',
    },
    {
      id: 'org-3',
      name: '営業本部',
      code: 'SALES',
      type: 'division',
      parentId: 'org-1',
      managerId: 'user-2',
      managerName: '佐藤 花子',
      memberCount: 35,
      status: 'active',
      createdAt: '2020-01-15',
      description: '営業・マーケティング活動を担当する本部',
    },
    {
      id: 'org-4',
      name: '開発部',
      code: 'DEV',
      type: 'department',
      parentId: 'org-2',
      managerId: 'user-3',
      managerName: '山田 次郎',
      memberCount: 25,
      status: 'active',
      createdAt: '2020-02-01',
      description: 'ソフトウェア開発を担当する部署',
    },
    {
      id: 'org-5',
      name: 'インフラ部',
      code: 'INFRA',
      type: 'department',
      parentId: 'org-2',
      managerId: 'user-4',
      managerName: '鈴木 三郎',
      memberCount: 15,
      status: 'active',
      createdAt: '2020-02-01',
      description: 'システムインフラの構築・運用を担当する部署',
    },
    {
      id: 'org-6',
      name: 'フロントエンドチーム',
      code: 'FE',
      type: 'team',
      parentId: 'org-4',
      managerId: 'user-5',
      managerName: '高橋 四郎',
      memberCount: 8,
      status: 'active',
      createdAt: '2020-03-01',
      description: 'フロントエンド開発を担当するチーム',
    },
    {
      id: 'org-7',
      name: 'バックエンドチーム',
      code: 'BE',
      type: 'team',
      parentId: 'org-4',
      managerId: 'user-6',
      managerName: '渡辺 五郎',
      memberCount: 12,
      status: 'active',
      createdAt: '2020-03-01',
      description: 'バックエンド開発を担当するチーム',
    },
    {
      id: 'org-8',
      name: '企画営業部',
      code: 'PLAN',
      type: 'department',
      parentId: 'org-3',
      managerId: 'user-7',
      managerName: '伊藤 六郎',
      memberCount: 20,
      status: 'active',
      createdAt: '2020-02-15',
      description: '企画営業を担当する部署',
    },
    {
      id: 'org-9',
      name: 'カスタマーサポート部',
      code: 'CS',
      type: 'department',
      parentId: 'org-3',
      managerId: 'user-8',
      managerName: '加藤 七子',
      memberCount: 15,
      status: 'active',
      createdAt: '2020-02-15',
      description: 'カスタマーサポートを担当する部署',
    },
  ];

  // 階層構造のTreeNode配列に変換
  const buildTreeData = useCallback((organizations: Organization[]): TreeNode[] => {
    const orgMap = new Map(organizations.map(org => [org.id, org]));
    const tree: TreeNode[] = [];

    const createNode = (org: Organization): TreeNode => {
      const typeIcons = {
        company: (
          <svg className="w-4 h-4 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
          </svg>
        ),
        division: (
          <svg className="w-4 h-4 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
          </svg>
        ),
        department: (
          <svg className="w-4 h-4 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16l7-3 7 3z" />
          </svg>
        ),
        team: (
          <svg className="w-4 h-4 text-orange-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197m13.5-9a2.5 2.5 0 11-5 0 2.5 2.5 0 015 0z" />
          </svg>
        ),
      };

      const children = organizations
        .filter(child => child.parentId === org.id)
        .map(createNode)
        .sort((a, b) => a.title.localeCompare(b.title));

      return {
        id: org.id,
        title: org.name,
        key: org.id,
        icon: typeIcons[org.type],
        children,
        data: org,
        isLeaf: children.length === 0,
      };
    };

    // ルートノード（親IDがないもの）から開始
    const rootOrgs = organizations.filter(org => !org.parentId);
    rootOrgs.forEach(org => {
      tree.push(createNode(org));
    });

    return tree;
  }, []);

  const treeData = useMemo(() => buildTreeData(mockOrganizations), [mockOrganizations, buildTreeData]);

  // 選択された組織の詳細情報取得
  const selectedOrg = useMemo(() => {
    if (selectedKeys.length === 0) return null;
    return mockOrganizations.find(org => org.id === selectedKeys[0]) || null;
  }, [selectedKeys, mockOrganizations]);

  // 組織タイプのラベル
  const getTypeLabel = (type: Organization['type']) => {
    const labels = {
      company: '会社',
      division: '本部',
      department: '部署',
      team: 'チーム',
    };
    return labels[type];
  };

  // ステータスバッジ
  const renderStatusBadge = (status: Organization['status']) => {
    return status === 'active' 
      ? <Badge variant="success">アクティブ</Badge>
      : <Badge variant="error">無効</Badge>;
  };

  // フォーム送信処理
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    setLoading(true);
    try {
      // モックAPI呼び出し
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      // 成功処理
      setShowCreateModal(false);
      setShowEditModal(false);
      setFormData({
        name: '',
        code: '',
        type: 'department',
        parentId: '',
        managerId: '',
        description: '',
        status: 'active',
      });
    } catch (error) {
      console.error('保存に失敗しました:', error);
    } finally {
      setLoading(false);
    }
  };

  // 編集モードの開始
  const handleEdit = (org: Organization) => {
    setEditingOrg(org);
    setFormData({
      name: org.name,
      code: org.code,
      type: org.type,
      parentId: org.parentId || '',
      managerId: org.managerId || '',
      description: org.description || '',
      status: org.status,
    });
    setShowEditModal(true);
  };

  // 削除処理
  const handleDelete = async (org: Organization) => {
    if (window.confirm(`組織「${org.name}」を削除しますか？\nこの操作は取り消せません。`)) {
      try {
        // モックAPI呼び出し
        await new Promise(resolve => setTimeout(resolve, 500));
        // 成功処理
      } catch (error) {
        console.error('削除に失敗しました:', error);
      }
    }
  };

  // ドラッグ&ドロップ処理
  const handleDrop = useCallback((info: any) => {
    if (!hasPermission('organizations.edit')) return;

    const { dragNode, node, dropPosition, dropToGap } = info;
    console.log('組織の移動:', {
      from: dragNode.data?.name,
      to: node.data?.name,
      position: dropPosition,
      dropToGap,
    });
    
    // 実際の移動処理をここに実装
  }, [hasPermission]);

  return (
    <PageContainer
      title="組織管理"
      subtitle="会社の組織構造と階層管理"
      actions={
        <div className="flex items-center space-x-3">
          {hasPermission('organizations.create') && (
            <Button onClick={() => setShowCreateModal(true)}>
              <svg className="h-4 w-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
              </svg>
              新規組織追加
            </Button>
          )}
        </div>
      }
    >
      <GridLayout cols={{ default: 1, lg: 3 }} gap="lg">
        {/* 左側: 組織ツリー */}
        <div className="lg:col-span-2">
          <CardLayout>
            <div className="mb-4">
              <h3 className="text-lg font-semibold mb-3">組織構造</h3>
              
              {/* 検索バー */}
              <div className="relative mb-4">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <svg className="h-5 w-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                  </svg>
                </div>
                <Input
                  placeholder="組織名で検索..."
                  value={searchValue}
                  onChange={(e) => setSearchValue(e.target.value)}
                  className="pl-10"
                />
              </div>

              {/* コントロールボタン */}
              <div className="flex items-center space-x-2 mb-4">
                <Button
                  size="sm"
                  variant="ghost"
                  onClick={() => setExpandedKeys(mockOrganizations.map(org => org.id))}
                >
                  すべて展開
                </Button>
                <Button
                  size="sm"
                  variant="ghost"
                  onClick={() => setExpandedKeys([])}
                >
                  すべて折りたたみ
                </Button>
              </div>
            </div>

            {/* ツリービュー */}
            <div className="border rounded-lg p-4" style={{ minHeight: '500px' }}>
              <TreeView
                treeData={treeData}
                selectedKeys={selectedKeys}
                expandedKeys={expandedKeys}
                searchValue={searchValue}
                showLine={true}
                draggable={hasPermission('organizations.edit')}
                onSelect={(keys) => setSelectedKeys(keys)}
                onExpand={(keys) => setExpandedKeys(keys)}
                onDrop={handleDrop}
                titleRender={(node) => (
                  <div className="flex items-center justify-between w-full mr-2">
                    <div className="flex items-center space-x-2">
                      <span>{node.title}</span>
                      <Badge variant="secondary" size="sm">
                        {node.data?.code}
                      </Badge>
                      <span className="text-xs text-gray-500">
                        ({node.data?.memberCount}名)
                      </span>
                    </div>
                    
                    {hasPermission('organizations.edit') && selectedKeys.includes(node.id) && (
                      <div className="flex items-center space-x-1 opacity-0 group-hover:opacity-100">
                        <Button
                          size="sm"
                          variant="ghost"
                          onClick={(e) => {
                            e.stopPropagation();
                            handleEdit(node.data);
                          }}
                        >
                          <svg className="h-3 w-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                          </svg>
                        </Button>
                        <Button
                          size="sm"
                          variant="ghost"
                          onClick={(e) => {
                            e.stopPropagation();
                            handleDelete(node.data);
                          }}
                          className="text-red-600 hover:text-red-700"
                        >
                          <svg className="h-3 w-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                          </svg>
                        </Button>
                      </div>
                    )}
                  </div>
                )}
              />
            </div>
          </CardLayout>
        </div>

        {/* 右側: 詳細情報 */}
        <div className="space-y-6">
          {selectedOrg ? (
            <>
              {/* 基本情報 */}
              <CardLayout>
                <div className="flex items-start justify-between mb-4">
                  <h3 className="text-lg font-semibold">組織詳細</h3>
                  {hasPermission('organizations.edit') && (
                    <div className="flex space-x-2">
                      <Button size="sm" variant="ghost" onClick={() => handleEdit(selectedOrg)}>
                        編集
                      </Button>
                    </div>
                  )}
                </div>
                
                <div className="space-y-4">
                  <div>
                    <h4 className="font-medium text-lg">{selectedOrg.name}</h4>
                    <div className="flex items-center space-x-2 mt-1">
                      <Badge variant="info" size="sm">{selectedOrg.code}</Badge>
                      <Badge variant="secondary" size="sm">{getTypeLabel(selectedOrg.type)}</Badge>
                      {renderStatusBadge(selectedOrg.status)}
                    </div>
                  </div>

                  {selectedOrg.description && (
                    <div>
                      <span className="text-sm text-gray-500">説明:</span>
                      <p className="text-sm mt-1">{selectedOrg.description}</p>
                    </div>
                  )}

                  <div className="grid grid-cols-1 gap-3 text-sm">
                    {selectedOrg.managerName && (
                      <div>
                        <span className="text-gray-500">責任者:</span>
                        <p className="font-medium">{selectedOrg.managerName}</p>
                      </div>
                    )}
                    <div>
                      <span className="text-gray-500">メンバー数:</span>
                      <p className="font-medium">{selectedOrg.memberCount}名</p>
                    </div>
                    <div>
                      <span className="text-gray-500">作成日:</span>
                      <p className="font-medium">{new Date(selectedOrg.createdAt).toLocaleDateString('ja-JP')}</p>
                    </div>
                  </div>
                </div>
              </CardLayout>

              {/* 統計情報 */}
              <CardLayout>
                <h3 className="text-lg font-semibold mb-4">統計情報</h3>
                <div className="space-y-3">
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-500">直属部署数</span>
                    <span className="font-semibold">
                      {mockOrganizations.filter(org => org.parentId === selectedOrg.id).length}
                    </span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-500">総メンバー数</span>
                    <span className="font-semibold">{selectedOrg.memberCount}名</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-500">アクティブプロジェクト</span>
                    <span className="font-semibold">3件</span>
                  </div>
                </div>
              </CardLayout>

              {/* クイックアクション */}
              {hasPermission('organizations.edit') && (
                <CardLayout>
                  <h3 className="text-lg font-semibold mb-4">クイックアクション</h3>
                  <div className="space-y-2">
                    <Button variant="ghost" size="sm" className="w-full justify-start">
                      <svg className="h-4 w-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                      </svg>
                      子組織を追加
                    </Button>
                    <Button variant="ghost" size="sm" className="w-full justify-start">
                      <svg className="h-4 w-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197m13.5-9a2.5 2.5 0 11-5 0 2.5 2.5 0 015 0z" />
                      </svg>
                      メンバー管理
                    </Button>
                    <Button variant="ghost" size="sm" className="w-full justify-start">
                      <svg className="h-4 w-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                      </svg>
                      レポート生成
                    </Button>
                  </div>
                </CardLayout>
              )}
            </>
          ) : (
            <CardLayout>
              <div className="text-center py-8 text-gray-500">
                <svg className="mx-auto h-12 w-12 text-gray-400 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
                </svg>
                <p>組織を選択して詳細を表示</p>
              </div>
            </CardLayout>
          )}
        </div>
      </GridLayout>

      {/* 新規作成モーダル */}
      <Modal
        isOpen={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        title="新規組織追加"
        size="lg"
      >
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                組織名 *
              </label>
              <Input
                value={formData.name}
                onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
                placeholder="例: 開発部"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                コード *
              </label>
              <Input
                value={formData.code}
                onChange={(e) => setFormData(prev => ({ ...prev, code: e.target.value.toUpperCase() }))}
                placeholder="例: DEV"
                required
              />
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                組織タイプ
              </label>
              <Select
                value={formData.type}
                onChange={(value) => setFormData(prev => ({ ...prev, type: value as Organization['type'] }))}
              >
                <Select.Option value="company">会社</Select.Option>
                <Select.Option value="division">本部</Select.Option>
                <Select.Option value="department">部署</Select.Option>
                <Select.Option value="team">チーム</Select.Option>
              </Select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                親組織
              </label>
              <Select
                value={formData.parentId}
                onChange={(value) => setFormData(prev => ({ ...prev, parentId: value }))}
                placeholder="親組織を選択"
                allowClear
              >
                {mockOrganizations.map(org => (
                  <Select.Option key={org.id} value={org.id}>
                    {org.name}
                  </Select.Option>
                ))}
              </Select>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              説明
            </label>
            <textarea
              value={formData.description}
              onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
              placeholder="組織の説明を入力してください"
              rows={3}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
          </div>

          <div className="flex justify-end space-x-3 pt-4">
            <Button type="button" variant="ghost" onClick={() => setShowCreateModal(false)}>
              キャンセル
            </Button>
            <Button type="submit" disabled={loading}>
              {loading ? '作成中...' : '作成'}
            </Button>
          </div>
        </form>
      </Modal>

      {/* 編集モーダル */}
      <Modal
        isOpen={showEditModal}
        onClose={() => setShowEditModal(false)}
        title="組織編集"
        size="lg"
      >
        <form onSubmit={handleSubmit} className="space-y-4">
          {/* 編集フォーム（新規作成と同じ構造） */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                組織名 *
              </label>
              <Input
                value={formData.name}
                onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                コード *
              </label>
              <Input
                value={formData.code}
                onChange={(e) => setFormData(prev => ({ ...prev, code: e.target.value.toUpperCase() }))}
                required
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              ステータス
            </label>
            <Select
              value={formData.status}
              onChange={(value) => setFormData(prev => ({ ...prev, status: value as Organization['status'] }))}
            >
              <Select.Option value="active">アクティブ</Select.Option>
              <Select.Option value="inactive">無効</Select.Option>
            </Select>
          </div>

          <div className="flex justify-end space-x-3 pt-4">
            <Button type="button" variant="ghost" onClick={() => setShowEditModal(false)}>
              キャンセル
            </Button>
            <Button type="submit" disabled={loading}>
              {loading ? '更新中...' : '更新'}
            </Button>
          </div>
        </form>
      </Modal>
    </PageContainer>
  );
};