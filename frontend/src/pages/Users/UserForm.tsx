import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Button } from '../../components/ui/Button';
import { Input } from '../../components/ui/Input';
import { Select } from '../../components/ui/Select';
import { Textarea } from '../../components/ui/Textarea';
import { LoadingSpinner } from '../../components/ui/LoadingSpinner';
import { Alert } from '../../components/ui/Alert';
import { PageContainer, CardLayout } from '../../layouts/MainLayout/MainLayout';

interface UserFormData {
  username: string;
  email: string;
  firstName: string;
  lastName: string;
  roles: string[];
  department: string;
  position: string;
  phoneNumber: string;
  status: 'active' | 'inactive' | 'pending';
  bio: string;
  password?: string;
  confirmPassword?: string;
}

interface FormErrors {
  [key: string]: string;
}

const DEPARTMENTS = [
  '営業部',
  '開発部',
  '人事部',
  '経理部',
  'マーケティング部',
  '総務部',
];

const ROLES = [
  { value: 'admin', label: '管理者' },
  { value: 'manager', label: 'マネージャー' },
  { value: 'user', label: 'ユーザー' },
  { value: 'viewer', label: '閲覧者' },
];

const STATUS_OPTIONS = [
  { value: 'active', label: 'アクティブ' },
  { value: 'inactive', label: '無効' },
  { value: 'pending', label: '保留中' },
];

