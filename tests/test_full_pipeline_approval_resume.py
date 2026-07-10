import pytest

from company.approval.human_approval import HumanApprovalGate
from company.artifacts.scene_artifact import SceneArtifact
from company.artifacts.script_artifact import ScriptArtifact
from company.core.ceo_decision import ACTION_STOP, CEODecision
from main_v12_full_video_company_dry_run import FullAutoVideoPipeline


class CountingRole:
    def __init__(self, result):
        self.result = result
        self.calls = []

    def execute(self, input_text):
        self.calls.append(input_text)
        return self.result


class FakeImageGenerator:
    def __init__(self, fail=False):
        self.calls = []
        self.fail = fail

    def generate(self, prompt):
        self.calls.append(prompt)
        if self.fail:
            raise RuntimeError("image failed")
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


class FakeEditor:
    def __init__(self):
        self.calls = []

    def generate(self, image_paths, audio_paths):
        self.calls.append((image_paths, audio_paths))
        return "video.mp4"


class FakePublisher:
    def __init__(self):
        self.calls = []

    def generate(self, task):
        self.calls.append(task)
        return {"status": "dry_run", "video_path": task.input_data["video_path"]}


class StopPolicy:
    def decide(
        self,
        *,
        stage,
        quality_feedback=None,
        retry_count=0,
        retry_limit=0,
        context=None,
    ):
        return CEODecision(
            action=ACTION_STOP,
            reason="Retry limit reached.",
            stage=stage,
            quality_decision=getattr(quality_feedback, "decision", ""),
            quality_score=getattr(quality_feedback, "score", 0.0),
            retry_count=retry_count,
            metadata={},
        )


def approved_review():
    return "【評価】\n構成が弱いです。\n\n【改善点】\n冒頭を改善\n\n【判定】\n修正必要"


def make_script_artifact():
    return ScriptArtifact(
        title="猫タイトル",
        narration="猫ナレーション",
        image_prompts=[],
        scenes=[
            SceneArtifact(
                index=1,
                narration="猫は箱が好きです。",
                image_prompt="箱に入る猫",
                duration_seconds=3.0,
            )
        ],
        raw_text="raw",
    )


def make_gate():
    values = iter(["approval-1"])
    times = iter(["2026-07-11T10:00:00", "2026-07-11T10:01:00"])
    return HumanApprovalGate(id_factory=lambda: next(values), clock=lambda: next(times))


def make_resume_context(gate=None):
    gate = gate or make_gate()
    request = gate.create_request(
        topic="猫の意外な雑学",
        stage="review",
        reason="Retry limit reached.",
        ceo_action="stop",
        quality_feedback={"decision": "修正必要", "score": 0.0},
        script_result="script",
        review_result=approved_review(),
    )
    gate.approve(request)
    return gate.build_resume_context(request, script_artifact=make_script_artifact())


def make_pipeline(image_generator=None):
    researcher = CountingRole("research")
    writer = CountingRole("script")
    reviewer = CountingRole(approved_review())
    image = image_generator or FakeImageGenerator()
    voice = FakeVoiceGenerator()
    editor = FakeEditor()
    composer = FakeSceneVideoComposer()
    publisher = FakePublisher()
    pipeline = FullAutoVideoPipeline(
        researcher=researcher,
        writer=writer,
        reviewer=reviewer,
        image_generator=image,
        voice_generator=voice,
        editor=editor,
        publisher=publisher,
        scene_video_composer=composer,
    )
    return pipeline, researcher, writer, reviewer, image, voice, editor, composer, publisher


def test_resume_approved_production_does_not_rerun_ai_roles():
    pipeline, researcher, writer, reviewer, image, voice, editor, composer, publisher = (
        make_pipeline()
    )

    result = pipeline.resume_approved_production(make_resume_context())

    assert researcher.calls == []
    assert writer.calls == []
    assert reviewer.calls == []
    assert image.calls == ["箱に入る猫"]
    assert voice.calls == ["猫は箱が好きです。"]
    assert composer.calls
    assert publisher.calls
    assert result["production_resumed"] is True
    assert result["production_resume_completed"] is True
    assert result["video_path"] == "outputs/videos/final_video.mp4"


def test_pending_request_cannot_build_resume_context_and_production_is_not_called():
    gate = make_gate()
    request = gate.create_request(
        topic="猫の意外な雑学",
        stage="review",
        reason="Retry limit reached.",
        ceo_action="stop",
        quality_feedback={"decision": "修正必要", "score": 0.0},
        script_result="script",
        review_result=approved_review(),
    )
    pipeline, _, _, _, image, voice, editor, composer, publisher = make_pipeline()

    with pytest.raises(ValueError):
        gate.build_resume_context(request, script_artifact=make_script_artifact())

    assert image.calls == []
    assert voice.calls == []
    assert editor.calls == []
    assert composer.calls == []
    assert publisher.calls == []


def test_rejected_request_cannot_build_resume_context_and_production_is_not_called():
    gate = make_gate()
    request = gate.create_request(
        topic="猫の意外な雑学",
        stage="review",
        reason="Retry limit reached.",
        ceo_action="stop",
        quality_feedback={"decision": "修正必要", "score": 0.0},
        script_result="script",
        review_result=approved_review(),
    )
    gate.reject(request)
    pipeline, _, _, _, image, voice, editor, composer, publisher = make_pipeline()

    with pytest.raises(ValueError):
        gate.build_resume_context(request, script_artifact=make_script_artifact())

    assert image.calls == []
    assert voice.calls == []
    assert editor.calls == []
    assert composer.calls == []
    assert publisher.calls == []


def test_normal_run_still_uses_existing_production_flow():
    pipeline, researcher, writer, reviewer, image, voice, editor, composer, publisher = (
        make_pipeline()
    )

    result = pipeline.run("猫の意外な雑学")

    assert researcher.calls
    assert writer.calls
    assert reviewer.calls
    assert result["production_resumed"] is False
    assert image.calls
    assert voice.calls
    assert publisher.calls


def test_stop_approved_resume_runs_production_after_initial_skip():
    gate = make_gate()
    pipeline, researcher, writer, reviewer, image, voice, editor, composer, publisher = (
        make_pipeline()
    )
    pipeline.ceo_decision_policy = StopPolicy()
    pipeline.stop_on_ceo_stop = True
    pipeline.human_approval_gate = gate
    pipeline.require_human_approval_on_stop = True
    pipeline.approval_decision = "approved"
    pipeline.resume_approved_production_enabled = True

    result = pipeline.run("猫の意外な雑学")

    assert len(researcher.calls) == 1
    assert len(writer.calls) == 1
    assert len(reviewer.calls) == 1
    assert result["stopped"] is True
    assert result["production_skipped"] is True
    assert result["production_resumed"] is True
    assert result["production_resume_completed"] is True
    assert image.calls == ["script"]
    assert voice.calls == ["script"]
    assert publisher.calls


def test_resume_failure_records_error_without_completing_production():
    pipeline, _, _, _, image, voice, editor, composer, publisher = make_pipeline(
        image_generator=FakeImageGenerator(fail=True)
    )

    result = pipeline.resume_approved_production(make_resume_context())

    assert result["production_resumed"] is True
    assert result["production_resume_completed"] is False
    assert result["approval_resume_result"]["error"] == "image failed"
    assert image.calls
    assert voice.calls == []
    assert editor.calls == []
    assert composer.calls == []
    assert publisher.calls == []
