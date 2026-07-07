from dataclasses import dataclass, field


@dataclass
class ScriptArtifact:
    title: str
    narration: str
    image_prompts: list[str] = field(default_factory=list)
    scenes: list[dict] = field(default_factory=list)
    raw_text: str = ""
