from company.core.employee_role import ResearchRole, ReviewerRole, WriterRole
from company.publishers.youtube_studio_publisher import YouTubeStudioPublisher
from main_v12_full_video_company_dry_run import FullAutoVideoPipeline, run_demo


class RecordingRole:
    def __init__(self, result):
        self.result = result
        self.inputs = []

    def execute(self, input_text: str):
        self.inputs.append(input_text)
        return self.result


class FakeProvider:
    def __init__(self):
        self.prompts = []

    def generate(self, prompt: str) -> str:
        self.prompts.append(prompt)
        if "YouTubeショート動画のリサーチャー" in prompt:
            return "fake research result"
        if "YouTubeショート動画の台本作家" in prompt:
            return "fake script result"
        if "YouTubeショート動画の編集長" in prompt:
            return "fake review result"
        return "fake text result"


class FakeImageGenerator:
    def generate(self, prompt: str) -> str:
        return "fake_image.png"


class FakeVoiceGenerator:
    def generate(self, text: str) -> str:
        return "fake_voice.wav"


class FakeEditor:
    def generate(self, image_paths: list[str], audio_paths: list[str]) -> str:
        return "fake_video.mp4"


def _publisher(tmp_path):
    return YouTubeStudioPublisher(dry_run=True, output_dir=str(tmp_path))


def test_injected_ai_roles_are_called_in_handoff_order(tmp_path):
    researcher = RecordingRole("research output")
    writer = RecordingRole("script output")
    reviewer = RecordingRole("review output")
    pipeline = FullAutoVideoPipeline(
        researcher=researcher,
        writer=writer,
        reviewer=reviewer,
        image_generator=FakeImageGenerator(),
        voice_generator=FakeVoiceGenerator(),
        editor=FakeEditor(),
        publisher=_publisher(tmp_path),
    )

    result = pipeline.run("猫の意外な雑学")

    assert researcher.inputs == ["猫の意外な雑学"]
    assert writer.inputs == ["research output"]
    assert reviewer.inputs == ["script output"]
    assert result["research_result"] == "research output"
    assert result["script_result"] == "script output"
    assert result["review_result"] == "review output"
    assert result["execution_order"] == [
        "Researcher",
        "Writer",
        "Reviewer",
        "Image",
        "Voice",
        "Editor",
        "Publisher",
    ]


def test_injected_provider_powered_roles_work_with_pipeline(tmp_path):
    provider = FakeProvider()
    pipeline = FullAutoVideoPipeline(
        researcher=ResearchRole(provider=provider),
        writer=WriterRole(provider=provider),
        reviewer=ReviewerRole(provider=provider),
        image_generator=FakeImageGenerator(),
        voice_generator=FakeVoiceGenerator(),
        editor=FakeEditor(),
        publisher=_publisher(tmp_path),
    )

    result = pipeline.run("猫の意外な雑学")

    assert result["research_result"] == "fake research result"
    assert result["script_result"] == "fake script result"
    assert result["review_result"] == "fake review result"
    assert len(provider.prompts) == 3
    assert "猫の意外な雑学" in provider.prompts[0]
    assert "fake research result" in provider.prompts[1]
    assert "fake script result" in provider.prompts[2]


def test_existing_fake_pipeline_compatibility_is_preserved(tmp_path):
    provider = FakeProvider()

    result = run_demo(
        text_provider=provider,
        image_generator=FakeImageGenerator(),
        voice_generator=FakeVoiceGenerator(),
        editor=FakeEditor(),
        publisher=_publisher(tmp_path),
    )

    assert result["research_result"] == "fake research result"
    assert result["script_result"] == "fake script result"
    assert result["review_result"] == "fake review result"
    assert result["image_path"] == "fake_image.png"
    assert result["voice_path"] == "fake_voice.wav"
    assert result["video_path"] == "fake_video.mp4"
    assert result["publish_result"]["status"] == "dry_run"
