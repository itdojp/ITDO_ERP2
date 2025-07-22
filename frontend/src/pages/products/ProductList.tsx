import React from 'react';

interface Product {
  id: string;
  code: string;
  name: string;
  category: string;
  price: number;
  stock: number;
  status: 'active' | 'inactive';
}

export const ProductListPage: React.FC = () => {
  // Mock product data
  const products: Product[] = [
    { id: '1', code: 'LT-001', name: 'ThinkPad X1 Carbon', category: 'ノートパソコン', price: 198000, stock: 25, status: 'active' },
    { id: '2', code: 'MN-001', name: 'Dell U2723QE', category: 'モニター', price: 85000, stock: 15, status: 'active' },
    { id: '3', code: 'KB-001', name: 'HHKB Professional', category: '周辺機器', price: 35000, stock: 8, status: 'active' },
    { id: '4', code: 'SW-001', name: 'システム開発サービス', category: 'サービス', price: 500000, stock: 0, status: 'active' },
    { id: '5', code: 'LT-002', name: 'MacBook Pro 14"', category: 'ノートパソコン', price: 298000, stock: 3, status: 'inactive' },
  ];

  return (
    <div className="min-h-screen bg-gray-100">
      {/* Header */}
      <div className="bg-white shadow">
        <div className="px-4 py-6">
          <h1 className="text-2xl font-bold text-gray-900">ITDO ERP - 商品管理</h1>
        </div>
      </div>

      {/* Main content */}
      <div className="py-8 px-4 sm:px-6 lg:px-8">
        <div className="bg-white shadow rounded-lg">
          <div className="px-4 py-5 sm:px-6 border-b border-gray-200">
            <h3 className="text-lg font-medium leading-6 text-gray-900">商品一覧</h3>
            <p className="mt-1 max-w-2xl text-sm text-gray-500">
              商品・サービスの在庫管理
            </p>
          </div>
          <div className="overflow-hidden">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    商品コード
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    商品名
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    カテゴリ
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    価格
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    在庫数
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    状態
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {products.map((product) => (
                  <tr key={product.id}>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900 font-mono">
                      {product.code}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {product.name}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {product.category}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 text-right">
                      ¥{product.price.toLocaleString()}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 text-right">
                      {product.stock === 0 && product.category === 'サービス' ? '−' : `${product.stock}個`}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                        product.status === 'active' 
                          ? 'bg-green-100 text-green-800' 
                          : 'bg-red-100 text-red-800'
                      }`}>
                        {product.status === 'active' ? 'アクティブ' : '無効'}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
};