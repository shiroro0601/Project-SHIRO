import argparse
import sys
from pathlib import Path

from company.youtube.auth import YouTubeAuthenticator, YouTubeClientFactory
from company.youtube.config import YouTubeOAuthConfig
from company.youtube.exceptions import YouTubeAuthError


def configure_stdout() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Set up Project SHIRO YouTube OAuth credentials.",
    )
    parser.add_argument("--client-secrets", default=None)
    parser.add_argument("--token-path", default=None)
    parser.add_argument("--no-browser", action="store_true")
    return parser.parse_args(argv)


def build_config_from_args(args) -> YouTubeOAuthConfig:
    base_config = YouTubeOAuthConfig.from_env()
    return YouTubeOAuthConfig(
        client_secrets_path=Path(args.client_secrets)
        if args.client_secrets
        else base_config.client_secrets_path,
        token_path=Path(args.token_path) if args.token_path else base_config.token_path,
        scopes=base_config.scopes,
        local_server_host=base_config.local_server_host,
        local_server_port=base_config.local_server_port,
        open_browser=False if args.no_browser else base_config.open_browser,
    )


def run_youtube_oauth_setup(
    config: YouTubeOAuthConfig,
    authenticator=None,
    client_factory=None,
) -> dict:
    authenticator = authenticator or YouTubeAuthenticator(config=config)
    credentials = authenticator.authenticate()
    client = (client_factory or YouTubeClientFactory()).build(credentials)
    return {
        "status": "authenticated",
        "token_path": str(config.token_path),
        "client": client,
    }


def main(argv=None, authenticator=None, client_factory=None) -> int:
    configure_stdout()
    args = parse_args(argv)
    config = build_config_from_args(args)
    try:
        result = run_youtube_oauth_setup(
            config,
            authenticator=authenticator,
            client_factory=client_factory,
        )
    except YouTubeAuthError as exc:
        print(f"YouTube OAuth setup failed: {exc}")
        return 1

    print("YouTube OAuth setup succeeded.")
    print(f"Token path: {result['token_path']}")
    print("No video upload was performed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
