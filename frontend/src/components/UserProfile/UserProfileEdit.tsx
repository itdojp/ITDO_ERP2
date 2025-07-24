/**
 * User Profile Edit Component
 * Form for editing user profile information
 */

import React, { useEffect } from "react";
import { useForm } from "react-hook-form";
import { Save, X, Upload, Trash2 } from "lucide-react";
import {
  useUpdateProfile,
  useUploadProfileImage,
  useDeleteProfileImage,
} from "../../hooks/useUserProfile";
import type { UserProfileUpdate } from "../../types/user";

interface UserProfileEditProps {
  userId: number;
  initialData?: {
    full_name: string;
    phone?: string;
    bio?: string;
    location?: string;
    website?: string;
    profile_image_url?: string;
  };
  onSave?: () => void;
  onCancel?: () => void;
}

export const UserProfileEdit: React.FC<UserProfileEditProps> = ({
  userId,
  initialData,
  onSave,
  onCancel,
}) => {
  const {
    register,
    handleSubmit,
    formState: { errors, isDirty },
    reset,
    watch,
  } = useForm<UserProfileUpdate>({
    defaultValues: initialData,
  });

  const updateProfileMutation = useUpdateProfile();
  const uploadImageMutation = useUploadProfileImage();
  const deleteImageMutation = useDeleteProfileImage();

  const [selectedFile, setSelectedFile] = React.useState<File | null>(null);
  const [imagePreview, setImagePreview] = React.useState<string | null>(
    initialData?.profile_image_url || null,
  );

  useEffect(() => {
    if (initialData) {
      reset(initialData);
      setImagePreview(initialData.profile_image_url || null);
    }
  }, [initialData, reset]);

  const onSubmit = async (data: UserProfileUpdate) => {
    try {
      // Upload image first if selected
      if (selectedFile) {
        await uploadImageMutation.mutateAsync({ userId, file: selectedFile });
      }

      // Update profile data
      await updateProfileMutation.mutateAsync({ userId, data });

      onSave?.();
    } catch (error) {
      // Error is handled by mutation state
    }
  };

  const handleImageSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      setSelectedFile(file);

      // Create preview
      const reader = new FileReader();
      reader.onload = (e) => {
        setImagePreview(e.target?.result as string);
      };
      reader.readAsDataURL(file);
    }
  };

  const handleDeleteImage = async () => {
    try {
      await deleteImageMutation.mutateAsync(userId);
      setImagePreview(null);
      setSelectedFile(null);
    } catch (error) {
      // Error is handled by mutation state
    }
  };

  const isLoading =
    updateProfileMutation.isPending ||
    uploadImageMutation.isPending ||
    deleteImageMutation.isPending;

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200">
      {/* Header */}
      <div className="px-6 py-4 border-b border-gray-200">
        <h2 className="text-xl font-semibold text-gray-900">
          プロフィール編集
        </h2>
      </div>

      <form onSubmit={handleSubmit(onSubmit)} className="p-6">
        {/* Profile Image Section */}
        <div className="mb-6">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            プロフィール画像
          </label>
          <div className="flex items-center space-x-4">
            {imagePreview ? (
              <img
                src={imagePreview}
                alt="Profile preview"
                className="w-20 h-20 rounded-full object-cover"
              />
            ) : (
              <div className="w-20 h-20 rounded-full bg-gray-200 flex items-center justify-center">
                <span className="text-gray-400 text-sm">画像なし</span>
              </div>
            )}

            <div className="flex space-x-2">
              <label className="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 cursor-pointer">
                <Upload className="w-4 h-4 mr-2" />
                選択
                <input
                  type="file"
                  accept="image/*"
                  onChange={handleImageSelect}
                  className="hidden"
                />
              </label>

              {imagePreview && (
                <button
                  type="button"
                  onClick={handleDeleteImage}
                  className="inline-flex items-center px-3 py-2 border border-red-300 shadow-sm text-sm leading-4 font-medium rounded-md text-red-700 bg-white hover:bg-red-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500"
                >
                  <Trash2 className="w-4 h-4 mr-2" />
                  削除
                </button>
              )}
            </div>
          </div>
          <p className="mt-2 text-sm text-gray-500">
            JPG, PNG形式で、最大5MBまでアップロードできます。
          </p>
        </div>

        {/* Form Fields */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Full Name */}
          <div className="md:col-span-2">
            <label
              htmlFor="full_name"
              className="block text-sm font-medium text-gray-700 mb-1"
            >
              氏名 <span className="text-red-500">*</span>
            </label>
            <input
              id="full_name"
              type="text"
              {...register("full_name", {
                required: "氏名は必須です",
                minLength: { value: 1, message: "氏名を入力してください" },
              })}
              className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
            />
            {errors.full_name && (
              <p className="mt-1 text-sm text-red-600">
                {errors.full_name.message}
              </p>
            )}
          </div>

          {/* Phone */}
          <div>
            <label
              htmlFor="phone"
              className="block text-sm font-medium text-gray-700 mb-1"
            >
              電話番号
            </label>
            <input
              id="phone"
              type="tel"
              {...register("phone")}
              className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
              placeholder="090-1234-5678"
            />
          </div>

          {/* Location */}
          <div>
            <label
              htmlFor="location"
              className="block text-sm font-medium text-gray-700 mb-1"
            >
              所在地
            </label>
            <input
              id="location"
              type="text"
              {...register("location")}
              className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
              placeholder="東京都渋谷区"
            />
          </div>

          {/* Website */}
          <div className="md:col-span-2">
            <label
              htmlFor="website"
              className="block text-sm font-medium text-gray-700 mb-1"
            >
              ウェブサイト
            </label>
            <input
              id="website"
              type="url"
              {...register("website", {
                pattern: {
                  value: /^https?:\/\/.+/,
                  message:
                    "有効なURLを入力してください (http:// または https:// で始まる)",
                },
              })}
              className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
              placeholder="https://example.com"
            />
            {errors.website && (
              <p className="mt-1 text-sm text-red-600">
                {errors.website.message}
              </p>
            )}
          </div>

          {/* Bio */}
          <div className="md:col-span-2">
            <label
              htmlFor="bio"
              className="block text-sm font-medium text-gray-700 mb-1"
            >
              自己紹介
            </label>
            <textarea
              id="bio"
              rows={4}
              {...register("bio", {
                maxLength: {
                  value: 500,
                  message: "自己紹介は500文字以内で入力してください",
                },
              })}
              className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
              placeholder="自己紹介を入力してください..."
            />
            {errors.bio && (
              <p className="mt-1 text-sm text-red-600">{errors.bio.message}</p>
            )}
            <p className="mt-1 text-sm text-gray-500">
              {watch("bio")?.length || 0}/500文字
            </p>
          </div>
        </div>

        {/* Error Display */}
        {(updateProfileMutation.isError ||
          uploadImageMutation.isError ||
          deleteImageMutation.isError) && (
          <div className="mt-6 p-4 bg-red-50 border border-red-200 rounded-md">
            <p className="text-red-600 text-sm">
              エラーが発生しました。もう一度お試しください。
            </p>
          </div>
        )}

        {/* Action Buttons */}
        <div className="mt-6 flex items-center justify-end space-x-3">
          <button
            type="button"
            onClick={onCancel}
            className="inline-flex items-center px-4 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
          >
            <X className="w-4 h-4 mr-2" />
            キャンセル
          </button>

          <button
            type="submit"
            disabled={isLoading || !isDirty}
            className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isLoading ? (
              <>
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                保存中...
              </>
            ) : (
              <>
                <Save className="w-4 h-4 mr-2" />
                保存
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  );
};
