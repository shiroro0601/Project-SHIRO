import argparse
import sys

from company.youtube.studio_upload import (
    PlaywrightCDPBrowserController,
    YouTubeCDPConfig,
    YouTubeStudioUploadError,
    YouTubeUploadReadinessChecker,
)


DEFAULT_CDP_ENDPOINT = "http://127.0.0.1:9222"


def configure_stdout() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Read-only inspection of current YouTube Studio save readiness.",
    )
    parser.add_argument("--cdp-endpoint", default=DEFAULT_CDP_ENDPOINT)
    return parser.parse_args(argv)


def inspect_readiness(args, browser=None):
    active_browser = browser or PlaywrightCDPBrowserController(
        YouTubeCDPConfig(endpoint_url=args.cdp_endpoint)
    ).start()
    should_close = browser is None
    try:
        result = YouTubeUploadReadinessChecker().check(active_browser)
        return {
            "current_step": result.current_step,
            "dialog_open": result.dialog_open,
            "upload_progress": result.upload_progress_text,
            "upload_complete": result.upload_complete,
            "processing": result.processing,
            "blocking_error": result.blocking_error,
            "error_messages": result.error_messages,
            "private_checked": result.private_checked,
            "save_button_found": result.save_button_found,
            "save_button_label": result.save_button_label,
            "save_button_enabled": result.save_enabled,
            "ready_for_save": result.ready_for_save,
        }
    finally:
        if should_close:
            active_browser.safe_disconnect()


def main(argv=None, browser=None) -> int:
    configure_stdout()
    args = parse_args(argv)
    try:
        result = inspect_readiness(args, browser=browser)
    except (RuntimeError, ValueError, YouTubeStudioUploadError) as exc:
        print(f"YouTube save readiness inspection failed: {exc}")
        return 1

    print(f"current_step: {result['current_step']}")
    print(f"dialog_open: {result['dialog_open']}")
    print(f"upload_progress: {result['upload_progress']}")
    print(f"upload_complete: {result['upload_complete']}")
    print(f"processing: {result['processing']}")
    print(f"blocking_error: {result['blocking_error']}")
    print(f"error_messages: {result['error_messages']}")
    print(f"private_checked: {result['private_checked']}")
    print(f"save_button_found: {result['save_button_found']}")
    print(f"save_button_label: {result['save_button_label']}")
    print(f"save_button_enabled: {result['save_button_enabled']}")
    print(f"ready_for_save: {result['ready_for_save']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
