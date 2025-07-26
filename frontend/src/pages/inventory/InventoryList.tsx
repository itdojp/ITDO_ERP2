import React, { useState } from "react";

interface InventoryItem {
  id: string;
  productCode: string;
  productName: string;
  category: string;
  location: string;
  currentStock: number;
  minStock: number;
  maxStock: number;
  unit: string;
  lastUpdated: string;
  status: "normal" | "low" | "out" | "excess";
  value: number;
}

const mockInventoryData: InventoryItem[] = [
  {
    id: "1",
    productCode: "LT-001",
    productName: "ThinkPad X1 Carbon Gen 11",
    category: "ラップトップ",
    location: "倉庫A-1-A",
    currentStock: 25,
    minStock: 5,
    maxStock: 100,
    unit: "台",
    lastUpdated: "2025-07-22T10:30:00",
    status: "normal",
    value: 4950000,
  },
  {
    id: "2",
    productCode: "MN-001",
    productName: "Dell UltraSharp U2723QE",
    category: "モニター",
    location: "倉庫A-2-B",
    currentStock: 15,
    minStock: 3,
    maxStock: 50,
    unit: "台",
    lastUpdated: "2025-07-22T09:15:00",
    status: "normal",
    value: 1275000,
  },
  {
    id: "3",
    productCode: "KB-001",
    productName: "HHKB Professional HYBRID",
    category: "キーボード",
    location: "倉庫B-1-C",
    currentStock: 3,
    minStock: 2,
    maxStock: 30,
    unit: "個",
    lastUpdated: "2025-07-22T11:45:00",
    status: "low",
    value: 105000,
  },
  {
    id: "4",
    productCode: "ACC-001",
    productName: "USB-C Hub 7-in-1",
    category: "アクセサリー",
    location: "倉庫B-2-A",
    currentStock: 120,
    minStock: 10,
    maxStock: 100,
    unit: "個",
    lastUpdated: "2025-07-22T08:20:00",
    status: "excess",
    value: 1020000,
  },
  {
    id: "5",
    productCode: "SW-001",
    productName: "Microsoft Office 365",
    category: "ソフトウェア",
    location: "デジタル倉庫",
    currentStock: 0,
    minStock: 50,
    maxStock: 1000,
    unit: "ライセンス",
    lastUpdated: "2025-07-21T16:30:00",
    status: "out",
    value: 0,
  },
  {
    id: "6",
    productCode: "LT-002",
    productName: 'MacBook Pro 14" M3',
    category: "ラップトップ",
    location: "倉庫A-1-B",
    currentStock: 8,
    minStock: 2,
    maxStock: 20,
    unit: "台",
    lastUpdated: "2025-07-22T12:00:00",
    status: "normal",
    value: 2384000,
  },
];

