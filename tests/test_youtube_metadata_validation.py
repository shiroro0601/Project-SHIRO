import pytest

from company.youtube.studio_upload import (
    YouTubeMetadataValidationError,
    YouTubeMetadataValidator,
    YouTubeVideoMetadata,
)


def validate(**kwargs):
    metadata = YouTubeVideoMetadata(
        title=kwargs.get("title", "猫の意外な雑学"),
        description=kwargs.get("description", "説明"),
        made_for_kids=kwargs.get("made_for_kids", False),
        tags=kwargs.get("tags", ("猫", "雑学")),
    )
    return YouTubeMetadataValidator().validate(metadata)


def test_validation_rejects_empty_title():
    with pytest.raises(YouTubeMetadataValidationError):
        validate(title=" ")


def test_validation_allows_100_character_title():
    assert validate(title="あ" * 100).title == "あ" * 100


def test_validation_rejects_101_character_title():
    with pytest.raises(YouTubeMetadataValidationError):
        validate(title="あ" * 101)


def test_validation_rejects_title_newline():
    with pytest.raises(YouTubeMetadataValidationError):
        validate(title="猫\n雑学")


def test_validation_allows_5000_character_description():
    assert validate(description="あ" * 5000).description == "あ" * 5000


def test_validation_rejects_5001_character_description():
    with pytest.raises(YouTubeMetadataValidationError):
        validate(description="あ" * 5001)


def test_validation_rejects_tag_with_comma():
    with pytest.raises(YouTubeMetadataValidationError):
        validate(tags=("猫,雑学",))


def test_validation_rejects_too_long_tag():
    with pytest.raises(YouTubeMetadataValidationError):
        validate(tags=("a" * 101,))


def test_validation_rejects_non_bool_made_for_kids():
    metadata = YouTubeVideoMetadata(
        title="猫",
        description="説明",
        made_for_kids="no",
    )

    with pytest.raises(YouTubeMetadataValidationError):
        YouTubeMetadataValidator().validate(metadata)
