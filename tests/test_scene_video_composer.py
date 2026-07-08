from company.artifacts.scene_asset import SceneAsset
from company.video.scene_video_composer import FakeSceneVideoComposer


def test_fake_scene_video_composer_receives_scene_assets():
    composer = FakeSceneVideoComposer()
    scene_assets = [
        SceneAsset(
            scene_index=1,
            image_path="scene_1.png",
            voice_path="scene_1.wav",
            narration="猫は狭い場所が好きです。",
            image_prompt="箱に入る猫",
            duration_seconds=5.0,
        )
    ]

    composer.compose(scene_assets, "outputs/videos/final_video.mp4")

    assert composer.received_scene_assets == scene_assets


def test_fake_scene_video_composer_returns_output_path():
    composer = FakeSceneVideoComposer()

    result = composer.compose([], "outputs/videos/final_video.mp4")

    assert result == "outputs/videos/final_video.mp4"
    assert composer.output_path == "outputs/videos/final_video.mp4"
