from types import SimpleNamespace

import pytest

from company.artifacts.scene_artifact import SceneArtifact
from company.artifacts.script_artifact import ScriptArtifact
from company.reports.run_report_memory_adapter import RunReportMemoryAdapter
from company.runtime.project_shiro_youtube_orchestrator import (
    ProjectShiroStopPoint,
    ProjectShiroYouTubeOrchestrator,
    ProjectShiroYouTubeRunConfig,
    ProjectShiroYouTubeServices,
)
from company.youtube.studio_upload import (
    UploadPreparationResult,
    YouTubeMetadataPreparationResult,
    YouTubePrivateSaveResult,
    YouTubePrivateSaveVerificationResult,
    YouTubeStudioChannelIdentity,
)


class FakePreflight:
    def __init__(self, calls, fail=False):
        self.calls = calls
        self.fail = fail

    def ensure_ready(self):
        self.calls.append("preflight")
        if self.fail:
            raise RuntimeError("preflight down")


class FakeVideoPipeline:
    def __init__(self, calls, video_path, fail=False):
        self.calls = calls
        self.video_path = video_path
        self.fail = fail

    def run(self, topic):
        self.calls.append("video")
        if self.fail:
            raise RuntimeError("video failed")
        self.video_path.write_bytes(b"mp4")
        return {
            "topic": topic,
            "research_result": "research",
            "script_result": "script",
            "script_artifact": ScriptArtifact(
                title="猫の意外な雑学",
                narration="script",
                image_prompts=["cat"],
                scenes=[
                    SceneArtifact(
                        index=1,
                        narration="script",
                        image_prompt="cat",
                        duration_seconds=1.0,
                    )
                ],
                raw_text="script",
            ),
            "review_result": "【評価】OK\n【改善点】なし\n【判定】\n合格",
            "scene_assets": [],
            "image_path": "image.png",
            "voice_path": "voice.wav",
            "scene_video_path": str(self.video_path),
            "video_path": str(self.video_path),
        }


class FakeValidator:
    def __init__(self, calls, fail=False):
        self.calls = calls
        self.fail = fail

    def validate(self, video_path):
        self.calls.append("video_validation")
        if self.fail:
            raise RuntimeError("invalid mp4")
        return {"video_path": video_path, "size_bytes": 3}


class FakeIdentityReader:
    def __init__(self, calls, confirmed=True):
        self.calls = calls
        self.confirmed = confirmed

    def read_identity(self, expected_channel_name=""):
        self.calls.append("channel_identity")
        return YouTubeStudioChannelIdentity(
            channel_name=expected_channel_name,
            studio_available=True,
            identity_confirmed=self.confirmed,
            error="" if self.confirmed else "wrong channel",
        )


class FakeUploadPreparer:
    def __init__(self, calls, status="prepared"):
        self.calls = calls
        self.status = status
        self.browser = SimpleNamespace()

    def prepare_upload(self, video_path, keep_open=False):
        self.calls.append("upload_prepare")
        return UploadPreparationResult(
            status=self.status,
            video_path=video_path,
            filename="final_video.mp4",
            upload_started=self.status == "prepared",
            details_visible=self.status == "prepared",
            logged_in=True,
            current_url="https://studio.youtube.com/",
            error="" if self.status == "prepared" else self.status,
        )


class FakeMetadataPreparer:
    def __init__(self, calls, status="metadata_prepared"):
        self.calls = calls
        self.status = status

    def prepare_metadata(self, video_path, metadata, keep_open=False):
        self.calls.append("metadata_prepare")
        return YouTubeMetadataPreparationResult(
            status=self.status,
            video_path=video_path,
            title=metadata.title,
            description=metadata.description,
            made_for_kids=metadata.made_for_kids,
            tags=metadata.tags,
            title_applied=self.status == "metadata_prepared",
            description_applied=self.status == "metadata_prepared",
            audience_applied=self.status == "metadata_prepared",
            tags_applied=True,
            saved=False,
            published=False,
            error="" if self.status == "metadata_prepared" else self.status,
        )


class FakeSaveConfirmer:
    def __init__(self, calls, result=None):
        self.calls = calls
        self.result = result

    def save_private(self, video_path, metadata, policy, keep_open=False):
        self.calls.append("private_save")
        return self.result or YouTubePrivateSaveResult(
            status="private_saved",
            video_path=video_path,
            title=metadata.title,
            privacy_status="private",
            private_selected=True,
            save_clicked=True,
            saved=True,
            published=False,
            video_url="https://youtu.be/video123",
            studio_url="https://studio.youtube.com/video/video123/edit",
        )


