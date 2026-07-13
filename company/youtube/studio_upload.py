from dataclasses import dataclass
from datetime import datetime
import json
import os
from pathlib import Path
import re
import time
from urllib.parse import urljoin, urlparse
import urllib.request
from uuid import uuid4

from company.runtime.real_video_runtime import VideoOutputValidator


STATUS_LOGGED_IN = "logged_in"
STATUS_LOGIN_REQUIRED = "login_required"
STATUS_CHANNEL_UNAVAILABLE = "channel_unavailable"
STATUS_STUDIO_UNAVAILABLE = "studio_unavailable"
STATUS_TIMEOUT = "timeout"
STATUS_UNKNOWN = "unknown"


@dataclass(frozen=True)
class YouTubeBrowserConfig:
    user_data_dir: Path = Path("outputs/browser_profiles/youtube")
    headless: bool = False
    browser_channel: str | None = None
    executable_path: str | None = None
    timeout_ms: int = 30000
    slow_mo_ms: int = 0
    locale: str = "ja-JP"
    studio_url: str = "https://studio.youtube.com/"

    def __post_init__(self):
        object.__setattr__(self, "user_data_dir", Path(self.user_data_dir))


@dataclass(frozen=True)
class YouTubeCDPConfig:
    endpoint_url: str = "http://127.0.0.1:9222"
    timeout_ms: int = 30000
    studio_url: str = "https://studio.youtube.com/"

    def __post_init__(self):
        _validate_cdp_endpoint(self.endpoint_url)


def _validate_cdp_endpoint(endpoint_url: str) -> None:
    parsed = urlparse(endpoint_url)
    hostname = (parsed.hostname or "").lower()
    if parsed.scheme not in {"http", "https"}:
        raise ValueError("CDP endpoint must use http or https.")
    if hostname not in {"127.0.0.1", "localhost"}:
        raise ValueError("CDP endpoint must point to 127.0.0.1 or localhost.")


@dataclass(frozen=True)
class YouTubeStudioSelectors:
    create_button: tuple[str, ...] = (
        "ytcp-button#create-icon",
        "button[aria-label='Create']",
        "button[aria-label='作成']",
    )
    upload_videos_menu_item: tuple[str, ...] = (
        "tp-yt-paper-item#text-item-0",
        "tp-yt-paper-item:has-text('Upload videos')",
        "tp-yt-paper-item:has-text('動画をアップロード')",
    )
    file_input: tuple[str, ...] = ("input[type=file]",)
    file_select_button: tuple[str, ...] = (
        "text=ファイルを選択",
        "text=SELECT FILES",
        "button:has-text('ファイルを選択')",
        "button:has-text('SELECT FILES')",
        "ytcp-button:has-text('ファイルを選択')",
        "ytcp-button:has-text('SELECT FILES')",
    )
    dialog_file_input: tuple[str, ...] = (
        "ytcp-uploads-dialog input[type=file]",
        "tp-yt-paper-dialog input[type=file]",
        "input[type=file]",
    )
    details_dialog: tuple[str, ...] = (
        "ytcp-uploads-dialog",
        "ytcp-video-metadata-editor",
        "input[name=title]",
    )
    logged_in_indicators: tuple[str, ...] = (
        "ytcp-button#create-icon",
        "a[href*='/channel/']",
        "ytcp-app",
    )
    channel_unavailable_indicators: tuple[str, ...] = (
        "text=Create a channel",
        "text=チャンネルを作成",
    )
    save_button: tuple[str, ...] = ("button[data-test-id=draft-save]",)
    publish_button: tuple[str, ...] = ("button:has-text('Publish')",)
    next_button: tuple[str, ...] = (
        "ytcp-button:has-text('次へ')",
        "ytcp-button:has-text('Next')",
    )
    title_input: tuple[str, ...] = (
        "input[name=title]",
        "#title-textarea #textbox",
        "ytcp-social-suggestions-textbox#title-textarea #textbox",
        "ytcp-social-suggestions-textbox[aria-label*='Title']",
        "ytcp-social-suggestions-textbox[aria-label*='タイトル']",
        "[contenteditable=true][aria-label*='Title']",
        "[contenteditable=true][aria-label*='タイトル']",
    )
    description_input: tuple[str, ...] = (
        "textarea[name=description]",
        "#description-textarea #textbox",
        "ytcp-social-suggestions-textbox#description-textarea #textbox",
        "ytcp-social-suggestions-textbox[aria-label*='Description']",
        "ytcp-social-suggestions-textbox[aria-label*='説明']",
        "[contenteditable=true][aria-label*='Description']",
        "[contenteditable=true][aria-label*='説明']",
    )
    made_for_kids_yes: tuple[str, ...] = (
        "tp-yt-paper-radio-button[name=VIDEO_MADE_FOR_KIDS_MFK]",
        "ytcp-radio-button:has-text(\"Yes, it's made for kids\")",
        "ytcp-radio-button:has-text('はい、子ども向けです')",
        "text=Yes, it's made for kids",
        "text=はい、子ども向けです",
    )
    made_for_kids_no: tuple[str, ...] = (
        "tp-yt-paper-radio-button[name=VIDEO_MADE_FOR_KIDS_NOT_MFK]",
        "ytcp-radio-button:has-text(\"No, it's not made for kids\")",
        "ytcp-radio-button:has-text('いいえ、子ども向けではありません')",
        "text=No, it's not made for kids",
        "text=いいえ、子ども向けではありません",
    )
    show_more_button: tuple[str, ...] = (
        "ytcp-video-metadata-editor ytcp-button:has-text('すべて表示')",
        "ytcp-video-metadata-editor ytcp-button:has-text('SHOW MORE')",
        "ytcp-video-metadata-editor ytcp-button:has-text('もっと見る')",
        "ytcp-uploads-dialog ytcp-button:has-text('すべて表示')",
        "ytcp-uploads-dialog ytcp-button:has-text('SHOW MORE')",
        "ytcp-uploads-dialog ytcp-button:has-text('もっと見る')",
        "ytcp-button:has-text('もっと見る')",
        "ytcp-button:has-text('SHOW MORE')",
        "ytcp-button:has-text('すべて表示')",
        "button:has-text('もっと見る')",
        "button:has-text('SHOW MORE')",
        "button:has-text('すべて表示')",
        "text=もっと見る",
        "text=SHOW MORE",
        "text=すべて表示",
    )
    tags_input: tuple[str, ...] = (
        "input[aria-label='Tags']",
        "input[aria-label='タグ']",
        "#tags-container input",
        "ytcp-free-text-chip-bar input",
        "input#text-input",
        "ytcp-form-input-container:has-text('Tags') input",
        "ytcp-form-input-container:has-text('タグ') input",
        "input[name=tags]",
    )
    tag_chips: tuple[str, ...] = (
        "ytcp-chip-bar ytcp-chip",
        "ytcp-chip",
        "[id*=chip]",
    )
    checks_section: tuple[str, ...] = (
        "ytcp-uploads-checks",
        "ytcp-video-checks",
        "text=チェック",
        "text=Checks",
    )
    checks_blocking_error: tuple[str, ...] = (
        "ytcp-uploads-checks ytcp-error",
        "ytcp-video-checks ytcp-error",
        "text=著作権侵害",
        "text=Copyright issue",
        "text=エラー",
        "text=Error",
    )
    upload_progress_text: tuple[str, ...] = (
        "ytcp-video-upload-progress",
        "ytcp-uploads-dialog [id*=progress]",
        "text=/アップロード/",
        "text=/Uploaded/",
        "text=/Processing/",
        "text=/処理中/",
    )
    upload_complete_text: tuple[str, ...] = (
        "text=アップロード済み",
        "text=Upload complete",
        "text=Uploaded",
        "text=完了",
        "text=Complete",
    )
    current_step_text: tuple[str, ...] = (
        "ytcp-uploads-dialog tp-yt-paper-stepper",
        "ytcp-uploads-dialog",
    )
    visibility_step: tuple[str, ...] = (
        "ytcp-video-visibility-select",
        "ytcp-uploads-review",
    )
    private_radio: tuple[str, ...] = (
        "tp-yt-paper-radio-button[name=PRIVATE]",
        "tp-yt-paper-radio-button[name='PRIVATE']",
        "tp-yt-paper-radio-button[aria-label*='非公開']",
        "tp-yt-paper-radio-button[aria-label*='Private']",
        "[role=radio][aria-label*='非公開']",
        "[role=radio][aria-label*='Private']",
        "ytcp-radio-button:has-text('非公開')",
        "ytcp-radio-button:has-text('非公開動画')",
        "ytcp-radio-button:has-text('Private')",
    )
    public_radio: tuple[str, ...] = (
        "tp-yt-paper-radio-button[name=PUBLIC]",
        "ytcp-radio-button:has-text('公開')",
        "ytcp-radio-button:has-text('Public')",
        "text=Public",
    )
    unlisted_radio: tuple[str, ...] = (
        "tp-yt-paper-radio-button[name=UNLISTED]",
        "ytcp-radio-button:has-text('限定公開')",
        "ytcp-radio-button:has-text('Unlisted')",
        "text=Unlisted",
    )
    schedule_option: tuple[str, ...] = (
        "ytcp-radio-button:has-text('スケジュール')",
        "ytcp-radio-button:has-text('Schedule')",
        "text=Schedule",
    )
    private_save_button: tuple[str, ...] = (
        "ytcp-button#done-button:has-text('保存')",
        "ytcp-button#done-button:has-text('SAVE')",
        "ytcp-button#done-button:has-text('完了')",
        "ytcp-button#done-button:has-text('DONE')",
        "button:has-text('保存')",
        "button:has-text('SAVE')",
        "button:has-text('完了')",
        "button:has-text('DONE')",
    )
    save_success: tuple[str, ...] = (
        "text=動画を公開しました",
        "text=非公開として保存済み",
        "text=Saved as private",
        "text=Video saved",
        "ytcp-video-share-dialog",
        "ytcp-uploads-dialog[hidden]",
    )
    video_link: tuple[str, ...] = (
        "a[href*='youtu.be/']",
        "a[href*='youtube.com/watch']",
        "a[href*='/video/']",
    )
    content_video_rows: tuple[str, ...] = (
        "ytcp-video-row",
        "ytcp-video-list-cell-video",
    )
    content_search_input: tuple[str, ...] = (
        "input[placeholder*='検索']",
        "input[aria-label*='検索']",
        "input[placeholder*='Search']",
        "input[aria-label*='Search']",
        "ytcp-omnisearch input",
    )

@dataclass(frozen=True)
class YouTubeVideoMetadata:
    title: str
    description: str
    made_for_kids: bool
    tags: tuple[str, ...] = ()

    def __post_init__(self):
        object.__setattr__(self, "title", str(self.title).strip())
        object.__setattr__(self, "description", str(self.description))
        object.__setattr__(self, "tags", self._normalize_tags(self.tags))

    def _normalize_tags(self, tags) -> tuple[str, ...]:
        seen = set()
        normalized = []
        for tag in tuple(tags or ()):
            clean = str(tag).strip()
            if not clean or clean in seen:
                continue
            seen.add(clean)
            normalized.append(clean)
        return tuple(normalized)


@dataclass
class YouTubeMetadataPreparationResult:
    status: str
    video_path: str
    title: str
    description: str
    made_for_kids: bool
    tags: tuple[str, ...]
    title_applied: bool
    description_applied: bool
    audience_applied: bool
    tags_applied: bool
    saved: bool = False
    published: bool = False
    error: str = ""


@dataclass
class YouTubePrivateSaveResult:
    status: str
    video_path: str
    title: str
    privacy_status: str
    private_selected: bool
    save_clicked: bool
    saved: bool
    published: bool
    video_url: str = ""
    studio_url: str = ""
    error: str = ""
    evidence: object | None = None


@dataclass
class YouTubePrivateSaveVerificationResult:
    status: str
    found: bool
    title: str
    title_matched: bool
    privacy_status: str
    private_confirmed: bool
    duplicate_count: int
    video_url: str = ""
    studio_url: str = ""
    error: str = ""
    matched_title: str = ""
    match_type: str = ""
    video_id: str = ""
    content_type: str = "unknown"
    processing: bool = False
    checked_locations: tuple[str, ...] = ()
    candidate_titles: tuple[str, ...] = ()
    elapsed_seconds: float = 0.0


