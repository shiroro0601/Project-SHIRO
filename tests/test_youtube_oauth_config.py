from pathlib import Path

from company.youtube.config import YOUTUBE_UPLOAD_SCOPE, YouTubeOAuthConfig


def test_youtube_oauth_config_defaults_are_safe_and_minimal(tmp_path):
    config = YouTubeOAuthConfig()

    assert config.scopes == (YOUTUBE_UPLOAD_SCOPE,)
    assert str(config.client_secrets_path) == "secrets\\youtube\\client_secret.json"
    assert str(config.token_path) == "secrets\\youtube\\token.json"
    assert config.local_server_host == "127.0.0.1"
    assert config.local_server_port == 0
    assert config.open_browser is True


def test_youtube_oauth_config_from_env_overrides_paths_and_server_options():
    config = YouTubeOAuthConfig.from_env(
        {
            "PROJECT_SHIRO_YOUTUBE_CLIENT_SECRETS": "custom/client.json",
            "PROJECT_SHIRO_YOUTUBE_TOKEN_PATH": "custom/token.json",
            "PROJECT_SHIRO_YOUTUBE_OAUTH_HOST": "localhost",
            "PROJECT_SHIRO_YOUTUBE_OAUTH_PORT": "8080",
            "PROJECT_SHIRO_YOUTUBE_OPEN_BROWSER": "false",
        }
    )

    assert config.client_secrets_path == Path("custom/client.json")
    assert config.token_path == Path("custom/token.json")
    assert config.local_server_host == "localhost"
    assert config.local_server_port == 8080
    assert config.open_browser is False


def test_youtube_oauth_config_does_not_create_files(tmp_path):
    client_secret = tmp_path / "missing" / "client.json"
    token_path = tmp_path / "missing" / "token.json"

    YouTubeOAuthConfig(
        client_secrets_path=client_secret,
        token_path=token_path,
    )

    assert not client_secret.exists()
    assert not token_path.exists()
    assert not token_path.parent.exists()


def test_youtube_oauth_config_scopes_are_copied_to_tuple():
    scopes = ["scope-b", YOUTUBE_UPLOAD_SCOPE]
    config = YouTubeOAuthConfig(scopes=scopes)
    scopes.append("scope-c")

    assert config.scopes == ("scope-b", YOUTUBE_UPLOAD_SCOPE)
