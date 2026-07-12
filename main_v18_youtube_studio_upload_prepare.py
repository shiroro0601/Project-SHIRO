import argparse
import sys
from pathlib import Path

from company.youtube.studio_upload import (
    PlaywrightCDPBrowserController,
    YouTubeCDPConfig,
    YouTubeBrowserConfig,
    YouTubeStudioUploadError,
    YouTubeStudioUploadPreparer,
)


DEFAULT_YOUTUBE_PROFILE_DIR = (
    Path(__file__).resolve().parent
    / "outputs"
    / "browser_profiles"
    / "youtube"
)
DEFAULT_YOUTUBE_CDP_PROFILE_DIR = (
    Path(__file__).resolve().parent
    / "outputs"
    / "browser_profiles"
    / "youtube_cdp"
)
DEFAULT_CDP_ENDPOINT = "http://127.0.0.1:9222"


def configure_stdout() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Prepare a generated MP4 in YouTube Studio without publishing.",
    )
    parser.add_argument("--video", default="")
    parser.add_argument("--login-only", action="store_true")
    parser.add_argument("--keep-open", action="store_true")
    parser.add_argument("--profile-dir", default=None)
    parser.add_argument("--headless", action="store_true")
    parser.add_argument("--browser-channel", default=None)
    parser.add_argument(
        "--connection-mode",
        choices=("persistent", "cdp"),
        default="persistent",
    )
    parser.add_argument("--cdp-endpoint", default=DEFAULT_CDP_ENDPOINT)
    parser.add_argument(
        "--print-cdp-chrome-command",
        action="store_true",
        help="Print a safe Chrome remote debugging launch command.",
    )
    return parser.parse_args(argv)


def build_config(args) -> YouTubeBrowserConfig:
    return YouTubeBrowserConfig(
        user_data_dir=Path(args.profile_dir)
        if args.profile_dir
        else DEFAULT_YOUTUBE_PROFILE_DIR,
        headless=args.headless,
        browser_channel=args.browser_channel,
    )


def build_cdp_config(args) -> YouTubeCDPConfig:
    return YouTubeCDPConfig(
        endpoint_url=args.cdp_endpoint,
        studio_url="https://studio.youtube.com/",
    )


def build_cdp_chrome_command(profile_dir: Path = DEFAULT_YOUTUBE_CDP_PROFILE_DIR) -> str:
    chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    return (
        f'"{chrome_path}" ^\n'
        "  --remote-debugging-address=127.0.0.1 ^\n"
        "  --remote-debugging-port=9222 ^\n"
        f'  --user-data-dir="{profile_dir}" ^\n'
        "  https://studio.youtube.com/"
    )


def build_preparer(args):
    if args.connection_mode == "cdp":
        cdp_config = build_cdp_config(args)
        browser = PlaywrightCDPBrowserController(config=cdp_config).start()
        return YouTubeStudioUploadPreparer(
            config=YouTubeBrowserConfig(studio_url=cdp_config.studio_url),
            browser=browser,
        )
    return YouTubeStudioUploadPreparer(config=build_config(args))


def run_upload_prepare(args, preparer=None) -> dict:
    preparer = preparer or build_preparer(args)
    if args.login_only:
        result = preparer.login_only(keep_open=args.keep_open)
        return {
            "status": result.status,
            "logged_in": result.logged_in,
            "current_url": result.current_url,
            "reason": result.reason,
            "upload_started": False,
            "saved": False,
            "published": False,
        }
    if not args.video:
        raise ValueError("--video is required unless --login-only is used.")
    result = preparer.prepare_upload(args.video, keep_open=args.keep_open)
    return {
        "status": result.status,
        "video_path": result.video_path,
        "filename": result.filename,
        "upload_started": result.upload_started,
        "details_visible": result.details_visible,
        "logged_in": result.logged_in,
        "current_url": result.current_url,
        "saved": result.saved,
        "published": result.published,
        "error": result.error,
    }


def main(argv=None, preparer=None) -> int:
    configure_stdout()
    args = parse_args(argv)
    if args.print_cdp_chrome_command:
        print(build_cdp_chrome_command())
        return 0
    try:
        result = run_upload_prepare(args, preparer=preparer)
    except (ValueError, RuntimeError, YouTubeStudioUploadError) as exc:
        print(f"YouTube Studio upload preparation failed: {exc}")
        return 1

    print(f"status: {result['status']}")
    print(f"logged_in: {result.get('logged_in')}")
    print(f"upload_started: {result.get('upload_started')}")
    print(f"saved: {result.get('saved')}")
    print(f"published: {result.get('published')}")
    if result.get("video_path"):
        print(f"video_path: {result['video_path']}")
    return 0 if result["status"] in {"logged_in", "prepared"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
