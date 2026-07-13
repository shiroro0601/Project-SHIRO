import argparse
import sys

from company.youtube.studio_upload import (
    PlaywrightCDPBrowserController,
    YouTubeBrowserConfig,
    YouTubeCDPConfig,
    YouTubeControlledPrivateSaveRunner,
    YouTubeMetadataPreparer,
    YouTubePrivateSaveAttemptStore,
    YouTubePrivateSaveConfirmer,
    YouTubePrivateSaveVerifier,
    YouTubePrivateSaveVerifierConfig,
    YouTubeStudioChannelIdentityReader,
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
        description="Controlled one-time YouTube Studio private save smoke.",
    )
    parser.add_argument("--cdp-endpoint", default=DEFAULT_CDP_ENDPOINT)
    parser.add_argument("--expected-channel-name", required=True)
    parser.add_argument("--video", required=True)
    parser.add_argument("--smoke-id", required=True)
    parser.add_argument("--description", default="")
    parser.add_argument("--tag", action="append", default=[])
    audience = parser.add_mutually_exclusive_group(required=True)
    audience.add_argument("--made-for-kids", action="store_true")
    audience.add_argument("--not-made-for-kids", action="store_true")
    parser.add_argument("--confirm-private-save", action="store_true", required=True)
    parser.add_argument("--keep-open", action="store_true")
    parser.add_argument(
        "--attempt-store",
        default="outputs/youtube_private_smoke/private_save_attempts.json",
    )
    return parser.parse_args(argv)


def build_metadata(args) -> YouTubeVideoMetadata:
    return YouTubeVideoMetadata(
        title="",
        description=args.description,
        made_for_kids=bool(args.made_for_kids),
        tags=tuple(args.tag or ()),
    )


def build_runner(args):
    cdp_config = YouTubeCDPConfig(endpoint_url=args.cdp_endpoint)
    browser = PlaywrightCDPBrowserController(config=cdp_config).start()
    upload_preparer = YouTubeStudioUploadPreparer(
        config=YouTubeBrowserConfig(studio_url=cdp_config.studio_url),
        browser=browser,
    )
    metadata_preparer = YouTubeMetadataPreparer(upload_preparer=upload_preparer)
    private_save_confirmer = YouTubePrivateSaveConfirmer(
        metadata_preparer=metadata_preparer
    )
    return YouTubeControlledPrivateSaveRunner(
        private_save_confirmer=private_save_confirmer,
        verifier=YouTubePrivateSaveVerifier(
            config=cdp_config,
            verifier_config=YouTubePrivateSaveVerifierConfig(
                timeout_seconds=180,
                poll_interval_seconds=10,
                max_items=50,
            ),
        ),
        identity_reader=YouTubeStudioChannelIdentityReader(
            browser=browser,
            config=cdp_config,
        ),
        attempt_store=YouTubePrivateSaveAttemptStore(args.attempt_store),
        post_save_disconnect=browser.safe_disconnect,
    )


def run_controlled_private_smoke(args, runner=None) -> dict:
    active_runner = runner or build_runner(args)
    result = active_runner.run(
        video_path=args.video,
        metadata=build_metadata(args),
        smoke_id=args.smoke_id,
        expected_channel_name=args.expected_channel_name,
        confirm_private_save=bool(args.confirm_private_save),
        keep_open=args.keep_open,
    )
    return result.__dict__.copy()


def main(argv=None, runner=None) -> int:
    configure_stdout()
    args = parse_args(argv)
    try:
        result = run_controlled_private_smoke(args, runner=runner)
    except (RuntimeError, ValueError, YouTubeStudioUploadError) as exc:
        print(f"YouTube controlled private smoke failed: {exc}")
        return 1

    print(f"status: {result['status']}")
    print(f"smoke_id: {result['smoke_id']}")
    print(f"title: {result['title']}")
    print(f"channel_identity_confirmed: {result['channel_identity_confirmed']}")
    print(f"private_selected: {result['private_selected']}")
    print(f"save_clicked: {result['save_clicked']}")
    print(f"saved: {result['saved']}")
    print(f"published: {result['published']}")
    print(f"privacy_status: {result['privacy_status']}")
    print(f"verification_status: {result['verification_status']}")
    print(f"found: {result['found']}")
    print(f"private_confirmed: {result['private_confirmed']}")
    print(f"duplicate_count: {result['duplicate_count']}")
    print(f"video_id: {result['video_id']}")
    print(f"video_url: {result['video_url']}")
    print(f"studio_url: {result['studio_url']}")
    print(f"content_type: {result['content_type']}")
    if result["error"]:
        print(f"error: {result['error']}")
    return 0 if result["status"] == "verified_private" else 1


if __name__ == "__main__":
    raise SystemExit(main())
