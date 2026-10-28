"""Voix off gratuite avec edge-tts (voix neuronales Microsoft, sans clé API)."""
import asyncio
import subprocess
import time

import edge_tts

import config


async def _save(text: str, path: str) -> None:
    await edge_tts.Communicate(text, config.VOICE, rate=config.RATE).save(path)


def synth(text: str, path: str) -> float:
    last = None
    for attempt in range(4):
        try:
            asyncio.run(_save(text, path))
            d = duration(path)
            if d > 0.3:
                return d
        except Exception as e:
            last = e
        time.sleep(3 * (attempt + 1))
    raise RuntimeError(f"Échec TTS : {last}")


def duration(path: str) -> float:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path],
        capture_output=True, text=True, check=True,
    ).stdout.strip()
    return float(out)
