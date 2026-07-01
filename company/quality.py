"""
Project SHIRO v0.8
品質管理部

完成した動画・画像・音声・シーン情報を確認し、
簡易チェックレポートを作成する。
"""

from pathlib import Path

from company.employee import Employee
from company.task import Task
from company.artifact import Artifact


class QualityChecker(Employee):
    """
    品質管理部AI
    """

    def __init__(self):
        super().__init__(
            name="Quality Checker AI",
            department="品質管理"
        )

    def run(self, task: Task) -> Artifact:
        self.log("品質チェックを開始しました。")

        scenes = task.data.get("scenes", [])
        images = task.data.get("images", [])
        voices = task.data.get("voices", [])
        video_path = task.data.get("video_path", "")

        report = []

        report.append("【品質チェックレポート】")
        report.append("")

        # 動画確認
        if video_path and Path(video_path).exists():
            report.append("✅ 動画ファイル：存在します")
            report.append(f"動画パス：{video_path}")
        else:
            report.append("❌ 動画ファイル：見つかりません")

        report.append("")

        # シーン数確認
        report.append(f"シーン数：{len(scenes)}")
        report.append(f"画像数：{len(images)}")
        report.append(f"音声数：{len(voices)}")

        if len(scenes) == len(images) == len(voices):
            report.append("✅ シーン・画像・音声の数は一致しています")
        else:
            report.append("⚠ シーン・画像・音声の数が一致していません")

        report.append("")

        # 音声時間確認
        total_duration = 0.0

        for voice in voices:
            duration = float(voice.get("duration", 0))
            total_duration += duration

            if duration < 2:
                report.append(
                    f"⚠ シーン{voice['scene_number']}：音声が短すぎる可能性があります"
                )
            elif duration > 10:
                report.append(
                    f"⚠ シーン{voice['scene_number']}：音声が長すぎる可能性があります"
                )
            else:
                report.append(
                    f"✅ シーン{voice['scene_number']}：音声長 {duration:.2f}秒"
                )

        report.append("")
        report.append(f"合計動画時間目安：{total_duration:.2f}秒")

        report.append("")
        report.append("【総評】")

        if video_path and Path(video_path).exists() and len(scenes) == len(images) == len(voices):
            report.append("Project SHIRO v0.8.0 の動画生成は成功しています。")
        else:
            report.append("一部確認が必要です。")

        result_text = "\n".join(report)

        self.log("品質チェックを完了しました。")

        return Artifact(
            artifact_type="quality_report",
            content=result_text,
            metadata={
                "department": self.department,
                "employee": self.name,
            }
        )