export const InventoryList: React.FC = () => {
  const [searchTerm, setSearchTerm] = useState("");
  const [categoryFilter, setCategoryFilter] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [locationFilter, setLocationFilter] = useState("");

  const filteredInventory = mockInventoryData.filter((item) => {
    const matchesSearch =
      item.productName.toLowerCase().includes(searchTerm.toLowerCase()) ||
      item.productCode.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesCategory = !categoryFilter || item.category === categoryFilter;
    const matchesStatus = !statusFilter || item.status === statusFilter;
    const matchesLocation =
      !locationFilter || item.location.includes(locationFilter);

    return matchesSearch && matchesCategory && matchesStatus && matchesLocation;
  });

  const categories = [
    ...new Set(mockInventoryData.map((item) => item.category)),
  ];
  const locations = [
    ...new Set(mockInventoryData.map((item) => item.location)),
  ];
  const statuses = [...new Set(mockInventoryData.map((item) => item.status))];

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "normal":
        return "bg-green-100 text-green-800";
      case "low":
        return "bg-yellow-100 text-yellow-800";
      case "out":
        return "bg-red-100 text-red-800";
      case "excess":
        return "bg-blue-100 text-blue-800";
      default:
        return "bg-gray-100 text-gray-800";
    }
  };

  const getStatusLabel = (status: string) => {
    switch (status) {
      case "normal":
        return "正常";
      case "low":
        return "在庫少";
      case "out":
        return "在庫切れ";
      case "excess":
        return "在庫過多";
      default:
        return status;
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "normal":
        return "✓";
      case "low":
        return "⚠️";
      case "out":
        return "❌";
      case "excess":
        return "📈";
      default:
        return "";
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return (
      date.toLocaleDateString("ja-JP") +
      " " +
      date.toLocaleTimeString("ja-JP", {
        hour: "2-digit",
        minute: "2-digit",
      })
    );
  };

  const totalValue = filteredInventory.reduce(
    (sum, item) => sum + item.value,
    0,
  );
  const alertItems = filteredInventory.filter(
    (item) => item.status === "low" || item.status === "out",
  ).length;

  return (
    <div className="max-w-7xl mx-auto p-6">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">在庫管理</h1>
          <p className="text-gray-600 mt-1">リアルタイム在庫状況と管理</p>
        </div>
        <button className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 transition-colors">
          在庫調整入力
        </button>
      </div>

      {/* サマリーカード */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <div className="bg-white p-4 rounded-lg shadow border-l-4 border-blue-500">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">総在庫価値</p>
              <p className="text-xl font-bold text-gray-900">
                ¥{totalValue.toLocaleString()}
              </p>
            </div>
            <div className="text-blue-500 text-2xl">💰</div>
          </div>
        </div>

        <div className="bg-white p-4 rounded-lg shadow border-l-4 border-green-500">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">総アイテム数</p>
              <p className="text-xl font-bold text-gray-900">
                {filteredInventory.length}品目
              </p>
            </div>
            <div className="text-green-500 text-2xl">📦</div>
          </div>
        </div>

        <div className="bg-white p-4 rounded-lg shadow border-l-4 border-yellow-500">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">要注意アイテム</p>
              <p className="text-xl font-bold text-gray-900">
                {alertItems}品目
              </p>
            </div>
            <div className="text-yellow-500 text-2xl">⚠️</div>
          </div>
        </div>

        <div className="bg-white p-4 rounded-lg shadow border-l-4 border-purple-500">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">最終更新</p>
              <p className="text-sm font-medium text-gray-900">
                {formatDate(new Date().toISOString())}
              </p>
            </div>
            <div className="text-purple-500 text-2xl">🔄</div>
          </div>
        </div>
      </div>

      {/* フィルター */}
      <div className="bg-white p-4 rounded-lg shadow mb-6">
        <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              検索
            </label>
            <input
              type="text"
              placeholder="商品名・コードで検索"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              カテゴリ
            </label>
            <select
              value={categoryFilter}
              onChange={(e) => setCategoryFilter(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">すべて</option>
              {categories.map((cat) => (
                <option key={cat} value={cat}>
                  {cat}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              ステータス
            </label>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">すべて</option>
              {statuses.map((status) => (
                <option key={status} value={status}>
                  {getStatusLabel(status)}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              保管場所
            </label>
            <input
              type="text"
              placeholder="保管場所で絞り込み"
              value={locationFilter}
              onChange={(e) => setLocationFilter(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div className="flex items-end">
            <button
              onClick={() => {
                setSearchTerm("");
                setCategoryFilter("");
                setStatusFilter("");
                setLocationFilter("");
              }}
              className="px-4 py-2 text-gray-600 hover:text-gray-800 transition-colors"
            >
              クリア
            </button>
          </div>
        </div>
      </div>

      {/* 在庫テーブル */}
      <div className="bg-white shadow rounded-lg overflow-hidden">
        <div className="px-4 py-3 border-b border-gray-200 bg-gray-50">
          <div className="flex justify-between items-center">
            <h3 className="text-lg font-medium text-gray-900">在庫一覧</h3>
            <p className="text-sm text-gray-600">
              {filteredInventory.length}件表示中
            </p>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  商品情報
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  保管場所
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  現在在庫
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  在庫レベル
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  ステータス
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  在庫価値
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  最終更新
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {filteredInventory.map((item) => (
                <tr key={item.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div>
                      <div className="text-sm font-medium text-gray-900">
                        {item.productName}
                      </div>
                      <div className="text-sm text-gray-500 font-mono">
                        {item.productCode}
                      </div>
                      <div className="text-xs text-gray-400">
                        {item.category}
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 font-mono">
                    {item.location}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm font-medium text-gray-900">
                      {item.currentStock} {item.unit}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-xs text-gray-500">
                      最小: {item.minStock} / 最大: {item.maxStock} {item.unit}
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2 mt-1">
                      <div
                        className={`h-2 rounded-full ${
                          item.currentStock <= item.minStock
                            ? "bg-red-500"
                            : item.currentStock >= item.maxStock
                              ? "bg-blue-500"
                              : "bg-green-500"
                        }`}
                        style={{
                          width: `${Math.min(
                            (item.currentStock / item.maxStock) * 100,
                            100,
                          )}%`,
                        }}
                      />
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span
                      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusBadge(item.status)}`}
                    >
                      <span className="mr-1">{getStatusIcon(item.status)}</span>
                      {getStatusLabel(item.status)}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 font-medium">
                    ¥{item.value.toLocaleString()}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-xs text-gray-500">
                    {formatDate(item.lastUpdated)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {filteredInventory.length === 0 && (
          <div className="text-center py-12">
            <div className="text-gray-500">
              <svg
                className="mx-auto h-12 w-12 text-gray-400 mb-4"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2M4 13h2m13-8l-2-2m0 0l-2 2m2-2v6m-7 4v-2"
                />
              </svg>
              <p className="text-lg font-medium">
                該当する在庫が見つかりません
              </p>
              <p className="text-sm">検索条件を変更してお試しください</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default InventoryList;
