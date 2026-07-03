from typing import Protocol


class TextGenerationProvider(Protocol):
    def generate(self, prompt: str) -> str:
        ...


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

    def __init__(self, provider: TextGenerationProvider | None = None):
        self.topic = ""
        self.provider = provider

    def prepare(self, task):
        self.topic = self._extract_topic(task)
        return task

    def execute(self, task):
        topic = self.topic or self._extract_topic(task)
        if self.provider is not None:
            return self.provider.generate(
                f"次のテーマについて調査してください: {topic}"
            )
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

    def __init__(self, provider: TextGenerationProvider | None = None):
        self.topic = ""
        self.provider = provider

    def prepare(self, task):
        self.topic = self._extract_topic(task)
        return task

    def execute(self, task):
        topic = self.topic or self._extract_topic(task)
        if self.provider is not None:
            return self.provider.generate(
                f"次のテーマについてYouTubeショート用の台本を書いてください: {topic}"
            )
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

    def __init__(self, provider: TextGenerationProvider | None = None):
        self.topic = ""
        self.provider = provider

    def prepare(self, task):
        self.topic = self._extract_topic(task)
        return task

    def execute(self, task):
        topic = self.topic or self._extract_topic(task)
        if self.provider is not None:
            return self.provider.generate(
                f"次の成果物をレビューしてください: {topic}"
            )
        return f"Review result: approved for {topic}"

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


class ImageRole(DefaultEmployeeRole):
    name = "Image"

    def __init__(self, generator: TextGenerationProvider | None = None):
        self.topic = ""
        self.generator = generator

    def prepare(self, task):
        self.topic = self._extract_topic(task)
        return task

    def execute(self, task):
        topic = self.topic or self._extract_topic(task)
        prompt = f"Image prompt for: {topic}"
        if self.generator is not None:
            return self.generator.generate(prompt)
        return prompt

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
