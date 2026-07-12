"""YouTube Data API authentication helpers."""

from company.youtube.auth import (
    YouTubeAuthenticator,
    YouTubeClientFactory,
    YouTubeCredentialStore,
)
from company.youtube.config import YOUTUBE_UPLOAD_SCOPE, YouTubeOAuthConfig
from company.youtube.exceptions import (
    YouTubeAuthError,
    YouTubeClientBuildError,
    YouTubeConfigurationError,
    YouTubeCredentialError,
)

__all__ = [
    "YOUTUBE_UPLOAD_SCOPE",
    "YouTubeAuthError",
    "YouTubeAuthenticator",
    "YouTubeClientBuildError",
    "YouTubeClientFactory",
    "YouTubeConfigurationError",
    "YouTubeCredentialError",
    "YouTubeCredentialStore",
    "YouTubeOAuthConfig",
]