@dataclass(frozen=True)
class YouTubePrivateSaveVerifierConfig:
    timeout_seconds: float = 120.0
    poll_interval_seconds: float = 10.0
    max_items: int = 50
    allow_partial_matches: bool = False

    def __post_init__(self):
        if self.timeout_seconds < 0:
            raise ValueError("timeout_seconds must be 0 or greater.")
        if self.poll_interval_seconds < 0:
            raise ValueError("poll_interval_seconds must be 0 or greater.")
        if self.max_items <= 0:
            raise ValueError("max_items must be greater than 0.")


@dataclass(frozen=True)
class YouTubeContentRecord:
    title: str
    normalized_title: str
    privacy_status: str
    processing_status: str
    content_type: str
    video_id: str = ""
    video_url: str = ""
    studio_url: str = ""
    displayed_date: str = ""
    row_index: int = 0
    candidate_reasons: tuple[str, ...] = ()


@dataclass(frozen=True)
class YouTubeRecentContentInspectionResult:
    status: str
    records: tuple[YouTubeContentRecord, ...] = ()
    checked_locations: tuple[str, ...] = ()
    total_records: int = 0
    private_count: int = 0
    processing_count: int = 0
    draft_count: int = 0
    records_without_video_id: int = 0
    exact_matches: tuple[YouTubeContentRecord, ...] = ()
    normalized_matches: tuple[YouTubeContentRecord, ...] = ()
    partial_matches: tuple[YouTubeContentRecord, ...] = ()
    project_shiro_candidates: tuple[YouTubeContentRecord, ...] = ()
    smoke_test_candidates: tuple[YouTubeContentRecord, ...] = ()
    private_recent_candidates: tuple[YouTubeContentRecord, ...] = ()
    processing_candidates: tuple[YouTubeContentRecord, ...] = ()
    draft_candidates: tuple[YouTubeContentRecord, ...] = ()
    empty_title_candidates: tuple[YouTubeContentRecord, ...] = ()
    no_video_id_candidates: tuple[YouTubeContentRecord, ...] = ()
    error: str = ""


@dataclass(frozen=True)
class YouTubeRecentContentInspectorConfig:
    max_items: int = 50
    max_items_per_location: int = 20
    row_retry_count: int = 3
    row_retry_interval_seconds: float = 1.0

    def __post_init__(self):
        if self.max_items <= 0:
            raise ValueError("max_items must be greater than 0.")
        if self.max_items_per_location <= 0:
            raise ValueError("max_items_per_location must be greater than 0.")
        if self.row_retry_count < 0:
            raise ValueError("row_retry_count must be 0 or greater.")
        if self.row_retry_interval_seconds < 0:
            raise ValueError("row_retry_interval_seconds must be 0 or greater.")


@dataclass
class YouTubeStudioChannelIdentity:
    channel_name: str = ""
    channel_id: str = ""
    current_url: str = ""
    studio_available: bool = False
    identity_confirmed: bool = False
    error: str = ""


@dataclass
class YouTubePrivateSaveAttempt:
    smoke_id: str
    title: str
    video_path: str
    video_size: int
    attempted_at: str
    save_clicked: bool = False
    verification_status: str = ""
    video_id: str = ""
    save_click_status: str = "not_attempted"
    save_completion_status: str = "not_started"
    cdp_disconnect_stage: str = ""
    last_error: str = ""
    updated_at: str = ""
    upload_readiness_status: str = ""
    upload_complete_before_save: bool = False
    blocking_error: bool = False
    save_button_label: str = ""
    save_response_status: str = ""
    completion_evidence: dict | None = None
    timeout_stage: str = ""
    post_save_video_id: str = ""
    post_save_private_confirmed: bool = False

    def to_dict(self) -> dict:
        return {
            "smoke_id": self.smoke_id,
            "title": self.title,
            "video_path": self.video_path,
            "video_size": self.video_size,
            "attempted_at": self.attempted_at,
            "save_clicked": self.save_clicked,
            "verification_status": self.verification_status,
            "video_id": self.video_id,
            "save_click_status": self.save_click_status,
            "save_completion_status": self.save_completion_status,
            "cdp_disconnect_stage": self.cdp_disconnect_stage,
            "last_error": self.last_error,
            "updated_at": self.updated_at,
            "upload_readiness_status": self.upload_readiness_status,
            "upload_complete_before_save": self.upload_complete_before_save,
            "blocking_error": self.blocking_error,
            "save_button_label": self.save_button_label,
            "save_response_status": self.save_response_status,
            "completion_evidence": self.completion_evidence or {},
            "timeout_stage": self.timeout_stage,
            "post_save_video_id": self.post_save_video_id,
            "post_save_private_confirmed": self.post_save_private_confirmed,
        }

    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            smoke_id=str(data.get("smoke_id", "")),
            title=str(data.get("title", "")),
            video_path=str(data.get("video_path", "")),
            video_size=int(data.get("video_size", 0)),
            attempted_at=str(data.get("attempted_at", "")),
            save_clicked=bool(data.get("save_clicked", False)),
            verification_status=str(data.get("verification_status", "")),
            video_id=str(data.get("video_id", "")),
            save_click_status=str(data.get("save_click_status", "not_attempted")),
            save_completion_status=str(data.get("save_completion_status", "not_started")),
            cdp_disconnect_stage=str(data.get("cdp_disconnect_stage", "")),
            last_error=str(data.get("last_error", "")),
            updated_at=str(data.get("updated_at", "")),
            upload_readiness_status=str(data.get("upload_readiness_status", "")),
            upload_complete_before_save=bool(data.get("upload_complete_before_save", False)),
            blocking_error=bool(data.get("blocking_error", False)),
            save_button_label=str(data.get("save_button_label", "")),
            save_response_status=str(data.get("save_response_status", "")),
            completion_evidence=dict(data.get("completion_evidence", {}) or {}),
            timeout_stage=str(data.get("timeout_stage", "")),
            post_save_video_id=str(data.get("post_save_video_id", "")),
            post_save_private_confirmed=bool(data.get("post_save_private_confirmed", False)),
        )


@dataclass
class YouTubeControlledPrivateSaveResult:
    status: str
    smoke_id: str
    title: str
    channel_identity_confirmed: bool
    private_selected: bool
    save_clicked: bool
    saved: bool
    published: bool
    privacy_status: str
    verification_status: str = ""
    found: bool = False
    private_confirmed: bool = False
    duplicate_count: int = 0
    video_id: str = ""
    video_url: str = ""
    studio_url: str = ""
    content_type: str = "unknown"
    error: str = ""


@dataclass(frozen=True)
class YouTubePrivateSavePolicy:
    confirm_private_save: bool = False
    max_next_clicks: int = 3

    def __post_init__(self):
        if self.max_next_clicks < 0:
            raise ValueError("max_next_clicks must be 0 or greater.")


class YouTubeMetadataValidationError(ValueError):
    pass


class YouTubeMetadataValidator:
    MAX_TITLE_LENGTH = 100
    MAX_DESCRIPTION_LENGTH = 5000
    MAX_TAG_LENGTH = 100
    MAX_TAGS_TOTAL_LENGTH = 500

    def validate(self, metadata: YouTubeVideoMetadata) -> YouTubeVideoMetadata:
        if not isinstance(metadata.made_for_kids, bool):
            raise YouTubeMetadataValidationError("made_for_kids must be bool.")
        self._validate_title(metadata.title)
        self._validate_description(metadata.description)
        self._validate_tags(metadata.tags)
        return metadata

    def _validate_title(self, title: str) -> None:
        if not title:
            raise YouTubeMetadataValidationError("title is required.")
        if len(title) > self.MAX_TITLE_LENGTH:
            raise YouTubeMetadataValidationError("title must be 100 characters or less.")
        if "\n" in title or "\r" in title:
            raise YouTubeMetadataValidationError("title must not contain newlines.")
        if self._has_control_chars(title, allow_newlines=False):
            raise YouTubeMetadataValidationError("title contains control characters.")

    def _validate_description(self, description: str) -> None:
        if len(description) > self.MAX_DESCRIPTION_LENGTH:
            raise YouTubeMetadataValidationError(
                "description must be 5000 characters or less."
            )
        if self._has_control_chars(description, allow_newlines=True):
            raise YouTubeMetadataValidationError(
                "description contains control characters."
            )

    def _validate_tags(self, tags: tuple[str, ...]) -> None:
        total = 0
        for tag in tags:
            if "," in tag:
                raise YouTubeMetadataValidationError(
                    "tags must not contain commas; pass each tag separately."
                )
            if len(tag) > self.MAX_TAG_LENGTH:
                raise YouTubeMetadataValidationError("tag is too long.")
            if self._has_control_chars(tag, allow_newlines=False):
                raise YouTubeMetadataValidationError("tag contains control characters.")
            total += len(tag)
        if total > self.MAX_TAGS_TOTAL_LENGTH:
            raise YouTubeMetadataValidationError("tags total length is too long.")

    def _has_control_chars(self, value: str, allow_newlines: bool) -> bool:
        allowed = {"\n", "\r", "\t"} if allow_newlines else set()
        return any(ord(char) < 32 and char not in allowed for char in value)


@dataclass
class YouTubeStudioLoginResult:
    status: str
    logged_in: bool
    current_url: str
    reason: str = ""


@dataclass
class UploadPreparationResult:
    status: str
    video_path: str
    filename: str
    upload_started: bool
    details_visible: bool
    logged_in: bool
    current_url: str
    published: bool = False
    saved: bool = False
    error: str = ""


@dataclass(frozen=True)
class CDPConnectionSnapshot:
    stage: str
    browser_connected: bool
    page_closed: bool
    context_count: int
    page_count: int
    current_url: str
    captured_at: str
    error_type: str = ""
    error_message: str = ""


@dataclass
class YouTubePrivateSaveEvidence:
    private_checked_before_click: bool = False
    upload_complete_before_click: bool = False
    upload_progress_text: str = ""
    blocking_error_detected: bool = False
    blocking_error_text: str = ""
    save_button_found: bool = False
    save_button_enabled: bool = False
    save_button_exact_label: str = ""
    save_button_label: str = ""
    save_click_dispatched: bool = False
    click_dispatched: bool = False
    dialog_closed: bool = False
    post_click_dialog_closed: bool = False
    success_message_detected: bool = False
    post_click_success_toast: bool = False
    post_click_video_id: str = ""
    post_click_video_link: str = ""
    post_click_content_row_detected: bool = False
    post_click_private_visibility_detected: bool = False
    completion_evidence_count: int = 0
    content_page_detected: bool = False
    video_link_detected: bool = False
    completion_confirmed: bool = False
    cdp_disconnect_stage: str = ""


@dataclass(frozen=True)
class YouTubeUploadReadiness:
    upload_complete: bool
    processing: bool
    checks_complete: bool
    blocking_error: bool
    save_enabled: bool
    private_checked: bool
    ready_for_save: bool
    upload_progress_text: str = ""
    current_step: str = ""
    dialog_open: bool = False
    save_button_found: bool = False
    save_button_label: str = ""
    error_messages: tuple[str, ...] = ()


@dataclass(frozen=True)
class CDPLifecycleCheckResult:
    status: str
    first_connect: bool
    first_disconnect: bool
    chrome_alive_after_disconnect: bool
    second_connect: bool
    studio_readable: bool
    second_disconnect: bool
    chrome_alive_final: bool
    browser_close_called: bool = False
    snapshots: tuple[CDPConnectionSnapshot, ...] = ()
    error: str = ""


class YouTubeStudioUploadError(Exception):
    pass


