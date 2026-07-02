from dataclasses import dataclass, field
from typing import Any, Dict, List

from company.core.task import Task


@dataclass
class TaskContext:
    task: Task
    artifacts: List[Any] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def add_artifact(self, artifact: Any) -> None:
        self.artifacts.append(artifact)

    def get_artifacts(self) -> List[Any]:
        return list(self.artifacts)

    def set_metadata(self, key: str, value: Any) -> None:
        self.metadata[key] = value

    def get_metadata(self, key: str, default: Any = None) -> Any:
        return self.metadata.get(key, default)


@dataclass
class TaskHandoff:
    sender: str
    receiver: str
    context: TaskContext
