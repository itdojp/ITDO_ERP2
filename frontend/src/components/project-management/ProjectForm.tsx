/**
 * プロジェクト作成・編集フォームコンポーネント
 */

import React, { useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { yupResolver } from '@hookform/resolvers/yup';
import * as yup from 'yup';
import { Project, ProjectCreate, ProjectUpdate } from '../../services/projectManagement';

const createSchema = yup.object({
  code: yup.string().required('プロジェクトコードは必須です'),
  name: yup.string().required('プロジェクト名は必須です'),
  description: yup.string().nullable(),
  parentId: yup.number().nullable(),
  startDate: yup.date().required('開始日は必須です'),
  endDate: yup
    .date()
    .required('終了日は必須です')
    .min(yup.ref('startDate'), '終了日は開始日より後に設定してください'),
  budget: yup.number().min(0, '予算は0以上で入力してください').required('予算は必須です'),
  status: yup.string().oneOf(['planning', 'active', 'completed', 'suspended']),
  projectType: yup.string().oneOf(['standard', 'recurring']),
});

const updateSchema = yup.object({
  name: yup.string(),
  description: yup.string().nullable(),
  startDate: yup.date(),
  endDate: yup.date().when('startDate', (startDate, schema) => {
    if (startDate) {
      return schema.min(startDate, '終了日は開始日より後に設定してください');
    }
    return schema;
  }),
  budget: yup.number().min(0, '予算は0以上で入力してください'),
  status: yup.string().oneOf(['planning', 'active', 'completed', 'suspended']),
});

interface ProjectFormProps {
  project?: Project;
  projects?: Project[]; // For parent project selection
  onSubmit: (data: ProjectCreate | ProjectUpdate) => Promise<void>;
  onCancel: () => void;
  isLoading?: boolean;
}

export const ProjectForm: React.FC<ProjectFormProps> = ({
  project,
  projects = [],
  onSubmit,
  onCancel,
  isLoading = false,
}) => {
  const isEdit = !!project;
  const schema = isEdit ? updateSchema : createSchema;

  const {
    register,
    handleSubmit,
    formState: { errors },
    reset,
  } = useForm({
    resolver: yupResolver(schema),
    defaultValues: project
      ? {
          name: project.name,
          description: project.description,
          startDate: project.startDate,
          endDate: project.endDate,
          budget: project.budget,
          status: project.status,
        }
      : {
          status: 'planning',
          projectType: 'standard',
        },
  });

  useEffect(() => {
    if (project) {
      reset({
        name: project.name,
        description: project.description,
        startDate: project.startDate,
        endDate: project.endDate,
        budget: project.budget,
        status: project.status,
      });
    }
  }, [project, reset]);

  const formatDateForInput = (dateString?: string): string => {
    if (!dateString) return '';
    return dateString.split('T')[0];
  };

  const availableParentProjects = projects.filter(p => p.id !== project?.id);

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
      {!isEdit && (
        <div>
          <label htmlFor="code" className="block text-sm font-medium text-gray-700">
            プロジェクトコード <span className="text-red-500">*</span>
          </label>
          <input
            type="text"
            id="code"
            {...register('code')}
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
            placeholder="PROJ-001"
          />
          {errors.code && (
            <p className="mt-1 text-sm text-red-600">{errors.code.message}</p>
          )}
        </div>
      )}

      <div>
        <label htmlFor="name" className="block text-sm font-medium text-gray-700">
          プロジェクト名 <span className="text-red-500">*</span>
        </label>
        <input
          type="text"
          id="name"
          {...register('name')}
          className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
          placeholder="新規プロジェクト"
        />
        {errors.name && (
          <p className="mt-1 text-sm text-red-600">{errors.name.message}</p>
        )}
      </div>

      <div>
        <label htmlFor="description" className="block text-sm font-medium text-gray-700">
          説明
        </label>
        <textarea
          id="description"
          {...register('description')}
          rows={3}
          className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
          placeholder="プロジェクトの概要を入力してください"
        />
      </div>

      {!isEdit && availableParentProjects.length > 0 && (
        <div>
          <label htmlFor="parentId" className="block text-sm font-medium text-gray-700">
            親プロジェクト
          </label>
          <select
            id="parentId"
            {...register('parentId')}
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
          >
            <option value="">なし</option>
            {availableParentProjects.map((p) => (
              <option key={p.id} value={p.id}>
                {p.code} - {p.name}
              </option>
            ))}
          </select>
        </div>
      )}

      <div className="grid grid-cols-2 gap-4">
        <div>
          <label htmlFor="startDate" className="block text-sm font-medium text-gray-700">
            開始日 <span className="text-red-500">*</span>
          </label>
          <input
            type="date"
            id="startDate"
            {...register('startDate')}
            defaultValue={formatDateForInput(project?.startDate)}
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
          />
          {errors.startDate && (
            <p className="mt-1 text-sm text-red-600">{errors.startDate.message}</p>
          )}
        </div>

        <div>
          <label htmlFor="endDate" className="block text-sm font-medium text-gray-700">
            終了日 <span className="text-red-500">*</span>
          </label>
          <input
            type="date"
            id="endDate"
            {...register('endDate')}
            defaultValue={formatDateForInput(project?.endDate)}
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
          />
          {errors.endDate && (
            <p className="mt-1 text-sm text-red-600">{errors.endDate.message}</p>
          )}
        </div>
      </div>

      <div>
        <label htmlFor="budget" className="block text-sm font-medium text-gray-700">
          予算 (円) <span className="text-red-500">*</span>
        </label>
        <input
          type="number"
          id="budget"
          {...register('budget', { valueAsNumber: true })}
          className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
          placeholder="10000000"
        />
        {errors.budget && (
          <p className="mt-1 text-sm text-red-600">{errors.budget.message}</p>
        )}
      </div>

      <div>
        <label htmlFor="status" className="block text-sm font-medium text-gray-700">
          ステータス
        </label>
        <select
          id="status"
          {...register('status')}
          className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
        >
          <option value="planning">計画中</option>
          <option value="active">進行中</option>
          <option value="completed">完了</option>
          <option value="suspended">中断</option>
        </select>
      </div>

      {!isEdit && (
        <div>
          <label htmlFor="projectType" className="block text-sm font-medium text-gray-700">
            プロジェクトタイプ
          </label>
          <select
            id="projectType"
            {...register('projectType')}
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
          >
            <option value="standard">標準</option>
            <option value="recurring">繰り返し</option>
          </select>
        </div>
      )}

      <div className="flex justify-end space-x-3">
        <button
          type="button"
          onClick={onCancel}
          className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md shadow-sm hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
          disabled={isLoading}
        >
          キャンセル
        </button>
        <button
          type="submit"
          className="px-4 py-2 text-sm font-medium text-white bg-indigo-600 border border-transparent rounded-md shadow-sm hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed"
          disabled={isLoading}
        >
          {isLoading ? '処理中...' : isEdit ? '更新' : '作成'}
        </button>
      </div>
    </form>
  );
};

export default ProjectForm;