class PlaywrightCDPBrowserController:
    def __init__(
        self,
        config: YouTubeCDPConfig | None = None,
        sync_playwright_factory=None,
    ):
        self.config = config or YouTubeCDPConfig()
        self.sync_playwright_factory = sync_playwright_factory
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        self.owns_browser = False
        self.owns_context = False
        self.owns_page = False

    def start(self):
        try:
            factory = self.sync_playwright_factory or self._default_sync_playwright
            self.playwright = factory().start()
            self.browser = self.playwright.chromium.connect_over_cdp(
                self.config.endpoint_url,
                timeout=self.config.timeout_ms,
            )
            if not getattr(self.browser, "contexts", []):
                raise YouTubeStudioUploadError("cdp_context_unavailable")
            self.context = self.browser.contexts[0]
            if getattr(self.context, "pages", []):
                self.page = self.context.pages[0]
                self.owns_page = False
            else:
                self.page = self.context.new_page()
                self.owns_page = True
            return self
        except YouTubeStudioUploadError:
            raise
        except Exception as exc:
            raise YouTubeStudioUploadError("cdp_connection_failed") from exc

    def close(self):
        self.safe_disconnect()

    def safe_disconnect(self):
        if self.owns_page and self.page is not None:
            try:
                self.page.close()
            except Exception:
                pass
        if self.playwright is not None:
            self.playwright.stop()

    def snapshot(self, stage: str, error: Exception | None = None) -> CDPConnectionSnapshot:
        contexts = getattr(self.browser, "contexts", []) or []
        pages = getattr(self.context, "pages", []) if self.context is not None else []
        page_closed = False
        if self.page is not None:
            try:
                is_closed = getattr(self.page, "is_closed", None)
                page_closed = bool(is_closed()) if callable(is_closed) else bool(getattr(self.page, "closed", False))
            except Exception:
                page_closed = True
        return CDPConnectionSnapshot(
            stage=stage,
            browser_connected=self.browser is not None,
            page_closed=page_closed,
            context_count=len(contexts),
            page_count=len(pages),
            current_url=self.current_url,
            captured_at=datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
            error_type=type(error).__name__ if error else "",
            error_message=str(error) if error else "",
        )

    def open(self, url: str) -> None:
        if self.current_url.rstrip("/") == url.rstrip("/"):
            return
        self.page.goto(url, wait_until="domcontentloaded", timeout=self.config.timeout_ms)

    def click(self, selector: str) -> None:
        self.page.locator(selector).first.click(timeout=self.config.timeout_ms)

    def _first_existing(self, selector: str):
        locator = self.page.locator(selector)
        try:
            if locator.count() <= 0:
                return None
        except Exception:
            return None
        return locator.first

    def click_first(self, selectors: tuple[str, ...]) -> bool:
        for selector in selectors:
            try:
                locator = self._first_existing(selector)
                if locator is None:
                    continue
                locator.click(timeout=self.config.timeout_ms)
                return True
            except Exception:
                continue
        return False

    def click_first_enabled(self, selectors: tuple[str, ...]) -> bool:
        for selector in selectors:
            try:
                locator = self._first_existing(selector)
                if locator is None:
                    continue
                if not locator.is_enabled(timeout=self.config.timeout_ms):
                    continue
                locator.click(timeout=self.config.timeout_ms)
                return True
            except Exception:
                continue
        return False

    def upload(self, selector: str, file_path: str) -> None:
        self.page.locator(selector).first.set_input_files(file_path)

    def choose_file(self, selectors: tuple[str, ...], file_path: str) -> bool:
        for selector in selectors:
            try:
                with self.page.expect_file_chooser(
                    timeout=self.config.timeout_ms
                ) as chooser_info:
                    self.page.locator(selector).first.click(
                        timeout=self.config.timeout_ms
                    )
                chooser_info.value.set_files(file_path)
                return True
            except Exception:
                continue
        return False

    def upload_in_frames(self, selectors: tuple[str, ...], file_path: str) -> bool:
        for frame in getattr(self.page, "frames", []) or []:
            for selector in selectors:
                try:
                    frame.locator(selector).first.set_input_files(file_path)
                    return True
                except Exception:
                    continue
        return False

    def wait_for_visible(self, selector: str) -> bool:
        try:
            self.page.locator(selector).first.wait_for(
                state="visible",
                timeout=self.config.timeout_ms,
            )
            return True
        except Exception:
            return False

    def wait_for_hidden(self, selector: str) -> bool:
        try:
            self.page.locator(selector).first.wait_for(
                state="hidden",
                timeout=self.config.timeout_ms,
            )
            return True
        except Exception:
            return False

    def is_visible(self, selector: str) -> bool:
        try:
            return bool(self.page.locator(selector).first.is_visible())
        except Exception:
            return False

    def is_enabled(self, selectors: tuple[str, ...]) -> bool:
        for selector in selectors:
            locator = self._first_existing(selector)
            if locator is None:
                continue
            try:
                return bool(locator.is_enabled(timeout=self.config.timeout_ms))
            except Exception:
                continue
        return False

    def fill_text(self, selectors: tuple[str, ...], value: str) -> bool:
        for selector in selectors:
            locator = self._first_existing(selector)
            if locator is None:
                continue
            try:
                locator.fill(value, timeout=self.config.timeout_ms)
                return True
            except Exception:
                try:
                    locator.click(timeout=self.config.timeout_ms)
                    locator.press("Control+A", timeout=self.config.timeout_ms)
                    locator.type(value, timeout=self.config.timeout_ms)
                    return True
                except Exception:
                    continue
        return False

    def read_text(self, selectors: tuple[str, ...]) -> str:
        for selector in selectors:
            locator = self._first_existing(selector)
            if locator is None:
                continue
            try:
                return locator.input_value(timeout=self.config.timeout_ms)
            except Exception:
                try:
                    return locator.text_content(timeout=self.config.timeout_ms) or ""
                except Exception:
                    try:
                        return (
                            locator.evaluate(
                                "el => el.value ?? el.innerText ?? el.textContent ?? ''"
                            )
                            or ""
                        )
                    except Exception:
                        continue
        return ""

    def is_checked(self, selectors: tuple[str, ...]) -> bool:
        for selector in selectors:
            locator = self._first_existing(selector)
            if locator is None:
                continue
            try:
                return bool(locator.is_checked(timeout=self.config.timeout_ms))
            except Exception:
                try:
                    return locator.get_attribute("aria-checked") == "true"
                except Exception:
                    continue
        return False

    def add_tags(self, selectors: tuple[str, ...], tags: tuple[str, ...]) -> bool:
        for selector in selectors:
            locator = self._first_existing(selector)
            if locator is None:
                continue
            try:
                locator.click(timeout=self.config.timeout_ms)
                locator.press("Control+A", timeout=self.config.timeout_ms)
                for _ in range(20):
                    locator.press("Backspace", timeout=self.config.timeout_ms)
                for tag in tags:
                    locator.type(tag, timeout=self.config.timeout_ms)
                    locator.press("Enter", timeout=self.config.timeout_ms)
                return True
            except Exception:
                continue
        return False

    def read_tags(
        self,
        chip_selectors: tuple[str, ...],
        input_selectors: tuple[str, ...],
    ) -> tuple[str, ...]:
        for selector in chip_selectors:
            try:
                values = self.page.locator(selector).all_text_contents()
                clean = tuple(value.strip() for value in values if value.strip())
                if clean:
                    return clean
            except Exception:
                continue
        text = self.read_text(input_selectors)
        if not text:
            return ()
        return tuple(part.strip() for part in text.split(",") if part.strip())

    def read_href(self, selectors: tuple[str, ...]) -> str:
        for selector in selectors:
            locator = self._first_existing(selector)
            if locator is None:
                continue
            try:
                return locator.get_attribute("href") or ""
            except Exception:
                continue
        return ""

    def read_label(self, selectors: tuple[str, ...]) -> str:
        for selector in selectors:
            locator = self._first_existing(selector)
            if locator is None:
                continue
            try:
                label = locator.text_content(timeout=500) or ""
                if label.strip():
                    return label.strip()
            except Exception:
                try:
                    label = locator.get_attribute("aria-label") or ""
                    if label.strip():
                        return label.strip()
                except Exception:
                    continue
        return ""

    def collect_video_rows(self, selectors: tuple[str, ...]) -> list[dict]:
        rows = []
        for selector in selectors:
            try:
                locator = self.page.locator(selector)
                count = locator.count()
            except Exception:
                continue
            for index in range(min(count, 50)):
                item = locator.nth(index)
                try:
                    text = item.inner_text(timeout=500) or ""
                except Exception:
                    try:
                        text = item.text_content(timeout=500) or ""
                    except Exception:
                        text = ""
                href = ""
                try:
                    href = (
                        item.locator("a[href*='/video/']").first.get_attribute("href")
                        or ""
                    )
                except Exception:
                    pass
                rows.append({"text": text, "href": href})
            if rows:
                return rows
        return rows

    def search_text(self, selectors: tuple[str, ...], value: str) -> bool:
        for selector in selectors:
            locator = self._first_existing(selector)
            if locator is None:
                continue
            try:
                locator.fill(value, timeout=1000)
                return True
            except Exception:
                try:
                    locator.click(timeout=1000)
                    locator.press("Control+A", timeout=1000)
                    locator.type(value, timeout=1000)
                    return True
                except Exception:
                    continue
        return False

    def scroll_content(self) -> None:
        try:
            self.page.mouse.wheel(0, 1600)
        except Exception:
            try:
                self.page.evaluate("window.scrollBy(0, 1600)")
            except Exception:
                pass

    @property
    def current_url(self) -> str:
        return getattr(self.page, "url", "")

    def _default_sync_playwright(self):
        from playwright.sync_api import sync_playwright

        return sync_playwright()


