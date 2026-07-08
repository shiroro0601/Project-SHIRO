from types import SimpleNamespace

import pytest

from company.artifacts.scene_asset import SceneAsset
from company.video.scene_video_composer import MoviePySceneVideoComposer


class FakeAudioClip:
    def __init__(self, path):
        self.path = path
        self.duration = 0.5
        self.closed = False

    def close(self):
        self.closed = True


class FakeImageClip:
    def __init__(self, path):
        self.path = path
        self.duration = None
        self.audio = None
        self.closed = False

    def set_duration(self, duration):
        self.duration = duration
        return self

    def set_audio(self, audio):
        self.audio = audio
        return self

    def close(self):
        self.closed = True


class FakeFinalClip:
    def __init__(self, clips):
        self.clips = clips
        self.write_calls = []
        self.closed = False

    def write_videofile(self, output_path, fps, codec, audio_codec):
        self.write_calls.append(
            {
                "output_path": output_path,
                "fps": fps,
                "codec": codec,
                "audio_codec": audio_codec,
            }
        )
        with open(output_path, "wb") as file:
            file.write(b"fake scene mp4")

    def close(self):
        self.closed = True


def _scene_assets(tmp_path):
    image_1 = tmp_path / "scene_1.png"
    image_2 = tmp_path / "scene_2.png"
    voice_1 = tmp_path / "scene_1.wav"
    voice_2 = tmp_path / "scene_2.wav"
    image_1.write_bytes(b"fake png 1")
    image_2.write_bytes(b"fake png 2")
    voice_1.write_bytes(b"fake wav 1")
    voice_2.write_bytes(b"fake wav 2")

    return [
        SceneAsset(
            scene_index=1,
            image_path=str(image_1),
            voice_path=str(voice_1),
            narration="シーン1のナレーション",
            image_prompt="シーン1の画像",
            duration_seconds=1.0,
        ),
        SceneAsset(
            scene_index=2,
            image_path=str(image_2),
            voice_path=str(voice_2),
            narration="シーン2のナレーション",
            image_prompt="シーン2の画像",
            duration_seconds=2.0,
        ),
    ]


def _fake_moviepy(final_clips):
    def concatenate_videoclips(clips, method):
        final_clip = FakeFinalClip(clips)
        final_clips.append({"clip": final_clip, "method": method})
        return final_clip

    return SimpleNamespace(
        AudioFileClip=FakeAudioClip,
        ImageClip=FakeImageClip,
        concatenate_videoclips=concatenate_videoclips,
    )


def test_moviepy_scene_video_composer_empty_scene_assets_raises_value_error(
    tmp_path,
):
    composer = MoviePySceneVideoComposer()

    with pytest.raises(ValueError, match="scene_assets must not be empty"):
        composer.compose([], str(tmp_path / "final_video.mp4"))


def test_moviepy_scene_video_composer_generates_mp4(monkeypatch, tmp_path):
    final_clips = []
    composer = MoviePySceneVideoComposer(fps=12)
    monkeypatch.setattr(composer, "_load_moviepy", lambda: _fake_moviepy(final_clips))

    output_path = composer.compose(
        _scene_assets(tmp_path),
        str(tmp_path / "videos" / "final_video.mp4"),
    )

    assert output_path == str(tmp_path / "videos" / "final_video.mp4")
    assert (tmp_path / "videos" / "final_video.mp4").exists()
    assert (tmp_path / "videos" / "final_video.mp4").read_bytes() == b"fake scene mp4"


def test_moviepy_scene_video_composer_uses_scene_assets_and_write_options(
    monkeypatch,
    tmp_path,
):
    final_clips = []
    composer = MoviePySceneVideoComposer(fps=30)
    monkeypatch.setattr(composer, "_load_moviepy", lambda: _fake_moviepy(final_clips))

    composer.compose(_scene_assets(tmp_path), str(tmp_path / "final_video.mp4"))

    final_clip = final_clips[0]["clip"]
    scene_clips = final_clip.clips
    assert final_clips[0]["method"] == "compose"
    assert [clip.path for clip in scene_clips] == [
        str(tmp_path / "scene_1.png"),
        str(tmp_path / "scene_2.png"),
    ]
    assert [clip.audio.path for clip in scene_clips] == [
        str(tmp_path / "scene_1.wav"),
        str(tmp_path / "scene_2.wav"),
    ]
    assert [clip.duration for clip in scene_clips] == [1.0, 2.0]
    assert final_clip.write_calls == [
        {
            "output_path": str(tmp_path / "final_video.mp4"),
            "fps": 30,
            "codec": "libx264",
            "audio_codec": "aac",
        }
    ]
