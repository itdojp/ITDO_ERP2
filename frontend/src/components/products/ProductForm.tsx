import React, { useState } from "react";

interface ProductFormProps {
  onSubmit: (product: any) => void;
  onCancel: () => void;
}

export const ProductForm: React.FC<ProductFormProps> = ({
  onSubmit,
  onCancel,
}) => {
  const [formData, setFormData] = useState({
    code: "",
    name: "",
    price: "",
    stock: "",
    description: "",
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit({
      ...formData,
      price: parseFloat(formData.price),
      stock: parseInt(formData.stock),
    });
  };

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>,
  ) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    });
  };

  return (
    <form
      onSubmit={handleSubmit}
      className="max-w-lg mx-auto p-6 bg-white rounded-lg shadow"
    >
      <h2 className="text-2xl font-bold mb-6">商品登録</h2>

      <div className="mb-4">
        <label htmlFor="code" className="block text-sm font-medium mb-2">
          商品コード *
        </label>
        <input
          type="text"
          id="code"
          name="code"
          required
          value={formData.code}
          onChange={handleChange}
          className="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          placeholder="P001"
        />
      </div>

      <div className="mb-4">
        <label htmlFor="name" className="block text-sm font-medium mb-2">
          商品名 *
        </label>
        <input
          type="text"
          id="name"
          name="name"
          required
          value={formData.name}
          onChange={handleChange}
          className="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          placeholder="ノートPC"
        />
      </div>

      <div className="mb-4">
        <label htmlFor="price" className="block text-sm font-medium mb-2">
          価格 *
        </label>
        <input
          type="number"
          id="price"
          name="price"
          required
          min="0"
          step="1"
          value={formData.price}
          onChange={handleChange}
          className="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          placeholder="120000"
        />
      </div>

      <div className="mb-4">
        <label htmlFor="stock" className="block text-sm font-medium mb-2">
          初期在庫数 *
        </label>
        <input
          type="number"
          id="stock"
          name="stock"
          required
          min="0"
          value={formData.stock}
          onChange={handleChange}
          className="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          placeholder="10"
        />
      </div>

      <div className="mb-6">
        <label htmlFor="description" className="block text-sm font-medium mb-2">
          説明
        </label>
        <textarea
          id="description"
          name="description"
          value={formData.description}
          onChange={handleChange}
          rows={3}
          className="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          placeholder="商品の詳細説明を入力..."
        />
      </div>

      <div className="flex justify-end space-x-4">
        <button
          type="button"
          onClick={onCancel}
          className="px-4 py-2 text-gray-700 bg-gray-200 rounded hover:bg-gray-300"
        >
          キャンセル
        </button>
        <button
          type="submit"
          className="px-4 py-2 text-white bg-blue-600 rounded hover:bg-blue-700"
        >
          登録
        </button>
      </div>
    </form>
  );
};

export default ProductForm;
