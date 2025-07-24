import React, { useState } from 'react';

interface Product {
  id: string;
  code: string;
  name: string;
  price: number;
  stock: number;
  unit: string;
}

interface SalesItem {
  id: string;
  product: Product;
  quantity: number;
  unitPrice: number;
  discount: number;
  subtotal: number;
}

interface Customer {
  id: string;
  code: string;
  name: string;
  email: string;
  phone: string;
}

const mockProducts: Product[] = [
  { id: '1', code: 'LT-001', name: 'ThinkPad X1 Carbon Gen 11', price: 198000, stock: 25, unit: '台' },
  { id: '2', code: 'MN-001', name: 'Dell UltraSharp U2723QE', price: 85000, stock: 15, unit: '台' },
  { id: '3', code: 'KB-001', name: 'HHKB Professional HYBRID', price: 35000, stock: 8, unit: '個' },
  { id: '4', code: 'SW-001', name: 'Microsoft Office 365', price: 12984, stock: 100, unit: 'ライセンス' },
  { id: '5', code: 'ACC-001', name: 'USB-C Hub 7-in-1', price: 8500, stock: 45, unit: '個' },
];

const mockCustomers: Customer[] = [
  { id: '1', code: 'CUST-001', name: '株式会社サンプル', email: 'info@sample.co.jp', phone: '03-1234-5678' },
  { id: '2', code: 'CUST-002', name: 'テスト商事株式会社', email: 'sales@test-corp.co.jp', phone: '03-9876-5432' },
  { id: '3', code: 'CUST-003', name: 'デモ株式会社', email: 'contact@demo.co.jp', phone: '03-5555-1234' },
];

