from dataclasses import dataclass

import requests


@dataclass
class ServiceStatus:
    name: str
    ok: bool
    url: str
    message: str


class ServiceHealthChecker:
    def __init__(self, timeout: int = 3):
        self.timeout = timeout

    def check_ollama(self) -> ServiceStatus:
        return self._check_service(
            name="Ollama",
            url="http://localhost:11434/api/tags",
            success_message="Ollama is running.",
            failure_message=(
                "Ollamaに接続できません。"
                "別PowerShellで `ollama serve` を実行してください。"
            ),
        )

    def check_stable_diffusion(self) -> ServiceStatus:
        return self._check_service(
            name="Stable Diffusion",
            url="http://127.0.0.1:7860/sdapi/v1/options",
            success_message="Stable Diffusion WebUI API is running.",
            failure_message=(
                "Stable Diffusion WebUI APIに接続できません。"
                "AUTOMATIC1111 WebUIを `--api` 付きで起動してください。"
            ),
        )

    def check_voicevox(self) -> ServiceStatus:
        return self._check_service(
            name="VOICEVOX",
            url="http://127.0.0.1:50021/version",
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

    def _check_service(
        self,
        name: str,
        url: str,
        success_message: str,
        failure_message: str,
    ) -> ServiceStatus:
        try:
            response = requests.get(url, timeout=self.timeout)
            if hasattr(response, "raise_for_status"):
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
