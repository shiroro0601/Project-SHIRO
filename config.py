"""
Project SHIRO Version 0.8
設定ファイル
"""

from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent

ASSETS_DIR = ROOT_DIR / "assets"
OUTPUTS_DIR = ROOT_DIR / "outputs"
PROMPTS_DIR = ROOT_DIR / "prompts"
TEMP_DIR = ROOT_DIR / "temp"

LOG_DIR = OUTPUTS_DIR / "logs"
IMAGE_DIR = OUTPUTS_DIR / "images"
VOICE_DIR = OUTPUTS_DIR / "voices"
VIDEO_DIR = OUTPUTS_DIR / "videos"

PROJECT_NAME = "Project SHIRO"
VERSION = "0.8.0"

LOG_FILE = LOG_DIR / "company.log"

STABLE_DIFFUSION_URL = "http://127.0.0.1:7860"

SD_WIDTH = 1280
SD_HEIGHT = 720
SD_STEPS = 30
SD_CFG_SCALE = 8
SD_SAMPLER = "DPM++ 2M Karras"

SD_NEGATIVE_PROMPT = (
    "low quality, worst quality, blurry, lowres, bad anatomy, "
    "bad hands, extra fingers, missing fingers, deformed, ugly, "
    "poorly drawn face, poorly drawn hands, text, watermark, logo"
)

# True  = 既存画像を削除して毎回再生成
# False = 既存画像があれば再利用
SD_REGENERATE_IMAGES = True

DIRECTORIES = [
    ASSETS_DIR,
    OUTPUTS_DIR,
    PROMPTS_DIR,
    TEMP_DIR,
    LOG_DIR,
    IMAGE_DIR,
    VOICE_DIR,
    VIDEO_DIR,
]


def create_directories() -> None:
    for directory in DIRECTORIES:
        directory.mkdir(parents=True, exist_ok=True)