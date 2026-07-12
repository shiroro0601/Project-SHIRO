import argparse
import sys

from company.youtube.studio_upload import (
    PlaywrightCDPBrowserController,
    YouTubeBrowserConfig,
    YouTubeCDPConfig,
    YouTubeMetadataPreparer,
    YouTubeStudioUploadError,
    YouTubeStudioUploadPreparer,
    YouTubeVideoMetadata,
)


DEFAULT_CDP_ENDPOINT = "http://127.0.0.1:9222"


def configure_stdout() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Prepare YouTube Studio metadata without saving or publishing.",
    )
    parser.add_argument("--cdp-endpoint", default=DEFAULT_CDP_ENDPOINT)
    parser.add_argument("--video", required=True)
    parser.add_argument("--title", required=True)
    parser.add_argument("--description", default="")
    parser.add_argument("--tag", action="append", default=[])
    audience = parser.add_mutually_exclusive_group(required=True)
    audience.add_argument("--made-for-kids", action="store_true")
    audience.add_argument("--not-made-for-kids", action="store_true")
    parser.add_argument("--keep-open", action="store_true")
    return parser.parse_args(argv)


def build_metadata(args) -> YouTubeVideoMetadata:
    return YouTubeVideoMetadata(
        title=args.title,
        description=args.description,
        made_for_kids=bool(args.made_for_kids),
        tags=tuple(args.tag or ()),
    )


def build_metadata_preparer(args):
    cdp_config = YouTubeCDPConfig(endpoint_url=args.cdp_endpoint)
    browser = PlaywrightCDPBrowserController(config=cdp_config).start()
    upload_preparer = YouTubeStudioUploadPreparer(
        config=YouTubeBrowserConfig(studio_url=cdp_config.studio_url),
        browser=browser,
    )
    return YouTubeMetadataPreparer(upload_preparer=upload_preparer)


def run_metadata_prepare(args, metadata_preparer=None) -> dict:
    metadata = build_metadata(args)
    preparer = metadata_preparer or build_metadata_preparer(args)
    result = preparer.prepare_metadata(
        args.video,
        metadata,
        keep_open=args.keep_open,
    )
    return {
        "status": result.status,
        "video_path": result.video_path,
        "title": result.title,
        "description": result.description,
        "made_for_kids": result.made_for_kids,
        "tags": result.tags,
        "title_applied": result.title_applied,
        "description_applied": result.description_applied,
        "audience_applied": result.audience_applied,
        "tags_applied": result.tags_applied,
        "saved": result.saved,
        "published": result.published,
        "error": result.error,
    }


def main(argv=None, metadata_preparer=None) -> int:
    configure_stdout()
    args = parse_args(argv)
    try:
        result = run_metadata_prepare(args, metadata_preparer=metadata_preparer)
    except (RuntimeError, ValueError, YouTubeStudioUploadError) as exc:
        print(f"YouTube Studio metadata preparation failed: {exc}")
        return 1

    print(f"status: {result['status']}")
    print(f"title_applied: {result['title_applied']}")
    print(f"description_applied: {result['description_applied']}")
    print(f"audience_applied: {result['audience_applied']}")
    print(f"tags_applied: {result['tags_applied']}")
    print(f"saved: {result['saved']}")
    print(f"published: {result['published']}")
    if result["error"]:
        print(f"error: {result['error']}")
    return 0 if result["status"] == "metadata_prepared" else 1


if __name__ == "__main__":
    raise SystemExit(main())
