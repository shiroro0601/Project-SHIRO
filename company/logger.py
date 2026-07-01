"""
Project SHIRO
ログ管理
"""

from datetime import datetime
from pathlib import Path

from config import LOG_FILE


class Logger:
    """
    共通ログクラス
    """

    def __init__(self):
        Path(LOG_FILE).parent.mkdir(parents=True, exist_ok=True)

    def write(self, department: str, name: str, message: str) -> None:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        text = (
            f"[{now}] "
            f"[{department}] "
            f"[{name}] "
            f"{message}"
        )

        print(text)

        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(text + "\n")