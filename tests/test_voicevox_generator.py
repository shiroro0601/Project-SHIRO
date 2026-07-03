import pytest

from company.generators.voicevox_generator import VOICEVOXGenerator


DUMMY_WAV_BYTES = b"RIFF\x24\x00\x00\x00WAVEfmt "


class FakeJsonResponse:
    def __init__(self, payload):
        self.payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self.payload


class FakeBytesResponse:
    def __init__(self, content):
        self.content = content

    def raise_for_status(self):
        return None


def test_voicevox_generator_empty_text_raises_value_error(tmp_path):
    generator = VOICEVOXGenerator(output_dir=str(tmp_path))

    with pytest.raises(ValueError, match="text must not be empty"):
        generator.generate("   ")


def test_voicevox_generator_generate_success(monkeypatch, tmp_path):
    def fake_post(url, params=None, json=None, timeout=None):
        if url.endswith("/audio_query"):
            return FakeJsonResponse({"query": "ok"})
        return FakeBytesResponse(DUMMY_WAV_BYTES)

    monkeypatch.setattr(
        "company.generators.voicevox_generator.requests.post",
        fake_post,
    )
    generator = VOICEVOXGenerator(output_dir=str(tmp_path))

    output_path = generator.generate("Voice script for: 猫")

    assert output_path.endswith(".wav")


def test_voicevox_generator_saves_wav_file(monkeypatch, tmp_path):
    def fake_post(url, params=None, json=None, timeout=None):
        if url.endswith("/audio_query"):
            return FakeJsonResponse({"query": "ok"})
        return FakeBytesResponse(DUMMY_WAV_BYTES)

    monkeypatch.setattr(
        "company.generators.voicevox_generator.requests.post",
        fake_post,
    )
    generator = VOICEVOXGenerator(output_dir=str(tmp_path))

    output_path = generator.generate("Voice script for: 猫")
    saved_file = tmp_path / output_path.split("\\")[-1].split("/")[-1]

    assert saved_file.exists()
    assert saved_file.read_bytes() == DUMMY_WAV_BYTES


def test_voicevox_generator_returns_saved_path(monkeypatch, tmp_path):
    def fake_post(url, params=None, json=None, timeout=None):
        if url.endswith("/audio_query"):
            return FakeJsonResponse({"query": "ok"})
        return FakeBytesResponse(DUMMY_WAV_BYTES)

    monkeypatch.setattr(
        "company.generators.voicevox_generator.requests.post",
        fake_post,
    )
    generator = VOICEVOXGenerator(output_dir=str(tmp_path))

    output_path = generator.generate("Voice script for: 犬")

    assert str(tmp_path) in output_path


def test_voicevox_generator_calls_audio_query_with_expected_request(
    monkeypatch,
    tmp_path,
):
    calls = []

    def fake_post(url, params=None, json=None, timeout=None):
        calls.append(
            {
                "url": url,
                "params": params,
                "json": json,
                "timeout": timeout,
            }
        )
        if url.endswith("/audio_query"):
            return FakeJsonResponse({"query": "ok"})
        return FakeBytesResponse(DUMMY_WAV_BYTES)

    monkeypatch.setattr(
        "company.generators.voicevox_generator.requests.post",
        fake_post,
    )
    generator = VOICEVOXGenerator(
        base_url="http://127.0.0.1:50021/",
        output_dir=str(tmp_path),
        speaker=3,
        timeout=12,
    )

    generator.generate("Voice script for: 猫")

    assert calls[0] == {
        "url": "http://127.0.0.1:50021/audio_query",
        "params": {
            "text": "Voice script for: 猫",
            "speaker": 3,
        },
        "json": None,
        "timeout": 12,
    }


def test_voicevox_generator_calls_synthesis_with_expected_request(
    monkeypatch,
    tmp_path,
):
    calls = []

    def fake_post(url, params=None, json=None, timeout=None):
        calls.append(
            {
                "url": url,
                "params": params,
                "json": json,
                "timeout": timeout,
            }
        )
        if url.endswith("/audio_query"):
            return FakeJsonResponse({"query": "ok"})
        return FakeBytesResponse(DUMMY_WAV_BYTES)

    monkeypatch.setattr(
        "company.generators.voicevox_generator.requests.post",
        fake_post,
    )
    generator = VOICEVOXGenerator(
        base_url="http://127.0.0.1:50021/",
        output_dir=str(tmp_path),
        speaker=2,
        timeout=20,
    )

    generator.generate("Voice script for: 猫")

    assert calls[1] == {
        "url": "http://127.0.0.1:50021/synthesis",
        "params": {
            "speaker": 2,
        },
        "json": {"query": "ok"},
        "timeout": 20,
    }


def test_voicevox_generator_request_error_raises_runtime_error(
    monkeypatch,
    tmp_path,
):
    def fake_post(url, params=None, json=None, timeout=None):
        raise RuntimeError("connection refused")

    monkeypatch.setattr(
        "company.generators.voicevox_generator.requests.post",
        fake_post,
    )
    generator = VOICEVOXGenerator(output_dir=str(tmp_path))

    with pytest.raises(RuntimeError, match="VOICEVOXGenerator request failed"):
        generator.generate("Voice script for: 猫")
