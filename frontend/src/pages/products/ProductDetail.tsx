import React from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/services/api';

interface Product {
  id: number;
  code: string;
  name: string;
  display_name: string;
  sku: string;
  standard_price: number;
  cost_price?: number;
  sale_price?: number;
  status: string;
  product_type: string;
  is_active: boolean;
  description?: string;
  category?: string;
  weight?: number;
  dimensions?: {
    length?: number;
    width?: number;
    height?: number;
  };
  barcode?: string;
  supplier?: string;
  lead_time_days?: number;
  minimum_stock_level?: number;
  reorder_point?: number;
  is_purchasable: boolean;
  is_sellable: boolean;
  is_trackable: boolean;
  created_at: string;
  updated_at: string;
}

export const ProductDetail: React.FC = () => {
  const { productId } = useParams<{ productId: string }>();
  const navigate = useNavigate();

  const { data: product, isLoading, error } = useQuery({
    queryKey: ['product', productId],
    queryFn: async (): Promise<Product> => {
      const response = await apiClient.get(`/api/v1/products-basic/${productId}`);
      return response.data;
    },
    enabled: !!productId,
  });

  const handleEdit = () => {
    navigate(`/products/${productId}/edit`);
  };

  const handleBack = () => {
    navigate('/products');
  };

  if (isLoading) {
    return (
      <div className="container mx-auto p-6">
        <div className="animate-pulse">
          <div className="h-8 bg-gray-200 rounded w-1/4 mb-4"></div>
          <div className="space-y-6">
            <div className="h-4 bg-gray-200 rounded w-1/2"></div>
            <div className="h-4 bg-gray-200 rounded w-1/3"></div>
            <div className="h-4 bg-gray-200 rounded w-1/4"></div>
          </div>
        </div>
      </div>
    );
  }

  if (error || !product) {
    return (
      <div className="container mx-auto p-6">
        <div className="text-center py-12">
          <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z" />
          </svg>
          <h3 className="mt-2 text-sm font-medium text-gray-900">Product not found</h3>
          <p className="mt-1 text-sm text-gray-500">
            The product you're looking for doesn't exist or has been removed.
          </p>
          <div className="mt-6">
            <button
              onClick={handleBack}
              className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
            >
              Back to Products
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-start">
        <div className="flex items-center space-x-4">
          <button
            onClick={handleBack}
            className="text-gray-400 hover:text-gray-600"
            title="Back to Products"
          >
            <svg className="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
          </button>
          <div>
            <h1 className="text-3xl font-bold text-gray-900">{product.name}</h1>
            {product.display_name !== product.name && (
              <p className="text-gray-600">{product.display_name}</p>
            )}
            <p className="text-sm text-gray-500">Product Code: {product.code}</p>
          </div>
        </div>
        <div className="flex space-x-3">
          <button
            onClick={handleEdit}
            className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 flex items-center gap-2"
          >
            <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
            </svg>
            Edit Product
          </button>
        </div>
      </div>

      {/* Status Badges */}
      <div className="flex space-x-3">
        <span className={`inline-flex px-3 py-1 text-sm font-medium rounded-full ${
          product.status === 'active' 
            ? 'bg-green-100 text-green-800' 
            : 'bg-gray-100 text-gray-800'
        }`}>
          {product.status}
        </span>
        <span className={`inline-flex px-3 py-1 text-sm font-medium rounded-full ${
          product.is_active 
            ? 'bg-green-100 text-green-800' 
            : 'bg-red-100 text-red-800'
        }`}>
          {product.is_active ? 'Active' : 'Inactive'}
        </span>
        <span className="inline-flex px-3 py-1 text-sm font-medium rounded-full bg-blue-100 text-blue-800">
          {product.product_type}
        </span>
      </div>

      {/* Main Content */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Basic Information */}
        <div className="lg:col-span-2 space-y-6">
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-lg font-semibold mb-4">Basic Information</h2>
            <dl className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <dt className="text-sm font-medium text-gray-500">SKU</dt>
                <dd className="mt-1 text-sm text-gray-900 font-mono">{product.sku}</dd>
              </div>
              <div>
                <dt className="text-sm font-medium text-gray-500">Category</dt>
                <dd className="mt-1 text-sm text-gray-900">{product.category || 'Not specified'}</dd>
              </div>
              <div>
                <dt className="text-sm font-medium text-gray-500">Barcode</dt>
                <dd className="mt-1 text-sm text-gray-900 font-mono">{product.barcode || 'Not specified'}</dd>
              </div>
              <div>
                <dt className="text-sm font-medium text-gray-500">Supplier</dt>
                <dd className="mt-1 text-sm text-gray-900">{product.supplier || 'Not specified'}</dd>
              </div>
              {product.description && (
                <div className="md:col-span-2">
                  <dt className="text-sm font-medium text-gray-500">Description</dt>
                  <dd className="mt-1 text-sm text-gray-900">{product.description}</dd>
                </div>
              )}
            </dl>
          </div>

          {/* Pricing Information */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-lg font-semibold mb-4">Pricing</h2>
            <dl className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <dt className="text-sm font-medium text-gray-500">Standard Price</dt>
                <dd className="mt-1 text-lg font-semibold text-gray-900">
                  ${parseFloat(product.standard_price.toString()).toFixed(2)}
                </dd>
              </div>
              {product.cost_price && (
                <div>
                  <dt className="text-sm font-medium text-gray-500">Cost Price</dt>
                  <dd className="mt-1 text-lg font-semibold text-gray-900">
                    ${parseFloat(product.cost_price.toString()).toFixed(2)}
                  </dd>
                </div>
              )}
              {product.sale_price && (
                <div>
                  <dt className="text-sm font-medium text-gray-500">Sale Price</dt>
                  <dd className="mt-1 text-lg font-semibold text-green-600">
                    ${parseFloat(product.sale_price.toString()).toFixed(2)}
                  </dd>
                </div>
              )}
            </dl>
          </div>

          {/* Physical Properties */}
          {(product.weight || product.dimensions) && (
            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="text-lg font-semibold mb-4">Physical Properties</h2>
              <dl className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {product.weight && (
                  <div>
                    <dt className="text-sm font-medium text-gray-500">Weight</dt>
                    <dd className="mt-1 text-sm text-gray-900">{product.weight} kg</dd>
                  </div>
                )}
                {product.dimensions && (
                  <div>
                    <dt className="text-sm font-medium text-gray-500">Dimensions (L×W×H)</dt>
                    <dd className="mt-1 text-sm text-gray-900">
                      {product.dimensions.length || '?'} × {product.dimensions.width || '?'} × {product.dimensions.height || '?'} cm
                    </dd>
                  </div>
                )}
              </dl>
            </div>
          )}
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Inventory Settings */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-lg font-semibold mb-4">Inventory Settings</h2>
            <dl className="space-y-3">
              {product.minimum_stock_level && (
                <div>
                  <dt className="text-sm font-medium text-gray-500">Minimum Stock Level</dt>
                  <dd className="mt-1 text-sm text-gray-900">{product.minimum_stock_level}</dd>
                </div>
              )}
              {product.reorder_point && (
                <div>
                  <dt className="text-sm font-medium text-gray-500">Reorder Point</dt>
                  <dd className="mt-1 text-sm text-gray-900">{product.reorder_point}</dd>
                </div>
              )}
              {product.lead_time_days && (
                <div>
                  <dt className="text-sm font-medium text-gray-500">Lead Time</dt>
                  <dd className="mt-1 text-sm text-gray-900">{product.lead_time_days} days</dd>
                </div>
              )}
            </dl>
          </div>

          {/* Product Capabilities */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-lg font-semibold mb-4">Capabilities</h2>
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-gray-700">Purchasable</span>
                <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                  product.is_purchasable 
                    ? 'bg-green-100 text-green-800' 
                    : 'bg-red-100 text-red-800'
                }`}>
                  {product.is_purchasable ? 'Yes' : 'No'}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-gray-700">Sellable</span>
                <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                  product.is_sellable 
                    ? 'bg-green-100 text-green-800' 
                    : 'bg-red-100 text-red-800'
                }`}>
                  {product.is_sellable ? 'Yes' : 'No'}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-gray-700">Trackable</span>
                <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                  product.is_trackable 
                    ? 'bg-green-100 text-green-800' 
                    : 'bg-red-100 text-red-800'
                }`}>
                  {product.is_trackable ? 'Yes' : 'No'}
                </span>
              </div>
            </div>
          </div>

          {/* Timestamps */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-lg font-semibold mb-4">History</h2>
            <dl className="space-y-3">
              <div>
                <dt className="text-sm font-medium text-gray-500">Created</dt>
                <dd className="mt-1 text-sm text-gray-900">
                  {new Date(product.created_at).toLocaleDateString()} {new Date(product.created_at).toLocaleTimeString()}
                </dd>
              </div>
              <div>
                <dt className="text-sm font-medium text-gray-500">Last Updated</dt>
                <dd className="mt-1 text-sm text-gray-900">
                  {new Date(product.updated_at).toLocaleDateString()} {new Date(product.updated_at).toLocaleTimeString()}
                </dd>
              </div>
            </dl>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ProductDetail;