import json
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

from company.reports.quality_feedback import QualityFeedbackParser


@dataclass
class RunReport:
    topic: str
    created_at: str
    media_mode: str
    status: str
    research_result: str
    script_result: str
    review_result: str
    script_title: str
    scenes: list[dict]
    assets: list[dict]
    image_path: str
    voice_path: str
    video_path: str
    scene_video_path: Optional[str]
    quality_feedback: dict = field(default_factory=dict)
    quality_retry_count: int = 0
    quality_retry_history: list[dict] = field(default_factory=list)
    research_retry_count: int = 0
    research_retry_history: list[dict] = field(default_factory=list)
    ceo_decision: dict | None = None
    ceo_decision_history: list[dict] = field(default_factory=list)
    stopped: bool = False
    stop_stage: Optional[str] = None
    stop_reason: str = ""
    production_skipped: bool = False
    approval_required: bool = False
    approval_status: str = "not_required"
    approval_request: dict | None = None
    approval_decision: dict | None = None
    resumed_from_approval: bool = False
    production_resumed: bool = False
    production_resume_completed: bool = False
    approval_resume_result: dict | None = None


class RunReportWriter:
    def __init__(self, output_dir: str = "outputs/reports"):
        self.output_dir = Path(output_dir)

    def write(self, report: RunReport) -> str:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = self.output_dir / f"real_ai_company_run_{timestamp}.json"
        output_path.write_text(
            json.dumps(asdict(report), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return str(output_path)


def build_run_report(
    topic: str,
    media_mode: str,
    result: dict,
    status: str = "completed",
) -> RunReport:
    script_artifact = result.get("script_artifact")
    scene_assets = result.get("scene_assets", [])
    review_result = str(result.get("review_result", ""))
    quality_feedback = QualityFeedbackParser().parse(review_result)

    return RunReport(
        topic=topic,
        created_at=datetime.now().isoformat(timespec="seconds"),
        media_mode=media_mode,
        status=status,
        research_result=str(result.get("research_result", "")),
        script_result=str(result.get("script_result", "")),
        review_result=review_result,
        script_title=str(getattr(script_artifact, "title", "") or ""),
        scenes=_scenes_to_dicts(script_artifact),
        assets=[_object_to_dict(asset) for asset in scene_assets],
        image_path=str(result.get("image_path", "")),
        voice_path=str(result.get("voice_path", "")),
        video_path=str(result.get("video_path", "")),
        scene_video_path=result.get("scene_video_path"),
        quality_feedback=asdict(quality_feedback),
        quality_retry_count=int(result.get("quality_retry_count", 0) or 0),
        quality_retry_history=[
            dict(item) for item in result.get("quality_retry_history", []) or []
        ],
        research_retry_count=int(result.get("research_retry_count", 0) or 0),
        research_retry_history=[
            dict(item) for item in result.get("research_retry_history", []) or []
        ],
        ceo_decision=_optional_dict(result.get("ceo_decision")),
        ceo_decision_history=[
            dict(item) for item in result.get("ceo_decision_history", []) or []
        ],
        stopped=bool(result.get("stopped", False)),
        stop_stage=result.get("stop_stage"),
        stop_reason=str(result.get("stop_reason", "")),
        production_skipped=bool(result.get("production_skipped", False)),
        approval_required=bool(result.get("approval_required", False)),
        approval_status=str(result.get("approval_status", "not_required")),
        approval_request=_optional_dict(result.get("approval_request")),
        approval_decision=_optional_dict(result.get("approval_decision")),
        resumed_from_approval=bool(result.get("resumed_from_approval", False)),
        production_resumed=bool(result.get("production_resumed", False)),
        production_resume_completed=bool(
            result.get("production_resume_completed", False)
        ),
        approval_resume_result=_optional_dict(result.get("approval_resume_result")),
    )


def _scenes_to_dicts(script_artifact) -> list[dict]:
    scenes = getattr(script_artifact, "scenes", []) or []
    return [_object_to_dict(scene) for scene in scenes]


def _object_to_dict(value) -> dict:
    if isinstance(value, dict):
        return dict(value)
    if hasattr(value, "__dataclass_fields__"):
        return asdict(value)
    if hasattr(value, "__dict__"):
        return dict(value.__dict__)
    return {}


def _optional_dict(value) -> dict | None:
    if value is None:
        return None
    if isinstance(value, dict):
        return dict(value)
    return _object_to_dict(value)
