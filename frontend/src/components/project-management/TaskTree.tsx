/**
 * タスクツリーコンポーネント（WBS表示）
 */

import React, { useState } from 'react';
import { Task } from '../../services/projectManagement';
import { ChevronRightIcon, ChevronDownIcon } from '@heroicons/react/24/outline';

interface TaskTreeProps {
  tasks: Task[];
  onTaskClick?: (task: Task) => void;
  onTaskEdit?: (task: Task) => void;
  onTaskDelete?: (task: Task) => void;
  onAddSubTask?: (parentTask: Task) => void;
  selectedTaskId?: number;
}

interface TaskNodeProps {
  task: Task;
  level: number;
  onTaskClick?: (task: Task) => void;
  onTaskEdit?: (task: Task) => void;
  onTaskDelete?: (task: Task) => void;
  onAddSubTask?: (parentTask: Task) => void;
  isSelected?: boolean;
}

const TaskNode: React.FC<TaskNodeProps> = ({
  task,
  level,
  onTaskClick,
  onTaskEdit,
  onTaskDelete,
  onAddSubTask,
  isSelected,
}) => {
  const [isExpanded, setIsExpanded] = useState(true);
  const hasSubTasks = task.subTasks && task.subTasks.length > 0;

  const getStatusColor = (status: string): string => {
    const colors = {
      not_started: 'bg-gray-100 text-gray-800',
      in_progress: 'bg-blue-100 text-blue-800',
      completed: 'bg-green-100 text-green-800',
      on_hold: 'bg-yellow-100 text-yellow-800',
    };
    return colors[status as keyof typeof colors] || 'bg-gray-100 text-gray-800';
  };

  const getPriorityColor = (priority: string): string => {
    const colors = {
      high: 'text-red-600',
      medium: 'text-yellow-600',
      low: 'text-gray-600',
    };
    return colors[priority as keyof typeof colors] || 'text-gray-600';
  };

  const formatDate = (dateString: string): string => {
    return new Date(dateString).toLocaleDateString('ja-JP');
  };

  return (
    <>
      <div
        className={`
          flex items-center p-3 hover:bg-gray-50 cursor-pointer
          ${isSelected ? 'bg-blue-50' : ''}
          ${level > 0 ? 'border-l-2 border-gray-200' : ''}
        `}
        style={{ paddingLeft: `${level * 24 + 12}px` }}
        onClick={() => onTaskClick?.(task)}
      >
        <div className="flex items-center flex-1">
          {hasSubTasks && (
            <button
              onClick={(e) => {
                e.stopPropagation();
                setIsExpanded(!isExpanded);
              }}
              className="p-1 hover:bg-gray-200 rounded mr-2"
            >
              {isExpanded ? (
                <ChevronDownIcon className="h-4 w-4" />
              ) : (
                <ChevronRightIcon className="h-4 w-4" />
              )}
            </button>
          )}
          {!hasSubTasks && <div className="w-6 mr-2" />}

          <div className="flex-1">
            <div className="flex items-center space-x-3">
              <h4 className="font-medium text-gray-900">{task.name}</h4>
              <span className={`text-xs font-medium ${getPriorityColor(task.priority)}`}>
                {task.priority === 'high' ? '高' : task.priority === 'medium' ? '中' : '低'}
              </span>
              <span className={`px-2 py-1 text-xs rounded-full ${getStatusColor(task.status)}`}>
                {task.status === 'not_started'
                  ? '未着手'
                  : task.status === 'in_progress'
                  ? '進行中'
                  : task.status === 'completed'
                  ? '完了'
                  : '保留'}
              </span>
            </div>
            <div className="flex items-center space-x-4 mt-1 text-sm text-gray-500">
              <span>{formatDate(task.startDate)} - {formatDate(task.endDate)}</span>
              {task.estimatedHours && <span>{task.estimatedHours}時間</span>}
              <span>{task.progressPercentage}%完了</span>
            </div>
          </div>

          <div className="flex items-center space-x-2">
            {task.progressPercentage > 0 && (
              <div className="w-24 bg-gray-200 rounded-full h-2">
                <div
                  className={`h-2 rounded-full ${
                    task.progressPercentage >= 100
                      ? 'bg-green-500'
                      : task.progressPercentage >= 50
                      ? 'bg-yellow-500'
                      : 'bg-red-500'
                  }`}
                  style={{ width: `${task.progressPercentage}%` }}
                />
              </div>
            )}

            <div className="flex space-x-1 opacity-0 group-hover:opacity-100 transition-opacity">
              {onAddSubTask && (
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    onAddSubTask(task);
                  }}
                  className="p-1 text-gray-400 hover:text-gray-600"
                  title="サブタスクを追加"
                >
                  <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                  </svg>
                </button>
              )}
              {onTaskEdit && (
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    onTaskEdit(task);
                  }}
                  className="p-1 text-gray-400 hover:text-gray-600"
                  title="編集"
                >
                  <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                  </svg>
                </button>
              )}
              {onTaskDelete && (
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    onTaskDelete(task);
                  }}
                  className="p-1 text-gray-400 hover:text-red-600"
                  title="削除"
                >
                  <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                  </svg>
                </button>
              )}
            </div>
          </div>
        </div>
      </div>

      {isExpanded && hasSubTasks && (
        <>
          {task.subTasks!.map((subTask) => (
            <TaskNode
              key={subTask.id}
              task={subTask}
              level={level + 1}
              onTaskClick={onTaskClick}
              onTaskEdit={onTaskEdit}
              onTaskDelete={onTaskDelete}
              onAddSubTask={onAddSubTask}
              isSelected={selectedTaskId === subTask.id}
            />
          ))}
        </>
      )}
    </>
  );
};

export const TaskTree: React.FC<TaskTreeProps> = ({
  tasks,
  onTaskClick,
  onTaskEdit,
  onTaskDelete,
  onAddSubTask,
  selectedTaskId,
}) => {
  return (
    <div className="bg-white rounded-lg shadow">
      <div className="px-4 py-3 border-b border-gray-200">
        <h3 className="text-lg font-medium text-gray-900">タスク一覧（WBS）</h3>
      </div>
      <div className="divide-y divide-gray-200">
        {tasks.length === 0 ? (
          <div className="p-8 text-center text-gray-500">
            タスクがありません
          </div>
        ) : (
          tasks.map((task) => (
            <div key={task.id} className="group">
              <TaskNode
                task={task}
                level={0}
                onTaskClick={onTaskClick}
                onTaskEdit={onTaskEdit}
                onTaskDelete={onTaskDelete}
                onAddSubTask={onAddSubTask}
                isSelected={selectedTaskId === task.id}
              />
            </div>
          ))
        )}
      </div>
    </div>
  );
};

export default TaskTree;