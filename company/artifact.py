"""
Project SHIRO v0.8
成果物クラス
"""

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict


@dataclass
class Artifact:
    """
    AI社員が作成した成果物
    """

    artifact_type: str

    # テキスト・パスなど
    content: Any

    # メタデータ
    metadata: Dict[str, Any] = field(default_factory=dict)

    created_at: datetime = field(default_factory=datetime.now)

    def is_file(self) -> bool:
        if isinstance(self.content, str):
            return Path(self.content).exists()
        return False

    def __str__(self) -> str:
        return f"{self.artifact_type}"