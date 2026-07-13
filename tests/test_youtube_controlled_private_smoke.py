import json

import pytest

from company.youtube.studio_upload import (
    YouTubeControlledPrivateSaveRunner,
    YouTubePrivateSaveEvidence,
    YouTubePrivateSaveAttempt,
    YouTubePrivateSaveAttemptStore,
    YouTubePrivateSaveResult,
    YouTubePrivateSaveVerificationResult,
    YouTubeStudioChannelIdentity,
    YouTubeStudioChannelIdentityReader,
    YouTubeVideoMetadata,
)


class FakeIdentityBrowser:
    def __init__(self, channel_name="恋愛らぼっ！", current_url=None):
        self.channel_name = channel_name
        self.current_url = current_url or "https://studio.youtube.com/channel/UC123"
        self.actions = []

    def open(self, url):
        self.actions.append(("open", url))
        self.current_url = self.current_url or url

    def read_channel_name(self):
        self.actions.append(("read_channel_name",))
        return self.channel_name


class FakePrivateSaveConfirmer:
    def __init__(self, result=None):
        self.calls = []
        self.result = result or YouTubePrivateSaveResult(
            status="private_saved",
            video_path="video.mp4",
            title="",
            privacy_status="private",
            private_selected=True,
            save_clicked=True,
            saved=True,
            published=False,
            evidence=YouTubePrivateSaveEvidence(
                private_checked_before_click=True,
                upload_complete_before_click=True,
                save_button_enabled=True,
                save_button_exact_label="保存",
                save_button_label="保存",
                save_click_dispatched=True,
                click_dispatched=True,
                dialog_closed=True,
                post_click_dialog_closed=True,
                post_click_video_id="private-video",
                post_click_video_link="https://youtu.be/private-video",
                post_click_private_visibility_detected=True,
                completion_evidence_count=2,
                completion_confirmed=True,
            ),
        )

    def save_private(self, video_path, metadata, policy, keep_open=False):
        self.calls.append((video_path, metadata, policy, keep_open))
        self.result.title = metadata.title
        self.result.video_path = video_path
        return self.result


class FailingPrivateSaveConfirmer:
    def __init__(self, error):
        self.calls = []
        self.error = error

    def save_private(self, video_path, metadata, policy, keep_open=False):
        self.calls.append((video_path, metadata, policy, keep_open))
        raise RuntimeError(self.error)


class FakeVerifier:
    def __init__(self, result=None):
        self.titles = []
        self.result = result or YouTubePrivateSaveVerificationResult(
            status="verified_private",
            found=True,
            title="",
            title_matched=True,
            privacy_status="private",
            private_confirmed=True,
            duplicate_count=1,
            video_id="abc123",
            video_url="https://www.youtube.com/watch?v=abc123",
            studio_url="https://studio.youtube.com/video/abc123/edit",
            content_type="video",
        )

    def verify(self, title):
        self.titles.append(title)
        self.result.title = title
        return self.result


class FailingVerifier:
    def __init__(self, error):
        self.titles = []
        self.error = error

    def verify(self, title):
        self.titles.append(title)
        raise RuntimeError(self.error)


class FakeIdentityReader:
    def __init__(self, identity=None):
        self.expected = []
        self.identity = identity or YouTubeStudioChannelIdentity(
            channel_name="恋愛らぼっ！",
            channel_id="UC123",
            current_url="https://studio.youtube.com/channel/UC123",
            studio_available=True,
            identity_confirmed=True,
        )

    def read_identity(self, expected_channel_name=""):
        self.expected.append(expected_channel_name)
        return self.identity


def metadata():
    return YouTubeVideoMetadata(
        title="",
        description="Project SHIROのPrivate保存確認動画です。",
        made_for_kids=False,
        tags=("ProjectSHIRO",),
    )