export const UserForm: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const isEdit = !!id && id !== 'create';
  
  const [formData, setFormData] = useState<UserFormData>({
    username: '',
    email: '',
    firstName: '',
    lastName: '',
    roles: ['user'],
    department: '',
    position: '',
    phoneNumber: '',
    status: 'active',
    bio: '',
    password: '',
    confirmPassword: '',
  });
  
  const [errors, setErrors] = useState<FormErrors>({});
  const [loading, setLoading] = useState(false);
  const [initialLoading, setInitialLoading] = useState(isEdit);
  const [submitError, setSubmitError] = useState<string | null>(null);

  // 編集時のデータ読み込み
  useEffect(() => {
    if (isEdit) {
      const fetchUser = async () => {
        try {
          setInitialLoading(true);
          
          // モックAPI呼び出し
          await new Promise(resolve => setTimeout(resolve, 800));
          
          // モックデータ
          const mockUser = {
            username: `user${id}`,
            email: `user${id}@example.com`,
            firstName: '太郎',
            lastName: '田中',
            roles: ['manager', 'user'],
            department: '開発部',
            position: 'シニアエンジニア',
            phoneNumber: '03-1234-5678',
            status: 'active' as const,
            bio: 'フルスタックエンジニアとして5年の経験があります。',
          };
          
          setFormData(prev => ({ ...prev, ...mockUser }));
        } catch (error) {
          setSubmitError('ユーザー情報の読み込みに失敗しました');
        } finally {
          setInitialLoading(false);
        }
      };
      
      fetchUser();
    }
  }, [isEdit, id]);

  // フォームバリデーション
  const validateForm = (): boolean => {
    const newErrors: FormErrors = {};

    // 必須項目チェック
    if (!formData.username.trim()) {
      newErrors.username = 'ユーザー名は必須です';
    } else if (!/^[a-zA-Z0-9_]+$/.test(formData.username)) {
      newErrors.username = 'ユーザー名は英数字とアンダースコアのみ使用可能です';
    }

    if (!formData.email.trim()) {
      newErrors.email = 'メールアドレスは必須です';
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
      newErrors.email = '有効なメールアドレスを入力してください';
    }

    if (!formData.firstName.trim()) {
      newErrors.firstName = '名前は必須です';
    }

    if (!formData.lastName.trim()) {
      newErrors.lastName = '姓は必須です';
    }

    if (!formData.department) {
      newErrors.department = '部署は必須です';
    }

    if (formData.roles.length === 0) {
      newErrors.roles = '少なくとも1つのロールを選択してください';
    }

    // パスワードチェック（新規作成時）
    if (!isEdit) {
      if (!formData.password) {
        newErrors.password = 'パスワードは必須です';
      } else if (formData.password.length < 8) {
        newErrors.password = 'パスワードは8文字以上で入力してください';
      }

      if (formData.password !== formData.confirmPassword) {
        newErrors.confirmPassword = 'パスワードが一致しません';
      }
    } else if (formData.password || formData.confirmPassword) {
      // 編集時でパスワード変更する場合
      if (formData.password && formData.password.length < 8) {
        newErrors.password = 'パスワードは8文字以上で入力してください';
      }
      
      if (formData.password !== formData.confirmPassword) {
        newErrors.confirmPassword = 'パスワードが一致しません';
      }
    }

    // 電話番号チェック（任意）
    if (formData.phoneNumber && !/^[\d-+() ]+$/.test(formData.phoneNumber)) {
      newErrors.phoneNumber = '有効な電話番号を入力してください';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  // フォーム送信処理
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }

    setLoading(true);
    setSubmitError(null);

    try {
      // モックAPI呼び出し
      await new Promise(resolve => setTimeout(resolve, 1500));
      
      // ランダムエラーシミュレーション
      if (Math.random() < 0.1) {
        throw new Error('ネットワークエラーが発生しました');
      }
      
      const successMessage = isEdit ? 'ユーザー情報を更新しました' : 'ユーザーを作成しました';
      
      navigate('/users', { 
        state: { message: successMessage }
      });
    } catch (error) {
      setSubmitError(error instanceof Error ? error.message : '保存に失敗しました');
    } finally {
      setLoading(false);
    }
  };

  // フィールド変更処理
  const handleFieldChange = (field: keyof UserFormData, value: any) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    
    // エラーをクリア
    if (errors[field]) {
      setErrors(prev => ({ ...prev, [field]: '' }));
    }
    
    // 確認用パスワードのエラーもクリア
    if (field === 'password' && errors.confirmPassword) {
      setErrors(prev => ({ ...prev, confirmPassword: '' }));
    }
  };

  // 複数選択のロール変更
  const handleRoleChange = (role: string, checked: boolean) => {
    const newRoles = checked 
      ? [...formData.roles, role]
      : formData.roles.filter(r => r !== role);
    
    handleFieldChange('roles', newRoles);
  };

  if (initialLoading) {
    return (
      <PageContainer>
        <div className="flex items-center justify-center py-12">
          <LoadingSpinner size="lg" />
          <span className="ml-3 text-gray-600">ユーザー情報を読み込んでいます...</span>
        </div>
      </PageContainer>
    );
  }

  return (
    <PageContainer
      title={isEdit ? 'ユーザー編集' : '新規ユーザー作成'}
      subtitle={isEdit ? formData.username ? `@${formData.username}` : '' : 'システムに新しいユーザーを追加'}
    >
      <div className="max-w-4xl mx-auto">
        <form onSubmit={handleSubmit} className="space-y-6">
          {submitError && (
            <Alert variant="error" title="エラー">
              {submitError}
            </Alert>
          )}

          {/* 基本情報 */}
          <CardLayout>
            <h3 className="text-lg font-semibold mb-6">基本情報</h3>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label htmlFor="username" className="block text-sm font-medium text-gray-700 mb-2">
                  ユーザー名 *
                </label>
                <Input
                  id="username"
                  value={formData.username}
                  onChange={(e) => handleFieldChange('username', e.target.value)}
                  error={errors.username}
                  disabled={loading}
                  placeholder="例: taro_tanaka"
                />
              </div>

              <div>
                <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-2">
                  メールアドレス *
                </label>
                <Input
                  id="email"
                  type="email"
                  value={formData.email}
                  onChange={(e) => handleFieldChange('email', e.target.value)}
                  error={errors.email}
                  disabled={loading}
                  placeholder="例: taro.tanaka@example.com"
                />
              </div>

              <div>
                <label htmlFor="lastName" className="block text-sm font-medium text-gray-700 mb-2">
                  姓 *
                </label>
                <Input
                  id="lastName"
                  value={formData.lastName}
                  onChange={(e) => handleFieldChange('lastName', e.target.value)}
                  error={errors.lastName}
                  disabled={loading}
                  placeholder="例: 田中"
                />
              </div>

              <div>
                <label htmlFor="firstName" className="block text-sm font-medium text-gray-700 mb-2">
                  名前 *
                </label>
                <Input
                  id="firstName"
                  value={formData.firstName}
                  onChange={(e) => handleFieldChange('firstName', e.target.value)}
                  error={errors.firstName}
                  disabled={loading}
                  placeholder="例: 太郎"
                />
              </div>

              <div>
                <label htmlFor="department" className="block text-sm font-medium text-gray-700 mb-2">
                  部署 *
                </label>
                <Select
                  value={formData.department}
                  onChange={(value) => handleFieldChange('department', value)}
                  disabled={loading}
                  placeholder="部署を選択してください"
                >
                  {DEPARTMENTS.map(dept => (
                    <Select.Option key={dept} value={dept}>
                      {dept}
                    </Select.Option>
                  ))}
                </Select>
                {errors.department && (
                  <p className="mt-1 text-sm text-red-600">{errors.department}</p>
                )}
              </div>

              <div>
                <label htmlFor="position" className="block text-sm font-medium text-gray-700 mb-2">
                  役職
                </label>
                <Input
                  id="position"
                  value={formData.position}
                  onChange={(e) => handleFieldChange('position', e.target.value)}
                  disabled={loading}
                  placeholder="例: シニアエンジニア"
                />
              </div>

              <div>
                <label htmlFor="phoneNumber" className="block text-sm font-medium text-gray-700 mb-2">
                  電話番号
                </label>
                <Input
                  id="phoneNumber"
                  value={formData.phoneNumber}
                  onChange={(e) => handleFieldChange('phoneNumber', e.target.value)}
                  error={errors.phoneNumber}
                  disabled={loading}
                  placeholder="例: 03-1234-5678"
                />
              </div>

              <div>
                <label htmlFor="status" className="block text-sm font-medium text-gray-700 mb-2">
                  ステータス
                </label>
                <Select
                  value={formData.status}
                  onChange={(value) => handleFieldChange('status', value)}
                  disabled={loading}
                >
                  {STATUS_OPTIONS.map(option => (
                    <Select.Option key={option.value} value={option.value}>
                      {option.label}
                    </Select.Option>
                  ))}
                </Select>
              </div>
            </div>

            <div className="mt-6">
              <label htmlFor="bio" className="block text-sm font-medium text-gray-700 mb-2">
                自己紹介
              </label>
              <Textarea
                id="bio"
                value={formData.bio}
                onChange={(e) => handleFieldChange('bio', e.target.value)}
                disabled={loading}
                placeholder="自己紹介や経歴について入力してください"
                rows={3}
              />
            </div>
          </CardLayout>

          {/* ロール・権限設定 */}
          <CardLayout>
            <h3 className="text-lg font-semibold mb-6">ロール・権限設定</h3>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-3">
                ロール *
              </label>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                {ROLES.map(role => (
                  <label key={role.value} className="flex items-center space-x-2 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={formData.roles.includes(role.value)}
                      onChange={(e) => handleRoleChange(role.value, e.target.checked)}
                      disabled={loading}
                      className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                    />
                    <span className="text-sm text-gray-700">{role.label}</span>
                  </label>
                ))}
              </div>
              {errors.roles && (
                <p className="mt-2 text-sm text-red-600">{errors.roles}</p>
              )}
            </div>
          </CardLayout>

          {/* パスワード設定 */}
          <CardLayout>
            <h3 className="text-lg font-semibold mb-6">
              {isEdit ? 'パスワード変更' : 'パスワード設定'}
            </h3>
            
            {isEdit && (
              <div className="mb-4 p-4 bg-yellow-50 rounded-lg border border-yellow-200">
                <p className="text-sm text-yellow-800">
                  パスワードを変更する場合のみ入力してください。空白の場合は変更されません。
                </p>
              </div>
            )}

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-2">
                  パスワード {!isEdit && '*'}
                </label>
                <Input
                  id="password"
                  type="password"
                  value={formData.password || ''}
                  onChange={(e) => handleFieldChange('password', e.target.value)}
                  error={errors.password}
                  disabled={loading}
                  placeholder="8文字以上で入力してください"
                />
              </div>

              <div>
                <label htmlFor="confirmPassword" className="block text-sm font-medium text-gray-700 mb-2">
                  パスワード確認 {!isEdit && '*'}
                </label>
                <Input
                  id="confirmPassword"
                  type="password"
                  value={formData.confirmPassword || ''}
                  onChange={(e) => handleFieldChange('confirmPassword', e.target.value)}
                  error={errors.confirmPassword}
                  disabled={loading}
                  placeholder="同じパスワードを入力してください"
                />
              </div>
            </div>
          </CardLayout>

          {/* 送信ボタン */}
          <div className="flex items-center justify-end space-x-4 pt-6">
            <Button
              type="button"
              variant="ghost"
              onClick={() => navigate('/users')}
              disabled={loading}
            >
              キャンセル
            </Button>
            
            <Button
              type="submit"
              disabled={loading}
              className="min-w-[120px]"
            >
              {loading ? (
                <>
                  <LoadingSpinner size="sm" className="mr-2" />
                  {isEdit ? '更新中...' : '作成中...'}
                </>
              ) : (
                isEdit ? '更新' : '作成'
              )}
            </Button>
          </div>
        </form>
      </div>
    </PageContainer>
  );
};