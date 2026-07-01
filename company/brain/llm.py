import json
import urllib.request
import urllib.error


class LLM:
    def __init__(self, provider="dummy", model="shiro-local"):
        self.provider = provider
        self.model = model

    def generate(self, prompt: str, system: str = "") -> str:
        if self.provider == "dummy":
            return self._dummy_response(prompt, system)

        if self.provider == "ollama":
            return self._ollama(prompt, system)

        if self.provider == "lmstudio":
            return self._lmstudio(prompt, system)

        raise ValueError(f"未対応のLLM providerです: {self.provider}")

    def _dummy_response(self, prompt: str, system: str = "") -> str:
        return (
            "【DUMMY LLM RESPONSE】\n"
            "AI Brainは正常に動作しています。\n\n"
            f"system:\n{system}\n\n"
            f"prompt:\n{prompt}\n"
        )

    def _ollama(self, prompt: str, system: str = "") -> str:
        url = "http://localhost:11434/api/generate"

        payload = {
            "model": self.model,
            "prompt": prompt,
            "system": system,
            "stream": False,
        }

        data = json.dumps(payload).encode("utf-8")

        req = urllib.request.Request(
            url,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=120) as response:
                result = json.loads(response.read().decode("utf-8"))
                return result.get("response", "")
        except urllib.error.URLError as e:
            return f"【LLM ERROR】Ollamaに接続できません: {e}"

    def _lmstudio(self, prompt: str, system: str = "") -> str:
        url = "http://localhost:1234/v1/chat/completions"

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.7,
        }

        data = json.dumps(payload).encode("utf-8")

        req = urllib.request.Request(
            url,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=120) as response:
                result = json.loads(response.read().decode("utf-8"))
                return result["choices"][0]["message"]["content"]
        except Exception as e:
            return f"【LLM ERROR】LM Studioに接続できません: {e}"