import React, { useState, useCallback, useMemo, useRef } from 'react';
import { cn } from '@/lib/utils';
import { EnhancedDataTable } from '@/components/ui/EnhancedDataTable';
import { FormBuilder } from '@/components/ui/FormBuilder';
import { AnalyticsDashboard } from '@/components/ui/AnalyticsDashboard';
import { ChartSystem } from '@/components/ui/ChartSystem';

export interface InventoryItem {
  id: string;
  sku: string;
  name: string;
  description?: string;
  category: string;
  location: string;
  quantity: number;
  reservedQuantity: number;
  availableQuantity: number;
  reorderLevel: number;
  reorderQuantity: number;
  maxStockLevel: number;
  unitCost: number;
  retailPrice: number;
  supplier: string;
  lastRestockDate?: Date;
  expiryDate?: Date;
  batchNumber?: string;
  barcode?: string;
  weight?: number;
  dimensions?: {
    length: number;
    width: number;
    height: number;
    unit: 'cm' | 'm' | 'in' | 'ft';
  };
  tags?: string[];
  status: 'in_stock' | 'low_stock' | 'out_of_stock' | 'discontinued' | 'expired';
  lastMovement?: Date;
  createdAt: Date;
  updatedAt: Date;
  metadata?: Record<string, any>;
}

export interface StockMovement {
  id: string;
  itemId: string;
  type: 'in' | 'out' | 'adjustment' | 'transfer';
  quantity: number;
  reason: string;
  reference?: string;
  fromLocation?: string;
  toLocation?: string;
  unitCost?: number;
  performedBy: string;
  notes?: string;
  timestamp: Date;
}

export interface StockAlert {
  id: string;
  itemId: string;
  type: 'low_stock' | 'out_of_stock' | 'overstock' | 'expiry_warning' | 'expiry_critical';
  severity: 'info' | 'warning' | 'error' | 'critical';
  message: string;
  threshold?: number;
  currentValue?: number;
  acknowledged: boolean;
  acknowledgedBy?: string;
  acknowledgedAt?: Date;
  createdAt: Date;
}

export interface InventoryFormData extends Omit<InventoryItem, 'id' | 'createdAt' | 'updatedAt' | 'availableQuantity'> {
  adjustmentReason?: string;
  adjustmentNotes?: string;
}

export interface InventoryManagementProps {
  items?: InventoryItem[];
  movements?: StockMovement[];
  alerts?: StockAlert[];
  categories?: Array<{ value: string; label: string }>;
  locations?: Array<{ value: string; label: string }>;
  suppliers?: Array<{ value: string; label: string }>;
  users?: Array<{ value: string; label: string }>;
  enableMovements?: boolean;
  enableAlerts?: boolean;
  enableBulkOperations?: boolean;
  enableExport?: boolean;
  enableImport?: boolean;
  enableBarcodeScanning?: boolean;
  enableAnalytics?: boolean;
  autoAlerts?: boolean;
  pageSize?: number;
  maxItems?: number;
  readOnly?: boolean;
  className?: string;
  onItemCreate?: (item: InventoryFormData) => Promise<InventoryItem>;
  onItemUpdate?: (id: string, updates: Partial<InventoryFormData>) => Promise<InventoryItem>;
  onItemDelete?: (id: string | string[]) => Promise<void>;
  onStockAdjustment?: (itemId: string, quantity: number, reason: string, notes?: string) => Promise<StockMovement>;
  onStockTransfer?: (itemId: string, fromLocation: string, toLocation: string, quantity: number, reason: string) => Promise<StockMovement>;
  onAlertAcknowledge?: (alertId: string) => Promise<void>;
  onBarcodeScanned?: (barcode: string) => Promise<InventoryItem | null>;
  onExport?: (format: 'csv' | 'xlsx' | 'pdf', type: 'inventory' | 'movements' | 'alerts') => Promise<void>;
  onImport?: (file: File, type: 'inventory' | 'movements') => Promise<{ success: number; errors: string[] }>;
  onError?: (error: Error) => void;
  'data-testid'?: string;
}