class PlaywrightPersistentBrowserController:
    def __init__(
        self,
        config: YouTubeBrowserConfig,
        sync_playwright_factory=None,
    ):
        self.config = config
        self.sync_playwright_factory = sync_playwright_factory
        self.playwright = None
        self.context = None
        self.page = None

    def start(self):
        self.config.user_data_dir.mkdir(parents=True, exist_ok=True)
        try:
            factory = self.sync_playwright_factory or self._default_sync_playwright
            self.playwright = factory().start()
            kwargs = {
                "user_data_dir": str(self.config.user_data_dir),
                "headless": self.config.headless,
                "timeout": self.config.timeout_ms,
                "slow_mo": self.config.slow_mo_ms,
                "locale": self.config.locale,
            }
            if self.config.browser_channel:
                kwargs["channel"] = self.config.browser_channel
            if self.config.executable_path:
                kwargs["executable_path"] = self.config.executable_path
            self.context = self.playwright.chromium.launch_persistent_context(**kwargs)
            self.page = self.context.pages[0] if self.context.pages else self.context.new_page()
            return self
        except Exception as exc:
            raise YouTubeStudioUploadError("browser_launch_failed") from exc

    def close(self):
        if self.context is not None:
            self.context.close()
        if self.playwright is not None:
            self.playwright.stop()

    def open(self, url: str) -> None:
        if self.current_url.rstrip("/") == url.rstrip("/"):
            return
        self.page.goto(url, wait_until="domcontentloaded", timeout=self.config.timeout_ms)

    def click(self, selector: str) -> None:
        self.page.locator(selector).first.click(timeout=self.config.timeout_ms)

    def _first_existing(self, selector: str):
        locator = self.page.locator(selector)
        try:
            if locator.count() <= 0:
                return None
        except Exception:
            return None
        return locator.first

    def click_first(self, selectors: tuple[str, ...]) -> bool:
        for selector in selectors:
            try:
                locator = self._first_existing(selector)
                if locator is None:
                    continue
                locator.click(timeout=self.config.timeout_ms)
                return True
            except Exception:
                continue
        return False

    def click_first_enabled(self, selectors: tuple[str, ...]) -> bool:
        for selector in selectors:
            try:
                locator = self._first_existing(selector)
                if locator is None:
                    continue
                if not locator.is_enabled(timeout=self.config.timeout_ms):
                    continue
                locator.click(timeout=self.config.timeout_ms)
                return True
            except Exception:
                continue
        return False

    def upload(self, selector: str, file_path: str) -> None:
        self.page.locator(selector).first.set_input_files(file_path)

    def choose_file(self, selectors: tuple[str, ...], file_path: str) -> bool:
        for selector in selectors:
            try:
                with self.page.expect_file_chooser(
                    timeout=self.config.timeout_ms
                ) as chooser_info:
                    self.page.locator(selector).first.click(
                        timeout=self.config.timeout_ms
                    )
                chooser_info.value.set_files(file_path)
                return True
            except Exception:
                continue
        return False

    def upload_in_frames(self, selectors: tuple[str, ...], file_path: str) -> bool:
        for frame in getattr(self.page, "frames", []) or []:
            for selector in selectors:
                try:
                    frame.locator(selector).first.set_input_files(file_path)
                    return True
                except Exception:
                    continue
        return False

    def wait_for_visible(self, selector: str) -> bool:
        try:
            self.page.locator(selector).first.wait_for(
                state="visible",
                timeout=self.config.timeout_ms,
            )
            return True
        except Exception:
            return False

    def wait_for_hidden(self, selector: str) -> bool:
        try:
            self.page.locator(selector).first.wait_for(
                state="hidden",
                timeout=self.config.timeout_ms,
            )
            return True
        except Exception:
            return False

    def is_visible(self, selector: str) -> bool:
        try:
            return bool(self.page.locator(selector).first.is_visible())
        except Exception:
            return False

    def is_enabled(self, selectors: tuple[str, ...]) -> bool:
        for selector in selectors:
            locator = self._first_existing(selector)
            if locator is None:
                continue
            try:
                return bool(locator.is_enabled(timeout=self.config.timeout_ms))
            except Exception:
                continue
        return False

    def fill_text(self, selectors: tuple[str, ...], value: str) -> bool:
        for selector in selectors:
            locator = self._first_existing(selector)
            if locator is None:
                continue
            try:
                locator.fill(value, timeout=self.config.timeout_ms)
                return True
            except Exception:
                try:
                    locator.click(timeout=self.config.timeout_ms)
                    locator.press("Control+A", timeout=self.config.timeout_ms)
                    locator.type(value, timeout=self.config.timeout_ms)
                    return True
                except Exception:
                    continue
        return False

    def read_text(self, selectors: tuple[str, ...]) -> str:
        for selector in selectors:
            locator = self._first_existing(selector)
            if locator is None:
                continue
            try:
                return locator.input_value(timeout=self.config.timeout_ms)
            except Exception:
                try:
                    return locator.text_content(timeout=self.config.timeout_ms) or ""
                except Exception:
                    try:
                        return (
                            locator.evaluate(
                                "el => el.value ?? el.innerText ?? el.textContent ?? ''"
                            )
                            or ""
                        )
                    except Exception:
                        continue
        return ""

    def is_checked(self, selectors: tuple[str, ...]) -> bool:
        for selector in selectors:
            locator = self._first_existing(selector)
            if locator is None:
                continue
            try:
                return bool(locator.is_checked(timeout=self.config.timeout_ms))
            except Exception:
                try:
                    return locator.get_attribute("aria-checked") == "true"
                except Exception:
                    continue
        return False

    def add_tags(self, selectors: tuple[str, ...], tags: tuple[str, ...]) -> bool:
        for selector in selectors:
            locator = self._first_existing(selector)
            if locator is None:
                continue
            try:
                locator.click(timeout=self.config.timeout_ms)
                locator.press("Control+A", timeout=self.config.timeout_ms)
                for _ in range(20):
                    locator.press("Backspace", timeout=self.config.timeout_ms)
                for tag in tags:
                    locator.type(tag, timeout=self.config.timeout_ms)
                    locator.press("Enter", timeout=self.config.timeout_ms)
                return True
            except Exception:
                continue
        return False

    def read_tags(
        self,
        chip_selectors: tuple[str, ...],
        input_selectors: tuple[str, ...],
    ) -> tuple[str, ...]:
        for selector in chip_selectors:
            try:
                values = self.page.locator(selector).all_text_contents()
                clean = tuple(value.strip() for value in values if value.strip())
                if clean:
                    return clean
            except Exception:
                continue
        text = self.read_text(input_selectors)
        if not text:
            return ()
        return tuple(part.strip() for part in text.split(",") if part.strip())

    def read_href(self, selectors: tuple[str, ...]) -> str:
        for selector in selectors:
            locator = self._first_existing(selector)
            if locator is None:
                continue
            try:
                return locator.get_attribute("href") or ""
            except Exception:
                continue
        return ""

    def read_label(self, selectors: tuple[str, ...]) -> str:
        for selector in selectors:
            locator = self._first_existing(selector)
            if locator is None:
                continue
            try:
                label = locator.text_content(timeout=500) or ""
                if label.strip():
                    return label.strip()
            except Exception:
                try:
                    label = locator.get_attribute("aria-label") or ""
                    if label.strip():
                        return label.strip()
                except Exception:
                    continue
        return ""

    def collect_video_rows(self, selectors: tuple[str, ...]) -> list[dict]:
        rows = []
        for selector in selectors:
            try:
                locator = self.page.locator(selector)
                count = locator.count()
            except Exception:
                continue
            for index in range(min(count, 50)):
                item = locator.nth(index)
                try:
                    text = item.inner_text(timeout=500) or ""
                except Exception:
                    try:
                        text = item.text_content(timeout=500) or ""
                    except Exception:
                        text = ""
                href = ""
                try:
                    href = (
                        item.locator("a[href*='/video/']").first.get_attribute("href")
                        or ""
                    )
                except Exception:
                    pass
                rows.append({"text": text, "href": href})
            if rows:
                return rows
        return rows

    def search_text(self, selectors: tuple[str, ...], value: str) -> bool:
        for selector in selectors:
            locator = self._first_existing(selector)
            if locator is None:
                continue
            try:
                locator.fill(value, timeout=1000)
                return True
            except Exception:
                try:
                    locator.click(timeout=1000)
                    locator.press("Control+A", timeout=1000)
                    locator.type(value, timeout=1000)
                    return True
                except Exception:
                    continue
        return False

    def scroll_content(self) -> None:
        try:
            self.page.mouse.wheel(0, 1600)
        except Exception:
            try:
                self.page.evaluate("window.scrollBy(0, 1600)")
            except Exception:
                pass

    @property
    def current_url(self) -> str:
        return getattr(self.page, "url", "")

    def _default_sync_playwright(self):
        from playwright.sync_api import sync_playwright

        return sync_playwright()


class CDPLifecycleChecker:
    def __init__(
        self,
        config: YouTubeCDPConfig | None = None,
        controller_factory=None,
        alive_checker=None,
    ):
        self.config = config or YouTubeCDPConfig()
        self.controller_factory = controller_factory or self._controller_factory
        self.alive_checker = alive_checker or self._chrome_alive

    def check(self) -> CDPLifecycleCheckResult:
        snapshots = []
        first_disconnect = False
        second_disconnect = False
        browser_close_called = False
        try:
            first = self.controller_factory()
            first.start()
            snapshots.append(first.snapshot("first_connect"))
            first.safe_disconnect()
            first_disconnect = True
            browser_close_called = browser_close_called or bool(
                getattr(getattr(first, "browser", None), "closed", False)
            )
            chrome_alive_after_disconnect = self.alive_checker()

            second = self.controller_factory()
            second.start()
            snapshots.append(second.snapshot("second_connect"))
            studio_readable = "studio.youtube.com" in getattr(second, "current_url", "")
            second.safe_disconnect()
            second_disconnect = True
            browser_close_called = browser_close_called or bool(
                getattr(getattr(second, "browser", None), "closed", False)
            )
            chrome_alive_final = self.alive_checker()

            ok = (
                chrome_alive_after_disconnect
                and studio_readable
                and chrome_alive_final
                and not browser_close_called
            )
            return CDPLifecycleCheckResult(
                status="ok" if ok else "failed",
                first_connect=True,
                first_disconnect=first_disconnect,
                chrome_alive_after_disconnect=chrome_alive_after_disconnect,
                second_connect=True,
                studio_readable=studio_readable,
                second_disconnect=second_disconnect,
                chrome_alive_final=chrome_alive_final,
                browser_close_called=browser_close_called,
                snapshots=tuple(snapshots),
            )
        except Exception as exc:
            return CDPLifecycleCheckResult(
                status="failed",
                first_connect=bool(snapshots),
                first_disconnect=first_disconnect,
                chrome_alive_after_disconnect=False,
                second_connect=len(snapshots) >= 2,
                studio_readable=False,
                second_disconnect=second_disconnect,
                chrome_alive_final=False,
                browser_close_called=browser_close_called,
                snapshots=tuple(snapshots),
                error=str(exc),
            )

    def _controller_factory(self):
        return PlaywrightCDPBrowserController(self.config)

    def _chrome_alive(self) -> bool:
        try:
            with urllib.request.urlopen(
                urljoin(self.config.endpoint_url.rstrip("/") + "/", "json/version"),
                timeout=max(self.config.timeout_ms / 1000, 1),
            ) as response:
                return 200 <= response.status < 500
        except Exception:
            return False


class YouTubeStudioLoginChecker:
    def __init__(self, selectors: YouTubeStudioSelectors | None = None):
        self.selectors = selectors or YouTubeStudioSelectors()

    def check(self, browser) -> YouTubeStudioLoginResult:
        current_url = getattr(browser, "current_url", "")
        lowered_url = current_url.lower()
        if "accounts.google.com" in lowered_url or "signin" in lowered_url:
            return YouTubeStudioLoginResult(
                status=STATUS_LOGIN_REQUIRED,
                logged_in=False,
                current_url=current_url,
                reason="Google sign-in is required.",
            )
        if self._any_visible(browser, self.selectors.channel_unavailable_indicators):
            return YouTubeStudioLoginResult(
                status=STATUS_CHANNEL_UNAVAILABLE,
                logged_in=False,
                current_url=current_url,
                reason="YouTube channel is unavailable.",
            )
        if "studio.youtube.com" not in lowered_url:
            return YouTubeStudioLoginResult(
                status=STATUS_STUDIO_UNAVAILABLE,
                logged_in=False,
                current_url=current_url,
                reason="YouTube Studio is unavailable.",
            )
        if self._any_visible(browser, self.selectors.logged_in_indicators):
            return YouTubeStudioLoginResult(
                status=STATUS_LOGGED_IN,
                logged_in=True,
                current_url=current_url,
                reason="YouTube Studio UI is visible.",
            )
        return YouTubeStudioLoginResult(
            status=STATUS_UNKNOWN,
            logged_in=False,
            current_url=current_url,
            reason="Unable to determine login status.",
        )

    def _any_visible(self, browser, selectors: tuple[str, ...]) -> bool:
        return any(browser.is_visible(selector) for selector in selectors)


class YouTubeStudioUploadPreparer:
    def __init__(
        self,
        config: YouTubeBrowserConfig | None = None,
        browser=None,
        selectors: YouTubeStudioSelectors | None = None,
        login_checker: YouTubeStudioLoginChecker | None = None,
        validator: VideoOutputValidator | None = None,
    ):
        self.config = config or YouTubeBrowserConfig()
        self.browser = browser
        self.selectors = selectors or YouTubeStudioSelectors()
        self.login_checker = login_checker or YouTubeStudioLoginChecker(self.selectors)
        self.validator = validator or VideoOutputValidator()

    def login_only(self, keep_open: bool = False, input_func=input) -> YouTubeStudioLoginResult:
        browser, should_close = self._browser()
        try:
            browser.open(self.config.studio_url)
            result = self.login_checker.check(browser)
            if keep_open:
                input_func("Press Enter to close the browser...")
                result = self.login_checker.check(browser)
            return result
        finally:
            if should_close:
                browser.close()

    def prepare_upload(
        self,
        video_path: str,
        keep_open: bool = False,
        input_func=input,
    ) -> UploadPreparationResult:
        validation = self.validator.validate(video_path)
        absolute_path = str(Path(validation["video_path"]).resolve())
        browser, should_close = self._browser()
        try:
            browser.open(self.config.studio_url)
            login_result = self.login_checker.check(browser)
            if not login_result.logged_in:
                return UploadPreparationResult(
                    status=login_result.status,
                    video_path=absolute_path,
                    filename=Path(absolute_path).name,
                    upload_started=False,
                    details_visible=False,
                    logged_in=False,
                    current_url=login_result.current_url,
                    error=login_result.reason,
                )

            self._click_first_visible(browser, self.selectors.create_button, "create_button_not_found")
            self._click_first_visible(
                browser,
                self.selectors.upload_videos_menu_item,
                "upload_menu_not_found",
            )
            self._upload_first(browser, absolute_path)
            details_visible = self._wait_any_visible(browser, self.selectors.details_dialog)
            if not details_visible:
                raise YouTubeStudioUploadError("details_not_visible")
            if keep_open:
                input_func("Upload prepared. Press Enter to close the browser...")
            return UploadPreparationResult(
                status="prepared",
                video_path=absolute_path,
                filename=Path(absolute_path).name,
                upload_started=True,
                details_visible=True,
                logged_in=True,
                current_url=getattr(browser, "current_url", ""),
                published=False,
                saved=False,
                error="",
            )
        finally:
            if should_close:
                browser.close()

    def _browser(self):
        if self.browser is not None:
            return self.browser, False
        return PlaywrightPersistentBrowserController(self.config).start(), True

    def _click_first_visible(self, browser, selectors: tuple[str, ...], error: str) -> None:
        for selector in selectors:
            if browser.is_visible(selector):
                browser.click(selector)
                return
        raise YouTubeStudioUploadError(error)

    def _upload_first(self, browser, file_path: str) -> None:
        if hasattr(browser, "choose_file") and browser.choose_file(
            self.selectors.file_select_button,
            file_path,
        ):
            return
        for selector in self.selectors.file_input:
            try:
                browser.upload(selector, file_path)
                return
            except Exception:
                continue
        for selector in self.selectors.dialog_file_input:
            try:
                browser.upload(selector, file_path)
                return
            except Exception:
                continue
        if hasattr(browser, "upload_in_frames") and browser.upload_in_frames(
            self.selectors.file_input,
            file_path,
        ):
            return
        raise YouTubeStudioUploadError("file_input_not_found")

    def _wait_any_visible(self, browser, selectors: tuple[str, ...]) -> bool:
        return any(browser.wait_for_visible(selector) for selector in selectors)


