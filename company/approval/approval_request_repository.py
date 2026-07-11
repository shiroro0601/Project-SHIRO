import json
import os
from pathlib import Path
from typing import Protocol
from uuid import uuid4

from company.approval.approval_event import ApprovalEvent
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

    def save_with_event(
        self,
        request: ApprovalRequest,
        event: ApprovalEvent,
    ) -> ApprovalRequest:
        data = self._load_data()
        self._upsert_request(data, request)
        self._append_event_to_data(data, event)
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

    def append_event(self, event: ApprovalEvent) -> ApprovalEvent:
        data = self._load_data()
        self._append_event_to_data(data, event)
        self._write_data(data)
        return event

    def list_events(self, approval_id: str) -> list[ApprovalEvent]:
        data = self._load_data()
        return [
            ApprovalEvent.from_dict(item)
            for item in data.get("approval_history", [])
            if item.get("approval_id") == approval_id
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
        payload = self._serialize_payload(data)
        try:
            self._write_payload_atomically(payload)
        except ApprovalPersistenceError:
            raise
        except Exception as exc:
            raise ApprovalPersistenceError(
                f"Failed to write approval request store: {self.path}"
            ) from exc

    def _serialize_payload(self, data: dict) -> str:
        try:
            return json.dumps(data, ensure_ascii=False, indent=2)
        except (TypeError, ValueError) as exc:
            raise ApprovalPersistenceError(
                "Failed to serialize approval request store."
            ) from exc

    def _write_payload_atomically(self, payload: str) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temp_path = self.path.parent / f".{self.path.name}.{uuid4().hex}.tmp"
        try:
            with open(temp_path, "w", encoding="utf-8") as temp_file:
                temp_file.write(payload)
                temp_file.flush()
                os.fsync(temp_file.fileno())
            os.replace(str(temp_path), str(self.path))
        except Exception as exc:
            raise ApprovalPersistenceError(
                f"Failed to atomically write approval request store: {self.path}"
            ) from exc
        finally:
            try:
                if temp_path.exists():
                    temp_path.unlink()
            except OSError:
                pass

    def _empty_data(self) -> dict:
        return {
            "schema_version": SCHEMA_VERSION,
            "approval_requests": [],
            "approval_history": [],
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
        if "approval_history" in data and not isinstance(data["approval_history"], list):
            raise ApprovalRequestDataError("approval_history must be a list.")
        data.setdefault("approval_history", [])

    def _upsert_request(self, data: dict, request: ApprovalRequest) -> None:
        requests = data["approval_requests"]
        request_data = request.to_dict()
        for index, existing in enumerate(requests):
            if existing.get("approval_id") == request.approval_id:
                requests[index] = request_data
                return
        requests.append(request_data)

    def _append_event_to_data(self, data: dict, event: ApprovalEvent) -> None:
        history = data.setdefault("approval_history", [])
        event_data = event.to_dict()
        if any(existing.get("event_id") == event.event_id for existing in history):
            return
        history.append(event_data)
