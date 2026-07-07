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
            "次のテーマに直接関係する雑学だけを調査風に出してください。\n"
            "テーマから逸脱してはいけません。\n"
            "テーマに直接関係する情報だけを出してください。\n"
            "不明な場合でも、別テーマを提案してはいけません。\n"
            "日本語で、5個、箇条書きで出してください。\n"
            "1個あたり1〜2文で、事実ベースにしてください。\n\n"
            "テーマ:\n"
            f"{topic}\n\n"
            "出力形式:\n"
            "1. 雑学:\n"
            "   理由:\n"
            "2. 雑学:\n"
            "   理由:\n"
            "3. 雑学:\n"
            "   理由:\n"
            "4. 雑学:\n"
            "   理由:\n"
            "5. 雑学:\n"
            "   理由:"
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
            "以下のリサーチ結果だけを材料にして、60秒以内の日本語ナレーション台本を書いてください。\n"
            "新しいテーマを作らないでください。\n"
            "ネットワーク、別ジャンル、無関係な話題に移らないでください。\n"
            "構成は「冒頭の引き → 本編3点 → まとめ」です。\n"
            "ナレーションで読み上げやすい自然な文章にしてください。\n\n"
            "リサーチ結果:\n"
            f"{topic}\n\n"
            "出力形式:\n"
            "【冒頭の引き】\n"
            "...\n"
            "【本編1】\n"
            "...\n"
            "【本編2】\n"
            "...\n"
            "【本編3】\n"
            "...\n"
            "【まとめ】\n"
            "..."
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
            "以下の台本だけをレビューしてください。\n"
            "台本が入力されている前提で評価してください。\n"
            "「内容がない」「不明」とは言わないでください。\n"
            "日本語で出力してください。\n\n"
            "台本:\n"
            f"{topic}\n\n"
            "出力形式:\n"
            "【評価】\n"
            "- 冒頭に引きがあるか\n"
            "- 60秒以内:\n"
            "- 分かりやすさ:\n"
            "- 改善点\n\n"
            "【判定】\n"
            "合格 または 修正必要"
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
