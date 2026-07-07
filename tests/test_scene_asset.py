from company.artifacts.scene_asset import SceneAsset


def test_scene_asset_can_be_created():
    scene_asset = SceneAsset(
        scene_index=1,
        image_path="scene_1.png",
        voice_path="scene_1.wav",
        narration="猫は狭い場所が好きです。",
        image_prompt="箱に入る猫",
        duration_seconds=5.0,
    )

    assert scene_asset.scene_index == 1
    assert scene_asset.image_path == "scene_1.png"
    assert scene_asset.voice_path == "scene_1.wav"
    assert scene_asset.narration == "猫は狭い場所が好きです。"
    assert scene_asset.image_prompt == "箱に入る猫"


def test_scene_asset_keeps_duration_as_float():
    scene_asset = SceneAsset(
        scene_index=2,
        image_path="scene_2.png",
        voice_path="scene_2.wav",
        narration="猫のひげはセンサーです。",
        image_prompt="猫のひげのクローズアップ",
        duration_seconds=6,
    )

    assert float(scene_asset.duration_seconds) == 6.0
