from company.reports.run_report import RunReport


class RunReportMemoryAdapter:
    def to_memory_record(self, report: RunReport) -> dict:
        scene_count = len(report.scenes)
        asset_count = len(report.assets)
        return {
            "type": "real_ai_company_run",
            "topic": report.topic,
            "created_at": report.created_at,
            "media_mode": report.media_mode,
            "status": report.status,
            "script_title": report.script_title,
            "scene_count": scene_count,
            "asset_count": asset_count,
            "video_path": report.video_path,
            "scene_video_path": report.scene_video_path,
            "summary": (
                f"{report.topic} を {report.media_mode} mode で制作し、"
                f"{scene_count} scenes / {asset_count} assets を生成しました。"
            ),
        }
