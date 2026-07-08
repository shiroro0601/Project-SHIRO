from company.publishers.youtube_studio_publisher import YouTubeStudioPublisher
from company.video.scene_video_composer import FakeSceneVideoComposer
from main_v12_full_video_company_dry_run import FullAutoVideoPipeline


class StaticRole:
    def __init__(self, output):
        self.output = output

    def execute(self, input_text: str):
        return self.output


class FakeImageGenerator:
    def generate(self, prompt: str) -> str:
        return f"image_for_{prompt}.png"


class FakeVoiceGenerator:
    def generate(self, text: str) -> str:
        return f"voice_for_{text}.wav"


class FailingEditor:
    def generate(self, image_paths: list[str], audio_paths: list[str]) -> str:
        raise AssertionError("legacy editor should not be called when composer is injected")


def _writer_output():
    return (
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


def test_pipeline_uses_scene_video_composer_for_scene_assets(tmp_path):
    composer = FakeSceneVideoComposer()
    pipeline = FullAutoVideoPipeline(
        researcher=StaticRole("research output"),
        writer=StaticRole(_writer_output()),
        reviewer=StaticRole("review output"),
        image_generator=FakeImageGenerator(),
        voice_generator=FakeVoiceGenerator(),
        editor=FailingEditor(),
        publisher=YouTubeStudioPublisher(dry_run=True, output_dir=str(tmp_path)),
        scene_video_composer=composer,
    )

    result = pipeline.run("猫の意外な雑学")

    assert len(result["scene_assets"]) == 2
    assert composer.received_scene_assets == result["scene_assets"]
    assert composer.output_path == "outputs/videos/final_video.mp4"
    assert result["scene_video_path"] == "outputs/videos/final_video.mp4"
    assert result["video_path"] == result["scene_video_path"]


def test_pipeline_keeps_scene_assets_and_script_compatibility(tmp_path):
    composer = FakeSceneVideoComposer()
    writer_output = _writer_output()
    pipeline = FullAutoVideoPipeline(
        researcher=StaticRole("research output"),
        writer=StaticRole(writer_output),
        reviewer=StaticRole("review output"),
        image_generator=FakeImageGenerator(),
        voice_generator=FakeVoiceGenerator(),
        editor=FailingEditor(),
        publisher=YouTubeStudioPublisher(dry_run=True, output_dir=str(tmp_path)),
        scene_video_composer=composer,
    )

    result = pipeline.run("猫の意外な雑学")

    assert result["script_result"] == writer_output
    assert result["script_artifact"].raw_text == writer_output
    assert result["scene_assets"]
    assert result["image_path"] == result["scene_assets"][0].image_path
    assert result["voice_path"] == result["scene_assets"][0].voice_path
