import React, { useState, useCallback, useMemo } from 'react';
import { DataTable } from '../../components/DataTable';
import { Button } from '../../components/ui/Button';
import { Input } from '../../components/ui/Input';
import { Select } from '../../components/ui/Select';
import { Modal } from '../../components/ui/Modal';
import { Badge } from '../../components/ui/Badge';
import { PageContainer, CardLayout, GridLayout } from '../../layouts/MainLayout/MainLayout';
import { useAuth } from '../../hooks/useAuth';
import type { DataTableColumn } from '../../components/DataTable';

interface Product {
  id: string;
  code: string;
  name: string;
  description: string;
  categoryId: string;
  categoryName: string;
  price: number;
  costPrice: number;
  stockQuantity: number;
  minStockLevel: number;
  maxStockLevel: number;
  unit: string;
  brand?: string;
  model?: string;
  imageUrl?: string;
  status: 'active' | 'inactive' | 'discontinued';
  isService: boolean;
  isTaxable: boolean;
  taxRate: number;
  weight?: number;
  dimensions?: string;
  barcode?: string;
  supplierIds: string[];
  tags: string[];
  createdAt: string;
  updatedAt: string;
  createdBy: string;
}

interface ProductFormData {
  code: string;
  name: string;
  description: string;
  categoryId: string;
  price: number;
  costPrice: number;
  stockQuantity: number;
  minStockLevel: number;
  maxStockLevel: number;
  unit: string;
  brand: string;
  model: string;
  status: Product['status'];
  isService: boolean;
  isTaxable: boolean;
  taxRate: number;
  weight: number | null;
  dimensions: string;
  barcode: string;
  tags: string[];
}

interface Category {
  id: string;
  name: string;
  code: string;
  parentId?: string;
}

type ViewMode = 'list' | 'grid';

