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
        return {"status": "dry_run", "video_path": task.input_data["video_path"]}


def approved_review():
    return "【評価】\n良い台本です。\n\n【改善点】\nなし\n\n【判定】\n合格"


def needs_revision_review(improvement="冒頭の引きを強くする"):
    return f"【評価】\n構成が弱いです。\n\n【改善点】\n{improvement}\n\n【判定】\n修正必要"


def unknown_review():
    return "review result without fixed sections"


def make_pipeline(writer, reviewer, quality_retry_limit=0):
    return FullAutoVideoPipeline(
        researcher=FakeResearcher(),
        writer=writer,
        reviewer=reviewer,
        image_generator=FakeImageGenerator(),
        voice_generator=FakeVoiceGenerator(),
        editor=FakeEditor(),
        publisher=FakePublisher(),
        quality_retry_limit=quality_retry_limit,
    )


def test_quality_retry_initial_pass_does_not_retry():
    writer = FakeWriter(["script v1"])
    reviewer = FakeReviewer([approved_review()])

    result = make_pipeline(writer, reviewer, quality_retry_limit=2).run("猫の意外な雑学")

    assert len(writer.inputs) == 1
    assert len(reviewer.inputs) == 1
    assert result["quality_retry_count"] == 0
    assert len(result["quality_retry_history"]) == 1
    assert result["quality_feedback"]["decision"] == "合格"


def test_quality_retry_rewrites_once_then_passes():
    writer = FakeWriter(["script v1", "script fixed"])
    reviewer = FakeReviewer([needs_revision_review(), approved_review()])

    result = make_pipeline(writer, reviewer, quality_retry_limit=2).run("猫の意外な雑学")

    assert len(writer.inputs) == 2
    assert len(reviewer.inputs) == 2
    assert result["quality_retry_count"] == 1
    assert len(result["quality_retry_history"]) == 2
    assert result["script_result"] == "script fixed"
    assert result["review_result"] == approved_review()
    assert result["quality_feedback"]["decision"] == "合格"


def test_quality_retry_stops_at_limit():
    writer = FakeWriter(["script v1", "script v2", "script v3"])
    reviewer = FakeReviewer(
        [
            needs_revision_review("改善1"),
            needs_revision_review("改善2"),
            needs_revision_review("改善3"),
        ]
    )

    result = make_pipeline(writer, reviewer, quality_retry_limit=2).run("猫の意外な雑学")

    assert len(writer.inputs) == 3
    assert len(reviewer.inputs) == 3
    assert result["quality_retry_count"] == 2
    assert len(result["quality_retry_history"]) == 3
    assert result["quality_feedback"]["decision"] == "修正必要"


def test_quality_retry_limit_zero_preserves_single_pass_behavior():
    writer = FakeWriter(["script v1", "script v2"])
    reviewer = FakeReviewer([needs_revision_review(), approved_review()])

    result = make_pipeline(writer, reviewer, quality_retry_limit=0).run("猫の意外な雑学")

    assert len(writer.inputs) == 1
    assert len(reviewer.inputs) == 1
    assert result["quality_retry_count"] == 0
    assert result["quality_feedback"]["decision"] == "修正必要"


def test_quality_retry_unknown_decision_does_not_retry():
    writer = FakeWriter(["script v1", "script v2"])
    reviewer = FakeReviewer([unknown_review(), approved_review()])

    result = make_pipeline(writer, reviewer, quality_retry_limit=2).run("猫の意外な雑学")

    assert len(writer.inputs) == 1
    assert len(reviewer.inputs) == 1
    assert result["quality_retry_count"] == 0
    assert result["quality_feedback"]["decision"] == "不明"


def test_quality_retry_revision_input_contains_feedback_context():
    writer = FakeWriter(["script v1", "script fixed"])
    reviewer = FakeReviewer(
        [
            needs_revision_review("冒頭の引きを強くする"),
            approved_review(),
        ]
    )

    make_pipeline(writer, reviewer, quality_retry_limit=1).run("猫の意外な雑学")

    revision_input = writer.inputs[1]
    assert "research result" in revision_input
    assert "script v1" in revision_input
    assert "冒頭の引きを強くする" in revision_input
    assert "構成が弱いです。" in revision_input