class FakeVerifier:
    def __init__(self, calls, status="verified_private"):
        self.calls = calls
        self.status = status

    def verify(self, title):
        self.calls.append("verification")
        return YouTubePrivateSaveVerificationResult(
            status=self.status,
            found=self.status == "verified_private",
            title=title,
            title_matched=self.status == "verified_private",
            privacy_status="private" if self.status == "verified_private" else "",
            private_confirmed=self.status == "verified_private",
            duplicate_count=1 if self.status == "verified_private" else 0,
            video_url="https://youtu.be/video123" if self.status == "verified_private" else "",
            studio_url="https://studio.youtube.com/video/video123/edit"
            if self.status == "verified_private"
            else "",
            video_id="video123" if self.status == "verified_private" else "",
            checked_locations=("video", "short", "live", "draft"),
            error="" if self.status == "verified_private" else "not found",
        )


class FakeAttemptStore:
    def __init__(self, calls, fail=False):
        self.calls = calls
        self.fail = fail

    def ensure_save_allowed(self, smoke_id):
        self.calls.append(f"attempt:{smoke_id}")
        if self.fail:
            raise RuntimeError("duplicate")


class FakeReportWriter:
    def __init__(self):
        self.report = None

    def write(self, report):
        self.report = report
        return "fake_report.json"


class FakeMemory:
    def __init__(self):
        self.data = {"jobs": [], "run_reports": []}

    def load(self):
        return self.data

    def save(self, data):
        self.data = data


def config(**overrides):
    data = {
        "topic": "猫の意外な雑学",
        "made_for_kids": False,
        "save_report": False,
        "save_memory": False,
    }
    data.update(overrides)
    return ProjectShiroYouTubeRunConfig(**data)


def services_factory(calls, **overrides):
    disconnected = {"value": False}

    def factory(_config):
        calls.append("cdp_connection")
        browser = SimpleNamespace()
        return ProjectShiroYouTubeServices(
            browser=browser,
            identity_reader=overrides.get("identity_reader")
            or FakeIdentityReader(calls),
            upload_preparer=overrides.get("upload_preparer")
            or FakeUploadPreparer(calls),
            metadata_preparer=overrides.get("metadata_preparer")
            or FakeMetadataPreparer(calls),
            readiness_checker=SimpleNamespace(),
            private_save_confirmer=overrides.get("save_confirmer")
            or FakeSaveConfirmer(calls),
            verifier_factory=overrides.get("verifier_factory")
            or (lambda: FakeVerifier(calls)),
            disconnect=lambda: (calls.append("safe_disconnect"), disconnected.update(value=True)),
            attempt_store=overrides.get("attempt_store"),
        )

    factory.disconnected = disconnected
    return factory


def orchestrator(tmp_path, calls, **overrides):
    return ProjectShiroYouTubeOrchestrator(
        preflight_checker=overrides.get("preflight")
        if "preflight" in overrides
        else FakePreflight(calls),
        video_pipeline=overrides.get("video_pipeline")
        or FakeVideoPipeline(calls, tmp_path / "final_video.mp4"),
        video_validator=overrides.get("video_validator") or FakeValidator(calls),
        youtube_services_factory=overrides.get("youtube_services_factory")
        or services_factory(calls),
        report_writer=overrides.get("report_writer"),
        memory=overrides.get("memory"),
        memory_adapter=RunReportMemoryAdapter(),
    )


def test_default_stops_before_save_without_calling_save(tmp_path):
    calls = []

    result = orchestrator(tmp_path, calls).run(
        config(expected_channel_name="恋愛らぼっ‼")
    )

    assert result.status == "stopped_before_save"
    assert "private_save" not in calls
    assert result.saved is False
    assert result.published is False


def test_confirmed_private_save_verifies_with_disconnect(tmp_path):
    calls = []

    result = orchestrator(tmp_path, calls).run(
        config(
            expected_channel_name="恋愛らぼっ‼",
            confirm_private_save=True,
            smoke_id="unique-1",
            stop_point=ProjectShiroStopPoint.NONE,
        )
    )

    assert result.status == "private_verified"
    assert calls == [
        "preflight",
        "video",
        "video_validation",
        "cdp_connection",
        "channel_identity",
        "upload_prepare",
        "metadata_prepare",
        "private_save",
        "safe_disconnect",
        "verification",
    ]
    assert result.video_id == "video123"
    assert result.saved is True
    assert result.published is False


def test_stop_after_video_never_connects_to_cdp(tmp_path):
    calls = []

    result = orchestrator(tmp_path, calls).run(
        config(stop_point=ProjectShiroStopPoint.AFTER_VIDEO)
    )

    assert result.status == "video_completed"
    assert calls == ["preflight", "video", "video_validation"]


def test_existing_video_path_skips_video_pipeline(tmp_path):
    calls = []
    existing = tmp_path / "existing.mp4"
    existing.write_bytes(b"mp4")

    result = orchestrator(tmp_path, calls).run(
        config(
            existing_video_path=str(existing),
            stop_point=ProjectShiroStopPoint.AFTER_VIDEO,
        )
    )

    assert result.status == "video_completed"
    assert result.video_path == str(existing)
    assert "video" not in calls
    assert calls == ["preflight", "video_validation"]


