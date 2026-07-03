class AICompany:
    def __init__(self, runner=None, workflow=None):
        self.runner = runner or workflow

    def run(self, topic: str):
        normalized_topic = topic.strip()
        if not normalized_topic:
            raise ValueError("topic must not be empty.")

        if self.runner is not None:
            return self.runner.run(normalized_topic)

        return {
            "status": "completed",
            "topic": normalized_topic,
        }
