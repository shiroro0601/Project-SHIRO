from dataclasses import dataclass

import pytest

from company.artifacts.scene_asset import SceneAsset
from company.artifacts.script_artifact import ScriptArtifact
from company.artifacts.scene_artifact import SceneArtifact
from company.runtime.real_video_runtime import RealVideoRuntimeConfig
from main_v16_topic_to_real_video import run_topic_to_real_video


@dataclass
class FakeStatus:
    name: str = "Fake"
    ok: bool = True
    url: str = "fake://service"
    message: str = "ok"


class FakePreflightChecker:
    def __init__(self):
        self.called = False

    def ensure_ready(self):
        self.called = True
        return [FakeStatus()]


class FakeFactory:
    def __init__(self, video_path):
        self.video_path = video_path
        self.built = False

    def build(self):
        self.built = True
        return FakeCompany(self.video_path)

    def create_preflight_checker(self):
        return FakePreflightChecker()


class FakeCompany:
    def __init__(self, video_path):
        self.video_path = video_path

    def run(self, topic):
        self.video_path.write_bytes(b"fake mp4")
        script_artifact = ScriptArtifact(
            title="猫の意外な雑学",
            narration="猫の台本",
            image_prompts=["猫の画像"],
            scenes=[
                SceneArtifact(
                    index=1,
                    narration="猫のナレーション",
                    image_prompt="猫の画像",
                    duration_seconds=1.0,
                )
            ],
            raw_text="raw",
        )
        return {
            "topic": topic,
            "research_result": "research",
            "script_result": "script",
            "script_artifact": script_artifact,
            "review_result": "【評価】よい\n【改善点】なし\n【判定】\n合格",
            "scene_assets": [
                SceneAsset(
                    scene_index=1,
                    image_path="image.png",
                    voice_path="voice.wav",
                    narration="猫のナレーション",
                    image_prompt="猫の画像",
                    duration_seconds=1.0,
                )
            ],
            "image_path": "image.png",
            "voice_path": "voice.wav",
            "scene_video_path": str(self.video_path),
            "video_path": str(self.video_path),
            "publish_result": {"status": "dry_run"},
        }


class FakeMemory:
    def __init__(self):
        self.data = {"jobs": [], "run_reports": []}

    def load(self):
        return self.data

    def save(self, data):
        self.data = data


def test_run_topic_to_real_video_runs_factory_and_saves_report_and_memory(tmp_path):
    video_path = tmp_path / "final_video.mp4"
    checker = FakePreflightChecker()
    memory = FakeMemory()

    result = run_topic_to_real_video(
        "猫の意外な雑学",
        config=RealVideoRuntimeConfig(output_root=str(tmp_path)),
        factory=FakeFactory(video_path),
        preflight_checker=checker,
        memory=memory,
    )

    assert checker.called is True
    assert result["status"] == "completed"
    assert result["media_mode"] == "real media"
    assert result["video_path"] == str(video_path)
    assert result["video_validation"]["size_bytes"] == 8
    assert result["report_path"].endswith(".json")
    assert memory.data["run_reports"][0]["topic"] == "猫の意外な雑学"


def test_run_topic_to_real_video_can_skip_report_and_memory(tmp_path):
    video_path = tmp_path / "final_video.mp4"

    result = run_topic_to_real_video(
        "猫の意外な雑学",
        config=RealVideoRuntimeConfig(output_root=str(tmp_path)),
        factory=FakeFactory(video_path),
        run_preflight=False,
        save_report=False,
        save_memory=False,
    )

    assert result["preflight_statuses"] == []
    assert result["report_path"] is None
    assert result["memory_record"] is None


def test_run_topic_to_real_video_rejects_empty_topic(tmp_path):
    with pytest.raises(ValueError):
        run_topic_to_real_video(
            "",
            config=RealVideoRuntimeConfig(output_root=str(tmp_path)),
            factory=FakeFactory(tmp_path / "final_video.mp4"),
        )


def test_run_topic_to_real_video_raises_when_video_is_missing(tmp_path):
    class MissingVideoCompany(FakeCompany):
        def run(self, topic):
            result = super().run(topic)
            self.video_path.unlink()
            return result

    class MissingVideoFactory(FakeFactory):
        def build(self):
            return MissingVideoCompany(self.video_path)

    with pytest.raises(RuntimeError):
        run_topic_to_real_video(
            "猫の意外な雑学",
            config=RealVideoRuntimeConfig(output_root=str(tmp_path)),
            factory=MissingVideoFactory(tmp_path / "final_video.mp4"),
            run_preflight=False,
        )


def test_run_topic_to_real_video_removes_stale_default_video(tmp_path):
    stale_video = tmp_path / "videos" / "final_video.mp4"
    stale_video.parent.mkdir(parents=True)
    stale_video.write_bytes(b"stale")

    result = run_topic_to_real_video(
        "猫の意外な雑学",
        config=RealVideoRuntimeConfig(output_root=str(tmp_path)),
        factory=FakeFactory(stale_video),
        run_preflight=False,
        save_report=False,
        save_memory=False,
    )

    assert result["video_validation"]["size_bytes"] == 8
    assert stale_video.read_bytes() == b"fake mp4"
