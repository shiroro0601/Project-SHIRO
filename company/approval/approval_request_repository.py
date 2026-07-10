import json
from pathlib import Path
from typing import Protocol

from company.approval.exceptions import (
    ApprovalPersistenceError,
    ApprovalRequestDataError,
)
from company.approval.human_approval import ApprovalRequest


SCHEMA_VERSION = 1


class ApprovalRequestRepository(Protocol):
    def save(self, request: ApprovalRequest) -> ApprovalRequest:
        ...

    def get(self, approval_id: str) -> ApprovalRequest | None:
        ...

    def list_all(self) -> list[ApprovalRequest]:
        ...


class JsonApprovalRequestRepository:
    def __init__(self, path: str = "outputs/approvals/approval_requests.json"):
        self.path = Path(path)

    def save(self, request: ApprovalRequest) -> ApprovalRequest:
        data = self._load_data()
        requests = data["approval_requests"]

        replaced = False
        request_data = request.to_dict()
        for index, existing in enumerate(requests):
            if existing.get("approval_id") == request.approval_id:
                requests[index] = request_data
                replaced = True
                break

        if not replaced:
            requests.append(request_data)

        self._write_data(data)
        return request

    def get(self, approval_id: str) -> ApprovalRequest | None:
        for request in self.list_all():
            if request.approval_id == approval_id:
                return request
        return None

    def list_all(self) -> list[ApprovalRequest]:
        data = self._load_data()
        return [
            ApprovalRequest.from_dict(item)
            for item in data.get("approval_requests", [])
        ]

    def _load_data(self) -> dict:
        if not self.path.exists():
            return self._empty_data()

        try:
            raw_data = json.loads(self.path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ApprovalPersistenceError(
                f"Invalid approval request JSON: {self.path}"
            ) from exc

        self._validate_data(raw_data)
        return raw_data

    def _write_data(self, data: dict) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def _empty_data(self) -> dict:
        return {
            "schema_version": SCHEMA_VERSION,
            "approval_requests": [],
        }

    def _validate_data(self, data: dict) -> None:
        if not isinstance(data, dict):
            raise ApprovalRequestDataError("Approval request store must be an object.")
        if "schema_version" not in data:
            raise ApprovalRequestDataError("Approval request store missing schema_version.")
        if "approval_requests" not in data:
            raise ApprovalRequestDataError(
                "Approval request store missing approval_requests."
            )
        if not isinstance(data["approval_requests"], list):
            raise ApprovalRequestDataError("approval_requests must be a list.")
