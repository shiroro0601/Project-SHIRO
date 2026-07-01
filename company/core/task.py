from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional


class TaskStatus(str, Enum):
    CREATED = "created"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class TaskType(str, Enum):
    PLANNING = "planning"
    SCRIPT_WRITING = "script_writing"
    DIRECTION = "direction"
    IMAGE_PROMPT = "image_prompt"
    VOICE = "voice"
    EDITING = "editing"
    QUALITY_CHECK = "quality_check"
    GENERAL = "general"


@dataclass
class Task:
    task_id: str
    task_type: TaskType
    instruction: str
    input_data: Dict[str, Any] = field(default_factory=dict)
    output_data: Dict[str, Any] = field(default_factory=dict)
    status: TaskStatus = TaskStatus.CREATED
    error: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now().isoformat(timespec="seconds"))
    started_at: Optional[str] = None
    finished_at: Optional[str] = None

    def start(self) -> None:
        self.status = TaskStatus.RUNNING
        self.started_at = datetime.now().isoformat(timespec="seconds")

    def complete(self, output_data: Dict[str, Any]) -> None:
        self.status = TaskStatus.COMPLETED
        self.output_data = output_data
        self.finished_at = datetime.now().isoformat(timespec="seconds")

    def fail(self, error: str) -> None:
        self.status = TaskStatus.FAILED
        self.error = error
        self.finished_at = datetime.now().isoformat(timespec="seconds")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "task_type": self.task_type.value,
            "instruction": self.instruction,
            "input_data": self.input_data,
            "output_data": self.output_data,
            "status": self.status.value,
            "error": self.error,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
        }