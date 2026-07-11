import json

from company.approval.approval_event import ApprovalEvent
from company.approval.approval_request_repository import (
    JsonApprovalRequestRepository,
)
from company.approval.human_approval import HumanApprovalGate


def make_repository(tmp_path):
    return JsonApprovalRequestRepository(str(tmp_path / "approval_requests.json"))


def make_gate(repository):
    request_ids = iter(["approval-1", "approval-2"])
    event_ids = iter(
        ["event-created-1", "event-approved-1", "event-created-2", "event-rejected-2"]
    )
    times = iter(
        [
            "2026-07-11T10:00:00",
            "2026-07-11T10:01:00",
            "2026-07-11T10:02:00",
            "2026-07-11T10:03:00",
        ]
    )
    return HumanApprovalGate(
        id_factory=lambda: next(request_ids),
        clock=lambda: next(times),
        repository=repository,
        event_id_factory=lambda: next(event_ids),
    )


def create_request(gate, topic="猫の意外な雑学"):
    return gate.create_request(
        topic=topic,
        stage="review",
        reason="人間承認が必要",
        ceo_action="stop",
        quality_feedback={"decision": "修正必要", "score": 0.0},
        script_result="script",
        review_result="review",
        metadata={"note": "日本語メタデータ"},
    )


def test_create_request_saves_created_event(tmp_path):
    repository = make_repository(tmp_path)
    gate = make_gate(repository)

    request = create_request(gate)

    events = repository.list_events(request.approval_id)
    assert [event.action for event in events] == ["created"]
    assert events[0].from_status is None
    assert events[0].to_status == "pending"


def test_approve_by_id_saves_approved_event(tmp_path):
    repository = make_repository(tmp_path)
    gate = make_gate(repository)
    request = create_request(gate)

    gate.approve_by_id(request.approval_id, decided_by="Koshi", comment="進めてよい")

    events = repository.list_events(request.approval_id)
    assert [event.action for event in events] == ["created", "approved"]
    assert events[1].from_status == "pending"
    assert events[1].to_status == "approved"
    assert events[1].reason == "進めてよい"
    assert events[1].metadata["decided_by"] == "Koshi"


def test_reject_by_id_saves_rejected_event(tmp_path):
    repository = make_repository(tmp_path)
    gate = make_gate(repository)
    request = create_request(gate)

    gate.reject_by_id(request.approval_id, decided_by="Koshi", comment="止める")

    events = repository.list_events(request.approval_id)
    assert [event.action for event in events] == ["created", "rejected"]
    assert events[1].from_status == "pending"
    assert events[1].to_status == "rejected"
    assert events[1].reason == "止める"


def test_history_is_filtered_by_approval_id(tmp_path):
    repository = make_repository(tmp_path)
    gate = make_gate(repository)
    first = create_request(gate, topic="猫")
    second = create_request(gate, topic="犬")

    first_events = repository.list_events(first.approval_id)
    second_events = repository.list_events(second.approval_id)

    assert [event.approval_id for event in first_events] == ["approval-1"]
    assert [event.approval_id for event in second_events] == ["approval-2"]


def test_event_order_is_stable(tmp_path):
    repository = make_repository(tmp_path)
    gate = make_gate(repository)
    request = create_request(gate)
    gate.approve_by_id(request.approval_id)

    assert [event.event_id for event in repository.list_events(request.approval_id)] == [
        "event-created-1",
        "event-approved-1",
    ]


def test_history_can_be_read_from_another_repository_instance(tmp_path):
    path = tmp_path / "approval_requests.json"
    repository = JsonApprovalRequestRepository(str(path))
    gate = make_gate(repository)
    request = create_request(gate)
    gate.approve_by_id(request.approval_id)

    other_repository = JsonApprovalRequestRepository(str(path))

    assert [event.action for event in other_repository.list_events("approval-1")] == [
        "created",
        "approved",
    ]


def test_get_and_list_do_not_add_events(tmp_path):
    repository = make_repository(tmp_path)
    gate = make_gate(repository)
    request = create_request(gate)

    before = len(repository.list_events(request.approval_id))
    repository.get(request.approval_id)
    repository.list_all()
    after = len(repository.list_events(request.approval_id))

    assert before == after == 1


def test_same_operation_does_not_create_duplicate_event(tmp_path):
    repository = make_repository(tmp_path)
    gate = make_gate(repository)
    request = create_request(gate)
    gate.approve_by_id(request.approval_id)

    assert [event.action for event in repository.list_events(request.approval_id)] == [
        "created",
        "approved",
    ]


def test_old_json_without_history_can_be_read_without_rewrite(tmp_path):
    path = tmp_path / "approval_requests.json"
    old_data = {
        "schema_version": 1,
        "approval_requests": [],
    }
    path.write_text(json.dumps(old_data, ensure_ascii=False), encoding="utf-8")
    before = path.read_text(encoding="utf-8")
    repository = JsonApprovalRequestRepository(str(path))

    assert repository.list_events("approval-1") == []
    assert path.read_text(encoding="utf-8") == before


def test_request_save_keeps_existing_history(tmp_path):
    repository = make_repository(tmp_path)
    gate = make_gate(repository)
    request = create_request(gate)

    request.reason = "更新後"
    repository.save(request)

    assert [event.action for event in repository.list_events(request.approval_id)] == [
        "created"
    ]


def test_event_append_keeps_existing_requests(tmp_path):
    repository = make_repository(tmp_path)
    gate = make_gate(repository)
    request = create_request(gate)

    repository.append_event(
        ApprovalEvent(
            event_id="manual-event",
            approval_id=request.approval_id,
            action="approved",
            occurred_at="2026-07-11T10:10:00",
            from_status="pending",
            to_status="approved",
            reason="手動イベント",
            metadata={"source": "test"},
        )
    )

    assert repository.get(request.approval_id) is not None
    assert [event.action for event in repository.list_events(request.approval_id)] == [
        "created",
        "approved",
    ]


def test_japanese_reason_and_metadata_survive_reload(tmp_path):
    path = tmp_path / "approval_requests.json"
    repository = JsonApprovalRequestRepository(str(path))
    gate = make_gate(repository)
    request = create_request(gate)
    gate.approve_by_id(request.approval_id, decided_by="Koshi", comment="承認します")

    other_repository = JsonApprovalRequestRepository(str(path))
    approved_event = other_repository.list_events("approval-1")[1]

    assert approved_event.reason == "承認します"
    assert approved_event.metadata["decided_by"] == "Koshi"


def test_list_events_returns_independent_event_objects(tmp_path):
    repository = make_repository(tmp_path)
    gate = make_gate(repository)
    request = create_request(gate)

    event = repository.list_events(request.approval_id)[0]
    event.metadata["note"] = "changed"

    assert (
        repository.list_events(request.approval_id)[0].metadata["reason"]
        == "人間承認が必要"
    )
