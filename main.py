"""
Project SHIRO Version0.8
"""

from config import (
    PROJECT_NAME,
    VERSION,
    create_directories
)

from company.company import Company
from company.task import Task

from company.planner import Planner
from company.script_writer import ScriptWriter
from company.director import Director
from company.artist import Artist
from company.voice_actor import VoiceActor
from company.editor import Editor
from company.quality import QualityChecker


def main():
    create_directories()

    print()
    print("=" * 50)
    print(PROJECT_NAME)
    print("Version", VERSION)
    print("=" * 50)
    print()

    company = Company(PROJECT_NAME)

    company.hire(Planner())
    company.hire(ScriptWriter())
    company.hire(Director())
    company.hire(Artist())
    company.hire(VoiceActor())
    company.hire(Editor())
    company.hire(QualityChecker())

    company.info()

    plan_task = Task(
        title="動画企画",
        description="企画を考える"
    )

    plan = company.ceo.assign(
        "企画",
        plan_task
    )

    script_task = Task(
        title="脚本作成",
        description="脚本を書く",
        data={
            "plan": plan.content
        }
    )

    script = company.ceo.assign(
        "脚本",
        script_task
    )

    scene_task = Task(
        title="シーン分割",
        description="脚本をシーンごとに分割する",
        data={
            "script": script.content
        }
    )

    scenes = company.ceo.assign(
        "演出",
        scene_task
    )

    image_task = Task(
        title="画像生成",
        description="各シーンの画像をStable Diffusionで生成する",
        data={
            "scenes": scenes.content
        }
    )

    images = company.ceo.assign(
        "美術",
        image_task
    )

    voice_task = Task(
        title="音声生成",
        description="各シーンの音声をVOICEVOXで生成する",
        data={
            "scenes": scenes.content
        }
    )

    voices = company.ceo.assign(
        "声優",
        voice_task
    )

    edit_task = Task(
        title="動画編集",
        description="画像・音声・字幕を結合して動画を作る",
        data={
            "scenes": scenes.content,
            "images": images.content,
            "voices": voices.content,
        }
    )

    video = company.ceo.assign(
        "編集",
        edit_task
    )

    print("\n動画完成")
    print("--------------------------------")
    print(video.content)

    quality_task = Task(
        title="品質チェック",
        description="完成動画の品質を確認する",
        data={
            "scenes": scenes.content,
            "images": images.content,
            "voices": voices.content,
            "video_path": video.content,
        }
    )

    quality_report = company.ceo.assign(
        "品質管理",
        quality_task
    )

    print("\n品質チェック完成")
    print("--------------------------------")
    print(quality_report.content)


if __name__ == "__main__":
    main()