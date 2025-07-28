/**
 * プロジェクト詳細ページ
 */

import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Project,
  Task,
  TaskCreate,
  TaskUpdate,
  ProjectMember,
  Budget,
  ProgressReport,
  GanttData,
} from '../../services/projectManagement';
import { projectManagementService } from '../../services/projectManagementExtended';
import { ProjectDashboard } from '../../components/project-management/ProjectDashboard';
import { TaskTree } from '../../components/project-management/TaskTree';
import { TaskForm } from '../../components/project-management/TaskForm';
import { GanttChart } from '../../components/project-management/GanttChart';
import { ProjectMemberList } from '../../components/project-management/ProjectMemberList';
import { BudgetManager } from '../../components/project-management/BudgetManager';
import {
  ArrowLeftIcon,
  PencilIcon,
  DocumentDuplicateIcon,
  ArrowPathIcon,
} from '@heroicons/react/24/outline';

interface TabItem {
  id: string;
  name: string;
  count?: number;
}

export const ProjectDetailPage: React.FC = () => {
  const { projectId } = useParams<{ projectId: string }>();
  const navigate = useNavigate();

  const [project, setProject] = useState<Project | null>(null);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [members, setMembers] = useState<ProjectMember[]>([]);
  const [budget, setBudget] = useState<Budget | null>(null);
  const [progressReport, setProgressReport] = useState<ProgressReport | null>(null);
  const [ganttData, setGanttData] = useState<GanttData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState('dashboard');
  const [showTaskForm, setShowTaskForm] = useState(false);
  const [editingTask, setEditingTask] = useState<Task | null>(null);
  const [parentTask, setParentTask] = useState<Task | null>(null);

  const tabs: TabItem[] = [
    { id: 'dashboard', name: 'ダッシュボード' },
    { id: 'tasks', name: 'タスク', count: tasks.length },
    { id: 'gantt', name: 'ガントチャート' },
    { id: 'members', name: 'メンバー', count: members.length },
    { id: 'budget', name: '予算管理' },
  ];

  const fetchProjectData = async () => {
    if (!projectId) return;

    try {
      setLoading(true);
      setError(null);

      // プロジェクト詳細を取得
      const projectData = await projectManagementService.projects.get(parseInt(projectId));
      setProject(projectData);

      // 関連データを並行して取得
      const [tasksData, membersData, budgetData, progressData] = await Promise.all([
        projectManagementService.tasks.list({ projectId: parseInt(projectId) }),
        projectManagementService.members.list({ projectId: parseInt(projectId) }),
        projectManagementService.budgets.getByProject(parseInt(projectId)),
        projectManagementService.projects.getProgress(parseInt(projectId)),
      ]);

      setTasks(tasksData.items);
      setMembers(membersData.items);
      setBudget(budgetData);
      setProgressReport(progressData);

      // ガントチャートデータを取得（タスクタブまたはガントタブが選択されている場合のみ）
      if (activeTab === 'gantt' || activeTab === 'tasks') {
        const gantt = await projectManagementService.projects.getGanttData(parseInt(projectId));
        setGanttData(gantt);
      }
    } catch (err) {
      setError('プロジェクトデータの取得に失敗しました');
      // console.error('Failed to fetch project data:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProjectData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [projectId, activeTab]);

  const handleTaskCreate = async (data: TaskCreate) => {
    if (!projectId) return;

    try {
      await projectManagementService.tasks.create({
        ...data,
        projectId: parseInt(projectId),
      });
      setShowTaskForm(false);
      setParentTask(null);
      fetchProjectData();
    } catch (err) {
      // console.error('Failed to create task:', err);
      alert('タスクの作成に失敗しました');
    }
  };

  const handleTaskUpdate = async (data: TaskUpdate) => {
    if (!editingTask) return;

    try {
      await projectManagementService.tasks.update(editingTask.id, data);
      setEditingTask(null);
      setShowTaskForm(false);
      fetchProjectData();
    } catch (err) {
      // console.error('Failed to update task:', err);
      alert('タスクの更新に失敗しました');
    }
  };

  const handleTaskDelete = async (task: Task) => {
    if (!window.confirm(`タスク「${task.name}」を削除してもよろしいですか？`)) {
      return;
    }

    try {
      await projectManagementService.tasks.delete(task.id);
      fetchProjectData();
    } catch (err) {
      // console.error('Failed to delete task:', err);
      alert('タスクの削除に失敗しました');
    }
  };

  const handleAddSubTask = (parent: Task) => {
    setParentTask(parent);
    setEditingTask(null);
    setShowTaskForm(true);
  };

  const handleEditTask = (task: Task) => {
    setEditingTask(task);
    setParentTask(null);
    setShowTaskForm(true);
  };

  const handleCloneProject = async () => {
    if (!project || !window.confirm('このプロジェクトを複製してもよろしいですか？')) {
      return;
    }

    try {
      const clonedProject = await projectManagementService.projects.clone(project.id);
      navigate(`/projects/${clonedProject.id}`);
    } catch (err) {
      // console.error('Failed to clone project:', err);
      alert('プロジェクトの複製に失敗しました');
    }
  };

  const handleAutoSchedule = async () => {
    if (!projectId || !window.confirm('タスクの自動スケジューリングを実行してもよろしいですか？')) {
      return;
    }

    try {
      await projectManagementService.projects.autoSchedule(parseInt(projectId));
      fetchProjectData();
      alert('自動スケジューリングが完了しました');
    } catch (err) {
      // console.error('Failed to auto-schedule:', err);
      alert('自動スケジューリングに失敗しました');
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
      </div>
    );
  }

  if (error || !project) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="bg-red-50 p-4 rounded-lg">
          <p className="text-red-600">{error || 'プロジェクトが見つかりません'}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8">
      {/* ヘッダー */}
      <div className="mb-8">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-4">
            <button
              onClick={() => navigate('/projects')}
              className="p-2 hover:bg-gray-100 rounded-md"
            >
              <ArrowLeftIcon className="h-5 w-5" />
            </button>
            <div>
              <h1 className="text-2xl font-bold text-gray-900">{project.name}</h1>
              <p className="text-sm text-gray-500">{project.code}</p>
            </div>
          </div>
          <div className="flex items-center space-x-2">
            <button
              onClick={() => navigate(`/projects/${project.id}/edit`)}
              className="p-2 hover:bg-gray-100 rounded-md"
              title="編集"
            >
              <PencilIcon className="h-5 w-5" />
            </button>
            <button
              onClick={handleCloneProject}
              className="p-2 hover:bg-gray-100 rounded-md"
              title="複製"
            >
              <DocumentDuplicateIcon className="h-5 w-5" />
            </button>
            {activeTab === 'tasks' && (
              <button
                onClick={handleAutoSchedule}
                className="p-2 hover:bg-gray-100 rounded-md"
                title="自動スケジューリング"
              >
                <ArrowPathIcon className="h-5 w-5" />
              </button>
            )}
          </div>
        </div>

        {/* タブ */}
        <div className="border-b border-gray-200">
          <nav className="-mb-px flex space-x-8">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`
                  py-2 px-1 border-b-2 font-medium text-sm
                  ${
                    activeTab === tab.id
                      ? 'border-indigo-500 text-indigo-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }
                `}
              >
                {tab.name}
                {tab.count !== undefined && (
                  <span className="ml-2 px-2 py-0.5 text-xs rounded-full bg-gray-100 text-gray-600">
                    {tab.count}
                  </span>
                )}
              </button>
            ))}
          </nav>
        </div>
      </div>

      {/* タブコンテンツ */}
      <div className="mt-6">
        {activeTab === 'dashboard' && (
          <ProjectDashboard
            project={project}
            progressReport={progressReport}
            budget={budget}
          />
        )}

        {activeTab === 'tasks' && (
          <div className="space-y-6">
            <div className="flex justify-between items-center">
              <h2 className="text-lg font-medium text-gray-900">タスク管理</h2>
              <button
                onClick={() => {
                  setEditingTask(null);
                  setParentTask(null);
                  setShowTaskForm(true);
                }}
                className="px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700"
              >
                タスクを追加
              </button>
            </div>

            <TaskTree
              tasks={tasks}
              onTaskClick={() => {}}
              onTaskEdit={handleEditTask}
              onTaskDelete={handleTaskDelete}
              onAddSubTask={handleAddSubTask}
            />
          </div>
        )}

        {activeTab === 'gantt' && ganttData && (
          <div className="space-y-6">
            <h2 className="text-lg font-medium text-gray-900">ガントチャート</h2>
            <GanttChart
              tasks={ganttData.tasks}
              dependencies={ganttData.dependencies}
              criticalPath={ganttData.criticalPath}
              startDate={project.startDate}
              endDate={project.endDate}
              onTaskClick={(taskId) => {
                const task = tasks.find((t) => t.id === taskId);
                if (task) handleEditTask(task);
              }}
            />
          </div>
        )}

        {activeTab === 'members' && (
          <div className="space-y-6">
            <h2 className="text-lg font-medium text-gray-900">プロジェクトメンバー</h2>
            <ProjectMemberList
              projectId={project.id}
              members={members}
              onUpdate={() => fetchProjectData()}
            />
          </div>
        )}

        {activeTab === 'budget' && (
          <div className="space-y-6">
            <h2 className="text-lg font-medium text-gray-900">予算管理</h2>
            <BudgetManager
              projectId={project.id}
              budget={budget}
              onUpdate={() => fetchProjectData()}
            />
          </div>
        )}
      </div>

      {/* タスクフォームモーダル */}
      {showTaskForm && (
        <div className="fixed inset-0 bg-gray-500 bg-opacity-75 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6">
              <h2 className="text-lg font-medium text-gray-900 mb-4">
                {editingTask ? 'タスクを編集' : 'タスクを追加'}
              </h2>
              <TaskForm
                task={editingTask || undefined}
                parentTask={parentTask || undefined}
                onSubmit={editingTask ? handleTaskUpdate : handleTaskCreate}
                onCancel={() => {
                  setShowTaskForm(false);
                  setEditingTask(null);
                  setParentTask(null);
                }}
              />
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ProjectDetailPage;