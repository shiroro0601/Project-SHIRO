from typing import Protocol


class EmployeeRole(Protocol):
    name: str

    def prepare(self, task):
        ...

    def execute(self, task):
        ...

    def finalize(self, result):
        ...


class DefaultEmployeeRole:
    name = "Default"

    def prepare(self, task):
        return task

    def execute(self, task):
        return task

    def finalize(self, result):
        return result


class ResearchRole(DefaultEmployeeRole):
    name = "Researcher"

    def __init__(self):
        self.topic = ""

    def prepare(self, task):
        self.topic = self._extract_topic(task)
        return task

    def execute(self, task):
        topic = self.topic or self._extract_topic(task)
        return f"Research result for: {topic}"

    def finalize(self, result):
        return result

    def _extract_topic(self, task) -> str:
        input_data = getattr(task, "input_data", {}) or {}

        for key in ("topic", "theme", "title"):
            value = input_data.get(key)
            if value:
                return str(value)

        instruction = getattr(task, "instruction", "")
        if instruction:
            return instruction

        return "unknown topic"


class WriterRole(DefaultEmployeeRole):
    name = "Writer"

    def __init__(self):
        self.topic = ""

    def prepare(self, task):
        self.topic = self._extract_topic(task)
        return task

    def execute(self, task):
        topic = self.topic or self._extract_topic(task)
        return f"Script draft for: {topic}"

    def finalize(self, result):
        return result

    def _extract_topic(self, task) -> str:
        input_data = getattr(task, "input_data", {}) or {}

        for key in ("topic", "theme", "title"):
            value = input_data.get(key)
            if value:
                return str(value)

        instruction = getattr(task, "instruction", "")
        if instruction:
            return instruction

        return "unknown topic"


class ReviewerRole(DefaultEmployeeRole):
    name = "Reviewer"
