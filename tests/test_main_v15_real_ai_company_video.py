import pytest

from company.runtime.service_health import ServiceStatus

import main_v15_real_ai_company_video as main_v15


class FakeProvider:
    def __init__(self):
        self.prompts = []

    def generate(self, prompt: str) -> str:
        self.prompts.append(prompt)
        if "リサーチャー" in prompt:
            return "猫は狭い場所に入る習性があります。"
        if "台本作家" in prompt:
            return (
                "【タイトル】\n"
                "猫の意外な雑学\n\n"
                "【シーン1】\n"
                "ナレーション: 猫は液体のように狭い場所へ入ります。\n"
                "画像: 箱に入る猫\n"
                "秒数: 3\n\n"
                "【シーン2】\n"
                "ナレーション: 猫のひげは通れる幅を測るセンサーです。\n"
                "画像: ひげが見える猫のアップ\n"
                "秒数: 4\n"
            )
        if "編集長" in prompt:
            return "【評価】\n分かりやすい台本です。\n\n【改善点】\nなし\n\n【判定】\n合格"
        return "unknown"


class FakeImageGenerator:
    def __init__(self):
        self.prompts = []

    def generate(self, prompt: str) -> str:
        self.prompts.append(prompt)
        return f"fake_image_{len(self.prompts)}.png"


class FakeVoiceGenerator:
    def __init__(self):
        self.texts = []

    def generate(self, text: str) -> str:
        self.texts.append(text)
        return f"fake_voice_{len(self.texts)}.wav"


class FakeSceneVideoComposer:
    def __init__(self):
        self.scene_assets = []
        self.output_path = None

    def compose(self, scene_assets, output_path: str) -> str:
        self.scene_assets = scene_assets
        self.output_path = output_path
        return "fake_final_video.mp4"


class FakePublisher:
    def generate(self, task):
        return {
            "status": "dry_run",
            "video_path": task.input_data["video_path"],
            "title": task.input_data["metadata"]["title"],
        }


class FakeServiceHealthChecker:
    def __init__(self, statuses):
        self.statuses = statuses
        self.check_all_calls = 0

    def check_all(self):
        self.check_all_calls += 1
        return self.statuses


class FakeReportWriter:
    def __init__(self):
        self.reports = []

    def write(self, report):
        self.reports.append(report)
        return "outputs/reports/fake_report.json"


class FakeMemory:
    def __init__(self):
        self.data = {"jobs": []}
        self.saved_data = []

    def load(self):
        return self.data

    def save(self, data):
        self.saved_data.append(data)
        self.data = data


class FakeMemoryContext:
    def __init__(self, prompt_text="過去の実行履歴:\n1. topic: 猫の意外な雑学"):
        self.prompt_text = prompt_text

    def to_prompt_text(self):
        return self.prompt_text


class FakeMemoryRetriever:
    def __init__(self, context=None):
        self.context = context or FakeMemoryContext()
        self.build_context_calls = []

    def build_context(self, limit=3):
        self.build_context_calls.append(limit)
        return self.context


def ok_statuses():
    return [
        ServiceStatus("Ollama", True, "ollama-url", "ok"),
        ServiceStatus("Stable Diffusion", True, "sd-url", "ok"),
        ServiceStatus("VOICEVOX", True, "voicevox-url", "ok"),
    ]


def ng_statuses():
    return [
        ServiceStatus("Ollama", True, "ollama-url", "ok"),
        ServiceStatus("Stable Diffusion", False, "sd-url", "not running"),
        ServiceStatus("VOICEVOX", True, "voicevox-url", "ok"),
    ]


def test_main_v15_importable():
    assert main_v15.DEFAULT_TOPIC == "猫の意外な雑学"


def test_build_company_accepts_dependency_injection():
    company = main_v15.build_company(
        provider=FakeProvider(),
        image_generator=FakeImageGenerator(),
        voice_generator=FakeVoiceGenerator(),
        scene_video_composer=FakeSceneVideoComposer(),
        publisher=FakePublisher(),
    )

    assert company is not None


def test_build_company_passes_memory_context_to_researcher_and_writer_only():
    memory_context = FakeMemoryContext()

    company = main_v15.build_company(
        provider=FakeProvider(),
        image_generator=FakeImageGenerator(),
        voice_generator=FakeVoiceGenerator(),
        scene_video_composer=FakeSceneVideoComposer(),
        publisher=FakePublisher(),
        memory_context=memory_context,
    )

    assert company.researcher.memory_context is memory_context
    assert company.writer.memory_context is memory_context
    assert not hasattr(company.reviewer, "memory_context")


def test_build_company_without_memory_context_keeps_roles_without_memory():
    company = main_v15.build_company(
        provider=FakeProvider(),
        image_generator=FakeImageGenerator(),
        voice_generator=FakeVoiceGenerator(),
        scene_video_composer=FakeSceneVideoComposer(),
        publisher=FakePublisher(),
    )

    assert company.researcher.memory_context is None
    assert company.writer.memory_context is None
    assert not hasattr(company.reviewer, "memory_context")


def test_parse_args_defaults_to_placeholder_mode():
    args = main_v15.parse_args([])

    assert args.real_media is False


def test_parse_args_accepts_real_media_mode():
    args = main_v15.parse_args(["--real-media"])

    assert args.real_media is True


def test_parse_args_accepts_check_services_mode():
    args = main_v15.parse_args(["--check-services"])

    assert args.check_services is True


def test_parse_args_accepts_no_report_mode():
    args = main_v15.parse_args(["--no-report"])

    assert args.no_report is True


def test_parse_args_accepts_save_memory_mode():
    args = main_v15.parse_args(["--save-memory"])

    assert args.save_memory is True


