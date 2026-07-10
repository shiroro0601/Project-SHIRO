import pytest

from company.approval.human_approval import HumanApprovalGate


def make_gate():
    values = iter(["approval-1"])
    times = iter(["2026-07-11T10:00:00", "2026-07-11T10:01:00"])
    return HumanApprovalGate(id_factory=lambda: next(values), clock=lambda: next(times))


def create_request(gate=None):
    gate = gate or make_gate()
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


def test_human_approval_gate_creates_pending_request():
    request = create_request()

    assert request.approval_id == "approval-1"
    assert request.status == "pending"
    assert request.topic == "猫の意外な雑学"
    assert request.stage == "review"
    assert request.reason == "Retry limit reached."
    assert request.ceo_action == "stop"
    assert request.quality_decision == "修正必要"
    assert request.quality_score == 0.0
    assert request.metadata["quality_retry_count"] == 1


def test_human_approval_gate_approves_request():
    gate = make_gate()
    request = create_request(gate)

    decision = gate.approve(
        request,
        decided_by="Koshi",
        comment="進めてよい",
    )

    assert request.status == "approved"
    assert decision.approval_id == "approval-1"
    assert decision.decision == "approved"
    assert decision.decided_by == "Koshi"
    assert decision.comment == "進めてよい"


def test_human_approval_gate_rejects_request():
    gate = make_gate()
    request = create_request(gate)

    decision = gate.reject(
        request,
        decided_by="Koshi",
        comment="やり直し",
    )

    assert request.status == "rejected"
    assert decision.decision == "rejected"
    assert decision.comment == "やり直し"


def test_human_approval_gate_rejects_double_approval():
    gate = make_gate()
    request = create_request(gate)
    gate.approve(request)

    with pytest.raises(ValueError, match="already resolved"):
        gate.approve(request)


def test_human_approval_gate_rejects_after_approval():
    gate = make_gate()
    request = create_request(gate)
    gate.approve(request)

    with pytest.raises(ValueError, match="already resolved"):
        gate.reject(request)
