import argparse
import base64
import sys
import wave
from pathlib import Path
from pprint import pprint

from company.brain.provider import OllamaProvider
from company.core.employee_role import ResearchRole, ReviewerRole, WriterRole
from company.memory.company_memory import CompanyMemory
from company.memory.memory_retriever import MemoryRetriever
from company.reports.run_report import RunReportWriter, build_run_report
from company.reports.run_report_memory_adapter import RunReportMemoryAdapter
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
    parser.add_argument(
        "--no-report",
        action="store_true",
        help="Skip writing the JSON run report.",
    )
    parser.add_argument(
        "--save-memory",
        action="store_true",
        help="Save a compact run report record to CompanyMemory.",
    )
    parser.add_argument(
        "--use-memory",
        action="store_true",
        help="Load recent run reports from CompanyMemory before execution.",
    )
    parser.add_argument(
        "--memory-loop",
        action="store_true",
        help="Enable both --use-memory and --save-memory for loop verification.",
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
    memory_context=None,
):
    provider = provider or OllamaProvider(model="llama3.2:3b")
    researcher = ResearchRole(provider=provider, memory_context=memory_context)
    writer = WriterRole(provider=provider, memory_context=memory_context)
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
    memory_context=None,
):
    company = build_company(
        provider=provider,
        image_generator=image_generator,
        voice_generator=voice_generator,
        scene_video_composer=scene_video_composer,
        publisher=publisher,
        real_media=real_media,
        memory_context=memory_context,
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


def write_run_report(
    report,
    report_writer=None,
) -> str:
    writer = report_writer or RunReportWriter()
    return writer.write(report)


def save_run_report_to_memory(report, memory=None, adapter=None) -> dict:
    memory = memory or CompanyMemory()
    adapter = adapter or RunReportMemoryAdapter()
    record = adapter.to_memory_record(report)

    if hasattr(memory, "add_run_report"):
        memory.add_run_report(record)
        return record

    data = memory.load()
    data.setdefault("run_reports", [])
    data["run_reports"].append(record)
    memory.save(data)
    return record


def count_run_reports(memory=None) -> int:
    memory = memory or CompanyMemory()
    data = memory.load() if hasattr(memory, "load") else getattr(memory, "data", {})
    if not isinstance(data, dict):
        return 0
    run_reports = data.get("run_reports", [])
    return len(run_reports) if isinstance(run_reports, list) else 0


def load_memory_context(memory=None, memory_retriever=None, limit: int = 3):
    retriever = memory_retriever or MemoryRetriever(memory or CompanyMemory())
    return retriever.build_context(limit=limit)


def print_memory_context(memory_context) -> None:
    print("Memory context:")
    print(memory_context.to_prompt_text())


def print_memory_loop_status(
    before_count: int,
    after_count: int,
    using_memory_context: bool,
    saved_memory: bool,
    memory_record=None,
) -> None:
    print("Memory loop:")
    print(f"- before run_reports: {before_count}")
    print(f"- using memory context: {'yes' if using_memory_context else 'no'}")
    print(f"- saved memory: {'yes' if saved_memory else 'no'}")
    print(f"- after run_reports: {after_count}")
    if memory_record:
        print(f"- saved summary: {memory_record.get('summary', '')}")
        print(f"- quality decision: {memory_record.get('quality_decision', '')}")
        print(f"- quality score: {memory_record.get('quality_score', '')}")
        print(f"- improvement points: {memory_record.get('improvement_points', '')}")


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


def main(
    argv=None,
    service_health_checker=None,
    report_writer=None,
    memory=None,
    memory_adapter=None,
    memory_retriever=None,
) -> None:
    configure_stdout()
    args = parse_args(argv)
    if args.memory_loop:
        args.use_memory = True
        args.save_memory = True
    if args.check_services:
        checker = service_health_checker or ServiceHealthChecker()
        print_service_statuses(checker.check_all())
        return

    mode = "real media" if args.real_media else "placeholder"
    print(f"media mode: {mode}")
    before_memory_count = count_run_reports(memory) if args.use_memory or args.save_memory else 0
    after_memory_count = before_memory_count
    memory_record = None
    memory_context = None
    if args.use_memory:
        memory_context = load_memory_context(
            memory=memory,
            memory_retriever=memory_retriever,
        )
        print_memory_context(memory_context)
    try:
        if args.real_media:
            ensure_services_ready(service_health_checker)
        run_kwargs = {"real_media": args.real_media}
        if memory_context is not None:
            run_kwargs["memory_context"] = memory_context
        result = run_real_ai_company_video(DEFAULT_TOPIC, **run_kwargs)
    except RuntimeError as exc:
        _print_runtime_hint(exc)
        raise

    print_result(result)
    report = build_run_report(
        topic=str(result.get("topic", DEFAULT_TOPIC)),
        media_mode=mode,
        result=result,
        status="completed",
    )
    if not args.no_report:
        report_path = write_run_report(report, report_writer=report_writer)
        print()
        print(f"Run report: {report_path}")
    if args.save_memory:
        memory_record = save_run_report_to_memory(
            report,
            memory=memory,
            adapter=memory_adapter,
        )
        after_memory_count = count_run_reports(memory)
        print(f"Memory saved: {memory_record['type']}")
        print_memory_loop_status(
            before_count=before_memory_count,
            after_count=after_memory_count,
            using_memory_context=args.use_memory,
            saved_memory=True,
            memory_record=memory_record,
        )


if __name__ == "__main__":
    main()