export const ProductList: React.FC = () => {
  const { hasPermission } = useAuth();

  // 状態管理
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [searchValue, setSearchValue] = useState('');
  const [categoryFilter, setCategoryFilter] = useState<string>('');
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [showImageModal, setShowImageModal] = useState(false);
  const [editingProduct, setEditingProduct] = useState<Product | null>(null);
  const [viewingImage, setViewingImage] = useState<string>('');
  const [viewMode, setViewMode] = useState<ViewMode>('list');
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState<ProductFormData>({
    code: '',
    name: '',
    description: '',
    categoryId: '',
    price: 0,
    costPrice: 0,
    stockQuantity: 0,
    minStockLevel: 10,
    maxStockLevel: 1000,
    unit: 'piece',
    brand: '',
    model: '',
    status: 'active',
    isService: false,
    isTaxable: true,
    taxRate: 10,
    weight: null,
    dimensions: '',
    barcode: '',
    tags: [],
  });

  // モック商品データ
  const mockProducts: Product[] = [
    {
      id: 'prod-1',
      code: 'LT-001',
      name: 'ThinkPad X1 Carbon',
      description: 'プレミアムビジネスラップトップ',
      categoryId: 'cat-1',
      categoryName: 'ノートパソコン',
      price: 198000,
      costPrice: 150000,
      stockQuantity: 25,
      minStockLevel: 5,
      maxStockLevel: 100,
      unit: '台',
      brand: 'Lenovo',
      model: 'X1 Carbon Gen 11',
      imageUrl: 'https://via.placeholder.com/400x300?text=ThinkPad',
      status: 'active',
      isService: false,
      isTaxable: true,
      taxRate: 10,
      weight: 1.12,
      dimensions: '314.5 x 221.6 x 14.9 mm',
      barcode: '4562123456789',
      supplierIds: ['sup-1'],
      tags: ['premium', 'business', 'ultrabook'],
      createdAt: '2024-01-15',
      updatedAt: '2024-01-20',
      createdBy: 'admin',
    },
    {
      id: 'prod-2',
      code: 'MN-001',
      name: 'Dell U2723QE',
      description: '27インチ4Kモニター USB-C対応',
      categoryId: 'cat-2',
      categoryName: 'モニター',
      price: 85000,
      costPrice: 60000,
      stockQuantity: 15,
      minStockLevel: 3,
      maxStockLevel: 50,
      unit: '台',
      brand: 'Dell',
      model: 'U2723QE',
      imageUrl: 'https://via.placeholder.com/400x300?text=Dell+Monitor',
      status: 'active',
      isService: false,
      isTaxable: true,
      taxRate: 10,
      weight: 6.8,
      dimensions: '611.6 x 518.3 x 185 mm',
      barcode: '4562123456790',
      supplierIds: ['sup-2'],
      tags: ['4k', 'usb-c', 'professional'],
      createdAt: '2024-01-16',
      updatedAt: '2024-01-18',
      createdBy: 'admin',
    },
    {
      id: 'prod-3',
      code: 'SW-001',
      name: 'システム開発サービス',
      description: '業務システム開発・保守サービス',
      categoryId: 'cat-3',
      categoryName: 'サービス',
      price: 500000,
      costPrice: 350000,
      stockQuantity: 0,
      minStockLevel: 0,
      maxStockLevel: 0,
      unit: '人月',
      brand: 'ITDO',
      model: '',
      status: 'active',
      isService: true,
      isTaxable: true,
      taxRate: 10,
      supplierIds: [],
      tags: ['development', 'service', 'custom'],
      createdAt: '2024-01-10',
      updatedAt: '2024-01-25',
      createdBy: 'admin',
    },
    {
      id: 'prod-4',
      code: 'KB-001',
      name: 'HHKB Professional HYBRID',
      description: 'プログラマー向け高級キーボード',
      categoryId: 'cat-4',
      categoryName: '周辺機器',
      price: 35000,
      costPrice: 25000,
      stockQuantity: 8,
      minStockLevel: 2,
      maxStockLevel: 30,
      unit: '個',
      brand: 'PFU',
      model: 'PD-KB800WS',
      imageUrl: 'https://via.placeholder.com/400x300?text=HHKB',
      status: 'active',
      isService: false,
      isTaxable: true,
      taxRate: 10,
      weight: 0.54,
      dimensions: '294 x 110 x 40 mm',
      barcode: '4562123456791',
      supplierIds: ['sup-3'],
      tags: ['mechanical', 'bluetooth', 'programmer'],
      createdAt: '2024-01-12',
      updatedAt: '2024-01-15',
      createdBy: 'admin',
    },
    {
      id: 'prod-5',
      code: 'LT-002',
      name: 'MacBook Pro 14"',
      description: 'Apple M3 Proチップ搭載',
      categoryId: 'cat-1',
      categoryName: 'ノートパソコン',
      price: 298000,
      costPrice: 250000,
      stockQuantity: 5,
      minStockLevel: 2,
      maxStockLevel: 20,
      unit: '台',
      brand: 'Apple',
      model: 'MacBook Pro 14" M3 Pro',
      imageUrl: 'https://via.placeholder.com/400x300?text=MacBook+Pro',
      status: 'active',
      isService: false,
      isTaxable: true,
      taxRate: 10,
      weight: 1.6,
      dimensions: '312.6 x 221.2 x 15.5 mm',
      barcode: '4562123456792',
      supplierIds: ['sup-4'],
      tags: ['apple', 'professional', 'creative'],
      createdAt: '2024-01-20',
      updatedAt: '2024-01-22',
      createdBy: 'admin',
    },
    {
      id: 'prod-6',
      code: 'ACC-001',
      name: 'USB-C ハブ',
      description: '7ポート多機能ハブ',
      categoryId: 'cat-4',
      categoryName: '周辺機器',
      price: 8500,
      costPrice: 5000,
      stockQuantity: 35,
      minStockLevel: 10,
      maxStockLevel: 100,
      unit: '個',
      brand: 'Anker',
      model: 'PowerExpand 7-in-1',
      imageUrl: 'https://via.placeholder.com/400x300?text=USB-C+Hub',
      status: 'active',
      isService: false,
      isTaxable: true,
      taxRate: 10,
      weight: 0.15,
      dimensions: '112 x 50 x 15 mm',
      barcode: '4562123456793',
      supplierIds: ['sup-5'],
      tags: ['usb-c', 'hub', 'portable'],
      createdAt: '2024-01-08',
      updatedAt: '2024-01-10',
      createdBy: 'admin',
    },
  ];

  // モックカテゴリデータ
  const mockCategories: Category[] = [
    { id: 'cat-1', name: 'ノートパソコン', code: 'LAPTOP' },
    { id: 'cat-2', name: 'モニター', code: 'MONITOR' },
    { id: 'cat-3', name: 'サービス', code: 'SERVICE' },
    { id: 'cat-4', name: '周辺機器', code: 'ACCESSORY' },
    { id: 'cat-5', name: 'ソフトウェア', code: 'SOFTWARE' },
  ];

  // フィルタリングされた商品データ
  const filteredProducts = useMemo(() => {
    let filtered = mockProducts;

    // 検索フィルター
    if (searchValue) {
      const search = searchValue.toLowerCase();
      filtered = filtered.filter(product =>
        product.name.toLowerCase().includes(search) ||
        product.code.toLowerCase().includes(search) ||
        product.description.toLowerCase().includes(search) ||
        product.brand?.toLowerCase().includes(search) ||
        product.tags.some(tag => tag.toLowerCase().includes(search))
      );
    }

    // カテゴリフィルター
    if (categoryFilter) {
      filtered = filtered.filter(product => product.categoryId === categoryFilter);
    }

    // ステータスフィルター
    if (statusFilter) {
      filtered = filtered.filter(product => product.status === statusFilter);
    }

    return filtered;
  }, [mockProducts, searchValue, categoryFilter, statusFilter]);

  // DataTableのカラム定義
  const columns: DataTableColumn<Product>[] = [
    {
      key: 'imageUrl',
      title: '画像',
      width: 80,
      render: (_, record) => (
        record.imageUrl ? (
          <img
            src={record.imageUrl}
            alt={record.name}
            className="w-12 h-12 object-cover rounded cursor-pointer hover:opacity-75"
            onClick={() => {
              setViewingImage(record.imageUrl!);
              setShowImageModal(true);
            }}
          />
        ) : (
          <div className="w-12 h-12 bg-gray-100 rounded flex items-center justify-center">
            <svg className="w-6 h-6 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
            </svg>
          </div>
        )
      ),
    },
    {
      key: 'code',
      title: '商品コード',
      width: 120,
      sorter: true,
      render: (value) => <span className="font-mono text-sm">{value}</span>,
    },
    {
      key: 'name',
      title: '商品名',
      width: 200,
      sorter: true,
      ellipsis: true,
    },
    {
      key: 'categoryName',
      title: 'カテゴリ',
      width: 120,
      render: (value) => <Badge variant="secondary" size="sm">{value}</Badge>,
    },
    {
      key: 'price',
      title: '販売価格',
      width: 120,
      sorter: true,
      align: 'right',
      render: (value) => `¥${value.toLocaleString()}`,
    },
    {
      key: 'stockQuantity',
      title: '在庫数',
      width: 100,
      sorter: true,
      align: 'right',
      render: (value, record) => {
        if (record.isService) return '-';
        const isLow = value <= record.minStockLevel;
        return (
          <span className={isLow ? 'text-red-600 font-semibold' : ''}>
            {value} {record.unit}
          </span>
        );
      },
    },
    {
      key: 'status',
      title: 'ステータス',
      width: 100,
      render: (value: Product['status']) => {
        const variants = {
          active: 'success',
          inactive: 'warning',
          discontinued: 'error',
        } as const;
        const labels = {
          active: 'アクティブ',
          inactive: '無効',
          discontinued: '廃止',
        };
        return <Badge variant={variants[value]} size="sm">{labels[value]}</Badge>;
      },
    },
    {
      key: 'tags',
      title: 'タグ',
      width: 150,
      render: (tags: string[]) => (
        <div className="flex flex-wrap gap-1">
          {tags.slice(0, 2).map(tag => (
            <Badge key={tag} variant="info" size="sm">{tag}</Badge>
          ))}
          {tags.length > 2 && (
            <span className="text-xs text-gray-500">+{tags.length - 2}</span>
          )}
        </div>
      ),
    },
    {
      key: 'actions',
      title: 'アクション',
      width: 120,
      render: (_, record) => (
        <div className="flex space-x-1">
          {hasPermission('products.read') && (
            <Button size="sm" variant="ghost" title="詳細表示">
              <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
              </svg>
            </Button>
          )}
          {hasPermission('products.edit') && (
            <Button
              size="sm"
              variant="ghost"
              onClick={() => handleEdit(record)}
              title="編集"
            >
              <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
              </svg>
            </Button>
          )}
          {hasPermission('products.delete') && (
            <Button
              size="sm"
              variant="ghost"
              onClick={() => handleDelete(record)}
              className="text-red-600 hover:text-red-700"
              title="削除"
            >
              <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
              </svg>
            </Button>
          )}
        </div>
      ),
    },
  ];

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
      resetForm();
    } catch (error) {
      console.error('保存に失敗しました:', error);
    } finally {
      setLoading(false);
    }
  };

  // フォームリセット
  const resetForm = () => {
    setFormData({
      code: '',
      name: '',
      description: '',
      categoryId: '',
      price: 0,
      costPrice: 0,
      stockQuantity: 0,
      minStockLevel: 10,
      maxStockLevel: 1000,
      unit: 'piece',
      brand: '',
      model: '',
      status: 'active',
      isService: false,
      isTaxable: true,
      taxRate: 10,
      weight: null,
      dimensions: '',
      barcode: '',
      tags: [],
    });
  };

  // 編集モードの開始
  const handleEdit = (product: Product) => {
    setEditingProduct(product);
    setFormData({
      code: product.code,
      name: product.name,
      description: product.description,
      categoryId: product.categoryId,
      price: product.price,
      costPrice: product.costPrice,
      stockQuantity: product.stockQuantity,
      minStockLevel: product.minStockLevel,
      maxStockLevel: product.maxStockLevel,
      unit: product.unit,
      brand: product.brand || '',
      model: product.model || '',
      status: product.status,
      isService: product.isService,
      isTaxable: product.isTaxable,
      taxRate: product.taxRate,
      weight: product.weight || null,
      dimensions: product.dimensions || '',
      barcode: product.barcode || '',
      tags: product.tags,
    });
    setShowEditModal(true);
  };

  // 削除処理
  const handleDelete = async (product: Product) => {
    if (window.confirm(`商品「${product.name}」を削除しますか？\nこの操作は取り消せません。`)) {
      try {
        // モックAPI呼び出し
        await new Promise(resolve => setTimeout(resolve, 500));
        // 成功処理
      } catch (error) {
        console.error('削除に失敗しました:', error);
      }
    }
  };

  // 一括削除処理
  const handleBulkDelete = async () => {
    if (selectedIds.length === 0) return;
    
    if (window.confirm(`選択した${selectedIds.length}件の商品を削除しますか？\nこの操作は取り消せません。`)) {
      try {
        // モックAPI呼び出し
        await new Promise(resolve => setTimeout(resolve, 1000));
        setSelectedIds([]);
      } catch (error) {
        console.error('一括削除に失敗しました:', error);
      }
    }
  };

  // グリッドビューのレンダリング
  const renderGridView = () => (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
      {filteredProducts.map(product => (
        <div key={product.id} className="bg-white rounded-lg shadow-sm border hover:shadow-md transition-shadow">
          {/* 商品画像 */}
          <div className="aspect-w-4 aspect-h-3 mb-4">
            {product.imageUrl ? (
              <img
                src={product.imageUrl}
                alt={product.name}
                className="w-full h-48 object-cover rounded-t-lg cursor-pointer"
                onClick={() => {
                  setViewingImage(product.imageUrl!);
                  setShowImageModal(true);
                }}
              />
            ) : (
              <div className="w-full h-48 bg-gray-100 rounded-t-lg flex items-center justify-center">
                <svg className="w-12 h-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                </svg>
              </div>
            )}
          </div>
          
          <div className="p-4">
            {/* 商品基本情報 */}
            <div className="mb-3">
              <h3 className="font-medium text-lg mb-1 truncate">{product.name}</h3>
              <p className="text-sm text-gray-600 font-mono">{product.code}</p>
              <p className="text-sm text-gray-500 line-clamp-2 mt-1">{product.description}</p>
            </div>

            {/* カテゴリとステータス */}
            <div className="flex items-center justify-between mb-3">
              <Badge variant="secondary" size="sm">{product.categoryName}</Badge>
              <Badge 
                variant={product.status === 'active' ? 'success' : product.status === 'inactive' ? 'warning' : 'error'} 
                size="sm"
              >
                {product.status === 'active' ? 'アクティブ' : product.status === 'inactive' ? '無効' : '廃止'}
              </Badge>
            </div>

            {/* 価格と在庫 */}
            <div className="mb-3">
              <div className="text-lg font-semibold text-blue-600">
                ¥{product.price.toLocaleString()}
              </div>
              {!product.isService && (
                <div className={`text-sm ${product.stockQuantity <= product.minStockLevel ? 'text-red-600 font-semibold' : 'text-gray-600'}`}>
                  在庫: {product.stockQuantity} {product.unit}
                </div>
              )}
            </div>

            {/* タグ */}
            <div className="flex flex-wrap gap-1 mb-3">
              {product.tags.slice(0, 3).map(tag => (
                <Badge key={tag} variant="info" size="sm">{tag}</Badge>
              ))}
              {product.tags.length > 3 && (
                <span className="text-xs text-gray-500">+{product.tags.length - 3}</span>
              )}
            </div>

            {/* アクションボタン */}
            <div className="flex space-x-2">
              {hasPermission('products.edit') && (
                <Button
                  size="sm"
                  variant="ghost"
                  onClick={() => handleEdit(product)}
                  className="flex-1"
                >
                  編集
                </Button>
              )}
              {hasPermission('products.delete') && (
                <Button
                  size="sm"
                  variant="ghost"
                  onClick={() => handleDelete(product)}
                  className="text-red-600 hover:text-red-700"
                >
                  削除
                </Button>
              )}
            </div>
          </div>
        </div>
      ))}
    </div>
  );

  return (
    <PageContainer
      title="商品管理"
      subtitle="商品・サービスの登録と管理"
      actions={
        <div className="flex items-center space-x-3">
          {/* 表示モード切り替え */}
          <div className="flex border rounded-md">
            <Button
              size="sm"
              variant={viewMode === 'list' ? 'primary' : 'ghost'}
              onClick={() => setViewMode('list')}
              className="rounded-r-none"
            >
              <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 10h16M4 14h16M4 18h16" />
              </svg>
            </Button>
            <Button
              size="sm"
              variant={viewMode === 'grid' ? 'primary' : 'ghost'}
              onClick={() => setViewMode('grid')}
              className="rounded-l-none border-l"
            >
              <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z" />
              </svg>
            </Button>
          </div>

          {hasPermission('products.create') && (
            <Button onClick={() => setShowCreateModal(true)}>
              <svg className="h-4 w-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
              </svg>
              新規商品登録
            </Button>
          )}
        </div>
      }
    >
      <CardLayout>
        {/* フィルター */}
        <div className="flex flex-col sm:flex-row gap-4 mb-6">
          <div className="flex-1">
            <Input
              placeholder="商品名、コード、ブランド、タグで検索..."
              value={searchValue}
              onChange={(e) => setSearchValue(e.target.value)}
              className="w-full"
            />
          </div>
          <div className="flex gap-3">
            <Select
              placeholder="カテゴリ"
              value={categoryFilter}
              onChange={setCategoryFilter}
              allowClear
              className="w-40"
            >
              {mockCategories.map(category => (
                <Select.Option key={category.id} value={category.id}>
                  {category.name}
                </Select.Option>
              ))}
            </Select>
            <Select
              placeholder="ステータス"
              value={statusFilter}
              onChange={setStatusFilter}
              allowClear
              className="w-32"
            >
              <Select.Option value="active">アクティブ</Select.Option>
              <Select.Option value="inactive">無効</Select.Option>
              <Select.Option value="discontinued">廃止</Select.Option>
            </Select>
          </div>
        </div>

        {/* 一括操作バー */}
        {selectedIds.length > 0 && (
          <div className="flex items-center justify-between bg-blue-50 border border-blue-200 rounded-lg px-4 py-3 mb-4">
            <span className="text-sm text-blue-700">
              {selectedIds.length}件の商品が選択されています
            </span>
            <div className="flex space-x-2">
              <Button size="sm" variant="ghost" onClick={() => setSelectedIds([])}>
                選択解除
              </Button>
              {hasPermission('products.delete') && (
                <Button size="sm" variant="ghost" onClick={handleBulkDelete} className="text-red-600">
                  一括削除
                </Button>
              )}
            </div>
          </div>
        )}

        {/* 商品表示 */}
        {viewMode === 'list' ? (
          <DataTable
            columns={columns}
            dataSource={filteredProducts}
            rowKey="id"
            pagination={{
              total: filteredProducts.length,
              pageSize: 20,
              showSizeChanger: true,
              showQuickJumper: true,
            }}
            selection={{
              selectedRowKeys: selectedIds,
              onChange: setSelectedIds,
            }}
          />
        ) : (
          renderGridView()
        )}
      </CardLayout>

      {/* 商品作成/編集モーダル */}
      <Modal
        isOpen={showCreateModal || showEditModal}
        onClose={() => {
          setShowCreateModal(false);
          setShowEditModal(false);
          resetForm();
        }}
        title={showCreateModal ? '新規商品登録' : '商品編集'}
        size="xl"
      >
        <form onSubmit={handleSubmit} className="space-y-6">
          {/* 基本情報 */}
          <div>
            <h4 className="text-lg font-medium mb-3">基本情報</h4>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  商品コード *
                </label>
                <Input
                  value={formData.code}
                  onChange={(e) => setFormData(prev => ({ ...prev, code: e.target.value.toUpperCase() }))}
                  placeholder="例: PROD-001"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  商品名 *
                </label>
                <Input
                  value={formData.name}
                  onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
                  placeholder="商品名を入力"
                  required
                />
              </div>
              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  商品説明
                </label>
                <textarea
                  value={formData.description}
                  onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
                  placeholder="商品の説明を入力"
                  rows={3}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  カテゴリ *
                </label>
                <Select
                  value={formData.categoryId}
                  onChange={(value) => setFormData(prev => ({ ...prev, categoryId: value }))}
                  placeholder="カテゴリを選択"
                  required
                >
                  {mockCategories.map(category => (
                    <Select.Option key={category.id} value={category.id}>
                      {category.name}
                    </Select.Option>
                  ))}
                </Select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  ステータス
                </label>
                <Select
                  value={formData.status}
                  onChange={(value) => setFormData(prev => ({ ...prev, status: value as Product['status'] }))}
                >
                  <Select.Option value="active">アクティブ</Select.Option>
                  <Select.Option value="inactive">無効</Select.Option>
                  <Select.Option value="discontinued">廃止</Select.Option>
                </Select>
              </div>
            </div>
          </div>

          {/* 価格情報 */}
          <div>
            <h4 className="text-lg font-medium mb-3">価格情報</h4>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  販売価格 *
                </label>
                <Input
                  type="number"
                  min="0"
                  value={formData.price}
                  onChange={(e) => setFormData(prev => ({ ...prev, price: parseInt(e.target.value) || 0 }))}
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  仕入価格
                </label>
                <Input
                  type="number"
                  min="0"
                  value={formData.costPrice}
                  onChange={(e) => setFormData(prev => ({ ...prev, costPrice: parseInt(e.target.value) || 0 }))}
                />
              </div>
              <div className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  id="isTaxable"
                  checked={formData.isTaxable}
                  onChange={(e) => setFormData(prev => ({ ...prev, isTaxable: e.target.checked }))}
                  className="w-4 h-4 text-blue-600"
                />
                <label htmlFor="isTaxable" className="text-sm font-medium text-gray-700">
                  課税対象
                </label>
              </div>
              {formData.isTaxable && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    税率 (%)
                  </label>
                  <Input
                    type="number"
                    min="0"
                    max="100"
                    step="0.1"
                    value={formData.taxRate}
                    onChange={(e) => setFormData(prev => ({ ...prev, taxRate: parseFloat(e.target.value) || 0 }))}
                  />
                </div>
              )}
            </div>
          </div>

          {/* 在庫情報 */}
          <div>
            <div className="flex items-center space-x-2 mb-3">
              <input
                type="checkbox"
                id="isService"
                checked={formData.isService}
                onChange={(e) => setFormData(prev => ({ ...prev, isService: e.target.checked }))}
                className="w-4 h-4 text-blue-600"
              />
              <label htmlFor="isService" className="text-lg font-medium text-gray-900">
                サービス商品（在庫管理不要）
              </label>
            </div>
            
            {!formData.isService && (
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    現在在庫数
                  </label>
                  <Input
                    type="number"
                    min="0"
                    value={formData.stockQuantity}
                    onChange={(e) => setFormData(prev => ({ ...prev, stockQuantity: parseInt(e.target.value) || 0 }))}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    最小在庫レベル
                  </label>
                  <Input
                    type="number"
                    min="0"
                    value={formData.minStockLevel}
                    onChange={(e) => setFormData(prev => ({ ...prev, minStockLevel: parseInt(e.target.value) || 0 }))}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    最大在庫レベル
                  </label>
                  <Input
                    type="number"
                    min="0"
                    value={formData.maxStockLevel}
                    onChange={(e) => setFormData(prev => ({ ...prev, maxStockLevel: parseInt(e.target.value) || 0 }))}
                  />
                </div>
              </div>
            )}
            
            <div className="mt-4">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                単位
              </label>
              <Select
                value={formData.unit}
                onChange={(value) => setFormData(prev => ({ ...prev, unit: value }))}
              >
                <Select.Option value="piece">個</Select.Option>
                <Select.Option value="unit">台</Select.Option>
                <Select.Option value="set">セット</Select.Option>
                <Select.Option value="kg">kg</Select.Option>
                <Select.Option value="liter">リットル</Select.Option>
                <Select.Option value="meter">メートル</Select.Option>
                <Select.Option value="hour">時間</Select.Option>
                <Select.Option value="day">日</Select.Option>
                <Select.Option value="month">月</Select.Option>
              </Select>
            </div>
          </div>

          {/* その他情報 */}
          <div>
            <h4 className="text-lg font-medium mb-3">その他情報</h4>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  ブランド
                </label>
                <Input
                  value={formData.brand}
                  onChange={(e) => setFormData(prev => ({ ...prev, brand: e.target.value }))}
                  placeholder="例: Apple, Dell, Microsoft"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  モデル
                </label>
                <Input
                  value={formData.model}
                  onChange={(e) => setFormData(prev => ({ ...prev, model: e.target.value }))}
                  placeholder="例: MacBook Pro, XPS 13"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  重量 (kg)
                </label>
                <Input
                  type="number"
                  min="0"
                  step="0.001"
                  value={formData.weight || ''}
                  onChange={(e) => setFormData(prev => ({ ...prev, weight: parseFloat(e.target.value) || null }))}
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  サイズ
                </label>
                <Input
                  value={formData.dimensions}
                  onChange={(e) => setFormData(prev => ({ ...prev, dimensions: e.target.value }))}
                  placeholder="例: 300 x 200 x 15 mm"
                />
              </div>
              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  バーコード/JAN
                </label>
                <Input
                  value={formData.barcode}
                  onChange={(e) => setFormData(prev => ({ ...prev, barcode: e.target.value }))}
                  placeholder="例: 4901234567890"
                />
              </div>
            </div>
          </div>

          <div className="flex justify-end space-x-3 pt-4 border-t">
            <Button 
              type="button" 
              variant="ghost" 
              onClick={() => {
                setShowCreateModal(false);
                setShowEditModal(false);
                resetForm();
              }}
            >
              キャンセル
            </Button>
            <Button type="submit" disabled={loading}>
              {loading ? (showCreateModal ? '登録中...' : '更新中...') : (showCreateModal ? '登録' : '更新')}
            </Button>
          </div>
        </form>
      </Modal>

      {/* 画像表示モーダル */}
      <Modal
        isOpen={showImageModal}
        onClose={() => setShowImageModal(false)}
        title="商品画像"
        size="lg"
      >
        <div className="text-center">
          <img
            src={viewingImage}
            alt="商品画像"
            className="max-w-full max-h-96 mx-auto rounded-lg"
          />
        </div>
      </Modal>
    </PageContainer>
  );
};