import wave
from pathlib import Path

def get_wav_duration(filename):
    filename = str(Path(filename))
    with wave.open(filename, "rb") as wav:
        frames = wav.getnframes()
        rate = wav.getframerate()
        return frames / float(rate)