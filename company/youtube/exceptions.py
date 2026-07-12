class YouTubeAuthError(Exception):
    """Raised when YouTube OAuth authentication fails."""


class YouTubeCredentialError(YouTubeAuthError):
    """Raised when token persistence or token content is invalid."""


class YouTubeConfigurationError(YouTubeAuthError):
    """Raised when OAuth configuration or client secret data is invalid."""


class YouTubeClientBuildError(YouTubeAuthError):
    """Raised when the YouTube Data API client cannot be built."""
