import React, { useState } from "react";

interface Product {
  id: string;
  code: string;
  name: string;
  price: number;
  stock: number;
}

const mockProducts: Product[] = [
  { id: "1", code: "P001", name: "ノートPC", price: 120000, stock: 15 },
  { id: "2", code: "P002", name: "マウス", price: 3000, stock: 50 },
  { id: "3", code: "P003", name: "キーボード", price: 8000, stock: 30 },
  { id: "4", code: "P004", name: "モニター", price: 35000, stock: 20 },
  { id: "5", code: "P005", name: "USBケーブル", price: 1000, stock: 100 },
];

export const ProductList: React.FC = () => {
  const [products] = useState<Product[]>(mockProducts);

  return (
    <div className="container mx-auto p-6">
      <div className="mb-6">
        <h1 className="text-3xl font-bold">商品管理</h1>
        <p className="text-gray-600">在庫商品の一覧表示</p>
      </div>

      <div className="bg-white shadow rounded-lg overflow-hidden">
        <table className="min-w-full">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                商品コード
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                商品名
              </th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                価格
              </th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                在庫数
              </th>
              <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase">
                操作
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {products.map((product) => (
              <tr key={product.id} className="hover:bg-gray-50">
                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                  {product.code}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                  {product.name}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 text-right">
                  ¥{product.price.toLocaleString()}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 text-right">
                  {product.stock}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-center text-sm font-medium">
                  <button className="text-blue-600 hover:text-blue-900 mr-4">
                    編集
                  </button>
                  <button className="text-red-600 hover:text-red-900">
                    削除
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="mt-6 flex justify-between items-center">
        <p className="text-sm text-gray-700">全{products.length}件を表示中</p>
        <button className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700">
          商品を追加
        </button>
      </div>
    </div>
  );
};

export default ProductList;
