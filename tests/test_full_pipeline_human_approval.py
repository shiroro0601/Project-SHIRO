from company.approval.human_approval import HumanApprovalGate
from company.core.ceo_decision import ACTION_PROCEED, ACTION_STOP, CEODecision
from main_v12_full_video_company_dry_run import FullAutoVideoPipeline


class FakeResearcher:
    def execute(self, input_text):
        return "research"


class FakeWriter:
    def execute(self, input_text):
        return "script"


class FakeReviewer:
    def __init__(self, result=None):
        self.result = result or needs_revision_review()

    def execute(self, input_text):
        return self.result


class FakeImageGenerator:
    def __init__(self):
        self.calls = []

    def generate(self, prompt):
        self.calls.append(prompt)
        return "image.png"


class FakeVoiceGenerator:
    def __init__(self):
        self.calls = []

    def generate(self, text):
        self.calls.append(text)
        return "voice.wav"


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
        return {"status": "dry_run"}


class FixedDecisionPolicy:
    def __init__(self, action, reason="fixed decision"):
        self.action = action
        self.reason = reason

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
            action=self.action,
            reason=self.reason,
            stage=stage,
            quality_decision=getattr(quality_feedback, "decision", ""),
            quality_score=getattr(quality_feedback, "score", 0.5),
            retry_count=retry_count,
            metadata={},
        )


def approved_review():
    return "【評価】\n良い台本です。\n\n【改善点】\nなし\n\n【判定】\n合格"


def needs_revision_review():
    return "【評価】\n構成が弱いです。\n\n【改善点】\n冒頭を改善\n\n【判定】\n修正必要"


def make_gate():
    values = iter(["approval-1"])
    times = iter(["2026-07-11T10:00:00", "2026-07-11T10:01:00"])
    return HumanApprovalGate(id_factory=lambda: next(values), clock=lambda: next(times))


def make_pipeline(
    *,
    action=ACTION_STOP,
    reviewer=None,
    human_approval_gate=None,
    require_human_approval_on_stop=False,
    approval_decision=None,
):
    image = FakeImageGenerator()
    voice = FakeVoiceGenerator()
    editor = FakeEditor()
    publisher = FakePublisher()
    pipeline = FullAutoVideoPipeline(
        researcher=FakeResearcher(),
        writer=FakeWriter(),
        reviewer=reviewer or FakeReviewer(),
        image_generator=image,
        voice_generator=voice,
        editor=editor,
        publisher=publisher,
        ceo_decision_policy=FixedDecisionPolicy(action, "Retry limit reached."),
        stop_on_ceo_stop=True,
        human_approval_gate=human_approval_gate,
        require_human_approval_on_stop=require_human_approval_on_stop,
        approval_decision=approval_decision,
        approval_decided_by="Koshi",
        approval_comment="確認済み",
    )
    return pipeline, image, voice, editor, publisher


def test_human_approval_pending_request_created_on_strict_ceo_stop():
    pipeline, image, voice, editor, publisher = make_pipeline(
        human_approval_gate=make_gate(),
        require_human_approval_on_stop=True,
    )

    result = pipeline.run("猫の意外な雑学")

    assert result["stopped"] is True
    assert result["production_skipped"] is True
    assert result["approval_required"] is True
    assert result["approval_status"] == "pending"
    assert result["approval_request"]["approval_id"] == "approval-1"
    assert result["approval_request"]["stage"] == "review"
    assert result["approval_request"]["reason"] == "Retry limit reached."
    assert result["approval_decision"] is None
    assert image.calls == []
    assert voice.calls == []
    assert editor.calls == []
    assert publisher.calls == []


def test_human_approval_disabled_keeps_plain_strict_stop():
    pipeline, image, voice, editor, publisher = make_pipeline(
        human_approval_gate=make_gate(),
        require_human_approval_on_stop=False,
    )

    result = pipeline.run("猫の意外な雑学")

    assert result["stopped"] is True
    assert result["approval_required"] is False
    assert result["approval_status"] == "not_required"
    assert image.calls == []
    assert voice.calls == []
    assert editor.calls == []
    assert publisher.calls == []


def test_ceo_proceed_does_not_require_approval_and_runs_production():
    pipeline, image, voice, editor, publisher = make_pipeline(
        action=ACTION_PROCEED,
        reviewer=FakeReviewer(approved_review()),
        human_approval_gate=make_gate(),
        require_human_approval_on_stop=True,
    )

    result = pipeline.run("猫の意外な雑学")

    assert result["stopped"] is False
    assert result["approval_required"] is False
    assert image.calls
    assert voice.calls
    assert publisher.calls


def test_policy_missing_does_not_require_approval_and_runs_production():
    image = FakeImageGenerator()
    voice = FakeVoiceGenerator()
    editor = FakeEditor()
    publisher = FakePublisher()
    pipeline = FullAutoVideoPipeline(
        researcher=FakeResearcher(),
        writer=FakeWriter(),
        reviewer=FakeReviewer(approved_review()),
        image_generator=image,
        voice_generator=voice,
        editor=editor,
        publisher=publisher,
        stop_on_ceo_stop=True,
        human_approval_gate=make_gate(),
        require_human_approval_on_stop=True,
    )

    result = pipeline.run("猫の意外な雑学")

    assert result["ceo_decision"] is None
    assert result["approval_required"] is False
    assert result["stopped"] is False
    assert image.calls
    assert voice.calls
    assert publisher.calls


def test_approval_decision_approved_is_recorded_without_resuming_production():
    pipeline, image, voice, editor, publisher = make_pipeline(
        human_approval_gate=make_gate(),
        require_human_approval_on_stop=True,
        approval_decision="approved",
    )

    result = pipeline.run("猫の意外な雑学")

    assert result["approval_status"] == "approved"
    assert result["approval_decision"]["decision"] == "approved"
    assert result["approval_decision"]["decided_by"] == "Koshi"
    assert result["video_path"] == ""
    assert image.calls == []
    assert voice.calls == []
    assert editor.calls == []
    assert publisher.calls == []


def test_approval_decision_rejected_is_recorded_without_resuming_production():
    pipeline, image, voice, editor, publisher = make_pipeline(
        human_approval_gate=make_gate(),
        require_human_approval_on_stop=True,
        approval_decision="rejected",
    )

    result = pipeline.run("猫の意外な雑学")

    assert result["approval_status"] == "rejected"
    assert result["approval_decision"]["decision"] == "rejected"
    assert result["video_path"] == ""
    assert image.calls == []
    assert voice.calls == []
    assert editor.calls == []
    assert publisher.calls == []