class YouTubeMetadataPreparer:
    def __init__(
        self,
        upload_preparer: YouTubeStudioUploadPreparer,
        selectors: YouTubeStudioSelectors | None = None,
        validator: YouTubeMetadataValidator | None = None,
    ):
        self.upload_preparer = upload_preparer
        self.selectors = selectors or upload_preparer.selectors
        self.validator = validator or YouTubeMetadataValidator()

    def prepare_metadata(
        self,
        video_path: str,
        metadata: YouTubeVideoMetadata,
        keep_open: bool = False,
        input_func=input,
    ) -> YouTubeMetadataPreparationResult:
        try:
            metadata = self.validator.validate(metadata)
        except YouTubeMetadataValidationError as exc:
            return self._failed(metadata, str(video_path), "invalid_metadata", str(exc))

        upload_result = self._prepare_or_reuse_upload(video_path)
        if upload_result.status != "prepared":
            return self._failed(
                metadata,
                upload_result.video_path,
                upload_result.status,
                upload_result.error,
            )

        browser = self.upload_preparer.browser
        try:
            title_applied = self._apply_text(
                browser,
                self.selectors.title_input,
                metadata.title,
                "title_input_not_found",
                "title_apply_failed",
            )
            description_applied = self._apply_text(
                browser,
                self.selectors.description_input,
                metadata.description,
                "description_input_not_found",
                "description_apply_failed",
            )
            audience_applied = self._apply_audience(browser, metadata.made_for_kids)
            tags_applied = self._apply_tags(browser, metadata.tags)
            if keep_open:
                input_func("Metadata prepared. Press Enter to close the browser...")
            return YouTubeMetadataPreparationResult(
                status="metadata_prepared",
                video_path=upload_result.video_path,
                title=metadata.title,
                description=metadata.description,
                made_for_kids=metadata.made_for_kids,
                tags=metadata.tags,
                title_applied=title_applied,
                description_applied=description_applied,
                audience_applied=audience_applied,
                tags_applied=tags_applied,
                saved=False,
                published=False,
                error="",
            )
        except YouTubeStudioUploadError as exc:
            return self._failed(metadata, upload_result.video_path, str(exc), str(exc))

    def _apply_text(
        self,
        browser,
        selectors: tuple[str, ...],
        value: str,
        not_found_error: str,
        apply_error: str,
    ) -> bool:
        if not browser.fill_text(selectors, value):
            raise YouTubeStudioUploadError(not_found_error)
        actual = browser.read_text(selectors)
        if not self._text_matches(actual, value):
            raise YouTubeStudioUploadError(apply_error)
        return True

    def _text_matches(self, actual: str, expected: str) -> bool:
        return actual == expected or actual.rstrip("\n") == expected

    def _apply_audience(self, browser, made_for_kids: bool) -> bool:
        target = (
            self.selectors.made_for_kids_yes
            if made_for_kids
            else self.selectors.made_for_kids_no
        )
        other = (
            self.selectors.made_for_kids_no
            if made_for_kids
            else self.selectors.made_for_kids_yes
        )
        if not browser.click_first(target):
            raise YouTubeStudioUploadError("audience_control_not_found")
        if not browser.is_checked(target) or browser.is_checked(other):
            raise YouTubeStudioUploadError("audience_apply_failed")
        return True

    def _apply_tags(self, browser, tags: tuple[str, ...]) -> bool:
        if tags and not self._ensure_tags_visible(browser):
            raise YouTubeStudioUploadError("show_more_not_found")
        if not browser.add_tags(self.selectors.tags_input, tags):
            raise YouTubeStudioUploadError("tags_input_not_found")
        actual = browser.read_tags(self.selectors.tag_chips, self.selectors.tags_input)
        if tuple(actual) != tuple(tags):
            raise YouTubeStudioUploadError("tags_apply_failed")
        return True

    def _prepare_or_reuse_upload(self, video_path: str) -> UploadPreparationResult:
        browser = self.upload_preparer.browser
        if browser is not None and self._details_visible(browser):
            validation = self.upload_preparer.validator.validate(video_path)
            absolute_path = str(Path(validation["video_path"]).resolve())
            return UploadPreparationResult(
                status="prepared",
                video_path=absolute_path,
                filename=Path(absolute_path).name,
                upload_started=True,
                details_visible=True,
                logged_in=True,
                current_url=getattr(browser, "current_url", ""),
                saved=False,
                published=False,
                error="",
            )
        return self.upload_preparer.prepare_upload(video_path, keep_open=False)

    def _details_visible(self, browser) -> bool:
        return any(browser.is_visible(selector) for selector in self.selectors.details_dialog)

    def _ensure_tags_visible(self, browser) -> bool:
        if any(browser.is_visible(selector) for selector in self.selectors.tags_input):
            return True
        if browser.click_first(self.selectors.show_more_button):
            return True
        return any(browser.is_visible(selector) for selector in self.selectors.tags_input)

    def _failed(
        self,
        metadata: YouTubeVideoMetadata,
        video_path: str,
        status: str,
        error: str,
    ) -> YouTubeMetadataPreparationResult:
        return YouTubeMetadataPreparationResult(
            status=status,
            video_path=str(video_path),
            title=getattr(metadata, "title", ""),
            description=getattr(metadata, "description", ""),
            made_for_kids=bool(getattr(metadata, "made_for_kids", False)),
            tags=tuple(getattr(metadata, "tags", ()) or ()),
            title_applied=False,
            description_applied=False,
            audience_applied=False,
            tags_applied=False,
            saved=False,
            published=False,
            error=error,
        )


class YouTubeUploadReadinessChecker:
    ALLOWED_SAVE_LABELS = {"保存", "SAVE", "完了", "DONE"}
    REJECTED_SAVE_LABELS = {
        "公開",
        "PUBLISH",
        "限定公開",
        "UNLISTED",
        "スケジュール",
        "SCHEDULE",
        "閉じる",
        "CLOSE",
        "次へ",
        "NEXT",
        "戻る",
        "BACK",
    }

    def __init__(self, selectors: YouTubeStudioSelectors | None = None):
        self.selectors = selectors or YouTubeStudioSelectors()

    def check(self, browser) -> YouTubeUploadReadiness:
        progress_text = self._read_first_text(browser, self.selectors.upload_progress_text)
        error_messages = self._error_messages(browser)
        blocking_error = bool(error_messages)
        private_checked = browser.is_checked(self.selectors.private_radio)
        save_enabled = browser.is_enabled(self.selectors.private_save_button)
        save_button_found = self._any_visible(browser, self.selectors.private_save_button) or save_enabled
        save_label = self._save_button_label(browser)
        upload_complete = self._upload_complete(browser, progress_text)
        processing = self._contains_any(progress_text, ("処理中", "Processing", "processing"))
        checks_complete = not blocking_error
        ready = (
            upload_complete
            and not blocking_error
            and private_checked
            and save_enabled
            and self.is_allowed_save_label(save_label)
        )
        return YouTubeUploadReadiness(
            upload_complete=upload_complete,
            processing=processing,
            checks_complete=checks_complete,
            blocking_error=blocking_error,
            save_enabled=save_enabled,
            private_checked=private_checked,
            ready_for_save=ready,
            upload_progress_text=progress_text,
            current_step=self._read_first_text(browser, self.selectors.current_step_text),
            dialog_open=self._any_visible(browser, self.selectors.details_dialog),
            save_button_found=save_button_found,
            save_button_label=save_label,
            error_messages=tuple(error_messages),
        )

    def is_allowed_save_label(self, label: str) -> bool:
        clean = label.strip()
        if clean in self.REJECTED_SAVE_LABELS:
            return False
        return clean in self.ALLOWED_SAVE_LABELS

    def _upload_complete(self, browser, progress_text: str) -> bool:
        if self._any_visible(browser, self.selectors.upload_complete_text):
            return True
        if "%" in progress_text and "100%" not in progress_text:
            return False
        if self._contains_any(progress_text, ("100%", "アップロード済み", "Complete", "完了")):
            return True
        if not progress_text and not hasattr(browser, "read_text"):
            return True
        return False

    def _save_button_label(self, browser) -> str:
        if hasattr(browser, "read_label"):
            return browser.read_label(self.selectors.private_save_button)
        if hasattr(browser, "save_button_label"):
            return str(browser.save_button_label)
        return "保存" if browser.is_enabled(self.selectors.private_save_button) else ""

    def _error_messages(self, browser) -> list[str]:
        messages = []
        for selector in self.selectors.checks_blocking_error:
            if browser.is_visible(selector):
                text = ""
                if hasattr(browser, "read_text"):
                    text = browser.read_text((selector,))
                messages.append(text or selector)
        return messages

    def _read_first_text(self, browser, selectors: tuple[str, ...]) -> str:
        if hasattr(browser, "read_text"):
            return browser.read_text(selectors)
        return ""

    def _any_visible(self, browser, selectors: tuple[str, ...]) -> bool:
        return any(browser.is_visible(selector) for selector in selectors)

    def _contains_any(self, value: str, needles: tuple[str, ...]) -> bool:
        return any(needle in value for needle in needles)


