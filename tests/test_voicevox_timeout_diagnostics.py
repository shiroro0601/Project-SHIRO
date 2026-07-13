import pytest

from company.generators.voicevox_generator import (
    VOICEVOXGenerator,
    VOICEVOXGeneratorError,
)


class FailingRequests:
    def __init__(self, exc):
        self.exc = exc

    def post(self, *args, **kwargs):
        raise self.exc


class Response:
    def __init__(self, json_data=None, content=b"RIFFfake"):
        self._json_data = json_data or {"query": "ok"}
        self.content = content

    def raise_for_status(self):
        return None

    def json(self):
        return self._json_data


class SequencedRequests:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def post(self, url, **kwargs):
        self.calls.append((url, kwargs))
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response


def test_audio_query_timeout_includes_safe_diagnostics(monkeypatch):
    import company.generators.voicevox_generator as module

    monkeypatch.setattr(module, "requests", FailingRequests(TimeoutError("slow")))
    generator = VOICEVOXGenerator(timeout=120)

    with pytest.raises(VOICEVOXGeneratorError) as exc_info:
        generator.generate("猫の短いナレーション")

    error = exc_info.value
    assert error.stage == "audio_query"
    assert error.timeout == 120
    assert error.narration_length == len("猫の短いナレーション")
    assert "猫の短いナレーション" not in str(error)
    assert "stage=audio_query" in str(error)


def test_synthesis_timeout_identifies_stage(monkeypatch):
    import company.generators.voicevox_generator as module

    fake_requests = SequencedRequests(
        [Response(json_data={"accent_phrases": []}), TimeoutError("slow synthesis")]
    )
    monkeypatch.setattr(module, "requests", fake_requests)
    generator = VOICEVOXGenerator(timeout=90)

    with pytest.raises(VOICEVOXGeneratorError) as exc_info:
        generator.generate("猫")

    assert exc_info.value.stage == "synthesis"
    assert exc_info.value.endpoint.endswith("/synthesis")


def test_empty_wav_bytes_are_not_success(tmp_path, monkeypatch):
    import company.generators.voicevox_generator as module

    fake_requests = SequencedRequests(
        [Response(json_data={"accent_phrases": []}), Response(content=b"")]
    )
    monkeypatch.setattr(module, "requests", fake_requests)
    generator = VOICEVOXGenerator(output_dir=str(tmp_path))

    with pytest.raises(VOICEVOXGeneratorError) as exc_info:
        generator.generate("猫")

    assert exc_info.value.stage == "file_write"
    assert not list(tmp_path.glob("*.wav"))
