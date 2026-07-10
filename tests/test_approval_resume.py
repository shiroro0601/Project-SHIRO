import pytest

from company.approval.human_approval import HumanApprovalGate
from company.artifacts.script_artifact import ScriptArtifact


def make_gate():
    values = iter(["approval-1"])
    times = iter(["2026-07-11T10:00:00", "2026-07-11T10:01:00"])
    return HumanApprovalGate(id_factory=lambda: next(values), clock=lambda: next(times))


def make_request(gate):
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


def make_script_artifact():
    return ScriptArtifact(
        title="猫タイトル",
        narration="猫ナレーション",
        image_prompts=["猫画像"],
        scenes=[],
        raw_text="raw",
    )


def test_build_resume_context_from_approved_request():
    gate = make_gate()
    request = make_request(gate)
    gate.approve(request, decided_by="Koshi", comment="OK")
    artifact = make_script_artifact()

    context = gate.build_resume_context(
        request,
        script_artifact=artifact,
        quality_feedback={"decision": "修正必要"},
        ceo_decision={"action": "stop"},
    )

    assert context.approval_id == "approval-1"
    assert context.topic == "猫の意外な雑学"
    assert context.script_result == "script"
    assert context.review_result == "review"
    assert context.script_artifact is artifact
    assert context.quality_feedback == {"decision": "修正必要"}
    assert context.ceo_decision == {"action": "stop"}


def test_build_resume_context_from_pending_request_fails():
    gate = make_gate()
    request = make_request(gate)

    with pytest.raises(ValueError, match="approved before resuming"):
        gate.build_resume_context(request, script_artifact=make_script_artifact())


def test_build_resume_context_from_rejected_request_fails():
    gate = make_gate()
    request = make_request(gate)
    gate.reject(request)

    with pytest.raises(ValueError, match="approved before resuming"):
        gate.build_resume_context(request, script_artifact=make_script_artifact())
