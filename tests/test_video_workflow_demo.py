from main_v12_video_workflow_demo import run_demo


class FakeImageGenerator:
    def __init__(self):
        self.prompts = []

    def generate(self, prompt):
        self.prompts.append(prompt)
        return "fake_image.png"


class FakeVoiceGenerator:
    def __init__(self):
        self.texts = []

    def generate(self, text):
        self.texts.append(text)
        return "fake_voice.wav"


class FakeEditor:
    def __init__(self):
        self.calls = []

    def generate(self, image_paths, audio_paths):
        self.calls.append(
            {
                "image_paths": image_paths,
                "audio_paths": audio_paths,
            }
        )
        return "fake_video.mp4"


def test_video_workflow_demo_calls_image_generator():
    image_generator = FakeImageGenerator()
    voice_generator = FakeVoiceGenerator()
    editor = FakeEditor()

    run_demo(
        image_generator=image_generator,
        voice_generator=voice_generator,
        editor=editor,
    )

    assert image_generator.prompts == ["Image prompt for: 猫の意外な雑学"]


def test_video_workflow_demo_calls_voice_generator():
    image_generator = FakeImageGenerator()
    voice_generator = FakeVoiceGenerator()
    editor = FakeEditor()

    run_demo(
        image_generator=image_generator,
        voice_generator=voice_generator,
        editor=editor,
    )

    assert voice_generator.texts == ["Voice script for: 猫の意外な雑学"]


def test_video_workflow_demo_calls_editor_generator():
    image_generator = FakeImageGenerator()
    voice_generator = FakeVoiceGenerator()
    editor = FakeEditor()

    run_demo(
        image_generator=image_generator,
        voice_generator=voice_generator,
        editor=editor,
    )

    assert editor.calls == [
        {
            "image_paths": ["fake_image.png"],
            "audio_paths": ["fake_voice.wav"],
        }
    ]


def test_video_workflow_demo_returns_final_video_path():
    result = run_demo(
        image_generator=FakeImageGenerator(),
        voice_generator=FakeVoiceGenerator(),
        editor=FakeEditor(),
    )

    assert result["video_path"] == "fake_video.mp4"


def test_video_workflow_demo_returns_all_generated_paths():
    result = run_demo(
        image_generator=FakeImageGenerator(),
        voice_generator=FakeVoiceGenerator(),
        editor=FakeEditor(),
    )

    assert result == {
        "topic": "猫の意外な雑学",
        "image_path": "fake_image.png",
        "voice_path": "fake_voice.wav",
        "video_path": "fake_video.mp4",
    }
