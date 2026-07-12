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
from company.youtube.studio_upload import (
    PlaywrightCDPBrowserController,
    PlaywrightPersistentBrowserController,
    UploadPreparationResult,
    YouTubeBrowserConfig,
    YouTubeCDPConfig,
    YouTubeStudioLoginChecker,
    YouTubeStudioLoginResult,
    YouTubeStudioSelectors,
    YouTubeStudioUploadPreparer,
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
    "PlaywrightCDPBrowserController",
    "PlaywrightPersistentBrowserController",
    "UploadPreparationResult",
    "YouTubeBrowserConfig",
    "YouTubeCDPConfig",
    "YouTubeStudioLoginChecker",
    "YouTubeStudioLoginResult",
    "YouTubeStudioSelectors",
    "YouTubeStudioUploadPreparer",
]