export const SalesInput: React.FC = () => {
  const [selectedCustomer, setSelectedCustomer] = useState<Customer | null>(null);
  const [salesItems, setSalesItems] = useState<SalesItem[]>([]);
  const [productSearch, setProductSearch] = useState('');
  const [selectedProduct, setSelectedProduct] = useState<Product | null>(null);
  const [quantity, setQuantity] = useState(1);
  const [discount, setDiscount] = useState(0);
  const [notes, setNotes] = useState('');
  const [salesDate, setSalesDate] = useState(new Date().toISOString().split('T')[0]);

  const filteredProducts = mockProducts.filter(product =>
    product.name.toLowerCase().includes(productSearch.toLowerCase()) ||
    product.code.toLowerCase().includes(productSearch.toLowerCase())
  );

  const addSalesItem = () => {
    if (!selectedProduct || quantity <= 0) return;

    const unitPrice = selectedProduct.price;
    const discountAmount = (unitPrice * quantity * discount) / 100;
    const subtotal = (unitPrice * quantity) - discountAmount;

    const newItem: SalesItem = {
      id: Date.now().toString(),
      product: selectedProduct,
      quantity,
      unitPrice,
      discount,
      subtotal,
    };

    setSalesItems([...salesItems, newItem]);
    setSelectedProduct(null);
    setQuantity(1);
    setDiscount(0);
    setProductSearch('');
  };

  const removeSalesItem = (itemId: string) => {
    setSalesItems(salesItems.filter(item => item.id !== itemId));
  };

  const updateItemQuantity = (itemId: string, newQuantity: number) => {
    setSalesItems(salesItems.map(item => {
      if (item.id === itemId) {
        const discountAmount = (item.unitPrice * newQuantity * item.discount) / 100;
        const subtotal = (item.unitPrice * newQuantity) - discountAmount;
        return { ...item, quantity: newQuantity, subtotal };
      }
      return item;
    }));
  };

  const updateItemDiscount = (itemId: string, newDiscount: number) => {
    setSalesItems(salesItems.map(item => {
      if (item.id === itemId) {
        const discountAmount = (item.unitPrice * item.quantity * newDiscount) / 100;
        const subtotal = (item.unitPrice * item.quantity) - discountAmount;
        return { ...item, discount: newDiscount, subtotal };
      }
      return item;
    }));
  };

  const totalAmount = salesItems.reduce((sum, item) => sum + item.subtotal, 0);
  const totalQuantity = salesItems.reduce((sum, item) => sum + item.quantity, 0);
  const totalDiscountAmount = salesItems.reduce((sum, item) => 
    sum + ((item.unitPrice * item.quantity * item.discount) / 100), 0
  );

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedCustomer || salesItems.length === 0) {
      alert('顧客と商品を選択してください');
      return;
    }

    // Here would be API call to save sales data
    const salesData = {
      customer: selectedCustomer,
      items: salesItems,
      totalAmount,
      salesDate,
      notes,
    };

    console.log('Sales data:', salesData);
    alert('売上データが登録されました！');
    
    // Reset form
    setSelectedCustomer(null);
    setSalesItems([]);
    setNotes('');
    setSalesDate(new Date().toISOString().split('T')[0]);
  };

  return (
    <div className="max-w-6xl mx-auto p-6">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">売上入力</h1>
          <p className="text-gray-600 mt-1">新規売上データの登録</p>
        </div>
        <div className="text-sm text-gray-500">
          売上日: {new Date(salesDate).toLocaleDateString('ja-JP')}
        </div>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* 顧客選択 */}
        <div className="bg-white p-6 rounded-lg shadow">
          <h2 className="text-xl font-semibold mb-4">顧客選択</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                顧客 <span className="text-red-500">*</span>
              </label>
              <select
                value={selectedCustomer?.id || ''}
                onChange={(e) => {
                  const customer = mockCustomers.find(c => c.id === e.target.value);
                  setSelectedCustomer(customer || null);
                }}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                required
              >
                <option value="">顧客を選択してください</option>
                {mockCustomers.map(customer => (
                  <option key={customer.id} value={customer.id}>
                    {customer.code} - {customer.name}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">売上日</label>
              <input
                type="date"
                value={salesDate}
                onChange={(e) => setSalesDate(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                required
              />
            </div>
          </div>
          
          {selectedCustomer && (
            <div className="mt-4 p-4 bg-blue-50 rounded-md">
              <div className="flex items-center space-x-4">
                <div>
                  <p className="font-medium text-blue-900">{selectedCustomer.name}</p>
                  <p className="text-sm text-blue-700">顧客コード: {selectedCustomer.code}</p>
                </div>
                <div className="text-sm text-blue-700">
                  <p>📧 {selectedCustomer.email}</p>
                  <p>📞 {selectedCustomer.phone}</p>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* 商品追加 */}
        <div className="bg-white p-6 rounded-lg shadow">
          <h2 className="text-xl font-semibold mb-4">商品追加</h2>
          <div className="grid grid-cols-1 md:grid-cols-5 gap-4 mb-4">
            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-gray-700 mb-2">商品検索</label>
              <input
                type="text"
                value={productSearch}
                onChange={(e) => setProductSearch(e.target.value)}
                placeholder="商品名またはコードで検索"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              {productSearch && filteredProducts.length > 0 && (
                <div className="absolute z-10 w-full mt-1 bg-white border border-gray-300 rounded-md shadow-lg max-h-60 overflow-y-auto">
                  {filteredProducts.map(product => (
                    <button
                      key={product.id}
                      type="button"
                      onClick={() => {
                        setSelectedProduct(product);
                        setProductSearch(product.name);
                      }}
                      className="w-full text-left px-4 py-2 hover:bg-gray-50 border-b border-gray-100"
                    >
                      <div className="font-medium">{product.name}</div>
                      <div className="text-sm text-gray-500">
                        {product.code} - ¥{product.price.toLocaleString()} - 在庫: {product.stock}{product.unit}
                      </div>
                    </button>
                  ))}
                </div>
              )}
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">数量</label>
              <input
                type="number"
                min="1"
                value={quantity}
                onChange={(e) => setQuantity(parseInt(e.target.value) || 1)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">割引 (%)</label>
              <input
                type="number"
                min="0"
                max="100"
                value={discount}
                onChange={(e) => setDiscount(parseFloat(e.target.value) || 0)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div className="flex items-end">
              <button
                type="button"
                onClick={addSalesItem}
                disabled={!selectedProduct}
                className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
              >
                追加
              </button>
            </div>
          </div>
        </div>

        {/* 売上明細 */}
        <div className="bg-white p-6 rounded-lg shadow">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-xl font-semibold">売上明細</h2>
            <div className="text-sm text-gray-600">
              {salesItems.length}品目 / 合計{totalQuantity}点
            </div>
          </div>
          
          {salesItems.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              <p>商品が追加されていません</p>
              <p className="text-sm">上記から商品を追加してください</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">商品</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">単価</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">数量</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">割引</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">小計</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">操作</th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {salesItems.map((item) => (
                    <tr key={item.id}>
                      <td className="px-4 py-4">
                        <div className="font-medium text-sm">{item.product.name}</div>
                        <div className="text-xs text-gray-500">{item.product.code}</div>
                      </td>
                      <td className="px-4 py-4 text-sm">¥{item.unitPrice.toLocaleString()}</td>
                      <td className="px-4 py-4">
                        <input
                          type="number"
                          min="1"
                          value={item.quantity}
                          onChange={(e) => updateItemQuantity(item.id, parseInt(e.target.value) || 1)}
                          className="w-20 px-2 py-1 text-sm border border-gray-300 rounded"
                        />
                        <span className="ml-1 text-xs text-gray-500">{item.product.unit}</span>
                      </td>
                      <td className="px-4 py-4">
                        <input
                          type="number"
                          min="0"
                          max="100"
                          value={item.discount}
                          onChange={(e) => updateItemDiscount(item.id, parseFloat(e.target.value) || 0)}
                          className="w-16 px-2 py-1 text-sm border border-gray-300 rounded"
                        />
                        <span className="ml-1 text-xs">%</span>
                      </td>
                      <td className="px-4 py-4 text-sm font-medium">¥{item.subtotal.toLocaleString()}</td>
                      <td className="px-4 py-4">
                        <button
                          type="button"
                          onClick={() => removeSalesItem(item.id)}
                          className="text-red-600 hover:text-red-800 text-sm"
                        >
                          削除
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* 合計金額 */}
        {salesItems.length > 0 && (
          <div className="bg-white p-6 rounded-lg shadow border-l-4 border-green-500">
            <div className="flex justify-between items-center">
              <div>
                <h3 className="text-lg font-semibold text-gray-900">売上合計</h3>
                {totalDiscountAmount > 0 && (
                  <p className="text-sm text-gray-600">割引合計: ¥{totalDiscountAmount.toLocaleString()}</p>
                )}
              </div>
              <div className="text-right">
                <div className="text-2xl font-bold text-green-600">¥{totalAmount.toLocaleString()}</div>
                <div className="text-sm text-gray-500">(税抜)</div>
              </div>
            </div>
          </div>
        )}

        {/* 備考 */}
        <div className="bg-white p-6 rounded-lg shadow">
          <h2 className="text-xl font-semibold mb-4">備考</h2>
          <textarea
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            rows={3}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="売上に関する備考を入力してください"
          />
        </div>

        {/* 送信ボタン */}
        <div className="flex justify-end space-x-4">
          <button
            type="button"
            className="px-6 py-2 border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50"
            onClick={() => {
              setSelectedCustomer(null);
              setSalesItems([]);
              setNotes('');
              setSalesDate(new Date().toISOString().split('T')[0]);
            }}
          >
            クリア
          </button>
          <button
            type="submit"
            disabled={!selectedCustomer || salesItems.length === 0}
            className="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
          >
            売上登録
          </button>
        </div>
      </form>
    </div>
  );
};

export default SalesInput;