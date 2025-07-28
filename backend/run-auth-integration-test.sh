#!/bin/bash

# 認証システム統合テストスクリプト

echo "🔧 認証システム統合テスト"
echo "=========================="

# 環境変数設定
export DATABASE_URL="sqlite:///./test.db"
export SECRET_KEY="test-secret-key-for-integration-testing"
export ALGORITHM="HS256"
export ACCESS_TOKEN_EXPIRE_MINUTES="30"

# Google OAuth (テスト用ダミー)
export GOOGLE_CLIENT_ID="test-client-id"
export GOOGLE_CLIENT_SECRET="test-client-secret"
export GOOGLE_REDIRECT_URI="http://localhost:8000/api/v1/auth/google/callback"

# テスト用設定
export SESSION_TIMEOUT_MINUTES="480"
export REMEMBER_ME_DURATION_DAYS="30"
export MAX_CONCURRENT_SESSIONS="5"
export MFA_ISSUER_NAME="ITDO ERP Test"

echo "1. データベースマイグレーション実行..."
cd /mnt/c/work/ITDO_ERP2/backend
uv run alembic upgrade head

echo -e "\n2. バックエンドサーバー起動..."
# バックグラウンドでサーバー起動
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!

# サーバーが起動するまで待機
echo "サーバーの起動を待っています..."
sleep 5

# ヘルスチェック
for i in {1..10}; do
    if curl -s http://localhost:8000/health > /dev/null; then
        echo "✅ バックエンドサーバーが起動しました"
        break
    fi
    echo "待機中... ($i/10)"
    sleep 2
done

echo -e "\n3. API動作確認..."

# ユーザー登録テスト
echo -e "\n--- ユーザー登録テスト ---"
curl -X POST http://localhost:8000/api/v1/users/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "TestPassword123!",
    "full_name": "Test User"
  }' | python -m json.tool

# ログインテスト
echo -e "\n\n--- ログインテスト ---"
LOGIN_RESPONSE=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "TestPassword123!"
  }')

echo "$LOGIN_RESPONSE" | python -m json.tool

# トークン抽出
ACCESS_TOKEN=$(echo "$LOGIN_RESPONSE" | python -c "import sys, json; print(json.load(sys.stdin).get('access_token', ''))")

if [ -n "$ACCESS_TOKEN" ]; then
    echo -e "\n✅ ログイン成功: トークンを取得しました"
    
    # ユーザー情報取得
    echo -e "\n--- ユーザー情報取得テスト ---"
    curl -X GET http://localhost:8000/api/v1/users/me \
      -H "Authorization: Bearer $ACCESS_TOKEN" | python -m json.tool
    
    # セッション一覧取得
    echo -e "\n--- セッション一覧取得テスト ---"
    curl -X GET http://localhost:8000/api/v1/sessions \
      -H "Authorization: Bearer $ACCESS_TOKEN" | python -m json.tool
else
    echo -e "\n❌ ログイン失敗: トークンを取得できませんでした"
fi

# パスワードリセット要求テスト
echo -e "\n--- パスワードリセット要求テスト ---"
curl -X POST http://localhost:8000/api/v1/password-reset/request \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com"}' | python -m json.tool

echo -e "\n4. クリーンアップ..."
# バックエンドサーバー停止
kill $BACKEND_PID 2>/dev/null

echo -e "\n✅ 統合テスト完了"
echo "=========================="
echo "次のステップ:"
echo "1. フロントエンドのE2Eテストを実行: cd frontend && npm run test:e2e"
echo "2. 本番環境用の設定を行う"
echo "3. CI/CDパイプラインに統合テストを追加"