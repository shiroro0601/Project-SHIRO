import json
from pathlib import Path
from urllib import parse, request

from audio_utils import get_wav_duration

VOICEVOX_URL = "http://127.0.0.1:50021"
OUTPUT_DIR = Path("outputs/voices")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def create_voice(text, output_path, speaker=3):
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    query_params = parse.urlencode({
        "text": text,
        "speaker": speaker
    })

    audio_query_url = f"{VOICEVOX_URL}/audio_query?{query_params}"

    req = request.Request(audio_query_url, method="POST")

    with request.urlopen(req) as response:
        audio_query = json.loads(response.read().decode("utf-8"))

    synthesis_params = parse.urlencode({
        "speaker": speaker
    })

    synthesis_url = f"{VOICEVOX_URL}/synthesis?{synthesis_params}"

    req = request.Request(
        synthesis_url,
        data=json.dumps(audio_query).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST"
    )

    with request.urlopen(req) as response:
        wav_data = response.read()

    output_path.write_bytes(wav_data)

    duration = get_wav_duration(output_path)

    print("音声を保存しました:", output_path)
    print(f"音声長: {duration:.2f}秒")

    return duration

if __name__ == "__main__":
    create_voice(
        "男性が本命女性だけに見せる行動。実はかなり分かりやすいです。",
        OUTPUT_DIR / "voice1.wav"
    )