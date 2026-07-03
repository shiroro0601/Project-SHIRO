import json
from pathlib import Path
from uuid import uuid4


class YouTubeStudioPublisher:
    def __init__(
        self,
        dry_run: bool = True,
        upload_url: str = "https://studio.youtube.com",
        output_dir: str = "outputs/publish",
    ):
        self.dry_run = dry_run
        self.upload_url = upload_url
        self.output_dir = Path(output_dir)

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
        self._save_dry_run_result(result)
        return result

    def _save_dry_run_result(self, result: dict) -> Path:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        output_path = self.output_dir / f"youtube_dry_run_{uuid4().hex}.json"
        output_path.write_text(
            json.dumps(result, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return output_path
