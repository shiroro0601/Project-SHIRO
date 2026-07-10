from company.core.ceo_decision import ACTION_PROCEED, ACTION_STOP, CEODecision
from company.core.ceo_decision import CEODecisionPolicy
from main_v12_full_video_company_dry_run import FullAutoVideoPipeline


class FakeResearcher:
    def __init__(self, results=None):
        self.results = list(results or ["research result"])
        self.inputs = []

    def execute(self, input_text):
        self.inputs.append(input_text)
        index = min(len(self.inputs) - 1, len(self.results) - 1)
        return self.results[index]


class FakeWriter:
    def __init__(self, results=None):
        self.results = list(results or ["script result"])
        self.inputs = []

    def execute(self, input_text):
        self.inputs.append(input_text)
        index = min(len(self.inputs) - 1, len(self.results) - 1)
        return self.results[index]


class FakeReviewer:
    def __init__(self, results=None):
        self.results = list(results or [approved_review()])
        self.inputs = []

    def execute(self, input_text):
        self.inputs.append(input_text)
        index = min(len(self.inputs) - 1, len(self.results) - 1)
        return self.results[index]


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


class FakeEditor:
    def __init__(self):
        self.calls = []

    def generate(self, image_paths, audio_paths):
        self.calls.append((image_paths, audio_paths))
        return "video.mp4"


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
            quality_score=getattr(quality_feedback, "score", 0.0),
            retry_count=retry_count,
            metadata={},
        )


def approved_review():
    return "【評価】\n良い台本です。\n\n【改善点】\nなし\n\n【判定】\n合格"


def needs_revision_review():
    return "【評価】\n構成が弱いです。\n\n【改善点】\n冒頭を改善\n\n【判定】\n修正必要"


def make_pipeline(
    *,
    researcher=None,
    reviewer=None,
    ceo_decision_policy=None,
    stop_on_ceo_stop=False,
    quality_retry_limit=0,
    research_retry_limit=0,
):
    image_generator = FakeImageGenerator()
    voice_generator = FakeVoiceGenerator()
    editor = FakeEditor()
    composer = FakeSceneVideoComposer()
    publisher = FakePublisher()
    pipeline = FullAutoVideoPipeline(
        researcher=researcher or FakeResearcher(),
        writer=FakeWriter(),
        reviewer=reviewer or FakeReviewer(),
        image_generator=image_generator,
        voice_generator=voice_generator,
        editor=editor,
        publisher=publisher,
        scene_video_composer=composer,
        quality_retry_limit=quality_retry_limit,
        research_retry_limit=research_retry_limit,
        ceo_decision_policy=ceo_decision_policy,
        stop_on_ceo_stop=stop_on_ceo_stop,
    )
    return pipeline, image_generator, voice_generator, editor, composer, publisher


def test_stop_on_ceo_stop_skips_production_steps():
    pipeline, image, voice, editor, composer, publisher = make_pipeline(
        ceo_decision_policy=FixedDecisionPolicy(ACTION_STOP, "Retry limit reached."),
        stop_on_ceo_stop=True,
    )

    result = pipeline.run("猫の意外な雑学")

    assert result["stopped"] is True
    assert result["production_skipped"] is True
    assert result["stop_stage"] == "review"
    assert result["stop_reason"] == "Retry limit reached."
    assert image.calls == []
    assert voice.calls == []
    assert editor.calls == []
    assert composer.calls == []
    assert publisher.calls == []
    assert result["scene_assets"] == []
    assert result["image_path"] == ""
    assert result["voice_path"] == ""
    assert result["scene_video_path"] is None
    assert result["video_path"] == ""
    assert result["publish_result"] is None


def test_ceo_stop_without_strict_flag_keeps_existing_production_behavior():
    pipeline, image, voice, editor, composer, publisher = make_pipeline(
        ceo_decision_policy=FixedDecisionPolicy(ACTION_STOP),
        stop_on_ceo_stop=False,
    )

    result = pipeline.run("猫の意外な雑学")

    assert result["stopped"] is False
    assert result["production_skipped"] is False
    assert len(image.calls) == 1
    assert len(voice.calls) == 1
    assert composer.calls
    assert publisher.calls
    assert result["video_path"] == "outputs/videos/final_video.mp4"


def test_proceed_decision_with_strict_flag_runs_production():
    pipeline, image, voice, editor, composer, publisher = make_pipeline(
        ceo_decision_policy=FixedDecisionPolicy(ACTION_PROCEED),
        stop_on_ceo_stop=True,
    )

    result = pipeline.run("猫の意外な雑学")

    assert result["stopped"] is False
    assert len(image.calls) == 1
    assert len(voice.calls) == 1
    assert composer.calls
    assert publisher.calls


def test_stop_flag_without_policy_keeps_existing_behavior():
    pipeline, image, voice, editor, composer, publisher = make_pipeline(
        stop_on_ceo_stop=True,
    )

    result = pipeline.run("猫の意外な雑学")

    assert result["ceo_decision"] is None
    assert result["stopped"] is False
    assert len(image.calls) == 1
    assert len(voice.calls) == 1
    assert composer.calls
    assert publisher.calls


def test_research_retry_limit_stop_skips_production_in_strict_mode():
    pipeline, image, voice, editor, composer, publisher = make_pipeline(
        researcher=FakeResearcher(results=[""]),
        ceo_decision_policy=CEODecisionPolicy(),
        research_retry_limit=0,
        stop_on_ceo_stop=True,
    )

    result = pipeline.run("猫の意外な雑学")

    assert result["ceo_decision"]["action"] == ACTION_STOP
    assert result["stopped"] is True
    assert result["production_skipped"] is True
    assert image.calls == []
    assert voice.calls == []
    assert editor.calls == []
    assert composer.calls == []
    assert publisher.calls == []


def test_quality_retry_limit_stop_skips_production_in_strict_mode():
    pipeline, image, voice, editor, composer, publisher = make_pipeline(
        reviewer=FakeReviewer(results=[needs_revision_review()]),
        ceo_decision_policy=CEODecisionPolicy(),
        quality_retry_limit=0,
        stop_on_ceo_stop=True,
    )

    result = pipeline.run("猫の意外な雑学")

    assert result["ceo_decision"]["action"] == ACTION_STOP
    assert result["quality_feedback"]["decision"] == "修正必要"
    assert result["stopped"] is True
    assert result["production_skipped"] is True
    assert image.calls == []
    assert voice.calls == []
    assert editor.calls == []
    assert composer.calls == []
    assert publisher.calls == []
