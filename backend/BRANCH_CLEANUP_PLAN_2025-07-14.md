# Branch Cleanup Plan - 2025-07-14

## 現状分析

### ブランチ統計
- **総リモートブランチ数**: 29
- **マージ済みブランチ数**: 1
- **未マージブランチ数**: 28

### 問題点
1. 大量の未マージブランチが蓄積
2. 1つしかマージされていない（3.4%のマージ率）
3. PRマージ時の`--delete-branch`オプション未使用

## クリーンアップ戦略

### Phase 1: 即座に実行可能な作業
1. **マージ済みブランチの削除**
   ```bash
   git branch -r --merged origin/main | grep -v HEAD | grep -v main | xargs -I {} git push origin --delete {}
   ```

2. **古いPRのブランチ確認**
   - 30日以上更新されていないPR
   - CI失敗が継続しているPR
   - 作業が中断されているPR

### Phase 2: 段階的マージ計画
1. **優先順位付け**
   - 失敗数が少ないPRから対応
   - 機能の依存関係を考慮
   - 影響範囲が小さいものから

2. **マージ手順の確立**
   ```bash
   # 必須: マージ時にブランチ削除
   gh pr merge [PR] --squash --delete-branch
   ```

### Phase 3: 予防策
1. **GitHub設定変更**
   - Repository Settings → General → Pull Requests
   - ✅ "Automatically delete head branches" を有効化

2. **チーム規約**
   - PRマージ後は必ずブランチ削除
   - 長期間更新されないPRは定期的にレビュー
   - WIPブランチは明確にラベル付け

## 実行計画

### 今週中に実施
1. PR #141 マージ（CI通過後）
2. PR #118 修正とマージ
3. PR #139 調査と対応

### 来週の目標
- 未マージブランチを20以下に削減
- 自動削除設定の有効化
- チーム向けガイドライン作成

## 成功指標
- マージ率を50%以上に向上
- 30日以上古いブランチをゼロに
- 新規PRは全て自動削除設定で処理

---
🤖 Generated with [Claude Code](https://claude.ai/code)