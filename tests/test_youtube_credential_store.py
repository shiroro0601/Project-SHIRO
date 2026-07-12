import json
import os

import pytest

from company.youtube.auth import YouTubeCredentialStore
from company.youtube.config import YouTubeOAuthConfig
from company.youtube.exceptions import YouTubeCredentialError


class FakeCredentials:
    def __init__(self, token="ACCESS_TOKEN", refresh_token="REFRESH_TOKEN"):
        self.token = token
        self.refresh_token = refresh_token
        self.scopes = ("https://www.googleapis.com/auth/youtube.upload",)

    def to_json(self):
        return json.dumps(
            {
                "token": self.token,
                "refresh_token": self.refresh_token,
                "scopes": list(self.scopes),
            }
        )


def test_credential_store_load_returns_none_when_token_missing(tmp_path):
    config = YouTubeOAuthConfig(token_path=tmp_path / "token.json")

    assert YouTubeCredentialStore(config).load() is None


def test_credential_store_load_success(tmp_path):
    token_path = tmp_path / "token.json"
    token_path.write_text('{"token": "secret"}', encoding="utf-8")

    def loader(data, scopes):
        return {"data": data, "scopes": scopes}

    config = YouTubeOAuthConfig(token_path=token_path)
    result = YouTubeCredentialStore(config, credential_loader=loader).load()

    assert result["data"] == {"token": "secret"}
    assert result["scopes"] == config.scopes


def test_credential_store_initialization_does_not_create_parent(tmp_path):
    config = YouTubeOAuthConfig(token_path=tmp_path / "nested" / "token.json")

    YouTubeCredentialStore(config)

    assert not config.token_path.parent.exists()


def test_credential_store_save_creates_parent_and_writes_utf8(tmp_path):
    token_path = tmp_path / "日本語" / "token.json"
    config = YouTubeOAuthConfig(token_path=token_path)

    YouTubeCredentialStore(config).save(FakeCredentials())

    data = json.loads(token_path.read_text(encoding="utf-8"))
    assert data["token"] == "ACCESS_TOKEN"
    assert data["refresh_token"] == "REFRESH_TOKEN"
    assert list(token_path.parent.glob("*.tmp")) == []


def test_credential_store_invalid_json_raises_without_secret_leak(tmp_path):
    token_path = tmp_path / "token.json"
    token_path.write_text('{"token": "ACCESS_TOKEN"', encoding="utf-8")
    config = YouTubeOAuthConfig(token_path=token_path)

    with pytest.raises(YouTubeCredentialError) as excinfo:
        YouTubeCredentialStore(config).load()

    assert "ACCESS_TOKEN" not in str(excinfo.value)
    assert excinfo.value.__cause__ is not None


def test_credential_store_save_failure_keeps_existing_token(tmp_path, monkeypatch):
    token_path = tmp_path / "token.json"
    token_path.write_text('{"token": "old"}', encoding="utf-8")
    config = YouTubeOAuthConfig(token_path=token_path)

    def fail_replace(source, destination):
        raise OSError("replace failed")

    monkeypatch.setattr(os, "replace", fail_replace)

    with pytest.raises(YouTubeCredentialError) as excinfo:
        YouTubeCredentialStore(config).save(FakeCredentials())

    assert "ACCESS_TOKEN" not in str(excinfo.value)
    assert excinfo.value.__cause__ is not None
    assert json.loads(token_path.read_text(encoding="utf-8")) == {"token": "old"}
    assert list(tmp_path.glob("*.tmp")) == []