def test_parse_args_accepts_use_memory_mode():
    args = main_v15.parse_args(["--use-memory"])

    assert args.use_memory is True


def test_parse_args_accepts_memory_loop_mode():
    args = main_v15.parse_args(["--memory-loop"])

    assert args.memory_loop is True


def test_parse_args_accepts_quality_retries():
    args = main_v15.parse_args(["--quality-retries", "2"])

    assert args.quality_retries == 2


def test_parse_args_accepts_ceo_decision():
    args = main_v15.parse_args(["--ceo-decision"])

    assert args.ceo_decision is True


def test_parse_args_accepts_research_retries():
    args = main_v15.parse_args(["--research-retries", "1"])

    assert args.research_retries == 1


def test_parse_args_accepts_stop_on_ceo_stop():
    args = main_v15.parse_args(["--stop-on-ceo-stop"])

    assert args.stop_on_ceo_stop is True


def test_parse_args_accepts_human_approval():
    args = main_v15.parse_args(["--human-approval"])

    assert args.human_approval is True


def test_parse_args_accepts_approval_decision():
    args = main_v15.parse_args(
        [
            "--human-approval",
            "--approval-decision",
            "approved",
            "--approval-comment",
            "OK",
            "--approval-decided-by",
            "Koshi",
        ]
    )

    assert args.approval_decision == "approved"
    assert args.approval_comment == "OK"
    assert args.approval_decided_by == "Koshi"


def test_parse_args_research_retries_default_is_zero():
    args = main_v15.parse_args([])

    assert args.research_retries == 0


def test_parse_args_stop_on_ceo_stop_default_is_false():
    args = main_v15.parse_args([])

    assert args.stop_on_ceo_stop is False


def test_parse_args_human_approval_default_is_false():
    args = main_v15.parse_args([])

    assert args.human_approval is False


def test_parse_args_ceo_decision_default_is_false():
    args = main_v15.parse_args([])

    assert args.ceo_decision is False


def test_parse_args_quality_retries_default_is_zero():
    args = main_v15.parse_args([])

    assert args.quality_retries == 0


def test_count_run_reports_returns_zero_without_run_reports():
    memory = FakeMemory()

    assert main_v15.count_run_reports(memory) == 0


def test_count_run_reports_counts_existing_run_reports():
    memory = FakeMemory()
    memory.data["run_reports"] = [{"topic": "old1"}, {"topic": "old2"}]

    assert main_v15.count_run_reports(memory) == 2


def test_create_media_generators_defaults_to_placeholder_mode():
    image_generator, voice_generator = main_v15.create_media_generators(False)

    assert isinstance(image_generator, main_v15.PlaceholderImageGenerator)
    assert isinstance(voice_generator, main_v15.PlaceholderVoiceGenerator)


def test_build_company_real_media_with_fakes_does_not_require_external_services():
    company = main_v15.build_company(
        provider=FakeProvider(),
        image_generator=FakeImageGenerator(),
        voice_generator=FakeVoiceGenerator(),
        scene_video_composer=FakeSceneVideoComposer(),
        publisher=FakePublisher(),
        real_media=True,
    )

    assert company is not None


def test_build_company_passes_quality_retry_limit():
    company = main_v15.build_company(
        provider=FakeProvider(),
        image_generator=FakeImageGenerator(),
        voice_generator=FakeVoiceGenerator(),
        scene_video_composer=FakeSceneVideoComposer(),
        publisher=FakePublisher(),
        quality_retry_limit=2,
    )

    assert company.quality_retry_limit == 2


def test_build_company_accepts_ceo_decision_policy():
    policy = main_v15.CEODecisionPolicy()

    company = main_v15.build_company(
        provider=FakeProvider(),
        image_generator=FakeImageGenerator(),
        voice_generator=FakeVoiceGenerator(),
        scene_video_composer=FakeSceneVideoComposer(),
        publisher=FakePublisher(),
        ceo_decision_policy=policy,
    )

    assert company.ceo_decision_policy is policy


def test_build_company_passes_research_retry_limit():
    company = main_v15.build_company(
        provider=FakeProvider(),
        image_generator=FakeImageGenerator(),
        voice_generator=FakeVoiceGenerator(),
        scene_video_composer=FakeSceneVideoComposer(),
        publisher=FakePublisher(),
        research_retry_limit=1,
    )

    assert company.research_retry_limit == 1


def test_build_company_passes_stop_on_ceo_stop():
    company = main_v15.build_company(
        provider=FakeProvider(),
        image_generator=FakeImageGenerator(),
        voice_generator=FakeVoiceGenerator(),
        scene_video_composer=FakeSceneVideoComposer(),
        publisher=FakePublisher(),
        stop_on_ceo_stop=True,
    )

    assert company.stop_on_ceo_stop is True


def test_build_company_passes_human_approval_options():
    gate = main_v15.HumanApprovalGate(id_factory=lambda: "approval-1")

    company = main_v15.build_company(
        provider=FakeProvider(),
        image_generator=FakeImageGenerator(),
        voice_generator=FakeVoiceGenerator(),
        scene_video_composer=FakeSceneVideoComposer(),
        publisher=FakePublisher(),
        human_approval_gate=gate,
        require_human_approval_on_stop=True,
        approval_decision="approved",
        approval_decided_by="Koshi",
        approval_comment="OK",
    )

    assert company.human_approval_gate is gate
    assert company.require_human_approval_on_stop is True
    assert company.approval_decision == "approved"
    assert company.approval_decided_by == "Koshi"
    assert company.approval_comment == "OK"


