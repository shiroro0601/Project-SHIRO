from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class ApprovalResumeContext:
    approval_id: str
    topic: str
    script_result: str
    review_result: str
    script_artifact: object
    quality_feedback: object | None = None
    ceo_decision: object | None = None
    metadata: dict = field(default_factory=dict)


@dataclass
class ApprovalResumeResult:
    resumed: bool
    approval_id: str
    resumed_at: str
    production_completed: bool
    image_path: str
    voice_path: str
    scene_assets: list
    scene_video_path: str | None
    video_path: str
    publish_result: object | None
    error: str = ""


def current_resume_time() -> str:
    return datetime.now().isoformat(timespec="seconds")
