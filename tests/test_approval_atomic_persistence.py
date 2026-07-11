import json
import os

import pytest

from company.approval.approval_request_repository import (
    JsonApprovalRequestRepository,
)
from company.approval.exceptions import ApprovalPersistenceError
from company.approval.human_approval import ApprovalRequest


def make_request(approval_id="approval-1", topic="猫の意外な雑学"):
    return ApprovalRequest(
        approval_id=approval_id,
        status="pending",
        created_at="2026-07-11T10:00:00",
        topic=topic,
        stage="review",
        reason="Retry limit reached.",
        ceo_action="stop",
        quality_decision="修正必要",
        quality_score=0.0,
        script_result="script",
        review_result="review",
        metadata={"quality_retry_count": 1},
    )


def test_atomic_save_creates_official_json(tmp_path):
    path = tmp_path / "approval_requests.json"
    repository = JsonApprovalRequestRepository(str(path))

    repository.save(make_request())

    assert path.exists()
    assert json.loads(path.read_text(encoding="utf-8"))["approval_requests"]


def test_atomic_save_leaves_no_temp_file(tmp_path):
    path = tmp_path / "approval_requests.json"
    repository = JsonApprovalRequestRepository(str(path))

    repository.save(make_request())

    assert list(tmp_path.glob("*.tmp")) == []


def test_atomic_save_uses_os_replace(tmp_path, monkeypatch):
    path = tmp_path / "approval_requests.json"
    repository = JsonApprovalRequestRepository(str(path))
    calls = []
    real_replace = os.replace

    def fake_replace(source, destination):
        calls.append((source, destination))
        return real_replace(source, destination)

    monkeypatch.setattr(os, "replace", fake_replace)

    repository.save(make_request())

    assert calls
    assert calls[0][1] == str(path)


def test_write_failure_keeps_existing_json(tmp_path, monkeypatch):
    path = tmp_path / "approval_requests.json"
    repository = JsonApprovalRequestRepository(str(path))
    repository.save(make_request(topic="既存データ"))
    before = path.read_text(encoding="utf-8")

    def fail_payload(_payload):
        raise OSError("write failed")

    monkeypatch.setattr(repository, "_write_payload_atomically", fail_payload)

    with pytest.raises(ApprovalPersistenceError) as exc_info:
        repository.save(make_request(topic="新しいデータ"))

    assert isinstance(exc_info.value.__cause__, OSError)
    assert path.read_text(encoding="utf-8") == before


def test_replace_failure_keeps_existing_json_and_removes_temp(tmp_path, monkeypatch):
    path = tmp_path / "approval_requests.json"
    repository = JsonApprovalRequestRepository(str(path))
    repository.save(make_request(topic="既存データ"))
    before = path.read_text(encoding="utf-8")

    def fail_replace(_source, _destination):
        raise OSError("replace failed")

    monkeypatch.setattr(os, "replace", fail_replace)

    with pytest.raises(ApprovalPersistenceError) as exc_info:
        repository.save(make_request(topic="新しいデータ"))

    assert isinstance(exc_info.value.__cause__, OSError)
    assert path.read_text(encoding="utf-8") == before
    assert list(tmp_path.glob("*.tmp")) == []


def test_json_serialization_failure_is_wrapped(tmp_path):
    path = tmp_path / "approval_requests.json"
    repository = JsonApprovalRequestRepository(str(path))
    request = make_request()
    request.metadata = {"bad": object()}

    with pytest.raises(ApprovalPersistenceError) as exc_info:
        repository.save(request)

    assert isinstance(exc_info.value.__cause__, TypeError)


def test_atomic_save_preserves_japanese_data(tmp_path):
    path = tmp_path / "approval_requests.json"
    repository = JsonApprovalRequestRepository(str(path))

    repository.save(make_request(topic="猫の意外な雑学"))

    assert "猫の意外な雑学" in path.read_text(encoding="utf-8")


def test_multiple_atomic_saves_keep_valid_json(tmp_path):
    path = tmp_path / "approval_requests.json"
    repository = JsonApprovalRequestRepository(str(path))

    repository.save(make_request("approval-1"))
    repository.save(make_request("approval-2"))

    data = json.loads(path.read_text(encoding="utf-8"))
    assert [item["approval_id"] for item in data["approval_requests"]] == [
        "approval-1",
        "approval-2",
    ]


def test_repository_initialization_does_not_create_file(tmp_path):
    path = tmp_path / "approval_requests.json"

    JsonApprovalRequestRepository(str(path))

    assert not path.exists()