def test_run_real_ai_company_video_with_fakes():
    provider = FakeProvider()
    image_generator = FakeImageGenerator()
    voice_generator = FakeVoiceGenerator()
    composer = FakeSceneVideoComposer()

    result = main_v15.run_real_ai_company_video(
        topic="猫の意外な雑学",
        provider=provider,
        image_generator=image_generator,
        voice_generator=voice_generator,
        scene_video_composer=composer,
        publisher=FakePublisher(),
        real_media=True,
        quality_retry_limit=1,
    )

    assert result["topic"] == "猫の意外な雑学"
    assert "research_result" in result
    assert "script_result" in result
    assert "review_result" in result
    assert result["script_artifact"].title == "猫の意外な雑学"
    assert len(result["scene_assets"]) == 2
    assert image_generator.prompts == [
        "箱に入る猫",
        "ひげが見える猫のアップ",
    ]
    assert voice_generator.texts == [
        "猫は液体のように狭い場所へ入ります。",
        "猫のひげは通れる幅を測るセンサーです。",
    ]
    assert composer.scene_assets == result["scene_assets"]
    assert result["scene_video_path"] == "fake_final_video.mp4"
    assert result["video_path"] == "fake_final_video.mp4"
    assert result["publish_result"]["status"] == "dry_run"
    assert result["quality_retry_count"] == 0


def test_check_services_mode_does_not_run_company(capsys):
    checker = FakeServiceHealthChecker(ok_statuses())

    main_v15.main(["--check-services"], service_health_checker=checker)

    captured = capsys.readouterr()
    assert checker.check_all_calls == 1
    assert "Project SHIRO Service Health Check" in captured.out
    assert "[OK] Ollama" in captured.out
    assert "media mode:" not in captured.out


def test_main_writes_report_by_default(monkeypatch, capsys):
    report_writer = FakeReportWriter()

    def fake_run_real_ai_company_video(topic, real_media=False):
        return {
            "topic": topic,
            "research_result": "research",
            "script_result": "script",
            "review_result": "review",
            "script_artifact": None,
            "scene_assets": [],
            "image_path": "image.png",
            "voice_path": "voice.wav",
            "scene_video_path": "video.mp4",
            "video_path": "video.mp4",
            "publish_result": {"status": "dry_run"},
        }

    monkeypatch.setattr(
        main_v15,
        "run_real_ai_company_video",
        fake_run_real_ai_company_video,
    )

    main_v15.main([], report_writer=report_writer)

    captured = capsys.readouterr()
    assert len(report_writer.reports) == 1
    assert report_writer.reports[0].topic == main_v15.DEFAULT_TOPIC
    assert "Run report: outputs/reports/fake_report.json" in captured.out


def test_main_no_report_skips_report_writer(monkeypatch, capsys):
    report_writer = FakeReportWriter()

    def fake_run_real_ai_company_video(topic, real_media=False):
        return {
            "topic": topic,
            "research_result": "research",
            "script_result": "script",
            "review_result": "review",
            "script_artifact": None,
            "scene_assets": [],
            "image_path": "image.png",
            "voice_path": "voice.wav",
            "scene_video_path": "video.mp4",
            "video_path": "video.mp4",
            "publish_result": {"status": "dry_run"},
        }

    monkeypatch.setattr(
        main_v15,
        "run_real_ai_company_video",
        fake_run_real_ai_company_video,
    )

    main_v15.main(["--no-report"], report_writer=report_writer)

    captured = capsys.readouterr()
    assert report_writer.reports == []
    assert "Run report:" not in captured.out


def test_main_save_memory_saves_memory_record(monkeypatch, capsys):
    memory = FakeMemory()

    def fake_run_real_ai_company_video(topic, real_media=False):
        return {
            "topic": topic,
            "research_result": "research",
            "script_result": "script",
            "review_result": "review",
            "script_artifact": None,
            "scene_assets": [],
            "image_path": "image.png",
            "voice_path": "voice.wav",
            "scene_video_path": "video.mp4",
            "video_path": "video.mp4",
            "publish_result": {"status": "dry_run"},
        }

    monkeypatch.setattr(
        main_v15,
        "run_real_ai_company_video",
        fake_run_real_ai_company_video,
    )

    main_v15.main(["--save-memory"], memory=memory)

    captured = capsys.readouterr()
    assert len(memory.saved_data) == 1
    assert memory.data["run_reports"][0]["type"] == "real_ai_company_run"
    assert memory.data["run_reports"][0]["topic"] == main_v15.DEFAULT_TOPIC
    assert "Memory saved: real_ai_company_run" in captured.out


def test_main_without_save_memory_does_not_touch_memory(monkeypatch):
    memory = FakeMemory()

    def fake_run_real_ai_company_video(topic, real_media=False):
        return {
            "topic": topic,
            "research_result": "research",
            "script_result": "script",
            "review_result": "review",
            "script_artifact": None,
            "scene_assets": [],
            "image_path": "image.png",
            "voice_path": "voice.wav",
            "scene_video_path": "video.mp4",
            "video_path": "video.mp4",
            "publish_result": {"status": "dry_run"},
        }

    monkeypatch.setattr(
        main_v15,
        "run_real_ai_company_video",
        fake_run_real_ai_company_video,
    )

    main_v15.main(["--no-report"], memory=memory)

    assert memory.saved_data == []


