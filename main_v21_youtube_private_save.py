import argparse
import sys

from company.youtube.studio_upload import (
    PlaywrightCDPBrowserController,
    YouTubeBrowserConfig,
    YouTubeCDPConfig,
    YouTubeMetadataPreparer,
    YouTubePrivateSaveConfirmer,
    YouTubePrivateSavePolicy,
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
        description="Save a YouTube Studio upload as Private after explicit confirmation.",
    )
    parser.add_argument("--cdp-endpoint", default=DEFAULT_CDP_ENDPOINT)
    parser.add_argument("--video", required=True)
    parser.add_argument("--title", required=True)
    parser.add_argument("--description", default="")
    parser.add_argument("--tag", action="append", default=[])
    audience = parser.add_mutually_exclusive_group(required=True)
    audience.add_argument("--made-for-kids", action="store_true")
    audience.add_argument("--not-made-for-kids", action="store_true")
    parser.add_argument("--confirm-private-save", action="store_true")
    parser.add_argument("--keep-open", action="store_true")
    return parser.parse_args(argv)


def build_metadata(args) -> YouTubeVideoMetadata:
    return YouTubeVideoMetadata(
        title=args.title,
        description=args.description,
        made_for_kids=bool(args.made_for_kids),
        tags=tuple(args.tag or ()),
    )


def build_private_save_confirmer(args):
    cdp_config = YouTubeCDPConfig(endpoint_url=args.cdp_endpoint)
    browser = PlaywrightCDPBrowserController(config=cdp_config).start()
    upload_preparer = YouTubeStudioUploadPreparer(
        config=YouTubeBrowserConfig(studio_url=cdp_config.studio_url),
        browser=browser,
    )
    metadata_preparer = YouTubeMetadataPreparer(upload_preparer=upload_preparer)
    return YouTubePrivateSaveConfirmer(metadata_preparer=metadata_preparer)


def run_private_save(args, private_save_confirmer=None) -> dict:
    metadata = build_metadata(args)
    confirmer = private_save_confirmer or build_private_save_confirmer(args)
    result = confirmer.save_private(
        args.video,
        metadata,
        policy=YouTubePrivateSavePolicy(
            confirm_private_save=bool(args.confirm_private_save)
        ),
        keep_open=args.keep_open,
    )
    return {
        "status": result.status,
        "video_path": result.video_path,
        "title": result.title,
        "privacy_status": result.privacy_status,
        "private_selected": result.private_selected,
        "save_clicked": result.save_clicked,
        "saved": result.saved,
        "published": result.published,
        "video_url": result.video_url,
        "studio_url": result.studio_url,
        "error": result.error,
    }


def main(argv=None, private_save_confirmer=None) -> int:
    configure_stdout()
    args = parse_args(argv)
    try:
        result = run_private_save(args, private_save_confirmer=private_save_confirmer)
    except (RuntimeError, ValueError, YouTubeStudioUploadError) as exc:
        print(f"YouTube Studio private save failed: {exc}")
        return 1

    print(f"status: {result['status']}")
    print(f"private_selected: {result['private_selected']}")
    print(f"save_clicked: {result['save_clicked']}")
    print(f"saved: {result['saved']}")
    print(f"published: {result['published']}")
    print(f"privacy_status: {result['privacy_status']}")
    print(f"video_url: {result['video_url']}")
    print(f"studio_url: {result['studio_url']}")
    if result["error"]:
        print(f"error: {result['error']}")
    return 0 if result["status"] == "private_saved" else 1


if __name__ == "__main__":
    raise SystemExit(main())
