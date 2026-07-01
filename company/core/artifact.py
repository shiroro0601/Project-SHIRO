from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional


class ArtifactType(str, Enum):
    PLAN = "plan"
    SCRIPT = "script"
    DIRECTION = "direction"
    IMAGE_PROMPT = "image_prompt"
    VOICE = "voice"
    VIDEO = "video"
    QUALITY_REPORT = "quality_report"
    GENERAL = "general"


@dataclass
class Artifact:
    artifact_id: str
    artifact_type: ArtifactType
    name: str
    content: Dict[str, Any]
    source_task_id: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now().isoformat(timespec="seconds"))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "artifact_id": self.artifact_id,
            "artifact_type": self.artifact_type.value,
            "name": self.name,
            "content": self.content,
            "source_task_id": self.source_task_id,
            "created_at": self.created_at,
        }


class ArtifactFactory:
    @staticmethod
    def create_artifact(
        artifact_type: ArtifactType,
        name: str,
        content: Dict[str, Any],
        source_task_id: str | None = None,
    ) -> Artifact:
        return Artifact(
            artifact_id=ArtifactFactory._generate_artifact_id(artifact_type),
            artifact_type=artifact_type,
            name=name,
            content=content,
            source_task_id=source_task_id,
        )

    @staticmethod
    def _generate_artifact_id(artifact_type: ArtifactType) -> str:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        return f"artifact_{artifact_type.value}_{timestamp}"
