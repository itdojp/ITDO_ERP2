/**
 * ガントチャートコンポーネント
 */

import React, { useMemo, useRef } from "react";
import { GanttTask, GanttDependency } from "../../services/projectManagement";

interface GanttChartProps {
  tasks: GanttTask[];
  dependencies: GanttDependency[];
  criticalPath: number[];
  startDate: string;
  endDate: string;
  onTaskClick?: (taskId: number) => void;
}

export const GanttChart: React.FC<GanttChartProps> = ({
  tasks,
  dependencies,
  criticalPath,
  startDate,
  endDate,
  onTaskClick,
}) => {
  const chartRef = useRef<HTMLDivElement>(null);
  const cellWidth = 30; // 1日あたりのピクセル幅
  const rowHeight = 40; // 行の高さ
  const headerHeight = 60; // ヘッダーの高さ

  // 日付範囲の計算
  const { dateRange, monthHeaders, totalDays } = useMemo(() => {
    const start = new Date(startDate);
    const end = new Date(endDate);
    const days: Date[] = [];
    const months: { month: string; days: number; startIndex: number }[] = [];

    const currentDate = new Date(start);
    let currentMonth = currentDate.getMonth();
    let monthDays = 0;
    let monthStartIndex = 0;

    while (currentDate <= end) {
      days.push(new Date(currentDate));

      if (currentDate.getMonth() !== currentMonth) {
        months.push({
          month: new Date(
            currentDate.getFullYear(),
            currentMonth,
          ).toLocaleDateString("ja-JP", { year: "numeric", month: "long" }),
          days: monthDays,
          startIndex: monthStartIndex,
        });
        currentMonth = currentDate.getMonth();
        monthStartIndex = days.length - 1;
        monthDays = 1;
      } else {
        monthDays++;
      }

      currentDate.setDate(currentDate.getDate() + 1);
    }

    // 最後の月を追加
    months.push({
      month: new Date(end.getFullYear(), currentMonth).toLocaleDateString(
        "ja-JP",
        { year: "numeric", month: "long" },
      ),
      days: monthDays,
      startIndex: monthStartIndex,
    });

    return {
      dateRange: days,
      monthHeaders: months,
      totalDays: days.length,
    };
  }, [startDate, endDate]);

  // タスクの位置計算
  const calculateTaskPosition = (task: GanttTask) => {
    const taskStart = new Date(task.startDate);
    const taskEnd = new Date(task.endDate);
    const chartStart = new Date(startDate);

    const startOffset = Math.floor(
      (taskStart.getTime() - chartStart.getTime()) / (1000 * 60 * 60 * 24),
    );
    const duration =
      Math.floor(
        (taskEnd.getTime() - taskStart.getTime()) / (1000 * 60 * 60 * 24),
      ) + 1;

    return {
      left: startOffset * cellWidth,
      width: duration * cellWidth,
      top: task.level * rowHeight,
    };
  };

  // タスクの色を取得
  const getTaskColor = (task: GanttTask): string => {
    if (criticalPath.includes(task.id)) {
      return "bg-red-500";
    }
    if (task.isMilestone) {
      return "bg-purple-500";
    }
    if (task.progress === 100) {
      return "bg-green-500";
    }
    if (task.progress > 0) {
      return "bg-blue-500";
    }
    return "bg-gray-400";
  };

  // 依存関係の線を描画
  const renderDependencyLine = (dep: GanttDependency) => {
    const sourceTask = tasks.find((t) => t.id === dep.source);
    const targetTask = tasks.find((t) => t.id === dep.target);

    if (!sourceTask || !targetTask) return null;

    const sourcePos = calculateTaskPosition(sourceTask);
    const targetPos = calculateTaskPosition(targetTask);

    const x1 = sourcePos.left + sourcePos.width;
    const y1 = sourcePos.top + rowHeight / 2;
    const x2 = targetPos.left;
    const y2 = targetPos.top + rowHeight / 2;

    return (
      <svg
        key={`dep-${dep.source}-${dep.target}`}
        className="absolute pointer-events-none"
        style={{
          left: 0,
          top: headerHeight,
          width: "100%",
          height: "100%",
        }}
      >
        <path
          d={`M ${x1} ${y1} L ${x2} ${y2}`}
          stroke="#666"
          strokeWidth="2"
          fill="none"
          markerEnd="url(#arrowhead)"
        />
      </svg>
    );
  };

  return (
    <div className="bg-white rounded-lg shadow overflow-hidden">
      <div className="p-4 border-b">
        <h3 className="text-lg font-medium text-gray-900">ガントチャート</h3>
      </div>

      <div className="relative overflow-auto" ref={chartRef}>
        <div style={{ width: totalDays * cellWidth + 300, minHeight: 400 }}>
          {/* 月ヘッダー */}
          <div className="sticky top-0 z-20 bg-white border-b">
            <div className="flex">
              <div className="w-[300px] border-r px-4 py-2 font-medium">
                タスク名
              </div>
              <div className="flex">
                {monthHeaders.map((month, index) => (
                  <div
                    key={index}
                    className="border-r text-center py-2 text-sm font-medium"
                    style={{ width: month.days * cellWidth }}
                  >
                    {month.month}
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* 日付ヘッダー */}
          <div className="sticky top-[40px] z-20 bg-white border-b">
            <div className="flex">
              <div className="w-[300px] border-r"></div>
              <div className="flex">
                {dateRange.map((date, index) => (
                  <div
                    key={index}
                    className="border-r text-center py-1 text-xs"
                    style={{ width: cellWidth }}
                  >
                    {date.getDate()}
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* タスク一覧とチャート */}
          <div className="relative" style={{ marginTop: headerHeight }}>
            {/* グリッド背景 */}
            <div className="absolute inset-0">
              {dateRange.map((date, index) => (
                <div
                  key={index}
                  className={`absolute top-0 bottom-0 border-r ${
                    date.getDay() === 0 || date.getDay() === 6
                      ? "bg-gray-50"
                      : "bg-white"
                  }`}
                  style={{
                    left: 300 + index * cellWidth,
                    width: cellWidth,
                  }}
                />
              ))}
            </div>

            {/* タスク */}
            {tasks.map((task) => {
              const position = calculateTaskPosition(task);
              const taskColor = getTaskColor(task);

              return (
                <div
                  key={task.id}
                  className="absolute flex items-center"
                  style={{
                    top: position.top,
                    height: rowHeight,
                  }}
                >
                  {/* タスク名 */}
                  <div
                    className="w-[300px] px-4 truncate cursor-pointer hover:text-blue-600"
                    style={{ paddingLeft: task.level * 20 + 16 }}
                    onClick={() => onTaskClick?.(task.id)}
                  >
                    {task.name}
                  </div>

                  {/* タスクバー */}
                  <div
                    className={`absolute h-6 rounded cursor-move ${taskColor} opacity-80 hover:opacity-100`}
                    style={{
                      left: 300 + position.left,
                      width: position.width,
                      top: (rowHeight - 24) / 2,
                    }}
                    title={`${task.name} (${task.progress}%完了)`}
                  >
                    {task.progress > 0 && (
                      <div
                        className="h-full bg-green-600 rounded-l"
                        style={{ width: `${task.progress}%` }}
                      />
                    )}
                  </div>

                  {/* リソース表示 */}
                  {task.resources.length > 0 && (
                    <div
                      className="absolute text-xs text-gray-600 truncate"
                      style={{
                        left: 300 + position.left + position.width + 4,
                        top: (rowHeight - 16) / 2,
                      }}
                    >
                      {task.resources.join(", ")}
                    </div>
                  )}
                </div>
              );
            })}

            {/* 依存関係の矢印 */}
            <svg className="absolute inset-0 pointer-events-none">
              <defs>
                <marker
                  id="arrowhead"
                  markerWidth="10"
                  markerHeight="7"
                  refX="9"
                  refY="3.5"
                  orient="auto"
                >
                  <polygon points="0 0, 10 3.5, 0 7" fill="#666" />
                </marker>
              </defs>
            </svg>
            {dependencies.map((dep) => renderDependencyLine(dep))}
          </div>
        </div>
      </div>

      {/* 凡例 */}
      <div className="p-4 border-t bg-gray-50">
        <div className="flex items-center space-x-6 text-sm">
          <div className="flex items-center space-x-2">
            <div className="w-4 h-4 bg-red-500 rounded"></div>
            <span>クリティカルパス</span>
          </div>
          <div className="flex items-center space-x-2">
            <div className="w-4 h-4 bg-purple-500 rounded"></div>
            <span>マイルストーン</span>
          </div>
          <div className="flex items-center space-x-2">
            <div className="w-4 h-4 bg-green-500 rounded"></div>
            <span>完了</span>
          </div>
          <div className="flex items-center space-x-2">
            <div className="w-4 h-4 bg-blue-500 rounded"></div>
            <span>進行中</span>
          </div>
          <div className="flex items-center space-x-2">
            <div className="w-4 h-4 bg-gray-400 rounded"></div>
            <span>未着手</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default GanttChart;
