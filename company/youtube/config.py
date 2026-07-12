import os
from dataclasses import dataclass
from pathlib import Path


YOUTUBE_UPLOAD_SCOPE = "https://www.googleapis.com/auth/youtube.upload"


def _parse_bool(value: str | bool) -> bool:
    if isinstance(value, bool):
        return value
    return value.strip().lower() not in {"0", "false", "no", "off"}


@dataclass(frozen=True)
class YouTubeOAuthConfig:
    client_secrets_path: Path = Path("secrets/youtube/client_secret.json")
    token_path: Path = Path("secrets/youtube/token.json")
    scopes: tuple[str, ...] = (YOUTUBE_UPLOAD_SCOPE,)
    local_server_host: str = "127.0.0.1"
    local_server_port: int = 0
    open_browser: bool = True

    def __post_init__(self):
        object.__setattr__(self, "client_secrets_path", Path(self.client_secrets_path))
        object.__setattr__(self, "token_path", Path(self.token_path))
        object.__setattr__(self, "scopes", tuple(self.scopes))

    @classmethod
    def from_env(cls, environ=None):
        environ = environ or os.environ
        return cls(
            client_secrets_path=Path(
                environ.get(
                    "PROJECT_SHIRO_YOUTUBE_CLIENT_SECRETS",
                    cls.client_secrets_path,
                )
            ),
            token_path=Path(
                environ.get(
                    "PROJECT_SHIRO_YOUTUBE_TOKEN_PATH",
                    cls.token_path,
                )
            ),
            local_server_host=environ.get(
                "PROJECT_SHIRO_YOUTUBE_OAUTH_HOST",
                cls.local_server_host,
            ),
            local_server_port=int(
                environ.get(
                    "PROJECT_SHIRO_YOUTUBE_OAUTH_PORT",
                    cls.local_server_port,
                )
            ),
            open_browser=_parse_bool(
                environ.get(
                    "PROJECT_SHIRO_YOUTUBE_OPEN_BROWSER",
                    str(cls.open_browser),
                )
            ),
        )
