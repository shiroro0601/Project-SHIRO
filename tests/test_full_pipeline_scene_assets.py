from company.artifacts.scene_asset import SceneAsset
from company.publishers.youtube_studio_publisher import YouTubeStudioPublisher
from main_v12_full_video_company_dry_run import FullAutoVideoPipeline


class StaticRole:
    def __init__(self, output):
        self.output = output

    def execute(self, input_text: str):
        return self.output


class RecordingImageGenerator:
    def __init__(self):
        self.prompts = []

    def generate(self, prompt: str) -> str:
        self.prompts.append(prompt)
        return f"image_{len(self.prompts)}.png"


class RecordingVoiceGenerator:
    def __init__(self):
        self.texts = []

    def generate(self, text: str) -> str:
        self.texts.append(text)
        return f"voice_{len(self.texts)}.wav"


class FakeEditor:
    def generate(self, image_paths: list[str], audio_paths: list[str]) -> str:
        return "video.mp4"


def _pipeline(tmp_path, writer_output: str, image_generator, voice_generator):
    return FullAutoVideoPipeline(
        researcher=StaticRole("research output"),
        writer=StaticRole(writer_output),
        reviewer=StaticRole("review output"),
        image_generator=image_generator,
        voice_generator=voice_generator,
        editor=FakeEditor(),
        publisher=YouTubeStudioPublisher(dry_run=True, output_dir=str(tmp_path)),
    )


def test_pipeline_generates_scene_assets_per_scene(tmp_path):
    image_generator = RecordingImageGenerator()
    voice_generator = RecordingVoiceGenerator()
    writer_output = (
        "【タイトル】\n猫の意外な雑学\n\n"
        "【シーン1】\n"
        "ナレーション: 猫は狭い場所が好きです。\n"
        "画像: 箱に入る猫\n"
        "秒数: 5\n\n"
        "【シーン2】\n"
        "ナレーション: 猫のひげはセンサーです。\n"
        "画像: 猫のひげのクローズアップ\n"
        "秒数: 6"
    )

    result = _pipeline(
        tmp_path,
        writer_output,
        image_generator,
        voice_generator,
    ).run("猫の意外な雑学")

    assert image_generator.prompts == [
        "箱に入る猫",
        "猫のひげのクローズアップ",
    ]
    assert voice_generator.texts == [
        "猫は狭い場所が好きです。",
        "猫のひげはセンサーです。",
    ]
    assert result["scene_assets"] == [
        SceneAsset(
            scene_index=1,
            image_path="image_1.png",
            voice_path="voice_1.wav",
            narration="猫は狭い場所が好きです。",
            image_prompt="箱に入る猫",
            duration_seconds=5.0,
        ),
        SceneAsset(
            scene_index=2,
            image_path="image_2.png",
            voice_path="voice_2.wav",
            narration="猫のひげはセンサーです。",
            image_prompt="猫のひげのクローズアップ",
            duration_seconds=6.0,
        ),
    ]


def test_pipeline_keeps_representative_image_and_voice_paths(tmp_path):
    image_generator = RecordingImageGenerator()
    voice_generator = RecordingVoiceGenerator()
    writer_output = (
        "【シーン1】\n"
        "ナレーション: 代表音声です。\n"
        "画像: 代表画像です。\n"
        "秒数: 5\n\n"
        "【シーン2】\n"
        "ナレーション: 2つ目の音声です。\n"
        "画像: 2つ目の画像です。\n"
        "秒数: 6"
    )

    result = _pipeline(
        tmp_path,
        writer_output,
        image_generator,
        voice_generator,
    ).run("猫の意外な雑学")

    assert result["image_path"] == result["scene_assets"][0].image_path
    assert result["voice_path"] == result["scene_assets"][0].voice_path


def test_pipeline_keeps_script_result_and_script_artifact(tmp_path):
    image_generator = RecordingImageGenerator()
    voice_generator = RecordingVoiceGenerator()
    writer_output = (
        "【シーン1】\n"
        "ナレーション: 猫はよく眠ります。\n"
        "画像: 眠る猫\n"
        "秒数: 5"
    )

    result = _pipeline(
        tmp_path,
        writer_output,
        image_generator,
        voice_generator,
    ).run("猫の意外な雑学")

    assert result["script_result"] == writer_output
    assert result["script_artifact"].raw_text == writer_output