def test_upload_failure_skips_metadata_and_save(tmp_path):
    calls = []
    factory = services_factory(calls, upload_preparer=FakeUploadPreparer(calls, "login_required"))

    result = orchestrator(tmp_path, calls, youtube_services_factory=factory).run(
        config(expected_channel_name="恋愛らぼっ‼")
    )

    assert result.status == "upload_prepare_failed"
    assert result.failure_stage == "upload_prepare"
    assert "metadata_prepare" not in calls
    assert "private_save" not in calls


def test_metadata_failure_skips_save(tmp_path):
    calls = []
    factory = services_factory(
        calls,
        metadata_preparer=FakeMetadataPreparer(calls, "title_apply_failed"),
    )

    result = orchestrator(tmp_path, calls, youtube_services_factory=factory).run(
        config(expected_channel_name="恋愛らぼっ‼")
    )

    assert result.status == "metadata_prepare_failed"
    assert result.failure_stage == "metadata_prepare"
    assert "private_save" not in calls


def test_channel_identity_failure_skips_upload(tmp_path):
    calls = []
    factory = services_factory(calls, identity_reader=FakeIdentityReader(calls, False))

    result = orchestrator(tmp_path, calls, youtube_services_factory=factory).run(
        config(expected_channel_name="恋愛らぼっ‼")
    )

    assert result.status == "channel_identity_failed"
    assert "upload_prepare" not in calls


def test_validation_failure_skips_cdp(tmp_path):
    calls = []

    result = orchestrator(
        tmp_path,
        calls,
        video_validator=FakeValidator(calls, fail=True),
    ).run(config())

    assert result.status == "video_validation_failed"
    assert "cdp_connection" not in calls


def test_voicevox_error_maps_to_voice_generation_stage(tmp_path):
    calls = []

    class VoiceFailingPipeline(FakeVideoPipeline):
        def run(self, topic):
            self.calls.append("video")
            raise RuntimeError(
                "VOICEVOXGenerator request failed: stage=synthesis; "
                "endpoint=http://127.0.0.1:50021/synthesis; timeout=60"
            )

    result = orchestrator(
        tmp_path,
        calls,
        video_pipeline=VoiceFailingPipeline(calls, tmp_path / "final_video.mp4"),
    ).run(config())

    assert result.status == "video_generation_failed"
    assert result.failure_stage == "voice_generation"
    assert "cdp_connection" not in calls


def test_cdp_failure_skips_upload(tmp_path):
    calls = []

    def failing_factory(_config):
        calls.append("cdp_connection")
        raise RuntimeError("cdp down")

    result = orchestrator(tmp_path, calls, youtube_services_factory=failing_factory).run(
        config(expected_channel_name="恋愛らぼっ‼")
    )

    assert result.status == "cdp_connection_failed"
    assert result.failure_stage == "cdp_connection"
    assert "upload_prepare" not in calls


def test_duplicate_guard_blocks_private_save(tmp_path):
    calls = []
    factory = services_factory(calls, attempt_store=FakeAttemptStore(calls, fail=True))

    result = orchestrator(tmp_path, calls, youtube_services_factory=factory).run(
        config(
            expected_channel_name="恋愛らぼっ‼",
            confirm_private_save=True,
            smoke_id="duplicate",
            stop_point=ProjectShiroStopPoint.NONE,
        )
    )

    assert result.status == "private_save_failed"
    assert "attempt:duplicate" in calls
    assert "private_save" not in calls


def test_save_unverified_does_not_mark_saved(tmp_path):
    calls = []
    factory = services_factory(
        calls,
        verifier_factory=lambda: FakeVerifier(calls, status="not_found"),
    )

    result = orchestrator(tmp_path, calls, youtube_services_factory=factory).run(
        config(
            expected_channel_name="恋愛らぼっ‼",
            confirm_private_save=True,
            smoke_id="unique-2",
            stop_point=ProjectShiroStopPoint.NONE,
        )
    )

    assert result.status == "save_unverified"
    assert result.save_clicked is True
    assert result.saved is False
    assert result.published is False


def test_run_report_and_memory_are_saved_for_safe_stop(tmp_path):
    calls = []
    writer = FakeReportWriter()
    memory = FakeMemory()

    result = orchestrator(
        tmp_path,
        calls,
        report_writer=writer,
        memory=memory,
    ).run(
        config(
            expected_channel_name="恋愛らぼっ‼",
            save_report=True,
            save_memory=True,
        )
    )

    assert result.run_report_path == "fake_report.json"
    assert writer.report.project_shiro_youtube_status == "stopped_before_save"
    assert memory.data["run_reports"][0]["project_shiro_youtube_status"] == "stopped_before_save"


def test_config_requires_explicit_audience():
    with pytest.raises(ValueError):
        ProjectShiroYouTubeRunConfig(topic="猫")


def test_config_requires_channel_and_smoke_id_for_confirm():
    with pytest.raises(ValueError):
        config(confirm_private_save=True, smoke_id="id")
    with pytest.raises(ValueError):
        config(confirm_private_save=True, expected_channel_name="恋愛らぼっ‼")
