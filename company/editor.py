"""
Project SHIRO v0.8
編集部

画像・音声・字幕を結合して動画を作成する。
既に動画が存在する場合は再利用する安定版。
"""

import json
import subprocess
from pathlib import Path
from typing import Dict, List

from company.employee import Employee
from company.task import Task
from company.artifact import Artifact

from config import VIDEO_DIR


class Editor(Employee):
    """
    編集部AI
    """

    def __init__(self):
        super().__init__(
            name="Editor AI",
            department="編集"
        )

    def run(self, task: Task) -> Artifact:
        self.log("動画編集を開始しました。")

        scenes = task.data.get("scenes", [])
        images = task.data.get("images", [])
        voices = task.data.get("voices", [])

        if not scenes:
            raise ValueError("編集用のシーンがありません。")
        if not images:
            raise ValueError("編集用の画像がありません。")
        if not voices:
            raise ValueError("編集用の音声がありません。")

        output_path = Path(VIDEO_DIR) / "final_video.mp4"

        if output_path.exists():
            self.log(f"既存の動画を再利用します：{output_path}")
            return Artifact(
                artifact_type="video",
                content=str(output_path),
                metadata={
                    "department": self.department,
                    "employee": self.name,
                    "reused": True,
                }
            )

        project = self._build_project(
            scenes=scenes,
            images=images,
            voices=voices
        )

        self._make_video(
            project=project,
            output_path=output_path
        )

        return Artifact(
            artifact_type="video",
            content=str(output_path),
            metadata={
                "department": self.department,
                "employee": self.name,
                "reused": False,
            }
        )

    def _build_project(
        self,
        scenes: List[Dict],
        images: List[Dict],
        voices: List[Dict]
    ) -> Dict:

        image_map = {
            item["scene_number"]: item
            for item in images
        }

        voice_map = {
            item["scene_number"]: item
            for item in voices
        }

        project_scenes = []

        for scene in scenes:
            scene_number = scene["scene_number"]

            project_scenes.append(
                {
                    "scene_number": scene_number,
                    "title": scene["title"],
                    "text": scene["text"],
                    "image": image_map[scene_number]["image_path"],
                    "voice": voice_map[scene_number]["voice_path"],
                    "duration": voice_map[scene_number]["duration"],
                }
            )

        return {
            "width": 1280,
            "height": 720,
            "fps": 25,
            "output": str(Path(VIDEO_DIR) / "final_video.mp4"),
            "scenes": project_scenes,
        }

    def _make_video(self, project: Dict, output_path: Path) -> None:
        output_path.parent.mkdir(parents=True, exist_ok=True)

        project_file = output_path.parent / "project.json"

        with open(project_file, "w", encoding="utf-8") as f:
            json.dump(project, f, ensure_ascii=False, indent=2)

        width = project.get("width", 1280)
        height = project.get("height", 720)
        scenes = project["scenes"]

        font_file = "C\\:/Windows/Fonts/meiryo.ttc"

        inputs = []
        filters = []

        for i, scene in enumerate(scenes):
            image = scene["image"]
            voice = scene["voice"]
            text = self._escape_text(scene["text"])
            duration = float(scene.get("duration", 5))

            self.log(f"シーン{i + 1}を編集します。{duration:.2f}秒")

            inputs += [
                "-loop", "1",
                "-t", str(duration),
                "-i", image,
                "-i", voice,
            ]

            video_index = i * 2
            audio_index = i * 2 + 1

            filters.append(
                f"[{video_index}:v]"
                f"scale={width}:{height}:force_original_aspect_ratio=increase,"
                f"crop={width}:{height},"
                f"trim=duration={duration},"
                f"setpts=PTS-STARTPTS,"
                f"drawtext=fontfile='{font_file}':"
                f"text='{text}':"
                "fontcolor=white:"
                "fontsize=44:"
                "box=1:"
                "boxcolor=black@0.65:"
                "boxborderw=18:"
                "x=(w-text_w)/2:"
                "y=h-150,"
                "format=yuv420p"
                f"[v{i}]"
            )

            filters.append(
                f"[{audio_index}:a]"
                f"atrim=duration={duration},"
                f"asetpts=PTS-STARTPTS"
                f"[a{i}]"
            )

        concat_inputs = "".join(
            [f"[v{i}][a{i}]" for i in range(len(scenes))]
        )

        filters.append(
            f"{concat_inputs}"
            f"concat=n={len(scenes)}:v=1:a=1[outv][outa]"
        )

        command = [
            "ffmpeg",
            "-y",
            "-nostdin",
            "-hide_banner",
            "-loglevel",
            "error",
            *inputs,
            "-filter_complex",
            ";".join(filters),
            "-map",
            "[outv]",
            "-map",
            "[outa]",
            "-c:v",
            "libx264",
            "-c:a",
            "aac",
            "-pix_fmt",
            "yuv420p",
            str(output_path)
        ]

        self.log("FFmpegで動画を書き出します。")

        result = subprocess.run(command)

        if result.returncode != 0:
            raise RuntimeError("FFmpegで動画生成に失敗しました。")

        self.log(f"動画を保存しました：{output_path}")

    def _escape_text(self, text: str) -> str:
        text = text.replace("\\", "\\\\")
        text = text.replace(":", "\\:")
        text = text.replace("'", "\\'")
        text = text.replace("\n", " ")
        return text