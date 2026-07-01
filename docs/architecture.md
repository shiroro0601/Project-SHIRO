# Project SHIRO Version1.0 アーキテクチャ

## Project SHIROの目的

Project SHIROは、AI動画生成ツールからAI会社OSへ進化することを目的としたプロジェクトです。

Version0.8では、Stable Diffusion、VOICEVOX、FFmpegを使い、企画、脚本、演出、画像生成、音声生成、編集、品質確認をつなぐ動画生成ワークフローを構築しました。

Version0.9では、Brain、LLM抽象化、Job、Employee、Workflow、CompanyMemory、PlannerAI、ScriptWriterAI、DirectorAI、ArtistAIを追加し、AI社員が役割ごとに仕事を進める構造へ発展しました。

Version1.0では、単なる動画生成パイプラインではなく、複数のAI社員が仕事を分担し、状態を管理し、失敗から回復し、将来的には相談しながら業務を進めるAI会社OSを目指します。

## Version0.9までの構造

Version0.9までの基本構造は以下です。

```text
Workflow
  ↓
Employee
  ↓
Brain
  ↓
LLM
```

この構造により、Workflowが社員の実行順序を管理し、EmployeeがBrainを通してLLMへ問い合わせる流れが成立しました。

一方で、仕事そのものの状態、入力、出力、失敗理由、再実行単位を表す独立した層が不足していました。そのため、Version1.0ではTask層とProvider層を追加して、拡張しやすい会社OS構造へ進化させます。

## Version1.0で目指す構造

Version1.0の目標構造は以下です。

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

この構造では、各層が明確な責務を持ちます。上位層は業務の流れと判断に集中し、下位層は実行、解釈、外部AI接続を担当します。

## レイヤー構造と責務

### CEO

CEOは会社全体の目的、優先順位、最終判断を担う概念レイヤーです。

将来的には、Jobの目的設定、社員への依頼、成果物の承認、再実行判断を行う中心になります。

### Workflow Engine

Workflow Engineは、社員の実行順序と状態管理に集中します。

責務は以下です。

- Job全体の状態管理
- Step単位の状態管理
- 実行順序の制御
- エラー時の停止判断
- 将来的な条件分岐、並列実行、自動リトライへの拡張

Workflow EngineはLLMやProviderを直接呼びません。

### Employee

EmployeeはAI社員です。各社員はPlanner、ScriptWriter、Director、Artistなどの役割を持ちます。

責務は以下です。

- Jobの目的を読み取る
- 自分の担当範囲に応じたTaskを作成する
- Taskの結果をJobへ保存する
- 仕事の粒度を管理する

Employeeは管理職として振る舞い、LLMやProviderを直接呼びません。

### Task

Taskは仕事そのものを表す単位です。

責務は以下です。

- 仕事の種類を保持する
- 指示文を保持する
- 入力データを保持する
- 出力データを保持する
- Task状態を管理する
- 失敗理由を保持する

Taskを独立させることで、仕事の再実行、差し戻し、品質評価、履歴保存がしやすくなります。

### Brain

BrainはTaskを解釈し、LLMへ渡すための思考レイヤーです。

責務は以下です。

- Taskの内容を理解する
- 役割に応じたプロンプトを構築する
- Providerに依頼する
- LLMからの応答をTaskの出力として整える

BrainはEmployeeから直接文字列だけを受け取るのではなく、将来的にはTaskを中心に処理します。

### Provider

ProviderはOpenAI、Ollama、LM Studio、OpenRouterなどのLLM接続先を差し替えるための層です。

責務は以下です。

- 外部LLM APIまたはローカルLLMとの通信
- モデル差し替え
- 認証情報の扱い
- レスポンス形式の吸収
- エラーやタイムアウトの正規化

Providerを追加することで、BrainやEmployeeを変更せずにLLM接続先を切り替えられます。

### LLM

LLMは実際に推論を行うモデルです。

Project SHIRO本体はLLMそのものに依存せず、Providerを通して利用します。

## なぜTask層を追加するのか

Task層を追加する理由は以下です。

- 仕事の入力、出力、状態を一つの単位として扱うため
- Job全体ではなく、細かい仕事単位で失敗を記録するため
- 再実行や差し戻しをTask単位で行うため
- QualityCheckerAIが各Taskを採点しやすくするため
- 将来30人以上のAI社員に増えても、社員間の受け渡しを安定させるため

Taskがない場合、Employeeの戻り値やJob内部の生成物が混在しやすくなります。Task層は状態管理と生成物管理を分離するための重要な境界です。

## なぜProvider層を追加するのか

Provider層を追加する理由は以下です。

- OpenAI、Ollama、LM Studio、OpenRouterを差し替え可能にするため
- API仕様の違いをBrainより下の層で吸収するため
- LLM接続先の変更がEmployeeやWorkflowへ波及しないようにするため
- 将来的なコスト管理、レート制限、リトライ制御を集約するため

Provider層がない場合、各EmployeeやBrainに外部API固有の処理が散らばり、保守が難しくなります。

## WorkflowV2の責務

WorkflowV2はVersion1.0のWorkflow Engineです。

責務は以下です。

- WorkflowStepを順番に実行する
- Stepの開始、完了、失敗を記録する
- JobStatusを更新する
- StepStatusを更新する
- 失敗時に自動停止する
- Jobのhistoryへ実行履歴を残す

WorkflowV2は、Employeeの内部実装やLLM呼び出しには関与しません。

## Employeeの責務

Employeeは担当領域の仕事をTaskとして作成し、結果をJobへ反映します。

責務は以下です。

- 自分の役割に対応するTaskTypeを選ぶ
- TaskFactoryを通してTaskを作る
- Taskの入力をJobから組み立てる
- Taskの結果をJobへ保存する
- 必要に応じてBrainへTask実行を依頼する

EmployeeはProviderやLLMを直接呼びません。

## Brainの責務

BrainはTaskを実行可能な思考処理へ変換する層です。

責務は以下です。

- Task内容の解釈
- プロンプト作成
- Provider選択
- Providerへの問い合わせ
- 返答の整形
- Task出力への反映

BrainはLLMそのものではありません。BrainはProject SHIRO内の思考ルールを担当し、Providerは外部モデル接続を担当します。

## 30人以上のAI社員に拡張するための設計方針

将来、AI社員が30人以上に増えても破綻しないように、以下の方針を守ります。

- 社員ごとに責務を小さく分ける
- 社員間の受け渡しはJobとTaskを中心に行う
- Workflowは実行順序と状態管理に限定する
- EmployeeはTask作成と結果保存に限定する
- BrainとProviderを通してLLM接続を共通化する
- 新機能は既存Workflowを破壊せず、V2系または新規ファイルで追加する
- テストでTask lifecycleとWorkflow lifecycleを守る

## やってはいけない設計

以下の設計は禁止します。

- Employeeが直接LLM Providerを呼ぶ
- WorkflowがLLMを直接呼ぶ
- 生成物と状態管理が混在する
- 既存Workflowを破壊的変更する
- Jobに無秩序にキーを追加し、保存形式を曖昧にする
- Taskを使わずに社員間で巨大なdictだけを渡す
- Provider固有の処理をEmployeeへ書く
- テストなしでWorkflowやTaskの仕様を変える

Project SHIRO Version1.0では、会社OSとして長期的に拡張できることを優先します。