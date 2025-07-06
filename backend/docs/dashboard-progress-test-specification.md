# ダッシュボード・進捗管理機能テスト仕様書

**文書番号**: ITDO-ERP-DASH-TEST-001  
**バージョン**: 1.0  
**作成日**: 2025年7月6日  
**作成者**: Claude Code AI  
**承認者**: ootakazuhiko

---

## 1. 概要

### 1.1 目的
Phase 3-B（ダッシュボード・進捗管理機能）のテスト仕様を定義し、TDD（テスト駆動開発）アプローチでの実装を支援する。

### 1.2 対象機能
- ダッシュボード統計機能（DASH-001）
- 進捗管理機能（PROJ-005）
- リアルタイム更新機能（WebSocket）

### 1.3 テスト方針
- **テスト駆動開発（TDD）**: Red-Green-Refactor サイクル
- **カバレッジ**: 80%以上
- **テスト分類**: Unit, Integration, Security
- **多層テスト**: Model, Service, API レイヤー

---

## 2. テストケース一覧

### 2.1 ユニットテスト（Unit Tests）

#### 2.1.1 Dashboard Service Tests

**TestDashboardService**

| テストID | テスト名 | 説明 | 期待結果 |
|----------|----------|------|----------|
| DASH-U-001 | test_get_dashboard_stats_success | 正常な統計データ取得 | 統計データが正しく返される |
| DASH-U-002 | test_get_dashboard_stats_no_data | データが存在しない場合 | ゼロ値の統計データが返される |
| DASH-U-003 | test_get_dashboard_stats_organization_filter | 組織フィルタリング | 指定組織のデータのみ返される |
| DASH-U-004 | test_get_progress_data_success | 進捗データ取得成功 | 進捗データが正しく返される |
| DASH-U-005 | test_get_progress_data_period_filter | 期間フィルタリング | 指定期間のデータのみ返される |
| DASH-U-006 | test_get_alerts_success | アラート取得成功 | 期日アラートが正しく返される |
| DASH-U-007 | test_get_alerts_no_overdue | 遅延がない場合 | 空のアラートリストが返される |
| DASH-U-008 | test_calculate_project_progress | プロジェクト進捗計算 | 進捗率が正しく計算される |

#### 2.1.2 Progress Service Tests

**TestProgressService**

| テストID | テスト名 | 説明 | 期待結果 |
|----------|----------|------|----------|
| PROG-U-001 | test_calculate_task_completion_rate | タスク完了率計算 | 完了率が正しく計算される |
| PROG-U-002 | test_calculate_effort_completion_rate | 工数完了率計算 | 工数ベース完了率が正しく計算される |
| PROG-U-003 | test_calculate_duration_completion_rate | 期間完了率計算 | 期間ベース完了率が正しく計算される |
| PROG-U-004 | test_detect_overdue_projects | 期日遅れプロジェクト検出 | 遅延プロジェクトが正しく検出される |
| PROG-U-005 | test_detect_overdue_tasks | 期日遅れタスク検出 | 遅延タスクが正しく検出される |
| PROG-U-006 | test_detect_upcoming_deadlines | 期限間近検出 | 期限間近項目が正しく検出される |
| PROG-U-007 | test_generate_progress_report_json | JSONレポート生成 | JSON形式のレポートが生成される |
| PROG-U-008 | test_generate_progress_report_csv | CSVレポート生成 | CSV形式のレポートが生成される |

#### 2.1.3 Database View Tests

**TestDashboardViews**

| テストID | テスト名 | 説明 | 期待結果 |
|----------|----------|------|----------|
| VIEW-U-001 | test_dashboard_stats_view | 統計ビュー正常動作 | 統計データが正しく集計される |
| VIEW-U-002 | test_project_progress_view | 進捗ビュー正常動作 | 進捗データが正しく計算される |
| VIEW-U-003 | test_view_performance | ビューパフォーマンス | 200ms以下で実行完了 |
| VIEW-U-004 | test_view_data_consistency | データ整合性確認 | 実データと計算結果が一致 |

### 2.2 統合テスト（Integration Tests）

#### 2.2.1 Dashboard API Tests

**TestDashboardAPI**

| テストID | テスト名 | 説明 | 期待結果 |
|----------|----------|------|----------|
| DASH-I-001 | test_get_dashboard_stats_endpoint | 統計API正常呼び出し | 200レスポンス、正しいデータ |
| DASH-I-002 | test_get_dashboard_stats_unauthorized | 未認証アクセス | 401エラー |
| DASH-I-003 | test_get_dashboard_stats_organization_access | 組織アクセス制御 | 権限に応じたデータのみ |
| DASH-I-004 | test_get_progress_data_endpoint | 進捗API正常呼び出し | 200レスポンス、正しいデータ |
| DASH-I-005 | test_get_progress_data_period_param | 期間パラメータ指定 | 指定期間のデータが返される |
| DASH-I-006 | test_get_alerts_endpoint | アラートAPI正常呼び出し | 200レスポンス、アラートデータ |
| DASH-I-007 | test_api_response_time | API応答時間 | 200ms以下で応答 |

