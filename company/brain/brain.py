from company.brain.llm import LLM
from company.brain.parser import BrainParser


class Brain:
    def __init__(self, provider="dummy", model="shiro-local"):
        self.llm = LLM(provider=provider, model=model)
        self.parser = BrainParser()

    def ask(self, role: str, prompt: str) -> str:
        system = self._system_prompt(role)
        return self.llm.generate(prompt=prompt, system=system)

    def chat(self, role: str, messages: list) -> str:
        text = ""
        for msg in messages:
            speaker = msg.get("speaker", "unknown")
            content = msg.get("content", "")
            text += f"{speaker}: {content}\n"

        return self.ask(role=role, prompt=text)

    def json(self, role: str, prompt: str):
        json_prompt = f"""
以下の指示に必ずJSON形式だけで答えてください。
説明文、前置き、コードブロックは禁止です。

指示:
{prompt}
"""
        response = self.ask(role=role, prompt=json_prompt)
        return self.parser.extract_json(response)

    def score(self, role: str, target: str) -> str:
        prompt = f"""
あなたは品質管理担当です。
以下の成果物を100点満点で評価してください。

評価対象:
{target}

出力形式:
点数:
良い点:
改善点:
次のアクション:
"""
        return self.ask(role=role, prompt=prompt)

    def retry(self, role: str, prompt: str, max_retry: int = 3) -> str:
        last_response = ""

        for i in range(max_retry):
            response = self.ask(role=role, prompt=prompt)
            last_response = response

            if response and "ERROR" not in response:
                return response

        return last_response

    def _system_prompt(self, role: str) -> str:
        base = """
あなたはProject SHIROのAI会社に所属する社員です。
目的は、YouTube向けの高品質な動画を自動生成することです。
日本語で、実用的で、具体的に答えてください。
"""

        roles = {
            "CEO": "あなたはCEOです。全体方針を決め、社員に指示します。",
            "Planner": "あなたは企画担当です。動画のテーマ、構成、狙いを考えます。",
            "ScriptWriter": "あなたは脚本家です。視聴維持率の高い台本を書きます。",
            "Director": "あなたは映像監督です。シーン構成と演出を設計します。",
            "Artist": "あなたは画像生成担当です。Stable Diffusion用のプロンプトを作ります。",
            "VoiceActor": "あなたは音声担当です。VOICEVOX向けに読みやすい文章へ整えます。",
            "Editor": "あなたは編集担当です。動画編集の流れを管理します。",
            "QualityChecker": "あなたは品質管理担当です。成果物を評価し改善案を出します。",
        }

        return base + "\n" + roles.get(role, f"あなたは{role}です。")