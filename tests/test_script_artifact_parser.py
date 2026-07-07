from company.artifacts.scene_artifact import SceneArtifact
from company.artifacts.script_artifact_parser import ScriptArtifactParser


def test_script_artifact_parser_extracts_title():
    text = "【タイトル】\n猫の意外な雑学\n\n【ナレーション】\n猫はよく眠ります。"

    artifact = ScriptArtifactParser().parse(text)

    assert artifact.title == "猫の意外な雑学"


def test_script_artifact_parser_extracts_narration():
    text = "【タイトル】\n猫\n\n【ナレーション】\n猫はひげで幅を測ります。\n猫は夜目がききます。"

    artifact = ScriptArtifactParser().parse(text)

    assert artifact.narration == "猫はひげで幅を測ります。\n猫は夜目がききます。"


def test_script_artifact_parser_extracts_image_prompts():
    text = (
        "【タイトル】\n猫\n\n"
        "【ナレーション】\n猫の雑学です。\n\n"
        "【画像指示】\n"
        "- 猫が狭い箱に入るシーン\n"
        "- 猫のひげのクローズアップ"
    )

    artifact = ScriptArtifactParser().parse(text)

    assert artifact.image_prompts == [
        "猫が狭い箱に入るシーン",
        "猫のひげのクローズアップ",
    ]
    assert artifact.scenes == [
        SceneArtifact(
            index=1,
            narration="猫の雑学です。",
            image_prompt="猫が狭い箱に入るシーン",
            duration_seconds=60.0,
        )
    ]


def test_script_artifact_parser_falls_back_when_sections_are_missing():
    text = "自由文の台本です。猫の話をします。"

    artifact = ScriptArtifactParser().parse(text)

    assert artifact.title == "untitled"
    assert artifact.narration == text
    assert artifact.image_prompts == []
    assert artifact.scenes == [
        SceneArtifact(
            index=1,
            narration=text,
            image_prompt=text,
            duration_seconds=60.0,
        )
    ]


def test_script_artifact_parser_keeps_raw_text():
    text = "【タイトル】\n猫\n\n【ナレーション】\n猫の話"

    artifact = ScriptArtifactParser().parse(text)

    assert artifact.raw_text == text


def test_script_artifact_parser_parses_scene_format():
    text = (
        "【タイトル】\n猫の意外な雑学\n\n"
        "【シーン1】\n"
        "ナレーション: 猫は狭い場所が好きです。\n"
        "画像: 箱に入る猫\n"
        "秒数: 5"
    )

    artifact = ScriptArtifactParser().parse(text)

    assert artifact.title == "猫の意外な雑学"
    assert artifact.narration == "猫は狭い場所が好きです。"
    assert artifact.image_prompts == ["箱に入る猫"]
    assert artifact.scenes == [
        SceneArtifact(
            index=1,
            narration="猫は狭い場所が好きです。",
            image_prompt="箱に入る猫",
            duration_seconds=5.0,
        )
    ]


def test_script_artifact_parser_parses_multiple_scenes():
    text = (
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

    artifact = ScriptArtifactParser().parse(text)

    assert artifact.scenes == [
        SceneArtifact(
            index=1,
            narration="猫は狭い場所が好きです。",
            image_prompt="箱に入る猫",
            duration_seconds=5.0,
        ),
        SceneArtifact(
            index=2,
            narration="猫のひげはセンサーです。",
            image_prompt="猫のひげのクローズアップ",
            duration_seconds=6.0,
        ),
    ]


def test_script_artifact_parser_keeps_legacy_format_supported():
    text = (
        "【タイトル】\n猫\n\n"
        "【ナレーション】\n猫はひげで幅を測ります。\n\n"
        "【画像指示】\n猫のひげのクローズアップ"
    )

    artifact = ScriptArtifactParser().parse(text)

    assert artifact.scenes == [
        SceneArtifact(
            index=1,
            narration="猫はひげで幅を測ります。",
            image_prompt="猫のひげのクローズアップ",
            duration_seconds=60.0,
        )
    ]