#### 2.2.2 Progress API Tests

**TestProgressAPI**

| テストID | テスト名 | 説明 | 期待結果 |
|----------|----------|------|----------|
| PROG-I-001 | test_get_project_progress_endpoint | プロジェクト進捗API | 200レスポンス、進捗データ |
| PROG-I-002 | test_get_project_progress_not_found | 存在しないプロジェクト | 404エラー |
| PROG-I-003 | test_get_project_progress_access_control | アクセス制御 | 権限チェック動作 |
| PROG-I-004 | test_generate_report_json_endpoint | JSONレポート生成API | JSON形式レポート |
| PROG-I-005 | test_generate_report_csv_endpoint | CSVレポート生成API | CSV形式レポート |
| PROG-I-006 | test_report_generation_time | レポート生成時間 | 500ms以下で生成 |

#### 2.2.3 WebSocket Tests

**TestWebSocketIntegration**

| テストID | テスト名 | 説明 | 期待結果 |
|----------|----------|------|----------|
| WS-I-001 | test_websocket_connection | WebSocket接続 | 接続成功 |
| WS-I-002 | test_websocket_authentication | WebSocket認証 | JWTトークンで認証 |
| WS-I-003 | test_websocket_unauthorized | 未認証WebSocket | 接続拒否 |
| WS-I-004 | test_project_update_broadcast | プロジェクト更新通知 | 更新がブロードキャスト |
| WS-I-005 | test_task_update_broadcast | タスク更新通知 | 更新がブロードキャスト |
| WS-I-006 | test_progress_update_broadcast | 進捗更新通知 | 進捗変更がブロードキャスト |
| WS-I-007 | test_websocket_organization_filter | 組織フィルタリング | 同組織のみ受信 |

### 2.3 セキュリティテスト（Security Tests）

#### 2.3.1 認証・認可テスト

**TestDashboardSecurity**

| テストID | テスト名 | 説明 | 期待結果 |
|----------|----------|------|----------|
| SEC-001 | test_dashboard_requires_authentication | 認証必須 | 未認証でアクセス拒否 |
| SEC-002 | test_dashboard_organization_isolation | 組織間データ分離 | 他組織データアクセス不可 |
| SEC-003 | test_dashboard_role_based_access | ロール別アクセス制御 | 権限に応じたアクセス |
| SEC-004 | test_websocket_jwt_validation | WebSocket JWT検証 | 不正トークン拒否 |
| SEC-005 | test_sql_injection_prevention | SQLインジェクション防止 | 悪意あるクエリ拒否 |
| SEC-006 | test_data_exposure_prevention | データ漏洩防止 | 不正データアクセス防止 |

#### 2.3.2 入力検証テスト

**TestInputValidation**

| テストID | テスト名 | 説明 | 期待結果 |
|----------|----------|------|----------|
| VAL-001 | test_invalid_organization_id | 不正組織ID | 400エラー |
| VAL-002 | test_invalid_period_parameter | 不正期間パラメータ | 400エラー |
| VAL-003 | test_invalid_project_id | 不正プロジェクトID | 400エラー |
| VAL-004 | test_malformed_request_body | 不正リクエストボディ | 422エラー |
| VAL-005 | test_oversized_request | 大きすぎるリクエスト | 413エラー |

### 2.4 パフォーマンステスト（Performance Tests）

#### 2.4.1 負荷テスト

**TestPerformance**

| テストID | テスト名 | 説明 | 期待結果 |
|----------|----------|------|----------|
| PERF-001 | test_dashboard_load_time | ダッシュボード読み込み時間 | 500ms以下 |
| PERF-002 | test_stats_calculation_time | 統計計算時間 | 200ms以下 |
| PERF-003 | test_concurrent_api_requests | 並行API要求処理 | 100並行処理可能 |
| PERF-004 | test_websocket_broadcast_latency | WebSocket通信遅延 | 100ms以下 |
| PERF-005 | test_large_dataset_handling | 大量データ処理 | 10000件まで処理可能 |

---

## 3. テストデータ

### 3.1 基本テストデータ

#### 3.1.1 組織データ
```python
test_organizations = [
    {"id": 1, "name": "テスト組織A", "code": "ORG-A"},
    {"id": 2, "name": "テスト組織B", "code": "ORG-B"},
    {"id": 3, "name": "テスト組織C", "code": "ORG-C"}
]
```

#### 3.1.2 プロジェクトデータ
```python
test_projects = [
    {
        "id": 1,
        "name": "プロジェクト1",
        "status": "in_progress",
        "start_date": "2025-06-01",
        "end_date": "2025-08-31",
        "organization_id": 1
    },
    {
        "id": 2,
        "name": "プロジェクト2",
        "status": "completed",
        "start_date": "2025-05-01",
        "end_date": "2025-07-01",
        "organization_id": 1
    },
    {
        "id": 3,
        "name": "遅延プロジェクト",
        "status": "in_progress",
        "start_date": "2025-05-01",
        "end_date": "2025-06-30",  # 期日過ぎ
        "organization_id": 1
    }
]
```

