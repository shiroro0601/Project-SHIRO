from dataclasses import dataclass


@dataclass
class SceneArtifact:
    index: int
    narration: str
    image_prompt: str
    duration_seconds: float
