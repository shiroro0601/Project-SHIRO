import pytest

from company.generators.stable_diffusion_generator import StableDiffusionGenerator


DUMMY_PNG_BASE64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+"
    "/p9sAAAAASUVORK5CYII="
)


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self.payload


def test_stable_diffusion_generator_empty_prompt_raises_value_error(tmp_path):
    generator = StableDiffusionGenerator(output_dir=str(tmp_path))

    with pytest.raises(ValueError, match="prompt must not be empty"):
        generator.generate("   ")


def test_stable_diffusion_generator_posts_expected_request(monkeypatch, tmp_path):
    calls = {}

    def fake_post(url, json, timeout):
        calls["url"] = url
        calls["json"] = json
        calls["timeout"] = timeout
        return FakeResponse({"images": [DUMMY_PNG_BASE64]})

    monkeypatch.setattr(
        "company.generators.stable_diffusion_generator.requests.post",
        fake_post,
    )
    generator = StableDiffusionGenerator(
        base_url="http://127.0.0.1:7860/",
        output_dir=str(tmp_path),
        timeout=15,
    )

    generator.generate("Image prompt for: 猫の意外な雑学")

    assert calls["url"] == "http://127.0.0.1:7860/sdapi/v1/txt2img"
    assert calls["json"] == {
        "prompt": "Image prompt for: 猫の意外な雑学",
        "steps": 20,
        "width": 512,
        "height": 512,
    }
    assert calls["timeout"] == 15


def test_stable_diffusion_generator_saves_png_file(monkeypatch, tmp_path):
    def fake_post(url, json, timeout):
        return FakeResponse({"images": [DUMMY_PNG_BASE64]})

    monkeypatch.setattr(
        "company.generators.stable_diffusion_generator.requests.post",
        fake_post,
    )
    generator = StableDiffusionGenerator(output_dir=str(tmp_path))

    output_path = generator.generate("Image prompt for: 猫")

    assert output_path.endswith(".png")
    saved_file = tmp_path / output_path.split("\\")[-1].split("/")[-1]
    assert saved_file.exists()
    assert saved_file.read_bytes().startswith(b"\x89PNG")


def test_stable_diffusion_generator_returns_saved_path(monkeypatch, tmp_path):
    def fake_post(url, json, timeout):
        return FakeResponse({"images": [DUMMY_PNG_BASE64]})

    monkeypatch.setattr(
        "company.generators.stable_diffusion_generator.requests.post",
        fake_post,
    )
    generator = StableDiffusionGenerator(output_dir=str(tmp_path))

    output_path = generator.generate("Image prompt for: 犬")

    assert str(tmp_path) in output_path


def test_stable_diffusion_generator_request_error_raises_runtime_error(
    monkeypatch,
    tmp_path,
):
    def fake_post(url, json, timeout):
        raise RuntimeError("connection refused")

    monkeypatch.setattr(
        "company.generators.stable_diffusion_generator.requests.post",
        fake_post,
    )
    generator = StableDiffusionGenerator(output_dir=str(tmp_path))

    with pytest.raises(RuntimeError, match="StableDiffusionGenerator request failed"):
        generator.generate("Image prompt for: 猫")
