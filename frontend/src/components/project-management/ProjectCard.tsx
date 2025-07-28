/**
 * プロジェクトカードコンポーネント
 */

import React from 'react';
import { Link } from 'react-router-dom';
import { Project } from '../../services/projectManagement';

interface ProjectCardProps {
  project: Project;
  onEdit?: (project: Project) => void;
  onDelete?: (project: Project) => void;
}

export const ProjectCard: React.FC<ProjectCardProps> = ({ project, onEdit, onDelete }) => {
  const getStatusColor = (status: string): string => {
    const colors = {
      planning: 'bg-gray-100 text-gray-800',
      active: 'bg-green-100 text-green-800',
      completed: 'bg-blue-100 text-blue-800',
      suspended: 'bg-yellow-100 text-yellow-800',
    };
    return colors[status as keyof typeof colors] || 'bg-gray-100 text-gray-800';
  };

  const getProgressColor = (percentage: number): string => {
    if (percentage >= 80) return 'bg-green-500';
    if (percentage >= 50) return 'bg-yellow-500';
    return 'bg-red-500';
  };

  const formatDate = (dateString: string): string => {
    return new Date(dateString).toLocaleDateString('ja-JP');
  };

  const formatBudget = (amount: number): string => {
    return new Intl.NumberFormat('ja-JP', {
      style: 'currency',
      currency: 'JPY',
    }).format(amount);
  };

  return (
    <div className="bg-white rounded-lg shadow-md hover:shadow-lg transition-shadow p-6">
      <div className="flex justify-between items-start mb-4">
        <div>
          <Link
            to={`/projects/${project.id}`}
            className="text-lg font-semibold text-gray-900 hover:text-blue-600"
          >
            {project.name}
          </Link>
          <p className="text-sm text-gray-500 mt-1">{project.code}</p>
        </div>
        <span className={`px-2 py-1 text-xs rounded-full ${getStatusColor(project.status)}`}>
          {project.status}
        </span>
      </div>

      {project.description && (
        <p className="text-gray-600 text-sm mb-4 line-clamp-2">{project.description}</p>
      )}

      <div className="space-y-3">
        <div className="flex justify-between text-sm">
          <span className="text-gray-500">期間:</span>
          <span className="text-gray-900">
            {formatDate(project.startDate)} - {formatDate(project.endDate)}
          </span>
        </div>

        <div className="flex justify-between text-sm">
          <span className="text-gray-500">予算:</span>
          <span className="text-gray-900">{formatBudget(project.budget)}</span>
        </div>

        {project.progressPercentage !== undefined && (
          <div>
            <div className="flex justify-between text-sm mb-1">
              <span className="text-gray-500">進捗:</span>
              <span className="text-gray-900">{project.progressPercentage}%</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className={`h-2 rounded-full ${getProgressColor(project.progressPercentage)}`}
                style={{ width: `${project.progressPercentage}%` }}
              />
            </div>
          </div>
        )}

        {project.parentProject && (
          <div className="flex justify-between text-sm">
            <span className="text-gray-500">親プロジェクト:</span>
            <Link
              to={`/projects/${project.parentProject.id}`}
              className="text-blue-600 hover:text-blue-800"
            >
              {project.parentProject.name}
            </Link>
          </div>
        )}

        {project.subProjects && project.subProjects.length > 0 && (
          <div className="text-sm">
            <span className="text-gray-500">サブプロジェクト:</span>
            <span className="text-gray-900 ml-2">{project.subProjects.length}件</span>
          </div>
        )}
      </div>

      {(onEdit || onDelete) && (
        <div className="flex justify-end space-x-2 mt-4 pt-4 border-t">
          {onEdit && (
            <button
              onClick={() => onEdit(project)}
              className="px-3 py-1 text-sm text-blue-600 hover:text-blue-800 hover:bg-blue-50 rounded"
            >
              編集
            </button>
          )}
          {onDelete && (
            <button
              onClick={() => onDelete(project)}
              className="px-3 py-1 text-sm text-red-600 hover:text-red-800 hover:bg-red-50 rounded"
            >
              削除
            </button>
          )}
        </div>
      )}
    </div>
  );
};

export default ProjectCard;