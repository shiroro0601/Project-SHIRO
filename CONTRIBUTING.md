# CONTRIBUTING

Project SHIROへの開発参加ルールです。

Project SHIROは、AI動画生成ツールからAI会社OSへ進化するプロジェクトです。長く安全に開発を続けるため、既存機能を壊さず、責務境界を守り、テストで確認してから変更を取り込みます。

## 開発の基本方針

- 既存機能を壊さない
- mainブランチを常に動く状態に保つ
- 変更は小さく、目的を明確にする
- アーキテクチャを勝手に変更しない
- 必要なファイルは完成版として実装する
- 部分修正のまま完了扱いにしない
- テストが通ってからPull Requestを出す

## ブランチ運用

mainブランチへ直接大きな変更を入れません。

作業内容ごとにfeatureブランチまたはfixブランチを作成します。

例:

```text
feature/docs-setup
feature/employee-task-integration
feature/provider-abstraction
fix/workflow-v2-error-handling
```

ドキュメントのみの変更でも、可能なら専用ブランチで作業します。

## コミットメッセージ方針

コミットメッセージは、何を変更したか分かる短い英語または日本語で書きます。

例:

```text
docs: add architecture overview
feature: add employee task integration
fix: handle workflow v2 step failure
```

推奨プレフィックス:

- `docs:` ドキュメント変更
- `feature:` 機能追加
- `fix:` 不具合修正
- `test:` テスト追加、修正
- `refactor:` 仕様を変えない整理
- `chore:` 開発環境や補助的な変更

## テスト実行方法

最低限、関連するテストを実行します。

```bash
python -m pytest tests/test_workflow_v2_basic.py
python -m pytest tests/test_task_factory.py
```

可能なら全体テストも実行します。

```bash
python -m pytest tests
```

テストが失敗した場合は、原因を確認して修正します。失敗したままPull Requestを出す場合は、理由と再現方法を明記してください。

## 新機能追加時の手順

1. 既存構成を確認する
2. 対象の責務がどの層に属するか確認する
3. featureブランチを作成する
4. 必要最小限のファイルを変更する
5. テストを追加または更新する
6. pytestを実行する
7. CHANGELOG.mdを更新する
8. Pull Requestを作成する

Version1.0の基本構造は以下です。

```text
CEO
  ↓
Workflow Engine
  ↓
Employee
  ↓
Task
  ↓
Brain
  ↓
Provider
  ↓
LLM
```

この責務境界を守って実装してください。

## Codexに依頼する場合の手順

CodexやAIエージェントに作業を依頼する場合は、以下を伝えてください。

- 作業目的
- 変更してよいファイル
- 変更してはいけないファイル
- 実行すべきテスト
- 期待する最終報告形式

Codexには以下を必ず守らせます。

- 変更前に既存構成を確認する
- 既存コードを読んでから編集する
- 既存機能を壊さない
- 勝手にアーキテクチャを変更しない
- 生成物を編集対象にしない
- 変更ファイルを明記する
- 実行したコマンドとテスト結果を報告する
- pytestが環境制約で実行できない場合は正直に報告する

## Pull Request前チェックリスト

Pull Requestを出す前に確認してください。

- 目的が明確か
- 変更ファイルが必要最小限か
- 既存Workflowを破壊していないか
- Employeeが直接ProviderやLLMを呼んでいないか
- Workflowが直接LLMを呼んでいないか
- Task、Brain、Providerの責務が混在していないか
- pytestを実行したか
- テスト結果をPR本文に書いたか
- CHANGELOG.mdを更新したか
- 生成物をコミットしていないか

## 禁止事項

以下は禁止です。

- mainブランチへ直接破壊的変更を入れる
- テストを実行せずに完了扱いにする
- 既存Workflowを破壊的変更する
- Employeeが直接LLM Providerを呼ぶ
- Workflowが直接LLMやProviderを呼ぶ
- 生成物と状態管理を混在させる
- `outputs/`、`temp/`、`__pycache__/`、`.pytest_cache/` をコミットする
- APIキーや秘密情報をコミットする
- 作業目的と無関係なリファクタリングを混ぜる
- 失敗したテストを放置する

Project SHIROは段階的に成長させます。小さく変更し、テストし、記録してから次へ進みます。
