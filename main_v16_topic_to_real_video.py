import argparse
import sys
import time
from pathlib import Path

from company.memory.company_memory import CompanyMemory
from company.reports.run_report import RunReportWriter, build_run_report
from company.reports.run_report_memory_adapter import RunReportMemoryAdapter
from company.runtime.real_video_pipeline_factory import RealVideoPipelineFactory
from company.runtime.real_video_runtime import (
    RealVideoRuntimeConfig,
    VideoOutputValidator,
)
from main_v15_real_ai_company_video import save_run_report_to_memory


def configure_stdout() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Run Project SHIRO topic-to-real-mp4 integration.",
    )
    parser.add_argument("topic", help="Video topic, e.g. 猫の意外な雑学")
    parser.add_argument(
        "--output-root",
        default=None,
        help="Output root for generated images, voices, videos, reports, and memory.",
    )
    parser.add_argument("--ollama-model", default=None)
    parser.add_argument("--voicevox-speaker-id", type=int, default=None)
    parser.add_argument(
        "--skip-preflight",
        action="store_true",
        help="Skip local service checks. Use only when services are already verified.",
    )
    parser.add_argument(
        "--no-report",
        action="store_true",
        help="Do not write the JSON run report.",
    )
    parser.add_argument(
        "--no-memory",
        action="store_true",
        help="Do not save the run summary to CompanyMemory.",
    )
    return parser.parse_args(argv)


def build_config_from_args(args) -> RealVideoRuntimeConfig:
    config = RealVideoRuntimeConfig.from_env()
    if args.output_root is not None:
        config.output_root = args.output_root
    if args.ollama_model is not None:
        config.ollama_model = args.ollama_model
    if args.voicevox_speaker_id is not None:
        config.voicevox_speaker_id = args.voicevox_speaker_id
    return config


def run_topic_to_real_video(
    topic: str,
    *,
    config: RealVideoRuntimeConfig | None = None,
    factory=None,
    preflight_checker=None,
    validator=None,
    report_writer=None,
    memory=None,
    memory_adapter=None,
    run_preflight: bool = True,
    save_report: bool = True,
    save_memory: bool = True,
) -> dict:
    if not topic or not topic.strip():
        raise ValueError("topic is required.")

    config = config or RealVideoRuntimeConfig.from_env()
    factory = factory or RealVideoPipelineFactory(config=config)

    statuses = []
    if run_preflight:
        checker = preflight_checker or factory.create_preflight_checker()
        if hasattr(checker, "ensure_ready"):
            statuses = checker.ensure_ready()
        else:
            statuses = checker.check_all()
            failed = [status for status in statuses if not status.ok]
            if failed:
                names = ", ".join(status.name for status in failed)
                raise RuntimeError(f"Real video services are not ready: {names}")

    expected_video_path = Path(config.final_video_path)
    if expected_video_path.exists():
        expected_video_path.unlink()
    run_started_ns = time.time_ns()

    company = factory.build()
    result = company.run(topic)

    validation = (validator or VideoOutputValidator()).validate(
        str(result.get("video_path", "")),
        created_after_ns=run_started_ns,
    )
    report = build_run_report(
        topic=topic,
        media_mode="real media",
        result=result,
        status="completed",
    )

    report_path = None
    if save_report:
        writer = report_writer or RunReportWriter(output_dir=config.reports_dir)
        report_path = writer.write(report)

    memory_record = None
    if save_memory:
        memory = memory or CompanyMemory(memory_path=config.memory_path)
        memory_record = save_run_report_to_memory(
            report,
            memory=memory,
            adapter=memory_adapter or RunReportMemoryAdapter(),
        )

    result.update(
        {
            "status": "completed",
            "media_mode": "real media",
            "preflight_statuses": statuses,
            "video_validation": validation,
            "report_path": report_path,
            "memory_record": memory_record,
        }
    )
    return result


def print_result(result: dict) -> None:
    print("Project SHIRO Topic to Real MP4")
    print("=" * 34)
    print(f"topic: {result.get('topic', '')}")
    print(f"video_path: {result.get('video_path', '')}")
    validation = result.get("video_validation", {}) or {}
    print(f"video_size_bytes: {validation.get('size_bytes', '')}")
    print(f"report_path: {result.get('report_path') or ''}")
    memory_record = result.get("memory_record") or {}
    if memory_record:
        print(f"memory_summary: {memory_record.get('summary', '')}")


def main(argv=None) -> int:
    configure_stdout()
    args = parse_args(argv)
    config = build_config_from_args(args)
    try:
        result = run_topic_to_real_video(
            args.topic,
            config=config,
            run_preflight=not args.skip_preflight,
            save_report=not args.no_report,
            save_memory=not args.no_memory,
        )
    except RuntimeError as exc:
        print(str(exc))
        return 1

    print_result(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
