from company.youtube.studio_upload import YouTubePrivateSaveResult


def test_private_save_result_defaults_to_not_published():
    result = YouTubePrivateSaveResult(
        status="private_saved",
        video_path="video.mp4",
        title="title",
        privacy_status="private",
        private_selected=True,
        save_clicked=True,
        saved=True,
        published=False,
    )

    assert result.privacy_status == "private"
    assert result.saved is True
    assert result.published is False
    assert result.video_url == ""
    assert result.studio_url == ""
    assert result.error == ""


def test_private_save_verification_result_defaults_are_safe():
    from company.youtube.studio_upload import YouTubePrivateSaveVerificationResult

    result = YouTubePrivateSaveVerificationResult(
        status="not_found",
        found=False,
        title="Title",
        title_matched=False,
        privacy_status="",
        private_confirmed=False,
        duplicate_count=0,
    )

    assert result.video_id == ""
    assert result.content_type == "unknown"
    assert result.processing is False
    assert result.checked_locations == ()
    assert result.candidate_titles == ()
