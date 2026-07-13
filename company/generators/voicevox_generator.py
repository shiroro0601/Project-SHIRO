from pathlib import Path
import time
from uuid import uuid4

import requests


class VOICEVOXGeneratorError(RuntimeError):
    def __init__(
        self,
        *,
        stage: str,
        endpoint: str,
        timeout: int,
        elapsed_seconds: float,
        narration_length: int,
        error_type: str,
        message: str,
    ):
        self.stage = stage
        self.endpoint = endpoint
        self.timeout = timeout
        self.elapsed_seconds = elapsed_seconds
        self.narration_length = narration_length
        self.error_type = error_type
        self.safe_message = message
        super().__init__(
            "VOICEVOXGenerator request failed: "
            f"stage={stage}; endpoint={endpoint}; timeout={timeout}; "
            f"elapsed_seconds={elapsed_seconds:.2f}; "
            f"narration_length={narration_length}; "
            f"error_type={error_type}; message={message}"
        )


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
        wav_bytes = self._request_synthesis(audio_query, len(normalized_text))
        output_path = self._save_wav(wav_bytes, len(normalized_text))
        return str(output_path)

    def _request_audio_query(self, text: str) -> dict:
        endpoint = f"{self.base_url}/audio_query"
        started = time.monotonic()
        try:
            response = requests.post(
                endpoint,
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
            raise self._error(
                stage="audio_query",
                endpoint=endpoint,
                started=started,
                narration_length=len(text),
                exc=exc,
            ) from exc

    def _request_synthesis(self, audio_query: dict, narration_length: int = 0) -> bytes:
        endpoint = f"{self.base_url}/synthesis"
        started = time.monotonic()
        try:
            response = requests.post(
                endpoint,
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
            raise self._error(
                stage="synthesis",
                endpoint=endpoint,
                started=started,
                narration_length=narration_length,
                exc=exc,
            ) from exc

    def _save_wav(self, wav_bytes: bytes, narration_length: int = 0) -> Path:
        started = time.monotonic()
        if not wav_bytes:
            raise self._error(
                stage="file_write",
                endpoint=str(self.output_dir),
                started=started,
                narration_length=narration_length,
                exc=RuntimeError("empty wav bytes"),
            )
        self.output_dir.mkdir(parents=True, exist_ok=True)
        output_path = self.output_dir / f"voicevox_{uuid4().hex}.wav"
        output_path.write_bytes(wav_bytes)
        return output_path

    def _error(
        self,
        *,
        stage: str,
        endpoint: str,
        started: float,
        narration_length: int,
        exc: Exception,
    ) -> VOICEVOXGeneratorError:
        return VOICEVOXGeneratorError(
            stage=stage,
            endpoint=endpoint,
            timeout=self.timeout,
            elapsed_seconds=time.monotonic() - started,
            narration_length=narration_length,
            error_type=type(exc).__name__,
            message=str(exc),
        )
