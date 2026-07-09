from company.runtime import service_health
from company.runtime.service_health import ServiceHealthChecker, ServiceStatus


class FakeResponse:
    def __init__(self, error=None):
        self.error = error

    def raise_for_status(self):
        if self.error:
            raise self.error


def test_service_status_can_be_created():
    status = ServiceStatus(
        name="Ollama",
        ok=True,
        url="http://localhost:11434/api/tags",
        message="running",
    )

    assert status.name == "Ollama"
    assert status.ok is True
    assert status.url == "http://localhost:11434/api/tags"
    assert status.message == "running"


def test_check_ollama_returns_ok_for_success(monkeypatch):
    calls = []

    def fake_get(url, timeout):
        calls.append({"url": url, "timeout": timeout})
        return FakeResponse()

    monkeypatch.setattr(service_health.requests, "get", fake_get)
    checker = ServiceHealthChecker(timeout=2)

    status = checker.check_ollama()

    assert status.ok is True
    assert status.name == "Ollama"
    assert calls == [{"url": "http://localhost:11434/api/tags", "timeout": 2}]


def test_check_stable_diffusion_returns_ng_for_exception(monkeypatch):
    def fake_get(url, timeout):
        raise RuntimeError("connection refused")

    monkeypatch.setattr(service_health.requests, "get", fake_get)
    checker = ServiceHealthChecker()

    status = checker.check_stable_diffusion()

    assert status.ok is False
    assert status.name == "Stable Diffusion"
    assert "AUTOMATIC1111 WebUI" in status.message


def test_check_voicevox_returns_ng_for_http_error(monkeypatch):
    def fake_get(url, timeout):
        return FakeResponse(error=RuntimeError("500"))

    monkeypatch.setattr(service_health.requests, "get", fake_get)
    checker = ServiceHealthChecker()

    status = checker.check_voicevox()

    assert status.ok is False
    assert status.name == "VOICEVOX"
    assert "VOICEVOX Engine" in status.message


def test_check_all_returns_three_statuses(monkeypatch):
    def fake_get(url, timeout):
        return FakeResponse()

    monkeypatch.setattr(service_health.requests, "get", fake_get)
    checker = ServiceHealthChecker()

    statuses = checker.check_all()

    assert [status.name for status in statuses] == [
        "Ollama",
        "Stable Diffusion",
        "VOICEVOX",
    ]
    assert all(status.ok for status in statuses)
