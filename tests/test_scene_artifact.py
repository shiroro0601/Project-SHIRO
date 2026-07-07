from company.artifacts.scene_artifact import SceneArtifact


def test_scene_artifact_can_be_created():
    scene = SceneArtifact(
        index=1,
        narration="猫は狭い場所が好きです。",
        image_prompt="箱に入る猫",
        duration_seconds=5.0,
    )

    assert scene.index == 1
    assert scene.narration == "猫は狭い場所が好きです。"
    assert scene.image_prompt == "箱に入る猫"


def test_scene_artifact_keeps_duration_as_float():
    scene = SceneArtifact(
        index=2,
        narration="猫のひげはセンサーです。",
        image_prompt="猫のひげのクローズアップ",
        duration_seconds=6,
    )

    assert float(scene.duration_seconds) == 6.0
