import base64
import json
from pathlib import Path
from urllib import request

API_URL = "http://127.0.0.1:7860/sdapi/v1/txt2img"

OUTPUT_DIR = Path("assets")
OUTPUT_DIR.mkdir(exist_ok=True)

def generate_image(prompt, output_path):
    payload = {
        "prompt": prompt,
        "negative_prompt": "low quality, blurry, bad anatomy, text, watermark",
        "steps": 20,
        "width": 1280,
        "height": 720,
        "cfg_scale": 7,
        "sampler_name": "Euler a"
    }

    data = json.dumps(payload).encode("utf-8")

    req = request.Request(
        API_URL,
        data=data,
        headers={"Content-Type": "application/json"}
    )

    print("画像生成中...")
    with request.urlopen(req) as response:
        result = json.loads(response.read().decode("utf-8"))

    image_base64 = result["images"][0]
    image_bytes = base64.b64decode(image_base64.split(",", 1)[0])

    output_path = Path(output_path)
    output_path.write_bytes(image_bytes)

    print("画像を保存しました:", output_path)

if __name__ == "__main__":
    generate_image(
        "beautiful cinematic bitcoin coin, futuristic city, dramatic lighting, high quality",
        OUTPUT_DIR / "scene1.png"
    )