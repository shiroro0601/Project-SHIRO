import base64
from pathlib import Path
from uuid import uuid4

import requests


class StableDiffusionGenerator:
    def __init__(
        self,
        base_url: str = "http://127.0.0.1:7860",
        output_dir: str = "outputs/images",
        timeout: int = 60,
    ):
        self.base_url = base_url.rstrip("/")
        self.output_dir = Path(output_dir)
        self.timeout = timeout

    def generate(self, prompt: str) -> str:
        normalized_prompt = prompt.strip()
        if not normalized_prompt:
            raise ValueError("prompt must not be empty.")

        data = self._request_image(normalized_prompt)
        image_base64 = self._extract_image_base64(data)
        image_bytes = self._decode_image(image_base64)
        output_path = self._save_png(image_bytes)
        return str(output_path)

    def _request_image(self, prompt: str) -> dict:
        try:
            response = requests.post(
                f"{self.base_url}/sdapi/v1/txt2img",
                json={
                    "prompt": prompt,
                    "steps": 20,
                    "width": 512,
                    "height": 512,
                },
                timeout=self.timeout,
            )
            if hasattr(response, "raise_for_status"):
                response.raise_for_status()
            return response.json()
        except Exception as exc:
            raise RuntimeError(
                f"StableDiffusionGenerator request failed: {exc}"
            ) from exc

    def _extract_image_base64(self, data: dict) -> str:
        try:
            image_base64 = data["images"][0]
        except (KeyError, IndexError, TypeError) as exc:
            raise RuntimeError(
                "StableDiffusionGenerator response must contain images[0]."
            ) from exc

        if not isinstance(image_base64, str) or not image_base64:
            raise RuntimeError("StableDiffusionGenerator image data must be a string.")

        if "," in image_base64:
            return image_base64.split(",", 1)[1]

        return image_base64

    def _decode_image(self, image_base64: str) -> bytes:
        try:
            return base64.b64decode(image_base64)
        except Exception as exc:
            raise RuntimeError("StableDiffusionGenerator image data is invalid.") from exc

    def _save_png(self, image_bytes: bytes) -> Path:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        output_path = self.output_dir / f"stable_diffusion_{uuid4().hex}.png"
        output_path.write_bytes(image_bytes)
        return output_path
