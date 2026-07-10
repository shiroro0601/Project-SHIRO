import json

import pytest

from company.approval.approval_request_repository import (
    JsonApprovalRequestRepository,
)
from company.approval.exceptions import ApprovalRequestNotFoundError
from company.approval.human_approval import HumanApprovalGate
from company.memory.company_memory import CompanyMemory
from company.memory.memory_retriever import MemoryRetriever
from company.reports.run_report import RunReportWriter, build_run_report
from main_v12_full_video_company_dry_run import FullAutoVideoPipeline
from main_v15_real_ai_company_video import save_run_report_to_memory


SCRIPT_RESULT = """【タイトル】
猫の意外な雑学

【シーン1】
ナレーション: 猫は狭い箱に入りたがります。
画像: 箱に入る猫
秒数: 3
"""

REVIEW_RESULT = """【評価】
制作可能です。

【改善点】
なし

【判定】
合格
"""


class CountingRole:
    def __init__(self, result):
        self.result = result
        self.calls = []

    def execute(self, input_text):
        self.calls.append(input_text)
        return self.result


class FakeImageGenerator:
    def __init__(self):
        self.calls = []

    def generate(self, prompt):
        self.calls.append(prompt)
        return f"image-{len(self.calls)}.png"


class FakeVoiceGenerator:
    def __init__(self):
        self.calls = []

    def generate(self, text):
        self.calls.append(text)
        return f"voice-{len(self.calls)}.wav"


class FakeSceneVideoComposer:
    def __init__(self):
        self.calls = []

    def compose(self, scene_assets, output_path):
        self.calls.append((scene_assets, output_path))
        return output_path


class FakePublisher:
    def __init__(self):
        self.calls = []

    def generate(self, task):
        self.calls.append(task)
        return {"status": "dry_run", "video_path": task.input_data["video_path"]}


def make_repository(tmp_path):
    return JsonApprovalRequestRepository(str(tmp_path / "approval_requests.json"))


def make_gate(repository):
    values = iter(["approval-1"])
    times = iter(["2026-07-11T10:00:00", "2026-07-11T10:01:00"])
    return HumanApprovalGate(
        id_factory=lambda: next(values),
        clock=lambda: next(times),
        repository=repository,
    )


def create_saved_request(repository, *, status="approved"):
    gate = make_gate(repository)
    request = gate.create_request(
        topic="猫の意外な雑学",
        stage="review",
        reason="Human approval required.",
        ceo_action="stop",
        quality_feedback={"decision": "合格", "score": 1.0},
        script_result=SCRIPT_RESULT,
        review_result=REVIEW_RESULT,
        metadata={"quality_retry_count": 0, "research_retry_count": 0},
    )
    if status == "approved":
        gate.approve(request, decided_by="Koshi")
    elif status == "rejected":
        gate.reject(request, decided_by="Koshi")
    return request


def make_pipeline(repository):
    researcher = CountingRole("research")
    writer = CountingRole(SCRIPT_RESULT)
    reviewer = CountingRole(REVIEW_RESULT)
    image = FakeImageGenerator()
    voice = FakeVoiceGenerator()
    composer = FakeSceneVideoComposer()
    publisher = FakePublisher()
    pipeline = FullAutoVideoPipeline(
        researcher=researcher,
        writer=writer,
        reviewer=reviewer,
        image_generator=image,
        voice_generator=voice,
        scene_video_composer=composer,
        publisher=publisher,
        human_approval_gate=HumanApprovalGate(repository=repository),
    )
    return pipeline, researcher, writer, reviewer, image, voice, composer, publisher


def test_persisted_approved_request_can_resume_from_another_instance(tmp_path):
    repository = make_repository(tmp_path)
    create_saved_request(repository, status="approved")
    other_repository = JsonApprovalRequestRepository(str(tmp_path / "approval_requests.json"))
    pipeline, researcher, writer, reviewer, image, voice, composer, publisher = (
        make_pipeline(other_repository)
    )

    result = pipeline.resume_approved_production_by_approval_id("approval-1")

    assert result["production_resumed"] is True
    assert result["production_resume_completed"] is True
    assert result["approval_status"] == "approved"
    assert result["approval_request"]["approval_id"] == "approval-1"
    assert result["video_path"] == "outputs/videos/final_video.mp4"
    assert researcher.calls == []
    assert writer.calls == []
    assert reviewer.calls == []
    assert image.calls == ["箱に入る猫"]
    assert voice.calls == ["猫は狭い箱に入りたがります。"]
    assert composer.calls
    assert publisher.calls


def test_persisted_pending_request_cannot_resume(tmp_path):
    repository = make_repository(tmp_path)
    create_saved_request(repository, status="pending")
    pipeline, _, _, _, image, voice, composer, publisher = make_pipeline(repository)

    with pytest.raises(ValueError):
        pipeline.resume_approved_production_by_approval_id("approval-1")

    assert image.calls == []
    assert voice.calls == []
    assert composer.calls == []
    assert publisher.calls == []


def test_persisted_rejected_request_cannot_resume(tmp_path):
    repository = make_repository(tmp_path)
    create_saved_request(repository, status="rejected")
    pipeline, _, _, _, image, voice, composer, publisher = make_pipeline(repository)

    with pytest.raises(ValueError):
        pipeline.resume_approved_production_by_approval_id("approval-1")

    assert image.calls == []
    assert voice.calls == []
    assert composer.calls == []
    assert publisher.calls == []


def test_missing_approval_id_cannot_resume(tmp_path):
    repository = make_repository(tmp_path)
    pipeline, _, _, _, _, _, _, _ = make_pipeline(repository)

    with pytest.raises(ApprovalRequestNotFoundError):
        pipeline.resume_approved_production_by_approval_id("missing")


def test_persisted_resume_result_keeps_existing_result_keys(tmp_path):
    repository = make_repository(tmp_path)
    create_saved_request(repository, status="approved")
    pipeline, _, _, _, _, _, _, _ = make_pipeline(repository)

    result = pipeline.resume_approved_production_by_approval_id("approval-1")

    for key in [
        "topic",
        "execution_order",
        "research_result",
        "script_result",
        "script_artifact",
        "scene_assets",
        "review_result",
        "image_path",
        "voice_path",
        "scene_video_path",
        "video_path",
        "publish_result",
        "approval_request",
        "approval_status",
        "resumed_from_approval",
        "production_resumed",
        "production_resume_completed",
        "approval_resume_result",
    ]:
        assert key in result


def test_persisted_resume_can_write_run_report_and_memory_context(tmp_path):
    repository = make_repository(tmp_path)
    create_saved_request(repository, status="approved")
    pipeline, _, _, _, _, _, _, _ = make_pipeline(repository)
    result = pipeline.resume_approved_production_by_approval_id("approval-1")
    report = build_run_report(
        topic=result["topic"],
        media_mode="placeholder",
        result=result,
    )
    report_path = RunReportWriter(output_dir=str(tmp_path / "reports")).write(report)
    memory = CompanyMemory(memory_path=str(tmp_path / "memory" / "company_memory.json"))

    record = save_run_report_to_memory(report, memory=memory)
    context = MemoryRetriever(memory).build_context(limit=1)

    assert json.loads(open(report_path, encoding="utf-8").read())[
        "production_resumed"
    ] is True
    assert record["production_resumed"] is True
    assert record["production_resume_completed"] is True
    assert "production_resumed: True" in context.to_prompt_text()
