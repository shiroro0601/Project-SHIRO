from dataclasses import FrozenInstanceError

import pytest

from company.approval.approval_event import ApprovalEvent
from company.approval.exceptions import ApprovalRequestDataError


def make_event(**overrides):
    data = {
        "event_id": "event-1",
        "approval_id": "approval-1",
        "action": "created",
        "occurred_at": "2026-07-11T10:00:00",
        "from_status": None,
        "to_status": "pending",
        "reason": "承認待ちを作成",
        "metadata": {"stage": "review"},
    }
    data.update(overrides)
    return ApprovalEvent(**data)


def test_approval_event_to_dict_from_dict_round_trip():
    event = make_event()

    restored = ApprovalEvent.from_dict(event.to_dict())

    assert restored == event


def test_approval_event_preserves_japanese_reason_and_metadata():
    event = make_event(reason="人間CEOの確認が必要", metadata={"コメント": "確認待ち"})

    restored = ApprovalEvent.from_dict(event.to_dict())

    assert restored.reason == "人間CEOの確認が必要"
    assert restored.metadata["コメント"] == "確認待ち"


def test_approval_event_from_dict_does_not_mutate_input():
    data = make_event().to_dict()
    original = dict(data)
    original["metadata"] = dict(data["metadata"])

    ApprovalEvent.from_dict(data)

    assert data == original


def test_approval_event_metadata_is_not_shared():
    data = make_event().to_dict()

    event = ApprovalEvent.from_dict(data)
    data["metadata"]["stage"] = "changed"

    assert event.metadata["stage"] == "review"


def test_approval_event_missing_required_key_fails():
    data = make_event().to_dict()
    del data["event_id"]

    with pytest.raises(ApprovalRequestDataError):
        ApprovalEvent.from_dict(data)


def test_approval_event_invalid_action_fails():
    data = make_event().to_dict()
    data["action"] = "invalid"

    with pytest.raises(ApprovalRequestDataError):
        ApprovalEvent.from_dict(data)


def test_approval_event_is_frozen():
    event = make_event()

    with pytest.raises(FrozenInstanceError):
        event.action = "approved"
