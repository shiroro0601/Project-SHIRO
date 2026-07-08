import base64
import sys
import wave
from pathlib import Path
from pprint import pprint

from company.brain.provider import OllamaProvider
from company.core.employee_role import ResearchRole, ReviewerRole, WriterRole
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


def build_company(
    provider=None,
    image_generator=None,
    voice_generator=None,
    scene_video_composer=None,
    publisher=None,
):
    provider = provider or OllamaProvider(model="llama3.2:3b")
    researcher = ResearchRole(provider=provider)
    writer = WriterRole(provider=provider)
    reviewer = ReviewerRole(provider=provider)

    return FullAutoVideoPipeline(
        researcher=researcher,
        writer=writer,
        reviewer=reviewer,
        image_generator=image_generator or PlaceholderImageGenerator(),
        voice_generator=voice_generator or PlaceholderVoiceGenerator(),
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
):
    company = build_company(
        provider=provider,
        image_generator=image_generator,
        voice_generator=voice_generator,
        scene_video_composer=scene_video_composer,
        publisher=publisher,
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


def main() -> None:
    configure_stdout()
    try:
        result = run_real_ai_company_video(DEFAULT_TOPIC)
    except RuntimeError as exc:
        if "OllamaProvider request failed" in str(exc):
            print("Ollamaに接続できません。")
            print("別PowerShellで `ollama serve` を実行してください。")
        raise

    print_result(result)


if __name__ == "__main__":
    main()
