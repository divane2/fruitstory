"""Images des scènes. Par défaut : Pollinations (gratuit, sans clé). Repli : carte colorée si le service échoue."""
import io
import time
import urllib.parse

import requests
from PIL import Image, ImageDraw

import config


def _from_pollinations(prompt: str, seed: int):
    url = (
        "https://image.pollinations.ai/prompt/" + urllib.parse.quote(prompt)
        + f"?width={config.W}&height={config.H}&seed={seed}&nologo=true&model=flux"
    )
    for attempt in range(4):
        try:
            r = requests.get(url, timeout=150)
            if r.status_code == 200 and r.headers.get("content-type", "").startswith("image"):
                return Image.open(io.BytesIO(r.content)).convert("RGB")
        except Exception:
            pass
        time.sleep(5 * (attempt + 1))
    return None


def _fallback(idx: int) -> Image.Image:
    palette = [(255, 99, 71), (255, 165, 0), (50, 205, 50), (138, 43, 226), (30, 144, 255)]
    base = palette[idx % len(palette)]
    img = Image.new("RGB", (config.W, config.H), base)
    d = ImageDraw.Draw(img)
    for y in range(config.H):  # dégradé vertical
        k = y / config.H
        d.line([(0, y), (config.W, y)], fill=tuple(int(c * (1 - 0.6 * k)) for c in base))
    return img


def make_image(prompt: str, path: str, idx: int, seed: int) -> bool:
    img = _from_pollinations(prompt, seed)
    ok = img is not None
    if img is None:
        img = _fallback(idx)
    img.save(path, "JPEG", quality=92)
    return ok
