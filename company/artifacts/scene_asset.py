from dataclasses import dataclass


@dataclass
class SceneAsset:
    scene_index: int
    image_path: str
    voice_path: str
    narration: str
    image_prompt: str
    duration_seconds: float
