# 🤖 ITDO_ERP2 エージェント協調ディレクトリ

## 📋 概要

このディレクトリは、ITDO_ERP2プロジェクトにおけるマルチエージェント協調システムのやりとりと記録を管理するために作成されました。

## 📂 ディレクトリ構造

```
docs/coordination/
├── README.md                           # このファイル
├── STATUS_REPORT_2025-07-17.md         # システム状況報告
├── CC03_BASH_ERROR_INVESTIGATION.md    # CC03エラー調査レポート
├── agent-communications/               # エージェント間通信記録
├── daily-reports/                      # 日次報告書
├── issue-processing/                   # Issue処理記録
└── system-status/                      # システム状態監視
```

## 🎯 目的

### 1. エージェント協調の透明性確保
- CC01 (フロントエンド)、CC02 (バックエンド)、CC03 (インフラ/テスト) 間の連携状況記録
- タスク分担と進捗状況の可視化
- 問題発生時の迅速な情報共有

### 2. 開発プロセスの文書化
- ラベルベース処理システムの運用記録
- GitHub Actions ワークフロー実行結果
- 品質基準達成状況の追跡

### 3. 問題解決とノウハウ蓄積
- エラー調査・対処法の記録
- 成功パターンの文書化
- 継続的改善のための知識ベース

## 🏷️ ファイル命名規則

### 状況報告書
```
STATUS_REPORT_YYYY-MM-DD.md
```

### エラー調査
```
[AGENT]_[ERROR_TYPE]_INVESTIGATION_YYYY-MM-DD.md
```

### 日次活動記録
```
DAILY_ACTIVITY_YYYY-MM-DD.md
```

### Issue処理記録
```
ISSUE_[NUMBER]_PROCESSING_RECORD.md
```

## 📊 記録対象

### エージェント活動
- 各エージェントの作業状況
- 処理したIssue数と成功率
- エラー発生と対処状況

### システム監視
- GitHub Actions ワークフロー実行状況
- ラベルベース処理システムの動作
- 品質ゲートの通過状況

### 協調活動
- エージェント間の作業分担
- 依存関係のある作業の調整
- 緊急事態時の連携対応

## 🔍 利用方法

### 開発チーム向け
1. 最新の `STATUS_REPORT_*.md` で全体状況確認
2. 問題発生時は該当エラー調査レポート確認
3. 日次報告で継続的な進捗把握

### エージェント向け
1. 作業開始前に最新状況報告確認
2. 問題発生時は調査レポート作成
3. 作業完了時は適切な記録更新

### プロジェクト管理向け
1. 週次・月次での進捗分析
2. 品質指標とパフォーマンス追跡
3. リソース配分の最適化判断

## 🚀 今後の拡張

### 自動化対応
- GitHub Actions による自動レポート生成
- エラー発生時の自動通知システム
- メトリクス収集とダッシュボード化

### 分析機能
- エージェント効率性分析
- 処理パターンの自動検出
- 予測分析とリスク評価

---

**維持管理責任**: Claude Code エージェント協調システム  
**更新頻度**: リアルタイム (重要な変更時)  
**保存期間**: プロジェクト完了まで継続