# CHANGELOG

Project SHIROの主要な変更履歴を記録します。

## Version1.0

Project SHIROをAI動画生成ツールからAI会社OSへ進化させるためのバージョンです。

### Phase1-2

Added:
- Task
- TaskFactory
- Task lifecycle
- TaskStatus
- TaskType

Tests:
- `tests/test_task_factory.py`

### Phase1-1

Added:
- WorkflowV2
- JobStatus
- StepStatus
- WorkflowStep
- WorkflowStepResult
- WorkflowV2Result
- Job状態管理
- Step状態管理
- エラー処理
- 自動停止

Tests:
- `tests/test_workflow_v2_basic.py`

### Documentation Setup

Added:
- `docs/architecture.md`
- `docs/roadmap.md`
- `docs/development_rules.md`
- `CHANGELOG.md`
- `CONTRIBUTING.md`

## Version0.9

Added:
- Brain
- LLM abstraction
- Job
- Employee
- Workflow
- CompanyMemory
- PlannerAI
- ScriptWriterAI
- DirectorAI
- ArtistAI

Purpose:
- AI社員が役割ごとに仕事を進める基本構造を整備
- Workflow、Employee、Brain、LLMの流れを確立
- AI会社OSへ進化するための基礎を作成

## Version0.8

Added:
- Stable Diffusion integration
- VOICEVOX integration
- FFmpeg video generation workflow
- Planner
- ScriptWriter
- Director
- Artist
- VoiceActor
- Editor
- QualityChecker

Purpose:
- AIを使った動画生成ワークフローの基礎を構築
- 企画、脚本、演出、画像、音声、編集、品質確認の流れを作成

## 今後の予定

Planned:
- Employee → Task接続
- Brain V2
- Provider抽象化
- VoiceActorAIのVersion1.0対応
- VOICEVOX統合の整理
- EditorAIのVersion1.0対応
- FFmpeg統合の整理
- QualityCheckerAIによる100点満点採点
- 70点未満の自動差し戻し
- 社員チャット
- CompanyMemory強化
- OpenAI、Ollama、LM Studio、OpenRouterへの正式対応
