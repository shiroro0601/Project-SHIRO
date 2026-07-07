from company.artifacts.script_artifact import ScriptArtifact
from company.artifacts.scene_artifact import SceneArtifact
from company.publishers.youtube_studio_publisher import YouTubeStudioPublisher
from main_v12_full_video_company_dry_run import FullAutoVideoPipeline


class StaticRole:
    def __init__(self, output):
        self.output = output
        self.inputs = []

    def execute(self, input_text: str):
        self.inputs.append(input_text)
        return self.output


class RecordingImageGenerator:
    def __init__(self):
        self.prompts = []

    def generate(self, prompt: str) -> str:
        self.prompts.append(prompt)
        return "image.png"


class FakeVoiceGenerator:
    def generate(self, text: str) -> str:
        return "voice.wav"


class FakeEditor:
    def generate(self, image_paths: list[str], audio_paths: list[str]) -> str:
        return "video.mp4"


def _pipeline(tmp_path, writer_output: str, image_generator=None):
    return FullAutoVideoPipeline(
        researcher=StaticRole("research output"),
        writer=StaticRole(writer_output),
        reviewer=StaticRole("review output"),
        image_generator=image_generator or RecordingImageGenerator(),
        voice_generator=FakeVoiceGenerator(),
        editor=FakeEditor(),
        publisher=YouTubeStudioPublisher(dry_run=True, output_dir=str(tmp_path)),
    )


def test_pipeline_result_contains_script_artifact(tmp_path):
    writer_output = (
        "【タイトル】\n猫の意外な雑学\n\n"
        "【ナレーション】\n猫は狭い場所が好きです。\n\n"
        "【画像指示】\n猫が箱に入る"
    )

    result = _pipeline(tmp_path, writer_output).run("猫の意外な雑学")

    assert isinstance(result["script_artifact"], ScriptArtifact)
    assert result["script_artifact"].title == "猫の意外な雑学"
    assert result["script_artifact"].narration == "猫は狭い場所が好きです。"
    assert result["script_artifact"].scenes == [
        SceneArtifact(
            index=1,
            narration="猫は狭い場所が好きです。",
            image_prompt="猫が箱に入る",
            duration_seconds=60.0,
        )
    ]


def test_pipeline_keeps_script_result_compatibility(tmp_path):
    writer_output = "自由文の台本"

    result = _pipeline(tmp_path, writer_output).run("猫の意外な雑学")

    assert result["script_result"] == writer_output
    assert result["script_artifact"].raw_text == writer_output
    assert result["script_artifact"].scenes == [
        SceneArtifact(
            index=1,
            narration=writer_output,
            image_prompt=writer_output,
            duration_seconds=60.0,
        )
    ]


def test_pipeline_uses_script_artifact_image_prompts_for_image_step(tmp_path):
    image_generator = RecordingImageGenerator()
    writer_output = (
        "【タイトル】\n猫の意外な雑学\n\n"
        "【ナレーション】\n猫は狭い場所が好きです。\n\n"
        "【画像指示】\n"
        "- 猫が箱に入る\n"
        "- 猫のひげのクローズアップ"
    )

    result = _pipeline(tmp_path, writer_output, image_generator).run("猫の意外な雑学")

    assert result["script_artifact"].image_prompts == [
        "猫が箱に入る",
        "猫のひげのクローズアップ",
    ]
    assert image_generator.prompts == ["猫が箱に入る"]


def test_pipeline_uses_scene_image_prompt_before_image_prompts(tmp_path):
    image_generator = RecordingImageGenerator()
    writer_output = (
        "【タイトル】\n猫の意外な雑学\n\n"
        "【画像指示】\n旧形式の画像指示\n\n"
        "【シーン1】\n"
        "ナレーション: 猫は箱が好きです。\n"
        "画像: シーン形式の猫画像\n"
        "秒数: 5"
    )

    result = _pipeline(tmp_path, writer_output, image_generator).run("猫の意外な雑学")

    assert result["script_artifact"].scenes[0].image_prompt == "シーン形式の猫画像"
    assert image_generator.prompts == ["シーン形式の猫画像"]