class YouTubePrivateSaveConfirmer:
    def __init__(
        self,
        metadata_preparer: YouTubeMetadataPreparer,
        selectors: YouTubeStudioSelectors | None = None,
        policy: YouTubePrivateSavePolicy | None = None,
    ):
        self.metadata_preparer = metadata_preparer
        self.selectors = selectors or metadata_preparer.selectors
        self.policy = policy or YouTubePrivateSavePolicy()
        self._save_clicked = False
        self.readiness_checker = YouTubeUploadReadinessChecker(self.selectors)

    def save_private(
        self,
        video_path: str,
        metadata: YouTubeVideoMetadata,
        policy: YouTubePrivateSavePolicy | None = None,
        keep_open: bool = False,
        input_func=input,
    ) -> YouTubePrivateSaveResult:
        active_policy = policy or self.policy
        metadata_result = self.metadata_preparer.prepare_metadata(
            video_path,
            metadata,
            keep_open=False,
            input_func=input_func,
        )
        if metadata_result.status != "metadata_prepared":
            return self._failed(
                metadata_result,
                metadata_result.status,
                metadata_result.error,
            )
        if not active_policy.confirm_private_save:
            return self._failed(
                metadata_result,
                "confirmation_required",
                "Private save requires --confirm-private-save.",
            )

        browser = self.metadata_preparer.upload_preparer.browser
        if self._has_unexpected_publish_state(browser):
            return self._failed(
                metadata_result,
                "unexpected_publish_state",
                "Publish/Schedule/Public/Unlisted controls are visible before Private selection.",
            )

        next_status = self._advance_to_visibility(browser, active_policy.max_next_clicks)
        if next_status != "":
            return self._failed(metadata_result, next_status, next_status)

        if not self._select_private(browser):
            return self._failed(
                metadata_result,
                "private_option_not_found",
                "Private option was not found.",
            )
        if not self._private_checked(browser):
            return self._failed(
                metadata_result,
                "private_selection_failed",
                "Private option was not checked.",
                private_selected=False,
            )

        readiness = self.readiness_checker.check(browser)
        if not readiness.ready_for_save:
            status = "blocking_error" if readiness.blocking_error else "upload_not_ready"
            if readiness.save_enabled is False and readiness.upload_complete:
                status = "save_button_disabled"
            return self._failed(
                metadata_result,
                status,
                "; ".join(readiness.error_messages) or status,
                private_selected=True,
                save_clicked=False,
                evidence=YouTubePrivateSaveEvidence(
                    private_checked_before_click=readiness.private_checked,
                    upload_complete_before_click=readiness.upload_complete,
                    upload_progress_text=readiness.upload_progress_text,
                    blocking_error_detected=readiness.blocking_error,
                    blocking_error_text="; ".join(readiness.error_messages),
                    save_button_found=readiness.save_button_found,
                    save_button_enabled=readiness.save_enabled,
                    save_button_exact_label=readiness.save_button_label,
                    save_button_label=readiness.save_button_label,
                ),
            )

        evidence = YouTubePrivateSaveEvidence(
            private_checked_before_click=True,
            upload_complete_before_click=readiness.upload_complete,
            upload_progress_text=readiness.upload_progress_text,
            blocking_error_detected=readiness.blocking_error,
            blocking_error_text="; ".join(readiness.error_messages),
            save_button_found=readiness.save_button_found,
            save_button_enabled=readiness.save_enabled,
            save_button_exact_label=readiness.save_button_label,
            save_button_label=readiness.save_button_label,
        )
        save_status = self._click_save_once(browser)
        if save_status != "":
            return self._failed(
                metadata_result,
                save_status,
                save_status,
                private_selected=True,
                save_clicked=False,
                evidence=evidence,
            )
        evidence.click_dispatched = True

        completion_evidence = self._wait_save_complete(browser)
        evidence.dialog_closed = completion_evidence.dialog_closed
        evidence.post_click_dialog_closed = completion_evidence.dialog_closed
        evidence.success_message_detected = completion_evidence.success_message_detected
        evidence.post_click_success_toast = completion_evidence.success_message_detected
        video_url = self._video_url(browser)
        video_id = self._video_id(video_url)
        evidence.video_link_detected = bool(video_url)
        evidence.post_click_video_link = video_url
        evidence.post_click_video_id = video_id
        evidence.content_page_detected = "/video/" in getattr(browser, "current_url", "")
        evidence.post_click_content_row_detected = evidence.content_page_detected
        evidence.post_click_private_visibility_detected = self._private_checked(browser)
        evidence.completion_evidence_count = sum(
            1
            for value in (
                evidence.post_click_video_id,
                evidence.post_click_private_visibility_detected,
                evidence.post_click_content_row_detected,
            )
            if value
        )
        evidence.completion_confirmed = (
            completion_evidence.completion_confirmed
            and bool(evidence.post_click_video_id)
            and evidence.post_click_private_visibility_detected
        )
        if not evidence.completion_confirmed:
            return self._failed(
                metadata_result,
                "save_unverified",
                "Save completion was not detected.",
                private_selected=True,
                save_clicked=True,
                evidence=evidence,
            )

        if keep_open:
            try:
                input_func("Private save completed. Press Enter to close the browser...")
            except EOFError:
                pass
        return YouTubePrivateSaveResult(
            status="private_saved",
            video_path=metadata_result.video_path,
            title=metadata_result.title,
            privacy_status="private",
            private_selected=True,
            save_clicked=True,
            saved=True,
            published=False,
            video_url=self._video_url(browser),
            studio_url=getattr(browser, "current_url", ""),
            error="",
            evidence=evidence,
        )

    def _advance_to_visibility(self, browser, max_next_clicks: int) -> str:
        for _ in range(max_next_clicks + 1):
            if self._any_visible(browser, self.selectors.visibility_step) or self._any_visible(
                browser, self.selectors.private_radio
            ):
                return ""
            if self._checks_blocking_error(browser):
                return "checks_failed"
            if not browser.click_first_enabled(self.selectors.next_button):
                return "next_button_not_found"
        return "next_step_timeout"

    def _checks_blocking_error(self, browser) -> bool:
        return self._any_visible(browser, self.selectors.checks_blocking_error)

    def _select_private(self, browser) -> bool:
        return browser.click_first(self.selectors.private_radio)

    def _private_checked(self, browser) -> bool:
        return browser.is_checked(self.selectors.private_radio)

    def _click_save_once(self, browser) -> str:
        if self._save_clicked:
            return "duplicate_save_blocked"
        if self._has_publish_button(browser):
            return "unexpected_publish_state"
        label = self.readiness_checker._save_button_label(browser)
        if not self.readiness_checker.is_allowed_save_label(label):
            return "save_button_label_rejected"
        if not browser.is_enabled(self.selectors.private_save_button):
            return "save_button_disabled"
        if not browser.click_first_enabled(self.selectors.private_save_button):
            return "save_button_not_found"
        self._save_clicked = True
        return ""

    def _wait_save_complete(self, browser) -> YouTubePrivateSaveEvidence:
        dialog_closed = any(
            browser.wait_for_hidden(selector) for selector in self.selectors.details_dialog
        )
        success_message_detected = any(
            browser.wait_for_visible(selector) for selector in self.selectors.save_success
        )
        return YouTubePrivateSaveEvidence(
            dialog_closed=dialog_closed,
            success_message_detected=success_message_detected,
            completion_confirmed=dialog_closed or success_message_detected,
        )

    def _video_url(self, browser) -> str:
        if hasattr(browser, "read_href"):
            return browser.read_href(self.selectors.video_link)
        return ""

    def _video_id(self, href: str) -> str:
        if not href:
            return ""
        for pattern in (r"/video/([^/?#]+)/?", r"[?&]v=([^&#]+)", r"youtu\.be/([^/?#]+)"):
            match = re.search(pattern, href)
            if match:
                return match.group(1)
        return ""

    def _has_unexpected_publish_state(self, browser) -> bool:
        return self._has_publish_button(browser)

    def _has_publish_button(self, browser) -> bool:
        return self._any_visible(browser, self.selectors.publish_button)

    def _any_visible(self, browser, selectors: tuple[str, ...]) -> bool:
        return any(browser.is_visible(selector) for selector in selectors)

    def _failed(
        self,
        metadata_result: YouTubeMetadataPreparationResult,
        status: str,
        error: str,
        private_selected: bool = False,
        save_clicked: bool = False,
        evidence=None,
    ) -> YouTubePrivateSaveResult:
        return YouTubePrivateSaveResult(
            status=status,
            video_path=metadata_result.video_path,
            title=metadata_result.title,
            privacy_status="private",
            private_selected=private_selected,
            save_clicked=save_clicked,
            saved=False,
            published=False,
            video_url="",
            studio_url="",
            error=error,
            evidence=evidence,
        )


class YouTubePrivateSaveVerifier:
    def __init__(
        self,
        browser=None,
        config: YouTubeCDPConfig | None = None,
        selectors: YouTubeStudioSelectors | None = None,
        verifier_config: YouTubePrivateSaveVerifierConfig | None = None,
        clock=None,
        sleeper=None,
    ):
        self.browser = browser
        self.config = config or YouTubeCDPConfig()
        self.selectors = selectors or YouTubeStudioSelectors()
        self.verifier_config = verifier_config or YouTubePrivateSaveVerifierConfig()
        self.clock = clock or time.monotonic
        self.sleeper = sleeper or time.sleep

    def verify(self, title: str) -> YouTubePrivateSaveVerificationResult:
        expected_title = str(title).strip()
        browser, should_close = self._browser()
        started_at = self.clock()
        last_result = None
        try:
            while True:
                elapsed = self.clock() - started_at
                last_result = self._verify_once(browser, expected_title, elapsed)
                if last_result.status in {
                    "verified_private",
                    "duplicate_candidates",
                    "visibility_mismatch",
                }:
                    return last_result
                if elapsed >= self.verifier_config.timeout_seconds:
                    if last_result.status == "processing":
                        return self._copy_result(
                            last_result,
                            status="verification_timeout",
                            error="Video is still processing after timeout.",
                            elapsed_seconds=elapsed,
                        )
                    return self._copy_result(
                        last_result,
                        status="verification_timeout"
                        if last_result.status != "not_found"
                        else "not_found",
                        elapsed_seconds=elapsed,
                    )
                self.sleeper(self.verifier_config.poll_interval_seconds)
        finally:
            if should_close:
                browser.close()

    def _browser(self):
        if self.browser is not None:
            return self.browser, False
        return PlaywrightCDPBrowserController(self.config).start(), True

    def _verify_once(
        self,
        browser,
        expected_title: str,
        elapsed_seconds: float,
    ) -> YouTubePrivateSaveVerificationResult:
        checked_locations = []
        rows = []
        for location in self._content_locations(browser):
            checked_locations.append(location["content_type"])
            browser.open(location["url"])
            if hasattr(browser, "search_text"):
                browser.search_text(self.selectors.content_search_input, expected_title)
            rows.extend(self._collect_rows(browser, location["content_type"]))
        candidates = self._candidate_rows(expected_title, rows)
        candidate_titles = self._candidate_titles(rows)
        strong = [candidate for candidate in candidates if candidate["match_type"] in {"exact", "normalized_exact"}]
        if not strong:
            processing = any(
                candidate["processing"]
                for candidate in candidates
                if candidate["match_type"] in {"starts_with", "contains"}
            )
            return self._result(
                "processing" if processing else "not_found",
                expected_title,
                found=False,
                processing=processing,
                checked_locations=tuple(checked_locations),
                candidate_titles=candidate_titles,
                elapsed_seconds=elapsed_seconds,
            )
        if len(strong) > 1:
            return self._result(
                "duplicate_candidates",
                expected_title,
                found=True,
                duplicate_count=len(strong),
                checked_locations=tuple(checked_locations),
                candidate_titles=tuple(candidate["title"] for candidate in strong[:5]),
                elapsed_seconds=elapsed_seconds,
                error="Multiple exact matching videos were found.",
            )
        row = strong[0]
        if row["processing"]:
            return self._row_result(
                row,
                expected_title,
                "processing",
                checked_locations,
                elapsed_seconds,
                error="Matching video is still processing.",
            )
        if row["privacy_status"] != "private":
            return self._row_result(
                row,
                expected_title,
                "visibility_mismatch",
                checked_locations,
                elapsed_seconds,
                error="Matching video is not private.",
            )
        return self._row_result(
            row,
            expected_title,
            "verified_private",
            checked_locations,
            elapsed_seconds,
            private_confirmed=True,
        )

    def _content_locations(self, browser) -> tuple[dict, ...]:
        current_url = getattr(browser, "current_url", "") or self.config.studio_url
        parsed = urlparse(current_url)
        parts = [part for part in parsed.path.split("/") if part]
        base = self.config.studio_url.rstrip("/") + "/"
        if len(parts) >= 2 and parts[0] == "channel":
            base = f"{parsed.scheme}://{parsed.netloc}/channel/{parts[1]}/"
        return (
            {"content_type": "video", "url": urljoin(base, "videos/upload")},
            {"content_type": "short", "url": urljoin(base, "videos/shorts")},
            {"content_type": "live", "url": urljoin(base, "videos/live")},
            {"content_type": "draft", "url": urljoin(base, "videos/drafts")},
        )

    def _collect_rows(self, browser, content_type: str) -> list[dict]:
        collected = []
        seen = set()
        stagnant_rounds = 0
        while len(collected) < self.verifier_config.max_items and stagnant_rounds < 2:
            before = len(collected)
            for row in browser.collect_video_rows(self.selectors.content_video_rows):
                text = str(row.get("text", ""))
                href = str(row.get("href", ""))
                key = (text, href)
                if key in seen:
                    continue
                seen.add(key)
                collected.append(
                    {
                        "text": text,
                        "href": href,
                        "content_type": content_type,
                    }
                )
                if len(collected) >= self.verifier_config.max_items:
                    break
            if len(collected) == before:
                stagnant_rounds += 1
            else:
                stagnant_rounds = 0
            if len(collected) >= self.verifier_config.max_items:
                break
            if hasattr(browser, "scroll_content"):
                browser.scroll_content()
            else:
                break
        return collected

    def _candidate_rows(self, expected_title: str, rows: list[dict]) -> list[dict]:
        candidates = []
        seen = set()
        for row in rows:
            title, match_type = self._best_title_match(expected_title, row.get("text", ""))
            if not match_type:
                continue
            privacy_status = self._privacy_status(row.get("text", ""))
            video_id = self._video_id(row.get("href", ""))
            studio_url = self._studio_url(row.get("href", ""), video_id)
            key = (title, match_type, video_id or studio_url)
            if key in seen:
                continue
            seen.add(key)
            candidates.append(
                {
                    **row,
                    "title": title,
                    "match_type": match_type,
                    "privacy_status": privacy_status,
                    "processing": self._is_processing(row.get("text", "")),
                    "video_id": video_id,
                    "studio_url": studio_url,
                    "video_url": self._watch_url_from_id(video_id),
                }
            )
        return candidates

    def _best_title_match(self, expected_title: str, text: str) -> tuple[str, str]:
        normalized_expected = self._normalize_title(expected_title)
        for candidate in self._title_candidates(text):
            if candidate == expected_title:
                return candidate, "exact"
            normalized_line = self._normalize_title(candidate)
            if normalized_line == normalized_expected:
                return candidate, "normalized_exact"
        for candidate in self._title_candidates(text):
            normalized_line = self._normalize_title(candidate)
            if normalized_line.startswith(normalized_expected):
                return candidate, "starts_with"
            if normalized_expected in normalized_line:
                return candidate, "contains"
        return "", ""

    def _text_lines(self, text: str) -> list[str]:
        return [line.strip() for line in text.splitlines() if line.strip()]

    def _title_candidates(self, text: str) -> list[str]:
        lines = self._text_lines(text)
        candidates = list(lines)
        for size in (2, 3):
            for index in range(0, max(len(lines) - size + 1, 0)):
                candidates.append(" ".join(lines[index : index + size]))
        return candidates

    def _normalize_title(self, value: str) -> str:
        normalized = value.replace("\u3000", " ").replace("\r\n", "\n").replace("\r", "\n")
        normalized = " ".join(normalized.split())
        if normalized.isascii():
            return normalized.casefold()
        return normalized

    def _privacy_status(self, text: str) -> str:
        lowered = text.lower()
        if "処理中" in text or "processing" in lowered:
            return "processing"
        if "下書き" in text or "draft" in lowered:
            return "draft"
        if "限定公開" in text or "unlisted" in lowered:
            return "unlisted"
        if "非公開" in text or "private" in lowered:
            return "private"
        if "公開" in text or "public" in lowered:
            return "public"
        return "unknown"

    def _is_processing(self, text: str) -> bool:
        lowered = text.lower()
        return "処理中" in text or "processing" in lowered

    def _video_id(self, href: str) -> str:
        if not href:
            return ""
        patterns = (
            r"/video/([^/?#]+)/?",
            r"[?&]v=([^&#]+)",
            r"youtu\.be/([^/?#]+)",
        )
        for pattern in patterns:
            match = re.search(pattern, href)
            if match:
                return match.group(1)
        return ""

    def _studio_url(self, href: str, video_id: str) -> str:
        if href:
            absolute = urljoin(self.config.studio_url, href)
            if "/video/" in absolute:
                return absolute
        if video_id:
            return f"https://studio.youtube.com/video/{video_id}/edit"
        return ""

    def _watch_url_from_id(self, video_id: str) -> str:
        if not video_id:
            return ""
        return f"https://www.youtube.com/watch?v={video_id}"

    def _candidate_titles(self, rows: list[dict]) -> tuple[str, ...]:
        titles = []
        for row in rows:
            for line in self._text_lines(row.get("text", "")):
                if line not in titles:
                    titles.append(line)
                if len(titles) >= 10:
                    return tuple(titles)
        return tuple(titles)

    def _row_result(
        self,
        row: dict,
        expected_title: str,
        status: str,
        checked_locations: list[str],
        elapsed_seconds: float,
        private_confirmed: bool = False,
        error: str = "",
    ) -> YouTubePrivateSaveVerificationResult:
        return self._result(
            status=status,
            title=expected_title,
            found=True,
            title_matched=row["match_type"] in {"exact", "normalized_exact"},
            matched_title=row["title"],
            match_type=row["match_type"],
            privacy_status=row["privacy_status"],
            private_confirmed=private_confirmed,
            duplicate_count=1,
            video_id=row["video_id"],
            video_url=row["video_url"],
            studio_url=row["studio_url"],
            content_type=row["content_type"],
            processing=row["processing"],
            checked_locations=tuple(checked_locations),
            candidate_titles=(row["title"],),
            elapsed_seconds=elapsed_seconds,
            error=error,
        )

    def _copy_result(self, result: YouTubePrivateSaveVerificationResult, **updates):
        values = result.__dict__.copy()
        values.update(updates)
        return YouTubePrivateSaveVerificationResult(**values)

    def _result(
        self,
        status: str,
        title: str,
        found: bool = False,
        title_matched: bool = False,
        privacy_status: str = "",
        private_confirmed: bool = False,
        duplicate_count: int = 0,
        video_url: str = "",
        studio_url: str = "",
        error: str = "",
        matched_title: str = "",
        match_type: str = "",
        video_id: str = "",
        content_type: str = "unknown",
        processing: bool = False,
        checked_locations: tuple[str, ...] = (),
        candidate_titles: tuple[str, ...] = (),
        elapsed_seconds: float = 0.0,
    ) -> YouTubePrivateSaveVerificationResult:
        return YouTubePrivateSaveVerificationResult(
            status=status,
            found=found,
            title=title,
            title_matched=title_matched,
            privacy_status=privacy_status,
            private_confirmed=private_confirmed,
            duplicate_count=duplicate_count,
            video_url=video_url,
            studio_url=studio_url,
            error=error,
            matched_title=matched_title,
            match_type=match_type,
            video_id=video_id,
            content_type=content_type,
            processing=processing,
            checked_locations=checked_locations,
            candidate_titles=candidate_titles,
            elapsed_seconds=elapsed_seconds,
        )


