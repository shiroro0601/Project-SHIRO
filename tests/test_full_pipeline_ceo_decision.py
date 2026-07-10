from company.core.ceo_decision import (
    ACTION_RESEARCH_AGAIN,
    CEODecision,
    CEODecisionPolicy,
)
from main_v12_full_video_company_dry_run import FullAutoVideoPipeline


class FakeResearcher:
    def __init__(self, result="research result"):
        self.result = result
        self.inputs = []

    def execute(self, input_text):
        self.inputs.append(input_text)
        return self.result


class FakeWriter:
    def __init__(self, results):
        self.results = list(results)
        self.inputs = []

    def execute(self, input_text):
        self.inputs.append(input_text)
        index = min(len(self.inputs) - 1, len(self.results) - 1)
        return self.results[index]


class FakeReviewer:
    def __init__(self, results):
        self.results = list(results)
        self.inputs = []

    def execute(self, input_text):
        self.inputs.append(input_text)
        index = min(len(self.inputs) - 1, len(self.results) - 1)
        return self.results[index]


class FakeImageGenerator:
    def generate(self, prompt):
        return "image.png"


class FakeVoiceGenerator:
    def generate(self, text):
        return "voice.wav"


class FakeEditor:
    def generate(self, image_paths, audio_paths):
        return "video.mp4"


class FakePublisher:
    def generate(self, task):
        return {"status": "dry_run"}


class ResearchAgainPolicy:
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
            action=ACTION_RESEARCH_AGAIN,
            reason="Research should be refreshed.",
            stage=stage,
            quality_decision=getattr(quality_feedback, "decision", ""),
            quality_score=getattr(quality_feedback, "score", 0.0),
            retry_count=retry_count,
            metadata={},
        )


def approved_review():
    return "【評価】\n良い台本です。\n\n【改善点】\nなし\n\n【判定】\n合格"


def needs_revision_review():
    return "【評価】\n構成が弱いです。\n\n【改善点】\n冒頭を改善\n\n【判定】\n修正必要"


def make_pipeline(
    researcher=None,
    writer=None,
    reviewer=None,
    quality_retry_limit=0,
    ceo_decision_policy=None,
):
    return FullAutoVideoPipeline(
        researcher=researcher or FakeResearcher(),
        writer=writer or FakeWriter(["script"]),
        reviewer=reviewer or FakeReviewer([approved_review()]),
        image_generator=FakeImageGenerator(),
        voice_generator=FakeVoiceGenerator(),
        editor=FakeEditor(),
        publisher=FakePublisher(),
        quality_retry_limit=quality_retry_limit,
        ceo_decision_policy=ceo_decision_policy,
    )


def test_ceo_decision_revise_then_proceed():
    writer = FakeWriter(["script v1", "script fixed"])
    reviewer = FakeReviewer([needs_revision_review(), approved_review()])

    result = make_pipeline(
        writer=writer,
        reviewer=reviewer,
        quality_retry_limit=2,
        ceo_decision_policy=CEODecisionPolicy(),
    ).run("猫の意外な雑学")

    assert result["quality_retry_count"] == 1
    assert [item["action"] for item in result["ceo_decision_history"]] == [
        "revise",
        "proceed",
    ]
    assert result["ceo_decision"]["action"] == "proceed"


def test_ceo_decision_stop_when_retry_limit_reached():
    writer = FakeWriter(["script v1"])
    reviewer = FakeReviewer([needs_revision_review()])

    result = make_pipeline(
        writer=writer,
        reviewer=reviewer,
        quality_retry_limit=0,
        ceo_decision_policy=CEODecisionPolicy(),
    ).run("猫の意外な雑学")

    assert result["quality_retry_count"] == 0
    assert result["ceo_decision"]["action"] == "stop"
    assert result["ceo_decision_history"][0]["action"] == "stop"


def test_pipeline_without_ceo_policy_keeps_quality_retry_behavior():
    writer = FakeWriter(["script v1", "script fixed"])
    reviewer = FakeReviewer([needs_revision_review(), approved_review()])

    result = make_pipeline(
        writer=writer,
        reviewer=reviewer,
        quality_retry_limit=1,
    ).run("猫の意外な雑学")

    assert result["quality_retry_count"] == 1
    assert result["ceo_decision"] is None
    assert result["ceo_decision_history"] == []


def test_research_again_is_recorded_without_research_retry():
    researcher = FakeResearcher()
    writer = FakeWriter(["script v1"])
    reviewer = FakeReviewer([approved_review()])

    result = make_pipeline(
        researcher=researcher,
        writer=writer,
        reviewer=reviewer,
        quality_retry_limit=2,
        ceo_decision_policy=ResearchAgainPolicy(),
    ).run("猫の意外な雑学")

    assert researcher.inputs == ["猫の意外な雑学"]
    assert len(writer.inputs) == 1
    assert result["ceo_decision"]["action"] == "research_again"
    assert result["quality_retry_count"] == 0
