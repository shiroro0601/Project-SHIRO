import pytest

from company.approval.approval_request_repository import (
    JsonApprovalRequestRepository,
)
from company.approval.exceptions import ApprovalRequestNotFoundError
from company.approval.human_approval import HumanApprovalGate


def make_repository(tmp_path):
    return JsonApprovalRequestRepository(str(tmp_path / "approval_requests.json"))


def make_gate(repository=None):
    values = iter(["approval-1"])
    times = iter(
        [
            "2026-07-11T10:00:00",
            "2026-07-11T10:01:00",
            "2026-07-11T10:02:00",
        ]
    )
    return HumanApprovalGate(
        id_factory=lambda: next(values),
        clock=lambda: next(times),
        repository=repository,
    )


def create_request(gate):
    return gate.create_request(
        topic="猫の意外な雑学",
        stage="review",
        reason="Retry limit reached.",
        ceo_action="stop",
        quality_feedback={"decision": "修正必要", "score": 0.0},
        script_result="script",
        review_result="review",
        metadata={"quality_retry_count": 1},
    )


def test_gate_without_repository_keeps_existing_memory_only_behavior(tmp_path):
    path = tmp_path / "approval_requests.json"
    gate = make_gate(repository=None)

    request = create_request(gate)
    gate.approve(request)

    assert request.status == "approved"
    assert not path.exists()


def test_gate_saves_pending_request_when_repository_is_provided(tmp_path):
    repository = make_repository(tmp_path)
    gate = make_gate(repository)

    request = create_request(gate)

    saved = repository.get(request.approval_id)
    assert saved is not None
    assert saved.status == "pending"
    assert saved.topic == "猫の意外な雑学"


def test_gate_saves_approved_state(tmp_path):
    repository = make_repository(tmp_path)
    gate = make_gate(repository)
    request = create_request(gate)

    decision = gate.approve(request, decided_by="Koshi", comment="OK")

    saved = repository.get("approval-1")
    assert saved.status == "approved"
    assert decision.decision == "approved"


def test_gate_saves_rejected_state(tmp_path):
    repository = make_repository(tmp_path)
    gate = make_gate(repository)
    request = create_request(gate)

    decision = gate.reject(request, decided_by="Koshi", comment="NG")

    saved = repository.get("approval-1")
    assert saved.status == "rejected"
    assert decision.decision == "rejected"


def test_saved_request_can_be_loaded_from_another_repository_instance(tmp_path):
    path = tmp_path / "approval_requests.json"
    repository = JsonApprovalRequestRepository(str(path))
    gate = make_gate(repository)

    create_request(gate)
    other_repository = JsonApprovalRequestRepository(str(path))

    assert other_repository.get("approval-1").topic == "猫の意外な雑学"


def test_approve_by_id_uses_existing_approval_logic_and_persists(tmp_path):
    repository = make_repository(tmp_path)
    gate = make_gate(repository)
    create_request(gate)

    decision = gate.approve_by_id("approval-1", decided_by="Koshi")

    assert decision.decision == "approved"
    assert repository.get("approval-1").status == "approved"


def test_reject_by_id_uses_existing_rejection_logic_and_persists(tmp_path):
    repository = make_repository(tmp_path)
    gate = make_gate(repository)
    create_request(gate)

    decision = gate.reject_by_id("approval-1", comment="止める")

    assert decision.decision == "rejected"
    assert repository.get("approval-1").status == "rejected"


def test_approve_by_unknown_id_fails(tmp_path):
    gate = make_gate(make_repository(tmp_path))

    with pytest.raises(ApprovalRequestNotFoundError):
        gate.approve_by_id("missing")


def test_reject_by_unknown_id_fails(tmp_path):
    gate = make_gate(make_repository(tmp_path))

    with pytest.raises(ApprovalRequestNotFoundError):
        gate.reject_by_id("missing")
