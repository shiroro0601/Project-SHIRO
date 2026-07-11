from pathlib import Path

import pytest

from company.runtime.real_video_runtime import (
    RealVideoPreflightChecker,
    RealVideoRuntimeConfig,
    VideoOutputValidator,
)


class FakeResponse:
    def __init__(self, payload=None):
        self.payload = payload or {}

    def raise_for_status(self):
        return None

    def json(self):
        return self.payload


def test_real_video_runtime_config_reads_environment():
    config = RealVideoRuntimeConfig.from_env(
        {
            "PROJECT_SHIRO_OLLAMA_BASE_URL": "http://ollama",
            "PROJECT_SHIRO_OLLAMA_MODEL": "test-model",
            "PROJECT_SHIRO_SD_BASE_URL": "http://sd",
            "PROJECT_SHIRO_VOICEVOX_BASE_URL": "http://voicevox",
            "PROJECT_SHIRO_VOICEVOX_SPEAKER_ID": "3",
            "PROJECT_SHIRO_OUTPUT_ROOT": "outputs/custom",
        }
    )

    assert config.ollama_base_url == "http://ollama"
    assert config.ollama_model == "test-model"
    assert config.stable_diffusion_base_url == "http://sd"
    assert config.voicevox_base_url == "http://voicevox"
    assert config.voicevox_speaker_id == 3
    assert Path(config.final_video_path).parts[-4:] == (
        "outputs",
        "custom",
        "videos",
        "final_video.mp4",
    )


def test_preflight_checks_ollama_model(monkeypatch):
    def fake_get(url, timeout):
        return FakeResponse({"models": [{"name": "llama3.2:3b"}]})

    monkeypatch.setattr("company.runtime.real_video_runtime.requests.get", fake_get)

    status = RealVideoPreflightChecker(RealVideoRuntimeConfig()).check_ollama()

    assert status.ok is True
    assert "llama3.2:3b" in status.message


def test_preflight_reports_missing_ollama_model(monkeypatch):
    def fake_get(url, timeout):
        return FakeResponse({"models": [{"name": "other"}]})

    monkeypatch.setattr("company.runtime.real_video_runtime.requests.get", fake_get)

    status = RealVideoPreflightChecker(RealVideoRuntimeConfig()).check_ollama()

    assert status.ok is False
    assert "ollama pull llama3.2:3b" in status.message


def test_preflight_ensure_ready_raises_for_failed_service(monkeypatch):
    def fake_get(url, timeout):
        if "/api/tags" in url:
            return FakeResponse({"models": [{"name": "llama3.2:3b"}]})
        raise RuntimeError("offline")

    monkeypatch.setattr("company.runtime.real_video_runtime.requests.get", fake_get)

    checker = RealVideoPreflightChecker(RealVideoRuntimeConfig())

    with pytest.raises(RuntimeError) as excinfo:
        checker.ensure_ready()

    assert "Stable Diffusion" in str(excinfo.value)
    assert "VOICEVOX" in str(excinfo.value)


def test_video_output_validator_accepts_nonempty_mp4(tmp_path):
    video_path = tmp_path / "final_video.mp4"
    video_path.write_bytes(b"mp4")

    validation = VideoOutputValidator().validate(str(video_path))

    assert validation["exists"] is True
    assert validation["is_file"] is True
    assert validation["size_bytes"] == 3
    assert validation["extension"] == ".mp4"


def test_video_output_validator_rejects_empty_or_missing_file(tmp_path):
    empty_video = tmp_path / "empty.mp4"
    empty_video.write_bytes(b"")

    validator = VideoOutputValidator()

    with pytest.raises(RuntimeError):
        validator.validate("")
    with pytest.raises(RuntimeError):
        validator.validate(str(tmp_path / "missing.mp4"))
    with pytest.raises(RuntimeError):
        validator.validate(str(empty_video))
    with pytest.raises(RuntimeError):
        validator.validate(str(Path(__file__)))


def test_video_output_validator_rejects_stale_mp4(tmp_path):
    video_path = tmp_path / "final_video.mp4"
    video_path.write_bytes(b"old mp4")

    with pytest.raises(RuntimeError):
        VideoOutputValidator().validate(
            str(video_path),
            created_after_ns=video_path.stat().st_mtime_ns + 1,
        )
