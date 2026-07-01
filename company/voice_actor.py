"""
Project SHIRO v0.8
声優部

VOICEVOXを使って、各シーンの音声を生成する。
既に音声が存在する場合は再利用する。
"""

from pathlib import Path

from company.employee import Employee
from company.task import Task
from company.artifact import Artifact

from voice import create_voice
from audio_utils import get_wav_duration
from config import VOICE_DIR


class VoiceActor(Employee):
    """
    声優部AI
    """

    def __init__(self):
        super().__init__(
            name="Voice Actor AI",
            department="声優"
        )

    def run(self, task: Task) -> Artifact:
        self.log("音声生成を開始しました。")

        scenes = task.data.get("scenes", [])

        if not scenes:
            raise ValueError("音声生成用のシーンがありません。")

        voice_results = []

        for scene in scenes:
            scene_number = scene["scene_number"]
            text = scene["text"]

            output_path = Path(VOICE_DIR) / f"scene{scene_number}.wav"

            if output_path.exists():
                self.log(f"シーン{scene_number}の音声は既に存在するため再利用します。")
                duration = get_wav_duration(output_path)
            else:
                self.log(f"シーン{scene_number}の音声を生成します。")

                duration = create_voice(
                    text=text,
                    output_path=output_path,
                    speaker=3
                )

            voice_results.append(
                {
                    "scene_number": scene_number,
                    "text": text,
                    "voice_path": str(output_path),
                    "duration": duration,
                }
            )

        return Artifact(
            artifact_type="voices",
            content=voice_results,
            metadata={
                "voice_count": len(voice_results),
                "department": self.department,
                "employee": self.name,
            }
        )