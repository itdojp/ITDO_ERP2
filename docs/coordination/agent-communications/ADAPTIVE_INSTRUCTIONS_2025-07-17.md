# 🎯 エージェント活動状況に対応した適応的指示

**作成日時**: 2025年7月17日 23:00 JST  
**作成者**: Claude Code (CC01) - システム統合担当  
**目的**: エージェント活動状況に応じた柔軟な指示

## 📢 シナリオA: エージェントが活動中の場合

### CC01への発展的指示

```markdown
@cc01

活動を確認しました。以下のタスクを進めてください：

**現在のフェーズ**:
1. 現在の作業内容を報告
2. 進捗率を確認（%で表示）
3. ブロッカーがあれば共有

**次のフェーズ**:
- UIコンポーネントの基本実装を継続
- Button, Input, Cardコンポーネントから優先
- TDDアプローチを必須

**品質基準**:
- TypeScript型安全性 100%
- テストカバレッジ >80%
- Storybookドキュメント作成
```

### CC02への発展的指示

```markdown
@cc02

活動を確認しました。以下のタスクを進めてください：

**現在のフェーズ**:
1. 実装中のAPIエンドポイントをリスト
2. テスト作成状況を報告
3. DBスキーマの更新状況

**次のフェーズ**:
- Organization Management APIの完成
- Department階層構造の実装
- 権限管理システムとの統合

**注意事項**:
- PR #179との競合を避ける
- 既存コードとの整合性を保つ
- SQLAlchemy 2.0のパターンを遵守
```

### CC03への発展的指示

```markdown
@cc03

活動を確認しました。以下のタスクを進めてください：

**現在のフェーズ**:
1. 実施した改善内容を報告
2. CI/CDパイプラインの状態
3. テスト実行結果

**次のフェーズ**:
- Issue #173の自動割り当てシステム完成
- E2Eテストフレームワーク構築
- パフォーマンス監視システム

**優先事項**:
- GitHub Actionsの最適化
- テスト実行時間の短縮
- セキュリティスキャンの強化
```

## 📢 シナリオB: エージェントが未活動の場合

### 全エージェントへの再起動指示

```markdown
@cc01 @cc02 @cc03

緊急再起動プロトコルを実施します。

**各エージェントの最小タスク**:

CC01: 
- frontend/docs/AGENT_STATUS.md を作成
- "CC01 Active: [timestamp]" を記載
- コミットして報告

CC02:
- backend/docs/AGENT_STATUS.md を作成  
- "CC02 Active: [timestamp]" を記載
- コミットして報告

CC03:
- .github/workflows/agent-health.yml を作成
- 最小限のワークフローを定義
- コミットして報告

**制限時間**: 30分以内に完了
**成功基準**: 1つ以上のコミット確認
```

### 人間への推奨事項

```markdown
エージェントが応答しない場合の対処法:

1. **短期対策**:
   - 人間による開発を継続
   - PR #179, #180の完成を優先
   - エージェントは補助的役割に

2. **中期対策**:
   - エージェント用の簡単なIssueを作成
   - 明確なassignee設定
   - 段階的なタスク複雑化

3. **長期対策**:
   - 自動化システムの構築
   - エージェント監視ダッシュボード
   - フェイルセーフ機構
```

## 📋 柔軟なタスク管理

### 活動中エージェント用タスクプール

```yaml
CC01_tasks:
  immediate:
    - Buttonコンポーネント完成
    - Inputコンポーネント開始
  next:
    - Formコンポーネント
    - Tableコンポーネント
  future:
    - Dashboardテンプレート

CC02_tasks:
  immediate:
    - Organization API完成
    - Department API開始
  next:
    - Role管理API
    - Permission API
  future:
    - レポートシステム

CC03_tasks:
  immediate:
    - 自動割り当て修正
    - CI最適化
  next:
    - E2Eテスト構築
    - 監視システム
  future:
    - パフォーマンス分析
```

### 未活動エージェント用初動タスク

```yaml
activation_tasks:
  level_1: # 最も簡単
    - ステータスファイル作成
    - README更新
    - コメント追加
  
  level_2: # 少し複雑
    - 簡単なテスト追加
    - ドキュメント更新
    - 設定ファイル修正
  
  level_3: # 通常タスク
    - コンポーネント実装
    - APIエンドポイント
    - CI/CD改善
```

## 🔧 監視とサポート

### 活動監視スクリプト
```bash
#!/bin/bash
# scripts/monitor-agents-adaptive.sh

echo "=== Adaptive Agent Monitoring ==="
date

# Check activity
ACTIVITY=$(git log --since="2 hours ago" --grep="CC0[123]" | wc -l)

if [ $ACTIVITY -gt 0 ]; then
    echo "Status: ACTIVE"
    echo "Mode: Development tasks"
    echo "Next: Monitor progress"
else
    echo "Status: INACTIVE" 
    echo "Mode: Restart protocol"
    echo "Next: Simple activation tasks"
fi

echo "=== End ==="
```

### フィードバックループ
```yaml
feedback_cycle:
  1_check: 活動状況確認
  2_adapt: 指示内容調整
  3_execute: タスク実行
  4_verify: 結果検証
  5_iterate: 次サイクルへ
```

## 🎯 結論

エージェントの活動状況に関わらず、柔軟に対応できる指示体系を準備しました。

- **活動中**: 発展的タスクで成長を促進
- **未活動**: 最小タスクで再起動を試みる
- **どちらでも**: 人間の開発を優先し、プロジェクトの進捗を確保

---

**📌 次のステップ**: エージェントの実際の活動状況を確認後、適切なシナリオを選択