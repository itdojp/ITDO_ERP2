# 最長自走実行プロンプト集

## 🚀 CC01 Frontend Agent - 最大自走モード

```
【CC01 最大自走モード開始 - 目標: 4-5時間継続】

📋 **実行優先順位タスクリスト**（合計50タスク以上）:

優先度P0（必須）:
- Issue #379: Frontend Development Sprint（20タスク）
- Issue #331: Testing Suite Expansion Phase 6-10（5タスク）

優先度P1（重要）:
- Issue #342: Component Performance Optimization（10タスク）
- Issue #358: Advanced UI Component Library（10タスク）

優先度P2（推奨）:
- Issue #343: Experimental Frontend Features（10タスク）
- Issue #332: Frontend Documentation（5タスク）

優先度P3（時間があれば）:
- Issue #330: UI/UX Improvements（10タスク）
- Issue #364: Bundle Size Reduction（5タスク）

🎯 **自走実行ルール**:
1. P0から順に実行、完了したら次の優先度へ
2. ブロック時は10分試行後、次タスクへ自動移行
3. 各タスク完了をIssue #351に簡潔に報告（1-2行）
4. 30分ごとに進捗サマリーを投稿
5. エラー3回で該当Issueをスキップ

⚡ **パフォーマンス最適化**:
- テスト実行は必須だが、全テストスイートは1時間ごと
- ビルド時間が5分超えたら簡易ビルドに切替
- コミットは5タスクごとにまとめて実行

📊 **自動報告フォーマット**:
30分報告: "CC01: 完了 8/50 | 現在: Issue #379 Task 9 | 順調"
エラー報告: "CC01: Issue #342 Task 3 ブロック | 次へ移行"

🔄 **継続条件**:
- 4時間経過 または
- 40タスク完了 または
- 全P0,P1タスク完了
上記いずれかで停止し、最終報告を作成

停止時: "CC01最大自走完了: [完了数]タスク/[時間]"
```

## 🔧 CC02 Backend Agent - 最大自走モード

```
【CC02 最大自走モード開始 - 目標: 4-5時間継続】

📋 **実行優先順位タスクリスト**（合計45タスク以上）:

優先度P0（必須・データ安全）:
- Issue #380: Backend API Sprint（18タスク）
- Issue #336: Backend Testing Quality Phase 1-5（5タスク）

優先度P1（重要・機能拡張）:
- Issue #344: GraphQL Complete Implementation（10タスク）
- Issue #333: Backend API Development（10タスク）

優先度P2（推奨・最適化）:
- Issue #345: Performance Optimization（8タスク）
- Issue #365: Database Query Optimization（5タスク）

優先度P3（時間があれば）:
- Issue #346: Third-Party Integrations（5タスク）
- Issue #371: API Versioning Strategy（3タスク）

🎯 **自走実行ルール**:
1. データベース操作は必ずトランザクション内で実行
2. マイグレーションは個別に実行し結果確認
3. API変更後は自動でOpenAPI仕様更新
4. パフォーマンステストは10タスクごと
5. 本番相当データでのテスト必須

⚡ **安全性最適化**:
- DB変更前に自動バックアップ（開発環境）
- 破壊的変更は警告付きで実行確認
- ロールバックスクリプト自動生成
- メモリ使用量監視（1GB超で一時停止）

📊 **自動報告フォーマット**:
30分報告: "CC02: 完了 7/45 | DB健全性:OK | API:15追加"
性能報告: "CC02: Query改善 -40% | メモリ:780MB"

🔄 **継続条件**:
- 4時間経過 または
- 35タスク完了 または
- データベースエラー2回連続
上記いずれかで安全に停止

停止時: "CC02最大自走完了: API[数] | DB最適化[%] | 安全停止"
```

## 🏗️ CC03 Infrastructure Agent - 最大自走モード

```
【CC03 最大自走モード開始 - 目標: 4-5時間継続】

📋 **実行優先順位タスクリスト**（合計40タスク以上）:

優先度P0（必須・安定性）:
- Issue #381: Infrastructure Sprint（15タスク）
- Issue #337: CI/CD Pipeline Enhancement Phase 1-5（5タスク）

優先度P1（重要・可用性）:
- Issue #347: Infrastructure Overhaul（8タスク）
- Issue #348: High Availability Setup（5タスク）

優先度P2（推奨・最適化）:
- Issue #349: DevOps Automation（8タスク）
- Issue #366: Cost Optimization（5タスク）

優先度P3（時間があれば）:
- Issue #360: Multi-Cloud Support（4タスク）
- Issue #377: Disaster Recovery（3タスク）

🎯 **自走実行ルール**:
1. 本番影響度を3段階評価（Low/Med/High）
2. High影響は開発環境のみで実施
3. インフラ変更はTerraform/IaCで管理
4. メトリクス計測は必須（前後比較）
5. セキュリティスキャン自動実行

⚡ **リソース最適化**:
- CI実行は並列度を動的調整
- コンテナビルドはキャッシュ最大活用
- 不要リソースの自動クリーンアップ
- コスト計算を10タスクごとに実施

📊 **自動報告フォーマット**:
30分報告: "CC03: 完了 6/40 | CI高速化:30% | コスト:-15%"
インフラ報告: "CC03: k8s最適化 | Pod削減:20 | 安定稼働"

🔄 **継続条件**:
- 4時間経過 または
- 30タスク完了 または
- 本番影響度High検出3回
上記いずれかで安全に停止

停止時: "CC03最大自走完了: Infra改善[項目数] | 月額削減[$]"
```

## 🎯 共通の長期実行サポート機能

### 自動回復メカニズム
```javascript
// 疑似コード
if (taskFailed) {
  retryCount++;
  if (retryCount < 3) {
    wait(30); // 30秒待機
    retryTask();
  } else {
    logError();
    moveToNextTask();
  }
}
```

### 進捗状態の永続化
```json
// /reports/marathon_state.json
{
  "CC01": {
    "startTime": "2025-07-21 10:00:00",
    "tasksCompleted": 15,
    "currentIssue": 379,
    "currentTask": 16,
    "errors": [],
    "nextPriority": "P1"
  }
}
```

### インテリジェント優先度調整
- 成功率が高いタスクを優先
- 依存関係を自動解析
- 時間帯による負荷分散
- リソース使用量による調整

### 最終報告テンプレート
```
## 🏁 [Agent] 最大自走実行完了報告

📊 **実行統計**:
- 総実行時間: 4時間23分
- 完了タスク: 38/50 (76%)
- 成功率: 92%
- 生産性: 8.7タスク/時間

✨ **主要成果**:
1. [最も重要な成果]
2. [2番目に重要な成果]
3. [3番目に重要な成果]

💡 **技術的改善**:
- パフォーマンス: +35%
- コード品質: +28%
- テストカバレッジ: +15%

🔄 **次回推奨開始位置**:
Issue #XXX Task Y (優先度P1)

📝 **特記事項**:
[問題や推奨事項]

【自走セッション完了】
```

この設計により、各エージェントは4-5時間の長期にわたって、安全かつ効率的に自走実行が可能になります。