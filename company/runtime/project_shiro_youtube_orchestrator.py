from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Callable, Optional

from company.memory.company_memory import CompanyMemory
from company.reports.run_report import RunReportWriter, build_run_report
from company.reports.run_report_memory_adapter import RunReportMemoryAdapter
from company.runtime.real_video_pipeline_factory import RealVideoPipelineFactory
from company.runtime.real_video_runtime import (
    RealVideoRuntimeConfig,
    VideoOutputValidator,
)
from company.youtube.studio_upload import (
    PlaywrightCDPBrowserController,
    YouTubeBrowserConfig,
    YouTubeCDPConfig,
    YouTubeMetadataPreparer,
    YouTubePrivateSavePolicy,
    YouTubePrivateSaveVerifier,
    YouTubePrivateSaveVerifierConfig,
    YouTubeStudioChannelIdentityReader,
    YouTubeStudioUploadPreparer,
    YouTubeUploadReadinessChecker,
    YouTubeVideoMetadata,
    YouTubePrivateSaveConfirmer,
)


class ProjectShiroStopPoint:
    AFTER_VIDEO = "after_video"
    BEFORE_UPLOAD = "before_upload"
    AFTER_UPLOAD_PREPARE = "after_upload_prepare"
    AFTER_METADATA = "after_metadata"
    BEFORE_SAVE = "before_save"
    AFTER_SAVE = "after_save"
    AFTER_VERIFICATION = "after_verification"
    NONE = "none"

    VALUES = {
        AFTER_VIDEO,
        BEFORE_UPLOAD,
        AFTER_UPLOAD_PREPARE,
        AFTER_METADATA,
        BEFORE_SAVE,
        AFTER_SAVE,
        AFTER_VERIFICATION,
        NONE,
    }


@dataclass(frozen=True)
class ProjectShiroYouTubeRunConfig:
    topic: str
    output_root: str = "outputs/real_video"
    existing_video_path: str = ""
    cdp_endpoint: str = "http://127.0.0.1:9222"
    expected_channel_name: str = ""
    title: str = ""
    description: str = ""
    tags: tuple[str, ...] = ()
    made_for_kids: Optional[bool] = None
    stop_point: str = ProjectShiroStopPoint.BEFORE_SAVE
    confirm_private_save: bool = False
    smoke_id: str = ""
    verify_timeout_seconds: float = 120.0
    verify_poll_interval_seconds: float = 10.0
    max_inspection_items: int = 50
    keep_open: bool = False
    save_report: bool = True
    save_memory: bool = True

    def __post_init__(self):
        if not str(self.topic).strip():
            raise ValueError("topic is required.")
        if self.stop_point not in ProjectShiroStopPoint.VALUES:
            raise ValueError(f"Unknown stop point: {self.stop_point}")
        if self.confirm_private_save and not self.expected_channel_name:
            raise ValueError("expected_channel_name is required for private save.")
        if self.confirm_private_save and not self.smoke_id:
            raise ValueError("smoke_id is required for private save.")
        if self.made_for_kids is None:
            raise ValueError("made_for_kids must be explicitly specified.")


@dataclass
class ProjectShiroYouTubeRunResult:
    status: str
    topic: str
    run_id: str = ""
    job_id: str = ""
    video_status: str = ""
    video_path: str = ""
    video_size: int = 0
    duration: float = 0.0
    upload_status: str = ""
    metadata_status: str = ""
    save_status: str = ""
    verification_status: str = ""
    channel_identity_confirmed: bool = False
    title: str = ""
    description: str = ""
    tags: tuple[str, ...] = ()
    made_for_kids: Optional[bool] = None
    private_selected: bool = False
    save_clicked: bool = False
    saved: bool = False
    published: bool = False
    privacy_status: str = ""
    video_id: str = ""
    video_url: str = ""
    studio_url: str = ""
    checked_locations: tuple[str, ...] = ()
    stop_point: str = ProjectShiroStopPoint.BEFORE_SAVE
    failure_stage: str = ""
    error: str = ""
    run_report_path: Optional[str] = None
    checkpoints: list[dict] = field(default_factory=list)
    memory_record: Optional[dict] = None
    video_result: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        data = asdict(self)
        data["tags"] = tuple(self.tags)
        data["checked_locations"] = tuple(self.checked_locations)
        return data


