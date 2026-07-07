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
            return self.provider.generate(self._build_prompt(topic))
        return f"Research result for: {topic}"

    def finalize(self, result):
        return result

    def _build_prompt(self, topic: str) -> str:
        return (
            "あなたはYouTubeショート動画のリサーチャーです。\n"
            "次のテーマについて、視聴者が「知らなかった」と感じる雑学を"
            "日本語で5個出してください。\n"
            "事実ベースで、短く、箇条書きで出してください。\n\n"
            "テーマ:\n"
            f"{topic}"
        )

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
            return self.provider.generate(self._build_prompt(topic))
        return f"Script draft for: {topic}"

    def finalize(self, result):
        return result

    def _build_prompt(self, topic: str) -> str:
        return (
            "あなたはYouTubeショート動画の台本作家です。\n"
            "以下のリサーチ結果をもとに、60秒以内の日本語ショート動画台本を"
            "書いてください。\n"
            "構成は「冒頭の引き → 本編3点 → まとめ」です。\n"
            "ナレーションで読み上げやすい自然な文章にしてください。\n\n"
            "リサーチ結果:\n"
            f"{topic}"
        )

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
            return self.provider.generate(self._build_prompt(topic))
        return f"Review result: approved for {topic}"

    def finalize(self, result):
        return result

    def _build_prompt(self, topic: str) -> str:
        return (
            "あなたはYouTubeショート動画の編集長です。\n"
            "以下の台本を日本語でレビューしてください。\n\n"
            "評価項目:\n"
            "- 冒頭に引きがあるか\n"
            "- 60秒以内に収まりそうか\n"
            "- 内容が分かりやすいか\n"
            "- 改善点\n\n"
            "最後に必ず「合格」または「修正必要」を出してください。\n\n"
            "台本:\n"
            f"{topic}"
        )

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


class VoiceRole(DefaultEmployeeRole):
    name = "Voice"

    def __init__(self, generator: TextGenerationProvider | None = None):
        self.topic = ""
        self.generator = generator

    def prepare(self, task):
        self.topic = self._extract_topic(task)
        return task

    def execute(self, task):
        topic = self.topic or self._extract_topic(task)
        text = f"Voice script for: {topic}"
        if self.generator is not None:
            return self.generator.generate(text)
        return text

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


class EditorRole(DefaultEmployeeRole):
    name = "Editor"

    def __init__(self, editor=None):
        self.topic = ""
        self.editor = editor

    def prepare(self, task):
        self.topic = self._extract_topic(task)
        return task

    def execute(self, task):
        if self.editor is not None:
            if hasattr(self.editor, "generate"):
                return self.editor.generate(task)
            if hasattr(self.editor, "edit"):
                return self.editor.edit(task)

        topic = self.topic or self._extract_topic(task)
        return f"Video edit plan for: {topic}"

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


class PublisherRole(DefaultEmployeeRole):
    name = "Publisher"

    def __init__(self, publisher=None):
        self.topic = ""
        self.publisher = publisher

    def prepare(self, task):
        self.topic = self._extract_topic(task)
        return task

    def execute(self, task):
        if self.publisher is not None:
            if hasattr(self.publisher, "generate"):
                return self.publisher.generate(task)
            if hasattr(self.publisher, "publish"):
                return self.publisher.publish(task)

        topic = self.topic or self._extract_topic(task)
        return {
            "title": topic,
            "description": "Generated by Project SHIRO",
            "tags": ["AI", "雑学", "Shorts"],
            "status": "draft",
        }

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
