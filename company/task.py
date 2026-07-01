"""
Project SHIRO v0.8
タスククラス
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict
import uuid


@dataclass
class Task:
    """
    社員へ依頼する仕事
    """

    title: str
    description: str

    # 追加情報
    data: Dict[str, Any] = field(default_factory=dict)

    # 自動生成
    task_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    created_at: datetime = field(default_factory=datetime.now)

    # 状態
    status: str = "WAITING"

    def start(self) -> None:
        self.status = "RUNNING"

    def complete(self) -> None:
        self.status = "COMPLETED"

    def fail(self) -> None:
        self.status = "FAILED"

    def __str__(self) -> str:
        return f"[{self.task_id}] {self.title} ({self.status})"