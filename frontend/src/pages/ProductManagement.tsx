import React, { useState, useCallback, useMemo, useRef } from 'react';
import { cn } from '@/lib/utils';
import { EnhancedDataTable } from '@/components/ui/EnhancedDataTable';
import { FormBuilder } from '@/components/ui/FormBuilder';
import { ChartSystem } from '@/components/ui/ChartSystem';
import { AnalyticsDashboard } from '@/components/ui/AnalyticsDashboard';
import { Image } from '@/components/ui/Image';
import { FileUpload } from '@/components/ui/FileUpload';

export interface Product {
  id: string;
  name: string;
  sku: string;
  description?: string;
  category: string;
  subcategory?: string;
  brand?: string;
  manufacturer?: string;
  supplier?: string;
  images: string[];
  specifications: Record<string, any>;
  pricing: {
    cost: number;
    msrp: number;
    retailPrice: number;
    wholesalePrice?: number;
    discountPrice?: number;
    currency: string;
  };
  inventory: {
    quantity: number;
    reserved: number;
    available: number;
    reorderLevel: number;
    maxStock: number;
    location?: string;
  };
  dimensions?: {
    length: number;
    width: number;
    height: number;
    weight: number;
    unit: string;
  };
  status: 'active' | 'inactive' | 'discontinued' | 'out_of_stock' | 'coming_soon';
  tags?: string[];
  barcode?: string;
  warranty?: {
    duration: number;
    unit: 'days' | 'months' | 'years';
    terms?: string;
  };
  compliance?: {
    certifications: string[];
    regulations: string[];
  };
  seo?: {
    metaTitle?: string;
    metaDescription?: string;
    keywords?: string[];
  };
  createdAt: Date;
  updatedAt: Date;
  createdBy: string;
  lastModifiedBy: string;
}

export interface ProductFormData extends Omit<Product, 'id' | 'createdAt' | 'updatedAt' | 'createdBy' | 'lastModifiedBy'> {}

export interface ProductManagementProps {
  products?: Product[];
  categories?: Array<{ value: string; label: string; subcategories?: Array<{ value: string; label: string }> }>;
  brands?: Array<{ value: string; label: string }>;
  suppliers?: Array<{ value: string; label: string }>;
  manufacturers?: Array<{ value: string; label: string }>;
  locations?: Array<{ value: string; label: string }>;
  currencies?: Array<{ value: string; label: string }>;
  enableBulkActions?: boolean;
  enableImportExport?: boolean;
  enableAnalytics?: boolean;
  enableImageUpload?: boolean;
  enableInventoryTracking?: boolean;
  enablePricingHistory?: boolean;
  pageSize?: number;
  maxProducts?: number;
  readOnly?: boolean;
  className?: string;
  onProductCreate?: (product: ProductFormData) => Promise<Product>;
  onProductUpdate?: (id: string, updates: Partial<ProductFormData>) => Promise<Product>;
  onProductDelete?: (id: string | string[]) => Promise<void>;
  onProductDuplicate?: (id: string) => Promise<Product>;
  onStatusChange?: (id: string, status: Product['status']) => Promise<void>;
  onInventoryUpdate?: (id: string, quantity: number, location?: string) => Promise<void>;
  onPriceUpdate?: (id: string, pricing: Partial<Product['pricing']>) => Promise<void>;
  onImageUpload?: (productId: string, files: File[]) => Promise<string[]>;
  onImageDelete?: (productId: string, imageUrl: string) => Promise<void>;
  onBulkAction?: (action: string, productIds: string[], data?: any) => Promise<void>;
  onExport?: (format: 'csv' | 'xlsx' | 'json') => Promise<void>;
  onImport?: (file: File) => Promise<{ success: number; errors: string[] }>;
  onError?: (error: Error) => void;
  'data-testid'?: string;
}

