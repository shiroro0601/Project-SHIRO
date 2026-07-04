import json
from pathlib import Path
from uuid import uuid4

from company.automation.browser import BrowserController


class YouTubeStudioPublisher:
    def __init__(
        self,
        dry_run: bool = True,
        upload_url: str = "https://studio.youtube.com",
        output_dir: str = "outputs/publish",
        browser: BrowserController | None = None,
    ):
        self.dry_run = dry_run
        self.upload_url = upload_url
        self.output_dir = Path(output_dir)
        self.browser = browser

    def generate(self, payload) -> dict:
        input_data = getattr(payload, "input_data", payload) or {}
        video_path = input_data.get("video_path", "")
        metadata = input_data.get("metadata", input_data)
        return self.publish(video_path=video_path, metadata=metadata)

    def publish(self, video_path: str, metadata: dict) -> dict:
        if not video_path:
            raise ValueError("video_path must not be empty.")
        if "title" not in metadata or not metadata["title"]:
            raise ValueError("metadata title is required.")

        if not self.dry_run:
            raise NotImplementedError(
                "YouTubeStudioPublisher real upload is not implemented yet."
            )

        result = {
            "status": "dry_run",
            "video_path": video_path,
            "title": metadata["title"],
            "description": metadata.get("description", ""),
            "tags": metadata.get("tags", []),
        }
        if self.browser is not None:
            self._record_browser_dry_run(video_path, result)

        self._save_dry_run_result(result)
        return result

    def _record_browser_dry_run(self, video_path: str, metadata: dict) -> None:
        tags = metadata.get("tags", [])
        tags_text = ", ".join(tags) if isinstance(tags, list) else str(tags)

        self.browser.open(self.upload_url)
        self.browser.upload("input[type=file]", video_path)
        self.browser.fill("input[name=title]", metadata["title"])
        self.browser.fill(
            "textarea[name=description]",
            metadata.get("description", ""),
        )
        self.browser.fill("input[name=tags]", tags_text)
        self.browser.click("button[data-test-id=draft-save]")

    def _save_dry_run_result(self, result: dict) -> Path:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        output_path = self.output_dir / f"youtube_dry_run_{uuid4().hex}.json"
        output_path.write_text(
            json.dumps(result, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return output_path
