import json

import pytest

from company.youtube.auth import YouTubeAuthenticator
from company.youtube.config import YOUTUBE_UPLOAD_SCOPE, YouTubeOAuthConfig
from company.youtube.exceptions import (
    YouTubeAuthError,
    YouTubeConfigurationError,
    YouTubeCredentialError,
)


class FakeCredentials:
    def __init__(
        self,
        *,
        valid=False,
        expired=False,
        refresh_token=None,
        scopes=None,
        refresh_error=None,
    ):
        self.valid = valid
        self.expired = expired
        self.refresh_token = refresh_token
        self.scopes = tuple(scopes or (YOUTUBE_UPLOAD_SCOPE,))
        self.refresh_calls = []
        self.refresh_error = refresh_error

    def refresh(self, request):
        self.refresh_calls.append(request)
        if self.refresh_error:
            raise self.refresh_error
        self.valid = True
        self.expired = False

    def has_scopes(self, scopes):
        return set(scopes).issubset(set(self.scopes))

    def to_json(self):
        return "{}"


class FakeStore:
    def __init__(self, credentials=None):
        self.credentials = credentials
        self.saved = []

    def load(self):
        return self.credentials

    def save(self, credentials):
        self.saved.append(credentials)


class FakeFlow:
    def __init__(self, credentials):
        self.credentials = credentials
        self.calls = []

    def run_local_server(self, **kwargs):
        self.calls.append(kwargs)
        return self.credentials


def _client_secret(path):
    path.write_text(
        json.dumps({"installed": {"client_id": "dummy"}}),
        encoding="utf-8",
    )
    return path


def test_authenticator_reuses_valid_token_without_browser_or_refresh(tmp_path):
    credentials = FakeCredentials(valid=True)
    store = FakeStore(credentials)
    flow_calls = []
    config = YouTubeOAuthConfig(client_secrets_path=tmp_path / "missing.json")

    authenticator = YouTubeAuthenticator(
        config=config,
        credential_store=store,
        flow_factory=lambda *args: flow_calls.append(args),
    )

    assert authenticator.authenticate() is credentials
    assert credentials.refresh_calls == []
    assert flow_calls == []
    assert store.saved == []


def test_authenticator_refreshes_expired_token_and_saves(tmp_path):
    credentials = FakeCredentials(valid=False, expired=True, refresh_token="refresh")
    store = FakeStore(credentials)

    result = YouTubeAuthenticator(
        config=YouTubeOAuthConfig(),
        credential_store=store,
        request_factory=lambda: "REQUEST",
    ).authenticate()

    assert result is credentials
    assert credentials.refresh_calls == ["REQUEST"]
    assert store.saved == [credentials]


def test_authenticator_refresh_failure_raises_without_token_leak():
    credentials = FakeCredentials(
        valid=False,
        expired=True,
        refresh_token="REFRESH_TOKEN",
        refresh_error=RuntimeError("network failed"),
    )

    with pytest.raises(YouTubeAuthError) as excinfo:
        YouTubeAuthenticator(
            credential_store=FakeStore(credentials),
            request_factory=lambda: "REQUEST",
        ).authenticate()

    assert "REFRESH_TOKEN" not in str(excinfo.value)
    assert excinfo.value.__cause__ is not None


def test_authenticator_starts_installed_app_flow_when_token_missing(tmp_path):
    secret = _client_secret(tmp_path / "client.json")
    credentials = FakeCredentials(valid=True)
    flow = FakeFlow(credentials)
    flow_args = []
    config = YouTubeOAuthConfig(
        client_secrets_path=secret,
        local_server_host="127.0.0.1",
        local_server_port=0,
        open_browser=False,
    )

    def flow_factory(client_secrets_path, scopes):
        flow_args.append((client_secrets_path, scopes))
        return flow

    store = FakeStore(None)
    result = YouTubeAuthenticator(
        config=config,
        credential_store=store,
        flow_factory=flow_factory,
    ).authenticate()

    assert result is credentials
    assert flow_args == [(str(secret), config.scopes)]
    assert flow.calls == [
        {"host": "127.0.0.1", "port": 0, "open_browser": False}
    ]
    assert store.saved == [credentials]


def test_authenticator_missing_client_secret_raises_configuration_error(tmp_path):
    config = YouTubeOAuthConfig(client_secrets_path=tmp_path / "missing.json")

    with pytest.raises(YouTubeConfigurationError):
        YouTubeAuthenticator(config=config, credential_store=FakeStore(None)).authenticate()


def test_authenticator_invalid_client_secret_json_raises(tmp_path):
    secret = tmp_path / "client.json"
    secret.write_text("{", encoding="utf-8")

    with pytest.raises(YouTubeConfigurationError):
        YouTubeAuthenticator(
            config=YouTubeOAuthConfig(client_secrets_path=secret),
            credential_store=FakeStore(None),
        ).authenticate()


def test_authenticator_requires_installed_app_client_secret(tmp_path):
    secret = tmp_path / "client.json"
    secret.write_text(json.dumps({"web": {"client_id": "dummy"}}), encoding="utf-8")

    with pytest.raises(YouTubeConfigurationError):
        YouTubeAuthenticator(
            config=YouTubeOAuthConfig(client_secrets_path=secret),
            credential_store=FakeStore(None),
        ).authenticate()


def test_authenticator_detects_missing_scope_order_independent():
    credentials = FakeCredentials(
        valid=True,
        scopes=("scope-a",),
    )

    with pytest.raises(YouTubeCredentialError) as excinfo:
        YouTubeAuthenticator(credential_store=FakeStore(credentials)).authenticate()

    assert YOUTUBE_UPLOAD_SCOPE in str(excinfo.value)


def test_authenticator_propagates_user_auth_rejection(tmp_path):
    secret = _client_secret(tmp_path / "client.json")

    class RejectingFlow:
        def run_local_server(self, **kwargs):
            raise RuntimeError("access_denied")

    with pytest.raises(YouTubeAuthError) as excinfo:
        YouTubeAuthenticator(
            config=YouTubeOAuthConfig(client_secrets_path=secret),
            credential_store=FakeStore(None),
            flow_factory=lambda *args: RejectingFlow(),
        ).authenticate()

    assert excinfo.value.__cause__ is not None
