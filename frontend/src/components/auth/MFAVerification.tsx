import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { Button } from '../ui/Button';
import { Input } from '../ui/Input';
import { Alert } from '../ui/Alert';
import { Card } from '../ui/Card';
import { Form } from '../ui/Form';
import { useAuth } from '../../hooks/useAuth';

interface LocationState {
  mfaToken: string;
  email: string;
}

export const MFAVerification: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { verifyMFA } = useAuth();
  const [code, setCode] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [useBackupCode, setUseBackupCode] = useState(false);

  const state = location.state as LocationState;

  useEffect(() => {
    if (!state?.mfaToken) {
      navigate('/auth/login');
    }
  }, [state, navigate]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      await verifyMFA(state.mfaToken, code, useBackupCode);
      navigate('/dashboard');
    } catch (err: any) {
      setError(err.message || '認証に失敗しました');
    } finally {
      setLoading(false);
    }
  };

  const handleResend = async () => {
    setError('');
    // In a real implementation, this would trigger a new MFA code
    setError('新しいコードを送信しました（実装予定）');
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <div>
          <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
            2段階認証
          </h2>
          <p className="mt-2 text-center text-sm text-gray-600">
            {state?.email} に送信された6桁のコードを入力してください
          </p>
        </div>
        <Card className="mt-8">
          <Form onSubmit={handleSubmit} className="space-y-6">
            {error && <Alert type="error" message={error} />}
            
            <div>
              <label htmlFor="code" className="block text-sm font-medium text-gray-700">
                {useBackupCode ? 'バックアップコード' : '認証コード'}
              </label>
              <Input
                id="code"
                name="code"
                type="text"
                autoComplete="one-time-code"
                required
                value={code}
                onChange={(e) => setCode(e.target.value.replace(/\D/g, ''))}
                className="mt-1 text-center text-2xl tracking-widest"
                placeholder={useBackupCode ? 'xxxxxxxx' : '000000'}
                maxLength={useBackupCode ? 8 : 6}
                pattern={useBackupCode ? '[a-zA-Z0-9]{8}' : '[0-9]{6}'}
              />
              <p className="mt-2 text-sm text-gray-500">
                {useBackupCode 
                  ? 'バックアップコードは8文字の英数字です' 
                  : '認証アプリに表示されている6桁の数字を入力してください'
                }
              </p>
            </div>

            <div>
              <Button
                type="submit"
                variant="primary"
                className="w-full"
                disabled={loading || (useBackupCode ? code.length !== 8 : code.length !== 6)}
              >
                {loading ? '確認中...' : '確認'}
              </Button>
            </div>

            <div className="space-y-3">
              <button
                type="button"
                onClick={() => setUseBackupCode(!useBackupCode)}
                className="text-sm text-blue-600 hover:text-blue-500 block w-full text-center"
              >
                {useBackupCode 
                  ? '認証アプリのコードを使用' 
                  : 'バックアップコードを使用'
                }
              </button>

              <button
                type="button"
                onClick={handleResend}
                className="text-sm text-gray-600 hover:text-gray-500 block w-full text-center"
              >
                コードが届かない場合
              </button>

              <button
                type="button"
                onClick={() => navigate('/auth/login')}
                className="text-sm text-gray-600 hover:text-gray-500 block w-full text-center"
              >
                ログイン画面に戻る
              </button>
            </div>
          </Form>
        </Card>
      </div>
    </div>
  );
};