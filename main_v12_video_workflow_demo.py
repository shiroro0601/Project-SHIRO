from pprint import pprint

from company.core.employee_role import EditorRole, ImageRole, VoiceRole
from company.core.task import TaskType
from company.core.task_factory import TaskFactory
from company.generators.moviepy_editor import MoviePyEditor
from company.generators.stable_diffusion_generator import StableDiffusionGenerator
from company.generators.voicevox_generator import VOICEVOXGenerator


class VideoEditorAdapter:
    def __init__(self, editor):
        self.editor = editor

    def generate(self, task):
        input_data = getattr(task, "input_data", {}) or {}
        image_paths = input_data.get("image_paths", [])
        audio_paths = input_data.get("audio_paths", [])
        return self.editor.generate(image_paths=image_paths, audio_paths=audio_paths)


def create_topic_task(topic: str):
    return TaskFactory.create_task(
        task_type=TaskType.GENERAL,
        instruction=f"{topic}の動画素材を制作してください。",
        input_data={"theme": topic},
    )


def create_edit_task(topic: str, image_paths: list[str], audio_paths: list[str]):
    return TaskFactory.create_task(
        task_type=TaskType.GENERAL,
        instruction=f"{topic}の動画を編集してください。",
        input_data={
            "theme": topic,
            "image_paths": image_paths,
            "audio_paths": audio_paths,
        },
    )


def run_demo(
    topic: str = "猫の意外な雑学",
    image_generator=None,
    voice_generator=None,
    editor=None,
):
    image_generator = image_generator or StableDiffusionGenerator()
    voice_generator = voice_generator or VOICEVOXGenerator()
    editor = editor or MoviePyEditor()

    image_role = ImageRole(generator=image_generator)
    voice_role = VoiceRole(generator=voice_generator)
    editor_role = EditorRole(editor=VideoEditorAdapter(editor))

    topic_task = create_topic_task(topic)

    image_role.prepare(topic_task)
    image_path = image_role.execute(topic_task)
    image_result = image_role.finalize(image_path)

    voice_role.prepare(topic_task)
    voice_path = voice_role.execute(topic_task)
    voice_result = voice_role.finalize(voice_path)

    edit_task = create_edit_task(
        topic=topic,
        image_paths=[image_result],
        audio_paths=[voice_result],
    )
    editor_role.prepare(edit_task)
    video_path = editor_role.execute(edit_task)
    video_result = editor_role.finalize(video_path)

    return {
        "topic": topic,
        "image_path": image_result,
        "voice_path": voice_result,
        "video_path": video_result,
    }


def main() -> None:
    print("Project SHIRO Version1.2 Video Production Workflow Demo")
    print("Flow: ImageRole -> VoiceRole -> EditorRole")
    print()

    try:
        result = run_demo()
    except RuntimeError as exc:
        print("Local video production service request failed.")
        print("Start Stable Diffusion WebUI and VOICEVOX locally before running.")
        print(f"Reason: {exc}")
        return

    pprint(result)


if __name__ == "__main__":
    main()
