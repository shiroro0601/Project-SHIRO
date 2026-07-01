import json
from pathlib import Path
from datetime import datetime


class CompanyMemory:
    def __init__(self, memory_path="outputs/memory/company_memory.json"):
        self.memory_path = Path(memory_path)
        self.memory_path.parent.mkdir(parents=True, exist_ok=True)

        if not self.memory_path.exists():
            self._write(self._default_data())

    def load(self) -> dict:
        try:
            with open(self.memory_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            if "jobs" not in data:
                data["jobs"] = []

            return data

        except Exception:
            return self._default_data()

    def save(self, data: dict):
        data["updated_at"] = self._now()
        self._write(data)

    def save_job(self, job):
        data = self.load()
        job_data = job.to_dict() if hasattr(job, "to_dict") else job

        job_id = job_data.get("job_id")

        replaced = False
        for i, existing_job in enumerate(data["jobs"]):
            if existing_job.get("job_id") == job_id:
                data["jobs"][i] = job_data
                replaced = True
                break

        if not replaced:
            data["jobs"].append(job_data)

        self.save(data)
        return job_id

    def get_job(self, job_id: str):
        data = self.load()

        for job in data.get("jobs", []):
            if job.get("job_id") == job_id:
                return job

        return None

    def latest_job(self):
        data = self.load()
        jobs = data.get("jobs", [])

        if not jobs:
            return None

        return jobs[-1]

    def add_job(self, theme: str) -> str:
        data = self.load()

        job_id = f"job_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        job = {
            "job_id": job_id,
            "theme": theme,
            "created_at": self._now(),
            "updated_at": self._now(),
            "status": "created",
            "planner": None,
            "script_writer": None,
            "director": None,
            "artist": None,
            "voice_actor": None,
            "editor": None,
            "quality_checker": None,
            "outputs": {
                "images": [],
                "voices": [],
                "video": None,
                "report": None
            },
            "logs": []
        }

        data["jobs"].append(job)
        self.save(data)

        return job_id

    def update_job(self, job_id: str, section: str, content):
        data = self.load()

        for job in data["jobs"]:
            if job.get("job_id") == job_id:
                job[section] = content
                job["updated_at"] = self._now()
                self.save(data)
                return True

        return False

    def update_status(self, job_id: str, status: str):
        return self.update_job(job_id, "status", status)

    def _default_data(self) -> dict:
        return {
            "project": "Project SHIRO",
            "version": "0.9",
            "created_at": self._now(),
            "updated_at": self._now(),
            "jobs": []
        }

    def _write(self, data: dict):
        with open(self.memory_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _now(self) -> str:
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")