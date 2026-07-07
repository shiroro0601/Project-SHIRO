import re

from company.artifacts.script_artifact import ScriptArtifact


class ScriptArtifactParser:
    def parse(self, text: str) -> ScriptArtifact:
        raw_text = text or ""
        title = self._extract_section(raw_text, "タイトル")
        narration = self._extract_section(raw_text, "ナレーション")
        image_text = self._extract_section(raw_text, "画像指示")

        if not title and not narration and not image_text:
            return ScriptArtifact(
                title="untitled",
                narration=raw_text,
                image_prompts=[],
                scenes=[],
                raw_text=raw_text,
            )

        image_prompts = self._parse_image_prompts(image_text)
        return ScriptArtifact(
            title=title or "untitled",
            narration=narration or raw_text,
            image_prompts=image_prompts,
            scenes=self._build_scenes(image_prompts),
            raw_text=raw_text,
        )

    def _extract_section(self, text: str, section_name: str) -> str:
        pattern = rf"【{re.escape(section_name)}】\s*(.*?)(?=\n\s*【[^】]+】|\Z)"
        match = re.search(pattern, text, flags=re.DOTALL)
        if not match:
            return ""
        return match.group(1).strip()

    def _parse_image_prompts(self, image_text: str) -> list[str]:
        if not image_text:
            return []

        prompts = []
        for line in image_text.splitlines():
            cleaned = re.sub(r"^\s*(?:[-*・]|\d+[.)、])\s*", "", line).strip()
            if cleaned:
                prompts.append(cleaned)

        return prompts or [image_text.strip()]

    def _build_scenes(self, image_prompts: list[str]) -> list[dict]:
        return [
            {
                "scene_number": index + 1,
                "image_prompt": image_prompt,
            }
            for index, image_prompt in enumerate(image_prompts)
        ]
