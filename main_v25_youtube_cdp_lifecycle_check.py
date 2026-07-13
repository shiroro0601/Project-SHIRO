import argparse
import sys

from company.youtube.studio_upload import (
    CDPLifecycleChecker,
    YouTubeCDPConfig,
)


DEFAULT_CDP_ENDPOINT = "http://127.0.0.1:9222"


def configure_stdout() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Read-only CDP lifecycle check for YouTube Studio.",
    )
    parser.add_argument("--cdp-endpoint", default=DEFAULT_CDP_ENDPOINT)
    parser.add_argument("--timeout-ms", type=int, default=30000)
    return parser.parse_args(argv)


def build_checker(args):
    return CDPLifecycleChecker(
        config=YouTubeCDPConfig(
            endpoint_url=args.cdp_endpoint,
            timeout_ms=args.timeout_ms,
        )
    )


def run_check(args, checker=None) -> dict:
    active_checker = checker or build_checker(args)
    result = active_checker.check()
    return {
        "status": result.status,
        "first_connect": result.first_connect,
        "first_disconnect": result.first_disconnect,
        "chrome_alive_after_disconnect": result.chrome_alive_after_disconnect,
        "second_connect": result.second_connect,
        "studio_readable": result.studio_readable,
        "second_disconnect": result.second_disconnect,
        "chrome_alive_final": result.chrome_alive_final,
        "browser_close_called": result.browser_close_called,
        "snapshots": result.snapshots,
        "error": result.error,
    }


def main(argv=None, checker=None) -> int:
    configure_stdout()
    args = parse_args(argv)
    try:
        result = run_check(args, checker=checker)
    except (RuntimeError, ValueError) as exc:
        print(f"YouTube CDP lifecycle check failed: {exc}")
        return 1

    print(f"status: {result['status']}")
    print(f"first_connect: {result['first_connect']}")
    print(f"first_disconnect: {result['first_disconnect']}")
    print(f"chrome_alive_after_disconnect: {result['chrome_alive_after_disconnect']}")
    print(f"second_connect: {result['second_connect']}")
    print(f"studio_readable: {result['studio_readable']}")
    print(f"second_disconnect: {result['second_disconnect']}")
    print(f"chrome_alive_final: {result['chrome_alive_final']}")
    print(f"browser_close_called: {result['browser_close_called']}")
    for snapshot in result["snapshots"]:
        print(
            "snapshot:"
            f" stage={snapshot.stage}"
            f" browser_connected={snapshot.browser_connected}"
            f" page_closed={snapshot.page_closed}"
            f" context_count={snapshot.context_count}"
            f" page_count={snapshot.page_count}"
            f" current_url={snapshot.current_url}"
        )
    if result["error"]:
        print(f"error: {result['error']}")
    return 0 if result["status"] == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
