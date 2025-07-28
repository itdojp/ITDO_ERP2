/**
 * プロジェクト進捗ダッシュボードコンポーネント
 */

import React from "react";
import {
  Project,
  ProgressReport,
  Budget,
} from "../../services/projectManagement";
import {
  ChartBarIcon,
  CurrencyYenIcon,
  ExclamationTriangleIcon,
} from "@heroicons/react/24/outline";

interface ProjectDashboardProps {
  project: Project;
  progressReport?: ProgressReport;
  budget?: Budget;
}

export const ProjectDashboard: React.FC<ProjectDashboardProps> = ({
  project,
  progressReport,
  budget,
}) => {
  const formatCurrency = (amount: number): string => {
    return new Intl.NumberFormat("ja-JP", {
      style: "currency",
      currency: "JPY",
    }).format(amount);
  };

  const formatDate = (dateString: string): string => {
    return new Date(dateString).toLocaleDateString("ja-JP");
  };

  const getProgressColor = (percentage: number): string => {
    if (percentage >= 80) return "text-green-600";
    if (percentage >= 50) return "text-yellow-600";
    return "text-red-600";
  };

  const getBudgetStatusColor = (consumptionRate: number): string => {
    if (consumptionRate <= 80) return "text-green-600";
    if (consumptionRate <= 100) return "text-yellow-600";
    return "text-red-600";
  };

  const calculateDaysRemaining = (): number => {
    const today = new Date();
    const endDate = new Date(project.endDate);
    const diffTime = endDate.getTime() - today.getTime();
    return Math.ceil(diffTime / (1000 * 60 * 60 * 24));
  };

  const daysRemaining = calculateDaysRemaining();
  const overallProgress = progressReport?.overallProgress || 0;

  return (
    <div className="space-y-6">
      {/* プロジェクト概要 */}
      <div className="bg-white shadow rounded-lg p-6">
        <h2 className="text-lg font-medium text-gray-900 mb-4">
          プロジェクト概要
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <div>
            <p className="text-sm text-gray-500">ステータス</p>
            <p className="mt-1 text-lg font-medium">
              <span
                className={`px-2 py-1 text-sm rounded-full ${
                  project.status === "active"
                    ? "bg-green-100 text-green-800"
                    : project.status === "completed"
                      ? "bg-blue-100 text-blue-800"
                      : project.status === "suspended"
                        ? "bg-yellow-100 text-yellow-800"
                        : "bg-gray-100 text-gray-800"
                }`}
              >
                {project.status === "planning"
                  ? "計画中"
                  : project.status === "active"
                    ? "進行中"
                    : project.status === "completed"
                      ? "完了"
                      : "中断"}
              </span>
            </p>
          </div>
          <div>
            <p className="text-sm text-gray-500">期間</p>
            <p className="mt-1 text-lg font-medium">
              {formatDate(project.startDate)} - {formatDate(project.endDate)}
            </p>
          </div>
          <div>
            <p className="text-sm text-gray-500">残り日数</p>
            <p
              className={`mt-1 text-lg font-medium ${
                daysRemaining < 0
                  ? "text-red-600"
                  : daysRemaining <= 7
                    ? "text-yellow-600"
                    : "text-gray-900"
              }`}
            >
              {daysRemaining < 0
                ? `${Math.abs(daysRemaining)}日超過`
                : `${daysRemaining}日`}
            </p>
          </div>
          <div>
            <p className="text-sm text-gray-500">予算</p>
            <p className="mt-1 text-lg font-medium">
              {formatCurrency(project.budget)}
            </p>
          </div>
        </div>
      </div>

      {/* 進捗状況 */}
      <div className="bg-white shadow rounded-lg p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-medium text-gray-900">進捗状況</h2>
          <ChartBarIcon className="h-5 w-5 text-gray-400" />
        </div>
        <div className="space-y-4">
          <div>
            <div className="flex justify-between mb-1">
              <span className="text-sm font-medium text-gray-700">
                全体進捗
              </span>
              <span
                className={`text-sm font-medium ${getProgressColor(overallProgress)}`}
              >
                {overallProgress}%
              </span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className={`h-2 rounded-full ${
                  overallProgress >= 80
                    ? "bg-green-500"
                    : overallProgress >= 50
                      ? "bg-yellow-500"
                      : "bg-red-500"
                }`}
                style={{ width: `${overallProgress}%` }}
              />
            </div>
          </div>

          {progressReport && (
            <div className="grid grid-cols-2 gap-4 mt-4">
              <div>
                <h3 className="text-sm font-medium text-gray-700 mb-2">
                  タスクステータス
                </h3>
                <div className="space-y-2">
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-600">未着手</span>
                    <span className="text-sm font-medium">
                      {progressReport.taskStatus.not_started || 0}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-600">進行中</span>
                    <span className="text-sm font-medium">
                      {progressReport.taskStatus.in_progress || 0}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-600">完了</span>
                    <span className="text-sm font-medium">
                      {progressReport.taskStatus.completed || 0}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-600">保留</span>
                    <span className="text-sm font-medium">
                      {progressReport.taskStatus.on_hold || 0}
                    </span>
                  </div>
                </div>
              </div>

              <div>
                <h3 className="text-sm font-medium text-gray-700 mb-2">
                  マイルストーン
                </h3>
                <div className="space-y-2">
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-600">未達成</span>
                    <span className="text-sm font-medium">
                      {progressReport.milestoneStatus.pending || 0}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-600">達成</span>
                    <span className="text-sm font-medium">
                      {progressReport.milestoneStatus.achieved || 0}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-600">遅延</span>
                    <span className="text-sm font-medium">
                      {progressReport.milestoneStatus.delayed || 0}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* 予算状況 */}
      {budget && (
        <div className="bg-white shadow rounded-lg p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-medium text-gray-900">予算状況</h2>
            <CurrencyYenIcon className="h-5 w-5 text-gray-400" />
          </div>
          <div className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <p className="text-sm text-gray-500">予算</p>
                <p className="mt-1 text-lg font-medium">
                  {formatCurrency(budget.budgetAmount)}
                </p>
              </div>
              <div>
                <p className="text-sm text-gray-500">実績コスト</p>
                <p className="mt-1 text-lg font-medium">
                  {formatCurrency(budget.actualCost)}
                </p>
              </div>
              <div>
                <p className="text-sm text-gray-500">消化率</p>
                <p
                  className={`mt-1 text-lg font-medium ${getBudgetStatusColor(budget.consumptionRate)}`}
                >
                  {budget.consumptionRate.toFixed(1)}%
                </p>
              </div>
            </div>

            <div>
              <h3 className="text-sm font-medium text-gray-700 mb-2">
                コスト内訳
              </h3>
              <div className="space-y-2">
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">人件費</span>
                  <div className="text-right">
                    <span className="text-sm font-medium">
                      {formatCurrency(budget.costBreakdown.labor.actual)}
                    </span>
                    <span className="text-xs text-gray-500 ml-2">
                      (予定:{" "}
                      {formatCurrency(budget.costBreakdown.labor.planned)})
                    </span>
                  </div>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">外注費</span>
                  <div className="text-right">
                    <span className="text-sm font-medium">
                      {formatCurrency(budget.costBreakdown.outsourcing.actual)}
                    </span>
                    <span className="text-xs text-gray-500 ml-2">
                      (予定:{" "}
                      {formatCurrency(budget.costBreakdown.outsourcing.planned)}
                      )
                    </span>
                  </div>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">経費</span>
                  <div className="text-right">
                    <span className="text-sm font-medium">
                      {formatCurrency(budget.costBreakdown.expense.actual)}
                    </span>
                    <span className="text-xs text-gray-500 ml-2">
                      (予定:{" "}
                      {formatCurrency(budget.costBreakdown.expense.planned)})
                    </span>
                  </div>
                </div>
              </div>
            </div>

            {budget.revenue > 0 && (
              <div className="border-t pt-4">
                <div className="grid grid-cols-3 gap-4">
                  <div>
                    <p className="text-sm text-gray-500">売上</p>
                    <p className="mt-1 text-lg font-medium">
                      {formatCurrency(budget.revenue)}
                    </p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-500">利益</p>
                    <p
                      className={`mt-1 text-lg font-medium ${
                        budget.profit >= 0 ? "text-green-600" : "text-red-600"
                      }`}
                    >
                      {formatCurrency(budget.profit)}
                    </p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-500">利益率</p>
                    <p
                      className={`mt-1 text-lg font-medium ${
                        budget.profitRate >= 20
                          ? "text-green-600"
                          : budget.profitRate >= 10
                            ? "text-yellow-600"
                            : "text-red-600"
                      }`}
                    >
                      {budget.profitRate.toFixed(1)}%
                    </p>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* リスク情報 */}
      {progressReport && progressReport.risks.length > 0 && (
        <div className="bg-white shadow rounded-lg p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-medium text-gray-900">リスク情報</h2>
            <ExclamationTriangleIcon className="h-5 w-5 text-yellow-500" />
          </div>
          <div className="space-y-3">
            {progressReport.risks.map((risk, index) => (
              <div
                key={index}
                className={`flex items-start space-x-3 p-3 rounded-lg ${
                  risk.impact === "high"
                    ? "bg-red-50"
                    : risk.impact === "medium"
                      ? "bg-yellow-50"
                      : "bg-gray-50"
                }`}
              >
                <ExclamationTriangleIcon
                  className={`h-5 w-5 flex-shrink-0 mt-0.5 ${
                    risk.impact === "high"
                      ? "text-red-600"
                      : risk.impact === "medium"
                        ? "text-yellow-600"
                        : "text-gray-600"
                  }`}
                />
                <div>
                  <p className="text-sm font-medium text-gray-900">
                    {risk.type === "schedule"
                      ? "スケジュールリスク"
                      : risk.type === "budget"
                        ? "予算リスク"
                        : risk.type === "resource"
                          ? "リソースリスク"
                          : "その他のリスク"}
                  </p>
                  <p className="text-sm text-gray-600 mt-1">
                    {risk.description}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default ProjectDashboard;
