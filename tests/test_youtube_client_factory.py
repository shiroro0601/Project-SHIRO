import pytest

from company.youtube.auth import YouTubeClientFactory
from company.youtube.exceptions import YouTubeClientBuildError


def test_youtube_client_factory_builds_youtube_v3_with_credentials():
    calls = []

    def fake_build(*args, **kwargs):
        calls.append((args, kwargs))
        return {"client": "youtube"}

    credentials = object()
    client = YouTubeClientFactory(build_function=fake_build).build(credentials)

    assert client == {"client": "youtube"}
    assert calls == [
        (
            ("youtube", "v3"),
            {"credentials": credentials, "cache_discovery": False},
        )
    ]


def test_youtube_client_factory_wraps_build_failure():
    def fake_build(*args, **kwargs):
        raise RuntimeError("build failed")

    with pytest.raises(YouTubeClientBuildError) as excinfo:
        YouTubeClientFactory(build_function=fake_build).build(object())

    assert excinfo.value.__cause__ is not None


def test_youtube_client_factory_does_not_call_api_methods():
    class FakeClient:
        def __init__(self):
            self.videos_called = False

        def videos(self):
            self.videos_called = True

    client = FakeClient()

    result = YouTubeClientFactory(build_function=lambda *args, **kwargs: client).build(
        object()
    )

    assert result is client
    assert client.videos_called is False
