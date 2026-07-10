from company.core.ceo_decision import CEODecisionPolicy
from main_v12_full_video_company_dry_run import FullAutoVideoPipeline


class FakeResearcher:
    def __init__(self, results):
        self.results = list(results)
        self.inputs = []

    def execute(self, input_text):
        self.inputs.append(input_text)
        index = min(len(self.inputs) - 1, len(self.results) - 1)
        return self.results[index]


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


def approved_review():
    return "【評価】\n良い台本です。\n\n【改善点】\nなし\n\n【判定】\n合格"


def needs_revision_review():
    return "【評価】\n構成が弱いです。\n\n【改善点】\n冒頭を改善\n\n【判定】\n修正必要"


def make_pipeline(
    researcher,
    writer,
    reviewer,
    research_retry_limit=0,
    quality_retry_limit=0,
    ceo_decision_policy=None,
):
    return FullAutoVideoPipeline(
        researcher=researcher,
        writer=writer,
        reviewer=reviewer,
        image_generator=FakeImageGenerator(),
        voice_generator=FakeVoiceGenerator(),
        editor=FakeEditor(),
        publisher=FakePublisher(),
        research_retry_limit=research_retry_limit,
        quality_retry_limit=quality_retry_limit,
        ceo_decision_policy=ceo_decision_policy,
    )


def test_research_retry_runs_again_when_initial_research_is_empty():
    researcher = FakeResearcher(["", "猫はひげで幅を測ります。"])
    writer = FakeWriter(["script empty", "script researched"])
    reviewer = FakeReviewer([approved_review(), approved_review()])

    result = make_pipeline(
        researcher,
        writer,
        reviewer,
        research_retry_limit=1,
        ceo_decision_policy=CEODecisionPolicy(),
    ).run("猫の意外な雑学")

    assert len(researcher.inputs) == 2
    assert len(writer.inputs) == 2
    assert len(reviewer.inputs) == 2
    assert result["research_retry_count"] == 1
    assert len(result["research_retry_history"]) == 2
    assert [item["action"] for item in result["ceo_decision_history"]] == [
        "research_again",
        "proceed",
    ]
    assert result["research_result"] == "猫はひげで幅を測ります。"


def test_research_retry_limit_zero_stops_without_research_retry():
    researcher = FakeResearcher([""])
    writer = FakeWriter(["script empty"])
    reviewer = FakeReviewer([approved_review()])

    result = make_pipeline(
        researcher,
        writer,
        reviewer,
        research_retry_limit=0,
        ceo_decision_policy=CEODecisionPolicy(),
    ).run("猫の意外な雑学")

    assert len(researcher.inputs) == 1
    assert result["research_retry_count"] == 0
    assert result["ceo_decision"]["action"] == "stop"


def test_research_retry_stops_when_research_stays_empty_until_limit():
    researcher = FakeResearcher(["", "", ""])
    writer = FakeWriter(["script 1", "script 2", "script 3"])
    reviewer = FakeReviewer([approved_review(), approved_review(), approved_review()])

    result = make_pipeline(
        researcher,
        writer,
        reviewer,
        research_retry_limit=2,
        ceo_decision_policy=CEODecisionPolicy(),
    ).run("猫の意外な雑学")

    assert len(researcher.inputs) == 3
    assert result["research_retry_count"] == 2
    assert result["ceo_decision"]["action"] == "stop"


def test_research_retry_does_not_run_when_research_is_available():
    researcher = FakeResearcher(["猫の調査結果"])
    writer = FakeWriter(["script"])
    reviewer = FakeReviewer([approved_review()])

    result = make_pipeline(
        researcher,
        writer,
        reviewer,
        research_retry_limit=2,
        ceo_decision_policy=CEODecisionPolicy(),
    ).run("猫の意外な雑学")

    assert len(researcher.inputs) == 1
    assert result["research_retry_count"] == 0
    assert result["ceo_decision"]["action"] == "proceed"


def test_research_retry_does_not_run_without_ceo_policy():
    researcher = FakeResearcher([""])
    writer = FakeWriter(["script"])
    reviewer = FakeReviewer([approved_review()])

    result = make_pipeline(
        researcher,
        writer,
        reviewer,
        research_retry_limit=2,
    ).run("猫の意外な雑学")

    assert len(researcher.inputs) == 1
    assert result["research_retry_count"] == 0
    assert result["ceo_decision"] is None


def test_quality_retry_can_run_after_research_retry():
    researcher = FakeResearcher(["", "猫の調査結果"])
    writer = FakeWriter(["script empty", "script v1", "script fixed"])
    reviewer = FakeReviewer(
        [
            approved_review(),
            needs_revision_review(),
            approved_review(),
        ]
    )

    result = make_pipeline(
        researcher,
        writer,
        reviewer,
        research_retry_limit=1,
        quality_retry_limit=1,
        ceo_decision_policy=CEODecisionPolicy(),
    ).run("猫の意外な雑学")

    assert result["research_retry_count"] == 1
    assert result["quality_retry_count"] == 1
    assert [item["action"] for item in result["ceo_decision_history"]] == [
        "research_again",
        "revise",
        "proceed",
    ]


def test_research_retry_input_contains_topic_previous_result_and_reason():
    researcher = FakeResearcher(["", "猫の調査結果"])
    writer = FakeWriter(["script empty", "script researched"])
    reviewer = FakeReviewer([approved_review(), approved_review()])

    make_pipeline(
        researcher,
        writer,
        reviewer,
        research_retry_limit=1,
        ceo_decision_policy=CEODecisionPolicy(),
    ).run("猫の意外な雑学")

    retry_input = researcher.inputs[1]
    assert "猫の意外な雑学" in retry_input
    assert "【前回の調査結果】" in retry_input
    assert "Research result is missing and should be regenerated." in retry_input
