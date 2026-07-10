from dataclasses import dataclass, field
from datetime import datetime
from uuid import uuid4


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


@dataclass
class ApprovalDecision:
    approval_id: str
    decision: str
    decided_at: str
    decided_by: str
    comment: str


class HumanApprovalGate:
    def __init__(self, id_factory=None, clock=None):
        self.id_factory = id_factory or (lambda: str(uuid4()))
        self.clock = clock or (lambda: datetime.now().isoformat(timespec="seconds"))

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
        return ApprovalRequest(
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

    def approve(
        self,
        request: ApprovalRequest,
        *,
        decided_by: str = "human",
        comment: str = "",
    ) -> ApprovalDecision:
        return self._decide(
            request,
            decision=STATUS_APPROVED,
            decided_by=decided_by,
            comment=comment,
        )

    def reject(
        self,
        request: ApprovalRequest,
        *,
        decided_by: str = "human",
        comment: str = "",
    ) -> ApprovalDecision:
        return self._decide(
            request,
            decision=STATUS_REJECTED,
            decided_by=decided_by,
            comment=comment,
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
