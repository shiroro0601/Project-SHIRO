import re

from company.artifacts.scene_artifact import SceneArtifact
from company.artifacts.script_artifact import ScriptArtifact


class ScriptArtifactParser:
    def parse(self, text: str) -> ScriptArtifact:
        raw_text = text or ""
        title = self._extract_section(raw_text, "タイトル")
        scenes = self._parse_scenes(raw_text)
        if scenes:
            return ScriptArtifact(
                title=title or "untitled",
                narration="\n".join(scene.narration for scene in scenes if scene.narration),
                image_prompts=[
                    scene.image_prompt for scene in scenes if scene.image_prompt
                ],
                scenes=scenes,
                raw_text=raw_text,
            )

        narration = self._extract_section(raw_text, "ナレーション")
        image_text = self._extract_section(raw_text, "画像指示")

        if not title and not narration and not image_text:
            return ScriptArtifact(
                title="untitled",
                narration=raw_text,
                image_prompts=[],
                scenes=[
                    SceneArtifact(
                        index=1,
                        narration=raw_text,
                        image_prompt=raw_text,
                        duration_seconds=60.0,
                    )
                ],
                raw_text=raw_text,
            )

        image_prompts = self._parse_image_prompts(image_text)
        scene_image_prompt = image_prompts[0] if image_prompts else narration or raw_text
        return ScriptArtifact(
            title=title or "untitled",
            narration=narration or raw_text,
            image_prompts=image_prompts,
            scenes=[
                SceneArtifact(
                    index=1,
                    narration=narration or raw_text,
                    image_prompt=scene_image_prompt,
                    duration_seconds=60.0,
                )
            ],
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

    def _parse_scenes(self, text: str) -> list[SceneArtifact]:
        scene_pattern = r"【シーン\s*(\d+)】\s*(.*?)(?=\n\s*【シーン\s*\d+】|\Z)"
        scenes = []
        for match in re.finditer(scene_pattern, text, flags=re.DOTALL):
            index = int(match.group(1))
            body = match.group(2).strip()
            narration = self._extract_field(body, "ナレーション", ["画像", "秒数"])
            image_prompt = self._extract_field(body, "画像", ["ナレーション", "秒数"])
            duration_text = self._extract_field(body, "秒数", ["ナレーション", "画像"])
            scenes.append(
                SceneArtifact(
                    index=index,
                    narration=narration,
                    image_prompt=image_prompt,
                    duration_seconds=self._parse_duration(duration_text),
                )
            )

        return scenes

    def _extract_field(
        self,
        text: str,
        field_name: str,
        following_field_names: list[str],
    ) -> str:
        following = "|".join(re.escape(name) for name in following_field_names)
        pattern = rf"{re.escape(field_name)}\s*[:：]\s*(.*?)(?=\n\s*(?:{following})\s*[:：]|\Z)"
        match = re.search(pattern, text, flags=re.DOTALL)
        if not match:
            return ""
        return match.group(1).strip()

    def _parse_duration(self, duration_text: str) -> float:
        match = re.search(r"\d+(?:\.\d+)?", duration_text or "")
        if not match:
            return 60.0
        return float(match.group(0))
