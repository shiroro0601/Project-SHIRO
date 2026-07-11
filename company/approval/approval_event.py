from dataclasses import dataclass, field
from typing import Any, Optional

from company.approval.exceptions import ApprovalRequestDataError


ACTION_CREATED = "created"
ACTION_APPROVED = "approved"
ACTION_REJECTED = "rejected"
VALID_ACTIONS = {ACTION_CREATED, ACTION_APPROVED, ACTION_REJECTED}


@dataclass(frozen=True)
class ApprovalEvent:
    event_id: str
    approval_id: str
    action: str
    occurred_at: str
    from_status: Optional[str] = None
    to_status: Optional[str] = None
    reason: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.action not in VALID_ACTIONS:
            raise ApprovalRequestDataError(f"Invalid approval event action: {self.action}")
        object.__setattr__(self, "metadata", dict(self.metadata or {}))

    def to_dict(self) -> dict:
        return {
            "event_id": self.event_id,
            "approval_id": self.approval_id,
            "action": self.action,
            "occurred_at": self.occurred_at,
            "from_status": self.from_status,
            "to_status": self.to_status,
            "reason": self.reason,
            "metadata": dict(self.metadata or {}),
        }

    @classmethod
    def from_dict(cls, data: dict):
        required_fields = [
            "event_id",
            "approval_id",
            "action",
            "occurred_at",
            "from_status",
            "to_status",
            "reason",
            "metadata",
        ]
        missing = [field_name for field_name in required_fields if field_name not in data]
        if missing:
            raise ApprovalRequestDataError(
                f"ApprovalEvent data missing required fields: {', '.join(missing)}"
            )
        if not isinstance(data["metadata"], dict):
            raise ApprovalRequestDataError("ApprovalEvent metadata must be a dict.")
        return cls(
            event_id=str(data["event_id"]),
            approval_id=str(data["approval_id"]),
            action=str(data["action"]),
            occurred_at=str(data["occurred_at"]),
            from_status=(
                None if data["from_status"] is None else str(data["from_status"])
            ),
            to_status=None if data["to_status"] is None else str(data["to_status"]),
            reason=str(data["reason"]),
            metadata=dict(data["metadata"]),
        )
