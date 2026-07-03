from types import SimpleNamespace

import pytest

from company.generators.moviepy_editor import MoviePyEditor


class FakeAudioClip:
    def __init__(self, path):
        self.path = path
        self.duration = 1.0
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
            file.write(b"fake mp4")

    def close(self):
        self.closed = True


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


def test_moviepy_editor_empty_image_paths_raises_value_error(tmp_path):
    editor = MoviePyEditor(output_dir=str(tmp_path))

    with pytest.raises(ValueError, match="image_paths must not be empty"):
        editor.generate([], ["audio.wav"])


def test_moviepy_editor_empty_audio_paths_raises_value_error(tmp_path):
    editor = MoviePyEditor(output_dir=str(tmp_path))

    with pytest.raises(ValueError, match="audio_paths must not be empty"):
        editor.generate(["image.png"], [])


def test_moviepy_editor_returns_mp4_path(monkeypatch, tmp_path):
    final_clips = []
    editor = MoviePyEditor(output_dir=str(tmp_path), fps=12)
    monkeypatch.setattr(editor, "_load_moviepy", lambda: _fake_moviepy(final_clips))

    output_path = editor.generate(["image.png"], ["audio.wav"])

    assert output_path.endswith("final_video.mp4")
    assert str(tmp_path) in output_path


def test_moviepy_editor_writes_mp4_file(monkeypatch, tmp_path):
    final_clips = []
    editor = MoviePyEditor(output_dir=str(tmp_path))
    monkeypatch.setattr(editor, "_load_moviepy", lambda: _fake_moviepy(final_clips))

    output_path = editor.generate(["image.png"], ["audio.wav"])

    assert (tmp_path / "final_video.mp4").exists()
    assert (tmp_path / "final_video.mp4").read_bytes() == b"fake mp4"
    assert output_path == str(tmp_path / "final_video.mp4")


def test_moviepy_editor_uses_moviepy_with_expected_write_options(
    monkeypatch,
    tmp_path,
):
    final_clips = []
    editor = MoviePyEditor(output_dir=str(tmp_path), fps=30)
    monkeypatch.setattr(editor, "_load_moviepy", lambda: _fake_moviepy(final_clips))

    editor.generate(["image.png"], ["audio.wav"])
    final_clip = final_clips[0]["clip"]

    assert final_clips[0]["method"] == "compose"
    assert final_clip.write_calls == [
        {
            "output_path": str(tmp_path / "final_video.mp4"),
            "fps": 30,
            "codec": "libx264",
            "audio_codec": "aac",
        }
    ]
