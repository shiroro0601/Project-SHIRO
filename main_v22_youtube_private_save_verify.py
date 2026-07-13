import argparse
import sys

from company.youtube.studio_upload import (
    YouTubeCDPConfig,
    YouTubePrivateSaveVerifierConfig,
    YouTubePrivateSaveVerifier,
    YouTubeStudioUploadError,
)


DEFAULT_CDP_ENDPOINT = "http://127.0.0.1:9222"


def configure_stdout() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Read-only verification for a YouTube Studio private save.",
    )
    parser.add_argument("--cdp-endpoint", default=DEFAULT_CDP_ENDPOINT)
    parser.add_argument("--title", required=True)
    parser.add_argument("--timeout-seconds", type=float, default=120.0)
    parser.add_argument("--poll-interval-seconds", type=float, default=10.0)
    parser.add_argument("--max-items", type=int, default=50)
    parser.add_argument("--no-wait", action="store_true")
    return parser.parse_args(argv)


def build_verifier(args):
    poll_interval = 0.0 if args.no_wait else args.poll_interval_seconds
    return YouTubePrivateSaveVerifier(
        config=YouTubeCDPConfig(endpoint_url=args.cdp_endpoint),
        verifier_config=YouTubePrivateSaveVerifierConfig(
            timeout_seconds=args.timeout_seconds,
            poll_interval_seconds=poll_interval,
            max_items=args.max_items,
        ),
    )


def run_verify(args, verifier=None) -> dict:
    active_verifier = verifier or build_verifier(args)
    result = active_verifier.verify(args.title)
    return {
        "status": result.status,
        "found": result.found,
        "title": result.title,
        "title_matched": result.title_matched,
        "privacy_status": result.privacy_status,
        "private_confirmed": result.private_confirmed,
        "duplicate_count": result.duplicate_count,
        "video_url": result.video_url,
        "studio_url": result.studio_url,
        "error": result.error,
        "matched_title": result.matched_title,
        "match_type": result.match_type,
        "video_id": result.video_id,
        "content_type": result.content_type,
        "processing": result.processing,
        "checked_locations": result.checked_locations,
        "candidate_titles": result.candidate_titles,
        "elapsed_seconds": result.elapsed_seconds,
    }


def main(argv=None, verifier=None) -> int:
    configure_stdout()
    args = parse_args(argv)
    try:
        result = run_verify(args, verifier=verifier)
    except (RuntimeError, ValueError, YouTubeStudioUploadError) as exc:
        print(f"YouTube Studio private save verification failed: {exc}")
        return 1

    print(f"status: {result['status']}")
    print(f"found: {result['found']}")
    print(f"title_matched: {result['title_matched']}")
    print(f"privacy_status: {result['privacy_status']}")
    print(f"private_confirmed: {result['private_confirmed']}")
    print(f"duplicate_count: {result['duplicate_count']}")
    print(f"video_url: {result['video_url']}")
    print(f"studio_url: {result['studio_url']}")
    print(f"matched_title: {result['matched_title']}")
    print(f"match_type: {result['match_type']}")
    print(f"video_id: {result['video_id']}")
    print(f"content_type: {result['content_type']}")
    print(f"processing: {result['processing']}")
    print(f"checked_locations: {result['checked_locations']}")
    print(f"candidate_titles: {result['candidate_titles']}")
    print(f"elapsed_seconds: {result['elapsed_seconds']}")
    if result["error"]:
        print(f"error: {result['error']}")
    return 0 if result["status"] == "verified_private" else 1


if __name__ == "__main__":
    raise SystemExit(main())
