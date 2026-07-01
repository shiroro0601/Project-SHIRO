"""
Project SHIRO v0.8
LLM共通クラス

今はAPIなしで動く簡易AI。
将来OpenAI / Claude / Gemini / ローカルLLMに差し替える。
"""


class LLM:
    """
    全AI社員が使う共通AI
    """

    def chat(self, role: str, prompt: str) -> str:
        """
        役割ごとに返答を作る
        """

        if role == "planner":
            return self._planner(prompt)

        if role == "script_writer":
            return self._script_writer(prompt)

        if role == "director":
            return self._director(prompt)

        return "未対応のAI社員です。"

    def _planner(self, prompt: str) -> str:
        return """
タイトル：
AI社員だけで会社を作ってみた

企画概要：
AI社員がそれぞれ専門部署を持ち、企画・脚本・演出・画像・音声・編集を分担する。
人間1人でもAI会社を運営できる未来を見せる動画。

狙い：
視聴者に「個人でもAIを使えば会社のように動ける」と感じてもらう。
""".strip()

    def _script_writer(self, prompt: str) -> str:
        return f"""
【台本】

皆さんこんにちは。

今回は、AI社員だけで会社を作るプロジェクトを紹介します。

まず企画部が動画のテーマを考えます。

次に脚本部が、視聴者に伝わりやすい台本を作ります。

さらに演出部が、台本をシーンごとに分けます。

その後、美術部が画像を作り、声優部が音声を作ります。

最後に編集部が、それらをまとめて一本の動画にします。

つまりこれは、ただの自動動画生成ではありません。

一人でAI会社を動かすための仕組みです。

それでは実際に見ていきましょう。
""".strip()

    def _director(self, prompt: str) -> str:
        return """
1|導入|皆さんこんにちは。今回はAI社員だけで会社を作るプロジェクトを紹介します。|futuristic AI company office, Japanese startup, cinematic lighting
2|企画部|まず企画部が動画のテーマを考えます。|AI planner working at modern desk, idea board, futuristic office
3|脚本部|次に脚本部が、視聴者に伝わりやすい台本を作ります。|AI script writer typing screenplay, modern office, cinematic
4|制作部|美術部が画像を作り、声優部が音声を作ります。|AI production studio, image generation and voice recording, futuristic
5|編集部|最後に編集部が、それらをまとめて一本の動画にします。|AI video editing room, timeline monitor, completed video
""".strip()