export const InventoryManagement: React.FC<InventoryManagementProps> = ({
  items = [],
  movements = [],
  alerts = [],
  categories = [],
  locations = [],
  suppliers = [],
  users = [],
  enableMovements = true,
  enableAlerts = true,
  enableBulkOperations = true,
  enableExport = true,
  enableImport = true,
  enableBarcodeScanning = true,
  enableAnalytics = true,
  autoAlerts = true,
  pageSize = 25,
  maxItems = 50000,
  readOnly = false,
  className,
  onItemCreate,
  onItemUpdate,
  onItemDelete,
  onStockAdjustment,
  onStockTransfer,
  onAlertAcknowledge,
  onBarcodeScanned,
  onExport,
  onImport,
  onError,
  'data-testid': dataTestId = 'inventory-management'
}) => {
  const [activeTab, setActiveTab] = useState<'inventory' | 'movements' | 'alerts' | 'analytics'>('inventory');
  const [selectedItems, setSelectedItems] = useState<string[]>([]);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [showEditForm, setShowEditForm] = useState(false);
  const [showAdjustmentForm, setShowAdjustmentForm] = useState(false);
  const [showTransferForm, setShowTransferForm] = useState(false);
  const [editingItem, setEditingItem] = useState<InventoryItem | null>(null);
  const [adjustingItem, setAdjustingItem] = useState<InventoryItem | null>(null);
  const [transferringItem, setTransferringItem] = useState<InventoryItem | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [filters, setFilters] = useState<{
    category?: string;
    location?: string;
    status?: string;
    supplier?: string;
    lowStock?: boolean;
    expiringSoon?: boolean;
  }>({});
  const [isLoading, setIsLoading] = useState(false);
  const [barcodeInput, setBarcodeInput] = useState('');

  const fileInputRef = useRef<HTMLInputElement>(null);

  // Filter inventory items based on search and filters
  const filteredItems = useMemo(() => {
    let filtered = [...items];

    // Apply search
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(item =>
        item.name.toLowerCase().includes(query) ||
        item.sku.toLowerCase().includes(query) ||
        item.description?.toLowerCase().includes(query) ||
        item.category.toLowerCase().includes(query) ||
        item.location.toLowerCase().includes(query) ||
        item.supplier.toLowerCase().includes(query) ||
        item.barcode?.toLowerCase().includes(query)
      );
    }

    // Apply filters
    if (filters.category) {
      filtered = filtered.filter(item => item.category === filters.category);
    }

    if (filters.location) {
      filtered = filtered.filter(item => item.location === filters.location);
    }

    if (filters.status) {
      filtered = filtered.filter(item => item.status === filters.status);
    }

    if (filters.supplier) {
      filtered = filtered.filter(item => item.supplier === filters.supplier);
    }

    if (filters.lowStock) {
      filtered = filtered.filter(item => item.availableQuantity <= item.reorderLevel);
    }

    if (filters.expiringSoon) {
      const thirtyDaysFromNow = new Date();
      thirtyDaysFromNow.setDate(thirtyDaysFromNow.getDate() + 30);
      filtered = filtered.filter(item => 
        item.expiryDate && item.expiryDate <= thirtyDaysFromNow
      );
    }

    return filtered;
  }, [items, searchQuery, filters]);

  // Inventory item form fields configuration
  const inventoryFormFields = useMemo(() => [
    {
      id: 'basic-section',
      type: 'section' as const,
      label: 'Basic Information',
      description: 'Item identification and description'
    },
    {
      id: 'sku',
      type: 'text' as const,
      label: 'SKU',
      placeholder: 'Enter SKU',
      required: true,
      validation: { pattern: '^[A-Z0-9-]+$' }
    },
    {
      id: 'name',
      type: 'text' as const,
      label: 'Item Name',
      placeholder: 'Enter item name',
      required: true,
      validation: { minLength: 2, maxLength: 100 }
    },
    {
      id: 'description',
      type: 'textarea' as const,
      label: 'Description',
      placeholder: 'Enter item description',
      rows: 3
    },
    {
      id: 'category',
      type: 'select' as const,
      label: 'Category',
      options: categories,
      required: true
    },
    {
      id: 'barcode',
      type: 'text' as const,
      label: 'Barcode',
      placeholder: 'Enter barcode'
    },
    {
      id: 'stock-section',
      type: 'section' as const,
      label: 'Stock Information',
      description: 'Quantity and stock levels'
    },
    {
      id: 'location',
      type: 'select' as const,
      label: 'Location',
      options: locations,
      required: true
    },
    {
      id: 'quantity',
      type: 'number' as const,
      label: 'Current Quantity',
      min: 0,
      required: true
    },
    {
      id: 'reservedQuantity',
      type: 'number' as const,
      label: 'Reserved Quantity',
      min: 0,
      defaultValue: 0
    },
    {
      id: 'reorderLevel',
      type: 'number' as const,
      label: 'Reorder Level',
      min: 0,
      required: true
    },
    {
      id: 'reorderQuantity',
      type: 'number' as const,
      label: 'Reorder Quantity',
      min: 1,
      required: true
    },
    {
      id: 'maxStockLevel',
      type: 'number' as const,
      label: 'Max Stock Level',
      min: 1
    },
    {
      id: 'pricing-section',
      type: 'section' as const,
      label: 'Pricing & Supplier',
      description: 'Cost and pricing information'
    },
    {
      id: 'unitCost',
      type: 'number' as const,
      label: 'Unit Cost',
      min: 0,
      step: 0.01,
      required: true
    },
    {
      id: 'retailPrice',
      type: 'number' as const,
      label: 'Retail Price',
      min: 0,
      step: 0.01,
      required: true
    },
    {
      id: 'supplier',
      type: 'select' as const,
      label: 'Supplier',
      options: suppliers,
      required: true
    },
    {
      id: 'additional-section',
      type: 'section' as const,
      label: 'Additional Information',
      description: 'Optional details'
    },
    {
      id: 'lastRestockDate',
      type: 'date' as const,
      label: 'Last Restock Date'
    },
    {
      id: 'expiryDate',
      type: 'date' as const,
      label: 'Expiry Date'
    },
    {
      id: 'batchNumber',
      type: 'text' as const,
      label: 'Batch Number',
      placeholder: 'Enter batch number'
    },
    {
      id: 'weight',
      type: 'number' as const,
      label: 'Weight (kg)',
      min: 0,
      step: 0.01
    },
    {
      id: 'status',
      type: 'select' as const,
      label: 'Status',
      options: [
        { value: 'in_stock', label: 'In Stock' },
        { value: 'low_stock', label: 'Low Stock' },
        { value: 'out_of_stock', label: 'Out of Stock' },
        { value: 'discontinued', label: 'Discontinued' },
        { value: 'expired', label: 'Expired' }
      ],
      defaultValue: 'in_stock'
    }
  ], [categories, locations, suppliers]);

  // Stock adjustment form fields
  const adjustmentFormFields = useMemo(() => [
    {
      id: 'quantity',
      type: 'number' as const,
      label: 'Adjustment Quantity',
      placeholder: 'Enter quantity (use negative for reduction)',
      required: true,
      validation: { min: -9999, max: 9999 }
    },
    {
      id: 'adjustmentReason',
      type: 'select' as const,
      label: 'Reason',
      options: [
        { value: 'damaged', label: 'Damaged/Defective' },
        { value: 'expired', label: 'Expired' },
        { value: 'lost', label: 'Lost/Stolen' },
        { value: 'found', label: 'Found/Located' },
        { value: 'correction', label: 'Count Correction' },
        { value: 'return', label: 'Customer Return' },
        { value: 'restock', label: 'Restocking' },
        { value: 'other', label: 'Other' }
      ],
      required: true
    },
    {
      id: 'adjustmentNotes',
      type: 'textarea' as const,
      label: 'Notes',
      placeholder: 'Enter additional notes (optional)',
      rows: 3
    }
  ], []);

  // Stock transfer form fields
  const transferFormFields = useMemo(() => [
    {
      id: 'fromLocation',
      type: 'select' as const,
      label: 'From Location',
      options: locations,
      required: true
    },
    {
      id: 'toLocation',
      type: 'select' as const,
      label: 'To Location',
      options: locations,
      required: true
    },
    {
      id: 'quantity',
      type: 'number' as const,
      label: 'Quantity to Transfer',
      min: 1,
      required: true
    },
    {
      id: 'reason',
      type: 'select' as const,
      label: 'Transfer Reason',
      options: [
        { value: 'rebalancing', label: 'Stock Rebalancing' },
        { value: 'demand', label: 'High Demand' },
        { value: 'reorganization', label: 'Warehouse Reorganization' },
        { value: 'consolidation', label: 'Stock Consolidation' },
        { value: 'other', label: 'Other' }
      ],
      required: true
    },
    {
      id: 'notes',
      type: 'textarea' as const,
      label: 'Notes',
      placeholder: 'Enter additional notes (optional)',
      rows: 3
    }
  ], [locations]);

  // Data table columns configuration
  const inventoryTableColumns = useMemo(() => [
    {
      key: 'sku',
      title: 'SKU',
      sortable: true,
      searchable: true,
      width: 120,
      render: (sku: string, item: InventoryItem) => (
        <div>
          <div className="font-medium">{sku}</div>
          {item.barcode && (
            <div className="text-xs text-gray-500">{item.barcode}</div>
          )}
        </div>
      )
    },
    {
      key: 'name',
      title: 'Item Name',
      sortable: true,
      searchable: true,
      render: (name: string, item: InventoryItem) => (
        <div>
          <div className="font-medium">{name}</div>
          <div className="text-sm text-gray-500">{item.category}</div>
        </div>
      )
    },
    {
      key: 'location',
      title: 'Location',
      sortable: true,
      filterable: true,
      width: 120
    },
    {
      key: 'quantity',
      title: 'Stock',
      sortable: true,
      width: 140,
      render: (_: any, item: InventoryItem) => (
        <div>
          <div className="font-medium">
            {item.availableQuantity} / {item.quantity}
          </div>
          <div className="text-xs text-gray-500">
            Available / Total
          </div>
          {item.reservedQuantity > 0 && (
            <div className="text-xs text-orange-600">
              {item.reservedQuantity} reserved
            </div>
          )}
        </div>
      )
    },
    {
      key: 'reorderLevel',
      title: 'Reorder Level',
      sortable: true,
      width: 100,
      render: (reorderLevel: number, item: InventoryItem) => (
        <div className={cn(
          "font-medium",
          item.availableQuantity <= reorderLevel ? "text-red-600" : "text-gray-900"
        )}>
          {reorderLevel}
        </div>
      )
    },
    {
      key: 'status',
      title: 'Status',
      sortable: true,
      filterable: true,
      width: 120,
      render: (status: InventoryItem['status'], item: InventoryItem) => {
        const getStatusColor = () => {
          if (item.availableQuantity <= 0) return "bg-red-100 text-red-800";
          if (item.availableQuantity <= item.reorderLevel) return "bg-yellow-100 text-yellow-800";
          if (status === 'discontinued') return "bg-gray-100 text-gray-800";
          if (status === 'expired') return "bg-red-100 text-red-800";
          return "bg-green-100 text-green-800";
        };

        return (
          <span className={cn(
            "px-2 py-1 text-xs rounded-full font-medium",
            getStatusColor()
          )}>
            {status.replace('_', ' ').charAt(0).toUpperCase() + status.slice(1).replace('_', ' ')}
          </span>
        );
      }
    },
    {
      key: 'unitCost',
      title: 'Unit Cost',
      sortable: true,
      width: 100,
      render: (cost: number) => `$${cost.toFixed(2)}`
    },
    {
      key: 'totalValue',
      title: 'Total Value',
      sortable: true,
      width: 120,
      render: (_: any, item: InventoryItem) => (
        <div className="font-medium">
          ${(item.quantity * item.unitCost).toFixed(2)}
        </div>
      )
    },
    {
      key: 'lastMovement',
      title: 'Last Movement',
      sortable: true,
      width: 140,
      render: (date: Date) => date ? date.toLocaleDateString() : 'Never'
    },
    {
      key: 'actions',
      title: 'Actions',
      width: 180,
      render: (_: any, item: InventoryItem) => (
        <div className="flex space-x-2">
          <button
            className="text-blue-600 hover:text-blue-800 text-sm"
            onClick={() => handleEditItem(item)}
            disabled={readOnly}
            data-testid={`edit-item-${item.id}`}
          >
            Edit
          </button>
          <button
            className="text-green-600 hover:text-green-800 text-sm"
            onClick={() => handleAdjustStock(item)}
            disabled={readOnly}
            data-testid={`adjust-stock-${item.id}`}
          >
            Adjust
          </button>
          <button
            className="text-purple-600 hover:text-purple-800 text-sm"
            onClick={() => handleTransferStock(item)}
            disabled={readOnly}
            data-testid={`transfer-stock-${item.id}`}
          >
            Transfer
          </button>
          <button
            className="text-red-600 hover:text-red-800 text-sm"
            onClick={() => handleDeleteItems([item.id])}
            disabled={readOnly}
            data-testid={`delete-item-${item.id}`}
          >
            Delete
          </button>
        </div>
      )
    }
  ], [readOnly]);

  // Stock movements table columns
  const movementsTableColumns = useMemo(() => [
    {
      key: 'timestamp',
      title: 'Date/Time',
      sortable: true,
      width: 140,
      render: (timestamp: Date) => (
        <div>
          <div className="font-medium">{timestamp.toLocaleDateString()}</div>
          <div className="text-xs text-gray-500">{timestamp.toLocaleTimeString()}</div>
        </div>
      )
    },
    {
      key: 'itemId',
      title: 'Item',
      width: 180,
      render: (itemId: string) => {
        const item = items.find(i => i.id === itemId);
        return item ? (
          <div>
            <div className="font-medium">{item.name}</div>
            <div className="text-xs text-gray-500">{item.sku}</div>
          </div>
        ) : itemId;
      }
    },
    {
      key: 'type',
      title: 'Type',
      sortable: true,
      width: 100,
      render: (type: StockMovement['type']) => (
        <span className={cn(
          "px-2 py-1 text-xs rounded font-medium",
          type === 'in' && "bg-green-100 text-green-800",
          type === 'out' && "bg-red-100 text-red-800",
          type === 'adjustment' && "bg-blue-100 text-blue-800",
          type === 'transfer' && "bg-purple-100 text-purple-800"
        )}>
          {type.charAt(0).toUpperCase() + type.slice(1)}
        </span>
      )
    },
    {
      key: 'quantity',
      title: 'Quantity',
      sortable: true,
      width: 100,
      render: (quantity: number, movement: StockMovement) => (
        <span className={cn(
          "font-medium",
          movement.type === 'in' && "text-green-600",
          movement.type === 'out' && "text-red-600"
        )}>
          {movement.type === 'out' ? '-' : '+'}{Math.abs(quantity)}
        </span>
      )
    },
    {
      key: 'reason',
      title: 'Reason',
      searchable: true,
      width: 150
    },
    {
      key: 'performedBy',
      title: 'Performed By',
      searchable: true,
      width: 120
    },
    {
      key: 'reference',
      title: 'Reference',
      searchable: true,
      width: 120
    }
  ], [items]);

  // Alerts table columns
  const alertsTableColumns = useMemo(() => [
    {
      key: 'createdAt',
      title: 'Date',
      sortable: true,
      width: 120,
      render: (date: Date) => date.toLocaleDateString()
    },
    {
      key: 'severity',
      title: 'Severity',
      sortable: true,
      width: 100,
      render: (severity: StockAlert['severity']) => (
        <span className={cn(
          "px-2 py-1 text-xs rounded font-medium",
          severity === 'info' && "bg-blue-100 text-blue-800",
          severity === 'warning' && "bg-yellow-100 text-yellow-800",
          severity === 'error' && "bg-red-100 text-red-800",
          severity === 'critical' && "bg-red-200 text-red-900"
        )}>
          {severity.charAt(0).toUpperCase() + severity.slice(1)}
        </span>
      )
    },
    {
      key: 'type',
      title: 'Type',
      sortable: true,
      width: 140,
      render: (type: StockAlert['type']) => 
        type.replace(/_/g, ' ').charAt(0).toUpperCase() + type.slice(1).replace(/_/g, ' ')
    },
    {
      key: 'itemId',
      title: 'Item',
      width: 180,
      render: (itemId: string) => {
        const item = items.find(i => i.id === itemId);
        return item ? (
          <div>
            <div className="font-medium">{item.name}</div>
            <div className="text-xs text-gray-500">{item.sku}</div>
          </div>
        ) : itemId;
      }
    },
    {
      key: 'message',
      title: 'Message',
      searchable: true
    },
    {
      key: 'acknowledged',
      title: 'Status',
      width: 100,
      render: (acknowledged: boolean) => (
        <span className={cn(
          "px-2 py-1 text-xs rounded font-medium",
          acknowledged 
            ? "bg-green-100 text-green-800" 
            : "bg-yellow-100 text-yellow-800"
        )}>
          {acknowledged ? 'Acknowledged' : 'Pending'}
        </span>
      )
    },
    {
      key: 'actions',
      title: 'Actions',
      width: 120,
      render: (_: any, alert: StockAlert) => (
        <div className="flex space-x-2">
          {!alert.acknowledged && (
            <button
              className="text-blue-600 hover:text-blue-800 text-sm"
              onClick={() => handleAcknowledgeAlert(alert.id)}
              data-testid={`acknowledge-alert-${alert.id}`}
            >
              Acknowledge
            </button>
          )}
        </div>
      )
    }
  ], [items]);

  // Analytics data
  const analyticsData = useMemo(() => {
    const totalItems = items.length;
    const totalValue = items.reduce((sum, item) => sum + (item.quantity * item.unitCost), 0);
    const lowStockItems = items.filter(item => item.availableQuantity <= item.reorderLevel).length;
    const outOfStockItems = items.filter(item => item.availableQuantity === 0).length;
    
    const categoryBreakdown = items.reduce((acc, item) => {
      acc[item.category] = (acc[item.category] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);

    const locationBreakdown = items.reduce((acc, item) => {
      acc[item.location] = (acc[item.location] || 0) + item.quantity;
      return acc;
    }, {} as Record<string, number>);

    return {
      widgets: [
        {
          id: 'inventory-metrics',
          type: 'metric',
          title: 'Inventory Overview',
          position: { row: 1, col: 1, width: 4, height: 2 },
          data: [
            {
              id: 'total-items',
              name: 'Total Items',
              value: totalItems,
              format: 'number',
              icon: '📦',
              color: '#3b82f6'
            },
            {
              id: 'total-value',
              name: 'Total Value',
              value: totalValue,
              format: 'currency',
              icon: '💰',
              color: '#10b981'
            },
            {
              id: 'low-stock',
              name: 'Low Stock Items',
              value: lowStockItems,
              format: 'number',
              trend: lowStockItems > totalItems * 0.1 ? 'up' : 'down',
              icon: '⚠️',
              color: '#f59e0b'
            },
            {
              id: 'out-of-stock',
              name: 'Out of Stock',
              value: outOfStockItems,
              format: 'number',
              trend: outOfStockItems > 0 ? 'up' : 'down',
              icon: '🚫',
              color: '#ef4444'
            }
          ]
        },
        {
          id: 'category-chart',
          type: 'chart',
          title: 'Items by Category',
          position: { row: 1, col: 5, width: 4, height: 4 },
          data: {
            id: 'category-distribution',
            title: 'Category Distribution',
            type: 'pie',
            data: Object.entries(categoryBreakdown).map(([category, count]) => ({
              x: category,
              y: count,
              label: category
            }))
          }
        },
        {
          id: 'location-chart',
          type: 'chart',
          title: 'Stock by Location',
          position: { row: 1, col: 9, width: 4, height: 4 },
          data: {
            id: 'location-distribution',
            title: 'Location Distribution',
            type: 'bar',
            data: Object.entries(locationBreakdown).map(([location, quantity]) => ({
              x: location,
              y: quantity,
              label: location
            }))
          }
        }
      ]
    };
  }, [items]);

  // Handle item creation
  const handleCreateItem = useCallback(async (formData: Record<string, any>) => {
    if (!onItemCreate) return;

    setIsLoading(true);
    try {
      const itemData: InventoryFormData = {
        sku: formData.sku,
        name: formData.name,
        description: formData.description,
        category: formData.category,
        location: formData.location,
        quantity: Number(formData.quantity),
        reservedQuantity: Number(formData.reservedQuantity || 0),
        reorderLevel: Number(formData.reorderLevel),
        reorderQuantity: Number(formData.reorderQuantity),
        maxStockLevel: formData.maxStockLevel ? Number(formData.maxStockLevel) : undefined,
        unitCost: Number(formData.unitCost),
        retailPrice: Number(formData.retailPrice),
        supplier: formData.supplier,
        lastRestockDate: formData.lastRestockDate ? new Date(formData.lastRestockDate) : undefined,
        expiryDate: formData.expiryDate ? new Date(formData.expiryDate) : undefined,
        batchNumber: formData.batchNumber,
        barcode: formData.barcode,
        weight: formData.weight ? Number(formData.weight) : undefined,
        status: formData.status || 'in_stock'
      };

      await onItemCreate(itemData);
      setShowCreateForm(false);
    } catch (error) {
      onError?.(error as Error);
    } finally {
      setIsLoading(false);
    }
  }, [onItemCreate, onError]);

  // Handle item editing
  const handleEditItem = useCallback((item: InventoryItem) => {
    setEditingItem(item);
    setShowEditForm(true);
  }, []);

  // Handle item update
  const handleUpdateItem = useCallback(async (formData: Record<string, any>) => {
    if (!onItemUpdate || !editingItem) return;

    setIsLoading(true);
    try {
      const updates: Partial<InventoryFormData> = {
        sku: formData.sku,
        name: formData.name,
        description: formData.description,
        category: formData.category,
        location: formData.location,
        quantity: Number(formData.quantity),
        reservedQuantity: Number(formData.reservedQuantity || 0),
        reorderLevel: Number(formData.reorderLevel),
        reorderQuantity: Number(formData.reorderQuantity),
        maxStockLevel: formData.maxStockLevel ? Number(formData.maxStockLevel) : undefined,
        unitCost: Number(formData.unitCost),
        retailPrice: Number(formData.retailPrice),
        supplier: formData.supplier,
        lastRestockDate: formData.lastRestockDate ? new Date(formData.lastRestockDate) : undefined,
        expiryDate: formData.expiryDate ? new Date(formData.expiryDate) : undefined,
        batchNumber: formData.batchNumber,
        barcode: formData.barcode,
        weight: formData.weight ? Number(formData.weight) : undefined,
        status: formData.status
      };

      await onItemUpdate(editingItem.id, updates);
      setShowEditForm(false);
      setEditingItem(null);
    } catch (error) {
      onError?.(error as Error);
    } finally {
      setIsLoading(false);
    }
  }, [onItemUpdate, editingItem, onError]);

  // Handle item deletion
  const handleDeleteItems = useCallback(async (itemIds: string[]) => {
    if (!onItemDelete) return;

    const confirmed = window.confirm(
      `Are you sure you want to delete ${itemIds.length} item(s)? This action cannot be undone.`
    );

    if (!confirmed) return;

    setIsLoading(true);
    try {
      await onItemDelete(itemIds.length === 1 ? itemIds[0] : itemIds);
      setSelectedItems([]);
    } catch (error) {
      onError?.(error as Error);
    } finally {
      setIsLoading(false);
    }
  }, [onItemDelete, onError]);

  // Handle stock adjustment
  const handleAdjustStock = useCallback((item: InventoryItem) => {
    setAdjustingItem(item);
    setShowAdjustmentForm(true);
  }, []);

  // Handle stock adjustment submission
  const handleSubmitAdjustment = useCallback(async (formData: Record<string, any>) => {
    if (!onStockAdjustment || !adjustingItem) return;

    setIsLoading(true);
    try {
      await onStockAdjustment(
        adjustingItem.id,
        Number(formData.quantity),
        formData.adjustmentReason,
        formData.adjustmentNotes
      );
      setShowAdjustmentForm(false);
      setAdjustingItem(null);
    } catch (error) {
      onError?.(error as Error);
    } finally {
      setIsLoading(false);
    }
  }, [onStockAdjustment, adjustingItem, onError]);

  // Handle stock transfer
  const handleTransferStock = useCallback((item: InventoryItem) => {
    setTransferringItem(item);
    setShowTransferForm(true);
  }, []);

  // Handle stock transfer submission
  const handleSubmitTransfer = useCallback(async (formData: Record<string, any>) => {
    if (!onStockTransfer || !transferringItem) return;

    setIsLoading(true);
    try {
      await onStockTransfer(
        transferringItem.id,
        formData.fromLocation,
        formData.toLocation,
        Number(formData.quantity),
        formData.reason
      );
      setShowTransferForm(false);
      setTransferringItem(null);
    } catch (error) {
      onError?.(error as Error);
    } finally {
      setIsLoading(false);
    }
  }, [onStockTransfer, transferringItem, onError]);

  // Handle alert acknowledgment
  const handleAcknowledgeAlert = useCallback(async (alertId: string) => {
    if (!onAlertAcknowledge) return;

    setIsLoading(true);
    try {
      await onAlertAcknowledge(alertId);
    } catch (error) {
      onError?.(error as Error);
    } finally {
      setIsLoading(false);
    }
  }, [onAlertAcknowledge, onError]);

  // Handle barcode scanning
  const handleBarcodeSubmit = useCallback(async (e: React.FormEvent) => {
    e.preventDefault();
    if (!barcodeInput.trim() || !onBarcodeScanned) return;

    setIsLoading(true);
    try {
      const item = await onBarcodeScanned(barcodeInput.trim());
      if (item) {
        handleEditItem(item);
      } else {
        alert('Item not found for barcode: ' + barcodeInput);
      }
      setBarcodeInput('');
    } catch (error) {
      onError?.(error as Error);
    } finally {
      setIsLoading(false);
    }
  }, [barcodeInput, onBarcodeScanned, onError, handleEditItem]);

  // Handle bulk actions
  const handleBulkAction = useCallback(async (action: string) => {
    if (selectedItems.length === 0) return;

    switch (action) {
      case 'delete':
        await handleDeleteItems(selectedItems);
        break;
      default:
        break;
    }

    setSelectedItems([]);
  }, [selectedItems, handleDeleteItems]);

  // Handle file import
  const handleImport = useCallback(async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file || !onImport) return;

    setIsLoading(true);
    try {
      const result = await onImport(file, 'inventory');
      alert(`Import completed: ${result.success} items imported successfully. ${result.errors.length} errors.`);
      if (result.errors.length > 0) {
        console.error('Import errors:', result.errors);
      }
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
        <h1 className="text-2xl font-bold text-gray-900">Inventory Management</h1>
        <p className="text-gray-600 mt-1">Track stock levels, movements, and alerts</p>
      </div>
      <div className="flex items-center space-x-3">
        {enableBarcodeScanning && (
          <form onSubmit={handleBarcodeSubmit} className="flex items-center space-x-2">
            <input
              type="text"
              placeholder="Scan barcode..."
              value={barcodeInput}
              onChange={(e) => setBarcodeInput(e.target.value)}
              className="px-3 py-2 text-sm border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
              data-testid="barcode-input"
            />
            <button
              type="submit"
              className="px-3 py-2 text-sm bg-gray-500 text-white rounded hover:bg-gray-600"
              disabled={isLoading || !barcodeInput.trim()}
              data-testid="barcode-submit"
            >
              Find
            </button>
          </form>
        )}
        {enableImport && !readOnly && (
          <>
            <input
              ref={fileInputRef}
              type="file"
              accept=".csv,.xlsx"
              onChange={handleImport}
              className="hidden"
              data-testid="import-file-input"
            />
            <button
              className="px-4 py-2 text-sm border border-gray-300 rounded hover:bg-gray-50"
              onClick={() => fileInputRef.current?.click()}
              disabled={isLoading}
              data-testid="import-inventory-button"
            >
              Import Items
            </button>
          </>
        )}
        {enableExport && (
          <button
            className="px-4 py-2 text-sm bg-gray-500 text-white rounded hover:bg-gray-600"
            onClick={() => onExport?.('csv', 'inventory')}
            disabled={isLoading}
            data-testid="export-inventory-button"
          >
            Export Inventory
          </button>
        )}
        {!readOnly && (
          <button
            className="px-4 py-2 text-sm bg-blue-500 text-white rounded hover:bg-blue-600"
            onClick={() => setShowCreateForm(true)}
            disabled={isLoading || items.length >= maxItems}
            data-testid="create-item-button"
          >
            Add Item
          </button>
        )}
      </div>
    </div>
  );

  // Render tabs
  const renderTabs = () => (
    <div className="border-b border-gray-200">
      <nav className="flex space-x-8 px-6">
        {['inventory', 'movements', 'alerts', 'analytics'].map(tab => {
          if (!enableMovements && tab === 'movements') return null;
          if (!enableAlerts && tab === 'alerts') return null;
          if (!enableAnalytics && tab === 'analytics') return null;
          
          return (
            <button
              key={tab}
              className={cn(
                "py-4 px-1 border-b-2 font-medium text-sm transition-colors",
                activeTab === tab
                  ? "border-blue-500 text-blue-600"
                  : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
              )}
              onClick={() => setActiveTab(tab as any)}
              data-testid={`tab-${tab}`}
            >
              {tab.charAt(0).toUpperCase() + tab.slice(1)}
            </button>
          );
        })}
      </nav>
    </div>
  );

  // Render inventory tab
  const renderInventoryTab = () => (
    <div className="p-6">
      <div className="mb-6 flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <input
            type="text"
            placeholder="Search inventory..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
            data-testid="search-inventory-input"
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
            value={filters.location || ''}
            onChange={(e) => setFilters(prev => ({ ...prev, location: e.target.value || undefined }))}
            className="px-3 py-2 border border-gray-300 rounded"
            data-testid="filter-location"
          >
            <option value="">All Locations</option>
            {locations.map(loc => (
              <option key={loc.value} value={loc.value}>
                {loc.label}
              </option>
            ))}
          </select>

          <label className="flex items-center space-x-2">
            <input
              type="checkbox"
              checked={filters.lowStock || false}
              onChange={(e) => setFilters(prev => ({ ...prev, lowStock: e.target.checked || undefined }))}
              data-testid="filter-low-stock"
            />
            <span className="text-sm">Low Stock Only</span>
          </label>

          <label className="flex items-center space-x-2">
            <input
              type="checkbox"
              checked={filters.expiringSoon || false}
              onChange={(e) => setFilters(prev => ({ ...prev, expiringSoon: e.target.checked || undefined }))}
              data-testid="filter-expiring-soon"
            />
            <span className="text-sm">Expiring Soon</span>
          </label>
        </div>

        {enableBulkOperations && selectedItems.length > 0 && (
          <div className="flex items-center space-x-2">
            <span className="text-sm text-gray-600">
              {selectedItems.length} selected
            </span>
            <select
              onChange={(e) => e.target.value && handleBulkAction(e.target.value)}
              className="px-3 py-2 text-sm border border-gray-300 rounded"
              defaultValue=""
              data-testid="bulk-actions-select"
            >
              <option value="">Bulk Actions</option>
              <option value="delete">Delete</option>
            </select>
          </div>
        )}
      </div>

      <EnhancedDataTable
        columns={inventoryTableColumns}
        data={filteredItems}
        enableSearch={false}
        enableFilters={false}
        enableSorting={true}
        enableBulkActions={enableBulkOperations}
        selectable={enableBulkOperations}
        pageSize={pageSize}
        selectedRows={selectedItems}
        onRowSelect={(selected) => setSelectedItems(selected)}
        loading={isLoading}
        data-testid="inventory-table"
      />
    </div>
  );

  // Render movements tab
  const renderMovementsTab = () => (
    <div className="p-6">
      <div className="mb-6 flex items-center justify-between">
        <h3 className="text-lg font-medium">Stock Movements</h3>
        {enableExport && (
          <button
            className="px-4 py-2 text-sm bg-gray-500 text-white rounded hover:bg-gray-600"
            onClick={() => onExport?.('csv', 'movements')}
            disabled={isLoading}
            data-testid="export-movements-button"
          >
            Export Movements
          </button>
        )}
      </div>

      <EnhancedDataTable
        columns={movementsTableColumns}
        data={movements}
        enableSearch={true}
        enableFilters={true}
        enableSorting={true}
        pageSize={pageSize}
        loading={isLoading}
        data-testid="movements-table"
      />
    </div>
  );

  // Render alerts tab
  const renderAlertsTab = () => (
    <div className="p-6">
      <div className="mb-6 flex items-center justify-between">
        <h3 className="text-lg font-medium">Stock Alerts</h3>
        <div className="flex items-center space-x-2">
          <span className="text-sm text-gray-600">
            {alerts.filter(a => !a.acknowledged).length} pending alerts
          </span>
          {enableExport && (
            <button
              className="px-4 py-2 text-sm bg-gray-500 text-white rounded hover:bg-gray-600"
              onClick={() => onExport?.('csv', 'alerts')}
              disabled={isLoading}
              data-testid="export-alerts-button"
            >
              Export Alerts
            </button>
          )}
        </div>
      </div>

      <EnhancedDataTable
        columns={alertsTableColumns}
        data={alerts}
        enableSearch={true}
        enableFilters={true}
        enableSorting={true}
        pageSize={pageSize}
        loading={isLoading}
        data-testid="alerts-table"
      />
    </div>
  );

  // Render analytics tab
  const renderAnalyticsTab = () => (
    <div className="p-6">
      <AnalyticsDashboard
        {...analyticsData}
        enableEdit={false}
        enableFilters={false}
        enableExport={enableExport}
        realTime={false}
        height="70vh"
        data-testid="inventory-analytics"
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
      {activeTab === 'inventory' && renderInventoryTab()}
      {activeTab === 'movements' && enableMovements && renderMovementsTab()}
      {activeTab === 'alerts' && enableAlerts && renderAlertsTab()}
      {activeTab === 'analytics' && enableAnalytics && renderAnalyticsTab()}

      {/* Create Item Modal */}
      {showCreateForm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl w-full max-w-3xl max-h-[90vh] overflow-y-auto">
            <div className="p-6 border-b border-gray-200">
              <h2 className="text-xl font-semibold">Add New Inventory Item</h2>
            </div>
            <div className="p-6">
              <FormBuilder
                fields={inventoryFormFields}
                onSubmit={handleCreateItem}
                submitLabel="Add Item"
                showPreview={false}
                loading={isLoading}
                data-testid="create-item-form"
              />
            </div>
            <div className="p-6 border-t border-gray-200 flex justify-end space-x-3">
              <button
                className="px-4 py-2 text-sm border border-gray-300 rounded hover:bg-gray-50"
                onClick={() => setShowCreateForm(false)}
                disabled={isLoading}
                data-testid="cancel-create-item"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Edit Item Modal */}
      {showEditForm && editingItem && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl w-full max-w-3xl max-h-[90vh] overflow-y-auto">
            <div className="p-6 border-b border-gray-200">
              <h2 className="text-xl font-semibold">
                Edit Item: {editingItem.name}
              </h2>
            </div>
            <div className="p-6">
              <FormBuilder
                fields={inventoryFormFields}
                initialData={editingItem}
                onSubmit={handleUpdateItem}
                submitLabel="Update Item"
                showPreview={false}
                loading={isLoading}
                data-testid="edit-item-form"
              />
            </div>
            <div className="p-6 border-t border-gray-200 flex justify-end space-x-3">
              <button
                className="px-4 py-2 text-sm border border-gray-300 rounded hover:bg-gray-50"
                onClick={() => {
                  setShowEditForm(false);
                  setEditingItem(null);
                }}
                disabled={isLoading}
                data-testid="cancel-edit-item"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Stock Adjustment Modal */}
      {showAdjustmentForm && adjustingItem && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl w-full max-w-lg">
            <div className="p-6 border-b border-gray-200">
              <h2 className="text-xl font-semibold">
                Adjust Stock: {adjustingItem.name}
              </h2>
              <p className="text-sm text-gray-600 mt-1">
                Current quantity: {adjustingItem.availableQuantity}
              </p>
            </div>
            <div className="p-6">
              <FormBuilder
                fields={adjustmentFormFields}
                onSubmit={handleSubmitAdjustment}
                submitLabel="Adjust Stock"
                showPreview={false}
                loading={isLoading}
                data-testid="adjustment-form"
              />
            </div>
            <div className="p-6 border-t border-gray-200 flex justify-end space-x-3">
              <button
                className="px-4 py-2 text-sm border border-gray-300 rounded hover:bg-gray-50"
                onClick={() => {
                  setShowAdjustmentForm(false);
                  setAdjustingItem(null);
                }}
                disabled={isLoading}
                data-testid="cancel-adjustment"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Stock Transfer Modal */}
      {showTransferForm && transferringItem && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl w-full max-w-lg">
            <div className="p-6 border-b border-gray-200">
              <h2 className="text-xl font-semibold">
                Transfer Stock: {transferringItem.name}
              </h2>
              <p className="text-sm text-gray-600 mt-1">
                Available quantity: {transferringItem.availableQuantity}
              </p>
            </div>
            <div className="p-6">
              <FormBuilder
                fields={transferFormFields}
                initialData={{ fromLocation: transferringItem.location }}
                onSubmit={handleSubmitTransfer}
                submitLabel="Transfer Stock"
                showPreview={false}
                loading={isLoading}
                data-testid="transfer-form"
              />
            </div>
            <div className="p-6 border-t border-gray-200 flex justify-end space-x-3">
              <button
                className="px-4 py-2 text-sm border border-gray-300 rounded hover:bg-gray-50"
                onClick={() => {
                  setShowTransferForm(false);
                  setTransferringItem(null);
                }}
                disabled={isLoading}
                data-testid="cancel-transfer"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default InventoryManagement;