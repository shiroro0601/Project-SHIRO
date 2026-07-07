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
        {"scene_number": 1, "image_prompt": "猫が狭い箱に入るシーン"},
        {"scene_number": 2, "image_prompt": "猫のひげのクローズアップ"},
    ]


def test_script_artifact_parser_falls_back_when_sections_are_missing():
    text = "自由文の台本です。猫の話をします。"

    artifact = ScriptArtifactParser().parse(text)

    assert artifact.title == "untitled"
    assert artifact.narration == text
    assert artifact.image_prompts == []
    assert artifact.scenes == []


def test_script_artifact_parser_keeps_raw_text():
    text = "【タイトル】\n猫\n\n【ナレーション】\n猫の話"

    artifact = ScriptArtifactParser().parse(text)

    assert artifact.raw_text == text
