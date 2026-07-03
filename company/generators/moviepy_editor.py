from pathlib import Path
from types import SimpleNamespace


class MoviePyEditor:
    def __init__(
        self,
        output_dir: str = "outputs/videos",
        fps: int = 24,
    ):
        self.output_dir = Path(output_dir)
        self.fps = fps

    def generate(self, image_paths: list[str], audio_paths: list[str]) -> str:
        if not image_paths:
            raise ValueError("image_paths must not be empty.")
        if not audio_paths:
            raise ValueError("audio_paths must not be empty.")

        self.output_dir.mkdir(parents=True, exist_ok=True)
        output_path = self.output_dir / "final_video.mp4"
        self._write_video(image_paths, audio_paths, output_path)
        return str(output_path)

    def _write_video(
        self,
        image_paths: list[str],
        audio_paths: list[str],
        output_path: Path,
    ) -> None:
        moviepy = self._load_moviepy()
        clips = []
        audio_clips = []
        final_clip = None

        try:
            for image_path, audio_path in zip(image_paths, audio_paths):
                audio_clip = moviepy.AudioFileClip(audio_path)
                audio_clips.append(audio_clip)
                duration = getattr(audio_clip, "duration", 1)
                clip = (
                    moviepy.ImageClip(image_path)
                    .set_duration(duration)
                    .set_audio(audio_clip)
                )
                clips.append(clip)

            final_clip = moviepy.concatenate_videoclips(clips, method="compose")
            final_clip.write_videofile(
                str(output_path),
                fps=self.fps,
                codec="libx264",
                audio_codec="aac",
            )
        finally:
            self._close_clip(final_clip)
            for clip in clips:
                self._close_clip(clip)
            for audio_clip in audio_clips:
                self._close_clip(audio_clip)

    def _load_moviepy(self):
        try:
            from moviepy.editor import (  # type: ignore
                AudioFileClip,
                ImageClip,
                concatenate_videoclips,
            )
        except ImportError:
            try:
                from moviepy import (  # type: ignore
                    AudioFileClip,
                    ImageClip,
                    concatenate_videoclips,
                )
            except ImportError as exc:
                raise RuntimeError("MoviePy is required for MoviePyEditor.") from exc

        return SimpleNamespace(
            AudioFileClip=AudioFileClip,
            ImageClip=ImageClip,
            concatenate_videoclips=concatenate_videoclips,
        )

    def _close_clip(self, clip) -> None:
        if clip is not None and hasattr(clip, "close"):
            clip.close()
