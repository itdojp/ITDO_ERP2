import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { Button } from '../../components/ui/Button';
import { Input } from '../../components/ui/Input';
import { Select } from '../../components/ui/Select';
import { Badge } from '../../components/ui/Badge';
import { PageContainer, CardLayout, GridLayout } from '../../layouts/MainLayout/MainLayout';
import { useAuth } from '../../hooks/useAuth';

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
  images: string[];
  status: 'active' | 'inactive' | 'discontinued';
  isService: boolean;
  isTaxable: boolean;
  taxRate: number;
  weight?: number;
  dimensions?: string;
  barcode?: string;
  supplierIds: string[];
  tags: string[];
  specifications: Record<string, string>;
  notes: string;
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
  specifications: Record<string, string>;
  notes: string;
}

interface Category {
  id: string;
  name: string;
  code: string;
  parentId?: string;
}

interface Supplier {
  id: string;
  name: string;
  code: string;
}

export const ProductForm: React.FC = () => {
  const navigate = useNavigate();
  const { id } = useParams<{ id: string }>();
  const { hasPermission } = useAuth();

  const isEditMode = Boolean(id);
  const [loading, setLoading] = useState(false);
  const [submitLoading, setSaveLoading] = useState(false);
  const [imageUploadLoading, setImageUploadLoading] = useState(false);
  const [activeTab, setActiveTab] = useState<'basic' | 'inventory' | 'pricing' | 'specifications' | 'images'>('basic');
  const [product, setProduct] = useState<Product | null>(null);
  
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
    specifications: {},
    notes: '',
  });

  const [errors, setErrors] = useState<Record<string, string>>({});
  const [newTag, setNewTag] = useState('');
  const [newSpecKey, setNewSpecKey] = useState('');
  const [newSpecValue, setNewSpecValue] = useState('');
  const [selectedImages, setSelectedImages] = useState<File[]>([]);
  const [previewImages, setPreviewImages] = useState<string[]>([]);

  // モックデータ
  const mockCategories: Category[] = [
    { id: 'cat-1', name: 'ノートパソコン', code: 'LAPTOP' },
    { id: 'cat-2', name: 'モニター', code: 'MONITOR' },
    { id: 'cat-3', name: 'サービス', code: 'SERVICE' },
    { id: 'cat-4', name: '周辺機器', code: 'ACCESSORY' },
    { id: 'cat-5', name: 'ソフトウェア', code: 'SOFTWARE' },
  ];

  const mockSuppliers: Supplier[] = [
    { id: 'sup-1', name: 'レノボ・ジャパン合同会社', code: 'LENOVO' },
    { id: 'sup-2', name: 'デル・テクノロジーズ株式会社', code: 'DELL' },
    { id: 'sup-3', name: 'PFUダイレクト', code: 'PFU' },
    { id: 'sup-4', name: 'Apple Japan合同会社', code: 'APPLE' },
    { id: 'sup-5', name: 'Anker Japan株式会社', code: 'ANKER' },
  ];

  // 商品データの読み込み
  useEffect(() => {
    if (isEditMode && id) {
      loadProduct(id);
    }
  }, [id, isEditMode]);

  const loadProduct = async (productId: string) => {
    setLoading(true);
    try {
      // モック商品データ（実際にはAPIから取得）
      const mockProduct: Product = {
        id: productId,
        code: 'LT-001',
        name: 'ThinkPad X1 Carbon',
        description: 'プレミアムビジネスラップトップ。軽量でありながら高い堅牢性を実現。14インチWUXGA液晶搭載。',
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
        images: [
          'https://via.placeholder.com/400x300?text=ThinkPad+Front',
          'https://via.placeholder.com/400x300?text=ThinkPad+Side',
          'https://via.placeholder.com/400x300?text=ThinkPad+Open',
        ],
        status: 'active',
        isService: false,
        isTaxable: true,
        taxRate: 10,
        weight: 1.12,
        dimensions: '314.5 x 221.6 x 14.9 mm',
        barcode: '4562123456789',
        supplierIds: ['sup-1'],
        tags: ['premium', 'business', 'ultrabook'],
        specifications: {
          'CPU': 'Intel Core i7-1355U',
          'メモリ': '16GB LPDDR5',
          'ストレージ': '512GB SSD',
          '画面サイズ': '14インチ',
          '解像度': '1920x1200 (WUXGA)',
          'OS': 'Windows 11 Pro',
          'バッテリー': '最大18時間',
          'インターフェース': 'USB-A×2, Thunderbolt 4×2, HDMI',
        },
        notes: '企業向け推奨モデル。3年保証付き。',
        createdAt: '2024-01-15',
        updatedAt: '2024-01-20',
        createdBy: 'admin',
      };

      await new Promise(resolve => setTimeout(resolve, 800));
      setProduct(mockProduct);
      setFormData({
        code: mockProduct.code,
        name: mockProduct.name,
        description: mockProduct.description,
        categoryId: mockProduct.categoryId,
        price: mockProduct.price,
        costPrice: mockProduct.costPrice,
        stockQuantity: mockProduct.stockQuantity,
        minStockLevel: mockProduct.minStockLevel,
        maxStockLevel: mockProduct.maxStockLevel,
        unit: mockProduct.unit,
        brand: mockProduct.brand || '',
        model: mockProduct.model || '',
        status: mockProduct.status,
        isService: mockProduct.isService,
        isTaxable: mockProduct.isTaxable,
        taxRate: mockProduct.taxRate,
        weight: mockProduct.weight || null,
        dimensions: mockProduct.dimensions || '',
        barcode: mockProduct.barcode || '',
        tags: mockProduct.tags,
        specifications: mockProduct.specifications,
        notes: mockProduct.notes,
      });
    } catch (error) {
      console.error('商品データの読み込みに失敗しました:', error);
    } finally {
      setLoading(false);
    }
  };

  // フォーム送信
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    // バリデーション
    const newErrors: Record<string, string> = {};
    if (!formData.code) newErrors.code = '商品コードは必須です';
    if (!formData.name) newErrors.name = '商品名は必須です';
    if (!formData.categoryId) newErrors.categoryId = 'カテゴリは必須です';
    if (formData.price <= 0) newErrors.price = '販売価格は0より大きい値を入力してください';

    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors);
      return;
    }

    setSaveLoading(true);
    try {
      // モックAPI呼び出し
      await new Promise(resolve => setTimeout(resolve, 1500));
      navigate('/products');
    } catch (error) {
      console.error('保存に失敗しました:', error);
    } finally {
      setSaveLoading(false);
    }
  };

  // タグ追加
  const handleAddTag = useCallback(() => {
    if (newTag && !formData.tags.includes(newTag)) {
      setFormData(prev => ({
        ...prev,
        tags: [...prev.tags, newTag]
      }));
      setNewTag('');
    }
  }, [newTag, formData.tags]);

  // タグ削除
  const handleRemoveTag = useCallback((tag: string) => {
    setFormData(prev => ({
      ...prev,
      tags: prev.tags.filter(t => t !== tag)
    }));
  }, []);

  // 仕様追加
  const handleAddSpecification = useCallback(() => {
    if (newSpecKey && newSpecValue) {
      setFormData(prev => ({
        ...prev,
        specifications: {
          ...prev.specifications,
          [newSpecKey]: newSpecValue
        }
      }));
      setNewSpecKey('');
      setNewSpecValue('');
    }
  }, [newSpecKey, newSpecValue]);

  // 仕様削除
  const handleRemoveSpecification = useCallback((key: string) => {
    setFormData(prev => ({
      ...prev,
      specifications: Object.fromEntries(
        Object.entries(prev.specifications).filter(([k]) => k !== key)
      )
    }));
  }, []);

  // 画像アップロード
  const handleImageUpload = useCallback(async (files: FileList | null) => {
    if (!files) return;
    
    setImageUploadLoading(true);
    try {
      const newImages = Array.from(files).slice(0, 5); // 最大5枚
      setSelectedImages(prev => [...prev, ...newImages].slice(0, 5));
      
      // プレビュー用URL作成
      const previews = newImages.map(file => URL.createObjectURL(file));
      setPreviewImages(prev => [...prev, ...previews].slice(0, 5));
      
      // モック画像アップロード処理
      await new Promise(resolve => setTimeout(resolve, 1000));
    } catch (error) {
      console.error('画像アップロードに失敗しました:', error);
    } finally {
      setImageUploadLoading(false);
    }
  }, []);

  // 画像削除
  const handleRemoveImage = useCallback((index: number) => {
    setSelectedImages(prev => prev.filter((_, i) => i !== index));
    setPreviewImages(prev => {
      URL.revokeObjectURL(prev[index]); // メモリリーク防止
      return prev.filter((_, i) => i !== index);
    });
  }, []);

  const tabs = [
    { id: 'basic', label: '基本情報', icon: '📝' },
    { id: 'pricing', label: '価格設定', icon: '💰' },
    { id: 'inventory', label: '在庫管理', icon: '📦' },
    { id: 'specifications', label: '仕様・詳細', icon: '🔧' },
    { id: 'images', label: '画像管理', icon: '🖼️' },
  ] as const;

  if (loading) {
    return (
      <PageContainer title="商品情報">
        <CardLayout>
          <div className="text-center py-8">
            <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            <p className="mt-2 text-gray-500">データを読み込み中...</p>
          </div>
        </CardLayout>
      </PageContainer>
    );
  }

  return (
    <PageContainer
      title={isEditMode ? `商品編集: ${product?.name}` : '新規商品登録'}
      subtitle={isEditMode ? `商品コード: ${product?.code}` : '商品情報を入力してください'}
      actions={
        <div className="flex items-center space-x-3">
          <Button variant="ghost" onClick={() => navigate('/products')}>
            <svg className="h-4 w-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
            </svg>
            戻る
          </Button>
          <Button onClick={handleSubmit} disabled={submitLoading}>
            {submitLoading ? (
              <div className="flex items-center">
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                {isEditMode ? '更新中...' : '登録中...'}
              </div>
            ) : (
              isEditMode ? '更新' : '登録'
            )}
          </Button>
        </div>
      }
    >
      <form onSubmit={handleSubmit}>
        <GridLayout cols={{ default: 1, lg: 4 }} gap="lg">
          {/* タブナビゲーション */}
          <div className="lg:col-span-1">
            <CardLayout>
              <nav className="space-y-1">
                {tabs.map(tab => (
                  <button
                    key={tab.id}
                    type="button"
                    className={`
                      w-full flex items-center px-3 py-2 text-sm font-medium rounded-md transition-colors
                      ${activeTab === tab.id
                        ? 'bg-blue-50 text-blue-700 border-r-2 border-blue-600'
                        : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
                      }
                    `}
                    onClick={() => setActiveTab(tab.id)}
                  >
                    <span className="mr-3">{tab.icon}</span>
                    {tab.label}
                  </button>
                ))}
              </nav>
            </CardLayout>
          </div>

          {/* メインコンテンツ */}
          <div className="lg:col-span-3">
            <CardLayout>
              {/* 基本情報タブ */}
              {activeTab === 'basic' && (
                <div className="space-y-6">
                  <div>
                    <h3 className="text-lg font-medium mb-4">基本情報</h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          商品コード *
                        </label>
                        <Input
                          value={formData.code}
                          onChange={(e) => {
                            setFormData(prev => ({ ...prev, code: e.target.value.toUpperCase() }));
                            if (errors.code) setErrors(prev => ({ ...prev, code: '' }));
                          }}
                          placeholder="例: PROD-001"
                          error={errors.code}
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          商品名 *
                        </label>
                        <Input
                          value={formData.name}
                          onChange={(e) => {
                            setFormData(prev => ({ ...prev, name: e.target.value }));
                            if (errors.name) setErrors(prev => ({ ...prev, name: '' }));
                          }}
                          placeholder="商品名を入力"
                          error={errors.name}
                        />
                      </div>
                      <div className="md:col-span-2">
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          商品説明
                        </label>
                        <textarea
                          value={formData.description}
                          onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
                          placeholder="商品の詳細な説明を入力してください"
                          rows={4}
                          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          カテゴリ *
                        </label>
                        <Select
                          value={formData.categoryId}
                          onChange={(value) => {
                            setFormData(prev => ({ ...prev, categoryId: value }));
                            if (errors.categoryId) setErrors(prev => ({ ...prev, categoryId: '' }));
                          }}
                          placeholder="カテゴリを選択"
                          error={errors.categoryId}
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
                    </div>
                  </div>

                  {/* タグ */}
                  <div>
                    <h4 className="text-md font-medium mb-3">タグ</h4>
                    <div className="flex flex-wrap gap-2 mb-3">
                      {formData.tags.map(tag => (
                        <Badge key={tag} variant="info" className="cursor-pointer" onClick={() => handleRemoveTag(tag)}>
                          {tag} ×
                        </Badge>
                      ))}
                    </div>
                    <div className="flex gap-2">
                      <Input
                        value={newTag}
                        onChange={(e) => setNewTag(e.target.value)}
                        placeholder="タグを入力"
                        onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), handleAddTag())}
                      />
                      <Button type="button" onClick={handleAddTag} disabled={!newTag}>
                        追加
                      </Button>
                    </div>
                  </div>
                </div>
              )}

              {/* 価格設定タブ */}
              {activeTab === 'pricing' && (
                <div className="space-y-6">
                  <div>
                    <h3 className="text-lg font-medium mb-4">価格設定</h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          販売価格 * (税抜)
                        </label>
                        <Input
                          type="number"
                          min="0"
                          value={formData.price}
                          onChange={(e) => {
                            setFormData(prev => ({ ...prev, price: parseInt(e.target.value) || 0 }));
                            if (errors.price) setErrors(prev => ({ ...prev, price: '' }));
                          }}
                          error={errors.price}
                        />
                        <p className="text-sm text-gray-500 mt-1">
                          税込価格: ¥{formData.isTaxable ? (formData.price * (1 + formData.taxRate / 100)).toLocaleString() : formData.price.toLocaleString()}
                        </p>
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          仕入価格 (税抜)
                        </label>
                        <Input
                          type="number"
                          min="0"
                          value={formData.costPrice}
                          onChange={(e) => setFormData(prev => ({ ...prev, costPrice: parseInt(e.target.value) || 0 }))}
                        />
                        <p className="text-sm text-gray-500 mt-1">
                          利益率: {formData.price > 0 ? ((formData.price - formData.costPrice) / formData.price * 100).toFixed(1) : 0}%
                        </p>
                      </div>
                    </div>
                  </div>

                  <div>
                    <h4 className="text-md font-medium mb-3">税金設定</h4>
                    <div className="space-y-4">
                      <div className="flex items-center space-x-2">
                        <input
                          type="checkbox"
                          id="isTaxable"
                          checked={formData.isTaxable}
                          onChange={(e) => setFormData(prev => ({ ...prev, isTaxable: e.target.checked }))}
                          className="w-4 h-4 text-blue-600"
                        />
                        <label htmlFor="isTaxable" className="text-sm font-medium text-gray-700">
                          課税対象商品
                        </label>
                      </div>
                      {formData.isTaxable && (
                        <div className="max-w-xs">
                          <label className="block text-sm font-medium text-gray-700 mb-1">
                            税率 (%)
                          </label>
                          <Select
                            value={formData.taxRate.toString()}
                            onChange={(value) => setFormData(prev => ({ ...prev, taxRate: parseFloat(value) }))}
                          >
                            <Select.Option value="8">8% (軽減税率)</Select.Option>
                            <Select.Option value="10">10% (標準税率)</Select.Option>
                          </Select>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              )}

              {/* 在庫管理タブ */}
              {activeTab === 'inventory' && (
                <div className="space-y-6">
                  <div>
                    <h3 className="text-lg font-medium mb-4">在庫管理</h3>
                    <div className="mb-4">
                      <div className="flex items-center space-x-2 mb-4">
                        <input
                          type="checkbox"
                          id="isService"
                          checked={formData.isService}
                          onChange={(e) => setFormData(prev => ({ ...prev, isService: e.target.checked }))}
                          className="w-4 h-4 text-blue-600"
                        />
                        <label htmlFor="isService" className="text-sm font-medium text-gray-700">
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
                            <p className="text-xs text-gray-500 mt-1">この数量を下回ると警告</p>
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
                            <p className="text-xs text-gray-500 mt-1">推奨最大在庫数</p>
                          </div>
                        </div>
                      )}
                      
                      <div className="mt-4 max-w-xs">
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
                  </div>

                  <div>
                    <h4 className="text-md font-medium mb-3">物理属性</h4>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
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
                          サイズ (W×D×H)
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
                </div>
              )}

              {/* 仕様・詳細タブ */}
              {activeTab === 'specifications' && (
                <div className="space-y-6">
                  <div>
                    <h3 className="text-lg font-medium mb-4">技術仕様</h3>
                    <div className="space-y-3 mb-4">
                      {Object.entries(formData.specifications).map(([key, value]) => (
                        <div key={key} className="flex items-center space-x-3 p-3 bg-gray-50 rounded-lg">
                          <div className="flex-1">
                            <span className="font-medium">{key}:</span> {value}
                          </div>
                          <Button
                            type="button"
                            size="sm"
                            variant="ghost"
                            onClick={() => handleRemoveSpecification(key)}
                            className="text-red-600"
                          >
                            削除
                          </Button>
                        </div>
                      ))}
                    </div>
                    
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                      <Input
                        value={newSpecKey}
                        onChange={(e) => setNewSpecKey(e.target.value)}
                        placeholder="項目名 (例: CPU)"
                      />
                      <Input
                        value={newSpecValue}
                        onChange={(e) => setNewSpecValue(e.target.value)}
                        placeholder="値 (例: Intel Core i7)"
                      />
                      <Button
                        type="button"
                        onClick={handleAddSpecification}
                        disabled={!newSpecKey || !newSpecValue}
                      >
                        追加
                      </Button>
                    </div>
                  </div>

                  <div>
                    <h4 className="text-md font-medium mb-3">備考・メモ</h4>
                    <textarea
                      value={formData.notes}
                      onChange={(e) => setFormData(prev => ({ ...prev, notes: e.target.value }))}
                      placeholder="商品に関する追加情報やメモを入力してください"
                      rows={6}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                </div>
              )}

              {/* 画像管理タブ */}
              {activeTab === 'images' && (
                <div className="space-y-6">
                  <div>
                    <h3 className="text-lg font-medium mb-4">商品画像</h3>
                    
                    {/* 既存画像（編集時） */}
                    {isEditMode && product?.images && product.images.length > 0 && (
                      <div className="mb-6">
                        <h4 className="text-md font-medium mb-3">現在の画像</h4>
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                          {product.images.map((imageUrl, index) => (
                            <div key={index} className="relative">
                              <img
                                src={imageUrl}
                                alt={`商品画像 ${index + 1}`}
                                className="w-full h-32 object-cover rounded-lg border"
                              />
                              <Button
                                type="button"
                                size="sm"
                                variant="ghost"
                                className="absolute top-1 right-1 bg-red-600 text-white hover:bg-red-700"
                                onClick={() => {/* 画像削除処理 */}}
                              >
                                ×
                              </Button>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* 新しい画像のアップロード */}
                    <div>
                      <h4 className="text-md font-medium mb-3">新しい画像をアップロード</h4>
                      <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center">
                        <input
                          type="file"
                          multiple
                          accept="image/*"
                          onChange={(e) => handleImageUpload(e.target.files)}
                          className="hidden"
                          id="image-upload"
                          disabled={imageUploadLoading}
                        />
                        <label htmlFor="image-upload" className="cursor-pointer">
                          <svg className="mx-auto h-12 w-12 text-gray-400 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                          </svg>
                          <div className="text-sm text-gray-600">
                            {imageUploadLoading ? (
                              <span>アップロード中...</span>
                            ) : (
                              <>
                                <span className="font-medium text-blue-600">クリックしてファイルを選択</span>
                                <span> またはドラッグ&ドロップ</span>
                              </>
                            )}
                          </div>
                          <p className="text-xs text-gray-500 mt-1">PNG, JPG, GIF (最大5MB, 5枚まで)</p>
                        </label>
                      </div>

                      {/* プレビュー画像 */}
                      {previewImages.length > 0 && (
                        <div className="mt-4">
                          <h5 className="text-sm font-medium mb-2">プレビュー</h5>
                          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                            {previewImages.map((imageUrl, index) => (
                              <div key={index} className="relative">
                                <img
                                  src={imageUrl}
                                  alt={`プレビュー ${index + 1}`}
                                  className="w-full h-32 object-cover rounded-lg border"
                                />
                                <Button
                                  type="button"
                                  size="sm"
                                  variant="ghost"
                                  className="absolute top-1 right-1 bg-red-600 text-white hover:bg-red-700"
                                  onClick={() => handleRemoveImage(index)}
                                >
                                  ×
                                </Button>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              )}
            </CardLayout>
          </div>
        </GridLayout>
      </form>
    </PageContainer>
  );
};