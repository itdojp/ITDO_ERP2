import React, { useState } from 'react';

interface UserFormProps {
  user?: {
    id: string;
    username: string;
    email: string;
    fullName: string;
    role: string;
    department: string;
    status: 'active' | 'inactive' | 'suspended';
    phone?: string;
    address?: string;
    emergencyContact?: string;
  };
  onSubmit: (userData: any) => void;
  onCancel: () => void;
  isEditing?: boolean;
}

export const UserForm: React.FC<UserFormProps> = ({ 
  user, 
  onSubmit, 
  onCancel, 
  isEditing = false 
}) => {
  const [formData, setFormData] = useState({
    username: user?.username || '',
    email: user?.email || '',
    fullName: user?.fullName || '',
    role: user?.role || '一般ユーザー',
    department: user?.department || '',
    status: user?.status || 'active',
    phone: user?.phone || '',
    address: user?.address || '',
    emergencyContact: user?.emergencyContact || '',
    password: '',
    confirmPassword: ''
  });

  const [errors, setErrors] = useState<Record<string, string>>({});

  const departments = [
    'システム部',
    '営業部',
    '経理部',
    '総務部',
    '人事部',
    'マーケティング部',
    '開発部',
    '品質管理部'
  ];

  const roles = [
    '管理者',
    'マネージャー',
    '一般ユーザー',
    'ゲスト'
  ];

  const statusOptions = [
    { value: 'active', label: 'アクティブ' },
    { value: 'inactive', label: '非アクティブ' },
    { value: 'suspended', label: '停止中' }
  ];

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
    
    // エラーをクリア
    if (errors[name]) {
      setErrors(prev => ({
        ...prev,
        [name]: ''
      }));
    }
  };

  const validateForm = () => {
    const newErrors: Record<string, string> = {};

    if (!formData.username.trim()) {
      newErrors.username = 'ユーザー名は必須です';
    } else if (!/^[a-zA-Z0-9._-]+$/.test(formData.username)) {
      newErrors.username = 'ユーザー名は英数字とピリオド、ハイフン、アンダースコアのみ使用できます';
    }

    if (!formData.email.trim()) {
      newErrors.email = 'メールアドレスは必須です';
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
      newErrors.email = '有効なメールアドレスを入力してください';
    }

    if (!formData.fullName.trim()) {
      newErrors.fullName = '氏名は必須です';
    }

    if (!formData.department.trim()) {
      newErrors.department = '部署は必須です';
    }

    if (!isEditing) {
      if (!formData.password) {
        newErrors.password = 'パスワードは必須です';
      } else if (formData.password.length < 8) {
        newErrors.password = 'パスワードは8文字以上で入力してください';
      }

      if (formData.password !== formData.confirmPassword) {
        newErrors.confirmPassword = 'パスワードが一致しません';
      }
    }

    if (formData.phone && !/^[\d-+()\\s]+$/.test(formData.phone)) {
      newErrors.phone = '有効な電話番号を入力してください';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    if (validateForm()) {
      const submitData = { ...formData };
      if (isEditing) {
        delete submitData.password;
        delete submitData.confirmPassword;
      }
      onSubmit(submitData);
    }
  };

  return (
    <div className="bg-white rounded-lg shadow">
      <div className="px-6 py-4 border-b border-gray-200">
        <h2 className="text-xl font-semibold text-gray-900">
          {isEditing ? 'ユーザー編集' : '新規ユーザー登録'}
        </h2>
        <p className="text-sm text-gray-500">
          {isEditing ? 'ユーザー情報を編集してください' : '新しいユーザーを登録してください'}
        </p>
      </div>

      <form onSubmit={handleSubmit} className="p-6 space-y-6">
        {/* 基本情報 */}
        <div>
          <h3 className="text-lg font-medium text-gray-900 mb-4">基本情報</h3>
          <div className="grid grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                ユーザー名 <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                name="username"
                value={formData.username}
                onChange={handleChange}
                disabled={isEditing}
                className={`w-full px-3 py-2 border rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 ${
                  errors.username ? 'border-red-300' : 'border-gray-300'
                } ${isEditing ? 'bg-gray-50' : ''}`}
                placeholder="yamada.taro"
              />
              {errors.username && <p className="text-red-500 text-sm mt-1">{errors.username}</p>}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                メールアドレス <span className="text-red-500">*</span>
              </label>
              <input
                type="email"
                name="email"
                value={formData.email}
                onChange={handleChange}
                className={`w-full px-3 py-2 border rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 ${
                  errors.email ? 'border-red-300' : 'border-gray-300'
                }`}
                placeholder="yamada@example.com"
              />
              {errors.email && <p className="text-red-500 text-sm mt-1">{errors.email}</p>}
            </div>

            <div className="col-span-2">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                氏名 <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                name="fullName"
                value={formData.fullName}
                onChange={handleChange}
                className={`w-full px-3 py-2 border rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 ${
                  errors.fullName ? 'border-red-300' : 'border-gray-300'
                }`}
                placeholder="山田太郎"
              />
              {errors.fullName && <p className="text-red-500 text-sm mt-1">{errors.fullName}</p>}
            </div>
          </div>
        </div>

        {/* 組織情報 */}
        <div>
          <h3 className="text-lg font-medium text-gray-900 mb-4">組織情報</h3>
          <div className="grid grid-cols-3 gap-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                役割 <span className="text-red-500">*</span>
              </label>
              <select
                name="role"
                value={formData.role}
                onChange={handleChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              >
                {roles.map(role => (
                  <option key={role} value={role}>{role}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                部署 <span className="text-red-500">*</span>
              </label>
              <select
                name="department"
                value={formData.department}
                onChange={handleChange}
                className={`w-full px-3 py-2 border rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 ${
                  errors.department ? 'border-red-300' : 'border-gray-300'
                }`}
              >
                <option value="">部署を選択してください</option>
                {departments.map(dept => (
                  <option key={dept} value={dept}>{dept}</option>
                ))}
              </select>
              {errors.department && <p className="text-red-500 text-sm mt-1">{errors.department}</p>}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                ステータス
              </label>
              <select
                name="status"
                value={formData.status}
                onChange={handleChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              >
                {statusOptions.map(option => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </div>
          </div>
        </div>

        {/* 連絡先情報 */}
        <div>
          <h3 className="text-lg font-medium text-gray-900 mb-4">連絡先情報</h3>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                電話番号
              </label>
              <input
                type="tel"
                name="phone"
                value={formData.phone}
                onChange={handleChange}
                className={`w-full px-3 py-2 border rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 ${
                  errors.phone ? 'border-red-300' : 'border-gray-300'
                }`}
                placeholder="090-1234-5678"
              />
              {errors.phone && <p className="text-red-500 text-sm mt-1">{errors.phone}</p>}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                住所
              </label>
              <input
                type="text"
                name="address"
                value={formData.address}
                onChange={handleChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder="東京都渋谷区..."
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                緊急連絡先
              </label>
              <input
                type="text"
                name="emergencyContact"
                value={formData.emergencyContact}
                onChange={handleChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder="山田花子 (配偶者) 090-8765-4321"
              />
            </div>
          </div>
        </div>

        {/* パスワード設定 */}
        {!isEditing && (
          <div>
            <h3 className="text-lg font-medium text-gray-900 mb-4">パスワード設定</h3>
            <div className="grid grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  パスワード <span className="text-red-500">*</span>
                </label>
                <input
                  type="password"
                  name="password"
                  value={formData.password}
                  onChange={handleChange}
                  className={`w-full px-3 py-2 border rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 ${
                    errors.password ? 'border-red-300' : 'border-gray-300'
                  }`}
                  placeholder="8文字以上で入力してください"
                />
                {errors.password && <p className="text-red-500 text-sm mt-1">{errors.password}</p>}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  パスワード確認 <span className="text-red-500">*</span>
                </label>
                <input
                  type="password"
                  name="confirmPassword"
                  value={formData.confirmPassword}
                  onChange={handleChange}
                  className={`w-full px-3 py-2 border rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 ${
                    errors.confirmPassword ? 'border-red-300' : 'border-gray-300'
                  }`}
                  placeholder="パスワードを再入力してください"
                />
                {errors.confirmPassword && <p className="text-red-500 text-sm mt-1">{errors.confirmPassword}</p>}
              </div>
            </div>
          </div>
        )}

        {/* フォームアクション */}
        <div className="flex justify-end space-x-4 pt-6 border-t border-gray-200">
          <button
            type="button"
            onClick={onCancel}
            className="px-4 py-2 border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
          >
            キャンセル
          </button>
          <button
            type="submit"
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
          >
            {isEditing ? '更新' : '登録'}
          </button>
        </div>
      </form>
    </div>
  );
};