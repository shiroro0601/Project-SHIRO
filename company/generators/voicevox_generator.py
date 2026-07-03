from pathlib import Path
from uuid import uuid4

import requests


class VOICEVOXGenerator:
    def __init__(
        self,
        base_url: str = "http://127.0.0.1:50021",
        output_dir: str = "outputs/voices",
        speaker: int = 1,
        timeout: int = 60,
    ):
        self.base_url = base_url.rstrip("/")
        self.output_dir = Path(output_dir)
        self.speaker = speaker
        self.timeout = timeout

    def generate(self, text: str) -> str:
        normalized_text = text.strip()
        if not normalized_text:
            raise ValueError("text must not be empty.")

        audio_query = self._request_audio_query(normalized_text)
        wav_bytes = self._request_synthesis(audio_query)
        output_path = self._save_wav(wav_bytes)
        return str(output_path)

    def _request_audio_query(self, text: str) -> dict:
        try:
            response = requests.post(
                f"{self.base_url}/audio_query",
                params={
                    "text": text,
                    "speaker": self.speaker,
                },
                timeout=self.timeout,
            )
            if hasattr(response, "raise_for_status"):
                response.raise_for_status()
            return response.json()
        except Exception as exc:
            raise RuntimeError(f"VOICEVOXGenerator request failed: {exc}") from exc

    def _request_synthesis(self, audio_query: dict) -> bytes:
        try:
            response = requests.post(
                f"{self.base_url}/synthesis",
                params={
                    "speaker": self.speaker,
                },
                json=audio_query,
                timeout=self.timeout,
            )
            if hasattr(response, "raise_for_status"):
                response.raise_for_status()
            return response.content
        except Exception as exc:
            raise RuntimeError(f"VOICEVOXGenerator request failed: {exc}") from exc

    def _save_wav(self, wav_bytes: bytes) -> Path:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        output_path = self.output_dir / f"voicevox_{uuid4().hex}.wav"
        output_path.write_bytes(wav_bytes)
        return output_path
