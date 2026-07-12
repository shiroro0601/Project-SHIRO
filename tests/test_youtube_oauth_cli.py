import importlib

import main_v17_youtube_oauth_setup as cli
from company.youtube.exceptions import YouTubeAuthError


class FakeAuthenticator:
    def __init__(self, credentials=None, error=None):
        self.credentials = credentials or object()
        self.error = error
        self.called = False

    def authenticate(self):
        self.called = True
        if self.error:
            raise self.error
        return self.credentials


class FakeClientFactory:
    def __init__(self):
        self.credentials = None

    def build(self, credentials):
        self.credentials = credentials
        return {"client": "youtube"}


def test_youtube_oauth_cli_parses_config_options():
    args = cli.parse_args(
        [
            "--client-secrets",
            "custom/client.json",
            "--token-path",
            "custom/token.json",
            "--no-browser",
        ]
    )
    config = cli.build_config_from_args(args)

    assert str(config.client_secrets_path) == "custom\\client.json"
    assert str(config.token_path) == "custom\\token.json"
    assert config.open_browser is False


def test_run_youtube_oauth_setup_authenticates_and_builds_client():
    authenticator = FakeAuthenticator(credentials="CREDENTIALS")
    client_factory = FakeClientFactory()

    result = cli.run_youtube_oauth_setup(
        cli.build_config_from_args(cli.parse_args([])),
        authenticator=authenticator,
        client_factory=client_factory,
    )

    assert authenticator.called is True
    assert client_factory.credentials == "CREDENTIALS"
    assert result["status"] == "authenticated"


def test_youtube_oauth_cli_success_hides_secrets(capsys):
    authenticator = FakeAuthenticator(credentials="ACCESS_TOKEN")
    exit_code = cli.main(
        ["--token-path", "safe/token.json"],
        authenticator=authenticator,
        client_factory=FakeClientFactory(),
    )

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Token path: safe\\token.json" in output
    assert "ACCESS_TOKEN" not in output
    assert "refresh" not in output.lower()
    assert "client_secret" not in output
    assert "upload" in output
    assert "No video upload was performed." in output


def test_youtube_oauth_cli_failure_returns_nonzero_without_secret_leak(capsys):
    exit_code = cli.main(
        [],
        authenticator=FakeAuthenticator(
            error=YouTubeAuthError("failed without token text")
        ),
        client_factory=FakeClientFactory(),
    )

    output = capsys.readouterr().out
    assert exit_code == 1
    assert "failed without token text" in output
    assert "ACCESS_TOKEN" not in output
    assert "REFRESH_TOKEN" not in output


def test_youtube_oauth_cli_import_has_no_side_effects(monkeypatch):
    called = {"main": False}
    monkeypatch.setattr(cli, "main", lambda *args, **kwargs: called.__setitem__("main", True))

    importlib.reload(cli)

    assert called["main"] is False
