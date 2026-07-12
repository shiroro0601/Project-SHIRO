from company.youtube.studio_upload import YouTubeVideoMetadata


def test_metadata_model_trims_title():
    metadata = YouTubeVideoMetadata(
        title="  猫の意外な雑学  ",
        description="説明",
        made_for_kids=False,
    )

    assert metadata.title == "猫の意外な雑学"


def test_metadata_model_preserves_description_newlines():
    metadata = YouTubeVideoMetadata(
        title="猫",
        description="1行目\n2行目",
        made_for_kids=False,
    )

    assert metadata.description == "1行目\n2行目"


def test_metadata_model_normalizes_tags_without_mutating_input():
    tags = [" 猫 ", "", "雑学", "猫", "Shorts"]

    metadata = YouTubeVideoMetadata(
        title="猫",
        description="説明",
        made_for_kids=False,
        tags=tags,
    )

    assert metadata.tags == ("猫", "雑学", "Shorts")
    assert tags == [" 猫 ", "", "雑学", "猫", "Shorts"]