#### 3.1.3 タスクデータ
```python
test_tasks = [
    {
        "id": 1,
        "title": "タスク1",
        "status": "completed",
        "priority": "high",
        "project_id": 1,
        "estimated_hours": 8,
        "actual_hours": 6
    },
    {
        "id": 2,
        "title": "タスク2",
        "status": "in_progress",
        "priority": "medium",
        "project_id": 1,
        "estimated_hours": 16,
        "actual_hours": 8
    },
    {
        "id": 3,
        "title": "遅延タスク",
        "status": "in_progress",
        "priority": "high",
        "project_id": 1,
        "end_date": "2025-07-01",  # 期日過ぎ
        "estimated_hours": 12,
        "actual_hours": 2
    }
]
```

### 3.2 エッジケースデータ

#### 3.2.1 境界値テスト
```python
edge_case_data = {
    "empty_organization": {"projects": [], "tasks": []},
    "single_project": {"projects": [test_projects[0]], "tasks": []},
    "all_completed": {"status": "completed"},
    "all_overdue": {"end_date": "2025-06-01"},
    "large_dataset": {"count": 10000}
}
```

#### 3.2.2 セキュリティテスト用データ
```python
security_test_data = {
    "sql_injection": "'; DROP TABLE projects; --",
    "xss_payload": "<script>alert('xss')</script>",
    "invalid_jwt": "invalid.jwt.token",
    "expired_jwt": "expired.jwt.token",
    "malformed_json": "{'malformed': json}"
}
```

---

## 4. テスト環境

### 4.1 テスト環境設定

#### 4.1.1 データベース
- **テスト用DB**: SQLite（インメモリ）
- **マイグレーション**: 自動実行
- **テストデータ**: Fixture自動投入

#### 4.1.2 認証設定
- **テスト用JWT**: 有効期限1時間
- **テスト用ユーザー**: 各権限レベル用意
- **組織設定**: マルチテナント対応

### 4.2 テスト実行コマンド

#### 4.2.1 基本実行
```bash
# 全テスト実行
uv run pytest tests/test_dashboard_progress/

# ユニットテストのみ
uv run pytest tests/test_dashboard_progress/unit/

# 統合テストのみ
uv run pytest tests/test_dashboard_progress/integration/

# セキュリティテストのみ
uv run pytest tests/test_dashboard_progress/security/
```

#### 4.2.2 詳細実行
```bash
# カバレッジ付き実行
uv run pytest tests/test_dashboard_progress/ --cov=app --cov-report=html

# 詳細出力
uv run pytest tests/test_dashboard_progress/ -v -s

# 並列実行
uv run pytest tests/test_dashboard_progress/ -n auto
```

---

## 5. 品質基準

### 5.1 テストカバレッジ
- **最低基準**: 80%以上
- **目標**: 90%以上
- **測定対象**: app/services/dashboard.py, app/api/v1/dashboard.py

### 5.2 パフォーマンス基準
- **API応答時間**: 200ms以下
- **ダッシュボード読み込み**: 500ms以下
- **WebSocket通信遅延**: 100ms以下

### 5.3 セキュリティ基準
- **認証**: 全APIで必須
- **認可**: 組織レベルでデータ分離
- **入力検証**: 全パラメータで実施

---

## 6. テスト実行計画

### 6.1 Phase 5: TDD Red（テスト実装）

#### 6.1.1 実装順序
1. **モデル層テスト**: データベースビューテスト
2. **サービス層テスト**: DashboardService, ProgressService
3. **API層テスト**: REST API, WebSocket API
4. **統合テスト**: エンドツーエンド
5. **セキュリティテスト**: 認証・認可・入力検証

#### 6.1.2 テスト作成指針
- **Red**: 失敗するテストを先に作成
- **具体的**: 明確な期待値を設定
- **独立性**: テスト間の依存関係を排除
- **再現性**: 同じ結果が得られる

### 6.2 テスト実行チェックリスト

#### 6.2.1 実行前チェック
- [ ] テストデータベース準備完了
- [ ] テスト用JWT設定完了
- [ ] モックデータ準備完了
- [ ] 依存関係インストール完了

#### 6.2.2 実行後チェック
- [ ] 全テストパス
- [ ] カバレッジ80%以上
- [ ] パフォーマンス基準クリア
- [ ] セキュリティテストパス

---

## 7. 改訂履歴

| バージョン | 改訂日 | 改訂内容 | 改訂者 |
|------------|--------|----------|--------|
| 1.0 | 2025/07/06 | 初版作成 | Claude Code AI |

---

**承認**

プロジェクトオーナー: ootakazuhiko _________________ 日付: 2025/07/06  
Claude Code AI: _________________ 日付: 2025/07/06