def test_main_no_report_and_save_memory_still_saves_memory(monkeypatch, capsys):
    memory = FakeMemory()
    report_writer = FakeReportWriter()

    def fake_run_real_ai_company_video(topic, real_media=False):
        return {
            "topic": topic,
            "research_result": "research",
            "script_result": "script",
            "review_result": "review",
            "script_artifact": None,
            "scene_assets": [],
            "image_path": "image.png",
            "voice_path": "voice.wav",
            "scene_video_path": "video.mp4",
            "video_path": "video.mp4",
            "publish_result": {"status": "dry_run"},
        }

    monkeypatch.setattr(
        main_v15,
        "run_real_ai_company_video",
        fake_run_real_ai_company_video,
    )

    main_v15.main(
        ["--no-report", "--save-memory"],
        report_writer=report_writer,
        memory=memory,
    )

    captured = capsys.readouterr()
    assert report_writer.reports == []
    assert len(memory.saved_data) == 1
    assert "Run report:" not in captured.out
    assert "Memory saved: real_ai_company_run" in captured.out


def test_main_use_memory_loads_and_prints_memory_context(monkeypatch, capsys):
    retriever = FakeMemoryRetriever()
    calls = []

    def fake_run_real_ai_company_video(
        topic,
        real_media=False,
        memory_context=None,
    ):
        calls.append(
            {
                "topic": topic,
                "real_media": real_media,
                "memory_context": memory_context,
            }
        )
        return {
            "topic": topic,
            "research_result": "research",
            "script_result": "script",
            "review_result": "review",
            "script_artifact": None,
            "scene_assets": [],
            "image_path": "image.png",
            "voice_path": "voice.wav",
            "scene_video_path": "video.mp4",
            "video_path": "video.mp4",
            "publish_result": {"status": "dry_run"},
        }

    monkeypatch.setattr(
        main_v15,
        "run_real_ai_company_video",
        fake_run_real_ai_company_video,
    )

    main_v15.main(["--use-memory", "--no-report"], memory_retriever=retriever)

    captured = capsys.readouterr()
    assert retriever.build_context_calls == [3]
    assert calls[0]["memory_context"] is retriever.context
    assert "Memory context:" in captured.out
    assert "1. topic: 猫の意外な雑学" in captured.out


def test_main_use_memory_and_save_memory_can_run_together(monkeypatch, capsys):
    memory = FakeMemory()
    retriever = FakeMemoryRetriever()
    calls = []

    def fake_run_real_ai_company_video(
        topic,
        real_media=False,
        memory_context=None,
    ):
        calls.append(memory_context)
        return {
            "topic": topic,
            "research_result": "research",
            "script_result": "script",
            "review_result": "review",
            "script_artifact": None,
            "scene_assets": [],
            "image_path": "image.png",
            "voice_path": "voice.wav",
            "scene_video_path": "video.mp4",
            "video_path": "video.mp4",
            "publish_result": {"status": "dry_run"},
        }

    monkeypatch.setattr(
        main_v15,
        "run_real_ai_company_video",
        fake_run_real_ai_company_video,
    )

    main_v15.main(
        ["--use-memory", "--save-memory", "--no-report"],
        memory=memory,
        memory_retriever=retriever,
    )

    captured = capsys.readouterr()
    assert retriever.build_context_calls == [3]
    assert calls == [retriever.context]
    assert len(memory.saved_data) == 1
    assert "Memory context:" in captured.out
    assert "Memory saved: real_ai_company_run" in captured.out


def test_main_save_memory_prints_memory_loop_status(monkeypatch, capsys):
    memory = FakeMemory()
    memory.data["run_reports"] = [{"topic": "old"}]

    def fake_run_real_ai_company_video(topic, real_media=False):
        return {
            "topic": topic,
            "research_result": "research",
            "script_result": "script",
            "review_result": (
                "【評価】\n"
                "分かりやすい台本です。\n\n"
                "【改善点】\n"
                "なし\n\n"
                "【判定】\n"
                "合格"
            ),
            "script_artifact": None,
            "scene_assets": [],
            "image_path": "image.png",
            "voice_path": "voice.wav",
            "scene_video_path": "video.mp4",
            "video_path": "video.mp4",
            "publish_result": {"status": "dry_run"},
        }

    monkeypatch.setattr(
        main_v15,
        "run_real_ai_company_video",
        fake_run_real_ai_company_video,
    )

    main_v15.main(["--save-memory", "--no-report"], memory=memory)

    captured = capsys.readouterr()
    assert "Memory loop:" in captured.out
    assert "- before run_reports: 1" in captured.out
    assert "- using memory context: no" in captured.out
    assert "- saved memory: yes" in captured.out
    assert "- after run_reports: 2" in captured.out
    assert "- saved summary:" in captured.out
    assert "- quality decision: 合格" in captured.out
    assert "- quality score: 1.0" in captured.out


def test_main_memory_loop_enables_use_memory_and_save_memory(monkeypatch, capsys):
    memory = FakeMemory()
    memory.data["run_reports"] = [{"topic": "old"}]
    retriever = FakeMemoryRetriever()
    calls = []

    def fake_run_real_ai_company_video(
        topic,
        real_media=False,
        memory_context=None,
    ):
        calls.append(memory_context)
        return {
            "topic": topic,
            "research_result": "research",
            "script_result": "script",
            "review_result": (
                "【評価】\n"
                "分かりやすい台本です。\n\n"
                "【改善点】\n"
                "冒頭の引きを強くする\n\n"
                "【判定】\n"
                "合格"
            ),
            "script_artifact": None,
            "scene_assets": [],
            "image_path": "image.png",
            "voice_path": "voice.wav",
            "scene_video_path": "video.mp4",
            "video_path": "video.mp4",
            "publish_result": {"status": "dry_run"},
        }

    monkeypatch.setattr(
        main_v15,
        "run_real_ai_company_video",
        fake_run_real_ai_company_video,
    )

    main_v15.main(
        ["--memory-loop", "--no-report"],
        memory=memory,
        memory_retriever=retriever,
    )

    captured = capsys.readouterr()
    assert retriever.build_context_calls == [3]
    assert calls == [retriever.context]
    assert len(memory.data["run_reports"]) == 2
    assert "Run report:" not in captured.out
    assert "Memory context:" in captured.out
    assert "Memory saved: real_ai_company_run" in captured.out
    assert "Memory loop:" in captured.out
    assert "- before run_reports: 1" in captured.out
    assert "- after run_reports: 2" in captured.out
    assert "- quality decision: 合格" in captured.out
    assert "- improvement points: 冒頭の引きを強くする" in captured.out