def runner(tmp_path, **kwargs):
    return YouTubeControlledPrivateSaveRunner(
        private_save_confirmer=kwargs.get("confirmer", FakePrivateSaveConfirmer()),
        verifier=kwargs.get("verifier", FakeVerifier()),
        identity_reader=kwargs.get("identity_reader", FakeIdentityReader()),
        attempt_store=kwargs.get(
            "attempt_store",
            YouTubePrivateSaveAttemptStore(tmp_path / "private_save_attempts.json"),
        ),
        post_save_disconnect=kwargs.get("post_save_disconnect"),
        clock=lambda: "2026-07-13T10:00:00",
    )


def test_channel_identity_reads_name_and_channel_id_without_cookie_access():
    browser = FakeIdentityBrowser()

    result = YouTubeStudioChannelIdentityReader(browser=browser).read_identity(
        "恋愛らぼっ！"
    )

    assert result.channel_name == "恋愛らぼっ！"
    assert result.channel_id == "UC123"
    assert result.identity_confirmed is True
    assert not any("cookie" in str(action).lower() for action in browser.actions)


def test_channel_mismatch_blocks_save(tmp_path):
    video = tmp_path / "video.mp4"
    video.write_bytes(b"mp4")
    identity_reader = FakeIdentityReader(
        YouTubeStudioChannelIdentity(
            channel_name="別チャンネル",
            current_url="https://studio.youtube.com/channel/UC123",
            studio_available=True,
            identity_confirmed=False,
            error="channel_mismatch",
        )
    )
    confirmer = FakePrivateSaveConfirmer()

    result = runner(
        tmp_path,
        identity_reader=identity_reader,
        confirmer=confirmer,
    ).run(str(video), metadata(), "20260713-001", "恋愛らぼっ！", True)

    assert result.status == "channel_mismatch"
    assert result.save_clicked is False
    assert confirmer.calls == []


def test_identity_unknown_blocks_save(tmp_path):
    video = tmp_path / "video.mp4"
    video.write_bytes(b"mp4")
    result = runner(
        tmp_path,
        identity_reader=FakeIdentityReader(
            YouTubeStudioChannelIdentity(error="identity_unverified")
        ),
    ).run(str(video), metadata(), "20260713-001", "恋愛らぼっ！", True)

    assert result.status == "identity_unverified"
    assert result.save_clicked is False


def test_attempt_store_initialization_does_not_create_file(tmp_path):
    path = tmp_path / "private_save_attempts.json"
    YouTubePrivateSaveAttemptStore(path)

    assert not path.exists()


def test_attempt_store_allows_unused_smoke_id_and_blocks_saved_smoke_id(tmp_path):
    path = tmp_path / "private_save_attempts.json"
    store = YouTubePrivateSaveAttemptStore(path)

    store.ensure_save_allowed("new")
    store.save(
        YouTubePrivateSaveAttempt(
            smoke_id="used",
            title="title",
            video_path="video.mp4",
            video_size=3,
            attempted_at="now",
            save_clicked=True,
        )
    )

    with pytest.raises(ValueError, match="duplicate_save_blocked"):
        store.ensure_save_allowed("used")


def test_attempt_store_uses_atomic_temp_then_replace(tmp_path):
    path = tmp_path / "private_save_attempts.json"
    store = YouTubePrivateSaveAttemptStore(path)

    store.save(
        YouTubePrivateSaveAttempt(
            smoke_id="20260713-001",
            title="title",
            video_path="video.mp4",
            video_size=3,
            attempted_at="now",
        )
    )

    assert path.exists()
    assert list(tmp_path.glob("*.tmp")) == []
    assert json.loads(path.read_text(encoding="utf-8"))["attempts"][0]["smoke_id"]


