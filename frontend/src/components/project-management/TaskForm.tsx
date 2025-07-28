/**
 * タスク作成・編集フォームコンポーネント
 */

import React, { useEffect } from "react";
import { useForm } from "react-hook-form";
import { yupResolver } from "@hookform/resolvers/yup";
import * as yup from "yup";
import { Task, TaskCreate, TaskUpdate } from "../../services/projectManagement";

const createSchema = yup.object({
  name: yup.string().required("タスク名は必須です"),
  description: yup.string().nullable(),
  parentTaskId: yup.number().nullable(),
  startDate: yup.date().required("開始日は必須です"),
  endDate: yup
    .date()
    .required("終了日は必須です")
    .min(yup.ref("startDate"), "終了日は開始日より後に設定してください"),
  estimatedHours: yup
    .number()
    .min(0, "見積時間は0以上で入力してください")
    .nullable(),
  priority: yup.string().oneOf(["high", "medium", "low"]),
});

const updateSchema = yup.object({
  name: yup.string(),
  description: yup.string().nullable(),
  startDate: yup.date(),
  endDate: yup.date().when("startDate", (startDate, schema) => {
    if (startDate) {
      return schema.min(startDate, "終了日は開始日より後に設定してください");
    }
    return schema;
  }),
  estimatedHours: yup
    .number()
    .min(0, "見積時間は0以上で入力してください")
    .nullable(),
  actualHours: yup
    .number()
    .min(0, "実績時間は0以上で入力してください")
    .nullable(),
  priority: yup.string().oneOf(["high", "medium", "low"]),
  status: yup
    .string()
    .oneOf(["not_started", "in_progress", "completed", "on_hold"]),
  progressPercentage: yup
    .number()
    .min(0)
    .max(100, "進捗率は0〜100で入力してください"),
});

interface TaskFormProps {
  task?: Task;
  parentTask?: Task;
  onSubmit: (data: TaskCreate | TaskUpdate) => Promise<void>;
  onCancel: () => void;
  isLoading?: boolean;
}

