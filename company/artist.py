"""
Project SHIRO v0.8
美術部

Stable Diffusion AUTOMATIC1111 APIを使って画像生成する。
設定により、既存画像の再利用・再生成を切り替える。
"""

import base64
import json
from pathlib import Path
from urllib import request

from company.employee import Employee
from company.task import Task
from company.artifact import Artifact

from config import (
    IMAGE_DIR,
    STABLE_DIFFUSION_URL,
    SD_WIDTH,
    SD_HEIGHT,
    SD_STEPS,
    SD_CFG_SCALE,
    SD_SAMPLER,
    SD_NEGATIVE_PROMPT,
    SD_REGENERATE_IMAGES,
)


class Artist(Employee):
    """
    美術部AI
    """

    def __init__(self):
        super().__init__(
            name="Artist AI",
            department="美術"
        )

    def run(self, task: Task) -> Artifact:
        self.log("画像生成を開始しました。")

        scenes = task.data.get("scenes", [])

        if not scenes:
            raise ValueError("画像生成用のシーンがありません。")

        image_results = []

        for scene in scenes:
            scene_number = scene["scene_number"]
            raw_prompt = scene["image_prompt"]

            prompt = self._improve_prompt(raw_prompt)

            output_path = Path(IMAGE_DIR) / f"scene{scene_number}.png"

            if output_path.exists() and SD_REGENERATE_IMAGES:
                self.log(f"シーン{scene_number}の既存画像を削除して再生成します。")
                output_path.unlink()

            if output_path.exists():
                self.log(f"シーン{scene_number}の画像は既に存在するため再利用します。")
            else:
                self.log(f"シーン{scene_number}の画像を生成します。")

                self._generate_image(
                    prompt=prompt,
                    output_path=output_path
                )

            image_results.append(
                {
                    "scene_number": scene_number,
                    "image_path": str(output_path),
                    "prompt": prompt,
                }
            )

        return Artifact(
            artifact_type="images",
            content=image_results,
            metadata={
                "image_count": len(image_results),
                "department": self.department,
                "employee": self.name,
            }
        )

    def _improve_prompt(self, prompt: str) -> str:
        quality_prompt = (
            "masterpiece, best quality, ultra detailed, highly detailed, "
            "cinematic lighting, professional composition, sharp focus, "
            "beautiful background, 4k, anime illustration style"
        )

        return f"{prompt}, {quality_prompt}"

    def _generate_image(self, prompt: str, output_path: Path) -> None:
        output_path.parent.mkdir(parents=True, exist_ok=True)

        url = f"{STABLE_DIFFUSION_URL}/sdapi/v1/txt2img"

        payload = {
            "prompt": prompt,
            "negative_prompt": SD_NEGATIVE_PROMPT,
            "steps": SD_STEPS,
            "width": SD_WIDTH,
            "height": SD_HEIGHT,
            "cfg_scale": SD_CFG_SCALE,
            "sampler_name": SD_SAMPLER,
        }

        data = json.dumps(payload).encode("utf-8")

        req = request.Request(
            url,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST"
        )

        with request.urlopen(req, timeout=300) as response:
            result = json.loads(response.read().decode("utf-8"))

        image_base64 = result["images"][0]
        image_data = base64.b64decode(image_base64)

        output_path.write_bytes(image_data)

        self.log(f"画像を保存しました：{output_path}")