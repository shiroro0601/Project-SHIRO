import pytest

from company.youtube.studio_upload import YouTubePrivateSavePolicy


def test_private_save_policy_requires_explicit_confirmation_by_default():
    policy = YouTubePrivateSavePolicy()

    assert policy.confirm_private_save is False
    assert policy.max_next_clicks == 3


def test_private_save_policy_accepts_confirmation_and_next_limit():
    policy = YouTubePrivateSavePolicy(confirm_private_save=True, max_next_clicks=2)

    assert policy.confirm_private_save is True
    assert policy.max_next_clicks == 2


def test_private_save_policy_rejects_negative_next_limit():
    with pytest.raises(ValueError):
        YouTubePrivateSavePolicy(max_next_clicks=-1)
