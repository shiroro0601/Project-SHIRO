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


def test_parse_args_defaults_to_placeholder_mode():
    args = main_v15.parse_args([])

    assert args.real_media is False


def test_parse_args_accepts_real_media_mode():
    args = main_v15.parse_args(["--real-media"])

    assert args.real_media is True


def test_parse_args_accepts_check_services_mode():
    args = main_v15.parse_args(["--check-services"])

    assert args.check_services is True


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


def test_check_services_mode_does_not_run_company(capsys):
    checker = FakeServiceHealthChecker(ok_statuses())

    main_v15.main(["--check-services"], service_health_checker=checker)

    captured = capsys.readouterr()
    assert checker.check_all_calls == 1
    assert "Project SHIRO Service Health Check" in captured.out
    assert "[OK] Ollama" in captured.out
    assert "media mode:" not in captured.out


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