class YouTubeRecentContentInspector:
    def __init__(
        self,
        browser=None,
        config: YouTubeCDPConfig | None = None,
        selectors: YouTubeStudioSelectors | None = None,
        inspector_config: YouTubeRecentContentInspectorConfig | None = None,
        sleeper=None,
    ):
        self.browser = browser
        self.config = config or YouTubeCDPConfig()
        self.selectors = selectors or YouTubeStudioSelectors()
        self.inspector_config = inspector_config or YouTubeRecentContentInspectorConfig()
        self.sleeper = sleeper or time.sleep
        self._parser = YouTubePrivateSaveVerifier(
            browser=browser,
            config=self.config,
            selectors=self.selectors,
            verifier_config=YouTubePrivateSaveVerifierConfig(
                max_items=self.inspector_config.max_items
            ),
        )

    def inspect(self, target_title: str = "") -> YouTubeRecentContentInspectionResult:
        browser, should_close = self._browser()
        checked_locations = []
        records = []
        try:
            for location in self._parser._content_locations(browser):
                if len(records) >= self.inspector_config.max_items:
                    break
                content_type = location["content_type"]
                checked_locations.append(content_type)
                browser.open(location["url"])
                rows = self._collect_location_rows(browser)
                for index, row in enumerate(rows[: self.inspector_config.max_items_per_location]):
                    if len(records) >= self.inspector_config.max_items:
                        break
                    records.append(self._record_from_row(row, content_type, index, target_title))
            return self._result(tuple(records), tuple(checked_locations), "")
        except Exception as exc:
            return self._result(tuple(records), tuple(checked_locations), str(exc), "inspect_failed")
        finally:
            if should_close:
                browser.close()

    def _browser(self):
        if self.browser is not None:
            return self.browser, False
        return PlaywrightCDPBrowserController(self.config).start(), True

    def _collect_location_rows(self, browser) -> list[dict]:
        rows = []
        for attempt in range(self.inspector_config.row_retry_count + 1):
            rows = list(browser.collect_video_rows(self.selectors.content_video_rows))
            if rows or attempt >= self.inspector_config.row_retry_count:
                return rows
            self.sleeper(self.inspector_config.row_retry_interval_seconds)
        return rows

    def _record_from_row(
        self,
        row: dict,
        content_type: str,
        row_index: int,
        target_title: str,
    ) -> YouTubeContentRecord:
        text = str(row.get("text", ""))
        href = str(row.get("href", ""))
        title = self._extract_title(text)
        normalized_title = self._parser._normalize_title(title)
        privacy_status = self._parser._privacy_status(text)
        processing_status = self._processing_status(text, privacy_status)
        video_id = self._parser._video_id(href)
        studio_url = self._parser._studio_url(href, video_id)
        displayed_date = self._displayed_date(text)
        record = YouTubeContentRecord(
            title=title,
            normalized_title=normalized_title,
            privacy_status=privacy_status,
            processing_status=processing_status,
            content_type=content_type,
            video_id=video_id,
            video_url=self._parser._watch_url_from_id(video_id),
            studio_url=studio_url,
            displayed_date=displayed_date,
            row_index=row_index,
        )
        return self._with_candidate_reasons(record, target_title)

    def _extract_title(self, text: str) -> str:
        for line in self._parser._text_lines(text):
            if self._is_metadata_line(line):
                continue
            return line
        return ""

    def _is_metadata_line(self, line: str) -> bool:
        lowered = line.lower()
        if re.fullmatch(r"\d{1,2}:\d{2}(:\d{2})?", line):
            return True
        if re.fullmatch(r"\d{4}/\d{1,2}/\d{1,2}", line):
            return True
        if line in {"—", "-", "公開日"}:
            return True
        if lowered in {"public", "private", "unlisted", "draft", "processing"}:
            return True
        if any(token in line for token in ("公開", "非公開", "限定公開", "下書き", "処理中")):
            return True
        if re.fullmatch(r"\d+", line):
            return True
        return False

    def _processing_status(self, text: str, privacy_status: str) -> str:
        lowered = text.lower()
        if "処理中" in text or "processing" in lowered:
            return "processing"
        if privacy_status == "draft" or "下書き" in text or "draft" in lowered:
            return "draft"
        return ""

    def _displayed_date(self, text: str) -> str:
        for line in self._parser._text_lines(text):
            if re.fullmatch(r"\d{4}/\d{1,2}/\d{1,2}", line):
                return line
        return ""

    def _with_candidate_reasons(
        self,
        record: YouTubeContentRecord,
        target_title: str,
    ) -> YouTubeContentRecord:
        reasons = []
        normalized_target = self._parser._normalize_title(target_title)
        if target_title and record.title == target_title:
            reasons.append("exact_title")
        elif normalized_target and record.normalized_title == normalized_target:
            reasons.append("normalized_exact_title")
        elif normalized_target and normalized_target in record.normalized_title:
            reasons.append("partial_title")
        normalized_record = record.normalized_title
        if "project shiro" in normalized_record:
            reasons.append("project_shiro")
        if "smoke test" in normalized_record:
            reasons.append("smoke_test")
        if record.privacy_status == "private":
            reasons.append("private_recent")
        if record.processing_status == "processing":
            reasons.append("processing")
        if record.privacy_status == "draft" or record.processing_status == "draft":
            reasons.append("draft")
        if not record.title:
            reasons.append("empty_title")
        if not record.video_id:
            reasons.append("no_video_id")
        return YouTubeContentRecord(
            title=record.title,
            normalized_title=record.normalized_title,
            privacy_status=record.privacy_status,
            processing_status=record.processing_status,
            content_type=record.content_type,
            video_id=record.video_id,
            video_url=record.video_url,
            studio_url=record.studio_url,
            displayed_date=record.displayed_date,
            row_index=record.row_index,
            candidate_reasons=tuple(reasons),
        )

    def _result(
        self,
        records: tuple[YouTubeContentRecord, ...],
        checked_locations: tuple[str, ...],
        error: str = "",
        status: str = "inspected",
    ) -> YouTubeRecentContentInspectionResult:
        return YouTubeRecentContentInspectionResult(
            status=status,
            records=records,
            checked_locations=checked_locations,
            total_records=len(records),
            private_count=sum(1 for record in records if record.privacy_status == "private"),
            processing_count=sum(
                1 for record in records if record.processing_status == "processing"
            ),
            draft_count=sum(
                1
                for record in records
                if record.privacy_status == "draft" or record.processing_status == "draft"
            ),
            records_without_video_id=sum(1 for record in records if not record.video_id),
            exact_matches=self._records_with(records, "exact_title"),
            normalized_matches=self._records_with(records, "normalized_exact_title"),
            partial_matches=self._records_with(records, "partial_title"),
            project_shiro_candidates=self._records_with(records, "project_shiro"),
            smoke_test_candidates=self._records_with(records, "smoke_test"),
            private_recent_candidates=self._records_with(records, "private_recent"),
            processing_candidates=self._records_with(records, "processing"),
            draft_candidates=self._records_with(records, "draft"),
            empty_title_candidates=self._records_with(records, "empty_title"),
            no_video_id_candidates=self._records_with(records, "no_video_id"),
            error=error,
        )

    def _records_with(
        self,
        records: tuple[YouTubeContentRecord, ...],
        reason: str,
    ) -> tuple[YouTubeContentRecord, ...]:
        return tuple(record for record in records if reason in record.candidate_reasons)


