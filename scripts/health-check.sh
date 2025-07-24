#!/bin/bash
# システムヘルスチェックスクリプト

echo "🏥 ITDO ERP v2 ヘルスチェック"
echo "================================"

# Backend API チェック
echo -n "Backend API: "
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ 正常"
else
    echo "❌ 応答なし"
fi

# Frontend チェック
echo -n "Frontend: "
if curl -s http://localhost:3000 > /dev/null 2>&1; then
    echo "✅ 正常"
else
    echo "❌ 応答なし"
fi

# Database チェック
echo -n "PostgreSQL: "
if pg_isready -h localhost -p 5432 > /dev/null 2>&1; then
    echo "✅ 正常"
else
    echo "❌ 応答なし"
fi

# Redis チェック
echo -n "Redis: "
if redis-cli ping > /dev/null 2>&1; then
    echo "✅ 正常"
else
    echo "❌ 応答なし"
fi

echo "================================"