def test_main_passes_quality_retries_to_runner(monkeypatch, capsys):
    calls = []

    def fake_run_real_ai_company_video(
        topic,
        real_media=False,
        quality_retry_limit=0,
    ):
        calls.append(
            {
                "topic": topic,
                "real_media": real_media,
                "quality_retry_limit": quality_retry_limit,
            }
        )
        return {
            "topic": topic,
            "research_result": "research",
            "script_result": "script",
            "review_result": (
                "【評価】\n"
                "分かりやすい台本です。\n\n"
                "【改善点】\n"
                "なし\n\n"
                "【判定】\n"
                "合格"
            ),
            "quality_feedback": {
                "evaluation": "分かりやすい台本です。",
                "improvement_points": "なし",
                "decision": "合格",
                "score": 1.0,
            },
            "quality_retry_count": 1,
            "quality_retry_history": [],
            "script_artifact": None,
            "scene_assets": [],
            "image_path": "image.png",
            "voice_path": "voice.wav",
            "scene_video_path": "video.mp4",
            "video_path": "video.mp4",
            "publish_result": {"status": "dry_run"},
        }

    monkeypatch.setattr(
        main_v15,
        "run_real_ai_company_video",
        fake_run_real_ai_company_video,
    )

    main_v15.main(["--quality-retries", "2", "--no-report"])

    captured = capsys.readouterr()
    assert calls == [
        {
            "topic": main_v15.DEFAULT_TOPIC,
            "real_media": False,
            "quality_retry_limit": 2,
        }
    ]
    assert "Quality retry:" in captured.out
    assert "- limit: 2" in captured.out
    assert "- retries used: 1" in captured.out
    assert "- final decision: 合格" in captured.out


def test_main_passes_ceo_decision_policy_to_runner(monkeypatch, capsys):
    calls = []

    def fake_run_real_ai_company_video(
        topic,
        real_media=False,
        ceo_decision_policy=None,
    ):
        calls.append(ceo_decision_policy)
        return {
            "topic": topic,
            "research_result": "research",
            "script_result": "script",
            "review_result": "review",
            "quality_feedback": {
                "evaluation": "良い台本です。",
                "improvement_points": "なし",
                "decision": "合格",
                "score": 1.0,
            },
            "quality_retry_count": 0,
            "quality_retry_history": [],
            "ceo_decision": {
                "action": "proceed",
                "reason": "Reviewer approved the script.",
                "stage": "review",
                "quality_decision": "合格",
                "quality_score": 1.0,
                "retry_count": 0,
                "metadata": {},
            },
            "ceo_decision_history": [],
            "script_artifact": None,
            "scene_assets": [],
            "image_path": "image.png",
            "voice_path": "voice.wav",
            "scene_video_path": "video.mp4",
            "video_path": "video.mp4",
            "publish_result": {"status": "dry_run"},
        }

    monkeypatch.setattr(
        main_v15,
        "run_real_ai_company_video",
        fake_run_real_ai_company_video,
    )

    main_v15.main(["--ceo-decision", "--no-report"])

    captured = capsys.readouterr()
    assert isinstance(calls[0], main_v15.CEODecisionPolicy)
    assert "CEO decision:" in captured.out
    assert "- action: proceed" in captured.out
    assert "- quality decision: 合格" in captured.out


def test_main_can_combine_ceo_decision_and_quality_retries(monkeypatch):
    calls = []

    def fake_run_real_ai_company_video(
        topic,
        real_media=False,
        quality_retry_limit=0,
        ceo_decision_policy=None,
    ):
        calls.append(
            {
                "quality_retry_limit": quality_retry_limit,
                "ceo_decision_policy": ceo_decision_policy,
            }
        )
        return {
            "topic": topic,
            "research_result": "research",
            "script_result": "script",
            "review_result": "review",
            "quality_feedback": {},
            "quality_retry_count": 0,
            "quality_retry_history": [],
            "ceo_decision": None,
            "ceo_decision_history": [],
            "script_artifact": None,
            "scene_assets": [],
            "image_path": "image.png",
            "voice_path": "voice.wav",
            "scene_video_path": "video.mp4",
            "video_path": "video.mp4",
            "publish_result": {"status": "dry_run"},
        }

    monkeypatch.setattr(
        main_v15,
        "run_real_ai_company_video",
        fake_run_real_ai_company_video,
    )

    main_v15.main(["--ceo-decision", "--quality-retries", "2", "--no-report"])

    assert calls[0]["quality_retry_limit"] == 2
    assert isinstance(calls[0]["ceo_decision_policy"], main_v15.CEODecisionPolicy)


