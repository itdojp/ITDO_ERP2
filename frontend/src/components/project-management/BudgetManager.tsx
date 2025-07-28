/**
 * 予算管理コンポーネント
 */

import React, { useState } from "react";
import { Budget, BudgetUpdate } from "../../services/projectManagement";
import { projectManagementService } from "../../services/projectManagementExtended";
import {
  CurrencyYenIcon,
  ChartBarIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
} from "@heroicons/react/24/outline";

interface BudgetManagerProps {
  projectId: number;
  budget: Budget | null;
  onUpdate: () => void;
}

export const BudgetManager: React.FC<BudgetManagerProps> = ({
  projectId,
  budget,
  onUpdate,
}) => {
  const [isEditing, setIsEditing] = useState(false);
  const [formData, setFormData] = useState<BudgetUpdate>({
    actualCost: budget?.actualCost || 0,
    costBreakdown: budget?.costBreakdown || {
      labor: { planned: 0, actual: 0 },
      outsourcing: { planned: 0, actual: 0 },
      expense: { planned: 0, actual: 0 },
    },
    revenue: budget?.revenue || 0,
  });

  const formatCurrency = (amount: number): string => {
    return new Intl.NumberFormat("ja-JP", {
      style: "currency",
      currency: "JPY",
    }).format(amount);
  };

  const handleUpdateBudget = async () => {
    try {
      if (budget) {
        await projectManagementService.budgets.update(budget.id, formData);
      } else {
        await projectManagementService.budgets.create({
          projectId,
          budgetAmount: 0, // This should come from project
          actualCost: formData.actualCost,
          costBreakdown: formData.costBreakdown,
          revenue: formData.revenue,
        });
      }
      setIsEditing(false);
      onUpdate();
    } catch (err) {
      // console.error('Failed to update budget:', err);
      alert("予算情報の更新に失敗しました");
    }
  };

  const calculateTotal = (type: "planned" | "actual"): number => {
    return (
      formData.costBreakdown.labor[type] +
      formData.costBreakdown.outsourcing[type] +
      formData.costBreakdown.expense[type]
    );
  };

  const updateCostItem = (
    category: keyof typeof formData.costBreakdown,
    type: "planned" | "actual",
    value: number,
  ) => {
    const newCostBreakdown = {
      ...formData.costBreakdown,
      [category]: {
        ...formData.costBreakdown[category],
        [type]: value,
      },
    };

    const newActualCost = calculateTotal("actual");

    setFormData({
      ...formData,
      costBreakdown: newCostBreakdown,
      actualCost: newActualCost,
    });
  };

  const getVarianceStatus = (
    variance: number,
  ): { color: string; icon: JSX.Element; label: string } => {
    if (variance <= 0) {
      return {
        color: "text-green-600",
        icon: <CheckCircleIcon className="h-5 w-5" />,
        label: "予算内",
      };
    } else if (variance <= 10) {
      return {
        color: "text-yellow-600",
        icon: <ExclamationTriangleIcon className="h-5 w-5" />,
        label: "警告",
      };
    } else {
      return {
        color: "text-red-600",
        icon: <ExclamationTriangleIcon className="h-5 w-5" />,
        label: "超過",
      };
    }
  };

  if (!budget && !isEditing) {
    return (
      <div className="bg-white shadow rounded-lg p-6">
        <div className="text-center">
          <CurrencyYenIcon className="mx-auto h-12 w-12 text-gray-400" />
          <h3 className="mt-2 text-sm font-medium text-gray-900">
            予算情報がありません
          </h3>
          <p className="mt-1 text-sm text-gray-500">
            予算情報を設定してください
          </p>
          <div className="mt-6">
            <button
              onClick={() => setIsEditing(true)}
              className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-indigo-600 hover:bg-indigo-700"
            >
              予算を設定
            </button>
          </div>
        </div>
      </div>
    );
  }

  const displayBudget = budget || {
    budgetAmount: 0,
    actualCost: formData.actualCost,
    consumptionRate: 0,
    costBreakdown: formData.costBreakdown,
    variance: 0,
    variancePercentage: 0,
    revenue: formData.revenue,
    profit: formData.revenue - formData.actualCost,
    profitRate:
      formData.revenue > 0
        ? ((formData.revenue - formData.actualCost) / formData.revenue) * 100
        : 0,
  };

  const varianceStatus = getVarianceStatus(displayBudget.variancePercentage);

  return (
    <div className="space-y-6">
      {/* 予算サマリー */}
      <div className="bg-white shadow rounded-lg p-6">
        <div className="flex justify-between items-center mb-6">
          <h3 className="text-lg font-medium text-gray-900">予算概要</h3>
          {!isEditing && (
            <button
              onClick={() => setIsEditing(true)}
              className="text-sm text-indigo-600 hover:text-indigo-900"
            >
              編集
            </button>
          )}
        </div>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <div>
            <p className="text-sm text-gray-500">予算額</p>
            <p className="mt-1 text-2xl font-semibold text-gray-900">
              {formatCurrency(displayBudget.budgetAmount)}
            </p>
          </div>
          <div>
            <p className="text-sm text-gray-500">実績コスト</p>
            <p className="mt-1 text-2xl font-semibold text-gray-900">
              {formatCurrency(displayBudget.actualCost)}
            </p>
          </div>
          <div>
            <p className="text-sm text-gray-500">消化率</p>
            <div className="mt-1 flex items-center">
              <p className="text-2xl font-semibold text-gray-900">
                {displayBudget.consumptionRate.toFixed(1)}%
              </p>
              <div className="ml-2 w-16 bg-gray-200 rounded-full h-2">
                <div
                  className={`h-2 rounded-full ${
                    displayBudget.consumptionRate <= 80
                      ? "bg-green-500"
                      : displayBudget.consumptionRate <= 100
                        ? "bg-yellow-500"
                        : "bg-red-500"
                  }`}
                  style={{
                    width: `${Math.min(displayBudget.consumptionRate, 100)}%`,
                  }}
                />
              </div>
            </div>
          </div>
          <div>
            <p className="text-sm text-gray-500">差異</p>
            <div className="mt-1 flex items-center">
              <span className={varianceStatus.color}>
                {varianceStatus.icon}
              </span>
              <p
                className={`ml-2 text-2xl font-semibold ${varianceStatus.color}`}
              >
                {formatCurrency(Math.abs(displayBudget.variance))}
              </p>
            </div>
            <p className={`text-sm ${varianceStatus.color}`}>
              {varianceStatus.label} (
              {displayBudget.variancePercentage.toFixed(1)}%)
            </p>
          </div>
        </div>
      </div>

      {/* コスト内訳 */}
      <div className="bg-white shadow rounded-lg p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-6">コスト内訳</h3>

        {isEditing ? (
          <div className="space-y-4">
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead>
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      費目
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      計画
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      実績
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  <tr>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                      人件費
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <input
                        type="number"
                        value={formData.costBreakdown.labor.planned}
                        onChange={(e) =>
                          updateCostItem(
                            "labor",
                            "planned",
                            parseInt(e.target.value) || 0,
                          )
                        }
                        className="w-32 rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                      />
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <input
                        type="number"
                        value={formData.costBreakdown.labor.actual}
                        onChange={(e) =>
                          updateCostItem(
                            "labor",
                            "actual",
                            parseInt(e.target.value) || 0,
                          )
                        }
                        className="w-32 rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                      />
                    </td>
                  </tr>
                  <tr>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                      外注費
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <input
                        type="number"
                        value={formData.costBreakdown.outsourcing.planned}
                        onChange={(e) =>
                          updateCostItem(
                            "outsourcing",
                            "planned",
                            parseInt(e.target.value) || 0,
                          )
                        }
                        className="w-32 rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                      />
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <input
                        type="number"
                        value={formData.costBreakdown.outsourcing.actual}
                        onChange={(e) =>
                          updateCostItem(
                            "outsourcing",
                            "actual",
                            parseInt(e.target.value) || 0,
                          )
                        }
                        className="w-32 rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                      />
                    </td>
                  </tr>
                  <tr>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                      経費
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <input
                        type="number"
                        value={formData.costBreakdown.expense.planned}
                        onChange={(e) =>
                          updateCostItem(
                            "expense",
                            "planned",
                            parseInt(e.target.value) || 0,
                          )
                        }
                        className="w-32 rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                      />
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <input
                        type="number"
                        value={formData.costBreakdown.expense.actual}
                        onChange={(e) =>
                          updateCostItem(
                            "expense",
                            "actual",
                            parseInt(e.target.value) || 0,
                          )
                        }
                        className="w-32 rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                      />
                    </td>
                  </tr>
                  <tr className="bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-bold text-gray-900">
                      合計
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-bold text-gray-900">
                      {formatCurrency(calculateTotal("planned"))}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-bold text-gray-900">
                      {formatCurrency(calculateTotal("actual"))}
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>

            <div className="mt-6">
              <label className="block text-sm font-medium text-gray-700">
                売上
              </label>
              <input
                type="number"
                value={formData.revenue}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    revenue: parseInt(e.target.value) || 0,
                  })
                }
                className="mt-1 w-48 rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
              />
            </div>

            <div className="flex justify-end space-x-3">
              <button
                onClick={() => {
                  setIsEditing(false);
                  setFormData({
                    actualCost: budget?.actualCost || 0,
                    costBreakdown: budget?.costBreakdown || {
                      labor: { planned: 0, actual: 0 },
                      outsourcing: { planned: 0, actual: 0 },
                      expense: { planned: 0, actual: 0 },
                    },
                    revenue: budget?.revenue || 0,
                  });
                }}
                className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md shadow-sm hover:bg-gray-50"
              >
                キャンセル
              </button>
              <button
                onClick={handleUpdateBudget}
                className="px-4 py-2 text-sm font-medium text-white bg-indigo-600 border border-transparent rounded-md shadow-sm hover:bg-indigo-700"
              >
                保存
              </button>
            </div>
          </div>
        ) : (
          <div className="space-y-4">
            <div className="grid grid-cols-3 gap-4">
              <div>
                <h4 className="text-sm font-medium text-gray-500">人件費</h4>
                <p className="mt-1 text-lg font-medium text-gray-900">
                  {formatCurrency(displayBudget.costBreakdown.labor.actual)}
                </p>
                <p className="text-sm text-gray-500">
                  予定:{" "}
                  {formatCurrency(displayBudget.costBreakdown.labor.planned)}
                </p>
              </div>
              <div>
                <h4 className="text-sm font-medium text-gray-500">外注費</h4>
                <p className="mt-1 text-lg font-medium text-gray-900">
                  {formatCurrency(
                    displayBudget.costBreakdown.outsourcing.actual,
                  )}
                </p>
                <p className="text-sm text-gray-500">
                  予定:{" "}
                  {formatCurrency(
                    displayBudget.costBreakdown.outsourcing.planned,
                  )}
                </p>
              </div>
              <div>
                <h4 className="text-sm font-medium text-gray-500">経費</h4>
                <p className="mt-1 text-lg font-medium text-gray-900">
                  {formatCurrency(displayBudget.costBreakdown.expense.actual)}
                </p>
                <p className="text-sm text-gray-500">
                  予定:{" "}
                  {formatCurrency(displayBudget.costBreakdown.expense.planned)}
                </p>
              </div>
            </div>

            {/* グラフ表示 */}
            <div className="mt-6">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-gray-700">
                  コスト構成比
                </span>
                <ChartBarIcon className="h-5 w-5 text-gray-400" />
              </div>
              <div className="w-full bg-gray-200 rounded-full h-8 flex overflow-hidden">
                {displayBudget.actualCost > 0 && (
                  <>
                    <div
                      className="bg-blue-500"
                      style={{
                        width: `${(displayBudget.costBreakdown.labor.actual / displayBudget.actualCost) * 100}%`,
                      }}
                    />
                    <div
                      className="bg-green-500"
                      style={{
                        width: `${(displayBudget.costBreakdown.outsourcing.actual / displayBudget.actualCost) * 100}%`,
                      }}
                    />
                    <div
                      className="bg-yellow-500"
                      style={{
                        width: `${(displayBudget.costBreakdown.expense.actual / displayBudget.actualCost) * 100}%`,
                      }}
                    />
                  </>
                )}
              </div>
              <div className="mt-2 flex justify-between text-xs text-gray-500">
                <span className="flex items-center">
                  <span className="w-3 h-3 bg-blue-500 rounded-full mr-1"></span>
                  人件費
                </span>
                <span className="flex items-center">
                  <span className="w-3 h-3 bg-green-500 rounded-full mr-1"></span>
                  外注費
                </span>
                <span className="flex items-center">
                  <span className="w-3 h-3 bg-yellow-500 rounded-full mr-1"></span>
                  経費
                </span>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* 収益性分析 */}
      {displayBudget.revenue > 0 && (
        <div className="bg-white shadow rounded-lg p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-6">収益性分析</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div>
              <p className="text-sm text-gray-500">売上</p>
              <p className="mt-1 text-2xl font-semibold text-gray-900">
                {formatCurrency(displayBudget.revenue)}
              </p>
            </div>
            <div>
              <p className="text-sm text-gray-500">利益</p>
              <p
                className={`mt-1 text-2xl font-semibold ${
                  displayBudget.profit >= 0 ? "text-green-600" : "text-red-600"
                }`}
              >
                {formatCurrency(displayBudget.profit)}
              </p>
            </div>
            <div>
              <p className="text-sm text-gray-500">利益率</p>
              <p
                className={`mt-1 text-2xl font-semibold ${
                  displayBudget.profitRate >= 20
                    ? "text-green-600"
                    : displayBudget.profitRate >= 10
                      ? "text-yellow-600"
                      : "text-red-600"
                }`}
              >
                {displayBudget.profitRate.toFixed(1)}%
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default BudgetManager;