@dataclass
class ProjectShiroYouTubeServices:
    browser: object
    identity_reader: object
    upload_preparer: object
    metadata_preparer: object
    readiness_checker: object
    private_save_confirmer: object
    verifier_factory: Callable[[], object]
    disconnect: Callable[[], None] | None = None
    attempt_store: object | None = None


class ProjectShiroYouTubeOrchestrator:
    def __init__(
        self,
        *,
        preflight_checker=None,
        video_pipeline=None,
        video_validator=None,
        youtube_services_factory=None,
        report_writer=None,
        memory=None,
        memory_adapter=None,
        clock=None,
    ):
        self.preflight_checker = preflight_checker
        self.video_pipeline = video_pipeline
        self.video_validator = video_validator or VideoOutputValidator()
        self.youtube_services_factory = youtube_services_factory
        self.report_writer = report_writer
        self.memory = memory
        self.memory_adapter = memory_adapter or RunReportMemoryAdapter()
        self.clock = clock

    def run(self, config: ProjectShiroYouTubeRunConfig) -> ProjectShiroYouTubeRunResult:
        result = ProjectShiroYouTubeRunResult(
            status="started",
            topic=config.topic,
            run_id=config.smoke_id,
            job_id=config.smoke_id,
            stop_point=config.stop_point,
            title=self._metadata_title(config, {}),
            description=config.description,
            tags=tuple(config.tags),
            made_for_kids=config.made_for_kids,
            published=False,
        )
        services = None
        try:
            if not self._run_preflight(result):
                return self._finish(config, result)

            video_result = self._run_video_pipeline(config, result)
            if video_result is None:
                return self._finish(config, result)

            if not self._validate_video(video_result, result):
                return self._finish(config, result)

            if self._stop(config, result, ProjectShiroStopPoint.AFTER_VIDEO, "video_completed"):
                return self._finish(config, result)
            if self._stop(config, result, ProjectShiroStopPoint.BEFORE_UPLOAD, "video_completed"):
                return self._finish(config, result)

            services = self._connect_youtube_services(config, result)
            if services is None:
                return self._finish(config, result)

            if not self._confirm_channel(config, services, result):
                return self._finish(config, result)

            if not self._prepare_upload(config, services, result):
                return self._finish(config, result)
            if self._stop(config, result, ProjectShiroStopPoint.AFTER_UPLOAD_PREPARE, "upload_prepared"):
                return self._finish(config, result)

            metadata = self._build_metadata(config, video_result)
            if not self._prepare_metadata(config, services, metadata, result):
                return self._finish(config, result)
            if self._stop(config, result, ProjectShiroStopPoint.AFTER_METADATA, "metadata_prepared"):
                return self._finish(config, result)

            if config.stop_point == ProjectShiroStopPoint.BEFORE_SAVE or not config.confirm_private_save:
                result.status = "stopped_before_save"
                self._checkpoint(result, "metadata_prepared")
                return self._finish(config, result)

            if not self._ensure_private_save_allowed(config, services, result):
                return self._finish(config, result)

            save_result = self._save_private(config, services, metadata, result)
            if save_result is None:
                return self._finish(config, result)

            self._disconnect(services)
            if config.stop_point == ProjectShiroStopPoint.AFTER_SAVE:
                services = None
                result.status = "save_unverified" if result.save_clicked else "private_save_failed"
                return self._finish(config, result)

            self._verify_private(services, result)
            services = None
            return self._finish(config, result)
        finally:
            if services is not None:
                self._disconnect(services)

    def _run_preflight(self, result: ProjectShiroYouTubeRunResult) -> bool:
        if self.preflight_checker is None:
            self._checkpoint(result, "preflight_skipped")
            return True
        try:
            if hasattr(self.preflight_checker, "ensure_ready"):
                self.preflight_checker.ensure_ready()
            else:
                statuses = self.preflight_checker.check_all()
                failed = [status for status in statuses if not getattr(status, "ok", False)]
                if failed:
                    raise RuntimeError(", ".join(status.name for status in failed))
        except Exception as exc:
            self._fail(result, "preflight_failed", "preflight", exc)
            return False
        self._checkpoint(result, "preflight_ok")
        return True

    def _run_video_pipeline(self, config, result):
        if config.existing_video_path:
            video_result = {
                "topic": config.topic,
                "research_result": "",
                "script_result": "",
                "review_result": "",
                "video_path": config.existing_video_path,
            }
            result.video_result = dict(video_result)
            result.video_status = "existing_video"
            result.video_path = config.existing_video_path
            self._checkpoint(result, "video_completed")
            return video_result
        try:
            pipeline = self.video_pipeline
            if pipeline is None:
                runtime_config = RealVideoRuntimeConfig(output_root=config.output_root)
                pipeline = RealVideoPipelineFactory(config=runtime_config).build()
            video_result = pipeline.run(config.topic)
        except Exception as exc:
            stage = "voice_generation" if "VOICEVOXGenerator" in str(exc) else "video"
            self._fail(result, "video_generation_failed", stage, exc)
            return None
        result.video_result = dict(video_result)
        result.video_status = str(video_result.get("status", "completed") or "completed")
        result.video_path = str(video_result.get("video_path", ""))
        self._checkpoint(result, "video_completed")
        return video_result

    def _validate_video(self, video_result, result) -> bool:
        try:
            validation = self.video_validator.validate(str(video_result.get("video_path", "")))
        except Exception as exc:
            self._fail(result, "video_validation_failed", "video_validation", exc)
            return False
        result.video_path = str(validation.get("video_path", result.video_path))
        result.video_size = int(validation.get("size_bytes", 0) or 0)
        self._checkpoint(result, "video_validated")
        return True

    def _connect_youtube_services(self, config, result):
        try:
            if self.youtube_services_factory is None:
                services = build_default_youtube_services(config)
            else:
                services = self.youtube_services_factory(config)
        except Exception as exc:
            self._fail(result, "cdp_connection_failed", "cdp_connection", exc)
            return None
        self._checkpoint(result, "cdp_connected")
        return services

    def _confirm_channel(self, config, services, result) -> bool:
        try:
            identity = services.identity_reader.read_identity(config.expected_channel_name)
        except Exception as exc:
            self._fail(result, "channel_identity_failed", "channel_identity", exc)
            return False
        confirmed = bool(getattr(identity, "identity_confirmed", False))
        result.channel_identity_confirmed = confirmed
        if config.expected_channel_name and not confirmed:
            self._fail(
                result,
                "channel_identity_failed",
                "channel_identity",
                getattr(identity, "error", "") or "expected channel did not match",
            )
            return False
        self._checkpoint(result, "channel_identity_confirmed")
        return True

    def _prepare_upload(self, config, services, result) -> bool:
        try:
            upload = services.upload_preparer.prepare_upload(
                result.video_path,
                keep_open=config.keep_open,
            )
        except Exception as exc:
            self._fail(result, "upload_prepare_failed", "upload_prepare", exc)
            return False
        result.upload_status = str(getattr(upload, "status", ""))
        if result.upload_status != "prepared":
            self._fail(
                result,
                "upload_prepare_failed",
                "upload_prepare",
                getattr(upload, "error", "") or result.upload_status,
            )
            return False
        self._checkpoint(result, "upload_prepared")
        return True

    def _prepare_metadata(self, config, services, metadata, result) -> bool:
        try:
            prepared = services.metadata_preparer.prepare_metadata(
                result.video_path,
                metadata,
                keep_open=config.keep_open,
            )
        except Exception as exc:
            self._fail(result, "metadata_prepare_failed", "metadata_prepare", exc)
            return False
        result.metadata_status = str(getattr(prepared, "status", ""))
        result.title = str(getattr(prepared, "title", metadata.title))
        result.description = str(getattr(prepared, "description", metadata.description))
        result.tags = tuple(getattr(prepared, "tags", metadata.tags) or ())
        result.made_for_kids = bool(getattr(prepared, "made_for_kids", metadata.made_for_kids))
        if result.metadata_status != "metadata_prepared":
            self._fail(
                result,
                "metadata_prepare_failed",
                "metadata_prepare",
                getattr(prepared, "error", "") or result.metadata_status,
            )
            return False
        self._checkpoint(result, "metadata_prepared")
        return True

    def _ensure_private_save_allowed(self, config, services, result) -> bool:
        if not config.confirm_private_save:
            result.status = "stopped_before_save"
            return False
        if not config.expected_channel_name:
            self._fail(result, "channel_identity_failed", "channel_identity", "expected channel is required")
            return False
        if not config.smoke_id:
            self._fail(result, "private_save_failed", "private_save", "smoke_id is required")
            return False
        if services.attempt_store is not None:
            try:
                services.attempt_store.ensure_save_allowed(config.smoke_id)
            except Exception as exc:
                self._fail(result, "private_save_failed", "private_save", exc)
                return False
        return True

    def _save_private(self, config, services, metadata, result):
        try:
            save_result = services.private_save_confirmer.save_private(
                result.video_path,
                metadata,
                policy=YouTubePrivateSavePolicy(confirm_private_save=True),
                keep_open=config.keep_open,
            )
        except Exception as exc:
            self._fail(result, "private_save_failed", "private_save", exc)
            return None
        result.save_status = str(getattr(save_result, "status", ""))
        result.private_selected = bool(getattr(save_result, "private_selected", False))
        result.save_clicked = bool(getattr(save_result, "save_clicked", False))
        result.saved = bool(getattr(save_result, "saved", False))
        result.published = bool(getattr(save_result, "published", False))
        result.privacy_status = str(getattr(save_result, "privacy_status", ""))
        result.video_url = str(getattr(save_result, "video_url", ""))
        result.studio_url = str(getattr(save_result, "studio_url", ""))
        if result.saved:
            self._checkpoint(result, "save_confirmed")
        elif result.save_clicked:
            self._checkpoint(result, "save_clicked")
        if result.save_status in {"upload_not_ready", "blocking_error", "save_button_disabled"}:
            self._fail(result, "upload_not_ready", "upload_readiness", getattr(save_result, "error", ""))
            return save_result
        if not result.save_clicked:
            self._fail(result, "private_save_failed", "private_save", getattr(save_result, "error", result.save_status))
            return save_result
        return save_result

    def _verify_private(self, services, result) -> None:
        try:
            verifier = services.verifier_factory()
            verification = verifier.verify(result.title)
        except Exception as exc:
            self._fail(result, "verification_failed", "verification", exc)
            return
        result.verification_status = str(getattr(verification, "status", ""))
        result.checked_locations = tuple(getattr(verification, "checked_locations", ()) or ())
        result.video_id = str(getattr(verification, "video_id", ""))
        result.video_url = str(getattr(verification, "video_url", result.video_url))
        result.studio_url = str(getattr(verification, "studio_url", result.studio_url))
        result.privacy_status = str(getattr(verification, "privacy_status", result.privacy_status))
        if result.verification_status == "verified_private":
            result.status = "private_verified"
            result.saved = True
            result.private_selected = True
            result.privacy_status = "private"
            self._checkpoint(result, "verified_private")
            return
        result.saved = False
        result.status = "save_unverified" if result.save_clicked else "verification_failed"
        result.failure_stage = "verification"
        result.error = str(getattr(verification, "error", "") or result.verification_status)

    def _finish(self, config, result):
        self._write_report_and_memory(config, result)
        return result

    def _write_report_and_memory(self, config, result) -> None:
        report = build_run_report(
            topic=config.topic,
            media_mode="real media",
            result=self._report_result_dict(result),
            status=result.status,
        )
        if config.save_report:
            writer = self.report_writer or RunReportWriter(
                output_dir=str(Path(config.output_root) / "reports")
            )
            result.run_report_path = writer.write(report)
        if config.save_memory:
            memory = self.memory or CompanyMemory(
                memory_path=str(Path(config.output_root) / "memory" / "company_memory.json")
            )
            record = self.memory_adapter.to_memory_record(report)
            if hasattr(memory, "add_run_report"):
                memory.add_run_report(record)
            else:
                data = memory.load()
                data.setdefault("run_reports", [])
                data["run_reports"].append(record)
                memory.save(data)
            result.memory_record = record

    def _report_result_dict(self, result) -> dict:
        data = dict(result.video_result or {})
        data.update(
            {
                "video_path": result.video_path,
                "youtube_save_status": result.save_status or result.status,
                "youtube_privacy_status": result.privacy_status,
                "youtube_saved": result.saved,
                "youtube_published": result.published,
                "youtube_video_url": result.video_url,
                "youtube_studio_url": result.studio_url,
                "youtube_save_error": result.error if result.failure_stage == "private_save" else "",
                "youtube_verification_status": result.verification_status,
                "youtube_private_confirmed": result.status == "private_verified",
                "youtube_duplicate_count": 1 if result.status == "private_verified" else 0,
                "youtube_video_id": result.video_id,
                "youtube_content_type": "",
                "youtube_verification_error": result.error if result.failure_stage == "verification" else "",
                "project_shiro_youtube_status": result.status,
                "project_shiro_youtube_failure_stage": result.failure_stage,
                "project_shiro_youtube_checkpoints": list(result.checkpoints),
                "project_shiro_youtube_run_id": result.run_id,
            }
        )
        return data

    def _build_metadata(self, config, video_result) -> YouTubeVideoMetadata:
        return YouTubeVideoMetadata(
            title=self._metadata_title(config, video_result),
            description=self._metadata_description(config, video_result),
            made_for_kids=bool(config.made_for_kids),
            tags=self._metadata_tags(config),
        )

    def _metadata_title(self, config, video_result) -> str:
        return config.title.strip() or str(video_result.get("script_title", "")).strip() or config.topic

    def _metadata_description(self, config, video_result) -> str:
        if config.description:
            return config.description
        script = str(video_result.get("script_result", "")).strip()
        if script:
            return f"{config.topic}\n\n{script[:1000]}"
        return config.topic

    def _metadata_tags(self, config) -> tuple[str, ...]:
        if config.tags:
            return tuple(config.tags)
        return ("ProjectSHIRO", config.topic[:50])

    def _stop(self, config, result, point: str, status: str) -> bool:
        if config.stop_point == point:
            result.status = status
            result.stop_point = point
            self._checkpoint(result, point)
            return True
        return False

    def _checkpoint(self, result, name: str) -> None:
        result.checkpoints.append({"name": name})

    def _fail(self, result, status: str, stage: str, exc) -> None:
        result.status = status
        result.failure_stage = stage
        result.error = str(exc)
        result.published = False
        self._checkpoint(result, status)

    def _disconnect(self, services: ProjectShiroYouTubeServices) -> None:
        if services.disconnect is not None:
            services.disconnect()
        elif hasattr(services.browser, "safe_disconnect"):
            services.browser.safe_disconnect()


