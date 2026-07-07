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
        topic = self._resolve_input(task)
        if self.provider is not None:
            return self.provider.generate(self._build_prompt(topic))
        return f"Research result for: {topic}"

    def finalize(self, result):
        return result

    def _build_prompt(self, topic: str) -> str:
        return (
            "あなたはYouTubeショート動画のリサーチャーです。\n"
            "あなたは指定テーマ専門のリサーチ担当です。\n"
            "指定テーマ以外を書いてはいけません。\n"
            "知らない場合でも別テーマへ変更禁止。\n"
            "次の調査テーマに直接関係する雑学だけを調査風に出してください。\n"
            "テーマから逸脱してはいけません。\n"
            "テーマに直接関係する情報だけを出してください。\n"
            "不明な場合でも、別テーマを提案してはいけません。\n"
            "猫の意外な雑学がテーマの場合は、必ず猫に直接関係する雑学だけを出してください。\n"
            "日本語で、5個、箇条書きで出してください。\n"
            "1個あたり1〜2文で、事実ベースにしてください。\n\n"
            "今回の調査テーマ:\n"
            f"{topic}\n\n"
            "【調査テーマ】\n"
            f"{topic}\n\n"
            "出力形式:\n"
            "【調査テーマ】\n"
            "...\n\n"
            "【雑学1】\n"
            "...\n\n"
            "【理由1】\n"
            "...\n\n"
            "【雑学2】\n"
            "...\n\n"
            "【理由2】\n"
            "...\n\n"
            "【雑学3】\n"
            "...\n\n"
            "【理由3】\n"
            "...\n\n"
            "【雑学4】\n"
            "...\n\n"
            "【理由4】\n"
            "...\n\n"
            "【雑学5】\n"
            "...\n\n"
            "【理由5】\n"
            "..."
        )

    def _resolve_input(self, task) -> str:
        topic = self._extract_topic(task)
        if topic != "unknown topic":
            return topic
        if self.topic and self.topic != "unknown topic":
            return self.topic
        return "unknown topic"

    def _extract_topic(self, task) -> str:
        if isinstance(task, str):
            value = task.strip()
            return value if value else "unknown topic"

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
        topic = self._resolve_input(task)
        if self.provider is not None:
            return self.provider.generate(self._build_prompt(topic))
        return f"Script draft for: {topic}"

    def finalize(self, result):
        return result

    def _build_prompt(self, topic: str) -> str:
        return (
            "あなたはYouTubeショート動画の台本作家です。\n"
            "以下のリサーチ結果だけを材料にして、60秒以内の日本語ナレーション台本を書いてください。\n"
            "入力された調査結果だけを使うこと。\n"
            "調査結果以外は禁止です。\n"
            "動物変更禁止。\n"
            "新しいテーマを作らないでください。\n"
            "推測追加禁止。\n"
            "research_resultに含まれないテーマ、ゲーム、車、パソコンなどへ変更しないでください。\n"
            "ネットワーク、別ジャンル、無関係な話題に移らないでください。\n"
            "ナレーションで読み上げやすい自然な文章にしてください。\n\n"
            "入力された調査結果:\n"
            f"{topic}\n\n"
            "リサーチ結果:\n"
            f"{topic}\n\n"
            "出力形式:\n"
            "【タイトル】\n"
            "...\n"
            "\n"
            "【ナレーション】\n"
            "...\n"
            "\n"
            "【画像指示】\n"
            "..."
        )

    def _resolve_input(self, task) -> str:
        topic = self._extract_topic(task)
        if topic != "unknown topic":
            return topic
        if self.topic and self.topic != "unknown topic":
            return self.topic
        return "unknown topic"

    def _extract_topic(self, task) -> str:
        if isinstance(task, str):
            value = task.strip()
            return value if value else "unknown topic"

        input_data = getattr(task, "input_data", {}) or {}

        for key in ("research_result", "script", "topic", "theme", "title"):
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
        topic = self._resolve_input(task)
        if self.provider is not None:
            return self.provider.generate(self._build_prompt(topic))
        return f"Review result: approved for {topic}"

    def finalize(self, result):
        return result

    def _build_prompt(self, topic: str) -> str:
        return (
            "あなたはYouTubeショート動画の編集長です。\n"
            "以下の台本だけをレビューしてください。\n"
            "executeで受け取った台本だけを評価してください。\n"
            "台本が入力されている前提で評価してください。\n"
            "「内容がない」「不明」とは言わないでください。\n"
            "判定は必ず「合格」または「修正必要」のどちらかだけにしてください。\n"
            "「合格。ただし修正必要」のような矛盾した判定は禁止です。\n"
            "「合格ですが修正必要」は禁止です。\n"
            "「一応合格」は禁止です。\n"
            "「改善推奨だが合格」は禁止です。\n"
            "テーマ不一致なら必ず「修正必要」と判定してください。\n"
            "改善点が1つでもある場合は「修正必要」と判定してください。\n"
            "事実不明、不自然な日本語、指定形式の欠落がある場合も「修正必要」と判定してください。\n"
            "出力形式以外の見出しや前置きは書かないでください。\n"
            "必ず【評価】【改善点】【判定】の3ブロックをすべて出力してください。\n"
            "【評価】には台本の良い点または問題点を1〜3文で書いてください。\n"
            "【改善点】には具体的な修正案を1〜3個書いてください。\n"
            "【判定】の次の1行には「合格」または「修正必要」だけを書いてください。\n"
            "日本語で出力してください。\n\n"
            "評価対象台本:\n"
            f"{topic}\n\n"
            "台本:\n"
            f"{topic}\n\n"
            "出力形式:\n"
            "【評価】\n"
            "...\n\n"
            "【改善点】\n"
            "...\n\n"
            "【判定】\n"
            "合格 または 修正必要"
        )

    def _resolve_input(self, task) -> str:
        topic = self._extract_topic(task)
        if topic != "unknown topic":
            return topic
        if self.topic and self.topic != "unknown topic":
            return self.topic
        return "unknown topic"

    def _extract_topic(self, task) -> str:
        if isinstance(task, str):
            value = task.strip()
            return value if value else "unknown topic"

        input_data = getattr(task, "input_data", {}) or {}

        for key in ("script_result", "script", "topic", "theme", "title"):
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