def test_main_passes_research_retries_to_runner(monkeypatch, capsys):
    calls = []

    def fake_run_real_ai_company_video(
        topic,
        real_media=False,
        research_retry_limit=0,
        ceo_decision_policy=None,
    ):
        calls.append(
            {
                "research_retry_limit": research_retry_limit,
                "ceo_decision_policy": ceo_decision_policy,
            }
        )
        return {
            "topic": topic,
            "research_result": "research",
            "script_result": "script",
            "review_result": "review",
            "quality_feedback": {},
            "quality_retry_count": 0,
            "quality_retry_history": [],
            "research_retry_count": 1,
            "research_retry_history": [],
            "ceo_decision": None,
            "ceo_decision_history": [],
            "script_artifact": None,
            "scene_assets": [],
            "image_path": "image.png",
            "voice_path": "voice.wav",
            "scene_video_path": "video.mp4",
            "video_path": "video.mp4",
            "publish_result": {"status": "dry_run"},
        }

    monkeypatch.setattr(
        main_v15,
        "run_real_ai_company_video",
        fake_run_real_ai_company_video,
    )

    main_v15.main(["--ceo-decision", "--research-retries", "1", "--no-report"])

    captured = capsys.readouterr()
    assert calls[0]["research_retry_limit"] == 1
    assert isinstance(calls[0]["ceo_decision_policy"], main_v15.CEODecisionPolicy)
    assert "Research retry:" in captured.out
    assert "- limit: 1" in captured.out
    assert "- retries used: 1" in captured.out
    assert "- final research available: yes" in captured.out


def test_main_warns_when_research_retries_without_ceo_decision(monkeypatch, capsys):
    calls = []

    def fake_run_real_ai_company_video(
        topic,
        real_media=False,
        research_retry_limit=0,
    ):
        calls.append(research_retry_limit)
        return {
            "topic": topic,
            "research_result": "research",
            "script_result": "script",
            "review_result": "review",
            "quality_feedback": {},
            "quality_retry_count": 0,
            "quality_retry_history": [],
            "research_retry_count": 0,
            "research_retry_history": [],
            "ceo_decision": None,
            "ceo_decision_history": [],
            "script_artifact": None,
            "scene_assets": [],
            "image_path": "image.png",
            "voice_path": "voice.wav",
            "scene_video_path": "video.mp4",
            "video_path": "video.mp4",
            "publish_result": {"status": "dry_run"},
        }

    monkeypatch.setattr(
        main_v15,
        "run_real_ai_company_video",
        fake_run_real_ai_company_video,
    )

    main_v15.main(["--research-retries", "1", "--no-report"])

    captured = capsys.readouterr()
    assert calls == [1]
    assert "Research retries require --ceo-decision" in captured.out


def test_main_can_combine_memory_loop_quality_and_research_retries(monkeypatch):
    memory = FakeMemory()
    retriever = FakeMemoryRetriever()
    calls = []

    def fake_run_real_ai_company_video(
        topic,
        real_media=False,
        memory_context=None,
        quality_retry_limit=0,
        research_retry_limit=0,
        ceo_decision_policy=None,
    ):
        calls.append(
            {
                "memory_context": memory_context,
                "quality_retry_limit": quality_retry_limit,
                "research_retry_limit": research_retry_limit,
                "ceo_decision_policy": ceo_decision_policy,
            }
        )
        return {
            "topic": topic,
            "research_result": "research",
            "script_result": "script",
            "review_result": "review",
            "quality_feedback": {},
            "quality_retry_count": 0,
            "quality_retry_history": [],
            "research_retry_count": 1,
            "research_retry_history": [],
            "ceo_decision": None,
            "ceo_decision_history": [],
            "script_artifact": None,
            "scene_assets": [],
            "image_path": "image.png",
            "voice_path": "voice.wav",
            "scene_video_path": "video.mp4",
            "video_path": "video.mp4",
            "publish_result": {"status": "dry_run"},
        }

    monkeypatch.setattr(
        main_v15,
        "run_real_ai_company_video",
        fake_run_real_ai_company_video,
    )

    main_v15.main(
        [
            "--memory-loop",
            "--ceo-decision",
            "--quality-retries",
            "2",
            "--research-retries",
            "1",
            "--no-report",
        ],
        memory=memory,
        memory_retriever=retriever,
    )

    assert calls[0]["memory_context"] is retriever.context
    assert calls[0]["quality_retry_limit"] == 2
    assert calls[0]["research_retry_limit"] == 1
    assert isinstance(calls[0]["ceo_decision_policy"], main_v15.CEODecisionPolicy)


def test_main_memory_loop_can_combine_with_quality_retries(monkeypatch):
    memory = FakeMemory()
    retriever = FakeMemoryRetriever()
    calls = []

    def fake_run_real_ai_company_video(
        topic,
        real_media=False,
        memory_context=None,
        quality_retry_limit=0,
    ):
        calls.append(
            {
                "memory_context": memory_context,
                "quality_retry_limit": quality_retry_limit,
            }
        )
        return {
            "topic": topic,
            "research_result": "research",
            "script_result": "script",
            "review_result": (
                "【評価】\n"
                "分かりやすい台本です。\n\n"
                "【改善点】\n"
                "なし\n\n"
                "【判定】\n"
                "合格"
            ),
            "quality_feedback": {
                "evaluation": "分かりやすい台本です。",
                "improvement_points": "なし",
                "decision": "合格",
                "score": 1.0,
            },
            "quality_retry_count": 1,
            "quality_retry_history": [],
            "script_artifact": None,
            "scene_assets": [],
            "image_path": "image.png",
            "voice_path": "voice.wav",
            "scene_video_path": "video.mp4",
            "video_path": "video.mp4",
            "publish_result": {"status": "dry_run"},
        }

    monkeypatch.setattr(
        main_v15,
        "run_real_ai_company_video",
        fake_run_real_ai_company_video,
    )

    main_v15.main(
        ["--memory-loop", "--quality-retries", "2", "--no-report"],
        memory=memory,
        memory_retriever=retriever,
    )

    assert calls == [
        {
            "memory_context": retriever.context,
            "quality_retry_limit": 2,
        }
    ]