export const ProductManagement: React.FC<ProductManagementProps> = ({
  products = [],
  categories = [],
  brands = [],
  suppliers = [],
  manufacturers = [],
  locations = [],
  currencies = [
    { value: 'USD', label: 'US Dollar ($)' },
    { value: 'EUR', label: 'Euro (€)' },
    { value: 'GBP', label: 'British Pound (£)' },
    { value: 'JPY', label: 'Japanese Yen (¥)' }
  ],
  enableBulkActions = true,
  enableImportExport = true,
  enableAnalytics = true,
  enableImageUpload = true,
  enableInventoryTracking = true,
  enablePricingHistory = true,
  pageSize = 25,
  maxProducts = 50000,
  readOnly = false,
  className,
  onProductCreate,
  onProductUpdate,
  onProductDelete,
  onProductDuplicate,
  onStatusChange,
  onInventoryUpdate,
  onPriceUpdate,
  onImageUpload,
  onImageDelete,
  onBulkAction,
  onExport,
  onImport,
  onError,
  'data-testid': dataTestId = 'product-management'
}) => {
  const [activeTab, setActiveTab] = useState<'products' | 'analytics' | 'inventory'>('products');
  const [selectedProducts, setSelectedProducts] = useState<string[]>([]);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [showEditForm, setShowEditForm] = useState(false);
  const [editingProduct, setEditingProduct] = useState<Product | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [filters, setFilters] = useState<{
    category?: string;
    brand?: string;
    status?: string;
    supplier?: string;
    priceRange?: { min: number; max: number };
    stockLevel?: 'in_stock' | 'low_stock' | 'out_of_stock';
  }>({});
  const [isLoading, setIsLoading] = useState(false);
  const [viewMode, setViewMode] = useState<'table' | 'grid'>('table');
  const [showImageGallery, setShowImageGallery] = useState(false);
  const [selectedProductImages, setSelectedProductImages] = useState<string[]>([]);

  const fileInputRef = useRef<HTMLInputElement>(null);

  // Filter products based on search and filters
  const filteredProducts = useMemo(() => {
    let filtered = [...products];

    // Apply search
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(product =>
        product.name.toLowerCase().includes(query) ||
        product.sku.toLowerCase().includes(query) ||
        product.description?.toLowerCase().includes(query) ||
        product.brand?.toLowerCase().includes(query) ||
        product.category.toLowerCase().includes(query) ||
        product.tags?.some(tag => tag.toLowerCase().includes(query))
      );
    }

    // Apply filters
    if (filters.category) {
      filtered = filtered.filter(product => product.category === filters.category);
    }

    if (filters.brand) {
      filtered = filtered.filter(product => product.brand === filters.brand);
    }

    if (filters.status) {
      filtered = filtered.filter(product => product.status === filters.status);
    }

    if (filters.supplier) {
      filtered = filtered.filter(product => product.supplier === filters.supplier);
    }

    if (filters.priceRange) {
      filtered = filtered.filter(product => 
        product.pricing.retailPrice >= filters.priceRange!.min &&
        product.pricing.retailPrice <= filters.priceRange!.max
      );
    }

    if (filters.stockLevel) {
      filtered = filtered.filter(product => {
        const { quantity, reorderLevel } = product.inventory;
        switch (filters.stockLevel) {
          case 'out_of_stock':
            return quantity === 0;
          case 'low_stock':
            return quantity > 0 && quantity <= reorderLevel;
          case 'in_stock':
            return quantity > reorderLevel;
          default:
            return true;
        }
      });
    }

    return filtered;
  }, [products, searchQuery, filters]);

  // Product form fields
  const productFormFields = useMemo(() => [
    {
      id: 'basic-section',
      type: 'section' as const,
      label: 'Basic Information',
      description: 'Product identification and basic details'
    },
    {
      id: 'name',
      type: 'text' as const,
      label: 'Product Name',
      placeholder: 'Enter product name',
      required: true,
      validation: { minLength: 2, maxLength: 200 }
    },
    {
      id: 'sku',
      type: 'text' as const,
      label: 'SKU',
      placeholder: 'PRD001',
      required: true,
      validation: { pattern: '^[A-Z0-9-]+$' }
    },
    {
      id: 'description',
      type: 'textarea' as const,
      label: 'Description',
      placeholder: 'Product description...',
      rows: 4,
      validation: { maxLength: 2000 }
    },
    {
      id: 'category',
      type: 'select' as const,
      label: 'Category',
      options: categories,
      required: true
    },
    {
      id: 'subcategory',
      type: 'select' as const,
      label: 'Subcategory',
      options: [] // Will be populated based on category selection
    },
    {
      id: 'brand',
      type: 'select' as const,
      label: 'Brand',
      options: [{ value: '', label: 'No Brand' }, ...brands]
    },
    {
      id: 'manufacturer',
      type: 'select' as const,
      label: 'Manufacturer',
      options: [{ value: '', label: 'Not specified' }, ...manufacturers]
    },
    {
      id: 'supplier',
      type: 'select' as const,
      label: 'Supplier',
      options: [{ value: '', label: 'Not specified' }, ...suppliers]
    },
    {
      id: 'barcode',
      type: 'text' as const,
      label: 'Barcode',
      placeholder: '123456789012'
    },
    {
      id: 'pricing-section',
      type: 'section' as const,
      label: 'Pricing Information',
      description: 'Cost and pricing details'
    },
    {
      id: 'pricing.cost',
      type: 'number' as const,
      label: 'Cost Price',
      placeholder: '0.00',
      min: 0,
      step: 0.01,
      required: true
    },
    {
      id: 'pricing.msrp',
      type: 'number' as const,
      label: 'MSRP',
      placeholder: '0.00',
      min: 0,
      step: 0.01,
      required: true
    },
    {
      id: 'pricing.retailPrice',
      type: 'number' as const,
      label: 'Retail Price',
      placeholder: '0.00',
      min: 0,
      step: 0.01,
      required: true
    },
    {
      id: 'pricing.wholesalePrice',
      type: 'number' as const,
      label: 'Wholesale Price',
      placeholder: '0.00',
      min: 0,
      step: 0.01
    },
    {
      id: 'pricing.currency',
      type: 'select' as const,
      label: 'Currency',
      options: currencies,
      defaultValue: 'USD',
      required: true
    },
    ...(enableInventoryTracking ? [
      {
        id: 'inventory-section',
        type: 'section' as const,
        label: 'Inventory Management',
        description: 'Stock levels and inventory settings'
      },
      {
        id: 'inventory.quantity',
        type: 'number' as const,
        label: 'Current Stock',
        placeholder: '0',
        min: 0,
        step: 1,
        required: true
      },
      {
        id: 'inventory.reorderLevel',
        type: 'number' as const,
        label: 'Reorder Level',
        placeholder: '10',
        min: 0,
        step: 1,
        required: true
      },
      {
        id: 'inventory.maxStock',
        type: 'number' as const,
        label: 'Maximum Stock',
        placeholder: '1000',
        min: 0,
        step: 1
      },
      {
        id: 'inventory.location',
        type: 'select' as const,
        label: 'Storage Location',
        options: [{ value: '', label: 'Not specified' }, ...locations]
      }
    ] : []),
    {
      id: 'physical-section',
      type: 'section' as const,
      label: 'Physical Properties',
      description: 'Dimensions and weight'
    },
    {
      id: 'dimensions.length',
      type: 'number' as const,
      label: 'Length',
      placeholder: '0',
      min: 0,
      step: 0.01
    },
    {
      id: 'dimensions.width',
      type: 'number' as const,
      label: 'Width',
      placeholder: '0',
      min: 0,
      step: 0.01
    },
    {
      id: 'dimensions.height',
      type: 'number' as const,
      label: 'Height',
      placeholder: '0',
      min: 0,
      step: 0.01
    },
    {
      id: 'dimensions.weight',
      type: 'number' as const,
      label: 'Weight',
      placeholder: '0',
      min: 0,
      step: 0.01
    },
    {
      id: 'dimensions.unit',
      type: 'select' as const,
      label: 'Unit',
      options: [
        { value: 'cm', label: 'Centimeters' },
        { value: 'in', label: 'Inches' },
        { value: 'm', label: 'Meters' },
        { value: 'ft', label: 'Feet' }
      ],
      defaultValue: 'cm'
    },
    {
      id: 'additional-section',
      type: 'section' as const,
      label: 'Additional Information',
      description: 'Status, tags, and warranty'
    },
    {
      id: 'status',
      type: 'select' as const,
      label: 'Status',
      options: [
        { value: 'active', label: 'Active' },
        { value: 'inactive', label: 'Inactive' },
        { value: 'discontinued', label: 'Discontinued' },
        { value: 'out_of_stock', label: 'Out of Stock' },
        { value: 'coming_soon', label: 'Coming Soon' }
      ],
      defaultValue: 'active'
    },
    {
      id: 'tags',
      type: 'multiselect' as const,
      label: 'Tags',
      options: [
        { value: 'bestseller', label: 'Bestseller' },
        { value: 'new', label: 'New' },
        { value: 'featured', label: 'Featured' },
        { value: 'sale', label: 'On Sale' },
        { value: 'premium', label: 'Premium' },
        { value: 'eco-friendly', label: 'Eco-Friendly' }
      ]
    },
    {
      id: 'warranty.duration',
      type: 'number' as const,
      label: 'Warranty Duration',
      placeholder: '12',
      min: 0,
      step: 1
    },
    {
      id: 'warranty.unit',
      type: 'select' as const,
      label: 'Warranty Unit',
      options: [
        { value: 'days', label: 'Days' },
        { value: 'months', label: 'Months' },
        { value: 'years', label: 'Years' }
      ],
      defaultValue: 'months'
    }
  ].filter(Boolean), [categories, brands, manufacturers, suppliers, locations, currencies, enableInventoryTracking]);

  // Data table columns
  const tableColumns = useMemo(() => [
    {
      key: 'image',
      title: '',
      width: 80,
      render: (_: any, product: Product) => (
        <div className="flex items-center justify-center">
          {product.images.length > 0 ? (
            <Image
              src={product.images[0]}
              alt={product.name}
              width={50}
              height={50}
              className="rounded object-cover cursor-pointer"
              onClick={() => {
                setSelectedProductImages(product.images);
                setShowImageGallery(true);
              }}
            />
          ) : (
            <div className="w-12 h-12 bg-gray-200 rounded flex items-center justify-center text-gray-400 text-xs">
              No Image
            </div>
          )}
        </div>
      )
    },
    {
      key: 'name',
      title: 'Product',
      sortable: true,
      searchable: true,
      render: (_: any, product: Product) => (
        <div>
          <div className="font-medium">{product.name}</div>
          <div className="text-sm text-gray-500">{product.sku}</div>
          {product.brand && (
            <div className="text-xs text-gray-400">{product.brand}</div>
          )}
        </div>
      )
    },
    {
      key: 'category',
      title: 'Category',
      sortable: true,
      filterable: true,
      width: 140,
      render: (_: any, product: Product) => (
        <div>
          <div className="text-sm">{product.category}</div>
          {product.subcategory && (
            <div className="text-xs text-gray-500">{product.subcategory}</div>
          )}
        </div>
      )
    },
    {
      key: 'pricing',
      title: 'Price',
      sortable: true,
      width: 120,
      render: (_: any, product: Product) => (
        <div>
          <div className="font-medium">
            {new Intl.NumberFormat('en-US', {
              style: 'currency',
              currency: product.pricing.currency
            }).format(product.pricing.retailPrice)}
          </div>
          <div className="text-xs text-gray-500">
            Cost: {new Intl.NumberFormat('en-US', {
              style: 'currency',
              currency: product.pricing.currency
            }).format(product.pricing.cost)}
          </div>
        </div>
      )
    },
    ...(enableInventoryTracking ? [{
      key: 'inventory',
      title: 'Stock',
      sortable: true,
      width: 100,
      render: (_: any, product: Product) => {
        const { quantity, reorderLevel } = product.inventory;
        const stockStatus = quantity === 0 ? 'out' : quantity <= reorderLevel ? 'low' : 'good';
        
        return (
          <div>
            <div className={cn(
              "font-medium",
              stockStatus === 'out' && "text-red-600",
              stockStatus === 'low' && "text-yellow-600",
              stockStatus === 'good' && "text-green-600"
            )}>
              {quantity}
            </div>
            <div className="text-xs text-gray-500">
              Min: {reorderLevel}
            </div>
          </div>
        );
      }
    }] : []),
    {
      key: 'status',
      title: 'Status',
      sortable: true,
      filterable: true,
      width: 120,
      render: (status: Product['status']) => (
        <span className={cn(
          "px-2 py-1 text-xs rounded-full font-medium",
          status === 'active' && "bg-green-100 text-green-800",
          status === 'inactive' && "bg-gray-100 text-gray-800",
          status === 'discontinued' && "bg-red-100 text-red-800",
          status === 'out_of_stock' && "bg-orange-100 text-orange-800",
          status === 'coming_soon' && "bg-blue-100 text-blue-800"
        )}>
          {status.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
        </span>
      )
    },
    {
      key: 'updatedAt',
      title: 'Updated',
      sortable: true,
      width: 120,
      render: (date: Date) => date.toLocaleDateString()
    },
    {
      key: 'actions',
      title: 'Actions',
      width: 180,
      render: (_: any, product: Product) => (
        <div className="flex space-x-2">
          <button
            className="text-blue-600 hover:text-blue-800 text-sm"
            onClick={() => handleEditProduct(product)}
            disabled={readOnly}
            data-testid={`edit-product-${product.id}`}
          >
            Edit
          </button>
          <button
            className="text-green-600 hover:text-green-800 text-sm"
            onClick={() => handleDuplicateProduct(product.id)}
            disabled={readOnly}
            data-testid={`duplicate-product-${product.id}`}
          >
            Duplicate
          </button>
          <button
            className="text-red-600 hover:text-red-800 text-sm"
            onClick={() => handleDeleteProducts([product.id])}
            disabled={readOnly}
            data-testid={`delete-product-${product.id}`}
          >
            Delete
          </button>
        </div>
      )
    }
  ].filter(Boolean), [enableInventoryTracking, readOnly]);

  // Analytics data
  const analyticsData = useMemo(() => {
    const totalProducts = products.length;
    const activeProducts = products.filter(p => p.status === 'active').length;
    const totalValue = products.reduce((sum, p) => sum + (p.pricing.retailPrice * p.inventory.quantity), 0);
    const lowStockProducts = products.filter(p => p.inventory.quantity <= p.inventory.reorderLevel).length;

    const categoryDistribution = products.reduce((acc, product) => {
      acc[product.category] = (acc[product.category] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);

    const statusDistribution = products.reduce((acc, product) => {
      acc[product.status] = (acc[product.status] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);

    const topCategories = Object.entries(categoryDistribution)
      .sort(([,a], [,b]) => b - a)
      .slice(0, 10);

    return {
      widgets: [
        {
          id: 'product-metrics',
          type: 'metric',
          title: 'Product Metrics',
          position: { row: 1, col: 1, width: 4, height: 3 },
          data: [
            {
              id: 'total-products',
              name: 'Total Products',
              value: totalProducts,
              format: 'number',
              icon: '📦',
              color: '#3b82f6'
            },
            {
              id: 'active-products',
              name: 'Active Products',
              value: activeProducts,
              format: 'number',
              trend: activeProducts > totalProducts * 0.8 ? 'up' : 'down',
              icon: '✅',
              color: '#10b981'
            },
            {
              id: 'inventory-value',
              name: 'Inventory Value',
              value: totalValue,
              format: 'currency',
              icon: '💰',
              color: '#f59e0b'
            },
            {
              id: 'low-stock',
              name: 'Low Stock Items',
              value: lowStockProducts,
              format: 'number',
              trend: lowStockProducts > 0 ? 'down' : 'up',
              icon: '⚠️',
              color: '#ef4444'
            }
          ]
        },
        {
          id: 'category-chart',
          type: 'chart',
          title: 'Products by Category',
          position: { row: 1, col: 5, width: 4, height: 4 },
          data: {
            id: 'category-distribution',
            title: 'Category Distribution',
            type: 'doughnut',
            data: topCategories.map(([category, count]) => ({
              x: category,
              y: count,
              label: category
            }))
          }
        },
        {
          id: 'status-chart',
          type: 'chart',
          title: 'Products by Status',
          position: { row: 1, col: 9, width: 4, height: 4 },
          data: {
            id: 'status-distribution',
            title: 'Status Distribution',
            type: 'bar',
            data: Object.entries(statusDistribution).map(([status, count]) => ({
              x: status.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase()),
              y: count,
              label: status
            }))
          }
        }
      ]
    };
  }, [products]);

  // Handle product creation
  const handleCreateProduct = useCallback(async (formData: Record<string, any>) => {
    if (!onProductCreate) return;

    setIsLoading(true);
    try {
      const productData: ProductFormData = {
        name: formData.name,
        sku: formData.sku,
        description: formData.description,
        category: formData.category,
        subcategory: formData.subcategory,
        brand: formData.brand,
        manufacturer: formData.manufacturer,
        supplier: formData.supplier,
        images: [],
        specifications: {},
        pricing: {
          cost: Number(formData['pricing.cost']),
          msrp: Number(formData['pricing.msrp']),
          retailPrice: Number(formData['pricing.retailPrice']),
          wholesalePrice: formData['pricing.wholesalePrice'] ? Number(formData['pricing.wholesalePrice']) : undefined,
          currency: formData['pricing.currency'] || 'USD'
        },
        inventory: {
          quantity: Number(formData['inventory.quantity'] || 0),
          reserved: 0,
          available: Number(formData['inventory.quantity'] || 0),
          reorderLevel: Number(formData['inventory.reorderLevel'] || 0),
          maxStock: Number(formData['inventory.maxStock'] || 1000),
          location: formData['inventory.location']
        },
        dimensions: {
          length: Number(formData['dimensions.length'] || 0),
          width: Number(formData['dimensions.width'] || 0),
          height: Number(formData['dimensions.height'] || 0),
          weight: Number(formData['dimensions.weight'] || 0),
          unit: formData['dimensions.unit'] || 'cm'
        },
        status: formData.status || 'active',
        tags: formData.tags || [],
        barcode: formData.barcode,
        warranty: formData['warranty.duration'] ? {
          duration: Number(formData['warranty.duration']),
          unit: formData['warranty.unit'] || 'months'
        } : undefined
      };

      await onProductCreate(productData);
      setShowCreateForm(false);
    } catch (error) {
      onError?.(error as Error);
    } finally {
      setIsLoading(false);
    }
  }, [onProductCreate, onError]);

  // Handle product editing
  const handleEditProduct = useCallback((product: Product) => {
    setEditingProduct(product);
    setShowEditForm(true);
  }, []);

  // Handle product update
  const handleUpdateProduct = useCallback(async (formData: Record<string, any>) => {
    if (!onProductUpdate || !editingProduct) return;

    setIsLoading(true);
    try {
      const updates: Partial<ProductFormData> = {
        name: formData.name,
        sku: formData.sku,
        description: formData.description,
        category: formData.category,
        subcategory: formData.subcategory,
        brand: formData.brand,
        manufacturer: formData.manufacturer,
        supplier: formData.supplier,
        pricing: {
          ...editingProduct.pricing,
          cost: Number(formData['pricing.cost']),
          msrp: Number(formData['pricing.msrp']),
          retailPrice: Number(formData['pricing.retailPrice']),
          wholesalePrice: formData['pricing.wholesalePrice'] ? Number(formData['pricing.wholesalePrice']) : undefined,
          currency: formData['pricing.currency'] || 'USD'
        },
        inventory: {
          ...editingProduct.inventory,
          quantity: Number(formData['inventory.quantity']),
          reorderLevel: Number(formData['inventory.reorderLevel']),
          maxStock: Number(formData['inventory.maxStock']),
          location: formData['inventory.location']
        },
        dimensions: {
          length: Number(formData['dimensions.length'] || 0),
          width: Number(formData['dimensions.width'] || 0),
          height: Number(formData['dimensions.height'] || 0),
          weight: Number(formData['dimensions.weight'] || 0),
          unit: formData['dimensions.unit'] || 'cm'
        },
        status: formData.status,
        tags: formData.tags || [],
        barcode: formData.barcode,
        warranty: formData['warranty.duration'] ? {
          duration: Number(formData['warranty.duration']),
          unit: formData['warranty.unit'] || 'months'
        } : undefined
      };

      await onProductUpdate(editingProduct.id, updates);
      setShowEditForm(false);
      setEditingProduct(null);
    } catch (error) {
      onError?.(error as Error);
    } finally {
      setIsLoading(false);
    }
  }, [onProductUpdate, editingProduct, onError]);

  // Handle product deletion
  const handleDeleteProducts = useCallback(async (productIds: string[]) => {
    if (!onProductDelete) return;

    const confirmed = window.confirm(
      `Are you sure you want to delete ${productIds.length} product(s)? This action cannot be undone.`
    );

    if (!confirmed) return;

    setIsLoading(true);
    try {
      await onProductDelete(productIds.length === 1 ? productIds[0] : productIds);
      setSelectedProducts([]);
    } catch (error) {
      onError?.(error as Error);
    } finally {
      setIsLoading(false);
    }
  }, [onProductDelete, onError]);

  // Handle product duplication
  const handleDuplicateProduct = useCallback(async (productId: string) => {
    if (!onProductDuplicate) return;

    setIsLoading(true);
    try {
      await onProductDuplicate(productId);
    } catch (error) {
      onError?.(error as Error);
    } finally {
      setIsLoading(false);
    }
  }, [onProductDuplicate, onError]);

  // Handle bulk actions
  const handleBulkAction = useCallback(async (action: string) => {
    if (selectedProducts.length === 0 || !onBulkAction) return;

    switch (action) {
      case 'activate':
        await onBulkAction('status_change', selectedProducts, { status: 'active' });
        break;
      case 'deactivate':
        await onBulkAction('status_change', selectedProducts, { status: 'inactive' });
        break;
      case 'delete':
        await handleDeleteProducts(selectedProducts);
        return; // Don't clear selection here as it's handled in delete function
      case 'export_selected':
        await onBulkAction('export', selectedProducts);
        break;
      default:
        break;
    }

    setSelectedProducts([]);
  }, [selectedProducts, onBulkAction, handleDeleteProducts]);

  // Handle file import
  const handleImport = useCallback(async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file || !onImport) return;

    setIsLoading(true);
    try {
      const result = await onImport(file);
      alert(`Import completed: ${result.success} products imported. ${result.errors.length} errors.`);
    } catch (error) {
      onError?.(error as Error);
    } finally {
      setIsLoading(false);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  }, [onImport, onError]);

  // Render header
  const renderHeader = () => (
    <div className="flex items-center justify-between p-6 border-b border-gray-200">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Product Management</h1>
        <p className="text-gray-600 mt-1">Manage products, inventory, and pricing</p>
      </div>
      <div className="flex items-center space-x-3">
        {enableImportExport && !readOnly && (
          <>
            <input
              ref={fileInputRef}
              type="file"
              accept=".csv,.xlsx,.json"
              onChange={handleImport}
              className="hidden"
              data-testid="import-file-input"
            />
            <button
              className="px-4 py-2 text-sm border border-gray-300 rounded hover:bg-gray-50"
              onClick={() => fileInputRef.current?.click()}
              disabled={isLoading}
              data-testid="import-products-button"
            >
              Import
            </button>
          </>
        )}
        {enableImportExport && (
          <button
            className="px-4 py-2 text-sm bg-gray-500 text-white rounded hover:bg-gray-600"
            onClick={() => onExport?.('xlsx')}
            disabled={isLoading}
            data-testid="export-products-button"
          >
            Export
          </button>
        )}
        {!readOnly && (
          <button
            className="px-4 py-2 text-sm bg-blue-500 text-white rounded hover:bg-blue-600"
            onClick={() => setShowCreateForm(true)}
            disabled={isLoading || products.length >= maxProducts}
            data-testid="create-product-button"
          >
            Add Product
          </button>
        )}
      </div>
    </div>
  );

  // Render tabs
  const renderTabs = () => (
    <div className="border-b border-gray-200">
      <nav className="flex space-x-8 px-6">
        {[
          { id: 'products', label: 'Products' },
          ...(enableAnalytics ? [{ id: 'analytics', label: 'Analytics' }] : []),
          ...(enableInventoryTracking ? [{ id: 'inventory', label: 'Inventory' }] : [])
        ].map(tab => (
          <button
            key={tab.id}
            className={cn(
              "py-4 px-1 border-b-2 font-medium text-sm transition-colors",
              activeTab === tab.id
                ? "border-blue-500 text-blue-600"
                : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
            )}
            onClick={() => setActiveTab(tab.id as any)}
            data-testid={`tab-${tab.id}`}
          >
            {tab.label}
          </button>
        ))}
      </nav>
    </div>
  );

  // Render products tab
  const renderProductsTab = () => (
    <div className="p-6">
      <div className="mb-6 flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <input
            type="text"
            placeholder="Search products..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
            data-testid="search-products-input"
          />
          
          <select
            value={filters.category || ''}
            onChange={(e) => setFilters(prev => ({ ...prev, category: e.target.value || undefined }))}
            className="px-3 py-2 border border-gray-300 rounded"
            data-testid="filter-category"
          >
            <option value="">All Categories</option>
            {categories.map(cat => (
              <option key={cat.value} value={cat.value}>
                {cat.label}
              </option>
            ))}
          </select>

          <select
            value={filters.status || ''}
            onChange={(e) => setFilters(prev => ({ ...prev, status: e.target.value || undefined }))}
            className="px-3 py-2 border border-gray-300 rounded"
            data-testid="filter-status"
          >
            <option value="">All Statuses</option>
            <option value="active">Active</option>
            <option value="inactive">Inactive</option>
            <option value="discontinued">Discontinued</option>
            <option value="out_of_stock">Out of Stock</option>
            <option value="coming_soon">Coming Soon</option>
          </select>

          {enableInventoryTracking && (
            <select
              value={filters.stockLevel || ''}
              onChange={(e) => setFilters(prev => ({ ...prev, stockLevel: e.target.value as any || undefined }))}
              className="px-3 py-2 border border-gray-300 rounded"
              data-testid="filter-stock"
            >
              <option value="">All Stock Levels</option>
              <option value="in_stock">In Stock</option>
              <option value="low_stock">Low Stock</option>
              <option value="out_of_stock">Out of Stock</option>
            </select>
          )}
        </div>

        <div className="flex items-center space-x-2">
          <div className="flex border border-gray-300 rounded">
            <button
              className={cn(
                "px-3 py-2 text-sm",
                viewMode === 'table' 
                  ? "bg-blue-500 text-white" 
                  : "bg-white text-gray-700 hover:bg-gray-50"
              )}
              onClick={() => setViewMode('table')}
              data-testid="view-table"
            >
              Table
            </button>
            <button
              className={cn(
                "px-3 py-2 text-sm border-l border-gray-300",
                viewMode === 'grid' 
                  ? "bg-blue-500 text-white" 
                  : "bg-white text-gray-700 hover:bg-gray-50"
              )}
              onClick={() => setViewMode('grid')}
              data-testid="view-grid"
            >
              Grid
            </button>
          </div>

          {enableBulkActions && selectedProducts.length > 0 && (
            <div className="flex items-center space-x-2">
              <span className="text-sm text-gray-600">
                {selectedProducts.length} selected
              </span>
              <select
                onChange={(e) => e.target.value && handleBulkAction(e.target.value)}
                className="px-3 py-2 text-sm border border-gray-300 rounded"
                defaultValue=""
                data-testid="bulk-actions-select"
              >
                <option value="">Bulk Actions</option>
                <option value="activate">Activate</option>
                <option value="deactivate">Deactivate</option>
                <option value="export_selected">Export Selected</option>
                <option value="delete">Delete</option>
              </select>
            </div>
          )}
        </div>
      </div>

      {viewMode === 'table' ? (
        <EnhancedDataTable
          columns={tableColumns}
          data={filteredProducts}
          enableSearch={false}
          enableFilters={false}
          enableSorting={true}
          enableBulkActions={enableBulkActions}
          selectable={enableBulkActions}
          pageSize={pageSize}
          selectedRows={selectedProducts}
          onRowSelect={(selected) => setSelectedProducts(selected)}
          loading={isLoading}
          data-testid="products-table"
        />
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6" data-testid="products-grid">
          {filteredProducts.map(product => (
            <div
              key={product.id}
              className="bg-white border border-gray-200 rounded-lg shadow-sm hover:shadow-md transition-shadow"
            >
              <div className="aspect-w-1 aspect-h-1 w-full">
                {product.images.length > 0 ? (
                  <Image
                    src={product.images[0]}
                    alt={product.name}
                    className="w-full h-48 object-cover rounded-t-lg cursor-pointer"
                    onClick={() => {
                      setSelectedProductImages(product.images);
                      setShowImageGallery(true);
                    }}
                  />
                ) : (
                  <div className="w-full h-48 bg-gray-200 rounded-t-lg flex items-center justify-center text-gray-400">
                    No Image
                  </div>
                )}
              </div>
              <div className="p-4">
                <h3 className="font-medium text-lg mb-1">{product.name}</h3>
                <p className="text-sm text-gray-600 mb-2">{product.sku}</p>
                <p className="text-lg font-bold text-blue-600 mb-2">
                  {new Intl.NumberFormat('en-US', {
                    style: 'currency',
                    currency: product.pricing.currency
                  }).format(product.pricing.retailPrice)}
                </p>
                {enableInventoryTracking && (
                  <p className="text-sm text-gray-600 mb-3">
                    Stock: {product.inventory.quantity}
                  </p>
                )}
                <div className="flex justify-between items-center">
                  <span className={cn(
                    "px-2 py-1 text-xs rounded-full",
                    product.status === 'active' && "bg-green-100 text-green-800",
                    product.status === 'inactive' && "bg-gray-100 text-gray-800",
                    product.status === 'discontinued' && "bg-red-100 text-red-800",
                    product.status === 'out_of_stock' && "bg-orange-100 text-orange-800",
                    product.status === 'coming_soon' && "bg-blue-100 text-blue-800"
                  )}>
                    {product.status.replace('_', ' ')}
                  </span>
                  <div className="flex space-x-1">
                    <button
                      className="text-blue-600 hover:text-blue-800 p-1"
                      onClick={() => handleEditProduct(product)}
                      disabled={readOnly}
                      title="Edit"
                    >
                      ✏️
                    </button>
                    <button
                      className="text-green-600 hover:text-green-800 p-1"
                      onClick={() => handleDuplicateProduct(product.id)}
                      disabled={readOnly}
                      title="Duplicate"
                    >
                      📋
                    </button>
                    <button
                      className="text-red-600 hover:text-red-800 p-1"
                      onClick={() => handleDeleteProducts([product.id])}
                      disabled={readOnly}
                      title="Delete"
                    >
                      🗑️
                    </button>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );

  // Render analytics tab
  const renderAnalyticsTab = () => (
    <div className="p-6">
      <AnalyticsDashboard
        {...analyticsData}
        enableEdit={false}
        enableFilters={false}
        enableExport={enableImportExport}
        realTime={false}
        height="70vh"
        data-testid="product-analytics"
      />
    </div>
  );

  // Render inventory tab
  const renderInventoryTab = () => (
    <div className="p-6">
      <div className="mb-4">
        <h3 className="text-lg font-medium mb-2">Inventory Overview</h3>
        <p className="text-sm text-gray-600">
          Monitor stock levels and inventory status across all products
        </p>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <div className="bg-white p-6 rounded-lg border border-gray-200">
          <h4 className="text-lg font-medium text-gray-900 mb-2">Total Items</h4>
          <p className="text-3xl font-bold text-blue-600">
            {products.reduce((sum, p) => sum + p.inventory.quantity, 0).toLocaleString()}
          </p>
          <p className="text-sm text-gray-600 mt-1">Across {products.length} products</p>
        </div>
        
        <div className="bg-white p-6 rounded-lg border border-gray-200">
          <h4 className="text-lg font-medium text-gray-900 mb-2">Low Stock Alerts</h4>
          <p className="text-3xl font-bold text-orange-600">
            {products.filter(p => p.inventory.quantity <= p.inventory.reorderLevel).length}
          </p>
          <p className="text-sm text-gray-600 mt-1">Products need reordering</p>
        </div>
        
        <div className="bg-white p-6 rounded-lg border border-gray-200">
          <h4 className="text-lg font-medium text-gray-900 mb-2">Out of Stock</h4>
          <p className="text-3xl font-bold text-red-600">
            {products.filter(p => p.inventory.quantity === 0).length}
          </p>
          <p className="text-sm text-gray-600 mt-1">Products unavailable</p>
        </div>
      </div>

      <EnhancedDataTable
        columns={[
          ...tableColumns.filter(col => ['image', 'name', 'category', 'inventory'].includes(col.key)),
          {
            key: 'reorder',
            title: 'Reorder',
            width: 120,
            render: (_: any, product: Product) => {
              const needsReorder = product.inventory.quantity <= product.inventory.reorderLevel;
              return needsReorder ? (
                <button
                  className="px-3 py-1 text-xs bg-orange-500 text-white rounded hover:bg-orange-600"
                  onClick={() => {
                    // Handle reorder action
                    alert(`Reorder ${product.name}?`);
                  }}
                  disabled={readOnly}
                >
                  Reorder
                </button>
              ) : (
                <span className="text-sm text-green-600">✓ Good</span>
              );
            }
          }
        ]}
        data={filteredProducts.filter(p => 
          p.inventory.quantity <= p.inventory.reorderLevel || p.inventory.quantity === 0
        )}
        enableSearch={true}
        enableSorting={true}
        pageSize={pageSize}
        loading={isLoading}
        emptyMessage="All products have sufficient stock levels"
        data-testid="inventory-table"
      />
    </div>
  );

  return (
    <div
      className={cn("bg-white min-h-screen", className)}
      data-testid={dataTestId}
    >
      {renderHeader()}
      {renderTabs()}

      {/* Tab Content */}
      {activeTab === 'products' && renderProductsTab()}
      {activeTab === 'analytics' && enableAnalytics && renderAnalyticsTab()}
      {activeTab === 'inventory' && enableInventoryTracking && renderInventoryTab()}

      {/* Create Product Modal */}
      {showCreateForm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl w-full max-w-4xl max-h-[90vh] overflow-y-auto">
            <div className="p-6 border-b border-gray-200">
              <h2 className="text-xl font-semibold">Add New Product</h2>
            </div>
            <div className="p-6">
              <FormBuilder
                fields={productFormFields}
                onSubmit={handleCreateProduct}
                submitLabel="Create Product"
                showPreview={false}
                loading={isLoading}
                data-testid="create-product-form"
              />
            </div>
            <div className="p-6 border-t border-gray-200 flex justify-end space-x-3">
              <button
                className="px-4 py-2 text-sm border border-gray-300 rounded hover:bg-gray-50"
                onClick={() => setShowCreateForm(false)}
                disabled={isLoading}
                data-testid="cancel-create-product"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Edit Product Modal */}
      {showEditForm && editingProduct && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl w-full max-w-4xl max-h-[90vh] overflow-y-auto">
            <div className="p-6 border-b border-gray-200">
              <h2 className="text-xl font-semibold">
                Edit Product: {editingProduct.name}
              </h2>
            </div>
            <div className="p-6">
              <FormBuilder
                fields={productFormFields}
                initialData={{
                  ...editingProduct,
                  'pricing.cost': editingProduct.pricing.cost,
                  'pricing.msrp': editingProduct.pricing.msrp,
                  'pricing.retailPrice': editingProduct.pricing.retailPrice,
                  'pricing.wholesalePrice': editingProduct.pricing.wholesalePrice,
                  'pricing.currency': editingProduct.pricing.currency,
                  'inventory.quantity': editingProduct.inventory.quantity,
                  'inventory.reorderLevel': editingProduct.inventory.reorderLevel,
                  'inventory.maxStock': editingProduct.inventory.maxStock,
                  'inventory.location': editingProduct.inventory.location,
                  'dimensions.length': editingProduct.dimensions?.length,
                  'dimensions.width': editingProduct.dimensions?.width,
                  'dimensions.height': editingProduct.dimensions?.height,
                  'dimensions.weight': editingProduct.dimensions?.weight,
                  'dimensions.unit': editingProduct.dimensions?.unit,
                  'warranty.duration': editingProduct.warranty?.duration,
                  'warranty.unit': editingProduct.warranty?.unit
                }}
                onSubmit={handleUpdateProduct}
                submitLabel="Update Product"
                showPreview={false}
                loading={isLoading}
                data-testid="edit-product-form"
              />
            </div>
            <div className="p-6 border-t border-gray-200 flex justify-end space-x-3">
              <button
                className="px-4 py-2 text-sm border border-gray-300 rounded hover:bg-gray-50"
                onClick={() => {
                  setShowEditForm(false);
                  setEditingProduct(null);
                }}
                disabled={isLoading}
                data-testid="cancel-edit-product"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Image Gallery Modal */}
      {showImageGallery && (
        <div className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-4xl max-h-[90vh] overflow-y-auto">
            <div className="p-6 border-b border-gray-200 flex justify-between items-center">
              <h2 className="text-xl font-semibold">Product Images</h2>
              <button
                className="text-gray-400 hover:text-gray-600"
                onClick={() => setShowImageGallery(false)}
                data-testid="close-image-gallery"
              >
                ✕
              </button>
            </div>
            <div className="p-6">
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {selectedProductImages.map((image, index) => (
                  <Image
                    key={index}
                    src={image}
                    alt={`Product image ${index + 1}`}
                    className="w-full h-64 object-cover rounded-lg"
                  />
                ))}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ProductManagement;