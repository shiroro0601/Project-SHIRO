import json
from pathlib import Path

PROJECT_FILE = "project.json"

def create_love_short_project(theme):
    project = {
        "title": theme,
        "output": "outputs/final_video.mp4",
        "width": 1280,
        "height": 720,
        "scenes": [
            {
                "image": "assets/scene1.png",
                "text": f"{theme}。実は答えはかなりシンプルです。",
                "image_prompt": "romantic anime couple, emotional atmosphere, cinematic lighting",
                "duration": 5
            },
            {
                "image": "assets/scene2.png",
                "text": "相手の心を動かすのは、特別なテクニックではありません。",
                "image_prompt": "anime girl and boy talking softly in cafe, warm light, romance",
                "duration": 5
            },
            {
                "image": "assets/scene3.png",
                "text": "大切なのは、安心して一緒にいられる空気を作ることです。",
                "image_prompt": "romantic anime couple walking at sunset, beautiful background",
                "duration": 5
            }
        ]
    }

    with open(PROJECT_FILE, "w", encoding="utf-8") as f:
        json.dump(project, f, ensure_ascii=False, indent=2)

    print("project.json を作成しました。")
    return project

if __name__ == "__main__":
    theme = input("恋愛ショートのテーマを入力してください：")
    create_love_short_project(theme)