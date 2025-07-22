import React, { useState } from 'react';

interface SalesData {
  month: string;
  sales: number;
  target: number;
}

const mockSalesData: SalesData[] = [
  { month: '1月', sales: 4500000, target: 5000000 },
  { month: '2月', sales: 3200000, target: 4000000 },
  { month: '3月', sales: 5800000, target: 5500000 },
  { month: '4月', sales: 4200000, target: 4500000 },
  { month: '5月', sales: 6100000, target: 6000000 },
  { month: '6月', sales: 5400000, target: 5800000 },
];

export const SalesChart: React.FC = () => {
  const [period, setPeriod] = useState<'month' | 'quarter' | 'year'>('month');

  const maxValue = Math.max(...mockSalesData.map(d => Math.max(d.sales, d.target)));
  
  return (
    <div className="bg-white p-6 rounded-lg shadow">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">売上実績</h3>
          <p className="text-sm text-gray-500">月別売上と目標の比較</p>
        </div>
        <div className="flex space-x-1">
          {(['month', 'quarter', 'year'] as const).map((p) => (
            <button
              key={p}
              onClick={() => setPeriod(p)}
              className={`
                px-3 py-1 text-sm rounded
                ${period === p 
                  ? 'bg-blue-100 text-blue-700' 
                  : 'text-gray-500 hover:text-gray-700'
                }
              `}
            >
              {p === 'month' ? '月次' : p === 'quarter' ? '四半期' : '年次'}
            </button>
          ))}
        </div>
      </div>

      <div className="space-y-4">
        {mockSalesData.map((data, index) => (
          <div key={index} className="space-y-2">
            <div className="flex justify-between text-sm">
              <span className="font-medium text-gray-700">{data.month}</span>
              <span className="text-gray-500">
                ¥{data.sales.toLocaleString()} / ¥{data.target.toLocaleString()}
              </span>
            </div>
            <div className="flex space-x-2">
              <div className="flex-1 bg-gray-200 rounded-full h-3">
                <div
                  className="bg-blue-500 h-3 rounded-full"
                  style={{ width: `${(data.sales / maxValue) * 100}%` }}
                />
              </div>
              <div className="flex-1 bg-gray-200 rounded-full h-3">
                <div
                  className="bg-gray-400 h-3 rounded-full"
                  style={{ width: `${(data.target / maxValue) * 100}%` }}
                />
              </div>
            </div>
            <div className="flex justify-between text-xs text-gray-500">
              <span>実績: {((data.sales / data.target) * 100).toFixed(1)}%</span>
              <span className={data.sales >= data.target ? 'text-green-600' : 'text-red-600'}>
                {data.sales >= data.target ? '目標達成' : `未達 ${((data.target - data.sales) / 10000).toFixed(0)}万円`}
              </span>
            </div>
          </div>
        ))}
      </div>

      <div className="mt-6 pt-4 border-t border-gray-200">
        <div className="flex items-center justify-between text-sm">
          <div className="flex space-x-4">
            <div className="flex items-center">
              <div className="w-3 h-3 bg-blue-500 rounded mr-2" />
              <span>実績</span>
            </div>
            <div className="flex items-center">
              <div className="w-3 h-3 bg-gray-400 rounded mr-2" />
              <span>目標</span>
            </div>
          </div>
          <div className="text-gray-600">
            合計: ¥{mockSalesData.reduce((sum, d) => sum + d.sales, 0).toLocaleString()}
          </div>
        </div>
      </div>
    </div>
  );
};