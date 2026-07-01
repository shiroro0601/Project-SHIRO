# Project SHIRO 開発ルール

このドキュメントは、Project SHIROを安全に開発するための共通ルールです。

Project SHIROはAI動画生成ツールからAI会社OSへ進化するプロジェクトです。長期的に拡張できるよう、実装速度よりも既存機能を壊さないこと、責務境界を守ること、テストで確認することを優先します。

## 基本方針

- コードは完成版で実装する
- 部分修正禁止
- 既存機能を壊さない
- pytestを必ず実行する
- テストが通ってから次へ進む
- 保存先を明確にする
- アーキテクチャを優先する
- 保守性、拡張性、可読性、再利用性を重視する

## 既存コードの扱い

既存コードはProject SHIROの資産です。

変更前に必ず現在の構成と対象ファイルを確認します。目的と関係のないリファクタリング、命名変更、ディレクトリ移動、破壊的なAPI変更は行いません。

特に以下を守ります。

- 既存Workflowを破壊的変更しない
- Version1.0の拡張は原則として新規ファイルまたはV2系で行う
- 既存テストの前提を勝手に変えない
- 既存のJob保存形式を壊さない
- 既存Employeeの公開メソッドを不用意に変更しない

## アーキテクチャルール

Project SHIRO Version1.0の基本構造は以下です。

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

各層の責務を混ぜないことを最優先します。

### Workflow

Workflowは社員の実行順序と状態管理に集中します。

WorkflowがLLM、Provider、外部APIを直接呼ぶことは禁止です。

### Employee

EmployeeはTaskを作成し、Jobへ結果を保存する管理職として振る舞います。

Employeeが直接ProviderやLLMを呼ぶことは禁止です。

### Task

Taskは仕事の内容、入力、出力、状態、失敗理由を保持します。

生成物そのものと状態管理を混在させないようにします。

### Brain

BrainはTaskを解釈し、Providerへ渡す思考レイヤーです。

### Provider

ProviderはOpenAI、Ollama、LM Studio、OpenRouterなどの接続先差し替えを担当します。

Provider固有の処理をEmployeeやWorkflowへ書かないでください。

## 保存先ルール

保存先は目的ごとに明確にします。

- ソースコード: `company/`
- テスト: `tests/`
- ドキュメント: `docs/`
- 実行用サンプル: ルート直下の `main_*.py`
- 生成物: `outputs/`
- 一時ファイル: `temp/`

以下はGit管理しません。

- `outputs/`
- `temp/`
- `__pycache__/`
- `.pytest_cache/`
- 仮想環境
- ログファイル
- APIキーや秘密情報

## ブランチ運用

- `main` ブランチは常に動く状態にする
- 機能追加はfeatureブランチで行う
- ドキュメント追加も可能ならfeatureブランチで行う
- mainへ直接大きな変更を入れない

ブランチ名の例です。

- `feature/employee-task-integration`
- `feature/provider-abstraction`
- `feature/docs-setup`
- `fix/workflow-v2-error-handling`

## テストルール

変更後はpytestを実行します。

最低限、関連するテストを実行します。

```bash
python -m pytest tests/test_workflow_v2_basic.py
python -m pytest tests/test_task_factory.py
```

可能なら全体テストも実行します。

```bash
python -m pytest tests
```

テストが失敗した場合は、原因を特定して修正します。失敗したまま次の実装へ進みません。

外部API、VOICEVOX、FFmpeg、LLMなどに依存する処理は、テストで直接外部環境に依存しすぎないようにします。

## CHANGELOGルール

変更後は必要に応じて `CHANGELOG.md` を更新します。

記録する内容は以下です。

- 追加した機能
- 変更した仕様
- 修正した不具合
- 追加または更新したテスト
- 今後の注意点

## Codexが作業する場合のルール

CodexやAIエージェントが作業する場合は、以下を必ず守ります。

- 変更前に既存構成を確認する
- 変更対象ファイルを確認してから編集する
- 変更ファイルを明記する
- 勝手に設計変更しない
- 既存機能を壊さない
- 生成物や一時ファイルを編集対象にしない
- テスト失敗時は原因を特定して修正する
- 実行したコマンドを報告する
- pytestが環境制約で実行できない場合は正直に報告する

## 実装時のチェックリスト

実装前に確認します。

- 目的は明確か
- 既存コードの構造を確認したか
- 変更対象ファイルは最小限か
- アーキテクチャ責務に反していないか
- 保存先は正しいか

実装後に確認します。

- 既存テストが通るか
- 新しい仕様に必要なテストがあるか
- CHANGELOG.mdを更新したか
- 変更ファイルを説明できるか
- 生成物をGit管理に含めていないか

## 禁止事項

以下は禁止です。

- 部分修正のまま完了扱いにする
- テストせずに完了報告する
- Employeeから直接LLM Providerを呼ぶ
- Workflowから直接LLMを呼ぶ
- 生成物と状態管理を混在させる
- 既存Workflowを破壊的変更する
- APIキーや秘密情報をコミットする
- `outputs/` や `temp/` の生成物をコミットする
- unrelatedなリファクタリングを混ぜる
- mainブランチを壊す変更を直接入れる

Project SHIROでは、動くものを積み上げることを重視します。小さく作り、テストし、記録し、次へ進みます。
