from pathlib import Path

from company.youtube.studio_upload import YouTubeBrowserConfig


def test_youtube_browser_config_defaults_do_not_create_profile(tmp_path):
    profile_dir = tmp_path / "browser_profiles" / "youtube"

    config = YouTubeBrowserConfig(user_data_dir=profile_dir)

    assert config.user_data_dir == profile_dir
    assert config.headless is False
    assert config.timeout_ms >= 30000
    assert config.locale == "ja-JP"
    assert config.studio_url == "https://studio.youtube.com/"
    assert not profile_dir.exists()


def test_youtube_browser_config_accepts_runtime_options(tmp_path):
    config = YouTubeBrowserConfig(
        user_data_dir=tmp_path / "profile",
        headless=True,
        browser_channel="chrome",
        executable_path="chrome.exe",
        timeout_ms=45000,
        slow_mo_ms=20,
        locale="en-US",
        studio_url="https://studio.youtube.com/channel",
    )

    assert config.headless is True
    assert config.browser_channel == "chrome"
    assert config.executable_path == "chrome.exe"
    assert config.timeout_ms == 45000
    assert config.slow_mo_ms == 20
    assert config.locale == "en-US"
    assert config.studio_url == "https://studio.youtube.com/channel"
