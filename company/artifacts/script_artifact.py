from dataclasses import dataclass, field

from company.artifacts.scene_artifact import SceneArtifact


@dataclass
class ScriptArtifact:
    title: str
    narration: str
    image_prompts: list[str] = field(default_factory=list)
    scenes: list[SceneArtifact] = field(default_factory=list)
    raw_text: str = ""
