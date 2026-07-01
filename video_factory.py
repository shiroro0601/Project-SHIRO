import json
import subprocess
from pathlib import Path

PROJECT_FILE = "project.json"
FONT_FILE = r"C\:/Windows/Fonts/meiryo.ttc"
FPS = 25
MAX_SCENE_DURATION = 6.0

def load_project():
    with open(PROJECT_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def make_video(project):
    output_path = Path(project["output"])
    output_path.parent.mkdir(exist_ok=True)

    width = project.get("width", 1280)
    height = project.get("height", 720)
    scenes = project["scenes"]

    inputs = []
    filters = []

    for i, scene in enumerate(scenes):
        image = scene["image"]
        text = scene["text"]

        duration = float(scene.get("duration", 5))
        duration = min(duration, MAX_SCENE_DURATION)
        frames = int(duration * FPS)

        print(f"scene{i+1}: {duration:.2f}秒")

        inputs += ["-loop", "1", "-t", str(duration), "-i", image]

        filters.append(
            f"[{i}:v]"
            f"scale={width}:{height}:force_original_aspect_ratio=increase,"
            f"crop={width}:{height},"
            f"trim=duration={duration},"
            f"setpts=PTS-STARTPTS,"
            f"drawtext=fontfile='{FONT_FILE}':"
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

    concat_inputs = "".join([f"[v{i}]" for i in range(len(scenes))])
    filters.append(f"{concat_inputs}concat=n={len(scenes)}:v=1:a=0[outv]")

    command = [
        "ffmpeg",
        "-y",
        *inputs,
        "-filter_complex", ";".join(filters),
        "-map", "[outv]",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        str(output_path)
    ]

    print("動画を作成しています...")
    result = subprocess.run(command)

    if result.returncode == 0:
        print("完成しました:", output_path)
    else:
        print("エラーが発生しました。")

if __name__ == "__main__":
    project = load_project()
    make_video(project)