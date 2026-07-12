import json
import os
from pathlib import Path
from uuid import uuid4

from company.youtube.config import YouTubeOAuthConfig
from company.youtube.exceptions import (
    YouTubeAuthError,
    YouTubeClientBuildError,
    YouTubeConfigurationError,
    YouTubeCredentialError,
)


class YouTubeCredentialStore:
    def __init__(self, config: YouTubeOAuthConfig, credential_loader=None):
        self.config = config
        self.token_path = Path(config.token_path)
        self.credential_loader = credential_loader or self._default_credential_loader

    def load(self):
        if not self.token_path.exists():
            return None

        try:
            data = json.loads(self.token_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise YouTubeCredentialError(
                f"Invalid YouTube token JSON: {self.token_path}"
            ) from exc
        except OSError as exc:
            raise YouTubeCredentialError(
                f"Failed to read YouTube token file: {self.token_path}"
            ) from exc

        try:
            return self.credential_loader(data, self.config.scopes)
        except YouTubeCredentialError:
            raise
        except Exception as exc:
            raise YouTubeCredentialError(
                f"Failed to load YouTube credentials from token file: {self.token_path}"
            ) from exc

    def save(self, credentials) -> None:
        payload = self._serialize_credentials(credentials)
        self.token_path.parent.mkdir(parents=True, exist_ok=True)
        temp_path = self.token_path.parent / f".{self.token_path.name}.{uuid4().hex}.tmp"
        try:
            with open(temp_path, "w", encoding="utf-8") as temp_file:
                temp_file.write(payload)
                temp_file.flush()
                os.fsync(temp_file.fileno())
            os.replace(str(temp_path), str(self.token_path))
        except Exception as exc:
            raise YouTubeCredentialError(
                f"Failed to save YouTube token file: {self.token_path}"
            ) from exc
        finally:
            try:
                if temp_path.exists():
                    temp_path.unlink()
            except OSError:
                pass

    def _serialize_credentials(self, credentials) -> str:
        try:
            if hasattr(credentials, "to_json"):
                data = json.loads(credentials.to_json())
            elif isinstance(credentials, dict):
                data = dict(credentials)
            else:
                data = dict(credentials.__dict__)
            return json.dumps(data, ensure_ascii=False, indent=2)
        except Exception as exc:
            raise YouTubeCredentialError("Failed to serialize YouTube token.") from exc

    def _default_credential_loader(self, data: dict, scopes: tuple[str, ...]):
        try:
            from google.oauth2.credentials import Credentials
        except ImportError as exc:
            raise YouTubeCredentialError(
                "google-auth is required for YouTube OAuth credentials."
            ) from exc
        return Credentials.from_authorized_user_info(data, scopes=list(scopes))


class YouTubeAuthenticator:
    def __init__(
        self,
        config: YouTubeOAuthConfig | None = None,
        credential_store: YouTubeCredentialStore | None = None,
        flow_factory=None,
        request_factory=None,
    ):
        self.config = config or YouTubeOAuthConfig()
        self.credential_store = credential_store or YouTubeCredentialStore(
            self.config
        )
        self.flow_factory = flow_factory or self._default_flow_factory
        self.request_factory = request_factory or self._default_request_factory

    def authenticate(self):
        credentials = self.credential_store.load()
        if credentials is not None:
            self._ensure_required_scopes(credentials)
            if getattr(credentials, "valid", False):
                return credentials

            if getattr(credentials, "expired", False) and getattr(
                credentials, "refresh_token", None
            ):
                try:
                    credentials.refresh(self.request_factory())
                except Exception as exc:
                    raise YouTubeAuthError("Failed to refresh YouTube token.") from exc
                self._ensure_required_scopes(credentials)
                self.credential_store.save(credentials)
                return credentials

        credentials = self._run_installed_app_flow()
        self._ensure_required_scopes(credentials)
        self.credential_store.save(credentials)
        return credentials

    def _run_installed_app_flow(self):
        self._validate_client_secret_file()
        try:
            flow = self.flow_factory(
                str(self.config.client_secrets_path),
                self.config.scopes,
            )
            return flow.run_local_server(
                host=self.config.local_server_host,
                port=self.config.local_server_port,
                open_browser=self.config.open_browser,
            )
        except YouTubeAuthError:
            raise
        except Exception as exc:
            raise YouTubeAuthError("YouTube OAuth browser authentication failed.") from exc

    def _validate_client_secret_file(self) -> None:
        path = Path(self.config.client_secrets_path)
        if not path.exists():
            raise YouTubeConfigurationError(
                f"YouTube OAuth client secret file not found: {path}"
            )
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise YouTubeConfigurationError(
                f"Invalid YouTube OAuth client secret JSON: {path}"
            ) from exc
        except OSError as exc:
            raise YouTubeConfigurationError(
                f"Failed to read YouTube OAuth client secret file: {path}"
            ) from exc

        if "installed" not in data:
            raise YouTubeConfigurationError(
                "YouTube OAuth client secret must be a Desktop/Installed app."
            )

    def _ensure_required_scopes(self, credentials) -> None:
        missing = self._missing_scopes(credentials)
        if missing:
            raise YouTubeCredentialError(
                "YouTube token is missing required scopes: "
                + ", ".join(sorted(missing))
                + ". Re-authentication is required."
            )

    def _missing_scopes(self, credentials) -> set[str]:
        required = set(self.config.scopes)
        if hasattr(credentials, "has_scopes"):
            try:
                return set() if credentials.has_scopes(list(required)) else required
            except Exception:
                pass

        granted = set(getattr(credentials, "scopes", None) or [])
        if not granted:
            granted = set(getattr(credentials, "granted_scopes", None) or [])
        return required - granted

    def _default_flow_factory(self, client_secrets_path: str, scopes):
        try:
            from google_auth_oauthlib.flow import InstalledAppFlow
        except ImportError as exc:
            raise YouTubeConfigurationError(
                "google-auth-oauthlib is required for YouTube OAuth."
            ) from exc
        return InstalledAppFlow.from_client_secrets_file(
            client_secrets_path,
            list(scopes),
        )

    def _default_request_factory(self):
        try:
            from google.auth.transport.requests import Request
        except ImportError as exc:
            raise YouTubeAuthError(
                "google-auth is required to refresh YouTube credentials."
            ) from exc
        return Request()


class YouTubeClientFactory:
    def __init__(self, build_function=None):
        self.build_function = build_function or self._default_build_function

    def build(self, credentials):
        try:
            return self.build_function(
                "youtube",
                "v3",
                credentials=credentials,
                cache_discovery=False,
            )
        except Exception as exc:
            raise YouTubeClientBuildError(
                "Failed to build YouTube Data API client."
            ) from exc

    def _default_build_function(self, *args, **kwargs):
        try:
            from googleapiclient.discovery import build
        except ImportError as exc:
            raise YouTubeClientBuildError(
                "google-api-python-client is required for YouTube Data API."
            ) from exc
        return build(*args, **kwargs)