def test_controlled_private_save_reuses_existing_steps_and_verifies(tmp_path):
    video = tmp_path / "video.mp4"
    video.write_bytes(b"mp4")
    confirmer = FakePrivateSaveConfirmer()
    verifier = FakeVerifier()
    store = YouTubePrivateSaveAttemptStore(tmp_path / "private_save_attempts.json")

    result = runner(
        tmp_path,
        confirmer=confirmer,
        verifier=verifier,
        attempt_store=store,
    ).run(str(video), metadata(), "20260713-001", "恋愛らぼっ！", True)

    assert result.status == "verified_private"
    assert result.title == "Project SHIRO Private Smoke 20260713-001"
    assert result.title != "Project SHIRO Private Smoke Test"
    assert result.private_selected is True
    assert result.save_clicked is True
    assert result.saved is True
    assert result.published is False
    assert result.privacy_status == "private"
    assert result.duplicate_count == 1
    assert result.video_id == "abc123"
    assert len(confirmer.calls) == 1
    assert confirmer.calls[0][2].confirm_private_save is True
    assert verifier.titles == ["Project SHIRO Private Smoke 20260713-001"]
    saved_attempt = store.get("20260713-001")
    assert saved_attempt.save_clicked is True
    assert saved_attempt.save_click_status == "dispatched"
    assert saved_attempt.save_completion_status == "confirmed"
    assert saved_attempt.upload_readiness_status == "ready"
    assert saved_attempt.upload_complete_before_save is True
    assert saved_attempt.blocking_error is False
    assert saved_attempt.save_button_label == "保存"
    assert saved_attempt.save_response_status == "confirmed"
    assert saved_attempt.completion_evidence["completion_confirmed"] is True
    assert saved_attempt.post_save_video_id == "private-video"
    assert saved_attempt.post_save_private_confirmed is True
    assert saved_attempt.verification_status == "verified_private"
    assert saved_attempt.video_id == "abc123"


def test_duplicate_count_other_than_one_fails_without_resave(tmp_path):
    video = tmp_path / "video.mp4"
    video.write_bytes(b"mp4")
    verifier = FakeVerifier(
        YouTubePrivateSaveVerificationResult(
            status="duplicate_candidates",
            found=True,
            title="title",
            title_matched=True,
            privacy_status="private",
            private_confirmed=True,
            duplicate_count=2,
            video_id="abc123",
            video_url="https://www.youtube.com/watch?v=abc123",
            studio_url="https://studio.youtube.com/video/abc123/edit",
        )
    )

    result = runner(tmp_path, verifier=verifier).run(
        str(video), metadata(), "20260713-002", "恋愛らぼっ！", True
    )

    assert result.status == "save_unverified"
    assert result.save_clicked is True
    assert result.saved is False


def test_not_found_after_save_does_not_allow_second_save(tmp_path):
    video = tmp_path / "video.mp4"
    video.write_bytes(b"mp4")
    store = YouTubePrivateSaveAttemptStore(tmp_path / "private_save_attempts.json")
    verifier = FakeVerifier(
        YouTubePrivateSaveVerificationResult(
            status="not_found",
            found=False,
            title="title",
            title_matched=False,
            privacy_status="",
            private_confirmed=False,
            duplicate_count=0,
        )
    )
    controlled = runner(tmp_path, verifier=verifier, attempt_store=store)

    first = controlled.run(str(video), metadata(), "20260713-003", "恋愛らぼっ！", True)
    second = controlled.run(str(video), metadata(), "20260713-003", "恋愛らぼっ！", True)

    assert first.status == "save_unverified"
    assert second.status == "duplicate_save_blocked"


def test_confirmation_flag_required_before_save(tmp_path):
    video = tmp_path / "video.mp4"
    video.write_bytes(b"mp4")
    confirmer = FakePrivateSaveConfirmer()

    result = runner(tmp_path, confirmer=confirmer).run(
        str(video), metadata(), "20260713-004", "恋愛らぼっ！", False
    )

    assert result.status == "confirmation_required"
    assert confirmer.calls == []