def test_real_media_checks_services_before_running(monkeypatch):
    checker = FakeServiceHealthChecker(ok_statuses())
    calls = []

    def fake_run_real_ai_company_video(topic, real_media=False):
        calls.append({"topic": topic, "real_media": real_media})
        return {
            "topic": topic,
            "research_result": "research",
            "script_result": "script",
            "review_result": "review",
            "script_artifact": None,
            "scene_assets": [],
            "image_path": "image.png",
            "voice_path": "voice.wav",
            "scene_video_path": "video.mp4",
            "video_path": "video.mp4",
            "publish_result": {"status": "dry_run"},
        }

    monkeypatch.setattr(
        main_v15,
        "run_real_ai_company_video",
        fake_run_real_ai_company_video,
    )

    main_v15.main(["--real-media"], service_health_checker=checker)

    assert checker.check_all_calls == 1
    assert calls == [{"topic": main_v15.DEFAULT_TOPIC, "real_media": True}]


def test_real_media_service_ng_raises_runtime_error(monkeypatch):
    checker = FakeServiceHealthChecker(ng_statuses())

    def fail_if_called(*args, **kwargs):
        raise AssertionError("company run should not be called")

    monkeypatch.setattr(main_v15, "run_real_ai_company_video", fail_if_called)

    with pytest.raises(RuntimeError, match="Required local services are not ready"):
        main_v15.main(["--real-media"], service_health_checker=checker)

    assert checker.check_all_calls == 1


def test_main_passes_stop_on_ceo_stop_to_runner(monkeypatch, capsys):
    calls = []

    def fake_run_real_ai_company_video(
        topic,
        real_media=False,
        ceo_decision_policy=None,
        stop_on_ceo_stop=False,
    ):
        calls.append(
            {
                "ceo_decision_policy": ceo_decision_policy,
                "stop_on_ceo_stop": stop_on_ceo_stop,
            }
        )
        return {
            "topic": topic,
            "research_result": "research",
            "script_result": "script",
            "review_result": "review",
            "quality_feedback": {},
            "quality_retry_count": 0,
            "quality_retry_history": [],
            "research_retry_count": 0,
            "research_retry_history": [],
            "ceo_decision": {
                "action": "stop",
                "reason": "Retry limit reached.",
                "stage": "review",
            },
            "ceo_decision_history": [],
            "script_artifact": None,
            "scene_assets": [],
            "image_path": "",
            "voice_path": "",
            "scene_video_path": None,
            "video_path": "",
            "publish_result": None,
            "stopped": True,
            "stop_stage": "review",
            "stop_reason": "Retry limit reached.",
            "production_skipped": True,
        }

    monkeypatch.setattr(
        main_v15,
        "run_real_ai_company_video",
        fake_run_real_ai_company_video,
    )

    main_v15.main(["--ceo-decision", "--stop-on-ceo-stop", "--no-report"])

    captured = capsys.readouterr()
    assert isinstance(calls[0]["ceo_decision_policy"], main_v15.CEODecisionPolicy)
    assert calls[0]["stop_on_ceo_stop"] is True
    assert "CEO stop control:" in captured.out
    assert "- enabled: yes" in captured.out
    assert "- stopped: yes" in captured.out
    assert "- production skipped: yes" in captured.out


def test_main_warns_stop_on_ceo_stop_without_ceo_decision(monkeypatch, capsys):
    calls = []

    def fake_run_real_ai_company_video(
        topic,
        real_media=False,
        stop_on_ceo_stop=False,
    ):
        calls.append(stop_on_ceo_stop)
        return {
            "topic": topic,
            "research_result": "research",
            "script_result": "script",
            "review_result": "review",
            "quality_feedback": {},
            "quality_retry_count": 0,
            "quality_retry_history": [],
            "research_retry_count": 0,
            "research_retry_history": [],
            "ceo_decision": None,
            "ceo_decision_history": [],
            "script_artifact": None,
            "scene_assets": [],
            "image_path": "image.png",
            "voice_path": "voice.wav",
            "scene_video_path": "video.mp4",
            "video_path": "video.mp4",
            "publish_result": {"status": "dry_run"},
            "stopped": False,
            "stop_stage": None,
            "stop_reason": "",
            "production_skipped": False,
        }

    monkeypatch.setattr(
        main_v15,
        "run_real_ai_company_video",
        fake_run_real_ai_company_video,
    )

    main_v15.main(["--stop-on-ceo-stop", "--no-report"])

    captured = capsys.readouterr()
    assert calls == [True]
    assert "CEO stop control requires --ceo-decision" in captured.out


def test_main_saves_report_and_memory_when_stopped(monkeypatch):
    report_writer = FakeReportWriter()
    memory = FakeMemory()

    def fake_run_real_ai_company_video(
        topic,
        real_media=False,
        ceo_decision_policy=None,
        stop_on_ceo_stop=False,
    ):
        return {
            "topic": topic,
            "research_result": "research",
            "script_result": "script",
            "review_result": (
                "【評価】\n"
                "構成が弱いです。\n\n"
                "【改善点】\n"
                "冒頭を改善\n\n"
                "【判定】\n"
                "修正必要"
            ),
            "quality_feedback": {
                "evaluation": "構成が弱いです。",
                "improvement_points": "冒頭を改善",
                "decision": "修正必要",
                "score": 0.0,
            },
            "quality_retry_count": 0,
            "quality_retry_history": [],
            "research_retry_count": 0,
            "research_retry_history": [],
            "ceo_decision": {
                "action": "stop",
                "reason": "Retry limit reached.",
                "stage": "review",
            },
            "ceo_decision_history": [],
            "script_artifact": None,
            "scene_assets": [],
            "image_path": "",
            "voice_path": "",
            "scene_video_path": None,
            "video_path": "",
            "publish_result": None,
            "stopped": True,
            "stop_stage": "review",
            "stop_reason": "Retry limit reached.",
            "production_skipped": True,
        }

    monkeypatch.setattr(
        main_v15,
        "run_real_ai_company_video",
        fake_run_real_ai_company_video,
    )

    main_v15.main(
        ["--ceo-decision", "--stop-on-ceo-stop", "--save-memory"],
        report_writer=report_writer,
        memory=memory,
    )

    assert report_writer.reports[0].stopped is True
    assert report_writer.reports[0].production_skipped is True
    saved_record = memory.data["run_reports"][0]
    assert saved_record["stopped"] is True
    assert saved_record["stop_reason"] == "Retry limit reached."