export const TaskForm: React.FC<TaskFormProps> = ({
  task,
  parentTask,
  onSubmit,
  onCancel,
  isLoading = false,
}) => {
  const isEdit = !!task;
  const schema = isEdit ? updateSchema : createSchema;

  const {
    register,
    handleSubmit,
    formState: { errors },
    reset,
    watch,
  } = useForm({
    resolver: yupResolver(schema),
    defaultValues: task
      ? {
          name: task.name,
          description: task.description,
          startDate: task.startDate,
          endDate: task.endDate,
          estimatedHours: task.estimatedHours,
          actualHours: task.actualHours,
          priority: task.priority,
          status: task.status,
          progressPercentage: task.progressPercentage,
        }
      : {
          priority: "medium",
          parentTaskId: parentTask?.id,
        },
  });

  const watchStatus = watch("status");
  const watchProgress = watch("progressPercentage");

  useEffect(() => {
    if (task) {
      reset({
        name: task.name,
        description: task.description,
        startDate: task.startDate,
        endDate: task.endDate,
        estimatedHours: task.estimatedHours,
        actualHours: task.actualHours,
        priority: task.priority,
        status: task.status,
        progressPercentage: task.progressPercentage,
      });
    }
  }, [task, reset]);

  // ステータスと進捗率の連動
  useEffect(() => {
    if (isEdit) {
      if (watchProgress === 100 && watchStatus !== "completed") {
        reset({ ...watch(), status: "completed" });
      } else if (watchProgress === 0 && watchStatus !== "not_started") {
        reset({ ...watch(), status: "not_started" });
      } else if (
        watchProgress > 0 &&
        watchProgress < 100 &&
        watchStatus === "not_started"
      ) {
        reset({ ...watch(), status: "in_progress" });
      }
    }
  }, [watchProgress, watchStatus, isEdit, reset, watch]);

  const formatDateForInput = (dateString?: string): string => {
    if (!dateString) return "";
    return dateString.split("T")[0];
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
      {parentTask && (
        <div className="bg-gray-50 p-3 rounded">
          <p className="text-sm text-gray-600">
            親タスク: <span className="font-medium">{parentTask.name}</span>
          </p>
        </div>
      )}

      <div>
        <label
          htmlFor="name"
          className="block text-sm font-medium text-gray-700"
        >
          タスク名 <span className="text-red-500">*</span>
        </label>
        <input
          type="text"
          id="name"
          {...register("name")}
          className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
          placeholder="タスク名を入力"
        />
        {errors.name && (
          <p className="mt-1 text-sm text-red-600">{errors.name.message}</p>
        )}
      </div>

      <div>
        <label
          htmlFor="description"
          className="block text-sm font-medium text-gray-700"
        >
          説明
        </label>
        <textarea
          id="description"
          {...register("description")}
          rows={3}
          className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
          placeholder="タスクの詳細を入力してください"
        />
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <label
            htmlFor="startDate"
            className="block text-sm font-medium text-gray-700"
          >
            開始日 <span className="text-red-500">*</span>
          </label>
          <input
            type="date"
            id="startDate"
            {...register("startDate")}
            defaultValue={formatDateForInput(task?.startDate)}
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
          />
          {errors.startDate && (
            <p className="mt-1 text-sm text-red-600">
              {errors.startDate.message}
            </p>
          )}
        </div>

        <div>
          <label
            htmlFor="endDate"
            className="block text-sm font-medium text-gray-700"
          >
            終了日 <span className="text-red-500">*</span>
          </label>
          <input
            type="date"
            id="endDate"
            {...register("endDate")}
            defaultValue={formatDateForInput(task?.endDate)}
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
          />
          {errors.endDate && (
            <p className="mt-1 text-sm text-red-600">
              {errors.endDate.message}
            </p>
          )}
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <label
            htmlFor="estimatedHours"
            className="block text-sm font-medium text-gray-700"
          >
            見積時間（時間）
          </label>
          <input
            type="number"
            id="estimatedHours"
            {...register("estimatedHours", { valueAsNumber: true })}
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
            placeholder="40"
          />
          {errors.estimatedHours && (
            <p className="mt-1 text-sm text-red-600">
              {errors.estimatedHours.message}
            </p>
          )}
        </div>

        {isEdit && (
          <div>
            <label
              htmlFor="actualHours"
              className="block text-sm font-medium text-gray-700"
            >
              実績時間（時間）
            </label>
            <input
              type="number"
              id="actualHours"
              {...register("actualHours", { valueAsNumber: true })}
              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
              placeholder="0"
            />
            {errors.actualHours && (
              <p className="mt-1 text-sm text-red-600">
                {errors.actualHours.message}
              </p>
            )}
          </div>
        )}
      </div>

      <div>
        <label
          htmlFor="priority"
          className="block text-sm font-medium text-gray-700"
        >
          優先度
        </label>
        <select
          id="priority"
          {...register("priority")}
          className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
        >
          <option value="high">高</option>
          <option value="medium">中</option>
          <option value="low">低</option>
        </select>
      </div>

      {isEdit && (
        <>
          <div>
            <label
              htmlFor="status"
              className="block text-sm font-medium text-gray-700"
            >
              ステータス
            </label>
            <select
              id="status"
              {...register("status")}
              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
            >
              <option value="not_started">未着手</option>
              <option value="in_progress">進行中</option>
              <option value="completed">完了</option>
              <option value="on_hold">保留</option>
            </select>
          </div>

          <div>
            <label
              htmlFor="progressPercentage"
              className="block text-sm font-medium text-gray-700"
            >
              進捗率（%）
            </label>
            <input
              type="number"
              id="progressPercentage"
              {...register("progressPercentage", { valueAsNumber: true })}
              min="0"
              max="100"
              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
              placeholder="0"
            />
            {errors.progressPercentage && (
              <p className="mt-1 text-sm text-red-600">
                {errors.progressPercentage.message}
              </p>
            )}
          </div>
        </>
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
          {isLoading ? "処理中..." : isEdit ? "更新" : "作成"}
        </button>
      </div>
    </form>
  );
};

export default TaskForm;
