import React, { useState } from 'react';
import { useForm } from 'react-hook-form';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { apiClient } from '@/services/api';

interface Product {
  id: number;
  code: string;
  name: string;
  sku: string;
  current_stock?: number;
  unit?: string;
}

interface StockAdjustmentFormData {
  product_id: number;
  adjustment_type: 'positive' | 'negative' | 'absolute';
  quantity_change: number;
  new_quantity?: number;
  reason: string;
  reference_number?: string;
  notes?: string;
  location?: string;
}

interface StockAdjustmentResponse {
  id: number;
  product_id: number;
  old_quantity: number;
  new_quantity: number;
  quantity_change: number;
  adjustment_type: string;
  reason: string;
  created_at: string;
}

export const StockAdjustmentForm: React.FC = () => {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [selectedProduct, setSelectedProduct] = useState<Product | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [showProductSearch, setShowProductSearch] = useState(false);

  const {
    register,
    handleSubmit,
    watch,
    setValue,
    reset,
    formState: { errors, isSubmitting }
  } = useForm<StockAdjustmentFormData>({
    defaultValues: {
      adjustment_type: 'positive',
      reason: '',
      reference_number: '',
      notes: '',
      location: ''
    }
  });

  const adjustmentType = watch('adjustment_type');
  const quantityChange = watch('quantity_change');

  // Search products
  const { data: searchResults, isLoading: isSearching } = useQuery({
    queryKey: ['product-search', searchTerm],
    queryFn: async (): Promise<Product[]> => {
      if (!searchTerm || searchTerm.length < 2) return [];
      const response = await apiClient.get(`/api/v1/products-basic/search?q=${encodeURIComponent(searchTerm)}`);
      return response.data || [];
    },
    enabled: searchTerm.length >= 2,
  });

  // Get product details with current stock
  const { data: productDetails } = useQuery({
    queryKey: ['product-inventory', selectedProduct?.id],
    queryFn: async (): Promise<Product> => {
      const response = await apiClient.get(`/api/v1/inventory/product/${selectedProduct?.id}`);
      return response.data;
    },
    enabled: !!selectedProduct?.id,
  });

  // Stock adjustment mutation
  const adjustmentMutation = useMutation({
    mutationFn: async (data: StockAdjustmentFormData): Promise<StockAdjustmentResponse> => {
      const response = await apiClient.post('/api/v1/inventory/adjustments', data);
      return response.data;
    },
    onSuccess: (result) => {
      queryClient.invalidateQueries({ queryKey: ['inventory-statistics'] });
      queryClient.invalidateQueries({ queryKey: ['recent-movements'] });
      queryClient.invalidateQueries({ queryKey: ['inventory-alerts'] });
      queryClient.invalidateQueries({ queryKey: ['product-inventory', selectedProduct?.id] });
      
      // Show success message and redirect
      alert(`Stock adjustment completed successfully! New quantity: ${result.new_quantity}`);
      navigate('/inventory');
    },
    onError: (error) => {
      console.error('Stock adjustment failed:', error);
      alert('Failed to process stock adjustment. Please try again.');
    },
  });

  const onSubmit = async (data: StockAdjustmentFormData) => {
    if (!selectedProduct) {
      alert('Please select a product');
      return;
    }

    const submissionData = {
      ...data,
      product_id: selectedProduct.id,
    };

    if (adjustmentType === 'absolute' && data.new_quantity !== undefined) {
      submissionData.quantity_change = data.new_quantity - (productDetails?.current_stock || 0);
    }

    await adjustmentMutation.mutateAsync(submissionData);
  };

  const handleProductSelect = (product: Product) => {
    setSelectedProduct(product);
    setShowProductSearch(false);
    setSearchTerm('');
    setValue('product_id', product.id);
  };

  const handleCancel = () => {
    navigate('/inventory');
  };

  const calculateNewQuantity = () => {
    if (!productDetails?.current_stock || !quantityChange) return null;
    
    switch (adjustmentType) {
      case 'positive':
        return productDetails.current_stock + quantityChange;
      case 'negative':
        return productDetails.current_stock - quantityChange;
      case 'absolute':
        return quantityChange;
      default:
        return null;
    }
  };

  const newQuantity = calculateNewQuantity();

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Stock Adjustment</h1>
          <p className="text-gray-600">Adjust inventory quantities with proper documentation</p>
        </div>
        <button
          onClick={handleCancel}
          className="text-gray-400 hover:text-gray-600"
          title="Cancel"
        >
          <svg className="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Main Form */}
          <div className="lg:col-span-2 space-y-6">
            {/* Product Selection */}
            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="text-lg font-semibold mb-4">Product Selection</h2>
              
              {!selectedProduct ? (
                <div className="space-y-4">
                  <div>
                    <label htmlFor="product-search" className="block text-sm font-medium text-gray-700 mb-2">
                      Search Product
                    </label>
                    <div className="relative">
                      <input
                        type="text"
                        id="product-search"
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                        onFocus={() => setShowProductSearch(true)}
                        placeholder="Search by product name, code, or SKU..."
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      />
                      {isSearching && (
                        <div className="absolute right-3 top-2">
                          <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-blue-600"></div>
                        </div>
                      )}
                    </div>

                    {/* Search Results */}
                    {showProductSearch && searchResults && searchResults.length > 0 && (
                      <div className="absolute z-10 mt-1 w-full bg-white border border-gray-300 rounded-md shadow-lg max-h-60 overflow-y-auto">
                        {searchResults.map((product) => (
                          <button
                            key={product.id}
                            type="button"
                            onClick={() => handleProductSelect(product)}
                            className="w-full px-4 py-3 text-left hover:bg-gray-50 border-b border-gray-100 last:border-b-0"
                          >
                            <div className="font-medium text-gray-900">{product.name}</div>
                            <div className="text-sm text-gray-600">{product.code} • {product.sku}</div>
                          </button>
                        ))}
                      </div>
                    )}

                    {showProductSearch && searchTerm.length >= 2 && searchResults?.length === 0 && !isSearching && (
                      <div className="absolute z-10 mt-1 w-full bg-white border border-gray-300 rounded-md shadow-lg p-4 text-center text-gray-500">
                        No products found
                      </div>
                    )}
                  </div>
                </div>
              ) : (
                <div className="bg-gray-50 rounded-lg p-4">
                  <div className="flex justify-between items-start">
                    <div>
                      <h3 className="font-medium text-gray-900">{selectedProduct.name}</h3>
                      <p className="text-sm text-gray-600">{selectedProduct.code} • {selectedProduct.sku}</p>
                      {productDetails && (
                        <p className="text-sm text-gray-600 mt-1">
                          Current Stock: <span className="font-medium">{productDetails.current_stock} {productDetails.unit}</span>
                        </p>
                      )}
                    </div>
                    <button
                      type="button"
                      onClick={() => {
                        setSelectedProduct(null);
                        setValue('product_id', 0);
                      }}
                      className="text-gray-400 hover:text-gray-600"
                    >
                      <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                      </svg>
                    </button>
                  </div>
                </div>
              )}
            </div>

            {/* Adjustment Details */}
            {selectedProduct && (
              <div className="bg-white rounded-lg shadow p-6">
                <h2 className="text-lg font-semibold mb-4">Adjustment Details</h2>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label htmlFor="adjustment_type" className="block text-sm font-medium text-gray-700 mb-2">
                      Adjustment Type *
                    </label>
                    <select
                      id="adjustment_type"
                      {...register('adjustment_type', { required: 'Adjustment type is required' })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      <option value="positive">Increase Stock (+)</option>
                      <option value="negative">Decrease Stock (-)</option>
                      <option value="absolute">Set Absolute Quantity</option>
                    </select>
                    {errors.adjustment_type && (
                      <p className="mt-1 text-sm text-red-600">{errors.adjustment_type.message}</p>
                    )}
                  </div>

                  <div>
                    <label htmlFor="quantity_change" className="block text-sm font-medium text-gray-700 mb-2">
                      {adjustmentType === 'absolute' ? 'New Quantity *' : 'Quantity Change *'}
                    </label>
                    <input
                      type="number"
                      id="quantity_change"
                      step="0.01"
                      {...register('quantity_change', { 
                        required: 'Quantity is required',
                        min: { value: 0, message: 'Quantity must be positive' }
                      })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      placeholder={adjustmentType === 'absolute' ? 'Enter new quantity' : 'Enter quantity change'}
                    />
                    {errors.quantity_change && (
                      <p className="mt-1 text-sm text-red-600">{errors.quantity_change.message}</p>
                    )}
                    {newQuantity !== null && (
                      <p className="mt-1 text-sm text-gray-600">
                        New quantity will be: <span className="font-medium">{newQuantity} {productDetails?.unit}</span>
                      </p>
                    )}
                  </div>

                  <div className="md:col-span-2">
                    <label htmlFor="reason" className="block text-sm font-medium text-gray-700 mb-2">
                      Reason *
                    </label>
                    <select
                      id="reason"
                      {...register('reason', { required: 'Reason is required' })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      <option value="">Select a reason</option>
                      <option value="physical_count">Physical Count Adjustment</option>
                      <option value="damage">Damaged Goods</option>
                      <option value="theft">Theft/Loss</option>
                      <option value="receipt">Goods Receipt</option>
                      <option value="return">Customer Return</option>
                      <option value="obsolete">Obsolete Inventory</option>
                      <option value="transfer">Location Transfer</option>
                      <option value="correction">Data Correction</option>
                      <option value="other">Other</option>
                    </select>
                    {errors.reason && (
                      <p className="mt-1 text-sm text-red-600">{errors.reason.message}</p>
                    )}
                  </div>

                  <div>
                    <label htmlFor="reference_number" className="block text-sm font-medium text-gray-700 mb-2">
                      Reference Number
                    </label>
                    <input
                      type="text"
                      id="reference_number"
                      {...register('reference_number')}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      placeholder="PO number, receipt, etc."
                    />
                  </div>

                  <div>
                    <label htmlFor="location" className="block text-sm font-medium text-gray-700 mb-2">
                      Location
                    </label>
                    <input
                      type="text"
                      id="location"
                      {...register('location')}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      placeholder="Warehouse location"
                    />
                  </div>

                  <div className="md:col-span-2">
                    <label htmlFor="notes" className="block text-sm font-medium text-gray-700 mb-2">
                      Additional Notes
                    </label>
                    <textarea
                      id="notes"
                      rows={3}
                      {...register('notes')}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      placeholder="Additional details about this adjustment..."
                    />
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Summary Sidebar */}
          <div className="space-y-6">
            {selectedProduct && productDetails && (
              <div className="bg-white rounded-lg shadow p-6">
                <h2 className="text-lg font-semibold mb-4">Adjustment Summary</h2>
                <div className="space-y-3">
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-600">Current Stock:</span>
                    <span className="text-sm font-medium">{productDetails.current_stock} {productDetails.unit}</span>
                  </div>
                  {quantityChange && (
                    <>
                      <div className="flex justify-between">
                        <span className="text-sm text-gray-600">Adjustment:</span>
                        <span className={`text-sm font-medium ${
                          adjustmentType === 'positive' ? 'text-green-600' : 
                          adjustmentType === 'negative' ? 'text-red-600' : 'text-blue-600'
                        }`}>
                          {adjustmentType === 'positive' && '+'}
                          {adjustmentType === 'negative' && '-'}
                          {adjustmentType === 'absolute' && 'Set to '}
                          {quantityChange} {productDetails.unit}
                        </span>
                      </div>
                      <hr />
                      <div className="flex justify-between">
                        <span className="text-sm font-medium text-gray-900">New Stock:</span>
                        <span className="text-sm font-bold text-gray-900">
                          {newQuantity} {productDetails.unit}
                        </span>
                      </div>
                    </>
                  )}
                </div>
              </div>
            )}

            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
              <div className="flex">
                <svg className="h-5 w-5 text-yellow-400 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z" />
                </svg>
                <div>
                  <h3 className="text-sm font-medium text-yellow-800">Important</h3>
                  <p className="text-sm text-yellow-700 mt-1">
                    Stock adjustments are permanent and will be logged with your user information and timestamp.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Form Actions */}
        <div className="flex justify-end space-x-4 pt-6 border-t">
          <button
            type="button"
            onClick={handleCancel}
            className="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={isSubmitting || !selectedProduct}
            className="px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isSubmitting ? (
              <div className="flex items-center">
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                Processing...
              </div>
            ) : (
              'Process Adjustment'
            )}
          </button>
        </div>
      </form>
    </div>
  );
};

export default StockAdjustmentForm;