import json

import pytest

from company.approval.approval_request_repository import (
    JsonApprovalRequestRepository,
)
from company.approval.exceptions import (
    ApprovalPersistenceError,
    ApprovalRequestDataError,
)
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


def test_repository_initialization_does_not_create_file(tmp_path):
    path = tmp_path / "approvals" / "approval_requests.json"

    JsonApprovalRequestRepository(str(path))

    assert not path.exists()


def test_repository_saves_from_missing_file(tmp_path):
    path = tmp_path / "approvals" / "approval_requests.json"
    repository = JsonApprovalRequestRepository(str(path))

    repository.save(make_request())

    assert path.exists()
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["schema_version"] == 1
    assert data["approval_requests"][0]["approval_id"] == "approval-1"


def test_repository_gets_saved_request_by_id(tmp_path):
    repository = JsonApprovalRequestRepository(
        str(tmp_path / "approval_requests.json")
    )

    repository.save(make_request(topic="猫の意外な雑学"))
    restored = repository.get("approval-1")

    assert restored is not None
    assert restored.approval_id == "approval-1"
    assert restored.topic == "猫の意外な雑学"
    assert restored.metadata["quality_retry_count"] == 1


def test_repository_saves_multiple_requests(tmp_path):
    repository = JsonApprovalRequestRepository(
        str(tmp_path / "approval_requests.json")
    )

    repository.save(make_request("approval-1"))
    repository.save(make_request("approval-2"))

    assert [request.approval_id for request in repository.list_all()] == [
        "approval-1",
        "approval-2",
    ]


def test_repository_overwrites_same_id_without_removing_others(tmp_path):
    repository = JsonApprovalRequestRepository(
        str(tmp_path / "approval_requests.json")
    )

    repository.save(make_request("approval-1", topic="古いテーマ"))
    repository.save(make_request("approval-2", topic="別テーマ"))
    updated = make_request("approval-1", topic="新しいテーマ")
    updated.status = "approved"
    repository.save(updated)

    restored = repository.get("approval-1")
    assert restored.topic == "新しいテーマ"
    assert restored.status == "approved"
    assert repository.get("approval-2").topic == "別テーマ"
    assert len(repository.list_all()) == 2


def test_repository_preserves_japanese_text(tmp_path):
    path = tmp_path / "approval_requests.json"
    repository = JsonApprovalRequestRepository(str(path))

    repository.save(make_request(topic="猫の意外な雑学"))

    saved_text = path.read_text(encoding="utf-8")
    assert "猫の意外な雑学" in saved_text


def test_repository_creates_output_directory_on_save(tmp_path):
    path = tmp_path / "nested" / "approvals" / "approval_requests.json"
    repository = JsonApprovalRequestRepository(str(path))

    repository.save(make_request())

    assert path.exists()


def test_repository_invalid_json_fails_clearly(tmp_path):
    path = tmp_path / "approval_requests.json"
    path.write_text("{ invalid json", encoding="utf-8")
    repository = JsonApprovalRequestRepository(str(path))

    with pytest.raises(ApprovalPersistenceError):
        repository.list_all()


def test_repository_missing_required_store_data_fails(tmp_path):
    path = tmp_path / "approval_requests.json"
    path.write_text("{}", encoding="utf-8")
    repository = JsonApprovalRequestRepository(str(path))

    with pytest.raises(ApprovalRequestDataError):
        repository.list_all()


def test_repository_missing_required_request_data_fails(tmp_path):
    path = tmp_path / "approval_requests.json"
    path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "approval_requests": [{"approval_id": "approval-1"}],
            }
        ),
        encoding="utf-8",
    )
    repository = JsonApprovalRequestRepository(str(path))

    with pytest.raises(ApprovalRequestDataError):
        repository.list_all()
