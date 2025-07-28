import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '../ui/Button';
import { Card } from '../ui/Card';
import { Alert } from '../ui/Alert';
import { Badge } from '../ui/Badge';
import { Modal } from '../ui/Modal';
import { Input } from '../ui/Input';
import { useAuth } from '../../hooks/useAuth';
import { SessionManager } from './SessionManager';

export const SecuritySettings: React.FC = () => {
  const navigate = useNavigate();
  const { user, disableMFA } = useAuth();
  const [activeTab, setActiveTab] = useState<'overview' | 'mfa' | 'sessions'>('overview');
  const [showDisableMFAModal, setShowDisableMFAModal] = useState(false);
  const [password, setPassword] = useState('');
  const [disablingMFA, setDisablingMFA] = useState(false);
  const [error, setError] = useState('');

  const handleDisableMFA = async () => {
    setError('');
    setDisablingMFA(true);

    try {
      await disableMFA(password);
      setShowDisableMFAModal(false);
      setPassword('');
    } catch (err: any) {
      setError(err.message || 'MFAの無効化に失敗しました');
    } finally {
      setDisablingMFA(false);
    }
  };

  const SecurityOverview = () => (
    <div className="space-y-6">
      <Card>
        <h3 className="text-lg font-semibold mb-4">セキュリティステータス</h3>
        <div className="space-y-4">
          <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
            <div>
              <p className="font-medium">2段階認証</p>
              <p className="text-sm text-gray-600">
                アカウントの不正アクセスを防ぎます
              </p>
            </div>
            <Badge variant={user?.mfa_required ? 'success' : 'warning'}>
              {user?.mfa_required ? '有効' : '無効'}
            </Badge>
          </div>

          <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
            <div>
              <p className="font-medium">Googleアカウント連携</p>
              <p className="text-sm text-gray-600">
                Googleアカウントでログインできます
              </p>
            </div>
            <Badge variant={user?.has_google_account ? 'info' : 'default'}>
              {user?.has_google_account ? '連携済み' : '未連携'}
            </Badge>
          </div>

          <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
            <div>
              <p className="font-medium">パスワード強度</p>
              <p className="text-sm text-gray-600">
                強力なパスワードを使用してください
              </p>
            </div>
            <Button
              variant="outline"
              size="small"
              onClick={() => navigate('/settings/change-password')}
            >
              パスワードを変更
            </Button>
          </div>
        </div>
      </Card>

      <Card>
        <h3 className="text-lg font-semibold mb-4">セキュリティ推奨事項</h3>
        <ul className="space-y-3">
          {!user?.mfa_required && (
            <li className="flex items-start">
              <span className="text-yellow-500 mr-2">⚠️</span>
              <div>
                <p className="font-medium">2段階認証を有効にする</p>
                <p className="text-sm text-gray-600">
                  アカウントのセキュリティを大幅に向上させます
                </p>
                <Button
                  variant="primary"
                  size="small"
                  className="mt-2"
                  onClick={() => navigate('/settings/security/mfa-setup')}
                >
                  今すぐ設定
                </Button>
              </div>
            </li>
          )}
          <li className="flex items-start">
            <span className="text-blue-500 mr-2">💡</span>
            <div>
              <p className="font-medium">定期的にパスワードを変更する</p>
              <p className="text-sm text-gray-600">
                3〜6ヶ月ごとにパスワードを更新することを推奨します
              </p>
            </div>
          </li>
          <li className="flex items-start">
            <span className="text-blue-500 mr-2">💡</span>
            <div>
              <p className="font-medium">アクティブなセッションを確認する</p>
              <p className="text-sm text-gray-600">
                定期的に不審なセッションがないか確認してください
              </p>
            </div>
          </li>
        </ul>
      </Card>
    </div>
  );

  const MFASettings = () => (
    <div className="space-y-6">
      <Card>
        <h3 className="text-lg font-semibold mb-4">2段階認証設定</h3>
        {user?.mfa_required ? (
          <div className="space-y-4">
            <Alert
              type="success"
              message="2段階認証が有効になっています"
            />
            <div className="p-4 bg-gray-50 rounded-lg">
              <p className="font-medium mb-2">認証方法</p>
              <div className="flex items-center space-x-2">
                <Badge variant="info">TOTP (認証アプリ)</Badge>
              </div>
            </div>
            <div className="flex space-x-3">
              <Button
                variant="outline"
                onClick={() => navigate('/settings/security/mfa-devices')}
              >
                デバイスを管理
              </Button>
              <Button
                variant="outline"
                onClick={() => navigate('/settings/security/backup-codes')}
              >
                バックアップコード
              </Button>
              <Button
                variant="outline"
                onClick={() => setShowDisableMFAModal(true)}
                className="text-red-600 hover:text-red-700"
              >
                2段階認証を無効化
              </Button>
            </div>
          </div>
        ) : (
          <div className="text-center py-8">
            <div className="mb-4">
              <svg
                className="mx-auto h-12 w-12 text-gray-400"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"
                />
              </svg>
            </div>
            <h4 className="text-lg font-medium mb-2">
              2段階認証が無効になっています
            </h4>
            <p className="text-gray-600 mb-4">
              アカウントのセキュリティを強化するため、2段階認証の設定を推奨します
            </p>
            <Button
              variant="primary"
              onClick={() => navigate('/settings/security/mfa-setup')}
            >
              2段階認証を設定
            </Button>
          </div>
        )}
      </Card>
    </div>
  );

  return (
    <div className="max-w-4xl mx-auto">
      <h2 className="text-2xl font-bold mb-6">セキュリティ設定</h2>

      <div className="mb-6">
        <nav className="flex space-x-4 border-b">
          <button
            className={`pb-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'overview'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
            onClick={() => setActiveTab('overview')}
          >
            概要
          </button>
          <button
            className={`pb-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'mfa'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
            onClick={() => setActiveTab('mfa')}
          >
            2段階認証
          </button>
          <button
            className={`pb-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'sessions'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
            onClick={() => setActiveTab('sessions')}
          >
            セッション管理
          </button>
        </nav>
      </div>

      {activeTab === 'overview' && <SecurityOverview />}
      {activeTab === 'mfa' && <MFASettings />}
      {activeTab === 'sessions' && <SessionManager />}

      <Modal
        isOpen={showDisableMFAModal}
        onClose={() => {
          setShowDisableMFAModal(false);
          setPassword('');
          setError('');
        }}
        title="2段階認証を無効化"
      >
        <Alert
          type="warning"
          message="2段階認証を無効化すると、アカウントのセキュリティが低下します"
          className="mb-4"
        />
        
        {error && <Alert type="error" message={error} className="mb-4" />}

        <p className="text-gray-600 mb-4">
          続行するには、パスワードを入力してください。
        </p>

        <Input
          type="password"
          placeholder="パスワード"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          className="mb-4"
        />

        <div className="flex justify-end space-x-3">
          <Button
            variant="outline"
            onClick={() => {
              setShowDisableMFAModal(false);
              setPassword('');
              setError('');
            }}
          >
            キャンセル
          </Button>
          <Button
            variant="primary"
            onClick={handleDisableMFA}
            disabled={!password || disablingMFA}
            className="bg-red-600 hover:bg-red-700"
          >
            {disablingMFA ? '無効化中...' : '無効化'}
          </Button>
        </div>
      </Modal>
    </div>
  );
};