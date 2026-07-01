from company.core import Job
from company.memory import CompanyMemory


if __name__ == "__main__":
    memory = CompanyMemory()
    job = Job("猫の意外な雑学")

    job.update_status("completed")
    job.update_section("planner", "Plannerテスト結果")
    job.update_section("script_writer", "ScriptWriterテスト結果")

    saved_job_id = memory.save_job(job)
    latest = memory.latest_job()

    print("CompanyMemory Job保存テスト 完了")
    print("saved_job_id:", saved_job_id)
    print("latest_job_id:", latest.get("job_id"))
    print("latest_status:", latest.get("status"))
    print("保存先:", memory.memory_path)