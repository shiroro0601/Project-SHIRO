from pathlib import Path
from types import SimpleNamespace

from company.artifacts.scene_asset import SceneAsset


class SceneVideoComposer:
    def compose(self, scene_assets: list[SceneAsset], output_path: str) -> str:
        raise NotImplementedError("SceneVideoComposer must implement compose().")


class FakeSceneVideoComposer:
    def __init__(self):
        self.received_scene_assets = []
        self.output_path = None

    def compose(self, scene_assets, output_path):
        self.received_scene_assets = scene_assets
        self.output_path = output_path
        return output_path


class MoviePySceneVideoComposer:
    def __init__(self, fps: int = 24):
        self.fps = fps

    def compose(self, scene_assets: list[SceneAsset], output_path: str) -> str:
        if not scene_assets:
            raise ValueError("scene_assets must not be empty.")

        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        self._write_video(scene_assets, output)
        return str(output)

    def _write_video(self, scene_assets: list[SceneAsset], output_path: Path) -> None:
        moviepy = self._load_moviepy()
        clips = []
        audio_clips = []
        final_clip = None

        try:
            for scene_asset in scene_assets:
                audio_clip = moviepy.AudioFileClip(scene_asset.voice_path)
                audio_clips.append(audio_clip)
                duration = self._resolve_duration(scene_asset, audio_clip)
                clip = moviepy.ImageClip(scene_asset.image_path)
                clip = self._set_duration(clip, duration)
                clip = self._set_audio(clip, audio_clip)
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

    def _resolve_duration(self, scene_asset: SceneAsset, audio_clip) -> float:
        scene_duration = float(scene_asset.duration_seconds)
        audio_duration = getattr(audio_clip, "duration", None)
        if audio_duration is None:
            return scene_duration
        return max(scene_duration, float(audio_duration))

    def _set_duration(self, clip, duration: float):
        if hasattr(clip, "set_duration"):
            return clip.set_duration(duration)
        if hasattr(clip, "with_duration"):
            return clip.with_duration(duration)
        raise RuntimeError("MoviePy ImageClip does not support duration setting.")

    def _set_audio(self, clip, audio_clip):
        if hasattr(clip, "set_audio"):
            return clip.set_audio(audio_clip)
        if hasattr(clip, "with_audio"):
            return clip.with_audio(audio_clip)
        raise RuntimeError("MoviePy ImageClip does not support audio setting.")

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
                raise RuntimeError(
                    "MoviePy is required for MoviePySceneVideoComposer."
                ) from exc

        return SimpleNamespace(
            AudioFileClip=AudioFileClip,
            ImageClip=ImageClip,
            concatenate_videoclips=concatenate_videoclips,
        )

    def _close_clip(self, clip) -> None:
        if clip is not None and hasattr(clip, "close"):
            clip.close()
