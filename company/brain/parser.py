import json
import re


class BrainParser:
    @staticmethod
    def extract_json(text: str):
        if not text:
            return None

        text = text.strip()

        try:
            return json.loads(text)
        except Exception:
            pass

        match = re.search(r"\{[\s\S]*\}", text)
        if match:
            try:
                return json.loads(match.group(0))
            except Exception:
                return None

        return None