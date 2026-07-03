from company.publishers.youtube_studio_publisher import YouTubeStudioPublisher
from main_v12_full_video_company_dry_run import run_demo


class FakeProvider:
    def __init__(self):
        self.prompts = []

    def generate(self, prompt: str) -> str:
        self.prompts.append(prompt)
        if "調査してください" in prompt:
            return "fake research result"
        if "台本を書いてください" in prompt:
            return "fake script result"
        if "レビューしてください" in prompt:
            return "fake review result"
        return "fake text result"


class FakeImageGenerator:
    def __init__(self):
        self.prompts = []

    def generate(self, prompt: str) -> str:
        self.prompts.append(prompt)
        return "fake_image.png"


class FakeVoiceGenerator:
    def __init__(self):
        self.texts = []

    def generate(self, text: str) -> str:
        self.texts.append(text)
        return "fake_voice.wav"


class FakeEditor:
    def __init__(self):
        self.calls = []

    def generate(self, image_paths: list[str], audio_paths: list[str]) -> str:
        self.calls.append(
            {
                "image_paths": image_paths,
                "audio_paths": audio_paths,
            }
        )
        return "fake_video.mp4"


class RecordingDryRunPublisher:
    def __init__(self, output_dir: str):
        self.publisher = YouTubeStudioPublisher(dry_run=True, output_dir=output_dir)
        self.tasks = []

    def generate(self, task):
        self.tasks.append(task)
        return self.publisher.generate(task)


def _run(tmp_path):
    provider = FakeProvider()
    image_generator = FakeImageGenerator()
    voice_generator = FakeVoiceGenerator()
    editor = FakeEditor()
    publisher = RecordingDryRunPublisher(output_dir=str(tmp_path))

    result = run_demo(
        text_provider=provider,
        image_generator=image_generator,
        voice_generator=voice_generator,
        editor=editor,
        publisher=publisher,
    )

    return result, provider, image_generator, voice_generator, editor, publisher


def test_full_video_company_dry_run_executes_all_roles_in_order(tmp_path):
    result, *_ = _run(tmp_path)

    assert result["execution_order"] == [
        "Researcher",
        "Writer",
        "Reviewer",
        "Image",
        "Voice",
        "Editor",
        "Publisher",
    ]


def test_full_video_company_dry_run_executes_text_roles(tmp_path):
    result, provider, *_ = _run(tmp_path)

    assert result["research_result"] == "fake research result"
    assert result["script_result"] == "fake script result"
    assert result["review_result"] == "fake review result"
    assert len(provider.prompts) == 3


def test_full_video_company_dry_run_executes_image_and_voice(tmp_path):
    result, _, image_generator, voice_generator, *_ = _run(tmp_path)

    assert result["image_path"] == "fake_image.png"
    assert result["voice_path"] == "fake_voice.wav"
    assert image_generator.prompts == ["Image prompt for: 猫の意外な雑学"]
    assert voice_generator.texts == ["Voice script for: 猫の意外な雑学"]


def test_full_video_company_dry_run_executes_editor(tmp_path):
    result, _, _, _, editor, _ = _run(tmp_path)

    assert result["video_path"] == "fake_video.mp4"
    assert editor.calls == [
        {
            "image_paths": ["fake_image.png"],
            "audio_paths": ["fake_voice.wav"],
        }
    ]


def test_full_video_company_dry_run_executes_publisher(tmp_path):
    result, *_, publisher = _run(tmp_path)

    assert result["publish_result"]["status"] == "dry_run"
    assert publisher.tasks


def test_full_video_company_dry_run_publish_result_contains_video_path(tmp_path):
    result, *_ = _run(tmp_path)

    assert result["publish_result"]["video_path"] == "fake_video.mp4"
