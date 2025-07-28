# Phase 4 完了後の次のアクション

## 🎯 即座に実行すべきアクション

### 1. データベースマイグレーション作成
Phase 4で追加した新しいモデルのマイグレーションファイルを作成する必要があります。

```bash
cd backend
uv run alembic revision --autogenerate -m "Add authentication models - MFA, sessions, password reset"
uv run alembic upgrade head
```

### 2. 環境変数の設定
以下の環境変数を`.env`ファイルに追加：

```env
# Google OAuth2.0
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
GOOGLE_REDIRECT_URI=http://localhost:8000/api/v1/auth/google/callback

# Email Service (開発環境ではコンソール出力)
EMAIL_BACKEND=console
EMAIL_FROM=noreply@itdo-erp.com

# Session Configuration
SESSION_TIMEOUT_MINUTES=480
REMEMBER_ME_DURATION_DAYS=30
MAX_CONCURRENT_SESSIONS=5

# Security
PASSWORD_RESET_TIMEOUT_HOURS=1
MFA_ISSUER_NAME=ITDO ERP
ACCOUNT_LOCKOUT_THRESHOLD=5
ACCOUNT_LOCKOUT_DURATION_MINUTES=30
```

### 3. 依存関係の確認とインストール
```bash
cd backend
# 既に追加済みですが、確認のため
uv add pyotp qrcode[pil] user-agents google-auth google-auth-oauthlib google-auth-httplib2
```

### 4. フロントエンドのルーティング設定
`frontend/src/App.tsx`に認証関連のルートを追加：

```tsx
import { 
  LoginForm, 
  RegisterForm, 
  MFAVerification, 
  ForgotPassword, 
  ResetPassword,
  MFASetup,
  ProtectedRoute,
  SecuritySettings 
} from './components/auth';

// ルート設定
<Routes>
  {/* Public routes */}
  <Route path="/auth/login" element={<LoginForm />} />
  <Route path="/auth/register" element={<RegisterForm />} />
  <Route path="/auth/mfa-verify" element={<MFAVerification />} />
  <Route path="/auth/forgot-password" element={<ForgotPassword />} />
  <Route path="/auth/reset-password" element={<ResetPassword />} />
  
  {/* Protected routes */}
  <Route path="/dashboard" element={
    <ProtectedRoute>
      <Dashboard />
    </ProtectedRoute>
  } />
  
  <Route path="/settings/security" element={
    <ProtectedRoute>
      <SecuritySettings />
    </ProtectedRoute>
  } />
  
  <Route path="/settings/security/mfa-setup" element={
    <ProtectedRoute>
      <MFASetup />
    </ProtectedRoute>
  } />
</Routes>
```

### 5. API統合の確認
バックエンドAPIが正しく登録されているか確認：

```python
# backend/app/main.py に追加
from app.api.v1 import auth, users, sessions, mfa, security, password_reset

app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(users.router, prefix="/api/v1/users", tags=["users"])
app.include_router(sessions.router, prefix="/api/v1/sessions", tags=["sessions"])
app.include_router(mfa.router, prefix="/api/v1/mfa", tags=["mfa"])
app.include_router(security.router, prefix="/api/v1/security", tags=["security"])
app.include_router(password_reset.router, prefix="/api/v1/password-reset", tags=["password-reset"])
```

## 🚀 推奨される次のフェーズ

### Phase 5: 統合とデプロイメント

1. **統合テスト**
   - 既存システムとの統合
   - パフォーマンステスト
   - 負荷テスト

2. **セキュリティ監査**
   - コードレビュー
   - 脆弱性スキャン
   - ペネトレーションテスト

3. **本番環境準備**
   - Docker/Kubernetes設定
   - CI/CDパイプライン
   - 監視・アラート設定

4. **ドキュメント整備**
   - API ドキュメント
   - 管理者ガイド
   - ユーザーガイド

## 📝 確認チェックリスト

- [ ] データベースマイグレーションの実行
- [ ] 環境変数の設定
- [ ] フロントエンドルーティングの設定
- [ ] E2Eテストの実行
- [ ] セキュリティ設定の確認
- [ ] ログ設定の確認
- [ ] エラーハンドリングの確認

これらの準備が整えば、認証システムは本番環境で使用可能です。