from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import (
    ImageClip,
    AudioFileClip,
    CompositeVideoClip,
    concatenate_videoclips
)

FONT_PATH = r"C:\Windows\Fonts\meiryo.ttc"
TEMP_DIR = Path("temp")
TEMP_DIR.mkdir(exist_ok=True)

def create_subtitle_image(text, output_path, width=1280, height=220):
    img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    box_y = 20
    draw.rounded_rectangle(
        (70, box_y, width - 70, height - 20),
        radius=20,
        fill=(0, 0, 0, 170)
    )

    font = ImageFont.truetype(FONT_PATH, 42)

    max_width = width - 180
    lines = []
    current = ""

    for char in text:
        test = current + char
        bbox = draw.textbbox((0, 0), test, font=font)
        if bbox[2] - bbox[0] <= max_width:
            current = test
        else:
            lines.append(current)
            current = char

    if current:
        lines.append(current)

    total_h = len(lines) * 56
    y = (height - total_h) // 2

    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        text_w = bbox[2] - bbox[0]
        x = (width - text_w) // 2

        draw.text((x + 2, y + 2), line, font=font, fill=(0, 0, 0, 220))
        draw.text((x, y), line, font=font, fill=(255, 255, 255, 255))
        y += 56

    img.save(output_path)

def make_video(project):
    clips = []

    for i, scene in enumerate(project["scenes"], start=1):
        duration = float(scene["duration"])

        audio = AudioFileClip(scene["voice"])

        base = (
            ImageClip(scene["image"])
            .set_duration(duration)
            .resize(height=720)
            .set_position("center")
            .set_audio(audio)
        )

        subtitle_path = TEMP_DIR / f"subtitle_{i}.png"
        create_subtitle_image(scene["text"], subtitle_path)

        subtitle = (
            ImageClip(str(subtitle_path))
            .set_duration(duration)
            .set_position(("center", "bottom"))
        )

        clip = CompositeVideoClip(
            [base, subtitle],
            size=(1280, 720)
        ).set_duration(duration)

        clips.append(clip)

    final = concatenate_videoclips(clips, method="compose")

    final.write_videofile(
        project["output"],
        fps=30,
        codec="libx264",
        audio_codec="aac"
    )