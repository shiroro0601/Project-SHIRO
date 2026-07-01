from datetime import datetime


class Job:
    def __init__(self, theme: str, job_id: str = None):
        self.data = {
            "job_id": job_id or self._create_job_id(),
            "theme": theme,
            "status": "created",
            "created_at": self._now(),
            "updated_at": self._now(),
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

    def get(self, key: str, default=None):
        return self.data.get(key, default)

    def set(self, key: str, value):
        self.data[key] = value
        self.touch()

    def update_section(self, section: str, value):
        self.data[section] = value
        self.log(f"{section} updated")
        self.touch()

    def update_status(self, status: str):
        self.data["status"] = status
        self.log(f"status changed to {status}")
        self.touch()

    def add_output(self, output_type: str, value):
        outputs = self.data.setdefault("outputs", {})

        if output_type not in outputs:
            outputs[output_type] = []

        if isinstance(outputs[output_type], list):
            outputs[output_type].append(value)
        else:
            outputs[output_type] = value

        self.log(f"output added: {output_type}")
        self.touch()

    def log(self, message: str):
        self.data.setdefault("logs", []).append({
            "time": self._now(),
            "message": message
        })

    def touch(self):
        self.data["updated_at"] = self._now()

    def to_dict(self) -> dict:
        return self.data

    @classmethod
    def from_dict(cls, data: dict):
        job = cls(theme=data.get("theme", ""), job_id=data.get("job_id"))
        job.data = data
        return job

    def _create_job_id(self) -> str:
        return f"job_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    def _now(self) -> str:
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


if __name__ == "__main__":
    job = Job("猫の意外な雑学")
    job.update_status("running")
    job.update_section("planner", {
        "title": "猫の知られざる能力",
        "scenes": ["導入", "身体能力", "聴覚", "記憶力", "まとめ"]
    })
    job.add_output("images", "outputs/images/scene1.png")

    print("Jobクラス テスト完了")
    print("job_id:", job.get("job_id"))
    print("theme:", job.get("theme"))
    print("status:", job.get("status"))
    print("outputs:", job.get("outputs"))