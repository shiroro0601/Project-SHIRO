import os
from dataclasses import dataclass
from pathlib import Path

import requests

from company.runtime.service_health import ServiceStatus


@dataclass
class RealVideoRuntimeConfig:
    ollama_base_url: str = "http://127.0.0.1:11434"
    ollama_model: str = "llama3.2:3b"
    stable_diffusion_base_url: str = "http://127.0.0.1:7860"
    voicevox_base_url: str = "http://127.0.0.1:50021"
    voicevox_speaker_id: int = 1
    output_root: str = "outputs/real_video"
    fps: int = 24
    service_timeout: int = 3
    request_timeout: int = 60
    voicevox_timeout_seconds: int = 60

    @classmethod
    def from_env(cls, environ=None):
        environ = environ or os.environ
        return cls(
            ollama_base_url=environ.get(
                "PROJECT_SHIRO_OLLAMA_BASE_URL",
                cls.ollama_base_url,
            ),
            ollama_model=environ.get(
                "PROJECT_SHIRO_OLLAMA_MODEL",
                cls.ollama_model,
            ),
            stable_diffusion_base_url=environ.get(
                "PROJECT_SHIRO_SD_BASE_URL",
                cls.stable_diffusion_base_url,
            ),
            voicevox_base_url=environ.get(
                "PROJECT_SHIRO_VOICEVOX_BASE_URL",
                cls.voicevox_base_url,
            ),
            voicevox_speaker_id=int(
                environ.get(
                    "PROJECT_SHIRO_VOICEVOX_SPEAKER_ID",
                    cls.voicevox_speaker_id,
                )
            ),
            output_root=environ.get(
                "PROJECT_SHIRO_OUTPUT_ROOT",
                cls.output_root,
            ),
            voicevox_timeout_seconds=int(
                environ.get(
                    "PROJECT_SHIRO_VOICEVOX_TIMEOUT_SECONDS",
                    cls.voicevox_timeout_seconds,
                )
            ),
        )

    @property
    def images_dir(self) -> str:
        return str(Path(self.output_root) / "images")

    @property
    def voices_dir(self) -> str:
        return str(Path(self.output_root) / "voices")

    @property
    def videos_dir(self) -> str:
        return str(Path(self.output_root) / "videos")

    @property
    def reports_dir(self) -> str:
        return str(Path(self.output_root) / "reports")

    @property
    def memory_path(self) -> str:
        return str(Path(self.output_root) / "memory" / "company_memory.json")

    @property
    def final_video_path(self) -> str:
        return str(Path(self.videos_dir) / "final_video.mp4")


class RealVideoPreflightChecker:
    def __init__(self, config: RealVideoRuntimeConfig):
        self.config = config

    def check_ollama(self) -> ServiceStatus:
        url = f"{self.config.ollama_base_url.rstrip('/')}/api/tags"
        try:
            response = requests.get(url, timeout=self.config.service_timeout)
            response.raise_for_status()
            data = response.json() if hasattr(response, "json") else {}
            models = data.get("models", []) if isinstance(data, dict) else []
            model_names = {str(model.get("name", "")) for model in models}
            if self.config.ollama_model not in model_names:
                return ServiceStatus(
                    name="Ollama",
                    ok=False,
                    url=url,
                    message=(
                        f"Ollama model '{self.config.ollama_model}' が見つかりません。"
                        f"`ollama pull {self.config.ollama_model}` を実行してください。"
                    ),
                )
        except Exception as exc:
            return ServiceStatus(
                name="Ollama",
                ok=False,
                url=url,
                message=(
                    "Ollamaに接続できません。"
                    "別PowerShellで `ollama serve` を実行してください。"
                    f" ({exc})"
                ),
            )

        return ServiceStatus(
            name="Ollama",
            ok=True,
            url=url,
            message=f"Ollama model '{self.config.ollama_model}' is available.",
        )

    def check_stable_diffusion(self) -> ServiceStatus:
        url = f"{self.config.stable_diffusion_base_url.rstrip('/')}/sdapi/v1/options"
        return self._check_simple_service(
            name="Stable Diffusion",
            url=url,
            success_message="Stable Diffusion WebUI API is running.",
            failure_message=(
                "Stable Diffusion WebUI APIに接続できません。"
                "AUTOMATIC1111 WebUIを `--api` 付きで起動してください。"
            ),
        )

    def check_voicevox(self) -> ServiceStatus:
        url = f"{self.config.voicevox_base_url.rstrip('/')}/version"
        return self._check_simple_service(
            name="VOICEVOX",
            url=url,
            success_message="VOICEVOX Engine is running.",
            failure_message=(
                "VOICEVOX Engineに接続できません。"
                "VOICEVOX Engineを起動してください。"
            ),
        )

    def check_all(self) -> list[ServiceStatus]:
        return [
            self.check_ollama(),
            self.check_stable_diffusion(),
            self.check_voicevox(),
        ]

    def ensure_ready(self) -> list[ServiceStatus]:
        statuses = self.check_all()
        failed = [status for status in statuses if not status.ok]
        if failed:
            messages = "\n".join(
                f"- {status.name}: {status.message}" for status in failed
            )
            raise RuntimeError(f"Real video services are not ready:\n{messages}")
        return statuses

    def _check_simple_service(
        self,
        *,
        name: str,
        url: str,
        success_message: str,
        failure_message: str,
    ) -> ServiceStatus:
        try:
            response = requests.get(url, timeout=self.config.service_timeout)
            response.raise_for_status()
        except Exception as exc:
            return ServiceStatus(
                name=name,
                ok=False,
                url=url,
                message=f"{failure_message} ({exc})",
            )
        return ServiceStatus(
            name=name,
            ok=True,
            url=url,
            message=success_message,
        )


class VideoOutputValidator:
    def validate(self, video_path: str, created_after_ns: int | None = None) -> dict:
        if not video_path:
            raise RuntimeError("video_path is empty.")

        path = Path(video_path)
        if not path.exists():
            raise RuntimeError(f"Video file does not exist: {video_path}")
        if not path.is_file():
            raise RuntimeError(f"Video path is not a file: {video_path}")
        if path.suffix.lower() != ".mp4":
            raise RuntimeError(f"Video file is not mp4: {video_path}")

        size = path.stat().st_size
        if size <= 0:
            raise RuntimeError(f"Video file is empty: {video_path}")
        if created_after_ns is not None and path.stat().st_mtime_ns < created_after_ns:
            raise RuntimeError(f"Video file was not generated by this run: {video_path}")

        return {
            "video_path": str(path),
            "exists": True,
            "is_file": True,
            "size_bytes": size,
            "extension": path.suffix.lower(),
            "mtime_ns": path.stat().st_mtime_ns,
        }
