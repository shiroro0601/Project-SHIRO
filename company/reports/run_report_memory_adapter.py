from company.reports.run_report import RunReport


class RunReportMemoryAdapter:
    def to_memory_record(self, report: RunReport) -> dict:
        scene_count = len(report.scenes)
        asset_count = len(report.assets)
        quality_feedback = getattr(report, "quality_feedback", {}) or {}
        quality_decision = quality_feedback.get("decision", "")
        quality_score = quality_feedback.get("score", 0.5)
        improvement_points = quality_feedback.get("improvement_points", "")
        quality_retry_count = getattr(report, "quality_retry_count", 0)
        research_retry_count = getattr(report, "research_retry_count", 0)
        ceo_decision = getattr(report, "ceo_decision", None) or {}
        ceo_action = ceo_decision.get("action", "")
        ceo_reason = ceo_decision.get("reason", "")
        stopped = bool(getattr(report, "stopped", False))
        stop_stage = getattr(report, "stop_stage", None)
        stop_reason = getattr(report, "stop_reason", "")
        production_skipped = bool(getattr(report, "production_skipped", False))
        summary = (
            f"{report.topic} を {report.media_mode} mode で制作し、"
            f"{scene_count} scenes / {asset_count} assets を生成しました。"
        )
        if quality_decision:
            summary += f"品質判定: {quality_decision}。"
        summary += f"Writer修正回数: {quality_retry_count}回。"
        summary += f"再調査回数: {research_retry_count}回。"
        if ceo_action:
            summary += f"CEO判断: {ceo_action}。"
        if stopped:
            summary += f"CEO判断により{stop_stage or 'review'}工程で制作停止。"
            if stop_reason:
                summary += f"理由: {stop_reason}。"
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
            "quality_decision": quality_decision,
            "quality_score": quality_score,
            "improvement_points": improvement_points,
            "quality_retry_count": quality_retry_count,
            "research_retry_count": research_retry_count,
            "ceo_action": ceo_action,
            "ceo_reason": ceo_reason,
            "stopped": stopped,
            "stop_stage": stop_stage,
            "stop_reason": stop_reason,
            "production_skipped": production_skipped,
            "summary": summary,
        }