def test_main_human_approval_enables_ceo_stop_and_gate(monkeypatch, capsys):
    calls = []

    def fake_run_real_ai_company_video(
        topic,
        real_media=False,
        ceo_decision_policy=None,
        stop_on_ceo_stop=False,
        human_approval_gate=None,
        require_human_approval_on_stop=False,
        approval_decision=None,
        approval_decided_by="human",
        approval_comment="",
    ):
        calls.append(
            {
                "ceo_decision_policy": ceo_decision_policy,
                "stop_on_ceo_stop": stop_on_ceo_stop,
                "human_approval_gate": human_approval_gate,
                "require_human_approval_on_stop": require_human_approval_on_stop,
                "approval_decision": approval_decision,
                "approval_decided_by": approval_decided_by,
                "approval_comment": approval_comment,
            }
        )
        return {
            "topic": topic,
            "research_result": "research",
            "script_result": "script",
            "review_result": "review",
            "quality_feedback": {},
            "quality_retry_count": 0,
            "quality_retry_history": [],
            "research_retry_count": 0,
            "research_retry_history": [],
            "ceo_decision": {"action": "stop", "reason": "Retry limit reached."},
            "ceo_decision_history": [],
            "script_artifact": None,
            "scene_assets": [],
            "image_path": "",
            "voice_path": "",
            "scene_video_path": None,
            "video_path": "",
            "publish_result": None,
            "stopped": True,
            "stop_stage": "review",
            "stop_reason": "Retry limit reached.",
            "production_skipped": True,
            "approval_required": True,
            "approval_request": {
                "approval_id": "approval-1",
                "status": "pending",
                "stage": "review",
                "reason": "Retry limit reached.",
            },
            "approval_status": "pending",
            "approval_decision": None,
        }

    monkeypatch.setattr(
        main_v15,
        "run_real_ai_company_video",
        fake_run_real_ai_company_video,
    )

    main_v15.main(["--human-approval", "--no-report"])

    captured = capsys.readouterr()
    assert isinstance(calls[0]["ceo_decision_policy"], main_v15.CEODecisionPolicy)
    assert calls[0]["stop_on_ceo_stop"] is True
    assert isinstance(calls[0]["human_approval_gate"], main_v15.HumanApprovalGate)
    assert calls[0]["require_human_approval_on_stop"] is True
    assert "Human approval:" in captured.out
    assert "- required: yes" in captured.out
    assert "- approval id: approval-1" in captured.out
    assert "- status: pending" in captured.out


def test_main_human_approval_can_record_approved_decision(monkeypatch, capsys):
    calls = []

    def fake_run_real_ai_company_video(
        topic,
        real_media=False,
        ceo_decision_policy=None,
        stop_on_ceo_stop=False,
        human_approval_gate=None,
        require_human_approval_on_stop=False,
        approval_decision=None,
        approval_decided_by="human",
        approval_comment="",
    ):
        calls.append(
            {
                "approval_decision": approval_decision,
                "approval_decided_by": approval_decided_by,
                "approval_comment": approval_comment,
            }
        )
        return {
            "topic": topic,
            "research_result": "research",
            "script_result": "script",
            "review_result": "review",
            "quality_feedback": {},
            "quality_retry_count": 0,
            "quality_retry_history": [],
            "research_retry_count": 0,
            "research_retry_history": [],
            "ceo_decision": {"action": "stop", "reason": "Retry limit reached."},
            "ceo_decision_history": [],
            "script_artifact": None,
            "scene_assets": [],
            "image_path": "",
            "voice_path": "",
            "scene_video_path": None,
            "video_path": "",
            "publish_result": None,
            "stopped": True,
            "stop_stage": "review",
            "stop_reason": "Retry limit reached.",
            "production_skipped": True,
            "approval_required": True,
            "approval_request": {
                "approval_id": "approval-1",
                "status": "approved",
                "stage": "review",
                "reason": "Retry limit reached.",
            },
            "approval_status": "approved",
            "approval_decision": {
                "decision": "approved",
                "decided_by": "Koshi",
                "comment": "OK",
            },
        }

    monkeypatch.setattr(
        main_v15,
        "run_real_ai_company_video",
        fake_run_real_ai_company_video,
    )

    main_v15.main(
        [
            "--human-approval",
            "--approval-decision",
            "approved",
            "--approval-decided-by",
            "Koshi",
            "--approval-comment",
            "OK",
            "--no-report",
        ]
    )

    captured = capsys.readouterr()
    assert calls[0] == {
        "approval_decision": "approved",
        "approval_decided_by": "Koshi",
        "approval_comment": "OK",
    }
    assert "- status: approved" in captured.out
    assert "- decision: approved" in captured.out
    assert "production resume is not implemented" in captured.out


def test_main_rejects_approval_decision_without_human_approval():
    with pytest.raises(ValueError, match="requires --human-approval"):
        main_v15.main(["--approval-decision", "approved", "--no-report"])