def build_default_verifier(config: ProjectShiroYouTubeRunConfig):
    return YouTubePrivateSaveVerifier(
        config=YouTubeCDPConfig(endpoint_url=config.cdp_endpoint),
        verifier_config=YouTubePrivateSaveVerifierConfig(
            timeout_seconds=config.verify_timeout_seconds,
            poll_interval_seconds=config.verify_poll_interval_seconds,
            max_items=config.max_inspection_items,
        ),
    )


def build_default_youtube_services(config: ProjectShiroYouTubeRunConfig):
    cdp_config = YouTubeCDPConfig(endpoint_url=config.cdp_endpoint)
    browser = PlaywrightCDPBrowserController(config=cdp_config).start()
    upload_preparer = YouTubeStudioUploadPreparer(
        config=YouTubeBrowserConfig(studio_url=cdp_config.studio_url),
        browser=browser,
    )
    metadata_preparer = YouTubeMetadataPreparer(upload_preparer=upload_preparer)
    return ProjectShiroYouTubeServices(
        browser=browser,
        identity_reader=YouTubeStudioChannelIdentityReader(
            browser=browser,
            config=cdp_config,
        ),
        upload_preparer=upload_preparer,
        metadata_preparer=metadata_preparer,
        readiness_checker=YouTubeUploadReadinessChecker(),
        private_save_confirmer=YouTubePrivateSaveConfirmer(
            metadata_preparer=metadata_preparer,
        ),
        verifier_factory=lambda: build_default_verifier(config),
        disconnect=browser.safe_disconnect,
    )
