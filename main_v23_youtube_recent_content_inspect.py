import argparse
import sys

from company.youtube.studio_upload import (
    YouTubeCDPConfig,
    YouTubeRecentContentInspector,
    YouTubeRecentContentInspectorConfig,
    YouTubeStudioUploadError,
)


DEFAULT_CDP_ENDPOINT = "http://127.0.0.1:9222"


def configure_stdout() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Read-only inspection of recent YouTube Studio content.",
    )
    parser.add_argument("--cdp-endpoint", default=DEFAULT_CDP_ENDPOINT)
    parser.add_argument("--max-items", type=int, default=50)
    parser.add_argument("--max-items-per-location", type=int, default=20)
    parser.add_argument("--target-title", default="")
    return parser.parse_args(argv)


def build_inspector(args):
    return YouTubeRecentContentInspector(
        config=YouTubeCDPConfig(endpoint_url=args.cdp_endpoint),
        inspector_config=YouTubeRecentContentInspectorConfig(
            max_items=args.max_items,
            max_items_per_location=args.max_items_per_location,
        ),
    )


def run_inspect(args, inspector=None) -> dict:
    active_inspector = inspector or build_inspector(args)
    result = active_inspector.inspect(target_title=args.target_title)
    return {
        "status": result.status,
        "records": result.records,
        "checked_locations": result.checked_locations,
        "total_records": result.total_records,
        "private_count": result.private_count,
        "processing_count": result.processing_count,
        "draft_count": result.draft_count,
        "records_without_video_id": result.records_without_video_id,
        "exact_matches": result.exact_matches,
        "normalized_matches": result.normalized_matches,
        "partial_matches": result.partial_matches,
        "project_shiro_candidates": result.project_shiro_candidates,
        "smoke_test_candidates": result.smoke_test_candidates,
        "private_recent_candidates": result.private_recent_candidates,
        "processing_candidates": result.processing_candidates,
        "draft_candidates": result.draft_candidates,
        "empty_title_candidates": result.empty_title_candidates,
        "no_video_id_candidates": result.no_video_id_candidates,
        "error": result.error,
    }


def _print_records(records, limit: int = 20) -> None:
    for index, record in enumerate(records[:limit], start=1):
        print(f"[{index}] title: {record.title}")
        print(f"    privacy_status: {record.privacy_status}")
        print(f"    processing_status: {record.processing_status}")
        print(f"    content_type: {record.content_type}")
        print(f"    video_id: {record.video_id}")
        print(f"    studio_url: {record.studio_url}")
        print(f"    displayed_date: {record.displayed_date}")
        print(f"    candidate_reasons: {record.candidate_reasons}")


def main(argv=None, inspector=None) -> int:
    configure_stdout()
    args = parse_args(argv)
    try:
        result = run_inspect(args, inspector=inspector)
    except (RuntimeError, ValueError, YouTubeStudioUploadError) as exc:
        print(f"YouTube Studio recent content inspection failed: {exc}")
        return 1

    print(f"status: {result['status']}")
    print(f"checked_locations: {result['checked_locations']}")
    print(f"total_records: {result['total_records']}")
    print(f"private_count: {result['private_count']}")
    print(f"processing_count: {result['processing_count']}")
    print(f"draft_count: {result['draft_count']}")
    print(f"records_without_video_id: {result['records_without_video_id']}")
    print(f"exact_matches: {len(result['exact_matches'])}")
    print(f"normalized_matches: {len(result['normalized_matches'])}")
    print(f"partial_matches: {len(result['partial_matches'])}")
    print(f"project_shiro_candidates: {len(result['project_shiro_candidates'])}")
    print(f"smoke_test_candidates: {len(result['smoke_test_candidates'])}")
    print(f"private_recent_candidates: {len(result['private_recent_candidates'])}")
    print(f"processing_candidates: {len(result['processing_candidates'])}")
    print(f"draft_candidates: {len(result['draft_candidates'])}")
    print(f"empty_title_candidates: {len(result['empty_title_candidates'])}")
    print(f"no_video_id_candidates: {len(result['no_video_id_candidates'])}")
    _print_records(result["records"])
    if result["error"]:
        print(f"error: {result['error']}")
    return 0 if result["status"] == "inspected" else 1


if __name__ == "__main__":
    raise SystemExit(main())
