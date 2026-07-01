# Project SHIRO Version1.0 ロードマップ

Project SHIRO Version1.0は、AI動画生成ツールからAI会社OSへ進化するための開発ロードマップです。

各Phaseでは、目的、完了条件、注意点を明確にし、既存機能を壊さず段階的に拡張します。

## Phase1: AI会社OSの中核基盤

### 目的

Workflow、Task、Brain、Providerを整理し、AI社員が安全に拡張できる会社OSの中核を作ります。

### 実装項目

- Workflow V2
- Task層
- Employee → Task接続
- Brain V2
- Provider抽象化
- 条件分岐
- 並列実行
- 自動停止
- エラー処理
- Job状態管理

### 完了条件

- WorkflowV2がJobとStepの状態を管理できる
- Taskが仕事の入力、出力、状態、失敗理由を保持できる
- EmployeeがTaskFactoryを使ってTaskを作成できる
- Brain V2がTaskを解釈してProviderへ渡せる
- Providerを差し替えてもEmployeeとWorkflowに影響しない
- 条件分岐、並列実行、自動停止、エラー処理の基本テストが通る

### 注意点

- 既存Workflowは破壊的変更しない
- Version1.0拡張は原則V2系または新規ファイルで行う
- Employeeが直接LLMやProviderを呼ばない
- WorkflowがLLMやProviderを直接呼ばない

## Phase2: VoiceActorAIとVOICEVOX統合

### 目的

音声生成担当のVoiceActorAIをVersion1.0構造へ統合し、VOICEVOXをProviderまたは外部実行層として扱えるようにします。

### 実装項目

- VoiceActorAI
- VOICEVOX統合

### 完了条件

- VoiceActorAIが音声生成Taskを作成できる
- VOICEVOXに渡すテキスト、話者、速度などをTaskで管理できる
- 生成された音声ファイルの保存先がJob outputsに記録される
- テストで音声生成Taskのライフサイクルを確認できる

### 注意点

- 音声ファイルなどの生成物はGit管理しない
- VOICEVOXが起動していない環境でもテスト可能な設計にする
- 外部サービス依存部分はモック可能にする

## Phase3: EditorAIとFFmpeg統合

### 目的

画像、音声、字幕などの素材を統合し、EditorAIが動画編集Taskを扱えるようにします。

### 実装項目

- EditorAI
- FFmpeg統合

### 完了条件

- EditorAIが編集Taskを作成できる
- 入力素材と出力動画パスをTaskで管理できる
- FFmpeg実行結果をJob outputsに保存できる
- FFmpeg未導入環境でもテストが落ちないようにできる

### 注意点

- 生成動画はoutputs/に保存し、Git管理しない
- FFmpegの実行コマンドをEmployeeへ直接書きすぎない
- 将来的な編集テンプレート差し替えを考慮する

## Phase4: QualityCheckerAIによる品質評価

### 目的

完成物や中間成果物をQualityCheckerAIが採点し、改善点を提示できるようにします。

### 実装項目

- QualityCheckerAI
- 100点満点採点
- 改善案生成

### 完了条件

- QualityCheckerAIが品質チェックTaskを作成できる
- 成果物を100点満点で採点できる
- 改善案を構造化して出力できる
- Jobに品質評価履歴を保存できる

### 注意点

- 採点基準をコード内に散らばらせない
- 改善案は次Phaseの差し戻しに使える形式にする
- 主観評価だけでなく、チェック項目を明確にする

## Phase5: 自動リトライと差し戻し

### 目的

品質が低い成果物を自動で担当社員へ差し戻し、改善ループを作ります。

### 実装項目

- 自動リトライ
- QualityCheckerが70点未満なら担当社員へ差し戻し

### 完了条件

- QualityCheckerAIの評価点が閾値未満の場合、対象Taskを再実行できる
- リトライ回数の上限を管理できる
- 差し戻し理由をTaskまたはJob履歴に保存できる
- 無限ループを防止できる

### 注意点

- 自動リトライは必ず上限を持つ
- 差し戻し先を曖昧にしない
- 失敗履歴と改善履歴を分けて記録する

## Phase6: 社員チャット

### 目的

AI社員同士が相談しながら仕事を進められるようにし、単純な直列処理から協調型の会社OSへ進化させます。

### 実装項目

- 社員チャット
- AI社員同士が相談しながら仕事を進める

### 完了条件

- 社員間の会話履歴を保存できる
- 会話がJobやTaskに紐づく
- 相談結果をTaskの入力または出力として利用できる
- 不要な会話で処理が暴走しない

### 注意点

- 会話履歴と成果物を混在させない
- 社員チャットはWorkflow制御下で行う
- LLM呼び出し回数の増加に注意する

## Phase7: CompanyMemory強化

### 目的

会社としての記憶を強化し、過去の仕事、会話、失敗、改善、学習を次のJobへ活用できるようにします。

### 実装項目

- CompanyMemory強化
- Job履歴
- 会話履歴
- 失敗履歴
- 改善履歴
- 学習履歴

### 完了条件

- Job履歴を検索できる
- 会話履歴をJobとTaskに紐づけられる
- 失敗履歴と改善履歴を保存できる
- 学習履歴を次回のTask作成や品質改善に利用できる

### 注意点

- 個人情報やAPIキーをMemoryへ保存しない
- 履歴データの肥大化に注意する
- 保存形式を将来の検索に耐える形にする

## Phase8: LLM正式対応

### 目的

複数のLLM接続先を正式にサポートし、用途や環境に応じて切り替えられるようにします。

### 実装項目

- LLM正式対応
- OpenAI
- Ollama
- LM Studio
- OpenRouter

### 完了条件

- Provider抽象化を通して各LLMへ接続できる
- 同じTaskを複数Providerで実行できる
- APIキーや接続設定を安全に扱える
- Providerごとのエラーを共通形式へ変換できる

### 注意点

- APIキーをGit管理しない
- Provider固有処理をEmployeeへ書かない
- テストでは外部APIを直接呼ばない
- コスト、レート制限、タイムアウトを考慮する

## 開発の進め方

- 各Phaseは小さなPull Requestに分ける
- mainブランチは常に動く状態を維持する
- 既存テストが通ることを確認してから次へ進む
- 生成物はGit管理しない
- アーキテクチャの責務境界を守る
