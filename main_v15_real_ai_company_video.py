import argparse
import base64
import sys
import wave
from pathlib import Path
from pprint import pprint

from company.brain.provider import OllamaProvider
from company.core.employee_role import ResearchRole, ReviewerRole, WriterRole
from company.runtime.service_health import ServiceHealthChecker
from company.video.scene_video_composer import MoviePySceneVideoComposer
from main_v12_full_video_company_dry_run import FullAutoVideoPipeline


DEFAULT_TOPIC = "猫の意外な雑学"


class PlaceholderImageGenerator:
    def __init__(self, output_dir: str = "outputs/v15_assets/images"):
        self.output_dir = Path(output_dir)
        self.count = 0

    def generate(self, prompt: str) -> str:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.count += 1
        output_path = self.output_dir / f"scene_{self.count}.png"
        # 1x1 RGB PNG. Good enough for wiring verification.
        output_path.write_bytes(
            base64.b64decode(
                "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAIAAACQd1PeAAAADElEQVR42mP4"
                "z8AAAAMBAQDJ/pLvAAAAAElFTkSuQmCC"
            )
        )
        return str(output_path)


class PlaceholderVoiceGenerator:
    def __init__(
        self,
        output_dir: str = "outputs/v15_assets/voices",
        sample_rate: int = 8000,
    ):
        self.output_dir = Path(output_dir)
        self.sample_rate = sample_rate
        self.count = 0

    def generate(self, text: str) -> str:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.count += 1
        output_path = self.output_dir / f"scene_{self.count}.wav"
        duration_seconds = 1
        frame_count = self.sample_rate * duration_seconds
        silence = b"\x00\x00" * frame_count
        with wave.open(str(output_path), "wb") as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(self.sample_rate)
            wav_file.writeframes(silence)
        return str(output_path)


def configure_stdout() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Run Project SHIRO real AI company video integration.",
    )
    parser.add_argument(
        "--real-media",
        action="store_true",
        help="Use StableDiffusionGenerator and VOICEVOXGenerator instead of placeholders.",
    )
    parser.add_argument(
        "--check-services",
        action="store_true",
        help="Check local Ollama, Stable Diffusion, and VOICEVOX service health.",
    )
    return parser.parse_args(argv)


def create_media_generators(real_media: bool):
    if real_media:
        from company.generators.stable_diffusion_generator import (
            StableDiffusionGenerator,
        )
        from company.generators.voicevox_generator import VOICEVOXGenerator

        return StableDiffusionGenerator(), VOICEVOXGenerator()

    return PlaceholderImageGenerator(), PlaceholderVoiceGenerator()


def build_company(
    provider=None,
    image_generator=None,
    voice_generator=None,
    scene_video_composer=None,
    publisher=None,
    real_media: bool = False,
):
    provider = provider or OllamaProvider(model="llama3.2:3b")
    researcher = ResearchRole(provider=provider)
    writer = WriterRole(provider=provider)
    reviewer = ReviewerRole(provider=provider)
    if image_generator is None or voice_generator is None:
        default_image_generator, default_voice_generator = create_media_generators(
            real_media
        )
        image_generator = image_generator or default_image_generator
        voice_generator = voice_generator or default_voice_generator

    return FullAutoVideoPipeline(
        researcher=researcher,
        writer=writer,
        reviewer=reviewer,
        image_generator=image_generator,
        voice_generator=voice_generator,
        scene_video_composer=scene_video_composer or MoviePySceneVideoComposer(),
        publisher=publisher,
    )


def run_real_ai_company_video(
    topic: str = DEFAULT_TOPIC,
    provider=None,
    image_generator=None,
    voice_generator=None,
    scene_video_composer=None,
    publisher=None,
    real_media: bool = False,
):
    company = build_company(
        provider=provider,
        image_generator=image_generator,
        voice_generator=voice_generator,
        scene_video_composer=scene_video_composer,
        publisher=publisher,
        real_media=real_media,
    )
    return company.run(topic)


def print_result(result: dict) -> None:
    script_artifact = result.get("script_artifact")
    scene_assets = result.get("scene_assets", [])

    print("Project SHIRO Version1.5 Real AI Company Video")
    print("=" * 48)
    print(f"topic: {result.get('topic')}")
    print("\nresearch_result:")
    print(result.get("research_result"))
    print("\nscript_result:")
    print(result.get("script_result"))
    print("\nreview_result:")
    print(result.get("review_result"))

    print("\nscript_artifact.title:")
    print(getattr(script_artifact, "title", ""))
    print(f"\nscene count: {len(getattr(script_artifact, 'scenes', []) or [])}")

    print("\nscene_assets:")
    for scene_asset in scene_assets:
        print(
            "- "
            f"scene={scene_asset.scene_index}, "
            f"image_path={scene_asset.image_path}, "
            f"voice_path={scene_asset.voice_path}, "
            f"duration={scene_asset.duration_seconds}"
        )

    print("\npaths:")
    print(f"image_path: {result.get('image_path')}")
    print(f"voice_path: {result.get('voice_path')}")
    print(f"scene_video_path: {result.get('scene_video_path')}")
    print(f"video_path: {result.get('video_path')}")

    print("\npublish_result:")
    pprint(result.get("publish_result"))


def print_service_statuses(statuses) -> None:
    print("Project SHIRO Service Health Check")
    print("=" * 36)
    for status in statuses:
        mark = "OK" if status.ok else "NG"
        print(f"[{mark}] {status.name}")
        print(f"  url: {status.url}")
        print(f"  message: {status.message}")


def ensure_services_ready(service_health_checker=None) -> None:
    checker = service_health_checker or ServiceHealthChecker()
    statuses = checker.check_all()
    print_service_statuses(statuses)
    failed = [status for status in statuses if not status.ok]
    if failed:
        names = ", ".join(status.name for status in failed)
        raise RuntimeError(f"Required local services are not ready: {names}")


def _print_runtime_hint(exc: RuntimeError) -> None:
    message = str(exc)
    if "OllamaProvider request failed" in message:
        print("Ollamaに接続できません。")
        print("別PowerShellで `ollama serve` を実行してください。")
    elif "StableDiffusionGenerator request failed" in message:
        print("Stable Diffusion WebUI APIに接続できません。")
        print("AUTOMATIC1111 WebUIを `--api` 付きで起動してください。")
    elif "VOICEVOXGenerator request failed" in message:
        print("VOICEVOX Engineに接続できません。")
        print("VOICEVOX Engineを起動してください。")


def main(argv=None, service_health_checker=None) -> None:
    configure_stdout()
    args = parse_args(argv)
    if args.check_services:
        checker = service_health_checker or ServiceHealthChecker()
        print_service_statuses(checker.check_all())
        return

    mode = "real media" if args.real_media else "placeholder"
    print(f"media mode: {mode}")
    try:
        if args.real_media:
            ensure_services_ready(service_health_checker)
        result = run_real_ai_company_video(
            DEFAULT_TOPIC,
            real_media=args.real_media,
        )
    except RuntimeError as exc:
        _print_runtime_hint(exc)
        raise

    print_result(result)


if __name__ == "__main__":
    main()