def test_cdp_connection_failure_keeps_attempt_save_clicked_false(tmp_path):
    video = tmp_path / "video.mp4"
    video.write_bytes(b"mp4")
    store = YouTubePrivateSaveAttemptStore(tmp_path / "private_save_attempts.json")

    result = runner(
        tmp_path,
        confirmer=FailingPrivateSaveConfirmer("cdp_connection_failed"),
        attempt_store=store,
    ).run(str(video), metadata(), "20260713-005", "恋愛らぼっ！", True)

    attempt = store.get("20260713-005")
    assert result.status == "cdp_connection_failed"
    assert result.save_clicked is False
    assert result.saved is False
    assert attempt.save_clicked is False
    assert attempt.save_click_status == "failed"
    assert attempt.save_completion_status == "failed"
    assert attempt.last_error == "cdp_connection_failed"
    assert attempt.verification_status == ""


def test_private_selection_failure_keeps_attempt_save_clicked_false(tmp_path):
    video = tmp_path / "video.mp4"
    video.write_bytes(b"mp4")
    store = YouTubePrivateSaveAttemptStore(tmp_path / "private_save_attempts.json")
    confirmer = FakePrivateSaveConfirmer(
        YouTubePrivateSaveResult(
            status="private_selection_failed",
            video_path="video.mp4",
            title="",
            privacy_status="private",
            private_selected=False,
            save_clicked=False,
            saved=False,
            published=False,
        )
    )

    result = runner(tmp_path, confirmer=confirmer, attempt_store=store).run(
        str(video), metadata(), "20260713-006", "恋愛らぼっ！", True
    )

    attempt = store.get("20260713-006")
    assert result.status == "private_selection_failed"
    assert result.private_selected is False
    assert result.save_clicked is False
    assert attempt.save_clicked is False
    assert attempt.save_click_status == "failed"
    assert attempt.save_completion_status == "failed"


def test_verifier_failure_keeps_save_clicked_true_but_saved_false(tmp_path):
    video = tmp_path / "video.mp4"
    video.write_bytes(b"mp4")
    store = YouTubePrivateSaveAttemptStore(tmp_path / "private_save_attempts.json")
    verifier = FakeVerifier(
        YouTubePrivateSaveVerificationResult(
            status="not_found",
            found=False,
            title="title",
            title_matched=False,
            privacy_status="",
            private_confirmed=False,
            duplicate_count=0,
        )
    )

    result = runner(tmp_path, verifier=verifier, attempt_store=store).run(
        str(video), metadata(), "20260713-007", "恋愛らぼっ！", True
    )

    attempt = store.get("20260713-007")
    assert result.status == "save_unverified"
    assert result.save_clicked is True
    assert result.saved is False
    assert attempt.save_clicked is True
    assert attempt.save_click_status == "dispatched"
    assert attempt.save_completion_status == "confirmed"
    assert attempt.verification_status == "not_found"


def test_verifier_exception_after_save_becomes_save_unverified(tmp_path):
    video = tmp_path / "video.mp4"
    video.write_bytes(b"mp4")
    store = YouTubePrivateSaveAttemptStore(tmp_path / "private_save_attempts.json")

    result = runner(
        tmp_path,
        verifier=FailingVerifier("cdp_connection_failed"),
        attempt_store=store,
    ).run(str(video), metadata(), "20260713-008", "恋愛らぼっ！", True)

    attempt = store.get("20260713-008")
    assert result.status == "save_unverified"
    assert result.save_clicked is True
    assert result.saved is False
    assert result.error == "cdp_connection_failed"
    assert attempt.save_clicked is True
    assert attempt.save_click_status == "dispatched"
    assert attempt.save_completion_status == "confirmed"
    assert attempt.verification_status == "cdp_connection_failed"


def test_post_save_disconnect_runs_before_verifier(tmp_path):
    video = tmp_path / "video.mp4"
    video.write_bytes(b"mp4")
    events = []

    class OrderedVerifier(FakeVerifier):
        def verify(self, title):
            events.append("verify")
            return super().verify(title)

    result = runner(
        tmp_path,
        verifier=OrderedVerifier(),
        post_save_disconnect=lambda: events.append("disconnect"),
    ).run(str(video), metadata(), "20260713-009", "恋愛らぼっ！", True)

    assert result.status == "verified_private"
    assert events == ["disconnect", "verify"]
