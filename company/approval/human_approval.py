from dataclasses import dataclass, field
from datetime import datetime
from uuid import uuid4

from company.approval.approval_resume import ApprovalResumeContext
from company.approval.exceptions import (
    ApprovalRequestDataError,
    ApprovalRequestNotFoundError,
)


STATUS_PENDING = "pending"
STATUS_APPROVED = "approved"
STATUS_REJECTED = "rejected"


@dataclass
class ApprovalRequest:
    approval_id: str
    status: str
    created_at: str
    topic: str
    stage: str
    reason: str
    ceo_action: str
    quality_decision: str
    quality_score: float
    script_result: str
    review_result: str
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "approval_id": self.approval_id,
            "status": self.status,
            "created_at": self.created_at,
            "topic": self.topic,
            "stage": self.stage,
            "reason": self.reason,
            "ceo_action": self.ceo_action,
            "quality_decision": self.quality_decision,
            "quality_score": self.quality_score,
            "script_result": self.script_result,
            "review_result": self.review_result,
            "metadata": dict(self.metadata or {}),
        }

    @classmethod
    def from_dict(cls, data: dict):
        required_fields = [
            "approval_id",
            "status",
            "created_at",
            "topic",
            "stage",
            "reason",
            "ceo_action",
            "quality_decision",
            "quality_score",
            "script_result",
            "review_result",
            "metadata",
        ]
        missing = [field_name for field_name in required_fields if field_name not in data]
        if missing:
            raise ApprovalRequestDataError(
                f"ApprovalRequest data missing required fields: {', '.join(missing)}"
            )
        if not isinstance(data["metadata"], dict):
            raise ApprovalRequestDataError("ApprovalRequest metadata must be a dict.")
        return cls(
            approval_id=str(data["approval_id"]),
            status=str(data["status"]),
            created_at=str(data["created_at"]),
            topic=str(data["topic"]),
            stage=str(data["stage"]),
            reason=str(data["reason"]),
            ceo_action=str(data["ceo_action"]),
            quality_decision=str(data["quality_decision"]),
            quality_score=float(data["quality_score"]),
            script_result=str(data["script_result"]),
            review_result=str(data["review_result"]),
            metadata=dict(data["metadata"]),
        )


@dataclass
class ApprovalDecision:
    approval_id: str
    decision: str
    decided_at: str
    decided_by: str
    comment: str


class HumanApprovalGate:
    def __init__(self, id_factory=None, clock=None, repository=None):
        self.id_factory = id_factory or (lambda: str(uuid4()))
        self.clock = clock or (lambda: datetime.now().isoformat(timespec="seconds"))
        self.repository = repository

    def create_request(
        self,
        *,
        topic: str,
        stage: str,
        reason: str,
        ceo_action: str,
        quality_feedback,
        script_result: str,
        review_result: str,
        metadata: dict | None = None,
    ) -> ApprovalRequest:
        request = ApprovalRequest(
            approval_id=self.id_factory(),
            status=STATUS_PENDING,
            created_at=self.clock(),
            topic=topic,
            stage=stage,
            reason=reason,
            ceo_action=ceo_action,
            quality_decision=self._quality_value(quality_feedback, "decision", ""),
            quality_score=float(self._quality_value(quality_feedback, "score", 0.5)),
            script_result=script_result,
            review_result=review_result,
            metadata=dict(metadata or {}),
        )
        self._save_if_available(request)
        return request

    def approve(
        self,
        request: ApprovalRequest,
        *,
        decided_by: str = "human",
        comment: str = "",
    ) -> ApprovalDecision:
        decision = self._decide(
            request,
            decision=STATUS_APPROVED,
            decided_by=decided_by,
            comment=comment,
        )
        self._save_if_available(request)
        return decision

    def reject(
        self,
        request: ApprovalRequest,
        *,
        decided_by: str = "human",
        comment: str = "",
    ) -> ApprovalDecision:
        decision = self._decide(
            request,
            decision=STATUS_REJECTED,
            decided_by=decided_by,
            comment=comment,
        )
        self._save_if_available(request)
        return decision

    def get_request(self, approval_id: str) -> ApprovalRequest:
        request = self._get_from_repository(approval_id)
        if request is None:
            raise ApprovalRequestNotFoundError(
                f"Approval request not found: {approval_id}"
            )
        return request

    def approve_by_id(
        self,
        approval_id: str,
        *,
        decided_by: str = "human",
        comment: str = "",
    ) -> ApprovalDecision:
        request = self.get_request(approval_id)
        return self.approve(request, decided_by=decided_by, comment=comment)

    def reject_by_id(
        self,
        approval_id: str,
        *,
        decided_by: str = "human",
        comment: str = "",
    ) -> ApprovalDecision:
        request = self.get_request(approval_id)
        return self.reject(request, decided_by=decided_by, comment=comment)

    def build_resume_context_by_id(
        self,
        approval_id: str,
        *,
        script_artifact,
        quality_feedback=None,
        ceo_decision=None,
    ) -> ApprovalResumeContext:
        request = self.get_request(approval_id)
        return self.build_resume_context(
            request,
            script_artifact=script_artifact,
            quality_feedback=quality_feedback,
            ceo_decision=ceo_decision,
        )

    def build_resume_context(
        self,
        request: ApprovalRequest,
        *,
        script_artifact,
        quality_feedback=None,
        ceo_decision=None,
    ) -> ApprovalResumeContext:
        if request.status != STATUS_APPROVED:
            raise ValueError("Approval request must be approved before resuming production.")
        return ApprovalResumeContext(
            approval_id=request.approval_id,
            topic=request.topic,
            script_result=request.script_result,
            review_result=request.review_result,
            script_artifact=script_artifact,
            quality_feedback=quality_feedback,
            ceo_decision=ceo_decision,
            metadata=dict(request.metadata or {}),
        )

    def _decide(
        self,
        request: ApprovalRequest,
        *,
        decision: str,
        decided_by: str,
        comment: str,
    ) -> ApprovalDecision:
        if request.status != STATUS_PENDING:
            raise ValueError("Approval request is already resolved.")
        request.status = decision
        return ApprovalDecision(
            approval_id=request.approval_id,
            decision=decision,
            decided_at=self.clock(),
            decided_by=decided_by,
            comment=comment,
        )

    def _quality_value(self, quality_feedback, key: str, default):
        if isinstance(quality_feedback, dict):
            return quality_feedback.get(key, default)
        return getattr(quality_feedback, key, default)

    def _save_if_available(self, request: ApprovalRequest) -> None:
        if self.repository is not None:
            self.repository.save(request)

    def _get_from_repository(self, approval_id: str):
        if self.repository is None:
            return None
        return self.repository.get(approval_id)
