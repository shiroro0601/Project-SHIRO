import argparse
import sys

from company.runtime.project_shiro_youtube_orchestrator import (
    ProjectShiroStopPoint,
    ProjectShiroYouTubeOrchestrator,
    ProjectShiroYouTubeRunConfig,
    build_default_youtube_services,
)
from company.runtime.real_video_pipeline_factory import RealVideoPipelineFactory
from company.runtime.real_video_runtime import RealVideoRuntimeConfig, VideoOutputValidator


DEFAULT_CDP_ENDPOINT = "http://127.0.0.1:9222"


def configure_stdout() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Run Project SHIRO end-to-end with safe YouTube private-save gates.",
    )
    parser.add_argument("--topic", required=True)
    parser.add_argument("--existing-video", default="")
    parser.add_argument("--title", default="")
    parser.add_argument("--description", default="")
    parser.add_argument("--tag", action="append", default=[])
    audience = parser.add_mutually_exclusive_group(required=True)
    audience.add_argument("--made-for-kids", action="store_true")
    audience.add_argument("--not-made-for-kids", action="store_true")
    parser.add_argument("--output-root", default=None)
    parser.add_argument("--cdp-endpoint", default=DEFAULT_CDP_ENDPOINT)
    parser.add_argument("--expected-channel-name", default="")
    parser.add_argument("--smoke-id", default="")
    parser.add_argument("--confirm-private-save", action="store_true")
    parser.add_argument("--verify-timeout-seconds", type=float, default=120.0)
    parser.add_argument("--verify-poll-interval-seconds", type=float, default=10.0)
    parser.add_argument("--max-inspection-items", type=int, default=50)
    parser.add_argument("--voicevox-timeout-seconds", type=int, default=None)
    parser.add_argument("--keep-open", action="store_true")
    parser.add_argument("--no-report", action="store_true")
    parser.add_argument("--no-memory", action="store_true")
    parser.add_argument("--skip-preflight", action="store_true")
    stop_group = parser.add_mutually_exclusive_group()
    stop_group.add_argument("--stop-after-video", action="store_true")
    stop_group.add_argument("--stop-before-upload", action="store_true")
    stop_group.add_argument("--stop-after-upload-prepare", action="store_true")
    stop_group.add_argument("--stop-after-metadata", action="store_true")
    stop_group.add_argument("--stop-before-save", action="store_true")
    stop_group.add_argument("--stop-after-save", action="store_true")
    return parser.parse_args(argv)


def stop_point_from_args(args) -> str:
    if args.stop_after_video:
        return ProjectShiroStopPoint.AFTER_VIDEO
    if args.stop_before_upload:
        return ProjectShiroStopPoint.BEFORE_UPLOAD
    if args.stop_after_upload_prepare:
        return ProjectShiroStopPoint.AFTER_UPLOAD_PREPARE
    if args.stop_after_metadata:
        return ProjectShiroStopPoint.AFTER_METADATA
    if args.stop_before_save:
        return ProjectShiroStopPoint.BEFORE_SAVE
    if args.stop_after_save:
        return ProjectShiroStopPoint.AFTER_SAVE
    if args.confirm_private_save:
        return ProjectShiroStopPoint.NONE
    return ProjectShiroStopPoint.BEFORE_SAVE


def build_config(args) -> ProjectShiroYouTubeRunConfig:
    return ProjectShiroYouTubeRunConfig(
        topic=args.topic,
        output_root=args.output_root or RealVideoRuntimeConfig.from_env().output_root,
        existing_video_path=args.existing_video,
        cdp_endpoint=args.cdp_endpoint,
        expected_channel_name=args.expected_channel_name,
        title=args.title,
        description=args.description,
        tags=tuple(args.tag or ()),
        made_for_kids=bool(args.made_for_kids),
        stop_point=stop_point_from_args(args),
        confirm_private_save=bool(args.confirm_private_save),
        smoke_id=args.smoke_id,
        verify_timeout_seconds=args.verify_timeout_seconds,
        verify_poll_interval_seconds=args.verify_poll_interval_seconds,
        max_inspection_items=args.max_inspection_items,
        keep_open=args.keep_open,
        save_report=not args.no_report,
        save_memory=not args.no_memory,
    )


def build_orchestrator(args, config=None, youtube_services_factory=None):
    config = config or build_config(args)
    runtime_config = RealVideoRuntimeConfig.from_env()
    runtime_config.output_root = config.output_root
    if args.voicevox_timeout_seconds is not None:
        runtime_config.voicevox_timeout_seconds = args.voicevox_timeout_seconds
    factory = RealVideoPipelineFactory(config=runtime_config)
    return ProjectShiroYouTubeOrchestrator(
        preflight_checker=None if args.skip_preflight else factory.create_preflight_checker(),
        video_pipeline=factory.build(),
        video_validator=VideoOutputValidator(),
        youtube_services_factory=youtube_services_factory or build_default_youtube_services,
    )


def run_project_shiro(args, orchestrator=None):
    config = build_config(args)
    active_orchestrator = orchestrator or build_orchestrator(args, config=config)
    return active_orchestrator.run(config)


def print_result(result) -> None:
    print("Project SHIRO Unified Run")
    print("=" * 25)
    print(f"status: {result.status}")
    print(f"topic: {result.topic}")
    print(f"video_path: {result.video_path}")
    print(f"video_size: {result.video_size}")
    print(f"upload_status: {result.upload_status}")
    print(f"metadata_status: {result.metadata_status}")
    print(f"save_status: {result.save_status}")
    print(f"verification_status: {result.verification_status}")
    print(f"channel_identity_confirmed: {result.channel_identity_confirmed}")
    print(f"title: {result.title}")
    print(f"private_selected: {result.private_selected}")
    print(f"save_clicked: {result.save_clicked}")
    print(f"saved: {result.saved}")
    print(f"published: {result.published}")
    print(f"privacy_status: {result.privacy_status}")
    print(f"video_id: {result.video_id}")
    print(f"video_url: {result.video_url}")
    print(f"studio_url: {result.studio_url}")
    print(f"stop_point: {result.stop_point}")
    print(f"failure_stage: {result.failure_stage}")
    print(f"run_report_path: {result.run_report_path or ''}")
    if result.error:
        print(f"error: {result.error}")


def main(argv=None, orchestrator=None) -> int:
    configure_stdout()
    try:
        args = parse_args(argv)
        result = run_project_shiro(args, orchestrator=orchestrator)
    except (RuntimeError, ValueError) as exc:
        print(f"Project SHIRO unified run failed: {exc}")
        return 1
    print_result(result)
    if result.status in {
        "private_verified",
        "video_completed",
        "upload_prepared",
        "metadata_prepared",
        "stopped_before_save",
        "save_unverified",
    }:
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