class YouTubePrivateSaveAttemptStore:
    def __init__(
        self,
        path: str | Path = "outputs/youtube_private_smoke/private_save_attempts.json",
    ):
        self.path = Path(path)

    def get(self, smoke_id: str) -> YouTubePrivateSaveAttempt | None:
        for attempt in self.list_all():
            if attempt.smoke_id == smoke_id:
                return attempt
        return None

    def list_all(self) -> list[YouTubePrivateSaveAttempt]:
        data = self._load_data()
        return [
            YouTubePrivateSaveAttempt.from_dict(item)
            for item in data.get("attempts", [])
        ]

    def ensure_save_allowed(self, smoke_id: str) -> None:
        existing = self.get(smoke_id)
        if existing is None:
            return
        if existing.save_clicked:
            raise ValueError("duplicate_save_blocked")
        raise ValueError("duplicate_smoke_id")

    def save(self, attempt: YouTubePrivateSaveAttempt) -> YouTubePrivateSaveAttempt:
        data = self._load_data()
        attempts = data["attempts"]
        payload = attempt.to_dict()
        for index, existing in enumerate(attempts):
            if existing.get("smoke_id") == attempt.smoke_id:
                attempts[index] = payload
                break
        else:
            attempts.append(payload)
        self._write_data(data)
        return attempt

    def _load_data(self) -> dict:
        if not self.path.exists():
            return {"schema_version": 1, "attempts": []}
        return json.loads(self.path.read_text(encoding="utf-8"))

    def _write_data(self, data: dict) -> None:
        payload = json.dumps(data, ensure_ascii=False, indent=2)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temp_path = self.path.parent / f".{self.path.name}.{uuid4().hex}.tmp"
        try:
            with open(temp_path, "w", encoding="utf-8") as temp_file:
                temp_file.write(payload)
                temp_file.flush()
                os.fsync(temp_file.fileno())
            os.replace(str(temp_path), str(self.path))
        finally:
            try:
                if temp_path.exists():
                    temp_path.unlink()
            except OSError:
                pass


class YouTubeStudioChannelIdentityReader:
    def __init__(
        self,
        browser=None,
        config: YouTubeCDPConfig | None = None,
        channel_name_selectors: tuple[str, ...] | None = None,
    ):
        self.browser = browser
        self.config = config or YouTubeCDPConfig()
        self.channel_name_selectors = channel_name_selectors or (
            "#account-name",
            "#entity-name",
            "ytcp-app-header #entity-name",
            "ytcp-text-menu #text",
            "[aria-label*='チャンネル']",
            "[aria-label*='Channel']",
        )

    def read_identity(self, expected_channel_name: str = "") -> YouTubeStudioChannelIdentity:
        browser, should_close = self._browser()
        try:
            if hasattr(browser, "open"):
                browser.open(self.config.studio_url)
            current_url = getattr(browser, "current_url", "") or ""
            channel_name = self._channel_name(browser)
            channel_id = self._channel_id(current_url)
            if not channel_name:
                return YouTubeStudioChannelIdentity(
                    channel_name="",
                    channel_id=channel_id,
                    current_url=current_url,
                    studio_available="studio.youtube.com" in current_url,
                    identity_confirmed=False,
                    error="identity_unverified",
                )
            expected = expected_channel_name.strip()
            confirmed = not expected or channel_name.strip() == expected
            return YouTubeStudioChannelIdentity(
                channel_name=channel_name,
                channel_id=channel_id,
                current_url=current_url,
                studio_available="studio.youtube.com" in current_url,
                identity_confirmed=confirmed,
                error="" if confirmed else "channel_mismatch",
            )
        except Exception as exc:
            return YouTubeStudioChannelIdentity(
                current_url=getattr(browser, "current_url", ""),
                studio_available=False,
                identity_confirmed=False,
                error=str(exc) or "identity_unverified",
            )
        finally:
            if should_close:
                browser.close()

    def _browser(self):
        if self.browser is not None:
            return self.browser, False
        return PlaywrightCDPBrowserController(self.config).start(), True

    def _channel_name(self, browser) -> str:
        if hasattr(browser, "read_channel_name"):
            return str(browser.read_channel_name()).strip()
        if hasattr(browser, "read_text"):
            return str(browser.read_text(self.channel_name_selectors)).strip()
        return ""

    def _channel_id(self, current_url: str) -> str:
        parsed = urlparse(current_url)
        parts = [part for part in parsed.path.split("/") if part]
        if len(parts) >= 2 and parts[0] == "channel":
            return parts[1]
        return ""


class YouTubeControlledPrivateSaveRunner:
    PREVIOUS_SMOKE_TITLE = "Project SHIRO Private Smoke Test"

    def __init__(
        self,
        private_save_confirmer=None,
        verifier=None,
        identity_reader=None,
        attempt_store: YouTubePrivateSaveAttemptStore | None = None,
        post_save_disconnect=None,
        clock=None,
    ):
        self.private_save_confirmer = private_save_confirmer
        self.verifier = verifier
        self.identity_reader = identity_reader
        self.attempt_store = attempt_store or YouTubePrivateSaveAttemptStore()
        self.post_save_disconnect = post_save_disconnect
        self.clock = clock or (lambda: datetime.now().strftime("%Y-%m-%dT%H:%M:%S"))

    def run(
        self,
        video_path: str,
        metadata: YouTubeVideoMetadata,
        smoke_id: str,
        expected_channel_name: str,
        confirm_private_save: bool,
        keep_open: bool = False,
    ) -> YouTubeControlledPrivateSaveResult:
        title = self._title(smoke_id)
        if not expected_channel_name:
            return self._failed("expected_channel_required", smoke_id, title)
        if not smoke_id:
            return self._failed("smoke_id_required", smoke_id, title)
        if not confirm_private_save:
            return self._failed("confirmation_required", smoke_id, title)
        if title == self.PREVIOUS_SMOKE_TITLE:
            return self._failed("previous_title_rejected", smoke_id, title)
        if len(title) > 100:
            return self._failed("title_too_long", smoke_id, title)

        identity = self.identity_reader.read_identity(expected_channel_name)
        if not identity.identity_confirmed:
            return self._failed(identity.error or "identity_unverified", smoke_id, title)

        try:
            self.attempt_store.ensure_save_allowed(smoke_id)
        except ValueError as exc:
            return self._failed(str(exc), smoke_id, title, channel_confirmed=True)

        video = Path(video_path)
        if not video.exists() or not video.is_file():
            return self._failed("video_not_found", smoke_id, title, channel_confirmed=True)

        attempt = YouTubePrivateSaveAttempt(
            smoke_id=smoke_id,
            title=title,
            video_path=str(video_path),
            video_size=video.stat().st_size,
            attempted_at=self.clock(),
            save_clicked=False,
        )
        self.attempt_store.save(attempt)

        save_metadata = YouTubeVideoMetadata(
            title=title,
            description=metadata.description,
            made_for_kids=metadata.made_for_kids,
            tags=metadata.tags,
        )
        try:
            save_result = self.private_save_confirmer.save_private(
                str(video_path),
                save_metadata,
                policy=YouTubePrivateSavePolicy(confirm_private_save=True),
                keep_open=keep_open,
            )
        except Exception as exc:
            attempt.save_clicked = False
            attempt.save_click_status = "failed"
            attempt.save_completion_status = "failed"
            attempt.last_error = str(exc) or "private_save_failed"
            attempt.updated_at = self.clock()
            self.attempt_store.save(attempt)
            return self._failed(
                str(exc) or "private_save_failed",
                smoke_id,
                title,
                channel_confirmed=True,
            )
        attempt.save_clicked = save_result.save_clicked
        attempt.save_click_status = "dispatched" if save_result.save_clicked else "failed"
        attempt.save_completion_status = (
            "confirmed"
            if save_result.saved
            else "unverified"
            if save_result.save_clicked
            else "failed"
        )
        if save_result.evidence is not None:
            evidence = save_result.evidence
            attempt.upload_readiness_status = (
                "ready" if evidence.upload_complete_before_click and not evidence.blocking_error_detected else "not_ready"
            )
            attempt.upload_complete_before_save = evidence.upload_complete_before_click
            attempt.blocking_error = evidence.blocking_error_detected
            attempt.save_button_label = evidence.save_button_exact_label or evidence.save_button_label
            attempt.save_response_status = (
                "confirmed" if evidence.completion_confirmed else "unverified"
            )
            attempt.completion_evidence = {
                "dialog_closed": evidence.dialog_closed,
                "success_message_detected": evidence.success_message_detected,
                "post_click_video_id": evidence.post_click_video_id,
                "post_click_private_visibility_detected": evidence.post_click_private_visibility_detected,
                "completion_evidence_count": evidence.completion_evidence_count,
                "completion_confirmed": evidence.completion_confirmed,
            }
            attempt.post_save_video_id = evidence.post_click_video_id
            attempt.post_save_private_confirmed = evidence.post_click_private_visibility_detected
        attempt.last_error = "" if save_result.saved else save_result.error or save_result.status
        attempt.updated_at = self.clock()
        self.attempt_store.save(attempt)
        if save_result.status != "private_saved":
            return self._from_save_result(smoke_id, title, save_result)

        if self.post_save_disconnect is not None:
            try:
                self.post_save_disconnect()
            except Exception as exc:
                attempt.last_error = str(exc) or "post_save_disconnect_failed"
                attempt.updated_at = self.clock()
                self.attempt_store.save(attempt)
                return YouTubeControlledPrivateSaveResult(
                    status="save_unverified",
                    smoke_id=smoke_id,
                    title=title,
                    channel_identity_confirmed=True,
                    private_selected=save_result.private_selected,
                    save_clicked=save_result.save_clicked,
                    saved=False,
                    published=False,
                    privacy_status="private",
                    error=attempt.last_error,
                )

        try:
            verification = self.verifier.verify(title)
        except Exception as exc:
            error = str(exc) or "verification_failed"
            attempt.verification_status = error
            attempt.last_error = error
            attempt.updated_at = self.clock()
            self.attempt_store.save(attempt)
            return YouTubeControlledPrivateSaveResult(
                status="save_unverified",
                smoke_id=smoke_id,
                title=title,
                channel_identity_confirmed=True,
                private_selected=save_result.private_selected,
                save_clicked=save_result.save_clicked,
                saved=False,
                published=False,
                privacy_status="private",
                verification_status=error,
                error=error,
            )
        attempt.verification_status = verification.status
        attempt.video_id = verification.video_id
        attempt.updated_at = self.clock()
        self.attempt_store.save(attempt)

        success = (
            verification.status == "verified_private"
            and verification.found
            and verification.private_confirmed
            and verification.duplicate_count == 1
            and bool(verification.video_id)
            and bool(verification.video_url)
            and bool(verification.studio_url)
        )
        return YouTubeControlledPrivateSaveResult(
            status="verified_private" if success else "save_unverified",
            smoke_id=smoke_id,
            title=title,
            channel_identity_confirmed=True,
            private_selected=save_result.private_selected,
            save_clicked=save_result.save_clicked,
            saved=success,
            published=False,
            privacy_status="private",
            verification_status=verification.status,
            found=verification.found,
            private_confirmed=verification.private_confirmed,
            duplicate_count=verification.duplicate_count,
            video_id=verification.video_id,
            video_url=verification.video_url,
            studio_url=verification.studio_url,
            content_type=verification.content_type,
            error="" if success else verification.error or verification.status,
        )

    def _title(self, smoke_id: str) -> str:
        return f"Project SHIRO Private Smoke {smoke_id}"

    def _from_save_result(self, smoke_id: str, title: str, save_result):
        return YouTubeControlledPrivateSaveResult(
            status=save_result.status,
            smoke_id=smoke_id,
            title=title,
            channel_identity_confirmed=True,
            private_selected=save_result.private_selected,
            save_clicked=save_result.save_clicked,
            saved=False,
            published=False,
            privacy_status="private",
            error=save_result.error or save_result.status,
        )

    def _failed(
        self,
        status: str,
        smoke_id: str,
        title: str,
        channel_confirmed: bool = False,
    ) -> YouTubeControlledPrivateSaveResult:
        return YouTubeControlledPrivateSaveResult(
            status=status,
            smoke_id=smoke_id,
            title=title,
            channel_identity_confirmed=channel_confirmed,
            private_selected=False,
            save_clicked=False,
            saved=False,
            published=False,
            privacy_status="private",
            error=status,
        )
