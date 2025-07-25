# ゼロコンテキスト開発指示

## 📝 用途: トークン消費最適化のための簡素化アプローチ

**目的**: Claude使用量削減・効率化のための最小限指示
**適用場面**: トークン制限対策、コスト最適化、高速開発

## Frontend開発（旧CC01）

### 試行順序

1️⃣
```
UserProfile.tsxを作成してください
```

2️⃣
```
frontend/src/components/にUserProfileコンポーネントを追加
```

3️⃣
```
Reactでユーザープロフィール画面を作って
```

4️⃣
```
import React from 'react';

const UserProfile = () => {
  return <div>Profile</div>;
};

これを完成させて
```

---

## Backend開発（旧CC02）

### 試行順序

1️⃣
```
role.pyにcreate_role関数を追加
```

2️⃣
```
FastAPIでロール管理APIを作って
```

3️⃣
```
@router.post("/roles")
async def create_role():
    pass

これを実装して
```

4️⃣
```
SQLAlchemyでRoleモデルのCRUD操作を書いて
```